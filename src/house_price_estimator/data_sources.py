"""Approved source adapters and metadata-backed historical dataset registry."""

from __future__ import annotations

from dataclasses import dataclass
import csv
from io import StringIO
import json
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd

from .location_catalog import normalize_state


NAPIC_OPEN_TRANSACTION_PAGE_URL = (
    "https://napic.jpph.gov.my/ms/data-transaksi?category=36&id=241"
)
NAPIC_OPEN_TRANSACTION_CSV_URL = (
    "https://public.tableau.com/views/NewPublishOpenDataMei2024/"
    "Dashboard1.csv?:showVizHome=no"
)
MALAYSIAN_GOVERNMENT_OPEN_DATA_TERMS_URL = (
    "https://www.malaysia.gov.my/my/my-initiative/data-terbuka-kerajaan/"
    "dasar-strategi-dan-tadbir-urus/terma-penggunaan-data-terbuka-kerajaan"
)
MALAYSIAN_GOVERNMENT_OPEN_DATA_ATTRIBUTION = (
    "Data and information are subject to the Malaysian Government Open Data "
    "Terms of Use 1.0"
)
NAPIC_OPEN_TRANSACTION_SOURCE_NAME = "NAPIC/JPPH Open Transaction Data"
NAPIC_OPEN_TRANSACTION_PRICE_TYPE = "completed_transaction"
NAPIC_OPEN_TRANSACTION_STATE_FILTERS = {
    "Penang": "Pulau Pinang",
    "Putrajaya": "WP Putrajaya",
    "Labuan": "WP Labuan",
}

# Tableau publishes two visually identical Unit headings. Their positions are
# meaningful: the first belongs to Land/Parcel Area and the second to Main Floor Area.
NAPIC_OPEN_TRANSACTION_HEADERS = (
    "District",
    "Land/Parcel Area",
    "Main Floor Area",
    "Mukim",
    "Month, Year of Transaction Date",
    "Property Type",
    "Road Name",
    "Scheme Name/Area",
    "Tenure",
    "Transaction Price  ",
    "Unit",
    "Unit        ",
    "Unit Level",
)

_NAPIC_RAW_FIELDS = (
    "district_raw",
    "land_parcel_area_raw",
    "main_floor_area_raw",
    "mukim_raw",
    "transaction_month_raw",
    "property_type_raw",
    "road_name_raw",
    "scheme_name_area_raw",
    "tenure_raw",
    "transaction_price_rm_raw",
    "land_parcel_area_unit_raw",
    "main_floor_area_unit_raw",
    "unit_level_raw",
)


@dataclass(frozen=True)
class DatasetMetadata:
    """Legal, provenance, presentation, and artifact metadata for one dataset."""

    dataset_id: str
    title: str
    source_name: str
    source_urls: tuple[str, ...]
    source_documents: tuple[str, ...]
    price_type: str
    dataset_version: str
    schema_version: str
    licence_status: str
    redistribution_allowed: bool
    model_kind: str
    processed_data_path: str
    coverage_catalog_path: str
    area_label: str
    observed_price_label: str
    prediction_label: str
    limitations: tuple[str, ...]

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "DatasetMetadata":
        tuple_fields = {"source_urls", "source_documents", "limitations"}
        normalized = {
            key: tuple(value) if key in tuple_fields else value
            for key, value in values.items()
        }
        return cls(**normalized)


class AggregateSourceAdapter(Protocol):
    """A source-specific mapper that returns the generic aggregate schema."""

    metadata: DatasetMetadata

    def load(self) -> pd.DataFrame: ...


@dataclass(frozen=True)
class CsvAggregateAdapter:
    """Load an already column-mapped aggregate CSV without source assumptions."""

    path: Path
    metadata: DatasetMetadata
    column_mapping: Mapping[str, str] | None = None

    def load(self) -> pd.DataFrame:
        frame = pd.read_csv(self.path)
        if self.column_mapping:
            frame = frame.rename(columns=dict(self.column_mapping))
        return frame


class _DownloadResponse(Protocol):
    headers: Mapping[str, str]

    def read(self, size: int = -1) -> bytes: ...

    def __enter__(self) -> "_DownloadResponse": ...

    def __exit__(self, *args: object) -> None: ...


class DownloadOpener(Protocol):
    def __call__(
        self, request: Request, *, timeout: float
    ) -> _DownloadResponse: ...


class NapicOpenTransactionAdapter:
    """Import one explicitly requested state from NAPIC's public transaction view."""

    def __init__(self, state: str) -> None:
        self.state = normalize_state(state)

    @property
    def download_url(self) -> str:
        # The published dashboard defaults to Kuala Lumpur and intermittently returns
        # an empty response when that same value is supplied as an explicit filter.
        if self.state == "Kuala Lumpur":
            return NAPIC_OPEN_TRANSACTION_CSV_URL
        source_state = NAPIC_OPEN_TRANSACTION_STATE_FILTERS.get(self.state, self.state)
        return f"{NAPIC_OPEN_TRANSACTION_CSV_URL}&State={quote(source_state)}"

    @property
    def source_metadata(self) -> dict[str, str]:
        return {
            "source_name": NAPIC_OPEN_TRANSACTION_SOURCE_NAME,
            "source_page_url": NAPIC_OPEN_TRANSACTION_PAGE_URL,
            "source_download_url": self.download_url,
            "licence_name": "Malaysian Government Open Data Terms of Use 1.0",
            "licence_terms_url": MALAYSIAN_GOVERNMENT_OPEN_DATA_TERMS_URL,
            "required_attribution": MALAYSIAN_GOVERNMENT_OPEN_DATA_ATTRIBUTION,
            "price_type": NAPIC_OPEN_TRANSACTION_PRICE_TYPE,
            "requested_state": self.state,
        }

    def download(
        self,
        *,
        timeout_seconds: float = 60.0,
        max_bytes: int = 100_000_000,
        opener: DownloadOpener = urlopen,  # type: ignore[assignment]
    ) -> bytes:
        """Return a bounded per-state CSV response without writing a snapshot."""
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        request = Request(
            self.download_url,
            headers={
                "Accept": "text/csv",
                "User-Agent": "malaysia-house-price-estimator/0.1 (+source-import)",
            },
        )
        with opener(request, timeout=timeout_seconds) as response:
            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) > max_bytes:
                raise ValueError(
                    f"NAPIC response exceeds maximum of {max_bytes} bytes"
                )
            content = response.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise ValueError(f"NAPIC response exceeds maximum of {max_bytes} bytes")
        if not content.strip():
            raise ValueError("NAPIC returned an empty CSV export; retry later")
        return content

    def parse(self, content: bytes) -> pd.DataFrame:
        """Map an untouched CSV response to raw and parsed transaction fields."""
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("NAPIC CSV is not valid UTF-8") from exc
        reader = csv.reader(StringIO(text), strict=True)
        try:
            header = tuple(next(reader))
        except StopIteration as exc:
            raise ValueError("NAPIC CSV is empty") from exc
        if header != NAPIC_OPEN_TRANSACTION_HEADERS:
            raise ValueError(
                "NAPIC CSV header mismatch; duplicate Unit columns or source schema changed"
            )

        records: list[dict[str, Any]] = []
        for row_number, values in enumerate(reader, start=2):
            if not values or all(not value for value in values):
                continue
            if len(values) != len(NAPIC_OPEN_TRANSACTION_HEADERS):
                raise ValueError(
                    f"NAPIC CSV row {row_number} has {len(values)} columns; "
                    f"expected {len(NAPIC_OPEN_TRANSACTION_HEADERS)}"
                )
            raw = dict(zip(_NAPIC_RAW_FIELDS, values, strict=True))
            records.append(self._map_record(raw, row_number))

        columns = (
            "state",
            *_NAPIC_RAW_FIELDS,
            "district",
            "mukim",
            "property_type",
            "road_name",
            "scheme_name_area",
            "tenure",
            "transaction_date",
            "land_parcel_area_sqm",
            "main_floor_area_sqm",
            "transaction_price_rm",
            "unit_level",
            "price_type",
            "source_name",
            "source_page_url",
            "source_download_url",
            "licence_name",
            "licence_terms_url",
            "required_attribution",
            "validation_status",
            "validation_notes",
            "source_row_number",
        )
        return pd.DataFrame.from_records(records, columns=columns)

    def _map_record(self, raw: Mapping[str, str], row_number: int) -> dict[str, Any]:
        warnings: list[str] = []

        land_area = self._area_in_sqm(
            raw["land_parcel_area_raw"],
            raw["land_parcel_area_unit_raw"],
            "LAND_PARCEL_AREA",
            warnings,
        )
        main_floor_area = self._area_in_sqm(
            raw["main_floor_area_raw"],
            raw["main_floor_area_unit_raw"],
            "MAIN_FLOOR_AREA",
            warnings,
        )
        transaction_price = self._optional_number(
            raw["transaction_price_rm_raw"], "TRANSACTION_PRICE", warnings
        )
        unit_level = self._optional_number(raw["unit_level_raw"], "UNIT_LEVEL", warnings)
        transaction_date = self._transaction_date(raw["transaction_month_raw"], warnings)
        metadata = self.source_metadata
        return {
            "state": self.state,
            **raw,
            "district": self._optional_text(raw["district_raw"]),
            "mukim": self._optional_text(raw["mukim_raw"]),
            "property_type": self._optional_text(raw["property_type_raw"]),
            "road_name": self._optional_text(raw["road_name_raw"]),
            "scheme_name_area": self._optional_text(raw["scheme_name_area_raw"]),
            "tenure": self._optional_text(raw["tenure_raw"]),
            "transaction_date": transaction_date,
            "land_parcel_area_sqm": land_area,
            "main_floor_area_sqm": main_floor_area,
            "transaction_price_rm": transaction_price,
            "unit_level": unit_level,
            "price_type": metadata["price_type"],
            "source_name": metadata["source_name"],
            "source_page_url": metadata["source_page_url"],
            "source_download_url": metadata["source_download_url"],
            "licence_name": metadata["licence_name"],
            "licence_terms_url": metadata["licence_terms_url"],
            "required_attribution": metadata["required_attribution"],
            "validation_status": "needs_review" if warnings else "imported_unvalidated",
            "validation_notes": "|".join(warnings),
            "source_row_number": row_number,
        }

    @staticmethod
    def _optional_text(value: str) -> str | None:
        stripped = value.strip()
        return None if stripped in {"", "-", "–", "—"} else stripped

    @classmethod
    def _optional_number(
        cls, value: str, field: str, warnings: list[str]
    ) -> float | None:
        normalized = cls._optional_text(value)
        if normalized is None:
            return None
        try:
            return float(normalized.replace(",", ""))
        except ValueError:
            warnings.append(f"INVALID_{field}")
            return None

    @classmethod
    def _area_in_sqm(
        cls,
        value: str,
        unit: str,
        field: str,
        warnings: list[str],
    ) -> float | None:
        parsed = cls._optional_number(value, field, warnings)
        if parsed is None:
            return None
        normalized_unit = (cls._optional_text(unit) or "").lower().replace(" ", "")
        if normalized_unit not in {"sq.m", "sqm", "m²", "m2"}:
            warnings.append(f"UNSUPPORTED_{field}_UNIT")
            return None
        return parsed

    @classmethod
    def _transaction_date(
        cls, value: str, warnings: list[str]
    ) -> pd.Timestamp | None:
        normalized = cls._optional_text(value)
        if normalized is None:
            return None
        try:
            return pd.to_datetime(normalized, format="%B %Y", errors="raise")
        except (TypeError, ValueError):
            warnings.append("INVALID_TRANSACTION_DATE")
            return None


class NapicAggregateAdapter:
    """Adapter for the approved JPPH/NAPIC regional-average workbooks."""

    def __init__(
        self, terraced_path: str | Path, highrise_path: str | Path, metadata: DatasetMetadata
    ) -> None:
        self.terraced_path = Path(terraced_path)
        self.highrise_path = Path(highrise_path)
        self.metadata = metadata

    def load(self) -> pd.DataFrame:
        from .regional_area import load_regional_area_prices

        return load_regional_area_prices(self.terraced_path, self.highrise_path)


def load_dataset_metadata(path: str | Path) -> tuple[DatasetMetadata, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    datasets = payload.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError("dataset catalog must contain a non-empty datasets list")
    return tuple(DatasetMetadata.from_mapping(item) for item in datasets)

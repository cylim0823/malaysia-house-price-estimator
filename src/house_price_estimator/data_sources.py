"""Approved source adapters and metadata-backed historical dataset registry."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Protocol

import pandas as pd

from .data_pipeline import AggregateTransactionBundle
from .regional_area import RegionalAreaBundle


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
    model_path: str
    processed_data_path: str
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


class PenangOpenDataAdapter:
    """Compatibility adapter for the two approved Penang government tables."""

    DISTRICT_COLUMNS = {
        "Daerah Timur Laut": "Timur Laut (George Town / northeast island)",
        "Daerah Barat Daya": "Barat Daya (southwest island / Teluk Bahang)",
        "Daerah Utara": "Seberang Perai Utara",
        "Daerah Tengah": "Seberang Perai Tengah",
        "Daerah Selatan": "Seberang Perai Selatan",
    }
    EXCLUDED_TYPES = {"Vacant Plot", "Others", "Total"}

    def __init__(self, directory: str | Path, metadata: DatasetMetadata) -> None:
        self.directory = Path(directory)
        self.metadata = metadata

    def load(self) -> pd.DataFrame:
        # These filenames, columns, and district labels belong only to this source.
        counts = pd.read_csv(
            self.directory / "residential_transaction_counts_2017.csv", skiprows=2
        )
        values = pd.read_csv(
            self.directory / "residential_transaction_values_rm_million_2017.csv",
            skiprows=2,
        )
        observations: list[dict[str, Any]] = []
        for row_number, count_row in counts.iterrows():
            property_type = str(count_row["PRO_TYPE"]).strip()
            if property_type in self.EXCLUDED_TYPES:
                continue
            quarter = int(str(count_row["QUARTER"]).split()[0].removeprefix("Q"))
            value_row = values.iloc[row_number]
            for source_column, district in self.DISTRICT_COLUMNS.items():
                count = pd.to_numeric(count_row[source_column], errors="coerce")
                total_value = pd.to_numeric(value_row[source_column], errors="coerce")
                if pd.isna(count) or pd.isna(total_value) or count <= 0 or total_value <= 0:
                    continue
                observations.append(
                    {
                        "state": "Penang",
                        "district": district,
                        "property_type": property_type,
                        "year": 2017,
                        "quarter": quarter,
                        "transaction_count": int(count),
                        "transaction_value_rm": float(total_value),
                        "average_price_rm": float(total_value) / float(count),
                        "price_type": "completed_transaction_average",
                    }
                )
        return pd.DataFrame(observations).sort_values(
            ["district", "property_type", "quarter"]
        ).reset_index(drop=True)


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


def load_historical_bundle(metadata: DatasetMetadata, project_root: Path) -> Any:
    """Load a trusted repository-owned bundle selected by dataset metadata."""
    path = project_root / metadata.model_path
    loaders = {
        "aggregate_transactions": AggregateTransactionBundle.load,
        "published_averages": RegionalAreaBundle.load,
    }
    try:
        loader = loaders[metadata.model_kind]
    except KeyError as exc:
        raise ValueError(f"unsupported model kind: {metadata.model_kind}") from exc
    return loader(path)

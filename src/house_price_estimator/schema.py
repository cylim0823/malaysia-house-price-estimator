"""Versioned canonical structures shared by ingestion, cleaning, and modelling."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from . import SCHEMA_VERSION


class StrEnum(str, Enum):
    pass


class State(StrEnum):
    JOHOR="Johor"; KEDAH="Kedah"; KELANTAN="Kelantan"; MELAKA="Melaka"
    NEGERI_SEMBILAN="Negeri Sembilan"; PAHANG="Pahang"; PENANG="Penang"; PERAK="Perak"
    PERLIS="Perlis"; SABAH="Sabah"; SARAWAK="Sarawak"; SELANGOR="Selangor"
    TERENGGANU="Terengganu"; KUALA_LUMPUR="Kuala Lumpur"; PUTRAJAYA="Putrajaya"; LABUAN="Labuan"


class PriceType(StrEnum):
    ASKING="asking"; COMPLETED_TRANSACTION="completed_transaction"; AUCTION="auction"; RENTAL="rental"


class PropertyCategory(StrEnum):
    LANDED="landed"; HIGH_RISE="high_rise"; OTHER="other"; UNKNOWN="unknown"


class PropertyType(StrEnum):
    CONDOMINIUM="Condominium"; APARTMENT="Apartment"; FLAT="Flat"; STUDIO="Studio"; TERRACED="Terraced House"
    SEMI_DETACHED="Semi-Detached House"; BUNGALOW="Bungalow"; TOWNHOUSE="Townhouse"; OTHER="Other"


class Tenure(StrEnum):
    FREEHOLD="Freehold"; LEASEHOLD="Leasehold"; UNKNOWN="Unknown"


class Furnishing(StrEnum):
    UNFURNISHED="Unfurnished"; PARTLY="Partly Furnished"; FULLY="Fully Furnished"; UNKNOWN="Unknown"


class ValidationStatus(StrEnum):
    VALID="valid"; REVIEW="review"; REJECTED="rejected"


class DuplicateStatus(StrEnum):
    UNIQUE="unique"; EXACT="exact_duplicate"; POSSIBLE="possible_duplicate"


class OutlierStatus(StrEnum):
    NOT_OUTLIER="not_outlier"; POSSIBLE="possible_outlier"; DATA_ERROR="confirmed_data_error"
    LEGITIMATE="legitimate_outlier"; EXCLUDED="excluded_from_model"


class DataSplit(StrEnum):
    TRAIN="train"; VALIDATION="validation"; TEST="test"; UNASSIGNED="unassigned"


class DatePrecision(StrEnum):
    DAY="day"; MONTH="month"; QUARTER="quarter"; YEAR="year"; UNKNOWN="unknown"


@dataclass(frozen=True)
class RawRecord:
    record_id: str
    source_name: str
    values: dict[str, Any]
    imported_at: datetime
    ingestion_batch_id: str
    dataset_version: str
    schema_version: str = SCHEMA_VERSION
    is_synthetic: bool = False

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["imported_at"] = self.imported_at.isoformat()
        return result


@dataclass
class ValidationResult:
    status: ValidationStatus
    error_codes: list[str] = field(default_factory=list)
    warning_codes: list[str] = field(default_factory=list)
    review_required: bool = False


@dataclass
class DuplicateResult:
    status: DuplicateStatus = DuplicateStatus.UNIQUE
    group_id: str | None = None
    method: str | None = None
    confidence: float | None = None
    canonical_record_id: str | None = None
    evidence: list[str] = field(default_factory=list)


@dataclass
class CleanedRecord:
    record_id: str
    source_name: str
    price: float
    price_type: PriceType
    state: State
    property_type: PropertyType
    dataset_version: str
    raw_values: dict[str, Any]
    district: str | None = None
    built_up_sqft: float | None = None
    land_area_sqft: float | None = None
    bedrooms: int | None = None
    additional_bedrooms: int | None = None
    bathrooms: int | None = None
    validation: ValidationResult = field(default_factory=lambda: ValidationResult(ValidationStatus.VALID))
    duplicate: DuplicateResult = field(default_factory=DuplicateResult)
    outlier_status: OutlierStatus = OutlierStatus.NOT_OUTLIER
    schema_version: str = SCHEMA_VERSION
    is_synthetic: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelReadyRecord:
    features: dict[str, Any]
    target_price: float
    record_id: str
    duplicate_group_id: str
    event_date: str | None
    price_type: PriceType
    dataset_version: str

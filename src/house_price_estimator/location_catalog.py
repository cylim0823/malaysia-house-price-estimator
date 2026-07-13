"""Canonical Malaysian locations and data-driven historical coverage."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping


MALAYSIAN_STATES = (
    "Johor",
    "Kedah",
    "Kelantan",
    "Melaka",
    "Negeri Sembilan",
    "Pahang",
    "Penang",
    "Perak",
    "Perlis",
    "Sabah",
    "Sarawak",
    "Selangor",
    "Terengganu",
    "Kuala Lumpur",
    "Putrajaya",
    "Labuan",
)

STATE_ALIASES = {
    "kl": "Kuala Lumpur",
    "malacca": "Melaka",
    "pulau pinang": "Penang",
    "n sembilan": "Negeri Sembilan",
    "w p kuala lumpur": "Kuala Lumpur",
    "wp kuala lumpur": "Kuala Lumpur",
    "wilayah persekutuan kuala lumpur": "Kuala Lumpur",
    "w p putrajaya": "Putrajaya",
    "wp putrajaya": "Putrajaya",
    "w p labuan": "Labuan",
    "wp labuan": "Labuan",
}


def _location_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).strip()


def normalize_state(value: object) -> str:
    """Return one of the 16 canonical state or federal-territory names."""
    canonical = {_location_key(state): state for state in MALAYSIAN_STATES}
    canonical.update(STATE_ALIASES)
    key = _location_key(value)
    if key not in canonical:
        raise ValueError(f"unknown Malaysian state or federal territory: {value!r}")
    return canonical[key]


@dataclass(frozen=True, order=True)
class CoverageCombination:
    """One selectable state/location/type/period combination."""

    state: str
    area: str
    property_type: str
    year: int
    quarter: int


class CoverageCatalog:
    """Selector options derived solely from validated observation combinations."""

    def __init__(self, combinations: Iterable[CoverageCombination]) -> None:
        values = tuple(sorted(set(combinations)))
        if not values:
            raise ValueError("coverage must contain at least one validated combination")
        self._combinations = values

    @classmethod
    def from_observation_keys(
        cls, observations: Mapping[str, object]
    ) -> "CoverageCatalog":
        combinations: list[CoverageCombination] = []
        for key in observations:
            parts = key.split("|")
            if len(parts) != 5:
                raise ValueError(f"invalid historical observation key: {key!r}")
            state, area, property_type, year, quarter = parts
            combinations.append(
                CoverageCombination(
                    normalize_state(state), area, property_type, int(year), int(quarter)
                )
            )
        return cls(combinations)

    @property
    def combinations(self) -> tuple[CoverageCombination, ...]:
        return self._combinations

    @property
    def states(self) -> tuple[str, ...]:
        return tuple(sorted({item.state for item in self._combinations}))

    def areas(self, state: str) -> tuple[str, ...]:
        values = {item.area for item in self._combinations if item.state == state}
        if not values:
            raise ValueError(f"Unsupported state: {state}")
        return tuple(sorted(values))

    def property_types(self, state: str, area: str) -> tuple[str, ...]:
        values = {
            item.property_type
            for item in self._combinations
            if item.state == state and item.area == area
        }
        if not values:
            raise ValueError(f"Unsupported area for {state}: {area}")
        return tuple(sorted(values))

    def years(self, state: str, area: str, property_type: str) -> tuple[int, ...]:
        values = {
            item.year
            for item in self._combinations
            if item.state == state
            and item.area == area
            and item.property_type == property_type
        }
        if not values:
            raise ValueError("Unsupported state/area/property-type combination")
        return tuple(sorted(values))

    def quarters(
        self, state: str, area: str, property_type: str, year: int
    ) -> tuple[int, ...]:
        values = {
            item.quarter
            for item in self._combinations
            if item.state == state
            and item.area == area
            and item.property_type == property_type
            and item.year == year
        }
        if not values:
            raise ValueError("Unsupported historical period")
        return tuple(sorted(values))

    @property
    def earliest_period(self) -> tuple[int, int]:
        return min((item.year, item.quarter) for item in self._combinations)

    @property
    def latest_period(self) -> tuple[int, int]:
        return max((item.year, item.quarter) for item in self._combinations)

"""Tests for the official NAPIC individual-transaction source adapter."""

from __future__ import annotations

from io import BytesIO
import unittest

import pandas as pd

from house_price_estimator.data_sources import (
    MALAYSIAN_GOVERNMENT_OPEN_DATA_ATTRIBUTION,
    MALAYSIAN_GOVERNMENT_OPEN_DATA_TERMS_URL,
    NAPIC_OPEN_TRANSACTION_HEADERS,
    NAPIC_OPEN_TRANSACTION_PAGE_URL,
    NAPIC_OPEN_TRANSACTION_PRICE_TYPE,
    NAPIC_OPEN_TRANSACTION_SOURCE_NAME,
    NapicOpenTransactionAdapter,
)


HEADER = ",".join(
    f'"{value}"' if "," in value else value
    for value in NAPIC_OPEN_TRANSACTION_HEADERS
)


class _FakeResponse(BytesIO):
    def __init__(self, content: bytes, content_length: int | None = None) -> None:
        super().__init__(content)
        self.headers = (
            {} if content_length is None else {"Content-Length": str(content_length)}
        )

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


class NapicOpenTransactionAdapterTests(unittest.TestCase):
    def test_parse_preserves_raw_values_and_requires_requested_state(self):
        csv_bytes = (
            HEADER
            + "\nJohor Bahru,120,-,Bandar Johor Bahru,January 2025,"
            "2 - 2 1/2 Storey Terraced,Jalan Test,Taman Test,Freehold,"
            "500000,sq.m,-,2\n"
        ).encode("utf-8")

        frame = NapicOpenTransactionAdapter("Johor").parse(csv_bytes)

        self.assertEqual(len(frame), 1)
        row = frame.iloc[0]
        self.assertEqual(row["state"], "Johor")
        self.assertEqual(row["district_raw"], "Johor Bahru")
        self.assertEqual(row["main_floor_area_raw"], "-")
        self.assertTrue(pd.isna(row["main_floor_area_sqm"]))
        self.assertEqual(row["land_parcel_area_sqm"], 120.0)
        self.assertEqual(row["land_parcel_area_unit_raw"], "sq.m")
        self.assertEqual(row["main_floor_area_unit_raw"], "-")
        self.assertEqual(row["transaction_price_rm"], 500000.0)
        self.assertEqual(row["transaction_date"], pd.Timestamp("2025-01-01"))
        self.assertEqual(row["price_type"], NAPIC_OPEN_TRANSACTION_PRICE_TYPE)
        self.assertNotIn("state_raw", frame.columns)

    def test_unknown_state_is_rejected_instead_of_inferred(self):
        with self.assertRaisesRegex(ValueError, "unknown Malaysian state"):
            NapicOpenTransactionAdapter("Johor Bahru")

    def test_duplicate_unit_headers_are_validated_by_exact_position(self):
        bad_headers = list(NAPIC_OPEN_TRANSACTION_HEADERS)
        bad_headers[10], bad_headers[11] = bad_headers[11], bad_headers[10]
        bad_csv = (",".join(bad_headers) + "\n").encode("utf-8")
        with self.assertRaisesRegex(ValueError, "header mismatch"):
            NapicOpenTransactionAdapter("Johor").parse(bad_csv)

    def test_malformed_values_are_preserved_and_flagged(self):
        csv_bytes = (
            HEADER
            + "\nKota Kinabalu,bad-area,800,Bandar Kota Kinabalu,not-a-date,"
            "Condominium/Apartment,,,Leasehold,bad-price,sq.m,sq.m,-\n"
        ).encode("utf-8")
        row = NapicOpenTransactionAdapter("Sabah").parse(csv_bytes).iloc[0]
        self.assertEqual(row["land_parcel_area_raw"], "bad-area")
        self.assertEqual(row["transaction_price_rm_raw"], "bad-price")
        self.assertTrue(pd.isna(row["land_parcel_area_sqm"]))
        self.assertTrue(pd.isna(row["transaction_price_rm"]))
        self.assertEqual(row["validation_status"], "needs_review")
        self.assertIn("INVALID_LAND_PARCEL_AREA", row["validation_notes"])
        self.assertIn("INVALID_TRANSACTION_DATE", row["validation_notes"])
        self.assertIn("INVALID_TRANSACTION_PRICE", row["validation_notes"])

    def test_source_and_licence_metadata_are_explicit(self):
        adapter = NapicOpenTransactionAdapter("Penang")
        metadata = adapter.source_metadata
        self.assertEqual(metadata["source_name"], NAPIC_OPEN_TRANSACTION_SOURCE_NAME)
        self.assertEqual(metadata["source_page_url"], NAPIC_OPEN_TRANSACTION_PAGE_URL)
        self.assertEqual(metadata["licence_terms_url"], MALAYSIAN_GOVERNMENT_OPEN_DATA_TERMS_URL)
        self.assertEqual(metadata["required_attribution"], MALAYSIAN_GOVERNMENT_OPEN_DATA_ATTRIBUTION)
        self.assertEqual(metadata["price_type"], "completed_transaction")
        self.assertIn("State=Pulau%20Pinang", adapter.download_url)
        self.assertIn(
            "State=WP%20Putrajaya",
            NapicOpenTransactionAdapter("Putrajaya").download_url,
        )
        self.assertIn("State=WP%20Labuan", NapicOpenTransactionAdapter("Labuan").download_url)
        self.assertNotIn("State=", NapicOpenTransactionAdapter("Kuala Lumpur").download_url)

    def test_download_is_state_filtered_and_bounded(self):
        requested_urls: list[str] = []
        content = (HEADER + "\n").encode("utf-8")

        def opener(request: object, *, timeout: float) -> _FakeResponse:
            requested_urls.append(request.full_url)  # type: ignore[attr-defined]
            self.assertEqual(timeout, 3.0)
            return _FakeResponse(content, len(content))

        adapter = NapicOpenTransactionAdapter("Negeri Sembilan")
        self.assertEqual(
            adapter.download(timeout_seconds=3.0, max_bytes=len(content), opener=opener),
            content,
        )
        self.assertIn("State=Negeri%20Sembilan", requested_urls[0])

        def oversized_opener(_request: object, *, timeout: float) -> _FakeResponse:
            self.assertEqual(timeout, 60.0)
            return _FakeResponse(b"12345", content_length=5)

        with self.assertRaisesRegex(ValueError, "exceeds maximum"):
            adapter.download(max_bytes=4, opener=oversized_opener)

        def empty_opener(_request: object, *, timeout: float) -> _FakeResponse:
            return _FakeResponse(b"\n")

        with self.assertRaisesRegex(ValueError, "empty CSV export"):
            adapter.download(opener=empty_opener)


if __name__ == "__main__":
    unittest.main()

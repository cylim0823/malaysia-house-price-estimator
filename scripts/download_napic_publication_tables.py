"""Download official NAPIC state transaction publications with provenance.

The workbooks are publicly downloadable but carry a copyright-reserved notice.
They are therefore stored locally under a Git-ignored directory; only the
manifest produced by this script is suitable for repository review.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE_URL = (
    "https://napic.jpph.gov.my/storage/app/media//3-penerbitan/Shahrul/"
    "Bahagian%20Pasaran%20Harta%20Tanah/Jadual%20Data%20Transaksi%20Harta%20Tanah/"
    "Q1%202026"
)
STATE_FILES = {
    "Kuala Lumpur": "1. Jadual Transaksi Harta Tanah WP. Kuala Lumpur Q1 2026.xlsx",
    "Putrajaya": "2. Jadual Transaksi Harta Tanah WP. Putrajaya Q1 2026.xlsx",
    "Labuan": "3. Jadual Transaksi Harta Tanah WP. Labuan Q1 2026.xlsx",
    "Selangor": "4. Jadual Transaksi Harta Tanah Selangor Q1 2026.xlsx",
    "Johor": "5. Jadual Transaksi Harta Tanah Johor Q1 2026.xlsx",
    "Perak": "6. Jadual Transaksi Harta Tanah Perak Q1 2026.xlsx",
    "Penang": "7. Jadual Transaksi Harta Tanah Penang Q1 2026.xlsx",
    "Negeri Sembilan": "8. Jadual Transaksi Harta Tanah Negeri Sembilan Q1 2026.xlsx",
    "Melaka": "9. Jadual Transaksi Harta Tanah Melaka Q1 2026.xlsx",
    "Kedah": "10. Jadual Transaksi Harta Tanah Kedah Q1 2026.xlsx",
    "Pahang": "11. Jadual Transaksi Harta Tanah Pahang Q1 2026.xlsx",
    "Terengganu": "12. Jadual Transaksi Harta Tanah Terengganu Q1 2026.xlsx",
    "Kelantan": "13. Jadual Transaksi Harta Tanah Kelantan Q1 2026.xlsx",
    "Perlis": "14. Jadual Transaksi Harta Tanah Perlis Q1 2026.xlsx",
    "Sabah": "15. Jadual Transaksi Harta Tanah Sabah Q1 2026.xlsx",
    "Sarawak": "16. Jadual Transaksi Harta Tanah Sarawak Q1 2026.xlsx",
}


def download(output_dir: Path, *, timeout: float = 60.0) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    records: list[dict[str, object]] = []
    for state, filename in STATE_FILES.items():
        url = f"{BASE_URL}/{quote(filename)}"
        request = Request(url, headers={"User-Agent": "malaysia-house-price-estimator/0.1"})
        with urlopen(request, timeout=timeout) as response:
            content = response.read(25_000_001)
        if len(content) > 25_000_000:
            raise ValueError(f"Publication exceeds 25 MB limit: {state}")
        if not content.startswith(b"PK"):
            raise ValueError(f"NAPIC did not return an XLSX workbook for {state}")
        path = output_dir / filename
        path.write_bytes(content)
        records.append(
            {
                "state": state,
                "year": 2026,
                "period": "Q1",
                "document_title": filename.removesuffix(".xlsx").split(". ", 1)[-1],
                "source_url": url,
                "path": path.as_posix(),
                "retrieved_at": retrieved_at,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "licence_status": "copyright_reserved_reuse_permission_not_found",
                "redistribution_allowed": False,
            }
        )
    return {
        "publisher": "National Property Information Centre (NAPIC), JPPH Malaysia",
        "archive_url": "https://napic.jpph.gov.my/ms/archives/jadual-data-transaksi-harta-tanah",
        "publication_cadence": "Direct tables are published for Q1 and Q3",
        "reuse_decision": "Local inspection only; raw workbooks are excluded from Git",
        "files": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("data/external/napic/2026"))
    parser.add_argument(
        "--manifest", type=Path, default=Path("data/external/napic/publication_manifest.json")
    )
    args = parser.parse_args()
    manifest = download(args.output_dir)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"downloaded": len(manifest["files"]), "manifest": str(args.manifest)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

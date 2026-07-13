"""Download immutable, per-state NAPIC open-transaction CSV snapshots."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from house_price_estimator.data_sources import NapicOpenTransactionAdapter
from house_price_estimator.location_catalog import MALAYSIAN_STATES


def collect(
    output_directory: Path,
    states: tuple[str, ...],
    *,
    attempts: int,
) -> dict[str, object]:
    """Download, validate, and describe raw snapshots without overwriting them."""
    output_directory.mkdir(parents=True, exist_ok=True)
    collected_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    snapshots: list[dict[str, object]] = []
    for state in states:
        adapter = NapicOpenTransactionAdapter(state)
        safe_name = state.lower().replace(" ", "_")
        path = output_directory / f"{safe_name}.csv"
        content: bytes | None = path.read_bytes() if path.exists() else None
        if content is None:
            last_error: Exception | None = None
            for attempt in range(1, attempts + 1):
                try:
                    content = adapter.download(timeout_seconds=120, max_bytes=100_000_000)
                    break
                except Exception as exc:  # network/source failures are recorded after retries
                    last_error = exc
                    if attempt < attempts:
                        time.sleep(min(2 ** attempt, 15))
            if content is None:
                raise RuntimeError(f"Could not download {state}: {last_error}")
        frame = adapter.parse(content)
        if frame.empty:
            raise ValueError(f"NAPIC export for {state} contains no records")
        if not path.exists():
            path.write_bytes(content)
        snapshots.append(
            {
                **adapter.source_metadata,
                "path": path.as_posix(),
                "retrieved_at": collected_at,
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
                "rows": len(frame),
                "districts": sorted(frame["district"].dropna().unique().tolist()),
                "earliest_transaction_month": frame["transaction_date"].min().date().isoformat(),
                "latest_transaction_month": frame["transaction_date"].max().date().isoformat(),
                "validation_warning_rows": int(frame["validation_status"].eq("needs_review").sum()),
            }
        )
        time.sleep(1)
    report = {"collected_at": collected_at, "snapshots": snapshots}
    metadata_path = output_directory / "metadata.json"
    if metadata_path.exists():
        raise FileExistsError(f"Refusing to overwrite raw metadata: {metadata_path}")
    metadata_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--state", action="append", dest="states")
    parser.add_argument("--attempts", type=int, default=4)
    args = parser.parse_args()
    if args.attempts < 1:
        parser.error("--attempts must be positive")
    states = tuple(args.states) if args.states else MALAYSIAN_STATES
    report = collect(args.output_dir, states, attempts=args.attempts)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

"""Detect PII leaks and latency SLO violations in JSONL request logs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.pii import PII_PATTERNS


def load_records(path: Path) -> list[dict]:
    records: list[dict] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def contains_pii(record: dict) -> bool:
    text = json.dumps(record, ensure_ascii=False)
    return any(re.search(pattern, text) for pattern in PII_PATTERNS.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-path", type=Path, default=Path("data/logs.jsonl"))
    parser.add_argument("--slo-path", type=Path, default=Path("config/slo.yaml"))
    parser.add_argument("--fail-on-anomaly", action="store_true")
    args = parser.parse_args()
    slo = yaml.safe_load(args.slo_path.read_text(encoding="utf-8"))
    threshold = float(slo["slis"]["latency_p95_ms"]["objective"])
    records = load_records(args.log_path)
    responses = [record for record in records if record.get("event") == "response_sent"]
    pii = [record for record in records if contains_pii(record)]
    slow = [record for record in responses if float(record.get("latency_ms") or 0) > threshold]
    print(f"records_analyzed={len(records)}")
    print(f"pii_leaks={len(pii)}")
    print(f"latency_slo_ms={threshold:g}")
    print(f"latency_violations={len(slow)}")
    for record in slow[:5]:
        print(f"LATENCY_VIOLATION correlation_id={record.get('correlation_id')} latency_ms={record.get('latency_ms')}")
    if args.fail_on_anomaly and (pii or slow):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

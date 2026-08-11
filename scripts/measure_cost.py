"""Summarize the newest response events for cost-optimization before/after evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def response_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("event") == "response_sent":
            events.append(record)
    return events


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--last", type=int, default=10, help="Number of newest response events to include")
    parser.add_argument("--label", default="measurement")
    parser.add_argument("--log-path", type=Path, default=Path("data/logs.jsonl"))
    args = parser.parse_args()
    if args.last < 1:
        parser.error("--last must be at least 1")
    events = response_events(args.log_path)[-args.last :]
    total = sum(float(event.get("cost_usd") or 0) for event in events)
    output_tokens = sum(int(event.get("tokens_out") or 0) for event in events)
    print(f"label={args.label}")
    print(f"response_count={len(events)}")
    print(f"total_cost_usd={total:.6f}")
    print(f"tokens_out_total={output_tokens}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import html
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

from .metrics import percentile


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "dashboard.yaml"


def _load_records(log_path: Path, now: datetime) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []

    cutoff = now - timedelta(minutes=60)
    records: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        if timestamp.astimezone(timezone.utc) >= cutoff:
            records.append(record)
    return records


def _thresholds(config_path: Path) -> dict[str, str]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    panels = config["dashboard"]["panels"]
    return {
        panel["id"]: f"{panel['threshold']['aggregation']} {panel['threshold']['operator']} {panel['threshold']['value']}"
        for panel in panels
    }


def _number(record: dict[str, Any], field: str) -> float | None:
    value = record.get(field)
    return float(value) if isinstance(value, (int, float)) else None


def _sparkline(values: list[float], color: str) -> str:
    if not values:
        return '<svg class="spark" viewBox="0 0 240 56" role="img" aria-label="No data"><text x="12" y="32">No data in selected window</text></svg>'
    low, high = min(values), max(values)
    spread = high - low or 1
    points = " ".join(
        f"{index * 240 / max(1, len(values) - 1):.1f},{50 - ((value - low) / spread) * 42:.1f}"
        for index, value in enumerate(values)
    )
    return (
        '<svg class="spark" viewBox="0 0 240 56" role="img" aria-label="Trend over time">'
        f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3" />'
        "</svg>"
    )


def _panel(title: str, value: str, unit: str, threshold: str, body: str) -> str:
    return f"""
    <section class="panel">
      <h2>{html.escape(title)}</h2>
      <div class="value">{html.escape(value)} <span>{html.escape(unit)}</span></div>
      <p class="threshold">Threshold: {html.escape(threshold)}</p>
      {body}
    </section>"""


def build_dashboard_html(
    log_path: Path = DEFAULT_LOG_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
    now: datetime | None = None,
) -> str:
    now = now or datetime.now(timezone.utc)
    records = _load_records(log_path, now)
    thresholds = _thresholds(config_path)
    responses = [record for record in records if record.get("event") == "response_sent"]
    received = [record for record in records if record.get("event") == "request_received"]
    failed = [record for record in records if record.get("event") == "request_failed"]

    latencies = [value for record in responses if (value := _number(record, "latency_ms")) is not None]
    costs = [value for record in responses if (value := _number(record, "cost_usd")) is not None]
    tokens_in = [value for record in responses if (value := _number(record, "tokens_in")) is not None]
    tokens_out = [value for record in responses if (value := _number(record, "tokens_out")) is not None]
    quality = [value for record in responses if (value := _number(record, "quality_score")) is not None]
    error_rate = (len(failed) / len(received) * 100) if received else 0.0

    buckets: dict[str, dict[str, float]] = defaultdict(lambda: {"traffic": 0, "cost": 0, "quality_total": 0, "quality_count": 0})
    for record in received:
        buckets[str(record.get("ts", ""))[:16]]["traffic"] += 1
    for record in responses:
        bucket = buckets[str(record.get("ts", ""))[:16]]
        bucket["cost"] += _number(record, "cost_usd") or 0
        score = _number(record, "quality_score")
        if score is not None:
            bucket["quality_total"] += score
            bucket["quality_count"] += 1
    ordered = [buckets[key] for key in sorted(buckets)]
    error_types = Counter(str(record.get("error_type", "UnknownError")) for record in failed)
    error_list = "".join(
        f"<li>{html.escape(error_type)}: {count}</li>" for error_type, count in error_types.items()
    ) or "<li>No failed requests</li>"

    panels = [
        _panel(
            "Latency percentiles",
            f"P50 {percentile(latencies, 50):.0f} · P95 {percentile(latencies, 95):.0f} · P99 {percentile(latencies, 99):.0f}",
            "ms",
            thresholds["latency"],
            _sparkline(latencies, "#2563eb"),
        ),
        _panel(
            "Request traffic",
            str(len(received)),
            "requests in 60m",
            thresholds["traffic"],
            _sparkline([bucket["traffic"] for bucket in ordered], "#059669"),
        ),
        _panel(
            "Error rate and breakdown",
            f"{error_rate:.2f}",
            "%",
            thresholds["errors"],
            f"<ul>{error_list}</ul>",
        ),
        _panel(
            "Cost over time",
            f"{sum(costs):.4f}",
            "USD",
            thresholds["cost"],
            _sparkline([bucket["cost"] for bucket in ordered], "#7c3aed"),
        ),
        _panel(
            "Input and output tokens",
            f"in {int(sum(tokens_in)):,} · out {int(sum(tokens_out)):,}",
            "tokens",
            thresholds["tokens"],
            "<p>Each field is summed independently.</p>",
        ),
        _panel(
            "Quality proxy",
            f"{mean(quality):.2f}" if quality else "0.00",
            "score 0–1",
            thresholds["quality"],
            _sparkline(
                [bucket["quality_total"] / bucket["quality_count"] for bucket in ordered if bucket["quality_count"]],
                "#d97706",
            ),
        ),
    ]
    generated_at = now.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="30">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Day 13 AI Observability Dashboard</title>
  <style>
    body {{ margin: 0; padding: 28px; font-family: system-ui, sans-serif; color: #172033; background: #f6f8fc; }}
    header {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; margin-bottom: 20px; }}
    h1 {{ margin: 0; font-size: 26px; }} h2 {{ font-size: 16px; margin: 0 0 12px; }}
    .meta, .threshold, .panel p, li {{ color: #52627c; font-size: 13px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 16px; }}
    .panel {{ min-height: 182px; padding: 18px; border: 1px solid #dce3f0; border-radius: 12px; background: white; }}
    .value {{ font-size: 24px; font-weight: 700; color: #15213a; }} .value span {{ font-size: 13px; font-weight: 500; }}
    .threshold {{ margin: 8px 0; }} .spark {{ width: 100%; height: 58px; }} .spark text {{ fill: #52627c; font-size: 11px; }}
    ul {{ margin: 10px 0 0; padding-left: 20px; }}
  </style>
</head>
<body>
  <header><h1>Day 13 AI Observability</h1><div class="meta">Last 60 minutes · refresh 30s · generated {generated_at}</div></header>
  <main class="grid">{''.join(panels)}</main>
</body>
</html>"""

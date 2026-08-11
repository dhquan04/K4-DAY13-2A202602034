from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.dashboard import build_dashboard_html
from app.main import app


def test_dashboard_renders_all_six_contract_panels_from_jsonl(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    records = [
        {"ts": now.isoformat(), "event": "request_received"},
        {"ts": now.isoformat(), "event": "request_received"},
        {"ts": now.isoformat(), "event": "request_failed", "error_type": "RuntimeError"},
        {
            "ts": now.isoformat(), "event": "response_sent", "latency_ms": 180,
            "cost_usd": 0.012, "tokens_in": 12, "tokens_out": 34, "quality_score": 0.8,
        },
    ]
    log_path = tmp_path / "logs.jsonl"
    log_path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

    page = build_dashboard_html(log_path=log_path, now=now)

    for panel in (
        "Latency percentiles", "Request traffic", "Error rate and breakdown",
        "Cost over time", "Input and output tokens", "Quality proxy",
    ):
        assert panel in page
    assert "50.00" in page
    assert "RuntimeError: 1" in page
    assert "Last 60 minutes" in page


def test_dashboard_endpoint_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/dashboard")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.text.count('<section class="panel">') == 6

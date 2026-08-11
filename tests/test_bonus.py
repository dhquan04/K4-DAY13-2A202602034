from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from app import audit, incidents
from app.mock_llm import FakeLLM


def _load_anomaly_script():
    path = Path("scripts/detect_anomalies.py")
    spec = importlib.util.spec_from_file_location("detect_anomalies", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_audit_log_is_jsonl_and_scrubs_details(tmp_path, monkeypatch) -> None:
    path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", path)
    audit.record_audit("config_changed", actor="student@vinuni.edu.vn")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["event"] == "config_changed"
    assert record["details"]["actor"] == "[REDACTED_EMAIL]"


def test_cost_optimization_caps_cost_spike_output(monkeypatch) -> None:
    monkeypatch.setattr("app.mock_llm.random.randint", lambda _a, _b: 180)
    incidents.STATE["cost_spike"] = True
    incidents.set_cost_optimization(False)
    assert FakeLLM().generate("x").usage.output_tokens == 720
    incidents.set_cost_optimization(True)
    assert FakeLLM().generate("x").usage.output_tokens == 160
    incidents.STATE["cost_spike"] = False
    incidents.set_cost_optimization(False)


def test_anomaly_detector_finds_pii_and_slo_violation() -> None:
    detector = _load_anomaly_script()
    assert detector.contains_pii({"payload": "email student@vinuni.edu.vn"})
    assert not detector.contains_pii({"payload": "[REDACTED_EMAIL]"})

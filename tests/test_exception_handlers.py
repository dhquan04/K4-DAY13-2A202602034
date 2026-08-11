from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config, metrics
from app.exception_handlers import safe_error_type
from app.main import app


def test_safe_error_type_strips_message_with_pii() -> None:
    assert safe_error_type(ValueError("email leak@vinuni.edu.vn")) == "ValueError"
    assert safe_error_type("ValueError: contact 0987654321") == "ValueError"
    assert safe_error_type("!!!") == "UnknownError"


def test_record_error_rejects_free_form_pii() -> None:
    metrics.ERRORS.clear()
    metrics.record_error("ValueError: student@vinuni.edu.vn called 0987654321")
    assert metrics.ERRORS == {"ValueError": 1}
    assert "student@" not in json.dumps(metrics.snapshot())


def test_unhandled_chat_error_returns_safe_json_and_logs(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    logging_config.configure_logging()
    metrics.ERRORS.clear()

    def boom(**_: object) -> object:
        raise RuntimeError("secret email boom@vinuni.edu.vn phone 0987654321")

    monkeypatch.setattr("app.main.agent.run", boom)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "u-err",
                "session_id": "s-err",
                "feature": "qa",
                "message": "trigger failure with card 4111 1111 1111 1111",
            },
        )

    assert response.status_code == 500
    body = response.json()
    assert body["ok"] is False
    assert body["status_code"] == 500
    assert body["error_type"] == "RuntimeError"
    assert body["detail"] == "Internal server error"
    assert body["correlation_id"]
    assert "boom@" not in response.text
    assert "0987654321" not in response.text
    assert "4111" not in response.text

    assert metrics.ERRORS.get("RuntimeError", 0) >= 1

    content = log_path.read_text(encoding="utf-8")
    assert "request_failed" in content
    assert "RuntimeError" in content
    assert "boom@vinuni.edu.vn" not in content
    assert "0987654321" not in content
    assert "4111 1111 1111 1111" not in content
    assert "REDACTED_EMAIL" in content or "Internal server error" in content


def test_validation_error_does_not_echo_pii() -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "u01",
                "session_id": "s01",
                "feature": "qa",
                # missing required message; also plant PII in an unexpected field
                "extra_email": "echo-me@vinuni.edu.vn",
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["error_type"] == "RequestValidationError"
    assert body["detail"] == "Request validation failed"
    assert "echo-me@vinuni.edu.vn" not in response.text

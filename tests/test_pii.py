from pathlib import Path

from app import logging_config
from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd() -> None:
    out = scrub_text("CCCD number: 001201012345")
    assert "001201012345" not in out
    assert "REDACTED_CCCD" in out


def test_scrub_credit_card() -> None:
    out = scrub_text("Card: 4111 1111 1111 1111")
    assert "4111 1111 1111 1111" not in out
    assert "REDACTED_CREDIT_CARD" in out


def test_scrub_passport_vn() -> None:
    out = scrub_text("Passport number B1234567 issued in Hanoi")
    assert "B1234567" not in out
    assert "REDACTED_PASSPORT_VN" in out


def test_scrub_address_vn() -> None:
    out = scrub_text("Tôi sống tại 123 Đường Nguyễn Trãi, Phường 5, Quận 1")
    assert "REDACTED_ADDRESS_VN" in out


def test_scrub_event_removes_pii_through_real_log_pipeline(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    logging_config.configure_logging()
    log = logging_config.get_logger()

    log.info(
        "test_event",
        service="api",
        payload={
            "message_preview": (
                "Email student@vinuni.edu.vn phone 0987654321 "
                "CCCD 001201012345 card 4111 1111 1111 1111 passport B1234567"
            )
        },
    )

    content = log_path.read_text(encoding="utf-8")
    assert "student@vinuni.edu.vn" not in content
    assert "0987654321" not in content
    assert "001201012345" not in content
    assert "4111 1111 1111 1111" not in content
    assert "B1234567" not in content
    for redacted in (
        "REDACTED_EMAIL",
        "REDACTED_PHONE_VN",
        "REDACTED_CCCD",
        "REDACTED_CREDIT_CARD",
        "REDACTED_PASSPORT_VN",
    ):
        assert redacted in content

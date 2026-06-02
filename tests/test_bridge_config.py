from __future__ import annotations

from bridge.config import load_bridge_settings


def test_load_bridge_settings_reads_reservation_ui_mode(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USERNAME", "sender@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "app-password")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "sender@gmail.com")
    monkeypatch.setenv("APP_BASE_URL", "https://example.streamlit.app")
    monkeypatch.setenv("RESERVATION_UI_MODE", "legacy")

    settings = load_bridge_settings()

    assert settings is not None
    assert settings.reservation_ui_mode == "legacy"

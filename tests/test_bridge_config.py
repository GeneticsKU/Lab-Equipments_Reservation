from __future__ import annotations

import sys
import types

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


def test_load_bridge_settings_reads_nested_streamlit_secret(monkeypatch) -> None:
    for env_name in (
        "DATABASE_URL",
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM_EMAIL",
        "APP_BASE_URL",
    ):
        monkeypatch.delenv(env_name, raising=False)

    fake_streamlit = types.SimpleNamespace(
        secrets={
            "credentials": {
                "usernames": {
                    "Yanawat4511": {
                        "DATABASE_URL": "postgresql://nested-example",
                        "SMTP_USERNAME": "sender@gmail.com",
                        "SMTP_PASSWORD": "app-password",
                        "SMTP_FROM_EMAIL": "sender@gmail.com",
                        "APP_BASE_URL": "https://example.streamlit.app",
                    }
                }
            }
        }
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    settings = load_bridge_settings()

    assert settings is not None
    assert settings.database_url == "postgresql://nested-example"
    assert settings.smtp_host == "smtp.gmail.com"
    assert settings.smtp_port == 465

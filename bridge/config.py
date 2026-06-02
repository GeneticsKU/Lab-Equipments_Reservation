from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class BridgeSettings:
    database_url: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_use_ssl: bool
    app_base_url: str
    deployment_label: str | None = None
    deployment_notice: str | None = None
    session_cookie_name: str = "genetics_lab_bridge_session"
    session_ttl_hours: int = 168
    login_code_ttl_minutes: int = 10
    login_code_cooldown_minutes: int = 2
    login_code_daily_limit_per_email: int = 5
    login_code_daily_limit_global: int = 80


def _read_streamlit_secret(name: str):
    try:
        import streamlit as st
    except Exception:
        return None

    try:
        if name in st.secrets:
            return st.secrets[name]
        bridge_section = st.secrets.get("bridge", {})
        return bridge_section.get(name)
    except Exception:
        return None


def _get_setting(name: str, default=None):
    value = os.getenv(name)
    if value not in (None, ""):
        return value
    secret_value = _read_streamlit_secret(name)
    if secret_value not in (None, ""):
        return secret_value
    return default


def _get_bool_setting(name: str, default: bool) -> bool:
    raw_value = _get_setting(name)
    if raw_value in (None, ""):
        return default
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}


def load_bridge_settings() -> BridgeSettings | None:
    database_url = _get_setting("DATABASE_URL")
    smtp_host = _get_setting("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(_get_setting("SMTP_PORT", 465))
    smtp_username = _get_setting("SMTP_USERNAME")
    smtp_password = _get_setting("SMTP_PASSWORD")
    smtp_from_email = _get_setting("SMTP_FROM_EMAIL", smtp_username)
    smtp_use_ssl = _get_bool_setting("SMTP_USE_SSL", True)
    app_base_url = _get_setting("APP_BASE_URL")

    if not all([database_url, smtp_host, smtp_port, smtp_username, smtp_password, smtp_from_email, app_base_url]):
        return None

    return BridgeSettings(
        database_url=database_url,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        smtp_from_email=smtp_from_email,
        smtp_use_ssl=smtp_use_ssl,
        app_base_url=app_base_url.rstrip("/"),
        deployment_label=_get_setting("DEPLOYMENT_LABEL"),
        deployment_notice=_get_setting("DEPLOYMENT_NOTICE"),
        session_cookie_name=_get_setting("SESSION_COOKIE_NAME", "genetics_lab_bridge_session"),
        session_ttl_hours=int(_get_setting("SESSION_TTL_HOURS", 168)),
        login_code_ttl_minutes=int(_get_setting("LOGIN_CODE_TTL_MINUTES", 10)),
        login_code_cooldown_minutes=int(_get_setting("LOGIN_CODE_COOLDOWN_MINUTES", 2)),
        login_code_daily_limit_per_email=int(_get_setting("LOGIN_CODE_DAILY_LIMIT_PER_EMAIL", 5)),
        login_code_daily_limit_global=int(_get_setting("LOGIN_CODE_DAILY_LIMIT_GLOBAL", 80)),
    )

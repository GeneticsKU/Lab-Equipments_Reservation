from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class BridgeSettings:
    database_url: str
    resend_api_key: str
    resend_from_email: str
    app_base_url: str
    session_cookie_name: str = "genetics_lab_bridge_session"
    session_ttl_hours: int = 12
    login_code_ttl_minutes: int = 10


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


def load_bridge_settings() -> BridgeSettings | None:
    database_url = _get_setting("DATABASE_URL")
    resend_api_key = _get_setting("RESEND_API_KEY")
    resend_from_email = _get_setting("RESEND_FROM_EMAIL")
    app_base_url = _get_setting("APP_BASE_URL")

    if not all([database_url, resend_api_key, resend_from_email, app_base_url]):
        return None

    return BridgeSettings(
        database_url=database_url,
        resend_api_key=resend_api_key,
        resend_from_email=resend_from_email,
        app_base_url=app_base_url.rstrip("/"),
        session_cookie_name=_get_setting("SESSION_COOKIE_NAME", "genetics_lab_bridge_session"),
        session_ttl_hours=int(_get_setting("SESSION_TTL_HOURS", 12)),
        login_code_ttl_minutes=int(_get_setting("LOGIN_CODE_TTL_MINUTES", 10)),
    )


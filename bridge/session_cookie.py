from __future__ import annotations

from datetime import datetime


def _cookie_manager():
    import extra_streamlit_components as stx

    return stx.CookieManager()


def get_session_cookie(cookie_name: str) -> str | None:
    manager = _cookie_manager()
    return manager.get(cookie_name)


def set_session_cookie(cookie_name: str, token: str, expires_at: datetime) -> None:
    manager = _cookie_manager()
    manager.set(cookie_name, token, expires_at=expires_at)


def clear_session_cookie(cookie_name: str) -> None:
    manager = _cookie_manager()
    manager.delete(cookie_name)


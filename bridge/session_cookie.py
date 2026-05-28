from __future__ import annotations

from datetime import datetime
import math


def _cookie_manager():
    import extra_streamlit_components as stx
    import streamlit as st

    manager = st.session_state.get("_bridge_cookie_manager")
    if manager is None:
        manager = stx.CookieManager(key="bridge_cookie_manager_init")
        st.session_state["_bridge_cookie_manager"] = manager
    return manager


def get_session_cookie(cookie_name: str) -> str | None:
    manager = _cookie_manager()
    # Refresh browser cookies on each rerun so we do not keep the empty
    # constructor snapshot from the first post-refresh render.
    cookies = manager.get_all(key=f"bridge_cookie_get_all_{cookie_name}")
    return cookies.get(cookie_name)


def set_session_cookie(cookie_name: str, token: str, expires_at: datetime) -> None:
    manager = _cookie_manager()
    max_age_seconds = max(1, math.ceil((expires_at - datetime.now(expires_at.tzinfo)).total_seconds()))
    manager.set(
        cookie_name,
        token,
        key=f"bridge_cookie_set_{cookie_name}",
        expires_at=expires_at,
        max_age=max_age_seconds,
        secure=True,
        same_site="lax",
    )


def clear_session_cookie(cookie_name: str) -> None:
    manager = _cookie_manager()
    manager.delete(cookie_name, key=f"bridge_cookie_delete_{cookie_name}")

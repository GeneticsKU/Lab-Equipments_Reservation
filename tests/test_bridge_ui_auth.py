from __future__ import annotations

from types import SimpleNamespace

import pytest

from bridge.auth_store import BridgeUser
from bridge import ui_auth


def test_finish_successful_login_updates_session_state_before_cookie_write(monkeypatch) -> None:
    settings = SimpleNamespace(session_ttl_hours=168, session_cookie_name="bridge_cookie")
    session_state = {
        "bridge_pending_email": "user@ku.th",
        "bridge_login_code": "123456",
    }
    user = BridgeUser(id="user-1", email="user@ku.th", full_name="Bridge User")

    def fake_set_session_cookie(cookie_name: str, raw_token: str, expires_at) -> None:
        assert session_state["bridge_pending_email"] == ""
        assert session_state["bridge_login_code"] is None if "bridge_login_code" in session_state else True
        assert session_state["authentication_status"] is True
        assert session_state["bridge_user"].email == "user@ku.th"
        assert session_state["bridge_raw_session_token"] == "session-token-123"
        raise RuntimeError("simulated-cookie-rerun")

    monkeypatch.setattr(ui_auth, "set_session_cookie", fake_set_session_cookie)

    with pytest.raises(RuntimeError, match="simulated-cookie-rerun"):
        ui_auth.finish_successful_login(settings, session_state, user, "session-token-123")


def test_finish_successful_login_returns_user_after_cookie_write(monkeypatch) -> None:
    settings = SimpleNamespace(session_ttl_hours=168, session_cookie_name="bridge_cookie")
    session_state = {
        "bridge_pending_email": "user@ku.th",
        "bridge_login_code": "123456",
    }
    user = BridgeUser(id="user-1", email="user@ku.th", full_name="Bridge User")
    cookie_calls = []

    def fake_set_session_cookie(cookie_name: str, raw_token: str, expires_at) -> None:
        cookie_calls.append((cookie_name, raw_token))

    monkeypatch.setattr(ui_auth, "set_session_cookie", fake_set_session_cookie)

    returned_user = ui_auth.finish_successful_login(settings, session_state, user, "session-token-123")

    assert returned_user == user
    assert cookie_calls == [("bridge_cookie", "session-token-123")]
    assert session_state["bridge_pending_email"] == ""
    assert "bridge_login_code" not in session_state
    assert session_state["bridge_raw_session_token"] == "session-token-123"

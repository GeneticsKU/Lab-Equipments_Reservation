from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bridge import session_cookie


class FakeCookieManager:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.cookies: dict[str, str] = {}

    def set(self, cookie_name, token, **kwargs) -> None:
        self.calls.append(
            {
                "cookie_name": cookie_name,
                "token": token,
                **kwargs,
            }
        )

    def get_all(self, key="get_all"):
        self.calls.append({"method": "get_all", "key": key})
        return dict(self.cookies)


def test_set_session_cookie_uses_secure_lax_cookie_with_max_age(monkeypatch) -> None:
    manager = FakeCookieManager()
    monkeypatch.setattr(session_cookie, "_cookie_manager", lambda: manager)

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_cookie.set_session_cookie("bridge_cookie", "token-123", expires_at)

    assert len(manager.calls) == 1
    call = manager.calls[0]
    assert call["cookie_name"] == "bridge_cookie"
    assert call["token"] == "token-123"
    assert call["secure"] is True
    assert call["same_site"] == "lax"
    assert call["max_age"] > 0


def test_get_session_cookie_refreshes_cookie_snapshot_each_rerun(monkeypatch) -> None:
    manager = FakeCookieManager()
    manager.cookies["bridge_cookie"] = "token-123"
    monkeypatch.setattr(session_cookie, "_cookie_manager", lambda: manager)

    token = session_cookie.get_session_cookie("bridge_cookie")

    assert token == "token-123"
    assert manager.calls == [
        {"method": "get_all", "key": "bridge_cookie_get_all_bridge_cookie"}
    ]

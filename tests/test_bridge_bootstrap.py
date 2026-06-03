from __future__ import annotations

from pathlib import Path

from bridge import bootstrap


def test_cached_schema_init_runs_once_per_database_and_schema(tmp_path, monkeypatch) -> None:
    schema_path = tmp_path / "schema.sql"
    schema_path.write_text("CREATE TABLE test_table(id INT);", encoding="utf-8")

    calls: list[tuple[str, str]] = []

    def fake_apply(database_url: str, sql_text: str) -> None:
        calls.append((database_url, sql_text))

    bootstrap._ensure_bridge_schema_once_cached.cache_clear()
    monkeypatch.setattr(bootstrap, "_apply_bridge_schema", fake_apply)

    bootstrap._ensure_bridge_schema_once_cached("postgres://db-one", str(schema_path))
    bootstrap._ensure_bridge_schema_once_cached("postgres://db-one", str(schema_path))

    assert calls == [("postgres://db-one", "CREATE TABLE test_table(id INT);")]


def test_cached_schema_init_repeats_for_different_database(tmp_path, monkeypatch) -> None:
    schema_path = tmp_path / "schema.sql"
    schema_path.write_text("CREATE TABLE test_table(id INT);", encoding="utf-8")

    calls: list[tuple[str, str]] = []

    def fake_apply(database_url: str, sql_text: str) -> None:
        calls.append((database_url, sql_text))

    bootstrap._ensure_bridge_schema_once_cached.cache_clear()
    monkeypatch.setattr(bootstrap, "_apply_bridge_schema", fake_apply)

    bootstrap._ensure_bridge_schema_once_cached("postgres://db-one", str(schema_path))
    bootstrap._ensure_bridge_schema_once_cached("postgres://db-two", str(schema_path))

    assert calls == [
        ("postgres://db-one", "CREATE TABLE test_table(id INT);"),
        ("postgres://db-two", "CREATE TABLE test_table(id INT);"),
    ]


def test_should_retry_cookie_restore_only_once_without_cookie() -> None:
    session_state = {}

    assert bootstrap.should_retry_cookie_restore(session_state, raw_session_token=None) is True
    assert session_state["bridge_cookie_restore_reruns"] == 1

    assert bootstrap.should_retry_cookie_restore(session_state, raw_session_token=None) is False


def test_should_retry_cookie_restore_skips_active_login_flow_and_resets_on_cookie() -> None:
    session_state = {"bridge_pending_email": "user@ku.th"}

    assert bootstrap.should_retry_cookie_restore(session_state, raw_session_token=None) is False

    session_state = {"bridge_cookie_restore_reruns": 1}
    assert bootstrap.should_retry_cookie_restore(session_state, raw_session_token="token-123") is False
    assert session_state["bridge_cookie_restore_reruns"] == 0


def test_write_authenticated_user_tracks_raw_session_token() -> None:
    session_state = {}
    user = bootstrap.BridgeUser(
        id="user-1",
        email="user@ku.th",
        full_name="Bridge User",
        affiliation="4511",
    )

    bootstrap.write_authenticated_user(session_state, user, raw_session_token="session-token-123")

    assert session_state["authentication_status"] is True
    assert session_state["name"] == "Bridge_4511"
    assert session_state["bridge_raw_session_token"] == "session-token-123"


def test_clear_bridge_session_state_removes_raw_session_token() -> None:
    session_state = {
        "authentication_status": True,
        "username": "user@ku.th",
        "name": "Bridge User",
        "bridge_user": object(),
        "bridge_role": "User",
        "bridge_raw_session_token": "session-token-123",
        "bridge_cookie_restore_reruns": 1,
    }

    bootstrap.clear_bridge_session_state(session_state)

    assert session_state["authentication_status"] is False
    assert session_state["bridge_raw_session_token"] is None


def test_derive_display_name_uses_first_name_and_affiliation() -> None:
    user = bootstrap.BridgeUser(
        id="user-1",
        email="kongtawan.wo@ku.th",
        full_name="Kongtawan Worraraparp",
        affiliation="4511",
    )

    assert bootstrap.derive_display_name(user) == "Kongtawan_4511"


def test_derive_display_name_falls_back_cleanly() -> None:
    no_affiliation = bootstrap.BridgeUser(
        id="user-2",
        email="teerasak.e@ku.th",
        full_name="Teerasak E-kobon",
        affiliation=None,
    )
    no_name = bootstrap.BridgeUser(
        id="user-3",
        email="bridge.user@ku.th",
        full_name=None,
        affiliation="4511",
    )

    assert bootstrap.derive_display_name(no_affiliation) == "Teerasak"
    assert bootstrap.derive_display_name(no_name) == "bridge.user_4511"

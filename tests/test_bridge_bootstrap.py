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

from __future__ import annotations

import argparse
from datetime import timedelta
from functools import lru_cache
import json
from pathlib import Path

from bridge.auth_store import AuthStore, BridgeUser
from bridge.config import BridgeSettings, load_bridge_settings
from bridge.db import PostgresBridgeRepository, connect_database, schema_sql_path
from scripts.migrate_legacy_users import migrate_legacy_users


def load_app_settings() -> BridgeSettings | None:
    return load_bridge_settings()


def build_auth_store(settings: BridgeSettings) -> AuthStore:
    return AuthStore(
        repository=PostgresBridgeRepository(settings),
        code_ttl=timedelta(minutes=settings.login_code_ttl_minutes),
        session_ttl=timedelta(hours=settings.session_ttl_hours),
    )


def ensure_bridge_schema(settings: BridgeSettings) -> None:
    sql_text = schema_sql_path().read_text(encoding="utf-8")
    _apply_bridge_schema(settings.database_url, sql_text)


def ensure_bridge_schema_once(settings: BridgeSettings) -> None:
    _ensure_bridge_schema_once_cached(settings.database_url, str(schema_sql_path()))


@lru_cache(maxsize=8)
def _ensure_bridge_schema_once_cached(database_url: str, schema_path: str) -> None:
    sql_text = Path(schema_path).read_text(encoding="utf-8")
    _apply_bridge_schema(database_url, sql_text)


def _apply_bridge_schema(database_url: str, sql_text: str) -> None:
    with connect_database(database_url) as conn, conn.cursor() as cur:
        statements = [statement.strip() for statement in sql_text.split(";") if statement.strip()]
        for statement in statements:
            cur.execute(statement)
        conn.commit()


def derive_legacy_role(user: BridgeUser) -> str:
    if user.is_admin:
        return "Admins"
    if user.is_sponsor:
        return "Lecturer"
    return "User"


def clear_bridge_session_state(session_state) -> None:
    session_state["authentication_status"] = False
    session_state["username"] = None
    session_state["name"] = None
    session_state["bridge_user"] = None
    session_state["bridge_role"] = None


def write_authenticated_user(session_state, user: BridgeUser) -> None:
    session_state["authentication_status"] = True
    session_state["username"] = user.email
    session_state["name"] = user.full_name or user.email
    session_state["bridge_user"] = user
    session_state["bridge_role"] = derive_legacy_role(user)


def hydrate_bridge_session_state(session_state, auth_store: AuthStore, raw_session_token: str | None) -> BridgeUser | None:
    user = auth_store.load_session_user(raw_session_token)
    if user is None:
        clear_bridge_session_state(session_state)
        return None
    write_authenticated_user(session_state, user)
    return user


def seed_sponsors(settings: BridgeSettings, sponsor_records: list[dict], *, source: str = "manual-sponsor-seed") -> dict[str, int]:
    repository = PostgresBridgeRepository(settings)
    summary = {"migrated": 0, "created": 0, "updated": 0}

    for record in sponsor_records:
        email = record["email"].strip().lower()
        existing_user = repository.get_user_by_email(email)
        seeded_user = BridgeUser(
            id=existing_user.id if existing_user else record.get("id", f"sponsor-{email}"),
            email=email,
            full_name=record.get("full_name") or record.get("name"),
            user_category="Lecturer",
            affiliation=record.get("affiliation"),
            is_email_verified=existing_user.is_email_verified if existing_user else False,
            approval_state=existing_user.approval_state if existing_user else "approved",
            is_sponsor=True,
            is_admin=existing_user.is_admin if existing_user else False,
            is_operator=existing_user.is_operator if existing_user else False,
            legacy_username=existing_user.legacy_username if existing_user else None,
            legacy_source=source,
        )
        repository.upsert_user(seeded_user)
        summary["migrated"] += 1
        if existing_user is None:
            summary["created"] += 1
        else:
            summary["updated"] += 1

    return summary


def load_json_file(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Bridge bootstrap commands for the Streamlit migration phase.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-schema", help="Create or update bridge auth tables in Postgres.")

    seed_parser = subparsers.add_parser("seed-sponsors", help="Seed or update sponsor records from a JSON file.")
    seed_parser.add_argument("--input", required=True, help="Path to sponsor JSON file.")
    seed_parser.add_argument("--source", default="manual-sponsor-seed")

    legacy_parser = subparsers.add_parser("migrate-legacy-users", help="Migrate exported legacy users into the bridge database.")
    legacy_parser.add_argument("--input", required=True, help="Path to exported legacy users JSON.")
    legacy_parser.add_argument("--source", default="legacy-secrets-export")

    args = parser.parse_args()
    settings = load_app_settings()
    if settings is None:
        raise SystemExit("Missing bridge configuration. Set DATABASE_URL, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL, and APP_BASE_URL.")

    if args.command == "init-schema":
        ensure_bridge_schema(settings)
        print("Bridge schema initialized.")
        return 0

    if args.command == "seed-sponsors":
        sponsor_records = load_json_file(args.input)
        summary = seed_sponsors(settings, sponsor_records, source=args.source)
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "migrate-legacy-users":
        repository = PostgresBridgeRepository(settings)
        legacy_payload = load_json_file(args.input)
        summary = migrate_legacy_users(repository, legacy_payload, source=args.source)
        print(json.dumps(summary, indent=2))
        return 0

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

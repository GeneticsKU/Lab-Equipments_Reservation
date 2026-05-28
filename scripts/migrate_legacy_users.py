from __future__ import annotations

import argparse
import json
from pathlib import Path
import uuid

from bridge.auth_store import BridgeUser, normalize_email
from bridge.config import load_bridge_settings
from bridge.db import PostgresBridgeRepository


def extract_legacy_user_map(raw_payload: dict) -> dict[str, dict]:
    if "credentials" in raw_payload and "usernames" in raw_payload["credentials"]:
        return raw_payload["credentials"]["usernames"]
    if "usernames" in raw_payload:
        return raw_payload["usernames"]
    raise ValueError("Legacy payload must contain usernames or credentials.usernames.")


def map_legacy_role(role: str) -> dict[str, bool]:
    if role == "Admins":
        return {"is_admin": True, "is_sponsor": True}
    if role == "Lecturer":
        return {"is_admin": False, "is_sponsor": True}
    if role == "User":
        return {"is_admin": False, "is_sponsor": False}
    raise ValueError(f"Unknown legacy role: {role}")


def build_migrated_user(existing_user: BridgeUser | None, legacy_username: str, legacy_record: dict, *, source: str) -> BridgeUser:
    email = normalize_email(legacy_record["email"])
    role_flags = map_legacy_role(legacy_record["role"])
    user_id = existing_user.id if existing_user else f"user-{uuid.uuid4()}"

    return BridgeUser(
        id=user_id,
        email=email,
        full_name=legacy_record["name"],
        user_category=existing_user.user_category if existing_user else None,
        affiliation=existing_user.affiliation if existing_user else None,
        is_email_verified=False,
        approval_state="approved",
        is_sponsor=role_flags["is_sponsor"],
        is_admin=role_flags["is_admin"],
        is_operator=existing_user.is_operator if existing_user else False,
        legacy_username=legacy_username,
        legacy_source=source,
    )


def migrate_legacy_users(repository, raw_payload: dict, *, source: str = "legacy-secrets-export") -> dict[str, int]:
    usernames = extract_legacy_user_map(raw_payload)
    summary = {"migrated": 0, "created": 0, "updated": 0}

    for legacy_username, legacy_record in usernames.items():
        email = normalize_email(legacy_record["email"])
        existing_user = repository.get_user_by_email(email)
        migrated_user = build_migrated_user(existing_user, legacy_username, legacy_record, source=source)
        repository.upsert_user(migrated_user)
        summary["migrated"] += 1
        if existing_user is None:
            summary["created"] += 1
        else:
            summary["updated"] += 1

    return summary


def load_legacy_payload(input_path: str | Path) -> dict:
    return json.loads(Path(input_path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy Streamlit users into the bridge auth database.")
    parser.add_argument("--input", required=True, help="Path to exported legacy user JSON.")
    parser.add_argument("--source", default="legacy-secrets-export", help="Legacy source label stored on migrated users.")
    args = parser.parse_args()

    settings = load_bridge_settings()
    if settings is None:
        raise SystemExit("Missing bridge configuration. Set DATABASE_URL, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL, and APP_BASE_URL.")

    repository = PostgresBridgeRepository(settings)
    payload = load_legacy_payload(args.input)
    summary = migrate_legacy_users(repository, payload, source=args.source)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

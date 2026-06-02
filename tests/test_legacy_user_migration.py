from __future__ import annotations

from dataclasses import replace

import pytest

from bridge.auth_store import BridgeUser
from scripts.migrate_legacy_users import migrate_legacy_users


class FakeMigrationRepository:
    def __init__(self) -> None:
        self.users: dict[str, BridgeUser] = {}

    def get_user_by_email(self, email: str) -> BridgeUser | None:
        return self.users.get(email)

    def upsert_user(self, user: BridgeUser) -> BridgeUser:
        self.users[user.email] = user
        return user


def test_migrate_admin_and_lecturer_roles_preserves_exact_name() -> None:
    repository = FakeMigrationRepository()
    legacy_payload = {
        "credentials": {
            "usernames": {
                "adminuser": {
                    "name": "Dr. Yanawat Exact Name",
                    "email": "ADMIN@KU.TH",
                    "role": "Admins",
                },
                "lectureruser": {
                    "name": "Assoc. Prof. Lecturer",
                    "email": "lecturer@ku.th",
                    "role": "Lecturer",
                },
            }
        }
    }

    summary = migrate_legacy_users(repository, legacy_payload, source="legacy-secrets")

    admin_user = repository.get_user_by_email("admin@ku.th")
    lecturer_user = repository.get_user_by_email("lecturer@ku.th")
    assert summary["migrated"] == 2
    assert admin_user is not None
    assert admin_user.full_name == "Dr. Yanawat Exact Name"
    assert admin_user.is_admin is True
    assert admin_user.is_sponsor is True
    assert admin_user.approval_state == "approved"
    assert admin_user.is_email_verified is False
    assert admin_user.legacy_username == "adminuser"
    assert lecturer_user is not None
    assert lecturer_user.is_sponsor is True
    assert lecturer_user.is_admin is False


def test_migrate_unknown_role_fails_closed() -> None:
    repository = FakeMigrationRepository()
    legacy_payload = {
        "credentials": {
            "usernames": {
                "mystery": {
                    "name": "Mystery User",
                    "email": "mystery@ku.th",
                    "role": "MysteryRole",
                }
            }
        }
    }

    with pytest.raises(ValueError, match="Unknown legacy role"):
        migrate_legacy_users(repository, legacy_payload)


def test_migrate_is_idempotent_by_lowercase_email() -> None:
    repository = FakeMigrationRepository()
    legacy_payload = {
        "credentials": {
            "usernames": {
                "legacyuser": {
                    "name": "Legacy User",
                    "email": "LegacyUser@ku.th",
                    "role": "User",
                }
            }
        }
    }

    first_summary = migrate_legacy_users(repository, legacy_payload, source="first-run")
    second_summary = migrate_legacy_users(repository, legacy_payload, source="second-run")

    migrated_user = repository.get_user_by_email("legacyuser@ku.th")
    assert first_summary["migrated"] == 1
    assert second_summary["migrated"] == 1
    assert second_summary["created"] == 0
    assert second_summary["updated"] == 1
    assert migrated_user is not None
    assert migrated_user.email == "legacyuser@ku.th"
    assert len(repository.users) == 1


def test_existing_user_record_keeps_same_id_while_gaining_legacy_mapping() -> None:
    repository = FakeMigrationRepository()
    existing = BridgeUser(
        id="existing-user-id",
        email="existing@ku.th",
        full_name="Existing Name",
        approval_state="pending",
        is_email_verified=True,
    )
    repository.upsert_user(existing)

    legacy_payload = {
        "credentials": {
            "usernames": {
                "existinguser": {
                    "name": "Existing Name",
                    "email": "existing@ku.th",
                    "role": "Lecturer",
                }
            }
        }
    }

    migrate_legacy_users(repository, legacy_payload, source="legacy-sync")

    migrated_user = repository.get_user_by_email("existing@ku.th")
    assert migrated_user is not None
    assert migrated_user.id == "existing-user-id"
    assert migrated_user.is_sponsor is True
    assert migrated_user.approval_state == "approved"
    assert migrated_user.is_email_verified is False
    assert migrated_user.legacy_source == "legacy-sync"


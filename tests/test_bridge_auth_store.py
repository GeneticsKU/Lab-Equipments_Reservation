from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone

import pytest

from bridge.auth_store import AuthStore, InvalidLoginCodeError, LoginCodeRateLimitError


@dataclass
class FakeUserRecord:
    id: str
    email: str
    full_name: str | None = None
    user_category: str | None = None
    affiliation: str | None = None
    is_email_verified: bool = False
    approval_state: str = "pending"
    is_sponsor: bool = False
    is_admin: bool = False
    is_operator: bool = False


class FakeBridgeRepository:
    def __init__(self) -> None:
        self.users: dict[str, FakeUserRecord] = {}
        self.login_codes: list[dict] = []
        self.sessions: list[dict] = []

    def get_user_by_email(self, email: str) -> FakeUserRecord | None:
        return self.users.get(email)

    def upsert_user(self, user: FakeUserRecord) -> FakeUserRecord:
        self.users[user.email] = user
        return user

    def store_login_code(self, login_code: dict) -> None:
        self.login_codes.append(login_code)

    def get_latest_login_code(self, email: str, purpose: str) -> dict | None:
        for login_code in reversed(self.login_codes):
            if login_code["email"] == email and login_code["purpose"] == purpose:
                return login_code
        return None

    def count_login_codes(self, *, email: str | None, purpose: str, created_after) -> int:
        return sum(
            1
            for login_code in self.login_codes
            if (email is None or login_code["email"] == email)
            and login_code["purpose"] == purpose
            and login_code["created_at"] >= created_after
        )

    def update_login_code(self, login_code: dict) -> None:
        for idx, current in enumerate(self.login_codes):
            if current["id"] == login_code["id"]:
                self.login_codes[idx] = login_code
                return
        raise AssertionError("login code not found")

    def mark_user_email_verified(self, email: str) -> FakeUserRecord:
        current = self.users[email]
        updated = replace(current, is_email_verified=True)
        self.users[email] = updated
        return updated

    def store_session(self, session_record: dict) -> None:
        self.sessions.append(session_record)

    def get_session_by_token_hash(self, token_hash: str) -> dict | None:
        for session_record in self.sessions:
            if session_record["token_hash"] == token_hash:
                return session_record
        return None

    def update_session(self, session_record: dict) -> None:
        for idx, current in enumerate(self.sessions):
            if current["id"] == session_record["id"]:
                self.sessions[idx] = session_record
                return
        raise AssertionError("session not found")

    def get_user_by_id(self, user_id: str) -> FakeUserRecord | None:
        for user in self.users.values():
            if user.id == user_id:
                return user
        return None


def build_store(repository: FakeBridgeRepository) -> AuthStore:
    fixed_now = datetime(2026, 5, 28, 10, 0, tzinfo=timezone.utc)
    return AuthStore(
        repository=repository,
        now=lambda: fixed_now,
        code_generator=lambda: "123456",
        token_generator=lambda: "session-token-123",
        code_ttl=timedelta(minutes=10),
        session_ttl=timedelta(hours=12),
    )


def build_limited_store(repository: FakeBridgeRepository, *, now) -> AuthStore:
    return AuthStore(
        repository=repository,
        now=now,
        code_generator=lambda: "123456",
        token_generator=lambda: "session-token-123",
        code_ttl=timedelta(minutes=10),
        session_ttl=timedelta(hours=12),
        code_cooldown=timedelta(minutes=2),
        code_daily_limit_per_email=2,
        code_daily_limit_global=3,
    )


def test_issue_login_code_rejects_non_ku_domain() -> None:
    repository = FakeBridgeRepository()
    store = build_store(repository)

    with pytest.raises(ValueError, match="@ku.th"):
        store.issue_login_code("user@example.com")


def test_issue_and_verify_login_code_marks_user_verified() -> None:
    repository = FakeBridgeRepository()
    repository.upsert_user(
        FakeUserRecord(
            id="user-1",
            email="student@ku.th",
            full_name="Student User",
            approval_state="approved",
            is_email_verified=False,
        )
    )
    store = build_store(repository)

    plain_code = store.issue_login_code("student@ku.th")
    verified_user = store.verify_login_code("student@ku.th", plain_code)

    assert plain_code == "123456"
    assert verified_user.email == "student@ku.th"
    assert verified_user.is_email_verified is True
    assert repository.get_latest_login_code("student@ku.th", "login")["consumed_at"] is not None


def test_issue_login_code_enforces_per_email_cooldown() -> None:
    repository = FakeBridgeRepository()
    repository.upsert_user(FakeUserRecord(id="user-1", email="student@ku.th"))
    current_time = datetime(2026, 5, 28, 10, 0, tzinfo=timezone.utc)
    store = build_limited_store(repository, now=lambda: current_time)

    store.issue_login_code("student@ku.th")

    with pytest.raises(LoginCodeRateLimitError, match="wait 2 minutes"):
        store.issue_login_code("student@ku.th")


def test_issue_login_code_enforces_per_email_daily_limit() -> None:
    repository = FakeBridgeRepository()
    repository.upsert_user(FakeUserRecord(id="user-1", email="student@ku.th"))
    current_time = datetime(2026, 5, 28, 10, 0, tzinfo=timezone.utc)
    store = build_limited_store(repository, now=lambda: current_time)

    store.issue_login_code("student@ku.th")
    current_time = datetime(2026, 5, 28, 10, 3, tzinfo=timezone.utc)
    store.issue_login_code("student@ku.th")
    current_time = datetime(2026, 5, 28, 10, 6, tzinfo=timezone.utc)

    with pytest.raises(LoginCodeRateLimitError, match="Daily login code limit reached for this email"):
        store.issue_login_code("student@ku.th")


def test_issue_login_code_enforces_global_daily_limit() -> None:
    repository = FakeBridgeRepository()
    for idx in range(4):
        repository.upsert_user(FakeUserRecord(id=f"user-{idx}", email=f"student{idx}@ku.th"))
    current_time = datetime(2026, 5, 28, 10, 0, tzinfo=timezone.utc)
    store = build_limited_store(repository, now=lambda: current_time)

    for idx in range(3):
        store.issue_login_code(f"student{idx}@ku.th")
        current_time = current_time + timedelta(minutes=3)

    with pytest.raises(LoginCodeRateLimitError, match="Daily login code limit reached for this app"):
        store.issue_login_code("student3@ku.th")


def test_verify_login_code_rejects_replay_after_consumption() -> None:
    repository = FakeBridgeRepository()
    repository.upsert_user(FakeUserRecord(id="user-1", email="student@ku.th"))
    store = build_store(repository)

    plain_code = store.issue_login_code("student@ku.th")
    store.verify_login_code("student@ku.th", plain_code)

    with pytest.raises(InvalidLoginCodeError):
        store.verify_login_code("student@ku.th", plain_code)


def test_create_session_and_load_session_user() -> None:
    repository = FakeBridgeRepository()
    repository.upsert_user(
        FakeUserRecord(
            id="user-1",
            email="lecturer@ku.th",
            full_name="Lecturer User",
            approval_state="approved",
            is_email_verified=True,
            is_sponsor=True,
        )
    )
    store = build_store(repository)

    raw_token = store.create_session("user-1")
    session_user = store.load_session_user(raw_token)

    assert raw_token == "session-token-123"
    assert session_user is not None
    assert session_user.email == "lecturer@ku.th"
    assert session_user.is_sponsor is True

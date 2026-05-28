from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from bridge.auth_store import AuthStore, BridgeUser


class UnauthorizedAccessRequestError(ValueError):
    pass


class FakeAccessRequestRepository:
    def __init__(self) -> None:
        self.users: dict[str, BridgeUser] = {}
        self.requests: list[dict] = []

    def get_user_by_email(self, email: str) -> BridgeUser | None:
        return next((user for user in self.users.values() if user.email == email), None)

    def upsert_user(self, user: BridgeUser) -> BridgeUser:
        self.users[user.id] = user
        return user

    def get_user_by_id(self, user_id: str) -> BridgeUser | None:
        return self.users.get(user_id)

    def update_user(self, user: BridgeUser) -> BridgeUser:
        self.users[user.id] = user
        return user

    def create_access_request(self, request_record: dict) -> dict:
        self.requests.append(request_record)
        return request_record

    def list_access_requests_for_sponsor(self, sponsor_user_id: str) -> list[dict]:
        return [request for request in self.requests if request["chosen_sponsor_user_id"] == sponsor_user_id]

    def get_access_request_by_id(self, request_id: str) -> dict | None:
        return next((request for request in self.requests if request["id"] == request_id), None)

    def update_access_request(self, updated_request: dict) -> dict:
        for idx, request in enumerate(self.requests):
            if request["id"] == updated_request["id"]:
                self.requests[idx] = updated_request
                return updated_request
        raise AssertionError("request not found")


def build_store(repository: FakeAccessRequestRepository) -> AuthStore:
    fixed_now = datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc)
    return AuthStore(
        repository=repository,
        now=lambda: fixed_now,
        code_generator=lambda: "123456",
        token_generator=lambda: "session-token-123",
        code_ttl=timedelta(minutes=10),
        session_ttl=timedelta(hours=12),
    )


def seed_user(repository: FakeAccessRequestRepository, **overrides) -> BridgeUser:
    user = BridgeUser(
        id=overrides.pop("id"),
        email=overrides.pop("email"),
        full_name=overrides.pop("full_name", None),
        user_category=overrides.pop("user_category", None),
        affiliation=overrides.pop("affiliation", None),
        is_email_verified=overrides.pop("is_email_verified", True),
        approval_state=overrides.pop("approval_state", "pending"),
        is_sponsor=overrides.pop("is_sponsor", False),
        is_admin=overrides.pop("is_admin", False),
        is_operator=overrides.pop("is_operator", False),
    )
    repository.upsert_user(user)
    return user


def test_create_access_request_updates_applicant_details() -> None:
    repository = FakeAccessRequestRepository()
    sponsor = seed_user(repository, id="sponsor-1", email="lecturer@ku.th", is_sponsor=True, approval_state="approved")
    applicant = seed_user(repository, id="user-1", email="student@ku.th", approval_state="pending", is_email_verified=True)
    store = build_store(repository)

    request_record = store.create_access_request(
        applicant_user_id=applicant.id,
        full_name="Student User",
        email="student@ku.th",
        chosen_sponsor_user_id=sponsor.id,
        suggested_user_category="Master Student",
        affiliation="Genetics Room 101",
    )

    assert request_record["chosen_sponsor_user_id"] == sponsor.id
    assert request_record["status"] == "Pending"
    updated_user = repository.get_user_by_id(applicant.id)
    assert updated_user.full_name == "Student User"
    assert updated_user.affiliation == "Genetics Room 101"


def test_list_sponsor_requests_only_returns_their_requests() -> None:
    repository = FakeAccessRequestRepository()
    sponsor_one = seed_user(repository, id="sponsor-1", email="lecturer1@ku.th", is_sponsor=True, approval_state="approved")
    sponsor_two = seed_user(repository, id="sponsor-2", email="lecturer2@ku.th", is_sponsor=True, approval_state="approved")
    applicant_one = seed_user(repository, id="user-1", email="student1@ku.th")
    applicant_two = seed_user(repository, id="user-2", email="student2@ku.th")
    store = build_store(repository)

    store.create_access_request(applicant_user_id=applicant_one.id, full_name="One", email=applicant_one.email, chosen_sponsor_user_id=sponsor_one.id, suggested_user_category="Researcher", affiliation="Lab A")
    store.create_access_request(applicant_user_id=applicant_two.id, full_name="Two", email=applicant_two.email, chosen_sponsor_user_id=sponsor_two.id, suggested_user_category="Researcher", affiliation="Lab B")

    visible_requests = store.list_sponsor_requests(sponsor_one.id)

    assert len(visible_requests) == 1
    assert visible_requests[0]["chosen_sponsor_user_id"] == sponsor_one.id


def test_approve_access_request_rejects_wrong_sponsor() -> None:
    repository = FakeAccessRequestRepository()
    sponsor_one = seed_user(repository, id="sponsor-1", email="lecturer1@ku.th", is_sponsor=True, approval_state="approved")
    sponsor_two = seed_user(repository, id="sponsor-2", email="lecturer2@ku.th", is_sponsor=True, approval_state="approved")
    applicant = seed_user(repository, id="user-1", email="student@ku.th")
    store = build_store(repository)

    request_record = store.create_access_request(
        applicant_user_id=applicant.id,
        full_name="Student User",
        email=applicant.email,
        chosen_sponsor_user_id=sponsor_one.id,
        suggested_user_category="Master Student",
        affiliation="Genetics Room 101",
    )

    with pytest.raises(PermissionError):
        store.approve_access_request(request_record["id"], sponsor_two.id, approved_user_category="Researcher")


def test_approve_and_deny_access_request_update_state() -> None:
    repository = FakeAccessRequestRepository()
    sponsor = seed_user(repository, id="sponsor-1", email="lecturer@ku.th", is_sponsor=True, approval_state="approved")
    applicant = seed_user(repository, id="user-1", email="student@ku.th")
    applicant_two = seed_user(repository, id="user-2", email="student2@ku.th")
    store = build_store(repository)

    approve_request = store.create_access_request(
        applicant_user_id=applicant.id,
        full_name="Student User",
        email=applicant.email,
        chosen_sponsor_user_id=sponsor.id,
        suggested_user_category="Master Student",
        affiliation="Genetics Room 101",
    )
    deny_request = store.create_access_request(
        applicant_user_id=applicant_two.id,
        full_name="Student Two",
        email=applicant_two.email,
        chosen_sponsor_user_id=sponsor.id,
        suggested_user_category="Undergraduate Student",
        affiliation="Genetics Room 102",
    )

    approved = store.approve_access_request(approve_request["id"], sponsor.id, approved_user_category="Researcher")
    denied = store.deny_access_request(deny_request["id"], sponsor.id)

    assert approved["status"] == "Approved"
    assert approved["approved_user_category"] == "Researcher"
    assert repository.get_user_by_id(applicant.id).approval_state == "approved"
    assert repository.get_user_by_id(applicant.id).user_category == "Researcher"
    assert denied["status"] == "Denied"
    assert repository.get_user_by_id(applicant_two.id).approval_state == "denied"


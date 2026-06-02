from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import uuid


DEFAULT_LOGIN_CODE_TTL = timedelta(minutes=10)
DEFAULT_SESSION_TTL = timedelta(days=7)
DEFAULT_LOGIN_CODE_COOLDOWN = timedelta(minutes=2)
DEFAULT_LOGIN_CODE_DAILY_LIMIT_PER_EMAIL = 5
DEFAULT_LOGIN_CODE_DAILY_LIMIT_GLOBAL = 80


class InvalidLoginCodeError(ValueError):
    """Raised when a one-time code is missing, expired, replayed, or invalid."""


class LoginCodeRateLimitError(ValueError):
    """Raised when one-time code sending is throttled to protect email quota."""


class InvalidAccessRequestError(ValueError):
    """Raised when an access request cannot be created or mutated safely."""


@dataclass(frozen=True)
class BridgeUser:
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
    legacy_username: str | None = None
    legacy_source: str | None = None


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_allowed_email(email: str) -> bool:
    return normalize_email(email).endswith("@ku.th")


def is_allowed_login_email(email: str, allowed_extra_emails: set[str] | None = None) -> bool:
    normalized_email = normalize_email(email)
    return is_allowed_email(normalized_email) or normalized_email in (allowed_extra_emails or set())


def hash_secret(raw_value: str) -> str:
    return hashlib.sha256(raw_value.encode("utf-8")).hexdigest()


class AuthStore:
    def __init__(
        self,
        repository,
        *,
        now=None,
        code_generator=None,
        token_generator=None,
        code_ttl: timedelta = DEFAULT_LOGIN_CODE_TTL,
        session_ttl: timedelta = DEFAULT_SESSION_TTL,
        code_cooldown: timedelta = DEFAULT_LOGIN_CODE_COOLDOWN,
        code_daily_limit_per_email: int = DEFAULT_LOGIN_CODE_DAILY_LIMIT_PER_EMAIL,
        code_daily_limit_global: int = DEFAULT_LOGIN_CODE_DAILY_LIMIT_GLOBAL,
        code_rate_limit_bypass_emails: set[str] | None = None,
        allowed_extra_login_emails: set[str] | None = None,
    ) -> None:
        self.repository = repository
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.code_generator = code_generator or (lambda: f"{secrets.randbelow(1_000_000):06d}")
        self.token_generator = token_generator or (lambda: secrets.token_urlsafe(32))
        self.code_ttl = code_ttl
        self.session_ttl = session_ttl
        self.code_cooldown = code_cooldown
        self.code_daily_limit_per_email = code_daily_limit_per_email
        self.code_daily_limit_global = code_daily_limit_global
        self.code_rate_limit_bypass_emails = {
            normalize_email(email)
            for email in (code_rate_limit_bypass_emails or set())
            if email
        }
        self.allowed_extra_login_emails = {
            normalize_email(email)
            for email in (allowed_extra_login_emails or set())
            if email
        }

    def issue_login_code(self, email: str, purpose: str = "login") -> str:
        normalized_email = normalize_email(email)
        if not is_allowed_login_email(normalized_email, self.allowed_extra_login_emails):
            raise ValueError("Only @ku.th email addresses or configured testing emails can request a login code.")

        timestamp = self.now()
        user = self.repository.get_user_by_email(normalized_email)
        if not self._bypasses_login_code_rate_limit(normalized_email, user):
            self._enforce_login_code_rate_limits(normalized_email, purpose, timestamp)

        if user is None:
            user = self.repository.upsert_user(
                BridgeUser(
                    id=f"user-{uuid.uuid4()}",
                    email=normalized_email,
                    full_name=None,
                    approval_state="pending",
                )
            )

        plain_code = self.code_generator()
        self.repository.store_login_code(
            {
                "id": f"login-code-{uuid.uuid4()}",
                "email": normalized_email,
                "user_id": user.id,
                "purpose": purpose,
                "code_hash": hash_secret(plain_code),
                "attempt_count": 0,
                "created_at": timestamp,
                "expires_at": timestamp + self.code_ttl,
                "consumed_at": None,
            }
        )
        return plain_code

    def _bypasses_login_code_rate_limit(self, email: str, user: BridgeUser | None) -> bool:
        return email in self.code_rate_limit_bypass_emails or bool(user and user.is_admin)

    def _enforce_login_code_rate_limits(self, email: str, purpose: str, timestamp: datetime) -> None:
        window_start = timestamp - self.code_cooldown
        if self.repository.count_login_codes(email=email, purpose=purpose, created_after=window_start) > 0:
            cooldown_minutes = max(1, int(self.code_cooldown.total_seconds() // 60))
            raise LoginCodeRateLimitError(
                f"Please wait {cooldown_minutes} minutes before requesting another login code."
            )

        day_start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_email_count = self.repository.count_login_codes(email=email, purpose=purpose, created_after=day_start)
        if daily_email_count >= self.code_daily_limit_per_email:
            raise LoginCodeRateLimitError("Daily login code limit reached for this email. Please try again tomorrow.")

        global_daily_count = self.repository.count_login_codes(email=None, purpose=purpose, created_after=day_start)
        if global_daily_count >= self.code_daily_limit_global:
            raise LoginCodeRateLimitError("Daily login code limit reached for this app. Please contact the administrator.")

    def verify_login_code(self, email: str, code: str, purpose: str = "login") -> BridgeUser:
        normalized_email = normalize_email(email)
        login_code = self.repository.get_latest_login_code(normalized_email, purpose)
        current_time = self.now()
        if login_code is None:
            raise InvalidLoginCodeError("Login code not found.")

        if login_code.get("consumed_at") is not None:
            raise InvalidLoginCodeError("Login code has already been used.")
        if login_code["expires_at"] < current_time:
            raise InvalidLoginCodeError("Login code has expired.")
        if login_code["code_hash"] != hash_secret(code):
            login_code["attempt_count"] = login_code.get("attempt_count", 0) + 1
            self.repository.update_login_code(login_code)
            raise InvalidLoginCodeError("Login code is invalid.")

        login_code["consumed_at"] = current_time
        self.repository.update_login_code(login_code)
        return self.repository.mark_user_email_verified(normalized_email)

    def create_session(self, user_id: str) -> str:
        raw_token = self.token_generator()
        timestamp = self.now()
        self.repository.store_session(
            {
                "id": f"session-{uuid.uuid4()}",
                "user_id": user_id,
                "token_hash": hash_secret(raw_token),
                "created_at": timestamp,
                "expires_at": timestamp + self.session_ttl,
                "revoked_at": None,
                "last_seen_at": timestamp,
            }
        )
        return raw_token

    def load_session_user(self, raw_token: str | None) -> BridgeUser | None:
        if not raw_token:
            return None
        session_record = self.repository.get_session_by_token_hash(hash_secret(raw_token))
        if session_record is None:
            return None
        current_time = self.now()
        if session_record.get("revoked_at") is not None:
            return None
        if session_record["expires_at"] < current_time:
            return None

        session_record["last_seen_at"] = current_time
        self.repository.update_session(session_record)
        return self.repository.get_user_by_id(session_record["user_id"])

    def revoke_session(self, raw_token: str | None) -> None:
        if not raw_token:
            return
        session_record = self.repository.get_session_by_token_hash(hash_secret(raw_token))
        if session_record is None:
            return
        session_record["revoked_at"] = self.now()
        self.repository.update_session(session_record)

    def create_access_request(
        self,
        *,
        applicant_user_id: str,
        full_name: str,
        email: str,
        chosen_sponsor_user_id: str,
        suggested_user_category: str,
        affiliation: str,
    ) -> dict:
        normalized_email = normalize_email(email)
        applicant = self.repository.get_user_by_id(applicant_user_id)
        sponsor = self.repository.get_user_by_id(chosen_sponsor_user_id)
        if applicant is None:
            raise InvalidAccessRequestError("Applicant user does not exist.")
        if sponsor is None or (not sponsor.is_sponsor and not sponsor.is_admin):
            raise InvalidAccessRequestError("Selected sponsor is not valid.")
        if applicant.email != normalized_email:
            raise InvalidAccessRequestError("Applicant email does not match the signed-in user.")

        updated_applicant = replace(
            applicant,
            full_name=full_name,
            affiliation=affiliation,
        )
        self.repository.update_user(updated_applicant)

        request_record = {
            "id": f"access-request-{uuid.uuid4()}",
            "applicant_user_id": applicant_user_id,
            "chosen_sponsor_user_id": chosen_sponsor_user_id,
            "suggested_user_category": suggested_user_category,
            "approved_user_category": None,
            "affiliation": affiliation,
            "status": "Pending",
            "decision_at": None,
            "decision_by_user_id": None,
            "created_at": self.now(),
            "expires_at": self.now() + timedelta(days=14),
        }
        return self.repository.create_access_request(request_record)

    def list_sponsor_requests(self, sponsor_user_id: str) -> list[dict]:
        return self.repository.list_access_requests_for_sponsor(sponsor_user_id)

    def list_reviewable_requests(self, reviewer_user: BridgeUser) -> list[dict]:
        if reviewer_user.is_admin:
            return self.list_all_access_requests()
        if reviewer_user.is_sponsor:
            return self.repository.list_access_requests_for_sponsor(reviewer_user.id)
        return []

    def list_all_access_requests(self) -> list[dict]:
        return self.repository.list_all_access_requests()

    def list_applicant_requests(self, applicant_user_id: str) -> list[dict]:
        return self.repository.list_access_requests_for_applicant(applicant_user_id)

    def get_access_request(self, request_id: str) -> dict | None:
        return self.repository.get_access_request_by_id(request_id)

    def approve_access_request(self, request_id: str, reviewer_user_id: str, *, approved_user_category: str) -> dict:
        request_record = self._get_pending_request_for_reviewer(request_id, reviewer_user_id)
        applicant = self.repository.get_user_by_id(request_record["applicant_user_id"])
        if applicant is None:
            raise InvalidAccessRequestError("Applicant for the request no longer exists.")

        updated_applicant = replace(
            applicant,
            user_category=approved_user_category,
            approval_state="approved",
        )
        self.repository.update_user(updated_applicant)

        request_record["approved_user_category"] = approved_user_category
        request_record["status"] = "Approved"
        request_record["decision_by_user_id"] = reviewer_user_id
        request_record["decision_at"] = self.now()
        return self.repository.update_access_request(request_record)

    def deny_access_request(self, request_id: str, reviewer_user_id: str) -> dict:
        request_record = self._get_pending_request_for_reviewer(request_id, reviewer_user_id)
        applicant = self.repository.get_user_by_id(request_record["applicant_user_id"])
        if applicant is None:
            raise InvalidAccessRequestError("Applicant for the request no longer exists.")

        updated_applicant = replace(applicant, approval_state="denied")
        self.repository.update_user(updated_applicant)

        request_record["status"] = "Denied"
        request_record["decision_by_user_id"] = reviewer_user_id
        request_record["decision_at"] = self.now()
        return self.repository.update_access_request(request_record)

    def list_sponsors(self) -> list[BridgeUser]:
        return self.repository.list_sponsors()

    def list_users(self) -> list[BridgeUser]:
        return self.repository.list_users()

    def _get_pending_request_for_reviewer(self, request_id: str, reviewer_user_id: str) -> dict:
        request_record = self.repository.get_access_request_by_id(request_id)
        if request_record is None:
            raise InvalidAccessRequestError("Access request was not found.")
        reviewer = self.repository.get_user_by_id(reviewer_user_id)
        if reviewer is None:
            raise PermissionError("Reviewer user was not found.")
        if not reviewer.is_admin and request_record["chosen_sponsor_user_id"] != reviewer_user_id:
            raise PermissionError("Only the selected sponsor or an admin can decide this request.")
        if request_record["status"] != "Pending":
            raise InvalidAccessRequestError("This access request has already been decided.")
        return request_record

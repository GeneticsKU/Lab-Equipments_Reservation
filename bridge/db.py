from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from bridge.auth_store import BridgeUser
from bridge.config import BridgeSettings


def connect_database(database_url: str):
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(database_url, row_factory=dict_row)


class PostgresBridgeRepository:
    def __init__(self, settings: BridgeSettings) -> None:
        self.settings = settings

    def _connect(self):
        return connect_database(self.settings.database_url)

    def get_user_by_email(self, email: str) -> BridgeUser | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, full_name, user_category, affiliation, is_email_verified,
                       approval_state, is_sponsor, is_admin, is_operator, legacy_username, legacy_source
                FROM bridge_users
                WHERE email = %s
                """,
                (email,),
            )
            row = cur.fetchone()
        return self._row_to_user(row)

    def upsert_user(self, user: BridgeUser) -> BridgeUser:
        payload = asdict(user)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bridge_users (
                    id, email, full_name, user_category, affiliation, is_email_verified,
                    approval_state, is_sponsor, is_admin, is_operator, legacy_username, legacy_source
                )
                VALUES (
                    %(id)s, %(email)s, %(full_name)s, %(user_category)s, %(affiliation)s,
                    %(is_email_verified)s, %(approval_state)s, %(is_sponsor)s, %(is_admin)s,
                    %(is_operator)s, %(legacy_username)s, %(legacy_source)s
                )
                ON CONFLICT (email) DO UPDATE SET
                    full_name = COALESCE(EXCLUDED.full_name, bridge_users.full_name),
                    user_category = COALESCE(EXCLUDED.user_category, bridge_users.user_category),
                    affiliation = COALESCE(EXCLUDED.affiliation, bridge_users.affiliation),
                    is_email_verified = EXCLUDED.is_email_verified,
                    approval_state = EXCLUDED.approval_state,
                    is_sponsor = EXCLUDED.is_sponsor,
                    is_admin = EXCLUDED.is_admin,
                    is_operator = EXCLUDED.is_operator,
                    legacy_username = COALESCE(EXCLUDED.legacy_username, bridge_users.legacy_username),
                    legacy_source = COALESCE(EXCLUDED.legacy_source, bridge_users.legacy_source),
                    updated_at = NOW()
                RETURNING id, email, full_name, user_category, affiliation, is_email_verified,
                          approval_state, is_sponsor, is_admin, is_operator, legacy_username, legacy_source
                """,
                payload,
            )
            row = cur.fetchone()
            conn.commit()
        return self._row_to_user(row)

    def store_login_code(self, login_code: dict) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bridge_login_codes (
                    id, user_id, email, purpose, code_hash, attempt_count,
                    created_at, expires_at, consumed_at
                )
                VALUES (
                    %(id)s, %(user_id)s, %(email)s, %(purpose)s, %(code_hash)s,
                    %(attempt_count)s, %(created_at)s, %(expires_at)s, %(consumed_at)s
                )
                """,
                login_code,
            )
            conn.commit()

    def get_latest_login_code(self, email: str, purpose: str) -> dict | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM bridge_login_codes
                WHERE email = %s AND purpose = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (email, purpose),
            )
            return cur.fetchone()

    def count_login_codes(self, *, email: str | None, purpose: str, created_after) -> int:
        with self._connect() as conn, conn.cursor() as cur:
            if email is None:
                cur.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM bridge_login_codes
                    WHERE purpose = %s
                      AND created_at >= %s
                    """,
                    (purpose, created_after),
                )
            else:
                cur.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM bridge_login_codes
                    WHERE email = %s
                      AND purpose = %s
                      AND created_at >= %s
                    """,
                    (email, purpose, created_after),
                )
            row = cur.fetchone()
        return int(row["count"])

    def update_login_code(self, login_code: dict) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bridge_login_codes
                SET attempt_count = %(attempt_count)s,
                    consumed_at = %(consumed_at)s
                WHERE id = %(id)s
                """,
                login_code,
            )
            conn.commit()

    def mark_user_email_verified(self, email: str) -> BridgeUser:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bridge_users
                SET is_email_verified = TRUE,
                    updated_at = NOW()
                WHERE email = %s
                RETURNING id, email, full_name, user_category, affiliation, is_email_verified,
                          approval_state, is_sponsor, is_admin, is_operator, legacy_username, legacy_source
                """,
                (email,),
            )
            row = cur.fetchone()
            conn.commit()
        return self._row_to_user(row)

    def store_session(self, session_record: dict) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bridge_sessions (
                    id, user_id, token_hash, created_at, expires_at, revoked_at, last_seen_at
                )
                VALUES (
                    %(id)s, %(user_id)s, %(token_hash)s, %(created_at)s,
                    %(expires_at)s, %(revoked_at)s, %(last_seen_at)s
                )
                """,
                session_record,
            )
            conn.commit()

    def get_session_by_token_hash(self, token_hash: str) -> dict | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM bridge_sessions
                WHERE token_hash = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (token_hash,),
            )
            return cur.fetchone()

    def update_session(self, session_record: dict) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bridge_sessions
                SET revoked_at = %(revoked_at)s,
                    last_seen_at = %(last_seen_at)s
                WHERE id = %(id)s
                """,
                session_record,
            )
            conn.commit()

    def get_user_by_id(self, user_id: str) -> BridgeUser | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, full_name, user_category, affiliation, is_email_verified,
                       approval_state, is_sponsor, is_admin, is_operator, legacy_username, legacy_source
                FROM bridge_users
                WHERE id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
        return self._row_to_user(row)

    def update_user(self, user: BridgeUser) -> BridgeUser:
        payload = asdict(user)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bridge_users
                SET full_name = %(full_name)s,
                    user_category = %(user_category)s,
                    affiliation = %(affiliation)s,
                    is_email_verified = %(is_email_verified)s,
                    approval_state = %(approval_state)s,
                    is_sponsor = %(is_sponsor)s,
                    is_admin = %(is_admin)s,
                    is_operator = %(is_operator)s,
                    legacy_username = %(legacy_username)s,
                    legacy_source = %(legacy_source)s,
                    updated_at = NOW()
                WHERE id = %(id)s
                RETURNING id, email, full_name, user_category, affiliation, is_email_verified,
                          approval_state, is_sponsor, is_admin, is_operator, legacy_username, legacy_source
                """,
                payload,
            )
            row = cur.fetchone()
            conn.commit()
        return self._row_to_user(row)

    def create_access_request(self, request_record: dict) -> dict:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bridge_access_requests (
                    id, applicant_user_id, chosen_sponsor_user_id, suggested_user_category,
                    approved_user_category, affiliation, status, decision_at, decision_by_user_id,
                    created_at, expires_at
                )
                VALUES (
                    %(id)s, %(applicant_user_id)s, %(chosen_sponsor_user_id)s, %(suggested_user_category)s,
                    %(approved_user_category)s, %(affiliation)s, %(status)s, %(decision_at)s,
                    %(decision_by_user_id)s, %(created_at)s, %(expires_at)s
                )
                RETURNING *
                """,
                request_record,
            )
            row = cur.fetchone()
            conn.commit()
        return row

    def list_reservations(self, reservation_type: str) -> list[dict]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT reservation_type, name, room, equipments, start_time, end_time
                FROM bridge_reservations
                WHERE reservation_type = %s
                ORDER BY start_time ASC, end_time ASC, id ASC
                """,
                (reservation_type,),
            )
            return cur.fetchall()

    def replace_reservations(self, reservation_type: str, rows: list[dict]) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM bridge_reservations
                WHERE reservation_type = %s
                """,
                (reservation_type,),
            )
            if rows:
                cur.executemany(
                    """
                    INSERT INTO bridge_reservations (
                        reservation_type, name, room, equipments, start_time, end_time
                    )
                    VALUES (
                        %(reservation_type)s, %(name)s, %(room)s, %(equipments)s,
                        %(start_time)s, %(end_time)s
                    )
                    """,
                    rows,
                )
            conn.commit()

    def list_access_requests_for_sponsor(self, sponsor_user_id: str) -> list[dict]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM bridge_access_requests
                WHERE chosen_sponsor_user_id = %s
                ORDER BY created_at DESC
                """,
                (sponsor_user_id,),
            )
            return cur.fetchall()

    def list_access_requests_for_applicant(self, applicant_user_id: str) -> list[dict]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM bridge_access_requests
                WHERE applicant_user_id = %s
                ORDER BY created_at DESC
                """,
                (applicant_user_id,),
            )
            return cur.fetchall()

    def list_all_access_requests(self) -> list[dict]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM bridge_access_requests
                ORDER BY
                    CASE WHEN status = 'Pending' THEN 0 ELSE 1 END,
                    created_at DESC
                """
            )
            return cur.fetchall()

    def get_access_request_by_id(self, request_id: str) -> dict | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM bridge_access_requests
                WHERE id = %s
                """,
                (request_id,),
            )
            return cur.fetchone()

    def update_access_request(self, request_record: dict) -> dict:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bridge_access_requests
                SET approved_user_category = %(approved_user_category)s,
                    affiliation = %(affiliation)s,
                    status = %(status)s,
                    decision_at = %(decision_at)s,
                    decision_by_user_id = %(decision_by_user_id)s,
                    expires_at = %(expires_at)s
                WHERE id = %(id)s
                RETURNING *
                """,
                request_record,
            )
            row = cur.fetchone()
            conn.commit()
        return row

    def list_sponsors(self) -> list[BridgeUser]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, full_name, user_category, affiliation, is_email_verified,
                       approval_state, is_sponsor, is_admin, is_operator, legacy_username, legacy_source
                FROM bridge_users
                WHERE is_sponsor = TRUE OR is_admin = TRUE
                ORDER BY COALESCE(full_name, email), email
                """
            )
            rows = cur.fetchall()
        return [self._row_to_user(row) for row in rows if row is not None]

    def list_users(self) -> list[BridgeUser]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, full_name, user_category, affiliation, is_email_verified,
                       approval_state, is_sponsor, is_admin, is_operator, legacy_username, legacy_source
                FROM bridge_users
                ORDER BY
                    CASE WHEN approval_state = 'pending' THEN 0 ELSE 1 END,
                    COALESCE(full_name, email),
                    email
                """
            )
            rows = cur.fetchall()
        return [self._row_to_user(row) for row in rows if row is not None]

    @staticmethod
    def _row_to_user(row: dict | None) -> BridgeUser | None:
        if row is None:
            return None
        return BridgeUser(
            id=row["id"],
            email=row["email"],
            full_name=row.get("full_name"),
            user_category=row.get("user_category"),
            affiliation=row.get("affiliation"),
            is_email_verified=row.get("is_email_verified", False),
            approval_state=row.get("approval_state", "pending"),
            is_sponsor=row.get("is_sponsor", False),
            is_admin=row.get("is_admin", False),
            is_operator=row.get("is_operator", False),
            legacy_username=row.get("legacy_username"),
            legacy_source=row.get("legacy_source"),
        )


def schema_sql_path() -> Path:
    return Path(__file__).resolve().parent.parent / "sql" / "001_bridge_auth.sql"

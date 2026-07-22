CREATE TABLE IF NOT EXISTS bridge_users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    user_category TEXT,
    affiliation TEXT,
    sponsor_user_id TEXT REFERENCES bridge_users(id),
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    approval_state TEXT NOT NULL DEFAULT 'pending',
    is_sponsor BOOLEAN NOT NULL DEFAULT FALSE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_operator BOOLEAN NOT NULL DEFAULT FALSE,
    legacy_username TEXT,
    legacy_source TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bridge_users
    ADD COLUMN IF NOT EXISTS sponsor_user_id TEXT REFERENCES bridge_users(id);

CREATE TABLE IF NOT EXISTS bridge_access_requests (
    id TEXT PRIMARY KEY,
    applicant_user_id TEXT NOT NULL REFERENCES bridge_users(id),
    chosen_sponsor_user_id TEXT NOT NULL REFERENCES bridge_users(id),
    suggested_user_category TEXT,
    approved_user_category TEXT,
    affiliation TEXT,
    status TEXT NOT NULL DEFAULT 'Pending',
    decision_at TIMESTAMPTZ,
    decision_by_user_id TEXT REFERENCES bridge_users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

UPDATE bridge_users AS applicant
SET sponsor_user_id = latest_request.chosen_sponsor_user_id,
    updated_at = NOW()
FROM (
    SELECT DISTINCT ON (request.applicant_user_id)
           request.applicant_user_id,
           request.chosen_sponsor_user_id
    FROM bridge_access_requests AS request
    JOIN bridge_users AS sponsor ON sponsor.id = request.chosen_sponsor_user_id
    WHERE request.status = 'Approved'
      AND sponsor.is_sponsor = TRUE
      AND sponsor.is_admin = FALSE
    ORDER BY request.applicant_user_id,
             COALESCE(request.decision_at, request.created_at) DESC,
             request.created_at DESC
) AS latest_request
WHERE applicant.id = latest_request.applicant_user_id
  AND applicant.sponsor_user_id IS NULL;

CREATE TABLE IF NOT EXISTS bridge_login_codes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES bridge_users(id),
    email TEXT NOT NULL,
    purpose TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS bridge_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES bridge_users(id),
    token_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    last_seen_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS bridge_reservations (
    id BIGSERIAL PRIMARY KEY,
    reservation_type TEXT NOT NULL,
    name TEXT NOT NULL,
    room TEXT NOT NULL,
    equipments TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS bridge_reservations_type_start_idx
    ON bridge_reservations (reservation_type, start_time);

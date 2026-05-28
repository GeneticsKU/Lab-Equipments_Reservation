CREATE TABLE IF NOT EXISTS bridge_users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    user_category TEXT,
    affiliation TEXT,
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


# Phase 01 Research

**Phase:** 01  
**Name:** Streamlit Bridge For Registration And Approval  
**Date:** 2026-05-28  
**Status:** Ready for planning

## Scope

This research is only for the temporary Streamlit bridge. It does not redesign reservation storage, role governance screens, or the later Next.js rewrite. The bridge goal is narrower:

- replace manual user registration in `st.secrets`
- add `@ku.th` one-time-code login
- add sponsor-gated access requests
- keep reservation CSVs and the existing booking UI alive during the bridge period

## Current Code Findings

### Current auth and authorization seam

- [app.py](/Users/nydeyanawat/PycharmProjects/Sandbox/Genetics_Lab_Equipement_Reservation_App/Genetics_Lab_Equipement_Reservation_App/app.py) reads users directly from `st.secrets["credentials"]["usernames"]`.
- Login is username + password only, duplicated across the mobile and desktop branches.
- Authorization is a single coarse role string such as `Admins` or `Lecturer`.
- The app already branches operational behavior on those strings:
  - announcement controls
  - admin tabs
  - booking horizon differences

### Current persistence seam

- Reservation data remains in:
  - `pcr_data.csv`
  - `non_pcr_data.csv`
- Logs remain in:
  - `change_log.csv`
- Equipment catalog remains in:
  - `equipment_details.json`
- Writes trigger in-app Git commits and pushes through `st.secrets["github"]`.

### Bridge implication

The bridge should not try to fix all of that. The narrow seam is:

- replace identity and approval state only
- keep reservation CSV reads and writes working
- derive the current coarse UI powers from bridge-backed user flags

## External Findings

### Streamlit native auth is the wrong fit for the fallback identity model

Streamlit’s native authentication is OIDC-based. The official docs say `st.login()` redirects to an OIDC provider, stores an identity cookie, and uses `st.user` for identity state. The same docs also say that if you need a generic OAuth provider or other custom auth behavior, you should use or create a custom component instead.

Sources:

- [Streamlit user authentication docs](https://docs.streamlit.io/develop/concepts/connections/authentication)
- [Streamlit `st.login()` docs](https://docs.streamlit.io/develop/api-reference/user/st.login)

### Session state alone is not enough for persistent login

The official session-state docs say Streamlit session state is tied to the WebSocket session and resets on browser reload or Markdown-link navigation. That means bridge login cannot rely only on `st.session_state` if it must survive refresh.

Sources:

- [Streamlit session state docs](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
- [Streamlit session state concept guide](https://docs.streamlit.io/develop/concepts/architecture/session-state)

### The pinned Streamlit version lacks `st.context`

The repo pins `streamlit==1.35.0` in [requirements.txt](/Users/nydeyanawat/PycharmProjects/Sandbox/Genetics_Lab_Equipement_Reservation_App/Genetics_Lab_Equipement_Reservation_App/requirements.txt). Streamlit’s versioned docs for `1.35.0` explicitly say `st.context` did not exist in that version. That matters because newer Streamlit versions can read request cookies, while the current version cannot.

Source:

- [Streamlit 1.35.0 `st.context` docs](https://docs.streamlit.io/1.35.0/develop/api-reference/caching-and-state/st.context)

### Neon is straightforward for a narrow bridge database

Neon’s official docs describe it as ordinary Postgres reachable through a standard connection string and recommend pooled connections when the application can create many concurrent connections.

Source:

- [Neon connection guide](https://neon.com/docs/get-started/connect-neon)

### Resend is sufficient for transactional one-time-code and sponsor emails

Resend’s official API docs expose a direct email-send endpoint with the minimal fields the bridge needs: `from`, `to`, `subject`, and HTML or text bodies.

Source:

- [Resend send-email API docs](https://resend.com/docs/api-reference/emails/send-email)

### Cookie persistence needs a custom or third-party bridge

The official Streamlit APIs do not provide a write-cookie primitive for custom auth flows. A practical bridge option is a component-backed cookie manager. The `Extra-Streamlit-Components` project documents a `CookieManager` that can get, set, and delete browser cookies. It also warns that cookies on shared Streamlit-hosted domains should not carry privileged claims directly.

Source:

- [Extra-Streamlit-Components Cookie Manager README](https://github.com/Mohamed-512/Extra-Streamlit-Components)

## Chosen Bridge Architecture

### Identity and session model

- Use passwordless one-time-code login restricted to `@ku.th`.
- Store issued login codes in Neon, not in session state.
- Store opaque session tokens in browser cookies.
- Store only the token in the cookie.
- Store only a hash of that token in Neon.
- Rehydrate `st.session_state` from the cookie-backed session record on each fresh page load.

### Why this is the right bridge shape

- It removes `st.secrets` as the user source of truth.
- It satisfies the user’s chosen fallback identity model without waiting for KU SSO.
- It keeps the bridge aligned with the later rewrite’s identity model instead of inventing a second one.
- It avoids putting approval state or authorization claims directly inside browser cookies.

## Recommended Data Model For The Bridge

### `bridge_users`

Purpose: source of truth for people who can log in or sponsor.

Recommended columns:

- `id`
- `email`
- `full_name`
- `user_category`
- `affiliation`
- `is_email_verified`
- `approval_state`
- `is_sponsor`
- `is_admin`
- `is_operator`
- `legacy_username`
- `legacy_source`
- `created_at`
- `updated_at`

Notes:

- Keep the flag model independent even though the bridge UI stays coarse.
- Preserve `full_name` exactly for migrated users so current CSV reservations still match the display name users expect.

### `bridge_access_requests`

Purpose: sponsor-gated onboarding for new users.

Recommended columns:

- `id`
- `applicant_user_id`
- `chosen_sponsor_user_id`
- `suggested_user_category`
- `approved_user_category`
- `affiliation`
- `status`
- `decision_at`
- `decision_by_user_id`
- `created_at`
- `expires_at`

### `bridge_login_codes`

Purpose: one-time-code issuance and replay protection.

Recommended columns:

- `id`
- `email`
- `code_hash`
- `purpose`
- `request_id`
- `expires_at`
- `consumed_at`
- `attempt_count`
- `created_at`

### `bridge_sessions`

Purpose: persistent login across refresh.

Recommended columns:

- `id`
- `user_id`
- `token_hash`
- `expires_at`
- `revoked_at`
- `last_seen_at`
- `created_at`

## Bridge Authorization Mapping

The bridge should derive current Streamlit powers from bridge-backed flags instead of keeping the old role strings as the source of truth.

Recommended mapping:

- approved user:
  - can reserve
- sponsor:
  - can approve requests addressed to them
  - can access announcement controls if we want to preserve current lecturer behavior
- admin:
  - can see the old admin interface
- operator:
  - optional bridge flag for compatibility, but no full new operations UI yet

This keeps Phase 1 narrow while still storing identity in a future-compatible shape.

## Manual Sponsor Directory Strategy

The bridge should keep sponsor management out of the Streamlit UI.

Recommended manual source:

- a small seed file or SQL bootstrap for sponsor records
- rerunnable import command to upsert sponsor users by `@ku.th` email

This is enough for the bridge and avoids building governance UI in the wrong stack.

## Legacy User Migration Strategy

### Existing manual users

Import users from the current `st.secrets["credentials"]["usernames"]` structure into `bridge_users` with:

- `approval_state = 'approved'`
- `is_email_verified = false`
- exact existing `full_name`
- `legacy_username` preserved

### Existing role mapping

Recommended bridge import mapping:

- `Admins`:
  - `is_admin = true`
  - `is_sponsor = true`
  - `approval_state = 'approved'`
- `Lecturer`:
  - `is_sponsor = true`
  - `approval_state = 'approved'`
- everyone else:
  - `approval_state = 'approved'`

This keeps existing trusted users working after one `@ku.th` verification without running a second approval campaign.

## Operational Risks And Mitigations

### Risk: sponsor-link tampering

Mitigation:

- email link carries only request ID
- sponsor still must sign in
- server checks that signed-in sponsor email matches the request’s selected sponsor

### Risk: OTP replay or brute force

Mitigation:

- hash stored codes
- short TTL
- single use
- attempt counter and lockout per code or email window

### Risk: cookie leakage on shared domains

Mitigation:

- store only opaque session tokens in cookies
- hash tokens in Neon
- avoid putting roles or approval state in the cookie payload
- prefer a dedicated domain or subdomain if deployment later moves there

### Risk: bridge grows into a partial rewrite

Mitigation:

- do not move reservations out of CSV in this phase
- do not build sponsor-management UI in Streamlit
- do not add full capability-management screens

## Phase 01 Planning Guidance

The execution plans for this phase should be split as follows:

1. Bridge auth foundation and database-backed session model.
2. Streamlit login, access-request, and sponsor-approval flow integration.
3. Legacy-user migration, operator runbook, and bridge verification.

That split keeps the highest-risk logic isolated first and makes the later rewrite migration cleaner.

## Research Conclusion

The bridge is feasible and should stay small. The critical constraint is that Streamlit’s native auth does not solve the chosen fallback login model, and plain `st.session_state` does not satisfy persistent login by itself. The correct bridge is therefore:

- custom OTP auth
- Neon-backed state
- Resend-backed transactional email
- cookie-backed opaque session restoration
- unchanged reservation CSV engine

## RESEARCH COMPLETE

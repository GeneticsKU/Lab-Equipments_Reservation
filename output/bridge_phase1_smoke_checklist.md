# Phase 1 Bridge Smoke Checklist

Use this after bridge setup and before relying on the Streamlit bridge in normal use.

## Preconditions

- `.venv` exists and dependencies are installed
- `DATABASE_URL`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, and `APP_BASE_URL` are set
- bridge schema is initialized
- at least one sponsor is seeded
- a legacy user export JSON is available

## Step 1: Migrate one legacy admin

Run:

```bash
.venv/bin/python -m bridge.bootstrap migrate-legacy-users --input legacy_users.json
```

Checks:

- migration summary reports at least one migrated user
- the legacy admin email is stored in lowercase
- the migrated admin has `approved` access state
- the migrated admin still has `is_email_verified = false`

## Step 2: Legacy admin first login

Log in through the app with the migrated admin `@ku.th` email.

Checks:

- a one-time code email is sent
- entering the correct code signs the user in
- the user reaches the normal reservation screens after verification

## Step 3: Refresh persistence

Refresh the browser after the migrated admin is signed in.

Checks:

- the session survives refresh
- the user does not need to request another code immediately

## Step 4: Submit a new access request

Use a second `@ku.th` account that is not already approved.

Checks:

- the app shows the access-request form instead of reservation screens
- the user can enter:
  - full name
  - chosen sponsor
  - suggested category
  - lab or department affiliation
- submitting the form shows a pending state

## Step 5: Sponsor approval flow

Open the sponsor approval email as the selected sponsor.

Checks:

- the approval link includes `approve_request=<request_id>`
- the sponsor must sign in before approval
- the sponsor can approve only their own request
- approving the request changes it from `Pending` to `Approved`

## Step 6: Approved user booking access

Return to the applicant account after sponsor approval.

Checks:

- refresh or re-login reaches the normal reservation screens
- the applicant is no longer stuck in the pending-access flow

## Step 7: Reservation write path still works

Create one test reservation and, if needed, cancel it.

Checks:

- the reservation still writes to `pcr_data.csv` or `non_pcr_data.csv`
- cancellation still updates the same CSV-based reservation source
- Phase 1 did not silently move reservation persistence away from the CSV files

## Step 8: Sponsor request history

While signed in as a sponsor, open the sponsor request history expander.

Checks:

- only requests addressed to that sponsor are visible
- the approved request appears with its final status

## Exit condition

Phase 1 bridge smoke check passes only if:

- legacy approved users can activate through one `@ku.th` verification
- new users require sponsor approval before booking
- sponsor approval is authenticated
- session refresh works
- reservation data still uses `pcr_data.csv` and `non_pcr_data.csv`

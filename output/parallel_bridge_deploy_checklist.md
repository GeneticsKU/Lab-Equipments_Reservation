# Parallel Bridge Deploy Checklist

Use this to launch the bridge as a second Streamlit app alongside the current production app.

## Goal

- Keep the current app available for all users.
- Launch the bridge as a separate pilot app.
- Validate bridge login and sponsor approval before asking users to migrate.

## Recommended topology

- **Current app**: existing production URL, unchanged, still the official reservation app.
- **Bridge pilot app**: second Streamlit deployment pointing to commit `cfb014b` or later.

## Required secrets for the bridge pilot app

- `DATABASE_URL`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USE_SSL`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `APP_BASE_URL`
- `DEPLOYMENT_LABEL`
- `DEPLOYMENT_NOTICE`
- `SESSION_COOKIE_NAME`
- `SESSION_TTL_HOURS`
- `LOGIN_CODE_TTL_MINUTES`
- `[github].username`
- `[github].email`
- `[github].token`
- `[github].branch`
- `[github].repo_owner` (optional)
- `[github].repo_name` (optional)

## Recommended pilot values

```toml
DEPLOYMENT_LABEL = "Bridge Pilot"
DEPLOYMENT_NOTICE = "Pilot deployment for login and approval testing. Keep using the current production app for normal reservations until migration is announced."
SESSION_COOKIE_NAME = "genetics_lab_bridge_pilot_session"
```

Recommended GitHub backup target:

```toml
[github]
username = "your-github-username"
email = "your-github-email"
token = "your-github-token"
branch = "bridge-pilot"
repo_owner = "GeneticsKU"
repo_name = "Lab-Equipments_Reservation_Bridge"
```

## Important separation rules

1. Use a different `APP_BASE_URL` for the pilot app.
2. Use a different `SESSION_COOKIE_NAME` for the pilot app.
3. Point reservation CSV backups at a dedicated bridge branch or dedicated bridge repo.
4. Do not announce the pilot URL broadly until smoke testing is complete.
5. Treat the current app as the source of truth for normal users until cutover.

## Operational warning

This bridge still uses the old reservation engine in `pcr_data.csv` and `non_pcr_data.csv`.

That means the pilot deployment is suitable for:

- login testing
- sponsor approval testing
- controlled booking smoke tests

It is not the right time yet to let all users freely use both apps in parallel without a cutover plan.

## Pilot smoke sequence

1. Existing approved user logs in through the pilot app.
2. Sponsor approves one pending request through the pilot app.
3. Approved user reaches reservation screens.
4. One controlled reservation smoke test is performed.
5. Pilot behavior is reviewed before any broader rollout.

## Exit criteria before migration announcement

- OTP delivery is reliable.
- Sponsor approval works without manual intervention.
- Existing approved users can log in successfully.
- Reservation screens still work after bridge login.
- At least one real new-user approval flow has been tested.

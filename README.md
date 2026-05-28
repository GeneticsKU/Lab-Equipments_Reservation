# Lab-Equipments_Reservation
This application is designed to streamline the reservation process and ensure efficient use of laboratory equipment, providing a user-friendly interface for both regular users and administrators.

Usage Guide
Login: Start sign-in with your `@ku.th` email and complete the one-time code flow. Existing migrated users keep access after email verification, and new users go through sponsor approval before booking.
Make a Reservation: Choose a room and equipment, then select a date and time. The system checks for availability and records the reservation if the selected slot is free.
View and Cancel Reservations: Access your current reservations from a dedicated tab and cancel them if necessary.

Features
Authentication: Passwordless `@ku.th` email login for the bridge flow, with sponsor approval for new users.
Equipment Reservation: Users can book PCR and non-PCR equipment through an interactive form that checks for availability and avoids scheduling conflicts.
Admin Interface: Admin users can toggle equipment availability and view all reservations.
Visual Display: Reservations are displayed in a Gantt chart format, providing an easy visual reference to equipment usage.
Cross-Timezone Support: Configured to handle time correctly for the Asia/Bangkok timezone.
Dynamic Content: Based on user permissions and actions, display dynamic content like forms and equipment details.
Styling for Accessibility: Custom CSS ensures better visibility in both light and dark modes.

## Phase 1 Bridge

The current implementation is in transition from manual `st.secrets` registration to a bridge auth layer backed by Postgres and email one-time codes.

### Required environment variables

- `DATABASE_URL`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `APP_BASE_URL`
- `DEPLOYMENT_LABEL` (optional, useful for a pilot deployment)
- `DEPLOYMENT_NOTICE` (optional, useful for a pilot deployment)
- `SMTP_HOST` (optional, default: `smtp.gmail.com`)
- `SMTP_PORT` (optional, default: `465`)
- `SMTP_USE_SSL` (optional, default: `true`)
- `SESSION_COOKIE_NAME` (optional, default: `genetics_lab_bridge_session`)
- `SESSION_TTL_HOURS` (optional, default: `168` / 7 days)
- `LOGIN_CODE_TTL_MINUTES` (optional, default: `10`)

### Free email path

For the lowest-cost path without KU support, the bridge uses standard SMTP and is designed to work with a dedicated Gmail sender account.

Recommended Gmail setup:

1. Create or choose a dedicated Gmail account for the app.
2. Enable 2-Step Verification on that Google account.
3. Create an App Password for Mail.
4. Set:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_USERNAME=your-sender@gmail.com
SMTP_PASSWORD=your-google-app-password
SMTP_FROM_EMAIL=your-sender@gmail.com
```

This keeps the bridge free at small scale and avoids needing a custom domain.

### Bridge setup

Initialize the bridge schema:

```bash
.venv/bin/python -m bridge.bootstrap init-schema
```

Seed sponsors from a JSON file:

```bash
.venv/bin/python -m bridge.bootstrap seed-sponsors --input sponsors.json
```

The sponsor JSON file should be a list of objects like:

```json
[
  {
    "email": "lecturer1@ku.th",
    "full_name": "Assoc. Prof. Lecturer One",
    "affiliation": "Genetics Department"
  }
]
```

Migrate legacy manually registered users from an exported JSON file:

```bash
.venv/bin/python -m bridge.bootstrap migrate-legacy-users --input legacy_users.json
```

Or run the migration script directly:

```bash
.venv/bin/python -m scripts.migrate_legacy_users --input legacy_users.json
```

If you already have the historical Google Form export workbook, generate both the sponsor seed and legacy-user import files from it:

```bash
.venv/bin/python -m scripts.export_bridge_seed_from_registration_xlsx \
  --input "Registration Form for Lab Equipment Reservation App (Responses).xlsx" \
  --sponsors-output scratch/sponsors_from_registration.json \
  --legacy-output scratch/legacy_users_from_registration.json \
  --report-output scratch/registration_import_report.json
```

This conversion treats:

- `Lecturer` rows as sponsor records
- `Admin` rows as bridge admins
- all other rows as already approved legacy users
- only `@ku.th` emails as valid bridge login identities

The legacy export must contain either:

- `credentials.usernames`
- or top-level `usernames`

with entries shaped like the old Streamlit secrets records.

### Important Phase 1 note

During this bridge phase, reservation data is still written to:

- `pcr_data.csv`
- `non_pcr_data.csv`

The bridge upgrades identity and approval only. It does not replace the reservation CSV engine yet.

### Smoke checklist

Operator smoke checklist:

- [bridge_phase1_smoke_checklist.md](/Users/nydeyanawat/PycharmProjects/Sandbox/Genetics_Lab_Equipement_Reservation_App/Genetics_Lab_Equipement_Reservation_App/output/bridge_phase1_smoke_checklist.md)

Parallel pilot deploy checklist:

- [parallel_bridge_deploy_checklist.md](/Users/nydeyanawat/PycharmProjects/Sandbox/Genetics_Lab_Equipement_Reservation_App/Genetics_Lab_Equipement_Reservation_App/output/parallel_bridge_deploy_checklist.md)
- [streamlit_bridge_pilot_secrets_template.toml](/Users/nydeyanawat/PycharmProjects/Sandbox/Genetics_Lab_Equipement_Reservation_App/Genetics_Lab_Equipement_Reservation_App/output/streamlit_bridge_pilot_secrets_template.toml)

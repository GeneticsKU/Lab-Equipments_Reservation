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
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `APP_BASE_URL`
- `SESSION_COOKIE_NAME` (optional, default: `genetics_lab_bridge_session`)
- `SESSION_TTL_HOURS` (optional, default: `12`)
- `LOGIN_CODE_TTL_MINUTES` (optional, default: `10`)

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

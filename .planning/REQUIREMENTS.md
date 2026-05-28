# Requirements: Genetics Lab Equipment Reservation Rewrite

**Defined:** 2026-05-27
**Core Value:** Eligible KU users can get approved and reserve lab equipment without manual account registration, while the system evolves toward a reliable long-term architecture with clear governance and auditable operations.

## v1 Requirements

### Authentication

- [x] **AUTH-00**: Temporary Streamlit bridge replaces manual registration before the full rewrite is complete.
- [x] **AUTH-01**: User can start sign-in only with an email address ending in `@ku.th`.
- [x] **AUTH-02**: User can complete passwordless authentication with a one-time code sent to their verified `@ku.th` email.
- [x] **AUTH-03**: User session persists across browser refresh and protected navigation.
- [x] **AUTH-04**: Imported approved users can activate their migrated access after one successful `@ku.th` email verification.

### Access Requests

- [x] **ACCS-01**: Applicant can submit an access request with full name, `@ku.th` email, chosen sponsor, suggested user category, and lab room number or department affiliation.
- [ ] **ACCS-02**: Access request status is tracked as exactly `Pending`, `Approved`, `Denied`, or `Expired`.
- [ ] **ACCS-03**: Changing the chosen sponsor requires a new access request.
- [ ] **ACCS-04**: Sponsor can see only their own pending and past approval decisions, with the minimum applicant details needed to decide.
- [x] **ACCS-05**: Sponsor must sign in from their own authenticated `@ku.th` account before approving or denying a request.
- [ ] **ACCS-06**: Sponsor approves ordinary users by confirming or changing the applicant’s suggested user category.
- [ ] **ACCS-07**: Operations Manager has read-only access to all access requests for troubleshooting.
- [ ] **ACCS-08**: Sponsor decisions cannot be delegated to Operations Manager or Admin.
- [x] **ACCS-09**: The temporary Streamlit bridge supports a simple sponsor approval flow inside Streamlit.

### Governance And Roles

- [x] **GOV-01**: System models one user category plus independent capability assignments instead of one exclusive role string.
- [ ] **GOV-02**: All Lecturer users automatically receive Sponsor Capability.
- [ ] **GOV-03**: Only Directory Manager or Admin can assign the Lecturer user category.
- [ ] **GOV-04**: Directory Manager can assign Lecturer, Sponsor Capability, Directory Manager, and Operations Manager, but cannot assign Admin.
- [ ] **GOV-05**: Operations Manager cannot change roles, capabilities, or user categories.
- [ ] **GOV-06**: Exactly one bootstrap-defined Admin account exists at launch.
- [ ] **GOV-07**: Launch Admin cannot be deactivated or reassigned through ordinary in-app controls.
- [ ] **GOV-08**: Admin has full visibility and override authority across users, requests, reservations, restrictions, sponsor data, announcements, and audit history.
- [ ] **GOV-09**: High-trust assignment changes by Admin or Directory Manager require a short reason stored in the audit log.
- [x] **GOV-10**: The temporary Streamlit bridge keeps a deliberately coarse permission model: approved users can reserve, sponsors can approve, and existing admin or operator powers remain coarse.

### Access Lifecycle

- [ ] **LIFE-01**: Access term defaults are enforced by user category for all non-lecturer users.
- [ ] **LIFE-02**: Lecturer is the only launch user category with indefinite access until deactivation.
- [ ] **LIFE-03**: Operations Manager can deactivate user access.
- [ ] **LIFE-04**: Operations Manager can apply access restrictions before deactivation by reducing booking horizon, active future reservation count, or max reservation duration.
- [ ] **LIFE-05**: Access renewal reminders and access expiry notifications are sent by email.

### Reservation Core

- [ ] **RSRV-01**: System supports two reservation models: slot reservation for PCR-like equipment and timed reservation for general equipment.
- [ ] **RSRV-02**: System enforces no-overlap booking conflicts while allowing back-to-back reservations by default.
- [ ] **RSRV-03**: System supports optional cleanup buffers per equipment, even if none are required at launch.
- [ ] **RSRV-04**: Reservation status is tracked as exactly `Scheduled`, `Cancelled`, or `Completed`.
- [ ] **RSRV-05**: User can cancel only before reservation start time.
- [ ] **RSRV-06**: Reservation changes happen through cancellation and rebooking, not in-place editing.
- [ ] **RSRV-07**: Cancelled reservations remain preserved as records with status `Cancelled`.
- [ ] **RSRV-08**: Timed reservation launch policy allows up to 168 hours max duration, with per-category horizon and active-booking limits.
- [ ] **RSRV-09**: Equipment notes remain advisory at launch and do not block booking.

### Reservation Policy

- [ ] **POL-01**: Undergraduate Student default policy is horizon 30 days, max 10 active future reservations, max duration 168 hours.
- [ ] **POL-02**: Master Student default policy is horizon 30 days, max 15 active future reservations, max duration 168 hours.
- [ ] **POL-03**: PhD Student default policy is horizon 30 days, max 15 active future reservations, max duration 168 hours.
- [ ] **POL-04**: Research Assistant default policy is horizon 30 days, max 15 active future reservations, max duration 168 hours.
- [ ] **POL-05**: Researcher default policy is horizon 45 days, max 15 active future reservations, max duration 168 hours.
- [ ] **POL-06**: Lecturer default policy is horizon 60 days, max 20 active future reservations, max duration 168 hours.

### Operations

- [ ] **OPER-01**: Operations Manager can manage equipment availability, announcements, reservations, restrictions, and user-facing operational visibility without sponsor-decision authority.
- [ ] **OPER-02**: Operations Manager and Admin can create delegated reservations on behalf of users with explicit attribution.
- [ ] **OPER-03**: Operations Manager and Admin can perform delegated cancellations on behalf of users with explicit attribution.
- [ ] **OPER-04**: Launch notifications are limited to directly affected users and sponsors.
- [ ] **OPER-05**: Mandatory email notifications are sent for one-time code login, request submitted, sponsor approval request, access approved, access denied, access request expired, access renewal reminder, access expired, reservation created, reservation cancelled, and delegated reservation or cancellation affecting a user.

### Audit And History

- [ ] **AUDT-01**: System stores an immutable audit log for access requests, sponsor decisions, sponsor changes, renewals, expiries, reservation creation, reservation cancellation, equipment availability changes, sponsor-directory changes, and announcement changes.
- [ ] **AUDT-02**: Audit log records actor, timestamp, affected entity, action, and required reason where applicable.
- [ ] **AUDT-03**: Delegated reservations and delegated cancellations record both the acting operator and the affected user.

### Migration And Cutover

- [x] **MIGR-00**: Existing manually registered users are migrated into the bridge auth database and treated as already approved after one successful `@ku.th` email verification.
- [ ] **MIGR-01**: Legacy migration imports equipment catalog data and current enabled or disabled status.
- [ ] **MIGR-02**: Legacy migration imports current future reservations.
- [ ] **MIGR-03**: Reliably matched approved legacy users keep access after one successful `@ku.th` email verification.
- [ ] **MIGR-04**: Unmatched legacy users re-enter through the normal applicant flow.
- [ ] **MIGR-05**: Historical legacy reservations are imported only as legacy-marked history, not as native audited records.
- [ ] **MIGR-06**: Launch cutover uses a short overlap period where only the new system accepts new approvals and new reservations.

## v2 Requirements

### Identity

- **IDEN-01**: Replace fallback email identity with KU SSO if KU provides a suitable integration.

### Policy Refinement

- **POL-07**: Add per-equipment booking-duration overrides and stricter limits where real abuse or operational need is observed.
- **POL-08**: Add equipment-specific booking bans or restrictions as a formal policy tool.
- **POL-09**: Add richer enforcement rules for abuse patterns beyond manual access restriction.

### Reservation Lifecycle

- **RSRV-10**: Add optional check-in or attendance confirmation if lab operations later support reliable detection.
- **RSRV-11**: Add stronger no-show handling only if the lab can verify actual attendance.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Native mobile app | Web-first launch is the lowest-maintenance path for this volunteer project |
| Split frontend/backend services | Integrated full-stack app is the chosen launch architecture |
| In-app password login | Passwordless email auth is lower-maintenance and safer for this project |
| Hard per-equipment booking bans at launch | Deferred until real misuse or policy need is observed |
| Check-in and no-show enforcement | Current operations cannot reliably detect attendance |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-00 | Phase 1 | Complete |
| AUTH-01 | Phase 1 | Complete |
| AUTH-02 | Phase 1 | Complete |
| AUTH-03 | Phase 1 | Complete |
| AUTH-04 | Phase 1 | Complete |
| ACCS-01 | Phase 1 | Complete |
| ACCS-02 | Phase 2 | Pending |
| ACCS-03 | Phase 2 | Pending |
| ACCS-04 | Phase 2 | Pending |
| ACCS-05 | Phase 1 | Complete |
| ACCS-06 | Phase 3 | Pending |
| ACCS-07 | Phase 4 | Pending |
| ACCS-08 | Phase 2 | Pending |
| ACCS-09 | Phase 1 | Complete |
| GOV-01 | Phase 1 | Complete |
| GOV-02 | Phase 3 | Pending |
| GOV-03 | Phase 3 | Pending |
| GOV-04 | Phase 4 | Pending |
| GOV-05 | Phase 4 | Pending |
| GOV-06 | Phase 2 | Pending |
| GOV-07 | Phase 2 | Pending |
| GOV-08 | Phase 4 | Pending |
| GOV-09 | Phase 4 | Pending |
| GOV-10 | Phase 1 | Complete |
| LIFE-01 | Phase 3 | Pending |
| LIFE-02 | Phase 3 | Pending |
| LIFE-03 | Phase 4 | Pending |
| LIFE-04 | Phase 4 | Pending |
| LIFE-05 | Phase 6 | Pending |
| RSRV-01 | Phase 5 | Pending |
| RSRV-02 | Phase 5 | Pending |
| RSRV-03 | Phase 5 | Pending |
| RSRV-04 | Phase 5 | Pending |
| RSRV-05 | Phase 5 | Pending |
| RSRV-06 | Phase 5 | Pending |
| RSRV-07 | Phase 5 | Pending |
| RSRV-08 | Phase 5 | Pending |
| RSRV-09 | Phase 5 | Pending |
| POL-01 | Phase 3 | Pending |
| POL-02 | Phase 3 | Pending |
| POL-03 | Phase 3 | Pending |
| POL-04 | Phase 3 | Pending |
| POL-05 | Phase 3 | Pending |
| POL-06 | Phase 3 | Pending |
| OPER-01 | Phase 4 | Pending |
| OPER-02 | Phase 5 | Pending |
| OPER-03 | Phase 5 | Pending |
| OPER-04 | Phase 6 | Pending |
| OPER-05 | Phase 6 | Pending |
| AUDT-01 | Phase 2 | Pending |
| AUDT-02 | Phase 2 | Pending |
| AUDT-03 | Phase 5 | Pending |
| MIGR-00 | Phase 1 | Complete |
| MIGR-01 | Phase 6 | Pending |
| MIGR-02 | Phase 6 | Pending |
| MIGR-03 | Phase 6 | Pending |
| MIGR-04 | Phase 6 | Pending |
| MIGR-05 | Phase 6 | Pending |
| MIGR-06 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 59 total
- Mapped to phases: 59
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-27*
*Last updated: 2026-05-27 after initial project definition*

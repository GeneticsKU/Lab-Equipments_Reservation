# Roadmap: Genetics Lab Equipment Reservation Rewrite

**Created:** 2026-05-27
**Granularity:** standard
**Execution:** parallel
**Project Mode:** standard

## Phase 1: Foundation And Core Data

**Goal:** Establish the integrated full-stack application foundation, database schema, bootstrap admin model, and immutable audit backbone.

**Why now:** Every later phase depends on a correct data model and trusted system boundaries. The current Streamlit app stores mutable CSV rows, runs Git commands from inside the app, and models access as one string role, so the rewrite needs a clean structural base first.

**Covers requirements:** AUTH-01, AUTH-02, AUTH-03, GOV-01, GOV-06, GOV-07, AUDT-01, AUDT-02

**Key deliverables:**
- Next.js app scaffold with Prisma, Postgres, Auth.js, and environment management
- Core schema for users, capability assignments, access requests, reservations, policies, equipment, and audit log
- Bootstrap-only admin initialization flow
- Base shared authorization primitives and domain enums

**Exit criteria:**
- App boots locally with database-backed persistence
- Bootstrap admin exists and is protected from ordinary in-app deactivation or reassignment
- Audit log writes for sensitive system actions exist and are queryable
- Core schema expresses user category plus capability assignments instead of a single role string

## Phase 2: Identity, Access Requests, And Approval Policy

**Goal:** Implement passwordless `@ku.th` login, sponsor-driven access approval, access lifecycle rules, and category-based reservation policy assignment.

**Why now:** The user’s biggest pain is manual account registration, and the domain model now depends on access request states, sponsor approval, lecturer-specific rules, and category-based policy defaults.

**Covers requirements:** ACCS-01, ACCS-02, ACCS-03, ACCS-04, ACCS-05, ACCS-06, ACCS-08, GOV-02, GOV-03, LIFE-01, LIFE-02, POL-01, POL-02, POL-03, POL-04, POL-05, POL-06

**Key deliverables:**
- `@ku.th` one-time-code authentication flow
- Access request submission and sponsor approval UI
- Sponsor-scoped request visibility
- User category suggestion and sponsor confirmation flow
- Access-term assignment and lecturer exception handling
- Category-based reservation policy defaults

**Exit criteria:**
- New applicant can authenticate, submit a request, and reach a sponsor approval decision flow
- Sponsor must act from their own authenticated account
- Lecturer automatically receives sponsor capability once classified as lecturer
- Approved user receives the correct access term and reservation policy defaults

## Phase 3: Governance, Operations, And Recovery Controls

**Goal:** Implement the operational and governance surfaces for directory management, operations, restrictions, recovery, and read visibility boundaries.

**Why now:** The system needs explicit human control points for the non-self-service parts of the domain, but those powers must stay separated and auditable.

**Covers requirements:** ACCS-07, GOV-04, GOV-05, GOV-08, GOV-09, LIFE-03, LIFE-04, OPER-01

**Key deliverables:**
- Admin and Directory Manager assignment-management screens
- Operations Manager operational dashboards
- Access restriction tools
- Read-only troubleshooting access to all access requests for operations
- Required audit-reason capture for sensitive assignment changes

**Exit criteria:**
- Operations Manager can manage operations without changing trust assignments
- Directory Manager can change lecturer, sponsor, directory, and operations assignments but not admin
- Admin can perform recovery overrides across all governance domains
- Sensitive governance changes require and store an audit reason

## Phase 4: Reservation Engine And Operational Actions

**Goal:** Rebuild the reservation engine around durable status-based records, dual reservation models, policy enforcement, and delegated staff actions.

**Why now:** This is the operational core of the product, but it depends on identity, access, and governance already being stable.

**Covers requirements:** RSRV-01, RSRV-02, RSRV-03, RSRV-04, RSRV-05, RSRV-06, RSRV-07, RSRV-08, RSRV-09, OPER-02, OPER-03, AUDT-03

**Key deliverables:**
- Slot reservation flow for PCR-like equipment
- Timed reservation flow for general equipment
- Reservation policy enforcement engine
- Reservation status lifecycle handling
- Delegated reservation and delegated cancellation flows with attribution
- Equipment-note display and cleanup-buffer-ready rule hooks

**Exit criteria:**
- Users can create and cancel reservations under the new policy model
- Cancelled reservations remain preserved with status changes
- Delegated staff actions are explicitly attributed
- Slot and timed models behave differently where required

## Phase 5: Notifications And Legacy Migration

**Goal:** Deliver the mandatory launch email notifications and migrate legacy data into the new system safely.

**Why now:** Email events are required for the chosen auth and sponsor workflow, and migration should happen only after the target model is stable enough to receive imported data.

**Covers requirements:** AUTH-04, LIFE-05, OPER-04, OPER-05, MIGR-01, MIGR-02, MIGR-03, MIGR-04, MIGR-05

**Key deliverables:**
- Resend-backed launch notification flows
- Legacy import scripts and mapping rules
- Matching logic for approved legacy users
- Legacy-marked history import path

**Exit criteria:**
- All mandatory launch notification types are sent correctly
- Equipment catalog and enabled-state migration succeed
- Future reservations migrate into native records
- Matched users activate after email verification
- Historical legacy reservations are explicitly marked as imported history

## Phase 6: Cutover, Validation, And Retirement Of Streamlit

**Goal:** Execute the controlled cutover period, validate the new system end-to-end, and retire the old Streamlit app from active use.

**Why now:** This phase proves that the rewrite is not just implemented but operationally ready, with the old system constrained to a short overlap period.

**Covers requirements:** MIGR-06

**Key deliverables:**
- Cutover checklist and operating procedure
- Read-only or fallback posture for the legacy Streamlit app
- End-to-end verification across auth, approval, booking, operations, audit, and notifications
- Final go-live and retirement criteria

**Exit criteria:**
- New approvals and new reservations happen only in the new app
- Legacy app is no longer the active write path
- Core workflows are manually verified against launch requirements
- Project is ready to move from migration mode into normal maintenance

## Parallelism Notes

- Phase 1 must complete before the later phases can build on the shared schema and bootstrap auth boundaries.
- Phase 2 and Phase 3 can overlap once the shared foundation exists.
- Phase 4 depends on Phases 1 and 2, and partially on Phase 3 for delegated operations behavior.
- Phase 5 depends on stable domain flows from Phases 2 through 4.
- Phase 6 depends on all earlier phases being implementation-complete and verified.

## Risks To Watch

- KU may later provide SSO, so auth must be replaceable without rewriting the domain layer.
- The automatic sponsor-capability rule for all lecturers makes lecturer classification a high-trust operation.
- The 168-hour timed reservation default may prove too generous operationally; the system must make later tightening easy.
- Legacy data quality may limit how much approved-user history can be trusted automatically.

---
*Roadmap defined: 2026-05-27*

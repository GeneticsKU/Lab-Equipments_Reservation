# Roadmap: Genetics Lab Equipment Reservation Rewrite

**Created:** 2026-05-27
**Granularity:** standard
**Execution:** parallel
**Project Mode:** standard

## Phase 1: Streamlit Bridge For Registration And Approval

**Goal:** Remove manual registration in the existing Streamlit app by adding passwordless `@ku.th` login, sponsor approval, and database-backed identity state.

**Why now:** This is the user’s immediate pain, and the bridge must deliver that relief before the full rewrite. The bridge stays intentionally narrow: reservations remain on CSV, coarse admin or operator powers remain coarse, and sponsor list management stays manual.

**Covers requirements:** AUTH-00, AUTH-01, AUTH-02, AUTH-03, ACCS-01, ACCS-05, ACCS-09, GOV-01, GOV-10, MIGR-00

**Key deliverables:**
- Neon-backed identity and approval tables for the Streamlit app
- Resend-backed one-time-code login flow for `@ku.th`
- Simple sponsor approval screen inside Streamlit
- Direct database-backed authorization replacing `st.secrets` as the user source of truth
- Migration path for existing manually registered users into bridge identity state

**Exit criteria:**
- New users no longer require manual registration in `st.secrets`
- Existing manually registered users can activate through one `@ku.th` verification
- Sponsor approval gates access for new users
- Reservation CSV flows still work against the existing Streamlit UI

## Phase 2: Rewrite Foundation And Core Data

**Goal:** Establish the integrated full-stack rewrite foundation, database schema, bootstrap admin model, and immutable audit backbone.

**Why now:** Once the bridge removes the immediate pain, the rewrite still needs a correct structural base that does not inherit Streamlit-era storage or role assumptions.

**Covers requirements:** GOV-06, GOV-07, AUDT-01, AUDT-02

**Key deliverables:**
- Next.js app scaffold with Prisma, Postgres, Auth.js, and environment management
- Core rewrite schema for users, capability assignments, access requests, reservations, policies, equipment, and audit log
- Bootstrap-only admin initialization flow
- Base shared authorization primitives and domain enums

**Exit criteria:**
- Rewrite app boots locally with database-backed persistence
- Bootstrap admin exists and is protected from ordinary in-app deactivation or reassignment
- Audit log writes for sensitive system actions exist and are queryable

## Phase 3: Rewrite Identity, Approval Policy, And User Classification

**Goal:** Implement the full approval model, lecturer classification rules, ordinary user categorization, access-term defaults, and reservation policy defaults in the rewrite.

**Why now:** The bridge keeps a coarse permission model on purpose. The rewrite is where the full trust model becomes durable and explicit.

**Covers requirements:** ACCS-02, ACCS-03, ACCS-04, ACCS-06, ACCS-08, GOV-02, GOV-03, LIFE-01, LIFE-02, POL-01, POL-02, POL-03, POL-04, POL-05, POL-06

**Key deliverables:**
- Full access request lifecycle
- Sponsor-scoped request history
- Applicant category suggestion and sponsor confirmation
- Lecturer assignment boundary
- User-category-driven access terms and reservation policy defaults

**Exit criteria:**
- Rewrite access request model matches the agreed domain states and boundaries
- Sponsor decisions remain non-delegable
- Lecturer and non-lecturer user classification rules are enforced
- Approved users receive the correct launch policy defaults

## Phase 4: Governance, Operations, And Recovery Controls

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

## Phase 5: Reservation Engine And Operational Actions

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

## Phase 6: Notifications And Legacy Migration

**Goal:** Deliver the mandatory launch email notifications and migrate legacy data into the new system safely.

**Why now:** Email events are required for the chosen auth and sponsor workflow, and migration should happen only after the target model is stable enough to receive imported data.

**Covers requirements:** AUTH-04, LIFE-05, OPER-04, OPER-05, MIGR-01, MIGR-02, MIGR-03, MIGR-04, MIGR-05

**Key deliverables:**
- Resend-backed launch notification flows
- Legacy import scripts and mapping rules
- Matching logic for approved legacy users
- Legacy-marked history import path
- Bridge-to-rewrite migration notes where the bridge identity state feeds the rewrite

**Exit criteria:**
- All mandatory launch notification types are sent correctly
- Equipment catalog and enabled-state migration succeed
- Future reservations migrate into native records
- Matched users activate after email verification
- Historical legacy reservations are explicitly marked as imported history

## Phase 7: Cutover, Validation, And Retirement Of Streamlit

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

- Phase 1 is the bridge milestone and should land before the rewrite phases proceed in earnest.
- Phase 2 must complete before the later rewrite phases can build on the shared schema and bootstrap auth boundaries.
- Phase 3 and Phase 4 can overlap once the rewrite foundation exists.
- Phase 5 depends on rewrite identity, access, and governance being stable.
- Phase 6 depends on stable domain flows from Phases 3 through 5.
- Phase 7 depends on all earlier phases being implementation-complete and verified.

## Risks To Watch

- KU may later provide SSO, so both bridge auth and rewrite auth must be replaceable without rewriting the domain layer.
- The automatic sponsor-capability rule for all lecturers makes lecturer classification a high-trust operation.
- The 168-hour timed reservation default may prove too generous operationally; the system must make later tightening easy.
- Legacy data quality may limit how much approved-user history can be trusted automatically.
- The bridge must stay narrow; otherwise it risks becoming a partial rewrite trapped inside Streamlit.

---
*Roadmap defined: 2026-05-27*

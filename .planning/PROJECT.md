# Genetics Lab Equipment Reservation Rewrite

## What This Is

This project is a clean rewrite of the current Streamlit-based Genetics Department equipment reservation app into a production-grade integrated web application for Kasetsart University users. The new system is for students, researchers, lecturers, and lab operators who need reliable reservation workflows, sponsor-based access approval, operational controls, and durable audit history without depending on manual account registration or CSV files.

## Core Value

Eligible KU users can get approved and reserve lab equipment through a reliable, low-maintenance system with clear governance and auditable operations.

## Requirements

### Validated

- ✓ Users can view equipment availability and make reservations in the current system — legacy Streamlit app
- ✓ PCR-like equipment and general equipment already need different reservation behaviors — legacy Streamlit app
- ✓ Lab staff need operational controls such as announcements and equipment availability toggles — legacy Streamlit app

### Active

- [ ] Replace secrets-based manual login with passwordless `@ku.th` email authentication, while preserving a future path to KU SSO.
- [ ] Implement sponsor-based approval, renewable access, explicit user categories, and separated capability assignments.
- [ ] Move reservation, user, policy, and audit data from CSV files into Postgres with durable history and status models.
- [ ] Preserve the dual reservation model: slot reservations for PCR-like equipment and timed reservations for general equipment.
- [ ] Support operational roles, recovery roles, delegated staff actions, and audit-backed governance changes.
- [ ] Migrate equipment data, future reservations, and reliably matched approved users from the legacy system with a controlled cutover.

### Out of Scope

- Native mobile apps — web-first launch is the lowest-maintenance path for this volunteer project.
- Separate frontend and backend services — a single integrated full-stack app is the chosen launch architecture.
- KU SSO-specific implementation before KU confirms support — launch must work with a verified `@ku.th` fallback identity.
- Equipment-specific hard access rules at launch — advisory notes remain advisory until there is real evidence for tighter enforcement.
- In-app check-in or no-show enforcement — current lab operations do not support reliable detection.

## Context

- The current app is a single-file Streamlit application in [app.py](/Users/nydeyanawat/PycharmProjects/Sandbox/Genetics_Lab_Equipement_Reservation_App/Genetics_Lab_Equipement_Reservation_App/app.py) with duplicated mobile and desktop flows, secrets-based username/password login, CSV persistence, and Git-based backup from inside the running app.
- The current reservation data model is split across `pcr_data.csv`, `non_pcr_data.csv`, `change_log.csv`, and `equipment_details.json`, with destructive cancellation and no durable reservation status model.
- The domain model has now been clarified in [CONTEXT.md](/Users/nydeyanawat/PycharmProjects/Sandbox/Genetics_Lab_Equipement_Reservation_App/Genetics_Lab_Equipement_Reservation_App/CONTEXT.md), including sponsor approval, user categories, capability assignments, audit rules, migration rules, and launch policy defaults.
- This is a volunteer project. Low operational burden and low hosting cost are first-class constraints, which is why the launch platform targets Vercel, Neon, and Resend.
- The launch auth fallback is `@ku.th` one-time-code email login. If KU later provides SSO, the identity layer should be replaceable without rewriting the domain model.

## Constraints

- **Budget**: Near-zero recurring cost at launch — this is a volunteer project with no paid maintenance budget.
- **Tech stack**: Next.js, Postgres, Prisma, Auth.js — chosen to fit the integrated full-stack architecture and low-ops deployment target.
- **Hosting**: Vercel, Neon, Resend — selected as the launch platform unless KU or departmental policy forbids external managed hosting.
- **Governance**: Sponsor approval is the final gate for ordinary applicants — operational roles cannot silently replace sponsor decisions.
- **Operational model**: Low monitoring after launch — policies and defaults must work without constant manual supervision.
- **Migration**: Legacy import must be selective and reliability-driven — old CSV history cannot be treated as native audited data by default.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Clean rewrite instead of evolving Streamlit in place | The current app’s storage, auth, and role model are too far from the target system | — Pending |
| Integrated full-stack app instead of split services | Lowest operational burden for a volunteer-maintained rewrite | — Pending |
| Next.js + Postgres + Prisma + Auth.js | Best fit for integrated deploy, email auth, and relational domain model | — Pending |
| Vercel + Neon + Resend launch platform | Cheapest practical managed stack for this architecture | — Pending |
| Passwordless `@ku.th` one-time-code auth fallback | KU SSO may be unavailable; passwords would add more maintenance burden | — Pending |
| Sponsor approval as the final access gate | Matches lab policy while removing manual account registration bottlenecks | — Pending |
| Separate user category from capability assignments | Needed to model lecturers, sponsors, operations, directory managers, and admin cleanly | — Pending |
| Selective legacy migration with marked imported history | Protects audit integrity while preserving the operationally important data | — Pending |

---
*Last updated: 2026-05-27 after project initialization questioning*

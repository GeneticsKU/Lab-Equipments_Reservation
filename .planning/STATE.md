# State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-27)

**Core value:** Eligible KU users can get approved and reserve lab equipment without manual account registration, while the system evolves toward a reliable long-term architecture with clear governance and auditable operations.
**Current focus:** Phase 1 - Streamlit Bridge For Registration And Approval (planned)

## Status

- Project initialized on 2026-05-27
- Planning mode: interactive
- Granularity: standard
- Parallelization: enabled
- Research before phase planning: enabled
- Plan check: enabled
- Post-phase verifier: enabled

## Current Reality

- Legacy system is a Streamlit app with CSV-backed persistence, manual secrets-based credentials, and in-app Git push behavior.
- Immediate target is a temporary Streamlit bridge using Neon + Resend for identity and approval state while leaving reservations on CSV.
- Long-term rewrite target is a Next.js + Postgres + Prisma + Auth.js integrated full-stack application on Vercel + Neon + Resend.
- Domain language has been established in `CONTEXT.md` and should be treated as the canonical glossary for future phases.
- Phase 1 planning artifacts now exist under `.planning/phases/01-streamlit-bridge-for-registration-and-approval/`.

## Next Step

- Execute Phase 1 plans in order:
  - `01-01-PLAN.md` bridge auth foundation and session persistence
  - `01-02-PLAN.md` Streamlit access request and sponsor approval flow
  - `01-03-PLAN.md` legacy migration, bootstrap, and smoke verification

# State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-27)

**Core value:** Eligible KU users can get approved and reserve lab equipment without manual account registration, while the system evolves toward a reliable long-term architecture with clear governance and auditable operations.
**Current focus:** Phase 1 - Streamlit Bridge For Registration And Approval (implemented, pending real-environment smoke test)

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
- Phase 1 bridge code is implemented in `app.py`, `bridge/`, `scripts/`, `sql/`, and `tests/`.
- Phase 1 planning artifacts exist under `.planning/phases/01-streamlit-bridge-for-registration-and-approval/`.
- Automated verification currently passes for bridge auth, access-request, and legacy-migration tests.
- Full live smoke verification still requires real `DATABASE_URL`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, and `APP_BASE_URL` configuration.

## Next Step

- Run the operator smoke checklist in a real bridge environment:
  - initialize schema
  - seed at least one sponsor
  - migrate one legacy approved user
  - verify OTP login, sponsor approval, and reservation CSV write behavior end to end

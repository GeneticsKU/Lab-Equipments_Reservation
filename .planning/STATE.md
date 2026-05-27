# State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-27)

**Core value:** Eligible KU users can get approved and reserve lab equipment through a reliable, low-maintenance system with clear governance and auditable operations.
**Current focus:** Phase 1 - Foundation And Core Data

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
- Rewrite target is a Next.js + Postgres + Prisma + Auth.js integrated full-stack application on Vercel + Neon + Resend.
- Domain language has been established in `CONTEXT.md` and should be treated as the canonical glossary for future phases.

## Next Step

- Run `$gsd-plan-phase 1` to plan the foundation and core data phase in detail.

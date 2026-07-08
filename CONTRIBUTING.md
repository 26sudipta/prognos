# Contributing to PROGNOS

Thanks for your interest in making PROGNOS better! Contributions of all kinds are welcome — bug fixes, features, docs, and ideas.

## Quick Start

1. **Fork** the repo and create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. **Set up locally** — follow the [Getting Started](README.md#-getting-started) section of the README (backend, frontend, and optionally mobile).
3. **Make your change.** Match the existing code style:
   - Backend: SQLAlchemy 2.0 `Mapped`/`mapped_column` style, Pydantic v2 schemas, all timestamps `TIMESTAMPTZ` (UTC), UUID primary keys.
   - Frontend: TypeScript, App Router conventions, Tailwind.
   - No raw SQL — use the ORM.
4. **Test it:**
   ```bash
   cd backend && .venv/bin/python -m pytest    # all tests must pass
   ```
   New backend features need tests (unit or integration).
5. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat(analytics): add per-tag solve velocity
   fix(auth): refresh token rotation race condition
   ```
6. **Open a Pull Request** with a clear description of *what* and *why*.

## What to Work On

- Check open [issues](../../issues) — anything labeled `good first issue` is a great entry point.
- Have your own idea? Open an issue first so we can discuss the design before you invest time in code.

## Design-First Workflow

PROGNOS follows a design-before-code discipline. For anything beyond a small fix, your PR description (or the preceding issue) should briefly cover:

- **Schema changes** — new tables/columns and their migration
- **API contract** — new/changed endpoints with request/response shapes
- **Logic flow** — how the pieces fit together

See [`docs/`](docs/) for how past phases were designed and documented — every decision has a written *why*.

## Contributor License Agreement

By submitting a contribution (pull request, patch, or code snippet) to this repository, you agree that:

1. You wrote the contribution yourself, or have the right to submit it.
2. You license your contribution under the project's current license ([AGPL-3.0](LICENSE)).
3. You grant the project maintainer (Sudipta Das) a perpetual, worldwide, irrevocable right to **relicense your contribution** as part of PROGNOS under other license terms — including commercial licenses — should the project's licensing model change in the future (e.g., if PROGNOS becomes an organization or company).

This keeps the project's future flexible without ever needing to track down past contributors. Your contribution always remains available under AGPL-3.0 in the versions where it was released.

## Code of Conduct

Be respectful and constructive. We're all here to build something useful for the competitive programming community.

# Phase 5.4 — Continuous Integration (GitHub Actions)

## What Was Built

```
.github/
└── workflows/
    ├── backend-ci.yml     # pytest against a real Postgres, after Alembic migrations
    ├── frontend-ci.yml    # next build (the same check Vercel runs, but blocking)
    └── mobile-ci.yml      # flutter analyze + flutter test (57 tests)

README.md                  # static "tests: 127 passing" badge → 3 live CI badges
backend/pyproject.toml     # + ruff pinned as a dev dependency (local lint tooling)
backend/uv.lock            # updated lockfile
```

## Concepts Explained

### 1. Why CI, and why only now

Deployment was already automated: Render redeploys the backend and Vercel rebuilds the
frontend on every push to `main`. What was missing is the **gate before** those deploys —
nothing stopped a commit with failing tests from going live. And since the repo is public
(AGPL, contributions invited via `CONTRIBUTING.md`), outside PRs need an automatic
correctness check that doesn't depend on the maintainer remembering to run test suites
locally.

A GitHub Actions workflow runs on GitHub's servers on every push/PR: fresh Ubuntu VM,
clone, run steps, report ✅/❌ on the commit. Free for public repos.

### 2. Why three workflows instead of one

This is a monorepo with three independent components. One combined workflow would run
Flutter tests when only a backend docstring changed — wasted minutes and slower feedback.
Each workflow instead declares `paths` filters:

| Workflow | Triggers on changes to |
|---|---|
| Backend CI | `backend/**` + its own workflow file |
| Frontend CI | `frontend/**` + its own workflow file |
| Mobile CI | `mobile/**` + its own workflow file |

Each workflow lists **its own file** in `paths` so editing a workflow re-runs it — and so
the initial commit (which adds all three files) triggers all three once, populating the
README badges immediately.

`concurrency` with `cancel-in-progress: true` cancels a still-running build when a newer
push to the same branch supersedes it — no queue of stale runs.

### 3. Why actions are pinned to exact versions

Steps like `astral-sh/setup-uv@v8.3.2` are pinned to full version tags, not moving majors
like `@v8`. Two reasons:

- **setup-uv v8+ deleted moving tags entirely** — `@v8` does not resolve; only immutable
  full-version tags exist (verified against the GitHub releases API on 2026-07-13:
  checkout v7.0.0, setup-node v6.4.0, setup-uv v8.3.2, flutter-action v2.23.0).
- **Supply-chain safety** — a moving tag can be repointed at malicious code; an immutable
  tag cannot silently change what runs with our repo contents.

### 4. Backend job anatomy

The backend tests hit a real database (`conftest.py` creates users through the actual
async engine), so the job declares a **service container**: GitHub starts `postgres:16`
alongside the VM and the job waits for `pg_isready` health checks before steps run.

The step order mirrors what a fresh machine needs:

```
uv sync --locked          # exact deps from uv.lock (fails if lock is stale)
uv run alembic upgrade head   # build the schema — migrations are the source of truth
uv run pytest -q
```

Config comes from `pydantic-settings` with required fields and no `.env` in CI, so the
job env supplies `DATABASE_URL` (pointing at the service container) plus dummy values for
`GOOGLE_*` and `JWT_*` — they only need to exist, no test exercises real Google OAuth
(HTTP is mocked with `respx`). `ENVIRONMENT: test` keeps `is_production` false so Alembic
doesn't demand SSL. No Redis service: `REDIS_URL` has a default and only the (untested)
worker modules connect, lazily.

Running migrations before tests also makes Backend CI a **migration gate**: a migration
that doesn't apply cleanly to a fresh database fails the build before it can reach Neon.

### 5. Why there are no lint gates (yet)

Both lint suites currently fail on pre-existing issues:

- `ruff check` → 190 violations (import order, pyupgrade, etc.)
- `npm run lint` → 3 errors (react-hooks correctness: setState-in-effect ×2, impure call
  during render) + 8 warnings

A CI gate that is red from day one gets ignored, which trains everyone to ignore red CI.
So the gates cover only what is green today: tests and builds. The workflow files carry
`# No ruff/eslint gate yet` comments marking exactly where to add the steps after a
dedicated lint-cleanup pass. (Ruff itself is now pinned in the backend dev dependencies
so the cleanup can happen with a reproducible version.)

`flutter analyze` **is** gated for mobile because it already passes with zero issues.

### 6. Local verification before the first push

Every gated command was run locally first so the first CI run (and the new public README
badges) start green, not red:

| Check | Result |
|---|---|
| `backend: uv run pytest` | 149 passed (in 7m45s — the suite hits a real Postgres) |
| `frontend: npm run build` | clean production build |
| `mobile: flutter analyze` | no issues |
| `mobile: flutter test` | 57 passed |

## Verification

```bash
# YAML validity
python3 -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/workflows/*.yml')]; print('OK')"

# After push: list the runs and their conclusions (public repo, no auth needed)
curl -s https://api.github.com/repos/26sudipta/prognos/actions/runs?per_page=5 \
  | python3 -c "import json,sys; [print(r['name'], r['status'], r['conclusion']) for r in json.load(sys.stdin)['workflow_runs']]"
# Expected: Backend CI / Frontend CI / Mobile CI — completed success
```

Live badges: the three README badges resolve to
`https://github.com/26sudipta/prognos/actions/workflows/<name>-ci.yml/badge.svg`
and flip red automatically if `main` breaks.

## Key Takeaways

- CI complements the existing auto-deploys: Render/Vercel answer "is it live?", CI
  answers "should it be?" — and it's the only check outside contributors can't skip.
- In a monorepo, path-filtered workflows keep feedback fast and minutes cheap.
- Gate only on checks that pass today; a permanently red gate is worse than none.
  Ratchet lint in later as a separate cleanup task.
- Pin actions to immutable full-version tags — moving majors may not even exist anymore
  (setup-uv v8+) and are a supply-chain risk besides.
- Service containers give tests a real Postgres per run, which doubles as a
  fresh-database migration check.

## Next

Lint-cleanup pass (190 ruff + 3 eslint errors), then enable the two commented-out lint
gates; later, a tag-triggered workflow to build the release APK.

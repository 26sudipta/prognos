# Refresh-Token Rotation — Grace Window (QA Slice 1)

Closes the one genuinely-open item from `docs/qa_audit_2026_07.md`: the **refresh-token
rotation race**. The audit filed it under "dismissed" with the note *"real but not worth
fixing here"* because the first attempt (a `SELECT … FOR UPDATE` row lock) 401'd a second
tab's concurrent refresh and bounced it to `/login`. This slice fixes the race **without**
that regression.

---

## What Was Built

```
backend/
├── alembic/versions/009_refresh_token_rotation_lineage.py   NEW — 2 columns on refresh_tokens
├── app/models/refresh_token.py                              rotated_at + replaced_by_id
├── app/services/auth.py                                     rotate_refresh_token rewrite + _issue_child
└── tests/integration/test_auth_service.py                   +4 tests (grace, replay, chain)
```

No frontend change — the single-flight refresh in `app/_lib/api.ts` stays as-is.

---

## Concepts Explained

### 1. Why the old rotation 401'd a second tab

The refresh token lives in **one httpOnly cookie shared by every tab** of the origin. JS
can't read it, so a tab never holds its own copy — the browser attaches whatever is in the
cookie jar. Two tabs can therefore send the **same** token in-flight before either's
`Set-Cookie` response updates the jar (e.g. both hit a 401 at the same instant and both
refresh).

The old code:

```python
select(RefreshToken).where(
    RefreshToken.token_hash == token_hash,
    RefreshToken.revoked_at.is_(None),   # ← only *live* tokens
    RefreshToken.expires_at > now,
)
# ... token_row.revoked_at = now  (hard revoke)
```

Whichever request commits first revokes the token. The second request now finds **no live
row** → `401` → the tab bounces to `/login`. The `FOR UPDATE` variant serialized the two
but still made the loser lose. That is the exact behavior the audit refused to ship.

### 2. Two race shapes, one fix

| Shape | What happens | How it's handled |
|---|---|---|
| **Truly simultaneous** | Both requests `SELECT` before either commits, so both read `revoked_at IS NULL` | Both take the normal-rotation branch and each mints its own valid child. Postgres row-locks the `UPDATE`s but neither errors. No 401. |
| **Near-simultaneous** | Loser's request arrives just *after* the winner committed, so it reads the token already rotated | **Grace window**: within `ROTATION_GRACE` (30 s) of `rotated_at`, serve a fresh pair instead of rejecting. |

The lookup drops the `revoked_at`/`expires` filters so we can *see* a rotated row and decide,
rather than treating "revoked" and "never existed" identically.

### 3. `rotated_at` vs. a logout revoke — telling them apart

A logout must still hard-kill the session; only a *rotation* is eligible for the grace pass.
Both set `revoked_at`, so that field alone can't distinguish them. The new `rotated_at` is
set **only by rotation**:

```python
if token_row.revoked_at is None:                     # live → rotate
    ... ; token_row.rotated_at = now ; token_row.replaced_by_id = child_id
elif token_row.rotated_at is not None and now - token_row.rotated_at <= ROTATION_GRACE:
    ...                                              # concurrent sibling → fresh pair
else:
    raise 401                                        # logout-revoked, or replay after grace
```

`revoke_token` / `revoke_all_tokens` (logout, logout-all, account delete) leave `rotated_at`
NULL, so a logged-out token can never slip through the grace branch. The existing
`test_rotate_refresh_token_rejects_already_revoked` still passes unchanged.

### 4. `replaced_by_id` — the rotation chain, and how it keeps logout-all honest

A nullable self-FK from a token to the child it rotated into. Beyond making a session's token
lineage auditable, it has a **functional role in the grace check**: grace is granted only while
that child is still unrevoked.

This closes an otherwise-subtle hole. `revoke_all_tokens` (logout-all) and the inline revoke in
`soft_delete_user` filter `WHERE revoked_at IS NULL` — a just-rotated parent is *already*
revoked, so they skip it, but they **do** revoke the live child. Without the child-liveness
check, a parent replayed inside the 30 s window after "log out everywhere" would still mint a
fresh 7-day session. Checking the child (`db.get(RefreshToken, replaced_by_id)`) makes logout-all
authoritative: dead child → grace denied → 401. A normal multi-tab race leaves the child alive,
so it still passes.

`ON DELETE SET NULL` so the self-FK never blocks the `ON DELETE CASCADE` that hard-removes a
user's tokens on account deletion.

### 5. Security posture — what still gets rejected

The window only widens acceptance for a token **that was legitimately rotated < 30 s ago and
whose child session is still alive**. Rejected: unknown tokens, expired tokens, logout-revoked
tokens, a rotated token whose child was since revoked (logout-all / delete), and any rotated
token **replayed after the grace window** (logged as `refresh-token reuse rejected`).

The residual exposure is deliberate and bounded: a stolen cookie replayed **within the 30 s
window** after a real rotation — and only while that session is still logged in — can mint fresh
sessions until the window closes. This is a wider, deterministic window than the audit's original
sub-second race, traded knowingly for multi-tab safety and now observable in logs. Account
deletion is unaffected regardless: `get_current_user` gates on `is_active=False`, so any token
minted for a deleted user is inert. We deliberately do **not** family-kill on post-grace reuse,
to avoid logging out a user whose old tab wakes up late.

---

## Verification

```bash
cd backend
.venv/bin/python -m alembic upgrade head        # 008 -> 009 applies cleanly
.venv/bin/python -m alembic downgrade 008        # reversible
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m pytest tests/integration/test_auth_service.py -q
```

Expected: migration round-trips with no error; **20 passed** (15 existing + 5 new):

- `test_rotate_links_replacement_chain` — normal rotation sets `rotated_at` + `replaced_by_id`.
- `test_rotate_within_grace_serves_concurrent_sibling` — replaying the rotated token
  immediately returns a fresh pair (no 401); both children are unrevoked.
- `test_rotate_grace_denied_after_logout_all` — logout-all revokes the child, so a replay
  inside the window is rejected → `401`.
- `test_rotate_after_grace_rejects_replay` — backdate `rotated_at` past the window → `401`.
- Existing `..._rejects_already_revoked` (logout) and `..._rejects_invalid_token` still `401`.

---

## Key Takeaways

- A shared httpOnly refresh cookie means "concurrent refresh" is normal, not an attack — a
  correct rotation scheme must **tolerate** it, not serialize-and-lose.
- Separate the *reason* a token was revoked (`rotated_at` vs. plain `revoked_at`) so a benign
  concurrency case and a real logout can diverge.
- A short grace window buys multi-tab safety at the cost of a 30 s reuse window that was
  already deemed acceptable — a strictly better trade than the reverted `FOR UPDATE`.

---

## Next

Slice 2 (per-user-timezone heatmap + streaks) awaits the **A vs. B** design pick;
Slice 3 (lint debt + CI gates) is queued after it.

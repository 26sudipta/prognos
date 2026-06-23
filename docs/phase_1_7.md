# Phase 1.7 — Handle Verification Frontend
**Status:** DONE  
**Date:** 2026-06-23  
**Goal:** Build the complete UI for the Codeforces handle verification flow — a multi-state wizard that guides a user from zero to verified, handling all error and lockout scenarios gracefully. The UI had to be professional enough that a competitive programmer would trust it on first sight.

---

## What Was Built

```
frontend/
├── app/
│   ├── _lib/
│   │   └── handles.ts                    ← typed API client for all 4 handle endpoints (new)
│   ├── _components/
│   │   └── sidebar.tsx                   ← Handles nav item enabled (modified)
│   └── (dashboard)/
│       └── handles/
│           └── page.tsx                  ← full 5-state verification wizard (new)

backend/
├── app/
│   ├── schemas/
│   │   └── handle.py                     ← added is_locked + lockout_expires_at to HandleResponse (modified)
│   └── services/
│       └── handle.py                     ← block re-initiate during active lockout (bug fix)
```

---

## Concepts Explained

### 1. Why UX Research Before Writing Code

Before writing a single line of component code, a research agent was dispatched to study real-world verification flows: Vercel domain verification, GitHub SSH key auth, Stripe payment link expiry, GitHub email verification.

The result: five specific, actionable decisions were imported directly from production patterns that millions of users already understand intuitively. This matters because **novelty in verification UX is a bug, not a feature** — a user who has done Vercel DNS verification will immediately recognize the PROGNOS flow. Familiar patterns reduce cognitive load and drop-off.

Key imports:
- Vercel → "Open a new tab — keep this page open" instruction copy
- GitHub SSH keys → the token display (monospace, read-only, single copy button)  
- Stripe → live expiry countdown on the pending state
- GitHub email → the verified artifact gets the badge (not a generic "you did it!" message)

### 2. The 3-Step Mental Model

The raw flow has 5 internal steps (submit handle → CF validation → token generation → user pastes token → confirm). Users should not see these 5 steps — they create analysis paralysis.

Collapsed into 3:

```
[1] Enter Handle → [2] Copy Token → [3] Verify
```

Steps 2 and 3 share the same card view — the user sees the token, pastes it externally, and presses "Verify" from the same screen. The step indicator at the top communicates progress without requiring a literal step-by-step navigation flow.

The stepper is purely decorational/orientational — it does not gate navigation. Users cannot click between steps. This prevents invalid state (e.g. reaching the confirm step without a token).

### 3. The 5-State Machine

The page is a pure state machine. Every piece of UI is determined by exactly one state type:

```typescript
type WizardState =
  | { status: "LOADING" }       // fetching existing handles on mount
  | { status: "NO_HANDLE" }     // no verified or pending handle
  | { status: "PENDING" }       // token generated, waiting for user action
  | { status: "FAILED" }        // wrong token, attempts remaining
  | { status: "LOCKED" }        // 5 failed attempts, in cooldown
  | { status: "SUCCESS" }       // handle verified
```

Each state carries exactly the data it needs and nothing more. `PENDING` carries `token` and `expiresAt`. `LOCKED` carries `lockoutExpiresAt`. `SUCCESS` carries `verifiedAt`. This prevents stale data leaking between transitions.

Transitions:
```
LOADING → NO_HANDLE | PENDING (restored) | LOCKED (restored) | SUCCESS (already verified)
NO_HANDLE → PENDING (on successful initiate)
PENDING → SUCCESS (token matched) | FAILED (wrong token) | LOCKED (5th failure)
FAILED → SUCCESS (token matched) | LOCKED (5th failure) | NO_HANDLE (token expired → 410)
LOCKED → (countdown expires → user must wait, no auto-transition)
SUCCESS → NO_HANDLE (on unlink)
```

### 4. State Restoration on Page Reload

When the user reloads the page, the mount `useEffect` calls `GET /handles` and derives the correct state:

| API response | State restored |
|---|---|
| No handles | `NO_HANDLE` |
| `is_verified = true` | `SUCCESS` |
| `is_locked = true`, lockout still active | `LOCKED` (countdown from `lockout_expires_at`) |
| `is_verified = false`, not locked | `NO_HANDLE` — re-initiate generates fresh token |

For the `PENDING` state after reload: rather than returning the token in the list response (a security concern), the user re-enters their handle. The service updates the row in-place with a fresh token and reset attempt count. This is intentionally friction-free — re-entering the handle takes 2 seconds.

This required adding `is_locked` and `lockout_expires_at` to `HandleResponse` — without these fields, the LOCKED state could not be restored across a page refresh.

### 5. The Lockout Bug Fix

A critical bug was discovered during this phase: `initiate_verification()` was resetting `is_locked = False` whenever a user re-initiated. This meant a user could bypass their lockout by simply re-typing their handle — the 5-attempt security measure was completely circumvented.

Fix added to `services/handle.py`:
```python
if existing is not None:
    # Block re-initiate while lockout is still active
    if existing.is_locked and existing.lockout_expires_at and existing.lockout_expires_at > now:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Handle is locked due to too many failed attempts. Try again after the lockout expires.",
        )
    # ... then reset
```

The `NO_HANDLE` state on the frontend also properly blocks the initiate form — the backend would reject it, but the UX never puts a locked user in a state where they can attempt to re-initiate. The LOCKED state replaces the verify button with a countdown timer.

### 6. Token Display: Copy UX

The token display is the most interaction-critical element — if the user can't easily copy `PGS-A3F7B2`, the entire flow fails.

Design decisions:
- `font-mono text-xl tracking-widest` — the widest letter-spacing available; each character is visually distinct
- `select-none` on the token text — the copy button is the affordance, not text selection. Prevents accidental partial copies
- One-click copy button with immediate inline feedback — icon transitions to checkmark for 1.5 seconds, no toast required
- `AnimatePresence` with `mode="wait"` ensures the icon swap is smooth (copy → checkmark → copy)
- The container has `border-border-default` (slightly brighter than subtle) to visually distinguish it as an interactive/important element

```tsx
<button onClick={copy}>
  <AnimatePresence mode="wait" initial={false}>
    {copied
      ? <motion.span key="check" ...><Check /> Copied</motion.span>
      : <motion.span key="copy"  ...><Copy />  Copy</motion.span>
    }
  </AnimatePresence>
</button>
```

### 7. Countdown Timer Hook

Both the token expiry (PENDING/FAILED) and lockout countdown (LOCKED) share a single `useCountdown` hook:

```typescript
function useCountdown(target: Date | null): string {
  const [display, setDisplay] = useState("");
  useEffect(() => {
    if (!target) return;
    const tick = () => {
      const diff = target.getTime() - Date.now();
      if (diff <= 0) { setDisplay("00:00"); return; }
      const m = Math.floor(diff / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setDisplay(`${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [target]);
  return display;
}
```

The hook takes a `Date | null` target. When `null`, it does nothing. The component passes different targets depending on state. Cleanup via `clearInterval` prevents timer leaks on unmount or state change.

The countdown is displayed in `font-mono tabular-nums` so digits don't cause layout shift as they change.

### 8. Error UX: Not Punishing

The FAILED state was designed to never feel punishing:

- No red on the button, stepper, or border — only the inline error text uses `danger-400`
- The error is below the button (not replacing it) — the action is still immediately visible
- The token display stays visible with its copy button — we assume the user needs to re-copy and try again
- Plain text for attempts remaining: "2 attempts remaining." — not a progress bar that drains, not a color gradient, not a decreasing row of dots. Plain text is informational, not emotional

The LOCKED state uses amber (`warning-400`) not red (`danger-400`). Red reads as "error" or "broken". Amber reads as "temporary limitation" — semantically correct. The copy from research: "Your token is still valid — try again after the cooldown" reframes the lockout as a queue, not a punishment.

### 9. Success State: Confident, Not Celebratory

The success state was deliberately designed to avoid corporate enthusiasm:

- **"Handle verified."** — period, not exclamation mark. To competitive programmers (who use terminals, CLIs, and bare output all day), a period reads as confident finality. An exclamation mark reads as marketing copy.
- The **handle itself** gets the verified badge (green "verified" chip), not a generic "You did it!" card. Mirroring GitHub's verified email pattern — the artifact is what's confirmed.
- One spring animation for the checkmark on mount, then fully static — no looping animations on a success state
- "Go to Dashboard" routes to the CF profile link — but this will point to the actual dashboard once Phase 2 is complete

### 10. Framer Motion: AnimatePresence for State Transitions

The outer wizard card and SUCCESS card use `AnimatePresence mode="wait"` to cleanly crossfade + slide between states:

```tsx
<AnimatePresence mode="wait">
  {state.status === "SUCCESS" && (
    <motion.div key="success" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} ...>
  )}
  {["NO_HANDLE", "PENDING", ...].includes(state.status) && (
    <motion.div key="wizard" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} ...>
  )}
</AnimatePresence>
```

The inner stepper content (step 1 ↔ step 2) uses a horizontal slide:
- Step 1 exits to the right (`x: 16`), step 2 enters from the right (`x: 16, → 0`)
- On "Start over", step 2 exits to the left, step 1 enters from the left

This gives spatial orientation — the user always knows if they're moving forward or backward in the flow.

---

## Verification

```bash
# 1. Start both servers
cd backend && .venv/bin/uvicorn app.main:app --reload
cd frontend && npm run dev

# 2. Log in at http://localhost:3000/login (Google OAuth)

# 3. Navigate to http://localhost:3000/handles
# ✓ 3-step stepper visible at top (step 1 active, indigo)
# ✓ "Link your Codeforces account" heading
# ✓ Monospace input with "tourist" placeholder
# ✓ "Continue →" primary button
# ✓ "How verification works" with 3 numbered items
# ✓ Handles sidebar item now clickable

# 4. Enter a CF handle and click Continue
# ✓ Transitions to step 2 with token visible
# ✓ Token: PGS-XXXXXX format, monospace, large
# ✓ Copy button → checkmark for 1.5s
# ✓ "Open a new tab — keep this page open" in amber
# ✓ Expiry countdown running (MM:SS)

# 5. Click "I've done it — Verify" without pasting token
# ✓ FAILED state: error inline below button, attempts remaining shown
# ✓ Token still visible with copy button

# 6. Fail 5 times
# ✓ LOCKED state: amber countdown replaces button
# ✓ "Try again in XX:XX" with lock icon

# 7. Go to codeforces.com, paste token in Last Name, return and verify
# ✓ SUCCESS state: spring-animated checkmark
# ✓ "Handle verified." (with period)
# ✓ Handle displayed in monospace with green "verified" chip

# 8. Reload page
# ✓ SUCCESS state restored immediately (no flash of NO_HANDLE)

# 9. Run backend tests
cd backend && .venv/bin/python -m pytest tests/ -v
# 19 passed
```

---

## Key Takeaways

- **Import from Vercel/GitHub/Stripe, don't invent.** Users arrive with mental models from tools they already use. Matching those patterns reduces cognitive load to near zero.
- **3-step model beats 5-step.** The internal flow has 5 steps. Users should never see more than 3. Collapse and simplify.
- **A state machine eliminates impossible UI states.** Every pixel on screen is determined by exactly one named state. There is no "loading + PENDING + error" overlap. This prevents the class of bugs where partial state causes undefined UI.
- **`select-none` on the token forces the copy button as the affordance.** Accidental partial text selection is the most common failure mode for "copy this code" UIs.
- **Lockout UX: amber not red, "queue" not "punishment".** The framing of "try again after the cooldown" vs "you failed too many times" changes how the user feels about the product.
- **Period, not exclamation mark.** "Handle verified." reads as confident and professional to a technical audience. Exclamation marks belong in marketing copy.
- **`useCountdown` belongs in a hook, not inline.** The same countdown logic serves token expiry and lockout — one hook, two use sites.

---

## Next

**Phase 2.1 — Celery + CF Sync Worker:** Once a handle is verified, trigger a full historical sync of submissions and rating changes from the Codeforces API. This is the first Phase 2 task and the first time the dashboard shows real data.

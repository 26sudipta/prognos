# Phase 3.3 — Contest UI

## What Was Built

```
frontend/
├── app/
│   ├── _lib/
│   │   └── contests.ts                        ← NEW: types, API client, platform identity, time utils
│   └── (dashboard)/
│       ├── contests/
│       │   ├── page.tsx                        ← NEW: orchestrator page
│       │   └── _components/
│       │       ├── platform-badge.tsx          ← NEW: colored abbreviation badge (CF, AC, LC…)
│       │       ├── countdown-display.tsx       ← NEW: useCountdown hook + card/hero display variants
│       │       ├── stale-data-banner.tsx       ← NEW: amber warning when is_stale=true
│       │       ├── contest-card.tsx            ← NEW: single contest row with live/urgency states
│       │       ├── contest-list-view.tsx       ← NEW: date-grouped list with empty state
│       │       ├── contest-detail-modal.tsx    ← NEW: click-to-modal overlay (framer-motion)
│       │       ├── contest-calendar-view.tsx   ← NEW: 7-column week grid with inline pill expand
│       │       ├── platform-filter-chips.tsx   ← NEW: multi-select filter chips
│       │       └── next-contest-hero.tsx       ← NEW: next/live contest countdown strip
│       └── _components/
│           └── sidebar.tsx                     ← MODIFIED: Contests nav item enabled (disabled removed)
```

---

## Concepts Explained

### 1. Why single fetch endpoint, not separate calendar endpoint

The backend exposes both `/contests` (flat list) and `/contests/calendar` (UTC-grouped). The frontend uses **only the list endpoint** for all views.

Reason: calendar grouping must respect the user's **local timezone**, not UTC. A contest at `22:00 UTC July 12` would land on July 12 in the backend calendar grouping, but appears on July 13 to a UTC+6 user. Grouping client-side by local date (via `localDateKey(new Date(c.start_time))`) is both correct and cheap — the dataset is at most 200 contests.

This also simplifies state: one `contests: ContestItem[]` array feeds both the list view (grouped by local date) and the calendar view (filtered to the displayed week, then grouped). The hero strip reads from the same array with zero extra API calls.

### 2. Countdown timer — precision escalation

The `useCountdown` hook returns `isSoon` (<24h to start) and `isUrgent` (<1h to start). The `CountdownDisplay` component changes both **format and color** based on state:

| State | Format | Color |
|---|---|---|
| >1 day away | `3d 14h` | `text-text-muted` (gray) |
| <24h away | `14:22:35` (HH:MM:SS) | `text-accent-400` (cyan) |
| <1h away | `00:42:18` | `text-danger-400` (red) |
| Live (running) | `● LIVE · ends 01:23:44` | success-400 dot + danger-400 time |
| Ended | `Ended` | `text-text-muted` at 50% opacity |

The `tabular-nums` CSS property is applied to all countdown spans. Without it, the digit column shifts width every second as `1` is narrower than `8`, causing visible jitter.

Two display variants exist:
- **`CountdownDisplay`** — compact, for contest cards (xs text)
- **`HeroCountdown`** — segmented with labels (`d`, `h`, `m`, `s`), for the hero strip (4xl text)

`HeroSegment` and `HeroSep` are module-level functions (not defined inside `HeroCountdown`), because `eslint-plugin-react` rule `react-hooks/static-components` flags components defined inside render functions — they'd get new identity on every tick, resetting their own state.

### 3. Platform identity system

CLIST returns platform names as domain strings (`codeforces.com`, `atcoder.jp`). Three maps in `contests.ts` provide display name, abbreviation, and color:

```typescript
platformColor("codeforces.com")  // "#1A81C4"
platformAbbr("codeforces.com")   // "CF"
platformDisplayName("codeforces.com") // "Codeforces"
```

Unknown platforms fall back gracefully: color `#64748B` (slate/neutral), abbreviation = first 2 chars uppercased. This handles new platforms that CLIST adds after the color map was written.

Platform badges use `bg-[color]/22` (8.5% opacity background) with the hex color as text — low saturation tint behind a saturated foreground. This works in dark mode without a white background.

Filter chips use `bg-[color]/18 border-[color]/50 text-[color]` when active — same color-coding pattern reinforces platform identity across the whole page.

### 4. useEffect without synchronous setState

The `react-hooks/set-state-in-effect` ESLint rule prohibits calling `setState` synchronously inside an effect body. The contest fetch effect uses a cancellation flag + `.then()` / `.catch()` pattern to keep all state mutations asynchronous:

```typescript
useEffect(() => {
  if (!token) return;
  let cancelled = false;
  fetchContests(token, params)
    .then((data) => { if (!cancelled) { setContests(data.contests); ... } })
    .catch(() => { if (!cancelled) { setContests([]); ... } });
  return () => { cancelled = true; };
}, [token, selectedPlatforms, view, weekOffset]);
```

The `cancelled` flag ensures that if the user changes a filter quickly (firing two requests), only the response matching the latest request is applied. Stale responses from superseded requests are silently discarded.

**Loading UX**: on initial mount `contests` is `undefined` → skeletons shown. On filter changes, `contests` remains the previous array until the new response arrives — users see stale data briefly rather than a blank skeleton. This is the standard stale-while-revalidate pattern.

### 5. Calendar — local timezone grouping

`getLocalWeekDays(weekOffset)` builds a Mon–Sun array in **local timezone** from the browser's `Date`:

```typescript
const dayOfWeek = now.getDay(); // 0=Sun … 6=Sat
const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
const monday = new Date(now);
monday.setDate(now.getDate() + daysToMonday + weekOffset * 7);
```

When in calendar view, `getWeekBoundsISO(weekOffset)` converts these local dates to UTC ISO strings to send as `from_dt` / `to_dt` query params. The API filters by those UTC boundaries, and the calendar client re-groups the returned contests by local date key — ensuring a contest at 23:30 UTC lands on the correct local day.

`CalendarDayCell` shows up to 3 pills. A "+N more" button expands the cell **inline** (not to a modal). Opening a modal to reveal more items — which you then click to open a second modal — creates two levels of indirection that confuses users.

### 6. Modal with framer-motion AnimatePresence

The detail modal uses `AnimatePresence` so the exit animation plays before the DOM node is removed. Without `AnimatePresence`, React unmounts the element immediately when `contest === null`, the exit animation never runs.

```tsx
<AnimatePresence>
  {contest && (
    <>
      <motion.div /* backdrop */ />
      <motion.div /* panel */ />
    </>
  )}
</AnimatePresence>
```

Pressing `Escape` or clicking the backdrop fires `onClose` (sets `selectedContest = null`), which triggers the `exit` animation sequence.

### 7. View toggle preserves filter state

The `view`, `selectedPlatforms`, and `weekOffset` are all page-level state in `ContestsPage`. Switching between List and Calendar never resets the platform filter — the filter chips stay selected. Switching to Calendar resets `weekOffset` to 0 (current week) once, so you don't return to last week's view unexpectedly.

### 8. Sidebar: removing `disabled`

The Contests nav item previously had `disabled: true` in `NAV_ITEMS`. This rendered a `<span>` with `cursor-not-allowed` instead of a `<Link>`. Removing `disabled: true` causes the type-narrowing in the render loop to take the `<Link>` path automatically — no other change needed.

---

## Verification

```bash
# TypeScript + build
cd frontend
npm run build
# Expected: ✓ Compiled successfully; /contests in route list

# Lint (new files only)
npx eslint "app/(dashboard)/contests/**/*.tsx" "app/_lib/contests.ts"
# Expected: no output (clean)

# Dev server
npm run dev
# Visit http://localhost:3000/contests
# - Hero strip shows skeleton → contest info with countdown
# - Platform chips populate from API
# - List view groups contests by local date
# - Filter by Codeforces → only CF contests
# - Toggle to Calendar → week grid, contest pills
# - Click any pill/card → detail modal opens
# - Press Escape → modal closes with animation
# - is_stale=true → amber banner appears
```

---

## Key Takeaways

- **Single fetch endpoint for both views** — client-side grouping is cheap, avoids UTC/local mismatch from server-side calendar grouping.
- **`tabular-nums` on all countdown spans** — prevents digit column jitter on every tick.
- **`HeroSegment` / `HeroSep` outside component body** — components defined inside render get new identity on every render; ESLint `react-hooks/static-components` catches this.
- **Cancellation flag in fetch effect** — prevents stale response from a superseded request from overwriting fresh data.
- **Platform colors: `hex/22` background + `hex` text** — high-contrast on dark backgrounds without needing a white card behind the pill.
- **"+N more" expands inline** — two-level modal indirection (expand modal → contest modal) degrades UX; inline expansion avoids it.
- **`AnimatePresence` required for exit animation** — React unmounts synchronously without it; the motion exit sequence never fires.

---

## Updates

### QA Audit — 4 bugs fixed (2026-06-25)

A full post-implementation audit of all Phase 3 code was performed. Four bugs were identified and fixed.

---

#### Bug 1 (Critical): Multi-platform filter silently discarded extra values

**Root cause.** The route declared `platform: str | None = Query(default=None)`. When the frontend sends `?platform=codeforces.com&platform=atcoder.jp` (one `append` per selected platform), FastAPI only captured the first value; the rest were silently dropped. Selecting two platforms returned only one.

**Fix.**

```python
# routes/contests.py — both list_contests and contests_calendar
platform: list[str] | None = Query(default=None),

# services/contests.py — both get_contests and get_contests_calendar
if platform:
    base_q = base_q.where(Contest.platform.in_(platform))
```

All integration tests that passed a bare string (`platform="codeforces.com"`) were updated to pass a list (`platform=["codeforces.com"]`). A new test — `test_get_contests_filters_by_multiple_platforms` — verifies that two platforms both appear in the result.

---

#### Bug 2 (Correctness): Multi-day contest end time shows no date

**Root cause.** All three surfaces — contest card (`"Sat, Jul 12 · 17:35 – 02:00"`), hero strip, and modal ("Ends: 02:00") — called `formatLocalTimeOnly(end_time)`. For a contest that crosses midnight or runs 24+ hours (CodeChef Long Challenge, ICPC), this is ambiguous and wrong: "02:00" looks like 2 AM the same night, but the contest ends two days later.

**Fix.** New utility added to `_lib/contests.ts`:

```typescript
export function formatLocalEndLabel(startIsoStr: string, endIsoStr: string): string {
  if (localDateKey(new Date(startIsoStr)) === localDateKey(new Date(endIsoStr))) {
    return formatLocalTimeOnly(endIsoStr);         // same local day: "02:00"
  }
  return formatLocalDateTimeShort(endIsoStr);       // different day: "Sun, Jul 13 · 02:00"
}
```

Applied in `contest-card.tsx`, `next-contest-hero.tsx`, and `contest-detail-modal.tsx`.

---

#### Bug 3 (UX): `CalendarDayCell` expanded state not reset on filter change

**Root cause.** `CalendarDayCell` has local `useState(false)` for the "+N more" expand toggle. Since it is keyed by day index (0–6), the component instance persists across filter changes. A user could expand Wednesday, change the platform filter (which triggers a new fetch and updates the `contests` prop), and still see the "+N more" expanded view even though the contests array had changed.

**Fix.** Added effect in `CalendarDayCell`:

```typescript
useEffect(() => { setExpanded(false); }, [contests]);
```

The `contests` reference changes on every new fetch, so the effect fires on any filter or week change, collapsing the cell automatically.

---

#### Bug 4 (Performance): Escape listener registered while modal is closed

**Root cause.** The `useEffect` in `ContestDetailModal` added the `keydown` listener unconditionally. The `onClose` dependency is an inline arrow defined in `page.tsx` — it gets a new reference on every parent render, so the listener was being removed and re-added repeatedly even when the modal was closed. Any Escape keypress while the modal was closed called `setSelectedContest(null)` (a no-op), but still triggered an unnecessary React re-render.

**Fix.**

```typescript
useEffect(() => {
  if (!contest) return; // only register while modal is open
  function handler(e: KeyboardEvent) {
    if (e.key === "Escape") onClose();
  }
  document.addEventListener("keydown", handler);
  return () => document.removeEventListener("keydown", handler);
}, [contest, onClose]);
```

Adding `contest` to deps causes the listener to be registered only when `contest` is non-null and cleaned up when it becomes null (modal closes).

---

#### Time-sensitive test fixed

`test_get_platforms_returns_distinct_sorted` seeded contests with hardcoded July 2026 dates. `get_platforms` uses a `now → now+30d` window, so the test would have silently broken after 2026-07-04. Replaced hardcoded dates with `now + timedelta(days=N)` offsets so the test never expires.

---

## Next

**Phase 4.1** — Classroom System: DB schema + backend (classrooms, invites, memberships, leaderboard cache tables).

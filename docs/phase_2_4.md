# Phase 2.4 — Dashboard UI

## What Was Built

```
frontend/app/_lib/analytics.ts                                  ← types + 5 fetch functions
frontend/app/(dashboard)/dashboard/page.tsx                     ← orchestrator (replaces placeholder)
frontend/app/(dashboard)/dashboard/_components/
  stat-strip.tsx          ← Row 1: 4 stat cards
  activity-heatmap.tsx    ← Row 2: GitHub-style contribution heatmap
  rating-chart.tsx        ← Row 3 left (60%): Recharts rating line chart
  tag-stats.tsx           ← Row 3 right (40%): horizontal tag bar list
  weakness-cards.tsx      ← Row 4 left: weakness signal cards
  recommendations.tsx     ← Row 4 right: problem recommendation list
```

---

## Concepts Explained

### 1. Parallel fetching with independent loading states

The brief requires all 5 endpoints to load in parallel and each section to show `.skeleton` independently while in-flight. A single `Promise.all` approach blocks every section until the slowest endpoint resolves — the wrong trade-off when a slow `/recommendations` should not delay the stat cards.

The solution: fire all 5 fetches concurrently inside a single `useEffect`, but update 5 independent state variables as each resolves.

```tsx
useEffect(() => {
  if (!token) return;
  fetchDashboard(token).then(setDashboard).catch(() => setDashboard(EMPTY_DASHBOARD));
  fetchTags(token).then(setTags).catch(() => setTags([]));
  fetchRatingHistory(token).then(setRatingHistory).catch(() => setRatingHistory([]));
  fetchWeaknesses(token).then(setWeaknesses).catch(() => setWeaknesses([]));
  fetchRecommendations(token).then(setRecs).catch(() => setRecs(null));
}, [token]);
```

Each section renders `<XSkeleton />` when its state is `undefined` (loading), and its data component when the state resolves to a value.

**Why errors fall through to empty states rather than an error UI**: The empty states are specific and actionable ("Link your handle", "Sync hasn't run"). A generic "Failed to load" error card would be worse UX for the most common failure mode (no handle linked), and API errors on an analytics dashboard don't require an alert — they just mean the data isn't there yet.

---

### 2. The `undefined` / `null` / `T` loading sentinel pattern

Standard React patterns use a boolean `isLoading` alongside the data. This requires two state variables per endpoint. A cleaner pattern for read-only data:

| Value | Meaning |
|---|---|
| `undefined` | In flight — show skeleton |
| `null` | Loaded, but genuinely empty (or error) |
| `T` | Loaded with data — render component |

For recommendations specifically, `null` is a valid API response (no set exists yet), so the type is `RecommendationSet | null | undefined`. The `Recommendations` component receives `data: RecommendationSet | null` — it distinguishes the two non-loading states without needing to know about `undefined`.

---

### 3. Empty handle detection vs. empty data

When no Codeforces handle is linked, all analytics endpoints return zeroes and empty arrays — not a 404. The page detects this state by checking:

```tsx
function noHandleLinked(d: DashboardData): boolean {
  return d.heatmap.length === 0 && d.total_solved === 0 && d.cf_rating === null;
}
```

All three conditions must be true simultaneously. A user with a linked handle who has never contested would have `cf_rating: null`, but they'd also have `total_solved > 0` from practice submissions — so the check doesn't false-positive for them.

When this state is detected, the entire page is replaced by a single nudge card instead of rendering six empty/zero sections. Broken charts with zero data are confusing; one clear action is not.

---

### 4. Heatmap cell sizing for 1280px

The constraint: 52 weeks × 7 days must fit without horizontal scroll at a 1280px viewport.

**Calculation:**
- Sidebar: 240px (`w-60`)
- Layout padding: 24px × 2 = 48px
- Usable content width: 1280 − 240 − 48 = **992px**

- Cell size: `w-3.5 h-3.5` = 14px
- Gap: `gap-[3px]` = 3px
- 52 weeks × (14 + 3) − 3 = **881px** for the week grid
- Day-of-week label column: 32px
- Total: 881 + 32 = **913px** — fits in 992px with 79px to spare

Cells smaller than 14px are hard to hover-target on high-DPI screens; larger would require a horizontal scrollbar on 1280px viewports.

---

### 5. Rating chart Y-axis: manual domain vs. auto-scale

Recharts auto-scale picks bounds that make the chart fill the vertical space but produces unintuitive tick values (e.g., `1234 … 1567`) with no padding at the line edges.

The alternative: `domain={[Math.max(0, minRating - 50), maxRating + 50]}`.

- The `−50` / `+50` buffer ensures the line never touches the top or bottom edge, giving visual breathing room.
- Ticks land on round CF-familiar numbers (e.g., 1600, 1700, 1800).
- `Math.max(0, ...)` prevents negative domains for users who started below 50 rating.

A full `[0, max]` domain was rejected: a user at 1800 rating would waste 1800px of chart height on empty space.

---

### 6. Tag visualization: horizontal list over bar/radar chart

**Rejected alternatives:**

| Option | Why rejected |
|---|---|
| Vertical bar chart | CF tag names average 15–20 chars. Rotation or truncation is mandatory — both hurt readability in a 40% column. |
| Radar chart | 8+ axes become unreadable at small sizes. Relative comparison across non-ordered axes (greedy vs. math vs. trees) has no semantic meaning. Doesn't show absolute counts. |

**Chosen: horizontal bar list.** Tag names render naturally left-to-right. The inline progress bar (width = `solved_count / max_solved_count * 100%`) communicates relative rank at a glance. The `solved_count` number on the right gives the absolute value. The combination beats a pure bar chart (which would need axis labels) or a pure list (which would need sorting context).

---

### 7. Weakness signal ordering: score vs. type grouping

The API returns signals sorted by `score DESC`. Score is a continuous 0–1 value encoding how severe the weakness is, computed by the sync worker.

**Grouping by `signal_type` first** would produce three blocks (Low Success / Neglected / Under-practiced) regardless of severity. A neglected tag at score 0.3 would appear before a low-success tag at 0.9 if sorted by type.

**Trusting score ordering** means the most urgent item is always first, regardless of type. The color-coded badge on each card (`danger-400`, `warning-400`, `accent-400`) communicates the type without requiring positional grouping.

---

### 8. Recommendations null state: not a spinner

When `GET /recommendations` returns `null`, it means the CF sync worker has never run for this user. This is a **permanent state** until the user triggers a sync — not an in-progress loading state.

A spinner implies "something is happening, wait." A null-recommendations state is static; showing a spinner would be actively misleading. Instead:

- Icon: `RefreshCw` (not a loading spinner)
- Copy: "Sync hasn't run yet." (factual, period not exclamation)
- Sub-copy: "Go to Handles and run a sync to generate problem recommendations."
- CTA: Link to `/handles`

This follows the same pattern as the no-handle nudge: one clear action instead of an ambiguous empty state.

---

### 9. CF rating color ladder

The standard Codeforces color ladder is applied to both the CF Rating stat card and problem difficulty badges. These are not design-system tokens — they're CF-canonical colors that users recognize instantly.

| Rating | Color | Token |
|---|---|---|
| < 1200 | Gray `#9E9E9E` | — |
| 1200–1399 | Green `#4CAF50` | — |
| 1400–1599 | Cyan `#22D3EE` | accent-400 |
| 1600–1899 | Blue `#1E88E5` | — |
| 1900–2099 | Violet `#AA46BE` | — |
| 2100–2399 | Orange `#FF8F00` | — |
| ≥ 2400 | Red `#F44336` | danger-500 |

The same `cfRatingColor` function is implemented in both `stat-strip.tsx` and `recommendations.tsx` (for difficulty). It's intentionally duplicated rather than extracted to a shared util — both components are self-contained per the ≤150-line constraint, and a shared utility would be a premature abstraction for two call sites.

---

## Verification

```bash
cd frontend
npm run dev        # dev server at localhost:3000
# Navigate to /dashboard
# — without a linked handle: shows "Link your Codeforces handle" nudge card
# — after linking + syncing: shows all 6 sections with real data
# — during fetch: each section shows shimmer skeleton independently

npm run build      # must exit 0 with no type errors
npx tsc --noEmit   # 0 errors
```

Expected build output:
```
✓ Compiled successfully
Route (app)
├ ○ /dashboard
└ ...
```

---

## Key Takeaways

- **5 separate state variables** (not `Promise.all`) is the correct pattern for parallel fetches where sections should load independently.
- **`undefined | null | T`** encodes loading/empty/data in a single variable without a companion boolean — particularly clean when `null` is a meaningful API response (recommendations).
- **Empty-state specificity matters**: one nudge card with a clear action is always better than six empty/zero sections.
- **Recharts `domain` prop** should always be set manually for rating-range data — auto-scale produces bounds that don't align with familiar reference points (CF rating brackets).
- **Horizontal bar list** is the right visualization for ranked tag data with long string labels — the alternatives (radar, vertical bar) both sacrifice either label readability or absolute values.
- **CF color ladder** belongs in the component, not a shared util, when there are only two call sites — avoid premature abstraction.

---

## Next

Phase 3 — Contest Discovery: `GET /api/v1/contests` endpoint pulling upcoming Codeforces contests, `/contests` page with a filterable list, countdown timers, and calendar export.

---

## Updates

### 2026-06-23 — QA Audit Fixes

**Heatmap tooltip label**

The tooltip rendered `{count} submissions` but `count` is `solved_count` (problems with verdict OK), not raw submission count. Changed to `{count} solved`.

**`noHandleLinked()` rewritten to use `has_verified_handle`**

The original proxy heuristic (`heatmap.length == 0 && total_solved == 0 && cf_rating == null`) false-positives for a verified user with only WA submissions. With the new `has_verified_handle` field on `DashboardResponse` (see Phase 2.2 Updates), the function now reads the flag directly:

```tsx
// Before (proxy — false-positives for all-WA users)
function noHandleLinked(d: DashboardData): boolean {
  return d.heatmap.length === 0 && d.total_solved === 0 && d.cf_rating === null;
}

// After (direct flag from backend)
function noHandleLinked(d: DashboardData): boolean {
  return !d.has_verified_handle;
}
```

`EMPTY_DASHBOARD` (used as error fallback when the fetch fails) sets `has_verified_handle: true` so a network error shows empty dashboard sections rather than the "Link your handle" nudge.

**`refreshRecommendations()` added to `_lib/analytics.ts`**

Wraps the new `POST /analytics/recommendations/refresh` endpoint. Not yet wired into a UI button — the endpoint exists and the client function is ready for Phase 3 integration.

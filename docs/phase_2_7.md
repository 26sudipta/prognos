# Phase 2.7 — Dashboard Polish & Data Audit

## What Was Built

**No new API surface or schema.** This phase was exclusively a polish + correctness pass over the dashboard built in Phase 2.4.

```
Modified files
├── frontend/app/(dashboard)/dashboard/
│   ├── page.tsx                          — layout, peak rating, refresh wiring, recTags
│   └── _components/
│       ├── activity-heatmap.tsx          — complete rewrite (GitHub-style)
│       ├── rating-chart.tsx              — hover fix, overflow chain, peak label
│       ├── stat-strip.tsx                — peak rating badge (inline, same card)
│       ├── tag-stats.tsx                 — scrollbar padding, label rename
│       ├── weakness-cards.tsx            — renamed section, priority dots, rec count
│       └── recommendations.tsx           — Refresh button, position badges restored
└── backend/app/
    ├── services/analytics.py             — streak parameter rename (clarity)
    └── workers/cf_sync.py                — recommendation randomization fix
```

---

## Concepts Explained

### 1. Recharts Hover: Why the Last Point Was Unreachable

The original `RatingChart` used a categorical `XAxis` with month/year strings as labels (`dataKey="label"`). The problem: multiple contests in the same month (e.g., three contests in "Nov '24") shared the same string label, so Recharts mapped them all to the **same X pixel position**. Only the first data point at that X position was hoverable; the rest were geometrically inaccessible.

The fix is a **sequential numeric index** as the true `dataKey`, with the label only used for display via `tickFormatter`:

```tsx
// Chart data: add a sequential idx alongside the original fields
const chartData = data.map((d, i) => ({
  ...d,
  idx: i,
  label: new Date(d.contest_time).toLocaleDateString("en", { month: "short", year: "2-digit" }),
}));

<XAxis
  dataKey="idx"          // unique integer per point
  type="number"
  domain={[0, chartData.length - 1]}
  ticks={chartData.map((_, i) => i)}
  tickFormatter={(i: number) => chartData[i]?.label ?? ""}  // display only
  interval="preserveStartEnd"
/>
```

Every contest now occupies a distinct pixel position on the X axis. All points — including peak and last — are hover-reachable.

### 2. Recharts Tooltip Overflow: The Four-Layer Chain

Recharts clips its SVG by default. A tooltip at the peak rating (top of chart) or at the last data point (right edge) would be cut off before leaving the chart box. The clipping is nested four layers deep:

| Layer | Element | Default behavior |
|---|---|---|
| 1 | Our wrapper `<div>` | `overflow: hidden` (browser default for flex/block) |
| 2 | `.recharts-responsive-container` | `overflow: hidden` set by Recharts |
| 3 | `.recharts-wrapper` | `overflow: hidden` set by Recharts |
| 4 | `.recharts-surface` (SVG) | clips at `viewBox` by default |

All four must be overridden simultaneously:

```tsx
<div
  className="[&_.recharts-responsive-container]:overflow-visible [&_.recharts-wrapper]:overflow-visible [&_.recharts-surface]:overflow-visible"
  style={{ overflow: "visible" }}
>
  <ResponsiveContainer ...>
    <LineChart margin={{ top: 60, right: 60, bottom: 4, left: 0 }}>
      <Tooltip allowEscapeViewBox={{ x: true, y: true }} />
```

`[&_.class]:overflow-visible` is Tailwind's arbitrary variant syntax — it generates a CSS rule that only applies to matching descendants of this element, without adding an extra wrapper component. The `margin` gives the chart canvas breathing room beyond the chart boundary so the SVG doesn't clip points near the edges.

### 3. GitHub Heatmap: Month Label Collision Prevention

Showing a month label requires that month to occupy at least 3 week-columns in the grid. Without this rule, a month that spans only 1–2 columns (e.g., June appears in the last 2 columns of a 52-week grid before July takes over) will collide with the next month's label.

The algorithm is a look-ahead span count — identical to GitHub's:

```typescript
function monthLabels(weeks: Cell[][]): { col: number; label: string }[] {
  const out: { col: number; label: string }[] = [];
  for (let w = 0; w < weeks.length; w++) {
    const d = new Date(weeks[w][0].date + "T12:00:00");
    const prev = w > 0 ? new Date(weeks[w - 1][0].date + "T12:00:00") : null;
    if (!prev || d.getMonth() !== prev.getMonth() || d.getFullYear() !== prev.getFullYear()) {
      let span = 0;
      for (let ww = w; ww < weeks.length; ww++) {
        const dd = new Date(weeks[ww][0].date + "T12:00:00");
        if (dd.getMonth() !== d.getMonth() || dd.getFullYear() !== d.getFullYear()) break;
        span++;
      }
      if (span >= 3) out.push({ col: w, label: d.toLocaleDateString("en", { month: "short" }) });
    }
  }
  return out;
}
```

The T12:00:00 suffix forces local-noon parsing so the date string is never shifted by timezone conversion. Without it, `new Date("2024-06-01")` parses as UTC midnight, which becomes the previous day in UTC+5:30 and later timezones.

Month labels are **absolutely positioned** within a `relative` container using `left: col * STRIDE` (where `STRIDE = CELL_SIZE + GAP = 17px`), not rendered inside the grid. This prevents the labels from affecting grid layout and guarantees alignment regardless of how many columns exist.

### 4. Peak Rating Badge — Card Height Constraint

The CF Rating card originally had 3 lines (icon+label / rating number / rank label) matching the other 3 stat cards. Adding the peak as a 4th line broke visual consistency — all four cards stretched differently.

Solution: display peak **inline on line 2**, beside the current rating number:

```
Line 1: [icon] CF RATING
Line 2: [1342]  [max 1450]     ← both on same row
Line 3: Pupil
```

The badge uses a surface-raised background with a visible border so it reads as a distinct element, not part of the rating number:

```tsx
<span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg
                  bg-bg-surface-raised border border-border-default text-[11px]">
  <span className="text-text-muted font-medium">max</span>
  <span className="font-mono font-bold" style={{ color: cfRatingColor(peakRating) }}>
    {peakRating}
  </span>
</span>
```

The badge only appears when `peakRating !== cf_rating` (i.e., the user is not currently at their peak). Showing "max 1342" when current is also 1342 would be noise.

`peakRating` is computed in `page.tsx` from `ratingHistory` (not stored separately) and passed down to `StatStrip`. The `RatingChart` also computes it locally for chart annotations. This duplication is intentional — no shared state is needed between two sibling components with different rendering goals.

### 5. Acceptance Rate: What "% solved" Really Means

The `tag_stats` table stores:

```sql
solved_count  = COUNT(DISTINCT problem_id) FILTER (WHERE verdict = 'OK')
attempt_count = COUNT(DISTINCT problem_id)
acceptance_rate = solved_count / attempt_count
```

This is **problem-level success rate**: of all distinct problems you have touched in this tag, how many did you solve? This is different from **submission-level acceptance rate** (accepted_submissions / total_submissions), which would penalize heavy trial-and-error.

Problem-level success rate is the more meaningful metric for diagnosing weakness — if you've tried 20 dp problems and solved 6, that's a pattern regardless of how many submissions each took. The label was changed from "% accepted" (implies submission-level) to "% solved" (matches the actual computation).

### 6. Focus Areas: Signal Priority vs. Signal Type

The original "Weaknesses" section labeled cards with `signal_type` badges ("Neglected", "Low Success", "Under-practiced"). Users unfamiliar with the system's internal signal vocabulary found these opaque. The redesign maps signal types to **priority levels** that communicate urgency directly:

| Signal type | Priority label | Color |
|---|---|---|
| `low_success` | High Priority | Red (#F87171) |
| `neglected` | Med Priority | Yellow (#FBBF24) |
| `under_practiced` | Low Priority | Cyan (#22D3EE) |

The original type badge ("Low Success") is kept as a small chip in the top-right of each card for users who want the technical detail. The priority dot + label at the bottom communicates the action urgency at a glance without vocabulary knowledge.

The "X problems selected" hint at the bottom of each card shows how many recommended problems correspond to that weakness tag. This connects the Focus Areas and Recommended Problems sections visually — users can see which areas have been acted on.

### 7. Layout: 70/30 Split + Centered Content

The original rating history / top tags row used a `grid-cols-5` split (3+2 = 60/40). This left too little width for the rating chart to show meaningful history while the tags section had excess empty space.

Changed to `grid-cols-10` (7+3 = 70/30). Additionally, the outer container changed from left-aligned `max-w-[1100px]` to `max-w-[1400px] mx-auto`:

- Wider max-width: better uses large monitors without sprawling on ultrawide
- `mx-auto`: centers the content block, eliminating the right-side dead space that was appearing at 1440px+ viewports

The bottom row (Focus Areas + Recommendations) uses `items-start` to prevent CSS grid from stretching shorter cards to match the taller one. Without this, if Recommendations has fewer items than Focus Areas, it still stretches to full height, which looks wrong.

### 8. Recommendation Randomization

`_pick_problem()` previously returned the **first** problem in the CF problemset that matched the tag and rating band. Since the CF API returns problems in a stable order (roughly by problem ID), this meant the same problem was always recommended for a tag until the user solved it. The Refresh button was effectively useless.

The fix collects all valid candidates first, then picks one at random:

```python
candidates = []
for p in problems:
    if tag not in p.get("tags", []):
        continue
    p_rating = p.get("rating", 0)
    if not p_rating or not (low <= p_rating <= high):
        continue
    p_id = f"{p.get('contestId', '')}{p.get('index', '')}"
    if p_id in solved_ids:
        continue
    candidates.append(p)
return random.choice(candidates) if candidates else None
```

`candidates` is built in a single pass over the problemset (already O(n)), so there's no performance cost. Each Refresh call now returns a different problem from the eligible pool.

---

## Data Audit — Full Findings

A full end-to-end audit was run across all six data paths (stat strip, heatmap, rating chart, tag stats, weakness signals, recommendations). Findings:

| # | Severity | Location | Finding | Action |
|---|---|---|---|---|
| 1 | Fixed | `cf_sync.py: _pick_problem` | Recommendations always returned first matching problem; Refresh was a no-op | Randomized via `random.choice(candidates)` |
| 2 | Fixed | `tag-stats.tsx` | "% accepted" label implied submission-level rate; metric is problem-level | Changed to "% solved" |
| 3 | Fixed | `analytics.py: _compute_streaks` | Parameter named `date_to_solved` received submission counts | Renamed to `date_to_submissions` with accurate docstring |
| 4 | No action | `activity-heatmap.tsx: totalSolvedThisYear` | Sums daily solved_count — can double-count a problem re-AC'd on multiple days | Acceptable approximation; this never happens in practice on CF |
| 5 | No action | `analytics.py: get_dashboard` | `is_syncing` checks only `LIMIT 1` handle — multi-handle users might miss the banner | Edge case; multi-handle support not yet a feature |
| 6 | No action | `analytics.py: get_tag_stats` | Tag rows not aggregated across handles — duplicate tags if user has 2 handles | Same edge case; deferred to Phase 3+ |

**Everything else verified correct:**

- `total_solved` uses `COUNT(DISTINCT problem_id WHERE verdict='OK')` — correctly deduplicates across all time ✓
- `cf_rating` = most recent `new_rating ORDER BY contest_time DESC` ✓
- `peak_rating` = `Math.max(...new_ratings)` from full history ✓
- Streak grace day: if no submission today, counts from yesterday ✓
- Rating history upsert: DELETE-then-INSERT; unique constraint `(user_handle_id, cf_contest_id)` exists since migration 004 ✓
- Heatmap color: relative to the period max via `max = Math.max(...data.map(d => d.count), 1)` ✓
- Tag stats sorted by `solved_count DESC` ✓
- Weakness signals sorted by `score DESC` — highest urgency first ✓
- Recommendation positions: 1-indexed, tied to top-5 weakness signals by score ✓

---

## Verification

```bash
# Backend: all 67 tests pass
cd backend && .venv/bin/python -m pytest --tb=short -q

# Frontend: TypeScript clean
cd frontend && npx tsc --noEmit

# Check recommendation randomization works
# Run sync, call GET /api/v1/analytics/recommendations twice after
# POST /api/v1/analytics/recommendations/refresh — problem IDs should differ
```

---

## Key Takeaways

- Recharts categorical XAxis collapses duplicate labels to the same pixel. Always use a sequential integer index when data points can share a string label.
- Recharts tooltip overflow requires fixing four independent layers (wrapper div, responsive-container, recharts-wrapper, recharts-surface). Miss any one of them and the tooltip clips.
- GitHub's month-label collision rule — span ≥ 3 columns — is the minimal rule that handles all edge cases without configuration. Implementing it exactly (look-ahead span count) is simpler than building ad-hoc collision detection.
- "% accepted" and "% solved" describe fundamentally different metrics. Submission-level acceptance measures retry behavior; problem-level success measures skill coverage. The label must match the computation.
- Randomizing recommendations requires collecting all candidates first. Returning the first match is an O(1) shortcut that silently breaks user-visible behavior (Refresh doing nothing).
- `items-start` on a CSS grid parent is the correct way to prevent shorter cards from stretching to match taller siblings. The default `items-stretch` is correct for coordinated-height layouts but wrong for independent content cards.

---

## Next

Phase 3 — Contest Discovery: browsing upcoming Codeforces rounds, filtering by division, setting reminders.

# Phase 5.1 — Insights Page (Analytics Split)

## What Was Built

The `/dashboard` page was overloaded with six sections: stat strip, heatmap, rating chart, tag stats, weakness cards, and problem recommendations. The quick-glance metrics (streaks, heatmap, rating graph) were buried alongside deep-dive analytics that require reading and deliberation. This phase splits the page in two:

- **Dashboard** → at-a-glance overview: streak stats, activity heatmap, rating trajectory
- **Insights** → dedicated analytics deep-dive: tag performance, focus areas (weakness signals), personalized practice recommendations

### File Tree

```
frontend/app/
├── (dashboard)/
│   ├── dashboard/
│   │   └── page.tsx          ← SIMPLIFIED: removed tags/weakness/recs sections
│   └── insights/
│       └── page.tsx          ← NEW: tag stats + focus areas + recommendations
└── _components/
    └── sidebar.tsx           ← UPDATED: Insights nav item added
```

No backend changes. No new components. All three components (`tag-stats.tsx`, `weakness-cards.tsx`, `recommendations.tsx`) are reused exactly as written.

---

## Concepts Explained

### 1. Why split rather than tab

One alternative was to add tabs to the dashboard page (Overview | Insights). Tabs were rejected because:

- They hide content behind a click — users who never discover the Insights tab miss the most actionable data
- A dedicated nav item gives Insights equal weight in the sidebar, making it a first-class destination
- The dashboard page's purpose becomes unambiguous: "what happened recently" not "everything"

A separate page also lets the Insights page load its own data independently, without the dashboard's stat strip and heatmap loading states blocking the weakness analysis from appearing.

### 2. What stays on Dashboard vs. what moves

| Section | Decision | Reason |
|---|---|---|
| Stat strip | **Stays** | Pure at-a-glance numbers — streak, total solved, CF rating |
| Activity heatmap | **Stays** | Visual summary of recent activity — inherently "overview" |
| Rating chart | **Stays** | Historical trajectory — a quick check, not a study |
| Tag stats | **Moves** | Requires scanning and comparing per-tag rows — a deliberate review |
| Weakness cards | **Moves** | Action-oriented — user needs to read the reason and decide what to drill |
| Recommendations | **Moves** | Directly follows from weakness analysis — belongs with it |

The rating chart was in a 70/30 grid with tag stats on the dashboard. After moving tags to Insights, the chart expands to full width — a cleaner, more readable view of rating history.

### 3. Cross-directory component imports

The `insights/page.tsx` imports components that live in `dashboard/_components/`. Both directories are under the `(dashboard)` route group, so the relative path is:

```ts
import { TagStats } from "../dashboard/_components/tag-stats";
```

This is intentional — the components were written for the dashboard but contain no dashboard-specific logic. They are pure display components that accept typed props. Moving them to a shared `_components/` directory was considered but rejected: it would be a larger refactor with no functional benefit, and the plan rule (no premature abstraction) applies.

### 4. Insights page data fetching pattern

The Insights page uses the same 3-value sentinel pattern and independent parallel fetches as the dashboard:

```
undefined = loading (show skeleton)
null      = loaded but empty (component shows its own empty state)
T         = has data (render)
```

Four fetches fire in parallel on mount:
- `fetchDashboard` — needed only for `is_syncing` and `has_verified_handle` flags
- `fetchTags` — powers Tag Performance section
- `fetchWeaknesses` — powers Focus Areas section
- `fetchRecommendations` — powers Practice Recommendations section

The polling loop (5s interval while `is_syncing=true`, then reload all sections) is duplicated from the dashboard. This is intentional — if a user is on the Insights page when a sync is running (e.g., just linked their handle), they should see the same live-updating behavior.

### 5. Sidebar placement

"Insights" is placed immediately after "Dashboard" in the nav:

```
Dashboard   (LayoutDashboard)
Insights    (Lightbulb)       ← new
Contests    (Calendar)
Handles     (Link2)
Classrooms  (GraduationCap)
```

The `Lightbulb` icon from `lucide-react` (already installed) was chosen over alternatives like `Brain` or `Sparkles` because it's unambiguous ("good idea / learn something") and doesn't imply that the AI layer is already live. `Brain` would be better once the actual AI features ship in Phase 6.

---

## Verification

```bash
cd frontend && npm run build
# Expected: 0 TypeScript errors, 0 ESLint errors
# /insights route appears as ○ (Static)

# Manual checks (npm run dev):
# 1. /dashboard → 3 sections only: stat strip, heatmap, rating chart (full width, no tag col)
# 2. /insights → 3 sections: tag breakdown | focus areas (side by side), then recommendations below
# 3. Sidebar → "Insights" visible between Dashboard and Contests
# 4. /insights Refresh button → regenerates recommendations in-place
# 5. /insights with no handle → "Link your Codeforces handle" nudge (not a blank page)
# 6. /insights while syncing → blue sync banner shown at top
```

---

## Key Takeaways

- **One page, one job.** A page that shows six unrelated sections will make users feel overwhelmed. Splitting into two pages with clear identities makes both better.
- **Don't move components — just import them differently.** `tag-stats.tsx`, `weakness-cards.tsx`, and `recommendations.tsx` required zero changes. The split was purely an orchestration concern.
- **The 3-value sentinel + parallel fetches pattern scales.** Adding a new page with four independent data sections took minimal code because the pattern was already established.

---

## Next

Phase 6 will be the AI layer (problem difficulty predictor, weakness-first recommendations, personalized practice plans). When that ships, the Insights page is the natural home for AI-generated content — and the `Lightbulb` icon in the sidebar can be upgraded to `Brain` or `Sparkles` to signal the AI capability.

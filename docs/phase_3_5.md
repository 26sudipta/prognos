# Phase 3.5 — Contest Page Redesign (Direction B: Reimagined)

## What Was Built

**User problem:** The Phase 3.4 overhaul applied surface-level polish (colors, borders, tokens) but left two core issues unresolved: (1) all contest cards read at the same visual weight regardless of urgency, and (2) the hero was structurally identical to every other card — just larger.

This phase is a structural redesign, not more polish. It addresses the root causes.

### Files Modified

```
frontend/app/_lib/contests.ts                          ← added UrgencyLane, ContestLane, groupContestsByUrgency, formatLocalDateShort
frontend/app/(dashboard)/contests/_components/
  countdown-display.tsx                                ← added isEndingSoon to CountdownState + useCountdown
  next-contest-hero.tsx                                ← full rewrite: split-panel layout + SVG arc progress ring
  contest-card.tsx                                     ← rewrite: status-based tint, badge pill, typographic weight
  contest-list-view.tsx                                ← rewrite: urgency-first swim lanes replace date grouping
  contest-calendar-view.tsx                            ← pill opacity 15%, live outline, past-day date dimming
```

---

## Concepts Explained

### 1. The Status Visual System

**Before:** Status (live/soon/upcoming) only changed a thin 3px left border color. No other visual distinction between a contest starting in 5 minutes and one starting in 3 weeks.

**After:** A consistent 5-level system applied globally:

| State | Trigger | Background tint | Left border | Badge / countdown |
|---|---|---|---|---|
| LIVE | `isLive` | `rgba(52,211,153,0.05)` | `success-400` 3px | `● LIVE` pill (green, pulsing dot) |
| ENDS SOON | `isLive && totalSeconds < 3600` | `rgba(248,113,113,0.05)` | `success-400` 3px | `Ends Soon` pill (red) |
| STARTS SOON | `isSoon` (<24h) | `rgba(34,211,238,0.04)` | `accent-400` 3px | HH:MM:SS in cyan |
| URGENT | `isUrgent` (<1h to start) | `rgba(34,211,238,0.04)` | `accent-400` 3px | HH:MM:SS in red |
| UPCOMING | default | none | `border-subtle` 2px | `Xd Yh` in muted |
| ENDED | `isEnded` | none | none | `opacity-40`, dimmed |

The color-to-semantic mapping is intentional: green = "happening now", red = "last chance", cyan = "coming soon", muted = "no urgency yet". These are universal associations — they require no legend.

A new `isEndingSoon` boolean was added to the `useCountdown` hook return value (distinct from `isUrgent` which means "< 1h to start"):

```ts
// New flag added to CountdownState
isEndingSoon: boolean;  // isLive && totalSeconds < 3600

// Previously existed:
isUrgent: boolean;      // !isLive && !isEnded && totalSeconds < 3600 (< 1h to START)
```

### 2. The Split-Panel Hero with SVG Arc

**Before:** `[countdown | vertical divider | info | button]` — a flat horizontal band. The contest name was `text-base font-semibold`. No visual difference between the hero and any list card.

**After:** The hero is a contained panel with a left arc-countdown section and a right info section, separated by a subtle hairline divider. Contest name is `text-2xl font-bold`. The platform color bleeds into the background as a gradient tint.

**The SVG arc** is a `<circle>` with `strokeDasharray = circumference` and `strokeDashoffset = circumference * (1 - progress)`. The arc starts at the 12 o'clock position via `transform="rotate(-90 cx cy)"`.

Arc progress semantics:
- **Live:** `progress = 1 - (remainingSeconds / duration_seconds)` → 0% at start, 100% at end
- **Upcoming, <24h:** `progress = (86400 - totalSeconds) / 86400` → 0% at 24h-away, 100% at start
- **Upcoming, ≥24h:** `progress = 0` → ring is empty (decorative frame only)

The `stroke-dashoffset: 0.8s linear` CSS transition smooths the per-second tick updates so the arc sweeps fluidly rather than jumping.

```tsx
// SVG arc core pattern
const RADIUS = 60;
const CIRC = 2 * Math.PI * RADIUS; // ≈ 376.99

<circle
  r={RADIUS}
  strokeDasharray={CIRC}
  strokeDashoffset={CIRC * (1 - arcProgress)} // = CIRC when progress = 0 (invisible)
  transform={`rotate(-90 ${CX} ${CY})`}       // start from top
  style={{ transition: "stroke-dashoffset 0.8s linear" }}
/>
```

### 3. Urgency-First Swim Lanes (replaces date grouping)

**Before:** Contests grouped by calendar date — "Saturday, June 28", "Sunday, June 29", etc. A user had to scan through every date group to find live or starting-soon contests.

**After:** Grouped by urgency status:
```
── LIVE NOW ──────────────────────────────  ← green, pulsing dot
   ● Codeforces Round 1044    [LIVE] →
── TODAY ─────────────────────────────────  ← cyan
   AtCoder Regular 203        in 4h 12m
── THIS WEEK ─────────────────────────────  ← muted
   ICPC Preliminary           Jul 1
── NEXT WEEK ─────────────────────────────
   ...
── LATER ─────────────────────────────────
   ...
```

The `groupContestsByUrgency` function in `contests.ts`:
- LIVE: `start ≤ now < end`
- TODAY: upcoming, `localDateKey(start) === localDateKey(now)`
- THIS WEEK: upcoming, `start ≤ sunday` (Sunday 23:59:59 of the current Mon–Sun week)
- NEXT WEEK: `start ≤ nextSunday`
- LATER: everything beyond

Empty lanes are omitted entirely. Each lane header shows the contest count on the right.

Ended contests are excluded — they no longer belong in any urgency category.

### 4. Calendar Pill Legibility

**Before:** Pills used `${color}22` (7% opacity) background on `#070B14` base — practically invisible. No weight differentiation between normal and live pills.

**After:**
- Background: `${color}26` (15% opacity) — clearly tinted on dark backgrounds
- Border: `3px solid ${color}` left (up from 2px)
- Live pills: additional `outline: 1px solid ${color}55` — visible without clashing
- Past-day numbers: `text-text-disabled` instead of `text-text-secondary` — past days recede

### 5. Compact Date Label in Cards

**Before:** `"Sat, Jun 28 · 17:35 – 19:35 · 2h"` — the `Sat, ` prefix consumed ~40px that the contest name needed.

**After:** `"Jun 28 · 17:35 – 19:35 · 2h"` via `formatLocalDateShort` (no weekday). The weekday context is already implied by the swim lane group (TODAY, THIS WEEK, etc.).

---

## Verification

```bash
cd frontend
npm run build     # must produce 0 TS errors, 0 ESLint errors
npm run dev       # visit localhost:3000/contests
```

**Visual checks:**
- Hero: left panel shows arc ring with countdown digits centered; right panel shows contest name at `2xl font-bold`
- When a contest is live: hero background has green tint; "Live Now" pill appears; arc shows elapsed %
- List view shows urgency lanes (LIVE NOW, TODAY, THIS WEEK…) not date groups
- LIVE contest card has green background tint + `● LIVE` badge pill
- STARTS SOON card (<24h) has cyan background tint + cyan HH:MM:SS countdown
- Calendar pills are clearly visible (15% opacity tint); live pills have a subtle outline ring
- Past day-numbers in calendar header are dimmed to `text-disabled`

---

## Key Takeaways

- **Root cause vs. symptoms:** The old design applied color fixes to symptoms. This redesign fixed the root cause — status information lived only in one place (border color) instead of being reinforced at card background, text weight, badge, and countdown color levels simultaneously.
- **Swim lanes flip the mental model:** Date-first grouping is a calendar idiom. Urgency-first is a priority-queue idiom — more appropriate for a discovery surface where the user's goal is "what should I register for right now."
- **SVG arcs are cheap:** The arc requires no animation library. `stroke-dashoffset` + a CSS `transition` is enough for smooth sweeping on a 1-second tick interval.
- **`isEndingSoon` vs `isUrgent`:** These are opposite ends of a contest — `isUrgent` = "< 1h to start", `isEndingSoon` = "live and < 1h to end". Both needed explicit flags because they have different semantic color meanings (cyan for approaching start, red for approaching end while live).

## Next

Phase 4 — Classroom System: `GET /classrooms`, leaderboard, invite links, cohort analytics for teachers.

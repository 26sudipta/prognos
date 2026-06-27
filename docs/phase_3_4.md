# Phase 3.4 — UI/UX Overhaul

## What Was Built

A comprehensive visual polish pass across every page. No new features, no schema changes — purely aesthetic improvements that make the interface feel premium rather than template-like.

### Files Modified

```
frontend/
├── app/
│   ├── globals.css                                       ← design token overhaul + new animations
│   ├── _components/
│   │   └── sidebar.tsx                                   ← section labels, neutral-dark bg, nav styles
│   └── (dashboard)/
│       ├── dashboard/_components/
│       │   ├── stat-strip.tsx                            ← sparkline, tighter type, streak accent
│       │   ├── activity-heatmap.tsx                      ← indigo palette, hover effect, stagger
│       │   ├── rating-chart.tsx                          ← AreaChart with gradient, mean ref line
│       │   └── tag-stats.tsx                             ← gradient bars, neutral track, tag text size
│       └── contests/_components/
│           ├── next-contest-hero.tsx                     ← live gradient tint, CTA label
│           ├── contest-card.tsx                          ← border-l-2, ended link fade
│           ├── platform-filter-chips.tsx                 ← ring-inset active state via box-shadow
│           ├── stale-data-banner.tsx                     ← slimmer, pulsing dot
│           └── contest-calendar-view.tsx                 ← dot today indicator, nav hover fix
```

---

## Concepts Explained

### 1. Why desaturate the backgrounds?

The old palette (`#070B14`, `#0F1623`, `#162032`) was explicitly nautical — it looked like a deep-sea app. Every premium dark-mode product (Linear, Vercel, Raycast) uses **desaturated neutral-dark** backgrounds: near-black with just enough blue-gray to avoid clinical coldness, without reading as "ocean".

| Token | Old | New | Why |
|---|---|---|---|
| `--bg-base` | `#070B14` | `#09090C` | Near-black, barely blue-tinted |
| `--bg-surface` | `#0F1623` | `#111116` | Cards sit visibly above base |
| `--bg-surface-raised` | `#162032` | `#18181E` | 3rd elevation level |
| `--bg-surface-overlay` | `#1C2A3F` | `#222228` | Modals/dropdowns |
| `--bg-sidebar` | (same as surface) | `#0D0D12` | Sidebar sits below the page |

The new backgrounds are still clearly dark and still clearly blue-tinted — they just don't dominate the accents anymore.

### 2. Semi-transparent borders vs. hex borders

Old: `--border-subtle: #1E2D45` — a fixed hex color that only looks good on the exact background it was designed for.

New: `--border-subtle: rgba(255,255,255,0.06)` — a fractional white overlay that works on any elevation. As cards stack (base → surface → raised → overlay), borders automatically maintain consistent *perceived* weight regardless of the background color beneath them.

This is how Linear and Radix UI themes work. It also means the border scale is future-proof: if the background colors change, the borders don't need to.

### 3. Skeleton shimmer redesign

Old skeleton: 3-stop gradient at hard 25/50/75% stops with the raised/overlay colors (both noticeably different from the surface color). The shimmer was high-contrast and visually "loud" — it drew more attention than the content it was placeholding.

New skeleton: single `rgba(255,255,255,0.03/0.07/0.03)` gradient at the same stops. The shimmer is barely visible — a suggestion of loading, not an animation competing with real content.

Also changed from `1.5s` linear to `1.4s ease-in-out` so the sweep accelerates naturally at start/end rather than marching uniformly.

### 4. Sidebar section labels

Before: flat list of 4 items — no visual grouping.

After: two sections ("Analytics" and "Tools") with a `text-[10px] text-text-disabled uppercase tracking-widest` header before each group. This:
- Establishes visual rhythm in the nav
- Prepares for future nav growth (Classroom → Tools; cohort features → Analytics)
- Matches how Linear, Notion, and Figma organize their sidebars

Active state changed from `bg-primary-500/10 text-primary-400` (colored like a brand accent) to `bg-white/[0.07] text-text-primary font-medium` (same color as body text, no accent bleed). The active page should feel *selected*, not highlighted.

### 5. Stat card micro-sparkline

The "Total Solved" card gains a 64×24px SVG sparkline showing the last 30 days of `solved` activity from the heatmap data that was already in memory. This:
- Adds motion and data density to the most important stat
- Costs zero API calls (data is re-used from `DashboardData.heatmap`)
- Uses an emerald fill gradient to echo the success/solved color scheme

The sparkline is rendered entirely as SVG `<path>` elements — no chart library, no extra imports.

### 6. Activity heatmap — indigo palette

Old colors: `["#162032", "#0d4a35", "#116b48", "#16a05b", "#10B981"]` — desaturated green on saturated navy background. The empty cells blended with the cards, and active cells looked washed out.

New colors: `["#18181E", "#1e1b4b", "#3730a3", "#6366f1", "#a5b4fc"]` — the empty cell is the new `bg-surface-raised` token; the active cells climb through indigo from barely-there to bright. On the new neutral-dark backgrounds, indigo pops far better than green.

Additional interaction improvements:
- **Hover scale**: cells scale to 1.25× on hover — tells the user they're hovering something interactive
- **Today ring**: today's cell has a permanent `ring-1 ring-accent-400/50` even when count is 0
- **Stagger entrance**: each week column animates in with a 5ms delay per column (`@keyframes cell-enter`) — a 260ms total left-to-right sweep that makes the grid feel alive on page load
- **Glassmorphism tooltip**: `bg: rgba(9,9,12,0.85)` + `backdrop-filter: blur(8px)` instead of the old flat overlay card

### 7. Rating chart — AreaChart with gradient

Changed from `<LineChart>` + `<Line>` to `<AreaChart>` + `<Area>`:
- Area fill uses a `linearGradient` from `rgba(818CF8, 0.18)` at the top to `rgba(818CF8, 0)` at the bottom
- This creates a "mountain chart" silhouette that communicates history at a glance — rating position relative to past is immediately visible
- Stroke width reduced from 2px to 1.5px — slightly more refined

Added a **mean rating reference line** (dashed gray horizontal line) when there are ≥ 3 contests. Shows the user their average alongside their peak. Implemented as a `<ReferenceLine y={meanRating}>` alongside the existing peak reference line.

Grid line color changed from `#1E2D45` (the old border hex) to `rgba(255,255,255,0.05)` — barely visible, so the chart reads as a visualization not a grid.

### 8. Contest page polish

| Component | Change | Why |
|---|---|---|
| `next-contest-hero` | Live contests get `bg: linear-gradient(135deg, rgba(52,211,153,0.05), transparent)` tint | Subtle green signal for "something is happening now" |
| `next-contest-hero` | CTA: "Register" → "Open Contest" when live | Semantic accuracy — live contests aren't registerable |
| `contest-card` | `border-l-[3px]` → `border-l-2` | Slightly thinner reads cleaner on dense lists |
| `contest-card` | Ended cards: external link `opacity-0` until `group-hover:opacity-100` | Reduces visual noise for past contests |
| `platform-filter-chips` | Active state uses `boxShadow: inset 0 0 0 1px ...` instead of `border` | Ring-inset effect without border-box interaction |
| `stale-data-banner` | Redesigned: pulsing dot + slim height + `py-2` | Less intrusive than the original with icon + border box |
| `contest-calendar-view` | Day number: `text-sm` → `text-[13px]`; today: dot below number instead of colored text | Matches Apple/Google Calendar "dot below today" pattern |

---

## Verification

Start both servers:
```bash
# Terminal 1
cd backend && .venv/bin/uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Then visit `http://localhost:3000`:

1. **Backgrounds**: page should read as near-black neutral, not navy blue
2. **Sidebar**: section labels ("Analytics", "Tools"); active item white not indigo; logo smaller
3. **Stat cards**: tight letter-spacing on numbers; sparkline on Total Solved card when data exists
4. **Heatmap**: indigo color scale; cells scale on hover; today has cyan ring; columns fade in on load
5. **Rating chart**: area gradient fill under the rating line; mean rating dashed line
6. **Tag bars**: gradient fill instead of flat color
7. **Contests > hero**: "Open Contest" label when contest is live
8. **Contests > filter chips**: ring-inset borders; `h-7` height (slightly smaller)
9. **Contests > calendar**: day number smaller; dot below today's date

Build gate (must be 0 errors before shipping):
```bash
cd frontend && npm run build
```

---

## Key Takeaways

1. **Token-first changes have massive leverage** — changing 6 CSS variables in `globals.css` improved every single page. The border rgba change alone eliminates all hard-coded elevation borders across 25+ components.

2. **Indigo heatmap reads better on neutral-dark** — saturated indigo on a neutralized background creates real contrast; green on navy blue was fighting itself. Match your accent palette to your background palette.

3. **Animations belong in global CSS** — the `@keyframes cell-enter` definition in `globals.css` means the heatmap component just applies a class name with a delay; no JavaScript animation library needed.

4. **SVG sparklines cost almost nothing** — a 64×24px SVG path drawn from 30 data points adds more visual information density than any number of typography tweaks. Always check if data you already have can be visualized.

5. **Box-shadow inset = ring-inset** — Tailwind's `ring` utility adds outline rings, but when you need per-button custom colors (platform colors), `boxShadow: "inset 0 0 0 1px ..."` gives the same result via inline style without fighting the class system.

## Next

Phase 4.1 — Classroom System: multi-user classrooms with leaderboard, cohort analytics, and invite links. See `docs/design_system.md` and `requirement.md §8`.

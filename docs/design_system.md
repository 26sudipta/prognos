# PROGNOS — Design System & UI/UX Brief
**Version:** 1.1  
**Date:** 2026-06-20  
**Audience:** Frontend implementation reference. Every decision here is final unless explicitly revised.

### Design philosophy (locked)
- **LeetCode-inspired is intentional.** Both are analytics tools for competitive programmers. Users will resonate with familiar patterns — activity heatmap, streak counter, stat cards. We take inspiration, not copy. Our data (Codeforces ecosystem, classroom system, multi-handle) is different enough that the product stands on its own.
- **No emojis anywhere in the UI.** Use icons (Lucide React) exclusively. Emojis render inconsistently across OS/browser and look unprofessional in a polished dashboard.
- **Graphs and stats are the product.** Every chart must be top-notch — smooth, labeled, interactive, and animated. A bad chart is worse than no chart.
- **Animations are required for stats.** Numbers count up. Charts draw in. Bars grow. Heatmap cells fade in sequentially. Motion communicates that data is alive and current.

---

## 1. Competitor Analysis

### 1.1 Codeforces
**What it looks like:** Web 1.0. Table-heavy, blue/white/gray, no visual hierarchy. Designed in ~2010, never meaningfully updated.  
**What works:** Nothing visual. Users tolerate it because it's the source of truth.  
**What's broken:** No analytics, no streaks, no weak-area detection, no dark mode, not mobile-friendly, raw data with zero visual processing.  
**PROGNOS opportunity:** Take their data, make it actually readable and actionable.

### 1.2 StopStalk
**What it looks like:** Bootstrap-based light theme. Submission heatmap, streak count, platform-wise stats in raw tables.  
**What works:** Multi-platform aggregation concept. Shows you the data.  
**What's broken:** Dated UI, no dark mode, cluttered layout, stats feel like a spreadsheet not a dashboard, zero gamification, no classroom/teacher features.  
**PROGNOS opportunity:** Same data but with real visual hierarchy, dark mode, and a motivating presentation.

### 1.3 LeetCode (closest to what PROGNOS should feel like)
**What it looks like:** Modern dark dashboard, streak with 🔥 icon, GitHub-style activity heatmap, circular progress rings, clean card layout.  
**What works:** Gamification (streaks feel important), visual data (heatmap is satisfying), clean typography, dark mode is default.  
**What's broken:** LeetCode-only data, no multi-platform, no classroom system, tag weakness analysis is shallow, no contest discovery.  
**PROGNOS opportunity:** Take LeetCode's visual quality + apply it to the full Codeforces ecosystem + add the classroom layer they don't have.

### 1.4 GitHub Contribution Graph
**What it looks like:** 52-week heatmap of green squares, activity density encoded in shade.  
**Why it works:** Psychologically, it makes inactivity visible — empty squares create a desire to fill them (the "don't break the chain" effect). Every serious programmer has an emotional reaction to their contribution graph.  
**PROGNOS opportunity:** Same heatmap for submissions. CP programmers will feel the same pull.

### 1.5 Reference dashboards (design quality bar)
- **Linear** (linear.app) — the gold standard for dark, clean, fast product UI
- **Vercel dashboard** — minimal, data-forward, premium feel
- **Raycast** — beautiful dark UI with great information density
- **Notion** — clean typography hierarchy

**Target feel:** If Linear and LeetCode had a child that was built specifically for competitive programmers.

---

## 2. Mood & Aesthetic

**Three words:** Focused. Polished. Motivating.

- **Focused** — no clutter, no noise. Every element earns its place. Dense information presented cleanly.
- **Polished** — premium dark theme, smooth interactions, consistent spacing. Looks like a product someone paid for.
- **Motivating** — streaks, progress rings, achievement colors. The UI should make you want to solve one more problem.

**Dark mode first.** The CP audience (aged 16-25, codes late at night) overwhelmingly prefers dark mode. Light mode can be a V2 addition. Building dark-first avoids the common trap of a bad dark mode that was retrofitted.

---

## 3. Color Palette

### 3.1 Base (backgrounds & surfaces)

| Token | Hex | Usage |
|---|---|---|
| `bg-base` | `#070B14` | Page background — deepest layer |
| `bg-surface` | `#0F1623` | Cards, panels |
| `bg-surface-raised` | `#162032` | Hover states, elevated cards |
| `bg-surface-overlay` | `#1C2A3F` | Modals, dropdowns, tooltips |
| `border-subtle` | `#1E2D45` | Card borders, dividers |
| `border-default` | `#2A3F5C` | Input borders, active dividers |

**Why deep navy, not pure black?**  
Pure `#000000` creates harsh contrast that causes eye fatigue during long sessions. Deep navy (`#070B14`) reduces strain while feeling premium — used by Linear, Raycast, and most modern dev tools. It also makes colored accents pop more than they would on pure black.

### 3.2 Primary — Indigo

| Token | Hex | Usage |
|---|---|---|
| `primary-400` | `#818CF8` | Hover states |
| `primary-500` | `#6366F1` | Buttons, links, active nav items |
| `primary-600` | `#4F46E5` | Pressed states |
| `primary-900/20` | `rgba(99,102,241,0.12)` | Subtle primary backgrounds |

**Why indigo?**  
Color psychology: indigo is associated with intelligence, focus, depth, and wisdom. It's what Notion, Linear, and GitHub use for interactive elements. It reads as "serious tool" without being cold (which blue can feel). At this saturation it's distinctive but not aggressive.

### 3.3 Success / Achievement — Emerald

| Token | Hex | Usage |
|---|---|---|
| `success-400` | `#34D399` | Streak flame, verified badge, solved count |
| `success-500` | `#10B981` | Positive delta, AC submissions |
| `success-900/20` | `rgba(16,185,129,0.12)` | Achievement backgrounds |

**Why emerald?**  
Green universally signals success, growth, and achievement. Emerald specifically (not lime, not teal) reads as premium — it's what Stripe uses for positive states. For the activity heatmap: gradient from `bg-surface` → `success-400` for density encoding.

### 3.4 Accent — Cyan

| Token | Hex | Usage |
|---|---|---|
| `accent-400` | `#22D3EE` | Contest timers, platform badges, charts secondary |
| `accent-500` | `#06B6D4` | Highlights, tag chips |
| `accent-900/20` | `rgba(6,182,212,0.12)` | Accent backgrounds |

**Why cyan?**  
Cyan reads as fast, technical, modern — the "electric" color associated with tech and speed. Good for time-sensitive elements (countdowns) and interactive chips. Pairs beautifully with indigo without clashing.

### 3.5 Warning & Danger

| Token | Hex | Usage |
|---|---|---|
| `warning-400` | `#FBBF24` | Upcoming contest (within 1 hour), lockout warning |
| `warning-500` | `#F59E0B` | Pending verification, expiring token |
| `danger-400` | `#F87171` | Wrong answer, sync error, failed verification |
| `danger-500` | `#EF4444` | Destructive actions |

### 3.6 Text

| Token | Hex | Usage |
|---|---|---|
| `text-primary` | `#F1F5F9` | Headings, important values |
| `text-secondary` | `#94A3B8` | Body text, descriptions |
| `text-muted` | `#64748B` | Timestamps, helper text, placeholders |
| `text-disabled` | `#334155` | Disabled states |

### 3.7 Rating Colors (Codeforces standard — users expect these)

| Rating range | Color | Hex |
|---|---|---|
| < 1200 | Gray | `#808080` |
| 1200–1399 | Green | `#008000` |
| 1400–1599 | Cyan | `#03A89E` |
| 1600–1899 | Blue | `#0000FF` |
| 1900–2099 | Violet | `#AA00AA` |
| 2100–2299 | Orange | `#FF8C00` |
| 2300–2399 | Orange | `#FF8C00` |
| ≥ 2400 | Red | `#FF0000` |

These are Codeforces canonical colors. **Do not deviate.** CP users have these colors burned into memory — changing them would be jarring and confusing.

---

## 4. Typography

### 4.1 Font Stack

| Role | Font | Fallback | Why |
|---|---|---|---|
| UI / Body | `Inter` | `system-ui, sans-serif` | The standard for modern dashboards. Optimized for screen readability, neutral character. Used by Linear, Vercel, Notion. |
| Display / Hero | `Inter` (700–800 weight) | same | No need for a separate display font — Inter at heavy weights is clean and strong. |
| Numbers / Stats | `JetBrains Mono` | `Fira Code, monospace` | Monospace for stats ensures digit alignment in tables and rating displays. The CP context makes mono feel natural. |
| Code snippets | `JetBrains Mono` | `Fira Code, monospace` | Same as stats — consistency. |

### 4.2 Type Scale

| Step | Size | Weight | Line height | Usage |
|---|---|---|---|---|
| `text-xs` | 12px | 400 | 1.5 | Timestamps, badges, helper text |
| `text-sm` | 14px | 400 | 1.5 | Body, table cells, secondary info |
| `text-base` | 16px | 400 | 1.6 | Primary body text |
| `text-lg` | 18px | 500 | 1.4 | Card titles, section labels |
| `text-xl` | 20px | 600 | 1.3 | Page section headings |
| `text-2xl` | 24px | 700 | 1.2 | Stat hero numbers (rating, streak) |
| `text-3xl` | 30px | 700 | 1.1 | Page titles |
| `text-4xl` | 36px | 800 | 1.0 | Landing hero |

**Stat numbers** (rating, streak count, solved count) use `JetBrains Mono` at `text-2xl` or `text-3xl` weight 700. These are the numbers users care most about — they should feel prominent and precise.

---

## 5. Layout System

### 5.1 Navigation — Left Sidebar

```
┌──────────────────────────────────────────────────┐
│ ▣ PROGNOS          [avatar] [notifications]      │ ← top bar (64px)
├────────────┬─────────────────────────────────────┤
│            │                                     │
│  nav items │   main content area                 │
│  (240px)   │   (flex-1)                          │
│            │                                     │
│  ─────     │                                     │
│  Dashboard │                                     │
│  Contests  │                                     │
│  Handles   │                                     │
│  Classroom │                                     │
│  ─────     │                                     │
│  Settings  │                                     │
│            │                                     │
└────────────┴─────────────────────────────────────┘
```

**Why sidebar over top nav?**  
PROGNOS has multiple distinct sections (Dashboard, Contests, Handles, Classroom, Settings). Top nav runs out of horizontal space quickly and forces dropdowns. Sidebar gives each section a permanent, scannable home — users always know where they are. It's what Linear, Notion, and every modern SaaS dashboard uses.

**Sidebar specs:**
- Width: 240px (expanded), 64px (collapsed — icon only)
- Background: `bg-surface` with a `border-subtle` right border
- Active item: `primary-500` text + `primary-900/20` background pill
- Collapsed on mobile (hamburger trigger)

### 5.2 Content Grid

- Max content width: `1280px`, centered
- Padding: `24px` horizontal on desktop, `16px` on mobile
- Card grid: 12-column CSS grid
- Gap: `16px` between cards

### 5.3 Card Anatomy

```
┌─────────────────────────────────┐
│ Card title          [action]    │  ← header (border-bottom)
│─────────────────────────────────│
│                                 │
│  content                        │
│                                 │
└─────────────────────────────────┘
```

- Background: `bg-surface`
- Border: `1px solid border-subtle`
- Border radius: `12px`
- Padding: `20px`
- Hover (interactive cards): `bg-surface-raised`, border → `border-default`

---

## 6. Key UI Components

### 6.1 Activity Heatmap (Dashboard)

Modeled on GitHub's contribution graph. 52 columns (weeks) × 7 rows (days).

```
Mon  ░ ░ ▒ ▓ ░ ░ ▒ ░ ▒ ▓ ...
Tue  ░ ▒ ▒ ░ ▓ ░ ░ ▓ ░ ▒ ...
Wed  ▓ ░ ░ ▒ ░ ▒ ▓ ░ ░ ░ ...
...
```

- Cell size: 12px × 12px, gap 3px
- Color scale (0 submissions → many):
  - `0` → `#162032` (surface raised — almost invisible)
  - `1–2` → `#064E3B`
  - `3–5` → `#065F46`
  - `6–9` → `#059669`
  - `10+` → `#34D399` (success-400)
- Hover tooltip: "3 submissions · Mon Jun 10"
- Month labels above, day labels left

**Psychological effect:** Empty cells are visually obvious. This creates the "don't break the chain" motivation loop — same reason people love GitHub's graph.

### 6.2 Streak Counter

```
┌─────────────────┐
│  [Flame icon]   │
│  42             │
│  day streak     │
│  ─────────────  │
│  Best: 67 days  │
└─────────────────┘
```

- Icon: Lucide `Flame` icon, `warning-400`, 28px. No emoji.
- Number: `text-3xl`, `JetBrains Mono`, `text-primary`. Animates counting up from 0 on load (600ms ease-out).
- "day streak": `text-sm`, `text-muted`
- Active streak: flame icon has a subtle CSS pulse animation (scale 1 → 1.08 → 1, 2s loop)
- If streak = 0: flame icon is `text-muted` (gray), number shows `0` — visible but desaturated (motivates restarting)

### 6.3 Rating Graph

Line chart (recharts `LineChart`):

- Line color: `primary-400`
- Area fill: gradient from `primary-500/30` (at line) → `transparent` (at bottom)
- X-axis: contest dates, `text-xs`, `text-muted`
- Y-axis: rating, `JetBrains Mono`, `text-muted`
- Dot on each data point: filled circle, colored by rating tier (Codeforces colors from section 3.7)
- Hover tooltip: contest name, date, rating change (`+125`, `-43`) with color coding
- Grid lines: `border-subtle`, dashed

### 6.4 Tag Weakness Chart

Horizontal bar chart showing solved count and success rate per tag:

```
dp          ████████████░░░░░░░░  62%  143 solved
graphs      ██████████░░░░░░░░░░  51%   89 solved
math        █████████████████░░░  84%  201 solved
strings     ████░░░░░░░░░░░░░░░░  23%   31 solved  ← highlighted red = weak
```

- Bar fill: gradient from `primary-600` to `primary-400`
- Weak tags (< 40% success rate): bar fill → `danger-500/60`, label → `danger-400`
- Strong tags (> 80%): bar fill → `success-500/60`
- Sort: by weakness (ascending) so the problem areas are at the top

### 6.5 Contest Countdown Card

```
┌──────────────────────────────────────────────────┐
│  [CF logo]  Codeforces Round #987          [⭐]  │
│                                                   │
│        02  :  14  :  37                          │
│        hr     min    sec                          │
│                                                   │
│  Duration: 2h 30min    Div. 2    Jun 21 21:35    │
│                                            [Set reminder]  │
└──────────────────────────────────────────────────┘
```

- Timer text: `JetBrains Mono`, `text-3xl`, `text-primary`
- Card border: `border-subtle` normally → `warning-400` when < 1 hour remaining
- Platform logo: small icon left of contest name
- Bookmark icon (⭐) top-right to save contest
- When contest is live: green pulsing dot + "LIVE" badge

### 6.6 Classroom Leaderboard

```
  #   Handle          Rating    Solved   Streak   Δ 7d
 ─────────────────────────────────────────────────────
  1   tourist         3979      ████      [flame] 42   +127
  2   jiangly         3891      ████      [flame] 31    +89
  3   Benq            3700      ████      [flame] 18    +45
 ...
 12   you             1547      ██░░      [flame]  3    +12  ← highlighted
```

- Rank 1–3: gold/silver/bronze left border accent
- Current user row: `primary-900/20` background — always visible even when scrolled off (sticky or highlighted)
- Rating displayed in Codeforces tier color
- Solved count: mini bar chart (sparkbar)
- Δ 7d (7-day rating change): green if positive, red if negative, `JetBrains Mono`

---

## 7. Spacing & Radius Tokens

| Token | Value | Usage |
|---|---|---|
| `space-1` | 4px | Icon gaps, tight inline spacing |
| `space-2` | 8px | Badge padding, small gaps |
| `space-3` | 12px | Input padding, nav item padding |
| `space-4` | 16px | Card internal gaps, mobile page padding |
| `space-5` | 20px | Card padding |
| `space-6` | 24px | Desktop page padding, section gaps |
| `space-8` | 32px | Large section spacing |
| `space-12` | 48px | Hero spacing |

| Token | Value | Usage |
|---|---|---|
| `radius-sm` | 6px | Badges, chips, small buttons |
| `radius-md` | 10px | Inputs, buttons |
| `radius-lg` | 12px | Cards, panels |
| `radius-xl` | 16px | Modals |
| `radius-full` | 9999px | Avatars, pill badges |

---

## 8. Component Library

**Use [shadcn/ui](https://ui.shadcn.com/) as the base.**

Why shadcn over MUI / Chakra / Mantine:
- Ships as copied source code — you own the components, no version lock-in
- Built on Radix UI primitives — fully accessible (keyboard nav, ARIA) out of the box
- Tailwind-based — our token system maps directly to Tailwind config
- Used by Vercel, many production Next.js apps
- Dark mode is a first-class citizen

**Tailwind config** will define all tokens from Section 3 as CSS variables so shadcn components automatically use our palette.

---

## 9. What Competitors Get Wrong — PROGNOS Differentiators

| Problem on existing platforms | PROGNOS solution |
|---|---|
| Raw data tables, no visual processing | Every stat gets a visual: graphs, heatmaps, bars |
| Light mode only or bad dark mode | Dark mode first, professionally designed |
| No gamification — numbers feel meaningless | Streak system, achievement colors, Δ indicators make progress feel real |
| No teacher/classroom layer | Full classroom system with cohort analytics |
| Single-platform (only LeetCode or only CF) | Multi-handle, multi-platform in V2 |
| No weakness detection — user has to figure it out | Tag analysis surfaces weak areas automatically |
| Contest discovery requires visiting each platform | Unified contest calendar |
| No explanation of what to do next | Dashboard has a "focus area" card: "Your weakest tag is `dp` — here's a problem list" |

---

## 10. Page-by-Page Layout Specs

### `/login`
- Full-screen centered layout, no sidebar
- PROGNOS logo + tagline ("Track. Analyze. Improve.")
- Single CTA: "Continue with Google" button (white bg, Google logo, black text)
- Background: `bg-base` with subtle animated gradient or particle effect (very subtle)

### `/dashboard` (main page after login)
```
Row 1: [Rating Card] [Streak Card] [Solved Total] [Rank Card]   ← 4 stat cards
Row 2: [Activity Heatmap — full width]
Row 3: [Rating Graph — 8 cols] [Tag Weakness — 4 cols]
Row 4: [Upcoming Contests — full width, horizontal scroll]
```

### `/classrooms/{id}`
```
Row 1: Classroom name, invite link button, member count
Row 2: [Leaderboard — 8 cols] [Cohort Tag Weakness — 4 cols]
Row 3: Individual student cards (expandable)
```

---

## 11. Motion & Interaction

Animations are a core part of the product — not decoration. They make data feel alive.

### 11.1 Stat number counters
Every large number (rating, solved count, streak, rank) counts up from 0 on mount.
- Duration: 800ms, `easeOut` curve
- Library: `framer-motion` with `useMotionValue` + `useTransform`, or a lightweight custom hook
- Numbers snap to final value before user can interact — no delay on interaction

### 11.2 Chart animations
- **Rating graph:** Line draws from left to right (SVG `stroke-dashoffset` animation, 1000ms)
- **Tag bar chart:** Bars grow from 0 width to full (staggered, 80ms delay per bar, 400ms each)
- **Activity heatmap:** Cells fade in row by row (staggered, 5ms per cell, opacity 0 → 1)
- **Pie/donut charts:** Rotate in from 0 (600ms, ease-out)
- All chart animations trigger once on mount, not on every re-render

### 11.3 Hover & focus states
- All interactive cards: `bg-surface` → `bg-surface-raised`, border → `border-default`, 150ms ease
- Buttons: scale(0.98) on press, scale(1.02) on hover, 100ms
- Nav items: background slides in (not just fades), 150ms

### 11.4 Page & route transitions
- Route change: outgoing page fades out (100ms), incoming page fades + slides up 8px (200ms)
- `framer-motion` `AnimatePresence` wrapping the page component in layout

### 11.5 Skeleton loaders
- Shape: exact placeholder of the real component (same dimensions)
- Animation: shimmer — gradient sweeps left to right, `bg-surface-raised` base, `bg-surface-overlay` shine
- Shown for: any data fetch > 200ms (use `React.Suspense` or loading states)
- Never show a spinner for data that has a known shape

### 11.6 Flame icon (streak)
- Active streak: CSS `@keyframes pulse` — scale 1 → 1.08 → 1, 2s infinite, ease-in-out
- No animation when streak = 0

### 11.7 Rules
- **No animation on every keystroke or scroll.** Animate on: mount, data load, user achievement.
- **Respect `prefers-reduced-motion`.** Wrap all animations: `@media (prefers-reduced-motion: reduce)` → disable or reduce.
- **Never block interaction.** Animations run in parallel with usability, never as a gate.

---

## 12. Implementation Notes for Phase 1.4

- Install: `shadcn/ui`, `tailwindcss`, `recharts` (charts), `framer-motion` (animations), `lucide-react` (icons — no emojis), `date-fns` (date formatting)
- Configure Tailwind `tailwind.config.ts` with all tokens from Section 3 as CSS custom properties
- Create `lib/tokens.ts` exporting all color/spacing tokens as JS constants (for recharts which can't use CSS vars)
- All pages use the sidebar layout from Section 5.1
- `/login` is the only page without the sidebar
- Font loading: `next/font` with Inter + JetBrains Mono (subset: latin)

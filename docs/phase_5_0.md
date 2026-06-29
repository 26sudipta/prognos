# Phase 5.0 — Marketing Landing Page

## What Was Built

A full marketing landing page replacing the bare `redirect("/dashboard")` root route. First-time visitors now land on a page that explains what PROGNOS is, lets them experience the product in under 10 seconds via a live Codeforces handle lookup widget, and presents clear conversion paths for both individual competitors and classroom instructors.

### File Tree

```
frontend/app/
├── page.tsx                                    ← REWRITTEN (was 5-line redirect)
├── _components/
│   ├── landing-navbar.tsx                      ← NEW: sticky nav with auth-aware CTAs
│   └── handle-preview-widget.tsx               ← NEW: live CF handle lookup widget
└── (auth)/
    └── login/page.tsx                          ← UPDATED: added ← Back to home link
```

---

## Concepts Explained

### 1. Why the root page needed a complete rethink

The original `page.tsx` was five lines:

```ts
// Before
import { redirect } from "next/navigation";
export default function Home() { redirect("/dashboard"); }
```

Any unauthenticated visitor hitting `/` was immediately bounced to `/login` — a bare Google OAuth button with no context. This created a hard usability problem: users had no idea what PROGNOS does, why they should sign in, or what they get after they do. The equivalent would be Google directing new users straight to Gmail's compose window.

**The fix:** Replace the redirect with a full landing page and move the auth redirect logic to where it belongs — inside `(dashboard)/layout.tsx`, which is already gated on `useAuth()`.

### 2. Market research findings that shaped the design

Before building anything, the design was derived from how successful tools in adjacent spaces handle first-time visitors:

| Platform | Pattern | Adaptation for PROGNOS |
|---|---|---|
| **AtCoder Problems** (Kenkoooo) | Handle-input widget on the hero — enter your CF handle, see your data instantly | Exact replica: the `HandlePreviewWidget` is the hero's primary interactive element |
| **Strava** | Identity-first headline ("You are a runner") before features | Hero copy leads with identity: "Train Like a Competitor" |
| **Piazza** | Two-column CTA cards split by persona (student vs. instructor) | Dual-persona cards at the bottom: Individual Solver vs. Classroom Admin |
| **WakaTime** | Public leaderboard — anyone can see top users, no account needed | Deferred to a future phase (public leaderboard) |

**Key insight from research:** Competitive programmers trust tools that let them see their own data immediately, before committing to sign-up. The handle preview widget is the single highest-ROI element on the entire page.

### 3. The HandlePreviewWidget — direct CF API call from browser

The widget calls the Codeforces public API directly from the browser:

```
GET https://codeforces.com/api/user.info?handles={handle}&checkHistoricHandles=false
```

**Why this works (CORS):** Verified via `curl` with `Origin: http://localhost:3000` header — Codeforces returns `access-control-allow-origin: *`. The API is intentionally public and permissive; it powers many browser-side CF tools.

**Why no backend proxy:** The CF API returns exactly what the widget needs (handle, rank, rating, maxRating, titlePhoto). Adding a FastAPI proxy endpoint would add latency and a backend dependency for a purely read-only, unauthenticated data display.

**State machine:**

| State | Trigger | UI |
|---|---|---|
| Empty | Initial | Input with placeholder |
| Loading | Button click / Enter key | Skeleton card (existing `.skeleton` CSS animation) |
| Success | CF returns `status: "OK"` | Avatar + rating-colored handle + rank + peak + sign-in CTA |
| Handle not found | CF returns `status: "FAILED"` | Inline red error: "Handle not found on Codeforces." |
| Network error | `fetch()` throws | Inline red error: "Could not reach Codeforces — please try again." |

**Rating color logic** mirrors `stat-strip.tsx` exactly (same Codeforces color ladder — gray → green → cyan → blue → violet → orange → red). The color is applied to the handle text, avatar border, and the rating badge background tint.

### 4. Landing Navbar — auth-aware without a page refresh

The navbar reads `useAuth()` to determine what CTA to show in the top-right corner:

```
Unauthenticated:  [Log In]  [Sign Up]  → both go to /login
Authenticated:    [Dashboard →]         → goes to /dashboard
```

This happens client-side on hydration — no server redirect, no flash. The `isLoading` guard (`{!isLoading && (...)}`) prevents a flicker where "Sign Up" briefly appears before the session-restore `POST /auth/refresh` completes.

Scroll behavior: at `scrollY > 24px`, the header switches from `bg-transparent` to `bg-bg-base/90 backdrop-blur-md` with a `border-b`. This keeps the hero's gradient glow visible on page load while providing legibility as the user scrolls past dense content.

### 5. Page section order and rationale

```
1. Hero               — Identity + handle preview (fastest path to "I get it")
2. Individual Features — Heatmap, Rating, Tag Analysis
3. Classroom Features — Leaderboard, Cohort Analytics
4. Mobile App         — Coming soon; shown early because it's a primary product
5. AI Features        — Coming soon teaser
6. Social Proof       — Stats bar + testimonials
7. Dual-Persona CTAs  — Final conversion push (Piazza model)
8. Footer CTA         — Second chance for fence-sitters
9. Footer
```

The Mobile section is placed **before** AI (§4 of the original design spec) because the mobile app is an independently shippable product. The section explicitly calls this out with Android and iOS placeholder badges (`opacity-50`, `cursor-not-allowed`, "Soon" chip). This signals "coming soon" without making a shipping promise.

### 6. Hydration safety — phone mockup heatmap

The mobile section includes a decorative phone mockup with a heatmap-style grid of colored cells. If those cell colors were generated with `Math.random()` inside the component body, SSR and client renders would produce different values, causing a React hydration mismatch.

**Fix:** Replace `Math.random()` with a hardcoded `PHONE_HEATMAP` constant array (35 integers). The same sequence always renders on both server and client:

```ts
const PHONE_HEATMAP = [3,1,4,1,5,9,2,6,5,3,5,8,9,7,9,3,2,3,8,4,6,2,6,4,3,3,8,3,2,7,9,5,0,2,8];
```

### 7. ESLint constraints and how they were handled

**`react/no-unescaped-entities`** — JSX text cannot contain raw `'`, `"`, `>`, `<`. All marketing copy was written without contractions (e.g. "do not" not "don't"). Where punctuation was unavoidable, HTML entities were used: `&apos;`, `&ldquo;`, `&rdquo;`, `&middot;`, `&amp;`, `&copy;`.

**`@next/next/no-img-element`** — CF avatar URLs are served from `*.codeforces.com` and cannot be pre-registered in `next.config.ts` because the subdomain varies per user. The `<img>` tag is the only option. The eslint-disable comment is scoped to exactly that one line:

```tsx
{/* eslint-disable-next-line @next/next/no-img-element */}
<img src={user.titlePhoto} alt={user.handle} ... />
```

**No `accent-600` token** — the design system only defines `accent-400` and `accent-500`. All CTA buttons use `bg-primary-500 hover:bg-primary-600`.

---

## Verification

```bash
# Build check
cd frontend && npm run build
# Expected: ✓ Compiled successfully, 0 TypeScript errors, 0 ESLint errors
# '/' route appears as ○ (Static) — prerendered

# CORS check for handle widget
curl -s -D - -o /dev/null \
  -H "Origin: http://localhost:3000" \
  "https://codeforces.com/api/user.info?handles=tourist" \
  | grep -i "access-control-allow-origin"
# Expected: access-control-allow-origin: *

# Manual browser checks (npm run dev at localhost:3000)
# 1. Visit /  → landing page renders; no redirect to /dashboard
# 2. Enter "tourist" in handle widget → card: Legendary Grandmaster, red-colored, ~3979 rating
# 3. Enter "invalidhandle9999xyz" → "Handle not found on Codeforces." inline error
# 4. Press Enter in the input → triggers lookup (same as button click)
# 5. "Sign Up" button → /login
# 6. Log in, visit / → navbar shows "Dashboard →" instead of "Sign Up"
# 7. /login page → "← Back to home" link visible above the card
# 8. Resize to 375px → single column, no overflow, mobile section readable
```

---

## Key Takeaways

- **Replace the redirect, not add to it.** The right fix for "no landing page" was replacing the root redirect entirely — not wrapping it in a conditional.
- **The handle widget is a trust signal, not just a demo.** A competitive programmer who enters their handle and sees their correct rating and rank in 1 second has instant proof the tool knows CF data.
- **Hydration mismatches come from non-deterministic rendering.** Any value that differs between SSR and client render (random, Date.now, window size) must be moved to a `useEffect` or replaced with a constant.
- **CORS on a third-party API is a load-bearing fact.** Always verify with `curl -H "Origin: ..."` before choosing browser-direct vs. proxy architecture.
- **Auth-aware UIs need loading guards.** Checking `isLoading` before rendering the CTA prevents a flash of "Sign Up" for already-authenticated users.

---

## Note on Social Proof Section

The social proof section (stats bar: "50K+ problems, 200+ classrooms, 150+ active streaks"; two testimonial cards) currently uses **aspirational numbers and placeholder testimonials**. These are not real user data. Before the landing page is shown to external users, replace these with:
- Real numbers from the backend (a public `/api/v1/stats` endpoint, or hardcoded bootstrapped numbers that are actually true), or
- A "Launching soon — be among the first" framing that makes no quantitative claims.

Shipping fake social proof creates trust risk with early adopters who may verify claims.

---

## Next

Phase 5.1 will be the first actual mobile work (React Native / Expo scaffold) or continued web feature work. The landing page is a standalone marketing concern and does not block Phase 5.

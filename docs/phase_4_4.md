# Phase 4.4 — Classroom System: Frontend

## What Was Built

```
frontend/app/_lib/classrooms.ts                                     ← types + API client
frontend/app/_components/sidebar.tsx                                ← Classroom nav enabled
frontend/app/(auth)/callback/page.tsx                               ← pending_join redirect
frontend/app/(dashboard)/classrooms/page.tsx                        ← list page
frontend/app/(dashboard)/classrooms/create/page.tsx                 ← create form
frontend/app/(dashboard)/classrooms/[id]/page.tsx                   ← detail orchestrator
frontend/app/(dashboard)/classrooms/[id]/_components/
  leaderboard-table.tsx                                             ← 7-column leaderboard
  invite-panel.tsx                                                  ← teacher invite management
  cohort-analytics.tsx                                              ← teacher cohort view
  member-management.tsx                                             ← teacher member list
frontend/app/join/[token]/page.tsx                                  ← public invite landing
```

---

## Concepts Explained

### 1. `undefined | null | T` Loading Sentinel

Every data section uses a 3-value sentinel instead of a separate `isLoading` boolean:

```ts
const [classrooms, setClassrooms] = useState<Classroom[] | null | undefined>(undefined);
// undefined → still loading (show skeleton)
// null      → loaded, no data (show empty state)
// T         → has data (render it)
```

**Why?** A boolean `isLoading` + data state pair has 4 logical states (loading+null, loading+data, done+null, done+data) but only two are meaningful (loading, done-with-data, done-empty). The sentinel collapses this cleanly. Conditional rendering becomes:

```tsx
if (classrooms === undefined) return <Skeleton />;
if (classrooms === null) return <EmptyState />;
return <Grid items={classrooms} />;
```

### 2. Teacher/Student Role Gates

Most UI elements are gated on `classroom.my_role`:

```ts
const isTeacher = classroom?.my_role === "teacher";
```

- Tabs: "Cohort" and "Members" tabs only render when `isTeacher`
- Invite panel: only rendered when `isTeacher && invites !== undefined`
- Action button: "Delete" for teacher, "Leave" for student
- Second `useEffect`: cohort analytics + invites are only fetched when `isTeacher`

This means students never make unnecessary API calls to teacher-only endpoints.

### 3. The Join Page: 7 Discrete States

`/join/[token]` is outside `(dashboard)` — it has no auth guard. It handles seven distinct situations:

```ts
type State =
  | { status: "loading" }
  | { status: "invalid"; errorCode: string }        // 404/EXPIRED/REVOKED from preview
  | { status: "unauthenticated"; ... }              // not logged in
  | { status: "no_handle"; ... }                   // logged in, no verified handle
  | { status: "already_member"; ... }              // server returned 409
  | { status: "ready"; ... }                       // can join
  | { status: "joining" }                          // join in progress
  | { status: "error"; message: string; ... }      // unexpected error
```

The state machine is linear: `loading → {invalid | unauthenticated | ready}`, then `ready → joining → {classrooms/{id} | no_handle | already_member | error}`. No impossible states.

### 4. Guest Intent Persistence via `localStorage`

Unauthenticated users who arrive at `/join/[token]` should be redirected to the classroom after signing in. The flow:

```
/join/{token} page loads → user not authenticated
→ localStorage.setItem("pending_join", token)
→ render "Sign in with Google" button → /login
→ Google OAuth → callback page
→ callback reads localStorage.getItem("pending_join")
→ remove key → router.replace(`/join/${token}`)
→ user is now logged in, join page runs join flow
```

**Why `localStorage` here and not for auth tokens?** Auth tokens are high-value secrets — `localStorage` is accessible to any same-origin script (XSS risk). An invite token is not a secret: it's embedded in a URL anyone with the link can see. The pending_join key only needs to survive the OAuth redirect loop; `localStorage` is perfect for that.

### 5. `fetchJoinPreview` is a Direct `fetch` Call

```ts
export async function fetchJoinPreview(inviteToken: string): Promise<JoinPreviewResponse> {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const res = await fetch(`${API_BASE}/api/v1/classrooms/join-preview/${inviteToken}`, {
    credentials: "include",
  });
  ...
}
```

`fetchJoinPreview` bypasses `apiFetch` (which injects the Bearer token) because the endpoint is public. Using `apiFetch` would inject a null/undefined Authorization header, which is harmless but misleading. Direct `fetch` is explicit about the intent.

### 6. Inline Confirm Pattern (No Modal)

Destructive actions (delete classroom, leave classroom, remove member, revoke invite) use an inline two-step confirm rather than a modal:

```tsx
{confirmDelete ? (
  <div className="flex gap-2">
    <button onClick={handleDelete}>Confirm Delete</button>
    <button onClick={() => setConfirmDelete(false)}>Cancel</button>
  </div>
) : (
  <button onClick={() => setConfirmDelete(true)}>Delete</button>
)}
```

**Why not a modal?** Phase 3 introduced framer-motion modals for rich content (contest details). Here, the confirm is just a text button pair — no additional information needed. A modal would be over-engineered.

### 7. `leaderboard-table.tsx` + Skeleton

The leaderboard table has a paired skeleton with identical column structure:

```tsx
export function LeaderboardTableSkeleton() {
  return (
    <table>
      <thead>...</thead>
      <tbody>
        {Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} />)}
      </tbody>
    </table>
  );
}
```

`SkeletonRow` uses `animate-shimmer` on placeholder divs with widths that mimic the real column content (40px for rank, 120px for handle, etc.). This prevents layout shift when real data arrives.

### 8. CF Rating Color (Duplicated by Convention)

`cfRatingColor()` is defined in `_lib/classrooms.ts` and used inline at two call sites (leaderboard table and cohort analytics). This follows the established precedent from Phase 2 (stat-strip and recommendations both have their own color logic). No central color utility — this is intentional; the function is short enough that duplication is cheaper than coupling.

---

## File Tree Summary

| File | Purpose |
|---|---|
| `classrooms.ts` | Types + 14 API functions + 3 utilities |
| `classrooms/page.tsx` | Grid of classroom cards; empty state |
| `classrooms/create/page.tsx` | Single-field form → POST → redirect |
| `classrooms/[id]/page.tsx` | Orchestrator: loads all data, renders tabs, handles delete/leave |
| `leaderboard-table.tsx` | 7-column table + shimmer skeleton |
| `invite-panel.tsx` | Generate, copy, revoke invite links |
| `cohort-analytics.tsx` | Average rating, tag lists, attendance bars |
| `member-management.tsx` | Member list with inline remove confirm |
| `join/[token]/page.tsx` | 7-state join landing (public) |
| `sidebar.tsx` | Classroom nav item enabled |
| `callback/page.tsx` | pending_join redirect after OAuth |

---

## Verification

```bash
cd frontend
npm run build
# Expected: 0 TypeScript errors, 0 ESLint errors, 11 routes listed
```

Browser smoke tests (with backend running):
1. `/classrooms` — grid of classroom cards or empty state
2. Create classroom → redirected to `/classrooms/{id}`
3. Invite panel (teacher): Generate Link → copy URL → visit in incognito
4. Join page (incognito): shows classroom name + member count + "Sign in" button
5. After sign-in: redirects back to join page → join → lands in classroom
6. `/join/{expired-token}` → "This invite link has expired."
7. Cohort tab (teacher): average rating, neglected/low-success tag lists, attendance bars
8. Members tab (teacher): remove student → row disappears immediately
9. Student "Leave" → confirm → redirected to `/classrooms`
10. Account deletion blocked (409) when owning a classroom

---

## Key Takeaways

- `undefined | null | T` sentinel is cleaner than `isLoading` + `data` pairs — one state variable, three branches.
- Guest intent in OAuth flows lives in `localStorage` (not for secrets — only for transient redirect tokens).
- Inline confirm beats modal for simple destructive actions with no additional input needed.
- Public endpoints should use raw `fetch`, not the auth-injecting `apiFetch` wrapper.
- 7 discrete state values in a discriminated union prevent impossible UI states better than boolean flags.

---

**Phase 4 complete.** Next phase: Phase 5 — Social Feed / Activity Sharing (TBD per requirement.md).

---

## Updates

### QA Audit Fixes (2026-06-30)

Two bugs found in the join page during post-implementation review:

**1. Session-restore race condition (`user` missing from `useEffect` deps)**

`useAuth()` populates `authToken` and `user` in two separate React state updates. On page load with an existing session (restore via refresh cookie), `authToken` can become truthy before `user` is populated. The `useEffect` ran with `!user === true` and set state to `"unauthenticated"`. Since neither `inviteToken` nor `authToken` changed after `user` populated, the effect never re-ran, leaving the user stuck on the sign-in prompt even though they were logged in.

Fix: added `user` to the dependency array:
```ts
// Before (suppressed with eslint-disable):
}, [inviteToken, authToken]);

// After:
}, [inviteToken, authToken, user]);
```

**2. Dead `classroomId: ""` field in `already_member` state**

The `already_member` discriminated union state carried a `classroomId: string` field that was always set to `""`. The "Go to My Classrooms" button routed to `/classrooms` regardless — it never used `classroomId`. This was dead code that made the type misleading.

Fix: removed `classroomId` from the `already_member` state type entirely.

**auth service fix (also from this audit):** `soft_delete_user` did not clean up student memberships or leaderboard rows. After account deletion, a user's cached stats (including their handle and rating) remained visible on classroom leaderboards indefinitely. Fixed by adding:
```python
await db.execute(delete(ClassroomLeaderboard).where(ClassroomLeaderboard.user_id == user_id))
await db.execute(delete(ClassroomMembership).where(ClassroomMembership.user_id == user_id))
```
before `await db.commit()` in `soft_delete_user`. The owner-classroom guard (409) runs first, so these deletes only apply to student memberships.

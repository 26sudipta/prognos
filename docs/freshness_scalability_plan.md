# PROGNOS — Data Freshness & Scalability Master Plan
**Status:** Reference / Future — not scheduled for implementation. A north-star design doc.
**Author intent:** written as a staff/principal-level system design so future-self (or any
engineer) can execute it incrementally without re-deriving the reasoning.

> When this gets built, split each layer into its own `phase_X_Y.md` as it ships (per
> CLAUDE.md §5.2). Build **one vertical slice at a time** — the roadmap at the bottom is
> ordered by value-per-effort, not by architectural tier.

---

## 1. Goals & Non-Goals

**Goal 1 — Freshness:** a user looking at their dashboard sees data that reflects their
Codeforces activity within minutes, ideally seconds for active users.

**Goal 2 — Scale:** the platform serves from thousands to (eventually) millions of users
without the freshness guarantee or the request latency degrading. Cost grows sub-linearly
with users (dormant users must be nearly free).

**Non-goals (be honest about these):**
- True real-time push from Codeforces — **CF has no webhooks**. All ingestion is polling,
  bounded by CF's ~1 request / 2 seconds limit. "Real-time" can only mean *we detect the
  change fast and push it to the open client*, never *CF tells us*.
- Rewriting the read path — it is already correct: clients read pre-computed projections
  (`daily_activity`, `tag_stats`, `rating_history`, leaderboards). That design is the reason
  scaling reads is easy. We preserve it.

---

## 2. The Two Independent Problems

Freshness and scale are **different axes** and must not be conflated:

| | Freshness problem | Scale problem |
|---|---|---|
| Bottleneck | CF rate limit + sync latency | DB connections, queue depth, web throughput |
| Binding resource | External API budget (1 call / 2s) | CPU, connections, Postgres write IOPS |
| Fix shape | *When* and *how often* we sync | *How many* parallel workers / replicas / shards |
| Failure mode | Stale dashboards | 500s, connection exhaustion, CF bans |

The architecture below solves them with **one shared chokepoint** (a CF gateway with a global
token bucket) so that adding freshness can never accidentally breach the rate limit and get
the whole platform banned. **That gateway is the keystone — build it first.**

---

## 3. Freshness Strategy — a tiered model

Freshness is a spend of a scarce, shared budget (CF API calls). Spend it where a human is
actually looking, and on users who actually changed. Five tiers, cheapest-first:

### Tier 0 — Global CF Gateway + token bucket (PREREQUISITE for everything)
All CF traffic funnels through one place (`_cf_get` today). Wrap it in a **global, Redis-backed
token bucket** (~1 token / 2s, small burst capacity) so every CF call across every worker is
throttled centrally. Without this, every freshness improvement below is a foot-gun that ends
in a CF ban. Degrade gracefully to a local 2s sleep if Redis is down. As scale grows, promote
this from a helper into a **dedicated CF-gateway service/queue** (single point that owns the
CF budget, exposes priority lanes, and emits 429/latency metrics).

### Tier 1 — Sync-on-view (lazy refresh) — the highest-leverage move
Freshness only matters when a human is looking. On dashboard load, if the handle's
`last_synced_at` is older than a threshold (~5–10 min), enqueue a sync and return
`is_syncing=true`. The frontend already polls every 5s and auto-reloads on completion
(Phase 2.6) — so this is nearly free to wire and **spends zero API budget on dormant users**.
Key it off `last_synced_at`, kept separate from the manual button's `last_manual_sync_at`
cooldown so user and auto syncs don't fight. Because `_fetch_submissions` is incremental
(cursor on `max(cf_submission_id)`), an on-view re-sync is ~2 CF calls and usually 0 new rows.

### Tier 2 — Adaptive background frequency (replace the flat 6h beat)
Stop syncing everyone every 6h. Sync by recency of activity:

| Cohort | Definition | Cadence |
|---|---|---|
| Hot | submitted in last 48h, or session active now | every 15–30 min |
| Warm | submitted in last ~2 weeks | every 2–6 h |
| Cold/dormant | nothing recent | every 24 h (or only on-view) |

This concentrates the fixed API budget on the few thousand users who are actually grinding.
Cohort is a cheap query on `daily_activity`/`last_synced_at`; the beat enqueues per-cohort.

### Tier 3 — Event-driven sync bursts
You already ingest the contest calendar (`contests` table). When a contest a user participated
in ends, CF publishes new ratings ~1–2h later. Schedule a **targeted sync wave** for affected
handles right after that window — the moment freshness matters most (rating change day). This
is precise spend: a handful of calls at exactly the right time, not a blanket re-sync.

### Tier 4 — Push freshness to the open client (perceived real-time)
Once a sync writes new data, push it to any **currently-open** dashboard via **SSE or
WebSocket** instead of 5s polling. We never get push *from* CF, but we give the user push-feel
*from us* the instant our sync lands. Polling is fine until concurrent open sessions make it
wasteful; SSE scales better and removes the 5s latency floor.

**Net effect:** active viewers ≈ seconds-fresh (Tier 1 + Tier 4), recently-active users
minutes-fresh in the background (Tier 2), rating days handled precisely (Tier 3), dormant
users cost almost nothing — all under one rate-limit ceiling (Tier 0).

---

## 4. Scalability Architecture — scale each tier independently

### 4.1 Web / API tier — horizontal, stateless
Already stateless (JWT, no server sessions) → just run N replicas behind a load balancer. No
sticky sessions needed. This is the easy axis; reads are cheap pre-computed lookups.

### 4.2 Database — the real ceiling, attacked in layers
1. **Connection pooling via PgBouncer (transaction mode).** Today each web process uses
   SQLAlchemy's default ~15-conn pool; Postgres caps ~100 conns. PgBouncer lets hundreds of
   app processes share a small real-connection set — the single highest-leverage scale fix.
2. **Read replicas.** Route all dashboard/leaderboard reads to replicas; keep the primary for
   sync writes. Reads vastly outnumber writes here, so this buys a lot of headroom.
3. **Partition the hot tables.** `submissions` grows unbounded and is the write-heavy table —
   partition by time (range) or by handle (hash). Keeps indexes small and writes local.
4. **Hot-read cache.** Redis cache for the dashboard/leaderboard JSON with short TTL +
   invalidate-on-sync. Turns repeated dashboard opens into O(1) Redis hits, sparing Postgres.

### 4.3 Sync / worker tier — shard and prioritize
1. **Multiple Celery workers, sharded** by `hash(handle_id) % N` so the active-user set
   spreads across workers — but the CF gateway (Tier 0) still globally caps total CF rate.
2. **Priority queues at the gateway:** on-view/interactive syncs jump ahead of bulk background
   syncs. A user staring at a spinner must not wait behind a 10k-handle nightly sweep.
3. **Split fast vs deep sync.** Fast path (submissions → daily_activity → rating_history) is
   what freshness needs — keep it ~2 CF calls and run it often. Deep path
   (`_compute_weakness_signals`, `_generate_recommendations`, leaderboard rebuilds) is
   CPU/DB-bound, not freshness-critical — run it less often / decoupled. This keeps the
   frequent path cheap, which is what makes high-frequency syncing affordable.
4. **Idempotency + backpressure.** Syncs are already idempotent (cursor + upserts); add a
   per-handle in-flight lock (Redis `SET NX`) so a flood of on-view triggers can't enqueue
   duplicates. Queue depth is the backpressure signal — shed/delay cold-tier work first.

### 4.4 Observability (you cannot scale what you cannot see)
Track and alert on: **sync lag** (now − `last_synced_at`, p50/p95 per cohort), **queue depth**
per priority lane, **CF 429 / call-budget utilization**, DB connection saturation, replica
lag. Sync-lag p95 is the single best health metric for the freshness SLO.

---

## 5. Capacity ladder — what to do at each scale

| Users (verified/active) | State of the system | Action |
|---|---|---|
| **≤ 1k** | Single web + single worker, default pool, flat 6h beat | Add **Tier 0 gateway + Tier 1 on-view**. Done. |
| **1k–10k** | One worker nears its 6h-sweep limit | Add **Tier 2 adaptive cadence**, **PgBouncer**, fast/deep split, per-handle lock |
| **10k–100k** | Reads pressure Postgres; sync budget tight | **Read replicas**, **hot-read Redis cache**, **sharded workers + priority queue**, **Tier 3** event sync |
| **100k–1M+** | Write volume + concurrency dominate | **Partition `submissions`**, dedicated CF-gateway service, **Tier 4 SSE push**, autoscale web replicas, regional considerations |

Each step is additive and independently shippable — never a big-bang rewrite. The read-model
design means none of these touch client code.

---

## 6. Failure modes & mitigations (design for them up front)

| Failure | Mitigation |
|---|---|
| CF ban from over-syncing | Tier 0 global token bucket is the hard ceiling; alert on 429 rate |
| Redis down | Gateway degrades to local 2s sleep; cache misses fall through to DB |
| Thundering herd of on-view triggers | Per-handle in-flight lock + staleness gate + idempotent upserts |
| Sync lag balloons under load | Priority queues protect interactive syncs; shed cold-tier work via backpressure |
| DB connection exhaustion | PgBouncer transaction pooling; reads on replicas |
| Worker crash mid-sync | Already safe — incremental cursor + upserts make re-runs idempotent |

---

## 7. Recommended build order (value-per-effort)

1. **Tier 0 — global CF gateway/token bucket** (prerequisite; small).
2. **Tier 1 — sync-on-view** (huge UX win; reuses Phase 2.6 polling; small).
3. **PgBouncer + per-handle in-flight lock** (cheap scale insurance).
4. **Tier 2 — adaptive background cadence** (replaces flat beat).
5. **Fast/deep sync split** (unlocks cheap high-frequency syncing).
6. **Read replicas + hot-read Redis cache** (scale reads).
7. **Sharded workers + priority queue** (scale sync).
8. **Tier 3 — post-contest event sync**.
9. **Tier 4 — SSE/WebSocket push** (perceived real-time).
10. **Partition `submissions` + dedicated gateway service** (six-figure-user territory).

Steps 1–2 are the original "fresh-on-view" slice and deliver most of the felt freshness for a
fraction of the work. Everything after is scale headroom, added only when metrics demand it.

---

## 8. Open decisions to revisit when implementing
- Exact on-view staleness threshold (start 5–10 min; tune from sync-lag metrics).
- Token-bucket capacity/burst vs strict 1-per-2s (confirm CF's current documented limit first).
- SSE vs WebSocket for Tier 4 (SSE simpler for one-way server→client updates).
- Partition key for `submissions`: time-range vs handle-hash (depends on query shape at scale).
- When to extract the CF gateway into its own deployable service vs keep it an in-process lib.

# PROGNOS — Endgame Architecture ("Max Plan")
**Status:** North-star reference — execute phase-by-phase (M0→M5), never big-bang.
**Scope:** any concurrent users · 100k+ active users · max read speed · max data freshness · paid cloud.
**Supersedes:** `freshness_scalability_plan.md` (its Tiers 0–4 are incorporated here).
**Unchanged foundations:** the read-model design (clients read pre-computed projections), the
trust model ("client triggers, server fetches" — Phase 5.2), JWT statelessness, UTC discipline.
Those decisions are already the load-bearing walls; this plan builds on them, not over them.

---

## 1. The Two Laws (everything below derives from these)

**Law 1 — Serving scales with money.** Reads are O(1) lookups of pre-computed projections.
CDN + cache + replicas + partitions buy effectively unlimited concurrent readers. Any
concurrency target is reachable by turning dials that cost dollars, not redesigns.

**Law 2 — Ingestion does not scale with money.** Codeforces has **no webhooks** and enforces
**~1 request / 2 s per IP**. No fleet of servers raises that number. Freshness at scale is won
three ways only:
1. **Intelligence** — spend the fixed budget exactly where a human is looking (tiers, priorities, events).
2. **Client-assisted fetch** — each user's browser has its *own* IP budget for its *own* data
   (personal-only until server-confirmed; the Phase 5.2 trust model stays intact).
3. **Partnership** — at genuine 100k scale, request elevated API access from Codeforces.
   That is the legitimate lever. **IP rotation is explicitly rejected** — it is a ToS/ban
   risk that gambles the entire platform.

A "max plan" that pretended servers could out-muscle Law 2 would be a worse plan, not a better
one. This plan is maximal *because* it respects the physics.

---

## 2. SLOs — "fast" and "fresh" as numbers

No SLO, no engineering. Every mechanism in §5–§6 exists to hit a row in this table; every row
has an alert in §7.

| # | SLO | Target | Primary mechanism |
|---|---|---|---|
| S1 | API p99, cached reads | < 200 ms | Redis hot-read cache (§5.2) |
| S2 | Dashboard TTFB, global | < 100 ms static / < 300 ms data | CDN + edge (§5.1) |
| S3 | Freshness — actively viewed own dashboard | < 30 s | sync-on-view + client-assisted fetch (§6.3) |
| S4 | Freshness — hot users, background | < 15 min | adaptive cadence, hot lane (§6.2) |
| S5 | Freshness — post-contest rating day | < 30 min after CF publishes | event waves (§6.4) |
| S6 | Leaderboard staleness while viewed | < 5 s from data landing | SSE push (§6.5) |
| S7 | Availability | 99.9% monthly | multi-AZ, autoscaling, load-shedding (§7) |
| S8 | Durability | RPO ≤ 5 min, RTO ≤ 1 h | PITR + tested restore (§7.1) |

---

## 3. The 100k-Active Budget Math (the honest core)

One IP: 1 call / 2 s → **43,200 CF calls/day**. A fast incremental sync ≈ **2 calls**
(`user.status` page-1 cursor check + `user.rating` when needed) → **~21,600 server
syncs/day/IP**. A flat daily sweep of 100k actives needs 200k calls/day — **4.6× over budget.
Impossible on one IP. Non-negotiable.** Therefore the budget must be *allocated*, and personal
freshness must come from somewhere other than the server IP:

| Cohort | Size (of 100k) | Personal-dashboard freshness | Server spend | Server syncs/day |
|---|---|---|---|---|
| **Hot** (active ≤ 48 h) | ~10k | **Client-assisted fetch** on view (their IP, seconds-fresh) | 1 confirm/day (leaderboard integrity) | 10,000 |
| **Warm** (active ≤ 14 d) | ~30k | on-view (server) when they look | 1 sync / 3 days | 10,000 |
| **Cold** (rest) | ~60k | on-view (server) only | on-view only (est.) | ~1,000 |
| **Total** | 100k | | | **~21,000 ≤ 21,600 ✓** |

Read the table honestly: **it fits only because client-assisted fetch carries hot-user personal
freshness** (S3) while the server budget is reserved for what *must* be authoritative — the
leaderboard confirmations (Phase 5.2 trust model) — plus event waves on contest days (borrowed
from the warm/cold lanes, since freshness demand is event-shaped, not uniform). Remove
client-assisted fetch and hot users alone (10k × even 4 syncs/day = 40k) blow the budget.

**Contest days:** a rated round touches a large slice of hot+warm at once. The event lane (§6.4)
pre-empts warm/cold background spend for the 2–3 h after CF publishes ratings — precisely when
humans check. This is the highest-leverage single spend in the whole system.

**The partnership step (M5):** at demonstrated 100k scale with a clean citizen record (single
gateway, zero 429 abuse — §6.1 produces exactly this evidence), request elevated access from
Codeforces. Every serious CF-ecosystem tool that survived did this or stayed small.

---

## 4. Target Architecture

```
                        ┌────────────────────────────────────────────────┐
   Users (global)       │                    CDN / Edge                  │  static, cached JSON,
      │                 │        (CloudFront / Cloudflare + WAF)         │  DDoS absorb
      ▼                 └───────────────┬────────────────────────────────┘
 Next.js (Vercel or ECS)                │ /api/*
                        ┌───────────────▼────────────────┐
                        │   API fleet — FastAPI, stateless│  N× autoscaled containers
                        │   (ECS Fargate, ALB in front)   │  JWT auth, no sessions
                        └───┬──────────────┬──────────────┘
                            │              │
                ┌───────────▼───┐   ┌──────▼──────────────────────┐
                │ Redis cluster │   │ PgBouncer / RDS Proxy       │
                │ • hot-read    │   │        │                    │
                │   JSON cache  │   │ ┌──────▼──────┐  ┌────────┐ │
                │ • token bucket│   │ │ Postgres    │→ │ read   │ │
                │ • queues      │   │ │ primary     │  │replicas│ │
                │ • locks       │   │ │ (partitioned│  └────────┘ │
                └───────┬───────┘   │ │ submissions)│             │
                        │           │ └─────────────┘             │
        ┌───────────────▼─────────────────┐        ┌──────────────▼─────────┐
        │ Worker fleet (Celery, autoscaled)│        │ SSE push gateway       │
        │ priority lanes:                  │        │ (fan-out sync results  │
        │ interactive > event > hot > warm │        │  to open dashboards/   │
        │ > cold ; fast/deep split         │        │  leaderboards)         │
        └───────────────┬─────────────────┘        └────────────────────────┘
                        │  every CF call, no exceptions
                ┌───────▼────────────────────┐
                │ CF GATEWAY (the keystone)  │  global token bucket (1/2s + small burst),
                │ sole owner of the CF budget│  priority lanes, per-handle in-flight locks,
                └───────┬────────────────────┘  429/latency/budget-utilization metrics
                        ▼
                  codeforces.com API          Observability: metrics + traces + logs
                                              (Prometheus/Grafana or CloudWatch, Sentry)
```

**Reference stack — AWS default** (chosen for depth of managed services; the shape is
cloud-agnostic — containers + Terraform make the whole thing portable):

| Component | AWS (recommended) | GCP equivalent | Azure equivalent |
|---|---|---|---|
| CDN + WAF | CloudFront + AWS WAF | Cloud CDN + Armor | Front Door + WAF |
| Next.js | Vercel (keep) or ECS | Vercel or Cloud Run | Vercel or Container Apps |
| API + workers | ECS Fargate | Cloud Run | Container Apps |
| Postgres | Aurora PostgreSQL | AlloyDB / Cloud SQL | Flexible Server |
| Conn pooling | RDS Proxy | built-in pooler | PgBouncer sidecar |
| Redis | ElastiCache | Memorystore | Azure Cache |
| Queue | Celery/Redis (start) → SQS | Cloud Tasks | Storage Queues |
| Secrets | Secrets Manager | Secret Manager | Key Vault |
| IaC / CI-CD | Terraform + GitHub Actions | same | same |

**Deliberate simplicity:** one API service + one gateway service + a worker pool. **No
Kubernetes** until team size (not user count) demands it — Fargate/Cloud Run deliver autoscaling
without the ops tax. **No microservices explosion** — at 100k users this system is, honestly, a
medium-sized workload; the CF budget is the hard problem, not compute.

---

## 5. Speed Layer — reads as fast as possible (Law 1)

### 5.1 Edge (S2)
Static assets and the marketing page from CDN. API responses get `Cache-Control` + `ETag`
(contests list, public join-preview are trivially edge-cacheable; per-user endpoints are not —
they hit the Redis layer instead). Single region + CDN first; **multi-region read-only replicas
are a labeled future step** (only if a measured user base outside the home region justifies it —
not before, cross-region replication is real complexity).

### 5.2 Hot-read cache (S1)
Redis JSON cache for the four hot endpoints (dashboard, leaderboard, tags, rating-history):
key `dash:{user_id}` / `lb:{classroom_id}`, TTL 60 s, **invalidate-on-sync** (the sync worker
deletes the key after recompute — the moment data changes, the next read rebuilds the cache).
Turns repeat opens into O(1) Redis hits; Postgres sees only cold reads. This also replaces the
Phase 5.2 `populate_existing` read-path rebuild pressure at scale.

### 5.3 Database (the real ceiling, attacked in order)
1. **PgBouncer/RDS Proxy, transaction mode** — hundreds of app containers share a small real
   connection set. The single highest-leverage DB dial; do it before adding the second API replica.
2. **Read replicas** — dashboards/leaderboards read replicas; the primary is reserved for sync
   writes. Reads outnumber writes enormously here.
3. **Partition `submissions`** — the only unbounded write-heavy table. **Hash by
   `user_handle_id`** (every query in `cf_sync.py` and the projections filters by handle —
   partition pruning hits exactly one partition; time-range would spray every handle's queries
   across all partitions). 32 partitions carries 100k users comfortably.
4. Keep covering indexes as-is (`(user_handle_id, cf_submission_id)`, `(user_handle_id,
   submitted_at DESC)` — already correct).

---

## 6. Freshness Layer — data as fresh as possible (Law 2)

### 6.1 CF Gateway — the keystone, built first (M0)
Every CF call from every process goes through one chokepoint (today that is `_cf_get` in
`app/workers/cf_sync.py` — it becomes a thin client of the gateway):
- **Global Redis token bucket**: 1 token/2 s, burst ≤ 5. Degrades to a local 2 s sleep if Redis
  is down (never fail open).
- **Priority lanes**: `interactive > event > hot > warm > cold`. A human staring at a spinner
  never waits behind a 10k-handle sweep.
- **Per-handle in-flight lock** (`SET NX`, TTL): a flood of on-view triggers enqueues one sync,
  not fifty. (Extends the Phase 5.2 `IN_PROGRESS` pre-mark with a real distributed lock.)
- **Telemetry**: budget utilization, 429 count, per-lane latency — this is both the ops dashboard
  and the *evidence file* for the CF partnership request (§3).
Starts as an in-process library; extracted into a dedicated service in M4 when workers shard.

### 6.2 Adaptive cadence (S4) — replace the flat sweep (M2)
Cohort assignment is a cheap query over `daily_activity`/`last_synced_at` (hot ≤ 48 h,
warm ≤ 14 d, cold otherwise). The scheduler enqueues per-cohort at the §3 rates into the
matching gateway lane. Dormant users cost ~zero — cost grows with *activity*, not registrations.

### 6.3 Client-assisted personal fetch (S3) — the parked idea, promoted (M5)
The user's original insight, now integrity-safe:
- Browser fetches **its own** `user.status` delta directly from CF (CORS verified open; the
  landing widget already does this) and POSTs it with `source='client'`.
- It renders **only on the owner's personal dashboard** — worst case you lie to yourself.
- **Leaderboard/cohort read only server-confirmed rows.** The daily hot-cohort confirm (§3)
  flips genuine rows to `source='cf_api'` via upsert; fabricated `cf_submission_id`s are never
  confirmed and never surface competitively. Submissions stay **append-only** — the Phase 5.2
  analysis (client writes can't erase forgeries; destructive-replace enables deletion attacks)
  holds; this design never lets client data cross the trust boundary.
- Net effect: hot users see **seconds-fresh** own data at **zero server CF spend** — the line
  item that makes the §3 table balance.

### 6.4 Event-driven contest waves (S5) — highest leverage per call (M4)
The `contests` table already knows when every round ends. ~60–90 min later, CF publishes
ratings. The scheduler queries participants among our handles (post-contest `user.rating`
delta check, batched) and floods the **event lane** — precise spend at the exact moment
freshness matters most, pre-empting warm/cold background work for that window.

### 6.5 SSE push (S6) — kill polling (M4)
Today the dashboard and classroom pages poll every 5 s (fine at hundreds of users, wasteful at
thousands). A small SSE gateway subscribes to Redis pub/sub; the sync worker publishes
`{handle_id}` / `{classroom_id}` on completion; open pages receive the nudge and refetch once.
Removes the 5 s latency floor and ~all idle polling load in one step. SSE over WebSocket:
one-way server→client is all this needs, and SSE survives proxies/CDNs with zero protocol ops.

### 6.6 Fast/deep sync split (enables high frequency)
Fast path (submissions → `daily_activity` → rating): ~2 CF calls + cheap SQL — run at cohort
frequency. Deep path (`_compute_weakness_signals`, `_generate_recommendations`, leaderboard
rebuild): CPU/DB-bound, zero CF calls, not freshness-critical — run at most 1–2×/day per user or
on-demand. High-frequency syncing is affordable *because* the frequent path is the cheap one.

---

## 7. Reliability, Security, Operations

### 7.1 Reliability (S7, S8)
- **Multi-AZ** everything (Aurora, ElastiCache, ≥2 API tasks across AZs). Single region until
  measured geography says otherwise.
- **Backups**: PITR (RPO ≤ 5 min); restore **tested quarterly** — an untested backup is a rumor.
- **Load-shedding order** (automated, queue-depth triggered): cold sync → deep recompute → warm
  sync → *never* interactive reads or interactive syncs. Freshness degrades gracefully;
  availability does not.
- **Worker crash mid-sync**: already safe — incremental cursor + idempotent upserts make re-runs
  free (this property is why the whole worker tier can autoscale carelessly; preserve it in code
  review as an invariant).
- **Deploys**: blue-green on ECS; migrations expand-then-contract (never breaking-in-place).

### 7.2 Security
WAF (managed rules + per-IP rate limits) at the edge; per-user API rate limits at the ALB/app
layer; secrets in Secrets Manager (no env-file secrets in images); least-privilege IAM per
service; refresh-token model unchanged (httpOnly, hashed, rotated — already right).

### 7.3 Observability — you cannot scale what you cannot see
| Signal | Alert when |
|---|---|
| **Sync-lag p95 per cohort** (now − `last_synced_at`) — THE freshness SLI | hot > 30 min (S4), post-contest > 45 min (S5) |
| CF budget utilization / 429 count | > 85% sustained / any 429 spike |
| Queue depth per lane | interactive lane non-empty > 60 s (S3) |
| API p99, error rate | > 200 ms (S1) / > 0.5% |
| DB: connection saturation, replica lag | > 80% / > 10 s |
| Cache hit ratio (hot-read) | < 90% |
Plus Sentry for exceptions and a runbook per alert (CF-ban response, Redis loss, replica
failover, queue flood).

---

## 8. Migration Roadmap — each phase independently shippable

| Phase | Scope | Exit criteria | Rough cost/mo |
|---|---|---|---|
| **M0** | Paid Redis; re-enable Celery (`enqueue_sync` already prefers it); **Tier-0 token bucket + per-handle locks** in `_cf_get` | Sync durable & retryable; CF-ban risk closed; 429s ≈ 0 | ~$20–50 |
| **M1** | API containers on paid compute ≥2 replicas + ALB; managed Postgres + PgBouncer/RDS-Proxy; Terraform + CI/CD; keep Vercel frontend | 5k concurrent browsers, p99 < 300 ms; zero cold starts | ~$150–400 |
| **M2** | Adaptive cadence + fast/deep split + priority lanes + autoscaled workers | 25k actives within cohort SLOs on one IP | ~$250–600 |
| **M3** | Read replicas + Redis hot-read cache (invalidate-on-sync) + CDN in front of API | 50k concurrent reads; S1/S2 met; primary DB write-only-ish | ~$500–1,200 |
| **M4** | SSE push gateway + event contest waves + CF Gateway extracted as service | S5 + S6 met on a real contest day | ~$700–1,500 |
| **M5** | Partition `submissions` (hash by handle) + **client-assisted personal fetch** + CF partnership request (with M0–M4 telemetry as evidence) | **100k actives inside the §3 budget table; S3 seconds-fresh for hot users** | ~$1.5k–4k |

**Rollback story:** every phase is additive behind config (broker URL, cache on/off, lane
weights, partition attach). M0's token bucket degrades to local sleep; M3's cache can be
flushed and bypassed; M5's client-assist is a frontend flag. Nothing is a one-way door except
the DB migration to partitions — which is why it is last and rehearsed on a restore first.

---

## 9. Anti-Goals — what "no better plan" deliberately excludes

- **No microservices explosion.** API + CF-gateway + workers + push gateway. Four deployables at
  100k users. Every additional service is a tax paid monthly.
- **No Kubernetes** until the *team* (not the traffic) outgrows Fargate/Cloud Run.
- **No multi-region writes.** Read-only edge/replicas at most. Write-multi-region is a
  different sport with costs this product never needs to pay.
- **No IP rotation / rate-limit evasion.** One clean gateway + partnership. The platform's
  existence is worth more than any freshness increment.
- **No big-bang rewrite.** FastAPI + Postgres + Redis carries this to 100k+ actives. The
  bottleneck was never the framework; it is the CF budget, and §3/§6 spend it optimally.
- **No trust-model regressions.** Client data never reaches a competitive surface unconfirmed —
  under any future feature pressure.

## Next
Execute **M0** first (token bucket + locks + Celery-on-paid-Redis) — small, cheap, and the
prerequisite that makes every later phase safe. Write `docs/phase_X_Y.md` per shipped slice as
usual (CLAUDE.md §5.2).

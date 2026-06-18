# CodeStats — Unified Competitive Programming Analytics & Planning Platform  
**Project Report (Web-First V1)**  
**Date:** 2026-04-27  

---

## Abstract  
Competitive programmers practice across multiple platforms such as Codeforces, LeetCode, AtCoder, and CodeChef. While each platform provides partial statistics, the overall learning journey remains fragmented, making it difficult to track consistency, understand weaknesses by topic, and decide what to practice next.  

**CodeStats** is a web-first analytics and planning platform that aggregates contest schedules and user activity data into a unified dashboard. It transforms raw activity into actionable insights such as activity heatmaps, streaks, topic-wise analytics, difficulty distribution, and improvement trends. Based on these insights, CodeStats generates **rule-based problem recommendations** to provide structured guidance without requiring an AI layer in the first version.  

---

## 1. Introduction  
### 1.1 Background  
Competitive programming improvement depends on:
- consistent problem solving  
- contest participation  
- balanced topic coverage (graphs, DP, greedy, etc.)  
- progressive difficulty scaling  
- feedback loops (measure → analyze → improve)

However, most users practice across multiple platforms and must manually consolidate performance information. This creates friction and leads to unplanned practice and slower improvement.

### 1.2 Motivation  
Users commonly ask:
- What contest is next?  
- How am I doing across all platforms?  
- Which topics am I weak in?  
- What should I solve next?  
- Am I improving or just solving randomly?

CodeStats is designed to answer these questions in a single system.

---

## 2. Problem Statement  
### 2.1 Identified Challenges  
1. **Fragmented progress visibility:** statistics and history are siloed per platform.  
2. **Weak feedback loop:** platforms show activity but limited structured guidance.  
3. **Manual weakness identification:** users must self-audit topics and performance gaps.  
4. **Contest planning overhead:** schedules are scattered across sources and timezones.  

### 2.2 Problem Definition  
Design and implement a scalable web platform that consolidates competitive programming contest schedules and user practice data into a unified dashboard, generates meaningful analytics to identify weaknesses, and recommends a structured practice plan.

---

## 3. Proposed Solution  
### 3.1 Solution Overview  
CodeStats provides:
- **Contest discovery and planning:** upcoming contests, countdowns, filters, calendar views  
- **Unified analytics:** heatmap, streak tracking, topic breakdown, difficulty distribution, rating trends  
- **Actionable guidance:** weakness detection and rule-based recommendations  

### 3.2 Web-First Strategy  
A web-first approach is chosen because it:
- reduces development overhead compared to mobile-first  
- supports rich dashboards and visualization  
- allows rapid iteration and easier deployment  
- enables later addition of a mobile companion (notifications + quick view)

---

## 4. Scope and Feature Set  
### 4.1 V1 Feature List  
**CodeStats = Your Competitive Programming Analytics Hub (V1)**  

1) Authentication & User Profile  
2) Handle Integration (Codeforces-first; extensible for more platforms)  
3) Unified Dashboard (next contest, countdown, quick stats, recent activity)  
4) Upcoming Contests (CLIST-powered list + filters)  
5) Contest Calendar View (week/month, platform filters)  
6) Platform Stats Dashboard (rating/solves/contests for supported platforms)  
7) Activity Heatmap + Streak Tracking  
8) Topic Breakdown / Skill Analytics (tag-wise counts + recency)  
9) Difficulty Distribution (rating buckets / easy-medium-hard where applicable)  
10) Rating & Performance Trends (time-series charts)  
11) Weakness Detection (rule-based signals)  
12) Rule-Based Problem Recommendations (“what to solve next” + reasons)  
13) Profile & Settings (handles, timezone, sync status)

### 4.2 Out of Scope for V1  
- AI chat assistant / AI coaching  
- Mobile app + push notifications  
- Social leaderboards / friend comparisons  
- Subscription billing  
- Full cross-platform tag ontology mapping (planned later)

---

## 5. Technology Stack  
  - **CLIST** for contest aggregation  
  - **Codeforces API** for user submissions and rating history  

### 6.2 Major Components  
1. **Web UI**: dashboard, contests, analytics, profile  
2. **API service**: auth, handle linking, aggregation endpoints  
3. **Connector layer**: platform integrations with a shared interface  
4. **Analytics engine**: computes derived metrics  
5. **Recommendation engine**: generates rule-based practice suggestions  
6. **Database**: raw + derived tables for performance  

### 6.3 Design Principles  
- separation of concerns  
- incremental sync  
- precomputed analytics (fast UI)  
- connector modularity for future platforms  

---

## 7. External Data Integrations  
### 7.1 Contest Data (CLIST)  
- periodic fetch of upcoming contests  
- cached globally in database  
- served to users with filtering and timezone support  

### 7.2 Codeforces Data  
Used for:
- submissions history → heatmap, streak, tags, success ratios  
- rating changes and contest history → trend charts  
- problem metadata (tags, rating) → analytics and recommendations  

---

## 8. Database Design (Conceptual)  
### 8.1 Core Entities  
- User  
- UserHandle (platform, handle, sync state)  
- Contest  
- Submission  
- Derived analytics (daily activity, tag stats, rating history, weakness signals)  
- Recommendation set  

### 8.2 Suggested Tables (V1)  
- `users`  
- `user_handles`  
- `contests`  
- `submissions`  
- `daily_activity`  
- `tag_stats`  
- `rating_history`  
- `weakness_signals`  
- `recommendation_sets` and `recommendations`  

### 8.3 Rationale for Derived Tables  
Derived tables reduce expensive computation during requests. Instead of aggregating raw submissions on every page load, the system updates summary tables after synchronization and serves dashboards efficiently.

---

## 9. Core Computations (Technical Logic)  
### 9.1 Activity Heatmap  
- group submissions by day (store in UTC)  
- compute daily activity count  
- use intensity levels for heatmap visualization  

### 9.2 Streak Calculation  
- define an “active day” as daily_count > 0  
- compute consecutive-day sequences  
- output current streak and longest streak  

### 9.3 Topic Breakdown  
- map solved problems → tags  
- compute solved/attempt counts per tag  
- store last activity timestamp per tag  

### 9.4 Weakness Detection (Rule-Based)  
Signals:
- neglected tags: long time since last activity  
- under-practiced tags: low solved count  
- low success tags: many attempts but low acceptance ratio  

Weakness output includes scores and human-readable reasons.

### 9.5 Recommendations (Rule-Based)  
- select top weak/neglected tags  
- determine difficulty band from user rating  
- filter out solved problems  
- recommend a balanced set with “why” explanations  

---

## 10. Data Sync and Scheduling  
### 10.1 Contest Sync  
- runs every 3–6 hours  
- upserts contest records into `contests` table  

### 10.2 User Sync  
- triggered on handle connection and via scheduled job (daily)  
- incremental fetching based on `last_synced_at`  
- after sync: recompute analytics and recommendations  

---

## 11. Security and Reliability  
### 11.1 Security  
- hashed passwords (bcrypt/argon2)  
- JWT-based access control  
- secure storage of API keys server-side  
- rate limiting for sync endpoints  

### 11.2 Reliability  
- timeouts + retries + exponential backoff for external API calls  
- graceful degradation when connectors fail  
- record sync status and errors for transparency  

---

## 12. Testing Strategy (Recommended)  
- unit tests: analytics computations, weakness scoring, recommendation rules  
- integration tests: sync pipeline end-to-end  
- UI tests: dashboard rendering with mock data  

---

## 13. Future Enhancements (Roadmap)  
### Phase 2 — Engagement & Reporting  
- goal tracking (rating targets, topic goals)  
- monthly report generation (shareable)  
- email digests (contests + weekly plan)

### Phase 3 — Multi-Platform Expansion  
- add LeetCode connector  
- add AtCoder connector  
- combined cross-platform heatmap  
- gradual tag taxonomy mapping

### Phase 4 — AI Layer (Post-Stability)  
- AI explanation of weaknesses  
- AI-generated practice plans with constraints  
- contest strategy guidance

### Phase 5 — Mobile Companion  
- push notifications (contest + practice nudges)  
- quick dashboard and countdown view  

---

## 14. Conclusion  
CodeStats is a scalable and practical solution that addresses a real gap: transforming distributed competitive programming activity into actionable guidance. The V1 focuses on high-value features using stable data sources and a modular architecture that supports future expansion.

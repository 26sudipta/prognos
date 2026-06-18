# CodeStats — Future Roadmap & Requirements (API-First & Classroom Edition)
**Status:** Strategic Planning (V2)  
**Role:** Senior SE / Product Manager Perspective

---

## 1. Executive Summary
CodeStats is evolving from a personal analytics dashboard into a **Social Competitive Programming Platform ("Strava for CP")**. The core value proposition is now split into two tiers:
1.  **B2C (Individual):** Unified stats, heatmaps, and skill-gap detection.
2.  **B2B/Community (Classrooms):** Transparent progress tracking, peer competition, and mentor dashboards for universities and bootcamps.

The platform will follow an **API-First Architecture** with a **Web-First Rollout**, followed by a **Mobile Companion App** focused on zero-cost native notifications.

---

## 2. Updated Functional Requirements

### 2.1 Multi-Tenant Classroom System
*   **Role-Based Access Control (RBAC):**
    *   **Mentor/Teacher:** Can create classrooms, manage invite links, and access "Cohort Analytics" (aggregated weakness reports for the whole group).
    *   **Student:** Can join multiple classrooms, view the "Transparent Leaderboard," and compare their skill matrix against the classroom average.
*   **Transparent Leaderboard:** By default, all classroom members see each other's:
    *   Activity Heatmaps & Streaks.
    *   Solved count and difficulty distribution.
    *   *Optional:* Specific problem solve history (to foster peer learning).
*   **Invite System:** Secure, unique tokens for joining classrooms (can be revoked or expired by mentors).

### 2.2 Handle Verification Protocol
To ensure data integrity (especially in classroom rankings):
1.  User enters their Codeforces handle.
2.  System generates a temporary random string (e.g., `CS-7G2K9`).
3.  User must paste this string into their **Codeforces Profile Summary/About Section**.
4.  System polls the CF API to verify the string exists.
5.  Once verified, the handle is permanently linked to the CodeStats account.

### 2.3 Mobile-Edge Notification Strategy
*   **Goal:** $0 Operating Cost for notifications.
*   **Implementation:** 
    *   Mobile app (Flutter) fetches the contest schedule on launch and caches it locally (SQLite).
    *   App uses native OS scheduling (`flutter_local_notifications`) to set alarms.
    *   **Background Fetch:** Periodically wakes up to sync schedule updates and adjust local alarms without server-side push (Firebase) costs.

### 2.4 Skill-Gap & Weakness Engine (Rule-Based)
*   **Phase 1 (Non-AI):** Logic to identify "Neglected Tags" (tags not solved in 14+ days) and "Low Success Tags" (high failure rate compared to peer average).
*   **Phase 2 (AI):** LLM-powered personalized coaching that reads the JSON output of the Phase 1 engine to provide conversational advice.

---

## 3. Technical Architecture (API-First)

### 3.1 Stack
*   **Backend:** FastAPI (Python) - serves a unified REST API for both Web and Mobile.
*   **Web Frontend:** Next.js (TypeScript) + Tailwind + shadcn/ui.
*   **Mobile App:** Flutter (for iOS/Android parity).
*   **Database:** PostgreSQL (with `Materialized Views` for classroom leaderboards).
*   **Task Queue:** Celery + Redis (for asynchronous CF data syncing).

### 3.2 Data Pipeline & Performance
*   **Incremental Sync:** Syncing 100 students in a classroom requires a background worker that respect's CF's rate limits (2 seconds between requests).
*   **Classroom Cache:** The `classroom_leaderboard` table is updated every 1–2 hours. The UI **never** aggregates raw submission data on request; it only reads from the pre-computed cache.

---

## 4. Market Positioning & Monetization
*   **Positioning:** "The Strava for CP." Focus on the "social pressure" of seeing peers' consistency.
*   **Monetization Path:** 
    *   **Free:** Individual stats + 1 Classroom (up to 5 members).
    *   **Premium/B2B:** Unlimited Classrooms + Advanced Cohort Reporting for Universities/Bootcamps.

---

## 5. Strategic Roadmap
1.  **V1.0 (Web + Core API):** Auth, Handle Verification, Personal Dashboard, Basic Classroom (Invite + Leaderboard).
2.  **V1.1 (Analytics Deep-Dive):** Skill-gap engine, advanced heatmaps, and "Comparison Mode."
3.  **V2.0 (Mobile Alpha):** Contest discovery, offline local alarms, and quick-view dashboard.
4.  **V3.0 (AI Layer):** Integrating LLM coaching based on the established analytics engine.

---

## 6. Implementation Notes for Claude/Devs
*   **Generic API:** All endpoints must return standard JSON. Do not couple the API to Next.js specific patterns (e.g., avoid Server Actions for core data fetching).
*   **Schema First:** Define Pydantic models for all entities before implementing routes.
*   **Timezones:** Store everything in UTC; convert to local time *only* on the client-side (Web/Mobile).

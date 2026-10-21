# PROGNOS Classroom v2: Product and Build Plan

**Status:** PROPOSED. Awaiting maintainer approval. Written 2026-10-16.
**Evidence:** every claim here traces to `docs/classroom_v2_research.md`, which covers 20+ similar
products, 27 real training programs, about 50 community posts, 25 peer-reviewed studies and the
Codeforces API.
**How to use it:** approve or amend the decisions in §13, then build one slice at a time, starting
with §10. Each slice gets its own `docs/phase_6_X.md` when it ships, following the project's
phase-doc convention, where X is the slice number.

---

## 0. The Short Version

**The problem.** Classroom today is an all-time table sorted by Codeforces rating, plus a teacher
panel of class averages. A teacher reads it once and finds nothing to do. A lower-rated student
reads it and learns, every day, that they're near the bottom.

**What the evidence says.**
- Comparison works when the target is a few people slightly ahead of you. It backfires when the target is the class star. In one MOOC study of 5,740 students, seeing excellent peer work made a large share of them quit (§3.1).
- Real programs all run on a weekly rhythm: a topic, a problem sheet, a contest, then upsolving. PROGNOS has no rhythm at all (§3.2).
- Teacher dashboards improve results only when the teacher acts on what they see. Charts on their own change nothing (§3.1).
- No CP product verifies Codeforces homework, and the last friends feed, StopStalk, shut down in August 2025 (§3.3).

**The direction in one line:** every student gets a race they can win this week, and every coach
gets a list of who needs them and why.

| Building block | Serves | In one line |
|---|---|---|
| Weekly Growth League | Both | A weekly race among about 12 near peers, scored by how far each solve stretched you past your own level |
| Assignments | Coach, then students | Verified Codeforces homework with due dates, including one-topic sets matched to each student's level |
| Contest Day | Both | Class standings for every CF round members played, plus each student's upsolve queue |
| Coach Inbox | Coach and mentors | Ranked "who needs you and why" cards with a one-click nudge, assignment or shout-out |
| Feed and peer help | Students | Milestones, kudos, and "who in my class solved this?" |
| Bootcamp structure | Coach | Co-teachers, mentors, sections, ownership transfer, export |
| Insights, Compare, Squads, Digests | Mixed | Lecture planning, near-peer comparison, team seasons, weekly recaps in Discord |

**First slice:** the Weekly Growth League (§10), after a two-week baseline measurement (Slice 0).

---

## 1. Goals, Non-Goals and How We'll Know

### 1.1 Goals

| # | Goal | Answers the RFC question |
|---|---|---|
| G1 | A teacher opens the classroom at least weekly and **does something**: assigns, nudges, celebrates, plans a lecture | What does a coach do after looking? |
| G2 | Students in the **bottom third** keep coming back at nearly the same rate as the top third | What keeps a lower-rated student coming back? |
| G3 | The classroom shows things no personal dashboard can: near-peer races, class blind spots, who solved what, contest-day standings | What can a group view show that a personal one can't? |
| G4 | It fits real courses, clubs and bootcamps: mixed levels, sections, mentors, weekly rhythms | "Make it a proper feature" |

### 1.2 Non-goals

- **No proctoring, exams or grading.** PROGNOS reports practice. It doesn't certify it.
- **No client-side Codeforces fetching.** Every number stays server-verified (see `docs/phase_5_2.md`).
- **No chat.** Clubs already live in Discord, WhatsApp and Telegram. We post into those, we don't replace them.
- **No new judges in this plan.** Codeforces only, but nothing here should block AtCoder or CodeChef later.
- **No public shaming.** Rating drops, failed attempts and inactivity are never pushed to the class.

### 1.3 Metrics

| Metric | Definition | Target after the pilot |
|---|---|---|
| **North star: weekly stretch rate** | Share of active students with at least one solve at Δ ≥ −100 this week (Δ is defined in §5) | Up from baseline |
| Bottom-third retention gap | 4-week return rate of the top rating third minus the bottom third | 10 points or less |
| Teacher action rate | Share of classrooms where a teacher or mentor took an action this week | 60% or more |
| Nudge re-engagement | Share of nudged students active again within 7 days | 30% or more. Dai et al. 2025 saw just over 30% with a similar intervention |
| Contest participation | Share of students who played at least one contest this week | Up from baseline |
| Guardrail: leave rate | Students leaving a classroom per month | No increase |

Measuring any of this needs a baseline first. That's why Slice 0 ships visit logging before
anything visible changes.

---

## 2. Where Classroom Stands Today

| Part | Today | Why it falls short |
|---|---|---|
| Leaderboard | All-time table sorted by CF rating: rating, solved, streaks, 30-day active days, top and weak tags | The research's weakest variant. It's absolute, it never resets, and the strongest student sits on top where everyone sees them (§3.1) |
| Teacher panel | Class average rating, most-neglected tags, 30-day attendance list | Describes the class but suggests no action, so there's nothing to do after reading it |
| Roles | Teacher (the creator) and student | No co-teachers, mentors, sections or ownership transfer, all of which bootcamps need |
| Rhythm | None | Nothing new this week, so nothing pulls people back |
| Streaks | Any submission counts, even a lone WA | Easy to keep alive without practicing. Community threads complain about exactly this (dossier §4.2, §4.4) |
| Data | Submissions stored without CF's participant type, and problem difficulty isn't joined in | Can't tell a stretch solve from a warm-up, or a contest solve from practice |
| Sync | Teacher "Sync" button with a 15-minute cooldown, hourly cron, inline rebuild on read | A solid base. Its scale limits are already tracked as D2, D5 and D6 in `docs/tech_debt_register.md` |

Worth keeping exactly as is: verified handles only, server-side fetching, compute-on-write
projections, and explicit consent to visibility at join time.

---

## 3. What the Research Says

### 3.1 Eight principles

| # | Principle | Evidence (research dossier) | What it means here |
|---|---|---|---|
| P1 | Compare with near peers, never the star | Diel et al. 2021: moderate gaps push people, extreme gaps make them give up. Rogers & Feller 2016: exposure to excellent peers caused quitting. Fleur et al. 2023: comparison with slightly-better peers raised grades in two RCTs (§5.2) | Brackets of about 12 by level. Students see only their own bracket |
| P2 | Score stretch against your own level | The TLE Discord bot already scores challenges this way (§2.2). A 2026 r/codeforces reply: "Rating responds to difficulty, not volume" (§4.4) | Growth Points come from Δ, the problem's rating minus your level |
| P3 | Reset the race often | Çiğdem et al. 2023: engagement dropped after week 3. Strava clubs, LeetCode study plans and Duolingo leagues all reset weekly (§2.3, §5.1) | A weekly league with a recap |
| P4 | Pair every comparison with "you vs you" and "you vs a goal" | Weidlich et al. 2024 and Pekrun et al. 2014 (§5.3). SlavicG's widely upvoted Codeforces post: "Compare only to your past self" (§4.2) | A "My week" card: GP against my own 4-week average, progress to the weekly target |
| P5 | Give teachers actions, not charts | Herodotou et al. 2019 and Karademir et al. 2024 (§5.4). Open-source trackers stop at a 7-day inactivity email (§2.2) | A Coach Inbox with reasons and one-click actions |
| P6 | Celebrate in public, correct in private | Pickal et al. 2026: negative leaderboard feedback can do more harm than none (§5.1). A club lead who grew from 2 active members to 5 Experts "celebrated every achievement, no matter how small" (§4.1) | The feed shows milestones only. Rating drops and failed attempts never go public |
| P7 | Put collaboration inside competition | Sailer & Homner 2019 meta-analysis. Papadopoulos et al. 2024: a permanently losing team suffers (§5.5) | Squads that reshuffle each season, pair quests, "who solved this?" |
| P8 | Trust contest-time evidence most | Codeforces allows AI tools in practice. Contest results were the top growth signal across 27 programs. Cheating is the loudest complaint in 2026 threads (§3.3, §4.3) | Contest solves score 1.5×. Integrity signals stay private and factual |

### 3.2 The weekly rhythm real programs run

Across 27 documented programs (dossier §3.2), counting only what each program's sources show:

| Ritual | Programs |
|---|---|
| Weekly topic lecture or module | 12 |
| Weekly problem sheet | 10 |
| Weekly contest (daily in camps) | 10 |
| Skill levels or divisions | 9 |
| Selection contests | 9 |
| Mentor groups, TAs, office hours | 8 |
| Leaderboard or live scoreboard | 7 |
| Post-contest discussion and upsolving | 5, plus 3 more from snippets |

Programs keep building their own trackers to support this: DIU ACM's ranking portal, TLE's
Codeforces sheet sync, Phitron's LMS, and Google Sheets with scripts (dossier §3.2, §4.1).
Classroom v2 should be the tool they stop rebuilding.

### 3.3 What the market leaves open

From the teardown of 20+ products (dossier §2):

- **Verified Codeforces homework doesn't exist.** USACO Guide Groups has the best assignment model, but for Codeforces problems it accepts any pasted submission link as accepted.
- **The friends feed is unclaimed.** StopStalk had 130k+ users and shut down on 2025-08-01. Its founder blamed broken crawlers and colleges that wouldn't pay.
- **No product turns class weaknesses into "teach this next"** or lists students who need help with a reason attached.
- **Every CP group board ranks absolute output.** The mechanics that protect weaker members exist only outside CP platforms: Duolingo's matched cohorts, Strava's Local Legend (most efforts, not fastest), HackerEarth showing only your gap to the leader, and TLE's rating-relative points.

### 3.4 What people say

A few lines that shaped the design (all sourced in dossier §4):

- "I just did 100+ easy (800 rated) problems, and thought that I'm doing well." A first-year student on r/codeforces, 2026-10-12, after finding friends had learned more.
- "Managing training groups, tracking handles, and updating standings via spreadsheets can be a headache." A Codeforces tool author, 2026-03-30.
- "It feels like almost 80% of people cheat in Codeforces contests now." r/codeforces, 2026-08-21.
- Advent of Code removed its global leaderboard in 2025 because "many people incorrectly concluded that they were somehow worse programmers because their own times didn't compare." It kept private leaderboards for groups of friends.

### 3.5 Gaps in the evidence

Bangladeshi and Indian club practice mostly lives in Facebook groups and Discord servers, which
weren't searchable. Reddit quotes came through an archive and weren't individually re-checked.
Academic findings come from paper abstracts. Dossier §1 lists the method and its limits in full.

---

## 4. The Product

### 4.1 Who it's for

| Persona | Today's workaround (dossier) | What they need from Classroom v2 |
|---|---|---|
| **Course teacher.** An algorithms course or lab, 40 students, mixed interest | LMS plus checking Codeforces by hand | Verified homework, a privacy mode, CSV export |
| **Club lead.** Student-run club, 20 to 80 members | A Google Sheet of handles, top 3 posted to a Messenger group, a home-made script to spot color changes (§4.1) | A weekly race with zero setup, contest-day recaps, a way to celebrate color changes |
| **Bootcamp coach with mentors.** 60 to 300 students, mentors at 1:5 or 1:1 | Their own LMS or portal, Discord, mentors tracking progress by hand (§3.1) | Sections, mentors scoped to their mentees, an inbox, completion rules |
| **Lower-rated student** | Compares with friends and gets discouraged (§4.2) | A race they can win, a clear next problem, private progress against their own past |
| **Higher-rated student** | Already motivated. Watches rating | Real stretch problems, contest-day standings, a way to help classmates |

### 4.2 Feature catalogue

Written in the RFC's own template. Ranked by evidence against the growth objective, which is also
the build order (§9).

| # | Feature | Serves | What it looks like | Data used | Habit or action it enables | Slice |
|---|---|---|---|---|---|---|
| F1 | **Weekly Growth League** | Both | Your bracket of about 12 near peers, GP with a breakdown, "5 GP behind Rafi", countdown to the weekly close | First-ever ACs, participant type, problem ratings, rating history | Come back weekly, pick problems a bit above your level | 1 |
| F2 | **My Week card** | Student | GP against your own 4-week average, progress to the target, 3 suggested problems | Weekly scores, existing recommendation engine | Self-referenced progress and a clear next step | 1 |
| F3 | **Verified assignments** | Coach, then students | A problem sheet with a due date. Teachers get a students-by-problems grid. Hint and editorial links unlock at a chosen time | CF problem keys, submissions | Teacher assigns the week's topic, students practice it | 2 |
| F4 | **Adaptive sets** | Coach | "5 binary search problems at each student's level": one assignment, different problems per student | `cf_problems` by tag and rating, each student's level and solved set | A mixed-level class where everyone stretches and nobody drowns | 2 |
| F5 | **Weekly targets** | Both | "1 rated round plus 5 problems at level", shown as a progress ring | Weekly scores | Goal-referenced feedback, the Assiut and NUS pattern | 2 |
| F6 | **Contest Day** | Both | Class standings for each CF round members played: rank, solved, rating change. A recap card afterwards | Rating history, submissions with participant type | Play together, celebrate gains | 3 |
| F7 | **Upsolve queue and class upsolve board** | Both | Your unsolved problems from the last round that are within reach. A board of who upsolved what | Submissions, `cf_problems` | The upsolving ritual most programs run | 3 |
| F8 | **Contest series** | Coach | Pick N rounds and get a series score with the worst K dropped | Rating history ranks | Team selection, as in 9 of 27 programs | 3 |
| F9 | **Coach Inbox** | Coach, mentors | Ranked cards: who needs you and why, with nudge, assign or shout-out one click away | All projections | Weekly intervention | 4 |
| F10 | **Student page and notes** | Coach, mentors | One page per student: weekly GP, assignments, contests, tags, private notes | Projections | Informed one-to-one conversations | 4 |
| F11 | **Feed, kudos, "who solved this?"** | Students | Milestones (new color, first 1600, cleared an upsolve list) with a kudos button. On any problem: classmates who solved it and are open to helping | Events, submissions | Public celebration, asking peers for help | 5 |
| F12 | **Bootcamp structure** | Coach | Co-teachers, mentors limited to their mentees, sections with placement rules, expected roster, ownership transfer, CSV export, completion rules | Memberships | Running a real cohort | 6 |
| F13 | **Class Insights** | Coach | A tag-by-level heatmap with "teach this next" and 5 matching problems. The class's difficulty frontier | Tag stats, submissions, `cf_problems` | Planning the next lecture | 7 |
| F14 | **Compare and private rivals** | Student | Side by side with one classmate: rating, tags, difficulty histogram, and "solved by them, not you, near your level" | Submissions | Learning from a near peer's path | 8 |
| F15 | **Squads and pair quests** | Both | Balanced squads for a 4-week season. Squad score is the sum of capped member GP. Random pairs share a weekly goal | Weekly scores | Collaboration inside competition | 9 |
| F16 | **Weekly digest and Discord** | Both | A Monday recap: league result, targets, highlights. A Discord webhook posts it and contest-day cards | Projections | Keeping the rhythm where clubs already gather | 10 |

### 4.3 Information architecture

| Viewer | Tabs, in order | Default |
|---|---|---|
| Student | League · Assignments · Contests · Feed · Members (compare) · All-time | League |
| Teacher, co-teacher | Inbox · League · Assignments · Contests · Insights · Members · Settings | League until Slice 4, then Inbox |
| Mentor | Inbox (own mentees) · League · Assignments · Contests · Members | Inbox |

Tabs appear as their slice ships. The current rating table survives as "All-time", one click away.

---

## 5. Scoring: Growth Points

Growth Points (GP) are the league's currency. They answer one question: *how much did you stretch
yourself this week, measured against your own level?* That last part is what lets a 1000-rated and
a 1900-rated student race each other fairly.

### 5.1 Your reference level

Every student gets a reference level `r`, frozen when the week starts so it can't drift mid-race.

| Student | `r` | Why |
|---|---|---|
| Rated on Codeforces | `max(current rating, peak rating in the last 180 days − 150)`, floor 800 | The peak rule stops anyone tanking their rating on purpose to farm easy points. It also keeps a slump from shrinking someone's targets overnight |
| Unrated, 10+ rated solves in the last 90 days | 70th percentile of those solves' problem ratings, floor 800 | Beginners who haven't played a rated round still get a level that tracks what they actually solve |
| Unrated, fewer than 10 rated solves | 800 | CF problem ratings start at 800 |

### 5.2 Points per problem

A problem scores only on its **first-ever accepted solve**, and only if that solve lands inside the
week. Re-solving old problems earns nothing. The rating is read from `cf_problems` at rebuild
time, so a problem Codeforces rates a few days after its round gets rescored automatically while
the week is still open. With `Δ = problem rating − r`:

| Band | Δ | GP | Rule |
|---|---|---|---|
| Warm-up | below −300 | 1 | Capped at 10 GP a week, so it can't be farmed |
| Practice | −300 to −101 | 3 | |
| At level | −100 to +99 | 6 | |
| Stretch | +100 to +299 | 10 | |
| Reach | +300 and above | 12 | Flat on purpose. Honest jumps that big are rare. Pasted AI answers aren't |
| Unrated problem | n/a | 2 | Gym problems, and new problems before Codeforces rates them |

Codeforces estimates a problem's rating from how contestants at each level did on it, so the same
Δ means roughly the same stretch at any level. That's the whole fairness argument.

The CP community already accepts this idea, which should help adoption. The TLE Discord bot, used
on many CP servers, scores its `;gitgud` challenges by problem rating minus your rating: 2 points
at −300, 8 at 0, 23 at +300. Our curve is flatter at the top for integrity reasons (§5.4).

### 5.3 Bonuses

| Habit | GP | Data |
|---|---|---|
| Rated contest played | +8 each | A `rating_history` row in the window |
| Unrated, gym or virtual contest played | +5 each, max 2 a week | `participant_type = VIRTUAL`, or `CONTESTANT` / `OUT_OF_COMPETITION` in a contest with no `rating_history` row |
| Solved live in a contest | Band points × 1.5, rounded up | An AC with `participant_type` of `CONTESTANT` or `OUT_OF_COMPETITION`. A strong student playing a lower division out of competition is still solving under contest conditions |
| Upsolve | +4 on top of the band points | A practice AC on a problem from a contest you played in the previous 14 days, which you didn't solve during it |
| Solve day | +2 a day, max 5 days | A local calendar day with at least one AC at Δ ≥ −300. A lone WA doesn't count, and the cap means two rest days a week cost nothing |

Contest points reward **showing up**, never the result. Rating changes are zero-sum between
classmates in the same round, and GP shouldn't be.

**Why contest solves weigh more.** Codeforces' rules allow AI tools freely in practice and ban them
only during contests. A practice solve is legal even when an AI wrote it, and invisible to us
either way. Coaches already trust contest-time evidence most: contest results were the top growth
signal across the 27 programs in the dossier (§3.3). The 1.5× multiplier and the upsolve bonus tilt
GP toward that evidence without ignoring practice.

**Why the solve-day cap is 5.** Community threads are full of streak burnout ("As someone with 500
days streak on CF and burnt out… trust me") and of people grinding 800-rated problems just to keep
a streak alive (dossier §4.2). Paying for 5 days, not 7, makes rest free.

**Team submissions.** In ICPC-style team practice, a submission shows up under every team member
with a `teamId`, so nobody can tell who solved it. Team submissions count toward the contest bonus
but earn no band points.

**Known Slice 1 limitation: a club's own contests.** Weekly contests in Codeforces groups and
mashups are one of the most common rituals, but they don't fit cleanly yet. Public gym contests
score as unrated contests: +5 for playing, 2 GP per solve. Private group contests may not show up
in anonymous `user.status` at all. A test against one camp contest came back "not found", and the
result was inconclusive (dossier §7). This has to be tested with a group member's API key before
Slice 3 is designed, and the "how points work" page should say so plainly.

### 5.4 Properties we want, and how the rules deliver them

| Property | Mechanism |
|---|---|
| Positive-sum | Your GP never depends on anyone else's. Only your rank inside the bracket does |
| Fair across levels | Points come from Δ, not absolute difficulty |
| Hard to farm | First-ever solves only, warm-up cap, flat top band, solve days need a real AC, contest solves weighted above practice |
| Rewards the habits coaches ask for | Contests, upsolving and steady practice all score |
| Kind to rest | Solve days cap at 5 |
| Explainable | Every row stores its breakdown, and the UI shows "how you earned this" |
| Tunable | Constants live in one config module. Each weekly row records `scoring_version` |

### 5.5 Brackets

The league never ranks the whole class at once.

- 20 or fewer active students: one bracket.
- More than 20: sort by `r`, then cut into contiguous brackets of about 12, with sizes within one of each other.
- Brackets freeze at week start. Someone joining mid-week goes into the bracket whose range contains their `r`.
- **Students see only their own bracket.** Teachers see all of them.
- Teachers and mentors are left out of the league by default (decision D-4).

Twelve is a judgment call. It's small enough that first place feels reachable and big enough that
the board isn't empty. Third-party teardowns put Duolingo leagues at about 30 people, matched on
study habits and time zone, but those are strangers. Tune it in the pilot.

---

## 6. The Coach Inbox: Rules (Slice 4)

The inbox is a short, ranked list of "who needs you and why", recomputed after each league rebuild.
Each card names the student, states the reason in plain words, shows the evidence, and offers one
or two actions. It shows at most 7 open cards a day, so a coach with 150 students isn't buried.

### 6.1 Flags

| Flag | Fires when | Evidence shown | Suggested action |
|---|---|---|---|
| **Went quiet** | No submission for 7+ days, after 8+ active days in the 30 days before | Last active date, previous weekly GP | Nudge: "Here's one warm-up problem to restart" |
| **Never started** | Joined 7+ days ago, zero submissions since | Join date | Nudge with a starter problem at their level |
| **Comfort zone** | 15+ solves in 14 days, 80%+ of them at Δ ≤ −300 | Difficulty histogram | Assign 3 problems at Δ 0 to +200 |
| **Stuck on a problem** | 5+ rejected submissions on one problem in 7 days, no AC | Problem link, attempts | Point them to a classmate who solved it, or post a hint |
| **Behind on an assignment** | Below 70% of a linear pace with 3 days or less left | Progress against the due date | Reminder, or extend the deadline for this student |
| **Missed the class contest** | Didn't play a round the class marked as its contest | The round | Nudge with that round's upsolve queue |
| **Rating slide** | 3 rated contests in a row adding up to Δ ≤ −150 | Last 3 rating changes | Encouraging note plus a practice plan. Never shown publicly |
| **Breakthrough** (positive) | New max rating, new rank color, first solve in a new 100-point band, or an assignment finished early | The milestone | One click: shout-out to the class feed, or a personal note |
| **Unusual jump** (private) | 5+ Reach-band solves in one day | The solves and their times | Worded neutrally: "Could be a breakthrough. Worth a chat." |
| **Integrity review** (private) | Every submission the student made in a round came back `SKIPPED`, and that round is missing from their rating history | The round and its verdicts | Talk privately. PROGNOS shows facts and never labels anyone |

A single `SKIPPED` verdict means nothing. Codeforces also marks superseded pretest-passed
submissions that way. The "all skipped, rating missing" pattern comes from memory, not from the
API docs, so it must be checked against real handles before Slice 4 ships. All thresholds above
are starting points to tune in the pilot.

Positive flags are there on purpose. Herodotou et al. found that teachers who intervened got
results. Celebrating is an intervention too, and it costs the student nothing.

### 6.2 Actions and the feedback loop

| Action | Effect |
|---|---|
| Nudge | In-app notification from a template or custom text. At most one per student per day per classroom |
| Assign | Opens a one-student assignment pre-filled with suggested problems |
| Shout-out | Posts the milestone to the class feed with the coach's note |
| Note | A private note on the student, visible only to teachers and mentors |
| Snooze or Done | Hides the card for 7 days, or closes it |

Every nudge records whether the student came back within 7 days, and the inbox header shows the
coach's own re-engagement rate. "Did my nudges work?" becomes a number they can see, which closes
the loop most teacher dashboards leave open (Ramaswami et al. 2022).

---

## 7. Privacy, Visibility and Integrity

### 7.1 Visibility modes

| Mode | Students see | Teachers see | Typical use |
|---|---|---|---|
| `full` (default) | Classmates' names, handles and avatars | Everything | Clubs, bootcamps |
| `anonymous` | Stable aliases such as "Member 7" for everyone except themselves. No handles, no avatars | Everything | University courses, classes with minors |

The mode applies to **every endpoint that returns classmates**: leaderboard, members, league, and
each later projection (assignments, contest day, feed). Masking changes values only, never field
names or types. That keeps the Android app already on people's phones working against the same
endpoints. Its Codeforces profile links won't resolve in anonymous mode until the app updates,
which is acceptable.

### 7.2 Never pushed to the class

Rating drops, failed attempts and WA counts, inactivity, inbox flags, private notes and nudges.
The current rating stays visible on the All-time tab, as it is today and as it is on Codeforces
itself.

### 7.3 Integrity stance

PROGNOS shows facts, not verdicts. Codeforces enforces its own rules (skipped verdicts, rating
removal), and we don't try to out-detect it. What we do instead:

1. Accept only server-fetched data from verified handles (already true).
2. Score contest-time evidence above practice (§5.3).
3. Keep GP low-stakes: weekly, bracketed, never tied to grades by default.
4. Give teachers private, factual signals that start a conversation (§6.1).

This is also a selling point. In 2026 threads, cheating is the most common reason people give for
losing motivation (dossier §4.3). A class where honest stretch is what scores is a better place to
practice than the global standings.

---

## 8. Data and Architecture

### 8.1 What the data can and can't do today

| Need | Status | Fix |
|---|---|---|
| Problem difficulty per solve | Not joined in. Ratings live only in the problemset cache used for recommendations | Persist `cf_problems` (refreshed daily) and join `submissions.problem_id = cf_problems.problem_key` at rebuild time. No new column on `submissions`, no rating backfill |
| Contest vs practice vs virtual | **Missing.** `_fetch_submissions` drops `author.participantType` | Store `participant_type`, plus a one-off re-fetch backfill (Slice 1) |
| Rated contest results | Present. `rating_history` has rank, rating change and time | None |
| Class timezone | Missing. Daily activity is bucketed by UTC date | `classrooms.timezone`. The per-user heatmap fix stays in the QA backlog |
| Who solved which problem, inside a class | Present in `submissions` | A visibility decision, not a data gap (D-3) |
| Gym contests | Public gym submissions arrive via `user.status`, with no rating and empty tags | Score them as unrated |
| Private group contests | **Unknown.** They may not appear in anonymous `user.status` | Test with a group member's API key before Slice 3. CF's `group.isManager` can confirm a coach really manages a group they link |
| Team submissions | Appear under every member with a `teamId` | Contest bonus only (§5.3) |

### 8.2 New tables by slice

| Slice | Tables and columns |
|---|---|
| 0 | `classroom_daily_visits` |
| 1 | `cf_problems`, `classroom_weekly_scores`; `submissions.participant_type`; `classrooms.timezone`, `week_starts_on`, `member_visibility` |
| 2 | `classroom_assignments`, `classroom_assignment_problems`, `classroom_assignment_progress` (cache) |
| 3 | `classroom_contests` (rounds and series the class marks), `classroom_contest_results` (cache) |
| 4 | `classroom_flags`, `notifications`, `classroom_nudges`, `classroom_student_notes` |
| 5 | `classroom_events` (feed), `classroom_kudos`; `classroom_memberships.open_to_help` |
| 6 | `classroom_sections`, `classroom_expected_roster`; the role enum gains `co_teacher` and `mentor`; `classroom_memberships.section_id`, `mentor_id` |
| 7 | `classroom_insights` (cache) |
| 8 | `classroom_rivals` |
| 9 | `classroom_seasons`, `classroom_squads`, `classroom_squad_members` |
| 10 | `classroom_integrations` (Discord webhook URL, stored encrypted) |

Every `*_progress`, `*_scores`, `*_results` and `*_insights` table is a projection like
`classroom_leaderboard`: written by a worker, read as-is, safe to drop and rebuild.

### 8.3 Compute model on the free tier

Production has no message broker, so `.delay()` is a no-op and the leaderboard already rebuilds
inline on read (`_ensure_leaderboard`). Classroom v2 keeps that contract so it runs on today's
infrastructure:

1. **On sync:** the handle sync already ends by triggering classroom rebuilds. League, flags, assignment progress and contest results join that hook.
2. **On read:** each projection gets an `_ensure_*` guard that rebuilds when the cache is stale or behind the newest member sync. DB-only, no CF calls.
3. **On schedule:** cron-job.org already calls `/cron/*` with the shared secret. Add `/cron/refresh-problems` (daily, one CF call) and `/cron/close-weeks` (hourly, DB-only).

**Rule:** no projection may call Codeforces. Only the sync worker talks to CF, through `_cf_get`.

### 8.4 Codeforces budget and scale gates

Codeforces allows at most one API call every 2 seconds. The docs don't say whether that's per IP or
per key, so treat it as one budget for the whole server: 1,800 calls an hour. A member sync costs
about 2 calls (`user.status` plus `user.rating`).

| Load | Calls per hour | Verdict |
|---|---|---|
| 15 users today, hourly | ~30 | Nothing to do |
| One 300-member bootcamp, synced every 2 hours | ~300 | Fine on its own |
| 1,000 active users, synced hourly | ~2,000 | Over budget. Needs the hot, warm and cold cadence from `docs/architecture_endgame.md` |

Two cheap savings from the API research: `contest.ratingChanges` returns a whole round's rating
changes in one call, which can replace per-member `user.rating` calls after a round, and
`user.info` takes up to 10,000 handles per call for current ratings.

Codeforces also changes things without notice. In April and May 2026 it restricted
`contest.standings`, which broke Carrot and CF-Predictor. Every CF-dependent feature needs a
degraded mode that keeps working from `user.status` alone.

**Gates before onboarding any class over 100 members:**

| Gate | Tech-debt item | Why it can't wait |
|---|---|---|
| Global Redis token bucket on every CF call | D2 | Several workers can jointly trip the limit and get the server banned |
| Fast vs deep sync split, rebuilds deduplicated per classroom | D5 | One member's sync currently rebuilds every classroom they belong to |
| Rebuilds off the request path, which needs a broker | D6 | An inline rebuild of a 300-row league would land on someone's page load |

Until those land, cap classrooms at 100 members in code, with a clear error message.

---

## 9. Roadmap

### 9.1 Vertical slices

One slice at a time, per the project's build rule. Sizes are relative: XS is about a day, L is a few weeks of
evenings.

| Slice | What ships | Depends on | Size |
|---|---|---|---|
| **0** | Visit logging, to capture a baseline | Nothing | XS |
| **1** | **Weekly Growth League**: participant type, `cf_problems`, class settings, visibility modes, league and My Week card | 0 | L |
| **2** | Assignments: fixed sheets, adaptive sets, weekly targets, progress grid | 1 (`cf_problems`) | M |
| **3** | Contest Day: class standings, upsolve queues, class upsolve board, contest series | 1 (participant type), group-contest key test | M |
| **4** | Coach Inbox: flags, nudges, in-app notifications, student page, private notes | 1 to 3 | L |
| **5** | Feed, kudos, milestones, "who solved this?" | 1, 3 | M |
| **6** | Bootcamp structure: co-teachers, mentors, sections, expected roster, transfer, CSV export, completion rules | 4, plus scale gates D2, D5 and D6 | L |
| **7** | Class Insights: tag-by-level heatmap, "teach this next", difficulty frontier | 1 | S |
| **8** | Compare with a classmate, private rivals | 1, decision D-1 | S |
| **9** | Squads, pair quests, ICPC teams | 1, 6 | M |
| **10** | Weekly digest by email, Discord webhook | 4, 5 | M |
| **11** | Flutter parity for the slices above | Each slice | M |

The order alternates between what teachers get and what students get, so both sides see value
early. Slices 7 and 8 are small and self-contained, which makes them good candidates for outside
contributors through the RFC (§15).

### 9.2 Traceability: nothing silently dropped

**Coach workflows from the bootcamp research (dossier §3.4):**

| # | Workflow | Where it lands |
|---|---|---|
| 1 | Sections with placement rules, bulk handle import | Slice 6. A pasted CSV of handles becomes an **expected roster** showing who has joined and verified. Importing handles directly would skip verification and break the integrity model |
| 2 | Sheets with due dates, auto-checked | Slice 2 |
| 3 | Weekly targets | Slice 2 |
| 4 | Internal contests, camp rating with the worst rounds dropped | Slice 3 for public rounds. Group contests and mashups wait on the API key test (§8.1) |
| 5 | Upsolve tracking | Slice 3 |
| 6 | Who is falling behind | Slice 4 |
| 7 | Completion rules, certificates, CSV export | Slice 6. PDF certificates are deferred, since the export covers grading |
| 8 | Mentors over sub-groups, with notes | Slice 4 (notes), Slice 6 (mentor role) |
| 9 | ICPC teams of three | Slice 9, using `teamId` from team submissions |
| 10 | Posting to Discord or WhatsApp | Slice 10. Discord gets a webhook. WhatsApp has no bot-free webhook, so it gets a copyable text recap |
| 11 | Integrity flags for review | Slice 4, after the `SKIPPED` pattern is verified on real handles |

**White space from the product teardown (dossier §2.5):**

| Gap | Where it lands |
|---|---|
| Verified Codeforces homework | Slice 2 |
| Tag-gap report that suggests a lecture | Slice 7 |
| Intervention list with reasons | Slice 4 |
| Post-contest class recap | Slice 3 |
| Self-relative scoring, rating-band sub-leagues | Slice 1 |
| Pair or team quests | Slice 9 |
| "Classmate solved, you haven't" | Slice 5 ("who solved this?") and Slice 8 (compare) |
| Verified class feed with kudos | Slice 5 |
| Class upsolve board | Slice 3 |
| Additive class score, Kattis-style | Slice 9 (squad score is a sum of capped member GP, so nobody drags a team down) |
| Student-by-tag heatmap | Slice 7 |

**Deliberately out:** other judges (AtCoder, CodeChef), private CF group integration until the key
test passes, proctoring and chat (never), and LLM coaching, which stays on the V3 roadmap.

---

## 10. Mini-Design for Approval: Slices 0 and 1

### 10.0 Slice 0: baseline visit logging

| Item | Design |
|---|---|
| Migration 010 | `classroom_daily_visits`: UUID PK, `classroom_id` FK CASCADE, `user_id` FK CASCADE, `visit_date DATE`. Unique `(classroom_id, user_id, visit_date)` |
| Write path | `get_classroom` and `get_leaderboard` (and later the league) each upsert one row per member per UTC day, as the last step of the read, inside a savepoint. Web opens a class with the detail call and the Android app with the leaderboard call, and the unique key makes the overlap free. `visit_date` stays UTC permanently, so baseline and pilot data stay comparable. Built in `docs/phase_6_0.md` |
| Read path | None yet. Metrics come from a SQL notebook during the pilot |
| Tests | Same-day reads across both endpoints make one row; non-members get 403 and no row; a failing insert never breaks the read; leaving keeps history; deleting the class or the account removes it |

Ship it, then wait two weeks before Slice 1 reaches users, so there's a baseline to compare with.

### 10.1 Slice 1 goal and build order

**Goal:** replace the all-time rating table as the classroom's front page with a weekly,
level-fair race among near peers. Later slices build on its data.

**Build order inside the slice:** data fidelity (1a), then the scoring engine (1b), then the API
(1c), then the web UI (1d). Each step ships on its own and keeps the app green.

### 10.2 Schema changes

**Migration 011, data fidelity**

| Table | Change | Why |
|---|---|---|
| `submissions` | add `participant_type VARCHAR(24) NULL` | CF's `author.participantType`. Separates contest, out-of-competition, virtual and practice solves |
| `submissions` | add index `(user_handle_id, submitted_at)` | Weekly window queries hit it on every rebuild |
| `cf_problems` (new) | UUID PK, `problem_key VARCHAR(32) UNIQUE` (same format as `submissions.problem_id`, e.g. `1903A`), `contest_id INT`, `problem_index VARCHAR(8)`, `name`, `rating INT NULL`, `tags JSONB`, `solved_count INT`, `updated_at TIMESTAMPTZ` | A local copy of `problemset.problems`, refreshed daily with one gzip-compressed call. Also powers assignments in Slice 2 |

**Migration 012, league**

| Table | Change | Why |
|---|---|---|
| `classrooms` | add `timezone VARCHAR(64) NOT NULL DEFAULT 'UTC'` | Weeks and solve days follow the class's clock, not the server's. The create form pre-fills the creator's browser zone |
| `classrooms` | add `week_starts_on SMALLINT NOT NULL DEFAULT 0` | 0 means Monday |
| `classrooms` | add `member_visibility VARCHAR(16) NOT NULL DEFAULT 'full'` | `full` or `anonymous` (§7.1) |
| `classroom_weekly_scores` (new) | UUID PK, `classroom_id` FK CASCADE, `user_id` FK CASCADE, `week_start DATE`, `ref_rating INT`, `bracket SMALLINT`, `growth_points INT`, `stretch_solves INT`, `breakdown JSONB`, `rank_in_bracket INT`, `status VARCHAR(8)` (`live` or `final`), `scoring_version SMALLINT`, `computed_at TIMESTAMPTZ`. Unique `(classroom_id, user_id, week_start)`. Index `(classroom_id, week_start, bracket)` | The precomputed cache the league reads. One row per member per week, the same pattern as `classroom_leaderboard` |

All columns follow the project's model conventions: `Mapped`/`mapped_column`, `TIMESTAMPTZ`, server-side UUIDs.

### 10.3 Backfill (one-off, idempotent)

1. **Problem catalogue:** the first `/cron/refresh-problems` run fills `cf_problems`. Ratings are joined at rebuild time from then on, so `submissions` needs no rating backfill.
2. **`participant_type`:** incremental sync stops at the newest stored submission, so old rows are never re-read. A one-off job re-fetches `user.status` per handle (500 per page, through the existing `_cf_get` throttle) and fills the column by `(user_handle_id, cf_submission_id)`. Today that's 15 users. It runs from a cron-secret endpoint in small batches, so a free-tier restart only costs a retry.
3. **Ongoing:** `_fetch_submissions` stores `participant_type` for every new row.

### 10.4 API contracts

| Method and path | Who | Returns |
|---|---|---|
| `GET /classrooms/{id}/league?week=current\|YYYY-MM-DD` | Members | `LeagueResponse`, below |
| `GET /classrooms/{id}/league/history?weeks=8` | Members | My GP per week plus the class median per week, for the self-referenced chart |
| `PATCH /classrooms/{id}` | Teacher | Any of `name`, `timezone`, `week_starts_on`, `member_visibility`. An unknown IANA zone returns 422 |

```jsonc
// LeagueResponse
{
  "week_start": "2026-10-12", "week_end": "2026-10-19", "status": "live",
  "closes_in_seconds": 190000, "timezone": "Asia/Dhaka",
  "me": {
    "growth_points": 46, "rank_in_bracket": 4, "bracket": 2, "ref_rating": 1180,
    "avg_last_4_weeks": 38,
    "breakdown": {"practice": 3, "at_level": 18, "stretch": 10, "contests": 8, "solve_days": 6, "upsolves": 4},
    "next_target": {"display_name": "Rafi", "gp_gap": 5}   // null when first in the bracket
  },
  "brackets": [                                              // students get only their own bracket
    {"bracket": 2, "rating_min": 1100, "rating_max": 1290,
     "entries": [{"rank": 1, "user_id": "...", "display_name": "...", "cf_handle": "...",
                  "avatar_url": "...", "growth_points": 61, "stretch_solves": 3,
                  "contests": 1, "delta_vs_last_week": 12}]}
  ],
  "pulse": null,   // teachers only: active_members, median_gp, stretch_solves, contests, zero_gp[]
  "syncing": false
}
```

**Compatibility rules for the shipped Android app:**

- `ClassroomResponse` only gains fields (`timezone`, `week_starts_on`, `member_visibility`). Nothing is renamed or removed.
- `GET /leaderboard`, `GET /members` and `GET /cohort` keep their exact shapes. In `anonymous` mode, a student viewer gets masked values in the same fields: alias strings for names and handles, `null` avatars.

### 10.5 Worker logic: `rebuild_league(classroom_id, week_start)`

1. Load the classroom's timezone and week start, and turn the local week into a UTC window `[start, end)`.
2. Load student members and their verified CF handle ids.
3. For each member, reuse this week's frozen `ref_rating` and `bracket` if a row exists. Otherwise compute `r` (§5.1).
4. One query per classroom: each member's first-ever AC per problem, kept only if it falls in the window. Left-join `cf_problems` on `problem_id = problem_key` for the rating, and carry `participant_type`, `contest_id` and `submitted_at`.
5. Score each solve by band (§5.2), apply the live-contest multiplier and the warm-up cap, then count solve days by **local** date, capped at 5.
6. Add contest bonuses from `rating_history` and `participant_type`. Detect upsolves against the member's non-practice submissions in the same contest within the previous 14 days. Skip band points for team submissions.
7. Assign brackets if this is the week's first build (§5.5), then rank inside each bracket by GP, then stretch solves, then name.
8. UPSERT every row with its breakdown, `scoring_version` and `computed_at`.
9. **Finalization:** the first rebuild after `week_end + 6h` scores the previous week one last time and flips it to `final`. Final rows never change again. The 6-hour grace lets late Sunday syncs land.

**Triggers, following the pattern already in production:**

- `_ensure_league` rebuilds inline on read when the cache is empty, older than its TTL, or behind the newest member sync, mirroring `_ensure_leaderboard`.
- `_trigger_leaderboard_rebuilds` also enqueues `rebuild_league`, for when a broker exists.
- A DB-only rebuild is fine up to about 100 members, which is the cap until gate D6 (§8.4).

### 10.6 Web UI

| Where | Student | Teacher |
|---|---|---|
| Default tab | **League**: own bracket, "5 GP behind Rafi", time left in the class's timezone, a "how points work" popover | **League** with every bracket, plus a pulse strip: active members, median GP, stretch solves, contests, zero-GP list |
| My Week card | GP against my 4-week average, breakdown bars, 3 suggested problems from the existing recommendation engine | n/a |
| All-time tab | The current rating table, unchanged | Same |
| Settings | n/a | Timezone, week start, member visibility |

Before any frontend code, the project's workflow calls for a UI research pass. The dossier's UI notes
(§2.6) are the starting brief: Strava's this-week club table, Duolingo's league list, and
HackerEarth's gap-to-leader display.

### 10.7 Test plan

**Unit tests (pure functions, no DB)**

| Area | Cases |
|---|---|
| Bands | Δ at −301, −300, −101, −100, 99, 100, 299 and 300; unrated problem; warm-up cap reached at exactly 10 |
| Multipliers | `CONTESTANT` and `OUT_OF_COMPETITION` get 1.5× rounded up; `PRACTICE` and `VIRTUAL` don't; team submission earns no band points |
| Reference level | Rated with current equal to peak; peak rule after a 200-point drop; unrated with 9 vs 10 rated solves; floor at 800 |
| Week window | Asia/Dhaka (no DST); America/New_York across both DST switches; `week_starts_on` other than Monday |
| Solve days | AC at 23:59 and at 00:01 local fall on different days; a WA-only day earns nothing; the sixth solve day earns nothing |
| Upsolves | In-contest AC is not an upsolve; practice AC on day 14 is; day 15 is not; a problem already solved during the contest is not |
| First-ever solve | Re-solving a problem first solved last month earns 0 |
| Brackets | 20 students give 1 bracket; 21 give 2; 150 give sizes within one of each other; a mid-week joiner lands in the right bracket |

**Integration tests (pytest against the isolated test DB)**

| Case | Expectation |
|---|---|
| Student GET league | Only their own bracket, and `pulse` is null |
| Teacher GET league | Every bracket plus `pulse` |
| Non-member | 403 |
| `anonymous` mode | Students see aliases in league, leaderboard and members, stable across calls. Teachers see names |
| Response shapes | Leaderboard, members and cohort JSON keys match a stored snapshot, so the shipped app keeps parsing them |
| PATCH as a student | 403. A bad timezone returns 422 |
| Member synced after `computed_at` | The next GET rebuilds and shows the new solves |
| A problem gets rated mid-week | The next rebuild rescores it from 2 GP to its band |
| Week finalization | Rows flip to `final` and stay unchanged when later submissions arrive |
| Ingest | New submissions store `participant_type` |
| Backfill | Fills `participant_type`. Running it twice changes nothing |
| Member removal | Their rows leave the league immediately |
| Member cap | The 101st join returns a clear 409 |

**Build gates:** `pytest` green, `npm run build` clean, migrations 009 to 012 round-trip on a
**local** database. Never run them against production from a laptop, which is what caused the
2026-10-14 outage.

### 10.8 Rollout

1. Ship Slice 0 and collect two weeks of baseline.
2. Ship 1a, run the backfill, and spot-check 20 submissions against Codeforces by hand.
3. Ship the league to the two production classrooms, with the All-time tab one click away.
4. Recruit the pilot club (§12) and run four weeks before starting Slice 2.

---

## 11. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Codeforces Terms forbid "commercializing any Website material"** (dossier §7) | Certain, as written | High for the B2B tier and any startup path | Free while piloting. If a paid tier happens, charge for PROGNOS's own coaching workflow, never for CF data, and ask Codeforces in writing first (D-6). Doesn't block any slice |
| AI-assisted or copied solutions inflate GP | High | Medium | Weekly, low-stakes GP. Flat Reach band. First-ever solves only. Contest solves weighted above practice. Private, factual integrity signals, never public accusations |
| A club's own group contests are invisible to the API | Medium | Medium | Key test before Slice 3 (§8.1). Public gyms still score as unrated contests |
| Codeforces changes its API without notice, as with `contest.standings` in 2026 | Medium | High | Degraded mode that works from `user.status` alone. No projection calls CF |
| CF API ban from added load | Low now, high at scale | Critical | No projection calls CF. Gates D2, D5 and D6 before classes over 100 members |
| Novelty wears off after about 3 weeks (Çiğdem et al. 2023) | High | High | Weekly reset and recap, assignments with due dates, contest-day standings, squad seasons. Each slice adds a new reason to come back |
| Scoring feels unfair to some group | Medium | High | Public "how points work" page, a breakdown on every row, `scoring_version`, tuning on pilot data before a wide launch |
| Public boards push some students away (Bursztyn & Jensen 2015) | Medium | High | Own-bracket view, `anonymous` mode, nothing negative made public, bottom-third retention as a tracked metric |
| Coach overload | Medium | Medium | At most 7 inbox cards a day, ranked by severity, with snooze and done |
| Free-tier compute | Medium | Medium | DB-only rebuilds, a 100-member cap, gate D6 before big classes |
| Minors in school or olympiad classes | Medium | High | `anonymous` mode, nothing public beyond the class, data deleted with the account. Get legal advice before selling to schools |
| Timezone confusion | Medium | Low | The class's timezone appears next to every countdown |

StopStalk is the cautionary tale here. Its founder named broken crawlers, unreliable data and
colleges that wouldn't pay as the reasons it shut down (dossier §2.2). PROGNOS already avoids
scraping by using the official API. The other two lessons are the reason for the degraded mode
and for validating value before any pricing talk.

---

## 12. Validation Plan

1. **Baseline, 2 weeks.** Slice 0 visit logging on the two production classrooms. Nothing visible changes.
2. **Recruit a real pilot.** One university club or bootcamp with 30+ active members. The maintainer's own CP community is the obvious first ask.
3. **Pilot Slice 1, 4 weeks.** Track the §1.3 metrics weekly. Interview 2 coaches and 6 students, two from each rating third, in weeks 2 and 4.
4. **Decision rule.** Go ahead with Slice 2 if the bottom-third gap didn't widen and the weekly stretch rate went up. If the gap widened, fix the league first.
5. **Tune.** Adjust band points and bracket size from real distributions, bump `scoring_version`, and record the change in the phase doc.

**What each group can actually test.** The two production classrooms have 15 members between them,
so each runs as a single bracket. They can test scoring, the My Week card and the weekly rhythm,
but not bracketing. Only the 30+ member pilot exercises brackets.

At this scale, A/B tests aren't realistic. Before-and-after numbers plus interviews are honest and
cheap. When results get reported, they should be described exactly that way.

---

## 13. Decisions Needed From the Maintainer

Each one has a recommended default. Approving the plan approves these defaults unless you say
otherwise.

| # | Decision | Recommended | Why |
|---|---|---|---|
| D-1 | Bring "Comparison Mode" back into scope | **Yes**, as Slice 8 (compare and private rivals) | requirement.md lists it as out of scope in every version. The ask now is students comparing with each other, and the research supports near-peer comparison done carefully |
| D-2 | Students see only their own bracket | **Yes** | Rogers & Feller 2016, Fleur et al. 2023. Teachers still see every bracket |
| D-3 | Show solved problem names inside a classroom (C.4 is TBD today) | **Yes for accepted solves, never for failed attempts** | "Who solved this?" and "solved by them, not you" are the best peer-learning features here, and both need it. Failed attempts stay private, except to teachers through the "stuck" flag |
| D-4 | Teachers and mentors in the league | **No by default**, opt-in per person | A coach who practices shouldn't take a student's first place |
| D-5 | Opt-out after joining (C.3 says there's none) | **Keep "leave" as the opt-out**, plus the class-level `anonymous` mode | A per-student hide toggle would break the board for everyone else. Courses that need privacy get it at the class level |
| D-6 | Tier limits and pricing (requirement.md §2: free means 1 classroom with 5 members) | **No enforcement during the pilot**, a 100-member cap for CF budget reasons, and **no pricing on CF data** | A 5-member cap would rule out every real club. The Codeforces Terms forbid commercializing site material, so any paid tier must sell PROGNOS's coaching workflow, and only after asking Codeforces |
| D-7 | Default timezone | **The creator's browser zone**, editable | Bangladeshi clubs shouldn't have their week close at 6 AM local time because the server runs on UTC |

---

## 14. Proposed requirement.md Changes

Not applied yet. They go in once the plan is approved, since requirement.md is the functional
source of truth.

| Section | Change |
|---|---|
| §2 Core mechanic | "Transparent classroom leaderboard" becomes "weekly near-peer league plus coach inbox". Add the principles: compare with near peers, pair every comparison with self and goal references, celebrate in public, correct in private |
| §2 Monetization | Add the Codeforces Terms constraint from D-6 |
| §3 Roles | Add `co_teacher` (all teacher rights except delete and transfer) and `mentor` (inbox, nudges and notes for assigned students). Resolve the "Teacher" TBD: any verified user can create a class |
| §4 Roadmap | Add "V2.x Classroom v2", pointing to this plan. Remove "Comparison Mode" from out-of-scope (D-1) |
| C.1 Lifecycle | Add ownership transfer, which also unblocks deleting a teacher's account |
| C.3 Joining | Add the 100-member cap and the expected roster |
| C.4 Transparency | Resolve the TBD per D-3. Add `member_visibility` |
| C.5 Leaderboard | The primary view becomes the weekly league. The rating table stays as "All-time". Resolve the secondary-sort TBD: GP, then stretch solves, then name |
| C.8 Cohort analytics | Superseded by the Coach Inbox (§6) and Class Insights (Slice 7) |
| New C.9 to C.15 | League, Assignments, Contest Day, Inbox, Feed and Kudos, Compare and Rivals, Squads |
| §8 Data model | Add the tables in §8.2 |
| §9 Routes | Add routes as each slice ships |

---

## 15. Relationship to the Open RFC

`classroom_rfc_issue.md` asks contributors for ideas and promises to post "our own research +
direction" after the first wave. This plan can be that post. Suggested split:

- **Post publicly:** §0, §3 and §4.2, plus a link to the research dossier. Credit any community proposal that matches a feature.
- **Keep maintainer-built:** Slices 1 to 4. They touch scoring, integrity and the data pipeline, where consistency matters most.
- **Open to contributors:** Slices 7 and 8 are small, self-contained and read existing projections only. Slice 10's Discord webhook is a good first issue.

Nothing here has been posted. That's the maintainer's call.

---

## Next

Approve the decisions in §13, then build Slice 0 (§10.0) and write `docs/phase_6_0.md` when it
ships.

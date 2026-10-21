# Classroom v2: Research Dossier

**Written:** 2026-10-16. **Companion to:** `docs/classroom_v2_plan.md`, which turns this evidence
into a build plan.

**The question:** what would make PROGNOS Classroom genuinely useful to university courses, CP
clubs and bootcamps, so teachers can track their students and peer pressure helps students grow
instead of burying the bottom half?

**Contents:** 1 Method and limits · 2 Similar products · 3 How real programs run cohorts · 4 What
the community says · 5 Academic evidence · 6 The PROGNOS survey · 7 Codeforces API feasibility ·
8 Sources

---

## 1. Method and Limits

| Stream | How | Coverage | Limits |
|---|---|---|---|
| Similar products (§2) | A research pass read product pages and docs, plus the source code of USACO Guide, AtCoder Problems, CLIST, DMOJ, StopStalk and the TLE bot | 20+ products, 54 sources (C1 to C54) | Codeforces, LeetCode and beecrowd blocked fetching, so those facts are search snippets |
| Training programs (§3) | Program and course pages, Codeforces blogs, ICPC camp pages | 27 programs, 46 sources (B1 to B46) | Internal training at BUET, SUST, DU, IUT, NSU and BRACU isn't published anywhere searchable. It probably lives in Facebook groups and Discord servers |
| Codeforces API (§7) | The official API docs plus live anonymous API calls on 2026-10-16 | Every method the plan relies on | Private group contests are still an open question |
| Community (§4) | Reddit through an archive, Codeforces blogs, Hacker News, forums | About 50 posts, 2018 to 2026, mostly 2025 and 2026 | The research pass stopped on a rate limit before writing its report, so §4 was written from its raw notes. Eight Codeforces quotes were re-checked against saved copies of the pages and all matched. Reddit quotes weren't re-checked |
| Academic (§5) | Consensus search over peer-reviewed literature | 25 studies | Summaries come from abstracts, not full texts. Several samples are small |
| First-party (§6) | The PROGNOS project survey | n = 20 | Informal and indicative only |

**Evidence tags.** Sections 2 and 4 use *primary* (read on the original page, docs or code),
*secondary* (a third party), *snippet* (search-result summary only, because the page couldn't be
fetched), *archive* (Reddit via an archive) and *memory* (unverified). Sections 3 and 7 use the same
idea abbreviated: **P**, **Sec**, **Snip**, **Mem**. Sections 2, 3 and 7 are the research passes'
reports, lightly edited. Their source IDs were renumbered C# and B# so the two lists don't collide.

---

## 2. Similar Products

- No CP product combines verified Codeforces homework, coach analytics and a peer feed. USACO Guide Groups comes closest, but for Codeforces problems it accepts any pasted submission URL as AC [C1 primary].
- Every CP platform's group board ranks absolute output (rating, solves, points); the one exception is a Discord bot, TLE, whose gitgud points scale with your own rating. Other protections for weaker members come from elsewhere: matched cohorts (Duolingo), effort crowns (Strava Local Legend), HackerEarth's gap-to-topper board.
- No verified, class-scoped activity feed exists. StopStalk (130k+ users, 8 judges) shut down on 2025-08-01 [C4 primary]; Codeforces has only an undocumented `?friends=on` filter on its status page [C13 snippet].
- Coach analytics in CP are paid graders (Kattis, beecrowd), USACO Guide's per-assignment roster, a CodeChef chapter-lead dashboard with undocumented contents, or hobby dashboards whose only intervention is a 7-day inactivity email.

### 2.1 Feature matrix: CP products

| Product | Group unit | Roles | Assignments / lists | Leaderboard | Rival / 1v1 | Feed | Nudges | Privacy | Coach analytics | Pricing |
|---|---|---|---|---|---|---|---|---|---|---|
| Codeforces | Group (open, moderated, invite-only) [C8 snippet]; friends | Manager, participant, spectator [C9 snippet] | Group contests, mashups, Gym; coach mode at 1900+ with 30 contests, or 2200+ [C12 snippet] | Standings; group ratings, 50% attendance default [C10 snippet] | Friends filter on standings [C13 snippet] | Group blog | ? | Private groups | None; an extension adds a progress donut [C15 primary] | Free |
| VJudge | Group [C18 primary] | Leader, managers | Contests over ~60 judges | Per contest; replays capped at 2000 rows [C19 snippet] | ? | ? | ? | Public flag, join policy, applicants | ? | Free |
| USACO Guide Groups | Group [C1 primary]; open to all since 2022-06 [C2 snippet] | Owner, admin, member | Assignments: due date, points, hints, solution release | Group and per-assignment points | N | Post feed | ? | Join links: expiry, max uses, email allowlist | Per-member assignment status | Free |
| AtCoder Problems | None; rivals typed into URL [C3 primary] | N | Problem lists; virtual contests (Normal, Lockout, Training); Training courses | Global AC count, rated points, streak | Per problem: rival solved, you didn't | Global recent submissions | N | Contests public or private | N | Free, OSS |
| StopStalk (dead) | Friends, "custom friends" [C5 primary] | N | To-do list | Friends board default; global; by institute, country | N | Friends' submissions | Friend streaks (later disabled) | Tracks any handle without consent | N | Free [C4 primary] |
| CLIST | Coder lists; parties [C6 primary] | Party author, admins | N | List filters any contest's standings; party ranking | Versus: head-to-head tally, rating-history charts [C6, C7 primary] | N | ? | Lists private, restricted, public | N | Free |
| Codolio | ? | ? | Sheets, tagged questions [C20 snippet] | ? | ? | ? | Contest reminders | ? | ? | ? |
| CodeChef | Institution field; College Chapters [C21 snippet] | Student lead; faculty mentor | Labs, exams [C22 secondary]; Learn paths with % [C54 snippet] | Ranklists by institution [C23 snippet] | ? | ? | ? | ? | Chapter-lead dashboard [C21 snippet] | Pro tier, needed for Learn certificates [C54 snippet]; institutional sales |
| LeetCode | One-way follow [C25 snippet] | N | Study plans | Study plan: weekly top 10 [C24 snippet] | Extensions only [C26 snippet] | ? | ? | ? | N | Premium |
| beecrowd Academic | Course in Moodle or Blackboard [C27 primary] | Professor | Activities, tests | ? | ? | ? | ? | LMS-gated | Auto grading, reports | B2B |
| Kattis | Course; university | Unlimited teachers | Assignments, 4,000+ archive | Geometric university score [C29 snippet] | ? | ? | Plagiarism alerts | Anonymous mode | Course and student dashboard [C28 primary] | EUR 25 to 39 per student per course [C28 primary] |
| DMOJ | Org > Class [C30 primary] | Org and class admins | Org-private contests | Contest scoreboards | N | ? | ? | Access codes, size caps, 4 scoreboard modes | N | Free, OSS |
| Toph | Institution as contest host [C31 primary] | Up to 5 moderators | Free training contests (50 people, 3 h) | Standings with freeze | ? | ? | ? | Network, geo limits | None found | Free tier, paid tiers [C31 primary] |
| HackerRank / HackerEarth | User-hosted contests [C32 snippet] | Contest admin | Contests | HE: only your gap to the weekly topper [C33 primary] | ? | ? | ? | ? | HE hiring dashboards [C53 snippet] | Hiring-funded |
| TUF A2Z / TLE CP-31 | ? | ? | TUF progress x/495, notes, revision [C34 primary]; CP-31 by rating [C35 snippet] | TUF links a leaderboard (rules not found) | ? | ? | ? | ? | ? | Free sheets |
| TLE bot and OSS | Discord server [C36 primary] | Admin, moderator | `;mashup`, `;gitgud` | Gitgud points vs own rating; duel Elo | Duels; Lockout-Bot [C37 primary] | Post-round rank updates | Pingable duel/VC roles | Server-scoped | N | Free |

### 2.2 Product by product: what to steal, what's weak

**Codeforces.** Steal: friends-filtered standings turn any public round into a class round with zero setup; group ratings over a chosen contest set [C10 snippet]. Weak: no manager analytics; third parties add a group-page progress donut [C15 primary] and an export CLI, conmato [C17 snippet], and profiles list only the last 10 virtual gyms [C16 snippet]. EDU is self-paced courses (ITMO pilot) with no class layer found [C14 snippet].

**VJudge.** Steal: one contest can mix ~60 judges. Weak: group pages show contest counts and members only; a `summaryContestId` field exists but is undocumented [C18 primary]. No cross-contest group rank found.

**USACO Guide Groups.** Steal: the assignment model (due date, per-problem points, hints, solution release at due date, now, never or custom) and admin member pages with per-assignment status, sortable by due date or completion [C1 primary]. Weak: Codeforces problems run on the honor system. The client stores `verdict: 'AC'`, `score: 1` for any pasted URL, and the Firestore trigger that updates the leaderboard (`submitToProblem.ts`) uses that score without checking the link [C1 primary]. Boards rank total points only; the sidebar defaults to 10 rows.

**AtCoder Problems.** Steal: rivals are just handles in the URL. The Table marks a problem red when a rival solved it and you haven't (`failedStatus.solvedRivals`); the List shows red rival badges. Lockout and Training contest modes [C3 primary]. Weak: no group, roles or assignments, and no rival chart exists: progress charts take one user ID.

**StopStalk.** Steal: friends leaderboard as the default view, with per-day solve rate and its change beside rating [C5 primary]. Weak: dead. The founder cited broken crawlers, lost trust in the rating, AWS bills paid from savings, and colleges and students who would not pay [C4 primary].

**CLIST.** Steal: a coder list filters any contest's standings across platforms; versus pages tally head-to-head results over shared contests and chart each platform's rating history [C6, C7 primary]. Weak: observation only.

**Codolio.** Cross-platform sheet tracking [C20 snippet]; no group or comparison feature found.

**CodeChef.** Steal: student chapter leads get a members dashboard [C21 snippet]; Learn courses and practice paths show completion %, but certificates need Pro [C54 snippet]. Weak: no faculty dashboard documented; users asked for college-wise rankings for years and used third-party sites [C23 snippet].

**LeetCode.** Steal: a study-plan board that counts only the current week and shows 10 names [C24 snippet], so newcomers can top it. Weak: no native friends ranking [C26 snippet].

**Kattis and beecrowd.** Steal (Kattis): university score uses geometric weights (f=5), so adding any member with a non-zero score raises the total [C29 snippet]; weak members never hurt the team. Steal (beecrowd): lives inside Moodle or Blackboard, no extra student account [C27 primary]. Weak: paid graders with no motivation layer.

**DMOJ.** Steal: Organization > Class with class-level admins and access codes; scoreboards visible, hidden during the contest, hidden during participation, or hidden permanently [C30 primary]. Weak: no analytics.

**Toph.** Steal: free training contests for any teacher with a .edu or .ac email [C31 primary]. Weak: no classroom, assignment or tracking feature found. Bangladeshi universities already use it, so PROGNOS complements it.

**HackerRank / HackerEarth.** Steal: HackerEarth hides your weekly points and shows only the gap to the topper [C33 primary]. Weak: both live on hiring revenue; hackerrank.com/schools now resolves to a user profile, so no schools product found [C32 primary].

**TUF A2Z / CP-31.** Steal: a fixed, rating-bucketed sheet is a ready curriculum a class can climb together. Weak: progress is personal; CP-31's tracker page returned no content, so its sync behavior is unverified [C35 snippet].

**TLE bot and OSS trackers.** Steal: gitgud points depend on problem rating minus your rating (-300: 2 points, 0: 8, +300: 23) [C36 primary], so a 1000-rated and a 2000-rated student earn the same for an equal stretch. Auto "Rank updates" and "Top rating increases" posts after each round. `;mashup` picks problems within 100 of the group's average rating. Weak: Discord-only, no coach view. A cluster of 2025-26 MERN "student progress manager" repos all land on daily sync plus a 7-day inactivity email, one per streak, with per-student opt-out [C38 primary, snippet]. Smaller OSS ideas: per-friend "solved today" icons, an email when inactivity drops your rank, and rooms for asking higher-ranked members [C39 primary].

### 2.3 Non-CP references

| Product | Group unit | Comparison | Social / nudges | Privacy |
|---|---|---|---|---|
| Duolingo | Weekly league; friends | 10 tiers, weekly, matched on study habits and time zone [C40 primary] | Friends Quest, Friend Streak, nudges [C42, C43 primary] | Opt out by making profile private [C40 primary] |
| Strava | Club, public or invite-only [C44 primary] | Weekly club board; segment boards filter to following or club [C45 snippet]; Local Legend [C46 snippet] | Club feed, kudos, post emails | Outsiders can't see invite-only club activity |
| GitHub Classroom | Classroom + roster [C48 primary] | None in docs | None in docs | Private repos |
| Exercism | Track | ? | Volunteer mentors; private link to your own teacher [C49 primary] | Link-based |
| Codewars | Clan = profile text field [C50 primary] | Allies board by honor | Auto mutual follow | ? |
| Kaggle | None | 5 tiers per category [C51 secondary] | ? | ? |

- Duolingo: Friend Streak users are 22% more likely to complete the daily lesson [C43 primary]; learners who follow friends are 5.6x more likely to finish a course [C42 primary]. Third-party teardowns report 30-person leagues with promotion slots shrinking from 20 at Bronze to 0 at Diamond; sources conflict [C41 secondary]. Weak: the teardown credits demotion's loss aversion, which bites hardest at the bottom.
- Strava: club boards show only this week and last week [C44 primary]. A study of 329 club members found less-active runners copied more-active friends [C47 secondary]. Weak: boards rank raw volume, and the app shows only 10 names.
- GitHub Classroom: deadline with optional cutoff, autograding on every push, feedback pull requests [C48 primary]. Weak: no motivation layer; tests run on repos, not a CP judge.
- Exercism: a private link sends work to your own teacher [C49 primary]. Weak: the public queue can sit for days or weeks.
- Codewars: sharing a clan name makes users allies automatically [C50 primary], the cheapest possible group. Weak: a clan only shares stats; no clan goals found.
- Kaggle: separate tiers per category let a weak competitor be Expert in notebooks [C51 secondary]. Weak: tiers are rare by design (2,973 Masters in 23.29M accounts).

### 2.4 Patterns

**(a) Coach dashboards.** Three shapes: a roster with per-assignment completion (USACO Guide, GitHub Classroom, Kattis); an LMS gradebook (beecrowd, Kattis); an inactivity monitor with email (OSS trackers). All are per-student drilldowns. None turns class weaknesses into "teach this next", and none flags students who submit a lot but keep failing.

**(b) Comparison that protects the bottom half.** Beginners quit after comparing themselves with classmates on standings [C52 snippet].
1. Matched cohorts: Duolingo matches on study habits and time zone [C40 primary].
2. Effort over skill: Local Legend goes to the most efforts in 90 days, not the fastest [C46 snippet].
3. Self-relative scoring: TLE gitgud; StopStalk per-day change.
4. Gap instead of rank: HackerEarth topper gap; Strava's histogram of efforts needed to catch the Legend.
5. Short windows: Strava, LeetCode and Duolingo all reset weekly.
6. Additive group scores: Kattis weighting.
7. Hiding: DMOJ scoreboard modes, Duolingo opt-out, Kattis anonymous mode.
8. Cooperative pairs: Friends Quest (random friend pairing, shared goal, five days) and Friend Streak.
9. Celebrate deltas: TLE "Top rating increases".

**(c) Assignment flows in CP.**
- Post-based homework (USACO Guide): points, hints, due date, solution release; judge-verified only for USACO and CSES.
- Timed contests (CF mashups and Gym, VJudge, AtCoder Problems): verified but time-boxed, so they test rather than build habits.
- Sheets (TUF, CP-31): fixed curriculum, self-paced, no deadlines or teacher.
- LMS graders (beecrowd, Kattis, GitHub Classroom): deadlines and gradebooks on their own judge, not Codeforces.

### 2.5 White space

**Q1, what the teacher does next**
- Verified Codeforces homework: USACO Guide's assignment model, auto-marked from synced submissions. Outside Codeforces' own group contests, which give the teacher no analytics, no reviewed tool verifies CF homework.
- A class tag-gap report that suggests a lecture: "14 of 20 have no AC in dp at 1200+; here are 5 problems". Absent in every product reviewed.
- An intervention list with reasons (absent, stuck on WA, rating plateau, avoiding a tag) instead of one inactivity email.
- An auto post-contest class recap (TLE-style) the teacher can celebrate from.

**Q2, keeping lower-rated students**
- Rank by points relative to your own rating, or by this week's improvement; rating-band sub-leagues inside a class.
- Weekly pair or team quests inside the class.
- "Classmate solved, you haven't" at class scale, on verified data.

**Q3, what only a group view shows**
- A verified, class-scoped activity feed with kudos (see section 0).
- A class upsolve board: last round's problems classmates solved and you didn't.
- Class-level metrics: an additive class score (Kattis-style) and a student-by-tag heatmap.

### 2.6 UI notes

- **USACO Guide group page** [C1 primary]: a post feed, each assignment tagged "X / Y points earned" and "Due on", with a leaderboard sidebar. Assignment pages link an "Assignment Leaderboard". The admin member page has expandable per-assignment rows, Promote/Demote, Remove and a "view as member" mode; a join-link modal sets expiry, max uses and allowed emails.
- **AtCoder Problems** [C3 primary]: the search bar takes a user ID plus rival IDs. The Table tab is a contest-by-problem grid whose cells use Bootstrap success, danger and warning classes for: you solved, a rival solved and you didn't, you tried. The List tab adds status filters and red rival badges. User page tabs (Achievement, Pies, Progress Charts, Recommendation, Trophy) show one user only.
- **Duolingo league** [C40 primary, C41 secondary]: one ranked list of a matched cohort, tier badge on top, promotion and demotion zones, a new league each Sunday in your time zone.
- **Strava club** [C44 primary]: This Week / Last Week table with sortable stats, distance for single-sport clubs and time for multisport, reset Sunday 23:59 club time, plus an activity feed. Local Legend shows a histogram of your effort count against the Legend's [C46 snippet].
- **TLE bot** [C36 primary]: after each round, Discord embeds titled "Rank updates" and "Top rating increases", or "Nobody got a positive delta :(" when nobody gained.
- **CLIST versus** [C6, C7 primary]: "A vs B" header with a tally such as 0 : 1, a rating-history chart per platform with range selection, then shared-contest rows with rated/unrated toggles.

---

## 3. How Real Programs Run Cohorts

### 3.1 Programs

| Program | Structure | Cadence | Tracked | Promotion / selection | Tooling | Reported problems | Src |
|---|---|---|---|---|---|---|---|
| TLE Eliminators (paid, IN) | 4 levels of 12-14 weeks; topic modules, 60+ h video, 100+ curated problems per level with hints and video solutions | Recorded modules; 400+ post-contest solution videos for upsolving | CP-31 sheet: 31 problems per rating 800-1900, synced with CF to auto-mark solved, leaderboard; homepage counts "doubts cleared" | Level 2/3/4 = can solve 1/2/3 Div2 problems | Own site + CF sync, Discord, WhatsApp | - | B10, B11, B12, B13 P; B14 Snip |
| Phitron (paid, BD) | Tracks Foundation, CP, Software Dev; finishing one unlocks the next | Module released daily at 8 pm, quiz and practice set per module, weekly exam, live support 3x/day | 1:1 mentor monitors progress; outcomes sold as title counts (CF: 144 Pupil, 33 Specialist, 10 Expert) | Track unlock | Own LMS, community contests, leaderboard | "We know who gets lost in which week, at which topic", from 20,000+ students | B15 P |
| CPS Academy (paid, BD) | 12 months, 6 modules, each = live class + problem set + contest; "zero to Expert" | 2 live classes/week (100+), 100+ contests, CF upsolving class after rounds, mentor doubt sessions | Students' "rating curve", title counts | None stated | Discord | - | B16 P |
| Placement-first (AlgoZenith, AlgoUniversity, Coding Ninjas, Newton) | AZ: own judge, "gamified growth process"; AU: batches of 50, 1:1 mentor every 15 days; CN: TAs, problem of the day | Evening/weekend live classes; Newton: monthly rated contests (2021-22) | Placement outcomes | n/a | Own judges | CP folded into interview prep | B17, B18 P; B19, B44 Snip |
| CodeChef Campus Chapters (IN) | Student lead (2-star+) runs a chapter of 50-200 | Contests, workshops, doubt sessions | Lead must get 60% of members through learning objectives; progress dashboard | n/a | CodeChef dashboard | Program page now 404 | B20 Snip |
| Indian ICPC Camp 2026 (11 host institutes) | Teams of up to 3 in Div1/Div2; 3,000+ teams in 2025 | Tue class, Fri homework discussion, Sun 5 h contest, next Thu contest discussion | Camp rating: P = 3000 x (n - place + 1)/n x solved/maxSolved, n = max(50, teams); lowest 2 dropped, a skip scores 0 | Div1 needs one member with max rating >= 1900 | CF group, Discord, WhatsApp, YouTube | AI banned; similarity checks; plagiarism removes team from camp ranklist; "we can't detect all cheating" | B9 P |
| DIU ACM Wing (BD) | Register, diagnostic contest, orientation and team formation, starter weekly sheet | Weekly problem sets, mock ICPC contests, multi-day alumni bootcamps | Live scoreboard across weekly diagnostic contests | Team selection rounds | Codeforces, vjudge, own ranking portal | - | B21 P |
| BACS camps (BD, 2017) | Toph selection contest (1,072 sat); 3-day regional, 5-day national camps; Dhaka split Beginner 71 / Intermediate 99 / Advanced 79 | Camp days | n/a | Selection contest | Toph | Few nationwide training years before | B22 Sec |
| ICPC Dhaka Regional 2025 rule | Onsite quota per university from 2023-24 results, cap 8 | Online prelim | n/a | Teams chosen "strictly" by prelim rank inside each university | n/a | n/a | B23 P |
| BdOI (BD olympiad) | 5 divisional rounds (~50 each), ~50 to national | 2013: 7-day camp, then BUET camp of ~20 | Test scores | Selection contests; final team from live + 3 online tests | UVa, Timus, CF, USACO, LightOJ | Weak school infrastructure | B24 P (2013) |
| Assiut ACPC Club (EG) | Level 1, 9 weeks, 60 trainees, 15 mentors (1:5) | Tue 5 h session (topic + problems), Sat mentor practice, weekly sheet, weekly 5 h CF contest of 12 problems (mostly A-C) | Sheet %, contest and session attendance | Certificate: 80% of sheet, every contest, 80% of sessions; goal Expert and 70% of A-C | Codeforces groups | - | B25 P |
| NUS CS3233 (credit course, SG) | Admission needs CF >= 1400 by 31 Dec 2025 | Weekly lecture, Mini contest (Mon, 75 min + debrief), Kattis set (12 total), HW "solve Mini B/C"; midterm and final team contests | Graded HW, Minis, team contests; Kattis standings | Rating gate | Kattis, class Discord for team formation | Week-2 drop deadline, "hopefully no-one-drop-by-week-02" | B26 P |
| US/CA ICPC teams | MIT: 2 selection contests/yr, PhD student coaches; UCF: "twice-weekly practice" on ICPC camp sets and Universal Cup; Waterloo: local 3 h contest each term; Berkeley: one selection contest plus CF rating and past ICPC | Weekly practices | Contest results | Selection contests | Local judges, Universal Cup | Berkeley author called single-contest selection a poor choice | B27, B28, B29 P; B33 Snip |
| US/CA clubs (Georgia Tech, UW, McGill) | McGill: beginner and advanced tracks; UW: no commitment | GT: weekly lecture + solving, weekend training before ICPC; UW: weekly talk on vjudge group problems | Live scoreboard at internal contest (McGill) | n/a | vjudge, Discord | - | B30, B31, B32 P |
| USACO + CPI classes (US olympiad) | 4 divisions; 3 online contests then proctored US Open; ~24 finalists, IOI team picked at camp | CPI: 10 weekly 2 h classes (9 in 2021), homework sets, office hours Tue/Thu | CPI LMS leaderboard "to incentivize friendly competition" | US Open was "the primary determinant" of camp invites; platinum reset to gold this season | usaco.org, CPI LMS | Season called "transitional" while proctoring settles | B34, B35 P; B45 Snip |
| IOITC (IN olympiad) | ZCO/ZIO, INOI, then a camp of ~25-36; 4 picked for IOI | Camp with selection tests | Test scores | Selection tests | n/a | n/a | B36 Snip |
| Russian camps (MIPT, ITMO, Petrozavodsk) | Moscow Pre-Finals 2016: "one and a half divisions" (WF-level Div1, next-season Div2) | Daily contest, analysis, lecture, upsolving time | n/a | ITMO 2010 camps used a first individual contest to form teams | CF Gym (Petrozavodsk "ghosts", B3) | Petrozavodsk now mostly online (50th edition, 2026) | B37, B38 P; B39 Snip |

**Searched, nothing published:** internal training at BUET, SUST, DU, IUT, NSU, BRACU (BRACU only shows a one-off 2023 workshop that put students on vjudge, B43 Snip); IIT/IIIT club internals beyond hosting camp weeks; Stanford; year-round ITMO/HSE/MIPT training; Scaler. That material probably lives in Facebook groups and Discord servers [inference].

### 3.2 Rituals

N = 27 programs. Counts mean "documented in sources found", not prevalence (TLE may run weekly contests; I found no evidence).

| Ritual | Count | Where |
|---|---|---|
| Weekly topic lecture or module | 12 | TLE, Phitron, CPS, AU, Indian ICPC Camp, NUS, CPI, Assiut, GT, UW, McGill, Moscow |
| Weekly problem sheet or set | 10 (+1 Snip) | TLE, Phitron, CPS, AU, Indian ICPC Camp, DIU, NUS, CPI, Assiut, UW; CN |
| Weekly contest (daily in camps) | 10 | CPS, Phitron, Indian ICPC Camp, DIU, Assiut, NUS, UCF, MIT, Moscow, Petrozavodsk |
| Skill levels or divisions | 9 | TLE, Phitron, Indian ICPC Camp, BACS, Assiut, McGill, USACO, CPI, Moscow |
| Selection contest or test | 9 (3 Snip) | DIU, BACS, BdOI, MIT, Waterloo, USACO; Berkeley, IOITC, ITMO |
| Mentor groups, TAs, office hours | 8 (2 Snip) | Phitron 1:1, AU 1:1, Assiut 1:5, CPS, TLE, CPI; CodeChef, CN |
| Leaderboard or live scoreboard | 7 | TLE CP-31, Phitron, Indian ICPC Camp, DIU, NUS, CPI, McGill |
| ICPC-format team practice | 7 | Indian ICPC Camp, DIU, NUS, UCF, MIT, Moscow, Petrozavodsk |
| Discord/WhatsApp hub | 6 | TLE, CPS, Indian ICPC Camp, NUS, UW, McGill |
| Post-contest discussion + upsolve | 5 (+3 Snip) | TLE, CPS, Indian ICPC Camp, NUS, Moscow; UCF, Petrozavodsk, ITMO |
| Completion or attendance rule | 5 (1 Snip) | Assiut, Indian ICPC Camp, DIU, NUS; CodeChef |
| Rating gate for entry or division | 3 | Indian ICPC Camp (max >= 1900), NUS (>= 1400), TLE (Div2 solves as proxy) |

Tracking overhead is not reported directly, but programs keep building their own trackers: DIU a ranking portal (B21), TLE a CF progress sync (B12), Phitron an LMS (B15), others Sheets/Apps Script trackers (B46 Snip). Coaches build private CF mashups from past problems inside groups (B41 Snip). The TLE Discord bot adds a "smart mashup creator", difficulty-weighted "gitgud" and ";upsolve" points, and a server ranklist (B40 P).

### 3.3 Growth metrics, ranked by how often they drive decisions

"Seen in" = programs (of N = 27) whose sources show the metric used for a decision or headline outcome.

| # | Metric | Seen in | Gameability |
|---|---|---|---|
| 1 | Contest result (internal or selection) | 11 (3 Snip) | Medium. CF bans in-contest AI and catches it mainly by code matching (B8 P); camps add similarity checks (B9) or proctoring (B34). |
| 2 | CF rating or title (current or max) | 7 (1 Snip) | Medium. AI-cheating complaints in 2025-26 rounds and alt accounts (B42 Snip); moves only after rated rounds; max rating never drops. |
| 3 | Sheet / set completion % | 7 (1 Snip) | High. CF's AI rule does not cover practice ("AI tools may be used freely for practice", B8 P), so AI-solved sheet problems are legal and invisible. Editorial copying. |
| 4 | Attendance / contest participation | 5 (1 Snip) | Medium. Register-and-leave counts; needs a minimum-submission rule [inference]. |
| 5 | Solve depth per round (Div2 problems solved, "70% of A-C") | 3 | Low when measured in-contest. |
| 6 | Upsolve completion | 2 + TLE bot | High (editorial copying). Time-to-upsolve and verdict history help [inference]. |
| 7 | Week-by-week engagement / drop-off | 2 | Trivial submissions keep streaks alive [inference]. |
| 8 | Difficulty relative to own rating (gitgud, "start at X-200") | 1 + TLE bot | High; good for targeting, weak as proof. |

Only contest-time results are real proof. Upsolves are a better effort signal than random solves because they tie to a contest the student actually sat, but they are still practice, so boards should rank contest results first, upsolves second and raw solve counts last [inference].

### 3.4 Workflow requirements for PROGNOS

**Coach must be able to:**
1. Create org, cohort (batch/term) and sections with placement rules by rating, max rating or Div2 solve depth (Indian ICPC Camp, NUS, TLE); bulk-import handles from CSV.
2. Assign sheets of CF problem IDs or filters (rating band, tags) with due dates, auto-checked via user.status, optionally grouped by rating not topic (CP-31).
3. Set weekly targets: N problems at rating X or more, one rated round, upsolve the week's contest (NUS "solve Mini B/C", Assiut 80% rule).
4. Run internal contests: attach a CF group contest, mashup or public round; compute a camp rating with drop-lowest-k and skip allowance (Indian ICPC Camp).
5. Track upsolves: problems failed or untried in-contest, later solved, with time to upsolve (CPS, NUS, Moscow) [metric inferred].
6. See who is falling behind: missed contest, sheet behind schedule, no AC in 7 days, falling rating, week-2 drop risk (Phitron, NUS) [thresholds inferred].
7. Apply completion rules and certificates (Assiut); export CSV for grading (NUS).
8. Assign mentors to sub-groups (Assiut 1:5, Phitron 1:1); mentors see only their mentees.
9. Form ICPC teams of 3 and see team contest history (team submissions carry teamId, B6).
10. Post to Discord/WhatsApp, where 6 of these programs already gather [webhooks inferred].
11. Show integrity flags for review, never auto-punish: all of a student's submissions in a round SKIPPED is the strong plagiarism sign; CF also marks superseded pretest-passed submissions SKIPPED [Mem].

**Students must see:** weekly targets and progress, sheet progress, next contest, an upsolve queue, problems near their rating (from X-200, B12), contest history, and section boards on several metrics (effort and growth, not only rating) so lower-rated students can top one; CPI frames its leaderboard as "friendly competition" (B35) [board design inferred].

---

## 4. What the Community Says

Collected on 2026-10-16 from r/codeforces, r/leetcode, r/adventofcode, Codeforces blogs, Hacker
News, the Toph community forum and CodeChef Discuss. Most posts are from 2025 and 2026. Reddit
threads were read through an archive and are tagged *archive*. Posts where the author was promoting
their own tool are tagged *promo*, because their framing is self-interested even when the quote is
real.

### 4.1 Coaches and club leads: how they track students today

| Finding | Quote | Source |
|---|---|---|
| Spreadsheets are the default tool, and nobody likes them | "Managing training groups, tracking handles, and updating standings via spreadsheets can be a headache." | [CF blog 152523](https://codeforces.com/blog/entry/152523), 2026-03-30, primary, promo |
| Celebration grew a club from 2 active members to 5 Experts | "we celebrated every achievement, no matter how small. After each contest, I made it a point to congratulate everyone who changed colors." And: "As our club grew, keeping track of these changes became a challenge. So, I wrote a script." They also held post-contest discussions after every Codeforces and CodeChef round | [CF blog 130537](https://codeforces.com/blog/entry/130537), 2024-06-16, primary |
| A university tracker built on a Google Sheet | A sheet of handles produced a ranking, the top 3 went to a Facebook Messenger group, and it fed team formation | [CF topic 131179](https://codeforces.com/topic/131179/en1), 2024-06-17, snippet |
| Codeforces itself hides team history | "Codeforces only shows the last 10 virtual gyms for each user, which made tracking our team's progress quite difficult." Also: "upsolving the gyms we had already attempted was even more valuable" | [CF blog 146049](https://codeforces.com/blog/entry/146049), 2025-09-03, primary |
| What a coach is for | "a coach who has a long-term view of your path and always monitors the path you are on. If your progress is slow, they will talk to you and give you the necessary hints." | [CF blog 124820](https://codeforces.com/blog/entry/124820), 2024-01-17, primary, promo |
| Faculty often can't coach the content | "very few professors keep up with the contest meta the same way most NAC-qualifying students do" | [CF blog 136842](https://codeforces.com/blog/entry/136842), 2024-12-03, primary |
| The monitoring gap, stated as a project brief | "coaches and mentors struggle to monitor students' progress effectively within the team, leading to a communication gap regarding practice problems and student advancement." | [Iowa State senior design](https://seniord.cs.iastate.edu/2024-Jan-11/), 2024-01, primary |
| Group chats for accountability burn out | "Initially, we had a group chat where we held each other accountable through messages. However, that became tiring and inefficient." | [r/leetcode](https://www.reddit.com/r/leetcode/comments/1sssqh5/), 2026-04-22, archive, promo |

### 4.2 Students on peer pressure

**When it helps**

| Quote | Source |
|---|---|
| "nothing pushes you harder than seeing a friend solve 5 problems while you're stuck on one." | [r/leetcode](https://www.reddit.com/r/leetcode/comments/1m7gzok/), 2025-07-23, archive, promo |
| "Join some community..it will motivate you to maintain consistency" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1wl8gzm/_/paxgwwq/), 2026-09-20, archive |
| "we can do serious CF journey together and motivate each other and sometimes force to study" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1weaiqx/_/p9csnd3/), 2026-09-12, archive |
| "caring only about rating is bad. but learning and using rating as a tool for motivation is a pretty good thing" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1ws6p2v/_/pcj1bjn/), 2026-09-28, archive |
| On seeing a near peer's past results: "So its good to see a possible future. Im motivated now." | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1wq5bb4/_/pc5zo1o/), 2026-09-26, archive |
| "it's better to compare yourself with people who started around the same time as you, or even after you." | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1vqflqw/_/p458u6o/), 2026-08-17, archive |

**When it hurts**

| Quote | Source |
|---|---|
| "I began comparing myself to others, and it felt like I was never good enough. No matter how hard I tried, it always seemed like someone else was faster or better." The author's fix: "I started celebrating small victories" | [CF blog 135193](https://codeforces.com/blog/entry/135193), 2024-10-16, primary |
| "Envy becomes a big issue... One can't even feel happy for his friends' success due to getting overpassed in rating or noticing their progress was slower." The advice: "Compare only to your past self. Where were you a year ago, and where are you now?" | SlavicG, [CF blog 111521](https://codeforces.com/blog/entry/111521), 2023-01-16, primary |
| On rating fear: "I know of quite a lot of people who got their desired ranks and just quit participating in contests" and "There are people who actually start cheating in contests due to fear of rating loss" | Same post |
| Comparison turning into a fixed mindset: "some friends of mine reached it easily in months (with like 100 problems), so yeah id say u need talent" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1wumfe8/_/pd7o7i5/), 2026-10-01, archive |
| A new International Grandmaster on rating obsession: "Almost every Codeforces round made me rage, hate myself, cry, scream ... all because I could not gain some extra 100 rating points." Friends "started intentionally dropping rating" after bad streaks | [CF blog 154854](https://codeforces.com/blog/entry/154854), 2026-06-29, primary |
| Avoiding the upsolve: "no upsolve because i get humbled and demotivated after this" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1uea8yr/_/otlhqf4/), 2026-06-24, archive |
| Streak burnout: "As someone with 500 days streak on CF and burnt out… trust me" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1vvcrwk/_/p5d21ua/), 2026-08-23, archive |
| Streaks as a lifeline and a leash at once. After an outage: "the streak is the system which keeps me moving ahead", and in the same thread, "i just lost 250 days streak" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1vtrth0/_/p4vk2l6/), 2026-08-20, archive |
| Advent of Code removed its global leaderboard in 2025: "People took things too seriously, going way outside the spirit of the contest" and "Many people incorrectly concluded that they were somehow worse programmers because their own times didn't compare." Private leaderboards stayed | [r/adventofcode](https://www.reddit.com/r/adventofcode/comments/1ocwh04/), 2025-10-22, archive |

### 4.3 Integrity

| Finding | Quote | Source |
|---|---|---|
| Codeforces bans AI only in contests | "Outside of such contests, AI tools may be used freely for practice, learning, or non-competitive problem-solving." | [CF blog 133941](https://codeforces.com/blog/entry/133941), 2024-09-14, primary |
| Cheating is the top demotivator in 2026 | "It feels like almost 80% of people cheat in Codeforces contests now... ruins the rank and rating for everyone who is trying seriously." | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1vuqzqm/), 2026-08-21, archive |
| People are quitting over it | "for the life of me I can't find any motivation to continue doing it since there are so many cheaters now." Elsewhere: "the rampant AI cheating is pretty demotivating" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1uhsg8w/), 2026-06-28, archive; [Hacker News](https://news.ycombinator.com/item?id=45711267), 2025-10-26, primary |
| It feels like theft | "it feels like my progress is being stolen by lazy cheaters" | [CF blog 142152](https://codeforces.com/blog/entry/142152), 2025-04-21, primary |
| It reaches ICPC | "after finding out that many teams from our college cheated and got 4 solves before us, while one team even got 5, I feel really demotivated." | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1wzpgfm/_/pedv9nc/), 2026-10-07, archive |
| Strong contestants are noticing | "30 minutes after the round the top of the standings is already full of gray accounts". A reply: "There is no report system for catching cheaters." | [CF blog 154602](https://codeforces.com/blog/entry/154602), 2026-06-18, primary |
| Detection by outsiders is unreliable | A profile-scoring extension flagged honest friends. A reply: "partial or clever cheating are difficult to detect" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1uaz06k/), 2026-06-20, archive |
| Streaks prove nothing | "cheater can also have CF profile looking like green forest with daily streaks." On LeetCode: "they just resubmit the ques to maintain their streak" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1x36kk9/_/pf92iha/), 2026-10-11; [r/codeforces](https://www.reddit.com/r/codeforces/comments/1tnfvwm/_/oo6fsf1/), 2026-05-27; both archive |
| Vigilante exposure is starting | A thread titled "Our college sub exposing cheaters, everyone please do this" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1wxarjc/), 2026-10-04, archive |
| Platforms are reacting | Codeforces hid an LLM trap in a problem statement. After LeetCode cleaned its leaderboard, a user said "Now I don't trust on rating of lc" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1ujunbn/), 2026-06-30; [r/codeforces](https://www.reddit.com/r/codeforces/comments/1vcz37l/), 2026-08-01; both archive |

### 4.4 Which metrics reflect growth

| Quote | Source |
|---|---|
| "433 problems and a flat line for seven months usually means one thing: the problems are too easy... Rating responds to difficulty, not volume. The streak is part of the trap." | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1wfghkm/_/p9sc5vb/), 2026-09-14, archive, promo |
| "it doesn't mean consistency when solving 800 a day, streak are leashes let go off the streak and solve good rating +200 problems" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1trgadc/_/oophi7c/), 2026-05-30, archive |
| "I have solved 800+ que, still I am 3 star and pupil. My friends who are specialist have solved 1000+ que" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1ts7ayu/_/oovstag/), 2026-05-31, archive |
| "I just did 100+ easy (800 rated) problems, and thought that I'm doing well. But then I got to know that what I learnt in 1 month, my friends learnt much more than that" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1x3vux6/_/pfeu8zz/), 2026-10-12, archive |
| A friend streak kept alive with trivial problems: "the 800-rated problems were a challenge to the streak between me and my friends" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1ubmea2/_/osxjlne/), 2026-06-21, archive |
| Some people practice on an alternate account and keep their main for serious contests, so one handle can undercount practice. Alts break Codeforces rules | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1t60hcj/_/okeq0l8/), 2026-05-07, archive |

### 4.5 Tools people use, or used

| Tool | What people say | Source |
|---|---|---|
| StopStalk (closed after 2025-08-01) | The founder's final update: "Multiple colleges using StopStalk rating as their placement criteria". "We tried talking to colleges for premium offerings of leaderboards/score/etc." Broken crawlers "led to a lot of failure, incorrect data and skewed information." And: "I would not want candidates to be judged for their campus placements on StopStalk rating." It began as "stalking my friends' coding profiles... This used to be my motivation for practicing more" | [stopstalk.com](https://www.stopstalk.com/), 2025, primary. Noticed in Bangladesh on the [Toph forum](https://community.toph.co/t/stopstalk-is-discontinued-what-now/6645), 2025-08-23 |
| Third-party CF tools | "CList, Carrot ... etc. not working, CF API problem" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1t0lpkn/), 2026-05-01, archive |
| TLE's CP-31 sheet | Widely recommended as a rating ladder, but "recent problems are much tougher than cp31 sheet" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1x0nkhl/_/pemokmg/), 2026-10-08, archive |
| Codolio | "Codolio needs subscription" | [r/codeforces](https://www.reddit.com/r/codeforces/comments/1v56ws2/_/ozp3gse/), 2026-07-25, archive |
| Lockout Bot | Very popular (+506): "The bot gives a set of 5 problems with ratings from [x, x+400], where x is chosen by you", picked from problems neither player has solved. It later broke after Discord changes, and users kept asking why it was offline | [CF blog 78546](https://codeforces.com/blog/entry/78546), 2020 to 2023, primary |
| LeetCode | Added a follow button in February 2026 and a "Friends check-in" on the daily-problem calendar in September 2026. The incumbents are moving toward social features | [r/leetcode](https://www.reddit.com/r/leetcode/comments/1qumesk/), [r/leetcode](https://www.reddit.com/r/leetcode/comments/1wdp7v1/), archive |
| An old wish | "form groups showing every member's progress over daily basis... help college and school students better compete with each other all round the year" | [CodeChef Discuss](https://discuss.codechef.com/t/just-an-opinion/20187), 2018-09-26, primary |

### 4.6 Red flags: what turns comparison toxic

1. **Mocking low ratings.** The top reply to "CP is Depressing" was "only if you suck" (+142), followed by "I would say 'imagine being grey' but I am not a toxic person." (+65) ([CF blog 135193](https://codeforces.com/blog/entry/135193)). A class space can't import that tone.
2. **Envy and fixed mindsets** from raw rating comparison (§4.2).
3. **Fear of losing rating**, which leads people to skip contests ("My strategy is just to not participate in contests until I know I have got alot better", a comment on [CF blog 111521](https://codeforces.com/blog/entry/111521)) and sometimes to cheat.
4. **Streaks as leashes**, which end in burnout or in trivial-problem farming (§4.2, §4.4).
5. **Public accusation.** Vigilante threads expose suspected cheaters with tools that also flag honest people (§4.3).
6. **High stakes.** Colleges used StopStalk's rating for placements, and job markets that value CF rating push people to cheat ([CF blog 154602](https://codeforces.com/blog/entry/154602)).

### 4.7 Design implications

| Do or don't | Because |
|---|---|
| Score difficulty relative to the student's level, not volume | §4.4: volume without difficulty produced flat ratings and false confidence |
| Keep streaks gentle: cap rewarded days, never count a lone WA | §4.2, §4.4: burnout and farming |
| Reward showing up to contests, not the rating change | §4.2, §4.6: rating fear keeps people out of contests |
| Celebrate color changes and small wins in public | §4.1: the club that grew to 5 Experts did exactly this |
| Compare students with people who started near them | §4.2: students said so themselves |
| Keep integrity signals private and factual | §4.3, §4.6: outside detection is unreliable and public exposure is ugly |
| Don't turn GP into a grade or placement score by default | §4.5, §4.6: StopStalk's founder warned against exactly this |
| Make the class its own space | Advent of Code's private leaderboards survived when the global one didn't |
| Frame upsolving as "within reach" | §4.2: students skip upsolves that humble them |
| Don't depend on any one CF endpoint staying stable | §4.5: tools broke when the API changed |

---

## 5. Academic Evidence: When Does Comparison Help?

Peer comparison is a lever with two ends. Pulled one way it makes people push harder. Pulled the
other way it makes them quit. The research is fairly consistent about which end is which.

### 5.1 Leaderboards on their own are a coin flip

| Study | Setting | Result |
|---|---|---|
| [Bai et al. 2021](https://consensus.app/papers/details/922c460177975418b0a0b12bd4a03982/?utm_source=claude_desktop), *Computers & Education* | Two online courses, absolute vs relative leaderboards | The bottom third wanted to be **anonymous** on an absolute board but were happy to be **public** on a relative board |
| [Pickal et al. 2026](https://consensus.app/papers/details/9685cdec586f5556b40cfe8b2a7aa6c5/?utm_source=claude_desktop), *Learning and Individual Differences* | RCT, N = 427 | Motivation peaked for "higher position, trending up". Negative leaderboard feedback was **worse than no feedback** |
| [Do et al. 2024](https://consensus.app/papers/details/32380382dfd455da886f327a5fa1a518/?utm_source=claude_desktop), *Learning and Individual Differences* | Longitudinal quasi-experiment, college course | A leaderboard did not increase optional practice and **lowered exam scores** |
| [Bursztyn & Jensen 2015](https://consensus.app/papers/details/cba55e4e47355fc4af2fcec8dc7347a4/?utm_source=claude_desktop), *Quarterly Journal of Economics* | Natural experiment, computer-based high school courses | Adding a leaderboard cut performance 24%. Top students dropped 40% to avoid being seen on it |
| [Çiğdem et al. 2023](https://consensus.app/papers/details/bf8f5a2e3bbd552f9904be189b1255b9/?utm_source=claude_desktop), *Computer Applications in Engineering Education* | Programming course, N = 96 | Quiz completion fell after week 3 in both groups. The novelty wears off fast |
| [Costa 2023](https://consensus.app/papers/details/6e541144c09f5e708855d4df1f80dd29/?utm_source=claude_desktop), meta-analysis, programming learning | 15 effect sizes | Gamification helped (d = 0.4), but the effect came from **levels**. Leaderboards, points and badges alone showed no significant learning effect |
| [Ortiz-Rojas et al. 2019](https://consensus.app/papers/details/27bd8b50812a567694ddceddd946fda5/?utm_source=claude_desktop) | Intro programming, N = 89 | A leaderboard condition did improve learning, so it can work |

**Takeaway:** a plain all-time ranking, which is exactly what PROGNOS ships today, is the weakest
version of the idea. The design details decide the outcome.

### 5.2 Near peers push you, stars make you quit

| Study | Result |
|---|---|
| [Diel et al. 2021](https://consensus.app/papers/details/f50e18347b5f544a8fcd2f5588a54396/?utm_source=claude_desktop), *J. Personality & Social Psychology* (5,400+ real comparisons, preregistered) | Non-linear. A **moderate** upward gap increases effort. An **extreme** upward gap leads to giving up. Looking down leads to coasting. The push is stronger when people feel they control the outcome |
| [Diel et al. 2021](https://consensus.app/papers/details/87a75e9b3ff25d74aec25b135e2664d8/?utm_source=claude_desktop), elite athletes over a semester | Same shape. Training partners who were moderately better motivated, far better ones caused disengagement |
| [Rogers & Feller 2016](https://consensus.app/papers/details/86725f24d12a52768bfffc8ac37a0bc1/?utm_source=claude_desktop), *Psychological Science* (MOOC, N = 5,740) | Seeing exemplary peer work **caused** a large share of students to quit ("discouraged by peer excellence") |
| [Thiemann 2021](https://consensus.app/papers/details/1ac90daddeb1507aa3a1c599307f6d47/?utm_source=claude_desktop), *Management Science* | Low-ability students randomly grouped with high-ability peers had worse first-year grades and dropped out more |
| [Fleur et al. 2023](https://consensus.app/papers/details/630d4e2bcb3557f4a1704d1702dc6aad/?utm_source=claude_desktop), *Computers and Education Open* (2 RCTs) | A dashboard that compared each student to peers with **similar goals**, sampled to be **slightly better**, raised motivation and final grades |
| [Dijkstra et al. 2008](https://consensus.app/papers/details/69d3d07c2a785077924d6af66555fb14/?utm_source=claude_desktop), *Review of Educational Research* | Students naturally compare upward with **similar** classmates. It helps performance but costs self-esteem |
| [Boissicat et al. 2021](https://consensus.app/papers/details/a27582d3e0ca5f62a90e596f51696d7b/?utm_source=claude_desktop), *British J. Educational Psychology* | "Approach" framing turns an upward comparison into a boost. "Avoidance" framing turns it into a hit |

**Takeaway:** the comparison target should be the few people just above you, never the class star.
Phrase it as "you can catch them", not "you are behind".

### 5.3 Compare to yourself and to a goal, not only to others

| Study | Result |
|---|---|
| [Weidlich et al. 2024](https://consensus.app/papers/details/0480465d65655481b6d28a1b6478fe39/?utm_source=claude_desktop), *J. Computer Assisted Learning* (RCT, N = 282) | Pure peer-referenced feedback hurt motivation. Peer **plus** goal-referenced feedback gave the best motivational state |
| [Pekrun et al. 2014](https://consensus.app/papers/details/1f2081f6cb8e56ea8b6deda788d615b6/?utm_source=claude_desktop), *Learning and Instruction* | Feedback against your own past builds mastery goals. Feedback against others builds both "prove it" and "avoid failing" goals |
| [McColskey & Leary 1985](https://consensus.app/papers/details/4bdab3b8d3ce578196d2ae3b2f3a5cf3/?utm_source=claude_desktop) | Losing against peers makes people blame their ability. Losing against their own baseline makes them blame effort, which they can change |
| [Shin et al. 2017](https://consensus.app/papers/details/fb0cedae55cc54189b09078340d24137/?utm_source=claude_desktop), *Learning and Instruction* | Promotion framing ("here's what you gain") removes most of the harm of peer comparison |

**Takeaway:** every comparison PROGNOS shows should sit next to a self-referenced number ("you vs
your last 4 weeks") and a goal ("this week's target").

### 5.4 Teacher dashboards only work when the teacher acts

| Study | Result |
|---|---|
| [Herodotou et al. 2019](https://consensus.app/papers/details/f47bae6aac6359be922b6446e48e2e97/?utm_source=claude_desktop), *British J. Educational Technology* (14,000+ students) | Teachers who checked an at-risk dashboard regularly **and intervened** got significantly better results than the year before |
| [Karademir et al. 2024](https://consensus.app/papers/details/bcab2492b046536a959d3058b8d548ab/?utm_source=claude_desktop), *J. Learning Analytics* (403 students) | A dashboard with a **built-in feedback channel** raised learning gains. Teachers mostly sent process feedback ("try this approach"), the kind known to work |
| [Dai et al. 2025](https://consensus.app/papers/details/ab838e1825ba590e873a5ae98463f7d7/?utm_source=claude_desktop), *J. Learning Analytics* | An early at-risk flag plus a personal message brought back over 30% of flagged students within two weeks |
| [Ramaswami et al. 2022](https://consensus.app/papers/details/0cfc4d7ff0de5daebba2cdbef0851368/?utm_source=claude_desktop), review | Most dashboards stop at "this student is at risk" and never say what to do |

**Takeaway:** the teacher view should be an inbox of "who needs you and why", with the action one
click away. Charts alone change nothing.

### 5.5 Teams help, if nobody is a permanent loser

| Study | Result |
|---|---|
| [Sailer & Homner 2019](https://consensus.app/papers/details/848fef56a8d352b49110b45b36b4e4f2/?utm_source=claude_desktop), *Educational Psychology Review* (meta-analysis, 1,400+ citations) | Competition **combined with collaboration** was the most effective setup for changing behaviour |
| [Liu et al. 2022](https://consensus.app/papers/details/b900ffcd555c5caf862383e6289b0844/?utm_source=claude_desktop), *Sustainability* | Team-vs-team competition beat individual competition on learning |
| [Papadopoulos et al. 2024](https://consensus.app/papers/details/94a5106129455d78ac4d1919d3d729ab/?utm_source=claude_desktop), *Learning and Individual Differences* | The losing team did worse than the no-game control on every measure |

**Takeaway:** squads are worth building, but they need balanced rosters and short seasons that
reshuffle, so the same group doesn't lose every week.

## 6. First-Party Evidence: the PROGNOS Survey

From the project report (Section 3.2, n = 20, informal and indicative only):

| Finding | Share | What it means for Classroom |
|---|---|---|
| Visible peer progress would help me stay consistent | ~65% | The social layer is wanted, so the question is how to show it, not whether |
| Unsure which problem to attempt next | ~70% | A classroom should hand each student a next step, not only a rank |
| Codeforces is my main judge | ~80% | Building deep on Codeforces data is still the right call |
| Don't track weak tags systematically | ~85% | Class-level tag gaps are news to both students and teachers |

Note the other ~35%. A third of respondents did not say yes to visible peer progress. That's the
group the design has to protect.

---

## 7. Codeforces API Feasibility

What the official API can and can't support, checked against the docs and live calls on
2026-10-16.

**Open question, decides the design:** do private group-contest submissions show in anonymous user.status? Camp contest 710855 is "not found" anonymously and contest.list?groupCode returns [] (B6 P). Three handles who cheered the camp had no non-public contest IDs in their last 1,000 submissions (Aug-Oct 2026 covered), but they may not have competed. Test with a group member's key first. Note `contestId >= 100000` is only a heuristic for gym; group contests like 710855 sit in that range but not in the public gym list.

**Rate and auth**
- Limit: "at most 1 time per two seconds", else FAILED "Call limit exceeded" (B1 P); per-IP vs per-key is not stated. That is 43,200 calls/day; one user.status call per student is ~17 min per sweep for 500 students.
- Auth: apiKey, time (within 5 min of server time), apiSig = 6 random chars + SHA-512 hex of `rand/method?sorted params#secret` (B1 P).
- Request gzip. Uncompressed problemset.problems timed out after 120 s at 364 KB; compressed it finished in 2.5 s (B6 P).

**user.status** (handle, from, count; includeSources only for your own account, B2 P)
- Submission: id, contestId, creationTimeSeconds, relativeTimeSeconds, problem {index, name, rating, tags, points}, author (Party), language, verdict, testset, passedTestCount, time, memory (B3 P).
- author.participantType is one of CONTESTANT, PRACTICE, VIRTUAL, MANAGER, OUT_OF_COMPETITION (B3 P). In a top user's last 2,000 submissions: PRACTICE 783, CONTESTANT 655, OUT_OF_COMPETITION 427, VIRTUAL 135. Most PRACTICE rows (765) carry relativeTimeSeconds = 2147483647. author also has an undocumented participantId (B6 P).
- Public gym submissions appear (181 of 2,000, all in public gyms) with no problem.rating and empty tags (B6 P).
- Team submissions appear under every member, with teamId and teamName (45 of 2,000) (B6 P). Decide whether team solves count toward a student's total.

**problemset.problems** (tags, problemsetName): Problem list plus ProblemStatistics {contestId, index, solvedCount} (B2, B3 P). Test: 11,457 problems, 11,152 rated (800-3500), no gym problems; the 305 unrated include the latest rounds (2271-2276) and some old ones (B6 P).

**contest.standings** (changed ~Apr-May 2026)
- Regular contests: anonymous GET with contestId only, returning full official standings; handles, from/count, showUnofficial, participantTypes and auth are all rejected (B2 P; confirmed in B6). Mike Mirzayanov says responses are cached about 1-3 min and the change followed heavy automated use that slowed the site (B4 P).
- Gym and mashup (including group) contests: authenticated request from a user who can view the contest; optional parameters still work, handles up to 10,000 (B2, B4 P). An anonymous gym request returns "You have to be authenticated" (B6 P).
- So: one call per public round covers all participants (filter locally); virtual results come from user.status (VIRTUAL); group contests need a key from a coach or bot account in the group.

**Other methods**
- contest.status works anonymously with a handle on regular rounds and on public gyms (B6 P); asManager and includeSources need manager rights (B2 P).
- contest.ratingChanges?contestId works anonymously and returns a whole round in one call (round 2271: 9,768 rows, 162 KB gzip, ~30 s), so it beats user.rating per student after each round (B6 P); user.rating gives RatingChange {contestId, rank, oldRating, newRating, time} (B2, B3 P).
- contest.list: gym=true lists public gyms (2,660 in test); signed calls add the caller's mashups and private gyms; groupCode needs read access (B2, B6 P).
- group.isManager(groupCode, handles), signed only: confirms a coach really manages the CF group they link (B2 P).
- user.info accepts up to 10,000 handles per call (B2 P; batch confirmed in B6). No method lists group members or creates contests (B1 P).

**Terms and platform risk**
- The Terms forbid "selling, sublicensing and/or otherwise commercializing any Website material" and use "that impacts user access to this Website" (B7 P). A paid tier on CF data is a business risk; ask Codeforces before charging [inference].
- The standings change landed unannounced (users asked when it took effect) and broke Carrot and CF-Predictor (B4, B5 P). Build a degraded mode: cache, back off, keep working from user.status alone.

---

## 8. Sources

Community sources are linked inline in §4 and academic sources in §5.

### 8.1 Product teardown sources (C#)

| ID | URL | Date | Tag |
|---|---|---|---|
| C1 | github.com/cpinitiative/usaco-guide (src/models/groups/*, components/Groups/*, hooks/groups/usePostActions.ts, useLeaderboardData.tsx, functions/src/groups/submitToProblem.ts) | last Groups commit 2026-09-23 | primary |
| C2 | usaco.guide/announcements (Groups beta 2021-09-05; open creation 2022-06) | 2021-22 | snippet |
| C3 | github.com/kenkoooo/AtCoderProblems (interfaces/Status.ts, utils/TableColor.ts, pages/ListPage/ListTable.tsx, Internal/VirtualContest/ContestConfig.tsx, TrainingPage, UserPage) | last commit 2026-07-15 | primary |
| C4 | stopstalk.com (sunset notice) | 2025 | primary |
| C5 | github.com/stopstalk/stopstalk-deployment/blob/master/controllers/default.py | 2025-08 | primary |
| C6 | github.com/aropan/clist (src/true_coders/models.py, src/ranking/views.py, templates/party.html, templates/versus.html) | 2026 | primary |
| C7 | clist.by/versus/tourist/vs/jiangly/ | fetched 2026-10-16 | primary |
| C8 | codeforces.com/blog/entry/9687 | 2013 | snippet |
| C9 | codeforces.com/blog/entry/9905 | ~2015 | snippet |
| C10 | codeforces.com/blog/entry/19229 | ~2015 | snippet |
| C11 | codeforces.com/blog/entry/153241 | 2026, exact date unclear | snippet |
| C12 | codeforces.com/blog/entry/53145 | ~2017-19 | snippet |
| C13 | codeforces.com/blog/entry/1882; codeforces.com/blog/entry/140629; codeforces.com/blog/entry/65275 (status ?friends=on) | old; ~2025; 2019 | snippet |
| C14 | codeforces.com/blog/entry/79530 (EDU launch, ITMO pilot course) | 2020 | snippet |
| C15 | chromewebstore.google.com/detail/dgdegiibcnemkbmgjpchpgggmolfhgkl (Codeforces Group Stats, ~1,000 users) | 2026-02-16 | primary |
| C16 | codeforces.com/blog/entry/146049 (CF Gym Tracker) | ~2025 | snippet |
| C17 | pypi.org/project/conmato (group management CLI for coaches) | 2021 | snippet |
| C18 | vjudge.net/group; vjudge.net/group/alan | fetched 2026-10-16 | primary |
| C19 | codeforces.com/blog/entry/91139 | 2021 | snippet |
| C20 | in.linkedin.com/company/codolio; chromeboard.com/extension/codolio-hhldiohknhejgggdehdeepiggieflfjo | 2024-25 | snippet |
| C21 | codechef.com/collegechapter | n/d | snippet |
| C22 | sode-edu.in/smvitm/uncategorized/codechef-empowering-tech-education/ | AY 2024-25 | secondary |
| C23 | discuss.codechef.com/t/how-do-i-find-the-list-of-users-from-my-college-on-codechef/10351 | old | snippet |
| C24 | leetcode.com/discuss/post/3482910/ (study plan leaderboard) | ~2023 | snippet |
| C25 | leetcode.com/discuss/post/5736503/ (release notes, follow) | ~2024 | snippet |
| C26 | chromewebstore.google.com/detail/aajplhnjobdefcjgghdpanciaiioihhm (LeetCode Friends Rank Checker) | n/d | snippet |
| C27 | beecrowd.com/wp-content/uploads/2024/12/AOU-Case-Study-PT.pdf; .../CSED-Case-Study-PT.pdf | 2024-12 | primary |
| C28 | kattis.com/universities | fetched 2026-10-16 | primary |
| C29 | po.kattis.com/help/ranklist | n/d | snippet |
| C30 | github.com/DMOJ/online-judge (judge/models/profile.py, judge/models/contest.py) | 2026 | primary |
| C31 | toph.co/academic; toph.co | fetched 2026-10-16 | primary |
| C32 | hackerrank.com/schools; hackerrank-community-knowledge-base.help.usepylon.com/articles/7535813777-introduction-to-contest | 2026; 2025 | primary; snippet |
| C33 | help.hackerearth.com/hc/en-us/articles/360002657934 | n/d | primary |
| C34 | takeuforward.org/strivers-a2z-dsa-course/strivers-a2z-dsa-course-sheet-2 | fetched 2026-10-16 | primary |
| C35 | codeforces.com/blog/Priyansh31dec (CP-31 sheet); tle-eliminators.com/cp-sheet (no content returned) | n/d | snippet |
| C36 | github.com/cheran-senthil/TLE (tle/cogs/codeforces.py, duel.py, handles.py) | last push 2026-03-18 | primary |
| C37 | github.com/pseudocoder10/Lockout-Bot | last push 2022-10-03 | primary |
| C38 | github.com/NamanGandhi2005/student-codeforces-progress-manager; github.com/arunyerram/student-Progress-Manager; mintlify.wiki/aakash811/Student-Progress-Tracker/features/inactivity-alerts | 2025-06 to 2026 | primary (READMEs); snippet (mintlify) |
| C39 | github.com/0xPolybit/cp-reminder; github.com/ronisarkarexe/Leaderboard-Pro; github.com/4xush/CForge | 2023-26 | primary |
| C40 | blog.duolingo.com/duolingo-leagues-leaderboards/ | 2023-05-03 | primary |
| C41 | duolingo.deconstructoroffun.com/mechanics/leagues | n/d | secondary |
| C42 | blog.duolingo.com/friends-quests/ | 2022-09-09 | primary |
| C43 | blog.duolingo.com/product-lessons-friend-streak/ | 2024-09-20 | primary |
| C44 | support.strava.com/hc/en-us/articles/216918347-Clubs-on-Strava | fetched 2026-10-16 | primary |
| C45 | support.strava.com/hc/en-us/articles/360030851772-Segment-Leaderboard-Filters | n/d | snippet |
| C46 | dcrainmaker.com/2020/06/strava-legends-feature.html; androidcentral.com/strava-announces-local-legends-new-way-compete-segments | 2020 (premium-only status may be stale) | snippet |
| C47 | runningmagazine.ca/?p=91520 (Radboud University kudos study) | 2023-01-10 | secondary |
| C48 | docs.github.com/en/education/manage-coursework-with-github-classroom/teach-with-github-classroom/create-an-individual-assignment | fetched 2026-10-16 | primary |
| C49 | exercism.org/docs/using/feedback/private; exercism.org/docs/mentoring/faqs | fetched 2026-10-16 | primary |
| C50 | docs.codewars.com/community/following | fetched 2026-10-16 | primary |
| C51 | en.wikipedia.org/wiki/Kaggle (2,973 Masters, 612 GMs of 23.29M accounts, 2025-04-02) | 2025 | secondary |
| C52 | codeforces.com/blog/entry/154304 (beginners quit after comparing themselves on standings) | ~2026 | snippet |
| C53 | hackerearth.com/recruit/customers/svec-recruitments (professors follow students on a live dashboard) | n/d | snippet |
| C54 | codechef.com/aboutus; public CodeChef profiles showing Learning and Practice Paths with completion % | n/d | snippet |

### 8.2 Program and API sources (B#)

- B1 P https://codeforces.com/apiHelp (2026-10-16)
- B2 P https://codeforces.com/apiHelp/methods (2026-10-16)
- B3 P https://codeforces.com/apiHelp/objects (2026-10-16)
- B4 P https://codeforces.com/blog/entry/153241 (post ~Apr 2026, Mirzayanov comment ~May 2026)
- B5 P https://codeforces.com/blog/entry/153167 (~Apr 2026)
- B6 P own anonymous API calls on 2026-10-16: user.status (4 handles), contest.standings 566 and 104857, contest.status 566/104857/710855, contest.list gym and groupCode, problemset.problems, contest.ratingChanges 2271, user.info
- B7 P https://codeforces.com/terms (2026-10-16)
- B8 P https://codeforces.com/blog/entry/133941 (revision 2024-09-14)
- B9 P https://codeforces.com/blog/entry/155816 (~Aug 2026)
- B10 P https://www.tle-eliminators.com/faqs (2026-10-16)
- B11 P https://www.tle-eliminators.com/ (2026-10-16)
- B12 P https://codeforces.com/blog/entry/139079 (~Feb 2025)
- B13 P https://codeforces.com/blog/entry/149065 (~Dec 2025)
- B14 Snip https://peerlist.io/company/tle_eliminators/courses/tle-90-level-2 (also level-3, level-4; undated)
- B15 P https://phitron.io/ (2026-10-16)
- B16 P https://cpsacademy.io/cpc (2026-10-16)
- B17 P https://maang.in/ (2026-10-16)
- B18 P https://www.algouniversity.com/ (2026-10-16)
- B19 Snip https://wordpress-blog.centralindia.cloudapp.azure.com/blog/?p=8265 (Coding Ninjas blog, undated)
- B20 Snip https://codechef.com/collegechapter (404 on 2026-10-16)
- B21 P https://gcpc.daffodilvarsity.edu.bd/wing-acm (undated)
- B22 Sec https://www.thedailystar.net/node/1481623 (2017-10-25)
- B23 P https://icpc.bubt.edu.bd/slot-distribution.php (2025 season)
- B24 P https://ioinformatics.org/journal/INFOL122.pdf (2013)
- B25 P https://life.aun.edu.eg/fci/sites/default/files/units/11.pdf (undated)
- B26 P https://www.comp.nus.edu.sg/~stevenha/cs3233.html (AY2025/26 B2)
- B27 P https://www.eecs.mit.edu/a-satisfying-solve/ (2022-11-21)
- B28 P https://www.ucf.edu/news/ucf-to-compete-in-the-international-collegiate-programming-contests-2026-world-finals-after-top-5-finish/ (2026-03-25)
- B29 P https://uwaterloo.ca/computer-science/events/next-local-icpc-style-programming-contest (2019)
- B30 P https://www.cc.gatech.edu/news/competitive-programming-team-excels-major-competitions (2025-01-27)
- B31 P https://uw-programming.netlify.app/ (undated)
- B32 P https://www.competemcgill.com/ (undated)
- B33 Snip https://codeforces.com/blog/Ohhiokbye (~Feb 2023)
- B34 P https://usaco.org/ (2025-26 season)
- B35 P https://joincpi.org/classes (undated) and https://forum.usaco.guide/t/want-to-improve-at-usaco-register-for-live-online-classes/1983 (2021-09-20)
- B36 Snip https://www.placementpreparation.io/blog/how-to-prepare-for-zco-inoi-ioi/ (2026, commercial)
- B37 P https://codeforces.com/blog/entry/43212 (2016)
- B38 P https://u.icpc.global/camps/ (verified 2026-08-03)
- B39 Snip https://is.ifmo.ru/programming_competitions/2011/ICPC-CLIS-2011-presentation.pdf (2011)
- B40 P https://codeforces.com/blog/entry/68927 (~2019) and https://github.com/cheran-senthil/TLE
- B41 Snip https://codeforces.com/topic/120971/en3 (undated)
- B42 Snip https://mirror.codeforces.com/blog/esum (Sep 2025), https://mirror.codeforces.com/blog/kkwlski (Jan 2026), https://codeforces.com/blog/Meri2024 (Jun 2026)
- B43 Snip https://www.bracu.ac.bd/news/brac-university-computer-club-organizes-workshop-competitive-programming (2023)
- B44 Snip https://codeforces.com/blog/Bublick (2022)
- B45 Snip https://orieladmissions.com/usaco/ (undated)
- B46 Snip https://github.com/YousefMahmoudMalek/CodeForces_Activity_Tracker and https://codeforces.com/blog/entry/124570 (undated)

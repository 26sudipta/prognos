import { apiFetch } from "./api";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ContestItem {
  id: string;
  clist_id: number;
  platform: string;
  name: string;
  start_time: string; // ISO UTC
  end_time: string;   // ISO UTC
  duration_seconds: number;
  url: string;
  last_synced_at: string;
}

export interface ContestsListResponse {
  contests: ContestItem[];
  total: number;
  is_stale: boolean;
}

// ─── API ──────────────────────────────────────────────────────────────────────

export interface FetchContestsParams {
  platform?: string[];
  from_dt?: string;
  to_dt?: string;
  limit?: number;
  offset?: number;
}

export async function fetchContests(
  token: string,
  params: FetchContestsParams = {},
): Promise<ContestsListResponse> {
  const qs = new URLSearchParams();
  params.platform?.forEach((p) => qs.append("platform", p));
  if (params.from_dt) qs.set("from_dt", params.from_dt);
  if (params.to_dt) qs.set("to_dt", params.to_dt);
  if (params.limit != null) qs.set("limit", String(params.limit));
  if (params.offset != null) qs.set("offset", String(params.offset));
  const query = qs.toString() ? `?${qs.toString()}` : "";
  const res = await apiFetch(`/api/v1/contests${query}`, { token });
  if (!res.ok) throw new Error("fetch contests failed");
  return res.json();
}

export async function fetchContestPlatforms(token: string): Promise<string[]> {
  const res = await apiFetch("/api/v1/contests/platforms", { token });
  if (!res.ok) throw new Error("fetch platforms failed");
  return res.json();
}

// ─── Platform identity ────────────────────────────────────────────────────────

const PLATFORM_COLORS: Record<string, string> = {
  "codeforces.com":  "#1A81C4",
  "atcoder.jp":      "#9B7EC8",
  "leetcode.com":    "#FFA116",
  "codechef.com":    "#F0923B",
  "hackerrank.com":  "#00EA64",
  "hackerearth.com": "#44C4A1",
  "topcoder.com":    "#EF3A3A",
  "codingcompetitions.withgoogle.com": "#4285F4",
};

const PLATFORM_ABBR: Record<string, string> = {
  "codeforces.com":  "CF",
  "atcoder.jp":      "AC",
  "leetcode.com":    "LC",
  "codechef.com":    "CC",
  "hackerrank.com":  "HR",
  "hackerearth.com": "HE",
  "topcoder.com":    "TC",
  "codingcompetitions.withgoogle.com": "GC",
};

const PLATFORM_DISPLAY: Record<string, string> = {
  "codeforces.com":  "Codeforces",
  "atcoder.jp":      "AtCoder",
  "leetcode.com":    "LeetCode",
  "codechef.com":    "CodeChef",
  "hackerrank.com":  "HackerRank",
  "hackerearth.com": "HackerEarth",
  "topcoder.com":    "Topcoder",
  "codingcompetitions.withgoogle.com": "Google",
};

export function platformColor(platform: string): string {
  return PLATFORM_COLORS[platform.toLowerCase()] ?? "#64748B";
}

export function platformAbbr(platform: string): string {
  return PLATFORM_ABBR[platform.toLowerCase()] ?? platform.slice(0, 2).toUpperCase();
}

export function platformDisplayName(platform: string): string {
  return PLATFORM_DISPLAY[platform.toLowerCase()] ?? platform;
}

// ─── Time / date utilities ────────────────────────────────────────────────────

// "Jun 28 · 17:35" — compact, no weekday
export function formatLocalDateShort(isoStr: string): string {
  const d = new Date(isoStr);
  const datePart = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `${datePart} · ${formatLocalTimeOnly(isoStr)}`;
}

// "HH:MM" in local TZ — reliable across locales
export function formatLocalTimeOnly(isoStr: string): string {
  const d = new Date(isoStr);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

// "Sat, Jul 12 · 17:35" in local TZ
export function formatLocalDateTimeShort(isoStr: string): string {
  const d = new Date(isoStr);
  const datePart = d.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
  return `${datePart} · ${formatLocalTimeOnly(isoStr)}`;
}

// "Saturday, July 12 at 17:35" in local TZ — for modal
export function formatLocalDateTimeLong(isoStr: string): string {
  const d = new Date(isoStr);
  const datePart = d.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
  return `${datePart} at ${formatLocalTimeOnly(isoStr)}`;
}

// "Saturday, July 12" — for list group headers
export function formatDateHeader(localDateKey: string): string {
  // Use T12:00:00 to avoid DST midnight edge cases when parsing a date-only string
  const d = new Date(`${localDateKey}T12:00:00`);
  return d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
}

// "YYYY-MM-DD" in local TZ — stable grouping key
export function localDateKey(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

// End-time label that includes the date when the contest crosses midnight locally
export function formatLocalEndLabel(startIsoStr: string, endIsoStr: string): string {
  if (localDateKey(new Date(startIsoStr)) === localDateKey(new Date(endIsoStr))) {
    return formatLocalTimeOnly(endIsoStr);
  }
  return formatLocalDateTimeShort(endIsoStr);
}

// "2h", "2h 15m", "45m"
export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

// ─── Contest grouping ─────────────────────────────────────────────────────────

export interface ContestGroup {
  date: string;  // "YYYY-MM-DD" in local TZ
  contests: ContestItem[];
}

export function groupContestsByLocalDate(contests: ContestItem[]): ContestGroup[] {
  const groups = new Map<string, ContestItem[]>();
  for (const c of contests) {
    const key = localDateKey(new Date(c.start_time));
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(c);
  }
  return Array.from(groups.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([date, cs]) => ({ date, contests: cs }));
}

// ─── Urgency swim-lane grouping ───────────────────────────────────────────────

export type UrgencyLane = "live" | "today" | "this-week" | "next-week" | "later";

export interface ContestLane {
  lane: UrgencyLane;
  label: string;
  contests: ContestItem[];
}

const LANE_LABELS: Record<UrgencyLane, string> = {
  live: "Live Now",
  today: "Today",
  "this-week": "This Week",
  "next-week": "Next Week",
  later: "Later",
};

const LANE_ORDER: UrgencyLane[] = ["live", "today", "this-week", "next-week", "later"];

export function groupContestsByUrgency(contests: ContestItem[]): ContestLane[] {
  const now = new Date();
  const nowMs = now.getTime();
  const todayKey = localDateKey(now);

  // Mon of current week (local time)
  const dow = now.getDay(); // 0=Sun, 1=Mon … 6=Sat
  const daysToMon = dow === 0 ? -6 : 1 - dow;
  const monday = new Date(now);
  monday.setDate(now.getDate() + daysToMon);
  monday.setHours(0, 0, 0, 0);

  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  sunday.setHours(23, 59, 59, 999);

  const nextSunday = new Date(sunday);
  nextSunday.setDate(sunday.getDate() + 7);
  nextSunday.setHours(23, 59, 59, 999);

  const buckets: Record<UrgencyLane, ContestItem[]> = {
    live: [],
    today: [],
    "this-week": [],
    "next-week": [],
    later: [],
  };

  for (const c of contests) {
    const start = new Date(c.start_time).getTime();
    const end = new Date(c.end_time).getTime();

    if (nowMs >= start && nowMs < end) {
      buckets.live.push(c);
    } else if (start > nowMs) {
      const startDate = new Date(c.start_time);
      if (localDateKey(startDate) === todayKey) {
        buckets.today.push(c);
      } else if (startDate <= sunday) {
        buckets["this-week"].push(c);
      } else if (startDate <= nextSunday) {
        buckets["next-week"].push(c);
      } else {
        buckets.later.push(c);
      }
    }
    // ended contests are omitted from swim lanes
  }

  for (const lane of LANE_ORDER) {
    buckets[lane].sort(
      (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime(),
    );
  }

  return LANE_ORDER.filter((lane) => buckets[lane].length > 0).map((lane) => ({
    lane,
    label: LANE_LABELS[lane],
    contests: buckets[lane],
  }));
}

// ─── Calendar week helpers ────────────────────────────────────────────────────

// Returns 7 Date objects for Mon–Sun of the week at the given offset (0 = current week)
export function getLocalWeekDays(weekOffset: number): Date[] {
  const now = new Date();
  const dayOfWeek = now.getDay(); // 0=Sun, 1=Mon … 6=Sat
  const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;

  const monday = new Date(now);
  monday.setDate(now.getDate() + daysToMonday + weekOffset * 7);
  monday.setHours(0, 0, 0, 0);

  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d;
  });
}

// ISO bounds to send to API when fetching calendar data
export function getWeekBoundsISO(weekOffset: number): { from_dt: string; to_dt: string } {
  const days = getLocalWeekDays(weekOffset);
  const start = new Date(days[0]);
  start.setHours(0, 0, 0, 0);
  const end = new Date(days[6]);
  end.setHours(23, 59, 59, 999);
  return { from_dt: start.toISOString(), to_dt: end.toISOString() };
}

// ─── Hero helpers ─────────────────────────────────────────────────────────────

// First contest that is live or the next upcoming one
export function getNextContest(contests: ContestItem[]): ContestItem | null {
  const now = Date.now();
  const live = contests.find((c) => {
    const s = new Date(c.start_time).getTime();
    const e = new Date(c.end_time).getTime();
    return now >= s && now < e;
  });
  if (live) return live;
  return contests.find((c) => new Date(c.start_time).getTime() > now) ?? null;
}

import { apiFetch } from "./api";

export interface HeatmapDay {
  date: string;
  count: number;
}

export interface DashboardData {
  heatmap: HeatmapDay[];
  current_streak: number;
  longest_streak: number;
  total_solved: number;
  cf_rating: number | null;
  has_verified_handle: boolean;
  is_syncing: boolean;
}

export interface TagStat {
  tag: string;
  solved_count: number;
  attempt_count: number;
  acceptance_rate: number;
  last_activity_at: string | null;
}

export interface RatingEntry {
  cf_contest_id: number;
  contest_name: string;
  old_rating: number;
  new_rating: number;
  delta: number;
  rank: number;
  contest_time: string;
}

export type WeaknessSignalType = "low_success" | "neglected" | "under_practiced";

export interface WeaknessSignal {
  id: string;
  tag: string;
  signal_type: WeaknessSignalType;
  score: number;
  reason: string;
  computed_at: string;
}

export interface Recommendation {
  id: string;
  problem_id: string;
  problem_name: string;
  tag: string;
  difficulty: number;
  url: string;
  reason: string;
  position: number;
}

export interface RecommendationSet {
  id: string;
  generated_at: string;
  recommendations: Recommendation[];
}

export async function fetchDashboard(token: string): Promise<DashboardData> {
  const res = await apiFetch("/api/v1/analytics/dashboard", { token });
  if (!res.ok) throw new Error("fetch dashboard failed");
  return res.json();
}

export async function fetchTags(token: string): Promise<TagStat[]> {
  const res = await apiFetch("/api/v1/analytics/tags", { token });
  if (!res.ok) throw new Error("fetch tags failed");
  return res.json();
}

export async function fetchRatingHistory(token: string): Promise<RatingEntry[]> {
  const res = await apiFetch("/api/v1/analytics/rating-history", { token });
  if (!res.ok) throw new Error("fetch rating history failed");
  return res.json();
}

export async function fetchWeaknesses(token: string): Promise<WeaknessSignal[]> {
  const res = await apiFetch("/api/v1/analytics/weaknesses", { token });
  if (!res.ok) throw new Error("fetch weaknesses failed");
  return res.json();
}

export async function fetchRecommendations(token: string): Promise<RecommendationSet | null> {
  const res = await apiFetch("/api/v1/analytics/recommendations", { token });
  if (!res.ok) throw new Error("fetch recommendations failed");
  return res.json();
}

export async function refreshRecommendations(token: string): Promise<RecommendationSet | null> {
  const res = await apiFetch("/api/v1/analytics/recommendations/refresh", {
    token,
    method: "POST",
  });
  if (!res.ok) throw new Error("refresh recommendations failed");
  return res.json();
}

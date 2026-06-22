"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Link2 } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import {
  fetchDashboard,
  fetchTags,
  fetchRatingHistory,
  fetchWeaknesses,
  fetchRecommendations,
  type DashboardData,
  type TagStat,
  type RatingEntry,
  type WeaknessSignal,
  type RecommendationSet,
} from "@/app/_lib/analytics";
import { StatStrip, StatStripSkeleton } from "./_components/stat-strip";
import { ActivityHeatmap, HeatmapSkeleton } from "./_components/activity-heatmap";
import { RatingChart, RatingChartSkeleton } from "./_components/rating-chart";
import { TagStats, TagStatsSkeleton } from "./_components/tag-stats";
import { WeaknessCards, WeaknessCardsSkeleton } from "./_components/weakness-cards";
import { Recommendations, RecommendationsSkeleton } from "./_components/recommendations";

// undefined = still loading; null = loaded but empty/error
type Async<T> = T | undefined | null;

const EMPTY_DASHBOARD: DashboardData = {
  heatmap: [],
  current_streak: 0,
  longest_streak: 0,
  total_solved: 0,
  cf_rating: null,
};

function noHandleLinked(d: DashboardData): boolean {
  return d.heatmap.length === 0 && d.total_solved === 0 && d.cf_rating === null;
}

export default function DashboardPage() {
  const { token } = useAuth();

  const [dashboard, setDashboard] = useState<Async<DashboardData>>(undefined);
  const [tags, setTags] = useState<Async<TagStat[]>>(undefined);
  const [ratingHistory, setRatingHistory] = useState<Async<RatingEntry[]>>(undefined);
  const [weaknesses, setWeaknesses] = useState<Async<WeaknessSignal[]>>(undefined);
  // undefined = loading, null = fetched but no set exists, RecommendationSet = has data
  const [recs, setRecs] = useState<RecommendationSet | null | undefined>(undefined);

  useEffect(() => {
    if (!token) return;

    fetchDashboard(token)
      .then(setDashboard)
      .catch(() => setDashboard(EMPTY_DASHBOARD));

    fetchTags(token)
      .then(setTags)
      .catch(() => setTags([]));

    fetchRatingHistory(token)
      .then(setRatingHistory)
      .catch(() => setRatingHistory([]));

    fetchWeaknesses(token)
      .then(setWeaknesses)
      .catch(() => setWeaknesses([]));

    fetchRecommendations(token)
      .then(setRecs)
      .catch(() => setRecs(null));
  }, [token]);

  // Show nudge if handle isn't linked yet (all endpoints return empty state)
  if (dashboard !== undefined && dashboard !== null && noHandleLinked(dashboard)) {
    return <NoHandleNudge />;
  }

  return (
    <div className="space-y-5 max-w-[1100px]">
      {/* Row 1 — stat strip */}
      {dashboard === undefined ? (
        <StatStripSkeleton />
      ) : (
        <StatStrip data={dashboard ?? EMPTY_DASHBOARD} />
      )}

      {/* Row 2 — activity heatmap */}
      {dashboard === undefined ? (
        <HeatmapSkeleton />
      ) : (
        <ActivityHeatmap data={(dashboard ?? EMPTY_DASHBOARD).heatmap} />
      )}

      {/* Row 3 — rating chart (60%) + tag stats (40%) */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        <div className="lg:col-span-3">
          {ratingHistory === undefined ? (
            <RatingChartSkeleton />
          ) : (
            <RatingChart data={ratingHistory ?? []} />
          )}
        </div>
        <div className="lg:col-span-2">
          {tags === undefined ? <TagStatsSkeleton /> : <TagStats data={tags ?? []} />}
        </div>
      </div>

      {/* Row 4 — weaknesses + recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div>
          {weaknesses === undefined ? (
            <WeaknessCardsSkeleton />
          ) : (
            <WeaknessCards data={weaknesses ?? []} />
          )}
        </div>
        <div>
          {recs === undefined ? (
            <RecommendationsSkeleton />
          ) : (
            <Recommendations data={recs} />
          )}
        </div>
      </div>
    </div>
  );
}

function NoHandleNudge() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-10 max-w-md w-full text-center">
        <div className="flex items-center justify-center w-14 h-14 rounded-full bg-bg-surface-raised border border-border-default mx-auto mb-5">
          <Link2 className="w-6 h-6 text-primary-400" />
        </div>
        <h2 className="text-lg font-semibold text-text-primary mb-2">
          Link your Codeforces handle to unlock your analytics.
        </h2>
        <p className="text-sm text-text-muted mb-6 leading-relaxed">
          Verify your handle once and PROGNOS will automatically track your ratings,
          streaks, and problem-solving patterns.
        </p>
        <Link
          href="/handles"
          className="inline-block bg-primary-500 hover:bg-primary-600 text-white text-sm font-semibold px-6 py-2.5 rounded-lg transition-colors"
        >
          Go to Handles →
        </Link>
      </div>
    </div>
  );
}

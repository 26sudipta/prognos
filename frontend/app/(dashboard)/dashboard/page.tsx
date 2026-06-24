"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { Link2, RefreshCw } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import {
  fetchDashboard,
  fetchTags,
  fetchRatingHistory,
  fetchWeaknesses,
  fetchRecommendations,
  refreshRecommendations,
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
  has_verified_handle: true, // don't show nudge on fetch failure
  is_syncing: false,
};

function noHandleLinked(d: DashboardData): boolean {
  return !d.has_verified_handle;
}

export default function DashboardPage() {
  const { token } = useAuth();

  const [dashboard, setDashboard] = useState<Async<DashboardData>>(undefined);
  const [tags, setTags] = useState<Async<TagStat[]>>(undefined);
  const [ratingHistory, setRatingHistory] = useState<Async<RatingEntry[]>>(undefined);
  const [weaknesses, setWeaknesses] = useState<Async<WeaknessSignal[]>>(undefined);
  // undefined = loading, null = fetched but no set exists, RecommendationSet = has data
  const [recs, setRecs] = useState<RecommendationSet | null | undefined>(undefined);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function loadAll(tok: string) {
    fetchDashboard(tok)
      .then((d) => {
        setDashboard(d);
        // Poll every 5s while sync is in progress; stop once completed
        if (d.is_syncing) {
          if (!pollRef.current) {
            pollRef.current = setInterval(() => {
              fetchDashboard(tok).then((fresh) => {
                setDashboard(fresh);
                if (!fresh.is_syncing) {
                  clearInterval(pollRef.current!);
                  pollRef.current = null;
                  // Reload all other sections once sync finishes
                  fetchTags(tok).then(setTags).catch(() => setTags([]));
                  fetchRatingHistory(tok).then(setRatingHistory).catch(() => setRatingHistory([]));
                  fetchWeaknesses(tok).then(setWeaknesses).catch(() => setWeaknesses([]));
                  fetchRecommendations(tok).then(setRecs).catch(() => setRecs(null));
                }
              }).catch(() => {});
            }, 5000);
          }
        } else {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
        }
      })
      .catch(() => setDashboard(EMPTY_DASHBOARD));

    fetchTags(tok).then(setTags).catch(() => setTags([]));
    fetchRatingHistory(tok).then(setRatingHistory).catch(() => setRatingHistory([]));
    fetchWeaknesses(tok).then(setWeaknesses).catch(() => setWeaknesses([]));
    fetchRecommendations(tok).then(setRecs).catch(() => setRecs(null));
  }

  const handleRefresh = useCallback(async () => {
    if (!token || isRefreshing) return;
    setIsRefreshing(true);
    try {
      const fresh = await refreshRecommendations(token);
      setRecs(fresh);
    } catch {
      // silently ignore — old recs remain shown
    } finally {
      setIsRefreshing(false);
    }
  }, [token, isRefreshing]);

  useEffect(() => {
    if (!token) return;
    loadAll(token);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // Show nudge if handle isn't linked yet (all endpoints return empty state)
  if (dashboard !== undefined && dashboard !== null && noHandleLinked(dashboard)) {
    return <NoHandleNudge />;
  }

  return (
    <div className="space-y-5 max-w-[1400px] mx-auto">
      {/* Sync banner — shown while initial sync is running */}
      {dashboard && dashboard.is_syncing && (
        <div className="flex items-center gap-3 px-4 py-3 bg-primary-500/10 border border-primary-500/25 rounded-xl text-sm text-primary-300">
          <RefreshCw className="w-4 h-4 shrink-0 animate-spin text-primary-400" />
          <span>Syncing your Codeforces data&hellip; This usually takes 1–2 minutes. The page will update automatically.</span>
        </div>
      )}

      {/* Row 1 — stat strip */}
      {dashboard === undefined ? (
        <StatStripSkeleton />
      ) : (
        <StatStrip
          data={dashboard ?? EMPTY_DASHBOARD}
          peakRating={
            ratingHistory && ratingHistory.length > 0
              ? Math.max(...ratingHistory.map((r) => r.new_rating))
              : null
          }
        />
      )}

      {/* Row 2 — activity heatmap */}
      {dashboard === undefined ? (
        <HeatmapSkeleton />
      ) : (
        <ActivityHeatmap data={(dashboard ?? EMPTY_DASHBOARD).heatmap} />
      )}

      {/* Row 3 — rating chart (60%) + tag stats (40%) */}
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-5">
        <div className="lg:col-span-7 flex flex-col">
          {ratingHistory === undefined ? (
            <RatingChartSkeleton />
          ) : (
            <RatingChart data={ratingHistory ?? []} />
          )}
        </div>
        <div className="lg:col-span-3 flex flex-col">
          {tags === undefined ? <TagStatsSkeleton /> : <TagStats data={tags ?? []} />}
        </div>
      </div>

      {/* Row 4 — weaknesses + recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">
        <div>
          {weaknesses === undefined ? (
            <WeaknessCardsSkeleton />
          ) : (
            <WeaknessCards
              data={weaknesses ?? []}
              recTags={recs?.recommendations.map((r) => r.tag) ?? []}
            />
          )}
        </div>
        <div>
          {recs === undefined ? (
            <RecommendationsSkeleton />
          ) : (
            <Recommendations
              data={recs}
              onRefresh={handleRefresh}
              isRefreshing={isRefreshing}
            />
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

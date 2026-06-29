"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { Link2, RefreshCw } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import {
  fetchDashboard,
  fetchTags,
  fetchWeaknesses,
  fetchRecommendations,
  refreshRecommendations,
  type DashboardData,
  type TagStat,
  type WeaknessSignal,
  type RecommendationSet,
} from "@/app/_lib/analytics";
import { TagStats, TagStatsSkeleton } from "../dashboard/_components/tag-stats";
import { WeaknessCards, WeaknessCardsSkeleton } from "../dashboard/_components/weakness-cards";
import { Recommendations, RecommendationsSkeleton } from "../dashboard/_components/recommendations";

type Async<T> = T | undefined | null;

const EMPTY_DASHBOARD: DashboardData = {
  heatmap: [],
  current_streak: 0,
  longest_streak: 0,
  total_solved: 0,
  cf_rating: null,
  has_verified_handle: true,
  is_syncing: false,
};

export default function InsightsPage() {
  const { token } = useAuth();

  const [dashboard, setDashboard] = useState<Async<DashboardData>>(undefined);
  const [tags, setTags] = useState<Async<TagStat[]>>(undefined);
  const [weaknesses, setWeaknesses] = useState<Async<WeaknessSignal[]>>(undefined);
  const [recs, setRecs] = useState<RecommendationSet | null | undefined>(undefined);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function loadAll(tok: string) {
    fetchDashboard(tok)
      .then((d) => {
        setDashboard(d);
        if (d.is_syncing) {
          if (!pollRef.current) {
            pollRef.current = setInterval(() => {
              fetchDashboard(tok)
                .then((fresh) => {
                  setDashboard(fresh);
                  if (!fresh.is_syncing) {
                    clearInterval(pollRef.current!);
                    pollRef.current = null;
                    fetchTags(tok).then(setTags).catch(() => setTags([]));
                    fetchWeaknesses(tok).then(setWeaknesses).catch(() => setWeaknesses([]));
                    fetchRecommendations(tok).then(setRecs).catch(() => setRecs(null));
                  }
                })
                .catch(() => {});
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

  if (dashboard !== undefined && dashboard !== null && !dashboard.has_verified_handle) {
    return <NoHandleNudge />;
  }

  const lastAnalyzed =
    weaknesses && weaknesses.length > 0
      ? new Date(weaknesses[0].computed_at).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
        })
      : null;

  return (
    <div className="space-y-5 max-w-[1400px] mx-auto">
      {/* Sync banner */}
      {dashboard && dashboard.is_syncing && (
        <div className="flex items-center gap-3 px-4 py-3 bg-primary-500/10 border border-primary-500/25 rounded-xl text-sm text-primary-300">
          <RefreshCw className="w-4 h-4 shrink-0 animate-spin text-primary-400" />
          <span>
            Syncing your Codeforces data&hellip; This usually takes 1&ndash;2 minutes. The page
            will update automatically.
          </span>
        </div>
      )}

      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-text-primary">Insights</h1>
        <p className="text-sm text-text-muted mt-0.5">
          {lastAnalyzed
            ? `Last analyzed ${lastAnalyzed}`
            : "Tag breakdown, focus areas, and practice recommendations."}
        </p>
      </div>

      {/* Row 1 — tag performance (left) + focus areas (right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">
        <div>
          {tags === undefined ? <TagStatsSkeleton /> : <TagStats data={tags ?? []} />}
        </div>
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
      </div>

      {/* Row 2 — recommendations (full width) */}
      {recs === undefined ? (
        <RecommendationsSkeleton />
      ) : (
        <Recommendations data={recs} onRefresh={handleRefresh} isRefreshing={isRefreshing} />
      )}
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
          Link your Codeforces handle to unlock insights.
        </h2>
        <p className="text-sm text-text-muted mb-6 leading-relaxed">
          Verify your handle once and PROGNOS will analyze your tag performance, detect weak
          areas, and recommend problems to practice.
        </p>
        <Link
          href="/handles"
          className="inline-block bg-primary-500 hover:bg-primary-600 text-white text-sm font-semibold px-6 py-2.5 rounded-lg transition-colors"
        >
          Go to Handles &rarr;
        </Link>
      </div>
    </div>
  );
}

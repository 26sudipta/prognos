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

function relativeDate(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diffMs / 86_400_000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

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

  // Computed stats
  const totalFocusAreas = Array.isArray(weaknesses) ? weaknesses.length : null;
  const highPriority = Array.isArray(weaknesses)
    ? weaknesses.filter((w) => w.signal_type === "low_success").length
    : null;
  const worstTag =
    Array.isArray(tags) && tags.length > 0
      ? (tags.filter((t) => t.attempt_count >= 5).sort((a, b) => a.acceptance_rate - b.acceptance_rate)[0] ?? null)
      : null;
  const lastAnalyzed =
    Array.isArray(weaknesses) && weaknesses.length > 0
      ? relativeDate(weaknesses[0].computed_at)
      : null;
  const statsLoading = weaknesses === undefined || tags === undefined;

  return (
    <div className="h-full flex flex-col gap-4 max-w-[1400px] mx-auto">
      {/* Sync banner */}
      {dashboard && dashboard.is_syncing && (
        <div className="flex items-center gap-3 px-4 py-3 bg-primary-500/10 border border-primary-500/25 rounded-xl text-sm text-primary-300 shrink-0">
          <RefreshCw className="w-4 h-4 shrink-0 animate-spin text-primary-400" />
          <span>
            Syncing your Codeforces data&hellip; This usually takes 1&ndash;2 minutes. The
            page will update automatically.
          </span>
        </div>
      )}

      {/* Weak stats strip */}
      {statsLoading ? (
        <div className="grid grid-cols-4 gap-4 shrink-0">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="bg-bg-surface border border-border-subtle rounded-xl px-5 py-4">
              <div className="skeleton h-2.5 w-20 mb-3" />
              <div className="skeleton h-7 w-12 mb-1.5" />
              <div className="skeleton h-2.5 w-24" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-4 gap-4 shrink-0">
          <StatCard
            label="Focus Areas"
            value={totalFocusAreas ?? 0}
            sub="total signals detected"
          />
          <StatCard
            label="High Priority"
            value={highPriority ?? 0}
            sub="low success rate tags"
            valueColor={highPriority ? "#F87171" : undefined}
          />
          <StatCard
            label="Weakest Tag"
            value={worstTag?.tag ?? "—"}
            sub={worstTag ? `${(worstTag.acceptance_rate * 100).toFixed(0)}% solved` : "no data yet"}
            subColor={worstTag ? "#F87171" : undefined}
            mono={false}
          />
          <StatCard
            label="Last Analyzed"
            value={lastAnalyzed ?? "—"}
            sub="weakness signals refreshed"
            mono={false}
          />
        </div>
      )}

      {/* Bottom: Focus Areas | Recommendations — fills remaining height */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
        <div className="h-full min-h-0">
          {weaknesses === undefined ? (
            <WeaknessCardsSkeleton />
          ) : (
            <WeaknessCards
              data={weaknesses ?? []}
              recTags={recs?.recommendations.map((r) => r.tag) ?? []}
            />
          )}
        </div>
        <div className="h-full min-h-0">
          {recs === undefined ? (
            <RecommendationsSkeleton />
          ) : (
            <Recommendations data={recs} onRefresh={handleRefresh} isRefreshing={isRefreshing} />
          )}
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  valueColor?: string;
  subColor?: string;
  mono?: boolean;
}

function StatCard({ label, value, sub, valueColor, subColor, mono = true }: StatCardProps) {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl px-5 py-4">
      <p className="text-[10px] font-semibold text-text-muted uppercase tracking-widest mb-2">
        {label}
      </p>
      <p
        className={`text-xl font-bold truncate ${mono ? "font-mono tabular-nums" : ""} ${!valueColor ? "text-text-primary" : ""}`}
        style={valueColor ? { color: valueColor } : undefined}
      >
        {value}
      </p>
      {sub && (
        <p
          className={`text-[10px] mt-1 truncate ${!subColor ? "text-text-disabled" : ""}`}
          style={subColor ? { color: subColor } : undefined}
        >
          {sub}
        </p>
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

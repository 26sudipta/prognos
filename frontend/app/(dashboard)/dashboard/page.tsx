"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Link2, RefreshCw } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import {
  fetchDashboard,
  fetchRatingHistory,
  type DashboardData,
  type RatingEntry,
} from "@/app/_lib/analytics";
import { StatStrip, StatStripSkeleton } from "./_components/stat-strip";
import { ActivityHeatmap, HeatmapSkeleton } from "./_components/activity-heatmap";
import { RatingChart, RatingChartSkeleton } from "./_components/rating-chart";

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

function noHandleLinked(d: DashboardData): boolean {
  return !d.has_verified_handle;
}

export default function DashboardPage() {
  const { token } = useAuth();

  const [dashboard, setDashboard] = useState<Async<DashboardData>>(undefined);
  const [ratingHistory, setRatingHistory] = useState<Async<RatingEntry[]>>(undefined);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollErrorsRef = useRef(0);

  function stopPoll() {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  function loadAll(tok: string) {
    fetchDashboard(tok)
      .then((d) => {
        setDashboard(d);
        if (d.is_syncing) {
          if (!pollRef.current) {
            pollErrorsRef.current = 0;
            pollRef.current = setInterval(() => {
              fetchDashboard(tok)
                .then((fresh) => {
                  pollErrorsRef.current = 0;
                  setDashboard(fresh);
                  if (!fresh.is_syncing) {
                    stopPoll();
                    fetchRatingHistory(tok).then(setRatingHistory).catch(() => setRatingHistory([]));
                  }
                })
                .catch(() => {
                  // Give up after repeated failures instead of polling forever.
                  if (++pollErrorsRef.current >= 5) stopPoll();
                });
            }, 5000);
          }
        } else {
          stopPoll();
        }
      })
      .catch(() => setDashboard(EMPTY_DASHBOARD));

    fetchRatingHistory(tok).then(setRatingHistory).catch(() => setRatingHistory([]));
  }

  useEffect(() => {
    if (!token) return;
    loadAll(token);
    return stopPoll;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (dashboard !== undefined && dashboard !== null && noHandleLinked(dashboard)) {
    return <NoHandleNudge />;
  }

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

      {/* Row 3 — rating chart (full width) */}
      {ratingHistory === undefined ? (
        <RatingChartSkeleton />
      ) : (
        <RatingChart data={ratingHistory ?? []} />
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
          Link your Codeforces handle to unlock your analytics.
        </h2>
        <p className="text-sm text-text-muted mb-6 leading-relaxed">
          Verify your handle once and PROGNOS will automatically track your ratings, streaks,
          and problem-solving patterns.
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

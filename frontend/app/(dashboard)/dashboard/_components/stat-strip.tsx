/*
 * StatStrip — 4 stat cards across the top row.
 * Flame icon uses .animate-flame (CSS keyframe defined in globals.css) when current_streak > 0.
 * CF rating rendered in the standard Codeforces color ladder, not a design-system token,
 * because these are CF-canonical colors that users recognise at a glance.
 */

"use client";

import { Flame, Trophy, CheckCircle2, TrendingUp } from "lucide-react";
import type { DashboardData } from "@/app/_lib/analytics";

export function cfRatingColor(rating: number | null): string {
  if (rating === null) return "#94A3B8";
  if (rating >= 2400) return "#F44336";
  if (rating >= 2100) return "#FF8F00";
  if (rating >= 1900) return "#AA46BE";
  if (rating >= 1600) return "#1E88E5";
  if (rating >= 1400) return "#22D3EE";
  if (rating >= 1200) return "#4CAF50";
  return "#9E9E9E";
}

function cfRatingLabel(rating: number | null): string {
  if (rating === null) return "Unrated";
  if (rating >= 2400) return "Grandmaster+";
  if (rating >= 2100) return "Master";
  if (rating >= 1900) return "Candidate Master";
  if (rating >= 1600) return "Expert";
  if (rating >= 1400) return "Specialist";
  if (rating >= 1200) return "Pupil";
  return "Newbie";
}

interface Props {
  data: DashboardData;
  peakRating?: number | null;
}

export function StatStrip({ data, peakRating }: Props) {
  const { current_streak, longest_streak, total_solved, cf_rating } = data;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard
        icon={
          <Flame
            className={`w-5 h-5 text-warning-400${current_streak > 0 ? " animate-flame" : ""}`}
          />
        }
        label="Current Streak"
        value={String(current_streak)}
        sub={current_streak === 1 ? "day" : "days"}
      />
      <StatCard
        icon={<Trophy className="w-5 h-5 text-primary-400" />}
        label="Longest Streak"
        value={String(longest_streak)}
        sub={longest_streak === 1 ? "day" : "days"}
      />
      <StatCard
        icon={<CheckCircle2 className="w-5 h-5 text-success-400" />}
        label="Total Solved"
        value={String(total_solved)}
        sub="problems"
      />
      <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="w-5 h-5" style={{ color: cfRatingColor(cf_rating) }} />
          <span className="text-[10px] text-text-muted uppercase tracking-widest">CF Rating</span>
        </div>
        <div className="flex items-center gap-2 leading-none">
          <p className="font-mono text-3xl font-bold" style={{ color: cfRatingColor(cf_rating) }}>
            {cf_rating !== null ? cf_rating : "—"}
          </p>
          {peakRating !== null && peakRating !== undefined && peakRating !== cf_rating && (
            <span
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-bg-surface-raised border border-border-default text-[11px]"
            >
              <span className="text-text-muted font-medium">max</span>
              <span className="font-mono font-bold" style={{ color: cfRatingColor(peakRating) }}>
                {peakRating}
              </span>
            </span>
          )}
        </div>
        <p className="text-xs text-text-muted mt-1.5">{cfRatingLabel(cf_rating)}</p>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  sub,
  valueColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
  valueColor?: string;
}) {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <span className="text-[10px] text-text-muted uppercase tracking-widest">{label}</span>
      </div>
      <p
        className="font-mono text-3xl font-bold leading-none"
        style={valueColor ? { color: valueColor } : { color: "var(--text-primary)" }}
      >
        {value}
      </p>
      <p className="text-xs text-text-muted mt-1.5">{sub}</p>
    </div>
  );
}

export function StatStripSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="bg-bg-surface border border-border-subtle rounded-xl p-5">
          <div className="skeleton h-4 w-28 mb-3" />
          <div className="skeleton h-8 w-16 mb-2" />
          <div className="skeleton h-3 w-14" />
        </div>
      ))}
    </div>
  );
}

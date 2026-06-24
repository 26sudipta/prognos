"use client";

import Link from "next/link";
import { ArrowUpRight, RefreshCw } from "lucide-react";
import type { RecommendationSet } from "@/app/_lib/analytics";

function difficultyColor(rating: number): string {
  if (rating >= 2400) return "#F44336";
  if (rating >= 2100) return "#FF8F00";
  if (rating >= 1900) return "#AA46BE";
  if (rating >= 1600) return "#1E88E5";
  if (rating >= 1400) return "#22D3EE";
  if (rating >= 1200) return "#4CAF50";
  return "#9E9E9E";
}

function positionBadgeStyle(pos: number): { color: string; bg: string } {
  if (pos === 1) return { color: "#FBBF24", bg: "rgba(251,191,36,0.12)" };
  if (pos === 2) return { color: "#94A3B8", bg: "rgba(148,163,184,0.10)" };
  if (pos === 3) return { color: "#B87333", bg: "rgba(184,115,51,0.10)" };
  return { color: "#475569", bg: "rgba(71,85,105,0.10)" };
}

interface Props {
  data: RecommendationSet | null;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function Recommendations({ data, onRefresh, isRefreshing }: Props) {
  if (data === null) {
    return (
      <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 h-full flex flex-col items-center justify-center text-center gap-4 min-h-[200px]">
        <div className="flex items-center justify-center w-12 h-12 rounded-full bg-bg-surface-raised border border-border-default">
          <RefreshCw className="w-5 h-5 text-text-muted" />
        </div>
        <div>
          <p className="text-sm font-medium text-text-primary">No recommendations yet.</p>
          <p className="text-xs text-text-muted mt-1 leading-relaxed max-w-[240px]">
            Go to Handles and run a sync to generate problem recommendations tailored to your focus areas.
          </p>
        </div>
        <Link
          href="/handles"
          className="text-xs font-medium text-primary-400 hover:text-primary-500 transition-colors"
        >
          Go to Handles →
        </Link>
      </div>
    );
  }

  const { recommendations, generated_at } = data;

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-[10px] font-semibold text-text-muted uppercase tracking-widest">
          Recommended Problems
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-text-disabled">
            {new Date(generated_at).toLocaleDateString("en", { month: "short", day: "numeric" })}
          </span>
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-1 text-[10px] text-text-muted hover:text-text-primary transition-colors disabled:opacity-40"
              title="Regenerate recommendations"
            >
              <RefreshCw className={`w-3 h-3 ${isRefreshing ? "animate-spin" : ""}`} />
              <span>{isRefreshing ? "Refreshing…" : "Refresh"}</span>
            </button>
          )}
        </div>
      </div>

      <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
        {recommendations.map((rec) => {
          const dc = difficultyColor(rec.difficulty);
          const badge = positionBadgeStyle(rec.position);
          return (
            <a
              key={rec.id}
              href={rec.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-start gap-3 p-3 rounded-lg bg-bg-surface-raised border border-border-subtle hover:border-border-default transition-colors group"
            >
              {/* Position badge */}
              <div
                className="shrink-0 flex items-center justify-center w-5 h-5 rounded text-[10px] font-mono font-bold mt-0.5"
                style={{ color: badge.color, backgroundColor: badge.bg }}
              >
                {rec.position}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary truncate group-hover:text-primary-400 transition-colors">
                  {rec.problem_name}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className="font-mono text-[10px] font-semibold px-1.5 py-0.5 rounded border"
                    style={{ color: dc, borderColor: dc + "50", backgroundColor: dc + "12" }}
                  >
                    {rec.difficulty}
                  </span>
                  <span className="text-[10px] text-text-muted bg-bg-surface-overlay px-1.5 py-0.5 rounded border border-border-subtle truncate max-w-[110px]">
                    {rec.tag}
                  </span>
                </div>
                <p className="text-[10px] text-text-muted mt-1 leading-relaxed line-clamp-2">
                  {rec.reason}
                </p>
              </div>

              <ArrowUpRight className="w-3.5 h-3.5 text-text-muted shrink-0 mt-0.5 group-hover:text-primary-400 transition-colors" />
            </a>
          );
        })}
      </div>
    </div>
  );
}

export function RecommendationsSkeleton() {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="flex justify-between mb-4">
        <div className="skeleton h-3 w-40" />
        <div className="skeleton h-3 w-12" />
      </div>
      <div className="space-y-2">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="skeleton h-[76px] w-full rounded-lg" />
        ))}
      </div>
    </div>
  );
}

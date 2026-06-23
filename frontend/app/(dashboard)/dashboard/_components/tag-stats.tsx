"use client";

import type { TagStat } from "@/app/_lib/analytics";

const MAX_TAGS = 10;

function relativeTime(isoStr: string | null): string {
  if (!isoStr) return "no activity";
  const diffMs = Date.now() - new Date(isoStr).getTime();
  const days = Math.floor(diffMs / 86_400_000);
  if (days === 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  return `${Math.floor(months / 12)}y ago`;
}

function acceptanceColor(rate: number): string {
  if (rate >= 0.7) return "#10B981"; // success green
  if (rate >= 0.4) return "#818CF8"; // primary
  return "#F87171"; // danger red
}

interface Props {
  data: TagStat[];
}

export function TagStats({ data }: Props) {
  const top = data.slice(0, MAX_TAGS);
  const maxSolved = Math.max(...top.map((t) => t.solved_count), 1);

  if (top.length === 0) {
    return (
      <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 h-full flex items-center justify-center min-h-[300px]">
        <p className="text-sm text-text-muted">No tag data yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 h-full">
      <h2 className="text-[10px] font-semibold text-text-muted uppercase tracking-widest mb-4">
        Top Tags
      </h2>
      <div className="space-y-3.5 overflow-y-auto max-h-[320px] pr-1">
        {top.map((t) => {
          const accColor = acceptanceColor(t.acceptance_rate);
          return (
            <div key={t.tag}>
              {/* Tag name + solved / attempted */}
              <div className="flex items-baseline justify-between mb-1">
                <span className="text-xs text-text-secondary truncate max-w-[60%]">{t.tag}</span>
                <span className="font-mono text-xs shrink-0">
                  <span className="text-text-primary">{t.solved_count}</span>
                  <span className="text-text-disabled">/{t.attempt_count}</span>
                </span>
              </div>

              {/* Progress bar — width = solved % of max solved in top N */}
              <div className="h-1.5 rounded-full bg-bg-surface-raised overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${(t.solved_count / maxSolved) * 100}%`,
                    backgroundColor: accColor,
                  }}
                />
              </div>

              {/* Acceptance rate + last activity */}
              <div className="flex items-center justify-between mt-1">
                <span className="text-[10px] text-text-disabled">{relativeTime(t.last_activity_at)}</span>
                <span className="text-[10px] font-mono" style={{ color: accColor }}>
                  {(t.acceptance_rate * 100).toFixed(0)}% accepted
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function TagStatsSkeleton() {
  const WIDTHS = ["85%", "70%", "90%", "60%", "78%", "65%", "82%", "55%"];
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="skeleton h-3 w-20 mb-4" />
      <div className="space-y-3.5">
        {WIDTHS.map((w, i) => (
          <div key={i}>
            <div className="flex justify-between mb-1">
              <div className="skeleton h-3 rounded" style={{ width: w }} />
              <div className="skeleton h-3 w-10 rounded" />
            </div>
            <div className="skeleton h-1.5 w-full rounded-full" />
            <div className="flex justify-between mt-1">
              <div className="skeleton h-2.5 w-12 rounded" />
              <div className="skeleton h-2.5 w-16 rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/*
 * TagStats — horizontal bar list, top 15 tags sorted by solved_count DESC.
 *
 * Chosen over alternatives:
 *   Vertical bar chart: CF tag names average 15–20 chars; rotation or truncation
 *     is mandatory, which kills readability.
 *   Radar chart: doesn't show absolute values; relative comparison across 15+
 *     axes is unreadable on a small panel.
 *   Horizontal list with inline progress bar: shows rank order AND magnitude
 *     at a glance. The bar width is %-of-max so it stays meaningful regardless
 *     of total submission volume.
 */

"use client";

import type { TagStat } from "@/app/_lib/analytics";

const MAX_TAGS = 15;
const SKELETON_WIDTHS = ["85%", "70%", "90%", "60%", "78%", "65%", "82%", "55%"];

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
      <div className="space-y-3 overflow-y-auto max-h-[260px] pr-1">
        {top.map((t) => (
          <div key={t.tag}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-text-secondary truncate max-w-[75%]">{t.tag}</span>
              <span className="font-mono text-xs text-text-primary shrink-0">{t.solved_count}</span>
            </div>
            <div className="h-1.5 rounded-full bg-bg-surface-raised overflow-hidden">
              <div
                className="h-full rounded-full bg-primary-500 transition-all duration-500"
                style={{ width: `${(t.solved_count / maxSolved) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function TagStatsSkeleton() {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="skeleton h-3 w-20 mb-4" />
      <div className="space-y-3">
        {SKELETON_WIDTHS.map((w, i) => (
          <div key={i}>
            <div className="flex justify-between mb-1">
              <div className="skeleton h-3 rounded" style={{ width: w }} />
              <div className="skeleton h-3 w-6 rounded" />
            </div>
            <div className="skeleton h-1.5 w-full rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

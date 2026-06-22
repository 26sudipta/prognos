/*
 * WeaknessCards — one card per weakness signal, color-coded by signal_type.
 *
 * Ordering: trust the API's score DESC ordering. Score encodes severity directly;
 * a neglected tag with score 0.9 is more urgent than a low_success tag at 0.3.
 * Grouping by type would fragment this priority without benefit — the color chip
 * already communicates signal_type without requiring visual grouping.
 *
 * Colors: danger-400 (#F87171) = low_success | warning-400 (#FBBF24) = neglected
 *         accent-400 (#22D3EE) = under_practiced
 */

"use client";

import type { WeaknessSignal, WeaknessSignalType } from "@/app/_lib/analytics";

const SIGNAL_CFG: Record<
  WeaknessSignalType,
  { label: string; color: string; bg: string; border: string }
> = {
  low_success: {
    label: "Low Success",
    color: "#F87171",
    bg: "rgba(248,113,113,0.06)",
    border: "rgba(248,113,113,0.25)",
  },
  neglected: {
    label: "Neglected",
    color: "#FBBF24",
    bg: "rgba(251,191,36,0.06)",
    border: "rgba(251,191,36,0.25)",
  },
  under_practiced: {
    label: "Under-practiced",
    color: "#22D3EE",
    bg: "rgba(34,211,238,0.06)",
    border: "rgba(34,211,238,0.25)",
  },
};

interface Props {
  data: WeaknessSignal[];
}

export function WeaknessCards({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 h-full flex items-center justify-center min-h-[200px]">
        <p className="text-sm text-text-muted">No weaknesses detected yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 h-full">
      <h2 className="text-[10px] font-semibold text-text-muted uppercase tracking-widest mb-4">
        Weaknesses
      </h2>
      <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
        {data.map((s) => {
          const cfg = SIGNAL_CFG[s.signal_type];
          return (
            <div
              key={s.id}
              className="rounded-lg border p-3.5"
              style={{ backgroundColor: cfg.bg, borderColor: cfg.border }}
            >
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <span className="text-sm font-medium text-text-primary truncate">{s.tag}</span>
                <span
                  className="shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full border whitespace-nowrap"
                  style={{
                    color: cfg.color,
                    borderColor: cfg.border,
                    backgroundColor: cfg.bg,
                  }}
                >
                  {cfg.label}
                </span>
              </div>
              <p className="text-xs text-text-muted leading-relaxed">{s.reason}</p>
              <p className="font-mono text-[10px] text-text-disabled mt-2">
                score {s.score.toFixed(2)}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function WeaknessCardsSkeleton() {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="skeleton h-3 w-24 mb-4" />
      <div className="space-y-2.5">
        {[0, 1, 2].map((i) => (
          <div key={i} className="skeleton h-[84px] w-full rounded-lg" />
        ))}
      </div>
    </div>
  );
}

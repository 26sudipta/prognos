"use client";

import type { WeaknessSignal, WeaknessSignalType } from "@/app/_lib/analytics";

const SIGNAL_CFG: Record<
  WeaknessSignalType,
  { label: string; priority: string; color: string; bg: string; border: string }
> = {
  low_success: {
    label: "Low Success",
    priority: "High Priority",
    color: "#F87171",
    bg: "rgba(248,113,113,0.06)",
    border: "rgba(248,113,113,0.25)",
  },
  neglected: {
    label: "Neglected",
    priority: "Med Priority",
    color: "#FBBF24",
    bg: "rgba(251,191,36,0.06)",
    border: "rgba(251,191,36,0.25)",
  },
  under_practiced: {
    label: "Under-practiced",
    priority: "Low Priority",
    color: "#22D3EE",
    bg: "rgba(34,211,238,0.06)",
    border: "rgba(34,211,238,0.25)",
  },
};

interface Props {
  data: WeaknessSignal[];
  recTags?: string[];
}

export function WeaknessCards({ data, recTags = [] }: Props) {
  if (data.length === 0) {
    return (
      <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 h-full flex items-center justify-center min-h-[200px]">
        <p className="text-sm text-text-muted">No focus areas detected yet.</p>
      </div>
    );
  }

  const analyzedAt = data[0].computed_at;
  const analyzedLabel = new Date(analyzedAt).toLocaleDateString("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 h-full">
      <div className="flex items-baseline justify-between mb-4">
        <h2 className="text-[10px] font-semibold text-text-muted uppercase tracking-widest">
          Focus Areas
        </h2>
        <span className="text-[10px] text-text-disabled">analyzed {analyzedLabel}</span>
      </div>

      <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
        {data.map((s) => {
          const cfg = SIGNAL_CFG[s.signal_type];
          const recCount = recTags.filter((t) => t === s.tag).length;
          return (
            <div
              key={s.id}
              className="rounded-lg border p-3.5"
              style={{ backgroundColor: cfg.bg, borderColor: cfg.border }}
            >
              {/* Tag + type badge */}
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <span className="text-sm font-medium text-text-primary truncate">{s.tag}</span>
                <span
                  className="shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full border whitespace-nowrap"
                  style={{ color: cfg.color, borderColor: cfg.border, backgroundColor: cfg.bg }}
                >
                  {cfg.label}
                </span>
              </div>

              {/* Reason */}
              <p className="text-xs text-text-muted leading-relaxed">{s.reason}</p>

              {/* Priority indicator + rec count */}
              <div className="flex items-center justify-between mt-2.5">
                <div className="flex items-center gap-1.5">
                  <div
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: cfg.color }}
                  />
                  <span className="text-[10px] font-semibold" style={{ color: cfg.color }}>
                    {cfg.priority}
                  </span>
                </div>
                {recCount > 0 && (
                  <span className="text-[10px] text-text-disabled">
                    {recCount} problem{recCount > 1 ? "s" : ""} selected
                  </span>
                )}
              </div>
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
      <div className="flex justify-between mb-4">
        <div className="skeleton h-3 w-24" />
        <div className="skeleton h-3 w-20" />
      </div>
      <div className="space-y-2.5">
        {[0, 1, 2].map((i) => (
          <div key={i} className="skeleton h-[90px] w-full rounded-lg" />
        ))}
      </div>
    </div>
  );
}

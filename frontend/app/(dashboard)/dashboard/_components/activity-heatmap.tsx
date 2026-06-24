"use client";

import { useRef, useState } from "react";
import type { HeatmapDay } from "@/app/_lib/analytics";

const COLORS = ["#162032", "#0d4a35", "#116b48", "#16a05b", "#10B981"];

function levelColor(count: number, max: number): string {
  if (count === 0) return COLORS[0];
  const pct = count / Math.max(max, 1);
  if (pct < 0.25) return COLORS[1];
  if (pct < 0.5) return COLORS[2];
  if (pct < 0.75) return COLORS[3];
  return COLORS[4];
}

interface Cell {
  date: string;
  count: number;  // total submissions
  solved: number; // accepted only
  isFuture: boolean;
}

function buildGrid(heatmap: HeatmapDay[]): Cell[][] {
  const lookup = new Map(heatmap.map((d) => [d.date, d]));

  const today = new Date();
  // Use UTC date string to match backend storage (TIMESTAMPTZ, dates stored in UTC)
  const todayStr = today.toISOString().slice(0, 10);

  // Anchor so the rightmost column always contains today's cell
  const endSunday = new Date(today);
  endSunday.setDate(today.getDate() - today.getDay()); // Sunday of this week

  const start = new Date(endSunday);
  start.setDate(endSunday.getDate() - 51 * 7); // 52 columns total

  const weeks: Cell[][] = [];
  for (let w = 0; w < 52; w++) {
    const week: Cell[] = [];
    for (let d = 0; d < 7; d++) {
      const cell = new Date(start);
      cell.setDate(start.getDate() + w * 7 + d);
      const key = cell.toISOString().slice(0, 10);
      const day = lookup.get(key);
      week.push({ date: key, count: day?.count ?? 0, solved: day?.solved ?? 0, isFuture: key > todayStr });
    }
    weeks.push(week);
  }
  return weeks;
}

function monthLabels(weeks: Cell[][]): { col: number; label: string }[] {
  const out: { col: number; label: string }[] = [];
  for (let w = 0; w < weeks.length; w++) {
    const d = new Date(weeks[w][0].date);
    const prev = w > 0 ? new Date(weeks[w - 1][0].date) : null;
    if (!prev || d.getMonth() !== prev.getMonth()) {
      out.push({ col: w, label: d.toLocaleDateString("en", { month: "short" }) });
    }
  }
  return out;
}

const DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""];

interface TooltipState {
  date: string;
  count: number;  // total submissions
  solved: number;
  x: number;
  y: number;
}

interface Props {
  data: HeatmapDay[];
}

export function ActivityHeatmap({ data }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [tip, setTip] = useState<TooltipState | null>(null);

  const weeks = buildGrid(data);
  const labels = monthLabels(weeks);
  // Only count non-future cells; backend already filters to last 364 days
  // Intensity based on submission count (any verdict) — matches CF heatmap behavior
  const max = Math.max(...data.map((d) => d.count), 1);
  // Header counter shows accepted solutions (more meaningful than raw submissions)
  const totalSolvedThisYear = data.reduce((sum, d) => sum + d.solved, 0);

  function onEnter(e: React.MouseEvent<HTMLDivElement>, cell: Cell) {
    const cr = containerRef.current?.getBoundingClientRect();
    const er = e.currentTarget.getBoundingClientRect();
    if (!cr) return;
    setTip({ date: cell.date, count: cell.count, solved: cell.solved, x: er.left - cr.left + er.width / 2, y: er.top - cr.top });
  }

  // Tooltip appears below cells near the top, above otherwise
  function tooltipTop(y: number): number {
    return y < 70 ? y + 22 : y - 68;
  }

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="flex items-baseline justify-between mb-4">
        <h2 className="text-[10px] font-semibold text-text-muted uppercase tracking-widest">
          Submission Activity
        </h2>
        <span className="text-xs text-text-muted">
          <span className="font-mono font-semibold text-text-primary">{totalSolvedThisYear}</span>
          {" "}solved in the last year
        </span>
      </div>

      <div ref={containerRef} className="relative overflow-visible">
        {/* Month labels */}
        <div className="flex gap-[3px] mb-1 pl-8">
          {weeks.map((_, wi) => {
            const lbl = labels.find((l) => l.col === wi);
            return (
              <div key={wi} className="w-3.5 shrink-0 text-[10px] text-text-muted truncate leading-none">
                {lbl ? lbl.label : ""}
              </div>
            );
          })}
        </div>

        {/* Grid */}
        <div className="flex gap-[3px]">
          {/* Day-of-week axis */}
          <div className="flex flex-col gap-[3px] mr-1 shrink-0 w-7">
            {DAY_LABELS.map((d, i) => (
              <div key={i} className="h-3.5 text-[9px] text-text-muted flex items-center justify-end pr-1">
                {d}
              </div>
            ))}
          </div>

          {/* Week columns */}
          {weeks.map((week, wi) => (
            <div key={wi} className="flex flex-col gap-[3px]">
              {week.map((cell) => (
                <div
                  key={cell.date}
                  className="w-3.5 h-3.5 rounded-[2px] shrink-0"
                  style={
                    cell.isFuture
                      ? { backgroundColor: "transparent", border: "1px solid #1E2D45" }
                      : { backgroundColor: levelColor(cell.count, max), cursor: "default" }
                  }
                  onMouseEnter={cell.isFuture ? undefined : (e) => onEnter(e, cell)}
                  onMouseLeave={cell.isFuture ? undefined : () => setTip(null)}
                />
              ))}
            </div>
          ))}
        </div>

        {/* Hover tooltip */}
        {tip && (
          <div
            className="absolute pointer-events-none z-20 bg-bg-surface-overlay border border-border-default rounded-lg px-3 py-2 text-xs shadow-xl -translate-x-1/2"
            style={{ left: tip.x, top: tooltipTop(tip.y) }}
          >
            <div className="text-text-muted mb-1">
              {new Date(tip.date + "T12:00:00").toLocaleDateString("en", {
                weekday: "short",
                month: "long",
                day: "numeric",
                year: "numeric",
              })}
            </div>
            <div className="flex items-baseline gap-1">
              <span className="font-mono font-semibold text-text-primary">{tip.solved}</span>
              <span className="text-text-muted">solved</span>
              {tip.count > tip.solved && (
                <span className="text-text-disabled ml-1">· {tip.count} submitted</span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-1.5 mt-3 justify-end">
        <span className="text-[10px] text-text-muted">Less</span>
        {COLORS.map((c, i) => (
          <div key={i} className="w-3 h-3 rounded-[2px]" style={{ backgroundColor: c }} />
        ))}
        <span className="text-[10px] text-text-muted">More</span>
      </div>
    </div>
  );
}

export function HeatmapSkeleton() {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="flex justify-between mb-4">
        <div className="skeleton h-3 w-32" />
        <div className="skeleton h-3 w-28" />
      </div>
      <div className="skeleton h-[112px] w-full rounded-md" />
      <div className="skeleton h-3 w-24 mt-3 ml-auto" />
    </div>
  );
}

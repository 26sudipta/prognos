"use client";

import { useRef, useState } from "react";
import type { HeatmapDay } from "@/app/_lib/analytics";

const COLORS = ["#162032", "#0d4a35", "#116b48", "#16a05b", "#10B981"];

// Each cell is 14px wide + 3px gap = 17px per column stride
const CELL_SIZE = 14;
const GAP = 3;
const STRIDE = CELL_SIZE + GAP;

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
  count: number;
  solved: number;
  isFuture: boolean;
}

function buildGrid(heatmap: HeatmapDay[]): Cell[][] {
  const lookup = new Map(heatmap.map((d) => [d.date, d]));
  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);

  // Keys come from the API as UTC calendar dates, so do ALL grid arithmetic in UTC too —
  // mixing local getDate/setDate with UTC toISOString keys shifts cells by a day for users
  // off UTC (e.g. IST), making today look empty.
  const endSunday = new Date(today);
  endSunday.setUTCDate(today.getUTCDate() - today.getUTCDay());

  const start = new Date(endSunday);
  start.setUTCDate(endSunday.getUTCDate() - 51 * 7);

  const weeks: Cell[][] = [];
  for (let w = 0; w < 52; w++) {
    const week: Cell[] = [];
    for (let d = 0; d < 7; d++) {
      const cell = new Date(start);
      cell.setUTCDate(start.getUTCDate() + w * 7 + d);
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
    const d = new Date(weeks[w][0].date + "T12:00:00");
    const prev = w > 0 ? new Date(weeks[w - 1][0].date + "T12:00:00") : null;
    if (!prev || d.getMonth() !== prev.getMonth() || d.getFullYear() !== prev.getFullYear()) {
      // Count how many consecutive week-columns this month occupies in the grid.
      // GitHub's rule: only show the label when the month spans ≥ 3 columns —
      // if June only has 1–2 columns before July starts, skip "Jun" and show "Jul".
      let span = 0;
      for (let ww = w; ww < weeks.length; ww++) {
        const dd = new Date(weeks[ww][0].date + "T12:00:00");
        if (dd.getMonth() !== d.getMonth() || dd.getFullYear() !== d.getFullYear()) break;
        span++;
      }
      if (span >= 3) {
        out.push({ col: w, label: d.toLocaleDateString("en", { month: "short" }) });
      }
    }
  }
  return out;
}

// Day label column: w-7 (28px) + mr-1 (4px) = 32px before the first cell column
const DAY_COL_WIDTH = 32;
const DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""];

interface TooltipState {
  date: string;
  count: number;
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
  const max = Math.max(...data.map((d) => d.count), 1);
  const totalSolvedThisYear = data.reduce((sum, d) => sum + d.solved, 0);

  function onEnter(e: React.MouseEvent<HTMLDivElement>, cell: Cell) {
    const cr = containerRef.current?.getBoundingClientRect();
    const er = e.currentTarget.getBoundingClientRect();
    if (!cr) return;
    setTip({
      date: cell.date,
      count: cell.count,
      solved: cell.solved,
      x: er.left - cr.left + er.width / 2,
      y: er.top - cr.top,
    });
  }

  function tooltipTop(y: number): number {
    return y < 60 ? y + 22 : y - 72;
  }

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      {/* Header: title left, legend + stat right — no bottom gap */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-[10px] font-semibold text-text-muted uppercase tracking-widest">
          Submission Activity
        </h2>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <span className="text-[9px] text-text-disabled">Less</span>
            {COLORS.map((c, i) => (
              <div key={i} className="w-2.5 h-2.5 rounded-[2px]" style={{ backgroundColor: c }} />
            ))}
            <span className="text-[9px] text-text-disabled">More</span>
          </div>
          <span className="text-[11px] text-text-muted">
            <span className="font-mono font-semibold text-text-primary">{totalSolvedThisYear}</span>
            {" "}solved this year
          </span>
        </div>
      </div>

      <div className="flex justify-center">
      <div ref={containerRef} className="relative overflow-visible">
        {/* Month labels — absolutely positioned so "Jan", "Feb" etc. are never truncated */}
        <div className="relative h-4 mb-0.5" style={{ paddingLeft: DAY_COL_WIDTH }}>
          {labels.map(({ col, label }) => (
            <span
              key={`${col}-${label}`}
              className="absolute text-[10px] text-text-muted leading-none select-none"
              style={{ left: col * STRIDE }}
            >
              {label}
            </span>
          ))}
        </div>

        {/* Grid */}
        <div className="flex gap-[3px]">
          {/* Day-of-week axis */}
          <div className="flex flex-col gap-[3px] mr-1 shrink-0 w-7">
            {DAY_LABELS.map((d, i) => (
              <div key={i} className="h-3.5 text-[9px] text-text-muted flex items-center justify-end pr-1 select-none">
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
      </div>
    </div>
  );
}

export function HeatmapSkeleton() {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="flex justify-between mb-4">
        <div className="skeleton h-3 w-32" />
        <div className="skeleton h-3 w-40" />
      </div>
      <div className="skeleton h-[116px] w-full rounded-md" />
    </div>
  );
}

/*
 * ActivityHeatmap — GitHub-style contribution heatmap, 52 weeks × 7 days.
 *
 * Cell sizing: w-3.5 h-3.5 (14px) + gap-[3px] → 52×17−3 = 881px.
 * Sidebar is 240px, layout padding is 48px → ~992px usable at 1280px viewport.
 * 881px fits with 111px to spare — enough for day-of-week labels (32px) + breathing room.
 *
 * 5 color levels scale from bg-surface-raised (#162032) at 0 submissions
 * to success-500 (#10B981) at max. Thresholds are %-of-max, not absolute,
 * so the intensity is always meaningful regardless of submission volume.
 */

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

function buildGrid(heatmap: HeatmapDay[]) {
  const lookup = new Map(heatmap.map((d) => [d.date, d.count]));

  const today = new Date();
  const start = new Date(today);
  start.setDate(start.getDate() - 363);
  start.setDate(start.getDate() - start.getDay()); // align to Sunday

  const cells: { date: string; count: number }[] = [];
  for (let i = 0; i < 364; i++) {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    const key = d.toISOString().slice(0, 10);
    cells.push({ date: key, count: lookup.get(key) ?? 0 });
  }

  const weeks: { date: string; count: number }[][] = [];
  for (let w = 0; w < 52; w++) {
    weeks.push(cells.slice(w * 7, (w + 1) * 7));
  }
  return weeks;
}

function monthLabels(weeks: { date: string }[][]): { col: number; label: string }[] {
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
  count: number;
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

  function onEnter(e: React.MouseEvent<HTMLDivElement>, date: string, count: number) {
    const cr = containerRef.current?.getBoundingClientRect();
    const er = e.currentTarget.getBoundingClientRect();
    if (!cr) return;
    setTip({ date, count, x: er.left - cr.left + er.width / 2, y: er.top - cr.top });
  }

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <h2 className="text-[10px] font-semibold text-text-muted uppercase tracking-widest mb-4">
        Activity
      </h2>
      <div ref={containerRef} className="relative overflow-visible">
        {/* Month labels row */}
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

        {/* Grid with day labels */}
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
                  className="w-3.5 h-3.5 rounded-[2px] shrink-0 cursor-default"
                  style={{ backgroundColor: levelColor(cell.count, max) }}
                  onMouseEnter={(e) => onEnter(e, cell.date, cell.count)}
                  onMouseLeave={() => setTip(null)}
                />
              ))}
            </div>
          ))}
        </div>

        {/* Hover tooltip */}
        {tip && (
          <div
            className="absolute pointer-events-none z-20 bg-bg-surface-overlay border border-border-default rounded-lg px-3 py-2 text-xs shadow-xl -translate-x-1/2"
            style={{ left: tip.x, top: tip.y - 60 }}
          >
            <span className="font-mono text-text-primary">{tip.count}</span>
            <span className="text-text-muted ml-1">solved</span>
            <div className="text-text-muted mt-0.5">
              {new Date(tip.date + "T12:00:00").toLocaleDateString("en", {
                month: "long",
                day: "numeric",
                year: "numeric",
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function HeatmapSkeleton() {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="skeleton h-3 w-16 mb-4" />
      <div className="skeleton h-[112px] w-full rounded-md" />
    </div>
  );
}

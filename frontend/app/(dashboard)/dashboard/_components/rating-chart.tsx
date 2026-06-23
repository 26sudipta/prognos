"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { RatingEntry } from "@/app/_lib/analytics";

export function cfColor(rating: number): string {
  if (rating >= 2400) return "#F44336";
  if (rating >= 2100) return "#FF8F00";
  if (rating >= 1900) return "#AA46BE";
  if (rating >= 1600) return "#1E88E5";
  if (rating >= 1400) return "#22D3EE";
  if (rating >= 1200) return "#4CAF50";
  return "#9E9E9E";
}

function cfLabel(rating: number): string {
  if (rating >= 2400) return "Grandmaster+";
  if (rating >= 2100) return "Master";
  if (rating >= 1900) return "Candidate Master";
  if (rating >= 1600) return "Expert";
  if (rating >= 1400) return "Specialist";
  if (rating >= 1200) return "Pupil";
  return "Newbie";
}

function RatingTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: RatingEntry & { label: string } }>;
}) {
  if (!active || !payload?.[0]) return null;
  const e = payload[0].payload;
  const sign = e.delta >= 0 ? "+" : "";
  return (
    <div className="bg-bg-surface-overlay border border-border-default rounded-lg px-3 py-2.5 text-xs shadow-xl max-w-[220px]">
      <p className="text-text-secondary font-medium mb-2 truncate">{e.contest_name}</p>
      <div className="flex items-baseline gap-2 mb-1">
        <span className="font-mono text-base font-bold" style={{ color: cfColor(e.new_rating) }}>
          {e.new_rating}
        </span>
        <span
          className="font-mono text-xs font-semibold"
          style={{ color: e.delta >= 0 ? "#34D399" : "#F87171" }}
        >
          {sign}{e.delta}
        </span>
      </div>
      <p className="text-text-muted text-[11px]">
        <span className="font-mono">{e.old_rating}</span>
        <span className="mx-1 opacity-40">→</span>
        <span className="font-mono" style={{ color: cfColor(e.new_rating) }}>{e.new_rating}</span>
        {" "}
        <span className="opacity-60">({cfLabel(e.new_rating)})</span>
      </p>
      <p className="text-text-muted mt-1">Rank #{e.rank.toLocaleString()}</p>
      <p className="text-text-muted">
        {new Date(e.contest_time).toLocaleDateString("en", {
          month: "short",
          day: "numeric",
          year: "numeric",
        })}
      </p>
    </div>
  );
}

interface Props {
  data: RatingEntry[];
}

export function RatingChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 flex items-center justify-center h-full min-h-[300px]">
        <p className="text-sm text-text-muted">No contest history yet.</p>
      </div>
    );
  }

  const ratings = data.map((d) => d.new_rating);
  const peakRating = Math.max(...ratings);
  const currentRating = ratings[ratings.length - 1];
  const yMin = Math.max(0, Math.min(...ratings) - 50);
  const yMax = peakRating + 60;

  const chartData = data.map((d) => ({
    ...d,
    label: new Date(d.contest_time).toLocaleDateString("en", {
      month: "short",
      year: "2-digit",
    }),
  }));

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="flex items-start justify-between mb-4">
        <h2 className="text-[10px] font-semibold text-text-muted uppercase tracking-widest">
          Rating History
        </h2>
        <div className="text-right">
          <span className="font-mono text-sm font-bold" style={{ color: cfColor(currentRating) }}>
            {currentRating}
          </span>
          {peakRating > currentRating && (
            <span className="text-[10px] text-text-muted ml-2">
              peak <span className="font-mono" style={{ color: cfColor(peakRating) }}>{peakRating}</span>
            </span>
          )}
          <p className="text-[10px] text-text-muted mt-0.5">{cfLabel(currentRating)} · {data.length} contests</p>
        </div>
      </div>

      {/*
        Three-layer overflow fix so the tooltip can escape above the chart
        and to the right of the last point:
          1. This div wrapper — overflow: visible
          2. .recharts-wrapper — Recharts' internal div (clips by default)
          3. .recharts-surface — the SVG element (clips by default in browsers)
      */}
      <div
        className="[&_.recharts-wrapper]:overflow-visible [&_.recharts-surface]:overflow-visible"
        style={{ overflow: "visible" }}
      >
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={chartData} margin={{ top: 48, right: 40, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E2D45" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: "#64748B", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[yMin, yMax]}
              tick={{ fill: "#64748B", fontSize: 10, fontFamily: "var(--font-jetbrains-mono)" }}
              tickLine={false}
              axisLine={false}
              width={44}
            />
            <Tooltip
              content={<RatingTooltip />}
              cursor={{ stroke: "#2A3F5C", strokeWidth: 1 }}
              allowEscapeViewBox={{ x: true, y: true }}
            />
            {/* Peak rating reference line — only shown when peak != current */}
            {peakRating > currentRating && (
              <ReferenceLine
                y={peakRating}
                stroke={cfColor(peakRating)}
                strokeDasharray="4 3"
                strokeOpacity={0.4}
                label={{
                  value: `Peak ${peakRating}`,
                  position: "insideTopRight",
                  fill: cfColor(peakRating),
                  fontSize: 9,
                  opacity: 0.6,
                }}
              />
            )}
            <Line
              type="monotone"
              dataKey="new_rating"
              stroke="#818CF8"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: "#22D3EE", stroke: "#0F1623", strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function RatingChartSkeleton() {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="flex justify-between mb-4">
        <div className="skeleton h-3 w-28" />
        <div className="skeleton h-4 w-16" />
      </div>
      <div className="skeleton h-[260px] w-full rounded-md" />
    </div>
  );
}

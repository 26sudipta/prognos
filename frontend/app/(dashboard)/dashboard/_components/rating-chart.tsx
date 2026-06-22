/*
 * RatingChart — Recharts LineChart of CF rating over contest history.
 *
 * Y-axis domain: [min−50, max+50] — manual clamp instead of Recharts auto-scale.
 * Auto-scale produces ugly bounds (e.g. 1234–1567) with no padding at chart edges.
 * A fixed ±50 buffer gives breathing room without wasting vertical space the way
 * a [0, max] domain would when the user is already Expert or above.
 *
 * Line: primary-400 (#818CF8). Active dot: accent-400 (#22D3EE) with surface fill.
 * Custom tooltip shows contest name, new rating in CF color, delta, and rank.
 */

"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { RatingEntry } from "@/app/_lib/analytics";

function cfColor(rating: number): string {
  if (rating >= 2400) return "#F44336";
  if (rating >= 2100) return "#FF8F00";
  if (rating >= 1900) return "#AA46BE";
  if (rating >= 1600) return "#1E88E5";
  if (rating >= 1400) return "#22D3EE";
  if (rating >= 1200) return "#4CAF50";
  return "#9E9E9E";
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
    <div className="bg-bg-surface-overlay border border-border-default rounded-lg px-3 py-2.5 text-xs shadow-xl max-w-[200px]">
      <p className="text-text-secondary font-medium mb-1.5 truncate">{e.contest_name}</p>
      <p className="font-mono font-bold" style={{ color: cfColor(e.new_rating) }}>
        {e.new_rating}
        <span
          className="ml-1.5 text-[11px]"
          style={{ color: e.delta >= 0 ? "#34D399" : "#F87171" }}
        >
          {sign}{e.delta}
        </span>
      </p>
      <p className="text-text-muted mt-1">Rank #{e.rank}</p>
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
  const yMin = Math.max(0, Math.min(...ratings) - 50);
  const yMax = Math.max(...ratings) + 50;

  const chartData = data.map((d) => ({
    ...d,
    label: new Date(d.contest_time).toLocaleDateString("en", {
      month: "short",
      year: "2-digit",
    }),
  }));

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <h2 className="text-[10px] font-semibold text-text-muted uppercase tracking-widest mb-4">
        Rating History
      </h2>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
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
          <Tooltip content={<RatingTooltip />} cursor={{ stroke: "#2A3F5C", strokeWidth: 1 }} />
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
  );
}

export function RatingChartSkeleton() {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="skeleton h-3 w-28 mb-4" />
      <div className="skeleton h-[260px] w-full rounded-md" />
    </div>
  );
}

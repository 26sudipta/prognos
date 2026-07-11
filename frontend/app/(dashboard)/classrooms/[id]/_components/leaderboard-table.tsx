"use client";

import { LeaderboardEntry, cfRatingColor, formatLastActive } from "@/app/_lib/classrooms";

interface Props {
  entries: LeaderboardEntry[];
}

function SkeletonRow() {
  return (
    <tr className="border-b border-border-subtle">
      {[40, 120, 100, 60, 60, 60, 80].map((w, i) => (
        <td key={i} className="px-4 py-3">
          <div className={`h-3.5 rounded bg-bg-surface-raised animate-shimmer`} style={{ width: w }} />
        </td>
      ))}
    </tr>
  );
}

export function LeaderboardTable({ entries }: Props) {
  if (entries.length === 0) {
    return (
      <div className="text-center py-16 text-text-muted text-sm">
        Leaderboard is being computed. Check back soon.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border-subtle text-left text-xs text-text-muted uppercase tracking-wide">
            <th className="px-4 py-2.5 w-12">#</th>
            <th className="px-4 py-2.5">Handle</th>
            <th className="px-4 py-2.5">Name</th>
            <th className="px-4 py-2.5 text-right">Rating</th>
            <th className="px-4 py-2.5 text-right">Solved</th>
            <th className="px-4 py-2.5 text-right">Streak</th>
            <th className="px-4 py-2.5 text-right">Last Active</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr
              key={entry.user_id}
              className={`border-b border-border-subtle transition-colors duration-100 hover:bg-bg-surface-raised ${
                entry.is_me ? "ring-1 ring-inset ring-primary-400/20 bg-primary-500/[0.04]" : ""
              }`}
            >
              <td className="px-4 py-3 text-text-muted font-mono tabular-nums">
                {entry.rank}
              </td>
              <td className="px-4 py-3">
                <span className="font-mono text-text-primary">
                  {entry.cf_handle}
                </span>
                {entry.is_me && (
                  <span className="ml-2 text-xs text-primary-400 font-medium">you</span>
                )}
              </td>
              <td className="px-4 py-3 text-text-secondary truncate max-w-[160px]">
                {entry.user_name}
              </td>
              <td className={`px-4 py-3 text-right font-mono tabular-nums font-semibold ${cfRatingColor(entry.cf_rating)}`}>
                {entry.cf_rating ?? "—"}
              </td>
              <td className="px-4 py-3 text-right text-text-primary tabular-nums">
                {entry.solved_count}
              </td>
              <td className="px-4 py-3 text-right text-text-secondary tabular-nums">
                {entry.current_streak > 0 ? (
                  <span className="text-success-400">{entry.current_streak}🔥</span>
                ) : (
                  <span className="text-text-muted">0</span>
                )}
              </td>
              <td className="px-4 py-3 text-right text-text-muted text-xs">
                {formatLastActive(entry.last_active_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function LeaderboardTableSkeleton() {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border-subtle text-left text-xs text-text-muted uppercase tracking-wide">
            <th className="px-4 py-2.5 w-12">#</th>
            <th className="px-4 py-2.5">Handle</th>
            <th className="px-4 py-2.5">Name</th>
            <th className="px-4 py-2.5 text-right">Rating</th>
            <th className="px-4 py-2.5 text-right">Solved</th>
            <th className="px-4 py-2.5 text-right">Streak</th>
            <th className="px-4 py-2.5 text-right">Last Active</th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonRow key={i} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

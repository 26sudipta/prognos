"use client";

import { useMemo, useState, useEffect } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import {
  type ContestItem,
  platformColor,
  localDateKey,
  getLocalWeekDays,
} from "@/app/_lib/contests";
import { useCountdown } from "./countdown-display";

interface Props {
  contests: ContestItem[] | undefined;
  weekOffset: number;
  onWeekChange: (offset: number) => void;
  onContestClick: (c: ContestItem) => void;
}

export function ContestCalendarView({
  contests,
  weekOffset,
  onWeekChange,
  onContestClick,
}: Props) {
  const weekDays = useMemo(() => getLocalWeekDays(weekOffset), [weekOffset]);

  const contestsByDay = useMemo(() => {
    const map = new Map<string, ContestItem[]>();
    if (!contests) return map;
    for (const c of contests) {
      const key = localDateKey(new Date(c.start_time));
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(c);
    }
    return map;
  }, [contests]);

  const isCurrentWeek = weekOffset === 0;

  // "Jun 30 – Jul 6, 2026" week label
  const weekLabel = (() => {
    const first = weekDays[0];
    const last = weekDays[6];
    const opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
    const firstStr = first.toLocaleDateString("en-US", opts);
    const lastStr = last.toLocaleDateString("en-US", { ...opts, year: "numeric" });
    return `${firstStr} – ${lastStr}`;
  })();

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl overflow-hidden">
      {/* Navigation header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border-subtle">
        <span className="text-sm font-medium text-text-primary">{weekLabel}</span>
        <div className="flex items-center gap-1">
          {!isCurrentWeek && (
            <button
              onClick={() => onWeekChange(0)}
              className="text-xs text-primary-400 hover:text-primary-300 px-3 py-1.5 rounded-lg hover:bg-primary-500/10 transition-colors mr-1"
            >
              Today
            </button>
          )}
          <button
            onClick={() => onWeekChange(weekOffset - 1)}
            className="p-1.5 text-text-secondary hover:text-text-primary hover:bg-bg-surface-raised rounded-lg transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => onWeekChange(weekOffset + 1)}
            className="p-1.5 text-text-secondary hover:text-text-primary hover:bg-bg-surface-raised rounded-lg transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Day name headers */}
      <div className="grid grid-cols-7 border-b border-border-subtle">
        {weekDays.map((day, i) => {
          const isToday = localDateKey(day) === localDateKey(new Date());
          return (
            <div
              key={i}
              className={`px-2 py-2 text-center border-r last:border-r-0 border-border-subtle ${
                isToday ? "bg-primary-500/5" : ""
              }`}
            >
              <p className="text-[10px] text-text-muted uppercase tracking-widest">
                {day.toLocaleDateString("en-US", { weekday: "short" })}
              </p>
              <p
                className={`text-sm font-semibold mt-0.5 ${
                  isToday ? "text-primary-400" : "text-text-secondary"
                }`}
              >
                {day.getDate()}
              </p>
            </div>
          );
        })}
      </div>

      {/* Contest cells */}
      <div className="grid grid-cols-7">
        {weekDays.map((day, i) => {
          const key = localDateKey(day);
          const dayContests = contestsByDay.get(key) ?? [];
          return (
            <CalendarDayCell
              key={i}
              date={day}
              contests={dayContests}
              loading={contests === undefined}
              onContestClick={onContestClick}
            />
          );
        })}
      </div>
    </div>
  );
}

// ─── Day cell ─────────────────────────────────────────────────────────────────

const MAX_VISIBLE = 3;

function CalendarDayCell({
  date,
  contests,
  loading,
  onContestClick,
}: {
  date: Date;
  contests: ContestItem[];
  loading: boolean;
  onContestClick: (c: ContestItem) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  // Reset expansion when contests change (e.g. platform filter changed)
  useEffect(() => { setExpanded(false); }, [contests]);
  const isToday = localDateKey(date) === localDateKey(new Date());
  const overflow = contests.length - MAX_VISIBLE;
  const visible = expanded ? contests : contests.slice(0, MAX_VISIBLE);

  return (
    <div
      className={`min-h-[160px] p-2 border-r last:border-r-0 border-border-subtle ${
        isToday ? "bg-primary-500/5" : ""
      }`}
    >
      {loading ? (
        <div className="space-y-1.5 pt-1">
          {[0, 1].map((i) => (
            <div key={i} className="skeleton h-6 rounded" />
          ))}
        </div>
      ) : (
        <div className="space-y-1">
          {visible.map((c) => (
            <CalendarPill
              key={c.id}
              contest={c}
              onClick={() => onContestClick(c)}
            />
          ))}
          {!expanded && overflow > 0 && (
            <button
              onClick={() => setExpanded(true)}
              className="w-full text-left text-[10px] text-text-muted hover:text-text-secondary px-1.5 py-0.5 rounded hover:bg-bg-surface-raised transition-colors"
            >
              +{overflow} more
            </button>
          )}
          {expanded && overflow > 0 && (
            <button
              onClick={() => setExpanded(false)}
              className="w-full text-left text-[10px] text-text-muted hover:text-text-secondary px-1.5 py-0.5 rounded hover:bg-bg-surface-raised transition-colors"
            >
              Show less
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Calendar pill ────────────────────────────────────────────────────────────

function CalendarPill({
  contest,
  onClick,
}: {
  contest: ContestItem;
  onClick: () => void;
}) {
  const color = platformColor(contest.platform);
  const { isLive } = useCountdown(contest.start_time, contest.end_time);

  return (
    <button
      onClick={onClick}
      className="w-full text-left px-1.5 py-1 rounded text-[11px] font-medium leading-tight truncate hover:opacity-90 transition-opacity"
      style={{
        backgroundColor: `${color}22`,
        color,
        borderLeft: `2px solid ${color}`,
      }}
      title={contest.name}
    >
      {isLive && (
        <span
          className="inline-block w-1 h-1 rounded-full bg-success-400 mr-1 animate-pulse"
          style={{ verticalAlign: "middle" }}
        />
      )}
      {contest.name}
    </button>
  );
}

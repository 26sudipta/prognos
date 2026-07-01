"use client";

import { useEffect, useState } from "react";
import { List, CalendarDays } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import {
  type ContestItem,
  fetchContests,
  fetchContestPlatforms,
  getWeekBoundsISO,
} from "@/app/_lib/contests";
import { NextContestHero } from "./_components/next-contest-hero";
import { StaleDataBanner } from "./_components/stale-data-banner";
import { PlatformFilterChips } from "./_components/platform-filter-chips";
import { ContestListView } from "./_components/contest-list-view";
import { ContestCalendarView } from "./_components/contest-calendar-view";
import { ContestDetailModal } from "./_components/contest-detail-modal";

type View = "list" | "calendar";

export default function ContestsPage() {
  const { token } = useAuth();

  // ── Filter + view state ─────────────────────────────────────────────────────
  const [view, setView] = useState<View>("list");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [weekOffset, setWeekOffset] = useState(0);

  // ── Data state ──────────────────────────────────────────────────────────────
  // undefined = initial loading (shows skeleton); array = loaded (may be stale while re-fetching)
  const [platforms, setPlatforms] = useState<string[] | undefined>(undefined);
  const [contests, setContests] = useState<ContestItem[] | undefined>(undefined);
  const [isStale, setIsStale] = useState(false);

  // ── Modal state ─────────────────────────────────────────────────────────────
  const [selectedContest, setSelectedContest] = useState<ContestItem | null>(null);

  // ── Fetch platforms once on mount ───────────────────────────────────────────
  useEffect(() => {
    if (!token) return;
    fetchContestPlatforms(token)
      .then(setPlatforms)
      .catch(() => setPlatforms([]));
  }, [token]);

  // ── Fetch contests when filter / view / week changes ───────────────────────
  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    const params: Parameters<typeof fetchContests>[1] = {
      platform: selectedPlatforms.length > 0 ? selectedPlatforms : undefined,
      limit: 200,
    };
    if (view === "calendar") {
      const bounds = getWeekBoundsISO(weekOffset);
      params.from_dt = bounds.from_dt;
      params.to_dt = bounds.to_dt;
    }

    fetchContests(token, params)
      .then((data) => {
        if (!cancelled) {
          setContests(data.contests);
          setIsStale(data.is_stale);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setContests([]);
          setIsStale(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token, selectedPlatforms, view, weekOffset]);

  // ── Switching views resets calendar to current week ─────────────────────────
  function handleViewChange(next: View) {
    if (next === view) return;
    setView(next);
    if (next === "calendar") setWeekOffset(0);
  }

  return (
    <div className="space-y-5 max-w-[1100px] mx-auto">
      {/* Hero — next/live contest */}
      <NextContestHero contests={contests} />

      {/* Stale data warning */}
      <StaleDataBanner isStale={isStale} />

      {/* Filter chips + view toggle — toggle on top (right) on mobile, inline on sm+ */}
      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:items-start sm:gap-4">
        <div className="flex-1 min-w-0">
          <PlatformFilterChips
            platforms={platforms ?? []}
            selected={selectedPlatforms}
            onChange={setSelectedPlatforms}
            loading={platforms === undefined}
          />
        </div>
        <div className="self-end sm:self-auto">
          <ViewToggle view={view} onChange={handleViewChange} />
        </div>
      </div>

      {/* Content */}
      {view === "list" ? (
        <ContestListView
          contests={contests}
          selectedPlatforms={selectedPlatforms}
          onClearFilter={() => setSelectedPlatforms([])}
          onContestClick={setSelectedContest}
        />
      ) : (
        <ContestCalendarView
          contests={contests}
          weekOffset={weekOffset}
          onWeekChange={setWeekOffset}
          onContestClick={setSelectedContest}
        />
      )}

      {/* Detail modal */}
      <ContestDetailModal
        contest={selectedContest}
        onClose={() => setSelectedContest(null)}
      />
    </div>
  );
}

// ─── View toggle ──────────────────────────────────────────────────────────────

function ViewToggle({ view, onChange }: { view: View; onChange: (v: View) => void }) {
  return (
    <div className="flex items-center shrink-0 bg-bg-surface-raised border border-border-default rounded-lg p-0.5">
      <ToggleBtn
        label="List"
        icon={<List className="w-3.5 h-3.5" />}
        active={view === "list"}
        onClick={() => onChange("list")}
      />
      <ToggleBtn
        label="Calendar"
        icon={<CalendarDays className="w-3.5 h-3.5" />}
        active={view === "calendar"}
        onClick={() => onChange("calendar")}
      />
    </div>
  );
}

function ToggleBtn({
  label,
  icon,
  active,
  onClick,
}: {
  label: string;
  icon: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150 ${
        active
          ? "bg-bg-surface-overlay text-text-primary shadow-sm"
          : "text-text-muted hover:text-text-secondary"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

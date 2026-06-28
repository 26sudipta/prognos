"use client";

import { Calendar } from "lucide-react";
import {
  type ContestItem,
  type UrgencyLane,
  groupContestsByUrgency,
} from "@/app/_lib/contests";
import { ContestCard, ContestCardSkeleton } from "./contest-card";

interface Props {
  contests: ContestItem[] | undefined;
  selectedPlatforms: string[];
  onClearFilter: () => void;
  onContestClick: (c: ContestItem) => void;
}

const LANE_LABEL_COLOR: Record<UrgencyLane, string> = {
  live: "text-success-400",
  today: "text-accent-400",
  "this-week": "text-text-muted",
  "next-week": "text-text-muted",
  later: "text-text-muted",
};

export function ContestListView({
  contests,
  selectedPlatforms,
  onClearFilter,
  onContestClick,
}: Props) {
  if (contests === undefined) return <ContestListSkeleton />;

  const lanes = groupContestsByUrgency(contests);

  if (lanes.length === 0) {
    return (
      <EmptyState
        selectedPlatforms={selectedPlatforms}
        onClearFilter={onClearFilter}
      />
    );
  }

  return (
    <div>
      {lanes.map(({ lane, label, contests: laneContests }, i) => (
        <div key={lane} className={i > 0 ? "mt-8" : ""}>
          {/* Swim-lane header */}
          <div className="flex items-center gap-2 mb-3">
            {lane === "live" && (
              <span className="w-1.5 h-1.5 rounded-full bg-success-400 animate-pulse shrink-0" />
            )}
            <h3
              className={`text-[11px] font-semibold uppercase tracking-widest ${LANE_LABEL_COLOR[lane]}`}
            >
              {label}
            </h3>
            <span className="text-[10px] text-text-disabled tabular-nums ml-1">
              ({laneContests.length})
            </span>
          </div>

          {/* Cards */}
          <div className="space-y-2">
            {laneContests.map((c) => (
              <ContestCard
                key={c.id}
                contest={c}
                onClick={() => onContestClick(c)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({
  selectedPlatforms,
  onClearFilter,
}: {
  selectedPlatforms: string[];
  onClearFilter: () => void;
}) {
  const filterLabel =
    selectedPlatforms.length === 1
      ? selectedPlatforms[0]
      : selectedPlatforms.length > 1
      ? `${selectedPlatforms.length} platforms`
      : null;

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-bg-surface-raised border border-border-default mb-4">
        <Calendar className="w-5 h-5 text-text-muted" />
      </div>
      <p className="text-sm font-medium text-text-secondary mb-1">
        {filterLabel
          ? `No ${filterLabel} contests in the next 30 days.`
          : "No upcoming contests in the next 30 days."}
      </p>
      {filterLabel && (
        <button
          onClick={onClearFilter}
          className="text-xs text-primary-400 hover:text-primary-300 transition-colors mt-1"
        >
          Clear filter
        </button>
      )}
    </div>
  );
}

export function ContestListSkeleton() {
  return (
    <div>
      {[0, 1, 2].map((g) => (
        <div key={g} className={g > 0 ? "mt-8" : ""}>
          <div className="flex items-center gap-3 mb-3">
            <div className="skeleton h-2.5 w-20 rounded" />
            <div className="flex-1 h-px bg-border-subtle" />
          </div>
          <div className="space-y-2">
            {[0, 1].map((i) => (
              <ContestCardSkeleton key={i} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

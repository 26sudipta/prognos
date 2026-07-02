"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Users, BarChart2, Settings2, Trash2, LogOut, Loader2, ArrowLeft, RefreshCw } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import {
  Classroom,
  CohortAnalytics,
  Invite,
  LeaderboardResponse,
  Member,
  deleteClassroom,
  fetchClassroom,
  fetchCohortAnalytics,
  fetchInvites,
  fetchLeaderboard,
  fetchMembers,
  leaveClassroom,
  syncClassroom,
} from "@/app/_lib/classrooms";
import { LeaderboardTable, LeaderboardTableSkeleton } from "./_components/leaderboard-table";
import { InvitePanel } from "./_components/invite-panel";
import { CohortAnalyticsPanel } from "./_components/cohort-analytics";
import { MemberManagement } from "./_components/member-management";

type Tab = "leaderboard" | "cohort" | "members";

export default function ClassroomDetailPage() {
  const { token, user } = useAuth();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const classroomId = params.id;

  const [classroom, setClassroom] = useState<Classroom | undefined>(undefined);
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | undefined>(undefined);
  const [members, setMembers] = useState<Member[] | undefined>(undefined);
  const [cohort, setCohort] = useState<CohortAnalytics | undefined>(undefined);
  const [invites, setInvites] = useState<Invite[] | undefined>(undefined);
  const [activeTab, setActiveTab] = useState<Tab>("leaderboard");
  const [isDeleting, setIsDeleting] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmLeave, setConfirmLeave] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollErrorsRef = useRef(0);

  const isTeacher = classroom?.my_role === "teacher";

  const stopPoll = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const loadLeaderboard = useCallback(() => {
    if (!token || !classroomId) return;
    fetchLeaderboard(token, classroomId)
      .then((lb) => {
        pollErrorsRef.current = 0;
        setLeaderboard(lb);
      })
      .catch(() => {
        // Keep the last good board on a transient poll error (only the very first load
        // may show the skeleton); give up polling after repeated failures.
        setLeaderboard((prev) => prev);
        if (++pollErrorsRef.current >= 5) stopPoll();
      });
  }, [token, classroomId, stopPoll]);

  useEffect(() => {
    if (!token || !classroomId) return;
    fetchClassroom(token, classroomId).then(setClassroom).catch(() => router.replace("/classrooms"));
  }, [token, classroomId, router]);

  useEffect(() => {
    if (!token || !classroomId) return;
    loadLeaderboard();
    fetchMembers(token, classroomId)
      .then((r) => setMembers(r.members))
      .catch(() => setMembers([]));
  }, [token, classroomId, loadLeaderboard]);

  // While any member is mid-sync, poll the leaderboard so rows refresh as results land.
  useEffect(() => {
    if (!leaderboard?.syncing) {
      stopPoll();
      return;
    }
    if (pollRef.current) return;
    pollErrorsRef.current = 0;
    pollRef.current = setInterval(loadLeaderboard, 5000);
    return stopPoll;
  }, [leaderboard?.syncing, loadLeaderboard, stopPoll]);

  async function handleSync() {
    if (!token || !classroomId || isSyncing) return;
    setIsSyncing(true);
    setSyncMsg(null);
    try {
      await syncClassroom(token, classroomId);
      loadLeaderboard(); // picks up syncing=true → starts the poll
    } catch (e) {
      setSyncMsg(e instanceof Error ? e.message : "Sync failed");
    } finally {
      setIsSyncing(false);
    }
  }

  useEffect(() => {
    if (!token || !classroomId || !isTeacher) return;
    fetchCohortAnalytics(token, classroomId).then(setCohort).catch(() => setCohort(undefined));
    fetchInvites(token, classroomId)
      .then((r) => setInvites(r.invites))
      .catch(() => setInvites([]));
  }, [token, classroomId, isTeacher]);

  async function handleDelete() {
    if (!token || !classroomId) return;
    setIsDeleting(true);
    try {
      await deleteClassroom(token, classroomId);
      router.replace("/classrooms");
    } finally {
      setIsDeleting(false);
      setConfirmDelete(false);
    }
  }

  async function handleLeave() {
    if (!token || !classroomId) return;
    setIsLeaving(true);
    try {
      await leaveClassroom(token, classroomId);
      router.replace("/classrooms");
    } finally {
      setIsLeaving(false);
      setConfirmLeave(false);
    }
  }

  const allTabs: { key: Tab; label: string; icon: React.ElementType; teacherOnly?: boolean }[] = [
    { key: "leaderboard" as Tab, label: "Leaderboard", icon: BarChart2 },
    { key: "cohort" as Tab, label: "Cohort", icon: BarChart2, teacherOnly: true },
    { key: "members" as Tab, label: "Members", icon: Users, teacherOnly: true },
  ];
  const tabs = allTabs.filter((t) => !t.teacherOnly || isTeacher);

  return (
    <div className="space-y-5 max-w-[1100px] mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/classrooms")}
            className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-surface-raised transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-text-primary">
              {classroom?.name ?? <span className="bg-bg-surface-raised rounded w-48 h-6 inline-block animate-shimmer" />}
            </h1>
            <p className="text-xs text-text-muted mt-0.5">
              {classroom ? (
                <>
                  {classroom.member_count} member{classroom.member_count !== 1 ? "s" : ""} ·{" "}
                  <span className={`font-medium ${isTeacher ? "text-primary-400" : "text-text-secondary"}`}>
                    {isTeacher ? "You are the teacher" : "You are a student"}
                  </span>
                </>
              ) : null}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleSync}
            disabled={isSyncing || leaderboard?.syncing}
            title="Refresh every member's data from Codeforces"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-text-muted hover:text-primary-400 hover:bg-primary-500/10 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing || leaderboard?.syncing ? "animate-spin" : ""}`} />
            {leaderboard?.syncing ? "Syncing…" : "Sync"}
          </button>
          {isTeacher ? (
            confirmDelete ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-danger-500/10 text-danger-400 hover:bg-danger-500/20 transition-colors"
                >
                  {isDeleting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                  Confirm Delete
                </button>
                <button
                  onClick={() => setConfirmDelete(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-bg-surface-raised text-text-muted hover:text-text-primary transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmDelete(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-text-muted hover:text-danger-400 hover:bg-danger-500/10 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Delete
              </button>
            )
          ) : (
            confirmLeave ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleLeave}
                  disabled={isLeaving}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-danger-500/10 text-danger-400 hover:bg-danger-500/20 transition-colors"
                >
                  {isLeaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                  Confirm Leave
                </button>
                <button
                  onClick={() => setConfirmLeave(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-bg-surface-raised text-text-muted hover:text-text-primary transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmLeave(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-text-muted hover:text-danger-400 hover:bg-danger-500/10 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
                Leave
              </button>
            )
          )}
        </div>
      </div>

      {syncMsg && (
        <div className="px-4 py-2 rounded-lg bg-warning-500/10 border border-warning-500/20">
          <p className="text-xs text-warning-400">{syncMsg}</p>
        </div>
      )}

      {/* Invite panel — teacher only */}
      {isTeacher && invites !== undefined && (
        <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle">
          <InvitePanel
            classroomId={classroomId}
            token={token!}
            invites={invites}
            onInvitesChange={setInvites}
          />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-0.5 bg-bg-surface rounded-xl p-1 border border-border-subtle w-fit">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-150 ${
              activeTab === key
                ? "bg-bg-base text-text-primary shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "leaderboard" && (
        <div className="rounded-xl bg-bg-surface border border-border-subtle overflow-hidden">
          {leaderboard === undefined ? (
            <LeaderboardTableSkeleton />
          ) : (
            <LeaderboardTable entries={leaderboard.entries} />
          )}
          {(leaderboard?.computed_at || leaderboard?.syncing) && (
            <div className="px-4 py-2 border-t border-border-subtle flex items-center gap-2">
              {leaderboard?.syncing && <Loader2 className="w-3 h-3 animate-spin text-primary-400" />}
              <p className="text-xs text-text-muted">
                {leaderboard?.syncing
                  ? "Refreshing members from Codeforces…"
                  : `Updated ${new Date(leaderboard!.computed_at!).toLocaleString()}`}
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === "cohort" && isTeacher && (
        <CohortAnalyticsPanel cohort={cohort} />
      )}

      {activeTab === "members" && isTeacher && (
        <div>
          {members === undefined ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-16 rounded-xl bg-bg-surface border border-border-subtle animate-shimmer" />
              ))}
            </div>
          ) : (
            <MemberManagement
              classroomId={classroomId}
              token={token!}
              ownerId={classroom?.owner_id ?? ""}
              members={members}
              onMembersChange={setMembers}
            />
          )}
        </div>
      )}
    </div>
  );
}

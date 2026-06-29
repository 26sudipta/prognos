"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Users, BarChart2, Settings2, Trash2, LogOut, Loader2, ArrowLeft } from "lucide-react";
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

  const isTeacher = classroom?.my_role === "teacher";

  useEffect(() => {
    if (!token || !classroomId) return;
    fetchClassroom(token, classroomId).then(setClassroom).catch(() => router.replace("/classrooms"));
  }, [token, classroomId, router]);

  useEffect(() => {
    if (!token || !classroomId) return;
    fetchLeaderboard(token, classroomId).then(setLeaderboard).catch(() => setLeaderboard(undefined));
    fetchMembers(token, classroomId)
      .then((r) => setMembers(r.members))
      .catch(() => setMembers([]));
  }, [token, classroomId]);

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
          {leaderboard?.computed_at && (
            <div className="px-4 py-2 border-t border-border-subtle">
              <p className="text-xs text-text-muted">
                Updated {new Date(leaderboard.computed_at).toLocaleString()}
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

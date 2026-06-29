"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { GraduationCap, Loader2, AlertTriangle, CheckCircle, LogIn, ShieldAlert } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import {
  JoinPreviewResponse,
  fetchJoinPreview,
  joinClassroom,
} from "@/app/_lib/classrooms";

type State =
  | { status: "loading" }
  | { status: "invalid"; errorCode: string }
  | { status: "unauthenticated"; classroom_name: string; member_count: number }
  | { status: "no_handle"; classroom_name: string }
  | { status: "already_member"; classroom_name: string; classroomId: string }
  | { status: "ready"; classroom_name: string; member_count: number }
  | { status: "joining" }
  | { status: "error"; message: string; classroom_name: string };

function errorLabel(code: string) {
  if (code === "EXPIRED") return "This invite link has expired.";
  if (code === "REVOKED") return "This invite link has been revoked.";
  return "This invite link is invalid or no longer exists.";
}

export default function JoinPage() {
  const { token: authToken, user } = useAuth();
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const inviteToken = params.token;

  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    if (!inviteToken) return;
    let cancelled = false;

    async function init() {
      const preview: JoinPreviewResponse = await fetchJoinPreview(inviteToken).catch(() => ({
        is_valid: false,
        error_code: "NOT_FOUND" as const,
      }));

      if (cancelled) return;

      if (!preview.is_valid) {
        setState({ status: "invalid", errorCode: preview.error_code ?? "NOT_FOUND" });
        return;
      }

      const classroomName = preview.classroom_name ?? "Classroom";
      const memberCount = preview.member_count ?? 0;

      // Not logged in — save intent, show sign-in prompt
      if (!authToken || !user) {
        localStorage.setItem("pending_join", inviteToken);
        setState({ status: "unauthenticated", classroom_name: classroomName, member_count: memberCount });
        return;
      }

      // Logged in — try to join immediately (server handles all guards)
      setState({ status: "ready", classroom_name: classroomName, member_count: memberCount });
    }

    init();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inviteToken, authToken]);

  async function handleJoin() {
    if (!authToken || state.status !== "ready") return;
    const classroom_name = state.classroom_name;
    setState({ status: "joining" });
    try {
      const classroom = await joinClassroom(authToken, inviteToken);
      router.replace(`/classrooms/${classroom.id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to join classroom.";
      // surface handle-not-verified as a dedicated state
      if (message.toLowerCase().includes("handle")) {
        setState({ status: "no_handle", classroom_name });
      } else if (message.toLowerCase().includes("already")) {
        // We don't have the classroom id here, so go to classrooms list
        setState({ status: "already_member", classroom_name, classroomId: "" });
      } else {
        setState({ status: "error", message, classroom_name });
      }
    }
  }

  return (
    <div className="min-h-screen bg-bg-base flex items-center justify-center p-4">
      <div className="w-full max-w-[420px]">
        <div className="p-6 rounded-2xl bg-bg-surface border border-border-subtle">
          {state.status === "loading" && (
            <div className="flex flex-col items-center gap-3 py-8">
              <Loader2 className="w-7 h-7 text-primary-400 animate-spin" />
              <p className="text-sm text-text-muted">Validating invite link…</p>
            </div>
          )}

          {state.status === "invalid" && (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <AlertTriangle className="w-8 h-8 text-danger-400" />
              <p className="text-base font-semibold text-text-primary">Invalid Invite</p>
              <p className="text-sm text-text-muted">{errorLabel(state.errorCode)}</p>
              <button
                onClick={() => router.push("/")}
                className="mt-2 text-xs text-primary-400 hover:underline"
              >
                Go to home
              </button>
            </div>
          )}

          {state.status === "unauthenticated" && (
            <div className="flex flex-col items-center gap-4 text-center">
              <GraduationCap className="w-9 h-9 text-primary-400" />
              <div>
                <p className="text-xs text-text-muted uppercase tracking-wide mb-1">You&apos;re invited to</p>
                <p className="text-lg font-bold text-text-primary">{state.classroom_name}</p>
                <p className="text-sm text-text-muted mt-1">
                  {state.member_count} member{state.member_count !== 1 ? "s" : ""}
                </p>
              </div>
              <p className="text-xs text-text-muted">Sign in to join this classroom.</p>
              <button
                onClick={() => router.push("/login")}
                className="flex items-center gap-2 w-full justify-center px-4 py-2.5 rounded-xl bg-primary-500 hover:bg-primary-600 text-white text-sm font-medium transition-colors"
              >
                <LogIn className="w-4 h-4" />
                Sign in with Google
              </button>
            </div>
          )}

          {state.status === "no_handle" && (
            <div className="flex flex-col items-center gap-4 text-center">
              <ShieldAlert className="w-8 h-8 text-warning-400" />
              <div>
                <p className="text-base font-semibold text-text-primary">Verify Your Handle First</p>
                <p className="text-sm text-text-muted mt-1">
                  You need a verified Codeforces handle to join{" "}
                  <strong className="text-text-primary">{state.classroom_name}</strong>.
                </p>
              </div>
              <button
                onClick={() => router.push("/handles")}
                className="w-full px-4 py-2.5 rounded-xl bg-warning-500/10 text-warning-400 hover:bg-warning-500/20 text-sm font-medium transition-colors"
              >
                Verify Handle
              </button>
            </div>
          )}

          {state.status === "already_member" && (
            <div className="flex flex-col items-center gap-4 text-center">
              <CheckCircle className="w-8 h-8 text-success-400" />
              <div>
                <p className="text-base font-semibold text-text-primary">Already a Member</p>
                <p className="text-sm text-text-muted mt-1">
                  You&apos;re already in <strong className="text-text-primary">{state.classroom_name}</strong>.
                </p>
              </div>
              <button
                onClick={() => router.push("/classrooms")}
                className="w-full px-4 py-2.5 rounded-xl bg-primary-500/10 text-primary-400 hover:bg-primary-500/20 text-sm font-medium transition-colors"
              >
                Go to My Classrooms
              </button>
            </div>
          )}

          {state.status === "ready" && (
            <div className="flex flex-col items-center gap-4 text-center">
              <GraduationCap className="w-9 h-9 text-primary-400" />
              <div>
                <p className="text-xs text-text-muted uppercase tracking-wide mb-1">You&apos;re invited to</p>
                <p className="text-lg font-bold text-text-primary">{state.classroom_name}</p>
                <p className="text-sm text-text-muted mt-1">
                  {state.member_count} member{state.member_count !== 1 ? "s" : ""}
                </p>
              </div>
              <button
                onClick={handleJoin}
                className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-xl bg-primary-500 hover:bg-primary-600 text-white text-sm font-medium transition-colors"
              >
                Join {state.classroom_name}
              </button>
            </div>
          )}

          {state.status === "joining" && (
            <div className="flex flex-col items-center gap-3 py-8">
              <Loader2 className="w-7 h-7 text-primary-400 animate-spin" />
              <p className="text-sm text-text-muted">Joining classroom…</p>
            </div>
          )}

          {state.status === "error" && (
            <div className="flex flex-col items-center gap-4 text-center">
              <AlertTriangle className="w-8 h-8 text-danger-400" />
              <div>
                <p className="text-base font-semibold text-text-primary">Could Not Join</p>
                <p className="text-sm text-text-muted mt-1">{state.message}</p>
              </div>
              <button
                onClick={() => router.push("/classrooms")}
                className="text-xs text-primary-400 hover:underline"
              >
                Go to My Classrooms
              </button>
            </div>
          )}
        </div>

        <p className="text-center text-xs text-text-muted mt-4">PROGNOS</p>
      </div>
    </div>
  );
}

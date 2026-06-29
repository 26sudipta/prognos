"use client";

import { apiFetch } from "@/app/_lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Classroom {
  id: string;
  name: string;
  owner_id: string;
  is_active: boolean;
  created_at: string;
  my_role: "teacher" | "student";
  member_count: number;
}

export interface ClassroomsListResponse {
  classrooms: Classroom[];
}

export interface Invite {
  id: string;
  classroom_id: string;
  token: string;
  expires_at: string;
  created_at: string;
  invite_url: string;
  is_active: boolean;
}

export interface InviteListResponse {
  invites: Invite[];
}

export interface Member {
  user_id: string;
  user_name: string;
  avatar_url: string | null;
  cf_handle: string | null;
  role: "teacher" | "student";
  joined_at: string;
}

export interface MembersListResponse {
  members: Member[];
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  cf_handle: string;
  user_name: string;
  avatar_url: string | null;
  cf_rating: number | null;
  solved_count: number;
  current_streak: number;
  longest_streak: number;
  days_active_30d: number;
  last_active_at: string | null;
  top_tags: { tag: string; solved_count: number }[] | null;
  weak_tags: { tag: string; signal_type: string; score: number }[] | null;
  computed_at: string;
  is_me: boolean;
}

export interface LeaderboardResponse {
  classroom_id: string;
  classroom_name: string;
  entries: LeaderboardEntry[];
  member_count: number;
  computed_at: string | null;
}

export interface CohortTag {
  tag: string;
  count: number;
}

export interface CohortMemberAttendance {
  user_id: string;
  user_name: string;
  cf_handle: string;
  days_active_30d: number;
}

export interface CohortAnalytics {
  classroom_id: string;
  classroom_name: string;
  member_count: number;
  class_average_rating: number | null;
  most_neglected_tags: CohortTag[];
  lowest_success_tags: CohortTag[];
  student_attendance: CohortMemberAttendance[];
}

export interface JoinPreviewResponse {
  is_valid: boolean;
  classroom_name?: string;
  member_count?: number;
  error_code?: "NOT_FOUND" | "EXPIRED" | "REVOKED";
}

// ── API Functions ──────────────────────────────────────────────────────────────

export async function fetchClassrooms(token: string): Promise<ClassroomsListResponse> {
  const res = await apiFetch("/api/v1/classrooms", { token });
  if (!res.ok) throw new Error("Failed to fetch classrooms");
  return res.json();
}

export async function createClassroom(token: string, name: string): Promise<Classroom> {
  const res = await apiFetch("/api/v1/classrooms", {
    token,
    method: "POST",
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error("Failed to create classroom");
  return res.json();
}

export async function fetchClassroom(token: string, id: string): Promise<Classroom> {
  const res = await apiFetch(`/api/v1/classrooms/${id}`, { token });
  if (!res.ok) throw new Error("Failed to fetch classroom");
  return res.json();
}

export async function deleteClassroom(token: string, id: string): Promise<void> {
  const res = await apiFetch(`/api/v1/classrooms/${id}`, { token, method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete classroom");
}

export async function fetchLeaderboard(token: string, id: string): Promise<LeaderboardResponse> {
  const res = await apiFetch(`/api/v1/classrooms/${id}/leaderboard`, { token });
  if (!res.ok) throw new Error("Failed to fetch leaderboard");
  return res.json();
}

export async function fetchCohortAnalytics(token: string, id: string): Promise<CohortAnalytics> {
  const res = await apiFetch(`/api/v1/classrooms/${id}/cohort`, { token });
  if (!res.ok) throw new Error("Failed to fetch cohort analytics");
  return res.json();
}

export async function fetchMembers(token: string, id: string): Promise<MembersListResponse> {
  const res = await apiFetch(`/api/v1/classrooms/${id}/members`, { token });
  if (!res.ok) throw new Error("Failed to fetch members");
  return res.json();
}

export async function removeMember(token: string, classroomId: string, userId: string): Promise<void> {
  const res = await apiFetch(`/api/v1/classrooms/${classroomId}/members/${userId}`, {
    token,
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to remove member");
}

export async function leaveClassroom(token: string, classroomId: string): Promise<void> {
  const res = await apiFetch(`/api/v1/classrooms/${classroomId}/members/me`, {
    token,
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to leave classroom");
}

export async function createInvite(token: string, classroomId: string): Promise<Invite> {
  const res = await apiFetch(`/api/v1/classrooms/${classroomId}/invites`, {
    token,
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to create invite");
  return res.json();
}

export async function fetchInvites(token: string, classroomId: string): Promise<InviteListResponse> {
  const res = await apiFetch(`/api/v1/classrooms/${classroomId}/invites`, { token });
  if (!res.ok) throw new Error("Failed to fetch invites");
  return res.json();
}

export async function revokeInvite(token: string, classroomId: string, inviteId: string): Promise<void> {
  const res = await apiFetch(`/api/v1/classrooms/${classroomId}/invites/${inviteId}`, {
    token,
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to revoke invite");
}

export async function joinClassroom(token: string, inviteToken: string): Promise<Classroom> {
  const res = await apiFetch("/api/v1/classrooms/join", {
    token,
    method: "POST",
    body: JSON.stringify({ token: inviteToken }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? "Failed to join classroom");
  }
  return res.json();
}

export async function fetchJoinPreview(inviteToken: string): Promise<JoinPreviewResponse> {
  const API_BASE =
    process.env.NEXT_PUBLIC_API_URL ??
    (process.env.NODE_ENV === "production" ? "" : "http://localhost:8000");
  const res = await fetch(`${API_BASE}/api/v1/classrooms/join-preview/${inviteToken}`, {
    credentials: "include",
  });
  if (!res.ok) return { is_valid: false, error_code: "NOT_FOUND" };
  return res.json();
}

// ── Utilities ──────────────────────────────────────────────────────────────────

export function cfRatingColor(rating: number | null): string {
  if (rating === null) return "text-text-muted";
  if (rating >= 2400) return "text-red-400";
  if (rating >= 2100) return "text-orange-400";
  if (rating >= 1900) return "text-violet-400";
  if (rating >= 1600) return "text-blue-400";
  if (rating >= 1400) return "text-cyan-400";
  if (rating >= 1200) return "text-green-400";
  return "text-text-secondary";
}

export function formatLastActive(isoStr: string | null): string {
  if (!isoStr) return "Never";
  const d = new Date(isoStr);
  const now = new Date();
  const days = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function formatExpiresAt(isoStr: string): string {
  const d = new Date(isoStr);
  const now = new Date();
  const hours = Math.floor((d.getTime() - now.getTime()) / (1000 * 60 * 60));
  if (hours <= 0) return "Expired";
  if (hours < 24) return `Expires in ${hours}h`;
  const days = Math.floor(hours / 24);
  return `Expires in ${days}d`;
}

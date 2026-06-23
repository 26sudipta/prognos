"use client";

import { apiFetch } from "./api";

export interface HandleData {
  id: string;
  handle: string;
  platform: string;
  is_verified: boolean;
  is_locked: boolean;
  status: string;
  sync_status: string;
  verified_at: string | null;
  last_synced_at: string | null;
  lockout_expires_at: string | null;
}

export interface InitiateData {
  handle_id: string;
  handle: string;
  platform: string;
  token: string;
  expires_at: string;
}

export interface VerifiedData {
  handle_id: string;
  handle: string;
  platform: string;
  verified_at: string;
}

export class ApiError extends Error {
  status: number;
  attemptsRemaining?: number;

  constructor(message: string, status: number, attemptsRemaining?: number) {
    super(message);
    this.status = status;
    this.attemptsRemaining = attemptsRemaining;
  }
}

export async function fetchHandles(token: string): Promise<HandleData[]> {
  const res = await apiFetch("/api/v1/handles", { token });
  if (!res.ok) throw new ApiError("Failed to fetch handles", res.status);
  return res.json();
}

export async function initiateVerification(
  token: string,
  handle: string,
): Promise<InitiateData> {
  const res = await apiFetch("/api/v1/handles/verify/initiate", {
    method: "POST",
    token,
    body: JSON.stringify({ handle, platform: "codeforces" }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail ?? "Failed to initiate verification";
    throw new ApiError(
      typeof detail === "string" ? detail : detail.message ?? "Failed to initiate verification",
      res.status,
    );
  }
  return res.json();
}

export async function confirmVerification(
  token: string,
  handleId: string,
): Promise<VerifiedData> {
  const res = await apiFetch("/api/v1/handles/verify/confirm", {
    method: "POST",
    token,
    body: JSON.stringify({ handle_id: handleId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail ?? {};
    const message =
      typeof detail === "string"
        ? detail
        : detail.message ?? "Verification failed";
    const attemptsRemaining =
      typeof detail === "object" ? detail.attempts_remaining : undefined;
    throw new ApiError(message, res.status, attemptsRemaining);
  }
  return res.json();
}

export async function unlinkHandle(token: string, handleId: string): Promise<void> {
  const res = await apiFetch(`/api/v1/handles/${handleId}`, {
    method: "DELETE",
    token,
  });
  if (!res.ok && res.status !== 204) throw new ApiError("Failed to unlink handle", res.status);
}

export async function syncHandle(token: string, handleId: string): Promise<void> {
  const res = await apiFetch(`/api/v1/handles/${handleId}/sync`, {
    method: "POST",
    token,
  });
  // 429 = cooldown active, treat as ok (sync already running or recently ran)
  if (!res.ok && res.status !== 429) throw new ApiError("Failed to start sync", res.status);
}

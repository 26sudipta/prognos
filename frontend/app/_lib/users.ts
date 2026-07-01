"use client";

import { apiFetch } from "./api";

export class UserApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function detailOf(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown })?.detail;
  return typeof detail === "string" ? detail : fallback;
}

export async function updateDisplayName(token: string, name: string): Promise<void> {
  const res = await apiFetch("/api/v1/users/me", {
    method: "PATCH",
    token,
    body: JSON.stringify({ name }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new UserApiError(detailOf(body, "Couldn't update your name"), res.status);
  }
}

export async function logoutEverywhere(token: string): Promise<void> {
  const res = await apiFetch("/api/v1/auth/logout-all", { method: "POST", token });
  if (!res.ok && res.status !== 204) {
    throw new UserApiError("Couldn't sign out everywhere", res.status);
  }
}

export async function deleteAccount(token: string): Promise<void> {
  const res = await apiFetch("/api/v1/users/me", { method: "DELETE", token });
  if (res.ok || res.status === 204) return;
  const body = await res.json().catch(() => ({}));
  throw new UserApiError(detailOf(body, "Couldn't delete your account"), res.status);
}

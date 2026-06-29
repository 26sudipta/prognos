"use client";

// In production the SPA reaches the API via the Vercel /api proxy (same-origin),
// so the base is "" (relative). Locally it falls back to the dev backend.
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "production" ? "" : "http://localhost:8000");

type RequestOptions = RequestInit & { token?: string | null };

let refreshPromise: Promise<string | null> | null = null;

async function doRefresh(): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include", // sends httpOnly cookie
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.access_token as string;
  } catch {
    return null;
  }
}

// Deduplicated refresh — multiple concurrent 401s share one refresh call
async function getRefreshedToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = doRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export async function apiFetch(
  path: string,
  options: RequestOptions = {},
  onTokenRefreshed?: (newToken: string) => void,
): Promise<Response> {
  const { token, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    ...fetchOptions,
    headers,
    credentials: "include",
  });

  // Auto-refresh on 401 then retry once
  if (res.status === 401 && token) {
    const newToken = await getRefreshedToken();
    if (!newToken) return res; // refresh failed — caller handles redirect

    if (onTokenRefreshed) onTokenRefreshed(newToken);

    return fetch(`${API_BASE}${path}`, {
      ...fetchOptions,
      headers: { ...headers, Authorization: `Bearer ${newToken}` },
      credentials: "include",
    });
  }

  return res;
}

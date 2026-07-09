// PROGNOS service worker.
// Scope: installability + instant repeat loads + a branded offline fallback.
// It NEVER touches /api/ — auth, sync freshness, and leaderboard integrity
// depend on those requests always hitting the network.

const CACHE = "prognos-static-v1";

// Self-contained fallback: no external CSS/JS, so it renders even when
// nothing else is cached.
const OFFLINE_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Offline — PROGNOS</title>
<style>
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:#070B14;color:#F1F5F9;font-family:system-ui,-apple-system,sans-serif;text-align:center}
  .card{padding:2rem;max-width:20rem}
  .icon{width:64px;height:64px;border-radius:14px;background:#6366F1;margin:0 auto 1.5rem;
    display:flex;align-items:center;justify-content:center}
  h1{font-size:1.25rem;margin:0 0 .5rem}
  p{color:#94A3B8;font-size:.875rem;line-height:1.5;margin:0 0 1.5rem}
  button{background:#6366F1;color:#fff;border:0;border-radius:10px;padding:.75rem 1.5rem;
    font-size:.875rem;font-weight:600;cursor:pointer}
</style>
</head>
<body>
<div class="card">
  <div class="icon">
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5"
      stroke-linecap="round" stroke-linejoin="round">
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>
    </svg>
  </div>
  <h1>You&rsquo;re offline</h1>
  <p>PROGNOS needs a connection to load fresh data. Check your network and try again.</p>
  <button onclick="location.reload()">Retry</button>
</div>
</body>
</html>`;

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) return; // network only, always

  // Pages: network-first, branded fallback when offline.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(
        () =>
          new Response(OFFLINE_HTML, {
            headers: { "Content-Type": "text/html; charset=utf-8" },
          })
      )
    );
    return;
  }

  // Hashed build assets + icons are immutable: cache-first.
  if (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.startsWith("/icons/")
  ) {
    event.respondWith(
      caches.open(CACHE).then(async (cache) => {
        const hit = await cache.match(request);
        if (hit) return hit;
        const response = await fetch(request);
        if (response.ok) cache.put(request, response.clone());
        return response;
      })
    );
  }
});

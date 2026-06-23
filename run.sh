#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Free a port by killing whatever holds it ─────────────────────────────────
free_port() {
    local port=$1
    local pids
    pids=$(lsof -ti:"$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        printf "Freeing port %s … " "$port"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 0.3
        echo "done"
    fi
}

free_port 8000
free_port 3000

# ── Backend (FastAPI / uvicorn) ───────────────────────────────────────────────
echo "Starting backend  →  http://localhost:8000"
cd "$ROOT/backend"
.venv/bin/uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# ── Frontend (Next.js) ────────────────────────────────────────────────────────
echo "Starting frontend →  http://localhost:3000"
cd "$ROOT/frontend"
npm run dev -- --port 3000 &
FRONTEND_PID=$!

# ── Shut both down on Ctrl+C / SIGTERM ───────────────────────────────────────
cleanup() {
    printf "\nShutting down…\n"
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM

echo ""
echo "Both servers running. Press Ctrl+C to stop."
wait

#!/usr/bin/env sh
# Container boot for the Render free-tier deployment.
#
# Why this exists instead of `alembic upgrade head && uvicorn ...`:
# the `&&` meant a single transient failure reaching Neon at boot (its compute
# scales to zero and can be slow to wake) left uvicorn unstarted. The container
# then exited, Render restarted it, and the service could sit with no healthy
# instance indefinitely. Migrations are now retried, and the server starts
# either way so the service stays reachable and reports its own state on
# /api/v1/ready instead of disappearing.
set -u

ATTEMPTS="${MIGRATE_ATTEMPTS:-5}"
DELAY="${MIGRATE_RETRY_DELAY:-5}"
n=1

while [ "$n" -le "$ATTEMPTS" ]; do
    echo "[entrypoint] alembic upgrade head (attempt $n/$ATTEMPTS)"
    if alembic upgrade head; then
        echo "[entrypoint] migrations applied"
        break
    fi
    if [ "$n" -eq "$ATTEMPTS" ]; then
        # Deliberately non-fatal: a reachable-but-unmigrated API is easier to
        # diagnose than a service with no instance at all. /api/v1/ready will
        # report the DB as down.
        echo "[entrypoint] WARNING: migrations failed after $ATTEMPTS attempts; starting server anyway"
        break
    fi
    echo "[entrypoint] migration attempt $n failed; retrying in ${DELAY}s"
    sleep "$DELAY"
    n=$((n + 1))
    DELAY=$((DELAY * 2))
done

echo "[entrypoint] starting uvicorn on port ${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

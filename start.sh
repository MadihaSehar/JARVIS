#!/usr/bin/env bash
set -euo pipefail

JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$JARVIS_DIR/backend"
FRONTEND_DIR="$JARVIS_DIR/frontend"
LOG_DIR="$JARVIS_DIR/.run-logs"
mkdir -p "$LOG_DIR"

BACKEND_PORT=8001
FRONTEND_PORT=3000

cleanup() {
  echo ""
  echo "Stopping J.A.R.V.I.S. ..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  echo "Stopped."
}
trap cleanup EXIT INT TERM

# --- backend ---
if [[ ! -d "$BACKEND_DIR/venv" ]]; then
  echo "ERROR: backend venv not found at $BACKEND_DIR/venv" >&2
  exit 1
fi

echo "Starting backend on :$BACKEND_PORT ..."
(
  cd "$BACKEND_DIR"
  source venv/bin/activate
  exec uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload
) > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

# Wait for backend to actually come up before starting the frontend
for i in $(seq 1 30); do
  if curl -s "http://localhost:$BACKEND_PORT/api/health" > /dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "ERROR: backend process died. Last log lines:" >&2
    tail -n 30 "$LOG_DIR/backend.log" >&2
    exit 1
  fi
  sleep 1
done

# --- frontend ---
echo "Starting frontend on :$FRONTEND_PORT ..."
(
  cd "$FRONTEND_DIR"
  exec npm run dev -- --port "$FRONTEND_PORT"
) > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to actually come up
for i in $(seq 1 60); do
  if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo "ERROR: frontend process died. Last log lines:" >&2
    tail -n 30 "$LOG_DIR/frontend.log" >&2
    exit 1
  fi
  sleep 1
done

LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"

echo ""
echo "================================================================"
echo " J.A.R.V.I.S. is running"
echo "   Backend:   http://localhost:$BACKEND_PORT  (logs: $LOG_DIR/backend.log)"
echo "   Frontend:  http://localhost:$FRONTEND_PORT  (logs: $LOG_DIR/frontend.log)"
if [[ -n "$LAN_IP" ]]; then
  echo ""
  echo "   Open this in a browser on your host machine:"
  echo "     http://$LAN_IP:$FRONTEND_PORT"
fi
echo ""
echo "   Press Ctrl+C to stop both servers."
echo "================================================================"
echo ""

wait

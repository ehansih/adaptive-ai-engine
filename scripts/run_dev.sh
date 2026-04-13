#!/usr/bin/env bash
# Start both backend and frontend for local development
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  echo "No .env found — copying from .env.example"
  cp .env.example .env
  echo "Edit .env and add your API keys, then re-run."
  exit 1
fi

# Backend
echo "[1/2] Starting FastAPI backend on :8000..."
cd "$ROOT"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Frontend
echo "[2/2] Starting Vite frontend on :5173..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait

#!/usr/bin/env bash
echo "========================================================"
echo " Kortex - Autonomous Research Intelligence"
echo "========================================================"

# Run backend
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Run frontend
cd frontend && npm run dev &
FRONTEND_PID=$!

echo "Backend running at:  http://127.0.0.1:8000"
echo "Frontend running at: http://127.0.0.1:5173"

trap "kill $BACKEND_PID $FRONTEND_PID" SIGINT SIGTERM EXIT
wait

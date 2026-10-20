#!/bin/bash

# ---------------------------------------------------------------
# Dashboard starter – runs the Flask UI without triggering any job bots
# ---------------------------------------------------------------
# Use the project's Python virtual environment (venv).
# ---------------------------------------------------------------

# Kill any existing dashboard process on port 5001
if lsof -ti :5001 >/dev/null 2>&1; then
  echo "🔴 Stopping any existing dashboard on port 5001..."
  lsof -ti :5001 | xargs kill -9 2>/dev/null
fi

# Activate the virtual environment
if [ -d "venv" ]; then
  source venv/bin/activate
else
  echo "❌ Virtual environment not found. Please create 'venv' first."
  exit 1
fi

# Start the Flask dashboard in the background
echo "✅ Starting dashboard (app.py) on http://localhost:5001 ..."
python3 app.py &
DASHBOARD_PID=$!

echo "Dashboard PID: $DASHBOARD_PID"

# Optional: run the Gmail tracker (read‑only) – it does not start job bots
if [ -f "modules/gmail_tracker.py" ]; then
  echo "🔄 Running Gmail tracker (read‑only)..."
  python modules/gmail_tracker.py "$@"
fi

# Keep script alive until user stops it (Ctrl+C)
trap "echo '🛑 Stopping dashboard...'; kill $DASHBOARD_PID; exit" SIGINT SIGTERM
wait $DASHBOARD_PID

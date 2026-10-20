#!/bin/bash

# ================================================================================
# LinkedIn Auto Job Applier - Startup Script (enhanced)
# ================================================================================
# This script starts both the LinkedIn Bot and the Web Dashboard simultaneously.
# It now includes log cleanup and enforces daily limits via the monitoring script.
# ================================================================================

echo "🤖 Starting the LinkedIn Auto Job Applier..."

# Ensure we are in the correct directory
cd "$(dirname "$0")" || exit

# Clean up the main log to keep it manageable (last 5000 lines)
if [ -f logs/log.txt ]; then
  tail -n 5000 logs/log.txt > logs/log.tmp && mv logs/log.tmp logs/log.txt
fi

# Check if virtual environment exists (unified Python 3.11)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "venv311" ]; then
    source venv311/bin/activate
else
    echo "❌ Error: Virtual environment not found."
    echo "Please run the setup commands first:"
    echo "/opt/homebrew/bin/python3.11 -m venv venv"
    echo "source venv/bin/activate"
    echo "pip install undetected-chromedriver pyautogui setuptools openai flask-cors flask bs4 google-generativeai google-api-python-client google-auth-httplib2 google-auth-oauthlib crewai browser-use langchain-openai playwright"
    exit 1
fi

# Kill any existing dashboard running on port 5001
lsof -ti :5001 | xargs kill -9 2>/dev/null

# Start the web dashboard in the background
echo "📊 Starting Web Dashboard (app.py) in the background..."
python3 app.py &
DASHBOARD_PID=$!

sleep 2 # Give the dashboard a second to boot up

echo "✅ Dashboard started! Monitor your applications at: http://localhost:5001"
echo "--------------------------------------------------------"
echo "🚀 Starting the Main AI Bot (runAiBot.py)..."
echo "⚠️  To stop everything at any time, press Ctrl+C"
echo "--------------------------------------------------------"

# Suppress resource_tracker warnings globally
export PYTHONWARNINGS="ignore::UserWarning"

# Catch Ctrl+C to kill the background dashboard cleanly
trap "echo 'Stopping dashboard...'; kill $DASHBOARD_PID; exit" SIGINT SIGTERM

# Start the main bot
python3 -W ignore runAiBot.py 2>/dev/null

# Cleanup if the bot exits naturally
kill $DASHBOARD_PID 2>/dev/null

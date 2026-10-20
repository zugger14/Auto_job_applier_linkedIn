#!/bin/bash

# ---------------------------------------------------------------
# LinkedIn Easy Apply Job Bot Starter
# ---------------------------------------------------------------
# This script runs only the LinkedIn Easy Apply automation (runAiBot.py)
# It does NOT launch the dashboard. Use start_dashboard.sh to start the UI.
# ---------------------------------------------------------------

# Ensure we are in the project directory
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1

# Activate the virtual environment (unified Python 3.11)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "venv311" ]; then
    source venv311/bin/activate
else
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Suppress resource_tracker warnings globally
export PYTHONWARNINGS="ignore::UserWarning"

echo "🚀 Starting LinkedIn Easy Apply bot (runAiBot.py)..."
python3 -W ignore runAiBot.py 2>/dev/null

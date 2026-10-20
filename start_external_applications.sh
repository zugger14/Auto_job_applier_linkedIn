#!/bin/bash

# Activate the virtual environment
if [ -d "venv" ]; then
  source venv/bin/activate
fi
export RESUME_PATH="$(pwd)/Shirish_Maharjan_CV copy.pdf"

# Clean up the main log to keep it manageable (last 5000 lines)
if [ -f logs/log.txt ]; then
  tail -n 5000 logs/log.txt > logs/log.tmp && mv logs/log.tmp logs/log.txt
fi

echo "============================================="
echo "   STARTING AI EXTERNAL APPLICATIONS JOB     "
echo "============================================="
echo "This will read the 'Apply Externally' jobs from your dashboard,"
echo "and use the Playwright AI Apply Engine to automatically fill them out."
echo ""

# Run the batch script
./venv/bin/python apply_external_jobs.py "$@"

echo ""
echo "Batch job finished."

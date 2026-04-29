#!/bin/bash

# Viral Video Pipeline Wrapper
# This script is designed to be called by cron or manually to process pending content.

# Configuration
PROJECT_DIR="/home/ubuntu/Desktop/gitwork/tgtoyt"
LOG_FILE="$PROJECT_DIR/automation.log"

# Navigate to project directory
cd "$PROJECT_DIR" || exit 1

# Ensure logs directory exists
mkdir -p logs

echo "--- Pipeline Run: $(date) ---" >> "$LOG_FILE"

# Check if another instance is already running
if pgrep -f "video_fetch.py" > /dev/null; then
    echo "⚠️  Another instance of video_fetch.py is already running. Skipping cron run." >> "$LOG_FILE"
    exit 0
fi

# Run the fetcher with --once flag (we will add this flag next)
# Using uv for environment management
echo "🚀 Starting pipeline..." >> "$LOG_FILE"
PYTHONUNBUFFERED=1 /home/ubuntu/.local/bin/uv run video_fetch.py --once >> "$LOG_FILE" 2>&1

echo "✅ Pipeline run finished." >> "$LOG_FILE"

#!/bin/bash

# Viral Video Bot Runner
# This script ensures the bot stays running even if it crashes or the network blips.

echo "🚀 Starting Viral Video Bot..."
echo "Press [CTRL+C] to stop."

while true; do
    # Run the main fetcher using uv with unbuffered output
    PYTHONUNBUFFERED=1 uv run video_fetch.py
    
    echo "⚠️ Bot process exited. Restarting in 5 seconds..."
    sleep 5
done

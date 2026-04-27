import os
import json
import requests
import subprocess
import time
import re
from pathlib import Path
from datetime import datetime
from logger import get_logger

TARGET_CHANNEL = "-1003737951848"
API_URL = "https://tele.alreadytaken.me"
OUTPUT_DIR = f"output/{TARGET_CHANNEL}"
PENDING_DIR = f"{OUTPUT_DIR}/pending_photos"
LOG_FILE = "processed_videos.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PENDING_DIR, exist_ok=True)
logger = get_logger()

def tlog(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def extract_yt_link(text):
    if not text: return None
    match = re.search(r'(https?://(?:www\.)?(?:youtube\.com/(?:shorts/|watch\?v=)|youtu\.be/)[^\s]+)', text)
    return match.group(1) if match else None

def main():
    tlog("🚀 Viral Video Bot starting (Terminal-only mode)...")
    while True:
        try:
            r = requests.get(f"{API_URL}/api/media?channels={TARGET_CHANNEL}", timeout=10)
            if r.status_code == 200:
                # Basic parsing
                for line in r.text.splitlines():
                    if line.startswith("data:"):
                        data = json.loads(line[5:].strip())
                        if "batch" in data:
                            for msg in data["batch"]:
                                msg_id = str(msg.get("msg_id"))
                                tlog(f"Detected msg: {msg_id}")
            
            # Simplified loop for debugging
            tlog("Cycle complete. Sleeping 10s...")
            time.sleep(10)
        except Exception as e:
            tlog(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
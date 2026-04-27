import os
import json
import requests
import subprocess
import time
import re
from pathlib import Path
from datetime import datetime

# Import our new modules
from logger import get_logger

# --- CONFIG ---
TARGET_CHANNEL = "-1003737951848"
API_URL = "https://tele.alreadytaken.me"
OUTPUT_DIR = f"output/{TARGET_CHANNEL}"
PENDING_DIR = f"{OUTPUT_DIR}/pending_photos"
LOG_FILE = "processed_videos.txt"

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PENDING_DIR, exist_ok=True)

# Initialize logger
logger = get_logger()

def send_telegram_status(message):
    """Send a status update message to the Telegram channel, trying multiple endpoints."""
    print(f"DEBUG: {message}")
    
    # List of endpoints to try
    endpoints = [
        f"{API_URL}/api/send",
        f"{API_URL}/api/text",
        f"{API_URL}/api/messages",
        f"{API_URL}/api/v1/send"
    ]
    
    payload = {
        "channel_id": TARGET_CHANNEL,
        "text": f"🤖 **BOT LOG**\n{message}"
    }

    success = False
    for url in endpoints:
        try:
            r = requests.post(url, json=payload, timeout=2)
            if r.status_code == 200:
                print(f"✅ Log sent via {url}")
                success = True
                break
        except:
            continue
            
    if not success:
        with open("logs/telegram_send_errors.log", "a") as f:
            f.write(f"{datetime.now()} | FAILED | {message}\n")

def tlog(message):
    """Helper to log both to terminal and Telegram."""
    print(message)
    send_telegram_status(message)

def download_file(channel_id, msg_id, save_path):
    """Download a file using the /api/file/{channel_id}/{msg_id} endpoint."""
    url = f"{API_URL}/api/file/{channel_id}/{msg_id}"
    try:
        r = requests.get(url, stream=True, timeout=30)
        if r.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        else:
            print(f"❌ Failed to download {msg_id}: HTTP {r.status_code}")
    except Exception as e:
        print(f"❌ Download Error ({msg_id}): {e}")
    return False

def extract_yt_link(text):
    if not text: return None
    match = re.search(r'(https?://(?:www\.)?(?:youtube\.com/(?:shorts/|watch\?v=)|youtu\.be/)[^\s]+)', text)
    return match.group(1) if match else None

def process_beat_sync(photos, yt_link, trigger_msg_id):
    """Trigger the beat-sync pipeline."""
    try:
        tlog(f"🎵 Starting beat-sync for {len(photos)} photos...")
        cmd = ["uv", "run", "beat_sync.py", "--link", yt_link, "--output", f"{OUTPUT_DIR}/sync_{trigger_msg_id}.mp4"]
        for p in photos:
            cmd.extend(["--photos", os.path.join(PENDING_DIR, p)])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            tlog(f"✅ Beat-sync complete! Output: sync_{trigger_msg_id}.mp4")
            # --- UPLOAD TO YOUTUBE ---
            final_output = f"{OUTPUT_DIR}/sync_{trigger_msg_id}.mp4"
            upscale_output = f"{OUTPUT_DIR}/sync_{trigger_msg_id}_4k.mp4"
            
            tlog("🚀 Upscaling to 4K...")
            upscale_cmd = [
                "ffmpeg", "-y", "-i", final_output,
                "-vf", "scale=2160:3840:flags=lanczos,unsharp=5:5:1.0:5:5:0.0",
                "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-c:a", "copy",
                upscale_output
            ]
            subprocess.run(upscale_cmd, capture_output=True)
            
            tlog("☁️ Uploading to YouTube...")
            upload_cmd = ["uv", "run", "upload_to_youtube.py", "--file", upscale_output, "--title", "Viral Beat Sync #Shorts"]
            subprocess.run(upload_cmd, capture_output=True)
            return True
        else:
            tlog(f"❌ Beat-sync failed: {result.stderr}")
    except Exception as e:
        tlog(f"❌ Error in process_beat_sync: {e}")
    return False

def process_standalone_video(channel_id, msg_id, caption):
    """Process a standalone video (viralize + upload)."""
    raw_path = os.path.join(OUTPUT_DIR, f"raw_video_{msg_id}.mp4")
    viral_path = os.path.join(OUTPUT_DIR, f"video_{msg_id}.mp4")
    upscale_path = os.path.join(OUTPUT_DIR, f"video_{msg_id}_4k.mp4")

    if download_file(channel_id, msg_id, raw_path):
        tlog(f"🪄 Applying viral effects to video {msg_id}...")
        viral_cmd = ["uv", "run", "viralize_video.py", "--input", raw_path, "--output", viral_path]
        res = subprocess.run(viral_cmd, capture_output=True, text=True)
        
        if res.returncode == 0:
            tlog(f"🚀 Upscaling video {msg_id} to 4K...")
            upscale_cmd = [
                "ffmpeg", "-y", "-i", viral_path,
                "-vf", "scale=2160:3840:flags=lanczos,unsharp=5:5:1.0:5:5:0.0",
                "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-c:a", "copy",
                upscale_path
            ]
            subprocess.run(upscale_cmd, capture_output=True)
            
            tlog(f"☁️ Uploading video {msg_id} to YouTube...")
            upload_cmd = ["uv", "run", "upload_to_youtube.py", "--file", upscale_path, "--title", f"Viral Edit {msg_id} #Shorts"]
            subprocess.run(upload_cmd, capture_output=True)
            return True
        else:
            tlog(f"❌ Viralizing failed: {res.stderr}")
    return False

def fetch_media_messages():
    """Fetch media messages (photos/videos) from /api/media."""
    messages = []
    try:
        r = requests.get(f"{API_URL}/api/media?channels={TARGET_CHANNEL}", timeout=10)
        if r.status_code == 200:
            for line in r.text.splitlines():
                if line.startswith("data:"):
                    try:
                        parsed = json.loads(line[5:].strip())
                        if "batch" in parsed:
                            messages.extend(parsed["batch"])
                    except: continue
    except Exception as e:
        print(f"⚠️ Media API error: {e}")
    return messages

def fetch_text_messages():
    """Fetch text/all messages from /api/updates."""
    messages = []
    try:
        r = requests.get(f"{API_URL}/api/updates?channels={TARGET_CHANNEL}", timeout=5)
        if r.status_code == 200:
            for line in r.text.splitlines():
                if line.startswith("data:"):
                    try:
                        parsed = json.loads(line[5:].strip())
                        if isinstance(parsed, dict) and "batch" in parsed:
                            messages.extend(parsed["batch"])
                        elif isinstance(parsed, list):
                            messages.extend(parsed)
                    except: continue
    except Exception as e:
        pass
    return messages

def main():
    tlog("🚀 **Viral Video Bot is now awake!**")
    tlog("📡 Monitoring channel for new content...")

    while True:
        try:
            all_messages = fetch_media_messages()
            text_messages = fetch_text_messages()

            seen_ids = set()
            merged = []
            for m in all_messages + text_messages:
                mid = m.get('msg_id')
                if mid and mid not in seen_ids:
                    seen_ids.add(mid)
                    merged.append(m)
            merged.sort(key=lambda x: x.get('msg_id', 0))

            processed_ids = set()
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r") as f:
                    processed_ids = set(f.read().splitlines())

            batch_yt_link = None
            for msg in merged:
                msg_id = str(msg.get('msg_id', ''))
                if not msg_id or msg_id in processed_ids: continue
                
                m_type = msg.get('type')
                caption = msg.get('caption', '') or msg.get('text', '') or ''
                yt_link = extract_yt_link(caption)

                if m_type == 'photo':
                    path = os.path.join(PENDING_DIR, f"photo_{msg_id}.jpg")
                    if download_file(TARGET_CHANNEL, msg_id, path):
                        count = len(os.listdir(PENDING_DIR))
                        tlog(f"📸 Photo {msg_id} stacked. (Total: {count})")
                    if yt_link: batch_yt_link = (yt_link, msg_id)
                    with open(LOG_FILE, "a") as f: f.write(f"{msg_id}\n")

                elif m_type == 'video' and yt_link:
                    photos = sorted(os.listdir(PENDING_DIR))
                    if len(photos) > 0:
                        tlog(f"🎵 Beat-Sync Triggered by video {msg_id}!")
                        if process_beat_sync(photos, yt_link, msg_id):
                            for p in photos: os.remove(os.path.join(PENDING_DIR, p))
                    with open(LOG_FILE, "a") as f: f.write(f"{msg_id}\n")

                elif m_type == 'video':
                    tlog(f"🎥 Standalone video {msg_id} detected.")
                    if process_standalone_video(TARGET_CHANNEL, msg_id, caption):
                        tlog(f"✅ Video {msg_id} processed.")
                    with open(LOG_FILE, "a") as f: f.write(f"{msg_id}\n")
                
                else:
                    if yt_link: batch_yt_link = (yt_link, msg_id)
                    with open(LOG_FILE, "a") as f: f.write(f"{msg_id}\n")

            if batch_yt_link:
                yt_link, trigger_id = batch_yt_link
                photos = sorted(os.listdir(PENDING_DIR))
                if len(photos) > 0:
                    tlog(f"🎵 Beat-Sync Triggered by text/link in batch!")
                    if process_beat_sync(photos, yt_link, trigger_id):
                        for p in photos: os.remove(os.path.join(PENDING_DIR, p))

        except Exception as e:
            print(f"Error in main loop: {e}")

        time.sleep(10)

if __name__ == "__main__":
    main()
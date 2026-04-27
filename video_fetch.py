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

def tlog(message):
    """Log to terminal and log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} | {message}")
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/bot_activity.log", "a") as f:
            f.write(f"{timestamp} | {message}\n")
    except Exception:
        pass

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
        # beat_sync.py expects: --photos (dir), --audio (link), --output (dir)
        cmd = ["uv", "run", "beat_sync.py", "--photos", PENDING_DIR, "--audio", yt_link, "--output", OUTPUT_DIR]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Find the output path in the stdout
            final_output = None
            for line in result.stdout.splitlines():
                if line.startswith("OUTPUT_PATH:"):
                    final_output = line.split(":", 1)[1].strip()
                    break
            
            if not final_output or not os.path.exists(final_output):
                tlog(f"❌ Beat-sync failed: Could not find output file in logs")
                return False

            tlog(f"✅ Beat-sync complete! Output: {os.path.basename(final_output)}")
            upscale_output = os.path.join(OUTPUT_DIR, f"sync_{trigger_msg_id}_upscaled.mp4")
            
            tlog("🚀 Upscaling for Shorts...")
            upscale_cmd = [
                "ffmpeg", "-y", "-i", final_output,
                "-vf", "scale=-2:3840:flags=lanczos,crop=2160:3840,unsharp=5:5:1.0:5:5:0.0",
                "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-c:a", "copy",
                upscale_output
            ]
            subprocess.run(upscale_cmd, capture_output=True)
            
            upload_file = upscale_output if os.path.exists(upscale_output) else final_output
            tlog(f"☁️ Uploading {upload_file} to YouTube...")
            upload_cmd = ["uv", "run", "upload_to_youtube.py", "--video", upload_file]
            res = subprocess.run(upload_cmd, capture_output=True, text=True)
            if res.returncode == 0:
                tlog(f"✅ Upload complete!")
            else:
                tlog(f"❌ Upload failed: {res.stderr[-200:] if res.stderr else 'unknown'}")
            return True
        else:
            tlog(f"❌ Beat-sync failed: {result.stderr[-300:] if result.stderr else 'unknown'}")
    except Exception as e:
        tlog(f"❌ Error in process_beat_sync: {e}")
    return False

def process_standalone_video(channel_id, msg_id, caption):
    """Process a standalone video (viralize + upload)."""
    raw_path = os.path.join(OUTPUT_DIR, f"raw_video_{msg_id}.mp4")
    viral_path = os.path.join(OUTPUT_DIR, f"video_{msg_id}.mp4")
    upscale_path = os.path.join(OUTPUT_DIR, f"video_{msg_id}_upscaled.mp4")

    if not download_file(channel_id, msg_id, raw_path):
        return False

    # Save caption for metadata generation
    if caption:
        caption_path = os.path.join(OUTPUT_DIR, f"video_{msg_id}.mp4.caption")
        with open(caption_path, "w") as f:
            f.write(caption)

    tlog(f"🪄 Applying viral effects to video {msg_id}...")
    viral_cmd = ["uv", "run", "viralize_video.py", "--input", raw_path, "--output", viral_path]
    res = subprocess.run(viral_cmd, capture_output=True, text=True)
    
    if res.returncode != 0:
        tlog(f"❌ Viralizing failed for {msg_id}: {res.stderr[-300:] if res.stderr else 'unknown'}")
        # Try uploading raw video instead
        tlog(f"⏩ Falling back to raw video upload for {msg_id}")
        viral_path = raw_path

    tlog(f"🚀 Upscaling video {msg_id} for Shorts...")
    upscale_cmd = [
        "ffmpeg", "-y", "-i", viral_path,
        "-vf", "scale=-2:3840:flags=lanczos,crop=2160:3840,unsharp=5:5:1.0:5:5:0.0",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-c:a", "copy",
        upscale_path
    ]
    up_res = subprocess.run(upscale_cmd, capture_output=True, text=True)
    
    upload_file = upscale_path if (up_res.returncode == 0 and os.path.exists(upscale_path)) else viral_path
    
    tlog(f"☁️ Uploading video {msg_id} to YouTube...")
    upload_cmd = ["uv", "run", "upload_to_youtube.py", "--video", upload_file]
    upload_res = subprocess.run(upload_cmd, capture_output=True, text=True)
    
    if upload_res.returncode == 0:
        tlog(f"✅ Video {msg_id} uploaded successfully!")
        # Cleanup intermediate files
        for f in [raw_path, viral_path, upscale_path]:
            if os.path.exists(f) and f != upload_file:
                try: os.remove(f)
                except: pass
        return True
    else:
        tlog(f"❌ Upload failed for {msg_id}: {upload_res.stderr[-200:] if upload_res.stderr else 'unknown'}")
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

def load_processed_ids():
    """Load the set of already-processed message IDs."""
    processed = set()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Handle both "123" and "SHORT:video_123.mp4" formats
                if ":" in line:
                    # Extract msg_id from "SHORT:video_123.mp4"
                    try:
                        fname = line.split(":", 1)[1]
                        mid = fname.split("_")[1].split(".")[0]
                        processed.add(mid)
                    except (IndexError, ValueError):
                        pass
                else:
                    processed.add(line)
    return processed


def mark_processed(msg_id):
    """Mark a message ID as processed."""
    with open(LOG_FILE, "a") as f:
        f.write(f"{msg_id}\n")


def main():
    tlog("🚀 Viral Video Bot is now awake!")
    tlog(f"📡 Monitoring channel {TARGET_CHANNEL} for new content...")

    while True:
        try:
            all_messages = fetch_media_messages()
            text_messages = fetch_text_messages()

            # Merge and deduplicate
            seen_ids = set()
            merged = []
            for m in all_messages + text_messages:
                mid = m.get('msg_id')
                if mid and mid not in seen_ids:
                    seen_ids.add(mid)
                    merged.append(m)
            merged.sort(key=lambda x: x.get('msg_id', 0))

            # Load processed IDs fresh each loop
            processed_ids = load_processed_ids()

            # Filter to only new messages
            new_messages = [m for m in merged if str(m.get('msg_id', '')) not in processed_ids]
            
            if not new_messages:
                # Nothing new — wait longer before next poll
                time.sleep(30)
                continue

            tlog(f"📥 {len(new_messages)} new message(s) to process")

            batch_yt_link = None
            for msg in new_messages:
                msg_id = str(msg.get('msg_id', ''))
                if not msg_id:
                    continue
                
                m_type = msg.get('type')
                caption = msg.get('caption', '') or msg.get('text', '') or ''
                yt_link = extract_yt_link(caption)

                if m_type == 'photo':
                    path = os.path.join(PENDING_DIR, f"photo_{msg_id}.jpg")
                    if not os.path.exists(path):  # Don't re-download
                        if download_file(TARGET_CHANNEL, msg_id, path):
                            count = len(os.listdir(PENDING_DIR))
                            tlog(f"📸 Photo {msg_id} stacked. (Total: {count})")
                    if yt_link:
                        batch_yt_link = (yt_link, msg_id)
                    mark_processed(msg_id)

                elif m_type == 'video' and yt_link:
                    # Video with YT link → trigger beat-sync with pending photos
                    photos = sorted(os.listdir(PENDING_DIR))
                    if len(photos) > 0:
                        tlog(f"🎵 Beat-Sync Triggered by video {msg_id}!")
                        if process_beat_sync(photos, yt_link, msg_id):
                            for p in photos:
                                try: os.remove(os.path.join(PENDING_DIR, p))
                                except: pass
                    else:
                        # No photos waiting, process as standalone
                        tlog(f"🎥 Video {msg_id} with link but no pending photos, processing standalone...")
                        process_standalone_video(TARGET_CHANNEL, msg_id, caption)
                    mark_processed(msg_id)

                elif m_type == 'video':
                    tlog(f"🎥 Standalone video {msg_id} detected.")
                    process_standalone_video(TARGET_CHANNEL, msg_id, caption)
                    mark_processed(msg_id)
                
                else:
                    # Text message — check for YT link
                    if yt_link:
                        batch_yt_link = (yt_link, msg_id)
                    mark_processed(msg_id)

            # After processing all messages, check if we have photos + a YT link
            if batch_yt_link:
                yt_link, trigger_id = batch_yt_link
                photos = sorted(os.listdir(PENDING_DIR))
                if len(photos) > 0:
                    tlog(f"🎵 Beat-Sync Triggered by link in msg {trigger_id}!")
                    if process_beat_sync(photos, yt_link, trigger_id):
                        for p in photos:
                            try: os.remove(os.path.join(PENDING_DIR, p))
                            except: pass

        except Exception as e:
            tlog(f"❌ Error in main loop: {e}")
            import traceback
            traceback.print_exc()

        time.sleep(15)


if __name__ == "__main__":
    main()
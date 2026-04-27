import os
import json
import requests
import subprocess
import time
import re
from pathlib import Path

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
    """Send a status update message to the Telegram channel."""
    try:
        url = f"{API_URL}/api/send"
        payload = {
            "channel_id": TARGET_CHANNEL,
            "text": f"🤖 **BOT STATUS**\n{message}"
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Failed to send Telegram notification: {e}")

def download_file(channel_id, msg_id, save_path):
    """Download a file using the /api/file/{channel_id}/{msg_id} endpoint."""
    url = f"{API_URL}/api/file/{channel_id}/{msg_id}"
    logger.log_download_start(url, save_path)
    send_telegram_status(f"📥 Downloading new media...\nID: `{msg_id}`")
    print(f"⬇️  Downloading from {url}...")

    try:
        r = requests.get(url, timeout=120)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(r.content)

            file_size = len(r.content)
            logger.log_download_complete(url, save_path, file_size, 0)
            print(f"✅ Saved to {save_path} ({file_size} bytes)")
            return True
        else:
            error_msg = f"HTTP {r.status_code}"
            logger.log_download_error(url, error_msg)
            print(f"❌ Download failed: {error_msg}")
            return False
    except Exception as e:
        logger.log_download_error(url, str(e))
        print(f"❌ Download failed: {e}")
        return False

def extract_yt_link(text):
    """Extract a YouTube/YouTube Shorts link from text."""
    if not text:
        return None
    # Match youtube.com/shorts/xxx, youtu.be/xxx, youtube.com/watch?v=xxx
    match = re.search(r'(https?://(?:www\.)?(?:youtube\.com/(?:shorts/|watch\?v=)|youtu\.be/)[^\s]+)', text)
    return match.group(1) if match else None

def process_beat_sync(photos, yt_link, msg_id):
    """Process beat sync with enhanced viral effects."""
    logger.log_pipeline_start(f"beat_sync_{msg_id}", "photo_sequence", "youtube_audio")

    try:
        print(f"🚀 TRIGGER! YouTube link found in caption of message {msg_id}")
        print(f"🎵 Audio source: {yt_link}")
        print(f"📸 Photos in stack: {len(photos)}")

        send_telegram_status(f"🎵 **Beat-Sync Triggered!**\n📸 Photos: {len(photos)}\n📻 Audio: {yt_link}")
        # Use enhanced beat sync with all new features
        result = subprocess.run([
            "uv", "run", "beat_sync.py",
            "--photos", PENDING_DIR,
            "--audio", yt_link,
            "--output", OUTPUT_DIR
        ], capture_output=True, text=True, check=True)

        print(result.stdout)

        video_path = None
        for line in result.stdout.splitlines():
            if line.startswith("OUTPUT_PATH:"):
                video_path = line.split("OUTPUT_PATH:")[1].strip()
                break

        if video_path and os.path.exists(video_path):
            print(f"📤 Uploading beat-sync video to YouTube...")
            logger.log_upload_start(video_path, "YouTube")

            # Upload to YouTube
            upload_result = subprocess.run([
                "uv", "run", "upload_to_youtube.py",
                "--video", video_path,
                "--type", "SHORT",
                "--delete-after"
            ], capture_output=True, text=True, check=True)

            print(upload_result.stdout)
            print("✅ Upload successful!")
            send_telegram_status(f"✅ **SUCCESS!**\nBeat-sync video uploaded to YouTube!")
            logger.log_upload_complete(video_path, "YouTube", "unknown", 0)
            return True
        else:
            print("❌ No video output generated")
            return False

    except subprocess.CalledProcessError as e:
        logger.log_processing_error(f"beat_sync_{msg_id}", "Beat Sync Process", str(e))
        print(f"❌ Error: {e}")
        if e.stdout: print(e.stdout)
        if e.stderr: print(e.stderr)
        return False

def process_standalone_video(channel_id, msg_id, caption):
    """Process standalone video with enhanced viral effects."""
    logger.log_pipeline_start(f"video_{msg_id}", "video", "standalone_processing")

    try:
        print(f"🎥 Standalone video {msg_id}. Downloading, viralizing, uploading...")

        raw_path = os.path.join(OUTPUT_DIR, f"raw_video_{msg_id}.mp4")
        viral_path = os.path.join(OUTPUT_DIR, f"video_{msg_id}.mp4")
        caption_path = viral_path + ".caption"

        if download_file(channel_id, msg_id, raw_path):
            # Save caption for metadata
            if caption:
                with open(caption_path, "w") as f:
                    f.write(caption)

            # Viralize — single fast pass (1080x1920 + viral filters)
            print(f"🪄 Viralizing video {msg_id}...")
            send_telegram_status(f"🪄 **Processing Video...**\nApplying viral effects to `{msg_id}`")
            subprocess.run([
                "uv", "run", "viralize_video.py",
                "--input", raw_path,
                "--output", viral_path
            ], check=True)

            # 4K Upscale — crystal clear before upload
            upscale_path = os.path.join(OUTPUT_DIR, f"video_{msg_id}_4k.mp4")
            print(f"📐 Upscaling to 4K...")
            send_telegram_status(f"📐 **Upscaling to 4K...**\nCrystal clear render for `{msg_id}`")
            subprocess.run([
                "ffmpeg", "-y", "-i", viral_path,
                "-vf", "scale=2160:3840:flags=lanczos,unsharp=5:5:0.8:5:5:0.0",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "copy",
                "-pix_fmt", "yuv420p", "-threads", "0",
                "-movflags", "+faststart",
                upscale_path
            ], check=True, capture_output=True, text=True)
            # Replace 1080p with 4K version
            os.replace(upscale_path, viral_path)
            print(f"✅ 4K upscale done!")

            # Upload to YouTube
            print(f"📤 Uploading to YouTube...")
            logger.log_upload_start(viral_path, "YouTube")

            upload_result = subprocess.run([
                "uv", "run", "upload_to_youtube.py",
                "--video", viral_path,
                "--type", "SHORT",
                "--delete-after"
            ], capture_output=True, text=True, check=True)

            print(upload_result.stdout)
            print(f"🚀 Video {msg_id} uploaded!")
            send_telegram_status(f"🚀 **UPLOADED!**\nVideo `{msg_id}` is now live on YouTube Shorts!")
            logger.log_upload_complete(viral_path, "YouTube", "unknown", 0)

            # Cleanup
            if os.path.exists(raw_path): os.remove(raw_path)
            if os.path.exists(caption_path): os.remove(caption_path)

            return True
        else:
            return False

    except Exception as e:
        logger.log_processing_error(f"video_{msg_id}", "Standalone Video Process", str(e))
        print(f"❌ Failed to process video {msg_id}: {e}")
        if os.path.exists(raw_path): os.remove(raw_path)
        return False

def main():
    print("📡 Advanced Video Automation System is now awake!")
    print("   ➡️  Enhanced with hook detection, 4K upscaling, and viral effects")
    print("   ➡️  Photos are stacked in the holding pen")
    print("   ➡️  A photo/video with a YouTube link as caption triggers beat-sync")
    print("   ➡️  Standalone videos get viralized with advanced processing and uploaded")
    print("   ➡️  All operations are logged with timestamps and status tracking")

    while True:
        all_messages = []

        try:
            r = requests.get(f"{API_URL}/api/media?channels={TARGET_CHANNEL}", timeout=30, stream=True)

            for line in r.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    json_string = line[5:].strip()
                    try:
                        parsed_data = json.loads(json_string)
                        if "batch" in parsed_data:
                            all_messages.extend(parsed_data["batch"])
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error_logger.error(f"API Request Failed: {e}. Retrying in 5 seconds...")
            print(f"❌ API Request Failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)
            continue

        processed_ids = set()
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                processed_ids = set(f.read().splitlines())

        # Sort messages by msg_id so we process in chronological order
        all_messages.sort(key=lambda m: m.get('msg_id', 0))

        for msg in all_messages:
            msg_id = str(msg.get('msg_id', ''))
            channel_id = str(msg.get('channel_id', TARGET_CHANNEL))
            m_type = msg.get('type')
            caption = msg.get('caption', '')

            if not msg_id or msg_id in processed_ids:
                continue

            yt_link = extract_yt_link(caption)

            # --- PATH A: PHOTO WITH YOUTUBE LINK = TRIGGER ---
            if m_type == 'photo' and yt_link:
                # This photo's caption has a YouTube link — it's the trigger!
                # First, save this photo too
                path = os.path.join(PENDING_DIR, f"photo_{msg_id}.jpg")
                download_file(channel_id, msg_id, path)

                photos = sorted(os.listdir(PENDING_DIR))
                if len(photos) > 0:
                    if process_beat_sync(photos, yt_link, msg_id):
                        # Cleanup all photos from the holding pen
                        for p in photos:
                            os.remove(os.path.join(PENDING_DIR, p))

                with open(LOG_FILE, "a") as f: f.write(f"{msg_id}\n")

            # --- PATH B: REGULAR PHOTO (no YT link) = STACK IT ---
            elif m_type == 'photo':
                path = os.path.join(PENDING_DIR, f"photo_{msg_id}.jpg")
                if download_file(channel_id, msg_id, path):
                    print(f"📸 Photo {msg_id} added to stack. ({len(os.listdir(PENDING_DIR))} total)")
                with open(LOG_FILE, "a") as f: f.write(f"{msg_id}\n")

            # --- PATH C: VIDEO WITH YOUTUBE LINK = TRIGGER ---
            elif m_type == 'video' and yt_link:
                photos = sorted(os.listdir(PENDING_DIR))
                if len(photos) > 0:
                    if process_beat_sync(photos, yt_link, msg_id):
                        # Cleanup all photos from the holding pen
                        for p in photos:
                            os.remove(os.path.join(PENDING_DIR, p))
                else:
                    print(f"ℹ️ Got a YouTube link on video {msg_id}, but photo stack is empty.")

                with open(LOG_FILE, "a") as f: f.write(f"{msg_id}\n")

            # --- PATH D: STANDALONE VIDEO (no YT link) = VIRALIZE & UPLOAD ---
            elif m_type == 'video':
                if process_standalone_video(channel_id, msg_id, caption):
                    print(f"✅ Successfully processed video {msg_id}")
                else:
                    print(f"❌ Failed to process video {msg_id}")

                with open(LOG_FILE, "a") as f: f.write(f"{msg_id}\n")

        # Wait before next check
        time.sleep(5)

if __name__ == "__main__":
    main()
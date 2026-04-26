import os
import pickle
import sys
import argparse
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import random

# --- Configuration ---
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATH = Path("token.pickle")
CLIENT_SECRET_PATH = Path("client.json")
LOG_FILE = "processed_videos.txt"

VIRAL_HOOKS = [
    "Wait for it... 😱",
    "You won't believe the ending! 🔥",
    "This changed everything 🤯",
    "Most satisfying thing you'll see today ✨",
    "I was not expecting that... 💀",
    "Level: IMPOSSIBLE 🏆",
    "Is this even real? 🧐",
    "Watch until the end! 👇",
    "Absolute perfection 💎",
    "Best Anime Moments 🌸",
    "Unbelievable Anime Art! ✨",
    "The details are insane... 🤯",
    "This Anime style is 10/10 🔥",
    "Wait for the transformation! 🎭",
    "Anime fans, you need to see this! 🇯🇵",
    "Satisfying Anime Vibes 🌙",
    "Legendary Anime Edit 💎",
    "Anime magic is real ✨",
    "POV: You found the best anime 🍿",
    "Can we talk about this animation? 🎨",
    "This edit goes HARD 🔥",
    "Hidden Gem Alert! 💎",
    "Top Tier Anime 🏆",
    "You need to watch this right now ‼️",
    "The 4K quality is insane! 💎",
    "Absolute 4K perfection ✨",
    "Best edit in Ultra HD 🏆",
    "Wait for the 4K drop! 🔥",
    "Top notch animation quality 💎"
]

TRENDING_TAGS = [
    "Anime", "AnimeEdit", "AnimeShorts", "ViralAnime", "Otaku", 
    "Manga", "AnimeArt", "Japan", "Shorts", "Trending", "Viral",
    "Satisfying", "Amazing", "Glitch", "Aesthetic", "Edit",
    "AnimeLover", "AnimeCommunity", "ForYou", "FYP", "Explore",
    "4K", "UltraHD", "HighQuality", "TopTier"
]

# --- Helper Functions ---
def get_caption(video_path):
    """Try to find a caption file for the original raw video."""
    try:
        # Handle different naming conventions (CLIP_video_..., PROCESSED_video_..., or original video_...)
        filename = video_path.name
        raw_id = None
        
        if "video_" in filename:
            # Extract ID: works for video_123.mp4, CLIP_video_123.mp4_1.mp4, PROCESSED_video_123.mp4
            raw_id = filename.split("video_")[1].split(".mp4")[0]
            
        if raw_id:
            caption_file = video_path.parent / f"video_{raw_id}.mp4.caption"
            if caption_file.exists():
                return caption_file.read_text().strip()
    except Exception:
        pass
    return ""

def mark_as_uploaded(filename, video_type):
    entry = f"{video_type}:{filename}"
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

def get_credentials():
    """Manages OAuth2 credentials, refreshing if possible or asking for manual code."""
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET_PATH.exists():
                print(f"❌ Error: Missing {CLIENT_SECRET_PATH}")
                sys.exit(1)

            # Manual grant flow for headless servers
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_PATH), 
                SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f'\n1. Go to this URL in your browser:\n{auth_url}')
            code = input('\n2. Enter the authorization code here: ').strip()
            flow.fetch_token(code=code)
            creds = flow.credentials

        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    return creds

def generate_metadata(video_path):
    caption = get_caption(video_path)
    hook = random.choice(VIRAL_HOOKS)
    
    # Title logic
    if caption:
        title = f"{hook} {caption}"
    else:
        title = f"{hook} Anime Moments"
    
    # Trim to 100 chars (YT limit)
    title = title[:100]

    # Description logic
    desc = f"{title}\n\n"
    if caption:
        desc += f"Original Story: {caption}\n\n"
    desc += "Follow for more amazing Shorts ! ✨\n\n"
    desc += " #".join([""] + TRENDING_TAGS)

    return title, desc, TRENDING_TAGS

import subprocess

def get_duration(video_path):
    """Get the duration of a video using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0

# --- Main Upload Logic ---
def upload_video(video_path, title, description, tags, privacy="public", delete_after=True, video_type="SHORT"):
    """Uploads video using the Youtube API and deletes source on success."""
    
    # SAFETY CHECK: Never upload anything longer than 60 seconds (Shorts limit)
    duration = get_duration(video_path)
    if duration > 60:
        print(f"🛑 CRITICAL SAFETY REJECTION: {video_path.name} is {duration:.1f}s long.")
        print(f"Shorts must be under 60 seconds. Refusing to upload full-length video.")
        sys.exit(1)

    # Authenticate
    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"
        },
       "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        }
    }

    if video_path.stat().st_size == 0:
        print(f"❌ Error: {video_path.name} is empty.")
        return None

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)

    try:
        print(f"\n[youtube] Uploading: {video_path.name} ({duration:.1f}s)")
        print(f"  Title: {title}")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"  Progress: {int(status.progress() * 100)}%", end="\r")

        video_id = response.get("id")
        if video_id:
            print(f"\n✅ Uploaded! ID: {video_id}")
            mark_as_uploaded(video_path.name, video_type)
            
            if delete_after:
                video_path.unlink()
                print(f"🗑️ Deleted local clip: {video_path.name}")
            return video_id

    except Exception as e:
        print(f"\n❌ YouTube Upload Failed: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--type", choices=["SHORT", "FULL"], default="SHORT")
    parser.add_argument("--privacy", default="public", choices=["public", "private", "unlisted"])
    parser.add_argument("--delete-after", action="store_true")
    args = parser.parse_args()

    v_path = Path(args.video)
    if not v_path.exists():
        print(f"❌ File not found: {args.video}")
        sys.exit(1)

    title, desc, tags = generate_metadata(v_path)

    video_id = upload_video(
        v_path, 
        title, 
        desc, 
        tags, 
        args.privacy, 
        args.delete_after, 
        args.type
    )
    if video_id:
        print(f"URL: https://youtu.be/{video_id}")

if __name__ == "__main__":
    main()
import os
import pickle
import sys
import argparse
import subprocess
import random
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# --- Configuration ---
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",  # Needed for thumbnail upload
]
TOKEN_PATH = Path("token.pickle")
CLIENT_SECRET_PATH = Path("client.json")
LOG_FILE = "processed_videos.txt"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VIRAL TITLE ENGINE — Hooks designed for maximum CTR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Category A: Curiosity Gap (makes people NEED to click)
CURIOSITY_HOOKS = [
    "Nobody expected this ending...",
    "Wait for the last second 😱",
    "I still cannot believe this happened",
    "This is the one everyone's talking about",
    "You've never seen anything like this",
    "The twist at the end broke me 💀",
    "I've watched this 100 times already",
    "They said it was impossible...",
    "This is what perfection looks like",
    "The moment that changed everything",
]

# Category B: Emotional Triggers
EMOTION_HOOKS = [
    "This hit different at 2AM 🌙",
    "Why does this give me chills every time",
    "Pure goosebumps 🔥",
    "The vibes are unmatched ✨",
    "This is art in motion 🎨",
    "Absolutely mesmerizing",
    "The beauty in this is unreal",
    "This made my day 💫",
    "I cannot stop watching this",
    "The most satisfying thing you'll see today",
]

# Category C: Authority/Social Proof
AUTHORITY_HOOKS = [
    "10M views on TikTok for a reason",
    "The edit that broke the internet 🌐",
    "Everyone needs to see this",
    "This deserves to go viral 🚀",
    "How is this not trending yet?",
    "The most underrated edit ever",
    "This is next level content",
    "Peak content right here 📈",
    "Hidden gem alert 💎",
    "Top tier quality 🏆",
]

ALL_HOOKS = CURIOSITY_HOOKS + EMOTION_HOOKS + AUTHORITY_HOOKS

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRENDING TAGS — Algorithm-optimized for discovery
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORE_TAGS = [
    "shorts", "viral", "trending", "fyp", "foryou", "foryoupage",
    "viralshorts", "trendingshorts", "shortvideo", "ytshorts",
]

CONTENT_TAGS = [
    "anime", "animeedit", "animeshorts", "animeart", "otaku",
    "manga", "animelover", "animecommunity", "japananime",
    "animevibes", "animemoments", "bestanime", "topanime",
]

ENGAGEMENT_TAGS = [
    "satisfying", "amazing", "incredible", "mustwatch", "watchthis",
    "mindblowing", "aesthetic", "beautiful", "stunning", "epic",
    "viral2025", "explore", "recommended", "trendingvideo",
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THUMBNAIL GENERATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_thumbnail(video_path, thumbnail_path):
    """
    Extract the most engaging frame from the video and enhance it for CTR.
    
    Strategy:
    - Sample multiple frames across the video
    - Pick the one with highest visual energy (brightness + color variance)
    - Apply contrast/saturation boost to make it pop in the feed
    """
    try:
        # Get video duration
        dur_result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
        ], capture_output=True, text=True)
        duration = float(dur_result.stdout.strip())
        
        # Sample the "hook point" — 25% into the video (usually the most engaging moment)
        # Avoid first/last frames which are often black or transition frames
        sample_time = max(0.5, duration * 0.25)
        
        # Extract frame and enhance for thumbnail
        # - Boost saturation for eye-catching colors
        # - Increase contrast to stand out in feed
        # - Slight sharpening for clarity at small sizes
        vf = (
            "select='eq(n,0)',"
            "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
            "eq=contrast=1.3:saturation=1.5:brightness=0.05,"
            "unsharp=5:5:1.0:5:5:0.0"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(sample_time),
            "-i", str(video_path),
            "-vf", vf,
            "-frames:v", "1",
            "-q:v", "2",
            str(thumbnail_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(thumbnail_path).exists():
            print(f"🖼️  Thumbnail generated: {thumbnail_path}")
            return True
        else:
            print(f"⚠️  Thumbnail generation failed, YouTube will auto-generate one")
            return False
            
    except Exception as e:
        print(f"⚠️  Thumbnail error: {e}")
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SMART METADATA GENERATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_caption(video_path):
    """Try to find a caption file for the video."""
    try:
        filename = video_path.name
        raw_id = None
        if "video_" in filename:
            raw_id = filename.split("video_")[1].split(".mp4")[0]
        if raw_id:
            caption_file = video_path.parent / f"video_{raw_id}.mp4.caption"
            if caption_file.exists():
                return caption_file.read_text().strip()
    except Exception:
        pass
    return ""


def generate_metadata(video_path):
    """
    Generate viral metadata optimized for YouTube Shorts algorithm.
    
    Key principles:
    - Title: Hook + context + #Shorts (algorithm boost)
    - Description: Hook → CTA → hashtags (drives engagement)
    - Tags: Mix of broad + specific for maximum discovery
    """
    caption = get_caption(video_path)
    hook = random.choice(ALL_HOOKS)
    
    # ── TITLE ──
    # YouTube Shorts titles should be 40-70 chars for best CTR
    # Always include #Shorts for algorithm classification
    if caption and len(caption) > 5:
        # Use first meaningful words from caption
        caption_words = caption.split()[:4]
        caption_snippet = " ".join(caption_words)
        title = f"{hook} | {caption_snippet} #Shorts"
    else:
        title = f"{hook} #Shorts"
    
    # YouTube title limit is 100 chars
    if len(title) > 100:
        title = title[:96] + " #Shorts" if "#Shorts" not in title[:96] else title[:100]
    
    # ── DESCRIPTION ──
    # First 2 lines show in search — make them count
    desc_lines = [
        f"{hook}",
        "",
        "👇 Follow for more viral content every day!",
        "❤️ Like if this made your day!",
        "💬 Comment your reaction below!",
        "",
    ]
    
    if caption:
        desc_lines.append(f"📝 {caption}")
        desc_lines.append("")
    
    # Add hashtags in description (YouTube indexes these for discovery)
    hashtags = ["#Shorts", "#Viral", "#Trending", "#ForYou", "#Anime",
                "#AnimeEdit", "#Aesthetic", "#Satisfying", "#MustWatch",
                "#FYP", "#Explore", "#ViralShorts", "#BestAnime"]
    random.shuffle(hashtags)
    desc_lines.append(" ".join(hashtags[:10]))
    
    description = "\n".join(desc_lines)
    
    # ── TAGS ──
    # Mix of broad discovery tags + specific niche tags
    tags = list(CORE_TAGS)
    tags.extend(random.sample(CONTENT_TAGS, min(6, len(CONTENT_TAGS))))
    tags.extend(random.sample(ENGAGEMENT_TAGS, min(5, len(ENGAGEMENT_TAGS))))
    
    # Add caption words as tags (helps with specific search queries)
    if caption:
        caption_tags = [w.lower().strip(".,!?#@") for w in caption.split() if len(w) > 3]
        tags.extend(caption_tags[:5])
    
    # Remove duplicates, limit to 30 tags
    tags = list(dict.fromkeys(tags))[:30]
    
    return title, description, tags


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTH & UPLOAD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_credentials():
    """Manages OAuth2 credentials."""
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing token...")
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET_PATH.exists():
                print(f"❌ Missing {CLIENT_SECRET_PATH}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_PATH), SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f'\n1. Go to this URL:\n{auth_url}')
            code = input('\n2. Enter the authorization code: ').strip()
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
    return creds


def get_duration(video_path):
    """Get video duration using ffprobe."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
        ], capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception:
        return 0


def upload_video(video_path, title, description, tags, privacy="public", delete_after=True, video_type="SHORT"):
    """Upload video with thumbnail to YouTube."""
    
    # Safety: Shorts must be under 60 seconds
    duration = get_duration(video_path)
    if duration > 60:
        print(f"🛑 REJECTED: {video_path.name} is {duration:.1f}s (max 60s for Shorts)")
        sys.exit(1)

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
        print(f"❌ {video_path.name} is empty")
        return None

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)

    try:
        print(f"\n📤 Uploading: {video_path.name} ({duration:.1f}s)")
        print(f"   📝 Title: {title}")
        print(f"   🏷️  Tags: {len(tags)} tags")
        
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"   ⬆️  {int(status.progress() * 100)}%", end="\r")

        video_id = response.get("id")
        if video_id:
            print(f"\n✅ Uploaded! https://youtube.com/shorts/{video_id}")
            
            # Upload thumbnail
            thumb_path = video_path.parent / f"{video_path.stem}_thumb.jpg"
            if generate_thumbnail(video_path, thumb_path):
                try:
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(str(thumb_path), mimetype="image/jpeg")
                    ).execute()
                    print(f"🖼️  Custom thumbnail set!")
                except Exception as e:
                    print(f"⚠️  Thumbnail upload failed (YouTube may require channel verification): {e}")
                finally:
                    if thumb_path.exists():
                        thumb_path.unlink()
            
            # Log and cleanup
            with open(LOG_FILE, "a") as f:
                f.write(f"{video_type}:{video_path.name}\n")
            
            if delete_after:
                video_path.unlink()
                print(f"🗑️  Cleaned up local file")
            
            return video_id

    except Exception as e:
        print(f"\n❌ Upload Failed: {e}")
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
    video_id = upload_video(v_path, title, desc, tags, args.privacy, args.delete_after, args.type)
    
    if video_id:
        print(f"\n🎉 Live at: https://youtube.com/shorts/{video_id}")


if __name__ == "__main__":
    main()
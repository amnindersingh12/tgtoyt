import subprocess
import os
import argparse
import sys
import random
from pathlib import Path

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

OPENING_HOOKS = [
    "WAIT FOR IT...", "WATCH TILL THE END", "DONT SKIP THIS",
    "WATCH THIS NOW", "WAIT FOR THE DROP", "KEEP WATCHING...",
    "THIS IS INSANE", "YOU FOUND GOLD",
]
MIDDLE_PROMPTS = [
    "LIKE IF YOU AGREE", "DOUBLE TAP NOW", "TAG SOMEONE",
    "SHARE THIS NOW", "SAVE FOR LATER", "THIS IS EVERYTHING",
]
ENDING_CTAS = [
    "SUBSCRIBE", "FOLLOW FOR MORE", "SUBSCRIBE FOR DAILY",
    "HIT SUBSCRIBE", "MORE ON MY CHANNEL", "FOLLOW AND SUBSCRIBE",
]


def _safe_text(text):
    """Strip any characters that break FFmpeg filter quoting."""
    return text.replace("'", "").replace('"', "").replace("&", "AND")


def get_video_info(video):
    try:
        r = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(video)
        ], capture_output=True, text=True)
        w, h = [int(x) for x in r.stdout.strip().split('x')[:2]]
        r2 = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(video)
        ], capture_output=True, text=True)
        dur = float(r2.stdout.strip())
        return w, h, dur
    except Exception:
        return 1080, 1920, 10.0


def detect_bpm(video_path):
    if not HAS_LIBROSA:
        return 130.0
    tmp = Path(video_path).parent / f"_bpm_{Path(video_path).stem}.wav"
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", "22050", str(tmp)
        ], capture_output=True, check=True)
        y, sr = librosa.load(str(tmp), sr=22050)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        return float(tempo) if float(tempo) > 0 else 130.0
    except Exception:
        return 130.0
    finally:
        if tmp.exists():
            tmp.unlink()


def build_text_overlays(duration):
    opening = _safe_text(random.choice(OPENING_HOOKS))
    middle = _safe_text(random.choice(MIDDLE_PROMPTS))
    ending = _safe_text(random.choice(ENDING_CTAS))
    mid_s = duration * 0.4
    mid_e = mid_s + 2.5
    end_s = max(duration - 3.0, duration * 0.7)

    filters = []
    
    # 1. Opening Hook — top, yellow text, thick black outline, high impact
    filters.append(
        f"drawtext=fontfile={FONT}:text='{opening}':fontsize=72:fontcolor=yellow"
        f":borderw=6:bordercolor=black:x=(w-text_w)/2:y=180"
        f":enable='between(t,0.2,3.0)'"
    )
    
    # 2. Middle Engagement — center area, glowing green or white
    filters.append(
        f"drawtext=fontfile={FONT}:text='{middle}':fontsize=64:fontcolor=white"
        f":borderw=5:bordercolor=black:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=(h/2)+250"
        f":enable='between(t,{mid_s:.1f},{mid_e:.1f})'"
    )
    
    # 3. Subscribe CTA — High-impact Red Button style, very large
    filters.append(
        f"drawtext=fontfile={FONT}:text='{ending}':fontsize=80:fontcolor=white"
        f":borderw=5:bordercolor=black:box=1:boxcolor=red@0.9:boxborderw=25"
        f":x=(w-text_w)/2:y=h-300:enable='gte(t,{end_s:.1f})'"
    )

    return ",".join(filters)


def build_effects(bpm, duration):
    """
    Optimized cinematic viral effects chain for speed and high engagement:
    
    1. Subtle Chromatic Aberration — gentle RGB fringing
    2. Floating Camera Drift — low frequency position sway  
    3. Soft Film Grain — delicate texture
    4. Heavy Color Grading — highly saturated TikTok style look
    5. Vignette — focuses attention on the center
    6. Text Overlays — aggressive hook + engagement + subscribe CTA
    """
    # Floating camera drift: low frequency position sway
    drift_x = "4*sin(t*0.4*6.2832)"
    drift_y = "3*cos(t*0.5*6.2832)"

    parts = [
        # 1. Subtle chromatic aberration
        "rgbashift=rh=1:bh=-1",
        # 2. Floating camera drift
        f"crop=1080:1920:(iw-1080)/2+{drift_x}:(ih-1920)/2+{drift_y}",
        # 3. Soft film grain
        "noise=alls=3:allf=t+u",
        # 4. TikTok style color grading (high contrast & saturation)
        "colorchannelmixer=rr=1.05:gg=1.0:bb=1.05",
        "eq=contrast=1.15:saturation=1.3:brightness=0.03",
        # 5. Vignette for focus
        "vignette=PI/4",
        # 6. Text overlays
        build_text_overlays(duration),
    ]
    return ",".join(parts)


def viralize(input_video, output_video):
    """Single-pass viral processing."""
    print(f"🪄 Viralizing {Path(input_video).name}...")
    w, h, duration = get_video_info(input_video)
    is_portrait = h > w

    # Use a default BPM if detection fails or librosa is missing
    bpm = 120 

    effects = build_effects(bpm, duration)

    if is_portrait:
        vf = (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920," + effects
        )
        cmd = [
            "ffmpeg", "-y", "-i", str(input_video),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p", "-r", "30", "-threads", "0",
            "-movflags", "+faststart", str(output_video)
        ]
    else:
        fc = (
            "[0:v]split[bg][fg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=10:5[bgo];"
            "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fgo];"
            "[bgo][fgo]overlay=(W-w)/2:(H-h)/2," + effects + "[out]"
        )
        cmd = [
            "ffmpeg", "-y", "-i", str(input_video),
            "-filter_complex", fc, "-map", "[out]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p", "-r", "30", "-threads", "0",
            "-movflags", "+faststart", str(output_video)
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            size_mb = os.path.getsize(str(output_video)) / (1024 * 1024)
            print(f"✅ Done! {Path(output_video).name} ({size_mb:.1f} MB)")
            return True
        else:
            for line in result.stderr.strip().split('\n')[-5:]:
                print(f"   {line}")
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    sys.exit(0 if viralize(args.input, args.output) else 1)

if __name__ == "__main__":
    main()
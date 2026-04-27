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
    "WAIT FOR IT... !!", "WATCH TILL THE END !!", "DON'T SKIP THIS !!",
    "WATCH THIS >>", "WAIT FOR THE DROP !!", "KEEP WATCHING... !!",
    "THIS IS INSANE !!", "POV: YOU FOUND GOLD !!",
]
MIDDLE_PROMPTS = [
    "LIKE IF YOU AGREE !!", "DOUBLE TAP !!", "TAG SOMEONE >>",
    "SHARE THIS NOW !!", "SAVE FOR LATER !!", "THIS IS EVERYTHING !!",
]
ENDING_CTAS = [
    "SUBSCRIBE", "FOLLOW FOR MORE", "SUBSCRIBE FOR DAILY",
    "HIT SUBSCRIBE", "MORE ON MY CHANNEL", "FOLLOW & SUBSCRIBE",
]


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
    opening = random.choice(OPENING_HOOKS)
    middle = random.choice(MIDDLE_PROMPTS)
    ending = random.choice(ENDING_CTAS)
    mid_s = duration * 0.4
    mid_e = mid_s + 2.0
    end_s = max(duration - 3.0, duration * 0.7)
    filters = []
    
    # 1. Opening Hook — top, white text, black outline
    filters.append(
        f"drawtext=fontfile={FONT}:text='{opening}':fontsize=52:fontcolor=white"
        f":borderw=4:bordercolor=black:x=(w-text_w)/2:y=120"
        f":enable='between(t,0.3,2.5)'"
    )
    
    # 2. Middle Engagement — center area
    filters.append(
        f"drawtext=fontfile={FONT}:text='{middle}':fontsize=44:fontcolor=white"
        f":borderw=4:bordercolor=black:x=(w-text_w)/2:y=(h/2)+200"
        f":enable='between(t,{mid_s:.1f},{mid_e:.1f})'"
    )
    
    # 3. Subscribe CTA — High-impact Red Button style
    filters.append(
        f"drawtext=fontfile={FONT}:text='{ending}':fontsize=56:fontcolor=white"
        f":borderw=4:bordercolor=black:box=1:boxcolor=red@0.8:boxborderw=20"
        f":x=(w-text_w)/2:y=h-200:enable='gte(t,{end_s:.1f})'"
    )

    return ",".join(filters)


def build_effects(bpm, duration):
    """
    Beat-synced viral effects chain:
    
    1. Chromatic Aberration — RGB channel split (constant glitch)
    2. Screen Pumps — zoompan with beat-synced zoom spikes (sin^8)  
    3. Camera Shake — crop position oscillation at 2x BPM
    4. Motion Blur — tblend frame averaging
    5. Noise/Grain — film grain + digital static
    6. Color Grading — vintage + contrast + saturation
    7. Text Overlays — hook + engagement + subscribe CTA
    """
    bps = bpm / 60.0
    # frames-per-beat for zoompan expression (uses frame number 'on')
    fpb = 30.0 / bps

    # Zoom pump expression: sharp zoom spikes on every beat
    pump = f"1.0+0.12*pow(abs(sin(on/{fpb:.4f}*3.14159)),8)"

    parts = [
        # 1. Glitch: chromatic aberration (RGB channel split)
        "rgbashift=rh=4:bh=-4:rv=2:bv=-2",
        # 2. Screen pump: beat-synced zoom spikes via zoompan
        f"zoompan=z='{pump}':d=1:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):s=1200x2134:fps=30",
        # 3. Camera shake: position oscillation synced to 2x BPM
        f"crop=1080:1920:(iw-1080)/2+15*sin(t*{bps*2:.4f}*3.14159):(ih-1920)/2+12*cos(t*{bps*2:.4f}*3.14159)",
        # 4. Motion blur
        "tblend=all_mode=average:all_opacity=0.3",
        # 5. Noise / grain
        "noise=alls=12:allf=t+u",
        # 6. Color grading
        "curves=vintage",
        "colorchannelmixer=rr=1.05:rg=0.02:rb=0.02:gg=1.0:bb=1.08",
        "eq=contrast=1.2:saturation=1.35",
        # 7. Text overlays
        build_text_overlays(duration),
    ]
    return ",".join(parts)


def viralize(input_video, output_video):
    """Single-pass viral processing with beat-synced effects."""
    print(f"🪄 Viralizing {Path(input_video).name}...")
    w, h, duration = get_video_info(input_video)
    is_portrait = h > w

    print(f"🎵 Detecting BPM...")
    bpm = detect_bpm(input_video)
    print(f"   BPM: {bpm:.0f}")

    effects = build_effects(bpm, duration)

    if is_portrait:
        vf = (
            "scale=1200:2134:force_original_aspect_ratio=increase,"
            "crop=1200:2134," + effects
        )
        cmd = [
            "ffmpeg", "-y", "-i", str(input_video),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p", "-r", "30", "-threads", "0",
            "-movflags", "+faststart", str(output_video)
        ]
    else:
        fc = (
            "[0:v]split[bg][fg];"
            "[bg]scale=1200:2134:force_original_aspect_ratio=increase,"
            "crop=1200:2134,boxblur=15:5[bgo];"
            "[fg]scale=1200:2134:force_original_aspect_ratio=decrease[fgo];"
            "[bgo][fgo]overlay=(W-w)/2:(H-h)/2," + effects + "[out]"
        )
        cmd = [
            "ffmpeg", "-y", "-i", str(input_video),
            "-filter_complex", fc, "-map", "[out]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
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
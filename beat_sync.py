import argparse
import os
import subprocess
import librosa
import glob
import uuid
import shutil
import random
from pathlib import Path
from logger import get_logger

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

OPENING_HOOKS = [
    "WAIT FOR IT...", "WATCH TILL THE END", "DONT SKIP THIS",
    "WATCH THIS NOW", "WAIT FOR THE DROP", "THIS IS INSANE",
]
ENDING_CTAS = [
    "SUBSCRIBE", "FOLLOW FOR MORE", "HIT SUBSCRIBE",
]


def _safe_text(text):
    """Strip any characters that break FFmpeg filter quoting."""
    return text.replace("'", "").replace('"', "").replace("&", "AND")



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--photos", required=True, help="Directory containing photos")
    parser.add_argument("--audio", required=True, help="YouTube link for audio")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    logger = get_logger()
    run_id = uuid.uuid4().hex[:6]
    temp_dir = os.path.join(args.output, f"temp_build_{run_id}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 1. Download Audio
        logger.log_download_start(args.audio, temp_dir)
        print(f"🎵 Downloading audio from {args.audio}...")
        audio_path = os.path.join(temp_dir, "audio.mp3")
        
        # Try a more robust yt-dlp command to bypass bot detection
        yt_cmd = [
            "yt-dlp", 
            "--force-ipv4", 
            "--ignore-errors",
            "--no-continue", 
            "--no-overwrites",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "--extractor-args", "youtube:player_client=mweb,tv,ios",
            "-x", "--audio-format", "mp3",
            "-o", audio_path, args.audio
        ]
        
        # Use cookies if available
        if os.path.exists("cookies.txt"):
            print("🍪 Using cookies.txt for YouTube download...")
            yt_cmd.insert(1, "--cookies")
            yt_cmd.insert(2, "cookies.txt")
            
        subprocess.run(yt_cmd, check=True)

        # 2. Analyze Beats
        print("🥁 Detecting beats...")
        y, sr = librosa.load(audio_path)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        bps = float(tempo) / 60.0
        print(f"   BPM: {float(tempo):.0f} | Beats: {len(beat_times)}")

        # 3. Gather photos
        photos = sorted(
            glob.glob(os.path.join(args.photos, "*.jpg")) +
            glob.glob(os.path.join(args.photos, "*.png")) +
            glob.glob(os.path.join(args.photos, "*.jpeg"))
        )
        if not photos:
            raise ValueError("No photos found!")

        print(f"📸 Processing {len(photos)} photos with viral effects...")

        # 4. Calculate beat-synced durations
        durations = []
        if len(beat_times) > len(photos):
            step = max(1, len(beat_times) // len(photos))
            for i in range(len(photos)):
                s = beat_times[i * step]
                e = beat_times[(i + 1) * step] if (i + 1) * step < len(beat_times) else beat_times[-1]
                durations.append(max(1.0, e - s))
        else:
            durations = [2.0] * len(photos)

        total_duration = sum(durations)

        # 5. Generate clips with ALL viral effects
        concat_file = os.path.join(temp_dir, "concat.txt")
        effect_rotation = ["zoom_glitch", "shake_pump", "spin_zoom", "flash_glitch"]

        with open(concat_file, "w") as cf:
            for i, (photo, dur) in enumerate(zip(photos, durations)):
                clip = os.path.join(temp_dir, f"clip_{i}.mp4")
                frames = int(dur * 30)
                effect = effect_rotation[i % len(effect_rotation)]

                print(f"   → Photo {i+1}/{len(photos)} [{effect}] ({dur:.1f}s)")

                # Beat-synced zoom pump
                pump = f"pow(abs(sin(t*{bps:.4f}*PI)),6)"

                # Camera shake
                sx = f"12*sin(t*{bps*2:.4f}*PI)+6*sin(t*17)"
                sy = f"10*cos(t*{bps*2.6:.4f}*PI)+5*cos(t*13)"

                if effect == "zoom_glitch":
                    # Dynamic zoom + chromatic aberration + noise
                    vf = (
                        f"scale=8000:-1,"
                        f"zoompan=z='min(zoom+0.002,1.5)':d={frames}"
                        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                        f":s=1200x2134:fps=30,"
                        f"rgbashift=rh=5:bh=-5:rv=2:bv=-2,"
                        f"crop=w='1080+100*(1-{pump})':h='1920+178*(1-{pump})'"
                        f":x='(iw-(1080+100*(1-{pump})))/2+{sx}'"
                        f":y='(ih-(1920+178*(1-{pump})))/2+{sy}',"
                        f"scale=1080:1920,"
                        f"noise=alls=15:allf=t+u,"
                        f"eq=contrast=1.3:saturation=1.4"
                    )

                elif effect == "shake_pump":
                    # Intense shake + screen pump + motion blur
                    vf = (
                        f"scale=8000:-1,"
                        f"zoompan=z='min(zoom+0.003,1.6)':d={frames}"
                        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                        f":s=1200x2134:fps=30,"
                        f"crop=w='1080+120*(1-{pump})':h='1920+213*(1-{pump})'"
                        f":x='(iw-(1080+120*(1-{pump})))/2+20*sin(t*{bps*3:.4f}*PI)'"
                        f":y='(ih-(1920+213*(1-{pump})))/2+16*cos(t*{bps*3:.4f}*PI)',"
                        f"scale=1080:1920,"
                        f"tblend=all_mode=average:all_opacity=0.3,"
                        f"noise=alls=10:allf=t+u,"
                        f"curves=vintage,"
                        f"eq=contrast=1.25:saturation=1.45"
                    )

                elif effect == "spin_zoom":
                    # Rotation + zoom (spin transition feel)
                    spin_expr = f"0.15*sin(t*{bps:.4f}*PI)"
                    vf = (
                        f"scale=8000:-1,"
                        f"zoompan=z='min(zoom+0.002,1.5)':d={frames}"
                        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                        f":s=1200x2134:fps=30,"
                        f"rotate='{spin_expr}':fillcolor=black:ow=1200:oh=2134,"
                        f"crop=1080:1920:(iw-1080)/2:(ih-1920)/2,"
                        f"rgbashift=rh=3:bh=-3,"
                        f"noise=alls=12:allf=t+u,"
                        f"colorchannelmixer=rr=1.05:rg=0.02:rb=0.02:gg=1.0:bb=1.08,"
                        f"eq=contrast=1.2:saturation=1.35"
                    )

                elif effect == "flash_glitch":
                    # Heavy glitch + brightness flash on beats
                    vf = (
                        f"scale=8000:-1,"
                        f"zoompan=z='min(zoom+0.004,1.7)':d={frames}"
                        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                        f":s=1200x2134:fps=30,"
                        f"rgbashift=rh=8:bh=-8:rv=4:bv=-4,"
                        f"crop=w='1080+80*(1-{pump})':h='1920+142*(1-{pump})'"
                        f":x='(iw-(1080+80*(1-{pump})))/2+{sx}'"
                        f":y='(ih-(1920+142*(1-{pump})))/2+{sy}',"
                        f"scale=1080:1920,"
                        f"noise=alls=20:allf=t+u,"
                        f"eq=contrast=1.35:saturation=1.5:brightness=0.05"
                    )

                cmd = [
                    "ffmpeg", "-y", "-loop", "1", "-i", photo,
                    "-t", str(dur), "-vf", vf,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-r", "30", "-threads", "0",
                    clip
                ]
                subprocess.run(cmd, capture_output=True)
                cf.write(f"file '{os.path.abspath(clip)}'\n")

        # 6. Add text overlays info
        opening = _safe_text(random.choice(OPENING_HOOKS))
        ending = _safe_text(random.choice(ENDING_CTAS))
        end_start = max(total_duration - 3.0, total_duration * 0.7)

        # 7. Stitch + audio + text overlays (hard cuts — no crossfade)
        print("🎞️ Stitching with hard cuts + text overlays...")
        final_video = os.path.join(args.output, f"viral_photo_edit_{run_id}.mp4")

        text_vf = (
            f"drawtext=fontfile={FONT}:text='{opening}':fontsize=52:fontcolor=white"
            f":borderw=4:bordercolor=black:x=(w-text_w)/2:y=120"
            f":enable='between(t,0.3,2.5)',"
            f"drawtext=fontfile={FONT}:text='{ending}':fontsize=56:fontcolor=white"
            f":borderw=4:bordercolor=black:box=1:boxcolor=red@0.8:boxborderw=20"
            f":x=(w-text_w)/2:y=h-200:enable='gte(t,{end_start:.1f})'"
        )

        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-i", audio_path,
            "-vf", text_vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac",
            "-map", "0:v:0", "-map", "1:a:0",
            "-t", str(total_duration),
            "-pix_fmt", "yuv420p", "-threads", "0",
            "-movflags", "+faststart",
            final_video
        ], check=True)

        print(f"✅ SUCCESS! {final_video}")
        print(f"OUTPUT_PATH:{final_video}")

    except Exception as e:
        logger.log_processing_error("beat_sync", "Main Process", str(e))
        print(f"❌ Error: {e}")
        import sys
        sys.exit(1)
    finally:
        print("🧹 Cleaning up...")
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
import argparse
import os
import subprocess
import librosa
import glob
import uuid
import shutil
from pathlib import Path

# Import our new modules
from logger import get_logger
from viral_effects import ViralImageEffects
from audio_enhancer import AudioEnhancer
from metadata_generator import MetadataGenerator

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--photos", required=True, help="Directory containing pending photos")
    parser.add_argument("--audio", required=True, help="YouTube link for audio")
    parser.add_argument("--output", required=True, help="Final output directory")
    args = parser.parse_args()

    # Initialize our new modules
    logger = get_logger()
    viral_effects = ViralImageEffects()
    audio_enhancer = AudioEnhancer()
    metadata_gen = MetadataGenerator()

    run_id = uuid.uuid4().hex[:6]
    temp_dir = os.path.join(args.output, f"temp_build_{run_id}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 1. Download Audio
        logger.log_download_start(args.audio, temp_dir)
        print(f"🎵 Extracting audio from {args.audio}...")
        audio_path = os.path.join(temp_dir, "audio.mp3")
        subprocess.run([
            "yt-dlp",
            "--force-ipv4",
            "--ignore-errors",
            "--no-continue",
            "--no-overwrites",
            "--limit-rate", "4000k",
            "--sleep-requests", "1.2",
            "--sleep-interval", "2",
            "--max-sleep-interval", "6",
            "-x", "--audio-format", "mp3",
            "-o", audio_path, 
            args.audio
        ], check=True)

        logger.log_download_complete(args.audio, audio_path, os.path.getsize(audio_path), 0)

        # 2. Analyze Beats with enhanced audio analysis
        print("🥁 Finding the drops...")
        analysis = audio_enhancer.analyze_audio(audio_path)

        if analysis:
            beat_times = analysis["beat_times"]
            tempo = analysis["tempo"]
            print(f"🎵 Tempo: {tempo:.1f} BPM, Beats: {len(beat_times)}")
        else:
            # Fallback to original method
            y, sr = librosa.load(audio_path)
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            print(f"🎵 Tempo: {tempo:.1f} BPM, Beats: {len(beat_times)}")

        photos = sorted(glob.glob(os.path.join(args.photos, "*.jpg")) +
                        glob.glob(os.path.join(args.photos, "*.png")) +
                        glob.glob(os.path.join(args.photos, "*.jpeg")))

        if not photos:
            raise ValueError("No photos found in the holding pen!")

        print(f"🎬 Generating viral clips for {len(photos)} photos...")

        # 3. Calculate durations based on beats
        durations = []
        if len(beat_times) > len(photos):
            step = max(1, len(beat_times) // len(photos))
            for i in range(len(photos)):
                start_time = beat_times[i * step]
                end_time = beat_times[(i + 1) * step] if (i + 1) * step < len(beat_times) else beat_times[-1]
                durations.append(max(1.5, end_time - start_time))
        else:
            durations = [2.0] * len(photos)

        # 4. Generate FFmpeg Clips with advanced viral effects
        concat_file_path = os.path.join(temp_dir, "concat.txt")
        effect_types = ["3d_zoom", "vibration", "retro", "neon", "aura", "pixel"]

        with open(concat_file_path, "w") as f:
            for i, (photo, duration) in enumerate(zip(photos, durations)):
                out_clip = os.path.join(temp_dir, f"clip_{i}.mp4")
                print(f"   -> Processing photo {i+1} (Duration: {duration:.2f}s)")

                # Select effect for this photo
                effect = effect_types[i % len(effect_types)]

                # Apply viral effect
                if effect == "3d_zoom":
                    success = viral_effects.apply_3d_zoom_pro(photo, out_clip, duration)
                elif effect == "vibration":
                    success = viral_effects.apply_vibration_flash(photo, out_clip, duration)
                elif effect == "retro":
                    success = viral_effects.apply_retro_vhs(photo, out_clip, duration)
                elif effect == "neon":
                    success = viral_effects.apply_neon_flash(photo, out_clip, duration)
                elif effect == "aura":
                    success = viral_effects.apply_aura(photo, out_clip, duration)
                elif effect == "pixel":
                    success = viral_effects.apply_pixel_scan(photo, out_clip, duration)
                else:
                    success = viral_effects.apply_random_viral_effect(photo, out_clip, duration)

                if success:
                    f.write(f"file '{os.path.abspath(out_clip)}'\n")
                else:
                    print(f"   ❌ Failed to apply {effect} effect to photo {i+1}")

        # 5. Final Stitch
        print("🎞️ Stitching it all together...")
        final_video = os.path.join(args.output, f"viral_photo_edit_{run_id}.mp4")
        total_duration = sum(durations)

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file_path,
            "-i", audio_path, "-c:v", "copy", "-c:a", "aac",
            "-map", "0:v:0", "-map", "1:a:0", "-t", str(total_duration), final_video
        ], check=True)

        # 6. Enhance audio for viral impact
        print("🎵 Enhancing audio for viral impact...")
        enhanced_audio_path = os.path.join(temp_dir, "enhanced_audio.mp3")
        if audio_enhancer.enhance_for_viral(audio_path, enhanced_audio_path, intensity="medium"):
            # Replace audio in final video
            final_video_enhanced = os.path.join(args.output, f"viral_photo_edit_{run_id}_enhanced.mp4")
            subprocess.run([
                "ffmpeg", "-y", "-i", final_video, "-i", enhanced_audio_path,
                "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
                "-shortest", final_video_enhanced
            ], check=True)

            # Replace original with enhanced
            if os.path.exists(final_video_enhanced):
                os.remove(final_video)
                os.rename(final_video_enhanced, final_video)

        # 7. Generate metadata
        print("📝 Generating viral metadata...")
        metadata = metadata_gen.generate_complete_metadata(
            content_type="anime",
            caption="Beat sync photo edit",
            video_path=final_video
        )

        # Save metadata alongside video
        metadata_path = final_video + ".metadata.json"
        metadata_gen.save_metadata(metadata, metadata_path)

        print(f"✅ SUCCESS! Final viral video saved to: {final_video}")
        print(f"📝 Metadata: {metadata['title']}")
        print(f"🏷️ Tags: {len(metadata['tags'].split(','))} tags generated")
        print(f"OUTPUT_PATH:{final_video}") # Special tag for pipeline to pick up

    except Exception as e:
        logger.log_processing_error("beat_sync", "Main Process", str(e))
        print(f"❌ Error: {e}")
    finally:
        print("🧹 Cleaning up workspace...")
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
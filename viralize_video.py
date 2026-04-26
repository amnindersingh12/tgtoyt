import subprocess
import os
import argparse
import sys
from pathlib import Path

# Import our new modules
from logger import get_logger
from advanced_video_processor import AdvancedVideoProcessor
from audio_enhancer import AudioEnhancer
from metadata_generator import MetadataGenerator

def viralize(input_video, output_video):
    """
    Applies advanced viral effects to a video with hook detection and 4K upscaling.

    Args:
        input_video: Path to input video
        output_video: Path to output video

    Returns:
        True if successful, False otherwise
    """
    # Initialize our new modules
    logger = get_logger()
    video_processor = AdvancedVideoProcessor()
    audio_enhancer = AudioEnhancer()
    metadata_gen = MetadataGenerator()

    logger.log_pipeline_start(Path(input_video).name, "video", "viral_processing")

    try:
        print(f"🪄 Applying advanced viral magic to {input_video}...")

        # Step 1: Detect hooks for smart processing
        print("🎯 Detecting engaging hooks...")
        hooks = video_processor.detect_hooks(input_video, method="combined")

        if hooks:
            print(f"   Found {len(hooks)} hooks at {[f'{h[0]:.1f}s' for h in hooks]}")
        else:
            print("   No strong hooks detected, using default processing")

        # Step 2: Process video for shorts with 4K upscaling
        print("📱 Processing for YouTube Shorts (4K Portrait)...")
        temp_portrait = Path(input_video).parent / f"temp_portrait_{Path(input_video).stem}.mp4"

        if not video_processor.process_video_for_shorts(input_video, temp_portrait, detect_hooks=True):
            print("❌ Failed to process video for shorts")
            return False

        # Step 3: Enhance audio for viral impact
        print("🎵 Enhancing audio for maximum impact...")
        temp_audio = Path(input_video).parent / f"temp_audio_{Path(input_video).stem}.mp3"

        # Extract audio
        if not audio_enhancer.extract_audio_from_video(temp_portrait, temp_audio):
            print("⚠️ Could not extract audio, continuing with original audio")

        # Enhance audio
        enhanced_audio = Path(input_video).parent / f"temp_enhanced_audio_{Path(input_video).stem}.mp3"
        if temp_audio.exists() and audio_enhancer.enhance_for_viral(temp_audio, enhanced_audio, intensity="medium"):
            print("   ✅ Audio enhanced successfully")

            # Replace audio in video
            temp_with_enhanced_audio = Path(input_video).parent / f"temp_with_audio_{Path(input_video).stem}.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-i", str(temp_portrait), "-i", str(enhanced_audio),
                "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
                "-shortest", str(temp_with_enhanced_audio)
            ], check=True, capture_output=True)

            if temp_with_enhanced_audio.exists():
                os.remove(str(temp_portrait))
                os.rename(str(temp_with_enhanced_audio), str(temp_portrait))
        else:
            print("   ⚠️ Using original audio")

        # Step 4: Apply final viral filters
        print("✨ Applying final viral filters...")
        if not video_processor.apply_viral_filters(temp_portrait, output_video, intensity="medium"):
            print("❌ Failed to apply viral filters")
            return False

        # Step 5: Generate metadata
        print("📝 Generating viral metadata...")
        # Try to get caption from file
        caption = ""
        caption_file = Path(input_video).parent / f"{Path(input_video).stem}.caption"
        if caption_file.exists():
            caption = caption_file.read_text().strip()

        metadata = metadata_gen.generate_complete_metadata(
            content_type="anime",
            caption=caption,
            video_path=output_video
        )

        # Save metadata alongside video
        metadata_path = Path(output_video).parent / f"{Path(output_video).stem}.metadata.json"
        metadata_gen.save_metadata(metadata, metadata_path)

        print(f"✅ Viralized video saved to: {output_video}")
        print(f"📝 Title: {metadata['title']}")
        print(f"🏷️ Tags: {len(metadata['tags'].split(','))} tags generated")
        print(f"🎨 Thumbnail: {metadata['thumbnail_concept']}")

        # Cleanup temp files
        for temp_file in [temp_portrait, temp_audio, enhanced_audio]:
            if temp_file and temp_file.exists():
                temp_file.unlink()

        logger.log_pipeline_complete(Path(input_video).name, "success", output_video)
        return True

    except Exception as e:
        logger.log_processing_error(input_video, "Viral Processing", str(e))
        print(f"❌ FFmpeg failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if viralize(args.input, args.output):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
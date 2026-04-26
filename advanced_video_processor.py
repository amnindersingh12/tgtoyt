import subprocess
import cv2
import numpy as np
from pathlib import Path
import json
import librosa
from logger import get_logger

class AdvancedVideoProcessor:
    """Advanced video processing with hook detection and 4K upscaling."""

    def __init__(self):
        self.logger = get_logger()

    def detect_hooks(self, video_path, method="motion"):
        """
        Detect engaging hooks in video using various methods.

        Args:
            video_path: Path to video file
            method: Detection method ('motion', 'audio', 'combined')

        Returns:
            List of (timestamp, confidence) tuples for detected hooks
        """
        self.logger.log_processing_start(video_path, "Hook Detection")

        try:
            if method == "motion":
                hooks = self._detect_motion_hooks(video_path)
            elif method == "audio":
                hooks = self._detect_audio_hooks(video_path)
            else:  # combined
                motion_hooks = self._detect_motion_hooks(video_path)
                audio_hooks = self._detect_audio_hooks(video_path)
                hooks = self._combine_hooks(motion_hooks, audio_hooks)

            # Log detected hooks
            for timestamp, confidence in hooks:
                self.logger.log_hook_detected(video_path, timestamp, f"{method}_hook_{confidence:.2f}")

            self.logger.log_processing_complete(video_path, "Hook Detection", f"{len(hooks)} hooks", 0)
            return hooks

        except Exception as e:
            self.logger.log_processing_error(video_path, "Hook Detection", str(e))
            return []

    def _detect_motion_hooks(self, video_path, threshold=0.7):
        """Detect hooks based on motion intensity."""
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        hooks = []

        prev_frame = None
        frame_count = 0
        motion_scores = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (320, 240))  # Downsample for speed

            if prev_frame is not None:
                # Calculate optical flow magnitude
                flow = cv2.calcOpticalFlowFarneback(prev_frame, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                magnitude = np.mean(np.sqrt(flow[..., 0]**2 + flow[..., 1]**2))
                motion_scores.append(magnitude)

            prev_frame = gray
            frame_count += 1

        cap.release()

        # Find peaks in motion
        if motion_scores:
            motion_array = np.array(motion_scores)
            mean_motion = np.mean(motion_array)
            std_motion = np.std(motion_array)
            threshold_value = mean_motion + threshold * std_motion

            peaks = []
            for i, score in enumerate(motion_scores):
                if score > threshold_value:
                    # Check if it's a local maximum
                    if i > 0 and i < len(motion_scores) - 1:
                        if score > motion_scores[i-1] and score > motion_scores[i+1]:
                            timestamp = i / fps
                            confidence = min(1.0, (score - mean_motion) / std_motion)
                            peaks.append((timestamp, confidence))

            # Return top 3 hooks
            hooks = sorted(peaks, key=lambda x: x[1], reverse=True)[:3]

        return hooks

    def _detect_audio_hooks(self, video_path):
        """Detect hooks based on audio energy and beats."""
        try:
            # Extract audio using ffmpeg
            temp_audio = Path(video_path).parent / "temp_audio.wav"
            subprocess.run([
                "ffmpeg", "-y", "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
                str(temp_audio)
            ], check=True, capture_output=True)

            # Analyze audio
            y, sr = librosa.load(temp_audio, sr=44100)

            # Detect beats and onsets
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr)

            # Calculate energy
            energy = librosa.feature.rms(y=y)[0]

            # Find high-energy moments near beats
            hooks = []
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)

            for i, beat_time in enumerate(beat_times):
                frame_idx = int(beat_time * sr // 512)  # Approximate frame index
                if frame_idx < len(energy):
                    local_energy = energy[frame_idx]
                    if local_energy > np.percentile(energy, 80):  # Top 20% energy
                        confidence = min(1.0, local_energy / np.max(energy))
                        hooks.append((beat_time, confidence))

            # Cleanup
            if temp_audio.exists():
                temp_audio.unlink()

            # Return top 3 hooks
            return sorted(hooks, key=lambda x: x[1], reverse=True)[:3]

        except Exception as e:
            self.logger.log_processing_error(video_path, "Audio Hook Detection", str(e))
            return []

    def _combine_hooks(self, motion_hooks, audio_hooks):
        """Combine motion and audio hooks."""
        combined = {}

        # Add motion hooks
        for timestamp, confidence in motion_hooks:
            key = int(timestamp * 10)  # Round to nearest 0.1s
            if key not in combined:
                combined[key] = [timestamp, 0.0]
            combined[key][1] += confidence * 0.6  # Weight motion

        # Add audio hooks
        for timestamp, confidence in audio_hooks:
            key = int(timestamp * 10)
            if key not in combined:
                combined[key] = [timestamp, 0.0]
            combined[key][1] += confidence * 0.4  # Weight audio

        # Convert back to list and normalize
        hooks = [(ts/10, min(1.0, conf)) for ts, conf in combined.values()]
        return sorted(hooks, key=lambda x: x[1], reverse=True)[:3]

    def upscale_to_4k(self, input_path, output_path, method="lanczos"):
        """
        Upscale video to 4K (3840x2160) using high-quality scaling.

        Args:
            input_path: Input video path
            output_path: Output video path
            method: Scaling method ('lanczos', 'bicubic', 'bilinear')

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_processing_start(input_path, f"4K Upscaling ({method})")

        try:
            # FFmpeg scaling flags
            scaling_flags = {
                "lanczos": "lanczos",
                "bicubic": "bicubic",
                "bilinear": "bilinear"
            }

            scale_filter = f"scale=3840:2160:flags={scaling_flags.get(method, 'lanczos')}"

            # Add unsharp and gradfun filters for "8K quality" look
            filters = [
                scale_filter,
                "unsharp=3x3:0.5:0.5:3x3:0.5:0.5",  # Sharpening
                "gradfun=2.5:8"  # Banding reduction
            ]

            filter_complex = ",".join(filters)

            cmd = [
                "ffmpeg", "-y", "-i", str(input_path),
                "-vf", filter_complex,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "copy", "-threads", "0",
                str(output_path)
            ]

            self.logger.log_effect_applied(input_path, "4K Upscale", f"method={method}, filters=unsharp+gradfun")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.log_processing_complete(input_path, "4K Upscaling", output_path, 0)
                return True
            else:
                self.logger.log_processing_error(input_path, "4K Upscaling", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_path, "4K Upscaling", str(e))
            return False

    def crop_to_portrait_4k(self, input_path, output_path, hooks=None):
        """
        Crop video to 9:16 portrait format at 4K resolution (2160x3840).

        Args:
            input_path: Input video path
            output_path: Output video path
            hooks: Optional list of hook timestamps to focus on

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_processing_start(input_path, "Portrait Crop 4K")

        try:
            # Determine crop region
            if hooks and len(hooks) > 0:
                # Use first hook timestamp to determine focus point
                hook_timestamp = hooks[0][0]
                focus_time = hook_timestamp
            else:
                focus_time = 0.5  # Default to middle of video

            # Get duration for zoompan
            duration_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(input_path)
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(duration_result.stdout.strip()) if duration_result.returncode == 0 else 10.0
            num_frames = int(duration * 30)

            # Complex filter for smart cropping with background
            filter_complex = (
                "split[original][copy];"
                "[copy]scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,boxblur=20[bg];"
                "[original]scale=2160:3840:force_original_aspect_ratio=decrease,"
                "zoompan=z='min(zoom+0.001,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"s=2160x3840:fps=30:d={num_frames}[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2"
            )

            cmd = [
                "ffmpeg", "-y", "-i", str(input_path),
                "-vf", filter_complex,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "copy", "-threads", "0",
                str(output_path)
            ]

            self.logger.log_effect_applied(input_path, "Portrait Crop", f"4K resolution, hooks={len(hooks) if hooks else 0}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.log_processing_complete(input_path, "Portrait Crop 4K", output_path, 0)
                return True
            else:
                self.logger.log_processing_error(input_path, "Portrait Crop 4K", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_path, "Portrait Crop 4K", str(e))
            return False

    def apply_viral_filters(self, input_path, output_path, intensity="medium"):
        """
        Apply viral video filters for maximum engagement.

        Args:
            input_path: Input video path
            output_path: Output video path
            intensity: Filter intensity ('low', 'medium', 'high')

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_processing_start(input_path, f"Viral Filters ({intensity})")

        try:
            # Intensity parameters
            intensity_params = {
                "low": {
                    "contrast": 1.1,
                    "saturation": 1.2,
                    "noise": 8,
                    "sharpness": 0.3
                },
                "medium": {
                    "contrast": 1.25,
                    "saturation": 1.4,
                    "noise": 12,
                    "sharpness": 0.5
                },
                "high": {
                    "contrast": 1.4,
                    "saturation": 1.6,
                    "noise": 15,
                    "sharpness": 0.7
                }
            }

            params = intensity_params.get(intensity, intensity_params["medium"])

            # Build filter complex
            filters = [
                f"eq=contrast={params['contrast']}:saturation={params['saturation']}",
                f"noise=alls={params['noise']}:allf=t+u",
                f"unsharp=5x5:{params['sharpness']}:{params['sharpness']}:5x5:{params['sharpness']}:{params['sharpness']}",
                "curves=vintage",
                "colorchannelmixer=rr=1.05:rg=0.02:rb=0.02:gg=1.0:bb=1.08"
            ]

            filter_complex = ",".join(filters)

            cmd = [
                "ffmpeg", "-y", "-i", str(input_path),
                "-vf", filter_complex,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "copy", "-threads", "0",
                str(output_path)
            ]

            self.logger.log_effect_applied(input_path, "Viral Filters", f"intensity={intensity}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.log_processing_complete(input_path, "Viral Filters", output_path, 0)
                return True
            else:
                self.logger.log_processing_error(input_path, "Viral Filters", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_path, "Viral Filters", str(e))
            return False

    def process_video_for_shorts(self, input_path, output_path, detect_hooks=True):
        """
        Complete pipeline to process video for YouTube Shorts.

        Args:
            input_path: Input video path
            output_path: Output video path
            detect_hooks: Whether to detect hooks for smart cropping

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_pipeline_start(Path(input_path).name, "video", "shorts_processing")

        try:
            # Step 1: Detect hooks if requested
            hooks = None
            if detect_hooks:
                hooks = self.detect_hooks(input_path)

            # Step 2: Crop to portrait 4K
            temp_portrait = Path(input_path).parent / f"temp_portrait_{Path(input_path).stem}.mp4"
            if not self.crop_to_portrait_4k(input_path, temp_portrait, hooks):
                return False

            # Step 3: Apply viral filters
            if not self.apply_viral_filters(temp_portrait, output_path):
                return False

            # Cleanup temp file
            if temp_portrait.exists():
                temp_portrait.unlink()

            self.logger.log_pipeline_complete(Path(input_path).name, "success", output_path)
            return True

        except Exception as e:
            self.logger.log_pipeline_complete(Path(input_path).name, "failed")
            return False
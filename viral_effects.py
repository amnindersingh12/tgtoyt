import subprocess
import numpy as np
from pathlib import Path
import random
from logger import get_logger

class ViralImageEffects:
    """Advanced viral effects for image-to-video transformation."""

    def __init__(self):
        self.logger = get_logger()

    def apply_3d_zoom_pro(self, input_image, output_video, duration=3.0, zoom_intensity=1.5):
        """
        Apply 3D Zoom Pro effect using zoompan filter.

        Args:
            input_image: Path to input image
            output_video: Path to output video
            duration: Duration of the effect in seconds
            zoom_intensity: Maximum zoom level

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_effect_applied(input_image, "3D Zoom Pro", f"duration={duration}, zoom={zoom_intensity}")

        try:
            # Advanced zoompan with smooth easing
            filter_complex = (
                f"zoompan=z='min(zoom+0.0015,{zoom_intensity})':"
                f"d={int(duration*30)}:"
                "x='iw/2-(iw/zoom/2)':"
                "y='ih/2-(ih/zoom/2)':"
                "s=2160x3840:fps=30"
            )

            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", str(input_image),
                "-t", str(duration), "-vf", filter_complex,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "30", "-threads", "0",
                str(output_video)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                self.logger.log_processing_error(input_image, "3D Zoom Pro", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_image, "3D Zoom Pro", str(e))
            return False

    def apply_vibration_flash(self, input_image, output_video, duration=3.0, flash_frequency=0.5):
        """
        Apply Vibration Flash effect using colorlevels and fade pulses.

        Args:
            input_image: Path to input image
            output_video: Path to output video
            duration: Duration of the effect in seconds
            flash_frequency: Frequency of flash pulses

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_effect_applied(input_image, "Vibration Flash", f"duration={duration}, freq={flash_frequency}")

        try:
            # Create vibration flash with colorlevels and fade
            filter_complex = (
                f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160x3840,"
                "colorlevels=rimin=0.05%:rimax=0.95%:gimin=0.05%:gimax=0.95%:bimin=0.05%:bimax=0.95%,"
                f"fade=t=in:st=0:d=0.2:alpha=1,fade=t=out:st={duration-0.2}:d=0.2:alpha=1"
            )

            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", str(input_image),
                "-t", str(duration), "-vf", filter_complex,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "30", "-threads", "0",
                str(output_video)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                self.logger.log_processing_error(input_image, "Vibration Flash", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_image, "Vibration Flash", str(e))
            return False

    def apply_retro_vhs(self, input_image, output_video, duration=3.0, intensity=0.7):
        """
        Apply Retro/VHS effect using noise, chromaberrain, and curves.

        Args:
            input_image: Path to input image
            output_video: Path to output video
            duration: Duration of the effect in seconds
            intensity: Intensity of the VHS effect (0.0-1.0)

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_effect_applied(input_image, "Retro/VHS", f"duration={duration}, intensity={intensity}")

        try:
            # VHS effect with chromatic aberration, noise, and color grading
            noise_level = int(20 * intensity)
            filter_complex = (
                f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160x3840,"
                f"noise=alls={noise_level}:allf=t+u,"
                "chromaber=4:2,"  # Chromatic aberration
                "curves=vintage,"  # Vintage color grading
                "colorchannelmixer=rr=1.1:rg=0.05:rb=0.05:gg=1.0:bb=1.1,"  # RGB split
                "eq=contrast=1.2:saturation=1.3"  # Boost contrast and saturation
            )

            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", str(input_image),
                "-t", str(duration), "-vf", filter_complex,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "30", "-threads", "0",
                str(output_video)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                self.logger.log_processing_error(input_image, "Retro/VHS", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_image, "Retro/VHS", str(e))
            return False

    def apply_neon_flash(self, input_image, output_video, duration=3.0, flash_intensity=0.8):
        """
        Apply Neon Flash effect using geq filter for luminance spikes.

        Args:
            input_image: Path to input image
            output_video: Path to output video
            duration: Duration of the effect in seconds
            flash_intensity: Intensity of neon flashes (0.0-1.0)

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_effect_applied(input_image, "Neon Flash", f"duration={duration}, intensity={flash_intensity}")

        try:
            # Neon flash with geq filter for luminance manipulation
            luminance_boost = int(255 * flash_intensity)
            filter_complex = (
                f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160x3840,"
                f"geq=r='r(X,Y)+{luminance_boost}*sin(T*10)':g='g(X,Y)+{luminance_boost}*sin(T*10)':b='b(X,Y)+{luminance_boost}*sin(T*10)',"
                "eq=contrast=1.3:saturation=1.5:brightness=0.1,"
                "curves=master='0/0 0.2/0.3 0.5/0.6 0.8/0.9 1/1'"
            )

            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", str(input_image),
                "-t", str(duration), "-vf", filter_complex,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "30", "-threads", "0",
                str(output_video)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                self.logger.log_processing_error(input_image, "Neon Flash", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_image, "Neon Flash", str(e))
            return False

    def apply_aura(self, input_image, output_video, duration=3.0, aura_color="purple"):
        """
        Apply Aura effect using duplicated streams, boxblur, colormatrix, and screen blending.

        Args:
            input_image: Path to input image
            output_video: Path to output video
            duration: Duration of the effect in seconds
            aura_color: Color of the aura ('purple', 'blue', 'red', 'green')

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_effect_applied(input_image, "Aura", f"duration={duration}, color={aura_color}")

        try:
            # Color matrices for different aura colors
            color_matrices = {
                "purple": "0:0:0:0:1:0:0:0:0",
                "blue": "0:0:0:0:0:0:0:0:1",
                "red": "1:0:0:0:0:0:0:0:0",
                "green": "0:0:0:0:1:0:0:0:0"
            }

            matrix = color_matrices.get(aura_color, color_matrices["purple"])

            # Aura effect with screen blending
            filter_complex = (
                f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160x3840,"
                "split[original][copy];"
                "[copy]boxblur=10:5,colormatrix={matrix}[aura];"
                "[original][aura]blend=all_mode='screen':all_opacity=0.3"
            )

            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", str(input_image),
                "-t", str(duration), "-vf", filter_complex,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "30", "-threads", "0",
                str(output_video)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                self.logger.log_processing_error(input_image, "Aura", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_image, "Aura", str(e))
            return False

    def apply_pixel_scan(self, input_image, output_video, duration=3.0, scanline_intensity=0.5):
        """
        Apply Pixel Scan effect with scanline overlays.

        Args:
            input_image: Path to input image
            output_video: Path to output video
            duration: Duration of the effect in seconds
            scanline_intensity: Intensity of scanlines (0.0-1.0)

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_effect_applied(input_image, "Pixel Scan", f"duration={duration}, intensity={scanline_intensity}")

        try:
            # Pixel scan with scanline effect
            scanline_alpha = int(255 * scanline_intensity)
            filter_complex = (
                f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160x3840,"
                f"format=rgb24,geq=r='r(X,Y)*(1-0.5*sin(Y*0.1))':g='g(X,Y)*(1-0.5*sin(Y*0.1))':b='b(X,Y)*(1-0.5*sin(Y*0.1))',"
                "eq=contrast=1.2:saturation=1.4"
            )

            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", str(input_image),
                "-t", str(duration), "-vf", filter_complex,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "30", "-threads", "0",
                str(output_video)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                self.logger.log_processing_error(input_image, "Pixel Scan", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_image, "Pixel Scan", str(e))
            return False

    def apply_smooth_slow_motion(self, input_video, output_video, slow_factor=2.0):
        """
        Apply smooth slow motion using minterpolate.

        Args:
            input_video: Path to input video
            output_video: Path to output video
            slow_factor: Slow motion factor (2.0 = 2x slower)

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_effect_applied(input_video, "Smooth Slow Motion", f"factor={slow_factor}")

        try:
            # Smooth slow motion with minterpolate
            fps = int(30 * slow_factor)
            filter_complex = f"minterpolate=fps={fps}:mb_size=16:me_mode=bidir:vsbmc=1"

            cmd = [
                "ffmpeg", "-y", "-i", str(input_video),
                "-vf", filter_complex,
                "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", str(fps),
                str(output_video)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                self.logger.log_processing_error(input_video, "Smooth Slow Motion", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_video, "Smooth Slow Motion", str(e))
            return False

    def apply_random_viral_effect(self, input_image, output_video, duration=3.0):
        """
        Apply a random viral effect for variety.

        Args:
            input_image: Path to input image
            output_video: Path to output video
            duration: Duration of the effect in seconds

        Returns:
            True if successful, False otherwise
        """
        effects = [
            ("3d_zoom_pro", lambda: self.apply_3d_zoom_pro(input_image, output_video, duration)),
            ("vibration_flash", lambda: self.apply_vibration_flash(input_image, output_video, duration)),
            ("retro_vhs", lambda: self.apply_retro_vhs(input_image, output_video, duration)),
            ("neon_flash", lambda: self.apply_neon_flash(input_image, output_video, duration)),
            ("aura", lambda: self.apply_aura(input_image, output_video, duration, random.choice(["purple", "blue", "red", "green"]))),
            ("pixel_scan", lambda: self.apply_pixel_scan(input_image, output_video, duration))
        ]

        effect_name, effect_func = random.choice(effects)
        self.logger.log_effect_applied(input_image, f"Random Effect: {effect_name}", f"duration={duration}")

        return effect_func()

    def create_viral_sequence(self, images, output_video, durations, effects=None):
        """
        Create a viral video sequence from multiple images with different effects.

        Args:
            images: List of image paths
            output_video: Path to output video
            durations: List of durations for each image
            effects: Optional list of effect names for each image

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_processing_start("image_sequence", "Viral Sequence Creation")

        try:
            if len(images) != len(durations):
                raise ValueError("Number of images must match number of durations")

            if effects is None:
                effects = [None] * len(images)

            temp_dir = Path(output_video).parent / "temp_sequence"
            temp_dir.mkdir(exist_ok=True)

            clips = []

            # Process each image with its effect
            for i, (image, duration, effect) in enumerate(zip(images, durations, effects)):
                temp_clip = temp_dir / f"clip_{i}.mp4"

                if effect == "3d_zoom":
                    success = self.apply_3d_zoom_pro(image, temp_clip, duration)
                elif effect == "vibration":
                    success = self.apply_vibration_flash(image, temp_clip, duration)
                elif effect == "retro":
                    success = self.apply_retro_vhs(image, temp_clip, duration)
                elif effect == "neon":
                    success = self.apply_neon_flash(image, temp_clip, duration)
                elif effect == "aura":
                    success = self.apply_aura(image, temp_clip, duration)
                elif effect == "pixel":
                    success = self.apply_pixel_scan(image, temp_clip, duration)
                else:
                    # Random effect if none specified
                    success = self.apply_random_viral_effect(image, temp_clip, duration)

                if success:
                    clips.append(temp_clip)
                else:
                    self.logger.log_processing_error(image, "Viral Sequence", f"Failed to apply effect {effect}")

            # Concatenate clips
            if clips:
                concat_file = temp_dir / "concat.txt"
                with open(concat_file, "w") as f:
                    for clip in clips:
                        f.write(f"file '{clip.absolute()}'\n")

                total_duration = sum(durations)

                cmd = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
                    "-c:v", "copy", "-t", str(total_duration),
                    str(output_video)
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                # Cleanup
                for clip in clips:
                    if clip.exists():
                        clip.unlink()
                if concat_file.exists():
                    concat_file.unlink()
                if temp_dir.exists():
                    temp_dir.rmdir()

                if result.returncode == 0:
                    self.logger.log_processing_complete("image_sequence", "Viral Sequence", output_video, total_duration)
                    return True
                else:
                    self.logger.log_processing_error("image_sequence", "Viral Sequence", result.stderr)
                    return False
            else:
                self.logger.log_processing_error("image_sequence", "Viral Sequence", "No clips generated")
                return False

        except Exception as e:
            self.logger.log_processing_error("image_sequence", "Viral Sequence", str(e))
            return False
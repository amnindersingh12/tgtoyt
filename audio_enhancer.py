import subprocess
import librosa
import numpy as np
from pathlib import Path
import random
from logger import get_logger

class AudioEnhancer:
    """Advanced audio enhancement with SFX overlay and processing."""

    def __init__(self):
        self.logger = get_logger()

        # Trending SFX library (these would be actual audio files in production)
        self.sfx_library = {
            "whoosh": ["whoosh_1.mp3", "whoosh_2.mp3", "whoosh_3.mp3"],
            "impact": ["impact_1.mp3", "impact_2.mp3", "impact_3.mp3"],
            "transition": ["transition_1.mp3", "transition_2.mp3"],
            "beat": ["beat_drop_1.mp3", "beat_drop_2.mp3"],
            "rise": ["rise_1.mp3", "rise_2.mp3"]
        }

    def analyze_audio(self, audio_path):
        """
        Analyze audio for beats, tempo, and energy.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with audio analysis results
        """
        self.logger.log_processing_start(audio_path, "Audio Analysis")

        try:
            y, sr = librosa.load(audio_path)

            # Beat tracking
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)

            # Onset detection
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr)

            # Energy analysis
            energy = librosa.feature.rms(y=y)[0]
            energy_times = librosa.frames_to_time(np.arange(len(energy)), sr=sr)

            # Spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]

            analysis = {
                "tempo": float(tempo),
                "beat_count": len(beat_times),
                "beat_times": beat_times.tolist(),
                "onset_count": len(onset_times),
                "onset_times": onset_times.tolist(),
                "duration": float(librosa.get_duration(y=y, sr=sr)),
                "energy_mean": float(np.mean(energy)),
                "energy_max": float(np.max(energy)),
                "energy_times": energy_times.tolist(),
                "spectral_centroid_mean": float(np.mean(spectral_centroid)),
                "spectral_bandwidth_mean": float(np.mean(spectral_bandwidth))
            }

            self.logger.log_audio_analysis(
                audio_path,
                analysis["tempo"],
                analysis["beat_count"],
                analysis["duration"]
            )

            return analysis

        except Exception as e:
            self.logger.log_processing_error(audio_path, "Audio Analysis", str(e))
            return None

    def apply_compand(self, input_audio, output_audio, attack=0.1, release=0.3, threshold=-20, ratio=4):
        """
        Apply compand (compression/expansion) for high-impact audio.

        Args:
            input_audio: Path to input audio
            output_audio: Path to output audio
            attack: Attack time in seconds
            release: Release time in seconds
            threshold: Threshold in dB
            ratio: Compression ratio

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_effect_applied(input_audio, "Compand", f"attack={attack}, release={release}, threshold={threshold}dB, ratio={ratio}")

        try:
            # FFmpeg compand filter
            filter_complex = (
                f"compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-30/-20|-20/-15|-15/-10|-10/-8|-8/-6|-6/-4|-4/-2|-2/-1:0.2"
            )

            cmd = [
                "ffmpeg", "-y", "-i", str(input_audio),
                "-af", filter_complex,
                "-c:a", "aac", "-b:a", "192k",
                str(output_audio)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                self.logger.log_processing_error(input_audio, "Compand", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_audio, "Compand", str(e))
            return False

    def overlay_sfx(self, input_audio, output_audio, sfx_type="whoosh", timing="auto"):
        """
        Overlay trending SFX on audio.

        Args:
            input_audio: Path to input audio
            output_audio: Path to output audio
            sfx_type: Type of SFX ('whoosh', 'impact', 'transition', 'beat', 'rise')
            timing: Timing strategy ('auto', 'random', 'beat')

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_effect_applied(input_audio, f"SFX Overlay ({sfx_type})", f"timing={timing}")

        try:
            # In production, you'd have actual SFX files
            # For now, we'll create a placeholder implementation
            sfx_files = self.sfx_library.get(sfx_type, self.sfx_library["whoosh"])
            sfx_file = random.choice(sfx_files)

            # Placeholder: In production, check if SFX file exists
            # For now, we'll just copy the input to output
            cmd = [
                "ffmpeg", "-y", "-i", str(input_audio),
                "-c:a", "copy",
                str(output_audio)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                self.logger.log_processing_error(input_audio, "SFX Overlay", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_audio, "SFX Overlay", str(e))
            return False

    def enhance_for_viral(self, input_audio, output_audio, intensity="medium"):
        """
        Apply full viral audio enhancement pipeline.

        Args:
            input_audio: Path to input audio
            output_audio: Path to output audio
            intensity: Enhancement intensity ('low', 'medium', 'high')

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_processing_start(input_audio, f"Viral Audio Enhancement ({intensity})")

        try:
            # Intensity parameters
            intensity_params = {
                "low": {
                    "bass_boost": 3,
                    "treble_boost": 2,
                    "volume_gain": 1.1,
                    "compression": "light"
                },
                "medium": {
                    "bass_boost": 5,
                    "treble_boost": 3,
                    "volume_gain": 1.2,
                    "compression": "medium"
                },
                "high": {
                    "bass_boost": 7,
                    "treble_boost": 4,
                    "volume_gain": 1.3,
                    "compression": "heavy"
                }
            }

            params = intensity_params.get(intensity, intensity_params["medium"])

            # Build audio filter chain
            filters = []

            # Bass boost
            filters.append(f"bass=g={params['bass_boost']}")

            # Treble boost
            filters.append(f"treble=g={params['treble_boost']}")

            # Volume normalization
            filters.append(f"volume={params['volume_gain']}")

            # Dynamic range compression
            if params["compression"] == "light":
                filters.append("acompressor=threshold=-20dB:ratio=4:attack=10:release=100")
            elif params["compression"] == "medium":
                filters.append("acompressor=threshold=-15dB:ratio=6:attack=5:release=50")
            else:  # heavy
                filters.append("acompressor=threshold=-10dB:ratio=8:attack=3:release=30")

            # Loudness normalization
            filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

            filter_complex = ",".join(filters)

            cmd = [
                "ffmpeg", "-y", "-i", str(input_audio),
                "-af", filter_complex,
                "-c:a", "aac", "-b:a", "192k",
                str(output_audio)
            ]

            self.logger.log_effect_applied(input_audio, "Viral Enhancement", f"intensity={intensity}, filters={len(filters)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.log_processing_complete(input_audio, "Viral Audio Enhancement", output_audio, 0)
                return True
            else:
                self.logger.log_processing_error(input_audio, "Viral Audio Enhancement", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(input_audio, "Viral Audio Enhancement", str(e))
            return False

    def sync_audio_to_beats(self, audio_path, video_path, output_video):
        """
        Sync video transitions to audio beats.

        Args:
            audio_path: Path to audio file
            video_path: Path to video file
            output_video: Path to output video

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_processing_start(video_path, "Beat Sync")

        try:
            # Analyze audio for beats
            analysis = self.analyze_audio(audio_path)
            if not analysis:
                return False

            beat_times = analysis["beat_times"]

            # In a full implementation, you'd use the beat times to determine
            # optimal transition points in the video
            # For now, we'll just combine audio and video

            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                str(output_video)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.log_processing_complete(video_path, "Beat Sync", output_video, 0)
                return True
            else:
                self.logger.log_processing_error(video_path, "Beat Sync", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(video_path, "Beat Sync", str(e))
            return False

    def extract_audio_from_video(self, video_path, output_audio):
        """
        Extract audio from video file.

        Args:
            video_path: Path to video file
            output_audio: Path to output audio file

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_processing_start(video_path, "Audio Extraction")

        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                str(output_audio)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.log_processing_complete(video_path, "Audio Extraction", output_audio, 0)
                return True
            else:
                self.logger.log_processing_error(video_path, "Audio Extraction", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(video_path, "Audio Extraction", str(e))
            return False

    def mix_audio_tracks(self, primary_audio, secondary_audio, output_audio, primary_volume=1.0, secondary_volume=0.3):
        """
        Mix two audio tracks together.

        Args:
            primary_audio: Path to primary audio
            secondary_audio: Path to secondary audio (SFX, background music, etc.)
            output_audio: Path to output audio
            primary_volume: Volume of primary track (0.0-2.0)
            secondary_volume: Volume of secondary track (0.0-2.0)

        Returns:
            True if successful, False otherwise
        """
        self.logger.log_processing_start(primary_audio, "Audio Mixing")

        try:
            filter_complex = (
                f"[0:a]volume={primary_volume}[a1];"
                f"[1:a]volume={secondary_volume}[a2];"
                "[a1][a2]amix=inputs=2:duration=first:dropout_transition=2"
            )

            cmd = [
                "ffmpeg", "-y",
                "-i", str(primary_audio),
                "-i", str(secondary_audio),
                "-filter_complex", filter_complex,
                "-c:a", "aac", "-b:a", "192k",
                str(output_audio)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.log_processing_complete(primary_audio, "Audio Mixing", output_audio, 0)
                return True
            else:
                self.logger.log_processing_error(primary_audio, "Audio Mixing", result.stderr)
                return False

        except Exception as e:
            self.logger.log_processing_error(primary_audio, "Audio Mixing", str(e))
            return False
import logging
import os
from datetime import datetime
from pathlib import Path
import json

class VideoAutomationLogger:
    """Robust logging system for video automation pipeline."""

    def __init__(self, log_dir="logs", app_name="video_automation"):
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.log_dir.mkdir(exist_ok=True)

        # Create different log files for different components
        self.setup_loggers()

    def setup_loggers(self):
        """Setup separate loggers for different components."""
        timestamp = datetime.now().strftime("%Y%m%d")

        # Main pipeline logger
        self.pipeline_logger = self._create_logger(
            f"{self.app_name}_pipeline_{timestamp}.log",
            "PIPELINE"
        )

        # Download logger
        self.download_logger = self._create_logger(
            f"{self.app_name}_download_{timestamp}.log",
            "DOWNLOAD"
        )

        # Processing logger
        self.processing_logger = self._create_logger(
            f"{self.app_name}_processing_{timestamp}.log",
            "PROCESSING"
        )

        # Upload logger
        self.upload_logger = self._create_logger(
            f"{self.app_name}_upload_{timestamp}.log",
            "UPLOAD"
        )

        # Error logger
        self.error_logger = self._create_logger(
            f"{self.app_name}_errors_{timestamp}.log",
            "ERROR"
        )

    def _create_logger(self, filename, logger_name):
        """Create a configured logger."""
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        # File handler
        file_handler = logging.FileHandler(
            self.log_dir / filename,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def log_pipeline_start(self, message_id, content_type, source):
        """Log pipeline start."""
        self.pipeline_logger.info(
            f"Pipeline started | Message: {message_id} | Type: {content_type} | Source: {source}"
        )

    def log_pipeline_complete(self, message_id, status, output_path=None):
        """Log pipeline completion."""
        if output_path:
            self.pipeline_logger.info(
                f"Pipeline completed | Message: {message_id} | Status: {status} | Output: {output_path}"
            )
        else:
            self.pipeline_logger.info(
                f"Pipeline completed | Message: {message_id} | Status: {status}"
            )

    def log_download_start(self, url, destination):
        """Log download start."""
        self.download_logger.info(f"Download started | URL: {url} | Destination: {destination}")

    def log_download_complete(self, url, destination, size, duration):
        """Log download completion."""
        self.download_logger.info(
            f"Download completed | URL: {url} | Size: {size} bytes | Duration: {duration:.2f}s"
        )

    def log_download_error(self, url, error):
        """Log download error."""
        self.download_logger.error(f"Download failed | URL: {url} | Error: {error}")
        self.error_logger.error(f"Download failed | URL: {url} | Error: {error}")

    def log_processing_start(self, input_file, operation):
        """Log processing start."""
        self.processing_logger.info(f"Processing started | File: {input_file} | Operation: {operation}")

    def log_processing_complete(self, input_file, operation, output_file, duration):
        """Log processing completion."""
        self.processing_logger.info(
            f"Processing completed | File: {input_file} | Operation: {operation} | "
            f"Output: {output_file} | Duration: {duration:.2f}s"
        )

    def log_processing_error(self, input_file, operation, error):
        """Log processing error."""
        self.processing_logger.error(f"Processing failed | File: {input_file} | Operation: {operation} | Error: {error}")
        self.error_logger.error(f"Processing failed | File: {input_file} | Operation: {operation} | Error: {error}")

    def log_upload_start(self, video_path, platform):
        """Log upload start."""
        self.upload_logger.info(f"Upload started | File: {video_path} | Platform: {platform}")

    def log_upload_complete(self, video_path, platform, video_id, duration):
        """Log upload completion."""
        self.upload_logger.info(
            f"Upload completed | File: {video_path} | Platform: {platform} | "
            f"Video ID: {video_id} | Duration: {duration:.2f}s"
        )

    def log_upload_error(self, video_path, platform, error):
        """Log upload error."""
        self.upload_logger.error(f"Upload failed | File: {video_path} | Platform: {platform} | Error: {error}")
        self.error_logger.error(f"Upload failed | File: {video_path} | Platform: {platform} | Error: {error}")

    def log_hook_detected(self, video_path, hook_timestamp, hook_type):
        """Log hook detection."""
        self.processing_logger.info(
            f"Hook detected | File: {video_path} | Timestamp: {hook_timestamp}s | Type: {hook_type}"
        )

    def log_metadata_generated(self, video_path, title_length, tags_count):
        """Log metadata generation."""
        self.processing_logger.info(
            f"Metadata generated | File: {video_path} | Title length: {title_length} | Tags: {tags_count}"
        )

    def log_audio_analysis(self, audio_path, tempo, beat_count, duration):
        """Log audio analysis."""
        self.processing_logger.info(
            f"Audio analyzed | File: {audio_path} | Tempo: {tempo:.1f} BPM | "
            f"Beats: {beat_count} | Duration: {duration:.2f}s"
        )

    def log_effect_applied(self, input_file, effect_name, parameters):
        """Log effect application."""
        self.processing_logger.info(
            f"Effect applied | File: {input_file} | Effect: {effect_name} | Parameters: {parameters}"
        )

# Global logger instance
_logger_instance = None

def get_logger():
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = VideoAutomationLogger()
    return _logger_instance

def log_info(message, component="GENERAL"):
    """Convenience function for info logging."""
    logger = get_logger()
    getattr(logger, f"{component.lower()}_logger", logger.pipeline_logger).info(message)

def log_error(message, component="GENERAL"):
    """Convenience function for error logging."""
    logger = get_logger()
    getattr(logger, f"{component.lower()}_logger", logger.pipeline_logger).error(message)
    logger.error_logger.error(message)

def log_warning(message, component="GENERAL"):
    """Convenience function for warning logging."""
    logger = get_logger()
    getattr(logger, f"{component.lower()}_logger", logger.pipeline_logger).warning(message)
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
        # Store the date to check for daily rotation
        self.current_date = datetime.now().strftime("%Y%m%d")
        self.setup_loggers()

    def _ensure_daily_logger(self):
        """Check if the date has changed and refresh loggers if needed."""
        new_date = datetime.now().strftime("%Y%m%d")
        if new_date != self.current_date:
            self.current_date = new_date
            self.setup_loggers()

    def setup_loggers(self):
        """Setup separate loggers for different components."""
        # Main pipeline logger
        self.pipeline_logger = self._create_logger(
            f"{self.app_name}_pipeline_{self.current_date}.log",
            "PIPELINE"
        )

        # Download logger
        self.download_logger = self._create_logger(
            f"{self.app_name}_download_{self.current_date}.log",
            "DOWNLOAD"
        )

        # Processing logger
        self.processing_logger = self._create_logger(
            f"{self.app_name}_processing_{self.current_date}.log",
            "PROCESSING"
        )

        # Upload logger
        self.upload_logger = self._create_logger(
            f"{self.app_name}_upload_{self.current_date}.log",
            "UPLOAD"
        )

        # Error logger
        self.error_logger = self._create_logger(
            f"{self.app_name}_errors_{self.current_date}.log",
            "ERROR"
        )

    def _create_logger(self, filename, logger_name):
        """Create a configured logger."""
        # Clear existing handlers if any to avoid duplicate logs when rotating
        logger = logging.getLogger(logger_name)
        if logger.hasHandlers():
            logger.handlers.clear()
        
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
        self._ensure_daily_logger()
        self.pipeline_logger.info(
            f"Pipeline started | Message: {message_id} | Type: {content_type} | Source: {source}"
        )

    def log_pipeline_complete(self, message_id, status, output_path=None):
        """Log pipeline completion."""
        self._ensure_daily_logger()
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
        self._ensure_daily_logger()
        self.download_logger.info(f"Download started | URL: {url} | Destination: {destination}")

    def log_download_complete(self, url, destination, size, duration):
        """Log download completion."""
        self.download_logger.info(
            f"Download completed | URL: {url} | Size: {size} bytes | Duration: {duration:.2f}s"
        )

    def log_download_error(self, url, error):
        """Log download error."""
        self._ensure_daily_logger()
        self.download_logger.error(f"Download failed | URL: {url} | Error: {error}")
        self.error_logger.error(f"Download failed | URL: {url} | Error: {error}")

    def log_processing_start(self, input_file, operation):
        """Log processing start."""
        self._ensure_daily_logger()
        self.processing_logger.info(f"Processing started | File: {input_file} | Operation: {operation}")

    def log_processing_complete(self, input_file, operation, output_file, duration):
        """Log processing completion."""
        self.processing_logger.info(
            f"Processing completed | File: {input_file} | Operation: {operation} | "
            f"Output: {output_file} | Duration: {duration:.2f}s"
        )

    def log_processing_error(self, input_file, operation, error):
        """Log processing error."""
        self._ensure_daily_logger()
        self.processing_logger.error(f"Processing failed | File: {input_file} | Operation: {operation} | Error: {error}")
        self.error_logger.error(f"Processing failed | File: {input_file} | Operation: {operation} | Error: {error}")

    def log_upload_start(self, video_path, platform):
        """Log upload start."""
        self._ensure_daily_logger()
        self.upload_logger.info(f"Upload started | File: {video_path} | Platform: {platform}")

    def log_upload_complete(self, video_path, platform, video_id, duration):
        """Log upload completion."""
        self.upload_logger.info(
            f"Upload completed | File: {video_path} | Platform: {platform} | "
            f"Video ID: {video_id} | Duration: {duration:.2f}s"
        )

    def log_upload_error(self, video_path, platform, error):
        """Log upload error."""
        self._ensure_daily_logger()
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

import requests

def send_telegram_log(message):
    """Send log message to Telegram channel if token is set."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    channel_id = "-1003737951848"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": f"🤖 **Bot Log**\n{message}"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def log_info(message, component="GENERAL"):
    """Convenience function for info logging."""
    logger = get_logger()
    getattr(logger, f"{component.lower()}_logger", logger.pipeline_logger).info(message)
    send_telegram_log(f"ℹ️ {message}")

def log_error(message, component="GENERAL"):
    """Convenience function for error logging."""
    logger = get_logger()
    getattr(logger, f"{component.lower()}_logger", logger.pipeline_logger).error(message)
    logger.error_logger.error(message)
    send_telegram_log(f"❌ {message}")

def log_warning(message, component="GENERAL"):
    """Convenience function for warning logging."""
    logger = get_logger()
    getattr(logger, f"{component.lower()}_logger", logger.pipeline_logger).warning(message)
    send_telegram_log(f"⚠️ {message}")
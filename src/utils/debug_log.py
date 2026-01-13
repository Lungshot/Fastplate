"""
Debug Logging System for Fastplate
Provides application-wide logging with file and console output.
Can be toggled on/off via the UI menu.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class DebugLogger:
    """Centralized debug logger with toggle capability."""

    _instance: Optional['DebugLogger'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._enabled = False
        self._log_file: Optional[Path] = None
        self._logger = logging.getLogger('fastplate')
        self._logger.setLevel(logging.DEBUG)

        # Console handler (always present, respects enabled state)
        self._console_handler = logging.StreamHandler(sys.stdout)
        self._console_handler.setLevel(logging.DEBUG)
        self._console_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        ))

        # File handler (created when logging enabled)
        self._file_handler: Optional[logging.FileHandler] = None

        # Callbacks for UI updates
        self._status_callbacks = []

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def log_file_path(self) -> Optional[Path]:
        return self._log_file

    def enable(self, log_dir: Optional[str] = None):
        """Enable debug logging."""
        if self._enabled:
            return

        self._enabled = True
        self._logger.addHandler(self._console_handler)

        # Create log file
        if log_dir is None:
            # Default to user's temp or documents folder
            if getattr(sys, 'frozen', False):
                # Running as bundled EXE
                log_dir = Path(os.path.expanduser('~')) / 'Documents' / 'Fastplate'
            else:
                # Running from source
                log_dir = Path(__file__).parent.parent.parent / 'logs'
        else:
            log_dir = Path(log_dir)

        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._log_file = log_dir / f'fastplate_debug_{timestamp}.log'

        # Create file handler
        self._file_handler = logging.FileHandler(self._log_file, encoding='utf-8')
        self._file_handler.setLevel(logging.DEBUG)
        self._file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(name)s - %(funcName)s:%(lineno)d\n    %(message)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self._logger.addHandler(self._file_handler)

        self._logger.info(f"Debug logging enabled. Log file: {self._log_file}")
        self._notify_status_change()

    def disable(self):
        """Disable debug logging."""
        if not self._enabled:
            return

        self._logger.info("Debug logging disabled")
        self._enabled = False

        # Remove handlers
        self._logger.removeHandler(self._console_handler)
        if self._file_handler:
            self._file_handler.close()
            self._logger.removeHandler(self._file_handler)
            self._file_handler = None

        self._notify_status_change()

    def toggle(self) -> bool:
        """Toggle logging state. Returns new enabled state."""
        if self._enabled:
            self.disable()
        else:
            self.enable()
        return self._enabled

    def add_status_callback(self, callback):
        """Add callback to be notified when logging state changes."""
        self._status_callbacks.append(callback)

    def remove_status_callback(self, callback):
        """Remove status callback."""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    def _notify_status_change(self):
        """Notify all registered callbacks of status change."""
        for callback in self._status_callbacks:
            try:
                callback(self._enabled)
            except Exception:
                pass

    # Logging methods
    def debug(self, msg: str, *args, **kwargs):
        if self._enabled:
            self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        if self._enabled:
            self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        if self._enabled:
            self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        if self._enabled:
            self._logger.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        if self._enabled:
            self._logger.exception(msg, *args, **kwargs)

    def log_geometry(self, operation: str, details: dict):
        """Log geometry operations with structured data."""
        if not self._enabled:
            return
        detail_str = ', '.join(f"{k}={v}" for k, v in details.items())
        self._logger.debug(f"GEOMETRY: {operation} - {detail_str}")

    def log_ui(self, event: str, widget: str, details: str = ""):
        """Log UI events."""
        if not self._enabled:
            return
        msg = f"UI: {event} on {widget}"
        if details:
            msg += f" - {details}"
        self._logger.debug(msg)

    def log_preset(self, action: str, name: str, details: str = ""):
        """Log preset operations."""
        if not self._enabled:
            return
        msg = f"PRESET: {action} '{name}'"
        if details:
            msg += f" - {details}"
        self._logger.info(msg)

    def log_export(self, format: str, path: str, success: bool, details: str = ""):
        """Log export operations."""
        if not self._enabled:
            return
        status = "SUCCESS" if success else "FAILED"
        msg = f"EXPORT: {format} to {path} - {status}"
        if details:
            msg += f" - {details}"
        if success:
            self._logger.info(msg)
        else:
            self._logger.error(msg)


# Global singleton instance
debug_log = DebugLogger()


# Convenience functions for quick access
def log_debug(msg: str, *args, **kwargs):
    debug_log.debug(msg, *args, **kwargs)

def log_info(msg: str, *args, **kwargs):
    debug_log.info(msg, *args, **kwargs)

def log_warning(msg: str, *args, **kwargs):
    debug_log.warning(msg, *args, **kwargs)

def log_error(msg: str, *args, **kwargs):
    debug_log.error(msg, *args, **kwargs)

def log_exception(msg: str, *args, **kwargs):
    debug_log.exception(msg, *args, **kwargs)

"""
Logging system for CustomRPC Manager.

Provides file and GUI logging capabilities with configurable levels.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class GUILogHandler(logging.Handler, QObject):
    """Custom log handler that emits signals for GUI display."""
    
    log_emitted = pyqtSignal(str)
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        
    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record as signal."""
        try:
            msg = self.format(record)
            self.log_emitted.emit(msg)
        except Exception:
            self.handleError(record)


class LoggerManager:
    """Manages application logging to file and GUI."""
    
    def __init__(self, log_dir: Path, app_name: str = "customrpcmanager"):
        """
        Initialize logger manager.
        
        Args:
            log_dir: Directory for log files
            app_name: Application name for logger
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.app_name = app_name
        self.gui_handler: Optional[GUILogHandler] = None
        
        # Create logger
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Setup file handler with rotation
        log_file = self.log_dir / f"{app_name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def add_gui_handler(self) -> GUILogHandler:
        """
        Add and return GUI handler for displaying logs in UI.
        
        Returns:
            GUILogHandler instance
        """
        if self.gui_handler is None:
            self.gui_handler = GUILogHandler()
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            self.gui_handler.setFormatter(formatter)
            self.gui_handler.setLevel(logging.INFO)
            self.logger.addHandler(self.gui_handler)
        
        return self.gui_handler
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger
    
    def get_log_file_path(self) -> Path:
        """Get path to current log file."""
        return self.log_dir / f"{self.app_name}.log"
    
    def clear_logs(self) -> None:
        """Clear all log files."""
        for log_file in self.log_dir.glob(f"{self.app_name}.log*"):
            try:
                log_file.unlink()
            except Exception as e:
                self.logger.error(f"Failed to delete log file {log_file}: {e}")

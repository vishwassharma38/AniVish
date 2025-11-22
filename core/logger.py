import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class AniVishLogger:
    """
    Centralized logger for AniVish application.
    Supports console and file logging with configurable levels.
    """
    
    _instance: Optional['AniVishLogger'] = None
    _initialized: bool = False
    
    # Log format templates
    CONSOLE_FORMAT = "%(levelname)s | %(name)s | %(message)s"
    FILE_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    def __new__(cls):
        """Singleton pattern - ensure only one logger instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if AniVishLogger._initialized:
            return
        
        self._loggers: dict = {}
        self._log_level = logging.INFO
        self._console_handler: Optional[logging.Handler] = None
        self._file_handler: Optional[logging.Handler] = None
        self._log_file_path: Optional[Path] = None
        
        # Setup root logger for AniVish
        self._root_logger = logging.getLogger("anivish")
        self._root_logger.setLevel(logging.DEBUG)
        self._root_logger.propagate = False
        
        # Default: console logging only
        self._setup_console_handler()
        
        AniVishLogger._initialized = True
    
    def _setup_console_handler(self):
        """Setup console output handler."""
        if self._console_handler:
            self._root_logger.removeHandler(self._console_handler)
        
        self._console_handler = logging.StreamHandler(sys.stdout)
        self._console_handler.setLevel(self._log_level)
        self._console_handler.setFormatter(
            logging.Formatter(self.CONSOLE_FORMAT)
        )
        self._root_logger.addHandler(self._console_handler)
    
    def _setup_file_handler(self, log_dir: Path):
        """Setup file output handler."""
        if self._file_handler:
            self._root_logger.removeHandler(self._file_handler)
        
        # Create log directory if needed
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        self._log_file_path = log_dir / f"anivish_{timestamp}.log"
        
        self._file_handler = logging.FileHandler(
            self._log_file_path,
            encoding='utf-8'
        )
        self._file_handler.setLevel(logging.DEBUG)
        self._file_handler.setFormatter(
            logging.Formatter(self.FILE_FORMAT, self.DATE_FORMAT)
        )
        self._root_logger.addHandler(self._file_handler)
    
    def configure(
        self,
        level: str = "INFO",
        log_to_file: bool = False,
        log_dir: Optional[str] = None,
        console_output: bool = True
    ):
        """
        Configure logger settings.
        
        Args:
            level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            log_to_file: Enable file logging
            log_dir: Directory for log files (default: ./logs)
            console_output: Enable console output
        """
        # Set level
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self._log_level = level_map.get(level.upper(), logging.INFO)
        
        # Update console handler
        if console_output:
            if not self._console_handler:
                self._setup_console_handler()
            self._console_handler.setLevel(self._log_level)
        elif self._console_handler:
            self._root_logger.removeHandler(self._console_handler)
            self._console_handler = None
        
        # Setup file logging
        if log_to_file:
            log_path = Path(log_dir) if log_dir else Path("./logs")
            self._setup_file_handler(log_path)
        elif self._file_handler:
            self._root_logger.removeHandler(self._file_handler)
            self._file_handler = None
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a named logger for a specific component.
        
        Args:
            name: Component name (e.g., 'backend', 'videomanager', 'ui')
            
        Returns:
            Logger instance for the component
        """
        full_name = f"anivish.{name}"
        if full_name not in self._loggers:
            logger = logging.getLogger(full_name)
            self._loggers[full_name] = logger
        return self._loggers[full_name]
    
    def get_log_file_path(self) -> Optional[Path]:
        """Get current log file path if file logging is enabled."""
        return self._log_file_path
    
    def set_level(self, level: str):
        """Change log level at runtime."""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self._log_level = level_map.get(level.upper(), logging.INFO)
        if self._console_handler:
            self._console_handler.setLevel(self._log_level)


# Global singleton instance
_logger_instance: Optional[AniVishLogger] = None


def get_logger(name: str = "core") -> logging.Logger:
    """
    Get a logger for a component.
    
    Args:
        name: Component name
        
    Returns:
        Logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AniVishLogger()
    return _logger_instance.get_logger(name)


def configure_logging(
    level: str = "INFO",
    log_to_file: bool = False,
    log_dir: Optional[str] = None,
    console_output: bool = True
):
    """
    Configure application-wide logging.
    
    Args:
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_to_file: Enable file logging
        log_dir: Directory for log files
        console_output: Enable console output
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AniVishLogger()
    _logger_instance.configure(level, log_to_file, log_dir, console_output)


def set_log_level(level: str):
    """Change log level at runtime."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AniVishLogger()
    _logger_instance.set_level(level)
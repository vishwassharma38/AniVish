import json
import os
from pathlib import Path
from typing import Any, Optional, Dict
from dataclasses import dataclass, field, asdict

from core.logger import get_logger

logger = get_logger("config")


@dataclass
class PlaybackConfig:
    """Playback-related settings."""
    default_volume: int = 100
    default_speed: float = 1.0
    resume_playback: bool = True
    skip_interval_short: int = 10000  # ms
    skip_interval_long: int = 60000   # ms
    auto_play_next: bool = False


@dataclass
class AudioConfig:
    """Audio-related settings."""
    preferred_audio_track: int = -1  # -1 = auto/default
    audio_delay_ms: int = 0
    normalize_audio: bool = False
    preferred_language: str = "eng"  # FIXED: Added missing field


@dataclass
class SubtitleConfig:
    """Subtitle-related settings."""
    enabled: bool = True
    preferred_language: str = ""
    subtitle_delay_ms: int = 0
    font_size: int = 24
    font_color: str = "#FFFFFF"
    background_opacity: float = 0.5


@dataclass
class UIConfig:
    """UI-related settings."""
    theme: str = "dark"
    window_width: int = 1280
    window_height: int = 720
    window_maximized: bool = False
    show_controls_on_hover: bool = True
    controls_timeout_ms: int = 3000


@dataclass
class LoggingConfig:
    """Logging-related settings."""
    level: str = "INFO"
    log_to_file: bool = False
    log_directory: str = "./logs"


@dataclass
class AniVishConfig:
    """Root configuration container."""
    playback: PlaybackConfig = field(default_factory=PlaybackConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    subtitle: SubtitleConfig = field(default_factory=SubtitleConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Recent files list
    recent_files: list = field(default_factory=list)
    max_recent_files: int = 10


class ConfigLoader:
    """
    Configuration loader and manager.
    Handles reading/writing config files and providing defaults.
    """
    
    DEFAULT_CONFIG_FILENAME = "anivish_config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        self._config_path = self._resolve_config_path(config_path)
        self._config = AniVishConfig()
        self._dirty = False
        
        # Load existing config or create default
        self._load()
    
    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """Determine config file path."""
        if config_path:
            return Path(config_path)
        
        # Default: user's config directory or app directory
        if os.name == 'nt':  # Windows
            base = Path(os.environ.get('APPDATA', '.'))
        else:  # Linux/macOS
            base = Path.home() / '.config'
        
        config_dir = base / 'anivish'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / self.DEFAULT_CONFIG_FILENAME
    
    def _load(self):
        """Load configuration from file."""
        if not self._config_path.exists():
            logger.info(f"No config file found, using defaults: {self._config_path}")
            self._save()  # Create default config file
            return
        
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._config = self._dict_to_config(data)
            logger.info(f"Loaded config from: {self._config_path}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid config JSON: {e}. Using defaults.")
            self._config = AniVishConfig()
        except Exception as e:
            logger.error(f"Failed to load config: {e}. Using defaults.")
            self._config = AniVishConfig()
    
    def _save(self):
        """Save configuration to file."""
        try:
            data = self._config_to_dict(self._config)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self._dirty = False
            logger.debug(f"Saved config to: {self._config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _config_to_dict(self, config: AniVishConfig) -> dict:
        """Convert config dataclass to dictionary."""
        return {
            'playback': asdict(config.playback),
            'audio': asdict(config.audio),
            'subtitle': asdict(config.subtitle),
            'ui': asdict(config.ui),
            'logging': asdict(config.logging),
            'recent_files': config.recent_files,
            'max_recent_files': config.max_recent_files
        }
    
    def _dict_to_config(self, data: dict) -> AniVishConfig:
        """Convert dictionary to config dataclass."""
        config = AniVishConfig()
        
        if 'playback' in data:
            config.playback = PlaybackConfig(**data['playback'])
        if 'audio' in data:
            config.audio = AudioConfig(**data['audio'])
        if 'subtitle' in data:
            config.subtitle = SubtitleConfig(**data['subtitle'])
        if 'ui' in data:
            config.ui = UIConfig(**data['ui'])
        if 'logging' in data:
            config.logging = LoggingConfig(**data['logging'])
        if 'recent_files' in data:
            config.recent_files = data['recent_files']
        if 'max_recent_files' in data:
            config.max_recent_files = data['max_recent_files']
        
        return config
    
    # ==========================================
    # Public API
    # ==========================================
    
    @property
    def config(self) -> AniVishConfig:
        """Get the full configuration object."""
        return self._config
    
    @property
    def playback(self) -> PlaybackConfig:
        """Get playback settings."""
        return self._config.playback
    
    @property
    def audio(self) -> AudioConfig:
        """Get audio settings."""
        return self._config.audio
    
    @property
    def subtitle(self) -> SubtitleConfig:
        """Get subtitle settings."""
        return self._config.subtitle
    
    @property
    def ui(self) -> UIConfig:
        """Get UI settings."""
        return self._config.ui
    
    @property
    def logging(self) -> LoggingConfig:
        """Get logging settings."""
        return self._config.logging
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a specific config value.
        
        Args:
            section: Config section ('playback', 'audio', 'subtitle', 'ui', 'logging')
            key: Setting key within section
            default: Default value if not found
        """
        section_obj = getattr(self._config, section, None)
        if section_obj is None:
            return default
        return getattr(section_obj, key, default)
    
    def set(self, section: str, key: str, value: Any):
        """
        Set a specific config value.
        
        Args:
            section: Config section
            key: Setting key
            value: New value
        """
        section_obj = getattr(self._config, section, None)
        if section_obj and hasattr(section_obj, key):
            setattr(section_obj, key, value)
            self._dirty = True
            logger.debug(f"Config updated: {section}.{key} = {value}")
    
    def save(self):
        """Save current configuration to file."""
        self._save()
    
    def save_if_dirty(self):
        """Save only if config has been modified."""
        if self._dirty:
            self._save()
    
    def reload(self):
        """Reload configuration from file."""
        self._load()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._config = AniVishConfig()
        self._dirty = True
        logger.info("Config reset to defaults")
    
    def reset_section(self, section: str):
        """Reset a specific section to defaults."""
        defaults = {
            'playback': PlaybackConfig(),
            'audio': AudioConfig(),
            'subtitle': SubtitleConfig(),
            'ui': UIConfig(),
            'logging': LoggingConfig()
        }
        if section in defaults:
            setattr(self._config, section, defaults[section])
            self._dirty = True
            logger.info(f"Config section '{section}' reset to defaults")
    
    # ==========================================
    # Recent Files Management
    # ==========================================
    
    def add_recent_file(self, path: str):
        """Add a file to recent files list."""
        # Remove if already exists (to move to top)
        if path in self._config.recent_files:
            self._config.recent_files.remove(path)
        
        # Add to beginning
        self._config.recent_files.insert(0, path)
        
        # Trim to max size
        self._config.recent_files = self._config.recent_files[:self._config.max_recent_files]
        self._dirty = True
    
    def get_recent_files(self) -> list:
        """Get list of recent files."""
        return self._config.recent_files.copy()
    
    def clear_recent_files(self):
        """Clear recent files list."""
        self._config.recent_files = []
        self._dirty = True
    
    # ==========================================
    # Config Path Info
    # ==========================================
    
    def get_config_path(self) -> Path:
        """Get the config file path."""
        return self._config_path


# ==========================================
# Global Config Instance
# ==========================================

_config_instance: Optional[ConfigLoader] = None


def get_config(config_path: Optional[str] = None) -> ConfigLoader:
    """
    Get the global config loader instance.
    
    Args:
        config_path: Optional path to config file (only used on first call)
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader(config_path)
    return _config_instance


def reload_config():
    """Reload the global config from file."""
    global _config_instance
    if _config_instance:
        _config_instance.reload()
import os
import vlc
from enum import Enum, auto
from typing import Optional, List, Tuple, Callable, Dict, Any
from urllib.parse import urlparse

from core.anivish_backend import AniVishBackend
from core.logger import get_logger
from core.config_loader import get_config, ConfigLoader

# Module logger
logger = get_logger("videomanager")


class PlaybackState(Enum):
    """Enumeration of possible playback states."""
    IDLE = auto()
    LOADING = auto()
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()
    BUFFERING = auto()
    ENDED = auto()
    ERROR = auto()


class MediaType(Enum):
    """Type of media source."""
    LOCAL_FILE = auto()
    HTTP_URL = auto()
    STREAM_HLS = auto()  # M3U8
    STREAM_DASH = auto()
    UNKNOWN = auto()


class VideoManagerError(Exception):
    """Base exception for VideoManager errors."""
    pass


class MediaLoadError(VideoManagerError):
    """Raised when media fails to load."""
    pass


class InvalidSourceError(VideoManagerError):
    """Raised when media source is invalid."""
    pass


class VideoManager:
    """
    Central API for AniVish video playback management.
    Wraps AniVishBackend and provides high-level media handling,
    event management, subtitle support, and error handling.
    """

    # Supported file extensions
    SUPPORTED_VIDEO_EXT = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg', '.mpg', '.3gp'}
    SUPPORTED_AUDIO_EXT = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
    SUPPORTED_SUBTITLE_EXT = {'.srt', '.ass', '.ssa', '.sub', '.vtt'}
    SUPPORTED_STREAM_EXT = {'.m3u8', '.m3u', '.mpd'}

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """
        Initialize VideoManager.
        
        Args:
            config_loader: Optional ConfigLoader instance. If None, uses global config.
        """
        logger.info("Initializing VideoManager")
        
        # Initialize backend
        self._backend = AniVishBackend()
        
        # Load configuration
        self._config = config_loader or get_config()
        
        # State management
        self._state = PlaybackState.IDLE
        self._current_source: Optional[str] = None
        self._media_type: MediaType = MediaType.UNKNOWN
        self._last_error: Optional[str] = None
        
        # Video info cache
        self._video_width: int = 0
        self._video_height: int = 0
        
        # Event callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            'on_playing': [],
            'on_paused': [],
            'on_stopped': [],
            'on_ended': [],
            'on_error': [],
            'on_time_changed': [],
            'on_position_changed': [],
            'on_buffering': [],
            'on_state_changed': [],
            'on_video_size_changed': [],
            'on_media_loaded': [],
        }
        
        # Setup VLC event handlers
        self._setup_vlc_events()
        
        # Apply initial settings from config
        self._apply_config_settings()
        
        logger.info("VideoManager initialized successfully")

    def _apply_config_settings(self):
        """Apply initial settings from configuration."""
        try:
            # Apply default volume
            default_vol = self._config.playback.default_volume
            self._backend.set_volume(default_vol)
            logger.debug(f"Applied default volume: {default_vol}")
            
            # Apply default playback speed
            default_speed = self._config.playback.default_speed
            self._backend.set_playback_speed(default_speed)
            logger.debug(f"Applied default speed: {default_speed}")
            
            # Apply audio delay if configured
            audio_delay = self._config.audio.audio_delay_ms
            if audio_delay != 0:
                self._backend.set_audio_delay(audio_delay * 1000)
                logger.debug(f"Applied audio delay: {audio_delay}ms")
                
        except Exception as e:
            logger.warning(f"Failed to apply some config settings: {e}")

    # ==========================================
    # Event System
    # ==========================================

    def _setup_vlc_events(self):
        """Wire up VLC event callbacks."""
        em = self._backend.get_event_manager()
        
        # FIXED: Use lambda to ensure proper callback context
        em.event_attach(vlc.EventType.MediaPlayerPlaying, lambda e: self._on_vlc_playing(e))
        em.event_attach(vlc.EventType.MediaPlayerPaused, lambda e: self._on_vlc_paused(e))
        em.event_attach(vlc.EventType.MediaPlayerStopped, lambda e: self._on_vlc_stopped(e))
        em.event_attach(vlc.EventType.MediaPlayerEndReached, lambda e: self._on_vlc_ended(e))
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError, lambda e: self._on_vlc_error(e))
        em.event_attach(vlc.EventType.MediaPlayerTimeChanged, lambda e: self._on_vlc_time_changed(e))
        em.event_attach(vlc.EventType.MediaPlayerPositionChanged, lambda e: self._on_vlc_position_changed(e))
        em.event_attach(vlc.EventType.MediaPlayerBuffering, lambda e: self._on_vlc_buffering(e))
        em.event_attach(vlc.EventType.MediaPlayerVout, lambda e: self._on_vlc_vout(e))
        
        logger.debug("VLC events wired up with lambda wrappers")

    def _emit(self, event_name: str, *args, **kwargs):
        """Emit an event to all registered callbacks."""
        callbacks = self._callbacks.get(event_name, [])
        logger.debug(f"Emitting event '{event_name}' to {len(callbacks)} callbacks")
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Callback error for {event_name}: {e}", exc_info=True)

    def _set_state(self, new_state: PlaybackState):
        """Update state and emit state change event."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            logger.info(f"State changed: {old_state.name} -> {new_state.name}")
            self._emit('on_state_changed', old_state, new_state)

    # VLC Event Handlers
    def _on_vlc_playing(self, event):
        logger.debug("VLC event: Playing")
        self._set_state(PlaybackState.PLAYING)
        self._update_video_size()
        self._emit('on_playing')

    def _on_vlc_paused(self, event):
        logger.debug("VLC event: Paused")
        self._set_state(PlaybackState.PAUSED)
        self._emit('on_paused')

    def _on_vlc_stopped(self, event):
        logger.debug("VLC event: Stopped")
        self._set_state(PlaybackState.STOPPED)
        self._emit('on_stopped')

    def _on_vlc_ended(self, event):
        logger.debug("VLC event: Ended")
        self._set_state(PlaybackState.ENDED)
        logger.info("Playback ended")
        self._emit('on_ended')

    def _on_vlc_error(self, event):
        logger.error("VLC event: Error")
        self._last_error = "Playback error occurred"
        self._set_state(PlaybackState.ERROR)
        logger.error(f"VLC error: {self._last_error}")
        self._emit('on_error', self._last_error)

    def _on_vlc_time_changed(self, event):
        time_ms = self._backend.get_current_time()
        self._emit('on_time_changed', time_ms)

    def _on_vlc_position_changed(self, event):
        position = self._backend.get_position()
        self._emit('on_position_changed', position)

    def _on_vlc_buffering(self, event):
        if self._state != PlaybackState.BUFFERING:
            self._set_state(PlaybackState.BUFFERING)
            logger.debug("Buffering started")
        # FIXED: Safely access event attribute
        try:
            cache = event.u.new_cache if hasattr(event, 'u') else 0
        except:
            cache = 0
        self._emit('on_buffering', cache)

    def _on_vlc_vout(self, event):
        logger.debug("VLC event: Video output ready")
        self._update_video_size()

    def _update_video_size(self):
        """Update cached video dimensions."""
        try:
            w = self._backend.player.video_get_width()
            h = self._backend.player.video_get_height()
            if w > 0 and h > 0 and (w != self._video_width or h != self._video_height):
                self._video_width = w
                self._video_height = h
                logger.info(f"Video size: {w}x{h}")
                self._emit('on_video_size_changed', w, h)
        except Exception as e:
            logger.debug(f"Could not get video size: {e}")

    # Public event registration
    def on(self, event_name: str, callback: Callable):
        """
        Register a callback for an event.
        
        Events:
            on_playing, on_paused, on_stopped, on_ended, on_error,
            on_time_changed, on_position_changed, on_buffering,
            on_state_changed, on_video_size_changed, on_media_loaded
        """
        if event_name in self._callbacks:
            self._callbacks[event_name].append(callback)
            logger.debug(f"Callback registered for: {event_name}")
        else:
            raise ValueError(f"Unknown event: {event_name}")

    def off(self, event_name: str, callback: Callable):
        """Unregister a callback."""
        if event_name in self._callbacks and callback in self._callbacks[event_name]:
            self._callbacks[event_name].remove(callback)
            logger.debug(f"Callback unregistered for: {event_name}")

    # ==========================================
    # Media Loading & Validation
    # ==========================================

    def _detect_media_type(self, source: str) -> MediaType:
        """Detect the type of media source."""
        parsed = urlparse(source)
        
        # Check if it's a URL
        if parsed.scheme in ('http', 'https', 'rtsp', 'rtmp', 'mms'):
            ext = os.path.splitext(parsed.path)[1].lower()
            if ext in ('.m3u8', '.m3u'):
                return MediaType.STREAM_HLS
            elif ext == '.mpd':
                return MediaType.STREAM_DASH
            return MediaType.HTTP_URL
        
        # Local file
        if os.path.exists(source):
            return MediaType.LOCAL_FILE
        
        return MediaType.UNKNOWN

    def _validate_local_file(self, path: str) -> Tuple[bool, Optional[str]]:
        """Validate a local file path."""
        if not os.path.exists(path):
            return False, f"File not found: {path}"
        
        if not os.path.isfile(path):
            return False, f"Not a file: {path}"
        
        ext = os.path.splitext(path)[1].lower()
        all_supported = self.SUPPORTED_VIDEO_EXT | self.SUPPORTED_AUDIO_EXT
        
        if ext and ext not in all_supported:
            return False, f"Unsupported format: {ext}"
        
        # Check file is readable
        try:
            with open(path, 'rb') as f:
                f.read(1024)
        except PermissionError:
            return False, f"Permission denied: {path}"
        except IOError as e:
            return False, f"Cannot read file: {e}"
        
        return True, None

    def _validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """Validate a URL (basic validation without network check)."""
        parsed = urlparse(url)
        
        if not parsed.scheme:
            return False, "URL missing scheme (http/https)"
        
        if parsed.scheme not in ('http', 'https', 'rtsp', 'rtmp', 'mms', 'file'):
            return False, f"Unsupported URL scheme: {parsed.scheme}"
        
        if not parsed.netloc and parsed.scheme != 'file':
            return False, "URL missing host"
        
        return True, None

    def validate_source(self, source: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a media source before loading.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        media_type = self._detect_media_type(source)
        
        if media_type == MediaType.LOCAL_FILE:
            return self._validate_local_file(source)
        elif media_type in (MediaType.HTTP_URL, MediaType.STREAM_HLS, MediaType.STREAM_DASH):
            return self._validate_url(source)
        else:
            # Try as URL if looks like one
            if '://' in source:
                return self._validate_url(source)
            return False, "Invalid or unrecognized media source"

    def load(self, source: str, validate: bool = True) -> bool:
        """
        Load a media source (file or URL).
        
        Args:
            source: File path or URL
            validate: Whether to validate before loading
            
        Returns:
            True if loaded successfully
            
        Raises:
            InvalidSourceError: If validation fails
            MediaLoadError: If loading fails
        """
        # Clean up source string
        source = source.strip().strip('"').strip("'")
        logger.info(f"Loading media: {source}")
        
        # Validate
        if validate:
            is_valid, error = self.validate_source(source)
            if not is_valid:
                self._last_error = error
                self._set_state(PlaybackState.ERROR)
                logger.error(f"Validation failed: {error}")
                raise InvalidSourceError(error)
        
        # Detect type
        self._media_type = self._detect_media_type(source)
        self._set_state(PlaybackState.LOADING)
        
        # Load via backend
        try:
            if not self._backend.set_media(source):
                self._last_error = "Failed to load media"
                self._set_state(PlaybackState.ERROR)
                logger.error("Backend failed to load media")
                raise MediaLoadError("Backend failed to load media")
            
            self._current_source = source
            self._last_error = None
            self._set_state(PlaybackState.STOPPED)
            
            # Add to recent files
            if self._media_type == MediaType.LOCAL_FILE:
                self._config.add_recent_file(source)
                self._config.save_if_dirty()
            
            logger.info(f"Media loaded successfully: {self._media_type.name}")
            self._emit('on_media_loaded', source, self._media_type)
            return True
            
        except (InvalidSourceError, MediaLoadError):
            raise
        except Exception as e:
            self._last_error = str(e)
            self._set_state(PlaybackState.ERROR)
            logger.error(f"Failed to load media: {e}", exc_info=True)
            raise MediaLoadError(f"Failed to load media: {e}")

    def load_url(self, url: str) -> bool:
        """Load media from URL."""
        return self.load(url)

    def load_file(self, path: str) -> bool:
        """Load media from local file."""
        return self.load(path)

    # ==========================================
    # Playback Controls API
    # ==========================================

    def play(self) -> bool:
        """Start or resume playback."""
        if self._current_source is None:
            logger.warning("Cannot play: no media loaded")
            return False
        logger.info("Play requested")
        result = self._backend.play()
        return result == 0

    def pause(self):
        """Pause playback."""
        logger.info("Pause requested")
        self._backend.pause()

    def stop(self):
        """Stop playback."""
        logger.info("Stop requested")
        self._backend.stop()

    def toggle_play_pause(self):
        """Toggle between play and pause."""
        logger.info(f"Toggle play/pause - current state: {self._state.name}")
        if self._state == PlaybackState.PLAYING:
            self.pause()
        else:
            self.play()

    def seek(self, position_ms: int):
        """Seek to position in milliseconds."""
        self._backend.seek(position_ms)
        logger.info(f"Seek to: {position_ms}ms")

    def seek_relative(self, offset_ms: int):
        """Seek relative to current position."""
        self._backend.seek_relative(offset_ms)
        logger.debug(f"Relative seek: {offset_ms:+d}ms")

    def seek_percent(self, percent: float):
        """Seek to percentage of total duration (0-100)."""
        self._backend.set_position(percent / 100.0)
        logger.debug(f"Seek to {percent:.1f}%")

    def skip_forward(self):
        """Skip forward by configured short interval."""
        interval = self._config.playback.skip_interval_short
        self.seek_relative(interval)
        logger.debug(f"Skip forward {interval}ms")

    def skip_backward(self):
        """Skip backward by configured short interval."""
        interval = self._config.playback.skip_interval_short
        self.seek_relative(-interval)
        logger.debug(f"Skip backward {interval}ms")

    def skip_forward_long(self):
        """Skip forward by configured long interval."""
        interval = self._config.playback.skip_interval_long
        self.seek_relative(interval)
        logger.debug(f"Skip forward (long) {interval}ms")

    def skip_backward_long(self):
        """Skip backward by configured long interval."""
        interval = self._config.playback.skip_interval_long
        self.seek_relative(-interval)
        logger.debug(f"Skip backward (long) {interval}ms")

    def get_current_time(self) -> int:
        """Get current position in milliseconds."""
        return self._backend.get_current_time()

    def get_total_duration(self) -> int:
        """Get total duration in milliseconds."""
        return self._backend.get_total_duration()

    def get_position(self) -> float:
        """Get position as fraction (0.0 to 1.0)."""
        return self._backend.get_position()

    def set_playback_speed(self, rate: float):
        """Set playback speed (0.25 to 4.0)."""
        self._backend.set_playback_speed(rate)
        logger.info(f"Playback speed: {rate}x")

    def get_playback_speed(self) -> float:
        """Get current playback speed."""
        return self._backend.get_playback_speed()

    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._backend.is_playing()

    def get_state(self) -> PlaybackState:
        """Get current playback state."""
        return self._state

    # ==========================================
    # Audio Subsystem
    # ==========================================

    def set_volume(self, vol: int):
        """Set volume (0-100)."""
        self._backend.set_volume(vol)
        logger.debug(f"Volume set to {vol}")

    def get_volume(self) -> int:
        """Get current volume."""
        return self._backend.get_volume()

    def mute(self):
        """Mute audio."""
        self._backend.mute()
        logger.debug("Muted")

    def unmute(self):
        """Unmute audio."""
        self._backend.unmute()
        logger.debug("Unmuted")

    def toggle_mute(self):
        """Toggle mute state."""
        self._backend.toggle_mute()
        logger.debug(f"Mute toggled - now {'muted' if self._backend.is_muted() else 'unmuted'}")

    def is_muted(self) -> bool:
        """Check if muted."""
        return self._backend.is_muted()

    def get_audio_tracks(self) -> List[Tuple[int, str]]:
        """Get available audio tracks."""
        return self._backend.get_audio_tracks()

    def get_current_audio_track(self) -> int:
        """Get current audio track ID."""
        return self._backend.get_current_audio_track()

    def set_audio_track(self, track_id: int) -> bool:
        """Set audio track by ID."""
        result = self._backend.set_audio_track(track_id)
        if result:
            logger.info(f"Audio track set: {track_id}")
        return result

    def set_audio_delay(self, delay_ms: int):
        """Set audio delay in milliseconds."""
        self._backend.set_audio_delay(delay_ms * 1000)
        logger.info(f"Audio delay: {delay_ms}ms")

    def get_audio_delay(self) -> int:
        """Get audio delay in milliseconds."""
        return self._backend.get_audio_delay() // 1000

    # ==========================================
    # Subtitle Subsystem (via Backend)
    # ==========================================

    def get_subtitle_tracks(self) -> List[Tuple[int, str]]:
        """Get available subtitle tracks."""
        return self._backend.get_subtitle_tracks()

    def get_current_subtitle_track(self) -> int:
        """Get current subtitle track ID (-1 for disabled)."""
        return self._backend.get_current_subtitle_track()

    def set_subtitle_track(self, track_id: int) -> bool:
        """
        Set subtitle track by ID.
        Use -1 to disable subtitles.
        """
        result = self._backend.set_subtitle_track(track_id)
        if result:
            logger.info(f"Subtitle track set: {track_id}")
        return result

    def disable_subtitles(self):
        """Disable subtitle display."""
        self.set_subtitle_track(-1)

    def load_subtitle_file(self, path: str) -> bool:
        """
        Load external subtitle file (.srt, .ass, .ssa, .sub, .vtt).
        
        Args:
            path: Path to subtitle file
            
        Returns:
            True if loaded successfully
        """
        if not os.path.exists(path):
            logger.error(f"Subtitle file not found: {path}")
            return False
        
        ext = os.path.splitext(path)[1].lower()
        if ext not in self.SUPPORTED_SUBTITLE_EXT:
            logger.error(f"Unsupported subtitle format: {ext}")
            return False
        
        # VLC expects absolute path
        abs_path = os.path.abspath(path)
        result = self._backend.load_subtitle_file(abs_path)
        
        if result:
            logger.info(f"Subtitle loaded: {path}")
        else:
            logger.error(f"Failed to load subtitle: {path}")
        
        return result

    def load_subtitle_url(self, url: str) -> bool:
        """
        Load subtitles from URL.
        
        Args:
            url: URL to subtitle file
            
        Returns:
            True if loaded successfully
        """
        result = self._backend.load_subtitle_file(url)
        if result:
            logger.info(f"Subtitle loaded from URL: {url}")
        return result

    def set_subtitle_delay(self, delay_ms: int):
        """
        Set subtitle delay in milliseconds.
        Positive = subtitles appear later, Negative = earlier.
        """
        self._backend.set_subtitle_delay(delay_ms * 1000)
        logger.info(f"Subtitle delay: {delay_ms}ms")

    def get_subtitle_delay(self) -> int:
        """Get subtitle delay in milliseconds."""
        return self._backend.get_subtitle_delay() // 1000

    # ==========================================
    # Video Info
    # ==========================================

    def get_video_size(self) -> Tuple[int, int]:
        """Get video dimensions (width, height)."""
        return (self._video_width, self._video_height)

    def get_media_info(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive media information."""
        info = self._backend.get_media_info()
        if info:
            info['video_width'] = self._video_width
            info['video_height'] = self._video_height
            info['media_type'] = self._media_type.name
            info['source'] = self._current_source
        return info

    def get_aspect_ratio(self) -> Optional[str]:
        """Get video aspect ratio string."""
        return self._backend.player.video_get_aspect_ratio()

    def set_aspect_ratio(self, ratio: Optional[str]):
        """
        Set video aspect ratio.
        
        Args:
            ratio: Ratio string like "16:9", "4:3", or None for default
        """
        self._backend.player.video_set_aspect_ratio(ratio)
        logger.info(f"Aspect ratio: {ratio}")

    # ==========================================
    # Video Output Integration
    # ==========================================

    def set_video_output(self, handle, platform: str = 'auto'):
        """
        Set video output window handle.
        
        Args:
            handle: Window handle/ID
            platform: 'windows', 'linux', 'macos', or 'auto'
        """
        if platform == 'auto':
            import sys
            if sys.platform == 'win32':
                platform = 'windows'
            elif sys.platform == 'darwin':
                platform = 'macos'
            else:
                platform = 'linux'
        
        if platform == 'windows':
            self._backend.set_hwnd(handle)
        elif platform == 'linux':
            self._backend.set_xwindow(handle)
        elif platform == 'macos':
            self._backend.set_nsobject(handle)
        
        logger.info(f"Video output set for platform: {platform}")

    # ==========================================
    # Error Handling
    # ==========================================

    def get_last_error(self) -> Optional[str]:
        """Get the last error message."""
        return self._last_error

    def clear_error(self):
        """Clear the last error."""
        self._last_error = None
        if self._state == PlaybackState.ERROR:
            self._set_state(PlaybackState.IDLE)

    def has_error(self) -> bool:
        """Check if there's an error state."""
        return self._state == PlaybackState.ERROR

    # ==========================================
    # Configuration Access
    # ==========================================

    def get_config(self) -> ConfigLoader:
        """Get the config loader instance."""
        return self._config

    def get_recent_files(self) -> List[str]:
        """Get list of recently played files."""
        return self._config.get_recent_files()

    # ==========================================
    # Cleanup
    # ==========================================

    def release(self):
        """Release all resources."""
        logger.info("Releasing VideoManager resources")
        self.stop()
        self._config.save_if_dirty()
        self._backend.release()
        self._current_source = None
        self._set_state(PlaybackState.IDLE)

    def __del__(self):
        try:
            self.release()
        except Exception:
            pass


# ==========================================
# Convenience Functions
# ==========================================

def create_video_manager(config_path: Optional[str] = None) -> VideoManager:
    """
    Factory function to create a VideoManager instance.
    
    Args:
        config_path: Optional path to config file
    """
    if config_path:
        config = get_config(config_path)
        return VideoManager(config)
    return VideoManager()
import vlc
from typing import Optional, List, Tuple


class AniVishBackend:
    """
    Core backend wrapper for VLC media playback.
    Exposes a clean API for playback controls, audio management, and media handling.
    """

    def __init__(self):
        # Create VLC instance with default args
        self.instance = vlc.Instance()
        # Create main media player
        self.player = self.instance.media_player_new()
        # Track mute state (VLC doesn't have a simple toggle)
        self._muted = False
        self._pre_mute_volume = 100

    # ==========================================
    # Media Loading
    # ==========================================

    def set_media(self, path: str) -> bool:
        """
        Load a media file into the VLC player.
        
        Args:
            path: File path or URL to the media
            
        Returns:
            True if media was loaded successfully
        """
        try:
            media = self.instance.media_new(path)
            if media is None:
                return False
            self.player.set_media(media)
            return True
        except Exception:
            return False

    def get_media_info(self) -> Optional[dict]:
        """
        Get information about the currently loaded media.
        
        Returns:
            Dictionary with media info or None if no media loaded
        """
        media = self.player.get_media()
        if media is None:
            return None
        
        media.parse()
        return {
            "mrl": media.get_mrl(),
            "duration_ms": media.get_duration(),
            "state": str(self.player.get_state()),
        }

    # ==========================================
    # Playback Controls API
    # ==========================================

    def play(self) -> int:
        """
        Start or resume playback.
        
        Returns:
            0 on success, -1 on error
        """
        return self.player.play()

    def pause(self):
        """Toggle pause state."""
        self.player.pause()

    def stop(self):
        """Stop playback completely."""
        self.player.stop()

    def seek(self, position_ms: int):
        """
        Seek to a specific position in milliseconds.
        
        Args:
            position_ms: Target position in milliseconds
        """
        self.player.set_time(position_ms)

    def seek_relative(self, offset_ms: int):
        """
        Seek relative to current position.
        
        Args:
            offset_ms: Offset in milliseconds (positive = forward, negative = backward)
        """
        current = self.get_current_time()
        if current >= 0:
            new_pos = max(0, current + offset_ms)
            total = self.get_total_duration()
            if total > 0:
                new_pos = min(new_pos, total)
            self.seek(new_pos)

    def get_current_time(self) -> int:
        """
        Get current playback position in milliseconds.
        
        Returns:
            Current time in ms, or -1 if not available
        """
        return self.player.get_time()

    def get_total_duration(self) -> int:
        """
        Get total duration of current media in milliseconds.
        
        Returns:
            Duration in ms, or -1 if not available
        """
        return self.player.get_length()

    def set_position(self, value: float):
        """
        Set playback position as a fraction (0.0 to 1.0).
        
        Args:
            value: Position fraction (0.0 = start, 1.0 = end)
        """
        self.player.set_position(max(0.0, min(1.0, value)))

    def get_position(self) -> float:
        """
        Get current playback position as a fraction.
        
        Returns:
            Position fraction (0.0 to 1.0), or -1 if not available
        """
        return self.player.get_position()

    def set_playback_speed(self, rate: float):
        """
        Set playback speed/rate.
        
        Args:
            rate: Playback rate (1.0 = normal, 0.5 = half speed, 2.0 = double speed)
        """
        self.player.set_rate(max(0.25, min(4.0, rate)))

    def get_playback_speed(self) -> float:
        """
        Get current playback speed/rate.
        
        Returns:
            Current playback rate
        """
        return self.player.get_rate()

    def is_playing(self) -> bool:
        """Check if media is currently playing."""
        return bool(self.player.is_playing())

    def get_state(self) -> str:
        """
        Get current player state.
        
        Returns:
            State string: 'playing', 'paused', 'stopped', 'ended', 'error', or 'unknown'
        """
        state = self.player.get_state()
        state_map = {
            vlc.State.Playing: "playing",
            vlc.State.Paused: "paused",
            vlc.State.Stopped: "stopped",
            vlc.State.Ended: "ended",
            vlc.State.Error: "error",
            vlc.State.Opening: "opening",
            vlc.State.Buffering: "buffering",
            vlc.State.NothingSpecial: "idle",
        }
        return state_map.get(state, "unknown")

    # ==========================================
    # Audio Subsystem
    # ==========================================

    def set_volume(self, vol: int):
        """
        Set volume level.
        
        Args:
            vol: Volume level (0-100)
        """
        vol = max(0, min(100, vol))
        self.player.audio_set_volume(vol)
        if vol > 0:
            self._muted = False

    def get_volume(self) -> int:
        """
        Get current volume level.
        
        Returns:
            Volume level (0-100)
        """
        return self.player.audio_get_volume()

    def mute(self):
        """Mute audio (preserves volume level for unmute)."""
        if not self._muted:
            self._pre_mute_volume = self.get_volume()
            self.player.audio_set_volume(0)
            self._muted = True

    def unmute(self):
        """Unmute audio (restores previous volume level)."""
        if self._muted:
            self.player.audio_set_volume(self._pre_mute_volume)
            self._muted = False

    def toggle_mute(self):
        """Toggle mute state."""
        if self._muted:
            self.unmute()
        else:
            self.mute()

    def is_muted(self) -> bool:
        """Check if audio is muted."""
        return self._muted

    def get_audio_tracks(self) -> List[Tuple[int, str]]:
        """
        Get list of available audio tracks.
        
        Returns:
            List of (track_id, track_name) tuples
        """
        tracks = []
        track_desc = self.player.audio_get_track_description()
        if track_desc:
            for track in track_desc:
                tracks.append((track[0], track[1].decode('utf-8') if isinstance(track[1], bytes) else track[1]))
        return tracks

    def get_current_audio_track(self) -> int:
        """
        Get currently selected audio track ID.
        
        Returns:
            Track ID, or -1 if none selected
        """
        return self.player.audio_get_track()

    def set_audio_track(self, track_id: int) -> bool:
        """
        Select an audio track by ID.
        
        Args:
            track_id: The track ID to select (from get_audio_tracks)
            
        Returns:
            True if successful
        """
        return self.player.audio_set_track(track_id) == 0

    def get_audio_delay(self) -> int:
        """
        Get audio delay in microseconds.
        
        Returns:
            Audio delay in microseconds
        """
        return self.player.audio_get_delay()

    def set_audio_delay(self, delay_us: int):
        """
        Set audio delay for sync adjustment.
        
        Args:
            delay_us: Delay in microseconds (positive = audio delayed)
        """
        self.player.audio_set_delay(delay_us)

    # ==========================================
    # Subtitle Subsystem
    # ==========================================

    def get_subtitle_tracks(self) -> List[Tuple[int, str]]:
        """
        Get list of available subtitle tracks.
        
        Returns:
            List of (track_id, track_name) tuples
        """
        tracks = []
        track_desc = self.player.video_get_spu_description()
        if track_desc:
            for track in track_desc:
                name = track[1].decode('utf-8') if isinstance(track[1], bytes) else track[1]
                tracks.append((track[0], name))
        return tracks

    def get_current_subtitle_track(self) -> int:
        """
        Get currently selected subtitle track ID.
        
        Returns:
            Track ID, or -1 if disabled
        """
        return self.player.video_get_spu()

    def set_subtitle_track(self, track_id: int) -> bool:
        """
        Select a subtitle track by ID.
        
        Args:
            track_id: The track ID to select (-1 to disable)
            
        Returns:
            True if successful
        """
        return self.player.video_set_spu(track_id) == 0

    def load_subtitle_file(self, path: str) -> bool:
        """
        Load external subtitle file.
        
        Args:
            path: Absolute path to subtitle file
            
        Returns:
            True if loaded successfully
        """
        return self.player.video_set_subtitle_file(path)

    def get_subtitle_delay(self) -> int:
        """
        Get subtitle delay in microseconds.
        
        Returns:
            Subtitle delay in microseconds
        """
        return self.player.video_get_spu_delay()

    def set_subtitle_delay(self, delay_us: int):
        """
        Set subtitle delay for sync adjustment.
        
        Args:
            delay_us: Delay in microseconds (positive = subtitles appear later)
        """
        self.player.video_set_spu_delay(delay_us)

    # ==========================================
    # Video Output (for future UI integration)
    # ==========================================

    def set_hwnd(self, handle):
        """
        Set window handle for video output (Windows).
        
        Args:
            handle: Window handle (HWND)
        """
        self.player.set_hwnd(handle)

    def set_xwindow(self, xid: int):
        """
        Set X window ID for video output (Linux).
        
        Args:
            xid: X11 window ID
        """
        self.player.set_xwindow(xid)

    def set_nsobject(self, nsobj):
        """
        Set NSObject for video output (macOS).
        
        Args:
            nsobj: NSView or NSOpenGLView
        """
        self.player.set_nsobject(nsobj)

    # ==========================================
    # Event Handling (for UI callbacks)
    # ==========================================

    def get_event_manager(self):
        """
        Get VLC event manager for attaching callbacks.
        
        Returns:
            VLC EventManager instance
        """
        return self.player.event_manager()

    def on_event(self, event_type, callback):
        """
        Attach a callback to a VLC event.
        
        Args:
            event_type: vlc.EventType (e.g., vlc.EventType.MediaPlayerTimeChanged)
            callback: Function to call when event fires
        """
        em = self.get_event_manager()
        em.event_attach(event_type, callback)

    def detach_event(self, event_type, callback):
        """
        Detach a callback from a VLC event.
        
        Args:
            event_type: vlc.EventType
            callback: Previously attached callback function
        """
        em = self.get_event_manager()
        em.event_detach(event_type, callback)

    # ==========================================
    # Cleanup
    # ==========================================

    def release(self):
        """Release VLC resources. Call when done with the player."""
        self.stop()
        self.player.release()
        self.instance.release()

    def __del__(self):
        """Destructor - ensure resources are released."""
        try:
            self.release()
        except Exception:
            pass
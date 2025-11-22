"""
AniVish CLI Test Harness
Comprehensive testing of all core features before GUI implementation.
"""

import sys
import os

# Initialize logging first
from core.logger import configure_logging, get_logger
configure_logging(level="DEBUG", log_to_file=True, console_output=True)
logger = get_logger("main")

from core.videomanager import VideoManager, PlaybackState, MediaType
from core.config_loader import get_config


def format_time(ms: int) -> str:
    """Convert milliseconds to HH:MM:SS format."""
    if ms < 0:
        return "--:--:--"
    seconds = ms // 1000
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def print_status(vm: VideoManager):
    """Print current playback status."""
    state = vm.get_state().name
    current = vm.get_current_time()
    total = vm.get_total_duration()
    volume = vm.get_volume()
    speed = vm.get_playback_speed()
    muted = vm.is_muted()
    
    mute_str = " [MUTED]" if muted else ""
    print(f"  State: {state} | Time: {format_time(current)} / {format_time(total)} | "
          f"Vol: {volume}%{mute_str} | Speed: {speed:.2f}x")


def print_media_info(vm: VideoManager):
    """Print comprehensive media information."""
    info = vm.get_media_info()
    if info:
        print("\n  === Media Info ===")
        print(f"  Source: {info.get('source', 'Unknown')}")
        print(f"  Type: {info.get('media_type', 'Unknown')}")
        print(f"  Duration: {format_time(info.get('duration_ms', -1))}")
        print(f"  Resolution: {info.get('video_width', 0)}x{info.get('video_height', 0)}")
        
        # Audio tracks
        audio_tracks = vm.get_audio_tracks()
        current_audio = vm.get_current_audio_track()
        print(f"  Audio Tracks: {len(audio_tracks)} (current: {current_audio})")
        
        # Subtitle tracks
        sub_tracks = vm.get_subtitle_tracks()
        current_sub = vm.get_current_subtitle_track()
        print(f"  Subtitle Tracks: {len(sub_tracks)} (current: {current_sub})")
        print()


def print_help():
    """Print available commands."""
    print("""
================================================================================
                            AniVish CLI Test Harness
================================================================================

  PLAYBACK CONTROLS
    p           Toggle play/pause
    s           Stop playback
    <  >        Seek -/+ 10 seconds
    << >>       Seek -/+ 60 seconds
    g <ms>      Go to specific position (milliseconds)
    g% <0-100>  Go to percentage position

  AUDIO CONTROLS
    + -         Volume up/down 5%
    v <0-100>   Set specific volume
    m           Toggle mute
    a           List audio tracks
    a <id>      Select audio track
    ad <ms>     Set audio delay (milliseconds)

  SUBTITLE CONTROLS
    t           List subtitle tracks
    t <id>      Select subtitle track (-1 to disable)
    t off       Disable subtitles
    tl <path>   Load external subtitle file
    td <ms>     Set subtitle delay (milliseconds)

  SPEED CONTROLS
    f           Faster (+0.25x)
    d           Slower (-0.25x)
    sp <rate>   Set specific speed (0.25-4.0)
    r           Reset speed to 1.0x

  INFO & CONFIG
    i           Show playback status
    info        Show detailed media info
    cfg         Show current config values
    recent      Show recent files list

  FILE OPERATIONS
    o <path>    Open new file/URL
    
  OTHER
    h           Show this help
    q           Quit

================================================================================
""")


def print_config(vm: VideoManager):
    """Print current configuration values."""
    cfg = vm.get_config()
    print("\n  === Current Configuration ===")
    print(f"  Config file: {cfg.get_config_path()}")
    print("\n  [Playback]")
    print(f"    Default Volume: {cfg.playback.default_volume}")
    print(f"    Default Speed: {cfg.playback.default_speed}")
    print(f"    Skip Short: {cfg.playback.skip_interval_short}ms")
    print(f"    Skip Long: {cfg.playback.skip_interval_long}ms")
    print(f"    Resume Playback: {cfg.playback.resume_playback}")
    print("\n  [Audio]")
    print(f"    Audio Delay: {cfg.audio.audio_delay_ms}ms")
    print("\n  [Subtitle]")
    print(f"    Enabled: {cfg.subtitle.enabled}")
    print(f"    Delay: {cfg.subtitle.subtitle_delay_ms}ms")
    print("\n  [Logging]")
    print(f"    Level: {cfg.logging.level}")
    print(f"    Log to File: {cfg.logging.log_to_file}")
    print()


def print_recent_files(vm: VideoManager):
    """Print recent files list."""
    recent = vm.get_recent_files()
    print("\n  === Recent Files ===")
    if recent:
        for i, path in enumerate(recent, 1):
            print(f"  {i}. {path}")
    else:
        print("  (no recent files)")
    print()


def handle_command(vm: VideoManager, command: str) -> bool:
    """
    Handle a command. Returns False if should quit.
    """
    parts = command.split(maxsplit=1)
    cmd = parts[0]
    arg = parts[1] if len(parts) > 1 else None
    
    # ==================== PLAYBACK ====================
    if cmd == "p":
        if vm.get_state() == PlaybackState.PLAYING:
            vm.pause()
            print("Paused")
        else:
            vm.play()
            print("Playing")
    
    elif cmd == "s":
        vm.stop()
        print("Stopped")
    
    elif cmd == "<":
        vm.skip_backward()
        print(f"Seek -10s")
        print_status(vm)
    
    elif cmd == ">":
        vm.skip_forward()
        print(f"Seek +10s")
        print_status(vm)
    
    elif cmd == "<<":
        vm.skip_backward_long()
        print(f"Seek -60s")
        print_status(vm)
    
    elif cmd == ">>":
        vm.skip_forward_long()
        print(f"Seek +60s")
        print_status(vm)
    
    elif cmd == "g" and arg:
        try:
            pos_ms = int(arg)
            vm.seek(pos_ms)
            print(f"Seek to {format_time(pos_ms)}")
            print_status(vm)
        except ValueError:
            print("Usage: g <milliseconds>")
    
    elif cmd == "g%" and arg:
        try:
            percent = float(arg)
            vm.seek_percent(percent)
            print(f"Seek to {percent:.1f}%")
            print_status(vm)
        except ValueError:
            print("Usage: g% <0-100>")
    
    # ==================== AUDIO ====================
    elif cmd == "+":
        new_vol = min(100, vm.get_volume() + 5)
        vm.set_volume(new_vol)
        print(f"Volume: {new_vol}%")
    
    elif cmd == "-":
        new_vol = max(0, vm.get_volume() - 5)
        vm.set_volume(new_vol)
        print(f"Volume: {new_vol}%")
    
    elif cmd == "v" and arg:
        try:
            vol = int(arg)
            vm.set_volume(vol)
            print(f"Volume: {vm.get_volume()}%")
        except ValueError:
            print("Usage: v <0-100>")
    
    elif cmd == "m":
        vm.toggle_mute()
        if vm.is_muted():
            print("Muted")
        else:
            print(f"Unmuted (Volume: {vm.get_volume()}%)")
    
    elif cmd == "a" and not arg:
        tracks = vm.get_audio_tracks()
        current = vm.get_current_audio_track()
        print("\n  Audio Tracks:")
        if tracks:
            for tid, tname in tracks:
                marker = " <-- current" if tid == current else ""
                print(f"    [{tid}] {tname}{marker}")
        else:
            print("    (none available)")
        print()
    
    elif cmd == "a" and arg:
        try:
            track_id = int(arg)
            if vm.set_audio_track(track_id):
                print(f"Audio track set to {track_id}")
            else:
                print("Failed to set audio track")
        except ValueError:
            print("Usage: a <track_id>")
    
    elif cmd == "ad" and arg:
        try:
            delay = int(arg)
            vm.set_audio_delay(delay)
            print(f"Audio delay: {delay}ms")
        except ValueError:
            print("Usage: ad <milliseconds>")
    
    # ==================== SUBTITLES ====================
    elif cmd == "t" and not arg:
        tracks = vm.get_subtitle_tracks()
        current = vm.get_current_subtitle_track()
        print("\n  Subtitle Tracks:")
        if tracks:
            for tid, tname in tracks:
                marker = " <-- current" if tid == current else ""
                print(f"    [{tid}] {tname}{marker}")
        else:
            print("    (none available)")
        print(f"  Current: {current} (-1 = disabled)")
        print()
    
    elif cmd == "t" and arg:
        if arg == "off":
            vm.disable_subtitles()
            print("Subtitles disabled")
        else:
            try:
                track_id = int(arg)
                if vm.set_subtitle_track(track_id):
                    print(f"Subtitle track set to {track_id}")
                else:
                    print("Failed to set subtitle track")
            except ValueError:
                print("Usage: t <track_id> or t off")
    
    elif cmd == "tl" and arg:
        path = arg.strip().strip('"').strip("'")
        if vm.load_subtitle_file(path):
            print(f"Subtitle loaded: {path}")
        else:
            print(f"Failed to load subtitle: {path}")
    
    elif cmd == "td" and arg:
        try:
            delay = int(arg)
            vm.set_subtitle_delay(delay)
            print(f"Subtitle delay: {delay}ms")
        except ValueError:
            print("Usage: td <milliseconds>")
    
    # ==================== SPEED ====================
    elif cmd == "f":
        new_speed = min(4.0, vm.get_playback_speed() + 0.25)
        vm.set_playback_speed(new_speed)
        print(f"Speed: {new_speed:.2f}x")
    
    elif cmd == "d":
        new_speed = max(0.25, vm.get_playback_speed() - 0.25)
        vm.set_playback_speed(new_speed)
        print(f"Speed: {new_speed:.2f}x")
    
    elif cmd == "sp" and arg:
        try:
            rate = float(arg)
            vm.set_playback_speed(rate)
            print(f"Speed: {vm.get_playback_speed():.2f}x")
        except ValueError:
            print("Usage: sp <0.25-4.0>")
    
    elif cmd == "r":
        vm.set_playback_speed(1.0)
        print("Speed reset to 1.0x")
    
    # ==================== INFO & CONFIG ====================
    elif cmd == "i":
        print_status(vm)
    
    elif cmd == "info":
        print_media_info(vm)
    
    elif cmd == "cfg":
        print_config(vm)
    
    elif cmd == "recent":
        print_recent_files(vm)
    
    # ==================== FILE OPERATIONS ====================
    elif cmd == "o" and arg:
        path = arg.strip().strip('"').strip("'")
        try:
            vm.stop()
            vm.load(path)
            print(f"Loaded: {path}")
            vm.play()
            print("Playing...")
        except Exception as e:
            print(f"Error: {e}")
    
    # ==================== OTHER ====================
    elif cmd == "h":
        print_help()
    
    elif cmd == "q":
        return False
    
    else:
        print(f"Unknown command: '{command}' (type 'h' for help)")
    
    return True


def setup_event_handlers(vm: VideoManager):
    """Setup event handlers for testing."""
    
    def on_ended():
        print("\n[EVENT] Playback ended")
        print(">> ", end="", flush=True)
    
    def on_error(error):
        print(f"\n[EVENT] Error: {error}")
        print(">> ", end="", flush=True)
    
    def on_state_changed(old_state, new_state):
        logger.debug(f"State: {old_state.name} -> {new_state.name}")
    
    def on_buffering(percent):
        if percent < 100:
            logger.debug(f"Buffering: {percent}%")
    
    vm.on('on_ended', on_ended)
    vm.on('on_error', on_error)
    vm.on('on_state_changed', on_state_changed)
    vm.on('on_buffering', on_buffering)


def main():
    print("=" * 60)
    print("           AniVish Video Player - CLI Test Harness")
    print("=" * 60)
    
    logger.info("Starting AniVish CLI Test")
    
    # Initialize VideoManager
    vm = VideoManager()
    
    # Setup event handlers
    setup_event_handlers(vm)
    
    # Get video path
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Show recent files if available
        recent = vm.get_recent_files()
        if recent:
            print("\nRecent files:")
            for i, path in enumerate(recent[:5], 1):
                print(f"  {i}. {os.path.basename(path)}")
            print()
        
        video_path = input("Enter path to video (or URL): ").strip()
        video_path = video_path.strip('"').strip("'")
    
    # Load media
    try:
        vm.load(video_path)
        logger.info(f"Loaded: {video_path}")
    except Exception as e:
        print(f"Error loading media: {e}")
        logger.error(f"Failed to load: {e}")
        vm.release()
        return
    
    # Print initial info
    print(f"\nLoaded: {os.path.basename(video_path)}")
    print_media_info(vm)
    
    # Start playback
    print("Starting playback...")
    vm.play()
    
    print("\nType 'h' for help, 'q' to quit\n")
    
    # Main command loop
    while True:
        try:
            command = input(">> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nQuitting...")
            break
        
        if not command:
            continue
        
        if not handle_command(vm, command):
            break
    
    # Cleanup
    logger.info("Shutting down")
    vm.release()
    print("Goodbye!")


if __name__ == "__main__":
    main()
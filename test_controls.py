import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.logger import configure_logging, get_logger
from core.videomanager import VideoManager

# Enable DEBUG logging
configure_logging(level="DEBUG", log_to_file=True, console_output=True)
logger = get_logger("test")

def test_video_manager():
    """Test VideoManager directly without GUI"""
    print("\n" + "=" * 60)
    print("TESTING VIDEO MANAGER")
    print("=" * 60)
    
    # Create video manager
    vm = VideoManager()
    
    # Test event registration
    events_received = []
    
    def on_playing():
        events_received.append('playing')
        print("✓ EVENT: playing")
    
    def on_paused():
        events_received.append('paused')
        print("✓ EVENT: paused")
    
    def on_stopped():
        events_received.append('stopped')
        print("✓ EVENT: stopped")
    
    def on_time_changed(time_ms):
        if len(events_received) < 10:  # Only print first few
            print(f"✓ EVENT: time_changed - {time_ms}ms")
    
    def on_state_changed(old, new):
        events_received.append(f'state:{new.name}')
        print(f"✓ EVENT: state_changed - {old.name} -> {new.name}")
    
    # Register events
    vm.on('on_playing', on_playing)
    vm.on('on_paused', on_paused)
    vm.on('on_stopped', on_stopped)
    vm.on('on_time_changed', on_time_changed)
    vm.on('on_state_changed', on_state_changed)
    
    print("\n✓ Events registered")
    
    # Get test video path
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = input("Enter path to test video file: ").strip().strip('"').strip("'")
    
    if not video_path:
        print("❌ No video path provided")
        return
    
    print(f"\n📹 Loading: {video_path}")
    
    # Load media
    try:
        vm.load(video_path)
        print("✓ Media loaded")
    except Exception as e:
        print(f"❌ Failed to load: {e}")
        return
    
    # Check duration
    duration = vm.get_total_duration()
    print(f"✓ Duration: {duration}ms ({duration/1000:.1f} seconds)")
    
    if duration <= 0:
        print("❌ WARNING: Duration is 0 or negative!")
        print("   This might indicate the media hasn't fully loaded yet")
        import time
        print("   Waiting 2 seconds...")
        time.sleep(2)
        duration = vm.get_total_duration()
        print(f"   Duration after wait: {duration}ms")
    
    # Test play
    print("\n▶ Testing PLAY...")
    result = vm.play()
    print(f"✓ Play result: {result}")
    
    import time
    time.sleep(2)
    
    # Check if playing
    is_playing = vm.is_playing()
    print(f"✓ Is playing: {is_playing}")
    
    # Get current time
    current = vm.get_current_time()
    print(f"✓ Current time: {current}ms")
    
    # Test pause
    print("\n⏸ Testing PAUSE...")
    vm.pause()
    time.sleep(1)
    is_playing = vm.is_playing()
    print(f"✓ Is playing after pause: {is_playing}")
    
    # Test seek
    print("\n⏭ Testing SEEK to 5000ms...")
    vm.seek(5000)
    time.sleep(1)
    current = vm.get_current_time()
    print(f"✓ Current time after seek: {current}ms")
    
    # Test volume
    print("\n🔊 Testing VOLUME...")
    vm.set_volume(50)
    vol = vm.get_volume()
    print(f"✓ Volume set to: {vol}")
    
    # Test toggle play/pause
    print("\n⏯ Testing TOGGLE PLAY/PAUSE...")
    vm.toggle_play_pause()
    time.sleep(1)
    is_playing = vm.is_playing()
    print(f"✓ Is playing after toggle: {is_playing}")
    
    # Stop
    print("\n■ Testing STOP...")
    vm.stop()
    time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Events received: {len(events_received)}")
    print(f"Event types: {set(events_received)}")
    
    if 'playing' in events_received:
        print("✓ Playing event received")
    else:
        print("❌ Playing event NOT received")
    
    if 'paused' in events_received:
        print("✓ Paused event received")
    else:
        print("❌ Paused event NOT received")
    
    if 'stopped' in events_received:
        print("✓ Stopped event received")
    else:
        print("❌ Stopped event NOT received")
    
    # Cleanup
    vm.release()
    print("\n✓ Test complete")


if __name__ == "__main__":
    test_video_manager()
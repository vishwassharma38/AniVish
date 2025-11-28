import json
from pathlib import Path
from typing import Dict, Callable

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QEvent, QObject
from PyQt5.QtGui import QKeySequence

from core.videomanager import VideoManager
from core.logger import get_logger

logger = get_logger("keybindings")


class KeybindingManager(QObject):
    """
    Manages keyboard shortcuts with JSON configuration support.
    Inherits from QObject to work as an event filter.
    """
    
    DEFAULT_KEYBINDINGS = {
        "Space": "toggle_play_pause",
        "K": "toggle_play_pause",
        "P": "toggle_play_pause",
        "S": "stop",
        "Left": "seek_backward",
        "Right": "seek_forward",
        "Shift+Left": "seek_backward_long",
        "Shift+Right": "seek_forward_long",
        "Up": "volume_up",
        "Down": "volume_down",
        "M": "toggle_mute",
        "F": "toggle_fullscreen",
        "Escape": "exit_fullscreen",
        "Ctrl+O": "open_file",
        "Ctrl+U": "open_url",
        "Ctrl+L": "open_url",
        "Ctrl+R": "show_recent",
        "Ctrl+,": "show_settings",
        "Ctrl+Q": "quit",
        "Ctrl+W": "quit",
        "J": "subtitle_delay_decrease",
        "L": "subtitle_delay_increase",
        "H": "audio_delay_decrease",
        ";": "audio_delay_increase",
        "[": "speed_decrease",
        "]": "speed_increase",
        "=": "speed_reset",
    }
    
    def __init__(self, window: QWidget, video_manager: VideoManager):
        super().__init__(window)  # Initialize QObject with parent
        
        self.window = window
        self.video_manager = video_manager
        self.keybindings: Dict[str, str] = {}
        self.actions: Dict[str, Callable] = {}
        
        self._setup_actions()
        self._install_event_filter()
    
    def _setup_actions(self):
        """Map action names to callables"""
        vm = self.video_manager
        
        self.actions = {
            # Playback
            "toggle_play_pause": vm.toggle_play_pause,
            "stop": vm.stop,
            "seek_backward": vm.skip_backward,
            "seek_forward": vm.skip_forward,
            "seek_backward_long": vm.skip_backward_long,
            "seek_forward_long": vm.skip_forward_long,
            
            # Audio
            "volume_up": lambda: vm.set_volume(min(100, vm.get_volume() + 5)),
            "volume_down": lambda: vm.set_volume(max(0, vm.get_volume() - 5)),
            "toggle_mute": vm.toggle_mute,
            
            # Speed
            "speed_decrease": lambda: vm.set_playback_speed(
                max(0.25, vm.get_playback_speed() - 0.25)
            ),
            "speed_increase": lambda: vm.set_playback_speed(
                min(4.0, vm.get_playback_speed() + 0.25)
            ),
            "speed_reset": lambda: vm.set_playback_speed(1.0),
            
            # Sync adjustments
            "subtitle_delay_increase": lambda: vm.set_subtitle_delay(
                vm.get_subtitle_delay() + 100
            ),
            "subtitle_delay_decrease": lambda: vm.set_subtitle_delay(
                vm.get_subtitle_delay() - 100
            ),
            "audio_delay_increase": lambda: vm.set_audio_delay(
                vm.get_audio_delay() + 100
            ),
            "audio_delay_decrease": lambda: vm.set_audio_delay(
                vm.get_audio_delay() - 100
            ),
            
            # Window actions (handled by app)
            "toggle_fullscreen": lambda: None,  # Will be overridden
            "exit_fullscreen": lambda: None,
            "open_file": lambda: None,
            "open_url": lambda: None,
            "show_recent": lambda: None,
            "show_settings": lambda: None,
            "quit": lambda: None,
        }
    
    def load_keybindings(self, config_path: Path = None):
        """Load keybindings from JSON or use defaults"""
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    self.keybindings = json.load(f)
                logger.info(f"Loaded keybindings from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load keybindings: {e}")
                self.keybindings = self.DEFAULT_KEYBINDINGS.copy()
        else:
            self.keybindings = self.DEFAULT_KEYBINDINGS.copy()
            logger.info("Using default keybindings")
    
    def save_keybindings(self, config_path: Path):
        """Save current keybindings to JSON"""
        try:
            with open(config_path, 'w') as f:
                json.dump(self.keybindings, f, indent=2)
            logger.info(f"Saved keybindings to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save keybindings: {e}")
    
    def _install_event_filter(self):
        """Install event filter to intercept key presses"""
        self.window.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Event filter to handle key presses"""
        if event.type() == QEvent.KeyPress:
            key_sequence = self._event_to_string(event)
            
            if key_sequence in self.keybindings:
                action_name = self.keybindings[key_sequence]
                if action_name in self.actions:
                    try:
                        self.actions[action_name]()
                    except Exception as e:
                        logger.error(f"Error executing action '{action_name}': {e}")
                    return True  # Event handled
        
        return super().eventFilter(obj, event)  # Pass to base class
    
    def _event_to_string(self, event) -> str:
        """Convert QKeyEvent to string representation"""
        modifiers = []
        if event.modifiers() & Qt.ControlModifier:
            modifiers.append("Ctrl")
        if event.modifiers() & Qt.ShiftModifier:
            modifiers.append("Shift")
        if event.modifiers() & Qt.AltModifier:
            modifiers.append("Alt")
        
        key = QKeySequence(event.key()).toString()
        
        if modifiers:
            return "+".join(modifiers + [key])
        return key
    
    def register_action(self, action_name: str, callback: Callable):
        """Register or override an action callback"""
        self.actions[action_name] = callback
        logger.debug(f"Registered action: {action_name}")
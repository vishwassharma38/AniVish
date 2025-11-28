from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider,
    QLabel, QStyle, QApplication, QToolButton
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QColor

from core.videomanager import VideoManager, PlaybackState
from core.logger import get_logger

logger = get_logger("control_bar")


class TimeLabel(QLabel):
    """Custom label for displaying time with consistent formatting"""
    
    def __init__(self, text="00:00:00", parent=None):
        super().__init__(text, parent)
        self.setMinimumWidth(70)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                background: rgba(0, 0, 0, 80);
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)


class GlassButton(QPushButton):
    """Glass-styled button with glow effect"""
    
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, parent)
        
        if icon:
            self.setIcon(icon)
        
        self.setMinimumSize(40, 40)
        self.setMaximumSize(50, 50)
        self.setCursor(Qt.PointingHandCursor)
        
        self._apply_style()
    
    def _apply_style(self):
        """Apply glass button styling"""
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(80, 120, 200, 150),
                    stop:1 rgba(50, 80, 150, 180)
                );
                border: 1px solid rgba(150, 180, 255, 100);
                border-radius: 20px;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(100, 140, 220, 180),
                    stop:1 rgba(70, 100, 170, 200)
                );
                border: 1px solid rgba(180, 200, 255, 150);
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 100, 180, 200),
                    stop:1 rgba(40, 70, 140, 220)
                );
            }
            QPushButton:disabled {
                background: rgba(50, 50, 50, 100);
                border: 1px solid rgba(100, 100, 100, 80);
                color: rgba(150, 150, 150, 100);
            }
        """)


class SeekSlider(QSlider):
    """Custom seek slider with glass styling"""
    
    # Signal emitted when user seeks (not during playback updates)
    seek_requested = pyqtSignal(int)  # milliseconds
    
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        
        self.setMinimum(0)
        self.setMaximum(1000)
        self.setValue(0)
        
        self._updating = False  # Prevent feedback loops
        self._user_seeking = False
        
        self.sliderPressed.connect(self._on_pressed)
        self.sliderReleased.connect(self._on_released)
        self.valueChanged.connect(self._on_value_changed)
        
        self._apply_style()
    
    def _apply_style(self):
        """Apply glass slider styling"""
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(50, 50, 50, 150);
                height: 8px;
                border-radius: 4px;
                border: 1px solid rgba(100, 100, 100, 100);
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(80, 150, 255, 200),
                    stop:1 rgba(100, 180, 255, 220)
                );
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(150, 200, 255, 255),
                    stop:1 rgba(100, 150, 255, 255)
                );
                border: 2px solid rgba(200, 220, 255, 255);
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(180, 220, 255, 255),
                    stop:1 rgba(120, 170, 255, 255)
                );
                border: 2px solid rgba(220, 240, 255, 255);
            }
        """)
    
    def _on_pressed(self):
        """User started dragging"""
        self._user_seeking = True
    
    def _on_released(self):
        """User finished dragging - emit seek request"""
        self._user_seeking = False
        # Convert slider position (0-1000) to milliseconds
        position_ms = int((self.value() / 1000.0) * self._total_duration_ms) if hasattr(self, '_total_duration_ms') else 0
        self.seek_requested.emit(position_ms)
    
    def _on_value_changed(self, value):
        """Value changed (could be user or programmatic)"""
        if self._user_seeking:
            # User is dragging - show preview if desired
            pass
    
    def update_position(self, current_ms: int, total_ms: int):
        """Update slider position from video manager (not user interaction)"""
        if self._user_seeking or self._updating:
            return  # Don't update while user is seeking
        
        self._updating = True
        self._total_duration_ms = total_ms
        
        if total_ms > 0:
            position = int((current_ms / total_ms) * 1000)
            self.setValue(position)
        else:
            self.setValue(0)
        
        self._updating = False


class VolumeSlider(QSlider):
    """Custom volume slider with glass styling"""
    
    volume_changed = pyqtSignal(int)  # 0-100
    
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(100)
        self.setMaximumWidth(100)
        
        self.valueChanged.connect(lambda v: self.volume_changed.emit(v))
        
        self._apply_style()
    
    def _apply_style(self):
        """Apply glass slider styling"""
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(50, 50, 50, 150);
                height: 6px;
                border-radius: 3px;
                border: 1px solid rgba(100, 100, 100, 100);
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(100, 200, 100, 200),
                    stop:1 rgba(120, 220, 120, 220)
                );
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: rgba(150, 255, 150, 255);
                border: 2px solid rgba(200, 255, 200, 255);
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)


class ControlBar(QWidget):
    """
    Main control bar with all playback controls.
    Features glass theme and connects directly to VideoManager.
    """
    
    # Signals
    open_file_clicked = pyqtSignal()
    open_url_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    playlist_clicked = pyqtSignal()
    fullscreen_clicked = pyqtSignal()
    
    def __init__(self, video_manager: VideoManager, parent=None):
        super().__init__(parent)
        
        self.video_manager = video_manager
        
        # Update timer for time display
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_time_display)
        self.update_timer.setInterval(100)  # 100ms updates
        
        self._init_ui()
        self._connect_signals()
        self._connect_video_manager()
        
        logger.info("Control bar initialized")
    
    def _init_ui(self):
        """Initialize UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(8)
        
        # Seek slider section
        seek_layout = QHBoxLayout()
        
        self.time_current = TimeLabel("00:00:00")
        seek_layout.addWidget(self.time_current)
        
        self.seek_slider = SeekSlider()
        seek_layout.addWidget(self.seek_slider, 1)
        
        self.time_total = TimeLabel("00:00:00")
        seek_layout.addWidget(self.time_total)
        
        main_layout.addLayout(seek_layout)
        
        # Control buttons section
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        # Playback buttons
        self.btn_play_pause = GlassButton("▶")
        self.btn_play_pause.setToolTip("Play/Pause (Space)")
        controls_layout.addWidget(self.btn_play_pause)
        
        self.btn_stop = GlassButton("■")
        self.btn_stop.setToolTip("Stop")
        controls_layout.addWidget(self.btn_stop)
        
        controls_layout.addSpacing(10)
        
        # Skip buttons
        self.btn_skip_back = GlassButton("⏪")
        self.btn_skip_back.setToolTip("Skip backward 10s (←)")
        controls_layout.addWidget(self.btn_skip_back)
        
        self.btn_skip_forward = GlassButton("⏩")
        self.btn_skip_forward.setToolTip("Skip forward 10s (→)")
        controls_layout.addWidget(self.btn_skip_forward)
        
        controls_layout.addSpacing(20)
        
        # Volume control
        self.btn_mute = GlassButton("🔊")
        self.btn_mute.setToolTip("Mute (M)")
        controls_layout.addWidget(self.btn_mute)
        
        self.volume_slider = VolumeSlider()
        self.volume_slider.setToolTip("Volume")
        controls_layout.addWidget(self.volume_slider)
        
        controls_layout.addStretch()
        
        # Right-side buttons
        self.btn_playlist = GlassButton("☰")
        self.btn_playlist.setToolTip("Recent files")
        controls_layout.addWidget(self.btn_playlist)
        
        self.btn_settings = GlassButton("⚙")
        self.btn_settings.setToolTip("Settings")
        controls_layout.addWidget(self.btn_settings)
        
        self.btn_fullscreen = GlassButton("⛶")
        self.btn_fullscreen.setToolTip("Fullscreen (F)")
        controls_layout.addWidget(self.btn_fullscreen)
        
        main_layout.addLayout(controls_layout)
        
        # Apply glass styling to container
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(20, 20, 40, 200),
                    stop:1 rgba(15, 15, 30, 220)
                );
                border-radius: 8px;
                border: 1px solid rgba(100, 150, 255, 80);
            }
        """)
    
    def _connect_signals(self):
        """Connect button signals to handlers"""
        self.btn_play_pause.clicked.connect(self._on_play_pause)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_skip_back.clicked.connect(self._on_skip_back)
        self.btn_skip_forward.clicked.connect(self._on_skip_forward)
        self.btn_mute.clicked.connect(self._on_mute)
        self.volume_slider.volume_changed.connect(self._on_volume_changed)
        self.seek_slider.seek_requested.connect(self._on_seek_requested)
        
        self.btn_playlist.clicked.connect(self.playlist_clicked.emit)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        self.btn_fullscreen.clicked.connect(self.fullscreen_clicked.emit)
    
    def _connect_video_manager(self):
        """Connect to video manager events"""
        self.video_manager.on('on_playing', self._on_playing)
        self.video_manager.on('on_paused', self._on_paused)
        self.video_manager.on('on_stopped', self._on_stopped_event)
        self.video_manager.on('on_media_loaded', self._on_media_loaded)
        self.video_manager.on('on_state_changed', self._on_state_changed)
        
        # Set initial volume
        self.volume_slider.setValue(self.video_manager.get_volume())
    
    # ==========================================
    # Button Handlers
    # ==========================================
    
    def _on_play_pause(self):
        """Handle play/pause button"""
        self.video_manager.toggle_play_pause()
    
    def _on_stop(self):
        """Handle stop button"""
        self.video_manager.stop()
    
    def _on_skip_back(self):
        """Handle skip backward"""
        self.video_manager.skip_backward()
    
    def _on_skip_forward(self):
        """Handle skip forward"""
        self.video_manager.skip_forward()
    
    def _on_mute(self):
        """Handle mute toggle"""
        self.video_manager.toggle_mute()
        self._update_mute_button()
    
    def _on_volume_changed(self, volume: int):
        """Handle volume slider change"""
        self.video_manager.set_volume(volume)
        self._update_mute_button()
    
    def _on_seek_requested(self, position_ms: int):
        """Handle seek slider release"""
        self.video_manager.seek(position_ms)
        logger.debug(f"Seek to {position_ms}ms")
    
    # ==========================================
    # Video Manager Event Handlers
    # ==========================================
    
    def _on_playing(self):
        """Called when playback starts"""
        self.btn_play_pause.setText("⏸")
        self.btn_play_pause.setToolTip("Pause (Space)")
        self.update_timer.start()
    
    def _on_paused(self):
        """Called when playback pauses"""
        self.btn_play_pause.setText("▶")
        self.btn_play_pause.setToolTip("Play (Space)")
        self.update_timer.stop()
    
    def _on_stopped_event(self):
        """Called when playback stops"""
        self.btn_play_pause.setText("▶")
        self.update_timer.stop()
        self.seek_slider.setValue(0)
        self.time_current.setText("00:00:00")
    
    def _on_media_loaded(self, source, media_type):
        """Called when media is loaded"""
        total_ms = self.video_manager.get_total_duration()
        self.time_total.setText(self._format_time(total_ms))
        self.seek_slider.setEnabled(total_ms > 0)
    
    def _on_state_changed(self, old_state, new_state):
        """Called when state changes"""
        # Enable/disable controls based on state
        has_media = new_state not in (PlaybackState.IDLE, PlaybackState.ERROR)
        self.btn_play_pause.setEnabled(has_media)
        self.btn_stop.setEnabled(has_media)
        self.btn_skip_back.setEnabled(has_media)
        self.btn_skip_forward.setEnabled(has_media)
    
    # ==========================================
    # UI Updates
    # ==========================================
    
    def _update_time_display(self):
        """Update time labels and seek slider"""
        current_ms = self.video_manager.get_current_time()
        total_ms = self.video_manager.get_total_duration()
        
        self.time_current.setText(self._format_time(current_ms))
        self.seek_slider.update_position(current_ms, total_ms)
    
    def _update_mute_button(self):
        """Update mute button appearance"""
        if self.video_manager.is_muted():
            self.btn_mute.setText("🔇")
            self.btn_mute.setToolTip("Unmute (M)")
        else:
            volume = self.video_manager.get_volume()
            if volume == 0:
                self.btn_mute.setText("🔇")
            elif volume < 50:
                self.btn_mute.setText("🔉")
            else:
                self.btn_mute.setText("🔊")
            self.btn_mute.setToolTip("Mute (M)")
    
    @staticmethod
    def _format_time(ms: int) -> str:
        """Format milliseconds as HH:MM:SS"""
        if ms < 0:
            return "00:00:00"
        seconds = ms // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    # ==========================================
    # Public API
    # ==========================================
    
    def set_enabled(self, enabled: bool):
        """Enable/disable all controls"""
        for child in self.findChildren(QWidget):
            if child != self.btn_settings:  # Keep settings always enabled
                child.setEnabled(enabled)
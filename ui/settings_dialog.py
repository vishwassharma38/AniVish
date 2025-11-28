from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QWidget, QCheckBox, QSpinBox,
    QComboBox, QGroupBox, QFormLayout, QSlider, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.config_loader import ConfigLoader  # FIXED: Changed from ConfigManager
from core.logger import get_logger

logger = get_logger("settings")


class SettingsDialog(QDialog):
    """Glass-themed settings dialog"""
    
    def __init__(self, parent, config: ConfigLoader):  # FIXED: Changed parameter type
        super().__init__(parent)
        
        self.config = config
        self._original_values = {}
        
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        self._init_ui()
        self._apply_style()
        self._load_settings()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self.tabs.addTab(self._create_playback_tab(), "Playback")
        self.tabs.addTab(self._create_audio_tab(), "Audio")
        self.tabs.addTab(self._create_subtitle_tab(), "Subtitles")
        self.tabs.addTab(self._create_interface_tab(), "Interface")
        self.tabs.addTab(self._create_advanced_tab(), "Advanced")
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_apply = QPushButton("Apply")
        self.btn_apply.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.btn_apply)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self._on_ok)
        self.btn_ok.setDefault(True)
        btn_layout.addWidget(self.btn_ok)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        btn_layout.addStretch()
        
        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_reset.clicked.connect(self._on_reset)
        btn_layout.addWidget(self.btn_reset)
        
        layout.addLayout(btn_layout)
    
    def _create_playback_tab(self) -> QWidget:
        """Create playback settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # General playback group
        group = QGroupBox("General")
        form = QFormLayout(group)
        
        self.resume_playback = QCheckBox()
        form.addRow("Resume playback on load:", self.resume_playback)
        
        self.default_volume = QSpinBox()
        self.default_volume.setRange(0, 100)
        self.default_volume.setSuffix("%")
        form.addRow("Default volume:", self.default_volume)
        
        self.default_speed = QComboBox()
        self.default_speed.addItems(["0.25x", "0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        form.addRow("Default playback speed:", self.default_speed)
        
        layout.addWidget(group)
        
        # Skip intervals group
        group2 = QGroupBox("Skip Intervals")
        form2 = QFormLayout(group2)
        
        self.skip_short = QSpinBox()
        self.skip_short.setRange(1, 60)
        self.skip_short.setSuffix(" sec")
        form2.addRow("Short skip (←/→):", self.skip_short)
        
        self.skip_long = QSpinBox()
        self.skip_long.setRange(10, 300)
        self.skip_long.setSuffix(" sec")
        form2.addRow("Long skip (Shift+←/→):", self.skip_long)
        
        layout.addWidget(group2)
        
        layout.addStretch()
        return widget
    
    def _create_audio_tab(self) -> QWidget:
        """Create audio settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Audio Settings")
        form = QFormLayout(group)
        
        self.audio_delay = QSpinBox()
        self.audio_delay.setRange(-5000, 5000)
        self.audio_delay.setSuffix(" ms")
        form.addRow("Audio delay:", self.audio_delay)
        
        self.preferred_audio_lang = QLineEdit()
        self.preferred_audio_lang.setPlaceholderText("e.g., eng, jpn, spa")
        form.addRow("Preferred audio language:", self.preferred_audio_lang)
        
        layout.addWidget(group)
        layout.addStretch()
        return widget
    
    def _create_subtitle_tab(self) -> QWidget:
        """Create subtitle settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Subtitle Settings")
        form = QFormLayout(group)
        
        self.subtitles_enabled = QCheckBox()
        form.addRow("Enable subtitles:", self.subtitles_enabled)
        
        self.subtitle_delay = QSpinBox()
        self.subtitle_delay.setRange(-5000, 5000)
        self.subtitle_delay.setSuffix(" ms")
        form.addRow("Subtitle delay:", self.subtitle_delay)
        
        self.preferred_sub_lang = QLineEdit()
        self.preferred_sub_lang.setPlaceholderText("e.g., eng, jpn, spa")
        form.addRow("Preferred subtitle language:", self.preferred_sub_lang)
        
        self.subtitle_size = QSpinBox()
        self.subtitle_size.setRange(8, 72)
        self.subtitle_size.setSuffix(" pt")
        form.addRow("Subtitle font size:", self.subtitle_size)
        
        layout.addWidget(group)
        layout.addStretch()
        return widget
    
    def _create_interface_tab(self) -> QWidget:
        """Create interface settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Interface Settings")
        form = QFormLayout(group)
        
        self.remember_window_size = QCheckBox()
        form.addRow("Remember window size:", self.remember_window_size)
        
        self.show_osd = QCheckBox()
        form.addRow("Show on-screen display:", self.show_osd)
        
        self.theme = QComboBox()
        self.theme.addItems(["Default Dark", "Light", "Aero Blue", "Custom"])
        form.addRow("Theme:", self.theme)
        
        layout.addWidget(group)
        layout.addStretch()
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Logging group
        group = QGroupBox("Logging")
        form = QFormLayout(group)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        form.addRow("Log level:", self.log_level)
        
        self.log_to_file = QCheckBox()
        form.addRow("Log to file:", self.log_to_file)
        
        layout.addWidget(group)
        
        # Performance group
        group2 = QGroupBox("Performance")
        form2 = QFormLayout(group2)
        
        self.hardware_acceleration = QCheckBox()
        form2.addRow("Hardware acceleration:", self.hardware_acceleration)
        
        self.cache_size = QSpinBox()
        self.cache_size.setRange(100, 10000)
        self.cache_size.setSuffix(" MB")
        form2.addRow("Cache size:", self.cache_size)
        
        layout.addWidget(group2)
        
        layout.addStretch()
        return widget
    
    def _apply_style(self):
        """Apply glass styling"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(20, 20, 40, 230),
                    stop:1 rgba(15, 15, 30, 250)
                );
            }
            QLabel {
                color: #FFFFFF;
            }
            QTabWidget::pane {
                background: rgba(0, 0, 0, 100);
                border: 1px solid rgba(100, 150, 255, 100);
                border-radius: 6px;
            }
            QTabBar::tab {
                background: rgba(50, 50, 80, 150);
                color: #FFFFFF;
                padding: 10px 20px;
                border: 1px solid rgba(100, 150, 255, 80);
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: rgba(80, 120, 200, 180);
            }
            QGroupBox {
                color: #FFFFFF;
                border: 1px solid rgba(100, 150, 255, 80);
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 5px;
            }
            QCheckBox, QRadioButton {
                color: #FFFFFF;
            }
            QSpinBox, QComboBox, QLineEdit {
                background: rgba(0, 0, 0, 150);
                color: #FFFFFF;
                border: 1px solid rgba(100, 150, 255, 100);
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background: rgba(80, 120, 200, 180);
                color: #FFFFFF;
                border: 1px solid rgba(150, 180, 255, 100);
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(100, 140, 220, 200);
            }
            QPushButton:pressed {
                background: rgba(60, 100, 180, 200);
            }
        """)
    
    def _load_settings(self):
        """Load current settings from config"""
        try:
            # Playback
            self.resume_playback.setChecked(self.config.playback.resume_playback)
            self.default_volume.setValue(self.config.playback.default_volume)
            speed_idx = self._speed_to_index(self.config.playback.default_speed)
            self.default_speed.setCurrentIndex(speed_idx)
            self.skip_short.setValue(self.config.playback.skip_interval_short // 1000)
            self.skip_long.setValue(self.config.playback.skip_interval_long // 1000)
            
            # Audio
            self.audio_delay.setValue(self.config.audio.audio_delay_ms)
            self.preferred_audio_lang.setText(self.config.audio.preferred_language)
            
            # Subtitles
            self.subtitles_enabled.setChecked(self.config.subtitle.enabled)
            self.subtitle_delay.setValue(self.config.subtitle.subtitle_delay_ms)
            self.preferred_sub_lang.setText(self.config.subtitle.preferred_language)
            self.subtitle_size.setValue(self.config.subtitle.font_size)
            
            # Interface
            self.remember_window_size.setChecked(True)  # Default
            self.show_osd.setChecked(True)  # Default
            
            # Advanced
            self.log_level.setCurrentText(self.config.logging.level)
            self.log_to_file.setChecked(self.config.logging.log_to_file)
            self.hardware_acceleration.setChecked(True)  # Default
            self.cache_size.setValue(1000)  # Default
            
            # Store original values
            self._store_original_values()
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    def _store_original_values(self):
        """Store original values for comparison"""
        self._original_values = {
            'resume_playback': self.resume_playback.isChecked(),
            'default_volume': self.default_volume.value(),
            'default_speed': self.default_speed.currentIndex(),
        }
    
    def _save_settings(self):
        """Save settings to config"""
        try:
            # Playback
            self.config.set('playback', 'resume_playback', self.resume_playback.isChecked())
            self.config.set('playback', 'default_volume', self.default_volume.value())
            self.config.set('playback', 'default_speed', self._index_to_speed(self.default_speed.currentIndex()))
            self.config.set('playback', 'skip_interval_short', self.skip_short.value() * 1000)
            self.config.set('playback', 'skip_interval_long', self.skip_long.value() * 1000)
            
            # Audio
            self.config.set('audio', 'audio_delay_ms', self.audio_delay.value())
            self.config.set('audio', 'preferred_language', self.preferred_audio_lang.text())
            
            # Subtitles
            self.config.set('subtitle', 'enabled', self.subtitles_enabled.isChecked())
            self.config.set('subtitle', 'subtitle_delay_ms', self.subtitle_delay.value())
            self.config.set('subtitle', 'preferred_language', self.preferred_sub_lang.text())
            self.config.set('subtitle', 'font_size', self.subtitle_size.value())
            
            # Advanced
            self.config.set('logging', 'level', self.log_level.currentText())
            self.config.set('logging', 'log_to_file', self.log_to_file.isChecked())
            
            # Save to file
            self.config.save_if_dirty()
            
            logger.info("Settings saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def _speed_to_index(self, speed: float) -> int:
        """Convert speed value to combo box index"""
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        try:
            return speeds.index(speed)
        except ValueError:
            return 3  # Default to 1.0x
    
    def _index_to_speed(self, index: int) -> float:
        """Convert combo box index to speed value"""
        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        return speeds[index] if 0 <= index < len(speeds) else 1.0
    
    def _on_apply(self):
        """Apply settings without closing"""
        self._save_settings()
    
    def _on_ok(self):
        """Save and close"""
        self._save_settings()
        self.accept()
    
    def _on_reset(self):
        """Reset to default values"""
        # Playback defaults
        self.resume_playback.setChecked(False)
        self.default_volume.setValue(100)
        self.default_speed.setCurrentIndex(3)  # 1.0x
        self.skip_short.setValue(10)
        self.skip_long.setValue(60)
        
        # Audio defaults
        self.audio_delay.setValue(0)
        self.preferred_audio_lang.setText("eng")
        
        # Subtitle defaults
        self.subtitles_enabled.setChecked(True)
        self.subtitle_delay.setValue(0)
        self.preferred_sub_lang.setText("eng")
        self.subtitle_size.setValue(24)
        
        # Advanced defaults
        self.log_level.setCurrentText("INFO")
        self.log_to_file.setChecked(True)
        self.hardware_acceleration.setChecked(True)
        self.cache_size.setValue(1000)
        
        logger.info("Settings reset to defaults")
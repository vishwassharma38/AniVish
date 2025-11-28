import sys
from pathlib import Path

# Add parent directory to path so we can import core modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QVBoxLayout
from PyQt5.QtCore import Qt

from core.videomanager import VideoManager
from core.config_loader import get_config
from core.logger import configure_logging, get_logger

from ui.main_window import AniVishMainWindow
from ui.video_widget import VideoWidget, AspectRatioVideoWidget
from ui.control_bar import ControlBar
from ui.keybindings import KeybindingManager
from ui.recent_files_dialog import RecentFilesDialog
from ui.open_url_dialog import OpenURLDialog
from ui.settings_dialog import SettingsDialog

logger = get_logger("app")


class AniVishApp:
    """Main application controller"""
    
    def __init__(self):
        # Initialize Qt application
        self.qapp = QApplication(sys.argv)
        self.qapp.setApplicationName("AniVish")
        self.qapp.setOrganizationName("AniVish")
        
        # Load configuration
        self.config = get_config()
        
        # Initialize VideoManager
        self.video_manager = VideoManager(self.config)
        
        # Create main window
        self.main_window = AniVishMainWindow(self.video_manager)
        
        # Setup UI components
        self._setup_video_area()
        self._setup_control_bar()
        self._setup_keybindings()
        self._setup_dialogs()
        
        logger.info("AniVish application initialized")
    
    def _setup_video_area(self):
        """Setup video display area"""
        content_frame = self.main_window.get_content_frame()
        layout = QVBoxLayout(content_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Video widget with aspect ratio container
        self.video_widget = VideoWidget(self.video_manager)
        self.video_container = AspectRatioVideoWidget(self.video_widget)
        layout.addWidget(self.video_container, 1)
        
        # Connect video widget signals
        self.video_widget.video_double_clicked.connect(
            self._toggle_fullscreen
        )
    
    def _setup_control_bar(self):
        """Setup control bar"""
        content_frame = self.main_window.get_content_frame()
        layout = content_frame.layout()
        
        self.control_bar = ControlBar(self.video_manager)
        layout.addWidget(self.control_bar)
        
        # Connect control bar signals
        self.control_bar.open_file_clicked.connect(self._open_file)
        self.control_bar.open_url_clicked.connect(self._open_url)
        self.control_bar.settings_clicked.connect(self._show_settings)
        self.control_bar.playlist_clicked.connect(self._show_recent_files)
        self.control_bar.fullscreen_clicked.connect(self._toggle_fullscreen)
    
    def _setup_keybindings(self):
        """Setup keyboard shortcuts"""
        self.keybinding_manager = KeybindingManager(
            self.main_window,
            self.video_manager
        )
        self.keybinding_manager.load_keybindings()
        
        # Register window-specific actions
        self.keybinding_manager.register_action('toggle_fullscreen', self._toggle_fullscreen)
        self.keybinding_manager.register_action('exit_fullscreen', lambda: self.main_window.showNormal() if self.main_window.isFullScreen() else None)
        self.keybinding_manager.register_action('open_file', self._open_file)
        self.keybinding_manager.register_action('open_url', self._open_url)
        self.keybinding_manager.register_action('show_recent', self._show_recent_files)
        self.keybinding_manager.register_action('show_settings', self._show_settings)
        self.keybinding_manager.register_action('quit', self.qapp.quit)
    
    def _setup_dialogs(self):
        """Setup UI dialogs"""
        self.recent_files_dialog = None
        self.open_url_dialog = None
        self.settings_dialog = None
    
    # ==========================================
    # UI Actions
    # ==========================================
    
    def _open_file(self):
        """Open file dialog"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Open Media File",
            "",
            "Media Files (*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.flac);;All Files (*.*)"
        )
        
        if file_path:
            try:
                self.video_manager.load(file_path)
                self.video_manager.play()
                logger.info(f"Opened file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to open file: {e}")
    
    def _open_url(self):
        """Show URL input dialog"""
        if not self.open_url_dialog:
            self.open_url_dialog = OpenURLDialog(
                self.main_window,
                self.video_manager
            )
        self.open_url_dialog.show()
    
    def _show_recent_files(self):
        """Show recent files dialog"""
        if not self.recent_files_dialog:
            self.recent_files_dialog = RecentFilesDialog(
                self.main_window,
                self.video_manager
            )
        self.recent_files_dialog.show()
    
    def _show_settings(self):
        """Show settings dialog"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(
                self.main_window,
                self.config
            )
        self.settings_dialog.show()
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.main_window.isFullScreen():
            self.main_window.showNormal()
        else:
            self.main_window.showFullScreen()
    
    # ==========================================
    # Application Lifecycle
    # ==========================================
    
    def run(self):
        """Show window and start event loop"""
        self.main_window.show()
        logger.info("Application started")
        return self.qapp.exec_()
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up application")
        self.video_manager.release()


def main():
    """Main entry point"""
    # Configure logging
    configure_logging(
        level="INFO",
        log_to_file=True,
        console_output=True
    )
    
    # Create and run application
    app = AniVishApp()
    exit_code = app.run()
    app.cleanup()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
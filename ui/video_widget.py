import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QPalette

from core.videomanager import VideoManager, PlaybackState
from core.logger import get_logger

logger = get_logger("video_widget")


class VideoWidget(QWidget):
    """
    Widget that hosts VLC video output.
    Handles platform-specific window embedding and maintains aspect ratio.
    """
    
    # Signals
    video_clicked = pyqtSignal()
    video_double_clicked = pyqtSignal()
    aspect_ratio_changed = pyqtSignal(float)  # width / height
    
    def __init__(self, video_manager: VideoManager, parent=None):
        super().__init__(parent)
        
        self.video_manager = video_manager
        self._aspect_ratio = 16.0 / 9.0  # Default aspect ratio
        self._has_video = False
        
        # Widget properties
        self.setMinimumSize(320, 180)
        
        # FIXED: In PyQt5, these attributes don't need Qt.WidgetAttribute prefix
        # They're accessible directly as Qt.WA_* constants
        try:
            self.setAttribute(Qt.WA_OpaquePaintBackground, True)
            self.setAttribute(Qt.WA_NoSystemBackground, True)
        except AttributeError:
            # If the above doesn't work, try without setting these attributes
            # VLC should still work, just might have some background artifacts
            logger.warning("Could not set widget attributes (Qt version issue)")
        
        # Black background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder label (shown when no video)
        self.placeholder = QLabel("No Media Loaded")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 18px;
                font-weight: 300;
            }
        """)
        layout.addWidget(self.placeholder)
        
        # Connect to video manager events
        self._connect_events()
        
        # Apply VLC video output
        self._embed_vlc_video()
        
        logger.info("Video widget initialized")
    
    def _connect_events(self):
        """Connect to video manager events"""
        self.video_manager.on('on_media_loaded', self._on_media_loaded)
        self.video_manager.on('on_playing', self._on_playing)
        self.video_manager.on('on_stopped', self._on_stopped)
        self.video_manager.on('on_video_size_changed', self._on_video_size_changed)
        self.video_manager.on('on_state_changed', self._on_state_changed)
    
    def _embed_vlc_video(self):
        """Embed VLC video output into this widget"""
        # Get platform-specific window handle
        if sys.platform.startswith('linux'):
            self.video_manager.set_video_output(int(self.winId()), 'linux')
            logger.debug("VLC output embedded (Linux X11)")
        elif sys.platform == 'win32':
            self.video_manager.set_video_output(int(self.winId()), 'windows')
            logger.debug("VLC output embedded (Windows)")
        elif sys.platform == 'darwin':
            self.video_manager.set_video_output(int(self.winId()), 'macos')
            logger.debug("VLC output embedded (macOS)")
        else:
            logger.warning(f"Unsupported platform for video embedding: {sys.platform}")
    
    # ==========================================
    # Event Handlers
    # ==========================================
    
    def _on_media_loaded(self, source, media_type):
        """Called when media is loaded"""
        self._has_video = True
        self.placeholder.hide()
        logger.debug(f"Media loaded in video widget: {media_type.name}")
    
    def _on_playing(self):
        """Called when playback starts"""
        self._has_video = True
        self.placeholder.hide()
    
    def _on_stopped(self):
        """Called when playback stops"""
        # Don't show placeholder immediately, keep last frame
        pass
    
    def _on_video_size_changed(self, width, height):
        """Called when video dimensions change"""
        if width > 0 and height > 0:
            self._aspect_ratio = width / height
            self.aspect_ratio_changed.emit(self._aspect_ratio)
            logger.debug(f"Video aspect ratio: {self._aspect_ratio:.3f} ({width}x{height})")
            self.update()
    
    def _on_state_changed(self, old_state, new_state):
        """Called when playback state changes"""
        if new_state == PlaybackState.IDLE:
            self._has_video = False
            self.placeholder.setText("No Media Loaded")
            self.placeholder.show()
        elif new_state == PlaybackState.ERROR:
            self.placeholder.setText("Playback Error")
            self.placeholder.show()
        elif new_state == PlaybackState.LOADING:
            self.placeholder.setText("Loading...")
            self.placeholder.show()
        elif new_state == PlaybackState.BUFFERING:
            self.placeholder.setText("Buffering...")
            self.placeholder.show()
    
    # ==========================================
    # Mouse Events
    # ==========================================
    
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.LeftButton:
            self.video_clicked.emit()
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click (typically for fullscreen toggle)"""
        if event.button() == Qt.LeftButton:
            self.video_double_clicked.emit()
        super().mouseDoubleClickEvent(event)
    
    # ==========================================
    # Size Management
    # ==========================================
    
    def sizeHint(self) -> QSize:
        """Provide size hint based on aspect ratio"""
        if self._has_video:
            width = 1280
            height = int(width / self._aspect_ratio)
            return QSize(width, height)
        return QSize(1280, 720)
    
    def heightForWidth(self, width: int) -> int:
        """Calculate height for given width maintaining aspect ratio"""
        if self._aspect_ratio > 0:
            return int(width / self._aspect_ratio)
        return width * 9 // 16
    
    def get_aspect_ratio(self) -> float:
        """Get current video aspect ratio"""
        return self._aspect_ratio
    
    def set_aspect_ratio(self, ratio: float):
        """Manually set aspect ratio"""
        if ratio > 0:
            self._aspect_ratio = ratio
            self.aspect_ratio_changed.emit(ratio)
            self.updateGeometry()
    
    # ==========================================
    # Visual Feedback
    # ==========================================
    
    def paintEvent(self, event):
        """Custom paint for visual feedback"""
        super().paintEvent(event)
        
        # Draw subtle border when focused
        if self.hasFocus():
            painter = QPainter(self)
            painter.setPen(QColor(100, 150, 255, 150))
            painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
    
    # ==========================================
    # Public API
    # ==========================================
    
    def has_video(self) -> bool:
        """Check if video is loaded"""
        return self._has_video
    
    def clear(self):
        """Clear video and show placeholder"""
        self._has_video = False
        self.placeholder.setText("No Media Loaded")
        self.placeholder.show()
        self.update()


class AspectRatioVideoWidget(QWidget):
    """
    Container that maintains video aspect ratio with letterboxing.
    Wraps the VideoWidget and adds black bars when necessary.
    """
    
    def __init__(self, video_widget: VideoWidget, parent=None):
        super().__init__(parent)
        
        self.video_widget = video_widget
        self._aspect_ratio = video_widget.get_aspect_ratio()
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.video_widget)
        
        # Connect to aspect ratio changes
        self.video_widget.aspect_ratio_changed.connect(self._on_aspect_ratio_changed)
        
        # Black background for letterboxing
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)
    
    def _on_aspect_ratio_changed(self, ratio: float):
        """Update aspect ratio and resize"""
        self._aspect_ratio = ratio
        self.updateGeometry()
    
    def resizeEvent(self, event):
        """Resize video widget maintaining aspect ratio"""
        super().resizeEvent(event)
        
        # Calculate video size with letterboxing
        container_width = self.width()
        container_height = self.height()
        container_ratio = container_width / container_height if container_height > 0 else 1.0
        
        if self._aspect_ratio > container_ratio:
            # Video is wider - fit to width, add top/bottom bars
            video_width = container_width
            video_height = int(video_width / self._aspect_ratio)
            x = 0
            y = (container_height - video_height) // 2
        else:
            # Video is taller - fit to height, add left/right bars
            video_height = container_height
            video_width = int(video_height * self._aspect_ratio)
            x = (container_width - video_width) // 2
            y = 0
        
        self.video_widget.setGeometry(x, y, video_width, video_height)
    
    def get_video_widget(self) -> VideoWidget:
        """Get the embedded video widget"""
        return self.video_widget
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QFrame, QApplication, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QPainter, QLinearGradient, QBrush

from core.videomanager import VideoManager
from core.config_loader import get_config
from core.logger import get_logger

logger = get_logger("main_window")


class WindowEdge:
    """Edge regions for window resizing"""
    NONE = 0
    LEFT = 1
    RIGHT = 2
    TOP = 4
    BOTTOM = 8
    TOPLEFT = TOP | LEFT
    TOPRIGHT = TOP | RIGHT
    BOTTOMLEFT = BOTTOM | LEFT
    BOTTOMRIGHT = BOTTOM | RIGHT


class AniVishMainWindow(QMainWindow):
    """
    Main frameless window with glass theme aesthetics.
    Features:
    - Frameless with custom dragging
    - Resizable edges
    - Translucent background
    - Glass blur effects
    - Embedded video widget
    """
    
    # Signals
    window_state_changed = pyqtSignal(str)  # 'maximized', 'minimized', 'normal'
    
    # Constants
    RESIZE_MARGIN = 10  # pixels for resize detection
    MIN_WIDTH = 800
    MIN_HEIGHT = 600
    
    def __init__(self, video_manager: VideoManager):
        super().__init__()
        
        self.video_manager = video_manager
        self.config = get_config()
        
        # Window state
        self._dragging = False
        self._drag_position = QPoint()
        self._resizing = False
        self._resize_edge = WindowEdge.NONE
        self._resize_start_geometry = QRect()
        self._resize_start_pos = QPoint()
        
        # Initialize UI
        self._init_window()
        self._init_central_widget()
        self._load_window_state()
        
        logger.info("Main window initialized")
    
    def _init_window(self):
        """Initialize window properties"""
        # Frameless window with transparency
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowSystemMenuHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Window properties
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        
        # Set window title
        self.setWindowTitle("AniVish - Anime Media Player")
        
        # Enable mouse tracking for edge detection
        self.setMouseTracking(True)
    
    def _init_central_widget(self):
        """Setup central widget structure"""
        # Main container
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Glass container frame
        self.glass_frame = QFrame()
        self.glass_frame.setObjectName("glassFrame")
        main_layout.addWidget(self.glass_frame)
        
        # Glass frame layout
        glass_layout = QVBoxLayout(self.glass_frame)
        glass_layout.setContentsMargins(8, 8, 8, 8)
        glass_layout.setSpacing(0)
        
        # Title bar (custom)
        self.title_bar = self._create_title_bar()
        glass_layout.addWidget(self.title_bar)
        
        # Content area (video + controls)
        self.content_frame = QFrame()
        self.content_frame.setObjectName("contentFrame")
        glass_layout.addWidget(self.content_frame)
        
        # Apply glass styling
        self._apply_glass_style()
    
    def _create_title_bar(self) -> QWidget:
        """Create custom draggable title bar"""
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        title_bar.setMouseTracking(True)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # Title label
        from PyQt5.QtWidgets import QLabel
        title_label = QLabel("AniVish")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Window control buttons (minimize, maximize, close)
        self._create_window_buttons(layout)
        
        return title_bar
    
    def _create_window_buttons(self, layout: QHBoxLayout):
        """Create minimize/maximize/close buttons"""
        from PyQt5.QtWidgets import QPushButton
        
        button_style = """
            QPushButton {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 16px;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """
        
        # Minimize button
        btn_minimize = QPushButton("−")
        btn_minimize.setFixedSize(30, 30)
        btn_minimize.setStyleSheet(button_style)
        btn_minimize.clicked.connect(self.showMinimized)
        layout.addWidget(btn_minimize)
        
        # Maximize/Restore button
        self.btn_maximize = QPushButton("□")
        self.btn_maximize.setFixedSize(30, 30)
        self.btn_maximize.setStyleSheet(button_style)
        self.btn_maximize.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.btn_maximize)
        
        # Close button
        btn_close = QPushButton("×")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet(button_style + """
            QPushButton:hover {
                background: rgba(255, 0, 0, 0.7);
            }
        """)
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
    
    def _apply_glass_style(self):
        """Apply glass/aero theme styling"""
        self.setStyleSheet("""
            #centralWidget {
                background: transparent;
            }
            
            #glassFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(20, 20, 40, 180),
                    stop:0.5 rgba(15, 15, 30, 200),
                    stop:1 rgba(10, 10, 20, 220)
                );
                border: 2px solid rgba(100, 150, 255, 100);
                border-radius: 12px;
            }
            
            #titleBar {
                background: rgba(0, 0, 0, 50);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            
            #titleLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                padding-left: 5px;
            }
            
            #contentFrame {
                background: rgba(0, 0, 0, 100);
                border-radius: 8px;
            }
        """)
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 100, 255, 100))
        shadow.setOffset(0, 0)
        self.glass_frame.setGraphicsEffect(shadow)
    
    # ==========================================
    # Window Dragging
    # ==========================================
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging and resizing"""
        if event.button() == Qt.LeftButton:
            # Check if in title bar (for dragging)
            if self.title_bar.geometry().contains(event.pos()):
                self._dragging = True
                self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
                return
            
            # Check if on resize edge
            edge = self._get_resize_edge(event.pos())
            if edge != WindowEdge.NONE and not self.isMaximized():
                self._resizing = True
                self._resize_edge = edge
                self._resize_start_geometry = self.geometry()
                self._resize_start_pos = event.globalPos()
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging/resizing/cursor"""
        if self._dragging:
            # Dragging window
            self.move(event.globalPos() - self._drag_position)
            event.accept()
            return
        
        if self._resizing:
            # Resizing window
            self._handle_resize(event.globalPos())
            event.accept()
            return
        
        # Update cursor based on edge
        if not self.isMaximized():
            edge = self._get_resize_edge(event.pos())
            self._update_cursor(edge)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._resizing = False
            self._resize_edge = WindowEdge.NONE
            self.unsetCursor()
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click on title bar to maximize"""
        if self.title_bar.geometry().contains(event.pos()):
            self._toggle_maximize()
            event.accept()
            return
        
        super().mouseDoubleClickEvent(event)
    
    # ==========================================
    # Resize Detection & Handling
    # ==========================================
    
    def _get_resize_edge(self, pos: QPoint) -> int:
        """Determine which edge/corner is under the cursor"""
        rect = self.rect()
        margin = self.RESIZE_MARGIN
        
        left = pos.x() <= margin
        right = pos.x() >= rect.width() - margin
        top = pos.y() <= margin
        bottom = pos.y() >= rect.height() - margin
        
        if top and left:
            return WindowEdge.TOPLEFT
        elif top and right:
            return WindowEdge.TOPRIGHT
        elif bottom and left:
            return WindowEdge.BOTTOMLEFT
        elif bottom and right:
            return WindowEdge.BOTTOMRIGHT
        elif left:
            return WindowEdge.LEFT
        elif right:
            return WindowEdge.RIGHT
        elif top:
            return WindowEdge.TOP
        elif bottom:
            return WindowEdge.BOTTOM
        
        return WindowEdge.NONE
    
    def _update_cursor(self, edge: int):
        """Update cursor shape based on resize edge"""
        cursor_map = {
            WindowEdge.LEFT: Qt.SizeHorCursor,
            WindowEdge.RIGHT: Qt.SizeHorCursor,
            WindowEdge.TOP: Qt.SizeVerCursor,
            WindowEdge.BOTTOM: Qt.SizeVerCursor,
            WindowEdge.TOPLEFT: Qt.SizeFDiagCursor,
            WindowEdge.BOTTOMRIGHT: Qt.SizeFDiagCursor,
            WindowEdge.TOPRIGHT: Qt.SizeBDiagCursor,
            WindowEdge.BOTTOMLEFT: Qt.SizeBDiagCursor,
        }
        
        if edge in cursor_map:
            self.setCursor(cursor_map[edge])
        else:
            self.unsetCursor()
    
    def _handle_resize(self, global_pos: QPoint):
        """Resize window based on edge and mouse position"""
        delta = global_pos - self._resize_start_pos
        geo = self._resize_start_geometry
        
        new_geo = QRect(geo)
        
        # Horizontal resize
        if self._resize_edge & WindowEdge.LEFT:
            new_geo.setLeft(geo.left() + delta.x())
        elif self._resize_edge & WindowEdge.RIGHT:
            new_geo.setRight(geo.right() + delta.x())
        
        # Vertical resize
        if self._resize_edge & WindowEdge.TOP:
            new_geo.setTop(geo.top() + delta.y())
        elif self._resize_edge & WindowEdge.BOTTOM:
            new_geo.setBottom(geo.bottom() + delta.y())
        
        # Enforce minimum size
        if new_geo.width() < self.MIN_WIDTH:
            if self._resize_edge & WindowEdge.LEFT:
                new_geo.setLeft(geo.right() - self.MIN_WIDTH)
            else:
                new_geo.setRight(geo.left() + self.MIN_WIDTH)
        
        if new_geo.height() < self.MIN_HEIGHT:
            if self._resize_edge & WindowEdge.TOP:
                new_geo.setTop(geo.bottom() - self.MIN_HEIGHT)
            else:
                new_geo.setBottom(geo.top() + self.MIN_HEIGHT)
        
        self.setGeometry(new_geo)
    
    # ==========================================
    # Window State Management
    # ==========================================
    
    def _toggle_maximize(self):
        """Toggle between maximized and normal state"""
        if self.isMaximized():
            self.showNormal()
            self.btn_maximize.setText("□")
            self.window_state_changed.emit('normal')
        else:
            self.showMaximized()
            self.btn_maximize.setText("❐")
            self.window_state_changed.emit('maximized')
    
    def _load_window_state(self):
        """Load window geometry from config"""
        ui_config = self.config.ui
        
        # Set window size
        self.resize(ui_config.window_width, ui_config.window_height)
        
        # Center on screen
        screen = QApplication.desktop().screenGeometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        # Apply maximized state
        if ui_config.window_maximized:
            self.showMaximized()
    
    def _save_window_state(self):
        """Save window geometry to config"""
        if not self.isMaximized():
            self.config.set('ui', 'window_width', self.width())
            self.config.set('ui', 'window_height', self.height())
        
        self.config.set('ui', 'window_maximized', self.isMaximized())
        self.config.save_if_dirty()
    
    # ==========================================
    # Public API
    # ==========================================
    
    def get_content_frame(self) -> QFrame:
        """Get the content frame for adding video widget and controls"""
        return self.content_frame
    
    # ==========================================
    # Cleanup
    # ==========================================
    
    def closeEvent(self, event):
        """Handle window close event"""
        logger.info("Closing main window")
        
        # Save window state
        self._save_window_state()
        
        # Stop playback
        self.video_manager.stop()
        
        event.accept()
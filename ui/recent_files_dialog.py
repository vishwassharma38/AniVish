from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.videomanager import VideoManager
from core.logger import get_logger

logger = get_logger("recent_files")


class RecentFilesDialog(QDialog):
    """Glass-themed recent files selector"""
    
    def __init__(self, parent, video_manager: VideoManager):
        super().__init__(parent)
        
        self.video_manager = video_manager
        
        self.setWindowTitle("Recent Files")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        self._init_ui()
        self._load_recent_files()
        self._apply_style()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Recent Files")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_selected)
        layout.addWidget(self.list_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_open = QPushButton("Open")
        self.btn_open.clicked.connect(self._on_open_clicked)
        btn_layout.addWidget(self.btn_open)
        
        self.btn_clear = QPushButton("Clear List")
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        btn_layout.addWidget(self.btn_clear)
        
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)
    
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
                padding: 10px;
            }
            QListWidget {
                background: rgba(0, 0, 0, 150);
                color: #FFFFFF;
                border: 1px solid rgba(100, 150, 255, 100);
                border-radius: 6px;
                padding: 5px;
            }
            QPushButton {
                background: rgba(80, 120, 200, 180);
                color: #FFFFFF;
                border: 1px solid rgba(150, 180, 255, 100);
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: rgba(100, 140, 220, 200);
            }
        """)
    
    def _load_recent_files(self):
        """Load recent files into list"""
        recent = self.video_manager.get_recent_files()
        
        self.list_widget.clear()
        
        for path in recent:
            item = QListWidgetItem(path)
            self.list_widget.addItem(item)
    
    def _on_item_selected(self, item):
        """Handle item double-click"""
        path = item.text()
        self._open_file(path)
    
    def _on_open_clicked(self):
        """Handle open button"""
        current = self.list_widget.currentItem()
        if current:
            path = current.text()
            self._open_file(path)
    
    def _open_file(self, path: str):
        """Open selected file"""
        try:
            self.video_manager.load(path)
            self.video_manager.play()
            self.accept()
            logger.info(f"Opened recent file: {path}")
        except Exception as e:
            logger.error(f"Failed to open file: {e}")
    
    def _on_clear_clicked(self):
        """Clear recent files list"""
        self.video_manager.get_config().clear_recent_files()
        self._load_recent_files()
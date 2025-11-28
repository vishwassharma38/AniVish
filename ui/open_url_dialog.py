from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.videomanager import VideoManager
from core.logger import get_logger

logger = get_logger("open_url")


class OpenURLDialog(QDialog):
    """Glass-themed URL input dialog for streaming"""
    
    def __init__(self, parent, video_manager: VideoManager):
        super().__init__(parent)
        
        self.video_manager = video_manager
        
        self.setWindowTitle("Open URL")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self._init_ui()
        self._apply_style()
        self._load_recent_urls()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Open Media URL")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Enter a direct media URL or streaming link:")
        desc.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        layout.addWidget(desc)
        
        # URL input with recent dropdown
        input_layout = QVBoxLayout()
        
        # Recent URLs dropdown (optional)
        self.recent_combo = QComboBox()
        self.recent_combo.setEditable(False)
        self.recent_combo.addItem("-- Recent URLs --")
        self.recent_combo.currentIndexChanged.connect(self._on_recent_selected)
        input_layout.addWidget(self.recent_combo)
        
        # URL text input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/video.mp4")
        self.url_input.returnPressed.connect(self._on_open_clicked)
        input_layout.addWidget(self.url_input)
        
        layout.addLayout(input_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_open = QPushButton("Open")
        self.btn_open.clicked.connect(self._on_open_clicked)
        self.btn_open.setDefault(True)
        btn_layout.addWidget(self.btn_open)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Focus on input
        self.url_input.setFocus()
    
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
                padding: 5px;
            }
            QLineEdit, QComboBox {
                background: rgba(0, 0, 0, 150);
                color: #FFFFFF;
                border: 1px solid rgba(100, 150, 255, 100);
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid rgba(100, 150, 255, 200);
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #FFFFFF;
                margin-right: 10px;
            }
            QPushButton {
                background: rgba(80, 120, 200, 180);
                color: #FFFFFF;
                border: 1px solid rgba(150, 180, 255, 100);
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(100, 140, 220, 200);
            }
            QPushButton:pressed {
                background: rgba(60, 100, 180, 200);
            }
            QPushButton:default {
                border: 2px solid rgba(150, 180, 255, 150);
            }
        """)
    
    def _load_recent_urls(self):
        """Load recent URLs from config"""
        try:
            recent_files = self.video_manager.get_recent_files()
            # Filter for URLs only
            urls = [f for f in recent_files if f.startswith(('http://', 'https://', 'rtsp://', 'rtmp://'))]
            
            for url in urls[:5]:  # Show last 5 URLs
                # Truncate long URLs for display
                display_url = url if len(url) <= 60 else url[:57] + "..."
                self.recent_combo.addItem(display_url, url)  # Store full URL as data
            
            if len(urls) == 0:
                self.recent_combo.hide()
        except Exception as e:
            logger.warning(f"Could not load recent URLs: {e}")
            self.recent_combo.hide()
    
    def _on_recent_selected(self, index):
        """Handle recent URL selection"""
        if index > 0:  # Skip the placeholder item
            url = self.recent_combo.itemData(index)
            if url:
                self.url_input.setText(url)
    
    def _on_open_clicked(self):
        """Handle open button"""
        url = self.url_input.text().strip()
        
        if not url:
            return
        
        # Basic validation
        if not url.startswith(('http://', 'https://', 'rtsp://', 'rtmp://', 'mms://', 'file://')):
            logger.warning(f"Invalid URL protocol: {url}")
            self.url_input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid rgba(255, 50, 50, 200);
                }
            """)
            return
        
        try:
            self.video_manager.load(url)
            self.video_manager.play()
            self.accept()
            logger.info(f"Opened URL: {url}")
        except Exception as e:
            logger.error(f"Failed to open URL: {e}")
            self.url_input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid rgba(255, 50, 50, 200);
                }
            """)
    
    def showEvent(self, event):
        """Reset input when dialog is shown"""
        super().showEvent(event)
        self.url_input.clear()
        self.url_input.setStyleSheet("")  # Reset error styling
        self.url_input.setFocus()
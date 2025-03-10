from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QComboBox, QSlider, QLabel, QFrame)
from PyQt5.QtCore import Qt
from .styles import COMBO_BOX_STYLE

class ResizeDropdown(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setVisible(False)  # Hidden by default
        
        # Style the dropdown
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        # Add shadow effect
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Size selection
        size_layout = QHBoxLayout()
        size_label = QLabel("Size:")
        self.size_combo = QComboBox()
        self.size_combo.addItems([
            "Small (800x600)",
            "Medium (1024x768)",
            "Large (1280x960)"
        ])
        self.size_combo.setFixedWidth(120)
        self.size_combo.setStyleSheet(COMBO_BOX_STYLE)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_combo)
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        # Quality slider
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Quality:")
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(80)
        self.quality_slider.setFixedWidth(120)
        self.quality_value = QLabel("80%")
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_value)
        layout.addLayout(quality_layout)
        
        # Resize buttons
        button_style = """
            QPushButton {
                background-color: #1877F2;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1464D2;
            }
        """
        
        buttons_layout = QHBoxLayout()
        self.resize_btn = QPushButton("Resize Selected")
        self.resize_all_btn = QPushButton("Resize All")
        self.resize_btn.setStyleSheet(button_style)
        self.resize_all_btn.setStyleSheet(button_style)
        buttons_layout.addWidget(self.resize_btn)
        buttons_layout.addWidget(self.resize_all_btn)
        layout.addLayout(buttons_layout)
        
        # Connect signals
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        
    def update_quality_label(self, value):
        self.quality_value.setText(f"{value}%")
        
    def show_under_button(self, button):
        pos = button.mapToGlobal(button.rect().bottomLeft())
        self.move(pos.x(), pos.y() + 5)
        self.show() 
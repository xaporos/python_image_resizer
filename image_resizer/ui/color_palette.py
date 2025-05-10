from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QColorDialog, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal, Qt

from image_resizer.ui.styles import BUTTON_STYLE

class ColorPalette(QWidget):
    colorChanged = pyqtSignal(QColor)  # Signal emitted when color is changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_color = QColor(Qt.black)  # Default color
        self.setFixedWidth(280)  # Match image list width
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)  # Reduced spacing between elements
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Create a horizontal layout for colors and current color display
        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(10)
        
        # Current color display
        self.current_color_btn = QPushButton()
        self.current_color_btn.setFixedSize(46, 46)
        self.current_color_btn.clicked.connect(self.show_color_picker)
        self.update_current_color_button()
        colors_layout.addWidget(self.current_color_btn)
        
        # Base colors section
        base_colors_layout = QGridLayout()
        base_colors_layout.setSpacing(2)  # Reduced spacing between color buttons
        
        # Reduced set of colors - 16 colors in 2x8 grid
        base_colors = [
            "#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF", "#FFFF00",
            "#FF00FF", "#00FFFF", "#808080", "#A52A2A", "#FFA500", "#32CD32",
            "#4169E1", "#800080", "#008080", "#D2691E"
        ]
        
        button_size = 22
        for i, color in enumerate(base_colors):
            btn = self.create_color_button(color, button_size)
            base_colors_layout.addWidget(btn, i // 8, i % 8)
        
        colors_layout.addLayout(base_colors_layout)
        
        main_layout.addLayout(colors_layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #DBDCDA;
                border-radius: 4px;
            }
        """)
        
    def create_color_button(self, color, size):
        btn = QPushButton()
        btn.setFixedSize(size, size)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 1px solid #DBDCDA;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid #242424;
            }}
        """)
        btn.clicked.connect(lambda checked, c=color: self.set_color(QColor(c)))
        return btn
        
    def update_current_color_button(self):
        self.current_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color.name()};
                border: 1px solid #DBDCDA;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid #242424;
            }}
        """)
        
    def set_color(self, color):
        self.current_color = color
        self.update_current_color_button()
        self.colorChanged.emit(color)
        
    def show_color_picker(self):
        color = QColorDialog.getColor(self.current_color)
        if color.isValid():
            self.set_color(color)
            
    def get_current_color(self):
        return self.current_color 
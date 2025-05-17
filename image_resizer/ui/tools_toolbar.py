import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QHBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from image_resizer.ui.styles import TOOL_BUTTON_STYLE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CROP_ICON_PATH = os.path.join(BASE_DIR, "assets", "crop.png")
PENCIL_ICON_PATH = os.path.join(BASE_DIR, "assets", "pencil.png")
LINE_ICON_PATH = os.path.join(BASE_DIR, "assets", "line.png")
ARROW_ICON_PATH = os.path.join(BASE_DIR, "assets", "arrow.png")
CIRCLE_ICON_PATH = os.path.join(BASE_DIR, "assets", "circle.png")
RECT_ICON_PATH = os.path.join(BASE_DIR, "assets", "rect.png")
TEXT_ICON_PATH = os.path.join(BASE_DIR, "assets", "text.png")
HIGHLIGHT_ICON_PATH = os.path.join(BASE_DIR, "assets", "highlight.png")
ERASER_ICON_PATH = os.path.join(BASE_DIR, "assets", "erase.png")

class ToolsToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Create main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 5, 5)
        self.layout.setSpacing(5)
        
        # Set fixed width for the toolbar
        self.setFixedWidth(50)
        
        # Style the toolbar
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #50242424;
                border-radius: 8px;
            }
        """)
        
        # Create drawing tools
        self.setup_tools()
        
        # Initially disable all tools
        self.set_tools_enabled(False)
        
    def setup_tools(self):
        """Setup drawing tool buttons"""
        # Common button size
        button_size = 36
        
        # Create tool buttons
        self.crop_btn = self.create_tool_button(CROP_ICON_PATH, "Crop", button_size)
        self.pencil_btn = self.create_tool_button(PENCIL_ICON_PATH, "Pencil", button_size)
        self.line_btn = self.create_tool_button(LINE_ICON_PATH, "Line", button_size)
        self.arrow_btn = self.create_tool_button(ARROW_ICON_PATH, "Arrow", button_size)
        self.circle_btn = self.create_tool_button(CIRCLE_ICON_PATH, "Circle", button_size)
        self.rect_btn = self.create_tool_button(RECT_ICON_PATH, "Rectangle", button_size)
        self.text_btn = self.create_tool_button(TEXT_ICON_PATH, "Text", button_size)
        self.highlight_btn = self.create_tool_button(HIGHLIGHT_ICON_PATH, "Highlighter", button_size)
        self.eraser_btn = self.create_tool_button(ERASER_ICON_PATH, "Eraser", button_size)
        
        # Create separator line
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.separator.setStyleSheet("background-color: #DBDCDA; margin: 5px 2px;")
        self.separator.setFixedHeight(1)
        
        # Create eraser mode toggle button
        self.eraser_mode_btn = self.create_switch_button("Clear", "Color Eraser", button_size-10)
        self.eraser_mode_btn.setToolTip("Toggle between transparent eraser and color eraser modes")
        self.eraser_mode_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                font-weight: 500;
                padding: 2px;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
        """)
        
        # Add buttons to layout
        self.layout.addWidget(self.crop_btn)
        self.layout.addWidget(self.pencil_btn)
        self.layout.addWidget(self.line_btn)
        self.layout.addWidget(self.arrow_btn)
        self.layout.addWidget(self.circle_btn)
        self.layout.addWidget(self.rect_btn)
        self.layout.addWidget(self.text_btn)
        self.layout.addWidget(self.highlight_btn)
        self.layout.addWidget(self.separator)
        self.layout.addWidget(self.eraser_btn)
        self.layout.addWidget(self.eraser_mode_btn)
        
        # Add stretch to push everything to the top
        self.layout.addStretch()
        
        # Keep track of drawing tools for easy access
        self.drawing_tools = [
            self.crop_btn,
            self.pencil_btn,
            self.line_btn,
            self.arrow_btn,
            self.circle_btn,
            self.rect_btn,
            self.text_btn,
            self.highlight_btn,
            self.eraser_btn
        ]
        
        # Connect eraser mode toggle
        self.eraser_mode_btn.clicked.connect(self.toggle_eraser_mode)
    
    def toggle_eraser_mode(self):
        """Toggle between transparent eraser and color eraser modes"""
        is_color_mode = self.eraser_mode_btn.isChecked()
        
        # Update the button text
        if is_color_mode:
            self.eraser_mode_btn.setText("Color")
        else:
            self.eraser_mode_btn.setText("Clear")
        
        # Update the eraser tool mode
        if hasattr(self.parent, 'tool_manager') and 'eraser' in self.parent.tool_manager.tools:
            eraser_tool = self.parent.tool_manager.tools['eraser']
            eraser_tool.set_color_mode(is_color_mode)
        
    def create_tool_button(self, icon_path, tooltip, size):
        """Create a tool button with consistent styling"""
        from PyQt5.QtWidgets import QPushButton
        btn = QPushButton("")
        btn.setIcon(QIcon(icon_path))
        btn.setToolTip(tooltip)
        btn.setCheckable(True)
        btn.setStyleSheet(TOOL_BUTTON_STYLE)
        btn.setFixedSize(size, size)
        return btn
    
    def create_switch_button(self, off_text, on_text, height):
        """Create a text toggle button"""
        from PyQt5.QtWidgets import QPushButton
        btn = QPushButton(off_text)
        btn.setCheckable(True)
        btn.setFixedHeight(height)
        return btn
        
    def set_tools_enabled(self, enabled):
        """Enable or disable all drawing tools"""
        for btn in self.drawing_tools:
            btn.setEnabled(enabled)
            if not enabled:
                btn.setChecked(False)
        
        # Also disable or enable the eraser mode toggle button
        if hasattr(self, 'eraser_mode_btn'):
            self.eraser_mode_btn.setEnabled(enabled) 
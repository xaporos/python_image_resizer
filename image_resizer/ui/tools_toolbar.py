from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt5.QtGui import QIcon
from image_resizer.ui.styles import TOOL_BUTTON_STYLE
from image_resizer.ui.toolbar import (CROP_ICON_PATH, PENCIL_ICON_PATH, LINE_ICON_PATH,
                                    ARROW_ICON_PATH, CIRCLE_ICON_PATH, RECT_ICON_PATH,
                                    TEXT_ICON_PATH, ERASER_ICON_PATH)

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
        
        # Create separator line
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.separator.setStyleSheet("background-color: #DBDCDA; margin: 5px 2px;")
        self.separator.setFixedHeight(1)
        
        # Create eraser button
        self.eraser_btn = self.create_tool_button(ERASER_ICON_PATH, "Eraser", button_size)
        
        # Add buttons to layout
        self.layout.addWidget(self.crop_btn)
        self.layout.addWidget(self.pencil_btn)
        self.layout.addWidget(self.line_btn)
        self.layout.addWidget(self.arrow_btn)
        self.layout.addWidget(self.circle_btn)
        self.layout.addWidget(self.rect_btn)
        self.layout.addWidget(self.text_btn)
        self.layout.addWidget(self.separator)
        self.layout.addWidget(self.eraser_btn)
        
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
            self.eraser_btn
        ]
        
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
        
    def set_tools_enabled(self, enabled):
        """Enable or disable all drawing tools"""
        for btn in self.drawing_tools:
            btn.setEnabled(enabled)
            if not enabled:
                btn.setChecked(False) 
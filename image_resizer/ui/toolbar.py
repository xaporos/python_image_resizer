import os
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QComboBox, QSlider, QLabel, QWidget, QToolBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from image_resizer.ui.styles import BUTTON_STYLE, SLIDER_STYLE, TOOL_BUTTON_STYLE, COMBO_BOX_STYLE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_ICON_PATH = os.path.join(BASE_DIR, "assets", "save.png")
SAVE_ALL_ICON_PATH = os.path.join(BASE_DIR, "assets", "save_all.png")
OPEN_ICON_PATH = os.path.join(BASE_DIR, "assets", "open.png")
CROP_ICON_PATH = os.path.join(BASE_DIR, "assets", "crop.png")
PENCIL_ICON_PATH = os.path.join(BASE_DIR, "assets", "pencil.png")
LINE_ICON_PATH = os.path.join(BASE_DIR, "assets", "line.png")
ARROW_ICON_PATH = os.path.join(BASE_DIR, "assets", "arrow.png")
CIRCLE_ICON_PATH = os.path.join(BASE_DIR, "assets", "circle.png")
RECT_ICON_PATH = os.path.join(BASE_DIR, "assets", "rect.png")
TEXT_ICON_PATH = os.path.join(BASE_DIR, "assets", "text.png")
UNDO_ICON_PATH = os.path.join(BASE_DIR, "assets", "undo.png")
REDO_ICON_PATH = os.path.join(BASE_DIR, "assets", "redo.png")

class Toolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(10)
        # Set smaller vertical margins for the toolbar
        self.layout.setContentsMargins(2, 0, 2, 0)
        # Set fixed height for the toolbar
        self.setFixedHeight(40)
        # Keep track of drawing tool buttons for easy access
        self.drawing_tools = []
        self.setup_tools()
        self.setup_controls()
        self.connect_signals()
        
        # Initially disable drawing tools
        self.set_drawing_tools_enabled(False)
        
    def connect_signals(self):
        """Connect all toolbar signals"""
        self.quality_slider.valueChanged.connect(self.quality_changed)
        
    def quality_changed(self, value):
        """Update quality label when slider value changes"""
        self.quality_label.setText(f"{value}%")
        
    def setup_tools(self):
        # Main container for all tools
        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(8, 0, 8, 0)
        
        # Common button size
        button_size = 36
        
        # Left section with Open button
        left_section = QHBoxLayout()
        left_section.setSpacing(5)
        
        # Open Images button
        self.open_btn = QPushButton("")
        self.open_btn.setIcon(QIcon(OPEN_ICON_PATH))
        self.open_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.open_btn.setFixedHeight(button_size)
        left_section.addWidget(self.open_btn)
        
        # Save buttons
        self.save_btn = QPushButton("")
        self.save_btn.setIcon(QIcon(SAVE_ICON_PATH))
        self.save_btn.setFlat(True)
        self.save_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.save_btn.setFixedSize(button_size, button_size)
        self.save_btn.setToolTip("Save Selected")
        left_section.addWidget(self.save_btn)
        
        self.save_all_btn = QPushButton("")  # Double arrow for save all
        self.save_all_btn.setIcon(QIcon(SAVE_ALL_ICON_PATH))
        self.save_all_btn.setFlat(True)
        self.save_all_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.save_all_btn.setFixedSize(button_size, button_size)
        self.save_all_btn.setToolTip("Save All")
        left_section.addWidget(self.save_all_btn)
        
        main_layout.addLayout(left_section)
        main_layout.addStretch(8)
     
        
        # Center container for tools section
        center_container = QWidget()
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(12)
        
        # Crop and pencil tools
        self.crop_btn = QPushButton("")
        self.crop_btn.setIcon(QIcon(CROP_ICON_PATH))
        self.crop_btn.setFlat(True)
        self.crop_btn.setCheckable(True)
        self.crop_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.crop_btn.setFixedSize(button_size, button_size)
        center_layout.addWidget(self.crop_btn)
        self.drawing_tools.append(self.crop_btn)
        
        self.pencil_btn = QPushButton("")
        self.pencil_btn.setIcon(QIcon(PENCIL_ICON_PATH))
        self.pencil_btn.setFlat(True)
        self.pencil_btn.setCheckable(True)
        self.pencil_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.pencil_btn.setFixedSize(button_size, button_size)
        center_layout.addWidget(self.pencil_btn)
        self.drawing_tools.append(self.pencil_btn)
        
        # Add vertical separator
        separator1 = QWidget()
        separator1.setFixedWidth(1)
        separator1.setStyleSheet("background-color: #ddd;")
        separator1.setFixedHeight(30)
        center_layout.addWidget(separator1)
        
        # Drawing tools with consistent size
        tool_buttons = [
            (LINE_ICON_PATH, "line_btn", "Line"),
            (ARROW_ICON_PATH, "arrow_btn", "Arrow"),
            (CIRCLE_ICON_PATH, "circle_btn", "Circle"),
            (RECT_ICON_PATH, "rect_btn", "Rectangle"),
            (TEXT_ICON_PATH, "text_btn", "Text")
        ]

        for icon, attr_name, tooltip in tool_buttons:
            btn = QPushButton("")
            btn.setIcon(QIcon(icon))
            btn.setFlat(True)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(TOOL_BUTTON_STYLE)
            btn.setFixedSize(button_size, button_size)
            center_layout.addWidget(btn)
            setattr(self, attr_name, btn)
            self.drawing_tools.append(btn)
        
        # Add vertical separator
        separator2 = QWidget()
        separator2.setFixedWidth(1)
        separator2.setStyleSheet("background-color: #ddd;")
        separator2.setFixedHeight(30)
        center_layout.addWidget(separator2)
        
        # Add undo/redo buttons
        self.undo_btn = QPushButton("")
        self.undo_btn.setIcon(QIcon(UNDO_ICON_PATH))
        self.undo_btn.setFlat(True)
        self.undo_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.undo_btn.setFixedSize(button_size, button_size)
        center_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("")
        self.redo_btn.setIcon(QIcon(REDO_ICON_PATH))
        self.redo_btn.setFlat(True)
        self.redo_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.redo_btn.setFixedSize(button_size, button_size)
        center_layout.addWidget(self.redo_btn)
        
        # Add center container to main layout
        main_layout.addWidget(center_container, 0, Qt.AlignCenter)
        main_layout.addStretch(1)
        
        self.layout.addWidget(main_container)

    def setup_controls(self):
        controls_group = QHBoxLayout()
        controls_group.setContentsMargins(0, 0, 0, 0)
        
        # Add stretch at the beginning to push everything to the right
        controls_group.addStretch()
        
        # Size combo with correct preset strings
        self.size_combo = QComboBox()
        self.size_combo.addItems([
            "Original",
            "Small",
            "Medium",
            "Large"
        ])
        self.size_combo.setFixedWidth(120)  # Increased width to fit text
        self.size_combo.setFixedHeight(28)
        self.size_combo.setStyleSheet(COMBO_BOX_STYLE)
        controls_group.addWidget(self.size_combo)
        
        controls_group.addSpacing(8)
        
        # Quality slider container with fixed width
        slider_container = QWidget()
        slider_container.setFixedWidth(180)
        slider_container.setFixedHeight(28)
        slider_layout = QHBoxLayout(slider_container)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(80)
        self.quality_slider.setFixedWidth(120)
        self.quality_slider.setFixedHeight(16)
        self.quality_slider.setStyleSheet(SLIDER_STYLE)
        
        self.quality_label = QLabel("80%")
        self.quality_label.setFixedHeight(16)
        self.quality_label.setAlignment(Qt.AlignVCenter)
        
        slider_layout.addWidget(self.quality_slider, 0, Qt.AlignVCenter)
        slider_layout.addWidget(self.quality_label, 0, Qt.AlignVCenter)
        
        controls_group.addWidget(slider_container)
        
        self.resize_btn = QPushButton("Resize")
        self.resize_btn.setFixedSize(80, 28)  # Fixed width and height
        self.resize_btn.setStyleSheet(BUTTON_STYLE)
        controls_group.addWidget(self.resize_btn)
        
        self.resize_all_btn = QPushButton("Resize All")
        self.resize_all_btn.setFixedSize(90, 28)  # Fixed width and height
        self.resize_all_btn.setStyleSheet(BUTTON_STYLE)
        controls_group.addWidget(self.resize_all_btn)
        
        self.layout.addLayout(controls_group)

    def set_drawing_tools_enabled(self, enabled):
        """Enable or disable all drawing tools"""
        for btn in self.drawing_tools:
            btn.setEnabled(enabled)
            if not enabled:
                btn.setChecked(False)

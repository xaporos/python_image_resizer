from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QComboBox, QSlider, QLabel, QWidget, QToolBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from image_resizer.ui.styles import TOOL_BUTTON_STYLE, COMBO_BOX_STYLE

class Toolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(10)
        # Set smaller vertical margins for the toolbar
        self.layout.setContentsMargins(10, 2, 10, 2)
        # Set fixed height for the toolbar
        self.setFixedHeight(40)
        self.setup_tools()
        self.setup_controls()
        self.connect_signals()
        
    def connect_signals(self):
        """Connect all toolbar signals"""
        self.quality_slider.valueChanged.connect(self.quality_changed)
        
    def quality_changed(self, value):
        """Update quality label when slider value changes"""
        self.quality_label.setText(f"{value}%")
        
    def setup_tools(self):
        # Drawing tools group
        tools_group = QHBoxLayout()
        tools_group.setSpacing(5)
        # Set no margins for the tools group
        tools_group.setContentsMargins(0, 0, 0, 0)
        
        # Common button size
        button_size = 28
        
        # Save button
        self.save_btn = QPushButton("⤓")
        self.save_btn.setFlat(True)
        self.save_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.save_btn.setFixedSize(button_size, button_size)
        tools_group.addWidget(self.save_btn)

        # Undo/Redo buttons
        self.undo_btn = QPushButton("↺")
        self.undo_btn.setFlat(True)
        self.undo_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.undo_btn.setFixedSize(button_size, button_size)
        tools_group.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("↻")
        self.redo_btn.setFlat(True)
        self.redo_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.redo_btn.setFixedSize(button_size, button_size)
        tools_group.addWidget(self.redo_btn)

        # Add spacing
        tools_group.addSpacing(180)

        # Drawing tools with consistent size
        tool_buttons = [
            ("▣", "crop_btn"),
            ("✎", "pencil_btn"),
            ("─", "line_btn"),
            ("➔", "arrow_btn"),
            ("○", "circle_btn"),
            ("□", "rect_btn"),
            ("T", "text_btn")
        ]

        for text, attr_name in tool_buttons:
            btn = QPushButton(text)
            btn.setFlat(True)
            btn.setCheckable(True)
            btn.setStyleSheet(TOOL_BUTTON_STYLE)
            btn.setFixedSize(button_size, button_size)
            tools_group.addWidget(btn)
            setattr(self, attr_name, btn)
        
        self.layout.addLayout(tools_group)
        self.layout.addStretch()

    def setup_controls(self):
        controls_group = QHBoxLayout()
        controls_group.setContentsMargins(0, 0, 0, 0)
        
        # Size combo
        self.size_combo = QComboBox()
        self.size_combo.addItems(["Small", "Medium", "Large"])
        self.size_combo.setFixedWidth(80)
        self.size_combo.setFixedHeight(28)  # Match button height
        self.size_combo.setStyleSheet(COMBO_BOX_STYLE)
        controls_group.addWidget(self.size_combo)
        
        controls_group.addSpacing(10)
        
        # Quality slider container
        slider_container = QWidget()
        slider_container.setFixedWidth(180)
        slider_container.setFixedHeight(28)  # Match button height
        slider_layout = QHBoxLayout(slider_container)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(80)
        self.quality_slider.setFixedWidth(120)
        slider_layout.addWidget(self.quality_slider)
        
        self.quality_label = QLabel("80%")
        slider_layout.addWidget(self.quality_label)
        
        controls_group.addWidget(slider_container)
        controls_group.addSpacing(10)
        
        # Resize buttons with fixed height
        button_style = TOOL_BUTTON_STYLE + """
            QPushButton {
                background-color: #1877F2;
                color: white;
                padding: 4px 15px;
            }
        """
        
        self.resize_btn = QPushButton("Resize")
        self.resize_btn.setFixedHeight(28)
        self.resize_btn.setStyleSheet(button_style)
        controls_group.addWidget(self.resize_btn)
        
        self.resize_all_btn = QPushButton("Resize All")
        self.resize_all_btn.setFixedHeight(28)
        self.resize_all_btn.setStyleSheet(button_style)
        controls_group.addWidget(self.resize_all_btn)
        
        self.layout.addLayout(controls_group) 

class ToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        # Arrow tool
        self.arrow_btn = QPushButton()
        self.arrow_btn.setIcon(QIcon("image_resizer/assets/arrow.png"))
        self.arrow_btn.setCheckable(True)
        self.arrow_btn.clicked.connect(lambda: self.parent.set_tool('arrow'))
        self.addWidget(self.arrow_btn)

        # Circle tool
        self.circle_btn = QPushButton()
        self.circle_btn.setIcon(QIcon("image_resizer/assets/circle.png"))
        self.circle_btn.setCheckable(True)
        self.circle_btn.clicked.connect(lambda: self.parent.set_tool('circle'))
        self.addWidget(self.circle_btn)

        # Other tools... 
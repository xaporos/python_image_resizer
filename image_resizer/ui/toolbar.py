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
        # Drawing tools group
        tools_group = QHBoxLayout()
        tools_group.setSpacing(5)
        tools_group.setContentsMargins(0, 0, 0, 0)
        
        # Common button size
        button_size = 28
        
        # Open Images button
        self.open_btn = QPushButton("📂 Open")
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877F2;
                color: white;
                padding: 4px 15px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1464D2;
            }
        """)
        self.open_btn.setFixedHeight(button_size)
        tools_group.addWidget(self.open_btn)
        
        # Add small spacing after Open button
        tools_group.addSpacing(10)
        
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
            btn.setStyleSheet(TOOL_BUTTON_STYLE + """
                QPushButton:disabled {
                    color: #999;
                    background: transparent;
                }
            """)
            btn.setFixedSize(button_size, button_size)
            tools_group.addWidget(btn)
            setattr(self, attr_name, btn)
            # Add to drawing tools list for easy access
            self.drawing_tools.append(btn)
        
        self.layout.addLayout(tools_group)
        
        # Add vertical separator
        separator = QWidget()
        separator.setFixedWidth(1)
        separator.setStyleSheet("""
            background-color: #ddd;
            margin: 5px 15px;
        """)
        separator.setFixedHeight(30)  # Match toolbar height
        self.layout.addWidget(separator)

    def setup_controls(self):
        controls_group = QHBoxLayout()
        controls_group.setContentsMargins(0, 0, 0, 0)
        
        # Add stretch at the beginning to push everything to the right
        controls_group.addStretch()
        
        # Size combo
        self.size_combo = QComboBox()
        self.size_combo.addItems(["Small", "Medium", "Large"])
        self.size_combo.setFixedWidth(100)
        self.size_combo.setFixedHeight(28)
        self.size_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 10px;
                background: white;
                color: #333;
                font-weight: 500;
            }
            QComboBox:hover {
                border-color: #1877F2;
            }
            QComboBox:focus {
                border-color: #1877F2;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                color: #666;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 3px;
                padding: 5px;
                min-width: 150px;  /* Make dropdown wider */
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                min-height: 24px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f0f7ff;
                color: #1877F2;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #1877F2;
                color: white;
            }
        """)
        controls_group.addWidget(self.size_combo)
        
        controls_group.addSpacing(8)
        
        # Quality slider container with fixed width
        slider_container = QWidget()
        slider_container.setFixedWidth(180)
        slider_container.setFixedHeight(28)
        slider_layout = QHBoxLayout(slider_container)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        slider_layout.setSpacing(8)
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(80)
        self.quality_slider.setFixedWidth(120)
        self.quality_slider.setFixedHeight(16)
        self.quality_slider.setStyleSheet("""
            QSlider {
                margin: 0;
                padding: 0;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #ddd;
                margin: 6px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #1877F2;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #1464D2;
            }
        """)
        
        self.quality_label = QLabel("80%")
        self.quality_label.setFixedHeight(16)
        self.quality_label.setAlignment(Qt.AlignVCenter)
        
        slider_layout.addWidget(self.quality_slider, 0, Qt.AlignVCenter)
        slider_layout.addWidget(self.quality_label, 0, Qt.AlignVCenter)
        
        controls_group.addWidget(slider_container)
        controls_group.addSpacing(8)
        
        # Resize buttons with fixed width
        button_style = """
            QPushButton {
                background-color: #1877F2;
                color: white;
                padding: 4px 15px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1464D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """
        
        self.resize_btn = QPushButton("Resize")
        self.resize_btn.setFixedSize(80, 28)  # Fixed width and height
        self.resize_btn.setStyleSheet(button_style)
        controls_group.addWidget(self.resize_btn)
        
        self.resize_all_btn = QPushButton("Resize All")
        self.resize_all_btn.setFixedSize(90, 28)  # Fixed width and height
        self.resize_all_btn.setStyleSheet(button_style)
        controls_group.addWidget(self.resize_all_btn)
        
        self.layout.addLayout(controls_group)

    def set_drawing_tools_enabled(self, enabled):
        """Enable or disable all drawing tools"""
        for btn in self.drawing_tools:
            btn.setEnabled(enabled)
            if not enabled:
                btn.setChecked(False)

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
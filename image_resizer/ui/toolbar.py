import os
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QComboBox, QSlider, QLabel, QWidget, QToolBar, QFrame
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QPoint
from image_resizer.ui.styles import BUTTON_STYLE, SLIDER_STYLE, TOOL_BUTTON_STYLE, COMBO_BOX_STYLE, LABEL_STYLE

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
ERASER_ICON_PATH = os.path.join(BASE_DIR, "assets", "eraser.png")
UNDO_ICON_PATH = os.path.join(BASE_DIR, "assets", "undo.png")
REDO_ICON_PATH = os.path.join(BASE_DIR, "assets", "redo.png")

class Toolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(10)
        # Set smaller vertical margins for the toolbar
        self.layout.setContentsMargins(62, 0, 2, 0)
        # Set fixed height for the toolbar
        self.setFixedHeight(40)
        # Keep track of drawing tool buttons for easy access
        self.drawing_tools = []
        self.setup_tools()
        self.setup_controls()
        self.connect_signals()
        
        # Initially disable drawing tools
        self.set_drawing_tools_enabled(False)
        
        # Initialize button states
        self.resize_btn.setEnabled(False)
        self.resize_all_btn.setEnabled(False)
        self.undo_btn.setEnabled(False)
        self.redo_btn.setEnabled(False)
        
    def connect_signals(self):
        """Connect all toolbar signals"""
        self.quality_slider.valueChanged.connect(self.quality_changed)
        self.thickness_slider.valueChanged.connect(self.thickness_changed)
        
    def quality_changed(self, value):
        """Update quality label when slider value changes"""
        self.quality_label.setText(f"{value}%")
        
    def thickness_changed(self, value):
        """Update thickness label and tool line width when slider value changes"""
        self.thickness_value_label.setText(f"{value}px")
        if hasattr(self.parent, 'tool_manager'):
            # Update line width for all tools
            for tool in self.parent.tool_manager.tools.values():
                if hasattr(tool, 'line_width'):
                    tool.line_width = value
                    # Update eraser cursor size if this is the active eraser tool
                    if hasattr(tool, 'update_cursor_size') and self.parent.tool_manager.current_tool == tool:
                        tool.update_cursor_size()
            
            # Update current tool's active shape if it exists
            current_tool = self.parent.tool_manager.current_tool
            if current_tool:
                if hasattr(current_tool, 'shape_handler') and current_tool.shape_handler.selected_shape:
                    # Update selected shape's pen width
                    pen = current_tool.shape_handler.selected_shape.pen()
                    pen.setWidth(value)
                    current_tool.shape_handler.selected_shape.setPen(pen)
                elif hasattr(current_tool, 'rect_item') and current_tool.rect_item:
                    # Update rectangle being drawn
                    pen = current_tool.rect_item.pen()
                    pen.setWidth(value)
                    current_tool.rect_item.setPen(pen)
                elif hasattr(current_tool, 'circle_item') and current_tool.circle_item:
                    # Update circle being drawn
                    pen = current_tool.circle_item.pen()
                    pen.setWidth(value)
                    current_tool.circle_item.setPen(pen)
                elif hasattr(current_tool, 'line_item') and current_tool.line_item:
                    # Update line being drawn
                    pen = current_tool.line_item.pen()
                    pen.setWidth(value)
                    current_tool.line_item.setPen(pen)
                elif hasattr(current_tool, 'arrow_item') and current_tool.arrow_item:
                    # Update arrow being drawn
                    pen = current_tool.arrow_item.pen()
                    pen.setWidth(value)
                    current_tool.arrow_item.setPen(pen)
        
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
    
        v_line = QFrame()
        v_line.setFrameShape(QFrame.VLine)
        v_line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(v_line)
        
        # Add undo/redo buttons
        self.undo_btn = QPushButton("")
        self.undo_btn.setIcon(QIcon(UNDO_ICON_PATH))
        self.undo_btn.setFlat(True)
        self.undo_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.undo_btn.setFixedSize(button_size, button_size)
        main_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("")
        self.redo_btn.setIcon(QIcon(REDO_ICON_PATH))
        self.redo_btn.setFlat(True)
        self.redo_btn.setStyleSheet(TOOL_BUTTON_STYLE)
        self.redo_btn.setFixedSize(button_size, button_size)
        main_layout.addWidget(self.redo_btn)

        # Add thickness slider
        thickness_container = QWidget()
        thickness_container.setFixedWidth(240)
        thickness_container.setFixedHeight(28)
        thickness_layout = QHBoxLayout(thickness_container)
        thickness_layout.setContentsMargins(8, 0, 0, 0)
        
        thickness_label = QLabel("Thickness:")
        thickness_label.setStyleSheet(LABEL_STYLE)
        thickness_label.setFixedHeight(16)
        thickness_label.setAlignment(Qt.AlignVCenter)
        
        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setMinimum(1)
        self.thickness_slider.setMaximum(20)
        self.thickness_slider.setValue(3)  # Default thickness
        self.thickness_slider.setFixedWidth(120)
        self.thickness_slider.setFixedHeight(16)
        self.thickness_slider.setStyleSheet(SLIDER_STYLE)
        
        self.thickness_value_label = QLabel("3px")
        self.thickness_value_label.setFixedHeight(16)
        self.thickness_value_label.setAlignment(Qt.AlignVCenter)
        self.thickness_value_label.setStyleSheet(LABEL_STYLE)
        
        thickness_layout.addWidget(thickness_label, 0, Qt.AlignVCenter)
        thickness_layout.addWidget(self.thickness_slider, 0, Qt.AlignVCenter)
        thickness_layout.addWidget(self.thickness_value_label, 0, Qt.AlignVCenter)
        
        main_layout.addWidget(thickness_container)
        
        main_layout.addStretch(1)
        
        self.layout.addWidget(main_container)

    def setup_controls(self):
        controls_group = QHBoxLayout()
        controls_group.setContentsMargins(0, 0, 0, 0)
        
        # Add stretch at the beginning to push everything to the right
        controls_group.addStretch()


        class CustomComboBox(QComboBox):
            def showPopup(self):
                super().showPopup()

                # This is the popup widget Qt uses internally
                popup = self.view().window()
                if popup:
                    combo_pos = self.mapToGlobal(QPoint(0, 0))
                    x = combo_pos.x()
                    y = combo_pos.y() + self.height()  # Position just below the combo box
                    popup.move(x, y)
                    popup.setAttribute(Qt.WA_NoSystemBackground, True)
                    popup.setAttribute(Qt.WA_TranslucentBackground, False)
                    popup.setStyleSheet("background-color: white; border: none;")
        
        # Size combo with correct preset strings
        self.size_combo = CustomComboBox()
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
        """Enable or disable drawing tools"""
        pass  # Drawing tools are now in the tools toolbar

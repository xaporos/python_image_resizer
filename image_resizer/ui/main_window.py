from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QListWidget, QSplitter, QMenuBar, QMenu, QGraphicsScene, QLabel, QSlider, QPushButton, QShortcut)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QKeySequence
from image_resizer.ui.styles import MAIN_STYLE
from image_resizer.ui.toolbar import Toolbar
from image_resizer.components.custom_graphics_view import CustomGraphicsView
from image_resizer.utils.image_handler import ImageHandler
from image_resizer.components.tools.tool_manager import ToolManager

class ImageResizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("resizex")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(QSize(800, 600))
        
        # Apply main style
        self.setStyleSheet(MAIN_STYLE)
        
        # Create menu bar
        self.setup_menu()
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create scene and view first
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        
        # Initialize handlers before toolbar
        self.image_handler = ImageHandler(self)
        self.tool_manager = ToolManager(self)
        
        # Create toolbar after handlers are initialized
        self.toolbar = Toolbar(self)
        self.main_layout.addWidget(self.toolbar)
        
        # Create horizontal layout for list and preview
        content_layout = QHBoxLayout()
        
        # Create image list
        self.image_list = QListWidget()
        self.image_list.setMinimumWidth(280)
        self.image_list.setMaximumWidth(280)
        content_layout.addWidget(self.image_list)
        
        # Create preview area
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(self.view)
        
        # Create bottom info bar with zoom
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(10, 5, 10, 5)
        
        # Info labels
        self.size_label = QLabel("Size: --")
        self.file_size_label = QLabel("File size: --")
        
        # Add info labels to left side
        bottom_layout.addWidget(self.size_label)
        bottom_layout.addWidget(self.file_size_label)
        
        # Add stretch to push zoom controls to right
        bottom_layout.addStretch()
        
        # Zoom controls on right side
        zoom_label = QLabel("Zoom:")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        self.zoom_value_label = QLabel("100%")
        self.zoom_value_label.setFixedWidth(50)
        
        # Add Fit button
        self.fit_button = QPushButton("Fit")
        self.fit_button.setFixedWidth(40)
        self.fit_button.clicked.connect(self.fit_to_view)
        
        bottom_layout.addWidget(zoom_label)
        bottom_layout.addWidget(self.zoom_slider)
        bottom_layout.addWidget(self.zoom_value_label)
        bottom_layout.addWidget(self.fit_button)
        
        # Add bottom layout to preview layout
        preview_layout.addLayout(bottom_layout)
        
        # Add preview layout to content layout
        content_layout.addLayout(preview_layout)
        
        # Add content layout to main layout
        self.main_layout.addLayout(content_layout)
        
        # Add keyboard shortcuts for undo/redo
        self.setup_shortcuts()
        
        # Connect signals after all UI elements are created
        self.connect_signals()
        
    def connect_signals(self):
        # Connect toolbar buttons
        self.toolbar.save_btn.clicked.connect(self.image_handler.save_current)
        self.toolbar.resize_btn.clicked.connect(self.image_handler.resize_image)
        self.toolbar.resize_all_btn.clicked.connect(self.image_handler.resize_all_images)
        
        # Connect menu actions
        self.open_action.triggered.connect(self.image_handler.select_files)
        self.save_selected_action.triggered.connect(self.image_handler.save_current)
        self.save_all_action.triggered.connect(self.image_handler.save_all)
        
        # Connect image list selection
        self.image_list.currentItemChanged.connect(self.image_handler.image_selected)
        
        # Connect tool buttons
        self.toolbar.crop_btn.clicked.connect(lambda: self.set_tool('crop'))
        self.toolbar.pencil_btn.clicked.connect(lambda: self.set_tool('pencil'))
        self.toolbar.arrow_btn.clicked.connect(lambda: self.set_tool('arrow'))
        self.toolbar.circle_btn.clicked.connect(lambda: self.set_tool('circle'))
        self.toolbar.rect_btn.clicked.connect(lambda: self.set_tool('rectangle'))
        self.toolbar.text_btn.clicked.connect(lambda: self.set_tool('text'))
        
        # Connect undo/redo buttons
        self.toolbar.undo_btn.clicked.connect(self.image_handler.undo)
        self.toolbar.redo_btn.clicked.connect(self.image_handler.redo)
        
        # Connect zoom slider
        self.zoom_slider.valueChanged.connect(self.zoom_changed)
        
        # Add tooltips with shortcuts for undo/redo buttons
        self.toolbar.undo_btn.setToolTip("Undo (Ctrl+Z)")
        self.toolbar.redo_btn.setToolTip("Redo (Ctrl+Y)")
        
    def setup_menu(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        
        # Create File menu
        file_menu = QMenu('&File', self)
        menubar.addMenu(file_menu)
        
        # Add File menu actions
        self.open_action = file_menu.addAction('Open Images...')
        self.save_selected_action = file_menu.addAction('Save Selected')
        self.save_all_action = file_menu.addAction('Save All')
        
        # Create Edit menu
        edit_menu = QMenu('&Edit', self)
        menubar.addMenu(edit_menu)
        
    def select_files(self):
        pass  # We'll implement this later
        
    def resize_image(self):
        pass  # We'll implement this later
        
    def resize_all_images(self):
        pass  # We'll implement this later
        
    def set_tool(self, tool_name):
        """Set the current drawing tool"""
        self.tool_manager.set_tool(tool_name)
        
        # Update button states
        tool_buttons = {
            'crop': self.toolbar.crop_btn,
            'pencil': self.toolbar.pencil_btn,
            'arrow': self.toolbar.arrow_btn,
            'circle': self.toolbar.circle_btn,
            'rectangle': self.toolbar.rect_btn,
            'text': self.toolbar.text_btn,
        }
        
        # Uncheck all buttons
        for btn in tool_buttons.values():
            btn.setChecked(False)
        
        # Check the selected tool's button
        if tool_name in tool_buttons:
            tool_buttons[tool_name].setChecked(True)

    def mouse_press(self, event):
        self.tool_manager.handle_mouse_press(event)
        
    def mouse_move(self, event):
        self.tool_manager.handle_mouse_move(event)
        
    def mouse_release(self, event):
        self.tool_manager.handle_mouse_release(event)

    def zoom_changed(self, value):
        """Handle zoom slider value changes"""
        # Update zoom value label
        self.zoom_value_label.setText(f"{value}%")
        
        # Calculate scale factor
        scale = value / 100.0
        
        # Reset view transform
        self.view.resetTransform()
        # Apply new scale
        self.view.scale(scale, scale)

    def fit_to_view(self):
        """Reset zoom to fit image to view"""
        # Reset zoom slider and label
        self.zoom_slider.setValue(100)
        self.zoom_value_label.setText("100%")
        
        # Reset view transform
        self.view.resetTransform()
        
        # Fit view to scene
        self.view.fitInView(self.view.sceneRect(), Qt.KeepAspectRatio)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Undo - Ctrl+Z (Cmd+Z on Mac)
        self.undo_shortcut = QShortcut(QKeySequence.Undo, self)
        self.undo_shortcut.activated.connect(self.image_handler.undo)
        
        # Redo - Ctrl+Y or Ctrl+Shift+Z (Cmd+Shift+Z on Mac)
        self.redo_shortcut = QShortcut(QKeySequence.Redo, self)
        self.redo_shortcut.activated.connect(self.image_handler.redo)
        
        # Alternative Redo shortcut (Ctrl+Y)
        self.redo_shortcut_alt = QShortcut(QKeySequence("Ctrl+Y"), self)
        self.redo_shortcut_alt.activated.connect(self.image_handler.redo) 
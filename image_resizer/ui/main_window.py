from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QListWidget, QSplitter, QMenuBar, QMenu, QGraphicsScene, QLabel)
from PyQt5.QtCore import Qt
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
        self.setMinimumSize(800, 600)
        
        # Apply main style
        self.setStyleSheet(MAIN_STYLE)
        
        # Create menu bar
        self.setup_menu()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add image handler
        self.image_handler = ImageHandler(self)
        
        # Add tool manager
        self.tool_manager = ToolManager(self)
        
        # Initialize UI components
        self.setup_ui()
        self.connect_signals()
        
    def connect_signals(self):
        # Connect toolbar buttons
        self.toolbar.save_btn.clicked.connect(self.image_handler.save_current)
        self.toolbar.resize_btn.clicked.connect(self.image_handler.resize_image)
        self.toolbar.resize_all_btn.clicked.connect(self.image_handler.resize_all_images)
        
        # Connect menu actions
        self.open_action.triggered.connect(self.image_handler.select_files)
        self.save_selected_action.triggered.connect(self.image_handler.resize_image)
        self.save_all_action.triggered.connect(self.image_handler.resize_all_images)
        
        # Connect image list selection
        self.image_list.currentItemChanged.connect(self.image_handler.image_selected)
        
        # Connect tool buttons
        self.toolbar.crop_btn.clicked.connect(lambda: self.set_tool('crop'))
        self.toolbar.pencil_btn.clicked.connect(lambda: self.set_tool('pencil'))
        self.toolbar.arrow_btn.clicked.connect(lambda: self.set_tool('arrow'))
        self.toolbar.circle_btn.clicked.connect(lambda: self.set_tool('circle'))
        
        # Connect undo/redo buttons
        self.toolbar.undo_btn.clicked.connect(self.image_handler.undo)
        self.toolbar.redo_btn.clicked.connect(self.image_handler.redo)
        
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
        
    def setup_ui(self):
        # Add toolbar
        self.toolbar = Toolbar(self)
        self.main_layout.addWidget(self.toolbar)
        
        # Create splitter for list and preview
        splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(splitter)
        
        # Create list widget for images
        self.image_list = QListWidget()
        self.image_list.setMinimumWidth(280)
        self.image_list.setMaximumWidth(280)
        splitter.addWidget(self.image_list)
        
        # Create right panel for preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        splitter.addWidget(right_panel)
        
        # Create graphics scene and view
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        right_layout.addWidget(self.view)
        
        # Set splitter sizes
        splitter.setSizes([200, 950])
        
        # Add info bar
        self.setup_info_bar()
    
    def setup_info_bar(self):
        info_bar = QHBoxLayout()
        info_bar.setSpacing(20)
        info_bar.setContentsMargins(10, 2, 10, 2)
        
        # Create labels for image info
        self.size_label = QLabel("Size: --")
        self.size_label.setFixedHeight(20)
        self.file_size_label = QLabel("File size: --")
        self.file_size_label.setFixedHeight(20)
        
        info_bar.addStretch()
        info_bar.addWidget(self.size_label)
        info_bar.addWidget(self.file_size_label)
        
        self.main_layout.addLayout(info_bar)

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
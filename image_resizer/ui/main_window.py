from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QListWidget, QListWidgetItem, QGraphicsDropShadowEffect, QMenuBar, 
                           QMenu, QGraphicsScene, QLabel, QSlider, QPushButton, 
                           QShortcut, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, QRectF
from PyQt5.QtGui import QKeySequence, QColor, QPainter, QPainterPath
from image_resizer.ui.styles import BUTTON_STYLE, IMAGE_LIST_STYLE, LABEL_STYLE, MAIN_STYLE, MAIN_WINDOW_STYLE, SLIDER_STYLE, ZOOM_SLIDER_STYLE
from image_resizer.ui.toolbar import Toolbar
from image_resizer.ui.tools_toolbar import ToolsToolbar
from image_resizer.ui.color_palette import ColorPalette
from image_resizer.components.custom_graphics_view import CustomGraphicsView
from image_resizer.utils.image_handler import ImageHandler
from image_resizer.components.tools.tool_manager import ToolManager
from image_resizer.ui.custom_list_item import ImageListItemWidget

class SimpleOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create label
        self.label = QLabel("Resizing images...")
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 500;
                background-color: rgba(0, 0, 0, 0.7);
                padding: 20px 40px;
                border-radius: 8px;
            }
        """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # Hide by default
        self.hide()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create semi-transparent background
        path = QPainterPath()
        rect = self.rect()
        path.addRect(QRectF(rect))  # Convert QRect to QRectF
        painter.fillPath(path, QColor(0, 0, 0, 128))

class ImageResizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("resizex")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(QSize(1400, 600))

        # Create and apply shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 40))  # semi-transparent black
        
        # Apply main style
        self.setStyleSheet(MAIN_STYLE)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setSpacing(4)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create left side container for toolbar and content
        left_container = QWidget()
        left_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scene and view first
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Initialize handlers before toolbar
        self.image_handler = ImageHandler(self)
        self.tool_manager = ToolManager(self)
        
        # Create toolbar after handlers are initialized
        self.toolbar = Toolbar(self)
        left_layout.addWidget(self.toolbar)
        
        # Create horizontal layout for tools and preview
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        
        # Create tools toolbar
        self.tools_toolbar = ToolsToolbar(self)
        content_layout.addWidget(self.tools_toolbar)
        
        # Create preview area with matching style
        preview_layout = QVBoxLayout()
        
        # Create a container for the view to apply styling
        view_container = QFrame()
        view_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        view_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #DBDCDA;
                border-radius: 4px;
            }
        """)
        view_layout = QVBoxLayout(view_container)
        view_layout.setContentsMargins(5, 5, 5, 5)
        view_layout.addWidget(self.view)
        
        # Style the graphics view
        self.view.setStyleSheet("""
            QGraphicsView {
                border: none;
                background-color: transparent;
            }
        """)
        
        preview_layout.addWidget(view_container)
        
        # Create bottom info bar container with border
        bottom_container = QWidget()
        bottom_container.setObjectName("bottomContainer")  # Set object name for specific styling
        bottom_container.setStyleSheet("""
            QWidget#bottomContainer {
                background-color: white;
                border: 1px solid #DBDCDA;
                border-radius: 4px;
            }
        """)
        bottom_container.setFixedHeight(50)
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(20, 5, 20, 5)
        
        # Info labels
        self.size_label = QLabel("Size: --")
        self.size_label.setStyleSheet(LABEL_STYLE)
        self.file_size_label = QLabel("File size: --")
        self.file_size_label.setStyleSheet(LABEL_STYLE)
        
        # Add info labels to left side
        bottom_layout.addWidget(self.size_label)
        bottom_layout.addWidget(self.file_size_label)
        
        # Add stretch to push zoom controls to right
        bottom_layout.addStretch()
        
        # Zoom controls on right side
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet(LABEL_STYLE)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setStyleSheet(ZOOM_SLIDER_STYLE)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        self.zoom_value_label = QLabel("100%")
        self.zoom_value_label.setStyleSheet(LABEL_STYLE)
        self.zoom_value_label.setFixedWidth(50)
        
        # Add Fit button
        self.fit_button = QPushButton("Fit")
        self.fit_button.setFixedWidth(80)
        self.fit_button.setStyleSheet("""QPushButton {
                color: black;
                background-color: white;
                padding: 4px 10px;
                border: 1px solid #DBDCDA;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                border: 1px solid #242424;
            }
            }""")
        self.fit_button.clicked.connect(self.fit_to_view)
        
        bottom_layout.addWidget(zoom_label)
        bottom_layout.addWidget(self.zoom_slider)
        bottom_layout.addWidget(self.zoom_value_label)
        bottom_layout.addWidget(self.fit_button)
        
        # Add bottom container to preview layout
        preview_layout.addWidget(bottom_container)
        
        # Add preview layout to content layout
        content_layout.addLayout(preview_layout)
        
        # Add content layout to left container
        left_layout.addLayout(content_layout)
        
        # Add left container to main layout
        self.main_layout.addWidget(left_container, 1)  # Stretch factor 1
        # Create right container for color palette and image list
        right_container = QWidget()
        right_container.setFixedWidth(280)  # Fixed width for right sidebar
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)  # Increased spacing between color palette and image list
        
        # Create color palette container
        color_palette_container = QWidget()
        color_palette_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #DBDCDA;
                border-radius: 4px;
            }
        """)
        color_palette_layout = QVBoxLayout(color_palette_container)
        color_palette_layout.setContentsMargins(2, 4, 8, 4)
        
        # Add color palette
        self.color_palette = ColorPalette()
        color_palette_layout.addWidget(self.color_palette)
        right_layout.addWidget(color_palette_container)
        
        # Create image list
        self.image_list = QListWidget()
        self.image_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.image_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #DBDCDA;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                background: transparent;
                border-radius: 4px;
                margin: 2px 4px;
            }
            QListWidget::item:selected {
                background-color: #f5f5f5;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.image_list.setSelectionMode(QListWidget.SingleSelection)
        self.image_list.setSelectionBehavior(QListWidget.SelectItems)
        right_layout.addWidget(self.image_list)
        
        # Add containers to main layout
        self.main_layout.addWidget(right_container, 0)  # No stretch
        self.main_layout.setSpacing(8)  # Increased spacing between main content and right sidebar
        
        # Add keyboard shortcuts for undo/redo
        self.setup_shortcuts()
        
        # Connect signals after all UI elements are created
        self.connect_signals()
        
        # Create overlay
        self.overlay = SimpleOverlay(self)
        self.overlay.hide()
        
    def connect_signals(self):
        # Connect toolbar buttons
        self.toolbar.open_btn.clicked.connect(self.image_handler.select_files)
        self.toolbar.save_btn.clicked.connect(self.image_handler.save_current)
        self.toolbar.save_all_btn.clicked.connect(self.image_handler.save_all)
        self.toolbar.resize_btn.clicked.connect(self.image_handler.resize_image)
        self.toolbar.resize_all_btn.clicked.connect(self.image_handler.resize_all_images)
        
        # Disable save and resize buttons initially
        self.toolbar.save_btn.setEnabled(False)
        self.toolbar.save_all_btn.setEnabled(False)
        self.toolbar.resize_btn.setEnabled(False)
        self.toolbar.resize_all_btn.setEnabled(False)
        
        # Connect image list selection
        self.image_list.itemClicked.connect(self.handle_item_selection)
        self.image_list.currentItemChanged.connect(self.update_ui_state)
        
        # Connect tool buttons
        self.tools_toolbar.crop_btn.clicked.connect(lambda: self.set_tool('crop'))
        self.tools_toolbar.pencil_btn.clicked.connect(lambda: self.set_tool('pencil'))
        self.tools_toolbar.line_btn.clicked.connect(lambda: self.set_tool('line'))
        self.tools_toolbar.arrow_btn.clicked.connect(lambda: self.set_tool('arrow'))
        self.tools_toolbar.circle_btn.clicked.connect(lambda: self.set_tool('circle'))
        self.tools_toolbar.rect_btn.clicked.connect(lambda: self.set_tool('rectangle'))
        self.tools_toolbar.text_btn.clicked.connect(lambda: self.set_tool('text'))
        self.tools_toolbar.eraser_btn.clicked.connect(lambda: self.set_tool('eraser'))
        
        # Connect undo/redo buttons
        self.toolbar.undo_btn.clicked.connect(self.image_handler.undo)
        self.toolbar.redo_btn.clicked.connect(self.image_handler.redo)
        
        # Connect zoom slider
        self.zoom_slider.valueChanged.connect(self.zoom_changed)
        
        # Connect color palette
        self.color_palette.colorChanged.connect(self.tool_manager.set_current_color)
        
        # Add tooltips with shortcuts for undo/redo buttons
        self.toolbar.undo_btn.setToolTip("Undo (Ctrl+Z)")
        self.toolbar.redo_btn.setToolTip("Redo (Ctrl+Y)")
        
    def set_tool(self, tool_name):
        """Set the current drawing tool"""
        # Only allow tool selection if there's an image
        if not self.image_handler.current_image:
            return
            
        self.tool_manager.set_tool(tool_name)
        
        # Update button states
        tool_buttons = {
            'crop': self.tools_toolbar.crop_btn,
            'pencil': self.tools_toolbar.pencil_btn,
            'line': self.tools_toolbar.line_btn,
            'arrow': self.tools_toolbar.arrow_btn,
            'circle': self.tools_toolbar.circle_btn,
            'rectangle': self.tools_toolbar.rect_btn,
            'text': self.tools_toolbar.text_btn,
            'eraser': self.tools_toolbar.eraser_btn,
        }
        
        # Uncheck all buttons
        for btn in tool_buttons.values():
            btn.setChecked(False)
        
        # Check the selected tool's button
        if tool_name in tool_buttons:
            tool_buttons[tool_name].setChecked(True)
            
    def update_ui_state(self, current, previous):
        """Update UI elements based on current state"""
        # Update previous item's selection state
        if previous:
            prev_widget = self.image_list.itemWidget(previous)
            if prev_widget:
                prev_widget.set_selected(False)
                
        # Update current item's selection state
        if current:
            curr_widget = self.image_list.itemWidget(current)
            if curr_widget:
                curr_widget.set_selected(True)
        
        # Enable/disable drawing tools based on image selection
        has_image = current is not None
        self.tools_toolbar.set_tools_enabled(has_image)
        
        # Call the original image selected handler
        self.image_handler.image_selected(current, previous)

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

    def add_image_to_list(self, image_name):
        """Add image to list with custom widget"""
        item = QListWidgetItem()
        widget = ImageListItemWidget(image_name)
        widget.renamed.connect(self.image_handler.rename_image)
        widget.deleted.connect(self.image_handler.delete_image)
        item.setSizeHint(widget.sizeHint())
        self.image_list.addItem(item)
        self.image_list.setItemWidget(item, widget)
        # Initially set as not selected
        widget.set_selected(False)

    def handle_item_selection(self, item):
        """Handle explicit item selection"""
        if item:
            self.image_list.setCurrentItem(item)
            widget = self.image_list.itemWidget(item)
            if widget:
                # Ensure proper selection state
                for i in range(self.image_list.count()):
                    curr_item = self.image_list.item(i)
                    curr_widget = self.image_list.itemWidget(curr_item)
                    if curr_widget:
                        curr_widget.set_selected(curr_item == item)
                
                # Update image display
                self.image_handler.image_selected(item, self.image_list.currentItem())

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Fit view to window size
        if self.scene.items():
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            self.view.centerOn(self.scene.sceneRect().center())
            
        # Update overlay size
        if hasattr(self, 'overlay'):
            self.overlay.resize(self.size())
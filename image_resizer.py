import os
import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                           QMessageBox, QComboBox, QSlider, QListWidget,
                           QSplitter, QColorDialog, QMenuBar, QMenu,
                           QGraphicsScene, QGraphicsView, QGraphicsRectItem,
                           QGraphicsPixmapItem, QGraphicsEllipseItem, QGraphicsLineItem,
                           QGraphicsPathItem, QGraphicsTextItem)
from PyQt5.QtCore import Qt, QPoint, QRect, QByteArray, QBuffer, QRectF, QLineF, QPointF
from PyQt5.QtGui import (QPixmap, QImage, QPainter, QPen, QColor, QPainterPath, QBrush)
from PIL import Image
import numpy as np

class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.parent = parent
        self.setRenderHint(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def mousePressEvent(self, event):
        if self.parent:
            self.parent.mouse_press(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.parent:
            self.parent.mouse_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.parent:
            self.parent.mouse_release(event)
        super().mouseReleaseEvent(event)

class ImageResizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("resizex")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # Create menu bar
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        
        # Create File menu
        file_menu = QMenu('&File', self)
        menubar.addMenu(file_menu)
        
        # Add File menu actions
        open_action = file_menu.addAction('Open Images...')
        open_action.triggered.connect(self.select_files)
        
        save_selected_action = file_menu.addAction('Save Selected')
        save_selected_action.triggered.connect(self.resize_image)
        
        save_all_action = file_menu.addAction('Save All')
        save_all_action.triggered.connect(self.resize_all_images)
        
        # Create Edit menu
        edit_menu = QMenu('&Edit', self)
        menubar.addMenu(edit_menu)
        
        # Initialize variables
        self.images = {}
        self.current_image = None
        self.aspect_ratio = 1.0
        
        # Drawing variables
        self.drawing = False
        self.last_point = None
        self.current_tool = None
        self.current_color = QColor(Qt.red)
        self.line_width = 2
        
        # Size presets
        self.size_presets = {
            "Custom": None,
            "Small (800px)": 800,
            "Medium (1200px)": 1200,
            "Large (1600px)": 1600
        }
        
        # Add history-related variables
        self.history = []
        self.redo_stack = []
        self.image_histories = {}
        self.image_redo_stacks = {}
        self.max_history = 10
        
        # Add storage for edited images and dimensions
        self.edited_images = {}
        self.edited_file_sizes = {}
        self.original_dimensions = {}
        self.current_dimensions = {}
        self.file_sizes = {}
        
        # Add variables for drawing tools
        self.drawing = False
        self.last_point = None
        self.current_tool = None
        self.temp_image = None
        
        # Add crop mode variables
        self.cropping = False
        self.crop_start = None
        self.crop_rect = None
        
        # Add variables for rectangle manipulation
        self.selected_rect = None
        self.drag_handle = None
        self.drag_start = None
        self.rect_handles = []
        self.handle_size = 8
        self.manipulating = False

        # Add variables for circle tool
        self.circle_item = None

        # Add variables for pencil tool
        self.pencil_path = None
        
        # Add variables for arrow tool
        self.arrow_item = None
        self.arrow_start = None

        # Add overlay for crop tool
        self.overlay_item = None
        self.crop_overlay_color = QColor(0, 0, 0, 127)  # Semi-transparent black

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Set light theme with Facebook blue
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #ffffff;
                color: #333333;
            }
            QMenuBar {
                background-color: #ffffff;
                color: #333333;
            }
            QMenuBar::item:selected {
                background-color: #1877F2;
                color: white;
            }
            QMenu {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #dadde1;
            }
            QMenu::item:selected {
                background-color: #1877F2;
                color: white;
            }
            QPushButton {
                background-color: #1877F2;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                min-width: 28px;
                min-height: 28px;
                color: white;
            }
            QPushButton:hover {
                background-color: #166fe5;
            }
            QPushButton:disabled {
                background-color: #dadde1;
                color: #606770;
            }
            QLabel {
                color: #333333;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #dadde1;
                border-radius: 4px;
                padding: 5px;
                min-width: 100px;
                color: #333333;
            }
            QComboBox:hover {
                border-color: #1877F2;
            }
            QComboBox::drop-down {
                border: none;  /* Remove the dropdown arrow border */
            }
            QComboBox::down-arrow {
                width: 0;  /* Hide the dropdown arrow */
                height: 0;
            }
            QSlider {
                margin: 10px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #dadde1;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #1877F2;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #dadde1;
                border-radius: 4px;
                padding: 5px;
                color: #333333;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #1877F2;
                color: white;
            }
            QSplitter::handle {
                background-color: #dadde1;
            }
        """)
        
        # Create simplified toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        main_layout.addLayout(toolbar)
        
        # Drawing tools group
        tools_group = QHBoxLayout()
        tools_group.setSpacing(5)
        
        # Common style for all tool buttons
        tool_button_style = """
            QPushButton {
                border: none;
                background: transparent;
                font-size: 18px;
                padding: 5px;
                color: #808080;  /* Grey color for inactive state */
            }
            QPushButton:checked {
                color: #1877F2;  /* Primary color (Facebook blue) for active state */
            }
            QPushButton:hover {
                color: #404040;  /* Darker grey on hover */
            }
        """
         # Add Save Selected button
        self.save_btn = QPushButton("⤓")  # Changed to a simple downward arrow that matches other icons
        self.save_btn.setFlat(True)
        self.save_btn.setStyleSheet(tool_button_style)
        self.save_btn.clicked.connect(self.save)
        tools_group.addWidget(self.save_btn)

        # Add undo/redo buttons
        self.undo_btn = QPushButton("↺")  # Changed to a more standard curved undo arrow
        self.undo_btn.setFlat(True)
        self.undo_btn.setStyleSheet(tool_button_style)
        self.undo_btn.clicked.connect(self.undo)
        tools_group.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("↻")  # Changed to a more standard curved redo arrow
        self.redo_btn.setFlat(True)
        self.redo_btn.setStyleSheet(tool_button_style)
        self.redo_btn.clicked.connect(self.redo)
        tools_group.addWidget(self.redo_btn)

        # Add larger spacing before undo/redo buttons
        tools_group.addSpacing(180)

        # Create buttons with icons only
        self.crop_btn = QPushButton("▣")
        self.crop_btn.setFlat(True)
        self.crop_btn.setCheckable(True)
        self.crop_btn.setStyleSheet(tool_button_style)
        self.crop_btn.clicked.connect(lambda: self.set_tool("crop"))
        tools_group.addWidget(self.crop_btn)

        self.pencil_btn = QPushButton("✎")
        self.pencil_btn.setFlat(True)
        self.pencil_btn.setCheckable(True)
        self.pencil_btn.setStyleSheet(tool_button_style)
        tools_group.addWidget(self.pencil_btn)
        
        self.arrow_btn = QPushButton("➔")
        self.arrow_btn.setFlat(True)
        self.arrow_btn.setCheckable(True)
        self.arrow_btn.setStyleSheet(tool_button_style)
        tools_group.addWidget(self.arrow_btn)
        
        self.circle_btn = QPushButton("○")  # Changed back to simpler circle
        self.circle_btn.setFlat(True)
        self.circle_btn.setCheckable(True)
        self.circle_btn.setStyleSheet(tool_button_style)
        tools_group.addWidget(self.circle_btn)
        
        self.rect_btn = QPushButton("□")
        self.rect_btn.setFlat(True)
        self.rect_btn.setCheckable(True)
        self.rect_btn.setStyleSheet(tool_button_style)
        tools_group.addWidget(self.rect_btn)
        
        self.text_btn = QPushButton("T")
        self.text_btn.setFlat(True)
        self.text_btn.setCheckable(True)
        self.text_btn.setStyleSheet(tool_button_style)
        tools_group.addWidget(self.text_btn)
        
        
        toolbar.addLayout(tools_group)
        toolbar.addStretch()
        
        # Size and quality controls
        controls_group = QHBoxLayout()
        
        self.size_combo = QComboBox()
        self.size_combo.addItems(["Small", "Medium", "Large"])
        self.size_combo.setFixedWidth(80)
        self.size_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #dadde1;
                border-radius: 4px;
                padding: 5px;
                color: #333333;
                text-align: center;
                padding-left: 15px;  /* Add padding to center the text */
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
            }
            /* Style for the dropdown list */
            QComboBox QAbstractItemView {
                selection-background-color: #1877F2;
                selection-color: white;
                padding: 5px;
            }
            /* Center text in the dropdown items */
            QComboBox::item {
                text-align: center;
            }
        """)
        controls_group.addWidget(self.size_combo)
        
        # Add spacer between combo and slider
        controls_group.addSpacing(10)
        
        # Create container for slider and label
        slider_container = QWidget()
        slider_container.setFixedWidth(180)  # Slightly reduced from 200
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
        
        # Add spacer between quality controls and buttons
        controls_group.addSpacing(10)  # Reduced from 20 to 10
        
        # Custom style for resize buttons with reduced vertical padding
        resize_button_style = """
            QPushButton {
                background-color: #1877F2;
                border: none;
                border-radius: 4px;
                padding: 3px 15px;  /* Reduced vertical padding from 5px to 3px */
                min-width: 28px;
                min-height: 22px;  /* Reduced from 28px */
                color: white;
            }
            QPushButton:hover {
                background-color: #166fe5;
            }
            QPushButton:disabled {
                background-color: #dadde1;
                color: #606770;
            }
        """
        
        self.resize_btn = QPushButton("Resize")
        self.resize_btn.setStyleSheet(resize_button_style)
        controls_group.addWidget(self.resize_btn)
        
        self.resize_all_btn = QPushButton("Resize All")
        self.resize_all_btn.setStyleSheet(resize_button_style)
        controls_group.addWidget(self.resize_all_btn)
        
        toolbar.addLayout(controls_group)
        
        # Create splitter for list and preview
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                width: 1px;
                background-color: #3b3b3b;
            }
            QSplitter::handle:hover {
                background-color: #4b4b4b;
            }
        """)
        main_layout.addWidget(splitter)
        
        # Create list widget for images
        self.image_list = QListWidget()
        self.image_list.setMinimumWidth(280)
        self.image_list.setMaximumWidth(280)
        self.image_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #dadde1;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                border-radius: 4px;  /* Add corner radius to items */
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #1877F2;
                color: white;
                border-radius: 4px;  /* Keep corner radius when selected */
            }
            QListWidget::item:hover {
                background-color: #f0f2f5;
                border-radius: 4px;  /* Keep corner radius on hover */
            }
        """)
        self.image_list.currentItemChanged.connect(self.image_selected)
        splitter.addWidget(self.image_list)
        
        # Create right panel for preview and info
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)  # Add left margin for spacing from list
        splitter.addWidget(right_panel)
        
        # Create graphics scene and view
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        right_layout.addWidget(self.view)
        
        # Add variables for drawing tools
        self.drawing = False
        self.last_point = None
        self.current_tool = None
        self.temp_image = None
        
        # Add variables for rectangle tool
        self.rect_item = None
        self.selected_rect = None
        self.drag_handle = None
        self.drag_start = None
        self.manipulating = False
        
        # Set splitter sizes
        splitter.setSizes([200, 950])  # Left panel 200px, right panel 950px
        
        # Connect quality slider
        self.quality_slider.valueChanged.connect(self.quality_changed)
        
        # Drawing tools connections
        self.pencil_btn.clicked.connect(lambda: self.set_tool("pencil"))
        self.rect_btn.clicked.connect(lambda: self.set_tool("rectangle"))
        self.circle_btn.clicked.connect(lambda: self.set_tool("circle"))
        self.arrow_btn.clicked.connect(lambda: self.set_tool("arrow"))
        self.text_btn.clicked.connect(lambda: self.set_tool("text"))
        self.crop_btn.clicked.connect(lambda: self.set_tool("crop"))
        
        # Connect resize buttons
        self.resize_btn.clicked.connect(self.resize_image)
        self.resize_all_btn.clicked.connect(self.resize_all_images)
        
        # Initially disable resize buttons
        self.resize_btn.setEnabled(False)
        self.resize_all_btn.setEnabled(False)

        # Initially disable undo/redo buttons
        self.undo_btn.setEnabled(False)
        self.redo_btn.setEnabled(False)

    def select_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.tiff)"
        )
        
        if file_paths:
            for file_path in file_paths:
                try:
                    image = Image.open(file_path)
                    self.images[file_path] = image
                    self.image_list.addItem(os.path.basename(file_path))
                except Exception as e:
                    QMessageBox.warning(self, "Warning", 
                                      f"Could not load {os.path.basename(file_path)}: {str(e)}")
            
            self.resize_btn.setEnabled(True)
            self.resize_all_btn.setEnabled(True)
            
            # Select first image
            if self.image_list.count() > 0:
                self.image_list.setCurrentRow(0)

    def image_selected(self, current, previous):
        if current:
            # Save current canvas state and history if there is one
            if previous and self.view.scene().items():
                prev_path = self.get_file_path_from_item(previous)
                if prev_path:
                    # Get the pixmap item (should be the last item in the scene)
                    for item in self.view.scene().items():
                        if isinstance(item, QGraphicsPixmapItem):
                            self.edited_images[prev_path] = item.pixmap().copy()
                            break
                    
                    # Save the history and file size for the previous image
                    self.image_histories[prev_path] = self.history.copy()
                    self.image_redo_stacks[prev_path] = self.redo_stack.copy()
                    if prev_path in self.edited_file_sizes:
                        for item in self.view.scene().items():
                            if isinstance(item, QGraphicsPixmapItem):
                                self.edited_file_sizes[prev_path] = self.calculate_file_size(item.pixmap())
                                break
            
            file_path = self.get_file_path_from_item(current)
            if file_path in self.images:
                self.current_image = self.images[file_path]
                
                # Initialize dimensions and file size if not already set
                if file_path not in self.original_dimensions:
                    self.original_dimensions[file_path] = self.current_image.size
                    self.current_dimensions[file_path] = self.current_image.size
                    self.file_sizes[file_path] = os.path.getsize(file_path) / (1024 * 1024)
                
                # Restore history for the current image
                self.history = self.image_histories.get(file_path, [])
                self.redo_stack = self.image_redo_stacks.get(file_path, [])
                
                # Check if we have an edited version
                if file_path in self.edited_images:
                    self.update_preview_with_edited(file_path)
                else:
                    self.update_preview_and_info(file_path)
                
                # Update undo/redo button states
                self.undo_btn.setEnabled(len(self.history) > 0)
                self.redo_btn.setEnabled(len(self.redo_stack) > 0)

    def get_file_path_from_item(self, item):
        for path in self.images.keys():
            if os.path.basename(path) == item.text():
                return path
        return None

    def calculate_file_size(self, pixmap, quality=80):
        """Calculate more accurate file size based on actual image data"""
        # Create a temporary QByteArray to store the image
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.WriteOnly)
        
        # Save the image to the buffer with PNG format to maintain quality
        pixmap.save(buffer, "PNG")
        
        # Get the size in MB
        size_in_mb = byte_array.size() / (1024 * 1024)
        
        # Close the buffer
        buffer.close()
        
        return size_in_mb

    def update_preview_and_info(self, file_path):
        if self.current_image:
            # Clear previous scene
            self.scene.clear()
            
            # Create preview
            preview = self.current_image.copy()
            preview.thumbnail((800, 800))
            
            # Convert to QPixmap and add to scene
            preview_array = np.array(preview)
            height, width, channels = preview_array.shape
            bytes_per_line = channels * width
            preview_array = preview_array[:, :, ::-1].copy()
            qimage = QImage(preview_array.data, width, height, 
                          bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            
            # Add pixmap to scene
            self.scene.addPixmap(pixmap)
            # Convert QRect to QRectF
            self.view.setSceneRect(QRectF(pixmap.rect()))
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            
            # Use stored dimensions and original file size
            orig_width, orig_height = self.original_dimensions[file_path]
            current_width, current_height = self.current_dimensions[file_path]
            
            # Use edited file size if exists, otherwise use original
            file_size = self.edited_file_sizes.get(file_path, self.file_sizes[file_path])
            
            # Create info label
            info_label = QLabel(f"""File: {os.path.basename(file_path)}
Original size: {orig_width} × {orig_height} pixels
Current size: {current_width} × {current_height} pixels
File size: {file_size:.2f} MB""")
            
            # Add info label to scene
            self.scene.addWidget(info_label)
            self.aspect_ratio = current_width / current_height

    def update_preview_with_edited(self, file_path):
        if self.edited_images.get(file_path):
            # Clear previous scene
            self.scene.clear()
            
            # Add edited pixmap
            edited_pixmap = self.edited_images[file_path]
            self.scene.addPixmap(edited_pixmap)
            
            # Set scene rect and fit view
            self.view.setSceneRect(QRectF(edited_pixmap.rect()))
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            
            # Use stored dimensions
            orig_width, orig_height = self.original_dimensions[file_path]
            current_width, current_height = self.current_dimensions[file_path]
            
            # Use edited file size if exists, otherwise use original
            if file_path in self.edited_file_sizes:
                file_size = self.edited_file_sizes[file_path]
            else:
                file_size = self.file_sizes[file_path]
            
            # Create info label
            info_label = QLabel(f"""File: {os.path.basename(file_path)}
Original size: {orig_width} × {orig_height} pixels
Current size: {current_width} × {current_height} pixels
File size: {file_size:.2f} MB""")
            
            # Add info label to scene using addWidget
            self.scene.addWidget(info_label)
            self.aspect_ratio = current_width / current_height

    def preset_selected(self, selection):
        if self.current_image and selection != "Custom":
            width = self.size_presets[selection]
            height = int(width / self.aspect_ratio)
            
            current_text = self.view.scene().items()[0].text().split('\n')
            if len(current_text) >= 3:
                current_text[2] = f"New size: {width} × {height} pixels"
                self.view.scene().items()[0].setText('\n'.join(current_text))

    def resize_image(self):
        if not self.current_image:
            QMessageBox.warning(self, "Warning", "Please select an image first!")
            return
            
        try:
            # Get dimensions
            current_width, current_height = self.current_image.size
            
            if self.size_combo.currentText() != "Custom":
                target_width = self.size_presets[self.size_combo.currentText()]
                
                # Only resize if image is larger than target
                if current_width > target_width:
                    width = target_width
                    height = int(target_width / current_width * current_height)
                else:
                    # Keep original size if image is smaller
                    width, height = current_width, current_height
            else:
                # For custom, keep original size
                width, height = current_width, current_height
            
            # Create a copy of the image for resizing
            resized_image = self.current_image.copy()
            
            # Only resize if dimensions changed
            if (width, height) != current_width:
                resized_image = resized_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Get original file extension
            current_item = self.image_list.currentItem()
            if not current_item:
                return
            file_path = self.get_file_path_from_item(current_item)
            original_ext = os.path.splitext(file_path)[1].lower()
            
            # Save dialog
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Resized Image",
                f"resized_{os.path.basename(file_path)}",
                f"Image Files (*{original_ext})"
            )
            
            if save_path:
                # Get original size before saving
                original_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                
                # Save with appropriate settings based on format
                if save_path.lower().endswith(('.jpg', '.jpeg')):
                    resized_image.save(save_path, 
                                     quality=self.quality_slider.value(),
                                     optimize=True)
                elif save_path.lower().endswith('.png'):
                    resized_image.save(save_path, 
                                     optimize=True,
                                     compress_level=9)
                else:
                    resized_image.save(save_path)
                
                # Calculate new size and reduction percentage
                new_size = os.path.getsize(save_path) / (1024 * 1024)  # MB
                reduction = ((original_size - new_size) / original_size * 100)
                
                # Show detailed success message
                QMessageBox.information(self, "Success", 
                    f"Image resized successfully!\n\n"
                    f"Original size: {original_size:.2f} MB\n"
                    f"New size: {new_size:.2f} MB\n"
                    f"Reduction: {reduction:.1f}%\n\n"
                    f"Original dimensions: {current_width}x{current_height}\n"
                    f"New dimensions: {width}x{height}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def resize_all_images(self):
        if not self.images:
            QMessageBox.warning(self, "Warning", "No images loaded!")
            return
        
        # Ask for output directory
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return
        
        success_count = 0
        total_original_size = 0
        total_new_size = 0
        
        for file_path in self.images.keys():
            try:
                image = self.images[file_path]
                current_width, current_height = image.size
                
                # Get dimensions
                if self.size_combo.currentText() != "Custom":
                    target_width = self.size_presets[self.size_combo.currentText()]
                    
                    # Only resize if image is larger than target
                    if current_width > target_width:
                        width = target_width
                        height = int(target_width / current_width * current_height)
                    else:
                        # Keep original size if image is smaller
                        width, height = current_width, current_height
                else:
                    # For custom, keep original size
                    width, height = current_width, current_height
                
                # Create a copy of the image for resizing
                resized_image = image.copy()
                
                # Only resize if dimensions changed
                if (width, height) != current_width:
                    resized_image = resized_image.resize((width, height), Image.Resampling.LANCZOS)
                
                output_path = os.path.join(output_dir, f"resized_{os.path.basename(file_path)}")
                
                # Get original size before saving
                original_size = os.path.getsize(file_path) / (1024 * 1024)
                
                # Save with appropriate settings
                if output_path.lower().endswith(('.jpg', '.jpeg')):
                    resized_image.save(output_path, 
                                     quality=self.quality_slider.value(),
                                     optimize=True)
                elif output_path.lower().endswith('.png'):
                    resized_image.save(output_path, 
                                     optimize=True,
                                     compress_level=9)
                else:
                    resized_image.save(output_path)
                
                # Track sizes
                new_size = os.path.getsize(output_path)
                total_original_size += original_size
                total_new_size += new_size
                success_count += 1
                
            except Exception as e:
                QMessageBox.warning(self, "Warning", 
                                  f"Failed to resize {os.path.basename(file_path)}: {str(e)}")
        
        if success_count > 0:
            # Calculate total statistics
            total_original_mb = total_original_size / (1024 * 1024)
            total_new_mb = total_new_size / (1024 * 1024)
            total_reduction = ((total_original_size - total_new_size) / total_original_size * 100)
            
            # Create simplified message
            message = f"Successfully resized {success_count} of {len(self.images)} images\n\n"
            message += f"Total original size: {total_original_mb:.2f} MB\n"
            message += f"Total new size: {total_new_mb:.2f} MB\n"
            message += f"Total reduction: {total_reduction:.1f}%"
            
            QMessageBox.information(self, "Success", message)

    def quality_changed(self, value):
        """Update quality label when slider value changes"""
        self.quality_label.setText(f"{value}%")

    def set_tool(self, tool):
        """Set the current drawing tool"""
        print(f"Setting tool to: {tool}")  # Debug print
        
        # Clean up previous tool
        if self.current_tool == "crop":
            if self.crop_rect:
                self.scene.removeItem(self.crop_rect)
            if self.overlay_item:
                self.scene.removeItem(self.overlay_item)
            if hasattr(self, 'path_item') and self.path_item in self.scene.items():
                self.scene.removeItem(self.path_item)
            self.crop_rect = None
            self.overlay_item = None
            self.path_item = None
        
        # Set up new tool
        self.current_tool = tool
        
        # Initialize crop tool if selected
        if tool == "crop":
            print("Setting up crop tool")  # Debug print
            for item in self.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    rect = item.boundingRect()
                    self.overlay_item = QGraphicsRectItem(rect)
                    self.overlay_item.setBrush(QColor(0, 0, 0, 127))
                    self.overlay_item.setPen(QPen(Qt.NoPen))
                    self.scene.addItem(self.overlay_item)
                    break
        
        # Reset states
        self.drawing = False
        self.cropping = False
        self.manipulating = False
        self.last_point = None
        
        # Update button states
        tool_buttons = {
            "crop": self.crop_btn,
            "pencil": self.pencil_btn,
            "rectangle": self.rect_btn,
            "circle": self.circle_btn,
            "arrow": self.arrow_btn,
            "text": self.text_btn
        }
        
        # Uncheck all buttons
        for btn in tool_buttons.values():
            btn.setChecked(False)
        
        # Check the selected tool's button
        if tool in tool_buttons:
            tool_buttons[tool].setChecked(True)

    def finalize_rectangle(self):
        """Finalize the rectangle by drawing it permanently on the pixmap"""
        if not self.rect_item:
            return
            
        # Save state before making changes
        self.save_state()
        
        # Find the pixmap item
        pixmap = None
        for item in self.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                pixmap = item.pixmap().copy()
                break
        
        if pixmap:
            # Draw the rectangle on the pixmap
            painter = QPainter(pixmap)
            painter.setPen(QPen(self.current_color, self.line_width))
            painter.drawRect(self.rect_item.rect())
            painter.end()
            
            # Update the scene
            self.scene.clear()
            self.scene.addPixmap(pixmap)
            
            # Reset rectangle state
            self.rect_item = None
            
            # Add info label back
            self.update_info_label()

    def finalize_circle(self):
        """Finalize the circle by drawing it permanently on the pixmap"""
        if not self.circle_item:
            return
            
        # Save state before making changes
        self.save_state()
        
        # Find the pixmap item
        pixmap = None
        for item in self.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                pixmap = item.pixmap().copy()
                break
        
        if pixmap:
            # Draw the circle on the pixmap
            painter = QPainter(pixmap)
            painter.setPen(QPen(self.current_color, self.line_width))
            painter.drawEllipse(self.circle_item.rect())
            painter.end()
            
            # Update the scene
            self.scene.clear()
            self.scene.addPixmap(pixmap)
            
            # Reset circle state
            self.circle_item = None
            
            # Add info label back
            self.update_info_label()

    def apply_rect_changes(self):
        """Apply rectangle changes and exit manipulation mode"""
        if not self.rect_item:
            return
            
        # Save state before applying changes
        self.save_state()
        
        # Find the pixmap item
        pixmap = None
        for item in self.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                pixmap = item.pixmap()
                break
                
        if pixmap:
            self.scene.clear()
            self.scene.addPixmap(pixmap)
            self.view.setSceneRect(QRectF(pixmap.rect()))
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
        # Update temp image
        self.rect_item = None
        self.drawing = False
        self.manipulating = False

    def save_state(self):
        """Save current state to history"""
        # Find the pixmap item
        for item in self.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                # Save current state
                self.history.append(item.pixmap().copy())
                if len(self.history) > self.max_history:
                    self.history.pop(0)
                
                # Clear redo stack when new action is performed
                self.redo_stack.clear()
                
                # Update button states
                self.undo_btn.setEnabled(True)
                self.redo_btn.setEnabled(False)
                break

    def update_image_info(self, pixmap, file_path):
        """Update image information based on current pixmap"""
        width = pixmap.width()
        height = pixmap.height()
        
        # Use stored original dimensions and current file size
        orig_width, orig_height = self.original_dimensions.get(file_path, (width, height))
        file_size = self.edited_file_sizes.get(file_path, self.file_sizes[file_path])
        
        info = f"""File: {os.path.basename(file_path)}
Original size: {orig_width} × {orig_height} pixels
Current size: {width} × {height} pixels
File size: {file_size:.2f} MB"""
        
        self.view.scene().addItem(QLabel(info))
        self.aspect_ratio = width / height

    def undo(self):
        """Undo the last action"""
        if len(self.history) > 0:
            # Reset all tool states
            self.reset_tool_states()
            
            # Find current pixmap
            for item in self.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    # Save current state to redo stack
                    self.redo_stack.append(item.pixmap().copy())
                    break
            
            # Restore previous state
            previous_pixmap = self.history.pop()
            
            # Update scene
            self.scene.clear()
            self.scene.addPixmap(previous_pixmap)
            self.update_info_label()
            
            # Update button states
            self.undo_btn.setEnabled(len(self.history) > 0)
            self.redo_btn.setEnabled(True)

    def redo(self):
        """Redo the last undone action"""
        if len(self.redo_stack) > 0:
            # Reset all tool states
            self.reset_tool_states()
            
            # Find current pixmap
            for item in self.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    # Save current state to history
                    self.history.append(item.pixmap().copy())
                    break
            
            # Restore next state
            next_pixmap = self.redo_stack.pop()
            
            # Update scene
            self.scene.clear()
            self.scene.addPixmap(next_pixmap)
            self.update_info_label()
            
            # Update button states
            self.undo_btn.setEnabled(True)
            self.redo_btn.setEnabled(len(self.redo_stack) > 0)

    def reset_tool_states(self):
        """Reset all tool states"""
        # Reset drawing states
        self.drawing = False
        self.manipulating = False
        self.last_point = None
        self.drag_handle = None
        self.drag_start = None
        
        # Reset tool items
        self.rect_item = None
        self.selected_rect = None
        self.circle_item = None
        self.arrow_item = None
        self.pencil_path = None
        
        # Uncheck all tool buttons
        self.pencil_btn.setChecked(False)
        self.rect_btn.setChecked(False)
        self.circle_btn.setChecked(False)
        self.arrow_btn.setChecked(False)
        self.text_btn.setChecked(False)
        self.crop_btn.setChecked(False)
        
        # Reset current tool
        self.current_tool = None

    def save(self):
        """Save the current image with drawings"""
        if not self.view.scene().items():
            QMessageBox.warning(self, "Warning", "No image to save!")
            return
            
        # Get original file extension
        current_item = self.image_list.currentItem()
        if not current_item:
            return
            
        file_path = self.get_file_path_from_item(current_item)
        original_ext = os.path.splitext(file_path)[1].lower()
        
        # Save dialog
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            f"edited_{os.path.basename(file_path)}",
            f"Image Files (*{original_ext})"
        )
        
        if save_path:
            try:
                self.view.scene().items()[0].pixmap().save(save_path)
                QMessageBox.information(self, "Success", "Image saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save image: {str(e)}")

    def draw_arrow_head(self, start, end):
        """Draw arrow head at the end point"""
        if not self.arrow_item:
            return
            
        # Find the pixmap item
        pixmap = None
        for item in self.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                pixmap = item.pixmap().copy()
                break
                
        if pixmap:
            # Calculate arrow head points
            line = QLineF(start, end)
            angle = math.atan2(-line.dy(), line.dx())
            arrow_size = 20.0
            
            arrow_p1 = QPointF(end.x() + arrow_size * math.cos(angle + math.pi/6),
                             end.y() - arrow_size * math.sin(angle + math.pi/6))
            arrow_p2 = QPointF(end.x() + arrow_size * math.cos(angle - math.pi/6),
                             end.y() - arrow_size * math.sin(angle - math.pi/6))
            
            # Draw arrow head
            painter = QPainter(pixmap)
            painter.setPen(QPen(self.current_color, self.line_width))
            painter.drawLine(end, arrow_p1)
            painter.drawLine(end, arrow_p2)
            painter.end()
            
            # Update scene
            self.scene.clear()
            self.scene.addPixmap(pixmap)
            
            # Add info label back
            self.update_info_label()

    def finalize_drawing(self):
        """Finalize any drawing by rendering it to the pixmap"""
        # Find the pixmap item
        for item in self.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                # Save state before making changes
                self.save_state()
                
                # Update scene with current state
                pixmap = item.pixmap().copy()
                self.scene.clear()
                self.scene.addPixmap(pixmap)
                self.update_info_label()
                
                # Reset drawing state
                self.drawing = False
                self.pencil_path = None
                self.arrow_item = None
                self.last_point = None
                break

    def update_info_label(self):
        """Update the info label with current image information"""
        current_item = self.image_list.currentItem()
        if current_item:
            file_path = self.get_file_path_from_item(current_item)
            if file_path:
                orig_width, orig_height = self.original_dimensions[file_path]
                current_width, current_height = self.current_dimensions[file_path]
                file_size = self.edited_file_sizes.get(file_path, self.file_sizes[file_path])
                
                info_label = QLabel(f"""File: {os.path.basename(file_path)}
Original size: {orig_width} × {orig_height} pixels
Current size: {current_width} × {current_height} pixels
File size: {file_size:.2f} MB""")
                
                self.scene.addWidget(info_label)

    def mouse_press(self, event):
        if not self.current_image:
            return
            
        pos = self.view.mapToScene(event.pos())
        
        if self.current_tool == "crop":
            self.cropping = True
            self.crop_start = pos
            # Create crop rectangle with white dashed border
            self.crop_rect = QGraphicsRectItem()
            self.crop_rect.setPen(QPen(Qt.white, 2, Qt.DashLine))
            self.scene.addItem(self.crop_rect)
            
        elif self.current_tool == "pencil":
            self.drawing = True
            self.last_point = pos
            # Find and store the current pixmap
            for item in self.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    self.temp_image = item.pixmap().copy()
                    break
            # Save state before starting to draw
            self.save_state()
            
        elif self.current_tool == "arrow":
            self.drawing = True
            self.arrow_start = pos
            # Store original pixmap
            for item in self.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    self.temp_image = item.pixmap().copy()
                    break
            # Create arrow line for preview
            self.arrow_item = QGraphicsLineItem()
            self.arrow_item.setPen(QPen(self.current_color, self.line_width))
            self.arrow_item.setZValue(2)  # Keep arrow preview on top
            self.scene.addItem(self.arrow_item)
            
        elif self.current_tool == "rectangle":
            if not self.manipulating:
                self.drawing = True
                self.last_point = pos
                # Find the pixmap item
                for item in self.scene.items():
                    if isinstance(item, QGraphicsPixmapItem):
                        self.temp_image = item.pixmap().copy()
                        break
                # Create rectangle
                self.rect_item = QGraphicsRectItem()
                self.rect_item.setPen(QPen(self.current_color, self.line_width))
                self.scene.addItem(self.rect_item)
            
        elif self.current_tool == "circle":
            self.drawing = True
            self.last_point = pos
            # Find the pixmap item
            for item in self.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    self.temp_image = item.pixmap().copy()
                    break
            # Create circle
            self.circle_item = QGraphicsEllipseItem()
            self.circle_item.setPen(QPen(self.current_color, self.line_width))
            self.scene.addItem(self.circle_item)

    def mouse_move(self, event):
        if not self.current_image:
            return
            
        pos = self.view.mapToScene(event.pos())
        
        if self.cropping and self.current_tool == "crop":
            if self.crop_rect:
                rect = QRectF(self.crop_start, pos).normalized()
                self.crop_rect.setRect(rect)
                
                # Create two separate overlay rectangles to avoid the selected area
                if hasattr(self, 'path_item') and self.path_item in self.scene.items():
                    self.scene.removeItem(self.path_item)
                
                # Create a path that covers everything except the selection
                path = QPainterPath()
                full_rect = self.overlay_item.rect()
                
                # Add four rectangles around the selection area
                path.addRect(QRectF(full_rect.left(), full_rect.top(), 
                                  full_rect.width(), rect.top() - full_rect.top()))  # Top
                path.addRect(QRectF(full_rect.left(), rect.bottom(), 
                                  full_rect.width(), full_rect.bottom() - rect.bottom()))  # Bottom
                path.addRect(QRectF(full_rect.left(), rect.top(), 
                                  rect.left() - full_rect.left(), rect.height()))  # Left
                path.addRect(QRectF(rect.right(), rect.top(), 
                                  full_rect.right() - rect.right(), rect.height()))  # Right
                
                self.path_item = QGraphicsPathItem(path)
                self.path_item.setBrush(QColor(0, 0, 0, 127))
                self.path_item.setPen(QPen(Qt.NoPen))
                self.scene.addItem(self.path_item)
                
                # Keep the crop rectangle visible and on top
                self.crop_rect.setZValue(2)
                
        elif self.drawing and self.current_tool == "pencil":
            if not hasattr(self, 'temp_image'):
                return
            
            # Draw line on temp image
            painter = QPainter(self.temp_image)
            painter.setPen(QPen(self.current_color, self.line_width))
            painter.setRenderHint(QPainter.Antialiasing)
            painter.drawLine(self.last_point, pos)
            painter.end()
            
            # Update scene
            self.scene.clear()
            self.scene.addPixmap(self.temp_image)
            self.update_info_label()
            self.last_point = pos
            
        elif self.drawing and self.current_tool == "arrow":
            if self.arrow_item:
                # Update arrow preview
                self.arrow_item.setLine(QLineF(self.arrow_start, pos))
                
        elif self.drawing and self.current_tool == "rectangle":
            if self.rect_item:
                # Update rectangle preview
                rect = QRectF(self.last_point, pos).normalized()
                self.rect_item.setRect(rect)
                # Keep rectangle on top
                self.rect_item.setZValue(1)
                
        elif self.drawing and self.current_tool == "circle":
            if self.circle_item:
                # Update circle preview
                rect = QRectF(self.last_point, pos).normalized()
                self.circle_item.setRect(rect)
                # Keep circle on top
                self.circle_item.setZValue(1)

    def mouse_release(self, event):
        if not self.drawing and not self.cropping:
            return
            
        pos = self.view.mapToScene(event.pos())
        
        if self.current_tool == "crop" and self.cropping:
            if self.crop_rect:
                try:
                    # Get crop rectangle
                    rect = self.crop_rect.rect().normalized()
                    
                    # Find the pixmap item
                    for item in self.scene.items():
                        if isinstance(item, QGraphicsPixmapItem):
                            # Save state before cropping
                            self.save_state()
                            
                            # Get the cropped portion of the image
                            pixmap = item.pixmap()
                            cropped = pixmap.copy(rect.toRect())
                            
                            # Clean up crop tool items before updating scene
                            if self.overlay_item and self.overlay_item.scene():
                                self.scene.removeItem(self.overlay_item)
                            if self.crop_rect and self.crop_rect.scene():
                                self.scene.removeItem(self.crop_rect)
                            
                            # Update scene with cropped image
                            self.scene.clear()
                            self.scene.addPixmap(cropped)
                            
                            # Update current dimensions
                            current_item = self.image_list.currentItem()
                            if current_item:
                                file_path = self.get_file_path_from_item(current_item)
                                if file_path:
                                    self.current_dimensions[file_path] = (cropped.width(), cropped.height())
                            
                            # Add info label back
                            self.update_info_label()
                            break
                    
                finally:
                    # Reset crop tool state
                    self.overlay_item = None
                    self.crop_rect = None
                    self.cropping = False
                
        elif self.current_tool == "pencil":
            # Just end drawing, state was saved at start
            self.drawing = False
            
            # Update scene with final result
            self.scene.clear()
            self.scene.addPixmap(self.temp_image)
            self.update_info_label()
            
        elif self.current_tool == "arrow":
            if self.arrow_item:
                # Save state before making changes
                self.save_state()
                
                # Remove preview arrow
                self.scene.removeItem(self.arrow_item)
                
                # Draw final arrow on the temp image
                painter = QPainter(self.temp_image)
                painter.setPen(QPen(self.current_color, self.line_width))
                painter.setRenderHint(QPainter.Antialiasing)
                
                # Draw main line
                painter.drawLine(self.arrow_start, pos)
                
                # Calculate and draw arrow head
                line = QLineF(pos, self.arrow_start)
                angle = math.atan2(-line.dy(), line.dx())
                arrow_size = 20.0
                
                arrow_p1 = QPointF(pos.x() + arrow_size * math.cos(angle - math.pi/6),
                                 pos.y() - arrow_size * math.sin(angle - math.pi/6))
                arrow_p2 = QPointF(pos.x() + arrow_size * math.cos(angle + math.pi/6),
                                 pos.y() - arrow_size * math.sin(angle + math.pi/6))
                
                painter.drawLine(pos, arrow_p1)
                painter.drawLine(pos, arrow_p2)
                painter.end()
                
                # Update scene with final result
                self.scene.clear()
                self.scene.addPixmap(self.temp_image)
                self.update_info_label()
                self.drawing = False
                
        elif self.current_tool == "rectangle":
            if self.rect_item:
                rect = QRectF(self.last_point, pos).normalized()
                self.rect_item.setRect(rect)
                self.finalize_rectangle()
                self.drawing = False
                
        elif self.current_tool == "circle":
            if self.circle_item:
                rect = QRectF(self.last_point, pos).normalized()
                self.circle_item.setRect(rect)
                self.finalize_circle()
                self.drawing = False

def main():
    app = QApplication(sys.argv)
    window = ImageResizerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
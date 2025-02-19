import os
import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                           QMessageBox, QComboBox, QSlider, QListWidget,
                           QSplitter, QColorDialog, QMenuBar, QMenu)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PIL import Image
import numpy as np

class ImageResizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("resizex")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # Create menu bar
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        menubar.setNativeMenuBar(False)
        
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
        self.last_point = QPoint()
        self.current_tool = "pencil"
        self.current_color = QColor(Qt.red)
        self.line_width = 2
        
        # Size presets
        self.size_presets = {
            "Custom": None,
            "Small (800px)": 800,
            "Medium (1200px)": 1200,
            "Large (1600px)": 1600
        }
        
        # Add undo/redo history
        self.history = []  # Store previous states
        self.redo_stack = []  # Store states that were undone
        self.max_history = 20  # Maximum number of states to store

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
                font-size: 18px;  /* Slightly reduced font size for better consistency */
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
        
        # Create buttons with icons only
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
        self.image_list.setMaximumWidth(200)
        self.image_list.currentItemChanged.connect(self.image_selected)
        splitter.addWidget(self.image_list)
        
        # Create right panel for preview and info
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)  # Add left margin for spacing from list
        splitter.addWidget(right_panel)
        
        # Create canvas for drawing
        self.canvas = QLabel()
        self.canvas.setMouseTracking(True)
        self.canvas.mousePressEvent = self.mouse_press
        self.canvas.mouseMoveEvent = self.mouse_move
        self.canvas.mouseReleaseEvent = self.mouse_release
        self.canvas.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.canvas)
        
        # Add info label
        self.info_label = QLabel("No image selected")
        self.info_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        right_layout.addWidget(self.info_label)
        
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
        
        # Connect resize buttons
        self.resize_btn.clicked.connect(self.resize_image)
        self.resize_all_btn.clicked.connect(self.resize_all_images)
        
        # Initially disable resize buttons
        self.resize_btn.setEnabled(False)
        self.resize_all_btn.setEnabled(False)

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
            file_path = self.get_file_path_from_item(current)
            if file_path in self.images:
                self.current_image = self.images[file_path]
                self.update_preview_and_info(file_path)

    def get_file_path_from_item(self, item):
        for path in self.images.keys():
            if os.path.basename(path) == item.text():
                return path
        return None

    def update_preview_and_info(self, file_path):
        if self.current_image:
            # Create preview
            preview = self.current_image.copy()
            preview.thumbnail((800, 800))  # Resize for preview
            
            # Convert PIL image to QPixmap
            preview_array = np.array(preview)
            height, width, channels = preview_array.shape
            bytes_per_line = channels * width
            
            # Convert RGB to BGR for Qt
            preview_array = preview_array[:, :, ::-1].copy()
            
            qimage = QImage(preview_array.data, width, height, 
                          bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            
            # Set the pixmap to the canvas
            self.canvas.setPixmap(pixmap)
            
            # Update info
            width, height = self.current_image.size
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            
            info = f"""File: {os.path.basename(file_path)}
Original size: {width} × {height} pixels
New size: {width} × {height} pixels
File size: {file_size:.2f} MB"""
            
            self.info_label.setText(info)
            self.aspect_ratio = width / height
            
            # Clear history when loading new image
            self.history.clear()
            self.redo_stack.clear()

    def preset_selected(self, selection):
        if self.current_image and selection != "Custom":
            width = self.size_presets[selection]
            height = int(width / self.aspect_ratio)
            
            current_text = self.info_label.text().split('\n')
            if len(current_text) >= 3:
                current_text[2] = f"New size: {width} × {height} pixels"
                self.info_label.setText('\n'.join(current_text))

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
        self.current_tool = tool
        # Map tools to their buttons
        tool_buttons = {
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

    def get_image_coordinates(self, event_pos):
        """Convert window coordinates to image coordinates"""
        pixmap = self.canvas.pixmap()
        if not pixmap:
            return event_pos
        
        # Get the canvas size and pixmap size
        canvas_size = self.canvas.size()
        pixmap_size = pixmap.size()
        
        # Calculate the offset (for centered image)
        x_offset = (canvas_size.width() - pixmap_size.width()) // 2
        y_offset = (canvas_size.height() - pixmap_size.height()) // 2
        
        # Adjust coordinates
        return QPoint(event_pos.x() - x_offset, event_pos.y() - y_offset)

    def mouse_press(self, event):
        if self.current_image and self.canvas.pixmap():
            self.drawing = True
            self.last_point = self.get_image_coordinates(event.pos())
            self.temp_image = self.canvas.pixmap().copy()
            # Save state before starting new action
            self.save_state()

    def mouse_move(self, event):
        if self.drawing and self.current_image and self.canvas.pixmap():
            current_pos = self.get_image_coordinates(event.pos())
            
            if self.current_tool == "pencil":
                # For pencil, draw directly
                pixmap = self.canvas.pixmap()
                painter = QPainter(pixmap)
                painter.setPen(QPen(self.current_color, self.line_width, Qt.SolidLine))
                painter.drawLine(self.last_point, current_pos)
                painter.end()
                self.last_point = current_pos
                self.canvas.setPixmap(pixmap)
            else:
                # For shapes, draw on temporary pixmap
                pixmap = self.temp_image.copy()
                painter = QPainter(pixmap)
                painter.setPen(QPen(self.current_color, self.line_width, Qt.SolidLine))
                
                if self.current_tool == "rectangle":
                    painter.drawRect(self.last_point.x(), self.last_point.y(),
                                   current_pos.x() - self.last_point.x(),
                                   current_pos.y() - self.last_point.y())
                elif self.current_tool == "circle":
                    painter.drawEllipse(self.last_point.x(), self.last_point.y(),
                                      current_pos.x() - self.last_point.x(),
                                      current_pos.y() - self.last_point.y())
                elif self.current_tool == "arrow":
                    self.draw_arrow(painter, self.last_point, current_pos)
                elif self.current_tool == "text":
                    self.draw_text(painter, self.last_point, current_pos)
                
                painter.end()
                self.canvas.setPixmap(pixmap)

    def mouse_release(self, event):
        if self.drawing and self.current_image and self.canvas.pixmap():
            current_pos = self.get_image_coordinates(event.pos())
            
            if self.current_tool != "pencil":
                pixmap = self.canvas.pixmap()
                painter = QPainter(pixmap)
                painter.setPen(QPen(self.current_color, self.line_width, Qt.SolidLine))
                
                if self.current_tool == "rectangle":
                    painter.drawRect(self.last_point.x(), self.last_point.y(),
                                   current_pos.x() - self.last_point.x(),
                                   current_pos.y() - self.last_point.y())
                elif self.current_tool == "circle":
                    painter.drawEllipse(self.last_point.x(), self.last_point.y(),
                                      current_pos.x() - self.last_point.x(),
                                      current_pos.y() - self.last_point.y())
                elif self.current_tool == "arrow":
                    self.draw_arrow(painter, self.last_point, current_pos)
                elif self.current_tool == "text":
                    self.draw_text(painter, self.last_point, current_pos)
                
                painter.end()
                self.canvas.setPixmap(pixmap)
            
            self.drawing = False

    def draw_arrow(self, painter, start, end):
        # Draw the line
        painter.drawLine(start, end)
        
        # Calculate arrow head
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        arrow_size = 20
        
        # Calculate arrow head points
        arrow_p1 = QPoint(end.x() - arrow_size * math.cos(angle - math.pi/6),
                         end.y() - arrow_size * math.sin(angle - math.pi/6))
        arrow_p2 = QPoint(end.x() - arrow_size * math.cos(angle + math.pi/6),
                         end.y() - arrow_size * math.sin(angle + math.pi/6))
        
        # Draw arrow head
        painter.drawLine(end, arrow_p1)
        painter.drawLine(end, arrow_p2)

    def save_state(self):
        """Save current state to history"""
        if self.canvas.pixmap():
            self.redo_stack.clear()  # Clear redo stack when new action is performed
            self.history.append(self.canvas.pixmap().copy())
            if len(self.history) > self.max_history:
                self.history.pop(0)

def main():
    app = QApplication(sys.argv)
    window = ImageResizerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
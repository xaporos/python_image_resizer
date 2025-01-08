import os
import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                           QMessageBox, QComboBox, QSlider, QListWidget,
                           QSplitter, QColorDialog)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PIL import Image
import numpy as np

class ImageResizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Resizer")
        self.setGeometry(100, 100, 1200, 800)  # Initial size
        self.setMinimumSize(800, 600)  # Minimum size
        
        # Initialize variables
        self.images = {}  # Dictionary to store image paths and their PIL Image objects
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
            "Custom": 0,
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
        
        # Create toolbar
        toolbar = QHBoxLayout()
        main_layout.addLayout(toolbar)
        
        # Add select button
        self.select_btn = QPushButton("Select Images")
        self.select_btn.clicked.connect(self.select_files)
        toolbar.addWidget(self.select_btn)
        
        # Add size preset dropdown
        toolbar.addWidget(QLabel("Size:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(self.size_presets.keys())
        self.size_combo.currentTextChanged.connect(self.preset_selected)
        toolbar.addWidget(self.size_combo)
        
        # Add quality slider and value label
        toolbar.addWidget(QLabel("Quality:"))
        quality_layout = QHBoxLayout()
        toolbar.addLayout(quality_layout)
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(85)
        self.quality_slider.valueChanged.connect(self.quality_changed)
        quality_layout.addWidget(self.quality_slider)
        
        self.quality_label = QLabel("85%")
        self.quality_label.setMinimumWidth(40)  # Ensure enough space for the text
        quality_layout.addWidget(self.quality_label)
        
        # Add resize button
        self.resize_btn = QPushButton("Resize Selected")
        self.resize_btn.clicked.connect(self.resize_image)
        self.resize_btn.setEnabled(False)
        toolbar.addWidget(self.resize_btn)
        
        # Add resize all button
        self.resize_all_btn = QPushButton("Resize All")
        self.resize_all_btn.clicked.connect(self.resize_all_images)
        self.resize_all_btn.setEnabled(False)
        toolbar.addWidget(self.resize_all_btn)
        
        # Create drawing toolbar
        drawing_toolbar = QHBoxLayout()
        main_layout.addLayout(drawing_toolbar)
        
        # Drawing tools
        self.pencil_btn = QPushButton("🖊 Pencil")
        self.pencil_btn.clicked.connect(lambda: self.set_tool("pencil"))
        self.pencil_btn.setCheckable(True)
        self.pencil_btn.setChecked(True)
        drawing_toolbar.addWidget(self.pencil_btn)
        
        self.rect_btn = QPushButton("⬜ Rectangle")
        self.rect_btn.clicked.connect(lambda: self.set_tool("rectangle"))
        self.rect_btn.setCheckable(True)
        drawing_toolbar.addWidget(self.rect_btn)
        
        self.circle_btn = QPushButton("⭕ Circle")
        self.circle_btn.clicked.connect(lambda: self.set_tool("circle"))
        self.circle_btn.setCheckable(True)
        drawing_toolbar.addWidget(self.circle_btn)
        
        self.arrow_btn = QPushButton("➡ Arrow")
        self.arrow_btn.clicked.connect(lambda: self.set_tool("arrow"))
        self.arrow_btn.setCheckable(True)
        drawing_toolbar.addWidget(self.arrow_btn)
        
        # Add separator
        separator = QLabel(" | ")
        drawing_toolbar.addWidget(separator)
        
        # Add undo/redo buttons
        self.undo_btn = QPushButton("↺ Undo")
        self.undo_btn.clicked.connect(self.undo)
        self.undo_btn.setEnabled(False)
        drawing_toolbar.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("↪ Redo")
        self.redo_btn.clicked.connect(self.redo)
        self.redo_btn.setEnabled(False)
        drawing_toolbar.addWidget(self.redo_btn)
        
        # Add save button
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_changes)
        drawing_toolbar.addWidget(self.save_btn)
        
        # Add separator
        separator2 = QLabel(" | ")
        drawing_toolbar.addWidget(separator2)
        
        # Color picker
        self.color_btn = QPushButton("🎨 Color")
        self.color_btn.clicked.connect(self.choose_color)
        drawing_toolbar.addWidget(self.color_btn)
        
        # Create splitter for list and preview
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create list widget for images
        self.image_list = QListWidget()
        self.image_list.currentItemChanged.connect(self.image_selected)
        splitter.addWidget(self.image_list)
        
        # Create right panel for preview and info
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
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
        splitter.setSizes([300, 900])  # Left panel 300px, right panel 900px

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
            
            # Set the pixmap to the canvas instead of preview_label
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
            self.update_undo_redo_buttons()

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
            if self.size_combo.currentText() != "Custom":
                # Calculate new dimensions based on preset
                target_width = self.size_presets[self.size_combo.currentText()]
                current_width, current_height = self.current_image.size
                
                # Only resize if image is larger than target
                if current_width > target_width:
                    width = target_width
                    height = int(target_width / current_width * current_height)
                else:
                    # Keep original size if image is smaller
                    width, height = current_width, current_height
            else:
                # For custom, maintain original dimensions
                width, height = self.current_image.size
            
            # Resize image
            resized_image = self.current_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Get original file extension
            current_item = self.image_list.currentItem()
            if not current_item:
                return
            file_path = self.get_file_path_from_item(current_item)
            original_ext = os.path.splitext(file_path)[1]
            
            # Save dialog
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Resized Image",
                f"resized_{os.path.basename(file_path)}",
                f"Image Files (*{original_ext})"
            )
            
            if save_path:
                # Save with quality for JPEG
                if save_path.lower().endswith(('.jpg', '.jpeg')):
                    # Use optimize=True for better compression
                    resized_image.save(save_path, 
                                     quality=self.quality_slider.value(),
                                     optimize=True,
                                     progressive=True)
                else:
                    resized_image.save(save_path, optimize=True)
                    
                # Show success message with file size info
                original_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                new_size = os.path.getsize(save_path) / (1024 * 1024)  # MB
                
                QMessageBox.information(self, "Success", 
                    f"Image resized successfully!\n\n"
                    f"Original size: {original_size:.2f} MB\n"
                    f"New size: {new_size:.2f} MB\n"
                    f"Reduction: {((original_size - new_size) / original_size * 100):.1f}%")
                
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
                    # For custom, maintain original dimensions
                    width, height = current_width, current_height
                
                # Resize image
                resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
                
                # Save file
                output_path = os.path.join(output_dir, f"resized_{os.path.basename(file_path)}")
                if output_path.lower().endswith(('.jpg', '.jpeg')):
                    resized_image.save(output_path, 
                                     quality=self.quality_slider.value(),
                                     optimize=True,
                                     progressive=True)
                else:
                    resized_image.save(output_path, optimize=True)
                
                # Track sizes
                total_original_size += os.path.getsize(file_path)
                total_new_size += os.path.getsize(output_path)
                success_count += 1
                
            except Exception as e:
                QMessageBox.warning(self, "Warning", 
                                  f"Failed to resize {os.path.basename(file_path)}: {str(e)}")
        
        if success_count > 0:
            total_original_mb = total_original_size / (1024 * 1024)
            total_new_mb = total_new_size / (1024 * 1024)
            reduction = ((total_original_size - total_new_size) / total_original_size * 100)
            
            QMessageBox.information(self, "Success", 
                f"Successfully resized {success_count} of {len(self.images)} images\n\n"
                f"Total original size: {total_original_mb:.2f} MB\n"
                f"Total new size: {total_new_mb:.2f} MB\n"
                f"Total reduction: {reduction:.1f}%")

    def quality_changed(self, value):
        self.quality_label.setText(f"{value}%")

    def set_tool(self, tool):
        self.current_tool = tool
        # Uncheck all buttons except the selected one
        for btn in [self.pencil_btn, self.rect_btn, self.circle_btn, self.arrow_btn]:
            btn.setChecked(btn.text().split()[1].lower() == tool)

    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color

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
                # For pencil, draw directly and save state periodically
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
            self.update_undo_redo_buttons()

    def undo(self):
        """Undo last action"""
        if self.history:
            # Save current state to redo stack
            current_state = self.canvas.pixmap().copy()
            self.redo_stack.append(current_state)
            
            # Restore previous state
            previous_state = self.history.pop()
            self.canvas.setPixmap(previous_state)
            
            self.update_undo_redo_buttons()

    def redo(self):
        """Redo last undone action"""
        if self.redo_stack:
            # Save current state to history
            current_state = self.canvas.pixmap().copy()
            self.history.append(current_state)
            
            # Restore redo state
            redo_state = self.redo_stack.pop()
            self.canvas.setPixmap(redo_state)
            
            self.update_undo_redo_buttons()

    def update_undo_redo_buttons(self):
        """Update the enabled state of undo/redo buttons"""
        self.undo_btn.setEnabled(bool(self.history))
        self.redo_btn.setEnabled(bool(self.redo_stack))

    def save_changes(self):
        """Save the current image with drawings"""
        if not self.current_image or not self.canvas.pixmap():
            return
            
        try:
            # Get the current pixmap
            pixmap = self.canvas.pixmap()
            
            # Convert QPixmap to QImage
            image = pixmap.toImage()
            
            # Convert QImage to bytes
            ptr = image.bits()
            ptr.setsize(image.byteCount())
            arr = np.array(ptr).reshape(image.height(), image.width(), 4)  # 4 for RGBA
            
            # Convert BGR to RGB (Qt uses BGR, PIL uses RGB)
            arr_rgb = arr[:, :, [2, 1, 0]]  # Reorder color channels
            
            # Create PIL Image
            pil_image = Image.fromarray(arr_rgb)
            
            # Get current file path
            current_item = self.image_list.currentItem()
            if not current_item:
                return
                
            file_path = self.get_file_path_from_item(current_item)
            
            # Update the stored image
            self.images[file_path] = pil_image
            
            # Show success message
            QMessageBox.information(self, "Success", "Changes saved to image!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save changes: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = ImageResizerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
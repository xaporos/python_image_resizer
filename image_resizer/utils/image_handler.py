import os
from PIL import Image
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import Qt, QRectF
import numpy as np
from image_resizer.utils.resizer import ImageResizer

class ImageHandler:
    def __init__(self, parent):
        self.parent = parent
        self.images = {}
        self.current_image = None
        self.edited_images = {}
        self.edited_file_sizes = {}
        self.original_dimensions = {}
        self.current_dimensions = {}
        self.file_sizes = {}
        self.aspect_ratio = 1.0
        self.history = []
        self.redo_stack = []
        self.image_histories = {}
        self.image_redo_stacks = {}
        self.max_history = 10
        self.resizer = ImageResizer()
        
    def select_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.parent,
            "Select Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.tiff)"
        )
        
        if file_paths:
            for file_path in file_paths:
                try:
                    image = Image.open(file_path)
                    self.images[file_path] = image
                    self.parent.image_list.addItem(os.path.basename(file_path))
                    
                    # Store original dimensions and file size
                    self.original_dimensions[file_path] = image.size
                    self.current_dimensions[file_path] = image.size
                    self.file_sizes[file_path] = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
                    
                except Exception as e:
                    QMessageBox.warning(self.parent, "Warning", 
                                      f"Could not load {os.path.basename(file_path)}: {str(e)}")
            
            # Enable buttons if images were loaded
            if self.parent.image_list.count() > 0:
                self.parent.toolbar.resize_btn.setEnabled(True)
                self.parent.toolbar.resize_all_btn.setEnabled(True)
                self.parent.image_list.setCurrentRow(0)

    def save_current(self):
        """Save the current image with drawings"""
        if not self.parent.view.scene().items():
            QMessageBox.warning(self.parent, "Warning", "No image to save!")
            return
            
        current_item = self.parent.image_list.currentItem()
        if not current_item:
            return
            
        file_path = self.get_file_path_from_item(current_item)
        original_ext = os.path.splitext(file_path)[1].lower()
        
        save_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Save Image",
            f"edited_{os.path.basename(file_path)}",
            f"Image Files (*{original_ext})"
        )
        
        if save_path:
            try:
                # Get the pixmap from the scene
                for item in self.parent.view.scene().items():
                    if isinstance(item, QPixmap):
                        item.pixmap().save(save_path)
                        QMessageBox.information(self.parent, "Success", "Image saved successfully!")
                        break
            except Exception as e:
                QMessageBox.critical(self.parent, "Error", f"Failed to save image: {str(e)}")

    def resize_image(self):
        if not self.current_image:
            QMessageBox.warning(self.parent, "Warning", "Please select an image first!")
            return
            
        try:
            current_item = self.parent.image_list.currentItem()
            if not current_item:
                return
                
            file_path = self.get_file_path_from_item(current_item)
            size_preset = self.parent.toolbar.size_combo.currentText()
            quality = self.parent.toolbar.quality_slider.value()
            
            # Resize image
            resized_image = self.resizer.resize_single(self.current_image, size_preset)
            if not resized_image:
                return
            
            # Get save path
            save_path = self.resizer.get_save_path(self.parent, file_path)
            if not save_path:
                return
            
            # Save image
            original_size = os.path.getsize(file_path)
            if self.resizer.save_image(resized_image, save_path, quality):
                new_size = os.path.getsize(save_path)
                orig_mb, new_mb, reduction = self.resizer.calculate_statistics(original_size, new_size)
                
                # Show success message
                QMessageBox.information(
                    self.parent, "Success",
                    f"Image resized successfully!\n\n"
                    f"Original size: {orig_mb:.2f} MB\n"
                    f"New size: {new_mb:.2f} MB\n"
                    f"Reduction: {reduction:.1f}%\n\n"
                    f"Original dimensions: {self.current_image.size[0]}x{self.current_image.size[1]}\n"
                    f"New dimensions: {resized_image.size[0]}x{resized_image.size[1]}"
                )
                
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"An error occurred: {str(e)}")

    def get_file_path_from_item(self, item):
        """Get the full file path from a list item"""
        for path in self.images.keys():
            if os.path.basename(path) == item.text():
                return path
        return None

    def calculate_file_size(self, pixmap, quality=80):
        """Calculate file size based on pixmap data"""
        from PyQt5.QtCore import QByteArray, QBuffer
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.WriteOnly)
        pixmap.save(buffer, "PNG")
        size_in_mb = byte_array.size() / (1024 * 1024)
        buffer.close()
        return size_in_mb 

    def resize_all_images(self):
        if not self.images:
            QMessageBox.warning(self.parent, "Warning", "No images loaded!")
            return
        
        # Get output directory
        output_dir = self.resizer.get_output_directory(self.parent)
        if not output_dir:
            return
        
        success_count = 0
        total_original_size = 0
        total_new_size = 0
        
        size_preset = self.parent.toolbar.size_combo.currentText()
        quality = self.parent.toolbar.quality_slider.value()
        
        for file_path, image in self.images.items():
            try:
                # Resize image
                resized_image = self.resizer.resize_single(image, size_preset)
                if not resized_image:
                    continue
                
                output_path = os.path.join(output_dir, f"resized_{os.path.basename(file_path)}")
                
                # Get original size before saving
                original_size = os.path.getsize(file_path)
                total_original_size += original_size
                
                # Save resized image
                if self.resizer.save_image(resized_image, output_path, quality):
                    new_size = os.path.getsize(output_path)
                    total_new_size += new_size
                    success_count += 1
                
            except Exception as e:
                QMessageBox.warning(
                    self.parent, 
                    "Warning", 
                    f"Failed to resize {os.path.basename(file_path)}: {str(e)}"
                )
        
        if success_count > 0:
            # Show statistics
            orig_mb, new_mb, reduction = self.resizer.calculate_statistics(
                total_original_size, total_new_size)
            
            message = f"Successfully resized {success_count} of {len(self.images)} images\n\n"
            message += f"Total original size: {orig_mb:.2f} MB\n"
            message += f"Total new size: {new_mb:.2f} MB\n"
            message += f"Total reduction: {reduction:.1f}%"
            
            QMessageBox.information(self.parent, "Success", message)

    def image_selected(self, current, previous):
        """Handle image selection from the list"""
        if current:
            # Save current canvas state and history if there is one
            if previous and self.parent.view.scene().items():
                prev_path = self.get_file_path_from_item(previous)
                if prev_path:
                    # Get the pixmap item (should be the last item in the scene)
                    for item in self.parent.view.scene().items():
                        if isinstance(item, QGraphicsPixmapItem):
                            self.edited_images[prev_path] = item.pixmap().copy()
                            break
                    
                    # Save the history for the previous image
                    self.image_histories[prev_path] = self.history.copy()
                    self.image_redo_stacks[prev_path] = self.redo_stack.copy()
                    if prev_path in self.edited_file_sizes:
                        for item in self.parent.view.scene().items():
                            if isinstance(item, QGraphicsPixmapItem):
                                self.edited_file_sizes[prev_path] = self.calculate_file_size(item.pixmap())
            
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
                self.parent.toolbar.undo_btn.setEnabled(len(self.history) > 0)
                self.parent.toolbar.redo_btn.setEnabled(len(self.redo_stack) > 0)

    def update_preview_and_info(self, file_path):
        """Update the preview area and info labels with current image"""
        if self.current_image:
            # Clear previous scene
            self.parent.scene.clear()
            
            # Create preview
            preview = self.current_image.copy()
            preview.thumbnail((800, 800))
            
            # Convert to QPixmap and add to scene
            preview_array = np.array(preview)
            height, width, channels = preview_array.shape
            bytes_per_line = channels * width
            preview_array = preview_array[:, :, ::-1].copy()  # Convert BGR to RGB
            qimage = QImage(preview_array.data, width, height, 
                          bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            
            # Add pixmap to scene
            self.parent.scene.addPixmap(pixmap)
            self.parent.view.setSceneRect(QRectF(pixmap.rect()))
            self.parent.view.fitInView(self.parent.scene.sceneRect(), Qt.KeepAspectRatio)
            
            # Update dimensions and file size
            current_width, current_height = self.current_dimensions[file_path]
            file_size = self.edited_file_sizes.get(file_path, self.file_sizes[file_path])
            
            # Update info labels
            self.parent.size_label.setText(f"Size: {current_width} × {current_height}px")
            self.parent.file_size_label.setText(f"File size: {file_size:.2f}MB")
            
            self.aspect_ratio = current_width / current_height

    def update_preview_with_edited(self, file_path):
        """Update preview with edited version of the image"""
        if self.edited_images.get(file_path):
            # Clear previous scene
            self.parent.scene.clear()
            
            # Add edited pixmap
            edited_pixmap = self.edited_images[file_path]
            self.parent.scene.addPixmap(edited_pixmap)
            
            # Set scene rect and fit view
            self.parent.view.setSceneRect(QRectF(edited_pixmap.rect()))
            self.parent.view.fitInView(self.parent.scene.sceneRect(), Qt.KeepAspectRatio)
            
            # Update dimensions and file size
            current_width, current_height = self.current_dimensions[file_path]
            file_size = self.edited_file_sizes.get(file_path, self.file_sizes[file_path])
            
            # Update info labels
            self.parent.size_label.setText(f"Size: {current_width} × {current_height}px")
            self.parent.file_size_label.setText(f"File size: {file_size:.2f}MB")
            
            self.aspect_ratio = current_width / current_height 
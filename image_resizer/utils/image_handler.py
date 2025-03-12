import os
from PIL import Image
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QGraphicsPixmapItem, QApplication
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import Qt, QRectF, QByteArray, QBuffer
import numpy as np
from image_resizer.utils.resizer import ImageResizer
from io import BytesIO

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
        self.modified = False
        
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
                    
                    # Add to list with custom widget
                    self.parent.add_image_to_list(os.path.basename(file_path))
                    
                    # Store original dimensions and file size
                    self.original_dimensions[file_path] = image.size
                    self.current_dimensions[file_path] = image.size
                    self.file_sizes[file_path] = os.path.getsize(file_path) / (1024 * 1024)
                    
                except Exception as e:
                    QMessageBox.warning(self.parent, "Warning", 
                                      f"Could not load {os.path.basename(file_path)}: {str(e)}")
            
            # Enable buttons if images were loaded
            if self.parent.image_list.count() > 0:
                self.parent.toolbar.resize_btn.setEnabled(True)
                self.parent.toolbar.resize_all_btn.setEnabled(True)
                self.parent.image_list.setCurrentRow(0)

    def resize_image(self):
        """Resize current image without saving"""
        if not self.current_image:
            QMessageBox.warning(self.parent, "Warning", "Please select an image first!")
            return
            
        try:
            # First capture the current state with all modifications
            scene = self.parent.scene
            scene_rect = scene.sceneRect()
            temp_pixmap = QPixmap(int(scene_rect.width()), int(scene_rect.height()))
            temp_pixmap.fill(Qt.white)  # Fill with white instead of transparent
            
            # Render current scene with all modifications
            painter = QPainter(temp_pixmap)
            scene.render(painter)
            painter.end()
            
            # Convert QPixmap to PIL Image for resizing
            temp_buffer = QByteArray()
            buffer = QBuffer(temp_buffer)
            buffer.open(QBuffer.WriteOnly)
            temp_pixmap.save(buffer, 'PNG')
            buffer.close()
            
            # Convert to PIL Image and ensure RGB mode
            modified_image = Image.open(BytesIO(temp_buffer.data()))
            if modified_image.mode in ('RGBA', 'LA'):
                # Convert to RGB by compositing on white background
                background = Image.new('RGB', modified_image.size, 'white')
                if modified_image.mode == 'RGBA':
                    background.paste(modified_image, mask=modified_image.split()[3])
                else:
                    background.paste(modified_image, mask=modified_image.split()[1])
                modified_image = background
            
            # Get current settings and resize
            size_preset = self.parent.toolbar.size_combo.currentText()
            quality = self.parent.toolbar.quality_slider.value()
            
            # Resize the modified image
            resized_image = self.resizer.resize_single(modified_image, size_preset)
            if not resized_image:
                return
            
            # Convert back to QPixmap with quality
            img_byte_arr = BytesIO()
            resized_image.save(img_byte_arr, format='JPEG', quality=quality)
            img_byte_arr.seek(0)
            
            # Convert to QPixmap and update display
            qimage = QImage.fromData(img_byte_arr.getvalue())
            pixmap = QPixmap.fromImage(qimage)
            
            # Save state before updating
            self.save_state()
            
            # Update scene
            self.parent.scene.clear()
            self.parent.scene.addPixmap(pixmap)
            
            # Set scene rect and ensure image fits view
            self.parent.view.setSceneRect(QRectF(pixmap.rect()))
            self.parent.view.fitInView(self.parent.view.sceneRect(), Qt.KeepAspectRatio)
            
            # Force an immediate update to ensure proper fitting
            QApplication.processEvents()
            self.parent.view.fitInView(self.parent.view.sceneRect(), Qt.KeepAspectRatio)
            
            # Mark as modified and store edited version
            self.modified = True
            current_item = self.parent.image_list.currentItem()
            if current_item:
                file_path = self.get_file_path_from_item(current_item)
                if file_path:
                    self.edited_images[file_path] = pixmap
                    self.current_dimensions[file_path] = resized_image.size
                    self.edited_file_sizes[file_path] = len(img_byte_arr.getvalue()) / (1024 * 1024)
                    self.update_info_label()
                
            # Adjust line width for drawing tools based on image size
            if hasattr(self.parent, 'tool_manager'):
                # Get image dimensions
                width, height = self.current_dimensions.get(file_path, (pixmap.width(), pixmap.height()))
                
                # Calculate a scale factor based on image diagonal
                diagonal = (width**2 + height**2)**0.5
                self._update_tool_sizes(diagonal)
        
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"An error occurred: {str(e)}")

    def save_current(self):
        """Save the current image"""
        current_item = self.parent.image_list.currentItem()
        if not current_item:
            return
        
        file_path = self.get_file_path_from_item(current_item)
        if not file_path:
            return

        # Get save path
        save_path = self.resizer.get_save_path(self.parent, file_path)
        if not save_path:
            return
        
        try:
            # Get current pixmap
            pixmap = None
            for item in self.parent.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    pixmap = item.pixmap()
                    break
                
            if not pixmap:
                return
            
            # Save with quality setting
            quality = self.parent.toolbar.quality_slider.value()
            if save_path.lower().endswith(('.jpg', '.jpeg')):
                pixmap.save(save_path, 'JPEG', quality)
            else:
                pixmap.save(save_path, 'PNG')  # PNG doesn't use quality
            
            # Show success message with statistics
            original_size = os.path.getsize(file_path)
            new_size = os.path.getsize(save_path)
            orig_mb, new_mb, reduction = self.resizer.calculate_statistics(original_size, new_size)
            
            QMessageBox.information(
                self.parent, "Success",
                f"Image saved successfully!\n\n"
                f"Original size: {orig_mb:.2f} MB\n"
                f"New size: {new_mb:.2f} MB\n"
                f"Reduction: {reduction:.1f}%"
            )
            
            self.modified = False
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to save image: {str(e)}")

    def resize_all_images(self):
        """Resize all images without saving"""
        if not self.images:
            QMessageBox.warning(self.parent, "Warning", "No images loaded!")
            return
        
        try:
            # Get current settings
            size_preset = self.parent.toolbar.size_combo.currentText()
            quality = self.parent.toolbar.quality_slider.value()
            
            # Store current selection to restore later
            current_item = self.parent.image_list.currentItem()
            
            # Process all images
            for i in range(self.parent.image_list.count()):
                item = self.parent.image_list.item(i)
                file_path = self.get_file_path_from_item(item)
                if not file_path:
                    continue
                
                # Get the original or edited image for this file
                source_image = None
                if file_path in self.edited_images:
                    # Convert QPixmap to PIL Image
                    pixmap = self.edited_images[file_path]
                    temp_buffer = QByteArray()
                    buffer = QBuffer(temp_buffer)
                    buffer.open(QBuffer.WriteOnly)
                    pixmap.save(buffer, 'PNG')
                    buffer.close()
                    source_image = Image.open(BytesIO(temp_buffer.data()))
                else:
                    source_image = self.images[file_path]
                
                # Resize the image
                resized_image = self.resizer.resize_single(source_image, size_preset)
                if not resized_image:
                    continue
                
                # Convert to QPixmap with quality
                img_byte_arr = BytesIO()
                resized_image.save(img_byte_arr, format='JPEG', quality=quality)
                img_byte_arr.seek(0)
                
                # Convert to QPixmap and store
                qimage = QImage.fromData(img_byte_arr.getvalue())
                pixmap = QPixmap.fromImage(qimage)
                
                # Store edited version
                self.edited_images[file_path] = pixmap
                self.current_dimensions[file_path] = resized_image.size
                self.edited_file_sizes[file_path] = len(img_byte_arr.getvalue()) / (1024 * 1024)
                
                # If this is the current image, update the preview
                if item == current_item:
                    self.parent.scene.clear()
                    self.parent.scene.addPixmap(pixmap)
                    self.parent.view.setSceneRect(QRectF(pixmap.rect()))
                    self.parent.view.fitInView(self.parent.view.sceneRect(), Qt.KeepAspectRatio)
                    self.update_info_label()
            
            # Mark all as modified
            self.modified = True
            
            QMessageBox.information(
                self.parent,
                "Success",
                f"Successfully resized {self.parent.image_list.count()} images!"
            )
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"An error occurred: {str(e)}")

    def image_selected(self, current, previous):
        """Handle image selection change"""
        if not current:
            return
        
        # Get file path from item
        file_path = self.get_file_path_from_item(current)
        if not file_path:
            return
        
        # Load the image into the scene
        if file_path in self.edited_images:
            # Use edited version
            pixmap = self.edited_images[file_path]
        else:
            # Convert original PIL Image to QPixmap
            original_image = self.images.get(file_path)
            if original_image:
                # Convert PIL Image to QPixmap
                img_array = np.array(original_image)
                if len(img_array.shape) == 3:  # Color image
                    height, width, channels = img_array.shape
                    bytes_per_line = channels * width
                    # No need to convert BGR to RGB since PIL already gives us RGB
                    qimage = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
                else:  # Grayscale image
                    height, width = img_array.shape
                    bytes_per_line = width
                    qimage = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
                pixmap = QPixmap.fromImage(qimage)
        
        if pixmap and not pixmap.isNull():
            # Update the scene
            self.parent.scene.clear()
            self.parent.scene.addPixmap(pixmap)
            self.parent.view.setSceneRect(QRectF(pixmap.rect()))
            self.parent.view.fitInView(self.parent.scene.sceneRect(), Qt.KeepAspectRatio)
            
            # Update current image reference
            self.current_image = self.images.get(file_path)
        
        # Adjust line width for drawing tools based on image size
        if hasattr(self.parent, 'tool_manager'):
            # Get image dimensions
            width, height = self.current_dimensions.get(file_path, (pixmap.width(), pixmap.height()))
            
            # Calculate a scale factor based on image diagonal
            diagonal = (width**2 + height**2)**0.5
            self._update_tool_sizes(diagonal)
        
        # Update info labels with correct dimensions and file size
        if file_path in self.current_dimensions:
            width, height = self.current_dimensions[file_path]
            self.parent.size_label.setText(f"Size: {width} × {height}px")
            
            # Get file size from stored values
            if file_path in self.edited_images:
                file_size = self.edited_file_sizes.get(file_path, 0)
            else:
                file_size = self.file_sizes.get(file_path, 0)
            
            self.parent.file_size_label.setText(f"File size: {file_size:.2f}MB")

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

    def save_state(self):
        """Save current state to history"""
        # Find the pixmap item
        for item in self.parent.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                current_item = self.parent.image_list.currentItem()
                if current_item:
                    file_path = self.get_file_path_from_item(current_item)
                    if file_path:
                        # Save current state
                        state = {
                            'pixmap': item.pixmap().copy(),
                            'dimensions': self.current_dimensions[file_path],
                            'file_size': self.edited_file_sizes.get(file_path, self.file_sizes[file_path])
                        }
                        self.history.append(state)
                        if len(self.history) > self.max_history:
                            self.history.pop(0)
                        
                        # Clear redo stack when new action is performed
                        self.redo_stack.clear()
                        
                        # Update button states
                        self.parent.toolbar.undo_btn.setEnabled(True)
                        self.parent.toolbar.redo_btn.setEnabled(False)
                        break

    def update_info_label(self):
        """Update the info labels with current image information"""
        current_item = self.parent.image_list.currentItem()
        if current_item:
            file_path = self.get_file_path_from_item(current_item)
            if file_path:
                current_width, current_height = self.current_dimensions[file_path]
                file_size = self.edited_file_sizes.get(file_path, self.file_sizes[file_path])
                
                self.parent.size_label.setText(f"Size: {current_width} × {current_height}px")
                self.parent.file_size_label.setText(f"File size: {file_size:.2f}MB") 

    def undo(self):
        """Undo the last action"""
        if len(self.history) > 0:
            # Get the previous state
            previous_state = self.history.pop()
            
            # Add current state to redo stack
            current_item = self.parent.image_list.currentItem()
            if current_item:
                file_path = self.get_file_path_from_item(current_item)
                if file_path:
                    current_pixmap = None
                    for item in self.parent.scene.items():
                        if isinstance(item, QGraphicsPixmapItem):
                            current_pixmap = item.pixmap()
                            break
                    
                    if current_pixmap:
                        current_state = {
                            'pixmap': current_pixmap.copy(),
                            'dimensions': self.current_dimensions[file_path],
                            'file_size': self.edited_file_sizes.get(file_path, self.file_sizes[file_path])
                        }
                        self.redo_stack.append(current_state)
            
            # Clear scene and restore previous state
            self.parent.scene.clear()
            self.parent.scene.addPixmap(previous_state['pixmap'])
            
            # Update view to fit the image
            self.parent.view.setSceneRect(QRectF(previous_state['pixmap'].rect()))
            self.parent.view.fitInView(self.parent.view.sceneRect(), Qt.KeepAspectRatio)
            
            # Restore dimensions and file size
            if current_item and file_path:
                self.current_dimensions[file_path] = previous_state['dimensions']
                self.edited_file_sizes[file_path] = previous_state['file_size']
                self.edited_images[file_path] = previous_state['pixmap']
            
            # Reset line widths based on restored image size
            width, height = self.current_dimensions[file_path]
            diagonal = (width**2 + height**2)**0.5
            self._update_tool_sizes(diagonal)
            
            # Update info label
            self.update_info_label()
            
            # Update button states
            self.parent.toolbar.undo_btn.setEnabled(len(self.history) > 0)
            self.parent.toolbar.redo_btn.setEnabled(len(self.redo_stack) > 0)

    def redo(self):
        """Redo the last undone action"""
        if len(self.redo_stack) > 0:
            # Get the next state
            next_state = self.redo_stack.pop()
            
            # Add current state to history before clearing
            current_item = self.parent.image_list.currentItem()
            if current_item:
                file_path = self.get_file_path_from_item(current_item)
                if file_path:
                    current_pixmap = None
                    for item in self.parent.scene.items():
                        if isinstance(item, QGraphicsPixmapItem):
                            current_pixmap = item.pixmap()
                            break
                    
                    if current_pixmap:
                        current_state = {
                            'pixmap': current_pixmap.copy(),
                            'dimensions': self.current_dimensions[file_path],
                            'file_size': self.edited_file_sizes.get(file_path, self.file_sizes[file_path])
                        }
                        self.history.append(current_state)
            
            # Clear scene and restore next state
            self.parent.scene.clear()
            self.parent.scene.addPixmap(next_state['pixmap'])
            
            # Update view to fit the image
            self.parent.view.setSceneRect(QRectF(next_state['pixmap'].rect()))
            self.parent.view.fitInView(self.parent.view.sceneRect(), Qt.KeepAspectRatio)
            
            # Restore dimensions and file size
            if current_item and file_path:
                self.current_dimensions[file_path] = next_state['dimensions']
                self.edited_file_sizes[file_path] = next_state['file_size']
                self.edited_images[file_path] = next_state['pixmap']
            
            # Update info label
            self.update_info_label()
            
            # Update button states
            self.parent.toolbar.undo_btn.setEnabled(len(self.history) > 0)
            self.parent.toolbar.redo_btn.setEnabled(len(self.redo_stack) > 0)

    def get_file_path_from_item(self, item):
        """Get the full file path from a list item"""
        if not item:
            return None
        
        # Get the image name from the custom widget
        widget = self.parent.image_list.itemWidget(item)
        if widget:
            image_name = widget.image_name
        else:
            # Fallback to item text if no widget
            image_name = item.text()
        
        # Find matching path
        for path in self.images.keys():
            if os.path.basename(path) == image_name:
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

    def save_all(self):
        """Save all modified images"""
        if not self.images:
            QMessageBox.warning(self.parent, "Warning", "No images loaded!")
            return
        
        # Get output directory
        output_dir = self.resizer.get_output_directory(self.parent)
        if not output_dir:
            return
        
        success_count = 0
        quality = self.parent.toolbar.quality_slider.value()
        
        # Store current selection to restore later
        current_item = self.parent.image_list.currentItem()
        
        try:
            # Process each image in the list
            for i in range(self.parent.image_list.count()):
                item = self.parent.image_list.item(i)
                file_path = self.get_file_path_from_item(item)
                
                if file_path not in self.edited_images:
                    continue
                    
                # Get the edited pixmap for this image
                pixmap = self.edited_images[file_path]
                base_name = os.path.basename(file_path)
                save_path = os.path.join(output_dir, f"edited_{base_name}")
                
                # Save with quality setting
                if save_path.lower().endswith(('.jpg', '.jpeg')):
                    pixmap.save(save_path, 'JPEG', quality)
                else:
                    pixmap.save(save_path, 'PNG')
                    
                success_count += 1
                
        except Exception as e:
            QMessageBox.warning(
                self.parent,
                "Warning",
                f"Failed to save images: {str(e)}"
            )
        finally:
            # Restore original selection
            if current_item:
                self.parent.image_list.setCurrentItem(current_item)
        
        if success_count > 0:
            QMessageBox.information(
                self.parent,
                "Success",
                f"Successfully saved {success_count} images to {output_dir}!"
            ) 

    def rename_image(self, old_name, new_name):
        """Rename image file in the list"""
        # Store current states
        temp_images = self.images.copy()
        temp_edited_images = self.edited_images.copy()
        temp_current_dimensions = self.current_dimensions.copy()
        temp_file_sizes = self.file_sizes.copy()
        temp_edited_file_sizes = self.edited_file_sizes.copy()
        
        # Find the file path
        old_path = None
        for path in temp_images.keys():
            if os.path.basename(path) == old_name:
                old_path = path
                break
        
        if old_path:
            # Create new path
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            
            # Clear all dictionaries
            self.images.clear()
            self.edited_images.clear()
            self.current_dimensions.clear()
            self.file_sizes.clear()
            self.edited_file_sizes.clear()
            
            # Clear the list widget
            self.parent.image_list.clear()
            
            # Rebuild dictionaries with updated paths
            for path, image in temp_images.items():
                if path == old_path:
                    self.images[new_path] = image
                    if old_path in temp_edited_images:
                        self.edited_images[new_path] = temp_edited_images[old_path]
                    if old_path in temp_current_dimensions:
                        self.current_dimensions[new_path] = temp_current_dimensions[old_path]
                    if old_path in temp_file_sizes:
                        self.file_sizes[new_path] = temp_file_sizes[old_path]
                    if old_path in temp_edited_file_sizes:
                        self.edited_file_sizes[new_path] = temp_edited_file_sizes[old_path]
                    # Add to list with new name
                    self.parent.add_image_to_list(new_name)
                else:
                    self.images[path] = image
                    if path in temp_edited_images:
                        self.edited_images[path] = temp_edited_images[path]
                    if path in temp_current_dimensions:
                        self.current_dimensions[path] = temp_current_dimensions[path]
                    if path in temp_file_sizes:
                        self.file_sizes[path] = temp_file_sizes[path]
                    if path in temp_edited_file_sizes:
                        self.edited_file_sizes[path] = temp_edited_file_sizes[path]
                    # Add to list with original name
                    self.parent.add_image_to_list(os.path.basename(path))
            
            # Find and select the renamed item
            for i in range(self.parent.image_list.count()):
                item = self.parent.image_list.item(i)
                if self.parent.image_list.itemWidget(item).image_name == new_name:
                    self.parent.image_list.setCurrentRow(i)
                    break

    def delete_image(self, image_name):
        """Delete image from the list"""
        # Find the file path
        for path in list(self.images.keys()):
            if os.path.basename(path) == image_name:
                # Remove from all dictionaries
                self.images.pop(path)
                self.edited_images.pop(path, None)
                self.current_dimensions.pop(path, None)
                self.file_sizes.pop(path, None)
                
                # Remove from list widget
                for i in range(self.parent.image_list.count()):
                    item = self.parent.image_list.item(i)
                    if self.parent.image_list.itemWidget(item).image_name == image_name:
                        self.parent.image_list.takeItem(i)
                        break
                
                # Clear view if this was the current image
                if not self.images:
                    self.parent.scene.clear()
                    self.parent.size_label.setText("Size: --")
                    self.parent.file_size_label.setText("File size: --")
                break 

    def _update_tool_sizes(self, diagonal, base_diagonal=1500.0):
        """Update line widths and handle sizes for all tools"""
        if not hasattr(self.parent, 'tool_manager'):
            return

        # Get current size preset
        size_preset = self.parent.toolbar.size_combo.currentText()
        
        # Base sizes (before any resize)
        base_line_width = 8  # Increased base width
        base_arrow_size = 45
        
        # Get resize factor and set sizes
        if size_preset == "Small":
            resize_factor = 4
            line_width = base_line_width / resize_factor
            arrow_size = base_arrow_size / resize_factor
        elif size_preset == "Medium":
            resize_factor = 3
            line_width = base_line_width / resize_factor
            arrow_size = base_arrow_size / resize_factor
        elif size_preset == "Large":
            resize_factor = 2
            line_width = base_line_width / resize_factor
            arrow_size = base_arrow_size / resize_factor
        else:  # Original size
            line_width = 20  # Fixed line width for original size
            arrow_size = 40  # Fixed arrow size for original size
        
        # Set sizes for all tools
        for tool_name, tool in self.parent.tool_manager.tools.items():
            if hasattr(tool, 'line_width'):
                tool.line_width = line_width
                
                if tool_name == 'arrow' and hasattr(tool, 'arrow_size'):
                    tool.arrow_size = arrow_size
                
            if hasattr(tool, 'shape_handler') and hasattr(tool.shape_handler, 'handle_size'):
                tool.shape_handler.handle_size = 8 
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
        self.images = {}  # Original images
        self.current_image = None
        self.edited_images = {}  # Images with edits (shapes, resizing)
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
        self.resized_images = set()  # Track which images have been resized
        self.view_scale = {}  # Track view scale for each image
        
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
            # Get current settings
            size_preset = self.parent.toolbar.size_combo.currentText()
            quality = self.parent.toolbar.quality_slider.value()
            
            # Get current file path
            current_item = self.parent.image_list.currentItem()
            if not current_item:
                return
            file_path = self.get_file_path_from_item(current_item)
            if not file_path:
                return

            # Save state before updating
            self.save_state()
            
            # Capture the entire scene including shapes
            scene_rect = self.parent.scene.sceneRect()
            temp_pixmap = QPixmap(int(scene_rect.width()), int(scene_rect.height()))
            temp_pixmap.fill(Qt.white)
            painter = QPainter(temp_pixmap)
            self.parent.scene.render(painter)
            painter.end()
            
            # Convert QPixmap to PIL Image for resizing
            temp_buffer = QByteArray()
            buffer = QBuffer(temp_buffer)
            buffer.open(QBuffer.WriteOnly)
            temp_pixmap.save(buffer, 'PNG')
            buffer.close()
            source_image = Image.open(BytesIO(temp_buffer.data()))
            
            # Convert to RGB mode if necessary
            if source_image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', source_image.size, 'white')
                if source_image.mode == 'RGBA':
                    background.paste(source_image, mask=source_image.split()[3])
                else:
                    background.paste(source_image, mask=source_image.split()[1])
                source_image = background

            # Resize image
            resized_image = self.resizer.resize_single(source_image, size_preset)
            if not resized_image:
                return

            # Get actual dimensions from the resized image
            actual_width, actual_height = resized_image.size
            
            # Convert PIL Image to QPixmap
            img_array = np.array(resized_image)
            height, width, channels = img_array.shape
            bytes_per_line = channels * width
            qimage = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            
            # Clear scene and add new pixmap
            self.parent.scene.clear()
            scene_pixmap_item = self.parent.scene.addPixmap(pixmap)
            scene_pixmap_item.setTransformationMode(Qt.SmoothTransformation)
            
            # Set scene rect to match the new image size
            self.parent.scene.setSceneRect(0, 0, actual_width, actual_height)
            
            # Store edited version and update dimensions
            self.edited_images[file_path] = pixmap
            self.current_dimensions[file_path] = (actual_width, actual_height)
            self.resized_images.add(file_path)  # Mark as resized ONLY when explicitly using resize
            
            # Calculate and store file size
            img_byte_arr = BytesIO()
            resized_image.save(img_byte_arr, format='JPEG', quality=quality)
            self.edited_file_sizes[file_path] = len(img_byte_arr.getvalue()) / (1024 * 1024)
            
            # Update info labels
            self.parent.size_label.setText(f"Size: {actual_width} × {actual_height}px")
            self.parent.file_size_label.setText(f"File size: {self.edited_file_sizes[file_path]:.2f}MB")
            
            # Reset view transform and fit to view
            self.parent.view.resetTransform()
            self.fit_image_to_view()
            
            # Store view scale
            self.view_scale[file_path] = self.parent.view.transform().m11()
            
            # Mark as modified
            self.modified = True
            
            # Update tool sizes with new dimensions
            diagonal = (actual_width**2 + actual_height**2)**0.5
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
            # Check if the image has been modified
            has_shapes = file_path in self.edited_images  # Has shapes or other edits
            is_resized = file_path in self.resized_images  # Has been explicitly resized
            
            if not has_shapes and not is_resized:
                # If not modified at all, just copy the original file
                import shutil
                shutil.copy2(file_path, save_path)
                
                # Show success message with statistics
                original_size = os.path.getsize(file_path)
                new_size = os.path.getsize(save_path)
                orig_mb = original_size / (1024 * 1024)
                
                QMessageBox.information(
                    self.parent, "Success",
                    f"Original image saved successfully!\n\n"
                    f"Size: {orig_mb:.2f} MB"
                )
                return
            
            # Get current pixmap for modified images
            pixmap = None
            for item in self.parent.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    pixmap = item.pixmap()
                    break
            
            if not pixmap:
                return
            
            # Save with quality setting only if the image was resized
            quality = self.parent.toolbar.quality_slider.value() if is_resized else 100
            
            if save_path.lower().endswith(('.jpg', '.jpeg')):
                pixmap.save(save_path, 'JPEG', quality)
            else:
                pixmap.save(save_path, 'PNG')  # PNG doesn't use quality
            
            # Show appropriate success message
            original_size = os.path.getsize(file_path)
            new_size = os.path.getsize(save_path)
            orig_mb, new_mb, reduction = self.resizer.calculate_statistics(original_size, new_size)
            
            if is_resized:
                message = (f"Resized image saved successfully!\n\n"
                          f"Original size: {orig_mb:.2f} MB\n"
                          f"New size: {new_mb:.2f} MB\n"
                          f"Reduction: {reduction:.1f}%")
            else:
                message = (f"Image with shapes saved successfully!\n\n"
                          f"Size: {new_mb:.2f} MB")
            
            QMessageBox.information(self.parent, "Success", message)
            
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
                    scene_pixmap_item = self.parent.scene.addPixmap(pixmap)
                    scene_pixmap_item.setTransformationMode(Qt.SmoothTransformation)
                    
                    # Use the helper method to fit image
                    self.fit_image_to_view()
                    
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

    def fit_image_to_view(self):
        """Helper method to properly fit and center image in view"""
        if self.parent.scene.items():
            # Reset transform and scrollbars first
            self.parent.view.resetTransform()
            self.parent.view.horizontalScrollBar().setValue(0)
            self.parent.view.verticalScrollBar().setValue(0)
            
            # Get the pixmap item
            pixmap_item = None
            for item in self.parent.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    pixmap_item = item
                    break
            
            if pixmap_item:
                # Set scene rect to exactly match the pixmap bounds
                pixmap_rect = pixmap_item.boundingRect()
                self.parent.scene.setSceneRect(pixmap_rect)
                
                # Fit in view while maintaining aspect ratio
                self.parent.view.fitInView(self.parent.scene.sceneRect(), Qt.KeepAspectRatio)
                
                # Process events to ensure view is updated
                QApplication.processEvents()
                
                # Store the view scale for the current image
                current_item = self.parent.image_list.currentItem()
                if current_item:
                    file_path = self.get_file_path_from_item(current_item)
                    if file_path:
                        self.view_scale[file_path] = self.parent.view.transform().m11()
                
                # Reset scrollbars again and fit view again
                self.parent.view.horizontalScrollBar().setValue(0)
                self.parent.view.verticalScrollBar().setValue(0)
                self.parent.view.fitInView(self.parent.scene.sceneRect(), Qt.KeepAspectRatio)

    def image_selected(self, current, previous):
        """Handle image selection change"""
        if not current:
            return
        
        # Get file path from item
        file_path = self.get_file_path_from_item(current)
        if not file_path:
            return
        
        # Clear the scene first
        self.parent.scene.clear()
        
        # Load the image into the scene
        if file_path in self.edited_images:
            # Use edited version with all its modifications
            pixmap = self.edited_images[file_path]
            width, height = self.current_dimensions[file_path]
            file_size = self.edited_file_sizes.get(file_path, self.file_sizes.get(file_path, 0))
            
            # Add pixmap to scene
            scene_pixmap_item = self.parent.scene.addPixmap(pixmap)
            scene_pixmap_item.setTransformationMode(Qt.SmoothTransformation)
            
            # Set scene rect to exactly match the image size
            self.parent.scene.setSceneRect(0, 0, width, height)
            
            # Use the helper method to fit image
            self.fit_image_to_view()
            
            # Clear any existing shape selection
            if hasattr(self.parent, 'tool_manager'):
                current_tool = self.parent.tool_manager.current_tool
                if current_tool and hasattr(current_tool, 'shape_handler'):
                    current_tool.shape_handler.clear_selection()
        else:
            # Use original PIL Image
            original_image = self.images.get(file_path)
            if original_image:
                # Store original dimensions first
                orig_width, orig_height = original_image.size
                self.current_dimensions[file_path] = (orig_width, orig_height)
                
                # Get file size
                file_size = self.file_sizes.get(file_path, 0)
                
                # Convert PIL Image to QPixmap
                img_array = np.array(original_image)
                if len(img_array.shape) == 3:  # Color image
                    array_height, array_width, channels = img_array.shape
                    bytes_per_line = channels * array_width
                    qimage = QImage(img_array.data, array_width, array_height, bytes_per_line, QImage.Format_RGB888)
                else:  # Grayscale image
                    array_height, array_width = img_array.shape
                    bytes_per_line = array_width
                    qimage = QImage(img_array.data, array_width, array_height, bytes_per_line, QImage.Format_Grayscale8)
                pixmap = QPixmap.fromImage(qimage)
                
                # Add pixmap to scene
                scene_pixmap_item = self.parent.scene.addPixmap(pixmap)
                scene_pixmap_item.setTransformationMode(Qt.SmoothTransformation)
                
                # Set scene rect to exactly match the image size
                self.parent.scene.setSceneRect(0, 0, orig_width, orig_height)
                
                # Use the helper method to fit image
                self.fit_image_to_view()
                
                # Use original dimensions for labels and calculations
                width, height = orig_width, orig_height
        
        # Update current image reference
        self.current_image = self.images.get(file_path)
        
        # Update info labels with correct dimensions and file size
        self.parent.size_label.setText(f"Size: {width} × {height}px")
        self.parent.file_size_label.setText(f"File size: {file_size:.2f}MB")
        
        # Adjust line width for drawing tools based on actual image dimensions
        actual_diagonal = (width**2 + height**2)**0.5
        self._update_tool_sizes(actual_diagonal)
        
        # Update the edited_file_sizes if it's not set
        if file_path not in self.edited_file_sizes:
            self.edited_file_sizes[file_path] = self.file_sizes.get(file_path, 0)
            
        # Update undo/redo button states based on the selected image's history
        has_history = file_path in self.image_histories and len(self.image_histories[file_path]) > 0
        has_redo = file_path in self.image_redo_stacks and len(self.image_redo_stacks[file_path]) > 0
        self.parent.toolbar.undo_btn.setEnabled(has_history)
        self.parent.toolbar.redo_btn.setEnabled(has_redo)

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
            scene_pixmap_item = self.parent.scene.addPixmap(edited_pixmap)
            scene_pixmap_item.setTransformationMode(Qt.SmoothTransformation)
            
            # Use helper method to fit image
            self.fit_image_to_view()
            
            # Update dimensions and file size
            current_width, current_height = self.current_dimensions[file_path]
            file_size = self.edited_file_sizes.get(file_path, self.file_sizes[file_path])
            
            # Update info labels
            self.parent.size_label.setText(f"Size: {current_width} × {current_height}px")
            self.parent.file_size_label.setText(f"File size: {file_size:.2f}MB")
            
            self.aspect_ratio = current_width / current_height

    def save_state(self):
        """Save current state for undo/redo"""
        # Get current item and file path
        current_item = self.parent.image_list.currentItem()
        if not current_item:
            return
            
        file_path = self.get_file_path_from_item(current_item)
        if not file_path:
            return
            
        # Clear any active tool or selection before capturing state
        if hasattr(self.parent, 'tool_manager'):
            current_tool = self.parent.tool_manager.current_tool
            if current_tool:
                # Clear shape selection if exists
                if hasattr(current_tool, 'shape_handler'):
                    current_tool.shape_handler.clear_selection()
                # Deactivate crop tool if active
                if hasattr(current_tool, 'is_active') and current_tool.is_active:
                    current_tool.deactivate()
                    # Force an immediate update of the scene after crop tool deactivation
                    QApplication.processEvents()
            
        # Get scene rect
        scene_rect = self.parent.scene.sceneRect()
        
        # Create temporary pixmap of exact scene size
        temp_pixmap = QPixmap(int(scene_rect.width()), int(scene_rect.height()))
        temp_pixmap.fill(Qt.white)  # Use white background
        
        # Create painter and render scene
        painter = QPainter(temp_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        self.parent.scene.render(painter, QRectF(), scene_rect)
        painter.end()
        
        # Store state
        state = {
            'pixmap': temp_pixmap,
            'dimensions': self.current_dimensions.get(file_path, (0, 0)),
            'file_size': self.edited_file_sizes.get(file_path, 0),
            'is_resized': file_path in self.resized_images,
            'view_scale': self.view_scale.get(file_path, 1.0),
            'file_path': file_path
        }
        
        # Initialize history for this image if it doesn't exist
        if file_path not in self.image_histories:
            self.image_histories[file_path] = []
        if file_path not in self.image_redo_stacks:
            self.image_redo_stacks[file_path] = []
        
        # Add state to image-specific history
        self.image_histories[file_path].append(state)
        self.image_redo_stacks[file_path].clear()
        
        # Store the edited version
        self.edited_images[file_path] = temp_pixmap.copy()
        
        # Update button states based on current image's history
        self.parent.toolbar.undo_btn.setEnabled(len(self.image_histories[file_path]) > 0)
        self.parent.toolbar.redo_btn.setEnabled(len(self.image_redo_stacks[file_path]) > 0)
        
        # Update info labels
        self.update_info_label()

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
        """Undo last action"""
        # Get current file path
        current_item = self.parent.image_list.currentItem()
        if not current_item:
            return
            
        current_file_path = self.get_file_path_from_item(current_item)
        if not current_file_path:
            return
            
        # Check if there's history for this image
        if current_file_path not in self.image_histories or not self.image_histories[current_file_path]:
            return
            
        # Clear any active tool or selection before undoing
        if hasattr(self.parent, 'tool_manager'):
            current_tool = self.parent.tool_manager.current_tool
            if current_tool:
                # Clear shape selection if exists
                if hasattr(current_tool, 'shape_handler'):
                    current_tool.shape_handler.clear_selection()
                # Deactivate crop tool if active
                if hasattr(current_tool, 'is_active') and current_tool.is_active:
                    current_tool.deactivate()
            
        # Get the current state for redo
        current_state = self.image_histories[current_file_path].pop()
        if current_file_path not in self.image_redo_stacks:
            self.image_redo_stacks[current_file_path] = []
        self.image_redo_stacks[current_file_path].append(current_state)
        
        if self.image_histories[current_file_path]:
            # Get the previous state
            prev_state = self.image_histories[current_file_path][-1]
            
            # Clear scene
            self.parent.scene.clear()
            
            # Add previous pixmap with proper transformation
            pixmap_item = self.parent.scene.addPixmap(prev_state['pixmap'])
            pixmap_item.setTransformationMode(Qt.SmoothTransformation)
            
            # Set scene rect to match the pixmap size
            width = prev_state['pixmap'].width()
            height = prev_state['pixmap'].height()
            self.parent.scene.setSceneRect(0, 0, width, height)
            
            # Update dimensions and file size
            self.current_dimensions[current_file_path] = prev_state['dimensions']
            self.edited_file_sizes[current_file_path] = prev_state['file_size']
            
            # Update resize state
            if prev_state['is_resized']:
                self.resized_images.add(current_file_path)
            else:
                self.resized_images.discard(current_file_path)
                
            # Store edited version
            self.edited_images[current_file_path] = prev_state['pixmap'].copy()
            
            # Reset view transform and fit image
            self.parent.view.resetTransform()
            self.fit_image_to_view()
            
            # Update line widths based on actual image size
            actual_width, actual_height = self.current_dimensions[current_file_path]
            diagonal = (actual_width**2 + actual_height**2)**0.5
            self._update_tool_sizes(diagonal)
            
            # Update info label
            self.update_info_label()
        else:
            # If no more history, revert to original image
            self.parent.scene.clear()
            if current_file_path in self.images:
                self.edited_images.pop(current_file_path, None)  # Remove edited version
                self.resized_images.discard(current_file_path)  # Remove from resized set
                
                # Convert original PIL Image to QPixmap
                original_image = self.images[current_file_path]
                img_array = np.array(original_image)
                if len(img_array.shape) == 3:  # Color image
                    height, width, channels = img_array.shape
                    bytes_per_line = channels * width
                    qimage = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
                else:  # Grayscale image
                    height, width = img_array.shape
                    bytes_per_line = width
                    qimage = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
                pixmap = QPixmap.fromImage(qimage)
                
                # Add to scene
                pixmap_item = self.parent.scene.addPixmap(pixmap)
                pixmap_item.setTransformationMode(Qt.SmoothTransformation)
                
                # Set scene rect
                self.parent.scene.setSceneRect(0, 0, width, height)
                
                # Reset view transform and fit
                self.parent.view.resetTransform()
                self.fit_image_to_view()
                
                # Update dimensions and info
                self.current_dimensions[current_file_path] = (width, height)
                self.update_info_label()
            
        # Update button states based on current image's history
        self.parent.toolbar.undo_btn.setEnabled(len(self.image_histories.get(current_file_path, [])) > 0)
        self.parent.toolbar.redo_btn.setEnabled(len(self.image_redo_stacks.get(current_file_path, [])) > 0)

    def redo(self):
        """Redo last undone action"""
        # Get current file path
        current_item = self.parent.image_list.currentItem()
        if not current_item:
            return
            
        current_file_path = self.get_file_path_from_item(current_item)
        if not current_file_path:
            return
            
        # Check if there's a redo stack for this image
        if current_file_path not in self.image_redo_stacks or not self.image_redo_stacks[current_file_path]:
            return
            
        # Get the next state
        next_state = self.image_redo_stacks[current_file_path].pop()
        if current_file_path not in self.image_histories:
            self.image_histories[current_file_path] = []
        self.image_histories[current_file_path].append(next_state)
        
        # Clear scene
        self.parent.scene.clear()
        
        # Add next pixmap with proper transformation
        pixmap_item = self.parent.scene.addPixmap(next_state['pixmap'])
        pixmap_item.setTransformationMode(Qt.SmoothTransformation)
        
        # Set scene rect to match the pixmap size
        width = next_state['pixmap'].width()
        height = next_state['pixmap'].height()
        self.parent.scene.setSceneRect(0, 0, width, height)
        
        # Update dimensions and file size
        self.current_dimensions[current_file_path] = next_state['dimensions']
        self.edited_file_sizes[current_file_path] = next_state['file_size']
        
        # Update resize state
        if next_state['is_resized']:
            self.resized_images.add(current_file_path)
        else:
            self.resized_images.discard(current_file_path)
            
        # Store edited version
        self.edited_images[current_file_path] = next_state['pixmap'].copy()
        
        # Reset view transform and fit image
        self.parent.view.resetTransform()
        self.fit_image_to_view()
        
        # Update line widths based on actual image size
        actual_width, actual_height = self.current_dimensions[current_file_path]
        diagonal = (actual_width**2 + actual_height**2)**0.5
        self._update_tool_sizes(diagonal)
        
        # Update info label
        self.update_info_label()
        
        # Update button states based on current image's history
        self.parent.toolbar.undo_btn.setEnabled(len(self.image_histories.get(current_file_path, [])) > 0)
        self.parent.toolbar.redo_btn.setEnabled(len(self.image_redo_stacks.get(current_file_path, [])) > 0)

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
        failed_count = 0
        quality = self.parent.toolbar.quality_slider.value()
        
        # Store current selection to restore later
        current_item = self.parent.image_list.currentItem()
        
        try:
            # Process each image in the list
            total_images = self.parent.image_list.count()
            print(f"Total images to process: {total_images}")
            
            for i in range(total_images):
                item = self.parent.image_list.item(i)
                file_path = self.get_file_path_from_item(item)
                
                if not file_path:
                    print(f"Could not get file path for item {i}")
                    continue
                    
                print(f"Processing image {i + 1}/{total_images}: {os.path.basename(file_path)}")
                
                # Get the pixmap to save - either edited or original
                pixmap = None
                if file_path in self.edited_images:
                    print(f"Using edited version for: {os.path.basename(file_path)}")
                    pixmap = self.edited_images[file_path]
                else:
                    print(f"Using original version for: {os.path.basename(file_path)}")
                    # Use original PIL Image directly
                    original_image = self.images.get(file_path)
                    if original_image:
                        # Save original image with original size
                        base_name = os.path.basename(file_path)
                        original_ext = os.path.splitext(file_path)[1].lower()
                        save_path = os.path.join(output_dir, f"edited_{os.path.splitext(base_name)[0]}{original_ext}")
                        
                        try:
                            if original_ext.lower() in ('.jpg', '.jpeg'):
                                original_image.save(save_path, 'JPEG', quality=quality)
                            else:
                                original_image.save(save_path, original_image.format)
                            success_count += 1
                            print(f"Successfully saved original: {os.path.basename(save_path)}")
                        except Exception as e:
                            print(f"Failed to save {os.path.basename(save_path)}: {str(e)}")
                            failed_count += 1
                        continue
                
                if not pixmap:
                    print(f"No pixmap found for: {os.path.basename(file_path)}")
                    failed_count += 1
                    continue
                    
                base_name = os.path.basename(file_path)
                
                # Ensure proper file extension is preserved
                original_ext = os.path.splitext(file_path)[1].lower()
                if not original_ext:
                    print(f"No extension found, using .jpg for: {base_name}")
                    original_ext = '.jpg'
                elif original_ext not in ['.jpg', '.jpeg', '.png']:
                    print(f"Unsupported extension {original_ext}, converting to .jpg for: {base_name}")
                    original_ext = '.jpg'
                
                # Create save path with proper extension
                save_path = os.path.join(output_dir, f"edited_{os.path.splitext(base_name)[0]}{original_ext}")
                print(f"Saving to: {save_path}")
                
                try:
                    # Save with quality setting
                    if original_ext.lower() in ('.jpg', '.jpeg'):
                        pixmap.save(save_path, 'JPEG', quality)
                    else:
                        pixmap.save(save_path, 'PNG')  # PNG doesn't use quality
                        
                    success_count += 1
                    print(f"Successfully saved: {os.path.basename(save_path)}")
                except Exception as e:
                    print(f"Failed to save {os.path.basename(save_path)}: {str(e)}")
                    failed_count += 1
                    
        except Exception as e:
            print(f"Error in save_all: {str(e)}")
            QMessageBox.warning(
                self.parent,
                "Warning",
                f"Failed to save images: {str(e)}"
            )
        finally:
            # Restore original selection
            if current_item:
                self.parent.image_list.setCurrentItem(current_item)
        
        # Show final results
        if success_count > 0:
            message = f"Successfully saved {success_count} images to {output_dir}!"
            if failed_count > 0:
                message += f"\nFailed to save {failed_count} images."
            QMessageBox.information(
                self.parent,
                "Success",
                message
            )
        elif failed_count > 0:
            QMessageBox.warning(
                self.parent,
                "Warning",
                f"Failed to save any images. {failed_count} images failed."
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

        # Get current item and file path
        current_item = self.parent.image_list.currentItem()
        if not current_item:
            return
        
        file_path = self.get_file_path_from_item(current_item)
        if not file_path:
            return
        
        # Get actual image dimensions
        actual_width, actual_height = self.current_dimensions.get(file_path, (0, 0))
        if actual_width == 0 or actual_height == 0:
            return
        
        # Calculate actual diagonal based on real image dimensions
        actual_diagonal = (actual_width**2 + actual_height**2)**0.5
        
        # Use fixed scale factor of 1 for handles as it works well
        handle_scale_factor = 1.0
        
        # For lines, use a scale factor based on whether the image is resized
        if file_path in self.resized_images:
            line_scale_factor = 1.0
        else:
            line_scale_factor = 3.0  # Higher scale factor for unresized images
        
        # Base sizes - different for lines and handles
        base_line_width = 2
        base_handle_size = 8
        base_arrow_size = 15
        
        # Get view scale for this image
        view_scale = self.view_scale.get(file_path, 1.0)
        
        # Calculate final sizes with different scale factors
        line_width = max(1, base_line_width * line_scale_factor)
        handle_size = max(4, base_handle_size * handle_scale_factor)
        arrow_size = max(8, base_arrow_size * line_scale_factor)  # Arrow size follows line scaling
        
        print(f"Image dimensions: {actual_width}x{actual_height}")
        print(f"Line scale factor: {line_scale_factor:.2f}")
        print(f"Handle scale factor: {handle_scale_factor:.2f}")
        print(f"View scale: {view_scale:.2f}")
        print(f"Is resized: {file_path in self.resized_images}")
        print(f"Has shapes: {file_path in self.edited_images}")
        print(f"Calculated sizes - Line: {line_width:.2f}, Handle: {handle_size:.2f}, Arrow: {arrow_size:.2f}")
        
        # Update sizes for all tools
        for tool_name, tool in self.parent.tool_manager.tools.items():
            if hasattr(tool, 'line_width'):
                tool.line_width = line_width
                if tool_name == 'arrow' and hasattr(tool, 'arrow_size'):
                    tool.arrow_size = arrow_size
            if hasattr(tool, 'shape_handler') and hasattr(tool.shape_handler, 'handle_size'):
                tool.shape_handler.handle_size = handle_size 
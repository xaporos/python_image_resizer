import os
from PIL import Image
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QGraphicsPixmapItem, QApplication
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import Qt, QRectF, QByteArray, QBuffer, QTimer
import numpy as np
from image_resizer.utils.resizer import ImageResizer
from io import BytesIO
import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

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
        self.redo_stack = {}
        self.image_histories = {}
        self.image_redo_stacks = {}
        self.max_history = 10
        self.resizer = ImageResizer()
        self.modified = False
        self.resized_images = set()  # Track which images have been resized
        self.view_scale = {}  # Track view scale for each image
        self.heic_message_shown = False  # Track whether HEIC conversion message has been shown
        
    def select_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.parent,
            "Select Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.heic *.HEIC)"
        )
        
        if file_paths:
            has_heic = any(file_path.lower().endswith(('.heic')) for file_path in file_paths)
            
            # Show HEIC conversion message once per session if HEIC files are loaded
            if has_heic and not self.heic_message_shown:
                QMessageBox.information(
                    self.parent,
                    "HEIC Image Support",
                    "HEIC images will be converted to JPEG format when edited or saved.\n\n"
                    "Note: While we apply optimized compression, the saved file may still be "
                    "larger than the original HEIC file due to format differences."
                )
                self.heic_message_shown = True
            
            for file_path in file_paths:
                try:
                    # Check if it's a HEIC file
                    is_heic = file_path.lower().endswith(('.heic'))
                    
                    # Open the image based on its format
                    image = Image.open(file_path)
                    
                    # Convert HEIC to RGB if needed
                    if is_heic and image.mode == 'RGBA':
                        image = image.convert('RGB')
                    
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
                self.parent.toolbar.save_btn.setEnabled(True)
                self.parent.toolbar.save_all_btn.setEnabled(True)
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

            # Check if it's a HEIC file
            is_heic = file_path.lower().endswith('.heic')

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
            is_modified = has_shapes or is_resized
            
            # Check if the original file exists (it might not if the image was renamed)
            original_file_exists = os.path.exists(file_path)
            
            # Check if original is HEIC
            is_heic_source = file_path.lower().endswith('.heic')
            
            # Ensure save_path has a valid image extension
            save_ext = os.path.splitext(save_path)[1].lower()
            if not save_ext or save_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                # Use the extension from the original file, but convert HEIC to JPG
                orig_ext = os.path.splitext(file_path)[1].lower()
                if not orig_ext or orig_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'] or orig_ext == '.heic':
                    # Default to .jpg if no valid extension or if HEIC
                    save_path = save_path + '.jpg'
                else:
                    save_path = save_path + orig_ext
            
            # Get the pixmap to save
            pixmap = None
            if file_path in self.edited_images:
                # For images with shapes or edits, use the edited image directly
                pixmap = self.edited_images[file_path]
            elif original_file_exists:
                # For unmodified images, use the original
                original_image = self.images.get(file_path)
                if original_image:
                    # Convert PIL image to RGB if it's RGBA
                    if original_image.mode == 'RGBA':
                        original_image = original_image.convert('RGB')
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
            
            if not pixmap:
                QMessageBox.critical(self.parent, "Error", "Could not get image data to save.")
                return
            
            # Save the image with appropriate settings
            save_ext = os.path.splitext(save_path)[1].lower()
            if save_ext in ['.jpg', '.jpeg']:
                # For JPEG, we need to handle quality settings
                if is_modified or is_heic_source:
                    # Only apply quality settings if the image has been modified or if from HEIC
                    quality = self.parent.toolbar.quality_slider.value()
                    
                    # For HEIC sources, apply higher compression to better match original file size
                    if is_heic_source and file_path in self.edited_images:
                        # Apply additional compression for HEIC sources
                        adjusted_quality = max(30, int(quality * 0.6))  # Scale down quality but keep minimum 30
                        pixmap.save(save_path, 'JPEG', adjusted_quality)
                    else:
                        pixmap.save(save_path, 'JPEG', quality)
                else:
                    # For unmodified images, save with maximum quality
                    pixmap.save(save_path, 'JPEG', 100)
            else:
                # For other formats, use their native format with maximum quality
                format_map = {
                    '.png': ('PNG', -1),  # -1 means maximum compression for PNG
                    '.gif': ('GIF', None),
                    '.bmp': ('BMP', None),
                    '.tiff': ('TIFF', None)
                }
                img_format, quality = format_map.get(save_ext, ('PNG', -1))
                if quality is not None:
                    pixmap.save(save_path, img_format, quality)
                else:
                    pixmap.save(save_path, img_format)
            
            # Show appropriate success message
            if original_file_exists:
                original_size = os.path.getsize(file_path)
                new_size = os.path.getsize(save_path)
                orig_mb, new_mb, reduction = self.resizer.calculate_statistics(original_size, new_size)
                
                if reduction < 0:
                    message = (f"Image saved successfully!\n\n"
                              f"Size: {new_mb:.2f} MB")
                else:
                    if is_resized:
                        message = (f"Resized image saved successfully!\n\n"
                                  f"Original size: {orig_mb:.2f} MB\n"
                                  f"New size: {new_mb:.2f} MB\n"
                                  f"Reduction: {reduction:.1f}%")
                    elif is_heic_source:
                        message = (f"HEIC image converted and saved successfully!\n\n"
                                  f"Original size: {orig_mb:.2f} MB\n"
                                  f"New size: {new_mb:.2f} MB\n"
                                  f"Reduction: {reduction:.1f}%")
                    elif has_shapes:
                        message = (f"Modified image saved successfully!\n\n"
                                  f"Original size: {orig_mb:.2f} MB\n"
                                  f"New size: {new_mb:.2f} MB\n"
                                  f"Reduction: {reduction:.1f}%")
                    else:
                        message = (f"Image saved successfully!\n\n"
                                  f"Size: {new_mb:.2f} MB")
            else:
                # For renamed images where original file doesn't exist
                new_size = os.path.getsize(save_path)
                new_mb = new_size / (1024 * 1024)
                message = (f"Image saved successfully!\n\n"
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
            
        # Show overlay
        self.parent.overlay.show()
        self.parent.overlay.resize(self.parent.size())
        # Set overlay text for resizing
        self.parent.overlay.label.setText("Resizing images...")
        
        # Force UI update and add a small delay to ensure overlay is visible
        QApplication.processEvents()
        QTimer.singleShot(100, self._perform_resize_all)
        
    def _perform_resize_all(self):
        """Perform the actual resize all operation"""
        try:
            # Get current settings
            size_preset = self.parent.toolbar.size_combo.currentText()
            quality = self.parent.toolbar.quality_slider.value()
            
            # Store current selection to restore later
            current_item = self.parent.image_list.currentItem()
            
            # Collect all items to process
            items_to_process = []
            for i in range(self.parent.image_list.count()):
                item = self.parent.image_list.item(i)
                file_path = self.get_file_path_from_item(item)
                if file_path:
                    items_to_process.append((item, file_path))
            
            # Update UI before processing starts
            QApplication.processEvents()
            
            # Process all images
            for idx, (item, file_path) in enumerate(items_to_process):
                # Update overlay text with progress
                self.parent.overlay.label.setText(f"Resizing images... ({idx + 1}/{len(items_to_process)})")
                QApplication.processEvents()
                
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
                    
                # Ensure source image is in RGB mode if needed
                if source_image.mode == 'RGBA':
                    source_image = source_image.convert('RGB')
                
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
                    
                    # Set scene rect to match the new image size
                    self.parent.scene.setSceneRect(0, 0, resized_image.size[0], resized_image.size[1])
                    
                    # Reset view transform and fit to view
                    self.parent.view.resetTransform()
                    self.fit_image_to_view()
                    
                    # Store view scale for current image
                    self.view_scale[file_path] = self.parent.view.transform().m11()
                    
                    self.update_info_label()
                
                # Force UI update every few processed files
                if idx % 3 == 0:
                    QApplication.processEvents()
            
            # Mark all as modified
            self.modified = True
            
            # Final UI update before showing success dialog
            QApplication.processEvents()
            
            # Create custom success dialog
            success_dialog = QMessageBox(self.parent)
            success_dialog.setWindowTitle("Success")
            success_dialog.setText(f"Successfully resized {len(items_to_process)} images!")
            success_dialog.setIcon(QMessageBox.Information)
            
            # Style the dialog to match app theme
            success_dialog.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #333333;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 10px;
                }
                QPushButton {
                    color: black;
                    background-color: white;
                    padding: 8px 16px;
                    border: 1px solid #DBDCDA;
                    border-radius: 4px;
                    font-weight: 500;
                    min-width: 80px;
                }
                QPushButton:hover {
                    border: 1px solid #242424;
                }
            """)
            
            # Show the dialog
            success_dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"An error occurred: {str(e)}")
        finally:
            # Hide overlay
            self.parent.overlay.hide()
            QApplication.processEvents()

    def fit_image_to_view(self):
        """Helper method to properly fit and center image in view"""
        if self.parent.scene.items():
            # Reset transform and scrollbars first
            self.parent.view.resetTransform()
            self.parent.view.horizontalScrollBar().setValue(0)
            self.parent.view.verticalScrollBar().setValue(0)
            
            # Get the scene rect
            scene_rect = self.parent.scene.sceneRect()
            
            # First fit attempt
            self.parent.view.fitInView(scene_rect, Qt.KeepAspectRatio)
            QApplication.processEvents()
            
            # Force scene update
            self.parent.scene.update()
            QApplication.processEvents()
            
            # Final fit attempt
            self.parent.view.fitInView(scene_rect, Qt.KeepAspectRatio)
            QApplication.processEvents()
            
            # Store the view scale for the current image
            current_item = self.parent.image_list.currentItem()
            if current_item:
                file_path = self.get_file_path_from_item(current_item)
                if file_path:
                    self.view_scale[file_path] = self.parent.view.transform().m11()
            
            # Reset scrollbars one final time
            self.parent.view.horizontalScrollBar().setValue(0)
            self.parent.view.verticalScrollBar().setValue(0)

    def image_selected(self, current, previous):
        """Handle image selection change"""
        # Make sure to save the eraser state of the previous image before switching
        if previous and hasattr(self.parent, 'tool_manager'):
            prev_file_path = self.get_file_path_from_item(previous)
            if prev_file_path and prev_file_path in self.edited_images:
                # Force save state to preserve eraser changes before switching
                # Get current tool to check if it's the eraser
                current_tool = self.parent.tool_manager.current_tool
                if current_tool and current_tool.__class__.__name__ == 'EraserTool':
                    # Deactivate eraser explicitly to ensure it saves properly
                    current_tool.deactivate()
                
                # Save state explicitly for the previous image
                self.save_state(prev_file_path)
        
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
        
        # Update current tool's image path if it's the eraser
        if hasattr(self.parent, 'tool_manager'):
            current_tool = self.parent.tool_manager.current_tool
            if current_tool and current_tool.__class__.__name__ == 'EraserTool':
                current_tool.current_image_path = file_path
                # Update temp_image to match current pixmap
                for item in self.parent.scene.items():
                    if isinstance(item, QGraphicsPixmapItem):
                        current_tool.temp_image = item.pixmap().copy()
                        break

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

    def save_state(self, specific_file_path=None):
        """Save current state for undo/redo"""
        current_item = self.parent.image_list.currentItem()
        if not current_item:
            return
            
        file_path = specific_file_path or self.get_file_path_from_item(current_item)
        if not file_path:
            return
        
        # Check if this is a crop operation
        is_crop_operation = False
        if hasattr(self.parent, 'tool_manager'):
            current_tool = self.parent.tool_manager.current_tool
            if current_tool:
                is_crop_operation = current_tool.__class__.__name__.lower() == 'croptool'
        
        # Clear any active tool or selection
        if hasattr(self.parent, 'tool_manager'):
            current_tool = self.parent.tool_manager.current_tool
            if current_tool:
                if hasattr(current_tool, 'shape_handler'):
                    current_tool.shape_handler.clear_selection()
                if hasattr(current_tool, 'is_active') and current_tool.is_active:
                    current_tool.deactivate()
                    QApplication.processEvents()
        
        # Get scene rect and dimensions
        scene_rect = self.parent.scene.sceneRect()
        width = int(scene_rect.width())
        height = int(scene_rect.height())
        
        # Create pixmap with white background
        temp_pixmap = QPixmap(width, height)
        temp_pixmap.fill(Qt.white)
        
        # Create painter with high quality settings
        painter = QPainter(temp_pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        
        # Render the scene at the correct dimensions
        self.parent.scene.render(painter, QRectF(temp_pixmap.rect()), scene_rect)
        painter.end()
        
        # Initialize history if needed
        if file_path not in self.image_histories:
            self.image_histories[file_path] = []
        
        # Create state
        state = {
            'pixmap': temp_pixmap,
            'dimensions': (width, height),
            'scene_rect': scene_rect,
            'file_size': self.calculate_file_size(temp_pixmap),
            'is_resized': file_path in self.resized_images,
            'view_scale': self.view_scale.get(file_path, 1.0),
            'file_path': file_path,
            'is_crop': is_crop_operation
        }
        
        # Add state to history
        self.image_histories[file_path].append(state)
        
        # Store edited version
        self.edited_images[file_path] = temp_pixmap.copy()
        
        # Update dimensions and file size
        self.current_dimensions[file_path] = (width, height)
        self.edited_file_sizes[file_path] = state['file_size']
        
        # Clear redo stack and disable redo button
        if file_path in self.image_redo_stacks:
            self.image_redo_stacks[file_path].clear()
        self.parent.toolbar.redo_btn.setEnabled(False)
        
        # Update undo button state
        self.parent.toolbar.undo_btn.setEnabled(len(self.image_histories.get(file_path, [])) > 0)
        
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
        current_item = self.parent.image_list.currentItem()
        if not current_item:
            return
            
        current_file_path = self.get_file_path_from_item(current_item)
        if not current_file_path or current_file_path not in self.image_histories:
            return
            
        # Clear any active tool or selection
        if hasattr(self.parent, 'tool_manager'):
            current_tool = self.parent.tool_manager.current_tool
            if current_tool:
                if hasattr(current_tool, 'shape_handler'):
                    current_tool.shape_handler.clear_selection()
                if hasattr(current_tool, 'is_active') and current_tool.is_active:
                    current_tool.deactivate()
                    QApplication.processEvents()
        
        # Get current state
        if not self.image_histories[current_file_path]:
            return
            
        current_state = self.image_histories[current_file_path].pop()
        
        # Initialize redo stack if needed
        if current_file_path not in self.image_redo_stacks:
            self.image_redo_stacks[current_file_path] = []
        
        # Add current state to redo stack
        self.image_redo_stacks[current_file_path].append(current_state)
        
        # If we have more history, restore the previous state
        if self.image_histories[current_file_path]:
            prev_state = self.image_histories[current_file_path][-1]
            self._apply_state(prev_state, current_file_path)
            
            # If we just undid a resize operation, clear redo stack and disable redo button
            if current_state.get('is_resized', False) and not prev_state.get('is_resized', False):
                self.image_redo_stacks[current_file_path].clear()
                self.parent.toolbar.redo_btn.setEnabled(False)
            else:
                # Update redo button state normally
                self.parent.toolbar.redo_btn.setEnabled(len(self.image_redo_stacks.get(current_file_path, [])) > 0)
            
            # Update file size label with the current state's file size
            current_file_size = self.calculate_file_size(prev_state['pixmap'])
            self.edited_file_sizes[current_file_path] = current_file_size
            self.parent.file_size_label.setText(f"File size: {current_file_size:.2f}MB")
            
            # Force UI update
            self.parent.file_size_label.repaint()
            QApplication.processEvents()
        else:
            # If no more history, revert to original
            self._revert_to_original(current_file_path)
            
            # Update file size label with original file size
            original_file_size = self.file_sizes[current_file_path]
            self.edited_file_sizes[current_file_path] = original_file_size
            self.parent.file_size_label.setText(f"File size: {original_file_size:.2f}MB")
            
            # Force UI update
            self.parent.file_size_label.repaint()
            QApplication.processEvents()
        
        # Update undo button state
        self.parent.toolbar.undo_btn.setEnabled(len(self.image_histories.get(current_file_path, [])) > 0)

    def _apply_state(self, state, file_path):
        """Helper method to apply a state"""
        # Clear scene and update
        self.parent.scene.clear()
        QApplication.processEvents()
        
        # Add pixmap
        pixmap_item = self.parent.scene.addPixmap(state['pixmap'])
        pixmap_item.setTransformationMode(Qt.SmoothTransformation)
        
        # Get dimensions from state
        width, height = state['dimensions']
        
        # Set scene rect
        self.parent.scene.setSceneRect(0, 0, width, height)
        
        # Calculate current file size
        current_file_size = self.calculate_file_size(state['pixmap'])
        
        # Update dimensions and file size
        self.current_dimensions[file_path] = state['dimensions']
        self.edited_file_sizes[file_path] = current_file_size
        
        # Update resize state
        if state['is_resized']:
            self.resized_images.add(file_path)
        else:
            self.resized_images.discard(file_path)
        
        # Store edited version
        self.edited_images[file_path] = state['pixmap'].copy()
        
        # Reset view transform
        self.parent.view.resetTransform()
        
        # Get view and scene rects
        view_rect = self.parent.view.viewport().rect()
        scene_rect = self.parent.scene.sceneRect()
        
        # Calculate scale to fit
        scale_w = view_rect.width() / scene_rect.width()
        scale_h = view_rect.height() / scene_rect.height()
        scale = min(scale_w, scale_h)
        
        # Apply scale
        self.parent.view.scale(scale, scale)
        
        # Center in view
        self.parent.view.centerOn(scene_rect.center())
        
        # Store the view scale
        self.view_scale[file_path] = scale
        
        # Update tool sizes
        actual_width, actual_height = self.current_dimensions[file_path]
        diagonal = (actual_width**2 + actual_height**2)**0.5
        self._update_tool_sizes(diagonal)
        
        # Update info labels with current dimensions and file size
        self.parent.size_label.setText(f"Size: {width} × {height}px")
        self.parent.file_size_label.setText(f"File size: {current_file_size:.2f}MB")
        
        # Force scene update
        self.parent.scene.update()
        QApplication.processEvents()

    def _revert_to_original(self, file_path):
        """Helper method to revert to original image"""
        # Clear scene
        self.parent.scene.clear()
        
        if file_path in self.images:
            self.edited_images.pop(file_path, None)
            self.resized_images.discard(file_path)
            
            # Convert original image to pixmap
            original_image = self.images[file_path]
            img_array = np.array(original_image)
            if len(img_array.shape) == 3:
                height, width, channels = img_array.shape
                bytes_per_line = channels * width
                qimage = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
            else:
                height, width = img_array.shape
                bytes_per_line = width
                qimage = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            
            # Add to scene
            pixmap_item = self.parent.scene.addPixmap(pixmap)
            pixmap_item.setTransformationMode(Qt.SmoothTransformation)
            
            # Update scene rect
            self.parent.scene.setSceneRect(0, 0, width, height)
            
            # Update dimensions
            self.current_dimensions[file_path] = (width, height)
            
            # Reset view and fit image
            self.parent.view.resetTransform()
            self.fit_image_to_view()
            
            # Update tool sizes
            diagonal = (width**2 + height**2)**0.5
            self._update_tool_sizes(diagonal)
            
            # Update info label
            self.update_info_label()

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
            
        # Clear any active tool or selection before redoing
        if hasattr(self.parent, 'tool_manager'):
            current_tool = self.parent.tool_manager.current_tool
            if current_tool:
                # Clear shape selection if exists
                if hasattr(current_tool, 'shape_handler'):
                    current_tool.shape_handler.clear_selection()
                # Deactivate crop tool if active
                if hasattr(current_tool, 'is_active') and current_tool.is_active:
                    current_tool.deactivate()
                    # Force an immediate update of the scene
                    QApplication.processEvents()
        
        # Get the next state
        next_state = self.image_redo_stacks[current_file_path].pop()
        
        # Initialize history if needed
        if current_file_path not in self.image_histories:
            self.image_histories[current_file_path] = []
            
        # Add state back to history
        self.image_histories[current_file_path].append(next_state)
        
        # Apply the state
        self._apply_state(next_state, current_file_path)
        
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
        """Calculate file size based on pixmap data using the same format that will be used for saving"""
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.WriteOnly)
        
        # Get current file path to determine format
        current_item = self.parent.image_list.currentItem()
        if current_item:
            file_path = self.get_file_path_from_item(current_item)
            if file_path:
                # Get file extension
                file_ext = os.path.splitext(file_path)[1].lower()
                
                # Check if this is a HEIC source file
                is_heic_source = file_path.lower().endswith('.heic')
                
                # Use same quality setting for both .jpg and .jpeg
                if file_ext in ['.jpg', '.jpeg'] or is_heic_source:
                    # For HEIC source files that have been edited, use higher compression
                    # to compensate for the loss of HEIC's efficient compression
                    if is_heic_source and file_path in self.edited_images:
                        # Get slider quality but apply additional compression
                        base_quality = self.parent.toolbar.quality_slider.value()
                        adjusted_quality = max(30, int(base_quality * 0.6))  # Scale down quality but keep minimum 30
                        pixmap.save(buffer, "JPEG", adjusted_quality)
                    else:
                        quality = self.parent.toolbar.quality_slider.value()
                        pixmap.save(buffer, "JPEG", quality)
                else:
                    # For other formats, use their native format
                    format_map = {
                        '.png': ('PNG', -1),
                        '.gif': ('GIF', None),
                        '.bmp': ('BMP', None),
                        '.tiff': ('TIFF', None)
                    }
                    img_format, quality = format_map.get(file_ext, ('PNG', -1))
                    if quality is not None:
                        pixmap.save(buffer, img_format, quality)
                    else:
                        pixmap.save(buffer, img_format)
                
                size_in_mb = byte_array.size() / (1024 * 1024)
                buffer.close()
                return size_in_mb
        
        # Default to PNG with maximum compression if no file path available
        pixmap.save(buffer, "PNG", -1)
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
        
        # Show overlay while saving
        self.parent.overlay.show()
        self.parent.overlay.resize(self.parent.size())
        # Change the overlay label text for saving
        self.parent.overlay.label.setText("Saving images...")
        
        # Force UI update and add a small delay to ensure overlay is visible
        QApplication.processEvents()
        QTimer.singleShot(100, lambda: self._perform_save_all(output_dir))
        
    def _perform_save_all(self, output_dir):
        """Perform the actual save all operation"""
        success_count = 0
        failed_count = 0
        
        # Store current selection to restore later
        current_item = self.parent.image_list.currentItem()
        
        try:
            # First, collect all items to process to avoid issues with renamed images
            items_to_process = []
            for i in range(self.parent.image_list.count()):
                item = self.parent.image_list.item(i)
                file_path = self.get_file_path_from_item(item)
                if file_path:
                    items_to_process.append((item, file_path))
            
            # Update UI before processing starts
            QApplication.processEvents()
            
            # Process each item
            for idx, (item, file_path) in enumerate(items_to_process):
                # Check if the image has been modified
                has_shapes = file_path in self.edited_images  # Has shapes or other edits
                is_resized = file_path in self.resized_images  # Has been explicitly resized
                is_heic = file_path.lower().endswith('.heic')  # Is HEIC format
                is_modified = has_shapes or is_resized or is_heic  # Consider HEIC as modified
                
                # Skip unmodified images
                if not is_modified:
                    continue
                
                # Update overlay text with progress
                self.parent.overlay.label.setText(f"Saving images... ({idx + 1}/{len(items_to_process)})")
                QApplication.processEvents()
                
                # Check if the original file exists
                original_file_exists = os.path.exists(file_path)
                
                # Create save path with proper extension
                base_name = os.path.basename(file_path)
                original_ext = os.path.splitext(file_path)[1].lower()
                
                # Ensure we have a valid extension, convert HEIC to JPG
                if not original_ext or original_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'] or original_ext == '.heic':
                    original_ext = '.jpg'
                
                save_path = os.path.join(output_dir, f"{os.path.splitext(base_name)[0]}{original_ext}")
                
                try:
                    # Get the pixmap to save
                    pixmap = None
                    if file_path in self.edited_images:
                        # For images with shapes, use the edited image directly
                        pixmap = self.edited_images[file_path]
                    elif original_file_exists:
                        # For unmodified images, use the original
                        original_image = self.images.get(file_path)
                        if original_image:
                            # Convert PIL image to RGB if it's RGBA
                            if original_image.mode == 'RGBA':
                                original_image = original_image.convert('RGB')
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
                    
                    if not pixmap:
                        failed_count += 1
                        continue
                    
                    # Convert pixmap to RGB if saving as JPEG
                    save_ext = os.path.splitext(save_path)[1].lower()
                    if save_ext in ['.jpg', '.jpeg']:
                        # Convert to RGB by saving to a temporary buffer and reloading
                        temp_buffer = QByteArray()
                        buffer = QBuffer(temp_buffer)
                        buffer.open(QBuffer.WriteOnly)
                        pixmap.save(buffer, 'PNG')  # Save as PNG to preserve quality
                        buffer.close()
                        
                        # Load as PIL image, convert to RGB, and back to QPixmap
                        pil_image = Image.open(BytesIO(temp_buffer.data()))
                        if pil_image.mode == 'RGBA':
                            pil_image = pil_image.convert('RGB')
                        
                        # Convert back to QPixmap
                        img_byte_arr = BytesIO()
                        pil_image.save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)
                        qimage = QImage.fromData(img_byte_arr.getvalue())
                        pixmap = QPixmap.fromImage(qimage)
                        
                        # Save with quality setting
                        quality = self.parent.toolbar.quality_slider.value()
                        
                        # For HEIC sources, apply higher compression to better match original file size
                        if is_heic and file_path in self.edited_images:
                            # Apply additional compression for HEIC sources
                            adjusted_quality = max(30, int(quality * 0.6))  # Scale down quality but keep minimum 30
                            pixmap.save(save_path, 'JPEG', adjusted_quality)
                        else:
                            pixmap.save(save_path, 'JPEG', quality)
                    else:
                        # For other formats, use their native format
                        format_map = {
                            '.png': ('PNG', -1),  # -1 means maximum compression for PNG
                            '.gif': ('GIF', None),
                            '.bmp': ('BMP', None),
                            '.tiff': ('TIFF', None)
                        }
                        img_format, quality = format_map.get(save_ext, ('PNG', -1))
                        if quality is not None:
                            pixmap.save(save_path, img_format, quality)
                        else:
                            pixmap.save(save_path, img_format)
                    
                    success_count += 1
                    
                    # Force UI update every few saved files
                    if idx % 3 == 0:
                        QApplication.processEvents()
                    
                except Exception as e:
                    failed_count += 1
                    print(f"Error saving {save_path}: {str(e)}")
                    
            # Final UI update before hiding overlay
            QApplication.processEvents()
                    
        except Exception as e:
            QMessageBox.warning(
                self.parent,
                "Warning",
                f"Failed to save images: {str(e)}"
            )
        finally:
            # Hide overlay
            self.parent.overlay.hide()
            # Reset the overlay label text
            self.parent.overlay.label.setText("Resizing images...")
            QApplication.processEvents()
            
            # Restore original selection
            if current_item:
                self.parent.image_list.setCurrentItem(current_item)
        
        # Show final results with styled dialog
        if success_count > 0:
            message = f"Successfully saved {success_count} images to {output_dir}!"
            if failed_count > 0:
                message += f"\nFailed to save {failed_count} images."
                
            # Create custom success dialog
            success_dialog = QMessageBox(self.parent)
            success_dialog.setWindowTitle("Success")
            success_dialog.setText(message)
            success_dialog.setIcon(QMessageBox.Information)
            
            # Style the dialog to match app theme
            success_dialog.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #333333;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 10px;
                }
                QPushButton {
                    color: black;
                    background-color: white;
                    padding: 8px 16px;
                    border: 1px solid #DBDCDA;
                    border-radius: 4px;
                    font-weight: 500;
                    min-width: 80px;
                }
                QPushButton:hover {
                    border: 1px solid #242424;
                }
            """)
            
            success_dialog.exec_()
        elif failed_count > 0:
            # Create custom error dialog
            error_dialog = QMessageBox(self.parent)
            error_dialog.setWindowTitle("Warning")
            error_dialog.setText(f"Failed to save any images. {failed_count} images failed.")
            error_dialog.setIcon(QMessageBox.Warning)
            
            # Style the dialog to match app theme
            error_dialog.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #333333;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 10px;
                }
                QPushButton {
                    color: black;
                    background-color: white;
                    padding: 8px 16px;
                    border: 1px solid #DBDCDA;
                    border-radius: 4px;
                    font-weight: 500;
                    min-width: 80px;
                }
                QPushButton:hover {
                    border: 1px solid #242424;
                }
            """)
            
            error_dialog.exec_()

    def rename_image(self, item, new_name):
        """Rename image file in the list"""
        # Get the old name from the item's widget
        widget = self.parent.image_list.itemWidget(item)
        if not widget:
            return
            
        old_name = widget.image_name
        
        # Ensure the new name has a valid image extension
        old_ext = os.path.splitext(old_name)[1].lower()
        new_ext = os.path.splitext(new_name)[1].lower()
        
        # If new name doesn't have an extension or has a different extension, add the original extension
        if not new_ext or new_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            new_name = os.path.splitext(new_name)[0] + old_ext
        
        # Store current states
        temp_images = self.images.copy()
        temp_edited_images = self.edited_images.copy()
        temp_current_dimensions = self.current_dimensions.copy()
        temp_file_sizes = self.file_sizes.copy()
        temp_edited_file_sizes = self.edited_file_sizes.copy()
        temp_image_histories = self.image_histories.copy()
        temp_redo_stack = self.redo_stack.copy() if hasattr(self, 'redo_stack') else {}
        temp_image_redo_stacks = self.image_redo_stacks.copy() if hasattr(self, 'image_redo_stacks') else {}
        
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
            self.image_histories.clear()
            if hasattr(self, 'redo_stack'):
                self.redo_stack.clear()
            if hasattr(self, 'image_redo_stacks'):
                self.image_redo_stacks.clear()
            
            # Clear the list widget
            self.parent.image_list.clear()
            
            # Rebuild dictionaries with updated paths
            for path, image in temp_images.items():
                if path == old_path:
                    self.images[new_path] = image
                    
                    # For renamed files, we need to ensure we have a valid pixmap
                    if old_path in temp_edited_images:
                        # If we have an edited version, use it
                        self.edited_images[new_path] = temp_edited_images[old_path]
                    else:
                        # If no edited version exists, create a pixmap from the original image
                        # without any quality changes or resizing
                        img_array = np.array(image)
                        if len(img_array.shape) == 3:  # Color image
                            array_height, array_width, channels = img_array.shape
                            bytes_per_line = channels * array_width
                            qimage = QImage(img_array.data, array_width, array_height, bytes_per_line, QImage.Format_RGB888)
                        else:  # Grayscale image
                            array_height, array_width = img_array.shape
                            bytes_per_line = array_width
                            qimage = QImage(img_array.data, array_width, array_height, bytes_per_line, QImage.Format_Grayscale8)
                        pixmap = QPixmap.fromImage(qimage)
                        self.edited_images[new_path] = pixmap
                    
                    # Copy all other properties
                    if old_path in temp_current_dimensions:
                        self.current_dimensions[new_path] = temp_current_dimensions[old_path]
                    if old_path in temp_file_sizes:
                        self.file_sizes[new_path] = temp_file_sizes[old_path]
                    if old_path in temp_edited_file_sizes:
                        self.edited_file_sizes[new_path] = temp_edited_file_sizes[old_path]
                    if old_path in temp_image_histories:
                        self.image_histories[new_path] = temp_image_histories[old_path]
                    if hasattr(self, 'redo_stack') and old_path in temp_redo_stack:
                        self.redo_stack[new_path] = temp_redo_stack[old_path]
                    if hasattr(self, 'image_redo_stacks') and old_path in temp_image_redo_stacks:
                        self.image_redo_stacks[new_path] = temp_image_redo_stacks[old_path]
                    
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
                    if path in temp_image_histories:
                        self.image_histories[path] = temp_image_histories[path]
                    if hasattr(self, 'redo_stack') and path in temp_redo_stack:
                        self.redo_stack[path] = temp_redo_stack[path]
                    if hasattr(self, 'image_redo_stacks') and path in temp_image_redo_stacks:
                        self.image_redo_stacks[path] = temp_image_redo_stacks[path]
                    
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
                    
                    # Disable resize and save buttons when no images are left
                    self.parent.toolbar.resize_btn.setEnabled(False)
                    self.parent.toolbar.resize_all_btn.setEnabled(False)
                    self.parent.toolbar.save_btn.setEnabled(False)
                    self.parent.toolbar.save_all_btn.setEnabled(False)
                break 

    def _update_tool_sizes(self, diagonal, base_diagonal=1500.0):
        """Update line widths, handle sizes, and text sizes for all tools"""
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
            # Calculate scale factors based on image dimensions
            base_width = 800  # Base width for scaling calculation
            dimension_scale = actual_width / base_width
            line_scale_factor = min(3.0, max(1.0, dimension_scale))  # Cap at 3.0
        
        # For text, calculate scale based on image dimensions
        # Reference size for text scaling (standard HD width)
        reference_width = 1920.0
        
        # Calculate text scale factor based on the ratio of image width to reference width
        # For images smaller than reference, scale up the text
        # For images larger than reference, keep text size constant
        if actual_width < reference_width:
            text_scale_factor = reference_width / actual_width
        else:
            text_scale_factor = 1.0
            
        # Clamp the text scale factor to reasonable bounds
        text_scale_factor = min(5.0, max(0.5, text_scale_factor))
        
        # Base sizes
        base_line_width = 2
        base_handle_size = 8
        base_arrow_size = 15
        base_font_size = 24  # Base font size for text tool
        
        # Get view scale for this image
        view_scale = self.view_scale.get(file_path, 1.0)
        
        # Calculate final sizes with different scale factors
        line_width = max(1, base_line_width * line_scale_factor)
        handle_size = max(4, base_handle_size * handle_scale_factor)
        arrow_size = max(8, base_arrow_size * line_scale_factor)  # Arrow size follows line scaling
        font_size = max(12, int(base_font_size * text_scale_factor))  # Scale text size based on image width
        
        print(f"Image dimensions: {actual_width}x{actual_height}")
        print(f"Line scale factor: {line_scale_factor:.2f}")
        print(f"Text scale factor: {text_scale_factor:.2f}")
        print(f"Handle scale factor: {handle_scale_factor:.2f}")
        print(f"View scale: {view_scale:.2f}")
        print(f"Is resized: {file_path in self.resized_images}")
        print(f"Has shapes: {file_path in self.edited_images}")
        print(f"Calculated sizes - Line: {line_width:.2f}, Handle: {handle_size:.2f}, Arrow: {arrow_size:.2f}, Font: {font_size}")
        
        # Update sizes for all tools
        for tool_name, tool in self.parent.tool_manager.tools.items():
            if hasattr(tool, 'line_width'):
                tool.line_width = line_width
                if tool_name == 'arrow' and hasattr(tool, 'arrow_size'):
                    tool.arrow_size = arrow_size
            if hasattr(tool, 'shape_handler') and hasattr(tool.shape_handler, 'handle_size'):
                tool.shape_handler.handle_size = handle_size
            # Update text tool font size
            if tool_name == 'text' and hasattr(tool, 'font_size'):
                tool.font_size = font_size  # Font size must be an integer 
                tool.font_size = font_size  # Font size must be an integer 
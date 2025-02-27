from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsPathItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QColor, QPainterPath
from .base_tool import BaseTool

class CropTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.cropping = False
        self.crop_start = None
        self.crop_rect = None
        self.overlay_item = None
        self.path_item = None

    def activate(self):
        # Create overlay
        for item in self.app.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                rect = item.boundingRect()
                self.overlay_item = QGraphicsRectItem(rect)
                self.overlay_item.setBrush(QColor(0, 0, 0, 127))
                self.overlay_item.setPen(QPen(Qt.NoPen))
                self.app.scene.addItem(self.overlay_item)
                break

    def deactivate(self):
        super().deactivate()
        if self.overlay_item and self.overlay_item.scene():
            self.app.scene.removeItem(self.overlay_item)
        if self.crop_rect and self.crop_rect.scene():
            self.app.scene.removeItem(self.crop_rect)
        if self.path_item and self.path_item.scene():
            self.app.scene.removeItem(self.path_item)
        self.overlay_item = None
        self.crop_rect = None
        self.path_item = None
        self.cropping = False

    def mouse_press(self, event):
        pos = self.app.view.mapToScene(event.pos())
        self.cropping = True
        self.crop_start = pos
        if self.crop_rect:
            self.app.scene.removeItem(self.crop_rect)
        self.crop_rect = QGraphicsRectItem()
        self.crop_rect.setPen(QPen(Qt.white, 2, Qt.DashLine))
        self.app.scene.addItem(self.crop_rect)

    def mouse_move(self, event):
        if not self.cropping:
            return
            
        pos = self.app.view.mapToScene(event.pos())
        if self.crop_rect:
            rect = QRectF(self.crop_start, pos).normalized()
            self.crop_rect.setRect(rect)
            self.update_overlay(rect)

    def mouse_release(self, event):
        if not self.cropping:
            return
            
        self.cropping = False
        if self.crop_rect:
            self.finalize_crop()

    def update_overlay(self, rect):
        """Update the overlay to show the cropped area"""
        if not self.overlay_item:
            return
        
        full_rect = self.overlay_item.rect()
        path = QPainterPath()
        path.addRect(full_rect)
        path.addRect(rect)
        
        if self.path_item:
            self.app.scene.removeItem(self.path_item)
        
        self.path_item = QGraphicsPathItem(path)
        self.path_item.setBrush(QColor(0, 0, 0, 127))
        self.path_item.setPen(QPen(Qt.NoPen))
        self.app.scene.addItem(self.path_item)

    def finalize_crop(self):
        """Apply the crop to the image"""
        if not self.crop_rect:
            return
        
        try:
            # Get crop rectangle
            rect = self.crop_rect.rect().normalized()
            
            # Find the pixmap item
            for item in self.app.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    # Save state before cropping
                    self.app.image_handler.save_state()
                    
                    # Get the cropped portion of the image
                    pixmap = item.pixmap()
                    cropped = pixmap.copy(rect.toRect())
                    
                    # Update scene with cropped image
                    self.app.scene.clear()  # This will delete all items
                    self.app.scene.addPixmap(cropped)
                    
                    # Update current dimensions
                    current_item = self.app.image_list.currentItem()
                    if current_item:
                        file_path = self.app.image_handler.get_file_path_from_item(current_item)
                        if file_path:
                            self.app.image_handler.current_dimensions[file_path] = (cropped.width(), cropped.height())
                            self.app.image_handler.edited_file_sizes[file_path] = self.app.image_handler.calculate_file_size(cropped)
                    
                    # Update info label
                    self.app.image_handler.update_info_label()
                    self.app.image_handler.modified = True
                    break
        except Exception as e:
            print(f"Error in finalize_crop: {str(e)}")
        finally:
            # Clean up and deselect tool
            try:
                self.cleanup()
            except Exception as e:
                print(f"Error in cleanup: {str(e)}")
            
            if hasattr(self.app.toolbar, 'crop_btn'):
                self.app.toolbar.crop_btn.setChecked(False)
            self.app.tool_manager.set_tool(None)

    def cleanup(self):
        """Clean up temporary items"""
        try:
            # Remove items from scene if they exist and are still valid
            if self.overlay_item is not None:
                try:
                    if self.overlay_item.scene():
                        self.app.scene.removeItem(self.overlay_item)
                except RuntimeError:
                    pass  # Item was already deleted
                
            if self.crop_rect is not None:
                try:
                    if self.crop_rect.scene():
                        self.app.scene.removeItem(self.crop_rect)
                except RuntimeError:
                    pass
                
            if self.path_item is not None:
                try:
                    if self.path_item.scene():
                        self.app.scene.removeItem(self.path_item)
                except RuntimeError:
                    pass
        finally:
            # Reset all references
            self.overlay_item = None
            self.crop_rect = None
            self.path_item = None
            self.crop_start = None
            self.cropping = False 
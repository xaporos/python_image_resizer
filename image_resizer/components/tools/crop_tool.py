from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsPathItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QColor
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

    def update_overlay(self, crop_rect):
        """Update the overlay to show the cropped area"""
        if hasattr(self, 'path_item') and self.path_item and self.path_item.scene():
            self.app.scene.removeItem(self.path_item)
        
        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        full_rect = self.overlay_item.rect()
        
        # Add four rectangles around the selection area
        path.addRect(QRectF(full_rect.left(), full_rect.top(), 
                          full_rect.width(), crop_rect.top() - full_rect.top()))  # Top
        path.addRect(QRectF(full_rect.left(), crop_rect.bottom(), 
                          full_rect.width(), full_rect.bottom() - crop_rect.bottom()))  # Bottom
        path.addRect(QRectF(full_rect.left(), crop_rect.top(), 
                          crop_rect.left() - full_rect.left(), crop_rect.height()))  # Left
        path.addRect(QRectF(crop_rect.right(), crop_rect.top(), 
                          full_rect.right() - crop_rect.right(), crop_rect.height()))  # Right
        
        self.path_item = QGraphicsPathItem(path)
        self.path_item.setBrush(QColor(0, 0, 0, 127))
        self.path_item.setPen(QPen(Qt.NoPen))
        self.app.scene.addItem(self.path_item)
        
        # Keep the crop rectangle visible and on top
        self.crop_rect.setZValue(2)

    def finalize_crop(self):
        """Apply the crop to the image"""
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
                    
                    # Clean up crop tool items
                    self.deactivate()
                    
                    # Update scene with cropped image
                    self.app.scene.clear()
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
                    break
                    
        finally:
            # Reset crop tool state
            self.deactivate() 
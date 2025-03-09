from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsLineItem, QGraphicsItemGroup, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import QPen, QBrush, QColor, QTransform

class ResizeHandle(QGraphicsRectItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRect(-4, -4, 8, 8)  # Small square handle
        self.setPen(QPen(Qt.white))
        self.setBrush(QBrush(Qt.black))
        self.setZValue(3)  # Above other items

class ShapeHandler:
    def __init__(self, app):
        self.app = app
        self.selected_shape = None
        self.resize_handles = []
        self.handle_size = 8
        self.dragging = False
        self.resizing = False
        self.resize_handle = None
        self.original_rect = None
        self.drag_start = None
        self.bounding_rect = None
        self.temp_shape = None  # Add this for temporary shape during resize

    def select_shape(self, shape):
        """Select a shape and create its resize handles"""
        self.clear_selection()
        self.selected_shape = shape
        
        # Create bounding rect
        rect = shape.boundingRect()
        self.bounding_rect = QGraphicsRectItem(rect)
        self.bounding_rect.setPen(QPen(Qt.white, 1, Qt.DashLine))
        self.bounding_rect.setZValue(2)
        self.app.scene.addItem(self.bounding_rect)
        
        # Create resize handles at corners
        positions = [
            (rect.topLeft(), Qt.SizeFDiagCursor),
            (rect.topRight(), Qt.SizeBDiagCursor),
            (rect.bottomLeft(), Qt.SizeBDiagCursor),
            (rect.bottomRight(), Qt.SizeFDiagCursor)
        ]

        for pos, cursor in positions:
            handle = ResizeHandle()
            handle.setPos(shape.mapToScene(pos))
            handle.setCursor(cursor)
            self.app.scene.addItem(handle)
            self.resize_handles.append(handle)

        shape.setZValue(1)

    def clear_selection(self):
        """Clear current selection and handles"""
        if self.selected_shape:
            self.selected_shape = None
        
        if self.bounding_rect and self.bounding_rect.scene():
            self.app.scene.removeItem(self.bounding_rect)
        self.bounding_rect = None
            
        for handle in self.resize_handles:
            if handle.scene():
                self.app.scene.removeItem(handle)
        self.resize_handles.clear()

    def handle_mouse_press(self, event, pos):
        if not self.selected_shape:
            return False

        # Check if clicking on a resize handle
        for handle in self.resize_handles:
            if handle.contains(handle.mapFromScene(pos)):
                self.resizing = True
                self.resize_handle = handle
                self.original_rect = self.selected_shape.boundingRect()
                self.drag_start = pos
                
                # Create temporary shape for preview
                self.temp_shape = self.selected_shape.clone()
                self.temp_shape.setZValue(4)  # Above everything
                self.app.scene.addItem(self.temp_shape)
                return True

        # Check if clicking on the shape itself
        if self.selected_shape.contains(self.selected_shape.mapFromScene(pos)):
            self.dragging = True
            self.drag_start = pos - self.selected_shape.pos()
            return True

        return False

    def handle_mouse_move(self, event, pos):
        if self.resizing and self.resize_handle:
            handle_index = self.resize_handles.index(self.resize_handle)
            
            if (isinstance(self.selected_shape, QGraphicsLineItem) and 
                self.selected_shape.data(0) == "arrow"):
                # Get the arrow's line
                line = self.selected_shape.line()
                
                # Update the appropriate end of the arrow
                if handle_index == 0:  # Start point
                    self.selected_shape.update_arrow(pos, line.p2())
                else:  # End point
                    self.selected_shape.update_arrow(line.p1(), pos)
                    
                # Update visuals
                self.update_bounding_rect()
                self.update_handles()
                return True
            
            # ... rest of the method for other shapes ...
            
        elif self.dragging:
            new_pos = pos - self.drag_start
            self.selected_shape.setPos(new_pos)
            self.update_bounding_rect()
            self.update_handles()
            return True
        return False

    def handle_mouse_release(self, event):
        if self.resizing:
            if self.temp_shape:
                # Apply the temporary shape's transform to the real shape
                self.selected_shape.setTransform(self.temp_shape.transform())
                # Remove temporary shape
                self.app.scene.removeItem(self.temp_shape)
                self.temp_shape = None
                # Update visuals
                self.update_bounding_rect()
                self.update_handles()
            
        self.resizing = False
        self.dragging = False
        self.resize_handle = None
        self.drag_start = None
        return True

    def update_bounding_rect(self):
        """Update the bounding rectangle position and size"""
        if self.selected_shape and self.bounding_rect:
            # Get transformed bounding rect
            rect = self.selected_shape.boundingRect()
            scene_rect = self.selected_shape.mapRectToScene(rect)
            self.bounding_rect.setRect(scene_rect)

    def update_handles(self):
        """Update position of resize handles"""
        if not self.selected_shape:
            return

        # Get transformed bounding rect
        rect = self.selected_shape.boundingRect()
        scene_rect = self.selected_shape.mapRectToScene(rect)
        
        # Update handle positions
        positions = [
            scene_rect.topLeft(),
            scene_rect.topRight(),
            scene_rect.bottomLeft(),
            scene_rect.bottomRight()
        ]

        for handle, pos in zip(self.resize_handles, positions):
            handle.setPos(pos)

    def handle_shape_resize(self, pos):
        """Handle shape resizing"""
        if not self.selected_shape:
            return

        if isinstance(self.selected_shape, QGraphicsEllipseItem):
            rect = QRectF(self.drag_start, pos).normalized()
            self.selected_shape.setRect(rect)
        elif isinstance(self.selected_shape, QGraphicsLineItem):
            line = QLineF(self.drag_start, pos)
            self.selected_shape.setLine(line)

    def finalize_shape(self):
        """Finalize the current shape"""
        if not self.selected_shape:
            return

        if isinstance(self.selected_shape, QGraphicsEllipseItem):
            # Handle circle finalization
            rect = self.selected_shape.rect()
            self.app.scene.removeItem(self.selected_shape)
            self.selected_shape = None
        elif isinstance(self.selected_shape, QGraphicsLineItem):
            # Handle arrow finalization
            line = self.selected_shape.line()
            self.app.scene.removeItem(self.selected_shape)
            self.selected_shape = None 
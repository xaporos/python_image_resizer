from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsLineItem, QGraphicsPixmapItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import QPen, QBrush, QPainter
import math

class BaseShapeHandler:
    def __init__(self, app):
        self.app = app
        self.selected_shape = None
        self.resize_handles = []
        self.handle_size = 8
        self.resizing = False
        self.moving = False
        self.resize_handle = None
        self.start_pos = None
        self.original_rect = None

    def handle_shape_start(self, pos):
        """Start drawing or resizing a shape"""
        self.start_pos = pos
        self.last_pos = pos
        self.drawing = True

    def handle_shape_resize(self, pos):
        """Handle shape resizing"""
        if not self.selected_shape or not self.resize_handle:
            return

        handle_index = self.resize_handles.index(self.resize_handle)
        new_rect = self.calculate_new_rect(pos, handle_index)
        self.update_shape(new_rect)
        self.update_resize_handles()

    def handle_drawing_new_shape(self, pos):
        """Handle drawing of new shape"""
        if not self.drawing or not self.start_pos:
            return

        rect = QRectF(self.start_pos, pos).normalized()
        self.update_shape(rect)
        self.last_pos = pos

    def select_shape(self, shape):
        """Select a shape and create its resize handles"""
        # Clear previous selection
        if self.selected_shape and self.selected_shape != shape:
            self.finalize_shape()
            
        # Set new shape
        self.selected_shape = shape
        if shape and shape.scene():  # Check if shape still exists
            shape.setZValue(1)
            
            # Create resize handles
            self.resize_handles = self.create_resize_handles(shape)
            
            # Set proper z-ordering
            for handle in self.resize_handles:
                handle.setZValue(3)

    def finalize_shape(self):
        """Finalize the current shape by drawing it permanently on the pixmap"""
        try:
            if not self.selected_shape or not self.selected_shape.scene():
                return

            # Save state before making permanent changes
            self.app.image_handler.save_state()

            # Get shape data before cleanup
            shape = self.selected_shape
            pen = shape.pen()
            
            # Clean up handles first
            self.clear_handles()

            # Find the pixmap item
            pixmap = None
            for item in self.app.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    pixmap = item.pixmap().copy()
                    break
                
            if pixmap and shape.scene():
                painter = QPainter(pixmap)
                painter.setPen(pen)
                painter.setRenderHint(QPainter.Antialiasing)
                
                if isinstance(shape, QGraphicsLineItem):
                    line = shape.line()
                    line.translate(shape.pos())
                    painter.drawLine(line)
                    
                    # Draw arrow head if this is an arrow shape
                    if shape.data(0) == "arrow":
                        angle = math.atan2(line.dy(), line.dx())
                        arrow_size = 20.0
                        
                        end = line.p2()
                        arrow_p1 = QPointF(end.x() - arrow_size * math.cos(angle + math.pi/6),
                                         end.y() - arrow_size * math.sin(angle + math.pi/6))
                        arrow_p2 = QPointF(end.x() - arrow_size * math.cos(angle - math.pi/6),
                                         end.y() - arrow_size * math.sin(angle - math.pi/6))
                        
                        painter.drawLine(end, arrow_p1)
                        painter.drawLine(end, arrow_p2)
                elif isinstance(shape, QGraphicsEllipseItem):
                    rect = shape.rect()
                    rect.translate(shape.pos())
                    painter.drawEllipse(rect)
                elif isinstance(shape, QGraphicsRectItem):
                    rect = shape.rect()
                    rect.translate(shape.pos())
                    painter.drawRect(rect)
                
                painter.end()
                
                # Update scene
                self.app.scene.clear()
                self.app.scene.addPixmap(pixmap)
        except:
            pass
        finally:
            # Always clear selection
            self.selected_shape = None

    def calculate_new_rect(self, pos, handle_index):
        """Calculate new rectangle or line based on resize handle movement"""
        if not self.selected_shape:
            return None

        if isinstance(self.selected_shape, QGraphicsLineItem):
            # For lines, update endpoint positions
            line = self.selected_shape.line()
            if handle_index == 0:  # Start point
                return QLineF(pos, line.p2())
            else:  # End point
                return QLineF(line.p1(), pos)
        else:
            # For rectangles and other shapes
            current_rect = self.selected_shape.rect()
            new_rect = QRectF(current_rect)

            if handle_index == 0:  # Top-left
                new_rect.setTopLeft(pos)
            elif handle_index == 1:  # Top-right
                new_rect.setTopRight(pos)
            elif handle_index == 2:  # Bottom-left
                new_rect.setBottomLeft(pos)
            elif handle_index == 3:  # Bottom-right
                new_rect.setBottomRight(pos)

            return new_rect.normalized()

    def create_resize_handles(self, item):
        """Create resize handles for a shape"""
        handles = []
        
        if isinstance(item, QGraphicsLineItem):
            # For arrow/line, only create handles at start and end points
            line = item.line()
            positions = [
                (line.p1(), Qt.SizeAllCursor),
                (line.p2(), Qt.SizeAllCursor)
            ]
        else:
            # For rectangle and circle, create handles at corners and edges
            rect = item.rect()
            positions = [
                (rect.topLeft(), Qt.SizeFDiagCursor),
                (rect.topRight(), Qt.SizeBDiagCursor),
                (rect.bottomLeft(), Qt.SizeBDiagCursor),
                (rect.bottomRight(), Qt.SizeFDiagCursor)
            ]
        
        # Create handles at the calculated positions
        for pos, cursor in positions:
            handle = QGraphicsRectItem()
            scene_pos = item.mapToScene(pos)
            handle.setRect(
                scene_pos.x() - self.handle_size/2,
                scene_pos.y() - self.handle_size/2,
                self.handle_size,
                self.handle_size
            )
            handle.setPen(QPen(Qt.white))
            handle.setBrush(QBrush(Qt.black))
            handle.setCursor(cursor)
            handle.setZValue(2)
            self.app.scene.addItem(handle)
            handles.append(handle)
        
        return handles

    def update_resize_handles(self):
        """Update position of resize handles"""
        if not self.selected_shape:
            return

        # Block signals temporarily to prevent flickering
        self.app.scene.blockSignals(True)

        shape_pos = self.selected_shape.pos()
        
        if isinstance(self.selected_shape, QGraphicsLineItem):
            line = self.selected_shape.line()
            positions = [
                self.selected_shape.mapToScene(line.p1()),
                self.selected_shape.mapToScene(line.p2())
            ]
        else:
            rect = self.selected_shape.rect()
            positions = [
                self.selected_shape.mapToScene(rect.topLeft()),
                self.selected_shape.mapToScene(rect.topRight()),
                self.selected_shape.mapToScene(rect.bottomLeft()),
                self.selected_shape.mapToScene(rect.bottomRight())
            ]

        for handle, pos in zip(self.resize_handles, positions):
            handle.setRect(
                pos.x() - self.handle_size/2,
                pos.y() - self.handle_size/2,
                self.handle_size,
                self.handle_size
            )

        self.app.scene.blockSignals(False)
        self.app.scene.update()

    def clear_handles(self):
        """Clear just the resize handles"""
        for handle in self.resize_handles[:]:
            if handle and handle.scene():
                self.app.scene.removeItem(handle)
        self.resize_handles.clear()

    def clear_selection(self):
        """Clear current selection and handles"""
        try:
            # Clear handles first
            self.clear_handles()
            
            # Clear selected shape if it still exists
            if self.selected_shape and self.selected_shape.scene():
                self.finalize_shape()  # Try to finalize the shape before clearing
            
            # Reset all states
            self.selected_shape = None
            self.resizing = False
            self.moving = False
            self.resize_handle = None
            self.start_pos = None
        except:
            # If any error occurs, just reset everything
            self.resize_handles = []
            self.selected_shape = None
            self.resizing = False
            self.moving = False
            self.resize_handle = None
            self.start_pos = None

    def handle_mouse_press(self, event, pos):
        """Handle mouse press for shape resizing"""
        if not self.selected_shape:
            return False

        # Check if clicking on a resize handle
        for handle in self.resize_handles:
            if handle.contains(handle.mapFromScene(pos)):
                self.resizing = True
                self.resize_handle = handle
                self.start_pos = pos
                return True

        # Check if clicking on the shape itself
        if self.selected_shape.contains(self.selected_shape.mapFromScene(pos)):
            self.moving = True
            self.start_pos = pos - self.selected_shape.pos()
            return True

        # If clicked outside, finalize the shape and deactivate tool
        self.finalize_shape()
        if self.app.tool_manager.current_tool:
            self.app.tool_manager.set_tool(None)
            # Uncheck the appropriate tool button
            if hasattr(self.app.toolbar, 'arrow_btn'):
                self.app.toolbar.arrow_btn.setChecked(False)
            if hasattr(self.app.toolbar, 'circle_btn'):
                self.app.toolbar.circle_btn.setChecked(False)
            if hasattr(self.app.toolbar, 'rect_btn'):
                self.app.toolbar.rect_btn.setChecked(False)
        return False

    def handle_mouse_move(self, event, pos):
        """Handle mouse move for shape resizing"""
        if self.resizing and self.resize_handle:
            handle_index = self.resize_handles.index(self.resize_handle)
            if isinstance(self.selected_shape, QGraphicsLineItem):
                # Convert scene position to item coordinates
                item_pos = self.selected_shape.mapFromScene(pos)
                line = self.selected_shape.line()
                
                if handle_index == 0:  # Start point
                    self.selected_shape.setLine(QLineF(item_pos, line.p2()))
                else:  # End point
                    self.selected_shape.setLine(QLineF(line.p1(), item_pos))
            else:
                new_rect = self.calculate_new_rect(pos, handle_index)
                self.update_shape(new_rect)
            self.update_resize_handles()
            return True
        elif self.moving:
            new_pos = pos - self.start_pos
            self.selected_shape.setPos(new_pos)
            self.update_resize_handles()
            return True
        return False

    def handle_mouse_release(self, event):
        """Handle mouse release for shape resizing"""
        if self.resizing or self.moving:
            self.resizing = False
            self.moving = False
            self.resize_handle = None
            self.start_pos = None
            return True
        return False

    def update_shape(self, new_geometry):
        """Update shape with new geometry"""
        if not self.selected_shape:
            return

        if isinstance(self.selected_shape, QGraphicsLineItem):
            if isinstance(new_geometry, QLineF):
                self.selected_shape.setLine(new_geometry)
        else:
            if isinstance(new_geometry, QRectF):
                self.selected_shape.setRect(new_geometry) 
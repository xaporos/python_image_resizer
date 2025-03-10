from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsLineItem, QGraphicsPixmapItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import QPen, QBrush, QPainter, QTransform
import math

class BaseShapeHandler:
    def __init__(self, app):
        print("\nBaseShapeHandler initialized")  # Debug print
        self.app = app
        self.selected_shape = None
        self.resize_handles = []
        self._handle_size = 16
        print(f"Initial _handle_size set to: {self._handle_size}")
        self.resizing = False
        self.moving = False
        self.resize_handle = None
        self.start_pos = None
        self.original_rect = None
        self.initial_shape_pos = None
        self.initial_geometry = None

    @property
    def handle_size(self):
        print(f"Getting handle_size: {self._handle_size}")
        return self._handle_size

    @handle_size.setter
    def handle_size(self, value):
        print(f"\nAttempting to set handle_size to {value}")
        import traceback
        print("Stack trace:")
        for line in traceback.format_stack():
            if 'image_resizer' in line:  # Only show our code's stack trace
                print(line.strip())
        self._handle_size = value

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
        if not shape or not shape.scene():
            return
            
        # Clear any previous selection
        self.clear_selection()
        
        # Set new selection
        self.selected_shape = shape
        
        # Create new handles
        self.create_resize_handles(shape)

    def finalize_shape(self):
        """Finalize the current shape and deselect the tool"""
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
                
                # Draw the shape on the pixmap
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

                # Deselect the current tool
                if hasattr(self.app, 'tool_manager'):
                    self.app.tool_manager.set_tool(None)
                    # Uncheck all tool buttons
                    if hasattr(self.app.toolbar, 'arrow_btn'):
                        self.app.toolbar.arrow_btn.setChecked(False)
                    if hasattr(self.app.toolbar, 'circle_btn'):
                        self.app.toolbar.circle_btn.setChecked(False)
                    if hasattr(self.app.toolbar, 'rect_btn'):
                        self.app.toolbar.rect_btn.setChecked(False)
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
        print(f"\nCreating handles with size: {self._handle_size}")
        # Clear any existing handles
        for handle in self.resize_handles:
            if handle.scene():
                self.app.scene.removeItem(handle)
        self.resize_handles = []
        
        # Get both view and image scales
        view_scale = self.app.view.transform().m11()
        
        # Get image scale by comparing scene rect to view rect
        scene_rect = self.app.scene.sceneRect()
        view_rect = self.app.view.rect()
        image_scale = min(view_rect.width() / scene_rect.width(),
                         view_rect.height() / scene_rect.height())
        
        # Calculate base size for handles
        if image_scale > 1:
            actual_size = self._handle_size * 0.4  # Smaller handles when zoomed in
        else:
            actual_size = self._handle_size  # Normal size when not zoomed
        
        # Apply view scale
        actual_size = actual_size / view_scale
        
        positions = []
        if isinstance(item, QGraphicsLineItem):
            line = item.line()
            positions = [
                item.mapToScene(line.p1()),
                item.mapToScene(line.p2())
            ]
        else:
            rect = item.rect()
            positions = [
                item.mapToScene(rect.topLeft()),
                item.mapToScene(rect.topRight()),
                item.mapToScene(rect.bottomLeft()),
                item.mapToScene(rect.bottomRight())
            ]
        
        for pos in positions:
            handle = QGraphicsRectItem()
            half_size = actual_size / 2
            handle.setRect(-half_size, -half_size, actual_size, actual_size)
            handle.setPen(QPen(Qt.black, 2))
            handle.setBrush(QBrush(Qt.white))
            handle.setPos(pos)
            handle.setZValue(5)
            self.app.scene.addItem(handle)
            self.resize_handles.append(handle)

    def update_resize_handles(self):
        """Update position of resize handles"""
        print(f"Base handle size in update: {self._handle_size}")  # Debug print
        if not self.selected_shape:
            return

        # Get both view and image scales
        view_scale = self.app.view.transform().m11()
        
        # Get image scale by comparing scene rect to view rect
        scene_rect = self.app.scene.sceneRect()
        view_rect = self.app.view.rect()
        image_scale = min(view_rect.width() / scene_rect.width(),
                         view_rect.height() / scene_rect.height())
        
        # Calculate base size for handles
        if image_scale > 1:
            actual_size = self._handle_size * 0.4  # Smaller handles when zoomed in
        else:
            actual_size = self._handle_size  # Normal size when not zoomed
        
        # Apply view scale
        actual_size = actual_size / view_scale
        
        if isinstance(self.selected_shape, QGraphicsLineItem):
            line = self.selected_shape.line()
            p1 = self.selected_shape.mapToScene(line.p1())
            p2 = self.selected_shape.mapToScene(line.p2())
            positions = [p1, p2]
        else:
            rect = self.selected_shape.rect()
            positions = [
                self.selected_shape.mapToScene(rect.topLeft()),
                self.selected_shape.mapToScene(rect.topRight()),
                self.selected_shape.mapToScene(rect.bottomLeft()),
                self.selected_shape.mapToScene(rect.bottomRight())
            ]

        # Update each handle position and size
        for handle, pos in zip(self.resize_handles, positions):
            half_size = actual_size / 2
            handle.setRect(-half_size, -half_size, actual_size, actual_size)
            handle.setPos(pos)

    def clear_handles(self):
        """Clear just the resize handles"""
        for handle in self.resize_handles[:]:
            if handle and handle.scene():
                self.app.scene.removeItem(handle)
        self.resize_handles.clear()

    def clear_selection(self):
        """Clear current selection and handles"""
        # Remove all handles
        for handle in self.resize_handles:
            if handle.scene():
                self.app.scene.removeItem(handle)
        self.resize_handles.clear()
        
        # Reset state
        self.selected_shape = None
        self.resizing = False
        self.moving = False
        self.resize_handle = None
        self.start_pos = None
        self.original_rect = None
        self.initial_shape_pos = None
        self.initial_geometry = None

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
                # Store initial shape position and geometry
                self.initial_shape_pos = self.selected_shape.pos()
                if isinstance(self.selected_shape, QGraphicsLineItem):
                    self.initial_geometry = self.selected_shape.line()
                else:
                    self.initial_geometry = self.selected_shape.rect()
                return True

        # Check if clicking on the shape itself
        if self.selected_shape.contains(self.selected_shape.mapFromScene(pos)):
            self.moving = True
            self.start_pos = pos
            self.initial_shape_pos = self.selected_shape.pos()
            return True

        # If clicked outside, finalize the shape and deselect the tool
        self.finalize_shape()
        if hasattr(self.app, 'tool_manager') and self.app.tool_manager.current_tool:
            self.app.tool_manager.set_tool(None)
            # Uncheck the tool button
            if hasattr(self.app.toolbar, f"{self.app.tool_manager.current_tool.__class__.__name__.lower()}_btn"):
                getattr(self.app.toolbar, f"{self.app.tool_manager.current_tool.__class__.__name__.lower()}_btn").setChecked(False)
        return False

    def handle_mouse_move(self, event, pos):
        """Handle mouse move for shape resizing"""
        if self.resizing and self.resize_handle:
            handle_index = self.resize_handles.index(self.resize_handle)
            if isinstance(self.selected_shape, QGraphicsLineItem):
                # Keep line handling as is - it works correctly
                item_pos = self.selected_shape.mapFromScene(pos)
                line = self.selected_shape.line()
                
                if handle_index == 0:  # Start point
                    self.selected_shape.setLine(QLineF(item_pos, line.p2()))
                else:  # End point
                    self.selected_shape.setLine(QLineF(line.p1(), item_pos))
            else:
                # For circles and rectangles, use the same coordinate handling as lines
                item_pos = self.selected_shape.mapFromScene(pos)
                current_rect = self.selected_shape.rect()
                
                if handle_index == 0:  # Top-left
                    new_rect = QRectF(item_pos, current_rect.bottomRight())
                elif handle_index == 1:  # Top-right
                    new_rect = QRectF(QPointF(current_rect.left(), item_pos.y()),
                                    QPointF(item_pos.x(), current_rect.bottom()))
                elif handle_index == 2:  # Bottom-left
                    new_rect = QRectF(QPointF(item_pos.x(), current_rect.top()),
                                    QPointF(current_rect.right(), item_pos.y()))
                else:  # Bottom-right
                    new_rect = QRectF(current_rect.topLeft(), item_pos)
                
                self.selected_shape.setRect(new_rect.normalized())
            
            self.update_resize_handles()
            return True
        elif self.moving:
            delta = pos - self.start_pos
            new_pos = self.initial_shape_pos + delta
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
            # Update initial position and geometry
            self.initial_shape_pos = self.selected_shape.pos()
            if isinstance(self.selected_shape, QGraphicsLineItem):
                self.initial_geometry = self.selected_shape.line()
            else:
                self.initial_geometry = self.selected_shape.rect()
            self.update_resize_handles()
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

    def update_handle_size(self, size):
        """Update the size of resize handles"""
        for handle in self.resize_handles:
            # Handles are typically centered at (0,0) with width/height
            half_size = size / 2
            handle.setRect(-half_size, -half_size, size, size) 
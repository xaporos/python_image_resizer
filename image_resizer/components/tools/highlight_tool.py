from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush
from PyQt5.QtCore import Qt, QRectF
from .base_tool import BaseTool

class HighlightTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.temp_image = None
        self.current_color = Qt.yellow  # Default color
        self.line_width = 10  # Default line width - wider than pencil
        self.width_multiplier = 10  # Multiplier for thickness (increased to 5)
        self.opacity = 0.1  # Default opacity for highlighting
        self.drawing = False
        self.last_point = None

    def activate(self):
        # Store the current image when tool is activated
        for item in self.app.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                self.temp_image = item.pixmap().copy()
                break

    def deactivate(self):
        super().deactivate()
        self.temp_image = None
        self.drawing = False
        self.last_point = None

    def set_current_color(self, color):
        """Set the current color for highlighting (overrides the one in BaseTool)"""
        # Store the base color
        self.current_color = color

    def get_highlight_color(self):
        """Get a semi-transparent version of the current color for highlighting"""
        # Create a semi-transparent version of the current color
        highlight_color = QColor(self.current_color)
        highlight_color.setAlphaF(self.opacity)
        return highlight_color
    
    @property
    def actual_width(self):
        """Get the actual line width after applying the multiplier"""
        return self.line_width * self.width_multiplier
        
    def mouse_press(self, event):
        pos = self.app.view.mapToScene(event.pos())
        self.drawing = True
        self.last_point = pos
        
        # Find and store the current pixmap and save state
        for item in self.app.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                self.temp_image = item.pixmap().copy()
                self.app.image_handler.save_state()  # Save state when starting to draw
                break
                
        # Draw initial marker at current position
        self.draw_marker_at(pos)

    def mouse_move(self, event):
        if not self.drawing or not self.temp_image:
            return
            
        pos = self.app.view.mapToScene(event.pos())
        if self.last_point:
            painter = QPainter(self.temp_image)
            
            # Get semi-transparent color
            highlight_color = self.get_highlight_color()
            
            # Setup painter with high quality
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw markers along the path from last point to current point
            # Calculate distance between points to determine number of steps
            dx = pos.x() - self.last_point.x()
            dy = pos.y() - self.last_point.y()
            distance = max(abs(dx), abs(dy))
            steps = max(int(distance / (self.actual_width / 4)), 1)  # At least 1 step
            
            for i in range(steps + 1):
                t = i / steps if steps > 0 else 0
                x = self.last_point.x() * (1 - t) + pos.x() * t
                y = self.last_point.y() * (1 - t) + pos.y() * t
                
                # Draw a rectangle/marker at this point
                rect_width = self.actual_width
                rect_height = self.actual_width * 1.2  # Make marker slightly taller than wide
                
                # Calculate rectangle coordinates
                rect_x = x - rect_width / 2
                rect_y = y - rect_height / 2
                
                # Draw the marker
                painter.setBrush(QBrush(highlight_color))
                painter.setPen(Qt.NoPen)  # No outline for the marker
                painter.drawRect(QRectF(rect_x, rect_y, rect_width, rect_height))
            
            painter.end()
            
            # Update scene with temporary image
            self.app.scene.clear()
            self.app.scene.addPixmap(self.temp_image)
            self.app.image_handler.update_info_label()
            self.last_point = pos

    def draw_marker_at(self, pos):
        """Draw a marker at the specified position"""
        if not self.temp_image:
            return
            
        painter = QPainter(self.temp_image)
        highlight_color = self.get_highlight_color()
        
        # Setup painter
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate rectangle dimensions (marker)
        rect_width = self.actual_width
        rect_height = self.actual_width * 1.2  # Make marker slightly taller than wide
        
        # Calculate rectangle coordinates
        rect_x = pos.x() - rect_width / 2
        rect_y = pos.y() - rect_height / 2
        
        # Draw the marker
        painter.setBrush(QBrush(highlight_color))
        painter.setPen(Qt.NoPen)  # No outline for the marker
        painter.drawRect(QRectF(rect_x, rect_y, rect_width, rect_height))
        
        painter.end()
        
        # Update scene with temporary image
        self.app.scene.clear()
        self.app.scene.addPixmap(self.temp_image)
        self.app.image_handler.update_info_label()

    def mouse_release(self, event):
        self.drawing = False
        self.last_point = None
        if self.temp_image:
            # Don't save state here since we already saved it at start
            self.app.scene.clear()
            self.app.scene.addPixmap(self.temp_image)
            self.app.image_handler.update_info_label() 
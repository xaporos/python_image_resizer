from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QRectF, QPointF
from .base_tool import BaseTool

class HighlightTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.temp_image = None
        self.current_color = Qt.yellow  # Default color
        self.line_width = 10  # Default line width - wider than pencil
        self.width_multiplier = 10  # Multiplier for thickness (increased to 10)
        self.opacity = 0.1  # Default opacity for highlighting
        self.drawing = False
        self.last_point = None
        self.path_points = []  # Store points for the current stroke

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
        self.path_points = []  # Clear the path points

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
        
        # Reset path points
        self.path_points = [pos]
        
        # Find and store the current pixmap and save state
        for item in self.app.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                self.temp_image = item.pixmap().copy()
                self.app.image_handler.save_state()  # Save state when starting to draw
                break
        
        # We'll draw the entire highlight at once, so we don't need to draw on mouse press

    def mouse_move(self, event):
        if not self.drawing or not self.temp_image:
            return
            
        pos = self.app.view.mapToScene(event.pos())
        if self.last_point:
            # Add point to path
            self.path_points.append(pos)
            
            # Create a temporary image for this stroke
            temp_image_copy = self.temp_image.copy()
            
            # Draw the complete path
            self.draw_uniform_highlight(temp_image_copy)
            
            # Update scene with temporary image
            self.app.scene.clear()
            self.app.scene.addPixmap(temp_image_copy)
            self.app.image_handler.update_info_label()
            self.last_point = pos

    def draw_uniform_highlight(self, pixmap):
        """Draw a uniform highlight along the entire path"""
        if not self.path_points or len(self.path_points) < 2:
            return
            
        painter = QPainter(pixmap)
        highlight_color = self.get_highlight_color()
        
        # Use SourceOver mode for natural alpha blending
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        # Setup painter with high quality
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # Create a path for this highlight
        half_width = self.actual_width / 2
        
        # We'll simplify the approach to ensure consistent results in both directions
        # Create a QPainterPath that follows the center line
        path = QPainterPath()
        path.moveTo(self.path_points[0])
        
        for point in self.path_points[1:]:
            path.lineTo(point)
        
        # Create a stroke with a flat cap and no joins for a clean highlighter look
        pen = QPen(highlight_color, self.actual_width)
        pen.setCapStyle(Qt.FlatCap)
        pen.setJoinStyle(Qt.RoundJoin)
        
        # Set the pen
        painter.setPen(pen)
        
        # Draw the path with the thick pen
        painter.drawPath(path)
        
        painter.end()

    def mouse_release(self, event):
        if not self.drawing or not self.path_points:
            self.drawing = False
            self.last_point = None
            self.path_points = []
            return
            
        # Create final highlight
        if self.temp_image:
            temp_image_copy = self.temp_image.copy()
            self.draw_uniform_highlight(temp_image_copy)
            
            # Update the temp_image with the final result
            self.temp_image = temp_image_copy
            
            # Clear scene and show the result
            self.app.scene.clear()
            self.app.scene.addPixmap(self.temp_image)
            self.app.image_handler.update_info_label()
        
        # Reset state
        self.drawing = False
        self.last_point = None
        self.path_points = [] 
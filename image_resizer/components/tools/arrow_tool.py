from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsLineItem
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QLineF, QPointF
import math
from .base_tool import BaseTool
from ..base_shape_handler import BaseShapeHandler

class ArrowTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.shape_handler = BaseShapeHandler(app)
        self.current_color = Qt.red
        self.line_width = 3  # Increased default line width
        self.arrow_size = 40  # Default arrow head size
        self.arrow_item = None

    def mouse_press(self, event):
        pos = self.app.view.mapToScene(event.pos())
        
        # Check for resize handle interaction or shape selection
        if self.shape_handler.handle_mouse_press(event, pos):
            return
            
        # Start new arrow
        self.drawing = True
        self.arrow_item = QGraphicsLineItem()
        self.arrow_item.setPen(QPen(self.current_color, self.line_width))
        self.arrow_item.setData(0, "arrow")  # Mark as arrow
        self.arrow_item.setData(1, self.arrow_size)  # Store arrow size
        self.app.scene.addItem(self.arrow_item)
        self.last_point = pos

    def mouse_move(self, event):
        pos = self.app.view.mapToScene(event.pos())
        
        if self.shape_handler.handle_mouse_move(event, pos):
            return
            
        if self.drawing and self.last_point:
            line = QLineF(self.last_point, pos)
            self.arrow_item.setLine(line)
            self._draw_arrow_head(line)

    def _draw_arrow_head(self, line):
        """Draw arrow head based on current arrow_size"""
        if not self.arrow_item:
            return
            
        angle = math.atan2(line.dy(), line.dx())
        arrow_size = self.arrow_size
        
        # Create arrow head points
        arrow_p1 = QPointF(
            line.p2().x() - arrow_size * math.cos(angle + math.pi/6),
            line.p2().y() - arrow_size * math.sin(angle + math.pi/6)
        )
        arrow_p2 = QPointF(
            line.p2().x() - arrow_size * math.cos(angle - math.pi/6),
            line.p2().y() - arrow_size * math.sin(angle - math.pi/6)
        )
        
        # Store arrow head points for later use
        self.arrow_item.setData(2, [arrow_p1, arrow_p2])

    def mouse_release(self, event):
        if not self.drawing:
            if self.shape_handler.handle_mouse_release(event):
                return
            return
            
        self.drawing = False
        pos = self.app.view.mapToScene(event.pos())
        
        if self.last_point and self.arrow_item:
            line = QLineF(self.last_point, pos)
            self.arrow_item.setLine(line)
            self._draw_arrow_head(line)
            self.shape_handler.select_shape(self.arrow_item)
            self.last_point = None
            # Note: Don't deactivate tool here - let it be deactivated when clicking outside

    def activate(self):
        """Called when the tool is activated"""
        super().activate()
        # Reset all states
        self.drawing = False
        self.last_point = None
        self.arrow_item = None
        # Clear any existing selection
        if self.shape_handler:
            self.shape_handler.clear_selection()

    def deactivate(self):
        """Called when the tool is deactivated"""
        super().deactivate()
        # Clean up
        if self.shape_handler:
            self.shape_handler.clear_selection()
        self.arrow_item = None
        self.drawing = False
        self.last_point = None 
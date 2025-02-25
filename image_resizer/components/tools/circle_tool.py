from PyQt5.QtWidgets import QGraphicsEllipseItem
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt, QRectF
from .base_tool import BaseTool
from ..base_shape_handler import BaseShapeHandler

class CircleTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.shape_handler = BaseShapeHandler(app)
        self.current_color = Qt.red
        self.line_width = 2
        self.circle_item = None
        self.drawing = False
        self.last_point = None

    def activate(self):
        """Called when the tool is activated"""
        super().activate()
        # Reset all states
        self.drawing = False
        self.last_point = None
        self.circle_item = None
        # Clear any existing selection
        if self.shape_handler:
            self.shape_handler.clear_selection()

    def deactivate(self):
        """Called when the tool is deactivated"""
        super().deactivate()
        # Clean up
        if self.shape_handler:
            self.shape_handler.clear_selection()
        self.circle_item = None
        self.drawing = False
        self.last_point = None

    def mouse_press(self, event):
        pos = self.app.view.mapToScene(event.pos())
        
        # Check for resize handle interaction or shape selection
        if self.shape_handler.handle_mouse_press(event, pos):
            return
            
        # Start new circle
        self.drawing = True
        self.circle_item = QGraphicsEllipseItem()
        self.circle_item.setPen(QPen(self.current_color, self.line_width))
        self.circle_item.setData(0, "circle")  # Mark as circle
        self.app.scene.addItem(self.circle_item)
        self.last_point = pos

    def mouse_move(self, event):
        pos = self.app.view.mapToScene(event.pos())
        
        if self.shape_handler.handle_mouse_move(event, pos):
            return
            
        if self.drawing and self.last_point:
            rect = QRectF(self.last_point, pos).normalized()
            self.circle_item.setRect(rect)

    def mouse_release(self, event):
        if not self.drawing:
            if self.shape_handler.handle_mouse_release(event):
                return
            return
            
        self.drawing = False
        pos = self.app.view.mapToScene(event.pos())
        
        if self.last_point and self.circle_item:
            rect = QRectF(self.last_point, pos).normalized()
            self.circle_item.setRect(rect)
            self.shape_handler.select_shape(self.circle_item)
            self.last_point = None 
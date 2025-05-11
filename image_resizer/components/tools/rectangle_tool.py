from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt, QRectF
from .base_tool import BaseTool
from ..base_shape_handler import BaseShapeHandler

class RectangleTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.shape_handler = BaseShapeHandler(app)
        self.current_color = Qt.red
        self.line_width = 2
        self.rect_item = None
        self.drawing = False
        self.last_point = None

    def activate(self):
        """Called when the tool is activated"""
        super().activate()
        # Reset all states
        self.drawing = False
        self.last_point = None
        self.rect_item = None
        # Clear any existing selection
        if self.shape_handler:
            self.shape_handler.clear_selection()

    def deactivate(self):
        """Called when the tool is deactivated"""
        super().deactivate()
        # Clean up
        if self.shape_handler:
            self.shape_handler.clear_selection()
        self.rect_item = None
        self.drawing = False
        self.last_point = None

    def mouse_press(self, event):
        pos = self.app.view.mapToScene(event.pos())
        
        # Check for resize handle interaction or shape selection
        if self.shape_handler.handle_mouse_press(event, pos):
            return
            
        # Start new rectangle
        self.drawing = True
        self.rect_item = QGraphicsRectItem()
        self.rect_item.setPen(QPen(self.current_color, self.line_width))
        self.rect_item.setData(0, "rectangle")  # Mark as rectangle
        self.rect_item.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.rect_item.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.app.scene.addItem(self.rect_item)
        self.last_point = pos

    def mouse_move(self, event):
        pos = self.app.view.mapToScene(event.pos())
        
        if self.shape_handler.handle_mouse_move(event, pos):
            return
            
        if self.drawing and self.last_point:
            rect = QRectF(self.last_point, pos).normalized()
            self.rect_item.setRect(rect)

    def mouse_release(self, event):
        if not self.drawing:
            if self.shape_handler.handle_mouse_release(event):
                return
            return
            
        self.drawing = False
        pos = self.app.view.mapToScene(event.pos())
        
        if self.last_point and self.rect_item:
            rect = QRectF(self.last_point, pos).normalized()
            self.rect_item.setRect(rect)
            self.shape_handler.select_shape(self.rect_item)
            self.last_point = None 
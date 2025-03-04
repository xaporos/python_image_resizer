from PyQt5.QtWidgets import QGraphicsLineItem
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt, QLineF
from .base_tool import BaseTool
from ..base_shape_handler import BaseShapeHandler

class LineTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.shape_handler = BaseShapeHandler(app)
        self.current_color = Qt.red
        self.line_width = 2
        self.line_item = None
        self.drawing = False
        self.start_point = None

    def activate(self):
        super().activate()
        self.drawing = False
        self.start_point = None
        self.line_item = None
        if self.shape_handler:
            self.shape_handler.clear_selection()

    def deactivate(self):
        super().deactivate()
        if self.shape_handler:
            self.shape_handler.clear_selection()
        self.line_item = None
        self.drawing = False
        self.start_point = None

    def mouse_press(self, event):
        pos = self.app.view.mapToScene(event.pos())
        
        if self.shape_handler.handle_mouse_press(event, pos):
            return
            
        self.drawing = True
        self.start_point = pos
        
        self.line_item = QGraphicsLineItem()
        pen = QPen(self.current_color, self.line_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        self.line_item.setPen(pen)
        self.line_item.setData(0, "line")
        self.line_item.setFlag(QGraphicsLineItem.ItemIsSelectable)
        self.app.scene.addItem(self.line_item)

    def mouse_move(self, event):
        pos = self.app.view.mapToScene(event.pos())
        
        if self.shape_handler.handle_mouse_move(event, pos):
            return
            
        if self.drawing and self.start_point and self.line_item:
            line = QLineF(self.start_point, pos)
            self.line_item.setLine(line)

    def mouse_release(self, event):
        if self.shape_handler.handle_mouse_release(event):
            return

        if not self.drawing:
            return

        pos = self.app.view.mapToScene(event.pos())
        
        if self.start_point and self.line_item and self.line_item.scene():
            line = QLineF(self.start_point, pos)
            self.line_item.setLine(line)
            
            self.shape_handler.select_shape(self.line_item)
            
            if hasattr(self.app, 'image_handler'):
                self.app.image_handler.save_state()
            
            self.drawing = False
            self.start_point = None
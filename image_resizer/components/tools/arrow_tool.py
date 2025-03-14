from PyQt5.QtWidgets import QGraphicsLineItem
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt, QLineF, QPointF
from .base_tool import BaseTool
from ..base_shape_handler import BaseShapeHandler
import math

class ArrowLineItem(QGraphicsLineItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_arrow = True
        self._arrow_size = 20
        # Set data for base shape handler compatibility
        self.setData(0, "arrow")
        self.setData(1, self._arrow_size)

    def paint(self, painter, option, widget):
        # Draw the main line
        painter.setPen(self.pen())
        painter.drawLine(self.line())
        
        # Calculate arrow head points in scene coordinates
        line = self.line()
        p1_scene = self.mapToScene(line.p1())
        p2_scene = self.mapToScene(line.p2())
        
        # Calculate angle in scene coordinates
        dx = p2_scene.x() - p1_scene.x()
        dy = p2_scene.y() - p1_scene.y()
        angle = math.atan2(dy, dx)
        
        # Calculate arrow head points in scene coordinates
        arrow_p1_scene = QPointF(
            p2_scene.x() - self._arrow_size * math.cos(angle + math.pi/6),
            p2_scene.y() - self._arrow_size * math.sin(angle + math.pi/6)
        )
        
        arrow_p2_scene = QPointF(
            p2_scene.x() - self._arrow_size * math.cos(angle - math.pi/6),
            p2_scene.y() - self._arrow_size * math.sin(angle - math.pi/6)
        )
        
        # Convert scene coordinates to item coordinates for drawing
        arrow_p1 = self.mapFromScene(arrow_p1_scene)
        arrow_p2 = self.mapFromScene(arrow_p2_scene)
        
        # Store points in scene coordinates for the base shape handler
        self.setData(2, [arrow_p1_scene, arrow_p2_scene])
        self.setData(3, angle)
        
        # Draw the arrow head
        painter.drawLine(self.line().p2(), arrow_p1)
        painter.drawLine(self.line().p2(), arrow_p2)

    def set_arrow_size(self, size):
        self._arrow_size = size
        self.setData(1, size)
        self.update()

class ArrowTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.shape_handler = BaseShapeHandler(app)
        self.current_color = Qt.red
        self.line_width = 2
        self.arrow_item = None
        self.drawing = False
        self.start_point = None
        self.arrow_size = 20  # Size of arrow head

    def activate(self):
        super().activate()
        self.drawing = False
        self.start_point = None
        self.arrow_item = None
        if self.shape_handler:
            self.shape_handler.clear_selection()

    def deactivate(self):
        super().deactivate()
        if self.shape_handler:
            self.shape_handler.clear_selection()
        self.arrow_item = None
        self.drawing = False
        self.start_point = None

    def mouse_press(self, event):
        pos = self.app.view.mapToScene(event.pos())
        
        if self.shape_handler.handle_mouse_press(event, pos):
            return
            
        self.drawing = True
        self.start_point = pos
        
        self.arrow_item = ArrowLineItem()
        self.arrow_item.set_arrow_size(self.arrow_size)  # Set arrow size
        pen = QPen(self.current_color, self.line_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        self.arrow_item.setPen(pen)
        self.arrow_item.setFlag(QGraphicsLineItem.ItemIsSelectable)
        self.app.scene.addItem(self.arrow_item)

    def mouse_move(self, event):
        pos = self.app.view.mapToScene(event.pos())
        
        if self.shape_handler.handle_mouse_move(event, pos):
            return
            
        if self.drawing and self.start_point and self.arrow_item:
            line = QLineF(self.start_point, pos)
            self.arrow_item.setLine(line)

    def mouse_release(self, event):
        if self.shape_handler.handle_mouse_release(event):
            return

        if not self.drawing:
            return

        pos = self.app.view.mapToScene(event.pos())
        
        if self.start_point and self.arrow_item and self.arrow_item.scene():
            line = QLineF(self.start_point, pos)
            self.arrow_item.setLine(line)
            
            # Save state before selecting the shape
            if hasattr(self.app, 'image_handler'):
                self.app.image_handler.save_state()
            
            # Select the shape but stay in arrow tool
            self.shape_handler.select_shape(self.arrow_item)
            
            self.drawing = False
            self.start_point = None 
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
        line = self.line()
        painter.drawLine(line)
        
        # Only draw arrow if line has some length
        if line.length() < 1:
            return
        
        # Get the line endpoints in item coordinates
        p2 = line.p2()  # End point
        
        # Calculate angle for arrow head
        angle = math.atan2(line.dy(), line.dx())
        
        # Calculate arrow head points in item coordinates
        arrow_p1 = QPointF(
            p2.x() - self._arrow_size * math.cos(angle + math.pi/6),
            p2.y() - self._arrow_size * math.sin(angle + math.pi/6)
        )
        
        arrow_p2 = QPointF(
            p2.x() - self._arrow_size * math.cos(angle - math.pi/6),
            p2.y() - self._arrow_size * math.sin(angle - math.pi/6)
        )
        
        # Draw the arrow head directly in item coordinates
        painter.drawLine(p2, arrow_p1)
        painter.drawLine(p2, arrow_p2)
        
        # Store the data for use in the shape handler when finalizing
        p2_scene = self.mapToScene(p2)
        arrow_p1_scene = self.mapToScene(arrow_p1)
        arrow_p2_scene = self.mapToScene(arrow_p2)
        
        # Store all necessary data
        self.setData(2, [arrow_p1_scene, arrow_p2_scene])
        self.setData(3, angle)
        self.setData(4, p2_scene)

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
            
            # Select the shape but stay in arrow tool
            self.shape_handler.select_shape(self.arrow_item)
            
            self.drawing = False
            self.start_point = None 
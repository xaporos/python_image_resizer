from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt
from .base_tool import BaseTool

class PencilTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.temp_image = None
        self.current_color = Qt.red  # Default color
        self.line_width = 2  # Default line width

    def activate(self):
        # Store the current image when tool is activated
        for item in self.app.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                self.temp_image = item.pixmap().copy()
                break

    def deactivate(self):
        super().deactivate()
        self.temp_image = None

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

    def mouse_move(self, event):
        if not self.drawing or not self.temp_image:
            return
            
        pos = self.app.view.mapToScene(event.pos())
        if self.last_point:
            painter = QPainter(self.temp_image)
            painter.setPen(QPen(self.current_color, self.line_width))
            painter.setRenderHint(QPainter.Antialiasing)
            painter.drawLine(self.last_point, pos)
            painter.end()
            
            # Update scene with temporary image
            self.app.scene.clear()
            self.app.scene.addPixmap(self.temp_image)
            self.app.image_handler.update_info_label()
            self.last_point = pos

    def mouse_release(self, event):
        self.drawing = False
        self.last_point = None
        if self.temp_image:
            # Don't save state here since we already saved it at start
            self.app.scene.clear()
            self.app.scene.addPixmap(self.temp_image)
            self.app.image_handler.update_info_label() 
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush
from PyQt5.QtCore import Qt, QRectF
from .base_tool import BaseTool

class EraserTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.temp_image = None
        self.erasing = False
        self.line_width = 10  # Default eraser size (wider than pencil)
        self.last_point = None
        self.square_eraser = True  # Whether to use a square or round eraser shape

    def activate(self):
        # Store the current image when tool is activated
        for item in self.app.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                self.temp_image = item.pixmap().copy()
                break
                
    def deactivate(self):
        super().deactivate()
        self.temp_image = None
        self.erasing = False
        self.last_point = None
        
    def mouse_press(self, event):
        pos = self.app.view.mapToScene(event.pos())
        self.erasing = True
        self.last_point = pos
        
        # Find and store the current pixmap and save state
        for item in self.app.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                self.temp_image = item.pixmap().copy()
                self.app.image_handler.save_state()  # Save state when starting to erase
                break
                
        # Apply the first eraser mark
        self.erase_at_position(pos)
                
    def mouse_move(self, event):
        if not self.erasing or not self.temp_image:
            return
            
        pos = self.app.view.mapToScene(event.pos())
        if self.last_point:
            # Erase along the path from last point to current point
            painter = QPainter(self.temp_image)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            
            # Set up the transparent pen for erasing
            pen = QPen(Qt.transparent, self.line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            
            # For smoother erasing, draw multiple points along the line
            # Calculate Manhattan distance between points
            manhattan_distance = abs(self.last_point.x() - pos.x()) + abs(self.last_point.y() - pos.y())
            steps = max(int(manhattan_distance / 2), 1)
            
            for i in range(steps + 1):
                t = i / steps if steps > 0 else 0
                x = self.last_point.x() * (1 - t) + pos.x() * t
                y = self.last_point.y() * (1 - t) + pos.y() * t
                
                if self.square_eraser:
                    # Draw a transparent square
                    half_width = self.line_width / 2
                    painter.fillRect(QRectF(x - half_width, y - half_width, 
                                          self.line_width, self.line_width), 
                                   Qt.transparent)
                else:
                    # Draw a transparent circle (for round eraser)
                    brush = QBrush(Qt.transparent)
                    painter.setBrush(brush)
                    painter.drawEllipse(x - self.line_width/2, y - self.line_width/2, 
                                      self.line_width, self.line_width)
            
            painter.end()
            
            # Update scene with temporary image
            self.app.scene.clear()
            self.app.scene.addPixmap(self.temp_image)
            self.app.image_handler.update_info_label()
            self.last_point = pos

    def erase_at_position(self, pos):
        """Erase at a specific position"""
        if not self.temp_image:
            return
            
        painter = QPainter(self.temp_image)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        
        if self.square_eraser:
            # Draw a transparent square
            half_width = self.line_width / 2
            painter.fillRect(QRectF(pos.x() - half_width, pos.y() - half_width, 
                                  self.line_width, self.line_width), 
                           Qt.transparent)
        else:
            # Draw a transparent circle (for round eraser)
            pen = QPen(Qt.transparent, 1)
            brush = QBrush(Qt.transparent)
            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawEllipse(pos.x() - self.line_width/2, pos.y() - self.line_width/2, 
                              self.line_width, self.line_width)
        
        painter.end()
        
        # Update scene with temporary image
        self.app.scene.clear()
        self.app.scene.addPixmap(self.temp_image)
        self.app.image_handler.update_info_label()

    def mouse_release(self, event):
        self.erasing = False
        self.last_point = None
        if self.temp_image:
            # Don't save state here since we already saved it at start
            self.app.scene.clear()
            self.app.scene.addPixmap(self.temp_image)
            self.app.image_handler.update_info_label() 
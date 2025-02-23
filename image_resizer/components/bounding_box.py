from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QBrush

class BoundingBoxItem(QGraphicsRectItem):
    def __init__(self, shape, parent=None):
        super().__init__(parent)
        self.shape = shape
        
        # Set appearance
        self.setPen(QPen(Qt.white, 1, Qt.DashLine))
        self.setBrush(QBrush(Qt.NoBrush))
        self.setZValue(2)
        
        self.update_geometry()

    def update_geometry(self):
        # Get shape geometry including its position
        if isinstance(self.shape, QGraphicsLineItem):
            rect = self.shape.boundingRect()
        else:
            rect = self.shape.rect()
        
        # Translate rect to shape's position
        rect.translate(self.shape.pos())
        
        # Add margin
        margin = 5
        rect.adjust(-margin, -margin, margin, margin)
        self.setRect(rect) 
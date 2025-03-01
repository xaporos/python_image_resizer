from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter

class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.parent = parent
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    def mousePressEvent(self, event):
        if self.parent:
            self.parent.mouse_press(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.parent:
            self.parent.mouse_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.parent:
            self.parent.mouse_release(event)
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """Override wheel event to sync with zoom slider"""
        if event.modifiers() & Qt.ControlModifier:
            # Get current zoom level from slider
            current_zoom = self.parent.zoom_slider.value()
            
            # Calculate zoom factor
            delta = event.angleDelta().y()
            zoom_factor = 1.1 if delta > 0 else 0.9
            
            # Calculate new zoom level
            new_zoom = current_zoom * zoom_factor
            
            # Clamp to slider range
            new_zoom = max(self.parent.zoom_slider.minimum(),
                         min(self.parent.zoom_slider.maximum(), new_zoom))
            
            # Update slider (which will trigger zoom_changed)
            self.parent.zoom_slider.setValue(int(new_zoom))
        else:
            super().wheelEvent(event) 
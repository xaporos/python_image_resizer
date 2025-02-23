from PyQt5.QtCore import QObject

class BaseTool(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.drawing = False
        self.last_point = None

    def mouse_press(self, event):
        pass

    def mouse_move(self, event):
        pass

    def mouse_release(self, event):
        pass

    def activate(self):
        pass

    def deactivate(self):
        self.drawing = False
        self.last_point = None 
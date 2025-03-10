from PyQt5.QtCore import QObject

class BaseTool:
    def __init__(self, app):
        self.app = app
        self.drawing = False
        self.last_point = None
        self.line_width = 3  # Set default line width for all tools

    def activate(self):
        # Add this method back
        pass

    def deactivate(self):
        self.drawing = False
        self.last_point = None

    def mouse_press(self, event):
        pass

    def mouse_move(self, event):
        pass

    def mouse_release(self, event):
        """Base mouse release handler that deselects the tool"""
        # Deselect the tool after use
        if hasattr(self.app, 'tool_manager'):
            self.app.tool_manager.set_tool(None)
            
            # Uncheck all tool buttons
            if hasattr(self.app.toolbar, 'arrow_btn'):
                self.app.toolbar.arrow_btn.setChecked(False)
            if hasattr(self.app.toolbar, 'circle_btn'):
                self.app.toolbar.circle_btn.setChecked(False)
            if hasattr(self.app.toolbar, 'rect_btn'):
                self.app.toolbar.rect_btn.setChecked(False)

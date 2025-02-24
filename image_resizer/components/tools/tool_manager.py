from PyQt5.QtWidgets import QGraphicsPixmapItem
from .crop_tool import CropTool
from .pencil_tool import PencilTool
from .arrow_tool import ArrowTool

class ToolManager:
    def __init__(self, app):
        self.app = app
        self.current_tool = None
        self.tools = {
            'crop': CropTool(app),
            'pencil': PencilTool(app),
            'arrow': ArrowTool(app),
            # We'll add other tools here later
        }

    def set_tool(self, tool_name):
        """Set the current tool"""
        print(f"Setting tool to: {tool_name}")
        
        # Deactivate current tool
        if self.current_tool:
            self.current_tool.deactivate()
        
        # Set new tool
        if tool_name is None:
            self.current_tool = None
        else:
            self.current_tool = self.tools.get(tool_name)
            if self.current_tool:
                self.current_tool.activate()

    def handle_mouse_press(self, event):
        if self.current_tool:
            self.current_tool.mouse_press(event)

    def handle_mouse_move(self, event):
        if self.current_tool:
            self.current_tool.mouse_move(event)

    def handle_mouse_release(self, event):
        if self.current_tool:
            self.current_tool.mouse_release(event) 
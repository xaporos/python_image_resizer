from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from image_resizer.components.tools.crop_tool import CropTool
from image_resizer.components.tools.pencil_tool import PencilTool
from image_resizer.components.tools.arrow_tool import ArrowTool
from image_resizer.components.tools.circle_tool import CircleTool
from image_resizer.components.tools.rectangle_tool import RectangleTool
from image_resizer.components.tools.text_tool import TextTool
from image_resizer.components.tools.line_tool import LineTool

class ToolManager:
    def __init__(self, app):
        self.app = app
        self.current_tool = None
        self.current_color = QColor(Qt.black)  # Default color
        self.tools = {
            'crop': CropTool(app),
            'pencil': PencilTool(app),
            'line': LineTool(app),
            'arrow': ArrowTool(app),
            'circle': CircleTool(app),
            'rectangle': RectangleTool(app),
            'text': TextTool(app),
            # We'll add other tools here later
        }

    def set_tool(self, tool_name):
        """Set the current tool"""
        # Finalize any active shapes on the current tool
        if self.current_tool and hasattr(self.current_tool, 'shape_handler'):
            self.current_tool.shape_handler.finalize_shape()
        
        # Deactivate current tool
        if self.current_tool:
            self.current_tool.deactivate()
        
        # Set new tool
        self.current_tool = self.tools.get(tool_name)
        if self.current_tool:
            self.current_tool.activate()
            # Set the current color for the new tool
            if hasattr(self.current_tool, 'current_color'):
                self.current_tool.current_color = self.current_color

        # Update toolbar button states
        if hasattr(self.app.toolbar, 'arrow_btn'):
            self.app.toolbar.arrow_btn.setChecked(tool_name == 'arrow')
        if hasattr(self.app.toolbar, 'circle_btn'):
            self.app.toolbar.circle_btn.setChecked(tool_name == 'circle')
        if hasattr(self.app.toolbar, 'pencil_btn'):
            self.app.toolbar.pencil_btn.setChecked(tool_name == 'pencil')
        if hasattr(self.app.toolbar, 'crop_btn'):
            self.app.toolbar.crop_btn.setChecked(tool_name == 'crop')
        if hasattr(self.app.toolbar, 'rect_btn'):
            self.app.toolbar.rect_btn.setChecked(tool_name == 'rectangle')
        if hasattr(self.app.toolbar, 'line_btn'):
            self.app.toolbar.line_btn.setChecked(tool_name == 'line')
        if hasattr(self.app.toolbar, 'text_btn'):
            self.app.toolbar.text_btn.setChecked(tool_name == 'text')

    def set_current_color(self, color):
        """Set the current color for drawing tools"""
        self.current_color = color
        # Update current tool's color if it has one
        if self.current_tool and hasattr(self.current_tool, 'current_color'):
            self.current_tool.current_color = color

    def handle_mouse_press(self, event):
        if self.current_tool:
            self.current_tool.mouse_press(event)

    def handle_mouse_move(self, event):
        if self.current_tool:
            self.current_tool.mouse_move(event)

    def handle_mouse_release(self, event):
        if self.current_tool:
            self.current_tool.mouse_release(event)
            # After shape is created, deselect the tool
            if hasattr(self.app, 'tools_toolbar'):
                if isinstance(self.current_tool, CropTool) and hasattr(self.app.tools_toolbar, 'crop_btn'):
                    self.app.tools_toolbar.crop_btn.setChecked(False)
                elif isinstance(self.current_tool, TextTool) and hasattr(self.app.tools_toolbar, 'text_btn'):
                    self.app.tools_toolbar.text_btn.setChecked(False)
                elif isinstance(self.current_tool, ArrowTool) and hasattr(self.app.tools_toolbar, 'arrow_btn'):
                    self.app.tools_toolbar.arrow_btn.setChecked(False)
                elif isinstance(self.current_tool, LineTool) and hasattr(self.app.tools_toolbar, 'line_btn'):
                    self.app.tools_toolbar.line_btn.setChecked(False)
                elif isinstance(self.current_tool, CircleTool) and hasattr(self.app.tools_toolbar, 'circle_btn'):
                    self.app.tools_toolbar.circle_btn.setChecked(False)
                elif isinstance(self.current_tool, RectangleTool) and hasattr(self.app.tools_toolbar, 'rect_btn'):
                    self.app.tools_toolbar.rect_btn.setChecked(False) 
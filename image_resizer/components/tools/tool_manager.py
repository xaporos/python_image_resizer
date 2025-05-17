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
from image_resizer.components.tools.eraser_tool import EraserTool
from image_resizer.components.tools.highlight_tool import HighlightTool

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
            'highlight': HighlightTool(app),
            'eraser': EraserTool(app),
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
            # Set the current line width for the new tool
            if hasattr(self.current_tool, 'line_width'):
                # Get current thickness from toolbar if available
                if hasattr(self.app, 'toolbar') and hasattr(self.app.toolbar, 'thickness_slider'):
                    self.current_tool.line_width = self.app.toolbar.thickness_slider.value()
                    # Update cursor size for eraser tool if applicable
                    if tool_name == 'eraser' and hasattr(self.current_tool, 'update_cursor_size'):
                        self.current_tool.update_cursor_size()
                else:
                    self.current_tool.line_width = 3  # Default thickness

        # Update toolbar button states
        if hasattr(self.app, 'tools_toolbar'):
            # Uncheck all buttons first
            self.app.tools_toolbar.crop_btn.setChecked(False)
            self.app.tools_toolbar.pencil_btn.setChecked(False)
            self.app.tools_toolbar.line_btn.setChecked(False)
            self.app.tools_toolbar.arrow_btn.setChecked(False)
            self.app.tools_toolbar.circle_btn.setChecked(False)
            self.app.tools_toolbar.rect_btn.setChecked(False)
            self.app.tools_toolbar.text_btn.setChecked(False)
            self.app.tools_toolbar.highlight_btn.setChecked(False)
            self.app.tools_toolbar.eraser_btn.setChecked(False)
            
            # Check the selected tool's button
            if tool_name == 'crop':
                self.app.tools_toolbar.crop_btn.setChecked(True)
            elif tool_name == 'pencil':
                self.app.tools_toolbar.pencil_btn.setChecked(True)
            elif tool_name == 'line':
                self.app.tools_toolbar.line_btn.setChecked(True)
            elif tool_name == 'arrow':
                self.app.tools_toolbar.arrow_btn.setChecked(True)
            elif tool_name == 'circle':
                self.app.tools_toolbar.circle_btn.setChecked(True)
            elif tool_name == 'rectangle':
                self.app.tools_toolbar.rect_btn.setChecked(True)
            elif tool_name == 'text':
                self.app.tools_toolbar.text_btn.setChecked(True)
            elif tool_name == 'highlight':
                self.app.tools_toolbar.highlight_btn.setChecked(True)
            elif tool_name == 'eraser':
                self.app.tools_toolbar.eraser_btn.setChecked(True)

    def set_current_color(self, color):
        """Set the current color for drawing tools"""
        self.current_color = color
        
        # Update eraser tool color even if it's not active
        if 'eraser' in self.tools:
            self.tools['eraser'].set_current_color(color)
        
        # Update current tool's color if it has one
        if self.current_tool:
            if hasattr(self.current_tool, 'current_color'):
                self.current_tool.current_color = color
                
            # Update active shape/text color if it exists
            if hasattr(self.current_tool, 'text_item') and self.current_tool.text_item:
                # For text tool
                self.current_tool.text_item.setDefaultTextColor(color)
            elif hasattr(self.current_tool, 'shape_handler'):
                # For shape tools (rectangle, circle, line, arrow)
                if self.current_tool.shape_handler.selected_shape:
                    pen = self.current_tool.shape_handler.selected_shape.pen()
                    pen.setColor(color)
                    self.current_tool.shape_handler.selected_shape.setPen(pen)
                elif hasattr(self.current_tool, 'rect_item') and self.current_tool.rect_item:
                    # For rectangle being drawn
                    pen = self.current_tool.rect_item.pen()
                    pen.setColor(color)
                    self.current_tool.rect_item.setPen(pen)
                elif hasattr(self.current_tool, 'circle_item') and self.current_tool.circle_item:
                    # For circle being drawn
                    pen = self.current_tool.circle_item.pen()
                    pen.setColor(color)
                    self.current_tool.circle_item.setPen(pen)
                elif hasattr(self.current_tool, 'line_item') and self.current_tool.line_item:
                    # For line being drawn
                    pen = self.current_tool.line_item.pen()
                    pen.setColor(color)
                    self.current_tool.line_item.setPen(pen)
                elif hasattr(self.current_tool, 'arrow_item') and self.current_tool.arrow_item:
                    # For arrow being drawn
                    pen = self.current_tool.arrow_item.pen()
                    pen.setColor(color)
                    self.current_tool.arrow_item.setPen(pen)

    def handle_mouse_press(self, event):
        if self.current_tool:
            self.current_tool.mouse_press(event)

    def handle_mouse_move(self, event):
        if self.current_tool:
            self.current_tool.mouse_move(event)

    def handle_mouse_release(self, event):
        if self.current_tool:
            self.current_tool.mouse_release(event) 
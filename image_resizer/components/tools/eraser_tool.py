from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsEllipseItem
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush
from PyQt5.QtCore import Qt, QRectF
from .base_tool import BaseTool

class EraserTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.temp_image = None
        self.erasing = False
        self.line_width = 10  # Default eraser size (wider than pencil)
        self.width_multiplier = 3  # Eraser size multiplier 
        self.last_point = None
        self.square_eraser = True  # Whether to use a square or round eraser shape
        self.cursor_item = None  # Visual indicator for eraser boundary
        self.color_mode = False  # False = transparent erasing, True = color erasing
        self.current_color = QColor(Qt.black)  # Default color for color mode
        self.current_image_path = None  # Track which image we're erasing
    
    @property
    def actual_line_width(self):
        """Get the actual line width after applying the multiplier"""
        return self.line_width * self.width_multiplier

    def set_color_mode(self, enabled):
        """Toggle between transparent eraser and color eraser modes"""
        self.color_mode = enabled
        # Update cursor to reflect the current mode
        self.update_cursor_appearance()
        
    def update_cursor_appearance(self):
        """Update cursor appearance based on the current mode"""
        if not self.is_cursor_valid():
            return
            
        try:
            # Update cursor style based on mode
            if self.color_mode:
                # Color mode - use current color with semi-transparency
                color = QColor(self.current_color)
                color.setAlpha(120)  # Semi-transparent
                self.cursor_item.setBrush(QBrush(color))
                self.cursor_item.setPen(QPen(QColor(0, 0, 0, 200), 1, Qt.DashLine))
            else:
                # Transparent mode - white with semi-transparency
                self.cursor_item.setBrush(QBrush(QColor(255, 255, 255, 60)))
                self.cursor_item.setPen(QPen(QColor(0, 0, 0, 150), 1, Qt.DashLine))
        except (RuntimeError, ReferenceError, TypeError):
            # If there's an error updating the appearance, recreate the cursor
            self.create_cursor_indicator()

    def is_cursor_valid(self):
        """Check if cursor item is still valid and not deleted"""
        return (self.cursor_item is not None and 
           hasattr(self.app, 'scene'))

    def activate(self):
        # Get current image path
        current_item = self.app.image_list.currentItem()
        if current_item:
            self.current_image_path = self.app.image_handler.get_file_path_from_item(current_item)
        
        # Store the current image when tool is activated
        for item in self.app.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                self.temp_image = item.pixmap().copy()
                break
        
        # Remove any existing cursor first
        self.remove_cursor_safely()
        self.cursor_item = None
        
        # Create cursor indicator for eraser
        self.create_cursor_indicator()
        
        # Get the current color from tool manager
        if hasattr(self.app, 'tool_manager'):
            self.current_color = self.app.tool_manager.current_color
                
    def deactivate(self):
        super().deactivate()
        self.temp_image = None
        self.erasing = False
        self.last_point = None
        self.current_image_path = None
        
        # Remove cursor indicator safely
        self.remove_cursor_safely()
        self.cursor_item = None
    
    def remove_cursor_safely(self):
        """Safely remove the cursor item from the scene"""
        if self.is_cursor_valid():
            try:
                # Check if the item is still in the scene
                if self.cursor_item.scene() == self.app.scene:
                    self.app.scene.removeItem(self.cursor_item)
            except (RuntimeError, ReferenceError, TypeError):
                # Catch any exceptions if the item or scene has been deleted
                pass
        
        # Always set to None after removal attempt
        self.cursor_item = None
    
    def create_cursor_indicator(self):
        """Create a visual indicator for the eraser cursor"""
        # Safely remove the old cursor first
        self.remove_cursor_safely()
        
        # Make sure we have a scene
        if not hasattr(self.app, 'scene'):
            return
        
        width = self.actual_line_width
        
        try:
            if self.square_eraser:
                # Create square cursor
                self.cursor_item = QGraphicsRectItem(0, 0, width, width)
                # Center the rect at origin
                self.cursor_item.setPos(-width/2, -width/2)
            else:
                # Create circle cursor
                self.cursor_item = QGraphicsEllipseItem(0, 0, width, width)
                # Center the ellipse at origin
                self.cursor_item.setPos(-width/2, -width/2)
            
            # Set appearance based on mode
            self.update_cursor_appearance()
            
            # Make it non-interactive with mouse events
            self.cursor_item.setAcceptHoverEvents(False)
            self.cursor_item.setAcceptedMouseButtons(Qt.NoButton)
            
            # Make it visible on top
            self.cursor_item.setZValue(1000)
            
            # Add to scene
            self.app.scene.addItem(self.cursor_item)
        except (RuntimeError, ReferenceError):
            # If there's an error creating the cursor, set it to None
            self.cursor_item = None
    
    def update_cursor_size(self):
        """Update the cursor size when thickness changes"""
        if self.is_cursor_valid():
            self.create_cursor_indicator()
        
    def update_cursor_position(self, pos):
        """Update the cursor position"""
        if not self.is_cursor_valid():
            return
            
        try:
            # Check that the cursor is still in the scene
            if self.cursor_item.scene() == self.app.scene:
                width = self.actual_line_width
                # Center the cursor at the mouse position
                self.cursor_item.setPos(pos.x() - width/2, pos.y() - width/2)
        except (RuntimeError, ReferenceError, TypeError):
            # If there's an error updating the position, recreate the cursor
            self.create_cursor_indicator()
    
    def set_current_color(self, color):
        """Set the current color for color erasing"""
        self.current_color = color
        self.update_cursor_appearance()
        
    def mouse_press(self, event):
        # Update the current image path before we start erasing
        current_item = self.app.image_list.currentItem()
        if current_item:
            self.current_image_path = self.app.image_handler.get_file_path_from_item(current_item)
            
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
        # Get position
        try:
            pos = self.app.view.mapToScene(event.pos())
        except (RuntimeError, ReferenceError):
            return
        
        # Update cursor position even if not erasing
        self.update_cursor_position(pos)
        
        # Verify we're still on the same image
        current_item = self.app.image_list.currentItem()
        if current_item:
            current_path = self.app.image_handler.get_file_path_from_item(current_item)
            if current_path != self.current_image_path:
                self.erasing = False
                self.last_point = None
                return
        
        if not self.erasing or not self.temp_image:
            return
            
        if self.last_point:
            # Erase along the path from last point to current point
            painter = QPainter(self.temp_image)
            
            # Set composition mode based on erasing mode
            if self.color_mode:
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            else:
                painter.setCompositionMode(QPainter.CompositionMode_Source)
            
            # Set up the brush/pen for erasing
            color = self.current_color if self.color_mode else Qt.transparent
            pen = QPen(color, self.actual_line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            brush = QBrush(color)
            painter.setPen(pen)
            painter.setBrush(brush)
            
            # For smoother erasing, draw multiple points along the line
            # Calculate Manhattan distance between points
            manhattan_distance = abs(self.last_point.x() - pos.x()) + abs(self.last_point.y() - pos.y())
            steps = max(int(manhattan_distance / 2), 1)
            
            for i in range(steps + 1):
                t = i / steps if steps > 0 else 0
                x = self.last_point.x() * (1 - t) + pos.x() * t
                y = self.last_point.y() * (1 - t) + pos.y() * t
                
                if self.square_eraser:
                    # Draw a square
                    half_width = self.actual_line_width / 2
                    painter.fillRect(QRectF(x - half_width, y - half_width, 
                                          self.actual_line_width, self.actual_line_width), 
                                   color)
                else:
                    # Draw a circle
                    painter.drawEllipse(x - self.actual_line_width/2, y - self.actual_line_width/2, 
                                      self.actual_line_width, self.actual_line_width)
            
            painter.end()
            
            # Store the cursor item's scene and remove it before clearing the scene
            self.remove_cursor_safely()
            
            try:
                # Update scene with temporary image
                self.app.scene.clear()
                self.app.scene.addPixmap(self.temp_image)
                
                # Re-add the cursor after the pixmap
                self.create_cursor_indicator()
                self.update_cursor_position(pos)
                
                self.app.image_handler.update_info_label()
                self.last_point = pos
            except (RuntimeError, ReferenceError):
                # Scene might have been deleted or changed
                self.erasing = False
                self.last_point = None

    def erase_at_position(self, pos):
        """Erase at a specific position"""
        if not self.temp_image:
            return
            
        painter = QPainter(self.temp_image)
        
        # Set composition mode based on erasing mode
        if self.color_mode:
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        else:
            painter.setCompositionMode(QPainter.CompositionMode_Source)
        
        # Use transparent color or the selected color
        color = self.current_color if self.color_mode else Qt.transparent
        
        if self.square_eraser:
            # Draw a square
            half_width = self.actual_line_width / 2
            painter.fillRect(QRectF(pos.x() - half_width, pos.y() - half_width, 
                                  self.actual_line_width, self.actual_line_width), 
                           color)
        else:
            # Draw a circle
            pen = QPen(color, 1)
            brush = QBrush(color)
            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawEllipse(pos.x() - self.actual_line_width/2, pos.y() - self.actual_line_width/2, 
                              self.actual_line_width, self.actual_line_width)
        
        painter.end()
        
        # Store the cursor item's scene and remove it before clearing the scene
        self.remove_cursor_safely()
        
        try:
            # Update scene with temporary image
            self.app.scene.clear()
            self.app.scene.addPixmap(self.temp_image)
            
            # Re-add the cursor after the pixmap
            self.create_cursor_indicator()
            self.update_cursor_position(pos)
            
            self.app.image_handler.update_info_label()
        except (RuntimeError, ReferenceError):
            # Scene might have been deleted or changed
            pass

    def mouse_release(self, event):
        # Verify we're still on the same image
        current_item = self.app.image_list.currentItem()
        if current_item:
            current_path = self.app.image_handler.get_file_path_from_item(current_item)
            if current_path != self.current_image_path:
                self.erasing = False
                self.last_point = None
                return
                
        if not self.erasing or not self.temp_image:
            self.erasing = False
            self.last_point = None
            return
            
        try:
            # Get position
            pos = self.app.view.mapToScene(event.pos())
            
            # Store the cursor item's scene and remove it before clearing the scene
            self.remove_cursor_safely()
            
            # Update edited images dictionary with current image
            if self.current_image_path and self.temp_image:
                self.app.image_handler.edited_images[self.current_image_path] = self.temp_image.copy()
            
            # Don't save state here since we already saved it at start
            self.app.scene.clear()
            self.app.scene.addPixmap(self.temp_image)
            
            # Re-add cursor after clearing the scene
            self.create_cursor_indicator()
            
            # Update cursor position
            self.update_cursor_position(pos)
            
            self.app.image_handler.update_info_label()
            
            # Save state after completing eraser action to ensure it's not lost
            self.app.image_handler.save_state()
            
        except (RuntimeError, ReferenceError):
            # Scene might have been deleted or changed
            pass
            
        self.erasing = False
        self.last_point = None 
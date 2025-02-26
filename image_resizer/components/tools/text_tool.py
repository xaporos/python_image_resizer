from PyQt5.QtWidgets import (QGraphicsTextItem, QWidget, QHBoxLayout, 
                           QFontComboBox, QSpinBox, QToolButton, QColorDialog,
                           QGraphicsPixmapItem)
from PyQt5.QtGui import QFont, QPen, QColor, QTextCursor, QIcon, QPainter, QCursor
from PyQt5.QtCore import Qt, QSize, QTimer, QRectF, QRect
from .base_tool import BaseTool

class TextFormatToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setup_ui()
        self.hide()
        self.text_item = None
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Font family combo box
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Arial"))
        self.font_combo.setFixedWidth(150)
        self.font_combo.activated.connect(lambda: self.setInteracting(True))
        layout.addWidget(self.font_combo)
        
        # Font size spinner
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(12)
        self.size_spin.setFixedWidth(50)
        layout.addWidget(self.size_spin)
        
        # Bold button
        self.bold_btn = QToolButton()
        self.bold_btn.setText("B")
        self.bold_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(QSize(24, 24))
        self.bold_btn.clicked.connect(lambda: self.setInteracting(True))
        layout.addWidget(self.bold_btn)
        
        # Italic button
        self.italic_btn = QToolButton()
        self.italic_btn.setText("I")
        self.italic_btn.setFont(QFont("Arial", 10, QFont.StyleItalic))
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedSize(QSize(24, 24))
        self.italic_btn.clicked.connect(lambda: self.setInteracting(True))
        layout.addWidget(self.italic_btn)
        
        # Color button
        self.color_btn = QToolButton()
        self.color_btn.setText("A")
        self.color_btn.setFixedSize(QSize(24, 24))
        self.color_btn.clicked.connect(lambda: self.setInteracting(True))
        layout.addWidget(self.color_btn)
        
        # Add some spacing
        layout.addSpacing(10)
        
        # Apply button
        self.apply_btn = QToolButton()
        self.apply_btn.setText("✓")  # Checkmark symbol
        self.apply_btn.setToolTip("Apply text and finish editing")
        self.apply_btn.setFixedSize(QSize(24, 24))
        self.apply_btn.setStyleSheet("""
            QToolButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #45a049;
            }
            QToolButton:pressed {
                background-color: #3d8b40;
            }
        """)
        layout.addWidget(self.apply_btn)
        
        self.setFixedHeight(40)
        self.adjustSize()

    def setInteracting(self, state):
        self.is_interacting = state
        if state:
            # Reset interaction state after a delay
            QTimer.singleShot(500, lambda: self.setInteracting(False))

    def enterEvent(self, event):
        super().enterEvent(event)
        self.is_interacting = True

    def leaveEvent(self, event):
        super().leaveEvent(event)
        # Only stop interacting if we're not using controls
        if not self.childAt(self.mapFromGlobal(QCursor.pos())):
            QTimer.singleShot(500, self.stopInteracting)

    def showEvent(self, event):
        super().showEvent(event)
        self.is_showing = True
        
    def hideEvent(self, event):
        super().hideEvent(event)
        self.is_showing = False

    def mousePressEvent(self, event):
        # Prevent toolbar from hiding when clicked
        event.accept()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # Keep interaction state for a bit longer
        QTimer.singleShot(1000, self.stopInteracting)

    def stopInteracting(self):
        # Only stop if we're not currently using any controls
        if not self.underMouse() and not self.hasFocus():
            self.is_interacting = False

    def focusOutEvent(self, event):
        # Ignore focus out if we're still interacting
        if self.is_interacting:
            event.ignore()
            return
        super().focusOutEvent(event)

class SimpleTextItem(QGraphicsTextItem):
    def __init__(self, format_toolbar, parent=None):
        super().__init__(parent)
        self.format_toolbar = format_toolbar
        self.format_toolbar.text_item = self
        self.setDefaultTextColor(Qt.black)
        self.setFont(QFont("Arial", 12))
        self.setTextWidth(300)
        self.setFlag(QGraphicsTextItem.ItemIsFocusable)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        
    def focusInEvent(self, event):
        super().focusInEvent(event)
        # Show toolbar when text item gets focus
        scene_pos = self.mapToScene(self.boundingRect().topLeft())
        view = self.scene().views()[0]
        view_pos = view.mapFromScene(scene_pos)
        screen_pos = view.mapToGlobal(view_pos)
        
        toolbar_x = screen_pos.x()
        toolbar_y = screen_pos.y() - self.format_toolbar.height() - 10
        
        self.format_toolbar.move(toolbar_x, toolbar_y)
        self.format_toolbar.show()
        self.format_toolbar.raise_()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        # Only hide toolbar if clicking outside both text item and toolbar
        cursor_pos = QCursor.pos()
        toolbar_rect = self.format_toolbar.geometry()
        
        # Get text item's screen coordinates
        view = self.scene().views()[0]
        scene_rect = self.sceneBoundingRect()
        top_left = view.mapToGlobal(view.mapFromScene(scene_rect.topLeft()))
        bottom_right = view.mapToGlobal(view.mapFromScene(scene_rect.bottomRight()))
        text_rect = QRect(top_left, bottom_right)
        
        if not toolbar_rect.contains(cursor_pos) and not text_rect.contains(cursor_pos):
            QTimer.singleShot(200, self.checkHideToolbar)

    def checkHideToolbar(self):
        cursor_pos = QCursor.pos()
        toolbar_rect = self.format_toolbar.geometry()
        if not toolbar_rect.contains(cursor_pos) and not self.hasFocus():
            self.format_toolbar.hide()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.toPlainText() == "" or self.hasFocus():
            rect = self.boundingRect()
            pen = QPen(QColor(0, 0, 0, 127))
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(rect)

class TextTool(BaseTool):
    def __init__(self, app):
        super().__init__(app)
        self.text_item = None
        self.format_toolbar = TextFormatToolbar()
        self.setup_format_toolbar()
        self.initial_activation = True  # Track first activation

    def setup_format_toolbar(self):
        # Make toolbar and its widgets focusable
        self.format_toolbar.setFocusPolicy(Qt.StrongFocus)
        self.format_toolbar.font_combo.setFocusPolicy(Qt.StrongFocus)
        self.format_toolbar.size_spin.setFocusPolicy(Qt.StrongFocus)
        self.format_toolbar.bold_btn.setFocusPolicy(Qt.StrongFocus)
        self.format_toolbar.italic_btn.setFocusPolicy(Qt.StrongFocus)
        self.format_toolbar.color_btn.setFocusPolicy(Qt.StrongFocus)
        
        # Connect signals
        self.format_toolbar.font_combo.currentFontChanged.connect(self.update_font)
        self.format_toolbar.size_spin.valueChanged.connect(self.update_font_size)
        self.format_toolbar.bold_btn.toggled.connect(self.update_bold)
        self.format_toolbar.italic_btn.toggled.connect(self.update_italic)
        self.format_toolbar.color_btn.clicked.connect(self.choose_color)
        self.format_toolbar.apply_btn.clicked.connect(self.apply_text)

    def activate(self):
        super().activate()
        self.text_item = None
        # Hide toolbar only on first activation
        if self.initial_activation:
            self.format_toolbar.hide()
            self.initial_activation = False

    def deactivate(self):
        self.initial_activation = True  # Reset for next activation
        super().deactivate()
        self.format_toolbar.hide()
        if self.text_item:
            if not self.text_item.toPlainText().strip():
                self.app.scene.removeItem(self.text_item)
            else:
                self.app.image_handler.save_state()
            self.text_item = None

    def mouse_press(self, event):
        pos = self.app.view.mapToScene(event.pos())
        
        if self.text_item:
            if not self.text_item.contains(self.text_item.mapFromScene(pos)):
                if not self.text_item.toPlainText().strip():
                    self.app.scene.removeItem(self.text_item)
                else:
                    self.app.image_handler.save_state()
                self.text_item = None
                self.format_toolbar.hide()
            return

        # Create new text item
        self.text_item = SimpleTextItem(self.format_toolbar)
        self.text_item.setPos(pos)
        self.app.scene.addItem(self.text_item)
        
        # Delay focus to ensure proper initialization
        QTimer.singleShot(100, lambda: self.setTextItemFocus())
        
    def setTextItemFocus(self):
        if self.text_item and self.text_item.scene():
            self.text_item.setFocus()

    def update_font(self, font):
        if self.text_item:
            current_font = self.text_item.font()
            current_font.setFamily(font.family())
            self.text_item.setFont(current_font)

    def update_font_size(self, size):
        if self.text_item:
            current_font = self.text_item.font()
            current_font.setPointSize(size)
            self.text_item.setFont(current_font)
            # Update the size spinner to reflect the actual size
            self.format_toolbar.size_spin.setValue(size)

    def update_bold(self, bold):
        if self.text_item:
            current_font = self.text_item.font()
            current_font.setBold(bold)
            self.text_item.setFont(current_font)

    def update_italic(self, italic):
        if self.text_item:
            current_font = self.text_item.font()
            current_font.setItalic(italic)
            self.text_item.setFont(current_font)

    def choose_color(self):
        if self.text_item:
            color = QColorDialog.getColor(self.text_item.defaultTextColor())
            if color.isValid():
                self.text_item.setDefaultTextColor(color)
                # Update color button appearance
                self.format_toolbar.color_btn.setStyleSheet(
                    f"QToolButton {{ color: {color.name()}; }}")

    def apply_text(self):
        """Finalize the text and deselect the tool"""
        if self.text_item:
            if self.text_item.toPlainText().strip():
                # Save state before making changes
                self.app.image_handler.save_state()
                
                # Get the text item's properties before removing it
                text = self.text_item.toPlainText()
                font = self.text_item.font()
                color = self.text_item.defaultTextColor()
                pos = self.text_item.pos()
                rect = self.text_item.boundingRect()
                
                # Remove the interactive text item
                self.text_item.clearFocus()
                self.app.scene.removeItem(self.text_item)
                
                # Find the pixmap item and draw the text permanently
                for item in self.app.scene.items():
                    if isinstance(item, QGraphicsPixmapItem):
                        pixmap = item.pixmap().copy()
                        painter = QPainter(pixmap)
                        painter.setFont(font)
                        painter.setPen(color)
                        painter.drawText(
                            QRectF(pos.x(), pos.y(), rect.width(), rect.height()),
                            Qt.TextWordWrap,
                            text
                        )
                        painter.end()
                        
                        # Update scene with new pixmap
                        self.app.scene.clear()
                        self.app.scene.addPixmap(pixmap)
                        break
                
                self.text_item = None
            else:
                self.app.scene.removeItem(self.text_item)
                self.text_item = None
            
        self.format_toolbar.hide()
        if hasattr(self.app.toolbar, 'text_btn'):
            self.app.toolbar.text_btn.setChecked(False)
        self.app.tool_manager.set_tool(None) 
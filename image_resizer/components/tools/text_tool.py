from PyQt5.QtWidgets import (QGraphicsTextItem, QWidget, QHBoxLayout, 
                           QFontComboBox, QSpinBox, QToolButton, QColorDialog)
from PyQt5.QtGui import QFont, QPen, QColor, QTextCursor, QIcon
from PyQt5.QtCore import Qt, QSize
from .base_tool import BaseTool

class TextFormatToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)  # Remove frameless hint
        self.setup_ui()
        self.hide()  # Start hidden
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Font family combo box
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Arial"))
        self.font_combo.setFixedWidth(150)
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
        layout.addWidget(self.bold_btn)
        
        # Italic button
        self.italic_btn = QToolButton()
        self.italic_btn.setText("I")
        self.italic_btn.setFont(QFont("Arial", 10, QFont.StyleItalic))
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedSize(QSize(24, 24))
        layout.addWidget(self.italic_btn)
        
        # Color button
        self.color_btn = QToolButton()
        self.color_btn.setText("A")
        self.color_btn.setFixedSize(QSize(24, 24))
        self.current_color = Qt.black
        layout.addWidget(self.color_btn)
        
        self.setFixedHeight(40)
        self.adjustSize()

class SimpleTextItem(QGraphicsTextItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDefaultTextColor(Qt.black)
        self.setFont(QFont("Arial", 12))
        self.setTextWidth(300)
        self.setFlag(QGraphicsTextItem.ItemIsFocusable)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        
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
        self.format_toolbar = TextFormatToolbar(self.app)
        self.setup_format_toolbar()

    def setup_format_toolbar(self):
        # Connect signals
        self.format_toolbar.font_combo.currentFontChanged.connect(self.update_font)
        self.format_toolbar.size_spin.valueChanged.connect(self.update_font_size)
        self.format_toolbar.bold_btn.toggled.connect(self.update_bold)
        self.format_toolbar.italic_btn.toggled.connect(self.update_italic)
        self.format_toolbar.color_btn.clicked.connect(self.choose_color)

    def activate(self):
        super().activate()
        # Add toolbar to info bar
        self.app.info_bar.insertWidget(0, self.format_toolbar)
        self.format_toolbar.show()

    def deactivate(self):
        super().deactivate()
        # Remove toolbar from info bar
        self.app.info_bar.removeWidget(self.format_toolbar)
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
            return

        self.text_item = SimpleTextItem()
        self.text_item.setPos(pos)
        self.app.scene.addItem(self.text_item)
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
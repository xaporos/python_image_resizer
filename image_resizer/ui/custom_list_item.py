import os

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                           QInputDialog, QLineEdit, QListWidget)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from image_resizer.ui.styles import RENAME_BUTTON_STYLE, IMAGE_NAME_LABEL_STYLE, DELETE_BUTTON_STYLE, RENAME_DIALOG_STYLE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DELETE_ICON_PATH = os.path.join(BASE_DIR, "assets", "delete.png")
RENAME_ICON_PATH = os.path.join(BASE_DIR, "assets", "rename.png")
class ImageListItemWidget(QWidget):
    renamed = pyqtSignal(object, str)  # item, new_name
    deleted = pyqtSignal(str)  # image_name
    
    def __init__(self, image_name, parent=None):
        super().__init__(parent)
        self.image_name = image_name
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Image name label
        self.name_label = QLabel(self.image_name)
        self.name_label.setMinimumWidth(150)
        self.name_label.setStyleSheet(IMAGE_NAME_LABEL_STYLE)
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
        # Rename button
        self.rename_btn = QPushButton()
        self.rename_btn.setIcon(QIcon(RENAME_ICON_PATH))
        self.rename_btn.setFixedSize(28, 28)
        self.rename_btn.setToolTip("Rename")
        self.rename_btn.clicked.connect(self.rename_clicked)
        self.rename_btn.setStyleSheet(RENAME_BUTTON_STYLE)
        layout.addWidget(self.rename_btn)
        
        # Delete button
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon(DELETE_ICON_PATH))
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.setToolTip("Delete")
        self.delete_btn.clicked.connect(self.delete_clicked)
        self.delete_btn.setStyleSheet(DELETE_BUTTON_STYLE)
        layout.addWidget(self.delete_btn)
        
        # Initially hide rename button, show delete button
        self.rename_btn.setVisible(False)
        self.delete_btn.setVisible(True)
        
        # Set fixed height for the widget
        self.setFixedHeight(44)
        
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
            QWidget:hover {
                background: #F5F5F5;
            }
        """)
        
        self.setLayout(layout)
        
    def set_selected(self, selected):
        """Show/hide rename button based on selection state"""
        self.rename_btn.setVisible(selected)
        
    def rename_clicked(self):
        # Create custom input dialog
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Rename Image")
        dialog.setLabelText("Enter new name:")
        dialog.setTextValue(self.image_name)
        
        # Style the dialog to match app theme
        dialog.setStyleSheet(RENAME_DIALOG_STYLE)
        
        ok = dialog.exec_()
        new_name = dialog.textValue()
        
        if ok and new_name and new_name != self.image_name:
            # Find the parent QListWidget
            parent_list = self.parent()
            while parent_list and not isinstance(parent_list, QListWidget):
                parent_list = parent_list.parent()
                
            if parent_list:
                for i in range(parent_list.count()):
                    item = parent_list.item(i)
                    if parent_list.itemWidget(item) == self:
                        self.renamed.emit(item, new_name)
                        # Update the internal image name
                        self.image_name = new_name
                        self.name_label.setText(new_name)
                        break
            
    def delete_clicked(self):
        self.deleted.emit(self.image_name)
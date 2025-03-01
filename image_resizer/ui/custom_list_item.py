from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                           QInputDialog, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

class ImageListItemWidget(QWidget):
    renamed = pyqtSignal(str, str)  # old_name, new_name
    deleted = pyqtSignal(str)  # image_name
    
    def __init__(self, image_name, parent=None):
        super().__init__(parent)
        self.image_name = image_name
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Image name label
        self.name_label = QLabel(self.image_name)
        self.name_label.setStyleSheet("""
            QLabel { 
                color: #333333;
                padding: 2px;
            }
        """)
        layout.addWidget(self.name_label)
        
        # Add stretch to push buttons to the right
        layout.addStretch()
        
        # Rename button with pencil symbol ✎
        self.rename_btn = QPushButton("✎")
        self.rename_btn.setFixedSize(24, 24)
        self.rename_btn.setToolTip("Rename")
        self.rename_btn.clicked.connect(self.rename_clicked)
        self.rename_btn.setVisible(False)  # Hide by default
        self.rename_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 2px;
                color: #666666;
                font-size: 16px;
                font-family: Arial;
            }
            QPushButton:hover {
                background: #4CAF50;
                border-radius: 4px;
                color: white;
            }
        """)
        
        # Delete button with trash symbol 🗑
        self.delete_btn = QPushButton("🗑")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setToolTip("Delete")
        self.delete_btn.clicked.connect(self.delete_clicked)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 2px;
                color: #ff4444;
                font-size: 16px;
                font-family: Arial;
            }
            QPushButton:hover {
                background: #F44336;
                border-radius: 4px;
                color: white;
            }
        """)
        
        # Add buttons to layout
        layout.addWidget(self.rename_btn)
        layout.addWidget(self.delete_btn)
        
        # Set widget style
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
        new_name, ok = QInputDialog.getText(
            self, 'Rename Image', 'Enter new name:',
            QLineEdit.Normal, self.image_name
        )
        if ok and new_name and new_name != self.image_name:
            self.renamed.emit(self.image_name, new_name)
            
    def delete_clicked(self):
        self.deleted.emit(self.image_name)
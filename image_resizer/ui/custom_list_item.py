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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Image name label
        self.name_label = QLabel(self.image_name)
        self.name_label.setMinimumWidth(150)
        self.name_label.setStyleSheet("""
            QLabel { 
                color: #333333;
                font-size: 13px;
                padding: 2px;
            }
        """)
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
        # Rename button
        self.rename_btn = QPushButton("✎")
        self.rename_btn.setFixedSize(28, 28)
        self.rename_btn.setToolTip("Rename")
        self.rename_btn.clicked.connect(self.rename_clicked)
        self.rename_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #666666;
                font-size: 16px;
                padding: 4px;
            }
            QPushButton:hover {
                background: #e8e8e8;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.rename_btn)
        
        # Delete button
        self.delete_btn = QPushButton("🗑")
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.setToolTip("Delete")
        self.delete_btn.clicked.connect(self.delete_clicked)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #666666;
                font-size: 16px;
                padding: 4px;
            }
            QPushButton:hover {
                background: #ffebee;
                color: #f44336;
                border-radius: 4px;
            }
        """)
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
        new_name, ok = QInputDialog.getText(
            self, 'Rename Image', 'Enter new name:',
            QLineEdit.Normal, self.image_name
        )
        if ok and new_name and new_name != self.image_name:
            self.renamed.emit(self.image_name, new_name)
            
    def delete_clicked(self):
        self.deleted.emit(self.image_name)
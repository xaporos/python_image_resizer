from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSpinBox, QCheckBox, QPushButton)
from PyQt5.QtCore import Qt

class ResizeDialog(QDialog):
    def __init__(self, current_size, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resize Image")
        self.setModal(True)
        
        # Store current dimensions
        self.current_width, self.current_height = current_size
        self.aspect_ratio = self.current_width / self.current_height
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Dimensions inputs
        dims_layout = QHBoxLayout()
        
        # Width input
        width_layout = QVBoxLayout()
        width_label = QLabel("Width:")
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(self.current_width)
        self.width_spin.valueChanged.connect(self.width_changed)
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_spin)
        dims_layout.addLayout(width_layout)
        
        # Height input
        height_layout = QVBoxLayout()
        height_label = QLabel("Height:")
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(self.current_height)
        self.height_spin.valueChanged.connect(self.height_changed)
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_spin)
        dims_layout.addLayout(height_layout)
        
        layout.addLayout(dims_layout)
        
        # Keep aspect ratio checkbox
        self.aspect_check = QCheckBox("Keep aspect ratio")
        self.aspect_check.setChecked(True)
        layout.addWidget(self.aspect_check)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

    def width_changed(self, new_width):
        if self.aspect_check.isChecked():
            # Update height maintaining aspect ratio
            self.height_spin.blockSignals(True)
            self.height_spin.setValue(int(new_width / self.aspect_ratio))
            self.height_spin.blockSignals(False)

    def height_changed(self, new_height):
        if self.aspect_check.isChecked():
            # Update width maintaining aspect ratio
            self.width_spin.blockSignals(True)
            self.width_spin.setValue(int(new_height * self.aspect_ratio))
            self.width_spin.blockSignals(False)

    def get_values(self):
        """Return the width and height values"""
        return self.width_spin.value(), self.height_spin.value()

    def keep_aspect_ratio(self):
        """Return whether to keep aspect ratio"""
        return self.aspect_check.isChecked() 
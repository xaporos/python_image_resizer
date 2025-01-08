import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                           QMessageBox, QComboBox, QSlider, QListWidget,
                           QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
import numpy as np

class ImageResizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Resizer")
        self.setGeometry(100, 100, 1200, 800)  # Initial size
        self.setMinimumSize(800, 600)  # Minimum size
        
        # Initialize variables
        self.images = {}  # Dictionary to store image paths and their PIL Image objects
        self.current_image = None
        self.aspect_ratio = 1.0
        
        # Size presets
        self.size_presets = {
            "Custom": 0,
            "Small (800px)": 800,
            "Medium (1200px)": 1200,
            "Large (1600px)": 1600
        }
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        toolbar = QHBoxLayout()
        main_layout.addLayout(toolbar)
        
        # Add select button
        self.select_btn = QPushButton("Select Images")
        self.select_btn.clicked.connect(self.select_files)
        toolbar.addWidget(self.select_btn)
        
        # Add size preset dropdown
        toolbar.addWidget(QLabel("Size:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(self.size_presets.keys())
        self.size_combo.currentTextChanged.connect(self.preset_selected)
        toolbar.addWidget(self.size_combo)
        
        # Add quality slider and value label
        toolbar.addWidget(QLabel("Quality:"))
        quality_layout = QHBoxLayout()
        toolbar.addLayout(quality_layout)
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(85)
        self.quality_slider.valueChanged.connect(self.quality_changed)
        quality_layout.addWidget(self.quality_slider)
        
        self.quality_label = QLabel("85%")
        self.quality_label.setMinimumWidth(40)  # Ensure enough space for the text
        quality_layout.addWidget(self.quality_label)
        
        # Add resize button
        self.resize_btn = QPushButton("Resize Selected")
        self.resize_btn.clicked.connect(self.resize_image)
        self.resize_btn.setEnabled(False)
        toolbar.addWidget(self.resize_btn)
        
        # Add resize all button
        self.resize_all_btn = QPushButton("Resize All")
        self.resize_all_btn.clicked.connect(self.resize_all_images)
        self.resize_all_btn.setEnabled(False)
        toolbar.addWidget(self.resize_all_btn)
        
        # Create splitter for list and preview
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create list widget for images
        self.image_list = QListWidget()
        self.image_list.currentItemChanged.connect(self.image_selected)
        splitter.addWidget(self.image_list)
        
        # Create right panel for preview and info
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        splitter.addWidget(right_panel)
        
        # Add preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.preview_label)
        
        # Add info label
        self.info_label = QLabel("No image selected")
        self.info_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        right_layout.addWidget(self.info_label)
        
        # Set splitter sizes
        splitter.setSizes([300, 900])  # Left panel 300px, right panel 900px

    def select_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.tiff)"
        )
        
        if file_paths:
            for file_path in file_paths:
                try:
                    image = Image.open(file_path)
                    self.images[file_path] = image
                    self.image_list.addItem(os.path.basename(file_path))
                except Exception as e:
                    QMessageBox.warning(self, "Warning", 
                                      f"Could not load {os.path.basename(file_path)}: {str(e)}")
            
            self.resize_btn.setEnabled(True)
            self.resize_all_btn.setEnabled(True)
            
            # Select first image
            if self.image_list.count() > 0:
                self.image_list.setCurrentRow(0)

    def image_selected(self, current, previous):
        if current:
            file_path = self.get_file_path_from_item(current)
            if file_path in self.images:
                self.current_image = self.images[file_path]
                self.update_preview_and_info(file_path)

    def get_file_path_from_item(self, item):
        for path in self.images.keys():
            if os.path.basename(path) == item.text():
                return path
        return None

    def update_preview_and_info(self, file_path):
        if self.current_image:
            # Create preview
            preview = self.current_image.copy()
            preview.thumbnail((800, 800))  # Resize for preview
            
            # Convert PIL image to QPixmap
            preview_array = np.array(preview)
            height, width, channels = preview_array.shape
            bytes_per_line = channels * width
            
            # Convert RGB to BGR for Qt
            preview_array = preview_array[:, :, ::-1].copy()
            
            qimage = QImage(preview_array.data, width, height, 
                          bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            
            self.preview_label.setPixmap(pixmap)
            
            # Update info
            width, height = self.current_image.size
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            
            info = f"""File: {os.path.basename(file_path)}
Original size: {width} × {height} pixels
New size: {width} × {height} pixels
File size: {file_size:.2f} MB"""
            
            self.info_label.setText(info)
            self.aspect_ratio = width / height

    def preset_selected(self, selection):
        if self.current_image and selection != "Custom":
            width = self.size_presets[selection]
            height = int(width / self.aspect_ratio)
            
            current_text = self.info_label.text().split('\n')
            if len(current_text) >= 3:
                current_text[2] = f"New size: {width} × {height} pixels"
                self.info_label.setText('\n'.join(current_text))

    def resize_image(self, file_path=None):
        if not file_path:
            current_item = self.image_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Warning", "Please select an image first!")
                return
            file_path = self.get_file_path_from_item(current_item)
        
        if file_path and file_path in self.images:
            try:
                image = self.images[file_path]
                
                # Get dimensions
                if self.size_combo.currentText() != "Custom":
                    width = self.size_presets[self.size_combo.currentText()]
                    height = int(width / self.aspect_ratio)
                else:
                    width, height = image.size
                
                # Resize image
                resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
                
                # Get original file extension
                original_ext = os.path.splitext(file_path)[1]
                
                # Save dialog
                save_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Resized Image",
                    f"resized_{os.path.basename(file_path)}",
                    f"Image Files (*{original_ext})"
                )
                
                if save_path:
                    # Save with quality for JPEG
                    if save_path.lower().endswith(('.jpg', '.jpeg')):
                        resized_image.save(save_path, quality=self.quality_slider.value())
                    else:
                        resized_image.save(save_path)
                    
                    return True
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
                return False
        
        return False

    def resize_all_images(self):
        if not self.images:
            QMessageBox.warning(self, "Warning", "No images loaded!")
            return
        
        # Ask for output directory
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return
        
        success_count = 0
        for file_path in self.images.keys():
            try:
                image = self.images[file_path]
                
                # Get dimensions
                if self.size_combo.currentText() != "Custom":
                    width = self.size_presets[self.size_combo.currentText()]
                    height = int(width / image.size[0] / image.size[1])
                else:
                    width, height = image.size
                
                # Resize image
                resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
                
                # Save file
                output_path = os.path.join(output_dir, f"resized_{os.path.basename(file_path)}")
                if output_path.lower().endswith(('.jpg', '.jpeg')):
                    resized_image.save(output_path, quality=self.quality_slider.value())
                else:
                    resized_image.save(output_path)
                
                success_count += 1
                
            except Exception as e:
                QMessageBox.warning(self, "Warning", 
                                  f"Failed to resize {os.path.basename(file_path)}: {str(e)}")
        
        QMessageBox.information(self, "Success", 
                              f"Successfully resized {success_count} of {len(self.images)} images")

    def quality_changed(self, value):
        self.quality_label.setText(f"{value}%")

def main():
    app = QApplication(sys.argv)
    window = ImageResizerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
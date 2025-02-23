from PIL import Image
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class ImageResizer:
    def __init__(self):
        self.size_presets = {
            "Small": 800,
            "Medium": 1200,
            "Large": 1600
        }

    def calculate_new_dimensions(self, current_width, current_height, target_width):
        """Calculate new dimensions maintaining aspect ratio"""
        if current_width > target_width:
            width = target_width
            height = int(target_width / current_width * current_height)
            return width, height
        return current_width, current_height

    def resize_single(self, image, size_preset, quality=80):
        """Resize a single image based on preset"""
        if not image:
            return None

        current_width, current_height = image.size
        target_width = self.size_presets.get(size_preset, current_width)
        
        width, height = self.calculate_new_dimensions(current_width, current_height, target_width)
        
        # Only resize if dimensions changed
        if (width, height) != (current_width, current_height):
            return image.resize((width, height), Image.Resampling.LANCZOS)
        return image.copy()

    def save_image(self, image, save_path, quality=80):
        """Save image with appropriate settings based on format"""
        try:
            if save_path.lower().endswith(('.jpg', '.jpeg')):
                image.save(save_path, quality=quality, optimize=True)
            elif save_path.lower().endswith('.png'):
                image.save(save_path, optimize=True, compress_level=9)
            else:
                image.save(save_path)
            return True
        except Exception as e:
            print(f"Error saving image: {str(e)}")
            return False

    def get_save_path(self, parent, original_path, prefix="resized"):
        """Get save path from user"""
        original_ext = original_path.lower().split('.')[-1]
        save_path, _ = QFileDialog.getSaveFileName(
            parent,
            "Save Resized Image",
            f"{prefix}_{original_path.split('/')[-1]}",
            f"Image Files (*.{original_ext})"
        )
        return save_path

    def get_output_directory(self, parent):
        """Get output directory for batch processing"""
        return QFileDialog.getExistingDirectory(parent, "Select Output Directory")

    def calculate_statistics(self, original_size, new_size):
        """Calculate size reduction statistics"""
        original_mb = original_size / (1024 * 1024)
        new_mb = new_size / (1024 * 1024)
        reduction = ((original_size - new_size) / original_size * 100)
        return original_mb, new_mb, reduction 
from PIL import Image
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class ImageResizer:
    def __init__(self):
        pass

    def resize_single(self, image, size_preset):
        """Resize a single image based on preset"""
        if not image:
            return None

        # Get original dimensions
        width, height = image.size
        print(f"Original size: {width}x{height}")

        # Get resize factor based on preset
        if size_preset == "Small":
            resize_factor = 4  # Resize 4 times smaller
        elif size_preset == "Medium":
            resize_factor = 3  # Resize 3 times smaller
        elif size_preset == "Large":
            resize_factor = 2  # Resize 2 times smaller
        else:
            print(f"Unknown size preset: {size_preset}")
            return image.copy()

        # Calculate new dimensions
        new_width = int(width / resize_factor)
        new_height = int(height / resize_factor)
        print(f"Size preset: {size_preset}, Factor: {resize_factor}")
        print(f"New size: {new_width}x{new_height}")

        return image.resize((new_width, new_height), Image.LANCZOS)

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
from PIL import Image
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class ImageResizer:
    def __init__(self):
        pass

    def resize_single(self, image, size_preset):
        """Resize a single image based on preset"""
        if not image:
            return None

        try:
            # Ensure we're working with a copy
            image = image.copy()
            
            # Get original dimensions
            width, height = image.size

            # Extract preset name without percentage
            preset_name = size_preset.split(" ")[0]

            # Calculate new dimensions based on preset
            if preset_name == "Small":
                scale = 0.25
            elif preset_name == "Medium":
                scale = 0.33
            elif preset_name == "Large":
                scale = 0.50
            elif preset_name == "Original":
                return image
            else:
                print(f"Unknown preset: {size_preset}")
                return image

            # Calculate new dimensions
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Ensure minimum dimensions
            new_width = max(new_width, 1)
            new_height = max(new_height, 1)
            
            print(f"Resizing to: {new_width}x{new_height}")
            
            # Perform the resize with high-quality resampling
            resized = image.resize((new_width, new_height), Image.LANCZOS)
            print(f"Final dimensions: {resized.size}")
            
            return resized

        except Exception as e:
            print(f"Error in resize_single: {str(e)}")
            return image

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
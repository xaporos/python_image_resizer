import os
import sys
from PIL import Image
from PyQt5.QtWidgets import QMessageBox

# Get the path to the original image_handler.py
project_root = os.path.dirname(os.path.abspath(__file__))
original_path = os.path.join(project_root, 'image_resizer', 'utils', 'image_handler.py')

# Create a backup if it doesn't exist
backup_path = original_path + '.backup'
if not os.path.exists(backup_path):
    try:
        with open(original_path, 'r') as f:
            original_content = f.read()
        
        with open(backup_path, 'w') as f:
            f.write(original_content)
        
        print(f"Backup created at {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {e}")

# Now create a modified version of the file
try:
    # Read the backup file
    with open(backup_path, 'r') as f:
        content = f.read()
    
    # Add debug code to update_info_label method
    if 'def update_info_label' in content:
        # Find the method
        start = content.find('def update_info_label')
        # Find the end of the method (next def or end of file)
        next_def = content.find('def ', start + 1)
        if next_def == -1:
            next_def = len(content)
        
        # Extract the method
        method = content[start:next_def]
        
        # Add debug code
        debug_code = """
    def update_info_label(self):
        \"\"\"Update the info labels with current image information\"\"\"
        current_item = self.parent.image_list.currentItem()
        if current_item:
            file_path = self.get_file_path_from_item(current_item)
            if file_path:
                # Get current dimensions
                current_width, current_height = self.current_dimensions.get(file_path, (0, 0))
                
                # Get file size directly from disk for original images
                if file_path not in self.edited_images:
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                else:
                    file_size = self.edited_file_sizes.get(file_path, 0)
                
                # Show a message box with the info
                QMessageBox.information(self.parent, "Debug Info", 
                    f"File: {file_path}\\n"
                    f"Dimensions: {current_width}x{current_height}\\n"
                    f"File size: {file_size:.2f}MB\\n"
                    f"Is edited: {file_path in self.edited_images}")
                
                # Update labels
                self.parent.size_label.setText(f"Size: {current_width} × {current_height}px")
                self.parent.file_size_label.setText(f"File size: {file_size:.2f}MB")
        """
        
        # Replace the method
        content = content.replace(method, debug_code)
    
    # Write the modified file
    with open(original_path, 'w') as f:
        f.write(content)
    
    print(f"Modified {original_path}")
    
except Exception as e:
    print(f"Error modifying file: {e}")

print("Please restart the application to see the changes.") 
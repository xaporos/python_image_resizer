# ResizeX - Image Resizer and Editor

ResizeX is a powerful desktop application for resizing, editing, and annotating images with an intuitive interface.

## Installation

1. Make sure you have Python 3.7+ installed
2. Clone this repository or download the source code
3. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python -m image_resizer
   ```

## Features

### Image Resizing and Format Conversion
- Resize single images or batch process multiple files
- Maintain aspect ratio automatically
- Adjust output quality for optimized file size
- Support for common formats: JPG, PNG, GIF, BMP, TIFF
- Apple HEIC/HEIF format support

### Image Editing Tools
- **Draw**: Free-hand drawing with adjustable line width
- **Text**: Add text annotations with customizable font size and color
- **Shapes**: Add rectangles, circles, lines, and arrows
- **Highlighter**: Highlight areas with semi-transparent marker
- **Eraser**: Remove parts of your annotations
- **Crop**: Crop images to desired dimensions

### Color Controls
- Color palette with preset colors
- Color picker for custom colors
- Transparency options for highlighting

### User Interface
- Intuitive toolbar design
- Image list for quick selection
- Real-time preview of edits
- Undo/redo functionality
- Zoom controls for detailed editing
- Image property information (dimensions and file size)

### File Management
- Open multiple files at once
- Save individual images or batch save all
- Rename images within the application
- Delete images from the workspace

## Size Presets

- Small: 800px width
- Medium: 1200px width
- Large: 1600px width
- Custom: Maintains original dimensions

## Keyboard Shortcuts

- **Ctrl+Z**: Undo
- **Ctrl+Y** or **Ctrl+Shift+Z**: Redo
- **Ctrl+S**: Save current image
- **Ctrl+O**: Open images

## Dependencies

- PyQt5: GUI framework
- Pillow: Image processing
- NumPy: Array operations
- Pillow-HEIF: HEIC/HEIF format support

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyQt5 for the GUI framework
- Pillow for image processing
- NumPy for array operations

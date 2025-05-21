import sys
from PyQt5.QtWidgets import QApplication
from image_resizer.ui.main_window import ImageResizerApp

def main():
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    window = ImageResizerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
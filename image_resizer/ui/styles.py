from image_resizer.ui.icons import COMBO_ARROW_PATH, UP_ARROW_PATH
combo_arrow_path = COMBO_ARROW_PATH.replace("\\", "/")
up_arrow_path = UP_ARROW_PATH.replace("\\", "/")

MAIN_STYLE = """
    QMainWindow, QWidget {
        background-color: #f5f5f5;
        color: #333333;
    }
    QMenuBar {
        background-color: #f5f5f5;
        color: #333333;
    }
    QMenuBar::item:selected {
        background-color: #f5f5f5;
        color: white;
    }
    QMenu {
        background-color: #f3f5f8;
        color: #333333;
        border: 1px solid #dadde1;
    }
    QMenu::item:selected {
        background-color: #1877F2;
        color: white;
    }
"""

BUTTON_STYLE = """
            QPushButton {
                color: black;
                padding: 4px 10px;
                border: 1px solid #DBDCDA;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                border: 1px solid #242424;
            }
            QPushButton:disabled {
                color: #DBDCDA;
            }
        """

TOOL_BUTTON_STYLE = """
    QPushButton {
        border: none;
        background: transparent;
        font-size: 18px;
        padding: 5px;
        color: #808080;
        icon-size: 24px;
    }
    QPushButton:checked {
        border: 1px solid #242424;
        border-radius: 5px;
        color: #404040;
    }
    QPushButton:hover {
        border: 1px solid #242424;
        border-radius: 5px;
        color: #404040;
    }
"""

RESIZE_BUTTON_STYLE = """
            QPushButton {
                background-color: #1877F2;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1464D2;
            }
        """

RENAME_BUTTON_STYLE = """
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
        """

DELETE_BUTTON_STYLE = """
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
        """

COMBO_BOX_STYLE = """
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding-right: 0;
                padding-top: 4px;
                padding-bottom: 4px;
                padding-left: 34px;
                background: #f5f5f5;
                color: #333;
                font-weight: 500;
                
            }
            QComboBox:hover {
                border-color: #242424;
            }
            QComboBox:focus {
                border-color: #242424;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
                color: white;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ddd;
                margin-top: 3px;
                padding: 5px;
                min-width: 108px;  /* Make dropdown wider */
                outline: 0px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                min-height: 24px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f0f7ff;
                color: #1877F2;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #1877F2;
                color: white;
            }
        """

DROPDOWN_STYLE = """
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
        """

SLIDER_STYLE = """
            QSlider {
                margin: 0;
                padding: 0;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #ddd;
                margin: 6px 0;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #242424;
                margin: 6px 0;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #242424;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #242424;
            }
        """

ZOOM_SLIDER_STYLE = """
            QSlider {
                margin: 4;
                padding: 0;
                background-color: white;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #ddd;
                margin: 6px 0;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #242424;
                margin: 6px 0;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #242424;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #242424;
            }
        """

MAIN_WINDOW_STYLE = """
            QWidget {
                background-color: white;
                border-radius: 4px;
            }
        """

IMAGE_LIST_STYLE = """
            QListWidget {
                background-color: white;
                border: 1px solid #DBDCDA;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                background: transparent;
                border-radius: 4px;
                margin: 2px 4px;
            }
            QListWidget::item:selected {
                background-color: #f5f5f5;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """

LABEL_STYLE = "background-color: white;"
TOOLBAR_LABEL_STYLE = "background-color: #f5f5f5;"
IMAGE_NAME_LABEL_STYLE = """
            QLabel { 
                color: #333333;
                font-size: 13px;
                padding: 2px;
                text-overflow: ellipsis;
                overflow: hidden;
            }
        """

RENAME_DIALOG_STYLE = """
            QInputDialog {
                background-color: white;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
                font-weight: 500;
                padding: 10px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #DBDCDA;
                border-radius: 4px;
                background-color: white;
                color: #333333;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #242424;
            }
            QPushButton {
                color: black;
                background-color: white;
                padding: 8px 16px;
                border: 1px solid #DBDCDA;
                border-radius: 4px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                border: 1px solid #242424;
            }
        """

SUCCESS_RESIZE_DIALOG_STYLE = """
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #333333;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 10px;
                }
                QPushButton {
                    color: black;
                    background-color: white;
                    padding: 8px 16px;
                    border: 1px solid #DBDCDA;
                    border-radius: 4px;
                    font-weight: 500;
                    min-width: 80px;
                }
                QPushButton:hover {
                    border: 1px solid #242424;
                }
            """

SUCCESS_SAVE_DIALOG = """
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #333333;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 10px;
                }
                QPushButton {
                    color: black;
                    background-color: white;
                    padding: 8px 16px;
                    border: 1px solid #DBDCDA;
                    border-radius: 4px;
                    font-weight: 500;
                    min-width: 80px;
                }
                QPushButton:hover {
                    border: 1px solid #242424;
                }
            """

ERROR_SAVE_DIALOG = """
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #333333;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 10px;
                }
                QPushButton {
                    color: black;
                    background-color: white;
                    padding: 8px 16px;
                    border: 1px solid #DBDCDA;
                    border-radius: 4px;
                    font-weight: 500;
                    min-width: 80px;
                }
                QPushButton:hover {
                    border: 1px solid #242424;
                }
            """

TEXT_TOOL_TOOLBAR_STYLE = """
            /* Make background white */
            QWidget#textFormatToolbar {
                background-color: #f5f5f5;
                
            }
            
            /* Style for all controls to have white backgrounds */
            QToolButton, QFontComboBox, QSpinBox {
                background-color: white;
                color: #333333;
                border: 1px solid #DBDCDA;
                border-radius: 3px;
            }
            
            /* Hover effect for all controls */
            QToolButton:hover, QFontComboBox:hover, QSpinBox:hover {
                border: 1px solid #AAAAAA;
            }
            
            /* Active/pressed state */
            QToolButton:pressed, QToolButton:checked {
                background-color: #F0F0F0;
            }
        """

FONT_COMBO_STYLE = f"""
        QFontComboBox {{ 
            border: 1px solid #DBDCDA; 
            background-color: white; 
            }}
        QComboBox::down-arrow {{
            image: url("{combo_arrow_path}");
            width: 12; 
            height: 12;
            }}
        QComboBox::drop-down {{
            border: none; 
            background: transparent; 
            width 24px;
            }}
        """

COMBO_SPINBOX_STYLE = f"""
        QSpinBox {{
            border: 1px solid #DBDCDA; 
            background-color: white; 
            }}
        QSpinBox::up-button, QSpinBox::down-button {{
            background: white;
            width: 14px;
            padding: 2px 0px 0px 0px;
            }}
        QSpinBox::up-arrow {{
            image: url("{up_arrow_path}");
            width: 12px;
            height: 12px;
            }}

        QSpinBox::down-arrow {{
            image: url("{combo_arrow_path}");
            width: 12px;
            height: 12px;
            }}
        """
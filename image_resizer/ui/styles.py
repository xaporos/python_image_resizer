MAIN_STYLE = """
    QMainWindow, QWidget {
        background-color: #ffffff;
        color: #333333;
    }
    QMenuBar {
        background-color: #ffffff;
        color: #333333;
    }
    QMenuBar::item:selected {
        background-color: #1877F2;
        color: white;
    }
    QMenu {
        background-color: #ffffff;
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
                background-color: #ccc;
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

COMBO_BOX_STYLE = """
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 10px;
                background: white;
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
                width: 20px;
            }
            QComboBox::down-arrow {
                color: #666;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 3px;
                padding: 5px;
                min-width: 150px;  /* Make dropdown wider */
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

IMAGE_LIST_STYLE = """
            QListWidget {
                background-color: white;
                border: 1px solid #242424;
                border-radius: 8px;
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

MAIN_WINDOW_STYLE = """
            QWidget {
                background-color: white;
                border: 1px solid #242424;
                border-radius: 8px;
            }
        """
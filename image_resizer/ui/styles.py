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
        background-color: #1877F2;
        border: none;
        border-radius: 4px;
        padding: 5px 15px;
        min-width: 28px;
        min-height: 28px;
        color: white;
    }
    QPushButton:hover {
        background-color: #166fe5;
    }
    QPushButton:disabled {
        background-color: #dadde1;
        color: #606770;
    }
"""

TOOL_BUTTON_STYLE = """
    QPushButton {
        border: none;
        background: transparent;
        font-size: 18px;
        padding: 5px;
        color: #808080;
    }
    QPushButton:checked {
        color: #1877F2;
    }
    QPushButton:hover {
        color: #404040;
    }
"""

COMBO_BOX_STYLE = """
    QComboBox {
        background-color: white;
        border: 1px solid #dadde1;
        border-radius: 4px;
        padding: 5px;
        min-width: 100px;
        color: #333333;
    }
    QComboBox:hover {
        border-color: #1877F2;
    }
""" 
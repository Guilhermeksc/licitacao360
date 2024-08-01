def get_menu_button_style():
    return """
        QPushButton {
            background-color: transparent;
            color: white;
            font-weight: bold;
            font-size: 16px;
            text-align: left;
            border: 1px solid black; 
            border-radius: 0px;
        }
        QPushButton:hover {
            background-color: white;
            color: black;
        }
    """

def get_menu_button_activated_style():
    return """
        QPushButton {
            background-color: #000000;
            color: white;
            font-weight: bold;
            font-size: 16px;
            text-align: left;
            border: 1px solid black;
            border-radius: 0px;
        }
    """


def get_menu_title_style():
    return """
        font-weight: bold;
        font-size: 22px;
        color: white;
        padding: 10px;
        margin: 0;
        background-color: transparent;
        border-bottom: 2px solid white;
    """

def get_content_title_style():
    return """
        QLabel {
            font-weight: bold;
            font-size: 22px;
            color: white;
            padding: 10px;
            margin: 0;
            background-color: rgba(0, 0, 0, 80);
            border-bottom: 1px solid white;
        }
    """

def get_transparent_title_style():
    return """
        QLabel {
            font-weight: bold;
            font-size: 22px;
            color: white;
            margin: 0;
            background-color: transparent;
            border: none;
        }
    """

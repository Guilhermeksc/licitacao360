def get_menu_button_style():
    return """
        QPushButton {
            background-color: transparent;
            font-weight: bold;
            font-size: 16px;
            text-align: left;
            border: 1px solid transparent;
            border-left: 2px solid transparent; 
            border-radius: 0px;
            padding: 10px;
        }
        QPushButton:hover {
            background-color: #3F4042;
            border-left: 2px solid #3F4042;
            color: white;
            border-radius: 0px;
        }
    """

def get_menu_button_activated_style():
    return """
        QPushButton {
            background-color: #202124;
            color: white;
            font-weight: bold;
            font-size: 16px;
            text-align: left;
            border: 1px solid #202124;
            border-left: 2px solid #8E4B79;
            border-radius: 0px;
            padding: 10px;
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

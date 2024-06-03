from PyQt6.QtGui import QPixmap, QIcon, QPainter
from PyQt6.QtCore import Qt, QRect

def get_menu_button_style():
    return """
        QPushButton {
            background-color: rgba(0, 0, 0, 99);
            color: white;
            font-weight: bold;
            font-size: 16px;
            letter-spacing: 2px;
            text-align: left;
            padding: 5px;
            margin: 0;  
            border: none; 
            border-bottom: 1px solid #ffffff;
        }
        QPushButton:hover {
            background-color: #FFFFFF;
            color: black;
        }    
    """

def get_menu_button_activated_style():
    return """
        QPushButton {
            background-color: #fcc200;
            color: rgb(0, 40, 40);
            font-weight: bold;
            font-size: 16px;
            letter-spacing: 2px;
            text-align: left;
            padding: 5px;
            margin: 0;  

        }    
    """

def get_menu_title_style():
    return """
        font-weight: bold;
        font-size: 22px;
        color: white;
        padding: 10px;
        margin: 0;
        background-color: rgba(0, 0, 0, 0);
        border-bottom: 2px solid #ffffff;
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
            border-bottom: 1px solid #ffffff;
        }
    """
def get_transparent_title_style():
    return """
        QLabel {
            font-weight: bold;
            font-size: 22px;
            color: white;
            margin: 0;
            color: rgb(255, 255, 255);
            background-color: rgba(0, 0, 0, 0);
            border: none;  
        }
    """

def get_updated_background(window_size, image_path):
    original_pixmap = QPixmap(str(image_path))
    scaled_pixmap = original_pixmap.scaled(window_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)

    final_pixmap = QPixmap(window_size)
    final_pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(final_pixmap)
    x_offset = final_pixmap.width() - scaled_pixmap.width()
    y_offset = (final_pixmap.height() - scaled_pixmap.height()) // 2
    source_rect = QRect(0, 0, scaled_pixmap.width(), scaled_pixmap.height())
    target_rect = QRect(x_offset, y_offset, scaled_pixmap.width(), scaled_pixmap.height())
    painter.drawPixmap(target_rect, scaled_pixmap, source_rect)
    painter.end()

    return final_pixmap


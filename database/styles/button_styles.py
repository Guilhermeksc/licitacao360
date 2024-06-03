from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import QSize
from diretorios import ICONS_DIR

def apply_button_style(button, isTransparent):
    if isTransparent:
        estilo_botao = """
            QToolButton {
                font-size: 16px;
                padding: 10px;
                background-color: transparent;
                color: white;
                border: none;
                text-decoration: none;
            }
            QToolButton:hover {
                color: rgb(0, 255, 255);
                background-color: transparent;
                border: none;
                text-decoration: underline;
            }
        """
    else:
        estilo_botao = """
            QToolButton {
                font-size: 16px;
                padding: 10px;
                background-color: rgba(0, 0, 0, 0.2);
                font-weight: bold;
                color: white;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                text-decoration: none;
            }
            QToolButton:hover {
                color: rgb(0, 255, 255);
                background-color: rgba(0, 0, 0, 0.8);
                border: 1px solid rgba(0, 255, 255, 0.8);
                text-decoration: underline;
            }
        """
    button.setStyleSheet(estilo_botao)

class CustomToolButton(QToolButton):
    def __init__(self, icon_normal, icon_hover, iconSize=QSize(60, 60), buttonSize=QSize(140, 160), isTransparent=False, *args, **kwargs):
        super(CustomToolButton, self).__init__(*args, **kwargs)
        self.icon_normal = QIcon(str(ICONS_DIR / icon_normal))
        self.icon_hover = QIcon(str(ICONS_DIR / icon_hover))
        self.setIcon(self.icon_normal)
        self.setIconSize(iconSize)
        self.setFixedSize(buttonSize)
        if isTransparent:
            self.setStyleSheet("background: transparent; border: none;")  # Estilo para botão transparente

    def enterEvent(self, event):
        self.setIcon(self.icon_hover)
        super(CustomToolButton, self).enterEvent(event)

    def leaveEvent(self, event):
        self.setIcon(self.icon_normal)
        super(CustomToolButton, self).leaveEvent(event)
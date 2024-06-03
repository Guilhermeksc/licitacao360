from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtCore import QSize
import pandas as pd
from pathlib import Path

def create_button(text, icon, callback, tooltip_text, icon_size=QSize(40, 40), parent=None):
    btn = QPushButton(text, parent)
    if icon:
        btn.setIcon(QIcon(icon))
        btn.setIconSize(icon_size)
    btn.clicked.connect(callback)
    btn.setToolTip(tooltip_text)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #f9f9f9;
            color: #333; 
            font-size: 16px; 
            min-height: 35px;
            padding: 5px;
            border-radius: 4px;
            border: 1px solid #ccc;
        }
        QPushButton:hover {
            background-color: #d3d3d3; 
            border: 1px solid #ccc;
        }
        QPushButton:pressed {
            background-color: #b0c4de;
            color: white; 
        }
        QPushButton:focus {
            border: 1px solid #b0c4de; 
        }
    """)
    return btn

def load_icons(icons_dir):
    icons = {}
    for icon_file in Path(icons_dir).glob("*.png"):  # Procura por arquivos .png no diretório
        icon_name = icon_file.stem  # Obtém o nome do arquivo sem a extensão
        icons[icon_name] = QIcon(str(icon_file))  # Cria o QIcon e adiciona ao dicionário
    return icons

def apply_standard_style(widget):
    widget.setStyleSheet("""
        QWidget {
            background-color: #f0f0f0;
            color: #333;
        }
    """)

def limpar_quebras_de_linha(dataframe):
    for coluna in dataframe.columns:
        if dataframe[coluna].dtype == object:  # Aplica a limpeza apenas em colunas de texto
            dataframe[coluna] = dataframe[coluna].apply(lambda x: x.replace('\n', ' ') if isinstance(x, str) else x)

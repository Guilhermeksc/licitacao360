# treeview_utils.py

from PyQt6.QtWidgets import QTreeView
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtCore import Qt
import pandas as pd
import os
import subprocess
import sys

def load_images(icons_dir, image_file_names):
    images = {}
    for image_file_name in image_file_names:
        image_path = icons_dir / image_file_name
        if not image_path.is_file():
            print(f"Image file not found: {image_path}")
            continue
        icon = QIcon(str(image_path))
        images[image_file_name.split('.')[0]] = icon
    return images

def create_button(text, icon, callback, tooltip_text, parent):
    from PyQt6.QtWidgets import QPushButton
    btn = QPushButton(text, parent)
    if icon:
        btn.setIcon(icon)
    if callback:
        btn.clicked.connect(callback)
    if tooltip_text:
        btn.setToolTip(tooltip_text)

    # Aplica folhas de estilo para personalizar a aparência do botão
    btn.setStyleSheet("""
    QPushButton {
        background-color: black;
        color: white;
        font-size: 12pt;
        min-height: 35px;
        padding: 5px;      
    }
    QPushButton:hover {
        background-color: white;
        color: black;
    }
    QPushButton:pressed {
        background-color: #ddd;
        color: black;
    }
    """)

    return btn


def save_dataframe_to_excel(data_frame, file_path):
    try:
        data_frame.to_excel(file_path, index=False)
        print("DataFrame saved successfully.")
    except Exception as e:
        print(f"Error saving DataFrame: {e}")

def open_folder(path):
    if sys.platform == 'win32':  # Para Windows
        os.startfile(path)
    elif sys.platform == 'darwin':  # Para macOS
        subprocess.Popen(['open', path])
    else:  # Para Linux e outros sistemas Unix-like
        subprocess.Popen(['xdg-open', path])


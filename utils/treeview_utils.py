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

def create_button(text, icon, callback, tooltip_text, parent, font_size=12):
    from PyQt6.QtWidgets import QPushButton
    from PyQt6.QtGui import QFont
    btn = QPushButton(text, parent)
    if icon:
        btn.setIcon(icon)
    if callback:
        btn.clicked.connect(callback)
    if tooltip_text:
        btn.setToolTip(tooltip_text)

    # Configure button font size
    font = btn.font()
    font.setPointSize(font_size)
    btn.setFont(font)
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
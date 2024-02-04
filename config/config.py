# Arquivo config.py

from pathlib import Path
from tkinter import filedialog
import json

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
ICONS_DIR = DATABASE_DIR / "icons"
LV_FINAL_DIR = DATABASE_DIR / "Nova pasta"
IMAGE_PATH = DATABASE_DIR / "image"
IMAGE_AGUIA_PATH = IMAGE_PATH / "aguia.jpg"

# Outras configurações globais
WINDOW_TITLE = "QDarkStyle Menu Lateral"
WINDOW_SIZE = (1600, 750)

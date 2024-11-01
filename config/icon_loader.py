# config/icon_loader.py
from pathlib import Path
from PyQt6.QtGui import QIcon
from config.paths import ICONS_DIR

# Cache para ícones
_icon_cache = {}

def load_icon(icon_name):
    """Carrega e armazena em cache os ícones como QIcon."""
    if icon_name not in _icon_cache:
        icon_path = ICONS_DIR / icon_name
        _icon_cache[icon_name] = QIcon(str(icon_path))
    return _icon_cache[icon_name]

# Funções específicas para carregar ícones usados frequentemente
def load_icons():
    return {
        "config": load_icon("setting_1.png"),
        "config_hover": load_icon("setting_2.png"),
        "confirm": load_icon("brasil.png"),
        "setting_1": load_icon("setting_1.png"),
        "setting_2": load_icon("setting_2.png")
    }

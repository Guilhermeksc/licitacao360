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
        "setting_2": load_icon("setting_2.png"),
        "business": load_icon("business.png"),
        "aproved": load_icon("aproved.png"),
        "session": load_icon("session.png"),
        "deal": load_icon("deal.png"),
        "emenda_parlamentar": load_icon("emenda_parlamentar.png"),
        "verify_menu": load_icon("verify_menu.png"),
        "archive": load_icon("archive.png"),
        "plus": load_icon("plus.png"),
        "import_de": load_icon("import_de.png"),
        "save_to_drive": load_icon("save_to_drive.png"),
        "loading": load_icon("loading.png"),
        "delete": load_icon("delete.png"),
        "performance": load_icon("performance.png"),
        "excel": load_icon("excel.png"),
        "calendar": load_icon("calendar.png"),
        "report": load_icon("report.png"),
        "management": load_icon("management.png"),
        "edit": load_icon("management.png"),
        "image-processing": load_icon("image-processing.png"),
        "brasil_2": load_icon("brasil_2.png"),
    }

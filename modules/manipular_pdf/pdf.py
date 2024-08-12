from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt

from diretorios import ICONS_DIR

from pathlib import Path

class ManipularPDFsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(ICONS_DIR)
        self.image_cache = self._load_images()
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: transparent;")  # Define o fundo branco

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self._create_title_layout())

    def _create_title_layout(self):
        layout = QHBoxLayout()
        icon_label = QLabel()
        icon = self.image_cache.get('pdf')
        if icon:
            scaled_icon = icon.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled_icon)
        title_label = QLabel("Edição de PDFs")
        title_label.setFont(self._get_title_font(30, bold=True))
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return layout

    def _get_title_font(self, size=14, bold=False):
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def _load_images(self):
        images = {
            'pdf': QPixmap(str(self.icons_dir / "pdf.png"))
        }
        return images

class RelatoriaWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(ICONS_DIR)
        self.image_cache = self._load_images()
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: transparent;")  # Define o fundo branco

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self._create_title_layout())

    def _create_title_layout(self):
        layout = QHBoxLayout()
        icon_label = QLabel()
        icon = self.image_cache.get('relatoria')
        if icon:
            scaled_icon = icon.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled_icon)
        title_label = QLabel("Relatoria de Conformidade")
        title_label.setFont(self._get_title_font(30, bold=True))
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return layout

    def _get_title_font(self, size=14, bold=False):
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def _load_images(self):
        images = {
            'relatoria': QPixmap(str(self.icons_dir / "relatoria.png"))
        }
        return images

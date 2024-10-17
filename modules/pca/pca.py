from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import ICONS_DIR


class PCAWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(ICONS_DIR)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        # Título do módulo
        self.title_label = QLabel("Planejamento de Contratações Anual")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 30px; font-weight: bold;")

        # Adiciona os widgets ao layout
        self.layout.addWidget(self.title_label)

        self.layout.addStretch(1)

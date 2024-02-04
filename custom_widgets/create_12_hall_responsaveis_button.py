# create_pdf_button.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from styles.styless import get_transparent_title_style

class HallResponsaveis(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        label_registro_fornecedor = QLabel("Hall de Responsáveis")
        label_registro_fornecedor.setStyleSheet(get_transparent_title_style())
        self.layout.addWidget(label_registro_fornecedor)

    def get_title(self):
        return "Manipular PDF"

    def get_content_widget(self):
        return self

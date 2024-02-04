# create_pdf_button.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class PDFWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        # Adicione os controles específicos para 'Manipular PDF'
        self.layout.addWidget(QLabel("Ferramentas para manipulação de PDF."))

    def get_title(self):
        return "Manipular PDF"

    def get_content_widget(self):
        return self

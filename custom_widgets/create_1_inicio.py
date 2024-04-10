# create_1_inicio.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from diretorios import IMAGE_PATH

class InicioWidget(QWidget):   
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setMinimumWidth(800) 

        self.layout.addStretch(1)
        # Adicionar label "Sistema de Gestão de Licitações" acima da imagem
        label_sistema_gestao = QLabel("Sistema de Gestão de Licitações")
        label_sistema_gestao.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centralizar texto
        label_sistema_gestao.setStyleSheet("color: white; font-size: 50px; font-weight: bold;")  # Definir a cor do texto como branca, o tamanho da fonte como 40px, negrito e o fundo como transparente
        self.layout.addWidget(label_sistema_gestao)  # Adicionar a label acima da imagem
        self.layout.addStretch(2)
        # QLabel para a imagem
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(IMAGE_PATH / "tucano_fundo.png"))  # Verifique se o caminho está correto
        self.image_label.setPixmap(pixmap.scaled(600, 300, Qt.AspectRatioMode.KeepAspectRatio))
        self.layout.addWidget(self.image_label)  # Adicionar a imagem ao layout principal

        self.layout.addStretch(2)
        # Criar um novo layout para os labels de contato
        label_contato_layout = QHBoxLayout()

        # Adicionar label de contato no canto inferior direito
        label_contato = QLabel(
            "Desenvolvido por:\n" 
            "CC (IM) Guilherme Kirschner de Siqueira Campos\n"
            "Contato: (61) 98264-0077\n"
            "E-mail: siqueira.campos@marinha.mil.br"
        )
        label_contato.setAlignment(Qt.AlignmentFlag.AlignRight)  # Alinhar à direita
        label_contato.setStyleSheet("color: white; font-size: 20px;")  # Definir a cor do texto como branca, o tamanho da fonte como 20px e o fundo como transparente
        label_contato_layout.addWidget(label_contato, alignment=Qt.AlignmentFlag.AlignRight)  # Adicionar a label ao layout de labels

        # Adicionar o layout de labels de contato ao layout principal
        self.layout.addLayout(label_contato_layout)
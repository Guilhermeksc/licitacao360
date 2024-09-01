from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize

class SaveTableDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Salvar Tabela")
        self.setFixedSize(400, 250)

        layout = QVBoxLayout()

        # Layout horizontal para o título com ícone
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon = QIcon(str(self.parent().icons_dir / "excel.png"))
        icon_label.setPixmap(icon.pixmap(QSize(24, 24)))
        title_layout.addWidget(icon_label)

        # Título com texto
        title_label = QLabel("Salvar Tabela")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)

        # Adiciona o layout de título ao layout principal
        layout.addLayout(title_layout)

        # Botão para salvar tabela completa
        btn_tabela_completa = QPushButton("Tabela Completa", self)
        btn_tabela_completa.setIcon(QIcon(str(self.parent().icons_dir / "complete_table.png")))  # Ícone específico
        btn_tabela_completa.setIconSize(QSize(30, 30))
        btn_tabela_completa.clicked.connect(self.salvar_tabela_completa)
        layout.addWidget(btn_tabela_completa)

        # Botão para salvar tabela resumida
        btn_tabela_resumida = QPushButton("Tabela Resumida", self)
        btn_tabela_resumida.setIcon(QIcon(str(self.parent().icons_dir / "summary_table.png")))  # Ícone específico
        btn_tabela_resumida.setIconSize(QSize(30, 30))
        btn_tabela_resumida.clicked.connect(self.salvar_tabela_resumida)
        layout.addWidget(btn_tabela_resumida)

        # Botão para carregar tabela
        btn_carregar_tabela = QPushButton("Carregar Tabela", self)
        btn_carregar_tabela.setIcon(QIcon(str(self.parent().icons_dir / "import_de.png")))  # Ícone específico
        btn_carregar_tabela.setIconSize(QSize(30, 30))
        btn_carregar_tabela.clicked.connect(self.carregar_tabela)
        layout.addWidget(btn_carregar_tabela)

        self.setLayout(layout)

    def salvar_tabela_completa(self):
        self.parent().salvar_tabela_completa()
        self.accept()

    def salvar_tabela_resumida(self):
        self.parent().salvar_tabela_resumida()
        self.accept()

    def carregar_tabela(self):
        self.parent().carregar_tabela()
        self.accept()
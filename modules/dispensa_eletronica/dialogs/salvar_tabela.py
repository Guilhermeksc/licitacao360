from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
import sqlite3
import os
from diretorios import ICONS_DIR, CONTROLE_DADOS

class SaveTableDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Salvar Tabela")
        self.setFixedSize(240, 300)  # Aumentado para ajustar o novo botão
        icon_confirm = QIcon(str(ICONS_DIR / "excel.png"))
        self.setWindowIcon(icon_confirm)

        layout = QVBoxLayout()
        self.setStyleSheet("QWidget { font-size: 16px; }")

        # Layout horizontal para o título com ícone
        title_layout = QHBoxLayout()
        # Título com texto
        title_label = QLabel("Tabelas")
        title_label.setStyleSheet("font-size: 36px; font-weight: bold;")
        title_layout.addWidget(title_label)

        # Adiciona o layout de título ao layout principal
        layout.addLayout(title_layout)

        # Botão para salvar tabela completa
        btn_tabela_completa = QPushButton(" Tabela Completa", self)
        btn_tabela_completa.setIcon(QIcon(str(self.parent().icons_dir / "table.png")))  # Ícone específico
        btn_tabela_completa.setIconSize(QSize(40, 40))
        btn_tabela_completa.clicked.connect(self.salvar_tabela_completa)
        layout.addWidget(btn_tabela_completa)

        # Botão para salvar tabela resumida
        btn_tabela_resumida = QPushButton(" Tabela Resumida", self)
        btn_tabela_resumida.setIcon(QIcon(str(self.parent().icons_dir / "table.png")))  # Ícone específico
        btn_tabela_resumida.setIconSize(QSize(40, 40))
        btn_tabela_resumida.clicked.connect(self.salvar_tabela_resumida)
        layout.addWidget(btn_tabela_resumida)

        # Botão para carregar tabela
        btn_carregar_tabela = QPushButton("  Carregar Tabela", self)
        btn_carregar_tabela.setIcon(QIcon(str(self.parent().icons_dir / "loading_table.png")))  # Ícone específico
        btn_carregar_tabela.setIconSize(QSize(40, 40))
        btn_carregar_tabela.clicked.connect(self.carregar_tabela)
        layout.addWidget(btn_carregar_tabela)

        # Botão para excluir a tabela 'controle_dispensas'
        btn_excluir_database = QPushButton(" Excluir Database", self)
        btn_excluir_database.setIcon(QIcon(str(self.parent().icons_dir / "delete.png")))  # Ícone específico
        btn_excluir_database.setIconSize(QSize(40, 40))
        btn_excluir_database.clicked.connect(self.excluir_database)
        layout.addWidget(btn_excluir_database)

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


    def excluir_database(self):
        reply = QMessageBox.question(
            self,
            "Confirmação de Exclusão",
            "Tem certeza que deseja excluir a tabela 'controle_dispensas'?\nRecomenda-se salvar um backup antes de proceder com a exclusão. Deseja prosseguir?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Caminho do backup na área de trabalho do usuário
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            backup_path = os.path.join(desktop_path, "controle_dispensas_backup.xlsx")
            
            # Salvar backup antes de excluir
            try:
                self.parent().output_path = backup_path  # Define o caminho de saída do backup
                self.parent().salvar_tabela_completa()
                QMessageBox.information(self, "Backup Criado", f"Backup salvo na área de trabalho: {backup_path}")
                
                # Excluir a tabela após o backup
                conn = sqlite3.connect(CONTROLE_DADOS)
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS controle_dispensas")
                conn.commit()
                cursor.close()
                conn.close()
                QMessageBox.information(self, "Sucesso", "Tabela 'controle_dispensas' excluída com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir a tabela: {str(e)}")
        else:
            QMessageBox.information(self, "Cancelado", "Exclusão cancelada pelo usuário.")

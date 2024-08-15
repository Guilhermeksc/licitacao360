from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
import pandas as pd
import sqlite3
from pathlib import Path
from openpyxl import load_workbook
from diretorios import CONTROLE_DADOS

class OrganizacoesDialog(QDialog):
    controle_dados_dir_updated = pyqtSignal(Path)
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.database_path = Path(CONTROLE_DADOS)
        self.setWindowTitle("Organizações Militares")
        self.setFixedSize(600, 400)
        self.model = QSqlTableModel(self)  # Criar o modelo para interagir com o banco de dados
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Configurar OM/UASG
        om_uasg_layout = QVBoxLayout()  
        om_uasg_layout.addWidget(QLabel("Configurar OM/UASG"))

        # Adicionar botões para gerar, importar e editar tabelas
        buttons_layout = QHBoxLayout()
        self.gerar_tabela_btn = QPushButton("Gerar Tabela")
        self.importar_tabela_btn = QPushButton("Importar Tabela")
        self.editar_dados_btn = QPushButton("Editar Dados")
        self.gerar_tabela_btn.clicked.connect(self.generate_table)
        self.importar_tabela_btn.clicked.connect(self.update_om)
        self.editar_dados_btn.clicked.connect(self.edit_data)
        buttons_layout.addWidget(self.gerar_tabela_btn)
        buttons_layout.addWidget(self.importar_tabela_btn)
        buttons_layout.addWidget(self.editar_dados_btn)

        # Adicionando o layout dos botões ao layout principal
        om_uasg_layout.addLayout(buttons_layout)
        main_layout.addLayout(om_uasg_layout)

        self.setLayout(main_layout)

    def generate_table(self):
        data = {
            'uasg': ['Ex: 787010'],  
            'orgao_responsavel': ['Ex: CENTRO DE INTENDÊNCIA DA MARINHA EM BRASÍLIA'],
            'sigla_om': ['Ex: CeIMBra']
        }
        df = pd.DataFrame(data)
        df.columns = ['uasg', 'orgao_responsavel', 'sigla_om']

        # Salvando a tabela em Excel
        file_path = "tabela_uasg.xlsx"
        df.to_excel(file_path, index=False, engine='openpyxl')

        # Ajuste da largura das colunas
        wb = load_workbook(file_path)
        ws = wb.active
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 60
        ws.column_dimensions['C'].width = 15
        wb.save(file_path)

        # Abrindo o arquivo Excel após ser criado
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))

    def update_om(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione o arquivo Excel",
            "",  
            "Arquivos Excel (*.xlsx);;Todos os Arquivos (*)"
        )

        if filename:
            self.import_uasg_to_db(filename)

    def import_uasg_to_db(self, filepath):
        try:
            df = pd.read_excel(filepath, usecols=['uasg', 'orgao_responsavel', 'sigla_om'])
            with sqlite3.connect(self.database_path) as conn:
                df.to_sql('controle_om', conn, if_exists='replace', index=False)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar dados: {str(e)}")

    def edit_data(self):
        pass
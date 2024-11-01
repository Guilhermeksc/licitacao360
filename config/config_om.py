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
        self.setFixedSize(800, 600)  # Ajustei o tamanho para acomodar a QTableView
        
        # Conectar ao banco de dados
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(str(self.database_path))
        if not self.db.open():
            QMessageBox.critical(self, "Erro", f"Erro ao abrir o banco de dados: {self.db.lastError().text()}")
            return
        
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable("controle_om")
        self.model.select()
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        om_uasg_layout = QVBoxLayout()  
        om_uasg_layout.addWidget(QLabel("Configurar OM/UASG"))

        self.table_view = QTableView()
        self.table_view.setModel(self.model)

        # Definir a largura específica para cada coluna
        self.table_view.setColumnWidth(0, 100)  # Coluna uasg
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_view.setColumnWidth(2, 100)  # Coluna orgao_responsavel
        self.table_view.setColumnWidth(3, 100)  # Coluna orgao_responsavel


        om_uasg_layout.addWidget(self.table_view)

        buttons_layout = QHBoxLayout()
        self.gerar_tabela_btn = QPushButton("Gerar Tabela")
        self.importar_tabela_btn = QPushButton("Importar Tabela")
        self.editar_dados_btn = QPushButton("Editar Dados")
        self.gerar_tabela_btn.clicked.connect(self.generate_table)
        self.importar_tabela_btn.clicked.connect(self.update_om)
        buttons_layout.addWidget(self.gerar_tabela_btn)
        buttons_layout.addWidget(self.importar_tabela_btn)
        buttons_layout.addWidget(self.editar_dados_btn)

        om_uasg_layout.addLayout(buttons_layout)
        main_layout.addLayout(om_uasg_layout)

        self.setLayout(main_layout)

    def generate_table(self):
        # Verifica se o modelo já tem dados
        self.model.setTable("controle_om")
        self.model.select()

        if self.model.rowCount() > 0:
            # Se o modelo já tem dados, gerar tabela a partir dos dados existentes
            data = []
            for row in range(self.model.rowCount()):
                record = self.model.record(row)
                data.append({
                    'uasg': record.value('uasg'),
                    'orgao_responsavel': record.value('orgao_responsavel'),
                    'sigla_om': record.value('sigla_om'),
                    'indicativo_om': record.value('indicativo_om'),
                    'uf': record.value('uf'),
                    'codigoMunicipioIbge': record.value('codigoMunicipioIbge')
                })

            df = pd.DataFrame(data)
        else:
            # Se não há dados, cria a tabela com os valores predefinidos
            data = {
                'uasg': ['Ex: 787010'],  
                'orgao_responsavel': ['Ex: CENTRO DE INTENDÊNCIA DA MARINHA EM BRASÍLIA'],
                'sigla_om': ['Ex: CeIMBra'],
                'indicativo_om': ['Ex: CITBRA'],
                'uf': ['DF'],
                'codigoMunicipioIbge': ['5300108']
            }
            df = pd.DataFrame(data)

        # Salvando a tabela em Excel
        file_path = "tabela_uasg.xlsx"
        df.to_excel(file_path, index=False, engine='openpyxl')

        # Ajuste da largura das colunas
        wb = load_workbook(file_path)
        ws = wb.active
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 60
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 30
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
            # Carrega os dados do Excel
            df = pd.read_excel(filepath)
            
            # Garante que todas as colunas necessárias estejam presentes no DataFrame
            required_columns = ['uasg', 'orgao_responsavel', 'sigla_om', 'indicativo_om', 'uf', 'codigoMunicipioIbge']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None  # Adiciona a coluna com valores None se estiver faltando

            # Reordena as colunas para garantir a ordem correta no banco de dados
            df = df[required_columns]

            # Salva o DataFrame no banco de dados
            with sqlite3.connect(self.database_path) as conn:
                df.to_sql('controle_om', conn, if_exists='replace', index=False)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar dados: {str(e)}")

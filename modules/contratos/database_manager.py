## modules/contratos/database_manager.py

from modules.contratos.edit_dialog import AtualizarDadosContratos
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
import sqlite3
import pandas as pd
from functools import partial
from datetime import datetime
from pathlib import Path
import logging

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.connection = None
        logging.basicConfig(level=logging.INFO, filename='app.log', filemode='a',
                            format='%(name)s - %(levelname)s - %(message)s')
    def __enter__(self):
        self.connection = self.connect_to_database()
        return self.connection

    def connect_to_database(self):
        try:
            connection = sqlite3.connect(self.db_path)
            return connection
        except sqlite3.Error as e:
            logging.error(f"Failed to connect to database at {self.db_path}: {e}")
            raise

    def execute_query(self, query, params=None):
        with self.connect_to_database() as conn:
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
            except sqlite3.Error as e:
                logging.error(f"Error executing query: {query}, Error: {e}")
                return None

    def execute_update(self, query, params=None):
        with self.connect_to_database() as conn:
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
            except sqlite3.Error as e:
                logging.error(f"Error executing update: {query}, Error: {e}")
                return False
            return True

    def close_connection(self):
        if self.connection:
            self.connection.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def ensure_database_exists(self):
        with self.connect_to_database() as conn:
            if not self.database_exists(conn):
                self.create_database(conn)
            required_columns = {
                    "status": "TEXT", "dias": "TEXT", "pode_renovar": "TEXT", "custeio": "TEXT", "numero_contrato": "INTEGER PRIMARY KEY",
                    "tipo": "TEXT", "id_processo": "TEXT", "empresa": "TEXT", "objeto": "TEXT", "valor_global": "TEXT", "uasg": "TEXT",
                    "nup": "TEXT", "cnpj": "TEXT", "natureza_continuada": "TEXT", "om": "TEXT", "sigla_om": "TEXT", "orgao_responsavel": "TEXT",
                    "material_servico": "TEXT", "link_pncp": "TEXT", "portaria": "TEXT", "posto_gestor": "TEXT", "gestor": "TEXT",
                    "posto_gestor_substituto": "TEXT", "gestor_substituto": "TEXT", "posto_fiscal": "TEXT", "fiscal": "TEXT",
                    "posto_fiscal_substituto": "TEXT", "fiscal_substituto": "TEXT", "posto_fiscal_administrativo": "TEXT",
                    "fiscal_administrativo": "TEXT", "vigencia_inicial": "TEXT", "vigencia_final": "TEXT", "setor": "TEXT",
                    "cp": "TEXT", "msg": "TEXT", "comentarios": "TEXT", "termo_aditivo": "TEXT", "atualizacao_comprasnet": "TEXT",
                    "instancia_governanca": "TEXT", "comprasnet_contratos": "TEXT", "registro_status": "TEXT"
            }
            self.verify_and_create_columns(conn, 'controle_processos', required_columns)
            self.check_and_fix_id_sequence(conn)

    @staticmethod
    def create_table_controle_contratos(conn):
        cursor = conn.cursor()
        # Query para criar tabela 'controle_processos'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS controle_contratos (
                status TEXT,
                dias TEXT,     
                pode_renovar TEXT,                          
                custeio TEXT,
                numero_contrato TEXT PRIMARY KEY,
                tipo TEXT,  
                id_processo TEXT,
                empresa TEXT,                                          
                objeto TEXT,
                valor_global TEXT, 
                uasg TEXT,
                nup TEXT,
                cnpj TEXT,                        
                natureza_continuada TEXT,
                om TEXT,
                sigla_om TEXT,
                orgao_responsavel TEXT,
                material_servico TEXT,
                link_pncp TEXT,
                portaria TEXT,
                posto_gestor TEXT,
                gestor TEXT,
                posto_gestor_substituto TEXT,
                gestor_substituto TEXT,
                posto_fiscal TEXT,
                fiscal TEXT,
                posto_fiscal_substituto TEXT,
                fiscal_substituto TEXT,
                posto_fiscal_administrativo TEXT,
                fiscal_administrativo TEXT,
                vigencia_inicial TEXT,
                vigencia_final TEXT,
                setor TEXT,
                cp TEXT,
                msg TEXT,
                comentarios TEXT,
                termo_aditivo TEXT,
                atualizacao_comprasnet TEXT,
                instancia_governanca TEXT,
                comprasnet_contratos TEXT,
                registro_status TEXT
            )
        ''')
        conn.commit()

    @staticmethod
    def verify_and_create_columns(conn, table_name, required_columns):
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1]: row[2] for row in cursor.fetchall()}  # Storing column names and types

        # Criar uma lista das colunas na ordem correta e criar as colunas que faltam
        for column, column_type in required_columns.items():
            if column not in existing_columns:
                # Assume a default type if not specified, e.g., TEXT
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column} {column_type}")
                logging.info(f"Column {column} added to {table_name} with type {column_type}")
            else:
                # Check if the type matches, if not, you might handle or log this situation
                if existing_columns[column] != column_type:
                    logging.warning(f"Type mismatch for {column}: expected {column_type}, found {existing_columns[column]}")

        conn.commit()
        logging.info(f"All required columns are verified/added in {table_name}")

    @staticmethod
    def database_exists(conn):
        """
        Verifica se o banco de dados já existe.

        Parameters:
            conn (sqlite3.Connection): Conexão com o banco de dados.

        Returns:
            bool: True se o banco de dados existe, False caso contrário.
        """
        cursor = conn.cursor()
        # Verifica se a tabela controle_contratos existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_contratos';")
        return cursor.fetchone() is not None

    @staticmethod
    def check_and_fix_id_sequence(conn):
        cursor = conn.cursor()
        # Buscar os IDs em ordem para verificar se há lacunas
        cursor.execute("SELECT id FROM controle_contratos ORDER BY id")
        ids = [row[0] for row in cursor.fetchall()]

        # Verificar se há lacunas nos IDs
        expected_id = 1  # Iniciando do ID 1, ajuste conforme sua lógica se necessário
        for actual_id in ids:
            if actual_id != expected_id:
                print(f"Gap before ID {actual_id}, expected {expected_id}")
                # Opção 1: Renumerar os IDs para preencher as lacunas
                # Este é um exemplo e pode ser perigoso se outras tabelas referenciarem esses IDs!
                # Seria necessário atualizar todas as referências para corresponder.
                cursor.execute("UPDATE controle_contratos SET id = ? WHERE id = ?", (expected_id, actual_id))
                conn.commit()
            expected_id += 1

        # Ajustar a sequência automática para o próximo ID disponível após o último ID usado
        if ids:
            last_id = ids[-1]
            cursor.execute("PRAGMA auto_vacuum = FULL")
            cursor.execute(f"UPDATE SQLITE_SEQUENCE SET seq = {last_id} WHERE name = 'controle_contratos'")
            cursor.execute("PRAGMA auto_vacuum = NONE")
            conn.commit()

class SqlModel:
    def __init__(self, database_manager, parent=None):
        self.database_manager = database_manager
        self.parent = parent
        self.init_database()

    def init_database(self):
        if QSqlDatabase.contains("my_conn"):
            QSqlDatabase.removeDatabase("my_conn")
        self.db = QSqlDatabase.addDatabase('QSQLITE', "my_conn")
        self.db.setDatabaseName(str(self.database_manager.db_path))
        if not self.db.open():
            print("Não foi possível abrir a conexão com o banco de dados.")
        else:
            print("Conexão com o banco de dados aberta com sucesso.")
            self.adjust_table_structure()

    def adjust_table_structure(self):
        query = QSqlQuery(self.db)
        if not query.exec("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_contratos'"):
            print("Erro ao verificar existência da tabela:", query.lastError().text())
        if not query.next():
            print("Tabela 'controle_contratos' não existe. Criando tabela...")
            self.create_table_if_not_exists()
        else:
            print("Tabela 'controle_contratos' existe. Verificando estrutura da coluna...")
            self.ensure_numero_contrato_primary_key()

    def ensure_numero_contrato_primary_key(self):
        query = QSqlQuery(self.db)
        query.exec("PRAGMA table_info(controle_contratos)")
        numero_contrato_is_primary = False
        while query.next():
            if query.value(1) == 'numero_contrato' and query.value(5) == 1:
                numero_contrato_is_primary = True
                # print("Coluna 'id_processo' já é PRIMARY KEY.")
                break
        if not numero_contrato_is_primary:
            print("Atualizando 'numero_contrato' para ser PRIMARY KEY.")
            query.exec("ALTER TABLE controle_contratos ADD COLUMN numero_contrato TEXT PRIMARY KEY")
            query.exec("UPDATE controle_contratos SET new_numero_contrato = numero_contrato")
            query.exec("ALTER TABLE controle_contratos DROP COLUMN numero_contrato")
            query.exec("ALTER TABLE controle_contratos RENAME COLUMN new_numero_contrato TO numero_contrato")
            if not query.isActive():
                print("Erro ao atualizar chave primária:", query.lastError().text())

    def create_table_if_not_exists(self):
        query = QSqlQuery(self.db)
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS controle_contratos (
                status TEXT,
                dias TEXT,     
                pode_renovar TEXT,                          
                custeio TEXT,
                numero_contrato TEXT PRIMARY KEY,
                tipo TEXT,  
                id_processo TEXT,
                empresa TEXT,                                          
                objeto TEXT,
                valor_global TEXT, 
                uasg TEXT,
                nup TEXT,
                cnpj TEXT,                        
                natureza_continuada TEXT,
                om TEXT,
                sigla_om TEXT,
                orgao_responsavel TEXT,
                material_servico TEXT,
                link_pncp TEXT,
                portaria TEXT,
                posto_gestor TEXT,
                gestor TEXT,
                posto_gestor_substituto TEXT,
                gestor_substituto TEXT,
                posto_fiscal TEXT,
                fiscal TEXT,
                posto_fiscal_substituto TEXT,
                fiscal_substituto TEXT,
                posto_fiscal_administrativo TEXT,
                fiscal_administrativo TEXT,
                vigencia_inicial TEXT,
                vigencia_final TEXT,
                setor TEXT,
                cp TEXT,
                msg TEXT,
                comentarios TEXT,
                termo_aditivo TEXT,
                atualizacao_comprasnet TEXT,
                instancia_governanca TEXT,
                comprasnet_contratos TEXT,
                registro_status TEXT
            )
        """):
            print("Falha ao criar a tabela 'controle_contratos':", query.lastError().text())
        else:
            print("Tabela 'controle_contratos' criada com sucesso.")

    def setup_model(self, table_name, editable=False):
        self.model = CustomSqlTableModel(parent=self.parent, db=self.db, non_editable_columns=[4, 8, 10, 13])
        self.model.setTable(table_name)
        if editable:
            self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.model.select()
        return self.model

    def configure_columns(self, table_view, visible_columns):
        for column in range(self.model.columnCount()):
            header = self.model.headerData(column, Qt.Orientation.Horizontal)
            if column not in visible_columns:
                table_view.hideColumn(column)
            else:
                self.model.setHeaderData(column, Qt.Orientation.Horizontal, header)
class CustomTableView(QTableView):
    def __init__(self, main_app, config_manager, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.config_manager = config_manager
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, pos):
        index = self.indexAt(pos)
        if index.isValid():
            contextMenu = TableMenu(self.main_app, index, self.model(), config_manager=self.config_manager)
            contextMenu.exec(self.viewport().mapToGlobal(pos))

class TableMenu(QMenu):
    def __init__(self, main_app, index, model=None, config_manager=None):
        super().__init__()
        self.main_app = main_app
        self.index = index
        self.model = model
        self.config_manager = config_manager
        self.setup_menu_style()
        self.add_menu_actions()

    def setup_menu_style(self):
        self.setStyleSheet("""
            QMenu {
                background-color: #f9f9f9;
                color: #333;
                border: 1px solid #ccc;
                font-size: 16px;
                font-weight: bold;
            }
            QMenu::item {
                background-color: transparent;
                padding: 5px 20px 5px 20px;
            }
            QMenu::item:selected {
                background-color: #b0c4de;
                color: white;
            }
            QMenu::separator {
                height: 2px;
                background-color: #d3d3d3;
                margin: 5px 0;
            }
        """)

    def add_menu_actions(self):
        actions = [
            "Editar Dados do Processo"
        ]
        for actionText in actions:
            action = QAction(actionText, self)
            action.triggered.connect(partial(self.trigger_action, actionText))
            self.addAction(action)

    def trigger_action(self, actionText):
        if self.index.isValid():
            source_index = self.model.mapToSource(self.index)
            row_data = self.get_row_data(source_index.row())
            df_registro_selecionado = pd.DataFrame([row_data])
            if not df_registro_selecionado.empty:
                print(df_registro_selecionado)
                self.perform_action(actionText, df_registro_selecionado, source_index.row())
            else:
                QMessageBox.warning(self, "Atenção", "Nenhum registro selecionado ou dados não encontrados.")

    def get_row_data(self, row):
        column_count = self.model.columnCount()
        row_data = {self.model.headerData(col, Qt.Orientation.Horizontal): self.model.data(self.model.index(row, col)) for col in range(column_count)}
        return row_data

    def perform_action(self, actionText, df_registro_selecionado, source_index):
        actions = {
            "Editar Dados do Processo": self.editar_dados
        }
        action = actions.get(actionText)
        if action:
            action(df_registro_selecionado, source_index)

    def editar_dados(self, df_registro_selecionado, indice_linha):
        dialog = AtualizarDadosContratos(
            self.main_app.icons_dir,
            df_registro_selecionado,
            self.main_app.ui_manager.table_view,
            self.main_app.model.sourceModel(),
            indice_linha
        )
        dialog.dadosContratosSalvos.connect(self.atualizar_interface)
        dialog.show()

    def atualizar_interface(self):
        print("Interface atualizada com os novos dados.")
        self.main_app.refresh_model()

class CustomSqlTableModel(QSqlTableModel):
    def __init__(self, parent=None, db=None, non_editable_columns=None, icons_dir=None):
        super().__init__(parent, db)
        self.non_editable_columns = non_editable_columns or []
        self.icons_dir = icons_dir

    def flags(self, index):
        default_flags = super().flags(index)
        if index.column() in self.non_editable_columns:
            return default_flags & ~Qt.ItemFlag.ItemIsEditable
        return default_flags

    def update_record(self, row, data):
        record = self.record(row)
        for column, value in data.items():
            record.setValue(column, value)
        if not self.setRecord(row, record):
            print("Erro ao definir registro:", self.lastError().text())
        if not self.submitAll():
            print("Erro ao submeter alterações:", self.lastError().text())

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if self.icons_dir and role == Qt.ItemDataRole.DecorationRole:
            if index.column() == self.fieldIndex("pode_renovar"):
                pode_renovar = self.index(index.row(), self.fieldIndex("pode_renovar")).data()
                if pode_renovar == 'Sim':
                    return QIcon(str(self.icons_dir / 'thumb-up.png'))
                elif pode_renovar == 'Não':
                    return QIcon(str(self.icons_dir / 'unchecked.png'))
            elif index.column() == self.fieldIndex("custeio"):
                custeio = self.index(index.row(), self.fieldIndex("custeio")).data()
                if custeio == 'Sim':
                    return QIcon(str(self.icons_dir / 'thumb-up.png'))
                elif custeio == 'Não':
                    return QIcon(str(self.icons_dir / 'unchecked.png'))

        if self.icons_dir and role == Qt.ItemDataRole.DecorationRole and index.column() == self.fieldIndex("status"):
            status = self.index(index.row(), self.fieldIndex("status")).data()
            status_icons = {
                'Minuta': 'status_secao_contratos.png',
                'Nota Técnica': 'status_nt.png',
                'Aguardando': 'status_cp_msg.png',
                'AGU': 'status_agu.png'
            }
            if status in status_icons:
                return QIcon(str(self.icons_dir / status_icons[status]))

        if role == Qt.ItemDataRole.DisplayRole and index.column() == self.fieldIndex("dias"):
            vigencia_final_index = self.fieldIndex("vigencia_final")
            vigencia_final = self.index(index.row(), vigencia_final_index).data()
            if vigencia_final:
                try:
                    vigencia_final_date = datetime.strptime(vigencia_final, '%d/%m/%Y')
                    hoje = datetime.today()
                    dias = (vigencia_final_date - hoje).days
                    return dias
                except ValueError:
                    return "Data Inválida"
        return super().data(index, role)


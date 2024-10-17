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
import time
from diretorios import *

class DatabaseATASManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None

    def connect_to_database(self):
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            # print(f"Conexão com o banco de dados aberta em {self.db_path}")
        return self.connection

    def close_connection(self):
        if self.connection:
            # print("Fechando conexão...")
            self.connection.close()
            self.connection = None
            # print(f"Conexão com o banco de dados fechada em {self.db_path}")

    def is_closed(self):
        return self.connection is None

    def __enter__(self):
        self.connect_to_database()
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def save_dataframe(self, df, table_name):
        conn = self.connect_to_database()
        try:
            df.to_sql(table_name, conn, if_exists='append', index=False)
        except sqlite3.IntegrityError as e:
            valor_duplicado = df.loc[df.duplicated(subset=['id'], keep=False), 'id']
            mensagem_erro = f"Erro ao salvar o DataFrame: Valor duplicado(s) encontrado(s) na coluna 'id': {valor_duplicado.to_list()}."
            logging.error(mensagem_erro)
            QMessageBox.warning(None, "Erro de Duplicação", mensagem_erro)
        except sqlite3.Error as e:
            logging.error(f"Erro ao salvar DataFrame: {e}")
        finally:
            self.close_connection()
            
    def delete_record(self, table_name, column, value):
        conn = self.connect_to_database()
        try:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE {column} = ?", (value,))
            conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error deleting record: {e}")
        finally:
            self.close_connection()

    def execute_query(self, query, params=None):
        conn = self.connect_to_database()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error executing query: {query}, Error: {e}")
            return None
        finally:
            self.close_connection()

    def load_contract_data_by_key(self, id):
        """
        Carrega os dados do contrato a partir da chave primária id.
        """
        conn = self.connect_to_database()
        try:
            query = "SELECT * FROM controle_contratos WHERE id = ?"
            df = pd.read_sql_query(query, conn, params=(id,))
            return df
        except sqlite3.Error as e:
            logging.error(f"Erro ao carregar dados do contrato '{id}': {e}")
            return pd.DataFrame()  # Retorna DataFrame vazio em caso de erro
        finally:
            self.close_connection()
            
class SqlModel:
    def __init__(self, icons_dir, database_manager, parent=None):
        self.icons_dir = icons_dir
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
        if not query.exec("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_atas'"):
            print("Erro ao verificar existência da tabela:", query.lastError().text())
        if not query.next():
            print("Tabela 'controle_atas' não existe. Criando tabela...")
            self.create_table_if_not_exists()
        else:
            print("Tabela 'controle_atas' existe. Verificando estrutura da coluna...")

    def create_table_if_not_exists(self):
        query = QSqlQuery(self.db)
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS controle_atas (
                status TEXT,
                dias INTEGER,
                cnpj TEXT,                
                referencia TEXT,
                sequencial TEXT,
                ano TEXT,
                numero_ata TEXT,
                id_pncp TEXT PRIMARY KEY,
                vigencia_inicial DATE,
                vigencia_final DATE,
                data_assinatura DATE,
                data_publicacao DATE,
                objeto TEXT,
                codigo_unidade TEXT,
                nome_unidade TEXT,
                nome_fornecedor TEXT,
                cnpj_cpf_fornecedor TEXT
            )
        """):
            print("Falha ao criar a tabela 'controle_atas':", query.lastError().text())
        else:
            print("Tabela 'controle_atas' criada com sucesso.")


    def setup_model(self, table_name, editable=False):
        self.model = CustomSqlTableModel(parent=self.parent, db=self.db, non_editable_columns=None, icons_dir=self.icons_dir)
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

class CustomSqlTableModel(QSqlTableModel):
    def __init__(self, parent=None, db=None, non_editable_columns=None, icons_dir=None):
        super().__init__(parent, db)
        self.non_editable_columns = non_editable_columns if non_editable_columns is not None else []
        self.icons_dir = icons_dir
        self.icon_column_name = "icon_column"  # Nome da coluna fictícia para ícones
            
    def order_by_vigencia_final(self):
        """Ordena a tabela pela coluna 'vigencia_final' em ordem decrescente."""
        vigencia_final_index = self.fieldIndex("Dias")

        if vigencia_final_index != -1:
            # Aplique a ordenação diretamente na coluna 'vigencia_final' que está no formato YYYY-MM-DD
            self.setSort(vigencia_final_index, Qt.SortOrder.DescendingOrder)
            self.select()  # Recarregar os dados para refletir a ordenação
        else:
            print("Coluna 'Dias' não encontrada para ordenação.")

    def flags(self, index):
        default_flags = super().flags(index)
        if index.column() == self.fieldIndex(self.icon_column_name) or index.column() in self.non_editable_columns:
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        return default_flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.column() in self.non_editable_columns:
            return False
        return super().setData(index, value, role)

    def update_record(self, row, data):
        record = self.record(row)
        for column, value in data.items():
            record.setValue(column, value)
        if not self.setRecord(row, record):
            print("Erro ao definir registro:", self.lastError().text())
        if not self.submitAll():
            print("Erro ao submeter alterações:", self.lastError().text())

    def columnCount(self, parent=QModelIndex()):
        # Adiciona uma coluna extra para os ícones
        return super().columnCount(parent) + 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):

        if self.icons_dir and role == Qt.ItemDataRole.DecorationRole:
            if index.column() == self.fieldIndex("prorrogavel"):
                prorrogavel = self.index(index.row(), self.fieldIndex("prorrogavel")).data()
                if prorrogavel == 'Sim':
                    return QIcon(str(self.icons_dir / 'thumb-up.png'))
                elif prorrogavel == 'Não':
                    return QIcon(str(self.icons_dir / 'unchecked.png'))
            elif index.column() == self.fieldIndex("custeio"):
                custeio = self.index(index.row(), self.fieldIndex("custeio")).data()
                if custeio == 'Sim':
                    return QIcon(str(self.icons_dir / 'thumb-up.png'))
                elif custeio == 'Não':
                    return QIcon(str(self.icons_dir / 'unchecked.png'))

        # Lógica para a coluna "dias"
        if role == Qt.ItemDataRole.DisplayRole and index.column() == self.fieldIndex("dias"):
            vigencia_final_index = self.fieldIndex("vigencia_final")
            vigencia_final = self.index(index.row(), vigencia_final_index).data()
            
            if vigencia_final:
                try:
                    # Tentativa de conversão da data no formato 'DD/MM/YYYY'
                    vigencia_final_date = datetime.strptime(vigencia_final, '%d/%m/%Y')
                except ValueError:
                    try:
                        # Tentativa de conversão da data no formato 'YYYY-MM-DD'
                        vigencia_final_date = datetime.strptime(vigencia_final, '%Y-%m-%d')
                    except ValueError:
                        return "Data Inválida"

                hoje = datetime.today()
                dias = (vigencia_final_date - hoje).days
                

                return dias

        # Lógica para cores da coluna "dias"
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == self.fieldIndex("dias"):
            dias = self.data(index, Qt.ItemDataRole.DisplayRole)
            if isinstance(dias, int):
                if dias < 31:
                    return QColor(255, 0, 0)  # Vermelho
                elif 31 <= dias <= 90:
                    return QColor(255, 165, 0)  # Laranja
                elif 91 <= dias <= 159:
                    return QColor(255, 255, 0)  # Amarelo
                else:
                    return QColor(0, 255, 0)  # Verde
                
        return super().data(index, role)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and section == self.fieldIndex(self.icon_column_name):
            if role == Qt.ItemDataRole.DisplayRole:
                return ""
        return super().headerData(section, orientation, role)

    def fieldIndex(self, field_name):
        if field_name == self.icon_column_name:
            return super().columnCount() - 1
        return super().fieldIndex(field_name)
                
class CustomTableView(QTableView):
    def __init__(self, main_app, config_manager, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.config_manager = config_manager

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
            df_registro_selecionado = self.get_row_data(self.index.row())  # Obter o DataFrame necessário
            source_index = self.index  # Assumindo que o índice da fonte é o índice atual
            action.triggered.connect(partial(self.trigger_action, actionText, df_registro_selecionado, source_index))
            self.addAction(action)

    def trigger_action(self, actionText, df_registro_selecionado, source_index):
        try:
            self.perform_action(actionText, df_registro_selecionado, source_index)
        except Exception as e:
            print(f"Erro ao executar a ação: {str(e)}")

    def get_row_data(self, row):
        column_count = self.model.columnCount()
        row_data = {self.model.headerData(col, Qt.Orientation.Horizontal): self.model.data(self.model.index(row, col)) for col in range(column_count)}
        return pd.DataFrame([row_data])  # Retorna um DataFrame em vez de um dicionário

    def perform_action(self, actionText, df_registro_selecionado, source_index):
        actions = {
            "Editar Dados do Processo": self.editar_dados
        }
        action = actions.get(actionText)
        if action:
            action(df_registro_selecionado)  # Chamando o método sem parênteses adicionais

    def editar_dados(self, df_registro_selecionado):
        dados = df_registro_selecionado.iloc[0].to_dict()
        dialog = AtualizarDadosContratos(ICONS_DIR, dados=dados, parent=self)
        dialog.dadosContratosSalvos.connect(self.atualizar_interface)
        dialog.show()

    def atualizar_interface(self):
        print("Interface atualizada com os novos dados.")
        self.main_app.refresh_model()

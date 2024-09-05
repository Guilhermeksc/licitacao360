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

class DatabaseContratosManager:
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

    def create_table_controle_assinatura(self):
        conn = self.connect_to_database()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS controle_assinaturas (
                    id TEXT PRIMARY KEY,
                    assinatura_contrato TEXT
                )
            """)
            conn.commit()
            print("Tabela 'controle_assinaturas' criada ou já existente.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao criar tabela 'controle_assinaturas': {e}")
        finally:
            self.close_connection()

    @staticmethod
    def create_table_controle_contratos(conn):
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS controle_contratos (
                status TEXT,
                dias TEXT,     
                prorrogavel TEXT,                          
                custeio TEXT,
                numero TEXT,
                tipo TEXT,  
                id_processo TEXT,
                nome_fornecedor TEXT,                                          
                objeto TEXT,
                valor_global TEXT, 
                codigo TEXT,
                processo TEXT,
                cnpj_cpf_idgener TEXT,                        
                natureza_continuada TEXT,
                nome_resumido TEXT,
                indicativo_om TEXT,
                nome TEXT,
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
                registro_status TEXT,                    
                termo_aditivo TEXT,
                atualizacao_comprasnet TEXT,
                instancia_governanca TEXT,
                comprasnet_contratos TEXT,
                licitacao_numero TEXT,
                data_assinatura TEXT,
                data_publicacao TEXT,
                categoria TEXT,
                subtipo TEXT,
                situacao TEXT,
                id TEXT PRIMARY KEY,
                amparo_legal TEXT,
                modalidade TEXT,
                assinatura_contrato TEXT                      
            )
        """)
        conn.commit()

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
        if not query.exec("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_contratos'"):
            print("Erro ao verificar existência da tabela:", query.lastError().text())
        if not query.next():
            print("Tabela 'controle_contratos' não existe. Criando tabela...")
            self.create_table_if_not_exists()
        else:
            print("Tabela 'controle_contratos' existe. Verificando estrutura da coluna...")
    def create_table_if_not_exists(self):
        query = QSqlQuery(self.db)
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS controle_contratos (
                status TEXT,
                dias TEXT,     
                prorrogavel TEXT,                          
                custeio TEXT,
                numero TEXT,
                tipo TEXT,  
                id_processo TEXT,
                nome_fornecedor TEXT,                                          
                objeto TEXT,
                valor_global TEXT, 
                codigo TEXT,
                processo TEXT,
                cnpj_cpf_idgener TEXT,                        
                natureza_continuada TEXT,
                nome_resumido TEXT,
                indicativo_om TEXT,
                nome TEXT,
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
                registro_status TEXT,                    
                termo_aditivo TEXT,
                atualizacao_comprasnet TEXT,
                instancia_governanca TEXT,
                comprasnet_contratos TEXT,
                licitacao_numero TEXT,
                data_assinatura TEXT,
                data_publicacao TEXT,
                categoria TEXT,
                subtipo TEXT,
                situacao TEXT,
                id TEXT PRIMARY KEY,
                amparo_legal TEXT,
                modalidade TEXT,
                assinatura_contrato TEXT                           
            )
        """):
            print("Falha ao criar a tabela 'controle_contratos':", query.lastError().text())
        else:
            print("Tabela 'controle_contratos' criada com sucesso.")

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

        # # Carregar a tabela e definir a ordenação
        # self.setTable('controle_contratos')
        # self.order_by_vigencia_final()
        # self.select()
        
    def update_record_by_primary_key(self, primary_key_column, primary_key_value, data):
        """
        Atualiza um registro na tabela com base na chave primária.

        :param primary_key_column: Nome da coluna da chave primária.
        :param primary_key_value: Valor da chave primária para identificar o registro a ser atualizado.
        :param data: Dicionário contendo os novos valores para o registro.
        """
        # Construir a cláusula SET para o SQL
        set_clause = ", ".join([f"{col} = :{col}" for col in data.keys()])
        sql_query = f"UPDATE {self.tableName()} SET {set_clause} WHERE {primary_key_column} = :primary_key_value"

        # Preparar a query
        query = QSqlQuery(self.database())
        query.prepare(sql_query)

        # Vincular os valores dos dados
        for col, value in data.items():
            query.bindValue(f":{col}", value)

        # Vincular o valor da chave primária
        query.bindValue(":primary_key_value", primary_key_value)

        # Executar a query e verificar por erros
        if not query.exec():
            print(f"Erro ao atualizar registro: {query.lastError().text()}")
            return False

        self.select()  # Recarregar os dados da tabela para refletir as mudanças
        return True
    
    def order_by_vigencia_final(self):
        """Ordena a tabela pela coluna 'vigencia_final' em ordem decrescente."""
        vigencia_final_index = self.fieldIndex("vigencia_final")
        
        # Verifique se o índice da coluna é válido
        if vigencia_final_index != -1:
            self.setSort(vigencia_final_index, Qt.SortOrder.DescendingOrder)
        else:
            print("Coluna 'vigencia_final' não encontrada para ordenação.")

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
                if dias < 30:
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
    #     self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    #     self.customContextMenuRequested.connect(self.showContextMenu)

    # def showContextMenu(self, pos):
    #     index = self.indexAt(pos)
    #     if index.isValid():
    #         contextMenu = TableMenu(self.main_app, index, self.model(), config_manager=self.config_manager)
    #         contextMenu.exec(self.viewport().mapToGlobal(pos))

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

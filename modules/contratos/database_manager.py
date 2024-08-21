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
                    numero_contrato TEXT PRIMARY KEY,
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
                indicativo_om TEXT,
                om_extenso TEXT,
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
                assinatura_contrato TEXT
            )
        """)
        conn.commit()

    def save_dataframe(self, df, table_name):
        conn = self.connect_to_database()
        try:
            df.to_sql(table_name, conn, if_exists='append', index=False)
        except sqlite3.Error as e:
            logging.error(f"Error saving dataframe: {e}")
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
            self.ensure_numero_contrato_primary_key()

    def ensure_numero_contrato_primary_key(self):
        query = QSqlQuery(self.db)
        query.exec("PRAGMA table_info(controle_contratos)")
        numero_contrato_is_primary = False
        while query.next():
            if query.value(1) == 'numero_contrato' and query.value(5) == 1:
                numero_contrato_is_primary = True
                break
        if not numero_contrato_is_primary:
            print("Atualizando 'numero_contrato' para ser PRIMARY KEY.")
            query.exec("ALTER TABLE controle_contratos ADD COLUMN new_numero_contrato TEXT PRIMARY KEY")
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
                indicativo_om TEXT,
                om_extenso TEXT,
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

    def flags(self, index):
        default_flags = super().flags(index)
        # Desabilita a edição na coluna de ícones
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
        # Lógica para a coluna "dias"
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

        # Lógica para a coluna de ícones ao lado direito de "dias"
        if index.column() == self.fieldIndex(self.icon_column_name) and role == Qt.ItemDataRole.DecorationRole:
            if self.icons_dir:
                # Lógica para ícones baseados em "dias"
                dias_index = self.fieldIndex("dias")
                dias = self.index(index.row(), dias_index).data()

                image_dias = None
                if isinstance(dias, int):
                    if 60 <= dias <= 180:
                        image_dias = QImage(str(self.icons_dir / "message_alert.png"))
                        print(f"[DEBUG] - Imagem para dias (60-180): {str(self.icons_dir / 'message_alert.png')}")
                    elif 1 <= dias < 60:
                        image_dias = QImage(str(self.icons_dir / "head_skull.png"))
                        print(f"[DEBUG] - Imagem para dias (1-60): {str(self.icons_dir / 'head_skull.png')}")

                # Lógica para ícones baseados em "status"
                status_index = self.fieldIndex("status")
                status = self.index(index.row(), status_index).data()

                status_images = {
                    'Minuta': 'status_secao_contratos.png',
                    'Nota Técnica': 'status_nt.png',
                    'Aguardando': 'status_cp_msg.png',
                    'AGU': 'status_agu.png',
                    'Seção de Contratos': 'status_secao_contratos.png',
                    'CP Enviada': '.png',
                }

                image_status = QImage(str(self.icons_dir / status_images[status])) if status in status_images else None

                if image_status:
                    print(f"[DEBUG] - Imagem para status '{status}': {str(self.icons_dir / status_images[status])}")

                # Defina o tamanho desejado das imagens
                desired_image_size = QSize(64, 64)

                # Redimensiona as imagens
                if image_dias:
                    image_dias = image_dias.scaled(desired_image_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    print(f"[DEBUG] - Tamanho da imagem dias depois da escala: {image_dias.size()}")

                if image_status:
                    image_status = image_status.scaled(desired_image_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    print(f"[DEBUG] - Tamanho da imagem status depois da escala: {image_status.size()}")

                # Combina as imagens (se ambas existirem)
                if image_status or image_dias:
                    pixmap_width = 2 * desired_image_size.width()
                    pixmap = QPixmap(pixmap_width, desired_image_size.height())  # Ajusta o pixmap para acomodar ambas as imagens
                    pixmap.fill(Qt.GlobalColor.transparent)  # Preenche o fundo com transparência
                    painter = QPainter(pixmap)

                    if image_status:
                        painter.drawPixmap(0, 0, QPixmap.fromImage(image_status))  # Desenha a imagem de status
                    if image_dias:
                        painter.drawPixmap(desired_image_size.width(), 0, QPixmap.fromImage(image_dias))  # Desenha a imagem de dias ao lado

                    painter.end()
                    return QIcon(pixmap)

            return None

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
            self.main_app.ui_manager.table_view.model().sourceModel(),
            indice_linha
        )
        dialog.dadosContratosSalvos.connect(self.atualizar_interface)
        dialog.show()


    def atualizar_interface(self):
        print("Interface atualizada com os novos dados.")
        self.main_app.refresh_model()

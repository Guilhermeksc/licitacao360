from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from pathlib import Path
from diretorios import *
from database.utils.treeview_utils import load_images, create_button
from modules.planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_pregao, carregar_dados_dispensa
import pandas as pd
import os
import psutil
import subprocess
from functools import partial
from datetime import datetime
import logging
import sqlite3
import re
import locale

class ExportThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, model, filepath):
        super().__init__()
        self.model = model
        self.filepath = filepath

    def run(self):
        try:
            df = self.model_to_dataframe(self.model)
            df.to_excel(self.filepath, index=False)
            self.finished.emit('Completed successfully!')
        except Exception as e:
            self.finished.emit(f"Failed: {str(e)}")

    def model_to_dataframe(self, model):
        headers = [model.headerData(i, Qt.Orientation.Horizontal) for i in range(model.columnCount())]
        data = [
            [model.data(model.index(row, col)) for col in range(model.columnCount())]
            for row in range(model.rowCount())
        ]
        return pd.DataFrame(data, columns=headers)
    
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

class DispensaEletronicaWidget(QMainWindow):
    dataUpdated = pyqtSignal()

    def __init__(self, icons_dir, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(icons_dir)
        self.setup_managers()
        self.load_initial_data()
        self.model = self.init_model()
        self.ui_manager = UIManager(self, self.icons_dir, self.config_manager, self.model)
        self.setup_ui()
        self.export_thread = None
        self.output_path = os.path.join(os.getcwd(), "controle_dispensa_eletronica.xlsx")
        self.dataUpdated.connect(self.refresh_model)

    def refresh_model(self):
        # Atualiza o modelo de dados e a visualização da tabela
        self.model.select()

    def setup_ui(self):
        self.setCentralWidget(self.ui_manager.main_widget)  # Define o widget central como o widget principal do UIManager

    def setup_managers(self):
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        self.event_manager = EventManager()

    def load_initial_data(self):
        print("Carregando dados iniciais...")
        self.image_cache = load_images(self.icons_dir, [
            "plus.png", "import_de.png", "save_to_drive.png", "loading.png", "delete.png", 
            "excel.png", "calendar.png", "report.png", "management.png"
        ])
        self.selectedIndex = None

    def init_model(self):
        # Inicializa e retorna o modelo SQL utilizando o DatabaseManager
        sql_model = SqlModel(self.database_manager, self)
        return sql_model.setup_model("controle_dispensas", editable=True)
    
    def teste(self):
        print("Teste de botão")

    def on_add_item(self):
        dialog = AddItemDialog(self)
        if dialog.exec():
            item_data = dialog.get_data()
            self.save_to_database(item_data)

    def excluir_linha(self):
        selection_model = self.ui_manager.table_view.selectionModel()

        if selection_model.hasSelection():
            # Supondo que a coluna 0 é 'id_processo'
            index_list = selection_model.selectedRows(0)

            if not index_list:
                QMessageBox.warning(self, "Nenhuma Seleção", "Nenhuma linha selecionada.")
                return

            selected_id_processo = index_list[0].data()  # Pega o 'id_processo' da primeira linha selecionada
            print(f"Excluindo linha com id_processo: {selected_id_processo}")

            # Confirmar a exclusão
            if Dialogs.confirm(self, 'Confirmar exclusão', f"Tem certeza que deseja excluir o registro com ID Processo '{selected_id_processo}'?"):
                data_to_delete = {'id_processo': selected_id_processo}
                try:
                    self.save_to_database(data_to_delete, delete=True)  # Passa o dado a ser deletado com uma flag de exclusão
                    QMessageBox.information(self, "Sucesso", "Registro excluído com sucesso.")
                except Exception as e:
                    QMessageBox.warning(self, "Erro ao excluir", f"Erro ao excluir o registro: {str(e)}")
                    print(f"Erro ao excluir o registro: {str(e)}")
        else:
            QMessageBox.warning(self, "Nenhuma Seleção", "Por favor, selecione uma linha para excluir.")

    def salvar_tabela(self):
        if self.is_file_open(self.output_path):
            QMessageBox.warning(self, "Erro ao salvar", "O arquivo já está aberto. Por favor, feche-o antes de tentar salvar novamente.")
            return

        self.export_thread = ExportThread(self.model, self.output_path)
        self.export_thread.finished.connect(self.handle_export_finished)
        self.export_thread.start()

    def handle_export_finished(self, message):
        if 'successfully' in message:
            QMessageBox.information(self, "Exportação de Dados", "Dados exportados com sucesso!")
            try:
                # Tentar abrir o arquivo com o Excel
                subprocess.run(f'start excel.exe "{self.output_path}"', shell=True, check=True)
            except Exception as e:
                QMessageBox.warning(self, "Erro ao abrir o arquivo", str(e))
        else:
            QMessageBox.warning(self, "Exportação de Dados", message)

    def carregar_tabela(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.xls *.ods)")
        if filepath:
            try:
                df = pd.read_excel(filepath)
                required_columns = ['ID Processo', 'NUP', 'Objeto', 'UASG']
                if not all(col in df.columns for col in required_columns):
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    QMessageBox.warning(self, "Erro ao carregar", f"O arquivo não contém todos os índices necessários. Faltando: {', '.join(missing_columns)}")
                    return
                rename_map = {'ID Processo': 'id_processo', 'NUP': 'nup', 'Objeto': 'objeto', 'UASG': 'uasg'}
                df.rename(columns=rename_map, inplace=True)
                print("Registros salvos:")
                print(df)

                # Obter dados de OM com base na UASG
                self.salvar_detalhes_uasg_sigla_nome(df)
                # Desmembrar 'id_processo' em 'tipo', 'numero', e 'ano'
                self.desmembramento_id_processo(df)

                self.save_to_database(df)
                QMessageBox.information(self, "Carregamento concluído", "Os dados foram carregados e transformados com sucesso.")
            except Exception as e:
                QMessageBox.warning(self, "Erro ao carregar", f"Um erro ocorreu: {str(e)}")
                print(f"Erro ao carregar o arquivo: {str(e)}")

    def desmembramento_id_processo(self, df):
        # Extraíndo valores de 'id_processo' e atribuindo a 'tipo', 'numero', e 'ano'
        # Assume que o formato de 'id_processo' é sempre 'DE xx/yyyy'
        df[['tipo', 'numero', 'ano']] = df['id_processo'].str.extract(r'(\D+)(\d+)/(\d+)')
        # Mapeando o tipo para um valor mais descritivo
        df['tipo'] = df['tipo'].map({'DE ': 'Dispensa Eletrônica'}).fillna('Tipo Desconhecido')

        print("Colunas desmembradas de 'id_processo':")
        print(df[['tipo', 'numero', 'ano']])
        
    def salvar_detalhes_uasg_sigla_nome(self, df):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uasg, sigla_om, orgao_responsavel FROM controle_om")
            om_details = {row[0]: {'sigla_om': row[1], 'orgao_responsavel': row[2]} for row in cursor.fetchall()}
        
        df['sigla_om'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('sigla_om', ''))
        df['orgao_responsavel'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('orgao_responsavel', ''))
        print("Dados enriquecidos com detalhes de OM:")
        print(df[['uasg', 'sigla_om', 'orgao_responsavel']])
                
    def is_file_open(self, file_path):
        """ Verifica se o arquivo está aberto por algum processo usando psutil. """
        try:
            for proc in psutil.process_iter(attrs=['open_files']):
                if file_path in (fl.path for fl in proc.info['open_files'] or []):
                    return True
        except psutil.Error as e:
            print(f"Erro ao verificar arquivos abertos: {e}")
        return False

    def save_to_database(self, data, delete=False):
        with self.database_manager as conn:
            cursor = conn.cursor()

            if delete:
                try:
                    delete_sql = "DELETE FROM controle_dispensas WHERE id_processo = ?"
                    cursor.execute(delete_sql, (data['id_processo'],))
                    print(f"Deleting {data['id_processo']}")
                except Exception as e:
                    print(f"Error deleting record: {e}")
                    raise e
            else:
                upsert_sql = '''
                INSERT INTO controle_dispensas (
                    id_processo, nup, objeto, uasg, tipo, numero, ano, sigla_om, material_servico, orgao_responsavel
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id_processo) DO UPDATE SET
                    nup=excluded.nup,
                    objeto=excluded.objeto,
                    uasg=excluded.uasg,
                    tipo=excluded.tipo,
                    numero=excluded.numero,
                    ano=excluded.ano,
                    sigla_om=excluded.sigla_om,
                    material_servico=excluded.material_servico,
                    orgao_responsavel=excluded.orgao_responsavel;
                '''
                try:
                    if isinstance(data, pd.DataFrame):
                        for _, row in data.iterrows():
                            cursor.execute(upsert_sql, (
                                row['id_processo'], row['nup'], row['objeto'], row['uasg'], 
                                row.get('tipo', ''), row.get('numero', ''), row.get('ano', ''),
                                row.get('sigla_om', ''), row.get('material_servico', ''), row.get('orgao_responsavel', '')
                            ))
                            print(f"Updating or inserting {row['id_processo']}")
                    else:
                        cursor.execute(upsert_sql, (
                            data['id_processo'], data['nup'], data['objeto'], data['uasg'],
                            data['tipo'], data['numero'], data['ano'],
                            data['sigla_om'], data['material_servico'], data['orgao_responsavel']
                        ))
                        print(f"Updating or inserting single item {data['id_processo']}")
                except Exception as e:
                    print(f"Database error during upsert: {e}")

            conn.commit()

        # Emita o sinal para atualizar a tabela
        self.dataUpdated.emit()
        print("Database operation completed and table view updated.")

class UIManager:
    def __init__(self, parent, icons, config_manager, model):
        self.parent = parent
        self.icons = icons
        self.config_manager = config_manager
        self.model = model
        self.main_widget = QWidget(parent)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.button_manager = ButtonManager(self.parent)
        self.init_ui()

    def init_ui(self):
        self.setup_search_bar()
        self.setup_buttons_layout()
        self.setup_table_view()
        self.parent.setCentralWidget(self.main_widget) 

    def setup_search_bar(self):
        self.search_bar = QLineEdit(self.parent)
        self.search_bar.setPlaceholderText("Digite para buscar...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #f9f9f9;
                color: #333;
                font-size: 16px;
                border: 1px solid #ccc;
                padding: 5px;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #a9a9a9;
            }
            QLineEdit:hover {
                background-color: #e0e0e0;
            }
        """)
        self.main_layout.addWidget(self.search_bar)

        def handle_text_change(text):
            regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.parent.proxy_model.setFilterRegularExpression(regex)

        self.search_bar.textChanged.connect(handle_text_change)
        self.main_layout.addWidget(self.search_bar)

    def setup_buttons_layout(self):
        self.buttons_layout = QHBoxLayout()
        self.button_manager.add_buttons_to_layout(self.buttons_layout)
        self.main_layout.addLayout(self.buttons_layout)

    def setup_table_view(self):
        self.table_view = CustomTableView(main_app=self.parent, config_manager=self.config_manager, parent=self.main_widget)
        self.table_view.setModel(self.model)
        self.main_layout.addWidget(self.table_view)
        self.configure_table_model()
        self.table_view.verticalHeader().setVisible(False)
        self.adjust_columns()
        self.apply_custom_style()
        
        center_delegate = CenterAlignDelegate(self.table_view)
        for column in range(self.model.columnCount()):
            self.table_view.setItemDelegateForColumn(column, center_delegate)

        status_index = self.model.fieldIndex("etapa")
        self.table_view.setItemDelegateForColumn(status_index, CustomItemDelegate(self.icons, self.table_view))

    def configure_table_model(self):
        self.parent.proxy_model = QSortFilterProxyModel(self.parent)
        self.parent.proxy_model.setSourceModel(self.model)
        self.parent.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.parent.proxy_model.setFilterKeyColumn(-1)
        self.parent.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)
        self.table_view.setModel(self.parent.proxy_model)

        self.model.dataChanged.connect(self.table_view.update)

        if self.table_view.selectionModel():
            self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
            self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
            # self.table_view.selectionModel().selectionChanged.connect(self.linhaSelecionada)

        self.update_column_headers()
        self.hide_unwanted_columns()
            
    def adjust_columns(self):
        # Ajustar automaticamente as larguras das colunas ao conteúdo
        self.table_view.resizeColumnsToContents()
        QTimer.singleShot(1, self.apply_custom_column_sizes) 

    def apply_custom_column_sizes(self):
        print("Aplicando configurações de tamanho de coluna...")
        header = self.table_view.horizontalHeader()
        
        # Configurações específicas de redimensionamento para colunas selecionadas
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(13, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(14, QHeaderView.ResizeMode.Fixed) 
        # Definir tamanhos específicos onde necessário
        header.resizeSection(0, 140)
        header.resizeSection(4, 175)
        header.resizeSection(8, 70)
        header.resizeSection(10, 100)
        header.resizeSection(13, 230)
        header.resizeSection(14, 180)

    def apply_custom_style(self):
        # Aplica um estilo CSS personalizado ao tableView
        self.table_view.setStyleSheet("""
            QTableView {
                background-color: #f9f9f9;
                alternate-background-color: #e0e0e0;
                color: #333;
                font-size: 16px;
                border: 1px solid #ccc;
            }
            QTableView::item:selected {
                background-color: #b0c4de;
                color: white;
            }
            QTableView::item:hover {
                background-color: #d3d3d3;
                color: black;
            }
            QTableView::section {
                background-color: #d3d3d3;
                color: #333;
                padding: 5px;
                border: 1px solid #ccc;
                font-size: 16px;
                font-weight: bold; 
            }
            QHeaderView::section:horizontal {
                background-color: #a9a9a9;
                color: white;
                border: 1px solid #ccc;
                padding: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QHeaderView::section:vertical {
                background-color: #d3d3d3;
                color: #333;
                border: 1px solid #ccc;
                padding: 5px;
                font-size: 16px;
            }
        """)

    def linhaSelecionada(self, selected, deselected):
        if selected.indexes():
            proxy_index = selected.indexes()[0]
            source_index = self.parent.proxy_model.mapToSource(proxy_index)
            print(f"Linha selecionada: {source_index.row()}, Coluna: {source_index.column()}")

            df_registro_selecionado = carregar_dados_pregao(source_index.row(), self.parent.database_path)
            if not df_registro_selecionado.empty:
                logging.debug(f"Registro selecionado: {df_registro_selecionado.iloc[0].to_dict()}")
            else:
                logging.warning("Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")
                QMessageBox.warning(self.parent, "Erro", "Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")

    def update_column_headers(self):
        titles = {
            0: "ID Processo",
            4: "NUP",
            5: "Objeto",
            8: "UASG",
            10: "OM",
            13: "Status",
            14: "Operador"
        }
        for column, title in titles.items():
            self.model.setHeaderData(column, Qt.Orientation.Horizontal, title)

    def hide_unwanted_columns(self):
        visible_columns = {0, 4, 5, 8, 10, 13, 14}
        for column in range(self.model.columnCount()):
            if column not in visible_columns:
                self.table_view.hideColumn(column)

class ButtonManager:
    def __init__(self, parent):
        self.parent = parent  # parent deveria ser uma instância de um QWidget ou classe derivada
        self.buttons = []
        self.create_buttons()

    def create_buttons(self):
        button_specs = [
            ("  Adicionar", self.parent.image_cache['plus'], self.parent.on_add_item, "Adiciona um novo item ao banco de dados"),
            ("  Salvar", self.parent.image_cache['excel'], self.parent.salvar_tabela, "Salva o dataframe em um arquivo excel('.xlsx')"),
            ("  Importar", self.parent.image_cache['import_de'], self.parent.carregar_tabela, "Carregar dados de uma tabela"),
            ("  Excluir", self.parent.image_cache['delete'], self.parent.excluir_linha, "Exclui um item selecionado"),
            ("  Controle de PDM", self.parent.image_cache['calendar'], self.parent.teste, "Abre o painel de controle do processo"),
        ]
        for text, icon, callback, tooltip in button_specs:
            btn = self.create_button(text, icon, callback, tooltip, self.parent)
            self.buttons.append(btn)

    def add_buttons_to_layout(self, layout):
        for btn in self.buttons:
            layout.addWidget(btn)

    def create_button(self, text, icon, callback, tooltip_text, parent, icon_size=QSize(40, 40)):
        btn = QPushButton(text, parent)
        if icon:
            btn.setIcon(QIcon(icon))
            btn.setIconSize(icon_size)
        if callback:
            btn.clicked.connect(callback)
        if tooltip_text:
            btn.setToolTip(tooltip_text)

        btn.setStyleSheet("""
        QPushButton {
            background-color: black;
            color: white;
            font-size: 14pt;
            min-height: 35px;
            padding: 5px;      
        }
        QPushButton:hover {
            background-color: white;
            color: black;
        }
        QPushButton:pressed {
            background-color: #ddd;
            color: black;
        }
        """)

        return btn

class CustomSqlTableModel(QSqlTableModel):
    def __init__(self, parent=None, db=None, non_editable_columns=None):
        super().__init__(parent, db)
        self.non_editable_columns = non_editable_columns if non_editable_columns is not None else []

    def flags(self, index):
        if index.column() in self.non_editable_columns:
            return super().flags(index) & ~Qt.ItemFlag.ItemIsEditable  # Remove a permissão de edição
        return super().flags(index)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # Verifica se a coluna deve ser não editável e ajusta o retorno para DisplayRole
        if role == Qt.ItemDataRole.DisplayRole and index.column() in self.non_editable_columns:
            return super().data(index, role)

        return super().data(index, role)
    
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
        if not query.exec("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_dispensas'"):
            print("Erro ao verificar existência da tabela:", query.lastError().text())
        if not query.next():
            print("Tabela 'controle_dispensas' não existe. Criando tabela...")
            self.create_table_if_not_exists()
        else:
            print("Tabela 'controle_dispensas' existe. Verificando estrutura da coluna...")
            self.ensure_id_processo_primary_key()

    def ensure_id_processo_primary_key(self):
        query = QSqlQuery(self.db)
        query.exec("PRAGMA table_info(controle_dispensas)")
        id_processo_is_primary = False
        while query.next():
            if query.value(1) == 'id_processo' and query.value(5) == 1:
                id_processo_is_primary = True
                print("Coluna 'id_processo' já é PRIMARY KEY.")
                break
        if not id_processo_is_primary:
            print("Atualizando 'id_processo' para ser PRIMARY KEY.")
            query.exec("ALTER TABLE controle_dispensas ADD COLUMN new_id_processo VARCHAR(100) PRIMARY KEY")
            query.exec("UPDATE controle_dispensas SET new_id_processo = id_processo")
            query.exec("ALTER TABLE controle_dispensas DROP COLUMN id_processo")
            query.exec("ALTER TABLE controle_dispensas RENAME COLUMN new_id_processo TO id_processo")
            if not query.isActive():
                print("Erro ao atualizar chave primária:", query.lastError().text())

    def create_table_if_not_exists(self):
        query = QSqlQuery(self.db)
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS controle_dispensas (
                id_processo VARCHAR(100) PRIMARY KEY,
                tipo VARCHAR(100),
                numero VARCHAR(100),
                ano VARCHAR(100),
                nup VARCHAR(100),
                objeto VARCHAR(100),
                objeto_completo TEXT,
                valor_total REAL,
                uasg VARCHAR(10),
                orgao_responsavel VARCHAR(250),
                sigla_om VARCHAR(100),
                setor_responsavel TEXT,
                operador VARCHAR(100),
                data_sessao DATE,
                material_servico VARCHAR(30),
                link_pncp TEXT,
                link_portal_marinha TEXT,
                comentarios TEXT
            )
        """):
            print("Falha ao criar a tabela 'controle_dispensas':", query.lastError().text())
        else:
            print("Tabela 'controle_dispensas' criada com sucesso.")

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

class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, icons, parent=None):
        super().__init__(parent)
        self.icons = icons

    def paint(self, painter, option, index):
        painter.save()
        super().paint(painter, option, index)  # Draw default text and background first
        status = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        icon = self.icons.get(status, None)

        if icon:
            icon_size = 24  # Using the original size of the icon
            icon_x = option.rect.left() + 5  # X position with a small offset to the left
            icon_y = option.rect.top() + (option.rect.height() - icon_size) // 2  # Centered Y position

            icon_rect = QRect(int(icon_x), int(icon_y), icon_size, icon_size)
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setWidth(size.width() + 30)  # Add extra width for the icon
        return size

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Garante que o alinhamento centralizado seja aplicado
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

class AddItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.database_path = Path(CONTROLE_DADOS)
        self.setWindowTitle("Adicionar Item")
        self.setFixedSize(900, 250)

        self.layout = QVBoxLayout(self)
        self.setup_ui()
        self.load_sigla_om()

    def setup_ui(self):
        self.tipo_cb, self.numero_le, self.ano_le = self.setup_first_line()
        self.objeto_le = self.setup_third_line()
        self.nup_le, self.sigla_om_cb = self.setup_fourth_line()
        self.material_radio, self.servico_radio = self.setup_fifth_line()
        self.setup_save_button()

    def setup_first_line(self):
        hlayout = QHBoxLayout()
        tipo_cb = QComboBox()
        numero_le = QLineEdit()
        ano_le = QLineEdit()

        [tipo_cb.addItem(option[0]) for option in [("Dispensa Eletrônica (DE)", "Dispensa Eletrônica")]]
        tipo_cb.setCurrentText("Dispensa Eletrônica (DE)")
        numero_le.setValidator(QIntValidator(1, 99999))
        ano_le.setValidator(QIntValidator(1000, 9999))
        ano_le.setText(str(datetime.now().year))

        hlayout.addWidget(QLabel("Tipo:"))
        hlayout.addWidget(tipo_cb)
        hlayout.addWidget(QLabel("Número:"))
        hlayout.addWidget(numero_le)
        hlayout.addWidget(QLabel("Ano:"))
        hlayout.addWidget(ano_le)
        self.layout.addLayout(hlayout)

        return tipo_cb, numero_le, ano_le

    def setup_third_line(self):
        hlayout = QHBoxLayout()
        objeto_le = QLineEdit()
        objeto_le.setPlaceholderText("Exemplo: 'Material de Limpeza' (Utilizar no máximo 3 palavras)")
        hlayout.addWidget(QLabel("Objeto:"))
        hlayout.addWidget(objeto_le)
        self.layout.addLayout(hlayout)
        return objeto_le

    def setup_fourth_line(self):
        hlayout = QHBoxLayout()
        nup_le = QLineEdit()
        sigla_om_cb = QComboBox()
        nup_le.setPlaceholderText("Exemplo: '00000.00000/0000-00'")
        hlayout.addWidget(QLabel("Nup:"))
        hlayout.addWidget(nup_le)
        hlayout.addWidget(QLabel("OM:"))
        hlayout.addWidget(sigla_om_cb)
        self.layout.addLayout(hlayout)
        return nup_le, sigla_om_cb

    def setup_fifth_line(self):
        hlayout = QHBoxLayout()
        material_radio = QRadioButton("Material")
        servico_radio = QRadioButton("Serviço")
        group = QButtonGroup(self)
        group.addButton(material_radio)
        group.addButton(servico_radio)
        material_radio.setChecked(True)

        hlayout.addWidget(QLabel("Material/Serviço:"))
        hlayout.addWidget(material_radio)
        hlayout.addWidget(servico_radio)
        self.layout.addLayout(hlayout)
        return material_radio, servico_radio

    def setup_save_button(self):
        btn = QPushButton("Adicionar Item")
        btn.clicked.connect(self.on_save)
        self.layout.addWidget(btn)

    def on_save(self):
        if self.check_id_exists():
            res = QMessageBox.question(self, "Confirmação", "ID do processo já existe. Deseja sobrescrever?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if res == QMessageBox.StandardButton.Yes:
                self.accept()  # Substitui o diálogo aceitar com a sobreposição
        else:
            self.accept()  # Aceita normalmente se o ID do processo não existir

    def check_id_exists(self):
        id_processo = f"{self.tipo_cb.currentText()} {self.numero_le.text()}/{self.ano_le.text()}"
        query = f"SELECT COUNT(*) FROM controle_dispensas WHERE id_processo = ?"
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute(query, (id_processo,))
        exists = cursor.fetchone()[0] > 0
        conn.close()
        return exists

    def load_next_numero(self):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(numero) FROM controle_dispensas")
                max_number = cursor.fetchone()[0]
                next_number = 1 if max_number is None else int(max_number) + 1
                self.numero_le.setText(str(next_number))
        except Exception as e:
            print(f"Erro ao carregar o próximo número: {e}")

    def get_data(self):
        sigla_selected = self.sigla_om_cb.currentText()
        material_servico = "Material" if self.material_radio.isChecked() else "Serviço"
        tipo_de_processo = self.tipo_cb.currentText()
        
        data = {
            'tipo': tipo_de_processo,  # Este é o texto visível no ComboBox
            'numero': self.numero_le.text(),
            'ano': self.ano_le.text(),
            'nup': self.nup_le.text(),
            'objeto': self.objeto_le.text(),
            'sigla_om': sigla_selected,
            'orgao_responsavel': self.om_details[sigla_selected]['orgao_responsavel'],
            'uasg': self.om_details[sigla_selected]['uasg'],
            'material_servico': material_servico
        }

        # Utilize um único mapa que combina os dois propósitos, se possível
        # Isso mapeia o tipo visível para seu código abreviado e nome no banco de dados
        tipo_map = {
            "Dispensa Eletrônica (DE)": ("DE", "Dispensa Eletrônica"),
        }

        # Se o tipo de processo está no mapa, use a abreviação e o nome interno; caso contrário, use valores padrão
        if tipo_de_processo in tipo_map:
            abreviatura, nome_interno = tipo_map[tipo_de_processo]
            data['tipo'] = nome_interno
            data['id_processo'] = f"{abreviatura} {data['numero']}/{data['ano']}"
        else:
            data['tipo'] = "Tipo Desconhecido"  # ou algum valor padrão
            data['id_processo'] = f"Desconhecido {data['numero']}/{data['ano']}"

        return data

    def import_uasg_to_db(self, filepath):
        # Ler os dados do arquivo Excel
        df = pd.read_excel(filepath, usecols=['uasg', 'orgao_responsavel', 'sigla_om'])
        
        # Conectar ao banco de dados e criar a tabela se não existir
        with sqlite3.connect(self.database_path) as conn:
            df.to_sql('controle_om', conn, if_exists='replace', index=False)  # Use 'replace' para substituir ou 'append' para adicionar

    def load_sigla_om(self):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT sigla_om, orgao_responsavel, uasg FROM controle_om ORDER BY sigla_om")
                self.om_details = {}
                self.sigla_om_cb.clear()
                ceimbra_found = False  # Variável para verificar se CeIMBra está presente
                default_index = 0  # Índice padrão se CeIMBra não for encontrado

                for index, row in enumerate(cursor.fetchall()):
                    sigla, orgao, uasg = row
                    self.sigla_om_cb.addItem(sigla)
                    self.om_details[sigla] = {"orgao_responsavel": orgao, "uasg": uasg}
                    if sigla == "CeIMBra":
                        ceimbra_found = True
                        default_index = index  # Atualiza o índice para CeIMBra se encontrado

                if ceimbra_found:
                    self.sigla_om_cb.setCurrentIndex(default_index)  # Define CeIMBra como valor padrão
        except Exception as e:
            print(f"Erro ao carregar siglas de OM: {e}")

class Dialogs:
    @staticmethod
    def info(parent, title, message):
        QMessageBox.information(parent, title, message)

    @staticmethod
    def warning(parent, title, message):
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def error(parent, title, message):
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def confirm(parent, title, message):
        reply = QMessageBox.question(parent, title, message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

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
            "Editar Dados do Processo",
            "1. Autorização para Abertura de Processo",
            "2. Documentos de Planejamento",
            "3. Aviso de Dispensa Eletrônica",
        ]
        for actionText in actions:
            action = QAction(actionText, self)
            action.triggered.connect(partial(self.trigger_action, actionText))
            self.addAction(action)

    def trigger_action(self, actionText):
        if self.index.isValid():
            source_index = self.model.mapToSource(self.index)
            # Assumindo que a chave primária é a primeira coluna do modelo
            id_processo = self.model.data(self.model.index(source_index.row(), 0))  
            df_registro_selecionado = carregar_dados_dispensa(id_processo, str(self.main_app.database_path))
            if not df_registro_selecionado.empty:
                self.perform_action(actionText, df_registro_selecionado)
            else:
                QMessageBox.warning(self, "Atenção", "Nenhum registro selecionado ou dados não encontrados.")


    def perform_action(self, actionText, df_registro_selecionado):
        actions = {
            "Editar Dados do Processo": self.editar_dados,
            "1. Autorização para Abertura de Processo": self.AutorizacaoDispensa,
            "2. Documentos de Planejamento": self.DocumentosPlanejamento,
            "3. Aviso de Dispensa Eletrônica": self.AvisoDispensaEletronica
        }
        action = actions.get(actionText)
        if action:
            action(df_registro_selecionado)

    def editar_dados(self, df_registro_selecionado):
        dialog = EditDataDialog(df_registro_selecionado, self.main_app.icons_dir)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.main_app.refresh_model()

    def AutorizacaoDispensa(self, df_registro_selecionado):
        pass

    def DocumentosPlanejamento(self, df_registro_selecionado):
        pass

    def AvisoDispensaEletronica(self, df_registro_selecionado):
        pass

class EditDataDialog(QDialog):
    def __init__(self, df_registro_selecionado, icons_dir, parent=None):
        super().__init__(parent)
        self.df_registro_selecionado = df_registro_selecionado
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        self.setWindowTitle("Editar Dados do Processo")
        self.setGeometry(300, 300, 900, 700)

        self.layout = QVBoxLayout(self)
        self.setup_frames()
        self.setLayout(self.layout)

    def setup_frames(self):
        # Criar QHBoxLayouts para organizar os frames horizontalmente
        self.topRow = QHBoxLayout()
        self.bottomRow = QHBoxLayout()
        
        # Criar QFrames
        self.frame1 = self.create_frame("Dados Gerais")
        self.frame2 = self.create_frame("Detalhes Financeiros")
        self.frame3 = self.create_frame("Comentários e Links")
        
        # Adicionar frames às linhas
        self.topRow.addWidget(self.frame1)
        self.topRow.addWidget(self.frame2)
        self.bottomRow.addWidget(self.frame3)
        
        # Adicionar QHBoxLayouts ao layout principal
        self.layout.addLayout(self.topRow)
        self.layout.addLayout(self.bottomRow)

        # Preencher cada frame com campos apropriados
        self.fill_frame1()
        self.fill_frame2()
        self.fill_frame3()

        # Adicionar botões de Salvar e Cancelar no final do layout
        self.add_action_buttons()

    def create_frame(self, title):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QFrame.Shadow.Raised)
        frame_layout = QVBoxLayout(frame)
        frame_label = QLabel(title)
        frame_layout.addWidget(frame_label)
        return frame

    def fill_frame1(self):
        # Suponha que 'frame1' contenha campos gerais como nome, data e ID
        self.add_label_line_edit(self.frame1.layout(), "Nome", "nome")
        self.add_date_edit(self.frame1.layout(), "Data de Início", "data_inicio")

    def fill_frame2(self):
        # Suponha que 'frame2' contenha detalhes financeiros
        self.add_label_line_edit(self.frame2.layout(), "Valor", "valor_total")
        self.add_label_line_edit(self.frame2.layout(), "Custo Adicional", "custo_adicional")

    def fill_frame3(self):
        # Suponha que 'frame3' contenha comentários e links
        self.add_label_line_edit(self.frame3.layout(), "Link do Documento", "link_documento")
        self.add_label_line_edit(self.frame3.layout(), "Comentários", "comentarios")

    def add_label_line_edit(self, layout, label_text, data_key):
        label = QLabel(label_text)
        line_edit = QLineEdit()
        line_edit.setText(str(self.df_registro_selecionado.get(data_key, "")))
        layout.addWidget(label)
        layout.addWidget(line_edit)

    def add_date_edit(self, layout, label_text, data_key):
        label = QLabel(label_text)
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_str = self.df_registro_selecionado.get(data_key, "")
        date = QDate.fromString(date_str, "yyyy-MM-dd") if date_str else QDate.currentDate()
        date_edit.setDate(date)
        layout.addWidget(label)
        layout.addWidget(date_edit)

    def add_action_buttons(self):
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.save_changes)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        self.layout.addWidget(save_button)
        self.layout.addWidget(cancel_button)

    def setup_ui(self):
        self.titleLabel = QLabel("Editar Dados")
        self.titleLabel.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        self.layout.addWidget(self.titleLabel)
        
        # Criar campos de entrada para cada coluna no DataFrame
        for column in self.df_registro_selecionado.columns:
            if "data" in column:  # Se a coluna representar uma data
                label = QLabel(column)
                date_edit = QDateEdit()
                date_edit.setCalendarPopup(True)
                try:
                    date_value = QDate.fromString(self.df_registro_selecionado.iloc[0][column], "yyyy-MM-dd")
                    date_edit.setDate(date_value)
                except:
                    date_edit.setDate(QDate.currentDate())
                self.date_inputs[column] = date_edit
                self.layout.addWidget(label)
                self.layout.addWidget(date_edit)
            else:
                label = QLabel(column)
                line_edit = QLineEdit()
                line_edit.setText(str(self.df_registro_selecionado.iloc[0][column]))
                self.inputs[column] = line_edit
                self.layout.addWidget(label)
                self.layout.addWidget(line_edit)

        # Adiciona botões de Salvar e Cancelar
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.save_changes)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)

        self.layout.addWidget(save_button)
        self.layout.addWidget(cancel_button)

    def save_changes(self):
        # Atualiza o DataFrame com as novas entradas e salva no banco de dados
        try:
            updated_values = {}
            for column, input_field in self.inputs.items():
                updated_values[column] = input_field.text()
            for column, date_field in self.date_inputs.items():
                updated_values[column] = date_field.date().toString("yyyy-MM-dd")
            
            connection = sqlite3.connect("path_to_your_database.db")
            cursor = connection.cursor()
            set_part = ', '.join([f"{key} = ?" for key in updated_values.keys()])
            values = list(updated_values.values())
            values.append(self.df_registro_selecionado.iloc[0]['id'])  # Assume 'id' as primary key
            cursor.execute(f"UPDATE your_table_name SET {set_part} WHERE id = ?", values)
            connection.commit()
            connection.close()
            
            self.accept()  # Fecha o diálogo com sucesso
            QMessageBox.information(self, "Sucesso", "Dados atualizados com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar as alterações: {str(e)}")
            self.reject()  # Fecha o diálogo com falha
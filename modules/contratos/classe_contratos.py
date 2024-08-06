## Módulo incluido em modules/contratos/classe_contratos.py ##

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
from database.utils.treeview_utils import load_images, create_button
from modules.contratos.utils import ExportThread, ColorDelegate, carregar_dados_contratos, Dialogs
from modules.contratos.database_manager import SqlModel, DatabaseContratosManager, CustomTableView
from modules.contratos.gerenciar_inclusao_exclusao import GerenciarInclusaoExclusaoContratos
import pandas as pd
import os
import subprocess
import logging
import sqlite3

class ContratosWidget(QMainWindow):
    dataUpdated = pyqtSignal()

    def __init__(self, icons_dir, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(icons_dir) if icons_dir else Path()
        self.required_columns = [
            'status', 'dias', 'pode_renovar', 'custeio', 'numero_contrato', 'tipo', 'id_processo', 'empresa', 'objeto',
            'valor_global', 'uasg', 'nup', 'cnpj', 'natureza_continuada', 'om', 'material_servico', 'link_pncp',
            'portaria', 'posto_gestor', 'gestor', 'posto_gestor_substituto', 'gestor_substituto', 'posto_fiscal',
            'fiscal', 'posto_fiscal_substituto', 'fiscal_substituto', 'posto_fiscal_administrativo', 'fiscal_administrativo',
            'vigencia_inicial', 'vigencia_final', 'setor', 'cp', 'msg', 'comentarios', 'termo_aditivo', 'atualizacao_comprasnet',
            'instancia_governanca', 'comprasnet_contratos', 'registro_status'
        ]
        self.setup_managers()
        self.load_initial_data()
        self.model = self.init_model()
        self.ui_manager = UIManager(self, self.icons_dir, self.config_manager, self.model)
        self.setup_ui()
        self.export_thread = None
        self.output_path = os.path.join(os.getcwd(), "controle_contratos.xlsx")
        self.dataUpdated.connect(self.refresh_model)
        self.refresh_model()

    def init_model(self):
        sql_model = SqlModel(self.database_manager, self)
        return sql_model.setup_model("controle_contratos", editable=True)

    def setup_managers(self):
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = Path(load_config("CONTROLE_CONTRATOS_DADOS", str(CONTROLE_CONTRATOS_DADOS)))
        self.database_om_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseContratosManager(self.database_path)

    def carregar_tabela(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.xls *.ods *.csv)")
        if filepath:
            try:
                if filepath.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)
                self.validate_and_process_data(df)
                df['status'] = 'Minuta'

                with self.database_manager as conn:
                    DatabaseContratosManager.create_table_controle_contratos(conn)

                self.database_manager.save_dataframe(df, 'controle_contratos')
                Dialogs.info(self, "Carregamento concluído", "Dados carregados com sucesso.")
            except Exception as e:
                logging.error("Erro ao carregar tabela: %s", e)
                Dialogs.warning(self, "Erro ao carregar", str(e))

    def refresh_model(self):
        self.model.select()

    def setup_ui(self):
        self.setCentralWidget(self.ui_manager.main_widget)

    def load_initial_data(self):
        self.image_cache = load_images(self.icons_dir, ["plus.png", "import_de.png", "save_to_drive.png", "loading.png", "delete.png", "excel.png", "calendar.png", "report.png", "management.png"])

    def gerenciar_itens(self):
        # Encerrar conexões existentes antes de abrir o diálogo
        self.close_database_connections()

        dialog = GerenciarInclusaoExclusaoContratos(self.database_path, self)
        dialog.exec()

    def close_database_connections(self):
        self.database_manager.close_connection()
        source_model = self.ui_manager.table_view.model().sourceModel()
        if hasattr(source_model, 'database_manager'):
            source_model.database_manager.close_connection()

    def salvar_tabela(self):
        self.export_thread = ExportThread(self.model, self.output_path)
        self.export_thread.finished.connect(self.handle_export_finished)
        self.export_thread.start()

    def handle_export_finished(self, message):
        if 'successfully' in message:
            Dialogs.info(self, "Exportação de Dados", "Dados exportados com sucesso!")
            subprocess.run(f'start excel.exe "{self.output_path}"', shell=True, check=True)
        else:
            Dialogs.warning(self, "Exportação de Dados", message)

    def validate_and_process_data(self, df):
        try:
            self.validate_columns(df)
            self.add_missing_columns(df)
            self.salvar_detalhes_uasg_sigla_nome(df)
        except ValueError as e:
            Dialogs.warning(self, "Erro de Validação", str(e))
        except Exception as e:
            Dialogs.error(self, "Erro Inesperado", str(e))

    def validate_columns(self, df):
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colunas obrigatórias faltando: {', '.join(missing_columns)}")

    def add_missing_columns(self, df):
        for col in self.required_columns:
            if col not in df.columns:
                df[col] = ""

    def salvar_detalhes_uasg_sigla_nome(self, df):
        with sqlite3.connect(self.database_om_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uasg, sigla_om, orgao_responsavel FROM controle_om")
            om_details = {row[0]: {'sigla_om': row[1], 'orgao_responsavel': row[2]} for row in cursor.fetchall()}
        df['sigla_om'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('sigla_om', ''))
        df['orgao_responsavel'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('orgao_responsavel', ''))

class UIManager:
    def __init__(self, parent, icons, config_manager, model):
        self.parent = parent
        self.icons_dir = icons
        self.config_manager = config_manager
        self.model = model
        self.main_widget = QWidget(parent)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.button_manager = ButtonManager(self.parent)
        self.init_ui()

    def init_ui(self):
        self.setup_search_bar()
        self.setup_table_view()
        self.setup_buttons_layout()
        self.parent.setCentralWidget(self.main_widget)

    def setup_search_bar(self):
        self.search_bar = QLineEdit(self.parent)
        self.search_bar.setPlaceholderText("Digite para buscar...")
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

        dias_index = self.model.fieldIndex("dias")
        status_index = self.model.fieldIndex("status")

        self.table_view.setItemDelegateForColumn(dias_index, ColorDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(status_index, CustomItemDelegate(self.icons_dir, self.table_view))

    def configure_table_model(self):
        self.parent.proxy_model = QSortFilterProxyModel(self.parent)
        self.parent.proxy_model.setSourceModel(self.model)
        self.parent.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.parent.proxy_model.setFilterKeyColumn(-1)
        self.parent.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)
        self.table_view.setModel(self.parent.proxy_model)
        print("Table view configured with proxy model")

        self.model.dataChanged.connect(self.table_view.update)

        if self.table_view.selectionModel():
            self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
            self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        self.update_column_headers()
        self.hide_unwanted_columns()

    def adjust_columns(self):
        self.table_view.resizeColumnsToContents()
        QTimer.singleShot(1, self.apply_custom_column_sizes)

    def apply_custom_column_sizes(self):
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 70)
        header.resizeSection(1, 50)
        header.resizeSection(2, 65)
        header.resizeSection(3, 65)
        header.resizeSection(4, 130)
        header.resizeSection(5, 75)
        header.resizeSection(6, 90)
        header.resizeSection(7, 150)
        header.resizeSection(8, 170)
        header.resizeSection(9, 125)

    def apply_custom_style(self):
        self.table_view.setStyleSheet("""
            QTableView {
                font-size: 14px;
            }
            QTableView::section {
                font-size: 14px;
            }
            QHeaderView::section:horizontal {
                font-size: 14px;
            }
            QHeaderView::section:vertical {
                font-size: 14px;
            }
        """)

    def linhaSelecionada(self, selected, deselected):
        if selected.indexes():
            proxy_index = selected.indexes()[0]
            source_index = self.parent.proxy_model.mapToSource(proxy_index)
            df_registro_selecionado = carregar_dados_contratos(source_index.row(), self.parent.database_path)
            if not df_registro_selecionado.empty:
                logging.debug(f"Registro selecionado: {df_registro_selecionado.iloc[0].to_dict()}")
            else:
                logging.warning("Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")
                QMessageBox.warning(self.parent, "Erro", "Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")

    def update_column_headers(self):
        titles = {
            0: "Status",
            1: "Dias",
            2: "Renova?",
            3: "Custeio?",
            4: "Contrato/Ata",
            5: "Tipo",
            6: "Processo",
            7: "Empresa",
            8: "Objeto",
            9: "Valor"
        }
        for column, title in titles.items():
            self.model.setHeaderData(column, Qt.Orientation.Horizontal, title)

    def reorder_columns(self):
        new_order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        for i, col in enumerate(new_order):
            self.table_view.horizontalHeader().moveSection(self.table_view.horizontalHeader().visualIndex(col), i)

    def hide_unwanted_columns(self):
        visible_columns = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
        for column in range(self.model.columnCount()):
            if column not in visible_columns:
                self.table_view.hideColumn(column)

class ButtonManager:
    def __init__(self, parent):
        self.parent = parent
        self.buttons = []
        self.create_buttons()

    def create_buttons(self):
        button_specs = [
            ("  Adicionar/Excluir Itens", self.parent.image_cache['plus'], self.parent.gerenciar_itens, "Adiciona um novo item ao banco de dados"),
            ("  Abrir Excel", self.parent.image_cache['excel'], self.parent.salvar_tabela, "Salva o dataframe em um arquivo Excel"),
            ("  Importar Tabela", self.parent.image_cache['import_de'], self.parent.carregar_tabela, "Carrega dados de uma tabela"),
        ]
        for text, icon, callback, tooltip in button_specs:
            btn = create_button(text, icon, callback, tooltip, self.parent)
            self.buttons.append(btn)

    def add_buttons_to_layout(self, layout):
        for btn in self.buttons:
            layout.addWidget(btn)

def create_button(text, icon, callback, tooltip_text, parent, icon_size=QSize(25, 25)):
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
            color: white;
            font-size: 14pt;
            min-height: 26px;
            padding: 5px;      
        }
        QPushButton:hover {
            background-color: white;
            color: black;
        }

    """)
    return btn

class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, icons, parent=None):
        super().__init__(parent)
        self.icons = icons

    def paint(self, painter, option, index):
        value = index.data(Qt.ItemDataRole.DecorationRole)
        if value:
            icon = value
            icon.paint(painter, option.rect, Qt.AlignmentFlag.AlignCenter)
        else:
            super().paint(painter, option, index)


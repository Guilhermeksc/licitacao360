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
from modules.contratos.treeview_atas import TreeViewAtasDialog
from modules.contratos.treeview_contratos import TreeViewContratosDialog
from modules.contratos.msg.msg_alerta_prazo import MensagemDialog
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
            'valor_global', 'uasg', 'nup', 'cnpj', 'natureza_continuada', 'om', 'indicativo_om', 'om_extenso', 'material_servico', 'link_pncp',
            'portaria', 'posto_gestor', 'gestor', 'posto_gestor_substituto', 'gestor_substituto', 'posto_fiscal',
            'fiscal', 'posto_fiscal_substituto', 'fiscal_substituto', 'posto_fiscal_administrativo', 'fiscal_administrativo',
            'vigencia_inicial', 'vigencia_final', 'setor', 'cp', 'msg', 'comentarios', 'registro_staus','termo_aditivo', 'atualizacao_comprasnet',
            'instancia_governanca', 'comprasnet_contratos', 'assinatura_contrato', 'atualizacao_comprasnet'
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
        sql_model = SqlModel(self.icons_dir, self.database_manager, self)
        return sql_model.setup_model("controle_contratos", editable=True)

    def setup_managers(self):
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = Path(load_config("CONTROLE_CONTRATOS_DADOS", str(CONTROLE_CONTRATOS_DADOS)))
        self.database_om_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseContratosManager(self.database_path)

    def refresh_model(self):
        self.model.sourceModel().select()

    def setup_ui(self):
        self.setCentralWidget(self.ui_manager.main_widget)

    def load_initial_data(self):
        self.image_cache = load_images(self.icons_dir, ["production.png", "production_red.png", "website_menu.png", "import_de.png", "save_to_drive.png", "loading.png", "delete.png", "excel.png", "calendar.png", "report.png", "management.png"])

    def show_mensagem_dialog(self):
        selected_index = self.ui_manager.table_view.selectionModel().currentIndex()
        source_index = self.proxy_model.mapToSource(selected_index)
        
        # Obtém os dados diretamente do modelo usando o índice da linha
        row_data = {}
        for column in range(self.model.columnCount()):
            header = self.model.headerData(column, Qt.Orientation.Horizontal)
            value = self.model.data(self.model.index(source_index.row(), column))
            row_data[header] = value
        
        # Converte os dados da linha selecionada em um DataFrame
        df_registro_selecionado = pd.DataFrame([row_data])
        
        # Print do DataFrame completo para depuração
        print(f"[DEBUG] - DataFrame completo:\n{df_registro_selecionado}")

        indice_linha = source_index.row()
        print(f"[DEBUG] - Indice da linha selecionada: {indice_linha}")  # Depuração

        if df_registro_selecionado is not None and not df_registro_selecionado.empty:
            dialog = MensagemDialog(df_registro_selecionado, self.icons_dir, indice_linha, self)
            dialog.exec()


    def gerenciar_itens(self):
        # Encerrar conexões existentes antes de abrir o diálogo
        self.close_database_connections()
        dialog = GerenciarInclusaoExclusaoContratos(self.icons_dir, self.database_path, self)
        dialog.exec()

    def treeview_atas(self):
        self.close_database_connections()
        dialog = TreeViewAtasDialog(self.database_path, self)
        dialog.exec()

    def treeview_contratos(self):
        self.close_database_connections()
        dialog = TreeViewContratosDialog(self.database_path, self)
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
        self.setup_search_bar_and_buttons()
        self.setup_table_view()
        self.parent.setCentralWidget(self.main_widget)

    def setup_search_bar_and_buttons(self):
        search_layout = QHBoxLayout()
        
        # Adicionar texto "Localizar:"
        search_label = QLabel("Localizar:")
        search_label.setStyleSheet("font-size: 14px;")
        search_layout.addWidget(search_label)
        
        # Adicionar barra de pesquisa
        self.search_bar = QLineEdit(self.parent)
        self.search_bar.setPlaceholderText("Digite para buscar...")
        self.search_bar.setStyleSheet("font-size: 14px;")
        search_layout.addWidget(self.search_bar)
        
        def handle_text_change(text):
            regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.parent.proxy_model.setFilterRegularExpression(regex)
        
        self.search_bar.textChanged.connect(handle_text_change)

        # Adicionar layout de botões na mesma linha da barra de pesquisa
        self.setup_buttons_layout(search_layout)
        self.main_layout.addLayout(search_layout)

    def setup_buttons_layout(self, parent_layout):
        self.buttons_layout = QHBoxLayout()
        self.button_manager.add_buttons_to_layout(self.buttons_layout)
        parent_layout.addLayout(self.buttons_layout)
        for i in range(self.buttons_layout.count()):
            widget = self.buttons_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setStyleSheet("font-size: 14px; min-width: 120px; min-height: 20px; max-width: 120px; max-height: 20px;")

    def setup_table_view(self):
        self.table_view = CustomTableView(main_app=self.parent, config_manager=self.config_manager, parent=self.main_widget)
        self.table_view.setModel(self.model)
        self.main_layout.addWidget(self.table_view)
        self.configure_table_model()
        self.table_view.verticalHeader().setVisible(False)
        self.adjust_columns()
        self.apply_custom_style()

        center_delegate = CenterAlignDelegate(self.table_view)
        for column in range(self.model.sourceModel().columnCount()):
            self.table_view.setItemDelegateForColumn(column, center_delegate)

        dias_index = self.model.sourceModel().fieldIndex("dias")
        status_index = self.model.sourceModel().fieldIndex("status")

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
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 70)
        header.resizeSection(1, 50)
        header.resizeSection(2, 65)
        header.resizeSection(3, 65)
        header.resizeSection(5, 75)
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
            ("  Mensagem", self.parent.image_cache['report'], self.parent.show_mensagem_dialog, "Enviar a mensagem de alerta entre outras"),
            ("  Atas", self.parent.image_cache['production'], self.parent.treeview_atas, "Abre a janela de visualização de atas"),
            ("  Contratos", self.parent.image_cache['production'], self.parent.treeview_contratos, "Abre a janela de visualização de contratos"),
            ("  Alterar Dados", self.parent.image_cache['website_menu'], self.parent.gerenciar_itens, "Adiciona um novo item ao banco de dados"),
            ("  Abrir Tabela", self.parent.image_cache['excel'], self.parent.salvar_tabela, "Salva o dataframe em um arquivo Excel"),
        ]
        for text, icon, callback, tooltip in button_specs:
            btn = create_button(text, icon, callback, tooltip, self.parent)
            self.buttons.append(btn)

    def add_buttons_to_layout(self, layout):
        for btn in self.buttons:
            layout.addWidget(btn)

def create_button(text, icon, callback, tooltip_text, parent, icon_size=QSize(30, 30)):
    btn = QPushButton(text, parent)
    if icon:
        btn.setIcon(QIcon(icon))
        btn.setIconSize(icon_size)
    if callback:
        btn.clicked.connect(callback)
    if tooltip_text:
        btn.setToolTip(tooltip_text)
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


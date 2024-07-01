from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
from database.utils.treeview_utils import load_images, create_button
from modules.planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_pregao, carregar_dados_dispensa
from modules.dispensa_eletronica.utilidades_dispensa_eletronica import ExportThread
from modules.dispensa_eletronica.sql_model import SqlModel, CustomTableView
from modules.dispensa_eletronica.add_item import AddItemDialog
import pandas as pd
import os
import subprocess
import logging
import sqlite3

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

    def setup_managers(self):
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        self.event_manager = EventManager()

    def refresh_model(self):
        self.model.select()

    def setup_ui(self):
        self.setCentralWidget(self.ui_manager.main_widget)

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
            # Add 'situacao' before saving
            item_data['situacao'] = 'Planejamento'
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
        self.export_thread = ExportThread(self.model, self.output_path)
        self.export_thread.finished.connect(self.handle_export_finished)
        self.export_thread.start()

    def handle_export_finished(self, message):
        if 'successfully' in message:
            Dialogs.info(self, "Exportação de Dados", "Dados exportados com sucesso!")
            subprocess.run(f'start excel.exe "{self.output_path}"', shell=True, check=True)
        else:
            Dialogs.warning(self, "Exportação de Dados", message)

    def carregar_tabela(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.xls *.ods)")
        if filepath:
            try:
                df = pd.read_excel(filepath)
                self.validate_and_process_data(df)
                df['situacao'] = 'Planejamento'
                self.save_to_database(df)
                Dialogs.info(self, "Carregamento concluído", "Dados carregados com sucesso.")
            except Exception as e:
                Dialogs.warning(self, "Erro ao carregar", str(e))

    def validate_and_process_data(self, df):
        required_columns = ['ID Processo', 'NUP', 'Objeto', 'UASG']
        if not all(col in df.columns for col in required_columns):
            missing_columns = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Faltando: {', '.join(missing_columns)}")
        df.rename(columns={'ID Processo': 'id_processo', 'NUP': 'nup', 'Objeto': 'objeto', 'UASG': 'uasg'}, inplace=True)
        self.desmembramento_id_processo(df)
        self.salvar_detalhes_uasg_sigla_nome(df)

    def desmembramento_id_processo(self, df):
        df[['tipo', 'numero', 'ano']] = df['id_processo'].str.extract(r'(\D+)(\d+)/(\d+)')
        df['tipo'] = df['tipo'].map({'DE ': 'Dispensa Eletrônica'}).fillna('Tipo Desconhecido')

    def salvar_detalhes_uasg_sigla_nome(self, df):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uasg, sigla_om, orgao_responsavel FROM controle_om")
            om_details = {row[0]: {'sigla_om': row[1], 'orgao_responsavel': row[2]} for row in cursor.fetchall()}
        df['sigla_om'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('sigla_om', ''))
        df['orgao_responsavel'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('orgao_responsavel', ''))
                
    def save_to_database(self, data, delete=False):
        with self.database_manager as conn:
            cursor = conn.cursor()
            if delete:
                cursor.execute("DELETE FROM controle_dispensas WHERE id_processo = ?", (data['id_processo'],))
            else:
                situacao = 'Planejamento'
                upsert_sql = '''
                INSERT INTO controle_dispensas (
                    id_processo, nup, objeto, uasg, tipo, numero, ano, sigla_om, setor_responsavel, 
                    material_servico, orgao_responsavel, situacao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id_processo) DO UPDATE SET
                    nup=excluded.nup,
                    objeto=excluded.objeto,
                    uasg=excluded.uasg,
                    tipo=excluded.tipo,
                    numero=excluded.numero,
                    ano=excluded.ano,
                    sigla_om=excluded.sigla_om,
                    setor_responsavel=excluded.setor_responsavel,
                    material_servico=excluded.material_servico,
                    orgao_responsavel=excluded.orgao_responsavel,
                    situacao=excluded.situacao;
                '''
                if isinstance(data, pd.DataFrame):
                    data['situacao'] = situacao
                    for _, row in data.iterrows():
                        cursor.execute(upsert_sql, (
                            row['id_processo'], row['nup'], row['objeto'], row['uasg'],
                            row.get('tipo', ''), row.get('numero', ''), row.get('ano', ''),
                            row.get('sigla_om', ''), row.get('setor_responsavel', ''), 
                            row.get('material_servico', ''), row.get('orgao_responsavel', ''),
                            row['situacao']
                        ))
                else:
                    data['situacao'] = situacao
                    cursor.execute(upsert_sql, (
                        data['id_processo'], data['nup'], data['objeto'], data['uasg'],
                        data['tipo'], data['numero'], data['ano'],
                        data['sigla_om'], data.get('setor_responsavel', ''), 
                        data['material_servico'], data['orgao_responsavel'], data['situacao']
                    ))
            conn.commit()
        self.dataUpdated.emit()


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
        header.setSectionResizeMode(17, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(12, QHeaderView.ResizeMode.Fixed) 
        # Definir tamanhos específicos onde necessário
        header.resizeSection(0, 140)
        header.resizeSection(4, 175)
        header.resizeSection(8, 70)
        header.resizeSection(10, 100)
        header.resizeSection(17, 230)
        header.resizeSection(12, 180)

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
        visible_columns = {0, 4, 5, 8, 10, 17, 12}
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
            ("  Adicionar", self.parent.image_cache['plus'], self.parent.on_add_item, "Adiciona um novo item ao banco de dados"),
            ("  Salvar", self.parent.image_cache['excel'], self.parent.salvar_tabela, "Salva o dataframe em um arquivo Excel"),
            ("  Importar", self.parent.image_cache['import_de'], self.parent.carregar_tabela, "Carrega dados de uma tabela"),
            ("  Excluir", self.parent.image_cache['delete'], self.parent.excluir_linha, "Exclui um item selecionado"),
            ("  Controle de PDM", self.parent.image_cache['calendar'], self.parent.teste, "Abre o painel de controle do processo"),
        ]
        for text, icon, callback, tooltip in button_specs:
            btn = create_button(text, icon, callback, tooltip, self.parent)
            self.buttons.append(btn)

    def add_buttons_to_layout(self, layout):
        for btn in self.buttons:
            layout.addWidget(btn)

def create_button(text, icon, callback, tooltip_text, parent, icon_size=QSize(40, 40)):
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

class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, icons, parent=None):
        super().__init__(parent)
        self.icons = icons

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        status = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        icon = self.icons.get(status, None)
        if icon:
            icon_size = 24
            icon_x = option.rect.left() + 5
            icon_y = option.rect.top() + (option.rect.height() - icon_size) // 2
            icon_rect = QRect(int(icon_x), int(icon_y), icon_size, icon_size)
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setWidth(size.width() + 30)
        return size

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

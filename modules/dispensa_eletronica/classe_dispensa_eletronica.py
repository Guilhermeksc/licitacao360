from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from pathlib import Path
from diretorios import *
from database.utils.treeview_utils import load_images, create_button
# from modules.dispensa_eletronica.utilidades_dispensa_eletronica import save_dataframe_to_excel
from modules.planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_pregao
import pandas as pd
import os
import psutil
import subprocess
df_uasg = pd.read_excel(TABELA_UASG_DIR)
global df_registro_selecionado
df_registro_selecionado = None
from functools import partial
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel
from datetime import datetime
import logging
import sqlite3

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

class TableMenu(QMenu):
    def __init__(self, main_app, index, model=None, config_manager=None):
        super().__init__()
        self.main_app = main_app
        self.index = index
        self.config_manager = config_manager 
        self.model = model

        # Configuração do estilo do menu
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

        # Opções do menu principal
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

    def trigger_sub_action(self, funcao):
        if self.index.isValid():
            source_index = self.model.mapToSource(self.index)
            selected_row = source_index.row()
            df_registro_selecionado = carregar_dados_pregao(selected_row, str(self.main_app.database_path))
            if not df_registro_selecionado.empty:
                funcao(df_registro_selecionado)
            else:
                QMessageBox.warning(self, "Atenção", "Dados não encontrados.")

    def trigger_action(self, actionText):
        if self.index.isValid():
            if isinstance(self.model, QSortFilterProxyModel):
                source_index = self.model.mapToSource(self.index)
            else:
                source_index = self.index
            
            selected_row = source_index.row()
            df_registro_selecionado = carregar_dados_pregao(selected_row, str(self.main_app.database_path))                                    
            if not df_registro_selecionado.empty:
                if actionText == "Editar Dados do Processo":
                    self.editar_dados(df_registro_selecionado)
                elif actionText == "1. Autorização para Abertura de Processo":
                    self.AutorizacaoDispensa(df_registro_selecionado)
                elif actionText == "2. Documentos de Planejamento":
                    self.DocumentosPlanejamento(df_registro_selecionado)
                elif actionText == "3. Aviso de Dispensa Eletrônica":
                    self.AvisoDispensaEletronica(df_registro_selecionado)
            else:
                QMessageBox.warning(self, "Atenção", "Nenhum registro selecionado ou dados não encontrados.")
        else:
            QMessageBox.warning(self, "Atenção", "Nenhuma linha selecionada.")

    def editar_dados(self, df_registro_selecionado):
        pass

    def AutorizacaoDispensa(self, df_registro_selecionado):
        pass

    def DocumentosPlanejamento(self, df_registro_selecionado):
        pass

    def AvisoDispensaEletronica(self, df_registro_selecionado):
        pass

class DispensaEletronicaWidget(QMainWindow):
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
            reply = QMessageBox.question(
                self, 'Confirmar exclusão',
                f"Tem certeza que deseja excluir o registro com ID Processo '{selected_id_processo}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    with self.database_manager as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM controle_dispensas WHERE id_processo = ?", (selected_id_processo,))
                        conn.commit()
                        QMessageBox.information(self, "Sucesso", "Registro excluído com sucesso.")
                        self.init_model()  # Atualizar o modelo
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
        """ Verifica se o arquivo está aberto por algum processo """
        for proc in psutil.process_iter(['pid', 'name', 'open_files']):
            if proc.info['open_files']:
                for fl in proc.info['open_files']:
                    if fl.path == file_path:
                        return True
        return False

    def save_to_database(self, data):
        with self.database_manager as conn:
            cursor = conn.cursor()
            upsert_sql = '''
            INSERT INTO controle_dispensas (id_processo, nup, objeto, uasg, tipo, numero, ano, sigla_om, material_servico, orgao_responsavel)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        self.init_model()

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

    # def on_add_item(self):
    #     dialog = AddItemDialog(self)
    #     if dialog.exec():
    #         item_data = dialog.get_data()
    #         self.save_to_database(item_data)

    # def save_to_database(self, data):
    #     with self.database_manager as conn:
    #         cursor = conn.cursor()
    #         cursor.execute(
    #             '''
    #             INSERT INTO controle_processos (
    #                 tipo, numero, ano, objeto, sigla_om, material_servico, 
    #                 id_processo, nup, orgao_responsavel, uasg) 
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #             ''', (data['tipo'], data['numero'], data['ano'], data['objeto'], 
    #                   data['sigla_om'], data['material_servico'], data['id_processo'], 
    #                   data['nup'], data['orgao_responsavel'], data['uasg'])
    #         )
    #         conn.commit()
    #     self.init_model()

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

class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

def load_and_map_icons(icons_dir):
    icons = {}
    icon_mapping = {
        'Concluído': 'concluido.png',
        'Em recurso': 'alarm.png',
        'Impugnado': 'alert.png',
        'Pré-Publicação': 'arrows.png',
        'Montagem do Processo': 'arrows.png',
        'IRP': 'icon_warning.png'
    }
    print(f"Verificando ícones no diretório: {icons_dir}")
    for status, filename in icon_mapping.items():
        icon_path = Path(icons_dir) / filename
        print(f"Procurando ícone para status '{status}': {icon_path}")
        if icon_path.exists():
            print(f"Ícone encontrado: {filename}")
            pixmap = QPixmap(str(icon_path))
            pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icons[status] = QIcon(pixmap)
        else:
            print(f"Ignore warning: Icon file {filename} not found in {icons_dir}")
    return icons

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

class AddItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.database_path = Path(CONTROLE_DADOS) 
        self.setWindowTitle("Adicionar Item")
        # Definindo o tamanho fixo do diálogo
        self.setFixedSize(900, 250)
        
        # Definindo o tamanho fixo do diálogo através de CSS
        self.setStyleSheet("""
            QDialog, QLabel, QComboBox, QLineEdit, QPushButton, QRadioButton {
                font-size: 14pt;
            }
        """)

        self.layout = QVBoxLayout(self)

        self.options = [
            ("Dispensa Eletrônica (DE)", "Dispensa Eletrônica"),
        ]

        # Linha 1: Tipo, Número, Ano
        hlayout1 = QHBoxLayout()
        self.tipo_cb = QComboBox()
        self.numero_le = QLineEdit()
        self.ano_le = QLineEdit()

        # Carregar o próximo número disponível
        self.load_next_numero()

        [self.tipo_cb.addItem(text) for text, _ in self.options]
        self.tipo_cb.setCurrentText("Dispensa Eletrônica (DE)")  # Valor padrão
        hlayout1.addWidget(QLabel("Tipo:"))
        hlayout1.addWidget(self.tipo_cb)
        
        hlayout1.addWidget(QLabel("Número:"))
        hlayout1.addWidget(self.numero_le)

        # Ano QLineEdit predefinido com o ano atual e validação para quatro dígitos
        
        self.ano_le.setValidator(QIntValidator(1000, 9999))  # Restringe a entrada para quatro dígitos
        current_year = datetime.now().year
        self.ano_le.setText(str(current_year))
        hlayout1.addWidget(QLabel("Ano:"))
        hlayout1.addWidget(self.ano_le)

        self.layout.addLayout(hlayout1)

        # Linha 3: Objeto
        hlayout3 = QHBoxLayout()
        self.objeto_le = QLineEdit()
        hlayout3.addWidget(QLabel("Objeto:"))
        self.objeto_le.setPlaceholderText("Exemplo: 'Material de Limpeza' (Utilizar no máximo 3 palavras)") 
        hlayout3.addWidget(self.objeto_le)
        self.layout.addLayout(hlayout3)

        # Linha 4: OM
        hlayout4 = QHBoxLayout()
        self.nup_le = QLineEdit()
        self.sigla_om_cb = QComboBox()  # Alterado para QComboBox
        hlayout4.addWidget(QLabel("Nup:"))
        self.nup_le.setPlaceholderText("Exemplo: '00000.00000/0000-00'")       
        hlayout4.addWidget(self.nup_le)
        hlayout4.addWidget(QLabel("OM:"))
        hlayout4.addWidget(self.sigla_om_cb)  # Usando QComboBox
        self.layout.addLayout(hlayout4)

        # Linha 5: Material/Serviço
        hlayout5 = QHBoxLayout()
        self.material_servico_group = QButtonGroup(self)  # Grupo para os botões de rádio

        self.material_radio = QRadioButton("Material")
        self.servico_radio = QRadioButton("Serviço")
        self.material_servico_group.addButton(self.material_radio)
        self.material_servico_group.addButton(self.servico_radio)

        hlayout5.addWidget(QLabel("Material/Serviço:"))
        hlayout5.addWidget(self.material_radio)
        hlayout5.addWidget(self.servico_radio)
        self.layout.addLayout(hlayout5)

        # Configurando um valor padrão
        self.material_radio.setChecked(True)

        # Botão de Salvar
        self.save_btn = QPushButton("Adicionar Item")
        self.save_btn.clicked.connect(self.accept)
        self.layout.addWidget(self.save_btn)
        self.load_sigla_om()

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
        data = {
            'tipo': self.tipo_cb.currentText(),
            'numero': self.numero_le.text(),
            'ano': self.ano_le.text(),
            'nup': self.nup_le.text(),
            'objeto': self.objeto_le.text(),
            'sigla_om': sigla_selected,
            'orgao_responsavel': self.om_details[sigla_selected]['orgao_responsavel'],
            'uasg': self.om_details[sigla_selected]['uasg'],
            'material_servico': material_servico
        }

        # Mapeando o tipo para o valor a ser salvo no banco de dados
        type_map = {option[0]: option[1] for option in self.options}
        abrev_map = {
            "Dispensa Eletrônica (DE)": "DE",
        }
        tipo_abreviado = abrev_map[data['tipo']]
        data['tipo'] = type_map[data['tipo']]
        data['id_processo'] = f"{tipo_abreviado} {data['numero']}/{data['ano']}"
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
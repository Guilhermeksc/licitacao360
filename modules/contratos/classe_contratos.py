## Módulo incluido em modules/contratos/classe_contratos.py ##

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
from database.utils.treeview_utils import load_images, create_button
from modules.contratos.utils import ExportThread, ColorDelegate, carregar_dados_contratos
from modules.contratos.database_manager import SqlModel, DatabaseManager, CustomTableView
from modules.contratos.add_item import AddItemDialog
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
        self.setup_managers()
        self.load_initial_data()  # Carregar dados iniciais antes de configurar o UI Manager
        self.model = self.init_model()
        self.ui_manager = UIManager(self, self.icons_dir, self.config_manager, self.model)
        self.setup_ui()
        self.export_thread = None
        self.output_path = os.path.join(os.getcwd(), "controle_contratos.xlsx")
        self.dataUpdated.connect(self.refresh_model)
        self.refresh_model()

    def init_model(self):
        # Inicializa e retorna o modelo SQL utilizando o DatabaseManager
        sql_model = SqlModel(self.database_manager, self)
        return sql_model.setup_model("controle_contratos", editable=True)

    def setup_managers(self):
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = Path(load_config("CONTROLE_CONTRATOS_DADOS", str(CONTROLE_CONTRATOS_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        self.event_manager = EventManager()

    def setup_ui(self):
        self.setCentralWidget(self.ui_manager.main_widget)

    def load_initial_data(self):
        print("Carregando dados iniciais...")
        self.image_cache = load_images(self.icons_dir, [
            "plus.png", "import_de.png", "save_to_drive.png", "loading.png", "delete.png", 
            "excel.png", "calendar.png", "report.png", "management.png"
        ])
        self.selectedIndex = None

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

                # Criar a tabela com a coluna numero_contrato como chave primária
                self.database_manager.create_table_controle_contratos()

                # Salvar o DataFrame na tabela
                self.database_manager.save_dataframe(df, 'controle_contratos')

                Dialogs.info(self, "Carregamento concluído", "Dados carregados com sucesso.")
            except Exception as e:
                Dialogs.warning(self, "Erro ao carregar", str(e))
            finally:
                # Fechar todas as conexões ao banco de dados
                self.database_manager.close_all_connections()

    def excluir_linha(self):
        selection_model = self.ui_manager.table_view.selectionModel()

        if selection_model.hasSelection():
            index_list = selection_model.selectedRows(0)

            if not index_list:
                QMessageBox.warning(self, "Nenhuma Seleção", "Nenhuma linha selecionada.")
                return
            
            selected_numero_contrato = index_list[0].data()
            print(f"Excluindo linha com numero_contrato: {selected_numero_contrato}")

            if Dialogs.confirm(self, 'Confirmar exclusão', f"Tem certeza que deseja excluir o registro com numero_contrato '{selected_numero_contrato}'?"):
                try:
                    self.database_manager.delete_record('controle_contratos', 'numero_contrato', selected_numero_contrato)
                    QMessageBox.information(self, "Sucesso", "Registro excluído com sucesso.")
                    self.refresh_model()  # Atualiza o modelo para refletir as mudanças
                except Exception as e:
                    QMessageBox.warning(self, "Erro ao excluir", f"Erro ao excluir o registro: {str(e)}")
                    print(f"Erro ao excluir o registro: {str(e)}")
        else:
            QMessageBox.warning(self, "Nenhuma Seleção", "Por favor, selecione uma linha para excluir.")

    def refresh_model(self):
        self.model.select()

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
        required_columns = [
            'status', 'dias', 'pode_renovar', 'custeio', 'numero_contrato', 'tipo', 'id_processo',
            'empresa', 'objeto', 'valor_global', 'uasg', 'nup', 'cnpj', 'natureza_continuada', 
            'om', 'material_servico', 'link_pncp', 'portaria', 'posto_gestor', 'gestor', 
            'posto_gestor_substituto', 'gestor_substituto', 'posto_fiscal', 'fiscal', 
            'posto_fiscal_substituto', 'fiscal_substituto', 'posto_fiscal_administrativo', 
            'fiscal_administrativo', 'vigencia_inicial', 'vigencia_final', 'setor', 'cp', 'msg', 
            'comentarios', 'termo_aditivo', 'atualizacao_comprasnet', 'instancia_governanca', 
            'comprasnet_contratos', 'registro_status'
        ]

        if 'numero_contrato' not in df.columns:
            raise ValueError("A coluna 'numero_contrato' é obrigatória e está faltando no DataFrame.")

        for col in required_columns:
            if col not in df.columns:
                df[col] = ""

        self.salvar_detalhes_uasg_sigla_nome(df)

    def salvar_detalhes_uasg_sigla_nome(self, df):
        om_details = {row[0]: {'sigla_om': row[1], 'orgao_responsavel': row[2]} for row in self.database_manager.fetch_query("SELECT uasg, sigla_om, orgao_responsavel FROM controle_om")}
        df['sigla_om'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('sigla_om', ''))
        df['orgao_responsavel'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('orgao_responsavel', ''))

    def on_add_item(self):
        dialog = AddItemDialog(self)
        dialog.itemAdded.connect(self.save_to_database)
        if dialog.exec():
            self.refresh_model()  # Atualiza a interface após adicionar o item

    def save_to_database(self, data, delete=False):
        with self.database_manager as conn:
            cursor = conn.cursor()
            if delete:
                cursor.execute("DELETE FROM controle_contratos WHERE numero_contrato = ?", (data['numero_contrato'],))
            else:
                print("Inserindo ou atualizando dado:")
                self.database_manager.upsert_data("controle_contratos", data, "numero_contrato")
            self.dataUpdated.emit()

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
                data_to_delete = {'numero_contrato': selected_id_processo}
                try:
                    self.save_to_database(data_to_delete, delete=True)  # Passa o dado a ser deletado com uma flag de exclusão
                    QMessageBox.information(self, "Sucesso", "Registro excluído com sucesso.")
                except Exception as e:
                    QMessageBox.warning(self, "Erro ao excluir", f"Erro ao excluir o registro: {str(e)}")
                    print(f"Erro ao excluir o registro: {str(e)}")
        else:
            QMessageBox.warning(self, "Nenhuma Seleção", "Por favor, selecione uma linha para excluir.")

    def save_to_database(self, data, delete=False):
        with self.database_manager as conn:
            cursor = conn.cursor()
            if delete:
                cursor.execute("DELETE FROM controle_contratos WHERE numero_contrato = ?", (data['numero_contrato'],))
            else:
                status = 'Minuta'
                upsert_sql = '''
                INSERT INTO controle_contratos (
                    status, dias, pode_renovar, custeio, numero_contrato, tipo, id_processo, empresa, objeto, valor_global, 
                    uasg, nup, cnpj, natureza_continuada, om, sigla_om, orgao_responsavel, material_servico, link_pncp, 
                    portaria, posto_gestor, gestor, posto_gestor_substituto, gestor_substituto, posto_fiscal, fiscal, 
                    posto_fiscal_substituto, fiscal_substituto, posto_fiscal_administrativo, fiscal_administrativo, 
                    vigencia_inicial, vigencia_final, setor, cp, msg, comentarios, termo_aditivo, atualizacao_comprasnet, 
                    instancia_governanca, comprasnet_contratos, registro_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(numero_contrato) DO UPDATE SET
                    status = excluded.status,
                    dias = excluded.dias,
                    pode_renovar = excluded.pode_renovar,
                    custeio = excluded.custeio,
                    tipo = excluded.tipo,
                    id_processo = excluded.id_processo,
                    empresa = excluded.empresa,
                    objeto = excluded.objeto,
                    valor_global = excluded.valor_global,
                    uasg = excluded.uasg,
                    nup = excluded.nup,
                    cnpj = excluded.cnpj,
                    natureza_continuada = excluded.natureza_continuada,
                    om = excluded.om,
                    sigla_om = excluded.sigla_om,
                    orgao_responsavel = excluded.orgao_responsavel,
                    material_servico = excluded.material_servico,
                    link_pncp = excluded.link_pncp,
                    portaria = excluded.portaria,
                    posto_gestor = excluded.posto_gestor,
                    gestor = excluded.gestor,
                    posto_gestor_substituto = excluded.posto_gestor_substituto,
                    gestor_substituto = excluded.gestor_substituto,
                    posto_fiscal = excluded.posto_fiscal,
                    fiscal = excluded.fiscal,
                    posto_fiscal_substituto = excluded.posto_fiscal_substituto,
                    fiscal_substituto = excluded.fiscal_substituto,
                    posto_fiscal_administrativo = excluded.posto_fiscal_administrativo,
                    fiscal_administrativo = excluded.fiscal_administrativo,
                    vigencia_inicial = excluded.vigencia_inicial,
                    vigencia_final = excluded.vigencia_final,
                    setor = excluded.setor,
                    cp = excluded.cp,
                    msg = excluded.msg,
                    comentarios = excluded.comentarios,
                    termo_aditivo = excluded.termo_aditivo,
                    atualizacao_comprasnet = excluded.atualizacao_comprasnet,
                    instancia_governanca = excluded.instancia_governanca,
                    comprasnet_contratos = excluded.comprasnet_contratos,
                    registro_status = excluded.registro_status
                '''
                if isinstance(data, pd.DataFrame):
                    data['status'] = status
                    for _, row in data.iterrows():
                        cursor.execute(upsert_sql, (
                            row['status'], row['dias'], row['pode_renovar'], row['custeio'], row['numero_contrato'], row['tipo'], 
                            row['id_processo'], row['empresa'], row['objeto'], row['valor_global'], row['uasg'], row['nup'], 
                            row['cnpj'], row['natureza_continuada'], row['om'], row['sigla_om'], row['orgao_responsavel'], 
                            row['material_servico'], row['link_pncp'], row['portaria'], row['posto_gestor'], row['gestor'], 
                            row['posto_gestor_substituto'], row['gestor_substituto'], row['posto_fiscal'], row['fiscal'], 
                            row['posto_fiscal_substituto'], row['fiscal_substituto'], row['posto_fiscal_administrativo'], 
                            row['fiscal_administrativo'], row['vigencia_inicial'], row['vigencia_final'], row['setor'], row['cp'], 
                            row['msg'], row['comentarios'], row['termo_aditivo'], row['atualizacao_comprasnet'], row['instancia_governanca'], 
                            row['comprasnet_contratos'], row['registro_status']
                        ))
                else:
                    data['status'] = status
                    cursor.execute(upsert_sql, (
                        data['status'], data['dias'], data['pode_renovar'], data['custeio'], data['numero_contrato'], data['tipo'], 
                        data['id_processo'], data['empresa'], data['objeto'], data['valor_global'], data['uasg'], data['nup'], 
                        data['cnpj'], data['natureza_continuada'], data['om'], data['sigla_om'], data['orgao_responsavel'], 
                        data['material_servico'], data['link_pncp'], data['portaria'], data['posto_gestor'], data['gestor'], 
                        data['posto_gestor_substituto'], data['gestor_substituto'], data['posto_fiscal'], data['fiscal'], 
                        data['posto_fiscal_substituto'], data['fiscal_substituto'], data['posto_fiscal_administrativo'], 
                        data['fiscal_administrativo'], data['vigencia_inicial'], data['vigencia_final'], data['setor'], data['cp'], 
                        data['msg'], data['comentarios'], data['termo_aditivo'], data['atualizacao_comprasnet'], data['instancia_governanca'], 
                        data['comprasnet_contratos'], data['registro_status']
                    ))
            conn.commit()
        self.dataUpdated.emit()

    def excluir_database(self):
        reply = QMessageBox.question(
            self, 'Confirmar Exclusão',
            'Tem certeza que deseja excluir a tabela controle_contratos?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database_manager.close_all_connections()  # Fechar todas as conexões antes de excluir
                self.database_manager.execute_query("DROP TABLE IF EXISTS controle_contratos")
                QMessageBox.information(self, "Sucesso", "Tabela controle_contratos excluída com sucesso.")
                self.refresh_model()
            except Exception as e:
                QMessageBox.warning(self, "Erro ao excluir", f"Erro ao excluir a tabela: {str(e)}")


    def teste(self):
        print("Teste de controle de PDM")   

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
            ("  Adicionar", self.parent.image_cache['plus'], self.parent.on_add_item, "Adiciona um novo item ao banco de dados"),
            ("  Salvar", self.parent.image_cache['excel'], self.parent.salvar_tabela, "Salva o dataframe em um arquivo Excel"),
            ("  Importar", self.parent.image_cache['import_de'], self.parent.carregar_tabela, "Carrega dados de uma tabela"),
            ("  Excluir", self.parent.image_cache['delete'], self.parent.excluir_linha, "Exclui um item selecionado"),
            ("  Controle de PDM", self.parent.image_cache['calendar'], self.parent.teste, "Abre o painel de controle do processo"),
            ("  Excluir Database", self.parent.image_cache['delete'], self.parent.excluir_database, "Exclui a tabela controle_contratos do banco de dados"),  # Novo botão
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

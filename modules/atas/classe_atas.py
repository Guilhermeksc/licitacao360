## Módulo incluido em modules/contratos/classe_contratos.py ##

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
from modules.atas.edit_dialog import AtualizarDadosContratos
from database.utils.treeview_utils import load_images, create_button
from modules.atas.utils import ExportThread, ColorDelegate, carregar_dados_contratos, Dialogs, CustomItemDelegate, CenterAlignDelegate, load_and_map_icons
from modules.atas.database_manager import SqlModel, DatabaseATASManager, CustomTableView
from modules.atas.consultar_api import GerenciarInclusaoExclusaoATAS
from modules.atas.msg.msg_alerta_prazo import MensagemDialog
import pandas as pd
import os
import subprocess
import logging
import sqlite3
import webbrowser
import requests
import time

class AtasWidget(QMainWindow):
    dataUpdated = pyqtSignal()

    def __init__(self, icons_dir, parent=None):
        super().__init__(parent)
        self.required_columns = [
            'status', 'dias', 'cnpj', 'referencia', 'sequencial', 'ano', 'numero_ata', 'id_pncp'
        ]
        self.icons_dir = Path(icons_dir) if icons_dir else Path()
        self.setup_managers()
        self.load_initial_data()
        self.model = self.init_model()
        self.image_cache = {}
        self.icons = load_and_map_icons(self.icons_dir, self.image_cache)      
        self.ui_manager = UIManager(self, self.icons, self.config_manager, self.model)
        self.setup_ui()
        self.export_thread = None
        self.output_path = os.path.join(os.getcwd(), "controle_atas.xlsx")
        self.dataUpdated.connect(self.refresh_model)
        self.refresh_model()

    def setup_managers(self):
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = Path(load_config("CONTROLE_ATAS_DADOS", str(CONTROLE_ATAS_DADOS)))
        self.database_manager = DatabaseATASManager(self.database_path)

    def load_initial_data(self):
        self.image_cache = load_images(self.icons_dir, ["data-transfer.png", "production.png", "production_red.png", "csv.png", "import_de.png", "save_to_drive.png", "loading.png", "delete.png", "excel.png", "calendar.png", "message_alert.png", "management.png"])

    def init_model(self):
        sql_model = SqlModel(self.icons_dir, self.database_manager, self)
        return sql_model.setup_model("controle_atas", editable=True)

    def refresh_model(self):
        self.model.select()  # Recarregar os dados

    def sort_by_vigencia_final(self):
        # Ordenar o modelo proxy pela coluna 'vigencia_final' em ordem decrescente
        self.parent.proxy_model.sort(self.model.fieldIndex("Dias"), Qt.SortOrder.DescendingOrder)

    def setup_ui(self):
        self.setCentralWidget(self.ui_manager.main_widget)

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

        indice_linha = source_index.row()

        if df_registro_selecionado is not None and not df_registro_selecionado.empty:
            dialog = MensagemDialog(df_registro_selecionado, self.icons_dir, indice_linha, self)
            dialog.exec()

    def gerenciar_itens(self):
        # Encerrar conexões existentes antes de abrir o diálogo
        self.close_database_connections()
        
        # Adicionar print para verificar se o banco de dados foi fechado
        print("Database connection closed:", self.database_manager.is_closed())

        # Supondo que self.required_columns esteja definido no contexto da classe chamadora
        dialog = GerenciarInclusaoExclusaoATAS(self.icons_dir, self.database_path, self.required_columns, self)
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

    def editar_dados(self, df_registro_selecionado):
        try:
            # Verifica se o modelo está corretamente inicializado
            if not self.model:
                QMessageBox.warning(self, "Erro", "Modelo de dados não inicializado.")
                return

            # Remover colunas com valores None
            df_registro_selecionado = df_registro_selecionado.dropna(axis=1, how='all')

            # Verifique se o DataFrame contém os dados necessários
            if 'id_pncp' not in df_registro_selecionado.columns:
                raise ValueError("Coluna 'id_pncp' não encontrada no DataFrame.")

            # Extraindo id_processo corretamente da coluna 'id_pncp'
            id_processo = df_registro_selecionado['id_pncp'].values[0]
            print(f"id_processo selecionado: {id_processo}")

            # Converte os dados do DataFrame em dicionário para passar ao diálogo
            data_function = lambda: df_registro_selecionado.to_dict(orient='records')[0]

            # Inicializar o diálogo de edição
            dialog = AtualizarDadosContratos(self.icons_dir, data_function=data_function, df_registro_selecionado=df_registro_selecionado, 
                                            table_view=self.ui_manager.table_view, model=self.model, indice_linha=0, parent=self)

            # Conectar o sinal de dados salvos ao refresh_model
            dialog.dadosContratosSalvos.connect(self.refresh_model)

            # Executar o diálogo
            print("Tentando abrir o diálogo...")
            dialog.exec()

        except Exception as e:
            print(f"Erro ao abrir o diálogo: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao abrir o diálogo de edição: {str(e)}")

class UIManager(QObject):
    def __init__(self, parent, icons, config_manager, model):
        super().__init__(parent)  # Inicializa a classe QObject
        self.parent = parent
        self.icons = icons
        self.config_manager = config_manager
        self.model = model
        self.main_widget = QWidget(parent)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Remove as margens do layout principal
        self.init_ui()

    def init_ui(self):
        self.setup_main_content()
        self.setup_side_menu()

        self.parent.setCentralWidget(self.main_widget)

    def setup_side_menu(self):
        # Cria um layout vertical para o menu lateral
        self.side_menu_layout = QVBoxLayout()
        self.side_menu_layout.setContentsMargins(0, 0, 0, 0)
        self.side_menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Mapeia as chaves dos ícones com os textos dos tooltips
        icon_keys_and_actions = [
            ("Mensagem", "Enviar Mensagem", self.parent.show_mensagem_dialog),
            ("API", "Configurações de API", self.parent.gerenciar_itens),
            ("excel", "Salvar Tabela", self.parent.salvar_tabela),
            ("statistics", "Visualizar Nota Técnica", self.parent.salvar_tabela),
            ("data-server", "Gerenciar Contratos", self.parent.salvar_tabela),
            ("external-link", "Abrir Site", self.parent.salvar_tabela),
            ("download-pdf", "Relatório de Contratos", self.parent.salvar_tabela),
            ("portaria_fiscal", "Portaria de Fiscalização", self.parent.salvar_tabela),
        ]

        # Adiciona os botões ao menu lateral e conecta os sinais
        for icon_key, tooltip_text, action in icon_keys_and_actions:
            button = self.create_menu_button(icon_key, tooltip_text)
            button.clicked.connect(action)  # Conecta o clique do botão à função correspondente
            self.side_menu_layout.addWidget(button)

        # Adiciona o menu lateral ao layout principal
        side_menu_widget = QWidget()
        side_menu_widget.setLayout(self.side_menu_layout)
        self.main_layout.addWidget(side_menu_widget)

    def create_menu_button(self, icon_key, tooltip_text):
        # Obtém os ícones não selecionado (padrão) e selecionado (azul)
        icon_default = self.icons.get(icon_key)
        icon_selected = self.icons.get(f"{icon_key}_azul")

        if not icon_default or not icon_selected:
            raise ValueError(f"Os ícones para '{icon_key}' não foram encontrados em 'self.icons'.")

        # Cria um botão com o ícone padrão para o menu lateral
        button = QPushButton()
        button.setIcon(icon_selected)  # Usa o ícone não selecionado inicialmente
        button.setIconSize(QSize(40, 40))
        button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0);
            }
            QToolTip {
                background-color: #13141F;
                color: white;
                border: none;
                font-size: 14px;
            }                             
        """)

        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedSize(50, 50)
        button.setToolTip(tooltip_text)  # Define o texto do tooltip
        button.setToolTipDuration(0)     # Faz o tooltip aparecer instantaneamente

        # Adiciona o evento de filtro para alterar o ícone no hover
        button.installEventFilter(self)

        # Armazena os ícones para uso posterior
        button.icon_default = icon_default
        button.icon_selected = icon_selected

        return button

    def eventFilter(self, source, event):
        if isinstance(source, QPushButton):
            if event.type() == QEvent.Type.Enter:
                # Muda o ícone para o ícone "hover" (azul) ao passar o mouse
                source.setIcon(source.icon_default)
            elif event.type() == QEvent.Type.Leave:
                # Restaura o ícone para o ícone padrão ao sair do botão
                source.setIcon(source.icon_selected)
        return super().eventFilter(source, event)

    def setup_main_content(self):
        # Cria um layout vertical para o conteúdo principal
        self.content_layout = QVBoxLayout()
        
        # Configura a barra de pesquisa e os botões
        self.setup_search_bar_and_buttons()
        self.setup_table_view()

        # Adiciona o layout de conteúdo ao layout principal
        content_widget = QWidget()
        content_widget.setLayout(self.content_layout)
        self.main_layout.addWidget(content_widget)

    def get_codigo_unidade(self):
        # Verifica se o modelo tem dados
        if self.model.rowCount() > 0:
            # Obtém o valor da primeira linha e da coluna específica que representa 'codigo_unidade'
            index = self.model.index(0, self.model.fieldIndex("codigo_unidade"))
            codigo_unidade = self.model.data(index)
            return codigo_unidade if codigo_unidade else "Não Definido"
        return "Não Definido"

    def setup_search_bar_and_buttons(self):
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        # Obtém o valor do código da unidade
        codigo_unidade = self.get_codigo_unidade()
        search_label = QLabel(f"Controle de Atas - Uasg {codigo_unidade}")
        search_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        search_layout.addWidget(search_label)

        self.search_bar = QLineEdit(self.parent)
        self.search_bar.setPlaceholderText("Digite para buscar...")
        self.search_bar.setStyleSheet("font-size: 14px;")
        search_layout.addWidget(self.search_bar)

        def handle_text_change(text):
            regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.parent.proxy_model.setFilterRegularExpression(regex)

        self.search_bar.textChanged.connect(handle_text_change)
        self.content_layout.addLayout(search_layout)

    def setup_buttons_layout(self, parent_layout):
        self.buttons_layout = QHBoxLayout()
        self.button_manager.add_buttons_to_layout(self.buttons_layout)
        parent_layout.addLayout(self.buttons_layout)
        for i in range(self.buttons_layout.count()):
            widget = self.buttons_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(
                    "font-size: 14px; min-width: 120px; min-height: 20px; max-width: 120px; max-height: 20px;"
                )

    def setup_table_view(self):
        self.table_view = CustomTableView(main_app=self.parent, config_manager=self.config_manager, parent=self.main_widget)
        self.table_view.setModel(self.model)
        self.content_layout.addWidget(self.table_view)
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.configure_table_model()
        self.table_view.verticalHeader().setVisible(False)
        self.adjust_columns()
        self.apply_custom_style()
        center_delegate = CenterAlignDelegate(self.table_view)
        for column in range(self.model.columnCount()):
            self.table_view.setItemDelegateForColumn(column, center_delegate)

        status_index = self.model.fieldIndex("status")
        for column in range(self.model.columnCount()):
            if column != status_index:
                self.table_view.setItemDelegateForColumn(column, center_delegate)

        self.table_view.setItemDelegateForColumn(
            status_index,
            CustomItemDelegate(self.icons, status_index, self.table_view)
        )
        self.reorder_columns()
        self.table_view.doubleClicked.connect(self.open_editar_dados_dialog)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        # Obter o índice da linha clicada
        index = self.table_view.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu()

        visualizar_ata_action = QAction("Visualizar Ata", self.parent)
        visualizar_ata_action.triggered.connect(self.visualizar_ata)

        relacao_itens_action = QAction("Relação de Itens", self.parent)
        relacao_itens_action.triggered.connect(self.relacao_itens)

        empenhos_action = QAction("Empenhos", self.parent)
        empenhos_action.triggered.connect(self.empenhos)

        menu.addAction(visualizar_ata_action)
        menu.addAction(relacao_itens_action)
        menu.addAction(empenhos_action)

        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def visualizar_ata(self):
        try:
            # Obter os dados da linha selecionada através de linhaSelecionada
            selected_index = self.table_view.selectionModel().currentIndex()
            source_index = self.parent.proxy_model.mapToSource(selected_index)
            
            selected_row = source_index.row()
            df_registro_selecionado = carregar_dados_contrato(selected_row, self.parent.database_path)

            if df_registro_selecionado.empty:
                QMessageBox.warning(self.parent, "Erro", "Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")
                return

            # Obter os valores de cnpj, ano, sequencial e numero_ata do df_registro_selecionado
            cnpj = df_registro_selecionado.get("cnpj", [None])[0]
            ano = df_registro_selecionado.get("sequencial_ano_pncp", [None])[0]
            sequencial = df_registro_selecionado.get("sequencial", [None])[0]
            numero_ata = df_registro_selecionado.get("sequencial_ata_pncp", [None])[0]

            # Verificar se todos os valores necessários estão presentes
            if not all([cnpj, ano, sequencial, numero_ata]):
                QMessageBox.warning(self.parent, "Erro", "Valores necessários não estão disponíveis para a consulta.")
                return

            # Formar a URL da API
            url = f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/atas/{numero_ata}/arquivos"

            # Fazer a requisição HTTP
            response = requests.get(url)
            if response.status_code != 200:
                QMessageBox.warning(self.parent, "Erro", f"Erro ao acessar a API: {response.status_code}")
                return

            # Obter a resposta JSON
            arquivos = response.json()
            if not arquivos:
                QMessageBox.warning(self.parent, "Erro", "Nenhum arquivo encontrado.")
                return

            # Pegar a URL do primeiro documento (por exemplo)
            arquivo_url = arquivos[0].get("url")
            if not arquivo_url:
                QMessageBox.warning(self.parent, "Erro", "URL do arquivo não disponível.")
                return

            # Tentar baixar o arquivo PDF até 10 vezes
            for tentativa in range(10):
                try:
                    arquivo_response = requests.get(arquivo_url)
                    if arquivo_response.status_code == 200:
                        # Salvar o arquivo PDF
                        caminho_pdf = os.path.join(os.getcwd(), f"{sequencial}-{numero_ata}-{ano}.pdf")
                        with open(caminho_pdf, 'wb') as f:
                            f.write(arquivo_response.content)

                        # Abrir o arquivo PDF
                        webbrowser.open_new(caminho_pdf)
                        QMessageBox.information(self.parent, "Sucesso", "Arquivo baixado e aberto com sucesso.")
                        return
                    else:
                        print(f"Tentativa {tentativa + 1} falhou, status: {arquivo_response.status_code}")
                except Exception as e:
                    print(f"Tentativa {tentativa + 1} falhou, erro: {e}")
                # Aguardar 2 segundos entre as tentativas
                time.sleep(2)

            # Caso não consiga baixar o arquivo após 10 tentativas
            QMessageBox.warning(self.parent, "Erro", "Falha ao baixar o arquivo após 10 tentativas.")

        except Exception as e:
            QMessageBox.critical(self.parent, "Erro", f"Ocorreu um erro ao tentar visualizar a ata: {str(e)}")

    
    def get_row_data(self, row):
        """
        Extrai os dados de uma linha específica do modelo.
        """
        column_count = self.model.columnCount()
        row_data = {self.model.headerData(col, Qt.Orientation.Horizontal): self.model.data(self.model.index(row, col)) for col in range(column_count)}
        return row_data

    def relacao_itens(self):
        # Método para relação de itens
        print("Relação de Itens selecionado")
        # Adicione a lógica aqui

    def empenhos(self):
        # Método para empenhos
        print("Empenhos selecionado")
        # Adicione a lógica aqui

    def open_editar_dados_dialog(self, index):
        """
        Método chamado quando uma linha é duplo clicada para abrir o diálogo de edição.
        """
        # Obter o índice da linha no modelo subjacente (source model)
        source_index = self.parent.proxy_model.mapToSource(index)
        row_data = self.get_row_data(source_index.row())

        # Converter os dados da linha para um DataFrame para compatibilidade com o método 'editar_dados'
        df_registro_selecionado = pd.DataFrame([row_data])

        # Abrir o diálogo de edição
        self.parent.editar_dados(df_registro_selecionado)
    
    def configure_table_model(self):
        self.parent.proxy_model = QSortFilterProxyModel(self.parent)
        self.parent.proxy_model.setSourceModel(self.model)
        self.parent.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.parent.proxy_model.setFilterKeyColumn(-1)

        # Configura a ordenação inicial pelo proxy model de forma decrescente pela coluna 'vigencia_final'
        self.sort_by_vigencia_final()

        self.table_view.setModel(self.parent.proxy_model)
        print("Table view configured with proxy model")

        self.model.dataChanged.connect(self.table_view.update)

        if self.table_view.selectionModel():
            self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
            self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
            self.table_view.selectionModel().selectionChanged.connect(self.linhaSelecionada)

        self.update_column_headers()
        self.hide_unwanted_columns()

    def sort_by_vigencia_final(self):
        self.parent.proxy_model.sort(self.model.fieldIndex("Dias"), Qt.SortOrder.DescendingOrder)

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
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(14, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 200)
        header.resizeSection(1, 60)
        header.resizeSection(2, 170)
        header.resizeSection(3, 65)
        header.resizeSection(5, 50)

    def apply_custom_style(self):
        # Aplica um estilo CSS personalizado ao tableView
        self.table_view.setStyleSheet("""
            QTableView {
                font-size: 16px;
                background-color: #13141F;                      
            }
            QTableView::section {
                font-size: 16px;
                font-weight: bold; 
            }
            QHeaderView::section:horizontal {
                font-size: 16px;
                font-weight: bold;
            }
            QHeaderView::section:vertical {
                font-size: 16px;
            }
        """)

    def linhaSelecionada(self, selected, deselected):
        if selected.indexes():
            proxy_index = selected.indexes()[0]
            source_index = self.parent.proxy_model.mapToSource(proxy_index)
            
            # Obter o valor da chave primária 'numero_contrato'
            selected_row = source_index.row()
            selected_column = source_index.column()
            id_processo = self.parent.model.data(self.parent.model.index(source_index.row(), self.parent.model.fieldIndex('id_pncp')))

            print(f"id_processo selecionado: {id_processo}")
            print(f"Linha selecionada: {selected_row}, Coluna: {selected_column}")

            df_registro_selecionado = carregar_dados_contrato(selected_row, self.parent.database_path)

            if not df_registro_selecionado.empty:
                logging.debug(f"Registro selecionado: {df_registro_selecionado.iloc[0].to_dict()}")
            else:
                logging.warning("Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")
                QMessageBox.warning(self.parent, "Erro", "Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")

    def update_column_headers(self):
        titles = {
            0: "Status",
            1: "Dias",
            2: "Cnpj",
            4: "Sequencial",
            5: "Ano",
            7: "Número",
            14: "Objeto",
        }
        for column, title in titles.items():
            self.model.setHeaderData(column, Qt.Orientation.Horizontal, title)

    def reorder_columns(self):
        # Inclua a coluna de ícones na nova ordem
        new_order = [0, 1, 2, 3, 4, 5]
        for i, col in enumerate(new_order):
            self.table_view.horizontalHeader().moveSection(self.table_view.horizontalHeader().visualIndex(col), i)

    def hide_unwanted_columns(self):
        # Inclua a coluna de ícones no conjunto de colunas visíveis
        visible_columns = {0, 1, 2, 4, 5, 7, 14}
        for column in range(self.model.columnCount()):
            if column not in visible_columns:
                self.table_view.hideColumn(column)

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

def carregar_dados_contrato(linha, database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Supondo que a chave é 'id_processo' e 'linha' representa a posição na tabela.
    try:
        cursor.execute("SELECT * FROM controle_atas LIMIT 1 OFFSET ?", (linha,))
        row = cursor.fetchone()
        if row:
            # Transformar em DataFrame ou outra estrutura conforme necessário
            df_registro_selecionado = pd.DataFrame([row], columns=[desc[0] for desc in cursor.description])
            return df_registro_selecionado
        else:
            return pd.DataFrame()  # Retorna DataFrame vazio se nada for encontrado
    except sqlite3.Error as e:
        print(f"Erro ao carregar os dados atas: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
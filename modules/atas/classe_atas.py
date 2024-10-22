## Módulo incluido em modules/contratos/classe_contratos.py ##

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
from modules.atas.edit_dialog import AtualizarDadosContratos
from modules.atas.utils import ExportThread, ColorDelegate, carregar_dados_contrato, Dialogs, CustomItemDelegate, CenterAlignDelegate, load_and_map_icons
from modules.atas.database_manager import SqlModel, DatabaseATASManager, CustomTableView
from modules.atas.consultar_api import GerenciarInclusaoExclusaoATAS
from modules.atas.menu_button.menu_button import create_menu_button, visualizar_ata, relacao_itens, empenhos
from modules.atas.menu_button.gerar_relatorio_pdf import gerar_relatorio_atas
from modules.atas.menu_button.obter_dados_pregao import DadosPregaoThread, LoadingDialog
from modules.atas.msg.msg_alerta_prazo import MensagemDialog
from modules.atas.gerar_atas.classe_gerar_atas import GerarAtas
import pandas as pd
import os
import subprocess
import logging
import sqlite3
from functools import partial

CONTROLE_ATAS_DADOS = CONTROLE_ATAS_DIR / "controle_atas.db"
DADOS_PREGAO_ATA = CONTROLE_ATAS_DIR / "controle_dados_pregao_ata.db"
class AtasWidget(QMainWindow):
    dataUpdated = pyqtSignal()

    def __init__(self, icons_dir, parent=None):
        super().__init__(parent)
        self.required_columns = [
            'status', 'dias', 'cnpj', 'referencia', 'sequencial', 'ano', 'numero_ata', 'id_pncp'
        ]
        self.icons_dir = Path(icons_dir) if icons_dir else Path()
        self.setup_managers()
        self.model = self.init_model()  # Inicializa o modelo com a primeira tabela disponível
        self.image_cache = {}
        self.icons = load_and_map_icons(self.icons_dir, self.image_cache)
        self.ui_manager = UIManager(self, self.icons, self.config_manager, self.model)
        self.setup_ui()
        self.export_thread = None
        self.output_path = os.path.join(os.getcwd(), "controle_atas.xlsx")
        self.dataUpdated.connect(self.refresh_model)
        self.refresh_model()
        self.gerar_atas_dialog = None

    def setup_managers(self):
        config_path = BASE_DIR / "config.json"
        self.database_path = CONTROLE_ATAS_DADOS
        self.config_manager = ConfigManager(config_path)
        self.database_manager = DatabaseATASManager(CONTROLE_ATAS_DADOS)
        self.setup_database_paths()

    def setup_database_paths(self):
        """Configura os caminhos para os bancos de dados usados."""
        # Configura os caminhos iniciais
        self.dados_pregao_ata_path = DADOS_PREGAO_ATA

    def switch_database(self, use_pregao=False):
        """Permite alternar entre os bancos de dados `CONTROLE_ATAS_DADOS` e `DADOS_PREGAO_ATA`."""
        if use_pregao:
            self.database_manager.set_database_path(self.dados_pregao_ata_path)
        else:
            self.database_manager.set_database_path(CONTROLE_ATAS_DADOS)

    def save_data_to_current_database(self, df, table_name, use_pregao=False):
        """Salva dados no banco de dados atual, podendo alternar para o banco de dados do pregão."""
        self.switch_database(use_pregao)
        self.database_manager.save_dataframe(df, table_name)

    # Exemplo de uso ao executar uma consulta
    def execute_query_on_current_database(self, query, params=None, use_pregao=False):
        """Executa uma query no banco de dados atual, podendo alternar para o banco de dados do pregão."""
        self.switch_database(use_pregao)
        return self.database_manager.execute_query(query, params)
    
    def init_model(self):
        """Inicializa o modelo com o nome da primeira tabela disponível."""
        sql_model = SqlModel(self.icons_dir, self.database_manager, self)
        first_table_name = sql_model.get_first_table_name()

        if first_table_name is None:
            return None  # Tratar caso não haja tabelas no banco de dados

        # Configura o modelo com a primeira tabela encontrada
        return sql_model.setup_model(first_table_name, editable=True)

    def refresh_model(self):
        if self.model:
            self.model.select()

    def update_model_with_table(self, unidade_codigo):
        """Atualiza o modelo para usar a tabela especificada pelo código da unidade."""
        if not unidade_codigo:
            return  # Caso nenhum código de unidade seja selecionado

        table_name = f"uasg_{unidade_codigo}"
        sql_model = SqlModel(self.icons, self.database_manager, self)

        # Reinicializa o modelo com a nova tabela
        self.model = sql_model.setup_model(table_name, editable=True)

        # Atualiza o proxy model para usar o novo modelo
        self.proxy_model.setSourceModel(self.model)

        # Atualiza a referência do modelo na UIManager
        self.ui_manager.model = self.model

        # Atualiza a interface da tabela
        self.refresh_model()
        self.ui_manager.update_column_headers()
        self.ui_manager.setup_delegates()
        self.ui_manager.adjust_columns()
        self.ui_manager.apply_custom_style() 

    def setup_ui(self):
        self.setCentralWidget(self.ui_manager.main_widget)

    def sort_by_vigencia_final(self):
        # Ordenar o modelo proxy pela coluna 'vigencia_final' em ordem decrescente
        self.parent.proxy_model.sort(self.model.fieldIndex("Dias"), Qt.SortOrder.DescendingOrder)

    def show_mensagem_dialog(self):
        # Verifica se existe uma linha selecionada armazenada
        df_registro_selecionado = self.ui_manager.selected_row_data if hasattr(self.ui_manager, 'selected_row_data') else pd.DataFrame()

        if df_registro_selecionado.empty:
            QMessageBox.warning(self, "Erro", "Nenhuma linha foi selecionada ou ocorreu um erro ao carregar os dados.")
            return  # Caso os dados estejam vazios, saia do método

        indice_linha = df_registro_selecionado.index[0]

        # Abrir o diálogo com os dados selecionados
        dialog = MensagemDialog(df_registro_selecionado, self.icons_dir, indice_linha, self)
        dialog.exec()

    def gerenciar_itens(self):
        self.close_database_connections()
        dialog = GerenciarInclusaoExclusaoATAS(self.icons_dir, self.database_path, self.required_columns, self)
        dialog.dataUpdated.connect(self.handle_data_updated)
        dialog.exec()

    def handle_data_updated(self, unidade_codigo):
        # Atualizar o combo box com o novo unidade_codigo
        self.ui_manager.load_unidades_into_combobox()
        index = self.ui_manager.combo_box_unidades.findText(unidade_codigo)
        if index != -1:
            self.ui_manager.combo_box_unidades.setCurrentIndex(index)
        # Atualizar o modelo com a nova tabela
        self.update_model_with_table(unidade_codigo)

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
        if not self.model:
            QMessageBox.warning(self, "Erro", "Modelo de dados não inicializado.")
            return

        df_registro_selecionado = df_registro_selecionado.dropna(axis=1, how='all')

        if 'id_pncp' not in df_registro_selecionado.columns:
            QMessageBox.critical(self, "Erro", "Coluna 'id_pncp' não encontrada no DataFrame.")
            return

        id_processo = df_registro_selecionado['id_pncp'].values[0]

        data_function = lambda: df_registro_selecionado.to_dict(orient='records')[0]

        dialog = AtualizarDadosContratos(
            self.icons_dir,
            data_function=data_function,
            df_registro_selecionado=df_registro_selecionado,
            table_view=self.ui_manager.table_view,
            model=self.model,
            indice_linha=0,
            parent=self
        )

        dialog.dadosContratosSalvos.connect(self.refresh_model)
        dialog.exec()

    def gerar_relatorio(self):
        try:
            table_name = self.model.tableName()  # Obtém o nome da tabela atual
            nome_unidade, codigo_unidade = self.ui_manager.get_nome_unidade_e_codigo()  # Obtém o nome da unidade

            # Gera o relatório
            gerar_relatorio_atas(self.model, table_name, nome_unidade, codigo_unidade, output_dir=os.getcwd())
            QMessageBox.information(self, "Sucesso", "Relatório gerado com sucesso!")
            
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar o relatório: {e}")

    def visualizar_dados_pregao(self):
        """Executa a função visualizar_dados_pregao em uma thread separada."""
        # Cria o diálogo de carregamento
        self.loading_dialog = LoadingDialog(self)
        self.loading_dialog.show()

        # Cria a thread para executar a requisição em segundo plano
        self.thread = DadosPregaoThread(self.ui_manager, self.dados_pregao_ata_path, self)

        # Conecta os sinais da thread
        self.thread.finished.connect(self.handle_thread_finished)
        self.thread.error.connect(self.handle_thread_error)

        # Inicia a execução da thread
        self.thread.start()

    def handle_thread_finished(self, message):
        """Lida com o sinal de finalização da thread."""
        self.loading_dialog.accept()  # Fecha o diálogo de carregamento
        QMessageBox.information(self, "Sucesso", message)

    def handle_thread_error(self, error_message):
        """Lida com o sinal de erro da thread."""
        self.loading_dialog.reject()  # Fecha o diálogo de carregamento
        QMessageBox.critical(self, "Erro", error_message)

    def abrir_gerar_atas_dialog(self):
        if self.gerar_atas_dialog is None or not self.gerar_atas_dialog.dialog.isVisible():
            self.gerar_atas_dialog = GerarAtas(self, self.icons_dir)
            # Conecta ao sinal destroyed do diálogo para redefinir a referência
            self.gerar_atas_dialog.dialog.destroyed.connect(self.on_gerar_atas_dialog_closed)
        else:
            # Traz o diálogo existente para a frente
            self.gerar_atas_dialog.dialog.raise_()
            self.gerar_atas_dialog.dialog.activateWindow()

    def on_gerar_atas_dialog_closed(self):
        self.gerar_atas_dialog = None

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

    def setup_main_content(self):
        self.content_layout = QVBoxLayout()
        self.setup_search_bar_and_buttons()
        self.setup_table_view()
        self.configure_table_model()

        content_widget = QWidget()
        content_widget.setLayout(self.content_layout)
        self.main_layout.addWidget(content_widget)

    def setup_table_view(self):
        # Initialize the table view
        self.table_view = CustomTableView(
            main_app=self.parent,
            config_manager=self.config_manager,
            parent=self.main_widget
        )
        self.content_layout.addWidget(self.table_view)

        # Basic configuration
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.verticalHeader().setVisible(False)

    def setup_side_menu(self):
        # Cria um layout vertical para o menu lateral
        self.side_menu_layout = QVBoxLayout()
        self.side_menu_layout.setContentsMargins(0, 0, 0, 0)
        self.side_menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Mapeia as chaves dos ícones com os textos dos tooltips
        icon_keys_and_actions = [
            ("Mensagem", "Enviar Mensagem", self.parent.show_mensagem_dialog),
            ("cp", "Comunicação Padronizada", self.parent.show_mensagem_dialog),
            ("API", "Configurações de API", self.parent.gerenciar_itens),
            ("excel", "Salvar Tabela", self.parent.salvar_tabela),
            ("statistics", "Relação de Itens da Contratação", self.parent.visualizar_dados_pregao),
            ("performance", "Indicador NORMCEIM", self.parent.salvar_tabela),
            ("data-server", "Gerenciar Contratos", self.parent.salvar_tabela),
            ("external-link", "Abrir Site", self.parent.salvar_tabela),
            ("download-pdf", "Relatório de Contratos", self.parent.gerar_relatorio),
            ("portaria_fiscal", "Portaria de Fiscalização", self.parent.salvar_tabela),
            ("downloading", "Dowload da Ata disponível no PNCP", self.parent.salvar_tabela),
            ("license", "Gerar Atas Automaticamente", self.parent.abrir_gerar_atas_dialog)
        ]

        # Adiciona os botões ao menu lateral e conecta os sinais
        for icon_key, tooltip_text, action in icon_keys_and_actions:
            button = create_menu_button(self.icons, icon_key, tooltip_text)
            button.clicked.connect(action)  # Conecta o clique do botão à função correspondente
            self.side_menu_layout.addWidget(button)

        # Adiciona o menu lateral ao layout principal
        side_menu_widget = QWidget()
        side_menu_widget.setLayout(self.side_menu_layout)
        self.main_layout.addWidget(side_menu_widget)

    def eventFilter(self, source, event):
        if isinstance(source, QPushButton):
            if event.type() == QEvent.Type.Enter:
                # Muda o ícone para o ícone "hover" (azul) ao passar o mouse
                source.setIcon(source.icon_default)
            elif event.type() == QEvent.Type.Leave:
                # Restaura o ícone para o ícone padrão ao sair do botão
                source.setIcon(source.icon_selected)
        return super().eventFilter(source, event)

    def get_nome_unidade_e_codigo(self):
        """Obtém o nome da unidade e o código UASG a partir do modelo."""
        # Verifica se o modelo tem dados
        if self.model.rowCount() > 0:
            # Obtém o valor da primeira linha e da coluna específica que representa 'nome_unidade'
            index_nome = self.model.index(0, self.model.fieldIndex("nome_unidade"))
            nome_unidade = self.model.data(index_nome) if index_nome.isValid() else "Não Definido"
            
            # Obtém o valor da primeira linha e da coluna específica que representa 'codigo_unidade'
            index_codigo = self.model.index(0, self.model.fieldIndex("codigo_unidade"))
            codigo_unidade = self.model.data(index_codigo) if index_codigo.isValid() else "Não Definido"
            
            return nome_unidade, codigo_unidade
        
        return "Não Definido", "Não Definido"

    def setup_search_bar_and_buttons(self):
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)

        # Layout para o label "Uasg:" e o combobox
        uasg_layout = QHBoxLayout()
        uasg_layout.setContentsMargins(0, 0, 0, 0)
        uasg_widget = QWidget()  # Usando um QWidget para aplicar o estilo no layout
        uasg_widget.setStyleSheet(
            "font-size: 20px; font-weight: bold;"
        )
        uasg_widget.setLayout(uasg_layout)

        uasg_label = QLabel("Uasg:")
        uasg_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        uasg_layout.addWidget(uasg_label)

        # Criação do QComboBox para selecionar a unidade
        self.combo_box_unidades = QComboBox(self.parent)
        self.combo_box_unidades.setStyleSheet(
            "font-size: 18px; background-color: #181928; color: white;"
        )
        uasg_layout.addWidget(self.combo_box_unidades)

        # Adiciona o widget com o layout UASG ao layout de busca
        search_layout.addWidget(uasg_widget)

        # Carregar os nomes das tabelas existentes no banco de dados
        self.load_unidades_into_combobox()

        # Conectar o sinal de alteração do QComboBox para atualizar o texto do search_label e o modelo
        self.combo_box_unidades.currentTextChanged.connect(self.parent.update_model_with_table)

        # Conectar o sinal para atualizar os cabeçalhos das colunas
        self.combo_box_unidades.currentTextChanged.connect(self.update_column_headers)

        # Label "Localizar:" antes do campo de busca
        localizar_label = QLabel("Localizar:")
        localizar_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        search_layout.addWidget(localizar_label)

        # Campo de busca
        self.search_bar = QLineEdit(self.parent)
        self.search_bar.setPlaceholderText("Digite para buscar...")
        self.search_bar.setStyleSheet("font-size: 18px")
        search_layout.addWidget(self.search_bar)

        # Conectar o campo de busca ao filtro do modelo
        def handle_text_change(text):
            regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.parent.proxy_model.setFilterRegularExpression(regex)

        self.search_bar.textChanged.connect(handle_text_change)

        # Adicionar o layout de busca ao layout principal
        self.content_layout.addLayout(search_layout)


    def update_model(self, unidade_codigo):
        """Atualiza o modelo do AtasWidget com a tabela selecionada no QComboBox."""
        if not unidade_codigo:
            return  # Caso nenhum código de unidade seja selecionado

        table_name = f"uasg_{unidade_codigo}"
        sql_model = SqlModel(self.icons, self.parent.database_manager, self.parent)

        # Configura o novo modelo com a tabela selecionada
        self.parent.model = sql_model.setup_model(table_name, editable=True)

        # Atualiza o proxy model com o novo modelo
        self.parent.proxy_model.setSourceModel(self.parent.model)

        # Atualiza a visualização da tabela
        self.parent.refresh_model()

        # Configurar os delegados e o estilo
        self.setup_delegates()
        self.adjust_columns()

    def load_unidades_into_combobox(self):
        try:
            self.combo_box_unidades.clear()  # Limpa os itens existentes
            with sqlite3.connect(str(CONTROLE_ATAS_DADOS)) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'uasg_%'")
                tables = cursor.fetchall()

                # Adicionar os valores ao QComboBox
                for table_name in tables:
                    # Extrair o código da unidade (ex: 'uasg_1234' -> '1234')
                    unidade_codigo = table_name[0].replace("uasg_", "")
                    self.combo_box_unidades.addItem(unidade_codigo)
        except Exception as e:
            QMessageBox.critical(self.parent, "Erro", f"Erro ao carregar as unidades: {e}")

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

    def configure_table_model(self):
        self.parent.proxy_model = QSortFilterProxyModel(self.parent)
        self.parent.proxy_model.setSourceModel(self.model)
        self.parent.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.parent.proxy_model.setFilterKeyColumn(-1)

        # Configure initial sorting
        self.sort_by_vigencia_final()

        # Assign the proxy model to the table view
        self.table_view.setModel(self.parent.proxy_model)
        print("Table view configured with proxy model")

        # Connect signals
        self.model.dataChanged.connect(self.table_view.update)
        if self.table_view.selectionModel():
            self.table_view.selectionModel().selectionChanged.connect(self.linhaSelecionada)

        # Update headers and hide columns
        self.update_column_headers()
        self.hide_unwanted_columns()

        # Set up delegates and context menus
        self.setup_delegates()
        self.setup_context_menu()

        # Adjust columns and styles
        self.adjust_columns()
        self.apply_custom_style()

    def setup_delegates(self):
        center_delegate = CenterAlignDelegate(self.table_view)
        status_index = self.model.fieldIndex("status")

        for column in range(self.model.columnCount()):
            if column != status_index:
                self.table_view.setItemDelegateForColumn(column, center_delegate)

        self.table_view.setItemDelegateForColumn(
            status_index,
            CustomItemDelegate(self.icons, status_index, self.table_view)
        )

    def setup_context_menu(self):
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        self.table_view.doubleClicked.connect(self.open_editar_dados_dialog)

    def show_context_menu(self, position):
        """
        Exibe o menu de contexto no table_view na posição especificada com as ações fornecidas.
        Carrega os dados da linha selecionada e os passa para as ações.
        """
        table_view = self.table_view
        proxy_model = self.parent.proxy_model
        database_path = self.parent.database_path
        parent = self.parent

        actions = [
            ("Visualizar Ata", visualizar_ata),
            ("Relação de Itens", relacao_itens),
            ("Empenhos", empenhos)
        ]

        if not isinstance(position, QPoint):
            return

        index = table_view.indexAt(position)
        if not index.isValid():
            return

        # Selecionar a linha no local do clique direito
        table_view.selectionModel().select(
            index,
            QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows
        )

        # Obter o índice no modelo original
        source_index = proxy_model.mapToSource(index)
        selected_row = source_index.row()

        # Carregar os dados da linha selecionada
        table_name = proxy_model.sourceModel().tableName()
        df_registro_selecionado = carregar_dados_contrato(selected_row, database_path, table_name)
        self.selected_row_data = df_registro_selecionado  # Armazena os dados da linha selecionada

        if df_registro_selecionado.empty:
            QMessageBox.warning(parent, "Erro", "Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")
            return

        # Criar o menu de contexto e passar os dados para as ações
        menu = QMenu()
        for action_text, action_function in actions:
            action = QAction(action_text, parent)
            action.triggered.connect(partial(action_function, df_registro_selecionado, parent))
            menu.addAction(action)

        # Exibir o menu de contexto
        menu.exec(table_view.viewport().mapToGlobal(position))

    def get_row_data(self, row):
        column_count = self.model.columnCount()
        row_data = {self.model.headerData(col, Qt.Orientation.Horizontal): self.model.data(self.model.index(row, col)) for col in range(column_count)}
        return row_data

    def open_editar_dados_dialog(self, index):
        # Obter o índice da linha no modelo subjacente (source model)
        source_index = self.parent.proxy_model.mapToSource(index)
        row_data = self.get_row_data(source_index.row())
        df_registro_selecionado = pd.DataFrame([row_data])
        self.parent.editar_dados(df_registro_selecionado)

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
        """Obtém e armazena os dados da linha selecionada."""
        if selected.indexes():
            proxy_index = selected.indexes()[0]
            source_index = self.parent.proxy_model.mapToSource(proxy_index)

            # Obter o valor da chave primária 'id_pncp'
            selected_row = source_index.row()
            id_pncp = self.parent.model.data(
                self.parent.model.index(selected_row, self.parent.model.fieldIndex('id_pncp'))
            )

            # Obter o nome da tabela atual
            table_name = self.parent.model.tableName()

            # Obter o caminho do banco de dados usando o DatabaseATASManager
            database_path = self.parent.database_manager.db_path

            # Carregar os dados do contrato
            df_registro_selecionado = carregar_dados_contrato(selected_row, database_path, table_name)
            self.selected_row_data = df_registro_selecionado

            if not df_registro_selecionado.empty:
                logging.debug(f"Registro selecionado: {df_registro_selecionado.iloc[0].to_dict()}")
            else:
                logging.warning("Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")
                QMessageBox.warning(self.parent, "Erro", "Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")


    def update_column_headers(self):
        titles = {
            'Status': 'Status',
            'Dias': 'Dias',
            'CNPJ': 'CNPJ',
            'sequencial': 'Sequencial',
            'numero_controle_ano': 'Ano',
            'numero_controle_ata': 'Número',
            'objeto': 'Objeto',
        }
        for field_name, title in titles.items():
            column = self.model.fieldIndex(field_name)
            if column >= 0:
                self.model.setHeaderData(column, Qt.Orientation.Horizontal, title)

    def hide_unwanted_columns(self):
        # Inclua a coluna de ícones no conjunto de colunas visíveis
        visible_columns = {0, 1, 2, 4, 5, 7, 14}
        for column in range(self.model.columnCount()):
            if column not in visible_columns:
                self.table_view.hideColumn(column)

    
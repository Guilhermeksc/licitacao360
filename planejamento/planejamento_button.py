from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
from utils.treeview_utils import load_images, create_button, save_dataframe_to_excel
import pandas as pd
import os
from planejamento.popup_relatorio import ReportDialog
from planejamento.escalacao_pregoeiro import EscalarPregoeiroDialog
from planejamento.autorizacao import AutorizacaoAberturaLicitacaoDialog
from planejamento.fluxo_dos_processos import ProcessFlowDialog
from planejamento.fluxoprocesso import FluxoProcessoDialog
from planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_processos,extrair_chave_processo, carregar_dados_pregao
df_uasg = pd.read_excel(TABELA_UASG_DIR)
global df_registro_selecionado
df_registro_selecionado = None
import json
from functools import partial
import sys
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel
import sqlite3

etapas = {
    'Planejamento': None,
    'Setor Responsável': None,
    'IRP': None,
    'Edital': None,
    'Nota Técnica': None,
    'AGU': None,
    'Recomendações AGU': None,
    'Divulgado': None,
    'Impugnado': None,
    'Sessão Pública': None,
    'Em recurso': None,
    'Homologado': None,
    'Assinatura Contrato': None,
    'Concluído': None
}

class EditarDadosDialog(QDialog):
    dados_atualizados = pyqtSignal()
    def __init__(self, parent=None, dados=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Dados")
        self.setFixedSize(700, 600)

        # Cria o QGroupBox com o título 'Índices das Variáveis'
        self.groupBox = QGroupBox('Índices das Variáveis', self)

        # Cria a QScrollArea e o QWidget que será o conteúdo da QScrollArea
        self.scrollArea = QScrollArea()
        self.scrollContentWidget = QWidget()
        self.scrollLayout = QFormLayout(self.scrollContentWidget)

        # Configura a área de rolagem
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollContentWidget)

        # Configura o layout do groupBox para conter a scrollArea
        self.groupBoxLayout = QVBoxLayout(self.groupBox)
        self.groupBoxLayout.addWidget(self.scrollArea)

        self.line_edits = {}  # Dicionário para armazenar as QLineEdit
        self.dados = dados  # Dicionário com os dados a serem editados

        # Define o layout principal da QDialog
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.groupBox)

        # Customização do QGroupBox, QLabel, e QLineEdit
        self.groupBox.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 1px solid gray;
                border-radius: 10px;
                margin-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left; 
                padding: 0 3px;
                background-color: transparent;
            }
            QLabel, QLineEdit {
                font-size: 16px;
            }            
            QLabel {
                font-weight: bold;
            }
        """)

        # Adiciona o botão "Confirmar" fora do QGroupBox para que ele fique fixo
        self.confirmar_button = QPushButton("Confirmar")
        self.confirmar_button.clicked.connect(self.confirmar_edicao)
        self.mainLayout.addWidget(self.confirmar_button)

        self.init_ui()

    def init_ui(self):
        # Adiciona uma QLineEdit para cada variável no dicionário de dados
        for coluna, valor in self.dados.items():
            line_edit = QLineEdit()
            line_edit.setText(str(valor))
            self.line_edits[coluna] = line_edit
            self.scrollLayout.addRow(QLabel(coluna), line_edit)

    def confirmar_edicao(self):
        conn = sqlite3.connect(CONTROLE_DADOS)
        cursor = conn.cursor()
        dados_atualizados = {coluna: line_edit.text() for coluna, line_edit in self.line_edits.items()}        
        # Cria a parte SET da consulta SQL dinamicamente
        set_part = ', '.join([f"{coluna} = ?" for coluna in dados_atualizados.keys()])
        
        # Prepara a lista de valores para a consulta (inclui os valores seguidos pelo id no final)
        valores = list(dados_atualizados.values())
        valores.append(self.dados['id'])  # Assume que 'self.dados' contém um campo 'id' com o ID do registro a ser atualizado
        
        # Constrói e executa a consulta SQL de UPDATE
        query = f"UPDATE controle_processos SET {set_part} WHERE id = ?"
        cursor.execute(query, valores)
        conn.commit()
        conn.close()
        self.dados_atualizados.emit()
        self.accept()

class CustomTableView(QTableView):
    def __init__(self, main_app, parent=None):
        super().__init__(parent)
        self.main_app = main_app  # Armazena a referência ao aplicativo principal
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, pos):
        index = self.indexAt(pos)
        if index.isValid():
            # Passa a referência correta ao aplicativo principal
            contextMenu = TableMenu(self.main_app, index, self.model())
            contextMenu.exec(self.viewport().mapToGlobal(pos))

class TableMenu(QMenu):
    def __init__(self, main_app, index, model=None):
        super().__init__()
        self.main_app = main_app
        self.index = index
        self.model = model

        # Aplicar estilos ao menu
        self.setStyleSheet("""
            QMenu {
                background-color: #333;
                padding: 4px;
                border: 0.5px solid #dcdcdc;
                color: white;
                font-size: 12pt;
            }
            QMenu::item {
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #565656;
            }
        """)
        # Opções do menu
        actions = [
            "Editar Dados do Processo",
            "Autorização para Abertura de Licitação",
            "Portaria de Equipe de Planejamento",
            "Documento de Formalização de Demanda (DFD)",
            "Declaração de Adequação Orçamentária",
	        "Capa do Edital",
 	        "Comunicação Padronizada AGU",
	        "Comunicação Padronizada Recomendações AGU",
            "Mensagem de Divulgação de IRP",
            "Mensagem de Publicação",
            "Mensagem de Homologação",
            "Escalar Pregoeiro",
        ]

        for actionText in actions:
            action = QAction(actionText, self)
            if actionText == "Editar Dados do Processo":
                action.triggered.connect(self.editar_dados)
            elif actionText == "Escalar Pregoeiro":  # Adicionando condição para "Escalar Pregoeiro"
                action.triggered.connect(self.on_get_pregoeiro)
            else:
                action.triggered.connect(partial(self.openDialog, actionText))
            self.addAction(action)

    # No final da classe TableMenu:
    def on_get_pregoeiro(self):
        modalidade = self.df_licitacao_completo['modalidade'].iloc[0]
        dialog = EscalarPregoeiroDialog(self.df_licitacao_completo, modalidade, self)
        dialog.exec()

    def editar_dados(self):
        if self.index.isValid():
            selected_row = self.index.row()
            # Supondo que carregar_dados_pregao retorne um DataFrame pandas ou um dicionário de dados para o registro selecionado
            df_registro_selecionado = carregar_dados_pregao(selected_row, str(self.main_app.database_path))
            if df_registro_selecionado is not None and not df_registro_selecionado.empty:
                # Cria a instância do diálogo de edição passando o registro selecionado como um dicionário
                dialog = EditarDadosDialog(parent=self, dados=df_registro_selecionado.iloc[0].to_dict())
                
                # Conecta o sinal de dados atualizados ao método que irá atualizar a tabela
                dialog.dados_atualizados.connect(self.main_app.atualizar_tabela)
                
                # Exibe o diálogo de edição
                dialog.exec()
            else:
                QMessageBox.warning(self, "Atenção", "Nenhum registro selecionado ou dados não encontrados.")
        else:
            QMessageBox.warning(self, "Atenção", "Nenhuma linha selecionada.")

    def openDialog(self, actionText):
        if self.index.isValid():  # Verifica se o índice é válido
            selected_row = self.index.row()
            df_registro_selecionado = carregar_dados_pregao(selected_row, str(self.main_app.database_path))
            print("Valores de df_registro_selecionado:")
            print(df_registro_selecionado.to_string())

            if df_registro_selecionado is not None and not df_registro_selecionado.empty:
                if actionText == "Autorização para Abertura de Licitação":
                    # Presumindo que os dados já estejam no DataFrame
                    dialog = AutorizacaoAberturaLicitacaoDialog(
                        main_app=self.main_app, 
                        df_registro=df_registro_selecionado, 
                    )
                    dialog.exec()
                # Adicione outras condições aqui para diferentes ações
            else:
                QMessageBox.warning(self, "Atenção", "Nenhum registro selecionado ou dados não encontrados.")
        else:
            QMessageBox.warning(self, "Atenção", "Nenhuma linha selecionada.")

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        # Aplica o alinhamento centralizado para todas as colunas
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        super().initStyleOption(option, index)

        # Altera a cor do texto para amarelo (#fcc200) apenas para as colunas "modalidade" e "objeto"
        if index.column() == index.model().fieldIndex("modalidade") or index.column() == index.model().fieldIndex("objeto"):
            painter.save()
            painter.setPen(QColor("#fcc200"))
            # Usa o alinhamento centralizado modificado anteriormente
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, str(index.model().data(index, Qt.ItemDataRole.DisplayRole)))
            painter.restore()
        else:
            # Para outras colunas, usa o método padrão de pintura com o alinhamento já ajustado
            super().paint(painter, option, index)

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Garante que o alinhamento centralizado seja aplicado
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

class ApplicationUI(QMainWindow):
    def __init__(self, app, icons_dir):
        super().__init__()
        # Essa parte parece ser duplicada e possivelmente está causando confusão.
        self.app = app
        self.icons_dir = Path(icons_dir)
        self.database_path = Path(CONTROLE_DADOS)  # Essa é a linha importante.
        self.selectedIndex = None
        self.image_cache = {}
        self.image_cache = load_images(self.icons_dir, [
            "plus.png", "save_to_drive.png", "loading.png", "delete.png", "excel.png", "website_menu.png"
        ])
        self.database_manager = DatabaseManager(CONTROLE_DADOS)
        self.ensure_database_exists()
        self.init_ui()

    def ensure_database_exists(self):
        with self.database_manager as conn:
            # Verifica se o banco de dados existe
            if not DatabaseManager.database_exists(conn):
                # Se não existir, cria o banco de dados
                DatabaseManager.create_database(conn)
            # Garante que a tabela de controle de prazos exista
            DatabaseManager.criar_tabela_controle_prazos(conn)
                
    def init_ui(self):
        self.main_widget = QWidget(self)  # Widget principal
        self.main_layout = QVBoxLayout(self.main_widget)  # Layout principal
        self._setup_buttons_layout()

        self.table_view = CustomTableView(self)
        self.init_sql_model()

        # Cria e aplica o CustomItemDelegate para todas as colunas da QTableView
        custom_item_delegate = CustomItemDelegate(self.table_view)  # Instancia o delegate
        
        for column in range(self.model.columnCount()):
            self.table_view.setItemDelegateForColumn(column, custom_item_delegate)

        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        header = self.table_view.horizontalHeader()
        header.setStretchLastSection(True)

        for column in range(self.model.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

        self.table_view.setModel(self.model)

        # Configurações visuais usando folhas de estilo (QSS)
        self.table_view.setStyleSheet("""
        QTableView {
            background-color: black;
            color: white;
            font-size: 12pt;
            border: 1px solid black;
        }
        QHeaderView::section {
            background-color: #333;
            padding: 4px;
            border: 0.5px solid #dcdcdc;
            color: white;
            font-size: 12pt;
        }
        QTableCornerButton::section {
            background-color: transparent;
        }
        """)

        # Adiciona a QTableView ao layout principal
        self.main_layout.addWidget(self.table_view)

        # Redimensiona as colunas para se ajustarem ao conteúdo
        self.table_view.resizeColumnsToContents()
        self.table_view.selectionModel().selectionChanged.connect(self.linhaSelecionada)

        # Configura o widget principal como o central
        self.setCentralWidget(self.main_widget)

    def linhaSelecionada(self, selected, deselected):
        if selected.indexes():
            selected_row = selected.indexes()[0].row()
            df_registro_selecionado = carregar_dados_pregao(selected_row, self.database_path)
            print(df_registro_selecionado.iloc[0].to_dict())

    def _setup_buttons_layout(self):
        self.buttons_layout = QHBoxLayout()
        self._create_buttons()
        self.main_layout.addLayout(self.buttons_layout)
            
    def _create_buttons(self):
        self.buttons_layout = QHBoxLayout()
        self.button_specs = [
            # ("  Adicionar", self.image_cache['plus'], self.on_add_item, "Adiciona um novo item"),
            ("  Salvar", self.image_cache['save_to_drive'], self.on_edit_item, "Salva o dataframe em um arquivo excel('.xlsx')"),
            ("  Carregar", self.image_cache['loading'], self.carregar_tabela, "Carrega o dataframe de um arquivo existente('.xlsx' ou '.odf')"),
            ("  Excluir", self.image_cache['delete'], self.on_edit_item, "Adiciona um novo item"),
            ("  Controle do Processo", self.image_cache['website_menu'], self.on_control_process, "Abre o painel de controle do processo"),            
            ("  Abrir Planilha Excel", self.image_cache['excel'], self.on_edit_item, "Abre a planilha de controle"),
            ("    Relatório", self.image_cache['website_menu'], self.on_edit_item, "Gera um relatório dos dados")
        ]

        for text, icon, callback, tooltip in self.button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self)
            self.buttons_layout.addWidget(btn)  # Adicione o botão ao layout dos botões

    def on_control_process(self):
        print("Iniciando on_control_process...")
        with self.database_manager as conn:
            # Atualiza etapas baseadas no último sequencial de controle_prazos
            self.database_manager.verificar_e_atualizar_etapas(conn)
            # Atualiza a contagem dos dias na última etapa
            self.database_manager.atualizar_dias_na_etapa(conn)
            # Verifica e popula controle_prazos se necessário
            self.database_manager.popular_controle_prazos_se_necessario()

        # Carrega os dados de processos já com as etapas atualizadas
        df_processos = carregar_dados_processos(CONTROLE_DADOS)

        if not df_processos.empty:
            self.exibir_dialogo_process_flow(df_processos)
        else:
            print("DataFrame de processos está vazio.")

    def exibir_dialogo_process_flow(self, df_processos):
        dialog = FluxoProcessoDialog(etapas, df_processos, self.database_manager, self)
        dialog.dialogClosed.connect(self.atualizarTableView)
        dialog.exec()

    def atualizarTableView(self):
        print("Atualizando TableView...")
        with self.database_manager as conn:
            # Atualiza etapas baseadas no último sequencial de controle_prazos
            self.database_manager.verificar_e_atualizar_etapas(conn)
        
        # Depois de atualizar os dados, re-inicialize o modelo SQL para refletir as mudanças
        self.init_sql_model()

        # Verifica se os dados foram recarregados corretamente
        if self.model.rowCount() == 0:
            print("DataFrame de processos está vazio após a atualização.")
        else:
            print("Dados no TableView foram atualizados.")


    def on_edit_item(self):
        # Implementar lógica de edição aqui
        print("Editar item")

    def carregar_tabela(self):
        fileName, _ = QFileDialog.getOpenFileName(
            self, 
            "Carregar dados", 
            "", 
            "Excel Files (*.xlsx);;ODF Files (*.odt)"
        )
        if fileName:
            try:
                # Lê o arquivo selecionado
                if fileName.endswith('.xlsx'):
                    df = pd.read_excel(fileName)
                # Incluir elif para .odt se necessário e possível
                else:
                    print("Formato de arquivo não suportado.")
                    return
                # Certifique-se de que todas as colunas necessárias estejam presentes no DataFrame
                expected_columns = ["modalidade", "nup", "objeto", "uasg", "orgao_responsavel", 
                                    "sigla_om", "setor_responsavel",  "coordenador_planejamento", 
                                    "etapa", "pregoeiro", "item_pca", "portaria_PCA", "data_sessao",
                                    "data_limite_entrega_tr", "nup_portaria_planejamento", "srp", 
                                    "material_servico", "parecer_agu", "msg_irp", "data_limite_manifestacao_irp",
                                    "data_limite_confirmacao_irp", "num_irp", "om_participantes"]
                for col in expected_columns:
                    if col not in df.columns:
                        df[col] = ""  # Adiciona colunas faltantes como vazias

                # Conecta ao banco de dados e insere os dados
                conn = sqlite3.connect(self.database_path)
                df.to_sql('controle_processos', conn, if_exists='append', index=False, method="multi")
                conn.close()
                print("Dados carregados com sucesso.")
            except Exception as e:
                print(f"Erro ao carregar os dados: {e}")
                
    def init_sql_model(self):
        # Agora self.database_path já deve estar corretamente definido.
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(str(self.database_path))

        if not self.db.open():
            print("Não foi possível abrir a conexão com o banco de dados.")
            return
        else:
            print("Conexão com o banco de dados aberta com sucesso.")

        # Configura o modelo SQL para a tabela controle_processos
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable('controle_processos')
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.model.select()
        # Especifica as colunas a serem exibidas
        self.model.setHeaderData(1, Qt.Orientation.Horizontal, "Modalidade")
        self.model.setHeaderData(2, Qt.Orientation.Horizontal, "NUP")
        self.model.setHeaderData(3, Qt.Orientation.Horizontal, "Objeto")
        self.model.setHeaderData(4, Qt.Orientation.Horizontal, "UASG")
        self.model.setHeaderData(6, Qt.Orientation.Horizontal, "OM")
        self.model.setHeaderData(9, Qt.Orientation.Horizontal, "Etapa")
        self.model.setHeaderData(10, Qt.Orientation.Horizontal, "Pregoeiro")

        # Aplica o modelo ao QTableView
        self.table_view.setModel(self.model)
        print("Colunas disponíveis no modelo:")
        for column in range(self.model.columnCount()):
            print(f"Índice {column}: {self.model.headerData(column, Qt.Orientation.Horizontal)}")
            if column not in [1, 2, 3, 4, 6, 9, 10]:
                self.table_view.hideColumn(column)

    def atualizar_tabela(self):
        # Verifica se o modelo da tabela é um QSqlTableModel
        if isinstance(self.model, QSqlTableModel):
            # Para QSqlTableModel, chame o método select() para atualizar os dados
            self.model.select()
        else:
            # Se não for um QSqlTableModel, talvez seja necessário realizar outras operações para atualizar a tabela
            print("O modelo da tabela não é um QSqlTableModel. Faça as operações de atualização apropriadas aqui.")

class ContextMenu(QMenu):
    def __init__(self, main_app, index, model=None):
        super().__init__()
        self.main_app = main_app
        self.index = index
        self.model = model

        # Opções do menu
        actions = [
            "Autorização para Abertura de Licitação",
            "Portaria de Equipe de Planejamento",
            "Documento de Formalização de Demanda (DFD)",
            "Declaração de Adequação Orçamentária",
            "Mensagem de Divulgação de IRP",
            "Mensagem de Publicação",
            "Mensagem de Homologação",
            "Capa do Edital"
        ]

        for actionText in actions:
            action = QAction(actionText, self)
            action.triggered.connect(lambda checked, a=actionText: self.openDialog(a))
            self.addAction(action)
            
    def openDialog(self, actionText):
        if actionText == "Autorização para Abertura de Licitação":
            df_registro_selecionado = carregar_dados_pregao()
            print(df_registro_selecionado.to_string())
            
            if df_registro_selecionado is not None and not df_registro_selecionado.empty:
                # Presumindo que os dados já estejam no DataFrame
                dialog = AutorizacaoAberturaLicitacaoDialog(
                    main_app=self.main_app, 
                    df_registro=df_registro_selecionado, 
                )
                dialog.exec()
            else:
                QMessageBox.warning(self, "Atenção", "Nenhum registro selecionado ou arquivo de dados não encontrado.")
        else:
            msgBox = QMessageBox()
            msgBox.setWindowTitle(actionText)
            msgBox.setText(f"Ação selecionada: {actionText}")
            msgBox.exec()
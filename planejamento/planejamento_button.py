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
        id_processo = self.df_licitacao_completo['id_processo'].iloc[0]
        dialog = EscalarPregoeiroDialog(self.df_licitacao_completo, id_processo, self)
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

        # Altera a cor do texto para amarelo (#fcc200) apenas para as colunas "id_processo" e "objeto"
        if index.column() == index.model().fieldIndex("id_processo") or index.column() == index.model().fieldIndex("objeto"):
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
            ("  Adicionar Item", self.image_cache['plus'], self.on_add_item, "Adiciona um novo item ao banco de dados"),
            ("  Salvar", self.image_cache['save_to_drive'], self.salvar_tabela, "Salva o dataframe em um arquivo excel('.xlsx')"),
            ("  Carregar", self.image_cache['loading'], self.carregar_tabela, "Carrega o dataframe de um arquivo existente('.xlsx' ou '.odf')"),
            ("  Excluir", self.image_cache['delete'], self.on_edit_item, "Adiciona um novo item"),
            ("  Controle do Processo", self.image_cache['website_menu'], self.on_control_process, "Abre o painel de controle do processo"),            
            ("  Abrir Planilha Excel", self.image_cache['excel'], self.on_edit_item, "Abre a planilha de controle"),
            ("    Relatório", self.image_cache['website_menu'], self.on_report, "Gera um relatório dos dados")
        ]

        for text, icon, callback, tooltip in self.button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self)
            self.buttons_layout.addWidget(btn)  # Adicione o botão ao layout dos botões

    def on_report(self):
        dialog = ReportDialog(self.model, self.icons_dir, parent=self)
        dialog.exec()

    def on_add_item(self):
        dialog = AddItemDialog(self)
        if dialog.exec():
            item_data = dialog.get_data()
            self.save_to_database(item_data)
            self.save_to_control_prazos(item_data['id_processo'])

    def save_to_control_prazos(self, id_processo):
        with self.database_manager as conn:
            cursor = conn.cursor()
            # Verificar se a chave já existe
            cursor.execute("SELECT COUNT(*) FROM controle_prazos WHERE chave_processo = ?", (id_processo,))
            if cursor.fetchone()[0] > 0:
                # Perguntar ao usuário se deseja sobrescrever
                reply = QMessageBox.question(self, "Confirmar Sobrescrita", 
                                            "Chave de processo já existe. Deseja sobrescrever?",
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                            QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    # Deletar as informações existentes
                    cursor.execute("DELETE FROM controle_prazos WHERE chave_processo = ?", (id_processo,))
                else:
                    return  # Não continuar se o usuário escolher não sobrescrever

            # Inserir novos dados
            today = datetime.today().strftime('%Y-%m-%d')
            cursor.execute('''
                INSERT INTO controle_prazos (chave_processo, etapa, data_inicial, sequencial)
                VALUES (?, ?, ?, ?)
            ''', (id_processo, "Planejamento", today, 1))
            conn.commit()
            
    def save_to_database(self, data):
        with self.database_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO controle_processos (
                    tipo, numero, ano, objeto, sigla_om, material_servico, 
                    id_processo, nup, orgao_responsavel, uasg) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (data['tipo'], data['numero'], data['ano'], data['objeto'], 
                      data['sigla_om'], data['material_servico'], data['id_processo'], 
                      data['nup'], data['orgao_responsavel'], data['uasg'])
            )
            conn.commit()
        self.init_sql_model()

    def salvar_tabela(self):
        # Cria um DataFrame vazio
        column_count = self.model.columnCount()
        row_count = self.model.rowCount()
        headers = [self.model.headerData(i, Qt.Orientation.Horizontal) for i in range(column_count)]
        data = []

        # Preenche o DataFrame com os dados do modelo
        for row in range(row_count):
            row_data = []
            for column in range(column_count):
                index = self.model.index(row, column)
                row_data.append(self.model.data(index))
            data.append(row_data)

        df = pd.DataFrame(data, columns=headers)

        # Define o caminho do arquivo Excel
        excel_path = os.path.join(os.path.expanduser("~"), "Dados_Exportados.xlsx")

        # Salva o DataFrame como Excel
        df.to_excel(excel_path, index=False, engine='openpyxl')

        # Abre o arquivo Excel
        os.startfile(excel_path)


    def carregar_tabela(self):
        """
        Método chamado pelo botão 'Carregar' para carregar dados do arquivo .xlsx.
        """
        self.database_manager.carregar_tabela(self)

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
        dialog = FluxoProcessoDialog(etapas, df_processos, self.database_manager, self.database_path, self)
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
        self.model.setHeaderData(4, Qt.Orientation.Horizontal, "ID Processo")
        self.model.setHeaderData(5, Qt.Orientation.Horizontal, "NUP")
        self.model.setHeaderData(6, Qt.Orientation.Horizontal, "Objeto")
        self.model.setHeaderData(8, Qt.Orientation.Horizontal, "UASG")
        self.model.setHeaderData(10, Qt.Orientation.Horizontal, "OM")
        self.model.setHeaderData(13, Qt.Orientation.Horizontal, "Etapa")
        self.model.setHeaderData(14, Qt.Orientation.Horizontal, "Pregoeiro")

        # Aplica o modelo ao QTableView
        self.table_view.setModel(self.model)
        # print("Colunas disponíveis no modelo:")
        for column in range(self.model.columnCount()):
            # print(f"Índice {column}: {self.model.headerData(column, Qt.Orientation.Horizontal)}")
            if column not in [4, 5, 6, 8, 10, 13, 14]:
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

from datetime import datetime

class AddItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.database_path = Path(CONTROLE_DADOS) 
        self.setWindowTitle("Adicionar Item")
        self.layout = QVBoxLayout(self)

        self.options = [
            ("Pregão Eletrônico (PE)", "Pregão Eletrônico"),
            ("Concorrência (CC)", "Concorrência"),
            ("Dispensa Eletrônica (DE)", "Dispensa Eletrônica"),
            ("Termo de Justificativa de Dispensa Eletrônica (TJDL)", "Termo de Justificativa de Dispensa Eletrônica"),
            ("Termo de Justificativa de Inexigibilidade de Licitação (TJIL)", "Termo de Justificativa de Inexigibilidade de Licitação")
        ]

        # Linha 1: Tipo, Número, Ano
        hlayout1 = QHBoxLayout()
        self.tipo_cb = QComboBox()
        self.numero_le = QLineEdit()
        self.ano_le = QLineEdit()

        # Carregar o próximo número disponível
        self.load_next_numero()

        [self.tipo_cb.addItem(text) for text, _ in self.options]
        self.tipo_cb.setCurrentText("Pregão Eletrônico (PE)")  # Valor padrão
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
        hlayout3.addWidget(self.objeto_le)
        self.layout.addLayout(hlayout3)

        # Linha 4: OM
        hlayout4 = QHBoxLayout()
        self.nup_le = QLineEdit()
        self.sigla_om_cb = QComboBox()  # Alterado para QComboBox
        self.update_om_btn = QPushButton("Atualizar OM")
        self.update_om_btn.clicked.connect(self.update_om)
        hlayout4.addWidget(QLabel("Nup:"))
        hlayout4.addWidget(self.nup_le)
        hlayout4.addWidget(QLabel("OM:"))
        hlayout4.addWidget(self.sigla_om_cb)  # Usando QComboBox
        hlayout4.addWidget(self.update_om_btn)
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
        self.save_btn = QPushButton("Salvar")
        self.save_btn.clicked.connect(self.accept)
        self.layout.addWidget(self.save_btn)
        self.load_sigla_om()

    def load_next_numero(self):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(numero) FROM controle_processos")
                max_number = cursor.fetchone()[0]
                next_number = 1 if max_number is None else int(max_number) + 1
                self.numero_le.setText(str(next_number))
        except Exception as e:
            print(f"Erro ao carregar o próximo número: {e}")

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
            "Pregão Eletrônico (PE)": "PE",
            "Concorrência (CC)": "CC",
            "Dispensa Eletrônica (DE)": "DE",
            "Termo de Justificativa de Dispensa Eletrônica (TJDL)": "TJDL",
            "Termo de Justificativa de Inexigibilidade de Licitação (TJIL)": "TJIL"
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

    def update_om(self):
        # Supondo que import_uasg_to_db atualize o banco de dados corretamente
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione o arquivo Excel",
            "",  # Diretório inicial, pode ser ajustado conforme necessidade
            "Arquivos Excel (*.xlsx);;Todos os Arquivos (*)"
        )

        if filename:
            self.import_uasg_to_db(filename)
            self.load_sigla_om() 

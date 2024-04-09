from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
from utils.treeview_utils import load_images, create_button, save_dataframe_to_excel
import pandas as pd
import os
import datetime
from datetime import datetime
import openpyxl
from planejamento.popup_relatorio import ReportDialog
from planejamento.escalacao_pregoeiro import EscalarPregoeiroDialog
from planejamento.autorizacao import AutorizacaoAberturaLicitacaoDialog
from planejamento.fluxo_dos_processos import ProcessFlowDialog
from planejamento.utilidades_planejamento import inicializar_json_do_excel, carregar_dados_processos, carregar_ou_criar_arquivo_json, extrair_chave_processo, carregar_dados_pregao
df_uasg = pd.read_excel(TABELA_UASG_DIR)
global df_registro_selecionado
df_registro_selecionado = None
from bs4 import BeautifulSoup
import json
from datetime import datetime
from functools import partial
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel
from pathlib import Path
import sqlite3

CONTROLE_DADOS = DATABASE_DIR / "controle_dados.db"

class EditarDadosDialog(QDialog):
    def __init__(self, parent=None, dados=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Dados")
        self.layout = QFormLayout(self)
        self.line_edits = {}  # Dicionário para armazenar as QLineEdit
        self.dados = dados  # DataFrame com os dados a serem editados
        self.init_ui()

    def init_ui(self):
        # Adiciona uma QLineEdit para cada variável no DataFrame
        for coluna, valor in self.dados.items():
            line_edit = QLineEdit(self)
            line_edit.setText(str(valor))  # Preenche o QLineEdit com o valor atual
            self.line_edits[coluna] = line_edit
            self.layout.addRow(coluna, line_edit)

        # Botão para confirmar as alterações
        confirmar_button = QPushButton("Confirmar", self)
        confirmar_button.clicked.connect(self.confirmar_edicao)
        self.layout.addRow(confirmar_button)

    def confirmar_edicao(self):
        # Atualiza os valores no DataFrame com os novos valores das QLineEdit
        for coluna, line_edit in self.line_edits.items():
            novo_valor = line_edit.text()
            self.dados[coluna] = novo_valor

        # Fecha o QDialog
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
            df_registro_selecionado = carregar_dados_pregao(selected_row, str(self.main_app.database_path))
            if df_registro_selecionado is not None and not df_registro_selecionado.empty:
                dialog = EditarDadosDialog(parent=self, dados=df_registro_selecionado.iloc[0].to_dict())
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    # O usuário confirmou as alterações, os dados foram atualizados no DataFrame
                    print("Dados atualizados:", df_registro_selecionado.iloc[0].to_dict())
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

class YellowTextDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        # Altera a cor do texto para a cor hexadecimal #fcc200 apenas para as colunas especificadas
        if index.column() == index.model().fieldIndex("modalidade") or index.column() == index.model().fieldIndex("objeto"):
            painter.save()
            # Configura a cor do pincel para amarelo #fcc200
            painter.setPen(QColor("#fcc200"))
            value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignLeft, str(value))
            painter.restore()
        else:
            # Para outras colunas, usa o método padrão de pintura
            super().paint(painter, option, index)

class ApplicationUI(QMainWindow):
    itemSelected = pyqtSignal(str) 

    def __init__(self, app, icons_dir):
        super().__init__()
        self.app = app
        self.icons_dir = Path(icons_dir)
        self.database_path = Path(CONTROLE_DADOS)
        self.selectedIndex = None 
        self.image_cache = {}
        self.image_cache = load_images(self.icons_dir, [
            "plus.png", "save_to_drive.png", "loading.png", "delete.png", "excel.png", "website_menu.png"
        ])
        self.ensure_database_exists()
        self.init_ui()

    def ensure_database_exists(self):
        # Verifica se o arquivo do banco de dados existe
        if not self.database_path.exists():
            self.create_database()

    def create_database(self):
        # Cria o banco de dados e a tabela controle_processos com as colunas especificadas
        connection = sqlite3.connect(self.database_path)
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS controle_processos (
                id INTEGER PRIMARY KEY,
                modalidade TEXT,
                nup TEXT,
                objeto TEXT,
                uasg TEXT,
                orgao_responsavel TEXT,
                sigla_om TEXT,
                setor_responsavel TEXT,
                coordenador_planejamento TEXT,
                etapa TEXT,
                pregoeiro TEXT,
                item_pca TEXT,
                portaria_PCA TEXT,
                data_sessao TEXT
            )
        ''')
        connection.commit()
        connection.close()

    def init_ui(self):
        self.main_widget = QWidget(self)  # Widget principal
        self.main_layout = QVBoxLayout(self.main_widget)  # Layout principal
        self._setup_buttons_layout()

        self.table_view = CustomTableView(self)
        self.init_sql_model()
        # Aplica o delegado personalizado para a QTableView
        yellow_delegate = YellowTextDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(self.model.fieldIndex("modalidade"), yellow_delegate)
        self.table_view.setItemDelegateForColumn(self.model.fieldIndex("objeto"), yellow_delegate)

        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        # Configura a seleção para ser de uma única linha por vez
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        # Continuação do seu código de inicialização, como configurar o modelo e estilos...
        self.table_view.setModel(self.model)
        header = self.table_view.horizontalHeader()
        header.setStretchLastSection(True)
        for column in range(self.model.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

        # Configurações visuais usando folhas de estilo (QSS)
        self.table_view.setStyleSheet("""
        QTableView {
            background-color: black;
            color: white;
            font-size: 12pt;
        }
        QHeaderView::section {
            background-color: #333;
            padding: 4px;
            border: 0.5px solid #dcdcdc;
            color: white;
            font-size: 12pt;
        }
        QHeaderView {
            background-color: black;
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
        # Carrega os dados dos processos antes de criar o diálogo
        df_processos = carregar_dados_processos(CONTROLE_DADOS)
        if not df_processos.empty:
            carregar_ou_criar_arquivo_json(df_processos, PROCESSOS_JSON_PATH)
            
            self.dialog = ProcessFlowDialog(etapas, df_processos, self)
            self.dialog.show()  # Mostra o diálogo
        else:
            self.dialog.raise_()  # Traz o diálogo para o primeiro plano se já estiver aberto
            self.dialog.activateWindow()

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
                
                # Preparar df para inserção no SQLite
                # Certifique-se de que todas as colunas necessárias estejam presentes no DataFrame
                expected_columns = ["modalidade", "nup", "objeto", "uasg", "orgao_responsavel", 
                                    "sigla_om", "setor_responsavel",  "coordenador_planejamento", 
                                    "etapa", "pregoeiro", "item_pca", "portaria_PCA", "data_sessao"]
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
        # Conexão com o banco de dados SQLite
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(str(self.database_path))
        if not self.db.open():
            print("Não foi possível abrir a conexão com o banco de dados.")
            return
        
        # Configuração do modelo SQL
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable('controle_processos')
        # Configura a estratégia de edição para submeter automaticamente as mudanças ao banco de dados
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        
        self.model.select()

        # Especifica as colunas a serem exibidas
        self.model.setHeaderData(1, Qt.Orientation.Horizontal, "Modalidade")
        self.model.setHeaderData(2, Qt.Orientation.Horizontal, "NUP")
        self.model.setHeaderData(3, Qt.Orientation.Horizontal, "Objeto")
        self.model.setHeaderData(4, Qt.Orientation.Horizontal, "UASG")
        self.model.setHeaderData(6, Qt.Orientation.Horizontal, "Sigla Órgão")
        self.model.setHeaderData(9, Qt.Orientation.Horizontal, "Etapa")
        self.model.setHeaderData(10, Qt.Orientation.Horizontal, "Pregoeiro")

        # Aplica o modelo ao QTableView
        self.table_view.setModel(self.model)
        for column in range(self.model.columnCount()):
            if column not in [1, 2, 3, 4, 6, 9, 10]:
                self.table_view.hideColumn(column)  # Oculta as colunas não necessárias

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

    def carregar_dados_pregao(self):
        try:
            df = pd.read_csv(ITEM_SELECIONADO_PATH)
            return df
        except Exception as e:
            QMessageBox.warning(None, "Erro", f"Erro ao carregar dados: {e}")
            # Retorna um DataFrame vazio em vez de None
            return pd.DataFrame()
            
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

class ApplicationUI2(QMainWindow):
    itemSelected = pyqtSignal(str, str, str)  # Sinal com dois argumentos de string

    NOME_COLUNAS = {
        'mod': 'Mod.',
        'num_pregao': 'N',
        'ano_pregao': 'Ano',
        # 'item_pca': 'Item PCA',
        # 'portaria_PCA': 'Portaria_PCA',	
        # 'data_sessao': 'Data Sessão',
        'nup': 'NUP',
        'objeto': 'Objeto',
        'uasg': 'UASG',
        # 'orgao_responsavel': 'Órgão Responsável',
        'sigla_om': 'Sigla Órgão',
        'setor_responsavel': 'Demandante',
        # 'coordenador_planejamento': 'Coordenador',
        'etapa': 'Etapa',
        'pregoeiro': 'Pregoeiro',
    }

    dtypes = {
        'mod': str,
        'num_pregao': int,
        'ano_pregao': int,
        'item_pca': str,
        'portaria_PCA': str,	
        'data_sessao': str,
        'nup': str,
        'objeto': str,
        'uasg': str,
        'orgao_responsavel': str,
        'sigla_om': str,
        'setor_responsavel': str,
        'coordenador_planejamento': str,
        'etapa': str,
        'pregoeiro': str
    }

    def __init__(self, app, icons_dir, database_dir, lv_final_dir):

        super().__init__()
        self.icons_dir = Path(icons_dir)
        self.database_dir = Path(database_dir)
        self.lv_final_dir = Path(lv_final_dir)
        self.app = app  # Armazenar a instância do App
        
        # Carregar df_uasg uma única vez aqui
        self.df_uasg = pd.read_excel(TABELA_UASG_DIR)     
        self.columns_treeview = list(self.NOME_COLUNAS.keys())
        self.image_cache = {}

        inicializar_json_do_excel(CONTROLE_PROCESSOS_DIR, PROCESSOS_JSON_PATH)

        # Carregar os dados de licitação no início, removendo a inicialização redundante
        self.df_licitacao_completo = pd.read_excel(CONTROLE_PROCESSOS_DIR, converters={'num_pregao': lambda x: self.convert_to_int(x)})
        # print("Valores de índices em df_licitacao_completo:")
        # for index in self.df_licitacao_completo.index:
        #     print(f"Índice: {index}, Valor: {self.df_licitacao_completo.loc[index].to_dict()}")

        self.image_cache = load_images(self.icons_dir, [
            "plus.png", "save_to_drive.png", "loading.png", "delete.png", "excel.png", "website_menu.png"
        ])
        self.setup_ui()
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.openContextMenu)

    def openContextMenu(self, position):
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        contextMenu = ContextMenu(self, index, self.model)
        contextMenu.exec(self.tree_view.viewport().mapToGlobal(position))
        
    def convert_to_int(self, cell_value):
        try:
            return int(cell_value)
        except ValueError:
            return pd.NA  # or some default value or error handling pd.NA  # or a default value like 0 or -1 depending on your requirements

    def _get_image(self, image_file_name):
        # Método para obter imagens do cache ou carregar se necessário
        if image_file_name not in self.image_cache:
            image_path = self.icons_dir / image_file_name
            self.image_cache[image_file_name] = QIcon(str(image_path))  # Usando QIcon para compatibilidade com botões
        return self.image_cache[image_file_name]

    def setup_ui(self):
        self._setup_central_widget()
        self._setup_treeview()  # Configura o QTreeView
        self._adjust_column_widths() 
        self._setup_buttons_layout()
        self.main_layout.addWidget(self.tree_view)
        self._load_data()
        self.tree_view.setStyleSheet("""
            QTreeView, QHeaderView {
                background-color: black;
                color: white;
                font-size: 12pt;
            }
            QTreeView::item:selected {
                background-color: #5682a3;
                color: white;
            }
            QHeaderView::section {
                background-color: #333;
                padding: 4px;
                border: 1px solid #dcdcdc;
                color: white;
                font-size: 12pt;
            }
        """)
    def _setup_central_widget(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
    def _setup_buttons_layout(self):
        self.buttons_layout = QHBoxLayout()
        self._create_buttons()
        self.main_layout.addLayout(self.buttons_layout)
            
    def _create_buttons(self):
        self.buttons_layout = QHBoxLayout()
        self.button_specs = [
            # ("  Adicionar", self.image_cache['plus'], self.on_add_item, "Adiciona um novo item"),
            ("  Salvar", self.image_cache['save_to_drive'], self.on_save_data, "Salva o dataframe em um arquivo excel('.xlsx')"),
            ("  Carregar", self.image_cache['loading'], self.on_load_data, "Carrega o dataframe de um arquivo existente('.xlsx' ou '.odf')"),
            ("  Excluir", self.image_cache['delete'], self.on_delete_item, "Adiciona um novo item"),
            ("  Controle do Processo", self.image_cache['website_menu'], self.on_control_process, "Abre o painel de controle do processo"),            
            ("  Escalar Pregoeiro", self.image_cache['delete'], self.on_get_pregoeiro, "Escala um novo pregoeiro para o pregão selecionado"),
            ("  Abrir Planilha Excel", self.image_cache['excel'], self.abrir_planilha_controle, "Abre a planilha de controle"),
            ("    Relatório", self.image_cache['website_menu'], self.on_generate_report, "Gera um relatório dos dados")
        ]

        for text, icon, callback, tooltip in self.button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self)
            self.buttons_layout.addWidget(btn)  # Adicione o botão ao layout dos botões

    def on_get_pregoeiro(self):
        index = self.tree_view.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Seleção", "Por favor, selecione um item da lista.")
            return
        # Ajuste os índices das colunas conforme a estrutura do seu modelo
        mod_index = self.tree_view.model().index(index.row(), 0)
        num_pregao_index = self.tree_view.model().index(index.row(), 1)
        ano_pregao_index = self.tree_view.model().index(index.row(), 2)

        mod = self.tree_view.model().data(mod_index)
        num_pregao = self.tree_view.model().data(num_pregao_index)
        ano_pregao = self.tree_view.model().data(ano_pregao_index)

        # Agora, você pode passar esses valores para o diálogo
        dialog = EscalarPregoeiroDialog(self.df_licitacao_completo, mod, ano_pregao, num_pregao, self)
        dialog.exec()

    def on_generate_report(self):
        dialog = ReportDialog(self.df_licitacao_completo, self.icons_dir, self)
        dialog.exec()

    def abrir_planilha_controle(self):
        file_path = str(CONTROLE_PROCESSOS_DIR)  # Defina o caminho do arquivo aqui
        try:
            os.startfile(file_path)
        except Exception as e:
            print(f"Erro ao abrir o arquivo: {e}")

    def _setup_treeview(self):
        # Cria uma nova instância do modelo
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([self.NOME_COLUNAS[col] for col in self.NOME_COLUNAS])

        # Configurações do QTreeView
        self.tree_view = QTreeView(self)
        self.tree_view.setModel(self.model)
        self.tree_view.clicked.connect(self._on_item_click)
        self.tree_view.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.model.dataChanged.connect(self._on_item_changed)

        # Configuração para tratar o clique com o botão direito
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.onCustomContextMenuRequested)

        # Adiciona o QTreeView ao layout principal
        self.main_layout.addWidget(self.tree_view)

        # Ajusta as larguras das colunas
        self._adjust_column_widths()

    def onCustomContextMenuRequested(self, position):
        # Seleciona a linha antes de mostrar o menu de contexto
        index = self.tree_view.indexAt(position)
        if index.isValid():
            self.tree_view.selectionModel().select(index, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
            self._on_item_click(index)  # Chamada para a função que trata a seleção de item
            # Aqui você pode implementar a abertura do menu de contexto se necessário
            
    def _adjust_column_widths(self):
        header = self.tree_view.header()
        header.setStretchLastSection(True)

        # Configura todas as colunas para ajustar-se ao conteúdo
        for column in range(self.model.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

    def on_context_menu(self, point):
        # Obter o índice do item sob o cursor quando o menu de contexto é solicitado
        index = self.tree_view.indexAt(point)
        
        if index.isValid():
            # Chamar _on_item_click se o índice é válido
            self._on_item_click(index)

            # Criar o menu de contexto
            context_menu = QMenu(self.tree_view)

            # Configurar o estilo do menu de contexto
            context_menu.setStyleSheet("QMenu { font-size: 12pt; }")

            # Adicionar outras ações ao menu
            edit_action = context_menu.addAction(QIcon(str(self.icons_dir / "engineering.png")), "Editar")
            delete_action = context_menu.addAction(QIcon(str(self.icons_dir / "delete.png")), "Excluir")
            view_action = context_menu.addAction(QIcon(str(self.icons_dir / "search.png")), "Visualizar")

            # Conectar ações a métodos
            edit_action.triggered.connect(self.on_edit_item)
            delete_action.triggered.connect(self.on_delete_item)
            view_action.triggered.connect(self.on_view_item)

            # Executar o menu de contexto na posição do cursor
            context_menu.exec(self.tree_view.viewport().mapToGlobal(point))

    def on_edit_item(self):
        # Implementar lógica de edição aqui
        print("Editar item")
    
    def on_save_data(self):
        try:
            # Preencher automaticamente valores NaN na coluna 'etapa' com 'Planejamento'
            self.df_licitacao_completo['etapa'] = self.df_licitacao_completo['etapa'].fillna('Planejamento')

            # Salvar o DataFrame no arquivo Excel
            self.df_licitacao_completo.to_excel(CONTROLE_PROCESSOS_DIR, index=False)

            QMessageBox.information(self, "Sucesso", "Dados salvos com sucesso!")
        except PermissionError:
            QMessageBox.warning(self, "Erro de Permissão", "Não foi possível salvar o arquivo. Por favor, feche o arquivo Excel e tente novamente.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao salvar o arquivo: {str(e)}")

    def on_load_data(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo", "", "Excel Files (*.xlsx *.xls);;ODF Files (*.odf)")
        if not file_name:
            return 
        try:
            loaded_df = pd.read_excel(file_name, dtype=self.dtypes)
            self.df_licitacao_completo = loaded_df
            self.model.clear()
            self.model.setHorizontalHeaderLabels([self.NOME_COLUNAS[col] for col in self.columns_treeview])

            # Preenche o QTreeView com os dados carregados
            for _, row in self.df_licitacao_completo.iterrows():
                items = [QStandardItem(str(row[col])) for col in self.columns_treeview]
                self.model.appendRow(items)

            # Chama a função para ajustar a largura das colunas
            self._adjust_column_widths()

            QMessageBox.information(self, "Sucesso", "Dados carregados com sucesso do arquivo.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {e}")

    def on_delete_item(self):
        # Obter o índice do item selecionado
        current_index = self.tree_view.currentIndex()
        if not current_index.isValid():
            QMessageBox.warning(self, "Seleção", "Por favor, selecione um item para excluir.")
            return

        # Obter o número do pregão e o ano do pregão do item selecionado
        row = current_index.row()
        num_pregao = self.model.item(row, self.columns_treeview.index('num_pregao')).text()
        ano_pregao = self.model.item(row, self.columns_treeview.index('ano_pregao')).text()

        # Remover a linha do modelo QTreeView
        self.model.removeRow(row)

        # Atualizar o DataFrame
        self.df_licitacao_completo = self.df_licitacao_completo[
            ~((self.df_licitacao_completo['num_pregao'].astype(str) == num_pregao) &
            (self.df_licitacao_completo['ano_pregao'].astype(str) == ano_pregao))
        ]

        # Salvar o DataFrame atualizado no arquivo Excel
        save_dataframe_to_excel(self.df_licitacao_completo, CONTROLE_PROCESSOS_DIR)

        QMessageBox.information(self, "Sucesso", "Item excluído com sucesso.")

    def on_view_item(self):
        # Implementar lógica de visualização aqui
        print("Visualizar item")

    def _load_data_to_treeview(self):
        # Atualiza o modelo com dados atuais do DataFrame
        self.model.clear()  # Limpa o modelo atual
        self.model.setHorizontalHeaderLabels([self.NOME_COLUNAS[col] for col in self.columns_treeview])

        # Preenche o QTreeView com os dados do DataFrame
        for _, row in self.df_licitacao_completo.iterrows():
            items = [QStandardItem(str(row[col])) for col in self.columns_treeview]
            self.model.appendRow(items)

        # Ajusta as larguras das colunas após carregar os dados
        self._adjust_column_widths()

    def _on_item_changed(self, top_left_index, bottom_right_index, roles):
        if Qt.ItemDataRole.EditRole in roles:
            # Salvar a posição atual do scrollbar
            scrollbar = self.tree_view.verticalScrollBar()
            old_scroll_pos = scrollbar.value()

            row = top_left_index.row()
            column = top_left_index.column()
            column_name = self.columns_treeview[column]

            # Obter o valor atualizado
            new_value = str(self.model.itemFromIndex(top_left_index).text())

            # Atualizar o DataFrame se a coluna UASG foi alterada
            if column_name == 'uasg':
                uasg_data = self.df_uasg[self.df_uasg['uasg'].astype(str) == new_value]

                # Se encontrou a UASG correspondente, atualizar as colunas no DataFrame
                if not uasg_data.empty:
                    orgao_responsavel = uasg_data['orgao_responsavel'].iloc[0]
                    sigla_om = uasg_data['sigla_om'].iloc[0]

                    # Atualizar o DataFrame df_licitacao_completo
                    self.df_licitacao_completo.loc[
                        (self.df_licitacao_completo['num_pregao'].astype(str) == self.model.item(row, self.columns_treeview.index('num_pregao')).text()) &
                        (self.df_licitacao_completo['ano_pregao'].astype(str) == self.model.item(row, self.columns_treeview.index('ano_pregao')).text()),
                        ['orgao_responsavel', 'sigla_om']
                    ] = [orgao_responsavel, sigla_om]

            # Obter os valores de identificação únicos (num_pregao e ano_pregao)
            num_pregao = self.model.item(row, self.columns_treeview.index('num_pregao')).text()
            ano_pregao = self.model.item(row, self.columns_treeview.index('ano_pregao')).text()

            # Atualizar o DataFrame para todas as outras colunas
            self.df_licitacao_completo.loc[
                (self.df_licitacao_completo['num_pregao'].astype(str) == num_pregao) &
                (self.df_licitacao_completo['ano_pregao'].astype(str) == ano_pregao),
                column_name
            ] = new_value

            # Salvar o DataFrame atualizado no arquivo Excel
            save_dataframe_to_excel(self.df_licitacao_completo, CONTROLE_PROCESSOS_DIR)

            self._load_data_to_treeview()

            # Restaurar a posição do scrollbar
            scrollbar.setValue(old_scroll_pos)

            # Garantir que a linha editada esteja visível
            self.tree_view.scrollTo(self.model.index(row, 0), QAbstractItemView.ScrollHint.PositionAtCenter)

    def _load_data(self):
        try:
            self.df_licitacao_completo = pd.read_excel(CONTROLE_PROCESSOS_DIR, dtype=self.dtypes)

            # Preencher automaticamente valores NaN na coluna 'etapa' com 'Planejamento'
            self.df_licitacao_completo['etapa'] = self.df_licitacao_completo['etapa'].fillna('Planejamento')

            for _, row in self.df_licitacao_completo.iterrows():
                items = [QStandardItem(str(row[col])) for col in self.NOME_COLUNAS]
                self.model.appendRow(items)
        except Exception as e:
            print(f"Ocorreu um erro ao carregar os dados: {e}")
        self.df_licitacao_exibicao = self.df_licitacao_completo[self.columns_treeview]
        self._populate_treeview()

    def _populate_treeview(self):
        """Populate the treeview with the loaded data."""
        self.model.removeRows(0, self.model.rowCount())
        for index, row in self.df_licitacao_exibicao.iterrows():
            items = [QStandardItem(str(row[col])) for col in self.columns_treeview]
            self.model.appendRow(items)

    def _on_item_click(self, index):
        # Obtenha os valores do item selecionado
        mod = self.model.item(index.row(), self.columns_treeview.index('mod')).text()
        num_pregao = self.model.item(index.row(), self.columns_treeview.index('num_pregao')).text()
        ano_pregao = self.model.item(index.row(), self.columns_treeview.index('ano_pregao')).text()

        print(f"Emitindo sinal para {mod} {num_pregao}/{ano_pregao}")  # Adicione isto para depuração
        self.itemSelected.emit(mod, num_pregao, ano_pregao)

        # Chama o método para processar e salvar o item selecionado
        selected_values = self._get_selected_item_values()
        if selected_values:
            self._process_selected_item(selected_values)

    def _get_selected_item_values(self):
        row = self.tree_view.currentIndex().row()
        if row == -1:
            return []  # Nenhuma linha selecionada

        values = []
        for col in range(self.model.columnCount()):
            item = self.model.item(row, col)
            if item is not None:
                values.append(item.text())
            else:
                values.append("")  # Se não houver item, adicione uma string vazia

        return values

    def _process_selected_item(self, selected_values):
        """Process the selected item."""
        # Recarregar os dados mais recentes do arquivo Excel
        self.df_licitacao_completo = pd.read_excel(CONTROLE_PROCESSOS_DIR, dtype=self.dtypes)

        mod, num_pregao, ano_pregao = selected_values[:3]

        # Filtra o DataFrame completo para encontrar a linha com o num_pregao e ano_pregao correspondentes
        registro_completo = self.df_licitacao_completo[
            (self.df_licitacao_completo['mod'].astype(str).str.strip() == mod) &            
            (self.df_licitacao_completo['num_pregao'].astype(str).str.strip() == num_pregao) &
            (self.df_licitacao_completo['ano_pregao'].astype(str).str.strip() == ano_pregao)
        ]

        if registro_completo.empty:
            # Se nenhum registro for encontrado, retorne False
            return False

        global df_registro_selecionado  # Declare o uso da variável global
        self.itemSelected.emit(mod, num_pregao, ano_pregao)

        df_registro_selecionado = pd.DataFrame(registro_completo)
        df_registro_selecionado.to_csv(ITEM_SELECIONADO_PATH, index=False, encoding='utf-8-sig')


        self.app.pregao_selecionado()

        return True

    def run(self):
        """Run the application."""
        self.show()
        self._adjust_column_widths()  

    def on_control_process(self):
        # Carregar os dados dos processos antes de criar a dialog
        df_processos = carregar_dados_processos(CONTROLE_PROCESSOS_DIR)
        if not df_processos.empty:
            carregar_ou_criar_arquivo_json(df_processos, PROCESSOS_JSON_PATH)
        
            self.dialog = ProcessFlowDialog(etapas, df_processos, self)
            self.dialog.show()  # Mostra o diálogo
        else:
            self.dialog.raise_()  # Traz o diálogo para o primeiro plano se já estiver aberto
            self.dialog.activateWindow()
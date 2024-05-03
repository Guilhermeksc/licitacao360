from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
from utils.treeview_utils import load_images, create_button, save_dataframe_to_excel
import pandas as pd
import os
from planejamento.capa_edital import CapaEdital
from planejamento.checklist import ChecklistWidget
from planejamento.msg_planejamento import MSGIRP, MSGHomolog, MSGPublicacao
from planejamento.dfd import GerarDFD
from planejamento.cp_agu import CPEncaminhamentoAGU
from planejamento.editar_dados import EditarDadosDialog
from planejamento.adicionar_itens import AddItemDialog
from planejamento.popup_relatorio import ReportDialog
from planejamento.escalar_pregoeiro import EscalarPregoeiroDialog
from planejamento.autorizacao import AutorizacaoAberturaLicitacaoDialog
from planejamento.edital import EditalDialog
from planejamento.fluxoprocesso import FluxoProcessoDialog
from planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_processos,extrair_chave_processo, carregar_dados_pregao
df_uasg = pd.read_excel(TABELA_UASG_DIR)
global df_registro_selecionado
df_registro_selecionado = None
from functools import partial
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel
from datetime import datetime

etapas = {
    'Planejamento': None,
    'Setor Responsável': None,
    'IRP': None,
    'Montagem do Processo': None,
    'Nota Técnica': None,
    'AGU': None,
    'Recomendações AGU': None,
    'Pré-Publicação': None,
    'Impugnado': None,
    'Sessão Pública': None,
    'Em recurso': None,
    'Homologado': None,
    'Assinatura Contrato': None,
    'Concluído': None
}


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setFixedSize(600, 400)  # Tamanho total da janela de diálogo
        self.parent_app = parent
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
        QDialog {
            font-size: 12pt;
            color: #333;
            background-color: #f0f0f0;
        }
        QGroupBox {
            font-size: 12pt;
            border: 2px solid #6c6c6c;
            border-radius: 5px;
            margin-top: 2ex;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
            color: #444;
        }
        QLineEdit, QPushButton, QLabel, QComboBox {
            font-size: 12pt;
        }
        QPushButton {
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 5px;
            background-color: #e7e7e7;
        }
        QPushButton:hover {
            background-color: #d7d7d7;
        }
        """)
        main_layout = QVBoxLayout(self)  # Único layout vertical para todo o diálogo

        # Configurar OM/UASG
        om_uasg_layout = QHBoxLayout()
        om_uasg_btn = QPushButton("Abrir")
        om_uasg_btn.clicked.connect(self.open_om_uasg)
        om_uasg_layout.addWidget(QLabel("Configurar OM/UASG"))
        om_uasg_layout.addWidget(om_uasg_btn)
        main_layout.addLayout(om_uasg_layout)

        # Configurar Local de Salvamento dos Arquivos
        file_save_layout = QHBoxLayout()
        file_save_btn = QPushButton("Definir novo local")
        file_save_btn.clicked.connect(self.define_file_save_location)
        file_save_layout.addWidget(QLabel("Local de Salvamento dos Arquivos"))
        file_save_layout.addWidget(file_save_btn)
        main_layout.addLayout(file_save_layout)

        # Configurar Agentes Responsáveis
        responsaveis_layout = QHBoxLayout()
        responsaveis_btn = QPushButton("Definir Agentes")
        responsaveis_btn.clicked.connect(self.define_agentes_responsaveis)
        responsaveis_layout.addWidget(QLabel("Definir Agentes Responsáveis"))
        responsaveis_layout.addWidget(responsaveis_btn)
        main_layout.addLayout(responsaveis_layout)

        # Configurar carregamento de tabela
        carregar_tabela_layout = QHBoxLayout()
        carregar_tabela_btn = QPushButton("Carregar Tabela")
        carregar_tabela_btn.clicked.connect(self.safe_load_table)
        carregar_tabela_layout.addWidget(QLabel("Carregar tabela excel ou libre"))
        carregar_tabela_layout.addWidget(carregar_tabela_btn)
        main_layout.addLayout(carregar_tabela_layout)

        # Configurar atualização de banco de dados
        carregar_database_layout = QHBoxLayout()
        carregar_database_btn = QPushButton("Atualizar Banco de Dados")
        carregar_database_btn.clicked.connect(self.safe_update_database)
        carregar_database_layout.addWidget(QLabel("Carregar dados de um arquivo .db"))
        carregar_database_layout.addWidget(carregar_database_btn)
        main_layout.addLayout(carregar_database_layout)

    def define_agentes_responsaveis(self):
        dialog = AgentesResponsaveisDialog(self)
        if dialog.exec():
            print("As alterações foram salvas com sucesso!")
        else:
            print("Edição cancelada.")

    def safe_load_table(self):
        try:
            self.parent_app.load_table()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar a tabela: {str(e)}")

    def safe_update_database(self):
        try:
            self.parent_app.update_database()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar o banco de dados: {str(e)}")

    def open_om_uasg(self):
        print("Abrir configuração de OM/UASG")

    def define_file_save_location(self):
        file_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        print(f"Local de salvamento definido: {file_path}")


class AgentesResponsaveisDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Agentes Responsáveis")
        self.setFixedSize(910, 800)  # Tamanho ajustado para melhor acomodar dois painéis
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)  # Layout vertical principal para organizar tudo verticalmente

        # Container horizontal para os grupos à esquerda e à direita
        groups_layout = QHBoxLayout()
        main_layout.addLayout(groups_layout)

        # Layout para a parte esquerda
        left_layout = QVBoxLayout()
        left_group = QGroupBox("Agentes - Esquerda")
        left_group.setLayout(left_layout)
        self.add_left_agents(left_layout)  # Adiciona agentes à esquerda

        # Layout para a parte direita
        right_layout = QVBoxLayout()
        right_group = QGroupBox("Agentes - Direita")
        right_group.setLayout(right_layout)
        self.add_right_agents(right_layout)  # Adiciona agentes à direita

        # Adiciona os grupos ao layout horizontal de grupos
        groups_layout.addWidget(left_group)
        groups_layout.addWidget(right_group)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)

        # Adiciona o layout de botões ao layout principal
        main_layout.addLayout(buttons_layout)

    def add_left_agents(self, layout):
        # Adiciona os agentes responsáveis à esquerda
        agents_left = [
            "Ordenador de Despesas", "Ordenador de Despesas Substituto",
            "Agente Financeiro", "Agente Financeiro Substituto",
            "Encarregado da Divisão de Obtenção", "Ajudante do Encarregado da Divisão de Obtenção"
        ]
        for agent in agents_left:
            layout.addWidget(self.posto_graduacao_layout(agent))

    def add_right_agents(self, layout):
        # Adiciona os agentes responsáveis à direita
        agents_right = [
            "Supervisor da Seção de Licitações", "Auxiliar da Seção de Licitações",
            "Auxiliar da Seção de Licitações", "Supervisor da Seção de Contratos",
            "Auxiliar da Seção de Contratos", "Auxiliar da Seção de Contratos"
        ]
        for agent in agents_right:
            layout.addWidget(self.posto_graduacao_layout(agent))

    def posto_graduacao_layout(self, label_text):
        group_box = QGroupBox(label_text) 
        layout = QVBoxLayout(group_box)  

        nome_layout = QHBoxLayout()
        nome_label = QLabel("Nome")
        nome_layout.addWidget(nome_label)
        nome = QLineEdit()
        nome_layout.addWidget(nome, 1)  
        layout.addLayout(nome_layout)

        posto_layout = QHBoxLayout()
        posto_label = QLabel("Posto Graduação")
        posto_layout.addWidget(posto_label)
        posto = self.create_editable_combobox()
        posto_layout.addWidget(posto, 1)
        layout.addLayout(posto_layout)

        return group_box  

    def create_editable_combobox(self):
        combobox = QComboBox()
        combobox.setEditable(True)
        combobox.addItems([
            "Capitão de Mar e Guerra (IM)",
            "Capitão de Fragata (IM)",
            "Capitão de Corveta (IM)"
        ])
        return combobox
    
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
            # "Portaria de Equipe de Planejamento",
            "Documento de Formalização de Demanda (DFD)",
            # "Declaração de Adequação Orçamentária",
	        "Capa do Edital",
            "Edital",
 	        "CP Encaminhamento AGU",
	        "CP Recomendações AGU",
            "Mensagem de Divulgação de IRP",
            "Mensagem de Publicação",
            "Mensagem de Homologação",
            "Nota Técnica",
            "Escalar Pregoeiro",
            "Gerar Relatório de Processo",
            "Check-list"  
        ]

        for actionText in actions:
            action = QAction(actionText, self)
            action.triggered.connect(partial(self.trigger_action, actionText))
            self.addAction(action)

    def trigger_action(self, actionText):
        if self.index.isValid():
            source_index = self.model.mapToSource(self.index)
            selected_row = source_index.row()
            df_registro_selecionado = carregar_dados_pregao(selected_row, str(self.main_app.database_path))
            
            if not df_registro_selecionado.empty:
                if actionText == "Editar Dados do Processo":
                    self.editar_dados(df_registro_selecionado)
                elif actionText == "Autorização para Abertura de Licitação":
                    self.openDialogAutorizacao(df_registro_selecionado)
                elif actionText == "Documento de Formalização de Demanda (DFD)":
                    self.openDialogDFD(df_registro_selecionado)
                elif actionText == "Edital":
                    self.openDialogEdital(df_registro_selecionado)
                elif actionText == "Escalar Pregoeiro":
                    self.openDialogEscalarPregoeiro(df_registro_selecionado)
                elif actionText == "CP Encaminhamento AGU":
                    self.openDialogEncaminhamentoAGU(df_registro_selecionado)
                elif actionText == "Capa do Edital":
                    self.openDialogCapaEdital(df_registro_selecionado)
                elif actionText == "Mensagem de Divulgação de IRP":
                    self.abrirDialogoIRP(df_registro_selecionado)
                elif actionText == "Mensagem de Publicação":
                    self.abrirDialogoPublicacao(df_registro_selecionado)
                elif actionText == "Mensagem de Homologação":
                    self.abrirDialogoHomologacao(df_registro_selecionado)
                elif actionText == "Check-list":
                    self.openChecklistDialog(df_registro_selecionado)
            else:
                QMessageBox.warning(self, "Atenção", "Nenhum registro selecionado ou dados não encontrados.")
        else:
            QMessageBox.warning(self, "Atenção", "Nenhuma linha selecionada.")

    # No final da classe TableMenu:
    def on_get_pregoeiro(self):
        id_processo = self.df_licitacao_completo['id_processo'].iloc[0]
        dialog = EscalarPregoeiroDialog(self.df_licitacao_completo, id_processo, self)
        dialog.exec()

    def abrirDialogoIRP(self, df_registro_selecionado):
        if not df_registro_selecionado.empty:
            dados = df_registro_selecionado.iloc[0].to_dict()
            dialogo = MSGIRP(dados=dados, icons_dir=str(ICONS_DIR), parent=self)
            dialogo.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum registro selecionado.")

    def abrirDialogoPublicacao(self, df_registro_selecionado):
        if not df_registro_selecionado.empty:
            dados = df_registro_selecionado.iloc[0].to_dict()
            dialogo = MSGPublicacao(dados=dados, icons_dir=str(ICONS_DIR), parent=self)
            dialogo.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum registro selecionado.")

    def abrirDialogoHomologacao(self, df_registro_selecionado):
        if not df_registro_selecionado.empty:
            dados = df_registro_selecionado.iloc[0].to_dict()
            dialogo = MSGHomolog(dados=dados, icons_dir=str(ICONS_DIR), parent=self)
            dialogo.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum registro selecionado.")

    def editar_dados(self, df_registro_selecionado):
        dialog = EditarDadosDialog(parent=self, dados=df_registro_selecionado.iloc[0].to_dict())
        dialog.dados_atualizados.connect(self.main_app.atualizar_tabela)
        dialog.exec()

    def openChecklistDialog(self, df_registro_selecionado):
        dialog = QDialog(self)
        dialog.setWindowTitle("Check-list")
        dialog.resize(950, 800)
        dialog.setStyleSheet("background-color: black; color: white;")
        
        # Instancia o ChecklistWidget e passa o DataFrame como argumento
        checklist_widget = ChecklistWidget(parent=dialog, icons_path=self.main_app.icons_dir, df_registro_selecionado=df_registro_selecionado)

        layout = QVBoxLayout(dialog)
        layout.addWidget(checklist_widget)
        dialog.exec()

    def openDialogDFD(self, df_registro_selecionado):
        dialog = GerarDFD(main_app=self.main_app, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogEncaminhamentoAGU(self, df_registro_selecionado):
        dialog = CPEncaminhamentoAGU(main_app=self.main_app, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogCapaEdital(self, df_registro_selecionado):
        dialog = CapaEdital(main_app=self.main_app, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogAutorizacao(self, df_registro_selecionado):
        dialog = AutorizacaoAberturaLicitacaoDialog(main_app=self.main_app, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogEdital(self, df_registro_selecionado):
        dialog = EditalDialog(main_app=self.main_app, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogEscalarPregoeiro(self, df_registro_selecionado):
        dialog = EscalarPregoeiroDialog(main_app=self.main_app, df_registro=df_registro_selecionado)
        dialog.exec()

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        source_index = index.model().mapToSource(index)
        source_model = index.model().sourceModel()

        # print(f"Pintando proxy index: {index.row()}, {index.column()} -> source index: {source_index.row()}, {source_index.column()}")

        if source_index.column() == source_model.fieldIndex("id_processo") or source_index.column() == source_model.fieldIndex("objeto"):
            painter.save()
            painter.setPen(QColor("#fcc200"))
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, str(source_model.data(source_index, Qt.ItemDataRole.DisplayRole)))
            painter.restore()
        else:
            super().paint(painter, option, index)

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Garante que o alinhamento centralizado seja aplicado
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

class CustomSqlTableModel(QSqlTableModel):
    def __init__(self, parent=None, db=None):
        super().__init__(parent, db)
        self.etapa_order = {
            'Concluído': 0, 'Assinatura Contrato': 1, 'Homologado': 2, 'Em recurso': 3,
            'Sessão Pública': 4, 'Impugnado': 5, 'Pré-Publicação': 6, 'Recomendações AGU': 7,
            'AGU': 8, 'Nota Técnica': 9, 'Montagem do Processo': 10, 'IRP': 11, 
            'Setor Responsável': 12, 'Planejamento': 13
        }

    def sort(self, column, order):
        if self.headerData(column, Qt.Orientation.Horizontal) == 'Etapa':
            self.setSortRole(Qt.ItemDataRole.UserRole)
        else:
            self.setSortRole(Qt.ItemDataRole.DisplayRole)
        super().sort(column, order)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.UserRole and self.headerData(index.column(), Qt.Orientation.Horizontal) == 'Etapa':
            etapa = super().data(index, Qt.ItemDataRole.DisplayRole)
            return self.etapa_order.get(etapa, 999)  # Default for undefined stages
        return super().data(index, role)
        
class ApplicationUI(QMainWindow):
    def __init__(self, app, icons_dir):
        super().__init__()
        self.app = app
        self.icons_dir = Path(icons_dir)
        
        # Carregar configuração inicial do diretório do banco de dados
        self.database_path = Path(load_config("database_path", str(CONTROLE_DADOS)))
        
        self.event_manager = EventManager()
        self.event_manager.controle_dir_updated.connect(self.handle_database_dir_update)
        
        self.selectedIndex = None
        self.image_cache = load_images(self.icons_dir, [
            "plus.png", "save_to_drive.png", "loading.png", "delete.png", "excel.png", "calendar.png", "report.png", "management.png"
        ])
        
        self.database_manager = DatabaseManager(self.database_path)
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
            # Verifica se todas as colunas necessárias estão presentes

            required_columns = {
                "id": "INTEGER PRIMARY KEY", "tipo": "TEXT", "numero": "TEXT", "ano": "TEXT", "id_processo": "TEXT", "nup": "TEXT",
                "objeto": "TEXT", "objeto_completo": "TEXT", "valor_total": "TEXT", "uasg": "TEXT", "orgao_responsavel": "TEXT",
                "sigla_om": "TEXT", "setor_responsavel": "TEXT", "coordenador_planejamento": "TEXT", "etapa": "TEXT",
                "pregoeiro": "TEXT", "item_pca": "TEXT", "portaria_PCA": "TEXT", "data_sessao": "TEXT", "data_limite_entrega_tr": "TEXT",
                "nup_portaria_planejamento": "TEXT", "srp": "TEXT", "material_servico": "TEXT", "parecer_agu": "TEXT", "msg_irp": "TEXT",
                "data_limite_manifestacao_irp": "TEXT", "data_limite_confirmacao_irp": "TEXT", "num_irp": "TEXT", "om_participantes": "TEXT",
                "link_pncp": "TEXT", "link_portal_marinha": "TEXT"
            }
            DatabaseManager.verify_and_create_columns(conn, 'controle_processos', required_columns)
            DatabaseManager.check_and_fix_id_sequence(conn)
                
    def init_ui(self):
        self.main_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.main_widget)

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Digite para buscar...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                font-size: 12pt;
                color: #fcc200;
                background-color: black;
                border: 2px solid #333;
                padding: 1px;
            }
            QLineEdit:focus {
                border-color: #fcc200;
            }
        """)
        self.main_layout.addWidget(self.search_bar)
        self._setup_buttons_layout()
        self.table_view = CustomTableView(self)
        self.init_sql_model()

        # Configurando o QSortFilterProxyModel
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)  # Considera todas as colunas para a busca

        def handle_text_change(text):
            regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.proxy_model.setFilterRegularExpression(regex)

        self.search_bar.textChanged.connect(handle_text_change)

        self.table_view.setModel(self.proxy_model)
        self.table_view.verticalHeader().setVisible(False)
        self.main_layout.addWidget(self.table_view)

        # Cria e aplica o CustomItemDelegate para todas as colunas da QTableView
        custom_item_delegate = CustomItemDelegate(self.table_view)
        for column in range(self.model.columnCount()):
            self.table_view.setItemDelegateForColumn(column, custom_item_delegate)

        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

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
        """)

        self.setCentralWidget(self.main_widget)
        self.table_view.selectionModel().selectionChanged.connect(self.linhaSelecionada)

        QTimer.singleShot(1, self.adjustColumnWidth) 

        # Conectar a reordenação ao proxy model
        header = self.table_view.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(self.on_header_clicked)

    def adjustColumnWidth(self):
        header = self.table_view.horizontalHeader()
        # Configurar outras colunas para ter tamanhos fixos
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(13, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(14, QHeaderView.ResizeMode.Stretch)  # Continua expansível
        
        # Ajusta o tamanho de colunas fixas
        header.resizeSection(4, 110)
        header.resizeSection(5, 220)
        header.resizeSection(8, 110)
        header.resizeSection(10, 110)
        header.resizeSection(13, 170)
        header.resizeSection(14, 110)

        # Configura a coluna 6 para ser expansível e define o tamanho mínimo
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(6, 220)  # Define o tamanho inicial
        header.setMinimumSectionSize(110)  # Define o tamanho mínimo


    def on_header_clicked(self, logicalIndex):
        # Alternar entre ordenação ascendente e descendente
        ascending = self.table_view.horizontalHeader().sortIndicatorOrder() == Qt.SortOrder.AscendingOrder
        self.proxy_model.sort(logicalIndex, Qt.SortOrder.AscendingOrder if not ascending else Qt.SortOrder.DescendingOrder)

    def linhaSelecionada(self, selected, deselected):
        if selected.indexes():
            proxy_index = selected.indexes()[0]
            source_index = self.proxy_model.mapToSource(proxy_index)
            print(f"Selecionado no proxy: row {proxy_index.row()}, column {proxy_index.column()}")
            print(f"Correspondente no modelo fonte: row {source_index.row()}, column {source_index.column()}")

            df_registro_selecionado = carregar_dados_pregao(source_index.row(), self.database_path)
            print(f"Registro selecionado: {df_registro_selecionado.iloc[0].to_dict()}")

    def _setup_buttons_layout(self):
        self.buttons_layout = QHBoxLayout()
        self._create_buttons()
        self.main_layout.addLayout(self.buttons_layout)
            
    def _create_buttons(self):
        self.buttons_layout = QHBoxLayout()
        icon_size = QSize(40, 40)  # Tamanho do ícone para todos os botões
        self.button_specs = [
            ("  Adicionar Item", self.image_cache['plus'], self.on_add_item, "Adiciona um novo item ao banco de dados", icon_size),
            ("  Salvar", self.image_cache['excel'], self.salvar_tabela, "Salva o dataframe em um arquivo excel('.xlsx')", icon_size),
            # ("  Carregar", self.image_cache['loading'], self.carregar_tabela, "Carrega o dataframe de um arquivo existente('.db', '.xlsx' ou '.odf')", icon_size),
            ("  Excluir", self.image_cache['delete'], self.on_delete_item, "Exclui um item selecionado", icon_size),
            ("  Controle de Datas", self.image_cache['calendar'], self.on_control_process, "Abre o painel de controle do processo", icon_size),            
            ("    Relatório", self.image_cache['report'], self.on_report, "Gera um relatório dos dados", icon_size),
            ("Configurações", self.image_cache['management'], self.open_settings_dialog, "Abre as configurações da aplicação", icon_size),            
        ]

        for text, icon, callback, tooltip, icon_size in self.button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self, icon_size=icon_size)
            self.buttons_layout.addWidget(btn)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.exec()
        
    def on_delete_item(self):
        selected_index = self.table_view.currentIndex()
        if not selected_index.isValid():
            QMessageBox.warning(self, "Seleção", "Nenhum item selecionado.")
            return

        # Obtém o ID do processo da linha selecionada
        id_processo = selected_index.sibling(selected_index.row(), 4).data()  # Assumindo que a coluna 4 é 'ID Processo'

        if id_processo is None:
            QMessageBox.warning(self, "Erro", "Não foi possível obter o ID do processo.")
            return

        reply = QMessageBox.question(self, "Confirmar exclusão", 
                                    "Você tem certeza que deseja excluir o item selecionado e todas as entradas correspondentes?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                    QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Exclui do controle_processos
            with self.database_manager as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM controle_processos WHERE id_processo = ?", (id_processo,))
                conn.commit()

            # Exclui do controle_prazos onde chave_processo é igual a id_processo
            with self.database_manager as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM controle_prazos WHERE chave_processo = ?", (id_processo,))
                conn.commit()

            self.init_sql_model()  # Atualiza o modelo para refletir as mudanças
            QMessageBox.information(self, "Exclusão", "Os registros foram excluídos com sucesso.")


    def on_report(self):
        with self.database_manager as conn:
            # Atualiza etapas baseadas no último sequencial de controle_prazos
            self.database_manager.verificar_e_atualizar_etapas(conn)
            # Atualiza a contagem dos dias na última etapa
            self.database_manager.atualizar_dias_na_etapa(conn)
            # Atualiza a data final para a última etapa de cada chave_processo para hoje
            self.database_manager.atualizar_ultima_etapa_data_final(conn)
            # Verifica e popula controle_prazos se necessário
            self.database_manager.popular_controle_prazos_se_necessario()
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
        # Define as colunas desejadas
        colunas_desejadas = [
            "ID Processo", "NUP", "Objeto", "UASG", "OM", "setor_responsavel", 
            "coordenador_planejamento", "Etapa", "Pregoeiro", "Item PCA"
        ]
        
        # Cria um DataFrame vazio
        column_count = self.model.columnCount()
        headers = [self.model.headerData(i, Qt.Orientation.Horizontal) for i in range(column_count)]
        filtered_headers = [header for header in headers if header in colunas_desejadas]
        data = []

        # Preenche o DataFrame com os dados do modelo filtrando as colunas
        for row in range(self.model.rowCount()):
            row_data = []
            for column in range(column_count):
                if headers[column] in colunas_desejadas:
                    index = self.model.index(row, column)
                    row_data.append(self.model.data(index))
            data.append(row_data)

        df = pd.DataFrame(data, columns=filtered_headers)

        # Define o caminho inicial com o nome do arquivo pré-definido
        initial_path = os.path.join(os.path.expanduser("~"), "controle_processos.xlsx")
        
        # Abre um diálogo para que o usuário escolha o diretório e nome do arquivo
        excel_path, _ = QFileDialog.getSaveFileName(None, 'Salvar Tabela', initial_path, 'Excel Files (*.xlsx)')
        if not excel_path:
            return  # Usuário cancelou o diálogo de salvar

        # Salva o DataFrame como Excel usando openpyxl para ajustar as colunas
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
            
            # Ajusta as colunas ao conteúdo
            for column_cells in writer.sheets['Sheet1'].columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                writer.sheets['Sheet1'].column_dimensions[column_cells[0].column_letter].width = length

        # Abre o arquivo Excel
        os.startfile(excel_path)

    def carregar_tabela(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Opções de Carregamento")
        layout = QVBoxLayout()

        btn_carregar_arquivo = QPushButton("Carregar Tabela de Arquivo")
        btn_carregar_arquivo.clicked.connect(self.carregar_tabela_de_arquivo)
        layout.addWidget(btn_carregar_arquivo)

        btn_atualizar_diretorio = QPushButton("Atualizar Diretório do Banco de Dados")
        btn_atualizar_diretorio.clicked.connect(self.update_database_file)
        layout.addWidget(btn_atualizar_diretorio)

        dialog.setLayout(layout)
        dialog.exec()

    def carregar_tabela_de_arquivo(self):
        self.database_manager.carregar_tabela(self)
        self.sender().parent().close()  # Fecha o QDialog após a operação

    def update_database_file(self):
        # Abrir o diálogo para seleção do arquivo do banco de dados
        fileName, _ = QFileDialog.getOpenFileName(self, 
                                                "Selecione o arquivo do banco de dados", 
                                                str(CONTROLE_DADOS),  # Diretório inicial
                                                "Database Files (*.db)")
        print(f"Debug: Seleção de arquivo iniciada. Arquivo escolhido: {fileName}")
        
        if fileName:
            newPath = Path(fileName)
            print(f"Debug: Novo caminho escolhido: {newPath}")

            if newPath != CONTROLE_DADOS:
                print(f"Debug: Atualizando o caminho do banco de dados. Antigo: {CONTROLE_DADOS}, Novo: {newPath}")
                self.event_manager.update_database_dir(newPath)
                print("Debug: O caminho do banco de dados foi atualizado com sucesso.")
                QMessageBox.information(self, "Atualização bem-sucedida", "O arquivo do banco de dados foi atualizado com sucesso.")
            else:
                print("Debug: O arquivo escolhido é o mesmo que o atualmente configurado.")
                QMessageBox.information(self, "Nenhuma mudança detectada", "O arquivo escolhido é o mesmo que o atualmente configurado. Nenhuma mudança foi realizada.")
        else:
            print("Debug: Nenhum arquivo foi escolhido.")
            QMessageBox.warning(self, "Carregamento Cancelado", "Nenhum arquivo de banco de dados foi selecionado.")

    def handle_database_dir_update(self, new_dir):
        global CONTROLE_DADOS
        CONTROLE_DADOS = new_dir
        save_config("database_path", str(new_dir))
        self.database_path = new_dir
        self.database_manager = DatabaseManager(new_dir)
        QMessageBox.information(self, "Atualização de Diretório", "Diretório do banco de dados atualizado para: " + str(new_dir))

    def on_control_process(self):
        print("Iniciando on_control_process...")
        with self.database_manager as conn:
            # Atualiza etapas baseadas no último sequencial de controle_prazos
            self.database_manager.verificar_e_atualizar_etapas(conn)
            # Atualiza a contagem dos dias na última etapa
            self.database_manager.atualizar_dias_na_etapa(conn)
            # Atualiza a data final para a última etapa de cada chave_processo para hoje
            self.database_manager.atualizar_ultima_etapa_data_final(conn)
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
            # Atualiza a data final para a última etapa de cada chave_processo para hoje
            self.database_manager.atualizar_ultima_etapa_data_final(conn)

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

    def load_table(self):
        # Isso agora é um método público que pode ser chamado de SettingsDialog
        self.carregar_tabela()

    def update_database(self):
        # Isso agora é um método público que pode ser chamado de SettingsDialog
        self.update_database_file()
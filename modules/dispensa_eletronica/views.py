from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.utils.search_bar import setup_search_bar, MultiColumnFilterProxyModel
from modules.utils.add_button import add_button
from config.styles.styless import apply_table_custom_style
from modules.dispensa_eletronica.dialogs.editar_dados import EditDataDialog
from pathlib import Path
import pandas as pd

class EditarDadosWindow(QMainWindow):
    """Classe para a janela de edição de dados."""
    def __init__(self, dados, icons, parent=None):
        super().__init__(parent)
        self.dados = dados
        self.icons = icons

        # Configurações da janela
        self.setWindowTitle("Editar Dados")
        self.setWindowIcon(self.icons.get("edit", None))
        self.setFixedSize(1250, 720)
        
        # Configuração da interface
        self.setup_ui()

    def setup_ui(self):
        # Widget principal e layout principal
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        layout_principal = QVBoxLayout(main_widget)
        
        # Configura layout título e adiciona ao layout principal
        layout_titulo = self.setup_layout_titulo()
        layout_principal.addLayout(layout_titulo)
        
        # Configura layout conteúdo e adiciona ao layout principal
        layout_conteudo = self.setup_layout_conteudo()
        layout_principal.addLayout(layout_conteudo)

    def setup_layout_titulo(self):
        """Configura o layout do título com o ID do processo e a seção de consulta API."""
        layout_titulo = QHBoxLayout()
        
        # Label de título com o id_processo
        id_processo = self.dados.get("id_processo", "N/A")
        title_label = QLabel(f"Detalhes do Processo: {id_processo}", self)
        layout_titulo.addWidget(title_label)
        
        # Layout consulta API em V dentro do título
        consulta_api_layout = QVBoxLayout()
        layout_titulo.addLayout(consulta_api_layout)
        
        return layout_titulo

    def setup_layout_conteudo(self):
        """Configura o layout de conteúdo com StackedWidget e agentes responsáveis."""
        layout_conteudo = QHBoxLayout()
        
        # Layout StackedWidget e ao lado layout agentes responsáveis
        stacked_widget = QStackedWidget(self)
        layout_conteudo.addWidget(stacked_widget)

        # Layout para agentes responsáveis ao lado do StackedWidget
        agentes_responsaveis_layout = QVBoxLayout()
        layout_conteudo.addLayout(agentes_responsaveis_layout)
        
        return layout_conteudo
    
class DispensaEletronicaWidget(QMainWindow):
    # Sinais para comunicação com o controlador
    addItem = pyqtSignal()
    deleteItem = pyqtSignal()
    salvar_tabela = pyqtSignal()
    salvar_graficos = pyqtSignal()
    salvar_print = pyqtSignal()
    loadData = pyqtSignal(str)
    # doubleClickRow = pyqtSignal(int)

    def __init__(self, icons, model, database_path, parent=None):
        super().__init__(parent)
        self.icons = icons
        self.model = model
        self.database_path = database_path
        self.selected_row_data = None
        
        # Inicializa o proxy_model e configura o filtro
        self.proxy_model = MultiColumnFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # Configura a interface de usuário
        self.setup_ui()

    def setup_ui(self):
        # Cria o widget principal e layout principal
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        
        # Layout para a barra de ferramentas
        top_layout = QHBoxLayout()
        self.setup_buttons(top_layout)
        self.main_layout.addLayout(top_layout)
        
        # Configuração da tabela
        self.setup_table_view()

    def on_table_double_click(self, index):
        row = self.proxy_model.mapToSource(index).row()
        id_processo = self.model.index(row, self.model.fieldIndex("id_processo")).data()
        
        dados = self.carregar_dados_por_id(id_processo)
        if dados:
            nova_janela = EditarDadosWindow(dados, self.icons, self)
            nova_janela.show()
        else:
            QMessageBox.warning(self, "Erro", "Falha ao carregar dados para o ID do processo selecionado.")
    
    def carregar_dados_por_id(self, id_processo):
        """Carrega os dados da linha selecionada a partir do banco de dados usando `id_processo`."""
        query = f"SELECT * FROM controle_dispensas WHERE id_processo = '{id_processo}'"
        try:
            # Obtenha os dados do banco de dados
            dados = self.model.database_manager.fetch_all(query)
            
            # Converte para DataFrame caso dados seja uma lista
            if isinstance(dados, list):
                dados = pd.DataFrame(dados, columns=self.model.column_names)  # Substitua `self.model.column_names` pela lista de nomes de colunas correta
            
            # Verifica se o DataFrame não está vazio
            return dados.iloc[0].to_dict() if not dados.empty else None
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return None
        
    def editar_dados(self, registro_selecionado):        
        window = EditDataDialog(self.icons, parent=self, dados=registro_selecionado.iloc[0].to_dict())
        window.dados_atualizados.connect(self.refresh_model)  
        window.show() 

    def setup_buttons(self, layout):
        add_button("Adicionar", "plus", self.addItem, layout, self.icons, tooltip="Adicionar um novo item")  # Alteração aqui
        add_button("Excluir", "delete", self.deleteItem, layout, self.icons, tooltip="Excluir o item selecionado")
        add_button("Tabelas", "excel", self.salvar_tabela, layout, self.icons, tooltip="Salva o dataframe em um arquivo Excel")
        add_button("Gráficos", "performance", self.salvar_graficos, layout, self.icons, tooltip="Carrega dados de uma tabela")
        add_button("ConGes", "image-processing", self.salvar_print, layout, self.icons, tooltip="Abre o painel de controle do processo")

    def refresh_model(self):
        """Atualiza a tabela com os dados mais recentes do banco de dados."""
        self.model.select()

    def setup_buttons(self, layout):
        # Adiciona botões para funcionalidades específicas (exemplo)
        add_button = QPushButton("Adicionar")
        add_button.clicked.connect(self.addItem.emit)
        layout.addWidget(add_button)
        
        delete_button = QPushButton("Excluir")
        delete_button.clicked.connect(self.deleteItem.emit)
        layout.addWidget(delete_button)

    def setup_table_view(self):
        self.table_view = QTableView(self)
        self.table_view.setModel(self.proxy_model)  # Usa o proxy_model corretamente
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.doubleClicked.connect(self.on_table_double_click)
        
        # Configurações adicionais de estilo e comportamento
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        # Define CenterAlignDelegate para centralizar o conteúdo em todas as colunas
        center_delegate = CenterAlignDelegate(self.table_view)
        for column in range(self.model.columnCount()):
            self.table_view.setItemDelegateForColumn(column, center_delegate)

        # Aplica CustomItemDelegate à coluna "situação" para exibir ícones
        situacao_index = self.model.fieldIndex('situacao')
        self.table_view.setItemDelegateForColumn(situacao_index, CustomItemDelegate(self.icons, self.table_view, self.model))

        self.main_layout.addWidget(self.table_view)

    def configure_table_model(self):
        self.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)
        self.update_column_headers()
        self.hide_unwanted_columns()

    def update_column_headers(self):
        titles = {0: "Status", 1: "ID Processo", 5: "NUP", 7: "Objeto", 17: "OM"}
        for column, title in titles.items():
            self.model.setHeaderData(column, Qt.Orientation.Horizontal, title)

    def hide_unwanted_columns(self):
        visible_columns = {0, 1, 5, 7, 17}
        for column in range(self.model.columnCount()):
            if column not in visible_columns:
                self.table_view.hideColumn(column)

    def adjust_columns(self):
        # Ajustar automaticamente as larguras das colunas ao conteúdo
        self.table_view.resizeColumnsToContents()
        QTimer.singleShot(1, self.apply_custom_column_sizes) 

    def apply_custom_column_sizes(self):
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(17, QHeaderView.ResizeMode.Fixed)

        header.resizeSection(0, 150)        
        header.resizeSection(1, 130)
        header.resizeSection(5, 170)
        header.resizeSection(17, 100)

class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, icons, parent=None, model=None):
        super().__init__(parent)
        self.icons = icons
        self.model = model

    def paint(self, painter, option, index):
        # Verifica se estamos na coluna de situação
        if index.column() == self.model.fieldIndex('situacao'):
            situacao = index.data(Qt.ItemDataRole.DisplayRole)
            # Define o mapeamento de ícones
            icon_key = {
                'Planejamento': 'business',
                'Aprovado': 'verify_menu',
                'Sessão Pública': 'session',
                'Homologado': 'deal',
                'Empenhado': 'emenda_parlamentar',
                'Concluído': 'aproved',
                'Arquivado': 'archive'
            }.get(situacao)

            # Desenha o ícone se encontrado no mapeamento
            if icon_key and icon_key in self.icons:
                icon = self.icons[icon_key]
                icon_size = 24
                icon_rect = QRect(option.rect.left() + 5,
                                  option.rect.top() + (option.rect.height() - icon_size) // 2,
                                  icon_size, icon_size)
                painter.drawPixmap(icon_rect, icon.pixmap(icon_size, icon_size))

                # Desenha o texto ao lado do ícone
                text_rect = QRect(icon_rect.right() + 5, option.rect.top(),
                                  option.rect.width() - icon_size - 10, option.rect.height())
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, situacao)
        else:
            # Desenha normalmente nas outras colunas
            super().paint(painter, option, index)
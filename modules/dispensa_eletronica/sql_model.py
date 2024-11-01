from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from modules.planejamento.utilidades_planejamento import carregar_dados_dispensa
from modules.dispensa_eletronica.edit_dialog import EditDataDialog
from functools import partial

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
        self.model = model
        self.config_manager = config_manager
        self.setup_menu_style()
        self.add_menu_actions()

    def setup_menu_style(self):
        self.setStyleSheet("""
            QMenu {
                font-size: 16px;
                font-weight: bold;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px;
            }
            QMenu::separator {
                height: 2px;
                margin: 5px 0;
            }
        """)

    def add_menu_actions(self):
        actions = [
            "Editar Dados do Processo"
        ]
        for actionText in actions:
            action = QAction(actionText, self)
            action.triggered.connect(partial(self.trigger_action, actionText))
            self.addAction(action)

    def trigger_action(self, actionText):
        if self.index.isValid():
            source_index = self.model.mapToSource(self.index)
            # Assumindo que a chave primária é a primeira coluna do modelo
            id_processo = self.model.data(self.model.index(source_index.row(), 0))  
            df_registro_selecionado = carregar_dados_dispensa(id_processo, str(self.main_app.database_path))
            if not df_registro_selecionado.empty:
                self.perform_action(actionText, df_registro_selecionado)
            else:
                QMessageBox.warning(self, "Atenção", "Nenhum registro selecionado ou dados não encontrados.")


    def perform_action(self, actionText, df_registro_selecionado):
        actions = {
            "Editar Dados do Processo": self.editar_dados
        }
        action = actions.get(actionText)
        if action:
            action(df_registro_selecionado)

    def atualizar_interface(self):
        print("Interface atualizada com os novos dados.")
        self.main_app.refresh_model() 

    def editar_dados(self, df_registro_selecionado):
        dialog = EditDataDialog(df_registro_selecionado, self.main_app.icons_dir)
        dialog.dados_atualizados.connect(self.atualizar_interface)  # Conectar o sinal ao método de atualização
        dialog.exec()

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

    def create_table_if_not_exists(self):
        query = QSqlQuery(self.db)
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS controle_dispensas (
                id_processo VARCHAR(100) PRIMARY KEY,
                tipo VARCHAR(100),
                numero VARCHAR(100),
                ano VARCHAR(100),
                situacao TEXT,
                nup VARCHAR(100),
                material_servico VARCHAR(30),
                objeto VARCHAR(100),
                vigencia TEXT,
                data_sessao DATE,
                operador VARCHAR(100),
                criterio_julgamento TEXT,
                com_disputa TEXT,
                pesquisa_preco TEXT,
                previsao_contratacao TEXT,          
                uasg VARCHAR(10),
                orgao_responsavel VARCHAR(250),
                sigla_om VARCHAR(100),
                setor_responsavel TEXT,
                responsavel_pela_demanda TEXT,
                ordenador_despesas TEXT,
                agente_fiscal TEXT,
                gerente_de_credito TEXT,
                cod_par TEXT,
                prioridade_par TEXT,
                cep TEXT,
                endereco TEXT,          
                email TEXT,
                telefone TEXT,
                dias_para_recebimento TEXT,
                horario_para_recebimento TEXT,
                valor_total REAL,
                acao_interna TEXT,
                fonte_recursos TEXT,
                natureza_despesa TEXT,
                unidade_orcamentaria TEXT,
                ptres TEXT,
                atividade_custeio TEXT,                          
                comentarios TEXT,                          
                justificativa TEXT,
                link_pncp TEXT,
                comunicacao_padronizada TEXT,
                do_responsavel TEXT,
                ao_responsavel TEXT,
                uf TEXT,
                codigoMunicipioIbge TEXT                   
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

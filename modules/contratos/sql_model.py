from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from modules.contratos.edit_dialog import EditDataDialog
from functools import partial
import sqlite3
import pandas as pd

def carregar_dados_contratos(index, caminho_banco_dados):
    """
    Carrega os dados de pregão do banco de dados SQLite especificado pelo caminho_banco_dados.

    Parâmetros:
    - index: O índice da linha selecionada na QTableView.
    - caminho_banco_dados: O caminho para o arquivo do banco de dados SQLite.
    
    Retorna:
    - Um DataFrame do Pandas contendo os dados do registro selecionado.
    """
    try:
        connection = sqlite3.connect(caminho_banco_dados)
        query = f"SELECT * FROM controle_processos WHERE id={index + 1}"
        df_registro_selecionado = pd.read_sql_query(query, connection)
        connection.close()
        return df_registro_selecionado
    except Exception as e:
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
    
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
            df_registro_selecionado = carregar_dados_contratos(id_processo, str(self.main_app.database_path))
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
            self.ensure_id_processo_primary_key()

    def ensure_id_processo_primary_key(self):
        query = QSqlQuery(self.db)
        query.exec("PRAGMA table_info(controle_dispensas)")
        id_processo_is_primary = False
        while query.next():
            if query.value(1) == 'id_processo' and query.value(5) == 1:
                id_processo_is_primary = True
                # print("Coluna 'id_processo' já é PRIMARY KEY.")
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
                programa_trabalho_resuminho TEXT,
                atividade_custeio TEXT,                          
                comentarios TEXT,                          
                justificativa TEXT,
                link_pncp TEXT,
                comunicacao_padronizada TEXT,
                do_responsavel TEXT,
                ao_responsavel TEXT
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

from modules.dispensa_eletronica.utils.db_manager import DatabaseManager
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from modules.planejamento.utilidades_planejamento import carregar_dados_dispensa
from modules.dispensa_eletronica.edit_dialog import EditDataDialog
from functools import partial

class DispensaEletronicaModel(QObject):
    def __init__(self, database_path, parent=None):
        super().__init__(parent)
        self.database_manager = DatabaseManager(database_path)
        self.db = None  # Adiciona um atributo para o banco de dados
        self.model = None  # Atributo para o modelo SQL
        self.init_database()  # Inicializa a conexão e a estrutura do banco de dados

    def init_database(self):
        """Inicializa a conexão com o banco de dados e ajusta a estrutura da tabela."""
        if QSqlDatabase.contains("my_conn"):
            QSqlDatabase.removeDatabase("my_conn")
        self.db = QSqlDatabase.addDatabase('QSQLITE', "my_conn")
        self.db.setDatabaseName(str(self.database_manager.db_path))
        
        if not self.db.open():
            print("Não foi possível abrir a conexão com o banco de dados.")
        else:
            print("Conexão com o banco de dados aberta com sucesso.")
            self.adjust_table_structure()  # Ajusta a estrutura da tabela, se necessário

    def adjust_table_structure(self):
        """Verifica e cria a tabela 'controle_dispensas' se não existir."""
        query = QSqlQuery(self.db)
        if not query.exec("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_dispensas'"):
            print("Erro ao verificar existência da tabela:", query.lastError().text())
        if not query.next():
            print("Tabela 'controle_dispensas' não existe. Criando tabela...")
            self.create_table_if_not_exists()
        else:
            print("Tabela 'controle_dispensas' existe. Verificando estrutura da coluna...")

    def create_table_if_not_exists(self):
        """Cria a tabela 'controle_dispensas' com a estrutura definida, caso ainda não exista."""
        query = QSqlQuery(self.db)
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS controle_dispensas (
                situacao TEXT,                         
                id_processo VARCHAR(100) PRIMARY KEY,
                tipo VARCHAR(100),
                numero VARCHAR(100),
                ano VARCHAR(100),
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
                comunicacao_padronizada TEXT             
            )
        """):
            print("Falha ao criar a tabela 'controle_dispensas':", query.lastError().text())
        else:
            print("Tabela 'controle_dispensas' criada com sucesso.")

    def setup_model(self, table_name, editable=False):
        """Configura o modelo SQL para a tabela especificada."""
        # Passa o database_manager para o modelo personalizado
        self.model = CustomSqlTableModel(parent=self, db=self.db, database_manager=self.database_manager, non_editable_columns=[4, 8, 10, 13])
        self.model.setTable(table_name)
        
        if editable:
            self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        
        self.model.select()
        return self.model

    def get_data(self, table_name):
        """Retorna todos os dados da tabela especificada."""
        return self.database_manager.fetch_all(f"SELECT * FROM {table_name}")
    
    def insert_or_update_data(self, data):
        """Insere ou atualiza dados na tabela 'controle_dispensas'."""
        upsert_sql = '''
        INSERT INTO controle_dispensas (
            situacao, id_processo, tipo, numero, ano, nup, material_servico, 
            objeto, uasg, sigla_om, setor_responsavel, 
            orgao_responsavel, data_sessao, operador, 
            criterio_julgamento, com_disputa, pesquisa_preco, previsao_contratacao, 
            responsavel_pela_demanda, ordenador_despesas, agente_fiscal, gerente_de_credito,
            cod_par, prioridade_par, cep, endereco, email, telefone, dias_para_recebimento,
            horario_para_recebimento, valor_total, acao_interna, fonte_recursos, natureza_despesa,
            unidade_orcamentaria, ptres
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id_processo) DO UPDATE SET
            nup=excluded.nup,
            objeto=excluded.objeto,
            uasg=excluded.uasg,
            tipo=excluded.tipo,
            numero=excluded.numero,
            ano=excluded.ano,
            sigla_om=excluded.sigla_om,
            setor_responsavel=excluded.setor_responsavel,
            material_servico=excluded.material_servico,
            orgao_responsavel=excluded.orgao_responsavel,
            situacao=excluded.situacao,
            data_sessao=excluded.data_sessao,
            operador=excluded.operador,
            criterio_julgamento=excluded.criterio_julgamento,
            com_disputa=excluded.com_disputa,
            pesquisa_preco=excluded.pesquisa_preco,
            previsao_contratacao=excluded.previsao_contratacao,
            responsavel_pela_demanda=excluded.responsavel_pela_demanda, 
            ordenador_despesas=excluded.ordenador_despesas, 
            agente_fiscal=excluded.agente_fiscal, 
            gerente_de_credito=excluded.gerente_de_credito,
            cod_par=excluded.cod_par, 
            prioridade_par=excluded.prioridade_par, 
            cep=excluded.cep, 
            endereco=excluded.endereco, 
            email=excluded.email, 
            telefone=excluded.telefone, 
            dias_para_recebimento=excluded.dias_para_recebimento,
            horario_para_recebimento=excluded.horario_para_recebimento, 
            valor_total=excluded.valor_total, 
            acao_interna=excluded.acao_interna, 
            fonte_recursos=excluded.fonte_recursos, 
            natureza_despesa=excluded.natureza_despesa,
            unidade_orcamentaria=excluded.unidade_orcamentaria,
            ptres=excluded.ptres
        '''

        # Verifica se 'situacao' está dentro dos valores válidos
        valid_situations = ["Planejamento", "Aprovado", "Sessão Pública", "Homologado", "Empenhado", "Concluído", "Arquivado"]
        data['situacao'] = data['situacao'] if data['situacao'] in valid_situations else 'Planejamento'

        # Executa a inserção ou atualização
        with self.database_manager as conn:
            cursor = conn.cursor()
            cursor.execute(upsert_sql, (
                data.get('id_processo'), data.get('nup'), data.get('objeto'), data.get('uasg'),
                data.get('tipo'), data.get('numero'), data.get('ano'),
                data.get('sigla_om'), data.get('setor_responsavel', ''), 
                data.get('material_servico'), data.get('orgao_responsavel'), data.get('situacao'),
                data.get('data_sessao', None), data.get('operador', ''),
                data.get('criterio_julgamento', ''), data.get('com_disputa', 0),
                data.get('pesquisa_preco', 0), data.get('previsao_contratacao', None), 
                data.get('responsavel_pela_demanda', None), data.get('ordenador_despesas', None), 
                data.get('agente_fiscal', None), data.get('gerente_de_credito', None), 
                data.get('cod_par', None), data.get('prioridade_par', None), 
                data.get('cep', None), data.get('endereco', None), 
                data.get('email', None), data.get('telefone', None), 
                data.get('dias_para_recebimento', None), data.get('horario_para_recebimento', None),
                data.get('valor_total', None), data.get('acao_interna', None), 
                data.get('fonte_recursos', None), data.get('natureza_despesa', None),  
                data.get('unidade_orcamentaria', None), data.get('ptres', None),
            ))
            conn.commit()

    def delete_data(self, id_processo):
        """Exclui um registro da tabela 'controle_dispensas' pelo id_processo."""
        with self.database_manager as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM controle_dispensas WHERE id_processo = ?", (id_processo,))
        conn.commit()

class CustomSqlTableModel(QSqlTableModel):
    def __init__(self, parent=None, db=None, database_manager=None, non_editable_columns=None):
        super().__init__(parent, db)
        self.database_manager = database_manager
        self.non_editable_columns = non_editable_columns if non_editable_columns is not None else []
        
        # Define os nomes das colunas
        self.column_names = [
            "situacao", "id_processo", "tipo", "numero", "ano", "nup", "material_servico", 
            "objeto", "vigencia", "data_sessao", "operador", "criterio_julgamento", 
            "com_disputa", "pesquisa_preco", "previsao_contratacao", "uasg", 
            "orgao_responsavel", "sigla_om", "setor_responsavel", "responsavel_pela_demanda", 
            "ordenador_despesas", "agente_fiscal", "gerente_de_credito", "cod_par", 
            "prioridade_par", "cep", "endereco", "email", "telefone", 
            "dias_para_recebimento", "horario_para_recebimento", "valor_total", 
            "acao_interna", "fonte_recursos", "natureza_despesa", "unidade_orcamentaria", 
            "ptres", "atividade_custeio", "comentarios", "justificativa", "link_pncp", 
            "comunicacao_padronizada"
        ]

    def flags(self, index):
        if index.column() in self.non_editable_columns:
            return super().flags(index) & ~Qt.ItemFlag.ItemIsEditable  # Remove a permissão de edição
        return super().flags(index)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # Verifica se a coluna deve ser não editável e ajusta o retorno para DisplayRole
        if role == Qt.ItemDataRole.DisplayRole and index.column() in self.non_editable_columns:
            return super().data(index, role)

        return super().data(index, role)
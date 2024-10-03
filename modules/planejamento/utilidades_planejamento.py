import json
import sqlite3
import pandas as pd
import os
import re
# from bs4 import BeautifulSoup 
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtWidgets import QMessageBox
import logging
import num2words
import locale
import pandas as pd
import re
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def formatar_valor_monetario(valor):
    if pd.isna(valor):  # Verifica se o valor é NaN e ajusta para string vazia
        valor = ''
    # Limpa a string e converte para float
    valor = re.sub(r'[^\d,]', '', str(valor)).replace(',', '.')
    valor_float = float(valor) if valor else 0
    # Formata para a moeda local sem usar locale
    valor_monetario = f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    # Converte para extenso
    valor_extenso = num2words.num2words(valor_float, lang='pt_BR', to='currency')
    return valor_monetario, valor_extenso

def remover_caracteres_especiais(texto):
    mapa_acentos = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
        'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'ç': 'c', 'Ç': 'C', 'ñ': 'n', 'Ñ': 'N'
    }
    for caractere_original, caractere_novo in mapa_acentos.items():
        texto = texto.replace(caractere_original, caractere_novo)

    # Adicionando substituição para caracteres impeditivos em nomes de arquivos e pastas
    caracteres_impeditivos = r'\\/:*?"<>|'
    for caractere in caracteres_impeditivos:
        texto = texto.replace(caractere, '-')

    return texto

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None
        logging.basicConfig(level=logging.INFO, filename='app.log', filemode='a',
                            format='%(name)s - %(levelname)s - %(message)s')

    def __enter__(self):
        self.connection = self.connect_to_database()
        return self.connection

    def connect_to_database(self):
        try:
            connection = sqlite3.connect(self.db_path)
            return connection
        except sqlite3.Error as e:
            logging.error(f"Failed to connect to database at {self.db_path}: {e}")
            raise

    def execute_query(self, query, params=None):
        with self.connect_to_database() as conn:
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
            except sqlite3.Error as e:
                logging.error(f"Error executing query: {query}, Error: {e}")
                return None

    def execute_update(self, query, params=None):
        with self.connect_to_database() as conn:
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
            except sqlite3.Error as e:
                logging.error(f"Error executing update: {query}, Error: {e}")
                return False
            return True

    def close_connection(self):
        if self.connection:
            self.connection.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def ensure_database_exists(self):
        with self.connect_to_database() as conn:
            if not self.database_exists(conn):
                self.create_database(conn)
            self.criar_tabela_controle_prazos(conn)
            required_columns = {
                "id": "INTEGER PRIMARY KEY",
                "etapa": "TEXT",
                "id_processo": "TEXT",
                "nup": "TEXT",
                "objeto": "TEXT", 
                "uasg": "TEXT",
                "sigla_om": "TEXT",
                "pregoeiro": "TEXT",    
                "tipo": "TEXT", 
                "numero": "TEXT", 
                "ano": "TEXT",          
                "objeto_completo": "TEXT", 
                "valor_total": "TEXT", 
                "orgao_responsavel": "TEXT",
                "setor_responsavel": "TEXT", 
                "coordenador_planejamento": "TEXT", 
                "item_pca": "TEXT", 
                "portaria_PCA": "TEXT", 
                "data_sessao": "TEXT", 
                "data_limite_entrega_tr": "TEXT",
                "nup_portaria_planejamento": "TEXT", 
                "srp": "TEXT", "material_servico": "TEXT", 
                "parecer_agu": "TEXT", 
                "msg_irp": "TEXT",
                "data_limite_manifestacao_irp": "TEXT", 
                "data_limite_confirmacao_irp": "TEXT", 
                "num_irp": "TEXT", 
                "om_participantes": "TEXT",
                "link_pncp": "TEXT", 
                "link_portal_marinha": "TEXT", 
                "comentarios": "TEXT"
            }
            self.verify_and_create_columns(conn, 'controle_processos', required_columns)
            self.check_and_fix_id_sequence(conn)
            
    @staticmethod
    def create_database(conn):
        """
        Cria o banco de dados e a tabela de controle de processos se não existirem.

        Parameters:
            conn (sqlite3.Connection): Conexão com o banco de dados.
        """
        cursor = conn.cursor()
        # Query para criar tabela 'controle_processos'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS controle_processos (
                    id INTEGER PRIMARY KEY,
                    etapa TEXT,
                    id_processo TEXT,
                    nup TEXT,
                    objeto TEXT,
                    uasg TEXT,
                    sigla_om TEXT,
                    pregoeiro TEXT,
                    tipo TEXT,
                    numero TEXT,
                    ano TEXT,
                    objeto_completo TEXT,
                    valor_total TEXT,
                    orgao_responsavel TEXT,
                    setor_responsavel TEXT,
                    coordenador_planejamento TEXT,
                    item_pca TEXT,
                    portaria_PCA TEXT,
                    data_sessao TEXT,
                    data_limite_entrega_tr TEXT,
                    nup_portaria_planejamento TEXT,
                    srp TEXT,
                    material_servico TEXT,
                    parecer_agu TEXT,
                    msg_irp TEXT,
                    data_limite_manifestacao_irp TEXT,
                    data_limite_confirmacao_irp TEXT,
                    num_irp TEXT,
                    om_participantes TEXT,
                    link_pncp TEXT,
                    link_portal_marinha TEXT,
                    comentarios TEXT   
                )
        ''')
        conn.commit()


    def atualizar_ultima_etapa_data_final(self, conn):
        today_str = datetime.today().strftime('%Y-%m-%d')
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE controle_prazos
                SET data_final = ? WHERE (chave_processo, sequencial) IN (
                    SELECT chave_processo, MAX(sequencial) AS max_sequencial
                    FROM controle_prazos GROUP BY chave_processo
                )
            ''', (today_str,))
            conn.commit()
            logging.info("Data final updated successfully.")
        except sqlite3.Error as e:
            logging.error(f"Error updating the last stage: {e}")
            conn.rollback()
            
    @staticmethod
    def verify_and_create_columns(conn, table_name, required_columns):
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1]: row[2] for row in cursor.fetchall()}  # Storing column names and types

        # Criar uma lista das colunas na ordem correta e criar as colunas que faltam
        for column, column_type in required_columns.items():
            if column not in existing_columns:
                # Assume a default type if not specified, e.g., TEXT
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column} {column_type}")
                logging.info(f"Column {column} added to {table_name} with type {column_type}")
            else:
                # Check if the type matches, if not, you might handle or log this situation
                if existing_columns[column] != column_type:
                    logging.warning(f"Type mismatch for {column}: expected {column_type}, found {existing_columns[column]}")

        conn.commit()
        logging.info(f"All required columns are verified/added in {table_name}")

    @staticmethod
    def database_exists(conn):
        """
        Verifica se o banco de dados já existe.

        Parameters:
            conn (sqlite3.Connection): Conexão com o banco de dados.

        Returns:
            bool: True se o banco de dados existe, False caso contrário.
        """
        cursor = conn.cursor()
        # Verifica se a tabela controle_processos existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_processos';")
        return cursor.fetchone() is not None
    
    @staticmethod
    def check_and_fix_id_sequence(conn):
        cursor = conn.cursor()
        # Buscar os IDs em ordem para verificar se há lacunas
        cursor.execute("SELECT id FROM controle_processos ORDER BY id")
        ids = [row[0] for row in cursor.fetchall()]

        # Verificar se há lacunas nos IDs
        expected_id = 1  # Iniciando do ID 1, ajuste conforme sua lógica se necessário
        for actual_id in ids:
            if actual_id != expected_id:
                print(f"Gap before ID {actual_id}, expected {expected_id}")
                # Opção 1: Renumerar os IDs para preencher as lacunas
                # Este é um exemplo e pode ser perigoso se outras tabelas referenciarem esses IDs!
                # Seria necessário atualizar todas as referências para corresponder.
                cursor.execute("UPDATE controle_processos SET id = ? WHERE id = ?", (expected_id, actual_id))
                conn.commit()
            expected_id += 1

        # Ajustar a sequência automática para o próximo ID disponível após o último ID usado
        if ids:
            last_id = ids[-1]
            cursor.execute("PRAGMA auto_vacuum = FULL")
            cursor.execute(f"UPDATE SQLITE_SEQUENCE SET seq = {last_id} WHERE name = 'controle_processos'")
            cursor.execute("PRAGMA auto_vacuum = NONE")
            conn.commit()
                
    @staticmethod
    def criar_tabela_controle_prazos(conn):
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS controle_prazos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave_processo TEXT,
                etapa TEXT,
                data_inicial TEXT,
                data_final TEXT,
                dias_na_etapa INTEGER,
                comentario TEXT,
                sequencial INTEGER
            )
        ''')
        conn.commit()

    @staticmethod
    def carregar_ou_criar_tabela_controle_prazos(df_processos, conn):
        print("Criando tabela controle_prazos e inserindo dados...")
        DatabaseManager.criar_tabela_controle_prazos(conn)  # Já recebe conn, então está correto
        
        cursor = conn.cursor()
        for _, processo in df_processos.iterrows():
            chave_processo = f"{processo['id_processo']}"
            etapa = processo['etapa']
            data_inicial = datetime.today().strftime("%d-%m-%Y")
            data_final = None  # Será atualizado quando o programa for recarregado
            dias_na_etapa = 0
            comentario = ""
            # Consulta para encontrar o maior valor de sequencial para a chave_processo
            cursor.execute('SELECT MAX(sequencial) FROM controle_prazos WHERE chave_processo = ?', (chave_processo,))
            max_sequencial = cursor.fetchone()[0]
            sequencial = max_sequencial + 1 if max_sequencial else 1

            # Insere os dados na tabela 'controle_prazos'
            cursor.execute('''
                INSERT INTO controle_prazos (chave_processo, etapa, data_inicial, data_final, dias_na_etapa, comentario, sequencial)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (chave_processo, etapa, data_inicial, data_final, dias_na_etapa, comentario, sequencial))
        
        conn.commit()
        print("Dados inseridos na tabela controle_prazos com sucesso.")


    def carregar_tabela(self, parent):
        """
        Carrega dados de um arquivo .xlsx selecionado pelo usuário, faz correspondência das colunas,
        e insere os dados na tabela controle_processos do banco de dados SQLite.
        """
        fileName, _ = QFileDialog.getOpenFileName(
            parent, 
            "Carregar dados", 
            "", 
            "Excel Files (*.xlsx);;ODF Files (*.odt)"
        )
        if not fileName:
            QMessageBox.warning(parent, "Carregar Dados", "Nenhum arquivo selecionado.")
            return

        if not fileName.endswith('.xlsx'):
            QMessageBox.warning(parent, "Carregar Dados", "Formato de arquivo não suportado.")
            return
        
        try:
            df = pd.read_excel(fileName)

            # Colunas esperadas no DataFrame
            expected_columns = ["tipo", "numero", "ano", "id_processo", "nup", "objeto", "objeto_completo", "valor_total", "uasg", 
                                "orgao_responsavel", "sigla_om", "setor_responsavel", "coordenador_planejamento", 
                                "etapa", "pregoeiro", "item_pca", "portaria_PCA", "data_sessao",
                                "data_limite_entrega_tr", "nup_portaria_planejamento", "srp", 
                                "material_servico", "parecer_agu", "msg_irp", "data_limite_manifestacao_irp",
                                "data_limite_confirmacao_irp", "num_irp", "om_participantes", 
                                "link_pncp", "link_portal_marinha"]

            for col in expected_columns:
                if col not in df.columns:
                    df[col] = None  # Adiciona colunas faltantes como nulas para compatibilidade com SQL

            # Mapeamento de tipos abreviados para tipos completos
            tipo_abreviado_para_tipo = {
                "PE": "Pregão Eletrônico",
                "DE": "Dispensa Eletrônica",
                "CC": "Concorrência",
                "TJDL": "Termo de Justificativa de Dispensa de Licitação",
                "TJIL": "Termo de Justificativa de Inexigibilidade de Licitação"
            }

            # Processa cada linha para ajustar os valores de 'tipo', 'numero' e 'ano' com base em 'id_processo'
            def processar_linha(row):
                if pd.notna(row['id_processo']):
                    partes = row['id_processo'].split()
                    if len(partes) == 2 and '/' in partes[1]:
                        tipo_abreviado, ano_numero = partes[0], partes[1].split('/')
                        if tipo_abreviado in tipo_abreviado_para_tipo:
                            row['tipo'] = tipo_abreviado_para_tipo[tipo_abreviado]
                            row['numero'], row['ano'] = ano_numero[0], ano_numero[1]
                            return row
                return row

            df = df.apply(processar_linha, axis=1)

            if not df.empty:
                # Conecta ao banco de dados e insere os dados
                with sqlite3.connect(self.db_path) as conn:
                    df.to_sql('controle_processos', conn, if_exists='append', index=False, method="multi")
                    QMessageBox.information(parent, "Carregar Dados", "Dados carregados com sucesso.")
            else:
                QMessageBox.warning(parent, "Carregar Dados", "O arquivo está vazio.")

        except Exception as e:
            QMessageBox.critical(parent, "Carregar Dados", f"Erro ao carregar os dados: {e}")

    def atualizar_ultima_etapa_data_final(self, conn):
        """
        Atualiza a data_final para hoje apenas para a última etapa de cada chave_processo.
        """
        today_str = datetime.today().strftime('%Y-%m-%d')
        try:
            cursor = conn.cursor()
            # Consulta para atualizar a data_final para hoje para o último sequencial de cada chave_processo
            cursor.execute('''
                UPDATE controle_prazos
                SET data_final = ?
                WHERE (chave_processo, sequencial) IN (
                    SELECT chave_processo, MAX(sequencial) AS max_sequencial
                    FROM controle_prazos
                    GROUP BY chave_processo
                )
            ''', (today_str,))

            # Recalcula os dias na etapa para todos os registros que foram atualizados
            cursor.execute('''
                UPDATE controle_prazos
                SET dias_na_etapa = julianday(data_final) - julianday(data_inicial)
            ''')

            conn.commit()
            print("Data final atualizada para todos os últimos sequenciais.")
        except sqlite3.Error as e:
            print("Erro ao atualizar a última etapa:", e)

            
    def atualizar_dias_na_etapa(self, conn):
        today_str = datetime.today().strftime('%Y-%m-%d')
        try:
            cursor = conn.cursor()
            # Atualizar a data_final para hoje para a última etapa de cada chave_processo
            cursor.execute('''
                UPDATE controle_prazos
                SET data_final = ?
                FROM (
                    SELECT chave_processo, MAX(sequencial) as max_sequencial
                    FROM controle_prazos
                    GROUP BY chave_processo
                ) AS max_etapas
                WHERE controle_prazos.chave_processo = max_etapas.chave_processo
                AND controle_prazos.sequencial = max_etapas.max_sequencial
                AND controle_prazos.data_final IS NULL
            ''', (today_str,))

            # Recalcular os dias na etapa
            cursor.execute('''
                UPDATE controle_prazos
                SET dias_na_etapa = julianday(data_final) - julianday(data_inicial)
            ''')

            conn.commit()
        except sqlite3.Error as e:
            print("Erro ao atualizar dias na etapa:", e)

    def inserir_controle_prazo(self, chave_processo, etapa, data_inicial, comentario):
        with self as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO controle_prazos (chave_processo, etapa, data_inicial, comentario, sequencial)
                VALUES (?, ?, ?, ?, (SELECT COALESCE(MAX(sequencial) + 1, 1) FROM controle_prazos WHERE chave_processo = ?))
            ''', (chave_processo, etapa, data_inicial, comentario, chave_processo))
            conn.commit()

    @staticmethod
    def verificar_e_atualizar_etapas(conn):
        # Verifica se há correspondência entre as tabelas controle_processos e controle_prazos
        query_verificar = """
        SELECT cp.id_processo, MAX(pr.sequencial) AS ultimo_sequencial
        FROM controle_processos cp
        LEFT JOIN controle_prazos pr ON cp.id_processo = pr.chave_processo
        GROUP BY cp.id_processo;
        """
        cursor = conn.cursor()
        cursor.execute(query_verificar)
        correspondencias = cursor.fetchall()
        
        # Atualiza a coluna etapa com o último sequencial correspondente ou com "Planejamento"
        for id_processo, ultimo_sequencial in correspondencias:
            if ultimo_sequencial is None:
                nova_etapa = "Planejamento"
            else:
                # Consulta para obter a etapa baseada no último sequencial
                query_etapa = """
                SELECT etapa
                FROM controle_prazos
                WHERE chave_processo = ? AND sequencial = ?;
                """
                cursor.execute(query_etapa, (id_processo, ultimo_sequencial))
                nova_etapa_result = cursor.fetchone()
                nova_etapa = nova_etapa_result[0] if nova_etapa_result else "Planejamento"
            
            # Atualiza a coluna etapa na tabela controle_processos
            query_atualizar = """
            UPDATE controle_processos
            SET etapa = ?
            WHERE id_processo = ?;
            """
            cursor.execute(query_atualizar, (nova_etapa, id_processo))
        conn.commit()

    def popular_controle_prazos_se_necessario(self):
        cursor = self.connection.cursor()
        # Verifica se existem registros na tabela controle_prazos
        cursor.execute("SELECT COUNT(*) FROM controle_prazos")
        registros = cursor.fetchone()[0]

        if registros == 0:
            # Se não existem registros em controle_prazos, busca os dados de controle_processos
            cursor.execute("SELECT id_processo FROM controle_processos")
            processos = cursor.fetchall()

            # Prepara os dados iniciais para inserção baseados em controle_processos
            dados_iniciais = []
            for processo in processos:
                chave_processo = processo[0]
                etapa = "Planejamento"
                data_inicial = datetime.today().strftime("%Y-%m-%d")
                dados_iniciais.append((chave_processo, etapa, data_inicial, None, 0, "", 1))

            # Insere os dados iniciais na tabela controle_prazos
            cursor.executemany("""
                INSERT INTO controle_prazos (chave_processo, etapa, data_inicial, data_final, dias_na_etapa, comentario, sequencial)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, dados_iniciais)

            self.connection.commit()
            print("Dados iniciais inseridos na tabela controle_prazos com sucesso.")

def carregar_dados_pregao(index, caminho_banco_dados):
    try:
        logging.debug(f"Conectando ao banco de dados: {caminho_banco_dados}")
        connection = sqlite3.connect(caminho_banco_dados)
        query = f"SELECT * FROM controle_processos WHERE id={index + 1}"
        logging.debug(f"Executando consulta SQL: {query}")
        df_registro_selecionado = pd.read_sql_query(query, connection)
        connection.close()
        logging.debug(f"Dados carregados com sucesso para o índice {index}: {df_registro_selecionado}")
        return df_registro_selecionado
    except Exception as e:
        logging.error(f"Erro ao carregar dados do banco de dados: {e}", exc_info=True)
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro

# def carregar_dados_licitacao(id_processo, caminho_banco_dados):
#     try:
#         logging.debug(f"Conectando ao banco de dados: {caminho_banco_dados}")
#         connection = sqlite3.connect(caminho_banco_dados)
#         query = f"SELECT * FROM controle_processos WHERE id_processo='{id_processo}'"
#         logging.debug(f"Executando consulta SQL: {query}")
#         df_registro_selecionado = pd.read_sql_query(query, connection)
#         connection.close()
#         logging.debug(f"Dados carregados com sucesso para id_processo {id_processo}: {df_registro_selecionado}")
#         return df_registro_selecionado
#     except Exception as e:
#         logging.error(f"Erro ao carregar dados do banco de dados: {e}", exc_info=True)
#         return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
def carregar_dados_licitacao(index, caminho_banco_dados):
    try:
        logging.debug(f"Conectando ao banco de dados: {caminho_banco_dados}")
        connection = sqlite3.connect(caminho_banco_dados)
        query = f"SELECT * FROM controle_processos WHERE id_processo='{index}'"
        logging.debug(f"Executando consulta SQL: {query}")
        df_registro_selecionado = pd.read_sql_query(query, connection)
        connection.close()
        
        if df_registro_selecionado.empty:
            logging.warning("A consulta retornou um DataFrame vazio.")
        
        logging.debug(f"Dados carregados com sucesso para o índice {index}: {df_registro_selecionado}")
        return df_registro_selecionado
    except Exception as e:
        logging.error(f"Erro ao carregar dados do banco de dados: {e}", exc_info=True)
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
    
def carregar_dados_dispensa(id_processo, caminho_banco_dados):
    try:
        logging.debug(f"Conectando ao banco de dados: {caminho_banco_dados}")
        connection = sqlite3.connect(caminho_banco_dados)
        query = f"SELECT * FROM controle_dispensas WHERE id_processo='{id_processo}'"
        logging.debug(f"Executando consulta SQL: {query}")
        df_registro_selecionado = pd.read_sql_query(query, connection)
        connection.close()
        logging.debug(f"Dados carregados com sucesso para id_processo {id_processo}: {df_registro_selecionado}")
        return df_registro_selecionado
    except Exception as e:
        logging.error(f"Erro ao carregar dados do banco de dados: {e}", exc_info=True)
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro

def carregar_dados_processos(controle_processos_path):
    try:
        conn = sqlite3.connect(str(controle_processos_path))
        df_processos = pd.read_sql_query("SELECT * FROM controle_processos", conn)
        df_processos['etapa'] = 'Planejamento'
        conn.close()
        return df_processos
    except Exception as e:
        print(f"Erro ao carregar dados do processo: {e}")
        return pd.DataFrame()

ABREV_MAP = {
    "Pregão Eletrônico": "PE",
    "Concorrência": "CC",
    "Dispensa Eletrônica": "DE",
    "Termo de Justificativa de Dispensa de Licitação": "TJDL",
    "Termo de Justificativa de Inexigibilidade de Licitação": "TJIL"
}

STYLE_BORDER = """
    QGroupBox { border: 1px solid gray; border-radius: 5px; margin-top: 0.5em; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }
"""


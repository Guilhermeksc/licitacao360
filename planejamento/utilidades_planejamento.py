import json
import sqlite3
import pandas as pd
import os
import re
from bs4 import BeautifulSoup 
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtWidgets import QMessageBox
import logging

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        logging.basicConfig(level=logging.INFO, filename='app.log', filemode='a',
                            format='%(name)s - %(levelname)s - %(message)s')

    def __enter__(self):
        try:
            self.connection = sqlite3.connect(self.db_path)
            return self.connection
        except sqlite3.Error as e:
            logging.error(f"Failed to connect to database at {self.db_path}: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.connection:
                self.connection.close()
        except sqlite3.Error as e:
            logging.error(f"Failed to close the database connection: {e}")
            raise

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
                    tipo TEXT,
                    numero TEXT,
                    ano TEXT,   
                    id_processo TEXT,
                    nup TEXT,
                    objeto TEXT,
                    objeto_completo TEXT,
                    uasg TEXT,
                    orgao_responsavel TEXT,
                    sigla_om TEXT,
                    setor_responsavel TEXT,
                    coordenador_planejamento TEXT,
                    etapa TEXT,
                    pregoeiro TEXT,
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
                    link_portal_marinha TEXT   
                )
        ''')
        conn.commit()

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
            expected_columns = ["tipo", "numero", "ano", "id_processo", "nup", "objeto", "objeto_completo", "uasg", 
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

def extrair_chave_processo(itemText):
    # Exemplo usando BeautifulSoup para análise HTML
    soup = BeautifulSoup(itemText, 'html.parser')
    texto_completo = soup.get_text()
    # Supondo que o texto completo tenha a forma 'MOD NUM_PREGAO/ANO_PREGAO Objeto'
    # Use expressão regular para extrair a chave
    match = re.search(r'(\w+)\s(\d+)/(\d+)', texto_completo)
    if match:
        return f"{match.group(1)} {match.group(2)}/{match.group(3)}"
    return None

def extrair_chave_processo(itemText):
    # Exemplo usando BeautifulSoup para análise HTML
    soup = BeautifulSoup(itemText, 'html.parser')
    texto_completo = soup.get_text()
    # Supondo que o texto completo tenha a forma 'MOD NUM_PREGAO/ANO_PREGAO Objeto'
    # Use expressão regular para extrair a chave
    match = re.search(r'(\w+)\s(\d+)/(\d+)', texto_completo)
    if match:
        return f"{match.group(1)} {match.group(2)}/{match.group(3)}"
    return None

def carregar_dados_pregao(index, caminho_banco_dados):
    """
    Carrega os dados de pregão do banco de dados SQLite especificado pelo caminho_banco_dados.

    Parâmetros:
    - index: O índice da linha selecionada na QTableView.
    - caminho_banco_dados: O caminho para o arquivo do banco de dados SQLite.
    
    Retorna:
    - Um DataFrame do Pandas contendo os dados do registro selecionado.
    """
    connection = sqlite3.connect(caminho_banco_dados)
    query = f"SELECT * FROM controle_processos WHERE id={index+1}"
    df_registro_selecionado = pd.read_sql_query(query, connection)
    connection.close()
    return df_registro_selecionado

def carregar_dados_processos(controle_processos_path):
    try:
        # Conecta ao banco de dados SQLite
        conn = sqlite3.connect(controle_processos_path)
        # Executa a consulta SQL para selecionar todos os dados da tabela 'controle_processos'
        df_processos = pd.read_sql_query("SELECT * FROM controle_processos", conn)
        # Fecha a conexão com o banco de dados
        conn.close()

        # Define a coluna 'etapa' como 'Planejamento' para todos os registros
        df_processos['etapa'] = 'Planejamento'

        return df_processos
    
    except Exception as e:
        print(f"Erro ao carregar dados do processo: {e}")
        return pd.DataFrame()



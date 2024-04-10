import json
import sqlite3
import pandas as pd
import os
import re
from bs4 import BeautifulSoup 
from datetime import datetime
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        return self.connection  # Certifique-se de retornar a conexão aqui

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()
            self.connection = None 

    def initialize_database(self):
        with self as conn:
            self.create_database(conn)
            self.criar_tabela_controle_prazos(conn)

    def create_database(self):
        # Não é mais necessário passar a conexão
        cursor = self.connection.cursor()
        # Query para criar tabela 'controle_processos'
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
                    om_participantes TEXT          
                )
        ''')
        self.connection.commit()

    def atualizar_etapa_processo(self, chave_processo, nova_etapa, data_atual_str, comentario):
        with self as conn:
            cursor = conn.cursor()
            # Atualizar a etapa do processo
            cursor.execute('''
                UPDATE controle_prazos SET etapa = ?, data_final = ?, comentario = ? 
                WHERE chave_processo = ? AND etapa != ?
            ''', (nova_etapa, data_atual_str, comentario, chave_processo, nova_etapa))
            conn.commit()

    def ensure_database_exists(self):
        if not Path(self.db_path).exists():
            with self:
                self.create_database() 

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
            chave_processo = f"{processo['modalidade']}"
            etapa = processo['etapa']
            data_inicial = datetime.today().strftime("%d-%m-%Y")
            data_final = None  # Será atualizado quando o programa for recarregado
            dias_na_etapa = 0
            comentario = ""
            sequencial = 1
            
            # Insere os dados na tabela 'controle_prazos'
            cursor.execute('''
                INSERT INTO controle_prazos (chave_processo, etapa, data_inicial, data_final, dias_na_etapa, comentario, sequencial)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (chave_processo, etapa, data_inicial, data_final, dias_na_etapa, comentario, sequencial))
        
        conn.commit()
        conn.close()
        print("Dados inseridos na tabela controle_prazos com sucesso.")

    def inserir_controle_prazo(self, chave_processo, etapa, data_inicial, comentario):
        with self as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO controle_prazos (chave_processo, etapa, data_inicial, comentario, sequencial)
                VALUES (?, ?, ?, ?, (SELECT COALESCE(MAX(sequencial) + 1, 1) FROM controle_prazos WHERE chave_processo = ?))
            ''', (chave_processo, etapa, data_inicial, comentario, chave_processo))
            conn.commit()

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



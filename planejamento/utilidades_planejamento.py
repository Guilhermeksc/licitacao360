import json
import sqlite3
import pandas as pd
import os
import re
from bs4 import BeautifulSoup 
from datetime import datetime

def inicializar_json_do_excel(caminho_excel, caminho_json):
    # Verificar se o arquivo JSON já existe
    if os.path.exists(caminho_json):
        print(f"O arquivo JSON '{caminho_json}' já existe. Nenhuma ação necessária.")
        return

    # Verificar se o caminho do Excel foi fornecido
    if caminho_excel is None:
        print("Caminho do arquivo Excel não fornecido.")
        return

    # Ler os dados do arquivo Excel
    df = pd.read_excel(caminho_excel)

    # Estrutura para armazenar os dados dos processos
    processos_json = {}

    # Iterar sobre cada linha do DataFrame
    for _, row in df.iterrows():
        chave_processo = f"{row['mod']} {row['num_pregao']}/{row['ano_pregao']}"
        # Inicializar a chave do processo com o objeto e um histórico inicial
        processos_json[chave_processo] = {
            "objeto": row["objeto"],
            "historico": [
                {
                    "etapa": "Planejamento",
                    "data_inicial": None,  # Definir conforme necessário
                    "data_final": None,    # Definir conforme necessário
                    "dias_na_etapa": 0,
                    "comentario": "",
                    "sequencial": 1
                }
            ]
        }

    # Escrever os dados em um arquivo JSON
    with open(caminho_json, 'w', encoding='utf-8') as file:
        json.dump(processos_json, file, indent=4, ensure_ascii=False)
    print(f"Arquivo JSON '{caminho_json}' criado com sucesso a partir do Excel.")

def ler_arquivo_json(caminho):
    try:
        with open(caminho, 'r', encoding='utf-8') as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        return {}

def escrever_arquivo_json(caminho, dados):
    with open(caminho, 'w', encoding='utf-8') as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)        

def carregar_ou_criar_arquivo_json(df_processos, caminho_json):
    print(f"Carregando ou criando o arquivo JSON: {caminho_json}")
    
    # Verifica se o arquivo JSON já existe
    if caminho_json.exists():
        print("O arquivo JSON já existe. Carregando e atualizando a data_final...")
        with open(caminho_json, 'r', encoding='utf-8') as file:
            processos_json = json.load(file)
    else:
        print("O arquivo JSON não existe. Criando com os dados atuais do DataFrame...")
        processos_json = {}

    # Adiciona os dados do DataFrame ao dicionário processos_json
    for _, processo in df_processos.iterrows():
        chave_processo = f"{processo['modalidade']}"
        print(f"Adicionando processo: {chave_processo} ao JSON")
        if chave_processo not in processos_json:
            processos_json[chave_processo] = {
                "objeto": processo['objeto'],
                "historico": [{
                    "etapa": processo['etapa'],
                    "data_inicial": datetime.today().strftime("%d-%m-%Y"),
                    "data_final": None,  # Será atualizado quando o programa for recarregado
                    "dias_na_etapa": 0,
                    "comentario": "",
                    "sequencial": 1
                }]
            }

    # Escreve o novo arquivo JSON
    with open(caminho_json, 'w', encoding='utf-8') as file:
        json.dump(processos_json, file, ensure_ascii=False, indent=4)
        print("Arquivo JSON criado com sucesso.")

    # Adicione este print para verificar se o arquivo foi realmente criado
    print(f"Arquivo JSON criado: {caminho_json}")

# def carregar_ou_criar_arquivo_json(df_processos, caminho_json):
#     print(f"Carregando ou criando o arquivo JSON: {caminho_json}")
#     processos_json = {}

#     if os.path.exists(caminho_json):
#         print("O arquivo JSON já existe. Carregando e atualizando a data_final...")
#         with open(caminho_json, 'r', encoding='utf-8') as file:
#             processos_json = json.load(file)

#         # Atualizar a data_final da última entrada do histórico para 'hoje' em todos os processos
#         data_atual_str = datetime.today().strftime("%d-%m-%Y")
#         for processo in processos_json.values():
#             if processo['historico']:  # Verificar se há histórico
#                 # Apenas atualizar a data_final se ela ainda não estiver definida
#                 if processo['historico'][-1]['data_final'] is None:
#                     processo['historico'][-1]['data_final'] = data_atual_str
#                     # Opcionalmente, atualize dias_na_etapa se aplicável
#                     if processo['historico'][-1]['data_inicial']:
#                         data_inicial = datetime.strptime(processo['historico'][-1]['data_inicial'], "%d-%m-%Y")
#                         dias_na_etapa = (datetime.today() - data_inicial).days
#                         processo['historico'][-1]['dias_na_etapa'] = dias_na_etapa

#         # Escrever as alterações de volta ao arquivo JSON
#         with open(caminho_json, 'w', encoding='utf-8') as file:
#             json.dump(processos_json, file, ensure_ascii=False, indent=4)
#     else:
#         print("O arquivo JSON não existe. Criando com os dados atuais do DataFrame...")
#         for _, processo in df_processos.iterrows():
#             chave_processo = f"{processo['modalidade']}"
#             print(f"Adicionando processo: {chave_processo} ao JSON")
#             if chave_processo not in processos_json:
#                 processos_json[chave_processo] = {
#                     "objeto": processo['objeto'],
#                     "historico": [{
#                         "etapa": processo['etapa'],
#                         "data_inicial": datetime.today().strftime("%d-%m-%Y"),
#                         "data_final": None,  # Será atualizado quando o programa for recarregado
#                         "dias_na_etapa": 0,
#                         "comentario": "",
#                         "sequencial": 1
#                     }]
#                 }
#         # Escreve o novo arquivo JSON
#         with open(caminho_json, 'w', encoding='utf-8') as file:
#             json.dump(processos_json, file, ensure_ascii=False, indent=4)
#         print("Arquivo JSON criado com sucesso.")

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

import os
import json

def carregar_dados_processos(controle_processos_path, controle_etapa_json):
    try:
        # Conecta ao banco de dados SQLite
        conn = sqlite3.connect(controle_processos_path)
        # Executa a consulta SQL para selecionar todos os dados da tabela 'controle_processos'
        df_processos = pd.read_sql_query("SELECT * FROM controle_processos", conn)
        # Fecha a conexão com o banco de dados
        conn.close()
        
        # Carrega os dados do arquivo JSON com a codificação UTF-8
        with open(controle_etapa_json, 'r', encoding='utf-8') as json_file:
            controle_etapa = json.load(json_file)

        # Preenche a coluna 'etapa' com base no arquivo JSON
        for index, row in df_processos.iterrows():
            modalidade = row['modalidade']
            if modalidade in controle_etapa:
                etapa = controle_etapa[modalidade]['historico'][-1]['etapa']
                df_processos.at[index, 'etapa'] = etapa
            else:
                df_processos.at[index, 'etapa'] = 'Planejamento'

        return df_processos
    except Exception as e:
        print(f"Erro ao carregar dados do processo: {e}")
        # Se ocorrer um erro ao carregar os dados, chame a função para criar o arquivo JSON
        print("Chamando a função para criar o arquivo JSON...")
        carregar_ou_criar_arquivo_json(pd.DataFrame(), controle_etapa_json)
        return pd.DataFrame()


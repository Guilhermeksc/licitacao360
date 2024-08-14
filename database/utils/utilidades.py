from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import pdfplumber
from pathlib import Path
import os
from datetime import datetime
import json
import pandas as pd
import locale

try:
    # Tenta a configuração comum em sistemas baseados em Unix
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    # Tenta a configuração comum em sistemas Windows
    locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')

import math

def convert_pdf_to_txt(pdf_dir, txt_dir, progress_bar, progress_callback):    
    # Verifica se TXT_DIR existe. Se não, cria o diretório.
    if not txt_dir.exists():
        txt_dir.mkdir(parents=True, exist_ok=True)
    else:
        # Se TXT_DIR existir, deleta todos os arquivos dentro dele.
        for file in txt_dir.iterdir():
            if file.is_file():
                file.unlink()

    # Inicia o processo de conversão
    pdf_files = list(pdf_dir.glob("*.pdf"))
    total_files = len(pdf_files)
    
    for index, pdf_file in enumerate(pdf_files):
        with pdfplumber.open(pdf_file) as pdf:
            texts = [page.extract_text() for page in pdf.pages]
            all_text = ' '.join(texts).replace('\n', ' ').replace('\x0c', ' ')

            txt_file = txt_dir / f"{pdf_file.stem}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(all_text)

        # Atualiza a barra de progresso
        progress = math.ceil((index + 1) / total_files * 100)
        progress_callback(progress)
    
    # Garante que a barra de progresso atinja 100%
    progress_callback(100)



def obter_arquivos_txt(directory: str) -> list:
    """Retorna a lista de arquivos TXT em um diretório."""
    return [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.txt')]

def ler_arquivos_txt(file_path: str) -> str:
    """Lê o conteúdo de um arquivo TXT."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def formatar_brl(valor):
    try:
        if valor is None:
            return "Não disponível"  # Retorna uma string informativa caso o valor seja None
        # Formata o número no formato monetário brasileiro sem utilizar a biblioteca locale
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "Valor inválido"  # Retorna isso se não puder converter para float

def save_to_excel(df, filepath):
    df.to_excel(filepath, index=False, engine='openpyxl')

def ler_arquivo_json(caminho):
    try:
        with open(caminho, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Retorna uma estrutura vazia

def escrever_arquivo_json(caminho, dados):
    with open(caminho, 'w', encoding='utf-8') as file:
        json.dump(dados, file, indent=4, ensure_ascii=False)

def inicializar_json_do_excel(caminho_excel, caminho_json):
    df = pd.read_excel(caminho_excel)
    processos_json = ler_arquivo_json(caminho_json)

    for _, row in df.iterrows():
        mod = row['mod']  # Supondo que 'mod' é uma coluna no seu DataFrame
        chave_processo = f"{mod} {row['num_pregao']}/{row['ano_pregao']}"
        processo_atual = processos_json.get(chave_processo, {})
        historico_atual = processo_atual.get("historico", [])

        processos_json[chave_processo] = {
            "nup": row["nup"],
            "objeto": row["objeto"],
            "uasg": row["uasg"],
            "orgao_responsavel": row["orgao_responsavel"],
            "sigla_om": row["sigla_om"],
            "setor_responsavel": row["setor_responsavel"],
            "historico": historico_atual,
            "etapa_atual": processo_atual.get("etapa_atual", "Planejamento")
        }

    with open(caminho_json, 'w', encoding='utf-8') as file:
        json.dump(processos_json, file, indent=4, ensure_ascii=False)

def sincronizar_json_com_dataframe(df, caminho_json):
    processos_json = ler_arquivo_json(caminho_json)
    chaves_df = set(df.apply(lambda row: f"{row['mod']} {row['num_pregao']}/{row['ano_pregao']}", axis=1))

    chaves_para_remover = set(processos_json.keys()) - chaves_df

    # Remover processos que não estão mais no DataFrame
    for chave in chaves_para_remover:
        del processos_json[chave]

    # Atualizar ou adicionar processos com base no DataFrame
    for _, row in df.iterrows():
        mod = row['mod']  # Supondo que 'mod' é uma coluna no seu DataFrame
        chave_processo = f"{mod} {row['num_pregao']}/{row['ano_pregao']}"
        historico_atual = processos_json.get(chave_processo, {}).get("historico", [])

        processos_json[chave_processo] = {
            "nup": row["nup"],
            "objeto": row["objeto"],
            "uasg": row["uasg"],
            "orgao_responsavel": row["orgao_responsavel"],
            "sigla_om": row["sigla_om"],
            "setor_responsavel": row["setor_responsavel"],
            "historico": historico_atual,
            "etapa_atual": row.get("etapa_atual", "Planejamento")
        }

    with open(caminho_json, 'w', encoding='utf-8') as file:
        json.dump(processos_json, file, indent=4, ensure_ascii=False)

def calcular_dias(data_inicial, data_final):
    """Calcula a diferença em dias entre duas datas.

    Args:
        data_inicial (datetime.date): A data inicial.
        data_final (datetime.date): A data final.

    Returns:
        int: A diferença em dias entre as duas datas.
    """
    if not data_inicial or not data_final:
        return 0
    return (data_final - data_inicial).days

def formatar_data(data_str, formato='%d-%m-%Y'):
    """Converte uma string de data para um objeto datetime.date.

    Args:
        data_str (str): A string da data para converter.
        formato (str, optional): O formato da string de data. Padrão para '%d-%m-%Y'.

    Returns:
        datetime.date: A data convertida, ou None se a conversão falhar.
    """
    try:
        return datetime.strptime(data_str, formato).date()
    except ValueError:
        return None
    
class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class NoScrollDateEdit(QDateEdit):
    def wheelEvent(self, event):
        event.ignore()

class CustomHeaderView(QHeaderView):
    def __init__(self, orientation, etapas, parent=None):
        super().__init__(orientation, parent)
        
        self.etapas = etapas
        self.setMouseTracking(True)  # Habilita o rastreamento do mouse

    def event(self, event):
        if event.type() == QEvent.Type.ToolTip:
            pos = event.pos()  # Para PyQt5, use pos() em vez de position()
            index = self.logicalIndexAt(pos.x(), pos.y())
            if index >= 0 and index < len(self.etapas):
                # Encontrar o nome completo da etapa para essa coluna
                etapa_nome = list(self.etapas.keys())[index]
                QToolTip.showText(event.globalPos(), etapa_nome, self)
                return True
        return super().event(event)
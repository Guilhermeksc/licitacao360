from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import pandas as pd
import os
import subprocess
from PyQt6.QtWidgets import QMessageBox

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import pandas as pd
import os
import subprocess
from datetime import datetime

def format_numero_controle_ata(numero_controle_ata):
    # Remove zeros à esquerda
    numero_sem_zeros = numero_controle_ata.lstrip('0')
    
    # Garante pelo menos três dígitos, adicionando zeros à esquerda se necessário
    if len(numero_sem_zeros) < 3:
        numero_sem_zeros = numero_sem_zeros.zfill(3)
    
    return numero_sem_zeros

def gerar_relatorio_atas(model, table_name, nome_unidade, codigo_unidade, output_dir=os.getcwd()):
    """Gera um relatório PDF com os dados da tabela do modelo fornecido e salva no diretório especificado."""
    if model is None:
        raise ValueError("Modelo de dados não inicializado.")

    # Extrair os dados do modelo para um DataFrame
    df = obter_dados_do_modelo(model)

    if df.empty:
        raise ValueError("Não há dados para gerar o relatório.")

    # Caminho para o PDF gerado com o nome baseado em table_name
    pdf_path = os.path.join(output_dir, f"relatorio_atas_{table_name}.pdf")

    # Gerar o PDF
    criar_pdf_relatorio(df, pdf_path, nome_unidade, codigo_unidade)

    # Abrir o PDF gerado
    subprocess.run(f'start {pdf_path}', shell=True, check=True)


def criar_pdf_relatorio(df, pdf_path, nome_unidade, codigo_unidade):
    print(df.columns)
    print(df)
    """Cria o PDF com os dados do DataFrame fornecido e formatação especificada."""
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica", 12)

    # Cabeçalho
    titulo = f"{nome_unidade} - UASG: {codigo_unidade}"
    subtitulo = "Controle de Atas"
    data_atual = datetime.now().strftime("%d/%m/%Y")
    atualizado_em = f"Atualizado em: {data_atual}"

    # Posições iniciais
    x_offset = 50
    y_offset = height - 50
    line_height = 14

    # Adicionar o cabeçalho ao PDF
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x_offset, y_offset, titulo)
    y_offset -= line_height
    c.setFont("Helvetica", 12)
    c.drawString(x_offset, y_offset, subtitulo)
    y_offset -= line_height
    # Alinhar o texto "Atualizado em" à direita e em itálico
    c.setFont("Helvetica-Oblique", 12)
    c.drawRightString(width - 50, y_offset, atualizado_em)
    y_offset -= line_height

    # Desenhar uma linha tracejada de uma borda à outra
    c.setDash(3, 3)  # Define o estilo de linha tracejada (comprimento do traço, comprimento do espaço)
    c.line(50, y_offset, width - 50, y_offset)
    c.setDash([])  # Retorna ao estilo de linha contínua
    y_offset -= line_height * 2  # Espaço extra antes dos dado
    
    # Escrever os dados das linhas no formato especificado
    for _, row in df.iterrows():
        id_pncp = row.get('id_pncp', 'N/A')
        vigencia_inicio = row.get('vigencia_inicial', 'N/A')
        vigencia_final = row.get('vigencia_final', 'N/A')
        numero_controle_ata = row.get('Número', 'N/A')
        numero_controle_ata_formatado = format_numero_controle_ata(numero_controle_ata)
        print(numero_controle_ata)
        cnpj = row.get('CNPJ', 'N/A')
        ano = row.get('sequencial_ano_pncp', 'N/A')
        sequencial = row.get('Sequencial', 'N/A') 
        numero = row.get('sequencial_ata_pncp', 'N/A')
        numero_ata = f"{codigo_unidade}/{ano}-{numero_controle_ata_formatado}/00"
        # URL do hiperlink
        url = f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/atas/{numero}/arquivos/1"

        # Adicionar os dados ao PDF
        c.setFont("Helvetica-Bold", 12)
        id_pncp_text = f"ID PNCP: {id_pncp}"
        c.drawString(x_offset, y_offset, id_pncp_text)

        # Calcular a largura do texto para posicionar "Abrir Documento"
        text_width = c.stringWidth(id_pncp_text, "Helvetica-Bold", 12)
        c.setFillColorRGB(0, 0, 1)  # Mudar a cor do texto para azul
        c.drawString(x_offset + text_width + 10, y_offset, "Download da Ata")
        c.linkURL(url, (x_offset + text_width + 10, y_offset, x_offset + text_width + 100, y_offset + line_height), relative=0)
        c.setFillColorRGB(0, 0, 0)  # Restaurar a cor do texto para preto
        y_offset -= line_height
        c.setFont("Helvetica", 12)
        c.drawString(x_offset, y_offset, f"Número da Ata: {numero_ata} - Vigência: {vigencia_inicio} até {vigencia_final}")
        y_offset -= line_height * 2  # Espaço extra entre registros

        # Quebrar a página se necessário
        if y_offset < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_offset = height - 50

    # Salvar o PDF
    c.save()


def obter_dados_do_modelo(model):
    """Extrai os dados do modelo PyQt para um DataFrame do pandas."""
    rows = [
        [model.data(model.index(row, col)) for col in range(model.columnCount())]
        for row in range(model.rowCount())
    ]
    headers = [model.headerData(col, Qt.Orientation.Horizontal) for col in range(model.columnCount())]
    return pd.DataFrame(rows, columns=headers)
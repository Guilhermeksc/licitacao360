import pandas as pd
from bs4 import BeautifulSoup
import os
from pathlib import Path

# Diretório base e caminho do arquivo HTML
BASE_DIR = Path(__file__).resolve().parent
html_path = BASE_DIR / "FornecedorResultadoDecreto.htm"

# Função para ler o conteúdo HTML
def ler_html(arquivo):
    with open(arquivo, 'r', encoding='iso-8859-1') as f:
        conteudo_html = f.read()
    return conteudo_html

# Função para analisar os blocos de fornecedores
def parse_fornecedores(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    fornecedores = soup.find_all('td', {'align': 'left', 'colspan': '7'})
    return fornecedores


def extrair_valor_com_tratamento_de_erros(tag_name, classe_css, fornecedor):
    """
    Extrai o valor de uma tag específica com tratamento de erros.

    Args:
        tag_name (str): Nome da tag HTML que contém o valor (por exemplo, 'span', 'p').
        classe_css (str): Classe CSS do elemento que contém o valor (por exemplo, 'classe-valor').
        fornecedor (BeautifulSoup.element): Elemento BeautifulSoup que representa o fornecedor (geralmente uma div ou seção).

    Returns:
        str: Valor extraído da tag ou string vazia se não encontrado.
    """

    try:
        # Localiza o elemento HTML que contém o valor desejado
        elemento_valor = fornecedor.find(tag_name, class_=classe_css)

        # Extrai o texto do elemento e remove espaços em branco desnecessários
        if elemento_valor:
            valor_extraido = elemento_valor.text.strip()
        else:
            valor_extraido = ""

    except Exception as e:
        # Registra o erro e retorna string vazia
        print(f"Erro ao extrair valor: {e}")
        valor_extraido = ""

    return valor_extraido

    
# Função para analisar os itens de cada fornecedor
def parse_itens(fornecedor):
    item_table = fornecedor.find_next('tr')
    rows = []
    for row in item_table.find_next_siblings('tr'):
        if row.find('td', {'align': 'left', 'colspan': '7'}):
            break
        cells = row.find_all('td')
        if len(cells) == 7:
            # Extração de Item, Descrição, Unidade de Fornecimento, Quantidade, Valor Estimado, Valor Homologado, Valor Total do Item
            item_dados = [cell.text.strip() for cell in cells]

            # Extração de Marca com Tratamento de Erros
            marca = extrair_valor_com_tratamento_de_erros("Marca", "tex5a", fornecedor)

            # Extração de Fabricante com Tratamento de Erros
            fabricante = extrair_valor_com_tratamento_de_erros("Fabricante", "tex5a", fornecedor)

            # Impressão de Combinações
            print(f"Combinações encontradas: Marca: {marca}, Fabricante: {fabricante}")

            # Criação da linha com dados e informações adicionais
            linha_completa = item_dados + [marca, fabricante]

            rows.append(linha_completa)

    return rows

# Função para criar um DataFrame a partir dos dados coletados
def criar_dataframe(dados):
    if dados:
        df = pd.DataFrame(
            dados,
            columns=[
                'Item',
                'Descrição',
                'Unidade de Fornecimento',
                'Quantidade',
                'Valor Estimado',
                'Valor Homologado',
                'Valor Total do Item',
                'Marca',
                'Fabricante',
                # 'Modelo',
                # 'Descrição Detalhada',
            ],
        )
        return df

# Função para salvar DataFrames em arquivos Excel
def salvar_dataframes(dataframes, diretorio_saida):
    for i, df in enumerate(dataframes):
        arquivo_saida = os.path.join(diretorio_saida, f"data_{i + 1}.xlsx")
        df.to_excel(arquivo_saida, index=False)


# Extração e salvamento dos dados
dados_html = ler_html(html_path)
fornecedores = parse_fornecedores(dados_html)
dataframes = []

for fornecedor in fornecedores:
    itens = parse_itens(fornecedor)
    if itens:
        dataframe = criar_dataframe(itens)
        dataframes.append(dataframe)

diretorio_saida = BASE_DIR / "dataframes_salvos"
os.makedirs(diretorio_saida, exist_ok=True)
salvar_dataframes(dataframes, diretorio_saida)
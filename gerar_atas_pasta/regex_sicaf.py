import re
from pathlib import Path
from typing import Dict, List, Optional
from diretorios import *
from utils.utilidades import convert_pdf_to_txt, ler_arquivos_txt, obter_arquivos_txt

# Constantes
COLETA_DADOS_SICAF = (
    r"Dados do Fornecedor CNPJ: (?P<cnpj>.*?) (DUNS®: .*?)?Razão Social: "
    r"(?P<empresa>.*?) Nome Fantasia:"
    r"(?P<nome_fantasia>.*?) Situação do Fornecedor: "
    r"(?P<situacao_cadastro>.*?) Data de Vencimento do Cadastro: "
    r"(?P<data_vencimento>\d{2}/\d{2}/\d{4}) Dados do Nível"
    r".*?Dados para Contato CEP: (?P<cep>.*?) Endereço: "
    r"(?P<endereco>.*?)Município / UF: "
    r"(?P<municipio_uf>.*?) Telefone:"
    r"(?P<tel>.*?)(?: E-mail: )"
    r"(?P<email>.*?)(?: Dados do Responsável Legal CPF:| Emitido em:|CPF:)"
)

def extrair_dados_sicaf(texto: str) -> Optional[Dict[str, str]]:
    match = re.search(COLETA_DADOS_SICAF, texto, re.S)
    if not match:
        return None
    
    return {
        'cnpj': match.group('cnpj').strip(),
        'empresa': match.group('empresa').strip(),
        'situação_fornecedor': match.group('situacao_cadastro').strip(),
        'data_vencimento_cadastro': match.group('data_vencimento').strip(),
        'cep': match.group('cep').strip(),
        'endereco': match.group('endereco').strip().title(),
        'municipio': match.group('municipio_uf').strip().title(),
        'telefone': match.group('tel').strip(),
        'email': match.group('email').strip().lower()
    }

COLETA_DADOS_RESPONSAVEL = (
    r"Dados do Responsável Legal CPF: (?P<cpf>\d{3}\.\d{3}\.\d{3}-\d{2}) Nome:"    
    r"(?P<nome>.*?)(?: Dados do Responsável pelo Cadastro| Emitido em:|CPF:)"
)

def extrair_dados_responsavel(texto: str) -> Optional[Dict[str, str]]:
    match = re.search(COLETA_DADOS_RESPONSAVEL, texto, re.S)
    if not match:
        return None

    return {
        'cpf': match.group('cpf').strip(),
        'responsavel_legal': match.group('nome').strip()
    }


def processar_arquivo(arquivo: Path) -> Dict[str, str]:
    texto = arquivo.read_text(encoding='utf-8')
    
    item = extrair_dados_sicaf(texto)
    if not item:
        return {'Erro': "Dados do SICAF não encontrados."}
    
    dados_responsavel = extrair_dados_responsavel(texto)
    if dados_responsavel:
        item.update(dados_responsavel)
    else:
        item['Erro'] = "Dados do Responsável Legal não encontrados."
    
    return item

import pandas as pd

def replace_invalid_chars(filename: str, invalid_chars: list, replacement: str = '_') -> str:
    """Substitui caracteres inválidos em um nome de arquivo."""
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, replacement)
    return filename

def clean_company_names_in_csv(csv_path: str, invalid_chars: list, replacement: str = '_') -> None:
    """Limpa os nomes das empresas na coluna 'empresa' de um arquivo CSV."""
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    # Carregar o CSV em um DataFrame
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    
    # Verificar se a coluna 'empresa' existe
    if 'empresa' in df.columns:
        # Aplicar a função de limpeza na coluna 'empresa'
        df['empresa'] = df['empresa'].apply(lambda x: replace_invalid_chars(str(x), invalid_chars, replacement))
        
        # Salvar as alterações de volta ao CSV
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')

def processar_arquivos_sicaf(frame, progress_bar, progress_var) -> None:
    import pandas as pd
    from pathlib import Path
    
    convert_pdf_to_txt(SICAF_DIR, SICAF_TXT_DIR, progress_bar, progress_var)
    arquivos_txt = obter_arquivos_txt(str(SICAF_TXT_DIR))

    # Passo 2: Processar cada arquivo e extrair dados
    dados_extraidos = []
    for arquivo_txt in arquivos_txt:
        texto = ler_arquivos_txt(arquivo_txt)
        dados_arquivo = processar_arquivo(Path(arquivo_txt))
        dados_extraidos.append(dados_arquivo)

    # Criar DataFrame
    df = pd.DataFrame(dados_extraidos)
    
    # Carregar o outro arquivo CSV em um DataFrame
    CSV_DIR = DATABASE_DIR / "dados.csv"
    df_dados = pd.read_csv(CSV_DIR, encoding='utf-8-sig')
    
    # Se a coluna "empresa" existir em ambos os dataframes, exclua-a de df
    if "empresa" in df.columns and "empresa" in df_dados.columns:
        df = df.drop(columns=["empresa"])

    columns_order = [
        "uasg", "orgao_responsavel", "ordenador_despesa", "num_pregao", "ano_pregao", 
        "srp", "objeto", "grupo", "item_num", "catalogo", "descricao_tr", 
        "descricao_detalhada_tr", "valor_estimado", "quantidade", "unidade", 
        "situacao", "melhor_lance", "valor_negociado", "marca_fabricante", 
        "modelo_versao", "valor_homologado_item_unitario", "valor_estimado_total_do_item", 
        "valor_homologado_total_item", "percentual_desconto", "cnpj", "empresa", 
        "situação_fornecedor", "data_vencimento_cadastro", "cep", "endereco", 
        "municipio", "telefone", "email", "cpf", "responsavel_legal"
    ]

    # Garanta que a coluna 'cnpj' exista em ambos os DataFrames
    if 'cnpj' not in df.columns:
        df['cnpj'] = pd.NA  # Adiciona a coluna com valores NaN
    if 'cnpj' not in df_dados.columns:
        df_dados['cnpj'] = pd.NA  # Adiciona a coluna com valores NaN

    # Tente fazer o merge
    try:
        df_final = pd.merge(df, df_dados, on='cnpj', how='outer')
    except KeyError as e:
        print(f"Erro ao fazer merge: {e}")
        return pd.DataFrame()  # Retorna um DataFrame vazio ou lida com o erro de outra forma

    # Verificar se todas as colunas em columns_order existem em df_final
    missing_columns = [col for col in columns_order if col not in df_final.columns]
    if missing_columns:
        print(f"Colunas ausentes: {missing_columns}")
        # Adicionar as colunas faltantes com valores NaN ou tomar outra ação
        for col in missing_columns:
            df_final[col] = pd.NA

    df_final_ordered = df_final[columns_order]

    # Agora, faça o merge
    df_final = pd.merge(df, df_dados, on='cnpj', how='outer')

    # Columns to be converted to int
    columns_to_int = ['uasg', 'num_pregao', 'ano_pregao', 'item_num', 'catalogo', 'quantidade']
    placeholder_value = -1  # Placeholder value for NaNs
    
    for col in columns_to_int:
        df_final[col] = df_final[col].fillna(placeholder_value).astype(int)

    # Special handling for 'grupo' column
    df_final['grupo'] = df_final['grupo'].fillna("N/A").astype(str)
    
    # Ordenar o DataFrame pela coluna 'item_num' em ordem crescente
    df_final_ordered = df_final_ordered.sort_values(by='item_num', ascending=True)
    
    # Limpar os nomes da coluna "empresa"
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    df_final_ordered['empresa'] = df_final_ordered['empresa'].apply(lambda x: replace_invalid_chars(x, invalid_chars) if isinstance(x, str) else x)

    # Verificar e substituir caracteres inválidos antes de salvar
    df_final_ordered.to_csv(CSV_SICAF_PATH, index=False, encoding='utf-8-sig')
    df_final_ordered.to_excel(XLSX_SICAF_PATH, index=False)

    return df_final_ordered
import re
from pathlib import Path
from typing import Dict, List, Optional
from diretorios import *
from database.utils.utilidades import convert_pdf_to_txt, ler_arquivos_txt, obter_arquivos_txt
import pandas as pd

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

import pandas as pd
from pathlib import Path

def processar_arquivos_sicaf(frame, progress_bar, progress_var, loaded_dataframe) -> pd.DataFrame:
    try:
        convert_pdf_to_txt(SICAF_DIR, SICAF_TXT_DIR, progress_bar, progress_var)
        arquivos_txt = obter_arquivos_txt(str(SICAF_TXT_DIR))

        dados_extraidos = []
        for arquivo_txt in arquivos_txt:
            texto = ler_arquivos_txt(arquivo_txt)
            dados_arquivo = processar_arquivo(Path(arquivo_txt))
            dados_extraidos.append(dados_arquivo)

        df = pd.DataFrame(dados_extraidos)
        if 'empresa' not in df.columns:
            df['empresa'] = None

        if loaded_dataframe is not None and not loaded_dataframe.empty:
            df_final = pd.merge(df, loaded_dataframe, on='cnpj', how='right')
            
            # Preservar todos os dados de loaded_dataframe
            df_final['match'] = df_final['empresa_x'] == df_final['empresa_y']
            
            print("DataFrame após merge e antes de limpeza:")
            print(df_final)

            # Limpeza e ajuste final das colunas
            for col in ['empresa', 'cep', 'endereco', 'municipio', 'telefone', 'email', 'responsavel_legal']:
                df_final[col] = df_final[col + '_y'].fillna(df_final[col + '_x'])
                df_final.drop(columns=[col + '_x', col + '_y'], inplace=True)

            df_final = df_final.sort_values(by='item_num', ascending=True)
            print("DataFrame final após ajustes e limpeza:")
            print(df_final)

        else:
            df_final = df  # Use o DataFrame original se não houver dados para combinar
            print("Não há loaded_dataframe disponível, usando df original.")

    except Exception as e:
        print(f"Erro durante o processamento: {e}")
        df_final = pd.DataFrame()  # Retorne um DataFrame vazio em caso de erro

    return df_final


import pandas as pd
from pathlib import Path

def preencher_campos_por_om(df):
    # Dicionário de mapeamento para os valores de cada om
    om_mapping = {
        'Com7ºDN': {'uasg': 787000, 'indicativo_om': 'SETDIS', 'om_extenso': 'COMANDO DO 7º DISTRITO NAVAL'},
        'CeIMBra': {'uasg': 787010, 'indicativo_om': 'CITBRA', 'om_extenso': 'CENTRO DE INTENDÊNCIA DA MARINHA EM BRASÍLIA'},
        'CFAT': {'uasg': 787310, 'indicativo_om': 'CFATOC', 'om_extenso': 'CAPITANIA FLUVIAL DE ARAGUAIA-TOCANTINS'},
        'CFB': {'uasg': 787320, 'indicativo_om': 'CFBRA', 'om_extenso': 'CAPITANIA FLUVIAL DE BRASÍLIA'},
        'GptFNB': {'uasg': 787200, 'indicativo_om': 'GRFBRA', 'om_extenso': 'GRUPAMENTO DE FUZILEIROS NAVAIS DE BRASÍLIA'},
        'CIAB': {'uasg': 787900, 'indicativo_om': 'CIABDF', 'om_extenso': 'CENTRO DE INSTRUÇÃO E ADESTRAMENTO DE BRASÍLIA'},
        'ERMB': {'uasg': 787400, 'indicativo_om': 'ERMBRA', 'om_extenso': 'ESTAÇÃO RÁDIO DA MARINHA EM BRASÍLIA'},
        'CFGO': {'uasg': 787330, 'indicativo_om': 'CFGOO', 'om_extenso': 'CAPITANIA FLUVIAL DE GOIÁS'},
        'HNBRA': {'uasg': 787700, 'indicativo_om': 'HOSBRA', 'om_extenso': 'HOSPITAL NAVAL DE BRASÍLIA'},
    }

    # Preenchendo os campos no DataFrame
    for om, valores in om_mapping.items():
        df.loc[df['om'] == om, 'uasg'] = valores['uasg']
        df.loc[df['om'] == om, 'indicativo_om'] = valores['indicativo_om']
        df.loc[df['om'] == om, 'om_extenso'] = valores['om_extenso']

    return df

# Definir o caminho para o arquivo Excel no mesmo diretório que o script
basepath = Path(__file__).parent
file_path = basepath / 'controle_contratos_atualizado.xlsx'

# Carregar os dados
df_controle_contratos = pd.read_excel(file_path, sheet_name='Sheet1')

# Aplicar a função para preencher os campos
df_atualizado = preencher_campos_por_om(df_controle_contratos)

# Salvar o arquivo atualizado
output_path = basepath / 'controle_contratos_atualizado_preenchido.xlsx'
df_atualizado.to_excel(output_path, index=False)

print(f"Arquivo salvo em: {output_path}")

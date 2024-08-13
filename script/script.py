import os
import pandas as pd

def format_numero_contrato(contrato):
    numero, ano = contrato.split('/')
    ano_formatado = ano[-2:]
    numero_formatado = numero.lstrip('0')  # Remove apenas os zeros à esquerda
    if len(numero_formatado) < 3:
        numero_formatado = numero_formatado.zfill(3)  # Garante que tenha pelo menos 3 dígitos
    formatted_contrato = f'87000/{ano_formatado}-{numero_formatado}/00'
    print(f"Original: {contrato} -> Formatado: {formatted_contrato}")
    return formatted_contrato

# Caminho do diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Caminhos para os arquivos
controle_contratos_path = os.path.join(script_dir, 'controle_contratos.xlsx')
contratos_csv_path = os.path.join(script_dir, 'Contratos.csv')

# Ler os arquivos em dataframes
controle_contratos_df = pd.read_excel(controle_contratos_path)
contratos_df = pd.read_csv(contratos_csv_path)

# Garantir que a coluna 'cnpj' tenha o tipo de dados como string
controle_contratos_df['cnpj'] = controle_contratos_df['cnpj'].astype(str)

# Lista para armazenar linhas sem correspondência
new_rows = []

# Iterar sobre as linhas de controle_contratos
for i, row in controle_contratos_df.iterrows():
    contrato = str(row['comprasnet_contratos'])
    # Verificar correspondência no arquivo contratos.csv
    matching_row = contratos_df[contratos_df['comprasnet_contratos'] == contrato]
    if not matching_row.empty:
        # Obter valor do fornecedor
        fornecedor_info = matching_row['Fornecedor'].values[0]
        # Separar o CNPJ/CPF e o nome da empresa/fornecedor
        parts = fornecedor_info.split(' - ')
        if len(parts) >= 2:
            cnpj = parts[0].strip()
            empresa = ' - '.join(parts[1:]).strip()
            # Atualizar as colunas 'Empresa' e 'cnpj' no controle_contratos_df
            controle_contratos_df.at[i, 'empresa'] = empresa
            controle_contratos_df.at[i, 'cnpj'] = cnpj

        # Limpar as colunas específicas
        controle_contratos_df.at[i, 'vigencia_inicial'] = ''
        controle_contratos_df.at[i, 'vigencia_final'] = ''
        controle_contratos_df.at[i, 'atualizacao_comprasnet'] = ''
        controle_contratos_df.at[i, 'valor_global'] = ''

        # Obter valores das colunas correspondentes no contratos_df
        vigencia_inicial = matching_row['Vig. Início'].values[0]
        vigencia_final = matching_row['Vig. Fim'].values[0]
        atualizacao_comprasnet = matching_row['Atualizado em'].values[0]
        valor_global = matching_row['Valor Global'].values[0]

        # Atualizar as colunas no controle_contratos_df com os novos valores
        controle_contratos_df.at[i, 'vigencia_inicial'] = vigencia_inicial
        controle_contratos_df.at[i, 'vigencia_final'] = vigencia_final
        controle_contratos_df.at[i, 'atualizacao_comprasnet'] = atualizacao_comprasnet
        controle_contratos_df.at[i, 'valor_global'] = valor_global

        # Atualizar a coluna numero_contrato
        controle_contratos_df.at[i, 'numero_contrato'] = format_numero_contrato(contrato)

# Iterar sobre as linhas de contratos_df para adicionar os contratos que não possuem correspondência em controle_contratos_df
for i, row in contratos_df.iterrows():
    contrato = str(row['comprasnet_contratos'])
    # Verificar se o contrato já está no controle_contratos_df
    if contrato not in controle_contratos_df['comprasnet_contratos'].values:
        fornecedor_info = row['Fornecedor']
        parts = fornecedor_info.split(' - ')
        if len(parts) >= 2:
            cnpj = parts[0].strip()
            empresa = ' - '.join(parts[1:]).strip()

            new_row = {
                'comprasnet_contratos': contrato,
                'empresa': empresa,
                'cnpj': cnpj,
                'vigencia_inicial': row['Vig. Início'],
                'vigencia_final': row['Vig. Fim'],
                'atualizacao_comprasnet': row['Atualizado em'],
                'valor_global': row['Valor Global']
            }

            # Preencher colunas adicionais com valores nulos
            for col in controle_contratos_df.columns:
                if col not in new_row:
                    new_row[col] = None

            # Adicionar o valor de numero_contrato formatado
            new_row['numero_contrato'] = format_numero_contrato(contrato)

            new_rows.append(new_row)

# Converter as novas linhas para DataFrame
new_rows_df = pd.DataFrame(new_rows)

# Concatenar as novas linhas ao DataFrame existente
controle_contratos_df = pd.concat([controle_contratos_df, new_rows_df], ignore_index=True)

# Caminho para salvar o arquivo atualizado
output_path = os.path.join(script_dir, 'controle_contratos_atualizado.xlsx')

# Salvar o dataframe atualizado de volta para um arquivo Excel
controle_contratos_df.to_excel(output_path, index=False)

print(f"Arquivo salvo em: {output_path}")

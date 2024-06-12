import os
import locale
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
import re
import html
from html import unescape
# Configurando o locale para português do Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        print("Locale não pode ser configurado para pt_BR ou Portuguese_Brazil.")

from num2words import num2words

def safe_company_name(company_name):
    return re.sub(r'[<>:"/\\|?*]', '_', company_name.replace(" ", "_").replace("&", "E").replace(",", "").replace(".", "").replace("/", "-"))

def parse_float(value):
    """
    Função para converter strings numéricas que usam ponto como separador de milhares
    e vírgula como separador decimal para float.
    """
    value = value.replace('.', '').replace(',', '.')
    return float(value)

def format_brl(value):
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

class DataExtractor:
    def __init__(self, base_dir, output_dir, start_sequence=25):
        self.base_dir = Path(base_dir)
        self.output_dir = Path(output_dir)
        self.current_sequence = start_sequence
        os.makedirs(self.output_dir, exist_ok=True)
    
    def read_html(self, file_path):
        with open(file_path, 'r', encoding='iso-8859-1') as file:
            return file.read()

    def parse_html(self, html_content):
        # print("Chamando parse_html...")  # Print de depuração
        soup = BeautifulSoup(html_content, 'html.parser')
        items = soup.find_all('tr', class_='tex3b')
        data = []
        for item in items:
            if item.find('td') and 'Item:' in item.find('td').text.strip():
                item_text = item.find('td').text.strip()
                # print(f"Item encontrado: {item_text}")  # Print de depuração
                item_numero, grupo_numero = self.extrair_item_grupo(item_text)
                
                item_details_table = item.find_next_sibling('tr').find('table')
                if not item_details_table:
                    continue

                full_description_text = ' '.join([td.text for td in item_details_table.find_all('td')])
                descricao, descricao_complementar = self.extrair_descricao(full_description_text)
                
                quantidade, unidade, valor_estimado, situacao, empresa, melhor_lance, valor_negociado, quantidade_homologada = '', '', '', '', '', '', '', ''
                
                detail_rows = item_details_table.find_all('tr', bgcolor="#FFFFFF")
                for row in detail_rows:
                    columns = row.find_all('td')
                    for col in columns:
                        text = col.text.strip()
                        if 'Quantidade:' in text:
                            quantidade = text.split(':', 1)[-1].strip()
                        elif 'Unidade de fornecimento:' in text:
                            unidade = text.split(':', 1)[-1].strip()
                        elif 'Valor Estimado:' in text:
                            valor_estimado = text.split(':', 1)[-1].strip().split(' ')[1]
                        elif 'Situação:' in text:
                            # print("Situação encontrada no HTML: ", text)  # Print de depuração
                            situacao, empresa, melhor_lance, valor_negociado, quantidade_homologada = self.extrair_situacao(col)

                data.append([item_numero, grupo_numero, descricao, descricao_complementar, quantidade, unidade, valor_estimado, situacao])

        return data

    def extrair_item_grupo(self, item_text):
        item_match = re.match(r"Item:\s*(\d+)", item_text)
        grupo_match = re.search(r"Grupo\s*(\d+)", item_text)
        item_numero = int(item_match.group(1)) if item_match else None
        grupo_numero = int(grupo_match.group(1)) if grupo_match else None
        return item_numero, grupo_numero

    def extrair_descricao(self, texto):
        descricao = ""
        descricao_complementar = ""

        # Regex para capturar a descrição até "Descrição Complementar:" se presente
        descricao_match = re.search(r'Descrição:(.*?)(?=Descrição Complementar:|$)', texto, re.DOTALL)
        if descricao_match:
            descricao = descricao_match.group(1).strip()

        # Regex para capturar a descrição complementar a partir de "Descrição Complementar:" até "Tratamento Diferenciado:" ou "Aplicabilidade Decreto 7174:"
        descricao_complementar_match = re.search(r'Descrição Complementar:(.*?)(?=Tratamento Diferenciado:|Aplicabilidade Decreto 7174:|$)', texto, re.DOTALL)
        if descricao_complementar_match:
            descricao_complementar = descricao_complementar_match.group(1).strip()

        return descricao, descricao_complementar

    def extrair_detalhes_adjudicacao(self, td):
        empresa = ""
        melhor_lance = ""
        valor_negociado = ""
        quantidade_homologada = ""

        # Padrao para extrair a informacao da empresa, melhor lance, valor negociado e quantidade homologada
        pattern = r"Adjudicado para:</b>\s*(.*?)<b>, pelo melhor lance de</b>\s*R\$ ([\d,.]+)"
        pattern_valor_negociado = r"<b>, com valor negociado a</b>\s*R\$ ([\d,.]+)"
        pattern_quantidade = r"<b>e a quantidade de </b>\s*([\d,.]+)"

        match = re.search(pattern, str(td), re.DOTALL)
        if match:
            empresa = html.unescape(match.group(1).strip())
            melhor_lance = match.group(2).strip().replace('.', '')

        match_valor_negociado = re.search(pattern_valor_negociado, str(td), re.DOTALL)
        if match_valor_negociado:
            valor_negociado = match_valor_negociado.group(1).strip().replace('.', '')

        match_quantidade = re.search(pattern_quantidade, str(td), re.DOTALL)
        if match_quantidade:
            quantidade_homologada = match_quantidade.group(1).strip().replace('.', '')

        return empresa, melhor_lance, valor_negociado, quantidade_homologada


    def extrair_situacao(self, col):
        print("Chamando extrair_situacao...")  # Print de depuração
        situacao = ""
        empresa = ""
        melhor_lance = ""
        valor_negociado = ""
        quantidade_homologada = ""

        # Extrai o texto depois de 'Situação:'
        situacao_match = re.search(r'Situação:\s*(.*)', col.text)
        if situacao_match:
            situacao = situacao_match.group(1).strip()
            # print(f"Situação encontrada: {situacao}")  # Print de depuração
            if "Homologado" in situacao:
                # Buscar detalhes de adjudicação no texto do elemento pai
                detalhes_text = col.find_parent('td').text
                empresa, melhor_lance, valor_negociado, quantidade_homologada = self.extrair_detalhes_adjudicacao(detalhes_text)
                # print(f"Detalhes adjudicação - Empresa: {empresa}, Melhor Lance: {melhor_lance}, Valor Negociado: {valor_negociado}, Quantidade Homologada: {quantidade_homologada}")  # Print de depuração

        return situacao, empresa, melhor_lance, valor_negociado, quantidade_homologada


    def encontrar_cnpj(self, soup, empresa):
        print(f"Buscando CNPJ para a empresa: {empresa}")  # Print de depuração
        cnpj = None
        rows = soup.find_all('tr', class_='tex3a', bgcolor="#FFFFFF")
        pattern = r"Fornecedor:\s*{}\s*,\s*CNPJ/CPF:\s*([\d./-]+)".format(re.escape(empresa))

        for row in rows:
            td = row.find_all('td')[-1]
            if td:
                text = html.unescape(td.text)
                match = re.search(pattern, text)
                if match:
                    cnpj = match.group(1)
                    # print(f"CNPJ encontrado: {cnpj} para empresa: {empresa}")  # Print de depuração
                    break

        if not cnpj:
            print(f"Nenhum CNPJ encontrado para a empresa: {empresa}")  # Print de depuração
        return cnpj



    def encontrar_adjudicacoes(self, soup):
        adjudicacoes = []
        adjudicacao_rows = soup.find_all('tr', bgcolor="#FFFFFF")
        for row in adjudicacao_rows:
            td = row.find('td', colspan="2")
            if td and td.find('b', string="Adjudicado para:"):
                item_tr = row.find_previous('tr', class_='tex3b')
                item_numero, grupo_numero = None, None
                if item_tr:
                    item_text = item_tr.text.strip()
                    item_numero, grupo_numero = self.extrair_item_grupo(item_text)
                empresa, melhor_lance, valor_negociado, quantidade_homologada = self.extrair_detalhes_adjudicacao(td)
                adjudicacoes.append([item_numero, grupo_numero, empresa, melhor_lance, valor_negociado, quantidade_homologada])
                # print(f"Adjudicação encontrada: Item {item_numero}, Grupo {grupo_numero}, Empresa: {empresa}, Melhor Lance: {melhor_lance}, Valor Negociado: {valor_negociado}, Quantidade Homologada: {quantidade_homologada}")  # Print de depuração

        return adjudicacoes

    def process_files(self):
        print("Iniciando process_files...")  # Print de depuração
        all_data = []
        all_adjudicacoes = []
        for html_file in self.base_dir.glob('*.html'):
            html_content = self.read_html(html_file)
            soup = BeautifulSoup(html_content, 'html.parser')
            extracted_data = self.parse_html(html_content)
            adjudicacoes = self.encontrar_adjudicacoes(soup)
            all_data.extend(extracted_data)
            all_adjudicacoes.extend(adjudicacoes)

        df = pd.DataFrame(all_data, columns=['Item', 'Grupo', 'Descrição', 'Descrição Detalhada', 'Quantidade', 'Unidade de Fornecimento', 'Valor Estimado', 'Situação'])
        df_adjudicacoes = pd.DataFrame(all_adjudicacoes, columns=['Item', 'Grupo', 'Empresa', 'Melhor Lance', 'Valor Negociado', 'Quantidade Homologada'])
        
        # Remover linhas onde Item é NaN
        df_adjudicacoes = df_adjudicacoes.dropna(subset=['Item'])
        
        # Convertendo 'Item' e 'Grupo' para int para correta ordenação
        df['Item'] = pd.to_numeric(df['Item'], downcast='integer')
        df['Grupo'] = pd.to_numeric(df['Grupo'], downcast='integer', errors='coerce')
        df_adjudicacoes['Item'] = pd.to_numeric(df_adjudicacoes['Item'], downcast='integer')
        df_adjudicacoes['Grupo'] = pd.to_numeric(df_adjudicacoes['Grupo'], downcast='integer')

        # Convertendo 'Grupo' para texto e ajustando valores
        df['Grupo'] = df['Grupo'].fillna('-').astype(str).replace(r'\.0$', '', regex=True)
        df_adjudicacoes['Grupo'] = df_adjudicacoes['Grupo'].fillna('-').astype(str).replace(r'\.0$', '', regex=True)

        # Ordenando por 'Grupo' e 'Item', mantendo '-' no final
        df['Grupo'] = df['Grupo'].astype('category')
        df = df.sort_values(by=['Grupo', 'Item'], ascending=[True, True])
        df_adjudicacoes['Grupo'] = df_adjudicacoes['Grupo'].astype('category')
        df_adjudicacoes = df_adjudicacoes.sort_values(by=['Grupo', 'Item'], ascending=[True, True])

        # Buscar e adicionar CNPJ às adjudicações
        df_adjudicacoes['CNPJ'] = df_adjudicacoes['Empresa'].apply(lambda x: self.encontrar_cnpj(soup, x))

        # Unir os dataframes
        df_final = pd.merge(df, df_adjudicacoes, on=['Item', 'Grupo'], how='left', suffixes=('', '_adj'))

        # Salvando os resultados finais
        df_final.to_csv(self.output_dir / 'dados_agregados_final.csv', index=False)
        df_adjudicacoes.to_csv(self.output_dir / 'adjudicacoes_final.csv', index=False)

        # Criar arquivos txt para cada combinação única de Empresa e CNPJ
        self.criar_arquivos_txt(df_final, self.output_dir / "relacao_empresas")

        print("Processamento concluído.")  # Print de depuração

    def criar_arquivos_txt(self, df_final, txt_dir):
        unique_combinations = df_final[['Empresa', 'CNPJ']].dropna().drop_duplicates()
        
        # Garantir que o diretório de saída existe
        txt_dir = Path(txt_dir)
        txt_dir.mkdir(parents=True, exist_ok=True)
        
        for _, row in unique_combinations.iterrows():
            empresa = row['Empresa']
            cnpj = row['CNPJ']
            
            # Sanitizar o nome da empresa para o nome do arquivo
            sanitized_company_name = safe_company_name(empresa)
            sanitized_cnpj = cnpj.replace('/', '-').replace('.', '')
            filename = txt_dir / f"{sanitized_company_name}_{sanitized_cnpj}.txt"
            
            # Número da Ata
            numero_ata = f"787000/2024-{self.current_sequence:03d}/00"
            self.current_sequence += 1
            # Dados Empresa
            dados_empresa = f"""
Razão Social: {empresa},
CNPJ: {cnpj},
Endereço:
Município-UF:
CEP:
Telefone:
E-mail:
Representada neste ato, por seu representante legal, o(a) Sr(a)
"""
            
            # Dados Itens
            dados_itens = df_final[(df_final['Empresa'] == empresa) & (df_final['CNPJ'] == cnpj)]
            dados_itens_text = ""
            total_homologado = 0
            for _, item in dados_itens.iterrows():
                grupo_numero = item['Grupo']
                item_numero = item['Item']
                descricao = item['Descrição']
                descricao_complementar = item['Descrição Detalhada']
                unidade = item.get('Unidade de Fornecimento', '')
                quantidade_homologada = parse_float(str(item['Quantidade']))
                melhor_lance = parse_float(str(item['Melhor Lance']))
                valor_negociado = item.get('Valor Negociado', None)
                if valor_negociado:
                    valor_negociado = parse_float(str(valor_negociado))
                valor_homologado = valor_negociado if valor_negociado else melhor_lance
                valor_homologado_total_item = quantidade_homologada * valor_homologado
                total_homologado += valor_homologado_total_item

                if pd.notna(grupo_numero) and str(grupo_numero).isdigit():
                    dados_itens_text += f"Grupo: {int(grupo_numero)} - Item {item_numero} - {descricao}\n"
                else:
                    dados_itens_text += f"Item {item_numero} - {descricao}\n"
                
                dados_itens_text += f"Descrição Detalhada: {descricao_complementar}\n"
                dados_itens_text += f"Unidade de Fornecimento: {unidade}\n"
                dados_itens_text += "Marca:   | Modelo:    | Fabricante:   "
                dados_itens_text += f"Quantidade: {int(quantidade_homologada)}   |   Valor Unitário: {format_brl(valor_homologado)}   |   Valor Total do Item: {format_brl(valor_homologado_total_item)}\n"
                dados_itens_text += "-" * 130 + "\n"

            total_homologado_brl = format_brl(total_homologado)
            total_homologado_extenso = num2words(total_homologado, lang='pt_BR', to='currency')
            
            # Conteúdo final do arquivo
            conteudo = f"Número da Ata:\n{numero_ata}\n\nDados Empresa:\n{dados_empresa}\nDados Itens:\n{dados_itens_text}"
            conteudo += f"\nValor total homologado para a empresa:\n{total_homologado_brl} ({total_homologado_extenso})"


            # Escrever no arquivo
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(conteudo)
                
                # Confirmar criação do arquivo
                if filename.exists():
                    print(f"Arquivo {filename} criado com sucesso.")  # Print de confirmação
                else:
                    print(f"Erro ao criar o arquivo {filename}.")  # Print de erro
            except Exception as e:
                print(f"Erro ao criar o arquivo {filename}: {e}")




# Uso da classe
BASE_DIR = Path(__file__).resolve().parent
html_dir = BASE_DIR / "pasta_htm"
output_dir = BASE_DIR / "dataframe_salvo"
txt_dir = output_dir = BASE_DIR / "relacao_empresas"
extractor = DataExtractor(html_dir, output_dir)
extractor.process_files()


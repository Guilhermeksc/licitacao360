import os
import locale
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
import re
# Configurando o locale para português do Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        print("Locale não pode ser configurado para pt_BR ou Portuguese_Brazil.")
    
class DataExtractor:
    def __init__(self, base_dir, output_dir):
        self.base_dir = Path(base_dir)
        self.output_dir = Path(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def read_html(self, file_path):
        with open(file_path, 'r', encoding='iso-8859-1') as file:
            return file.read()

    def parse_html(self, html_content):
        print("Chamando parse_html...")  # Print de depuração
        soup = BeautifulSoup(html_content, 'html.parser')
        items = soup.find_all('tr', class_='tex3b')
        data = []
        for item in items:
            if item.find('td') and 'Item:' in item.find('td').text.strip():
                item_text = item.find('td').text.strip()
                print(f"Item encontrado: {item_text}")  # Print de depuração
                item_numero, grupo_numero = self.extrair_item_grupo(item_text)
                
                item_details_table = item.find_next_sibling('tr').find('table')
                if not item_details_table:
                    continue

                full_description_text = ' '.join([td.text for td in item_details_table.find_all('td')])
                descricao, descricao_complementar = self.extrair_descricao(full_description_text)
                
                quantidade, unidade, valor_estimado, situacao, empresa, melhor_lance, valor_negociado = '', '', '', '', '', '', ''
                
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
                            print("Situação encontrada no HTML: ", text)  # Print de depuração
                            situacao, empresa, melhor_lance, valor_negociado = self.extrair_situacao(col)

                data.append([item_numero, grupo_numero, descricao, descricao_complementar, quantidade, unidade, valor_estimado, situacao, empresa, melhor_lance, valor_negociado])

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
    
    @staticmethod
    def extrair_detalhes_adjudicacao(text):
        empresa = ""
        melhor_lance = ""
        valor_negociado = ""

        # Padrao para extrair a informacao da empresa, melhor lance e valor negociado
        pattern = r"Adjudicado para:</b>\s*(.*?)<b>, pelo melhor lance de</b>\s*(.*?)<b>(, com valor negociado a</b>\s*(.*?)<b>)?(, e a quantidade de \b)?"

        match = re.search(pattern, text, re.DOTALL)
        if match:
            empresa = match.group(1).strip()
            melhor_lance = match.group(2).strip()
            if match.group(4):  # Se houver valor negociado
                valor_negociado = match.group(4).strip()

        return empresa, melhor_lance, valor_negociado

    def extrair_situacao(self, col):
        print("Chamando extrair_situacao...")  # Print de depuração
        situacao = ""
        empresa = ""
        melhor_lance = ""
        valor_negociado = ""

        # Extrai o texto depois de 'Situação:'
        situacao_match = re.search(r'Situação:\s*(.*)', col.text)
        if situacao_match:
            situacao = situacao_match.group(1).strip()
            print(f"Situação encontrada: {situacao}")  # Print de depuração
            if "Homologado" in situacao:
                # Buscar detalhes de adjudicação no texto do elemento pai
                detalhes_text = col.find_parent('td').text
                empresa, melhor_lance, valor_negociado = DataExtractor.extrair_detalhes_adjudicacao(detalhes_text)
                print(f"Detalhes adjudicação - Empresa: {empresa}, Melhor Lance: {melhor_lance}, Valor Negociado: {valor_negociado}")  # Print de depuração

        return situacao, empresa, melhor_lance, valor_negociado

    def process_files(self):
        print("Iniciando process_files...")  # Print de depuração
        all_data = []
        for html_file in self.base_dir.glob('*.html'):
            print(f"Lendo arquivo: {html_file}")  # Print de depuração
            html_content = self.read_html(html_file)
            extracted_data = self.parse_html(html_content)
            all_data.extend(extracted_data)

        df = pd.DataFrame(all_data, columns=['Item', 'Grupo', 'Descrição', 'Descrição Detalhada', 'Quantidade', 'Unidade de Fornecimento', 'Valor Estimado', 'Situação', 'Empresa', 'Melhor Lance', 'Valor Negociado'])
        
        # Convertendo 'Item' e 'Grupo' para int para correta ordenação
        df['Item'] = pd.to_numeric(df['Item'], downcast='integer')
        df['Grupo'] = pd.to_numeric(df['Grupo'], downcast='integer', errors='coerce')  # 'errors='coerce' para transformar valores não-numéricos em NaN
        # Convertendo 'Grupo' para texto e ajustando valores
        df['Grupo'] = df['Grupo'].fillna('-').astype(str).replace(r'\.0$', '', regex=True)

        # Ordenando por 'Grupo' e 'Item', mantendo '-' no final
        df['Grupo'] = df['Grupo'].astype('category')
        df = df.sort_values(by=['Grupo', 'Item'], ascending=[True, True])

        df.to_csv(self.output_dir / 'dados_agregados.csv', index=False)

# Uso da classe
BASE_DIR = Path(__file__).resolve().parent
html_dir = BASE_DIR / "pasta_htm"
output_dir = BASE_DIR / "dataframe_salvo"
extractor = DataExtractor(html_dir, output_dir)
extractor.process_files()

    # def extract_details(self, span):
    #     previous_text = (span.previous_sibling.strip() if span.previous_sibling and isinstance(span.previous_sibling, str) else '')
    #     current_text = span.text.strip()
    #     return previous_text, current_text

    # def parse_html(self, html_content):
    #     soup = BeautifulSoup(html_content, 'html.parser')
    #     return soup.find_all('td', {'align': 'left', 'colspan': '7'})

    # def parse_html(self, html_content):
    #     soup = BeautifulSoup(html_content, 'html.parser')
    #     return soup.find_all('td', {'align': 'left', 'colspan': '7'})

    # def extract_rows(self, item_table):
    #     rows = []
    #     for row in item_table.find_next_siblings('tr'):
    #         if row.find('td', {'align': 'left', 'colspan': '7'}):
    #             break
    #         cells = row.find_all('td')
    #         if len(cells) == 7:
    #             item_details = [cell.text.strip() for cell in cells]
    #             desc_row = row.find_next_sibling('tr')
    #             marca = fabricante = modelo = descricao_detalhada = ''
    #             if desc_row:
    #                 spans_tex5a = desc_row.find_all('span', class_='tex5a')
    #                 if len(spans_tex5a) >= 4:
    #                     marca = spans_tex5a[0].text.strip()
    #                     fabricante = spans_tex5a[1].text.strip()
    #                     modelo = spans_tex5a[2].text.strip()
    #                     descricao_detalhada = spans_tex5a[3].text.strip()
    #             item_details.extend([marca, fabricante, modelo, descricao_detalhada])
    #             rows.append(item_details)
    #     return rows

    # def save_data(self, soup):
    #     for fornecedor in soup:
    #         nome_fornecedor = self.clean_invalid_chars(fornecedor.text.strip()[:18])
    #         item_table = fornecedor.find_next('tr')
    #         rows = self.extract_rows(item_table)
    #         total_valor_item = 0
    #         with open(Path(self.output_dir, f"{nome_fornecedor}.txt"), 'w', encoding='utf-8') as file:
    #             for row in rows:
    #                 valor_total_item = self.convert_currency(row[6])
    #                 total_valor_item += valor_total_item
    #                 valor_estimado_item = self.convert_currency(row[4]) * self.safe_int_convert(row[3])
    #                 self.total_valor_estimado += valor_estimado_item
    #                 self.total_valor_homologado += valor_total_item

    #                 file.write(f"Item: {row[0]}, Descrição: {row[1]}, Unidade de Fornecimento: {row[2]}, Quantidade: {row[3]}\n")
    #                 file.write(f"Descrição detalhada: {row[10]}\n")
    #                 file.write(f"Valor Estimado: {locale.format_string('%.2f', valor_estimado_item, grouping=True)}, Valor Homologado: {locale.format_string('%.2f', valor_total_item, grouping=True)}, Valor Total do Item: {locale.format_string('%.2f', valor_total_item, grouping=True)}\n")
    #                 file.write(f"Marca: {row[7]}, Fabricante: {row[8]}, Modelo / Versão: {row[9]}\n\n")
    #             file.write(f"Valor Total da Ata: R$ {locale.format_string('%.2f', total_valor_item, grouping=True)}\n")

    #     with open(Path(self.output_dir, "resumo_desconto_licitacao.txt"), 'w', encoding='utf-8') as file:
    #         file.write(f"Valor Estimado Total: R$ {locale.format_string('%.2f', self.total_valor_estimado, grouping=True)}\n")
    #         file.write(f"Valor Total Homologado: R$ {locale.format_string('%.2f', self.total_valor_homologado, grouping=True)}\n")
    #         percentual_desconto = ((self.total_valor_estimado - self.total_valor_homologado) / self.total_valor_estimado) * 100
    #         file.write(f"Percentual de Desconto da Licitação: {locale.format_string('%.2f', percentual_desconto)}%\n")




    # def process_data(self, soup):
    #     for fornecedor in soup:
    #         nome_fornecedor = self.clean_invalid_chars(fornecedor.text.strip()[:18])
    #         item_table = fornecedor.find_next('tr')
    #         rows = self.extract_rows(item_table)
    #         if rows:
    #             df = pd.DataFrame(rows, columns=['Item', 'Descrição', 'Unidade de Fornecimento', 'Quantidade', 'Valor Estimado', 'Valor Homologado', 'Valor Total do Item', 'Marca', 'Fabricante', 'Modelo / Versão', 'Descrição Detalhada do Objeto Ofertado'])
    #             self.dfs.append(df)

    # def display_dataframes(self):
    #     for df in self.dfs:
    #         print(df)
    #         print("\n---\n")

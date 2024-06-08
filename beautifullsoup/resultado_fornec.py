import os
import locale
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup

# Configurando o locale para português do Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        print("Locale não pode ser configurado para pt_BR ou Portuguese_Brazil.")
    
class DataExtractor:
    def __init__(self, html_path, output_dir):
        self.html_path = html_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)  # Cria a pasta se não existir
        self.total_valor_estimado = 0
        self.total_valor_homologado = 0
        self.dfs = []

    def read_html(self):
        with open(self.html_path, 'r', encoding='iso-8859-1') as file:
            return file.read()

    @staticmethod
    def clean_invalid_chars(name):
        return name.translate(str.maketrans(':\\/?*[]', '-------'))

    @staticmethod
    def convert_currency(value):
        try:
            return float(value.replace('R$', '').replace('.', '').replace(',', '.'))
        except ValueError:
            return 0.0

    @staticmethod
    def safe_int_convert(value):
        try:
            return int(value)
        except ValueError:
            return 0
            return 0.0

    def parse_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.find_all('td', {'align': 'left', 'colspan': '7'})

    def extract_details(self, span):
        previous_text = (span.previous_sibling.strip() if span.previous_sibling and isinstance(span.previous_sibling, str) else '')
        current_text = span.text.strip()
        return previous_text, current_text

    def parse_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.find_all('td', {'align': 'left', 'colspan': '7'})

    def parse_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.find_all('td', {'align': 'left', 'colspan': '7'})

    def extract_rows(self, item_table):
        rows = []
        for row in item_table.find_next_siblings('tr'):
            if row.find('td', {'align': 'left', 'colspan': '7'}):
                break
            cells = row.find_all('td')
            if len(cells) == 7:
                item_details = [cell.text.strip() for cell in cells]
                desc_row = row.find_next_sibling('tr')
                marca = fabricante = modelo = descricao_detalhada = ''
                if desc_row:
                    spans_tex5a = desc_row.find_all('span', class_='tex5a')
                    if len(spans_tex5a) >= 4:
                        marca = spans_tex5a[0].text.strip()
                        fabricante = spans_tex5a[1].text.strip()
                        modelo = spans_tex5a[2].text.strip()
                        descricao_detalhada = spans_tex5a[3].text.strip()
                item_details.extend([marca, fabricante, modelo, descricao_detalhada])
                rows.append(item_details)
        return rows

    def save_data(self, soup):
        for fornecedor in soup:
            nome_fornecedor = self.clean_invalid_chars(fornecedor.text.strip()[:18])
            item_table = fornecedor.find_next('tr')
            rows = self.extract_rows(item_table)
            total_valor_item = 0
            with open(Path(self.output_dir, f"{nome_fornecedor}.txt"), 'w', encoding='utf-8') as file:
                for row in rows:
                    valor_total_item = self.convert_currency(row[6])
                    total_valor_item += valor_total_item
                    valor_estimado_item = self.convert_currency(row[4]) * self.safe_int_convert(row[3])
                    self.total_valor_estimado += valor_estimado_item
                    self.total_valor_homologado += valor_total_item

                    file.write(f"Item: {row[0]}, Descrição: {row[1]}, Unidade de Fornecimento: {row[2]}, Quantidade: {row[3]}\n")
                    file.write(f"Descrição detalhada: {row[10]}\n")
                    file.write(f"Valor Estimado: {locale.format_string('%.2f', valor_estimado_item, grouping=True)}, Valor Homologado: {locale.format_string('%.2f', valor_total_item, grouping=True)}, Valor Total do Item: {locale.format_string('%.2f', valor_total_item, grouping=True)}\n")
                    file.write(f"Marca: {row[7]}, Fabricante: {row[8]}, Modelo / Versão: {row[9]}\n\n")
                file.write(f"Valor Total da Ata: R$ {locale.format_string('%.2f', total_valor_item, grouping=True)}\n")

        with open(Path(self.output_dir, "resumo_desconto_licitacao.txt"), 'w', encoding='utf-8') as file:
            file.write(f"Valor Estimado Total: R$ {locale.format_string('%.2f', self.total_valor_estimado, grouping=True)}\n")
            file.write(f"Valor Total Homologado: R$ {locale.format_string('%.2f', self.total_valor_homologado, grouping=True)}\n")
            percentual_desconto = ((self.total_valor_estimado - self.total_valor_homologado) / self.total_valor_estimado) * 100
            file.write(f"Percentual de Desconto da Licitação: {locale.format_string('%.2f', percentual_desconto)}%\n")




    def process_data(self, soup):
        for fornecedor in soup:
            nome_fornecedor = self.clean_invalid_chars(fornecedor.text.strip()[:18])
            item_table = fornecedor.find_next('tr')
            rows = self.extract_rows(item_table)
            if rows:
                df = pd.DataFrame(rows, columns=['Item', 'Descrição', 'Unidade de Fornecimento', 'Quantidade', 'Valor Estimado', 'Valor Homologado', 'Valor Total do Item', 'Marca', 'Fabricante', 'Modelo / Versão', 'Descrição Detalhada do Objeto Ofertado'])
                self.dfs.append(df)

    def display_dataframes(self):
        for df in self.dfs:
            print(df)
            print("\n---\n")

# Uso da classe
BASE_DIR = Path(__file__).resolve().parent
html_path = BASE_DIR / "FornecedorResultadoDecreto.htm"
output_dir = BASE_DIR / "dataframe_salvo"
extractor = DataExtractor(html_path, output_dir)
html_content = extractor.read_html()
fornecedor_blocks = extractor.parse_html(html_content)
extractor.save_data(fornecedor_blocks)
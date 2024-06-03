from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from pathlib import Path
from modulo_ata_contratos.regex_termo_homolog import *
from modulo_ata_contratos.regex_sicaf import *
from modulo_ata_contratos.canvas_gerar_atas import *
from diretorios import *
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import contextily as ctx
import traceback
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm 
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE
import seaborn as sns
from planejamento.utilidades_planejamento import DatabaseManager
import logging
import os
import sys
import time
from win32com.client import Dispatch

ATA_CONTRATO_DIR = BASE_DIR / "modulo_ata_contratos"
INDICADORES_NORMCEIM = ATA_CONTRATO_DIR / "indicadores_normceim"
TEMPLATE_INDICADORES_PATH = INDICADORES_NORMCEIM / "template_indicadores.docx"
SHAPEFILE_MUNICIPIOS = DATABASE_DIR / "BR_Municipios_2022.shp"

from docx.oxml.shared import OxmlElement, qn
from docx.oxml.ns import nsdecls
from docx.shared import Pt
from docx.enum.text import WD_UNDERLINE

def add_hyperlink(paragraph, url, text, font_name='Carlito', font_size=12):
    """
    Insere um hiperlink em um parágrafo existente com estilos específicos.
    """
    part = paragraph.part
    r_id = part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    # Define a fonte
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rFonts.set(qn('w:cs'), font_name)
    rPr.append(rFonts)

    # Define o tamanho da fonte
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), str(font_size * 2))  # Tamanho da fonte em meia-pontos
    rPr.append(sz)

    # Define sublinhado
    u = OxmlElement('w:u')
    u.set(qn('w:val'), 'single')
    rPr.append(u)

    new_run.append(rPr)

    new_text = OxmlElement('w:t')
    new_text.text = text
    new_run.append(new_text)

    hyperlink.append(new_run)

    paragraph._p.append(hyperlink)


class RelatorioIndicadores(QDialog):
    def __init__(self, dataframe, parent=None, pe_pattern=None):
        super().__init__(parent)
        self.current_dataframe = dataframe
        self.db_manager = DatabaseManager(CONTROLE_DADOS)  # Ajuste para usar a conexão do banco
        self.pe_pattern = pe_pattern  # Adicionando o padrão PE como um atributo da classe
        self.setWindowTitle("Relatório de Indicadores")
        self.setup_ui()

    @staticmethod
    def convert_pe_format(pe_string):
        pe_formatted = pe_string.replace('PE-', 'PE ').replace('-', '/')
        print(f"Converted PE format: {pe_formatted}")  # Depuração
        return pe_formatted

    def formatar_brl(self, valor):
        if valor is None or pd.isna(valor) or valor == 0:
            return ""  # Retornar string vazia se não for um valor válido
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def fetch_pregao_data(self, pe_formatted):
        try:
            with DatabaseManager(CONTROLE_DADOS) as conn:
                query = f"SELECT ano, numero, objeto, nup, setor_responsavel, uasg, sigla_om, coordenador_planejamento, pregoeiro, parecer_agu, num_irp, msg_irp, link_portal_marinha, om_participantes FROM controle_processos WHERE id_processo LIKE '%{pe_formatted}%'"
                print(f"Executing query: {query}")  # Depuração
                df = pd.read_sql(query, conn)
                print(f"Query results: {df}")  # Depuração
                if not df.empty:
                    return df.iloc[0]
                else:
                    print("No data found matching the query.")  # Depuração adicional
                    return None
        except Exception as e:
            logging.error(f"Error querying database: {str(e)}")
            return None

    def title_case_custom(self, text):
        # Lista de palavras que devem permanecer em minúsculas, exceto quando são a primeira palavra da frase
        lowercase_words = ['e', 'de', 'do', 'da', 'dos', 'das', 'para', 'em', 'com', 'sem', 'por', 'sob', 'sobre', 'entre']
        
        # Dividir o texto em palavras
        words = text.split()
        # Aplicar capitalização corretamente
        final_words = [word.capitalize() if word.lower() not in lowercase_words else word.lower() for word in words]
        
        # Certificar que a primeira palavra seja capitalizada, independentemente de ser uma preposição/conjunção
        if final_words:
            final_words[0] = final_words[0].capitalize()
        
        # Juntar as palavras de volta em uma string
        return ' '.join(final_words)
            
    def verificar_pdm_e_classe(self):
        # Preencher valores nulos com 'PDM não definido' e 'Classe não definida' antes da agregação
        self.current_dataframe['Padrão Desc Material'] = self.current_dataframe['Padrão Desc Material'].fillna('PDM não definido')
        self.current_dataframe['Classe Material'] = self.current_dataframe['Classe Material'].fillna('Classe não definida')
        self.current_dataframe['Unnamed: 6'] = self.current_dataframe['Unnamed: 6'].fillna('Descrição PDM não disponível')
        self.current_dataframe['Unnamed: 4'] = self.current_dataframe['Unnamed: 4'].fillna('Descrição Classe não disponível')

        # Agrega os dados somando os valores estimados e homologados
        agregado_pdm = self.current_dataframe.groupby('Padrão Desc Material').agg({
            'valor_estimado_total_do_item': 'sum',
            'valor_homologado_total_item': 'sum',
            'Unnamed: 6': 'first'
        }).reset_index()

        agregado_classe = self.current_dataframe.groupby('Classe Material').agg({
            'valor_estimado_total_do_item': 'sum',
            'valor_homologado_total_item': 'sum',
            'Unnamed: 4': 'first'
        }).reset_index()

        # Converter para lista para uso no template
        lista_pdm = agregado_pdm.apply(lambda row: f"PDM {row['Padrão Desc Material']} - {self.title_case_custom(row['Unnamed: 6'])} | Valor Homologado: {self.formatar_brl(row['valor_homologado_total_item'])}" if row['valor_homologado_total_item'] > 0 else "", axis=1).tolist()
        lista_classe = agregado_classe.apply(lambda row: f"Classe {row['Classe Material']} - {self.title_case_custom(row['Unnamed: 4'])} | Valor Homologado: {self.formatar_brl(row['valor_homologado_total_item'])}" if row['valor_homologado_total_item'] > 0 else "", axis=1).tolist()

        # Remover entradas vazias
        lista_pdm = [item for item in lista_pdm if item]
        lista_classe = [item for item in lista_classe if item]

        total_estimado_pdm = self.current_dataframe['valor_estimado_total_do_item'].sum()
        if total_estimado_pdm > 0:
            lista_pdm.append(f"Total estimado dos itens homologados: {self.formatar_brl(total_estimado_pdm)}")

        # Adicionar somatório de valores homologados no final da lista de PDM
        total_homologado_pdm = self.current_dataframe['valor_homologado_total_item'].sum()
        if total_homologado_pdm > 0:
            lista_pdm.append(f"Total Homologado: {self.formatar_brl(total_homologado_pdm)}")

        return lista_pdm, lista_classe
    
    def adicionar_dados(self):
        with DatabaseManager(ARQUIVO_DADOS_PDM_CATSER) as conn_pdm:
            query = """
            SELECT `Codigo Material Serviço`, `Unnamed: 4`, `Padrão Desc Material`, `Unnamed: 6`, `Classe Material`
            FROM dados_pdm
            """
            pdm_data = pd.read_sql(query, conn_pdm)
        
        # Criar um dicionário a partir de pdm_data para mapeamento rápido
        pdm_dict = pdm_data.set_index('Codigo Material Serviço').to_dict('index')
        
        # Adiciona as novas colunas ao DataFrame
        self.current_dataframe['Padrão Desc Material'] = self.current_dataframe['catalogo'].map(
            lambda x: pdm_dict.get(x, {}).get('Padrão Desc Material', ''))
        self.current_dataframe['Unnamed: 6'] = self.current_dataframe['catalogo'].map(
            lambda x: pdm_dict.get(x, {}).get('Unnamed: 6', ''))
        self.current_dataframe['Classe Material'] = self.current_dataframe['catalogo'].map(
            lambda x: pdm_dict.get(x, {}).get('Classe Material', ''))
        self.current_dataframe['Unnamed: 4'] = self.current_dataframe['catalogo'].map(
            lambda x: pdm_dict.get(x, {}).get('Unnamed: 4', ''))

    def setup_ui(self):
        layout = QVBoxLayout()
        self.grafico_local_btn = QPushButton("Gráfico por Localidade Geográfica")
        self.grafico_desconto_btn = QPushButton("Gráfico por Percentual de Desconto")
        self.report_button = QPushButton("Gerar Relatório de Indicadores")
        
        self.grafico_local_btn.clicked.connect(self.grafico_localidade_geografica)
        self.grafico_desconto_btn.clicked.connect(self.grafico_percentual_desconto)
        self.report_button.clicked.connect(self.report_button_clicked)

        layout.addWidget(self.grafico_local_btn)
        layout.addWidget(self.grafico_desconto_btn)
        layout.addWidget(self.report_button)
        self.setLayout(layout)

    def report_button_clicked(self):
        self.gerar_relatorio_docx()

        original_doc_path = str(INDICADORES_NORMCEIM / "Relatorio_Indicadores_Final.docx")
        doc = Document(original_doc_path)
        
        pe_formatted = self.convert_pe_format(self.pe_pattern)

        pregao_data = self.fetch_pregao_data(pe_formatted)
        
        if pregao_data is not None and 'link_portal_marinha' in pregao_data:
            for paragraph in doc.paragraphs:
                if "<link portal marinha>" in paragraph.text:
                    paragraph.clear()
                    add_hyperlink(paragraph, pregao_data['link_portal_marinha'], "Link do processo íntegra no 'Portal de Licitações da Marinha'")
                    
            new_doc_path = str(INDICADORES_NORMCEIM / f"relatorio_{pe_formatted.replace('/', '_').replace(' ', '_')}.docx")
            doc.save(new_doc_path)

            QMessageBox.information(self, "Relatório Atualizado", f"O relatório com hiperlink foi gerado com sucesso em: {new_doc_path}")
            self.gerarPdf(new_doc_path)
        else:
            QMessageBox.warning(self, "Aviso", "Dados do pregão não encontrados ou incompletos para o padrão PE especificado.")

    def calcular_percentual_desconto_total(self):
        if self.current_dataframe is not None and 'valor_estimado_total_do_item' in self.current_dataframe.columns:
            df = self.current_dataframe
            df_valid = df.dropna(subset=['valor_estimado_total_do_item', 'valor_homologado_total_item'])
            total_estimado = df_valid['valor_estimado_total_do_item'].sum()
            total_homologado = df_valid['valor_homologado_total_item'].sum()

            if total_estimado > 0:
                percentual_desconto = ((total_estimado - total_homologado) / total_estimado) * 100
            else:
                percentual_desconto = 0
            return percentual_desconto, total_estimado, total_homologado
        return 0, 0, 0

    def gerar_relatorio_docx(self):
        self.adicionar_dados()  # Primeiro adicionar os dados de PDM e classe
        lista_pdm, lista_classe = self.verificar_pdm_e_classe()  # Obter as listas de PDM e classe com somas
        
        # Gerar gráficos
        self.grafico_percentual_desconto()
        grafico_path = str(INDICADORES_NORMCEIM / "grafico_01.png")
        # self.grafico_localidade_geografica()
        # grafico_localidade_geografica_path = str(INDICADORES_NORMCEIM / "grafico_02.png")

        # Formatar os valores totais
        percentual_desconto_total, total_estimado, total_homologado = self.calcular_percentual_desconto_total()
        total_estimado_fmt = self.formatar_brl(total_estimado)
        total_homologado_fmt = self.formatar_brl(total_homologado)

        top10_items = self.current_dataframe.nlargest(10, 'percentual_desconto')[['item_num', 'descricao_tr', 'percentual_desconto']]
       
        doc = DocxTemplate(str(TEMPLATE_INDICADORES_PATH))

        pe_formatted = self.convert_pe_format(self.pe_pattern)  # Garantir que esta chamada está correta
        print(f"Formatted PE pattern: {pe_formatted}")  # Depuração

        # Buscar dados relacionados ao pe_formatted em controle_prazos
        with DatabaseManager(CONTROLE_DADOS) as conn:
            query = f"SELECT sequencial, etapa, dias_na_etapa FROM controle_prazos WHERE chave_processo LIKE '%{pe_formatted}%' ORDER BY sequencial"
            controle_prazos_data = pd.read_sql(query, conn)
            # Filtrar para não incluir etapas de Planejamento
            controle_prazos_data = controle_prazos_data[controle_prazos_data['etapa'] != 'Planejamento']
            controle_dias_processo = "\n".join(f"{row['etapa']} ({row['dias_na_etapa']} dias" for index, row in controle_prazos_data.iterrows())
            # Calcular o somatório dos dias
            somatorio_dias_todas_etapas = controle_prazos_data['dias_na_etapa'].sum()
            controle_dias_processo += f"\nTotal de dias {somatorio_dias_todas_etapas}"

        pregao_data = self.fetch_pregao_data(pe_formatted)
        print(f"Pregao Data: {pregao_data}")  # Depuração

        if pregao_data is not None:
            # Preparar o texto para incluir no template
            relacao_itens_top10_desconto = [f"Item {row['item_num']} - {row['descricao_tr']} - {row['percentual_desconto']:.2f}%" for index, row in top10_items.iterrows()]
            context = {
                'percentual_desconto_total': f"{percentual_desconto_total:.2f}%",
                'total_estimado': total_estimado_fmt,  # Formatação como número com duas casas decimais
                'total_homologado': total_homologado_fmt,
                'grafico_01': InlineImage(doc, grafico_path, width=Mm(150)) if os.path.exists(grafico_path) else 'Gráfico não disponível',
                # 'grafico_02': InlineImage(doc, grafico_localidade_geografica_path, width=Mm(150)) if os.path.exists(grafico_localidade_geografica_path) else 'Gráfico não disponível',
                'controle_dias_processo': controle_dias_processo,  # Adicionar os dados da tabela controle_prazos ao contexto
                'relacao_itens_top10_desconto': '\n'.join(relacao_itens_top10_desconto),
                'lista_pdm': '\n'.join(lista_pdm),
                'lista_classe': '\n'.join(lista_classe),
                'pregoeiro': pregao_data['pregoeiro'],
                'parecer_agu': pregao_data['parecer_agu'],
                'msg_irp': pregao_data['msg_irp'],
                'link_portal_marinha': "link portal marinha",
                'num_irp': pregao_data['num_irp'],
                'om_participantes': pregao_data['om_participantes'],
                'ano': pregao_data['ano'],
                'numero': pregao_data['numero'],
                'objeto': pregao_data['objeto'],
                'nup': pregao_data['nup'],
                'setor_responsavel': pregao_data['setor_responsavel'],
                'uasg': f"{pregao_data['uasg']}-{pregao_data['sigla_om']}",
                'coordenador_planejamento': pregao_data['coordenador_planejamento']
            }
            try:
                doc.render(context)
                doc.save(str(INDICADORES_NORMCEIM / "Relatorio_Indicadores_Final.docx"))
            except Exception as e:
                error_message = f"Erro ao gerar o relatório: {str(e)}"
                print(error_message)
                QMessageBox.critical(self, "Erro ao Gerar Relatório", error_message)
        else:
            QMessageBox.warning(self, "Aviso", "Dados do pregão não encontrados para o padrão PE especificado.")

    def grafico_percentual_desconto(self):
        if self.current_dataframe is None:
            print("O DataFrame atual não está disponível.")
            return

        # Preparar os dados
        df_analysis = self.current_dataframe[['item_num', 'valor_estimado', 'valor_homologado_item_unitario']].dropna()
        df_analysis['valor_estimado'] = pd.to_numeric(df_analysis['valor_estimado'], errors='coerce')
        df_analysis['valor_homologado_item_unitario'] = pd.to_numeric(df_analysis['valor_homologado_item_unitario'], errors='coerce')
        df_analysis.dropna(inplace=True)
        df_analysis['economia'] = df_analysis['valor_estimado'] - df_analysis['valor_homologado_item_unitario']
        df_analysis['percentual_desconto'] = (df_analysis['economia'] / df_analysis['valor_estimado']) * 100
        df_top10_desconto = df_analysis.nlargest(10, 'percentual_desconto').sort_index()

        fig, ax1 = plt.subplots(figsize=(12, 8))
        bar_width = 0.35  # Largura das barras
        index = np.arange(len(df_top10_desconto))  # Array com a posição dos itens

        bars1 = ax1.bar(index - bar_width/2, df_top10_desconto['valor_estimado'], bar_width, label='Valor Estimado', color='navy')
        bars2 = ax1.bar(index + bar_width/2, df_top10_desconto['valor_homologado_item_unitario'], bar_width, label='Valor Homologado', color='darkorange')
        # Adicionando rótulos nas colunas de Valor Estimado
        for bar in bars1.patches:
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'R$ {bar.get_height():,.0f}'.replace(',', '.').replace('.', ','),
                    ha='center', va='bottom', fontsize=14, color='navy', fontweight='bold')

        # Adicionando rótulos nas colunas de Valor Homologado
        for bar in bars2.patches:
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'R$ {bar.get_height():,.0f}'.replace(',', '.').replace('.', ','),
                    ha='center', va='bottom', fontsize=14, color='darkorange', fontweight='bold')

        ax1.set_xlabel('Número do Item')
        ax1.set_ylabel('Valores em Reais')
        ax1.set_title('Top 10 Maiores Percentuais de Desconto, Valores Estimados e Valores Homologados por Item')
        ax1.set_xticks(index)
        ax1.set_xticklabels(df_top10_desconto['item_num'])
        ax1.legend(loc='upper left')

        # Criar o eixo secundário para a linha de percentual de desconto
        ax2 = ax1.twinx()
        ax2.plot(index, df_top10_desconto['percentual_desconto'], 'r-o', label='Percentual de Desconto', linewidth=2, markersize=8, color='red')
        ax2.set_ylabel('Percentual de Desconto (%)')
        ax2.legend(loc='upper right')

        # Adicionar rótulos ao lado de cada ponto de percentual de desconto
        for i, txt in enumerate(df_top10_desconto['percentual_desconto']):
            ax2.annotate(f'{txt:.1f}%', (index[i], df_top10_desconto['percentual_desconto'].iloc[i]), textcoords="offset points", xytext=(0,10), ha='center', color='darkred', fontsize=14, fontweight='bold')

        plt.xticks(rotation=45)
        plt.tight_layout()

        # Salvar o gráfico como uma imagem PNG no caminho adequado
        grafico_path = str(INDICADORES_NORMCEIM / "grafico_01.png")
        plt.savefig(grafico_path)
        plt.close()

    def grafico_localidade_geografica(self):
        grafico_localidade_geografica_path = str(INDICADORES_NORMCEIM / "grafico_02.png")
        if self.current_dataframe is not None:
            try:
                # Normalizar os nomes dos municípios
                self.current_dataframe['municipio_normalizado'] = self.current_dataframe['municipio'].apply(
                    lambda x: x.split('/')[0].strip() if x else ''
                )

                # Contar o número de fornecedores por município normalizado
                fornecedor_por_municipio = self.current_dataframe.groupby('municipio_normalizado').size().reset_index(name='contagem')
                fornecedor_por_municipio.rename(columns={'municipio_normalizado': 'NM_MUN'}, inplace=True)

                # Carregar o shapefile do Brasil e projetar
                brasil = gpd.read_file(str(SHAPEFILE_MUNICIPIOS)).to_crs(epsg=3857)

                # Filtrar os municípios de interesse
                municípios_para_plotar = brasil.loc[brasil['NM_MUN'].isin(fornecedor_por_municipio['NM_MUN'])].copy()
                municípios_para_plotar.loc[:, 'centroid'] = municípios_para_plotar.geometry.centroid

                # Merge com contagens
                municípios_para_plotar = municípios_para_plotar.merge(fornecedor_por_municipio, how='left', on='NM_MUN')
                municípios_para_plotar.loc[:, 'contagem'] = municípios_para_plotar['contagem'].fillna(0)

                # Plotar o mapa
                fig, ax = plt.subplots(1, 1, figsize=(10, 8))
                municípios_para_plotar.plot(ax=ax, color='red', markersize=50, marker='o')
                ctx.add_basemap(ax, crs=municípios_para_plotar.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)
                bounds = municípios_para_plotar.total_bounds
                dx = (bounds[2] - bounds[0]) * 0.1  # 10% padding
                dy = (bounds[3] - bounds[1]) * 0.1  # 10% padding
                ax.set_xlim([bounds[0] - dx, bounds[2] + dx])
                ax.set_ylim([bounds[1] - dy, bounds[3] + dy])
                ax.set_axis_off()
                plt.title('Distribuição Geográfica dos Fornecedores')

                # Salvar o gráfico como imagem PNG
                plt.savefig(grafico_localidade_geografica_path)
                plt.close()

            except Exception as e:
                error_msg = str(e) + "\n\n" + traceback.format_exc()
                print("Falha ao gerar o gráfico:\n" + error_msg)
                QMessageBox.warning(self, "Aviso", "Falha ao gerar gráfico de localidade geográfica.")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum DataFrame carregado para gerar indicadores.")

    def gerarPdf(self, docx_path):
        if docx_path is None or not os.path.isfile(docx_path):
            QMessageBox.warning(self, "Erro", "O arquivo DOCX não existe ou não pode ser acessado.")
            return

        try:
            absolute_docx_path = os.path.abspath(docx_path).replace('/', '\\')
            print(f"Caminho absoluto do DOCX: {absolute_docx_path}")

            word = Dispatch("Word.Application")
            word.Visible = False

            doc = word.Documents.Open(absolute_docx_path)

            pdf_path = absolute_docx_path.replace('.docx', '.pdf')
            doc.SaveAs(pdf_path, FileFormat=17)
            doc.Close(False)
            word.Quit()

            print(f"Arquivo PDF gerado com sucesso: {pdf_path}")
            self.abrirDocumento(pdf_path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Gerar PDF", f"Ocorreu um erro ao gerar o PDF: {str(e)}")
            if word:
                word.Quit()

    def abrirDocumento(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(path)  # Abrir o documento
                os.startfile(os.path.dirname(path))  # Abrir a pasta no Windows Explorer
            else:
                subprocess.run(["xdg-open", path])  # Abrir o documento no Linux ou MacOS
                subprocess.run(["xdg-open", os.path.dirname(path)])  # Abrir a pasta no gerenciador de arquivos do sistema
        except Exception as e:
            QMessageBox.critical(self, "Erro ao abrir documento", f"Não foi possível abrir o documento: {str(e)}")

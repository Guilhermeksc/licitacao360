from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from modules.gerar_atas.regex_termo_homolog import *
from modules.gerar_atas.regex_sicaf import *
from modules.gerar_atas.canvas_gerar_atas import *
from diretorios import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm 
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE
from modules.planejamento.utilidades_planejamento import DatabaseManager
import logging
import os
import sys
import time
from win32com.client import Dispatch

ATA_CONTRATO_DIR = MODULES_DIR / "atas"
INDICADORES_NORMCEIM = ATA_CONTRATO_DIR / "indicadores_normceim"
TEMPLATE_INDICADORES_PATH = INDICADORES_NORMCEIM / "template_indicadores.docx"

from docx.oxml.shared import OxmlElement, qn

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

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Adicionando o título "Relatório de Indicadores" com fonte tamanho 16
        title_label = QLabel("Relatório de Indicadores")
        title_label.setFont(QFont("Arial", 16))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centraliza o texto horizontalmente
        layout.addWidget(title_label)

        # Aqui você pode adicionar outros widgets ao layout

        self.setLayout(layout)

    @staticmethod
    def convert_pe_format(pe_string):
        pe_formatted = pe_string.replace('PE-', 'PE ').replace('-', '/')
        print(f"Converted PE format: {pe_formatted}")  # Depuração
        return pe_formatted

    def formatar_brl(self, valor):
        try:
            if valor is None or pd.isna(valor):
                return "R$ 0,00"  # Retorna string formatada se não for um valor válido
            valor_formatado = f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return valor_formatado
        except Exception as e:
            print(f"Erro ao formatar valor: {valor} - Erro: {str(e)}")
            return "R$ 0,00"
        
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
            
    def setup_ui(self):
        layout = QVBoxLayout()
        self.report_button = QPushButton(" Relatório de Indicadores")
        
        self.report_button.clicked.connect(self.report_button_clicked)

        layout.addWidget(self.report_button)
        self.setLayout(layout)

    def report_button_clicked(self):
        try:
            # Gera o relatório inicial
            self.gerar_relatorio_docx()

            # Carrega o documento original
            original_doc_path = str(INDICADORES_NORMCEIM / "Relatorio_Indicadores_Final.docx")
            doc = Document(original_doc_path)
            
            # Formata o padrão PE
            pe_formatted = self.convert_pe_format(self.pe_pattern)

            # Busca os dados do pregão
            pregao_data = self.fetch_pregao_data(pe_formatted)
            
            if pregao_data is not None and 'link_portal_marinha' in pregao_data:
                link_portal_marinha = pregao_data.get('link_portal_marinha')
                
                if link_portal_marinha:  # Verifica se o link não é None ou vazio
                    for paragraph in doc.paragraphs:
                        if "<link portal marinha>" in paragraph.text:
                            paragraph.clear()  # Limpa o conteúdo existente
                            add_hyperlink(paragraph, link_portal_marinha, "Link do processo íntegra no 'Portal de Licitações da Marinha'")
                
                # Salva o novo documento com o nome formatado
                new_doc_path = str(INDICADORES_NORMCEIM / f"relatorio_{pe_formatted.replace('/', '_').replace(' ', '_')}.docx")
                doc.save(new_doc_path)

                # Exibe uma mensagem de sucesso
                QMessageBox.information(self, "Relatório Atualizado", f"O relatório com hiperlink foi gerado com sucesso em: {new_doc_path}")
                
                # Gera o PDF a partir do novo documento
                self.gerarPdf(new_doc_path)
            else:
                QMessageBox.warning(self, "Aviso", "Dados do pregão não encontrados ou incompletos para o padrão PE especificado.")

        except Exception as e:
            # Tratamento de erro geral para capturar exceções e exibir uma mensagem de erro
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro durante a geração do relatório: {e}")
            print(f"Erro ao gerar relatório: {e}")


    def calcular_percentual_desconto_total(self):
        if self.current_dataframe is not None and 'valor_estimado_total_do_item' in self.current_dataframe.columns:
            df = self.current_dataframe
            df_valid = df.dropna(subset=['valor_estimado_total_do_item', 'valor_homologado_total_item'])
            total_estimado = df_valid['valor_estimado_total_do_item'].sum()
            total_homologado = df_valid['valor_homologado_total_item'].sum()

            if total_estimado > 0:
                percentual_desconto = (1 - (total_homologado / total_estimado))* 100
            else:
                percentual_desconto = 0
            return percentual_desconto, total_estimado, total_homologado
        return 0, 0, 0

    def preparar_relacao_empresas_contratadas(self):
        grupos = self.current_dataframe.groupby(['numero_ata', 'cnpj', 'empresa'])
        relacao_empresas = []
        dados_empresas = []

        for (numero_ata, cnpj, empresa), grupo in grupos:
            itens = grupo[['item_num', 'catalogo', 'descricao_tr', 'valor_homologado_item_unitario', 'quantidade', 'valor_homologado_total_item']].to_dict('records')
            valor_total_homologado = sum(item.get('valor_homologado_total_item', 0) for item in itens)
            valor_total_formatado = self.formatar_brl(valor_total_homologado)

            # Preparar os dados para cada empresa
            dados_empresas.append({
                'numero_ata': numero_ata,
                'cnpj': cnpj,
                'empresa': empresa,
                'valor_total_homologado': valor_total_homologado,
                'valor_total_formatado': valor_total_formatado,
                'itens': itens
            })

        # Agora, processar os dados para a saída final após todos os cálculos
        for dados in dados_empresas:
            itens_formatados = [
                f"Item {item['item_num']} - {item['descricao_tr']}\nValor Homologado: {self.formatar_brl(item['valor_homologado_item_unitario'])}, Quantidade:  {int(item['quantidade']) if item['quantidade'].is_integer() else item['quantidade']}, Valor Total do Item: {self.formatar_brl(item['valor_homologado_total_item'])}"
                for item in dados['itens']
            ]
            empresa_info = (
                f"{dados['numero_ata']} - {dados['empresa']} (CNPJ: {dados['cnpj']})\n" +
                "\n".join(itens_formatados) +
                f"\nValor total contratado = {dados['valor_total_formatado']}" +
                "\nLink para o PNCP"
            )
            relacao_empresas.append(empresa_info)

        return "\n\n".join(relacao_empresas)

    def gerar_relatorio_docx(self):
        # Gerar gráficos
        self.grafico_percentual_desconto()
        grafico_path = str(INDICADORES_NORMCEIM / "grafico_01.png")
        
        # Gerar o gráfico de dispersão
        self.grafico_dispersao()
        grafico_dispersao_path = str(INDICADORES_NORMCEIM / "grafico_dispersao.png")

        # self.grafico_barras_empilhadas()
        # grafico_barra_path = str(INDICADORES_NORMCEIM / "grafico_barras_empilhadas.png")

        # Formatar os valores totais
        percentual_desconto_total, total_estimado, total_homologado = self.calcular_percentual_desconto_total()
        total_estimado_fmt = self.formatar_brl(total_estimado)
        total_homologado_fmt = self.formatar_brl(total_homologado)

        top10_items = self.current_dataframe.nlargest(10, 'percentual_desconto')[['item_num', 'descricao_tr', 'percentual_desconto']]

        relacao_empresas_contratadas = self.preparar_relacao_empresas_contratadas()

        doc = DocxTemplate(str(TEMPLATE_INDICADORES_PATH))

        pe_formatted = self.convert_pe_format(self.pe_pattern)  # Garantir que esta chamada está correta
        print(f"Formatted PE pattern: {pe_formatted}")  # Depuração

        # Buscar dados relacionados ao pe_formatted em controle_prazos
        with DatabaseManager(CONTROLE_DADOS) as conn:
            query = f"SELECT sequencial, etapa, dias_na_etapa FROM controle_prazos WHERE chave_processo LIKE '%{pe_formatted}%' ORDER BY sequencial"
            controle_prazos_data = pd.read_sql(query, conn)
            controle_prazos_data = controle_prazos_data[controle_prazos_data['etapa'] != 'Planejamento']
            controle_dias_processo = "\n".join(f"{row['etapa']} ({row['dias_na_etapa']} dias)" for index, row in controle_prazos_data.iterrows())
            somatorio_dias_todas_etapas = controle_prazos_data['dias_na_etapa'].sum()
            controle_dias_processo += f"\nTotal de dias {somatorio_dias_todas_etapas}"

        pregao_data = self.fetch_pregao_data(pe_formatted)
        print(f"Pregao Data: {pregao_data}")  # Depuração

        if pregao_data is not None:
            # Preparar o texto para incluir no template
            relacao_itens_top10_desconto = [f"Item {row['item_num']} - {row['descricao_tr']} - {row['percentual_desconto']:.2f}%" for index, row in top10_items.iterrows()]
            context = {
                'percentual_desconto_total': f"{percentual_desconto_total:.2f}%",
                'total_estimado': total_estimado_fmt,
                'total_homologado': total_homologado_fmt,
                'grafico_01': InlineImage(doc, grafico_path, width=Mm(150)) if os.path.exists(grafico_path) else 'Gráfico não disponível',
                'grafico_dispersao': InlineImage(doc, grafico_dispersao_path, width=Mm(150)) if os.path.exists(grafico_dispersao_path) else 'Gráfico não disponível',
                # 'grafico_barras_empilhadas': InlineImage(doc, grafico_barra_path, width=Mm(150)) if os.path.exists(grafico_barra_path) else 'Gráfico não disponível',
                'controle_dias_processo': controle_dias_processo,
                'relacao_itens_top10_desconto': '\n'.join(relacao_itens_top10_desconto),
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
                'coordenador_planejamento': pregao_data['coordenador_planejamento'],
                'relacao_empresas_contratadas': relacao_empresas_contratadas
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

        self.grafico_dispersao()
        self.grafico_barras_empilhadas()

    def grafico_barras_empilhadas(self):
        if self.current_dataframe is None:
            print("O DataFrame atual não está disponível.")
            return

        # Preparar os dados
        df_analysis = self.current_dataframe[['item_num', 'valor_estimado', 'valor_homologado_item_unitario']].dropna()
        df_analysis['valor_estimado'] = pd.to_numeric(df_analysis['valor_estimado'], errors='coerce')
        df_analysis['valor_homologado_item_unitario'] = pd.to_numeric(df_analysis['valor_homologado_item_unitario'], errors='coerce')
        df_analysis['desconto'] = df_analysis['valor_estimado'] - df_analysis['valor_homologado_item_unitario']
        df_analysis['percentual_desconto'] = (df_analysis['desconto'] / df_analysis['valor_estimado']) * 100

        df_analysis = df_analysis.sort_values(by='percentual_desconto', ascending=False)

        # Plotar o gráfico de barras empilhadas
        plt.figure(figsize=(12, 8))
        plt.barh(df_analysis['item_num'], df_analysis['valor_homologado_item_unitario'], color='darkorange', label='Valor Homologado')
        plt.barh(df_analysis['item_num'], df_analysis['desconto'], left=df_analysis['valor_homologado_item_unitario'], color='navy', label='Desconto')

        plt.xlabel('Valor em Reais')
        plt.ylabel('Número do Item')
        plt.title('Desconto por Item: Valor Homologado vs Desconto')
        plt.legend()

        # Adicionar rótulos
        for index, row in df_analysis.iterrows():
            plt.text(row['valor_estimado'], index, f"{row['percentual_desconto']:.2f}%", va='center', ha='right', color='white', fontweight='bold')

        plt.tight_layout()
        grafico_empilhado_path = str(INDICADORES_NORMCEIM / "grafico_barras_empilhadas.png")
        plt.savefig(grafico_empilhado_path)
        plt.close()

        # Chamar essa função em gerar_relatorio_docx para incluir no relatório
        return grafico_empilhado_path

    def grafico_dispersao(self):
        if self.current_dataframe is None:
            print("O DataFrame atual não está disponível.")
            return

        # Preparar os dados
        df_analysis = self.current_dataframe[['item_num', 'percentual_desconto']].dropna()

        # Converter item_num para inteiros se não houver valores fracionados
        df_analysis['item_num'] = df_analysis['item_num'].astype(int)

        plt.figure(figsize=(10, 6))
        plt.scatter(df_analysis['item_num'], df_analysis['percentual_desconto'], color='blue', label='Percentual de Desconto')

        # Adicionar linha tracejada verde representando 30% de desconto
        plt.axhline(y=30, color='green', linestyle='--', label='30% de Desconto')

        # Marcar os 10 valores mais altos
        df_top10_desconto = df_analysis.nlargest(10, 'percentual_desconto')
        for i, row in df_top10_desconto.iterrows():
            plt.annotate(f"Item: {row['item_num']}", (row['item_num'], row['percentual_desconto']),
                        textcoords="offset points", xytext=(5, 5), ha='center', color='red', fontsize=10, fontweight='bold')

        plt.xlabel('Número do Item')
        plt.ylabel('Percentual de Desconto (%)')
        plt.title('Distribuição Percentual de Desconto por Item')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.legend()

        # Salvar o gráfico de dispersão
        grafico_dispersao_path = str(INDICADORES_NORMCEIM / "grafico_dispersao.png")
        plt.savefig(grafico_dispersao_path)
        plt.close()


    def gerarPdf(self, docx_path):
        if docx_path is None or not os.path.isfile(docx_path):
            QMessageBox.warning(self, "Erro", "O arquivo DOCX não existe ou não pode ser acessado.")
            return

        word = None
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
            print(f"Erro detalhado: {str(e)}")
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

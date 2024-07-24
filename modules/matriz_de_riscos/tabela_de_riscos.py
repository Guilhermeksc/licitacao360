from docx import Document
from openpyxl import load_workbook
from docx.shared import Pt, Inches
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from docx.enum.section import WD_ORIENT, WD_SECTION
import os

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_MATRIZ_RISCOS = BASE_DIR / "template_matriz_riscos.docx"
TEMPLATE_MATRIZ_PARTE2 = BASE_DIR / "template_matriz_parte2.docx"

# Dados extraídos do arquivo PDF
dados = [
    {"Risco": "R1", "Causa": "Definição de requisitos da contratação insuficientes ou indevidos.",
     "Evento": "Baixa participação/adesão ao registro de preços.", "Consequência": "Risco de imagem para a Central; não atingimento dos objetivos de centralização dos procedimentos de licitação e de padronização da estratégia da contratação, resultando em perdas de economia de escala, visto a baixa participação dos órgãos e entidades da APF.", "P": 1, "I": 5},
    {"Risco": "R2", "Causa": "Definição de requisitos da contratação insuficientes ou indevidos.",
     "Evento": "Contratação de solução que não atende à necessidade que originou a contratação.", "Consequência": "Mau uso de recursos públicos; ineficácia da prestação dos serviços e problemas de gerenciamento e fiscalização dos contratos advindos da licitação.", "P": 1, "I": 5},
    {"Risco": "R3", "Causa": "Estimativa da quantidade maior ou menor que a necessidade.",
     "Evento": "Exaurimento do quantitativo da ata antecipado, nos casos de subdimensionamento da necessidade ou de finalização da ata com grande saldo, nos casos de superdimensionamento.", "Consequência": "Realização de novo procedimento de registro de preços antes do prazo programado para os casos de subdimensionamento dos quantitativos; Frustração do mercado e preços não condizentes com a expectativa criada nos fornecedores, nos casos de superdimensionamento.", "P": 3, "I": 4},
    {"Risco": "R4", "Causa": "Não parcelar a solução cujo parcelamento é viável.",
     "Evento": "Restrição à competitividade, principalmente das empresas de pequeno porte. Questionamentos dos órgãos de controle sobre o não parcelamento.", "Consequência": "Aumento dos valores contratados; impugnações ao certame; paralisações do certame advindas das diligências de órgãos de controles externos.", "P": 2, "I": 5},
    {"Risco": "R5", "Causa": "Imposição de indicativo de economicidade mínima de 10%.",
     "Evento": "Falta de assertividade quanto à potencialidade de economia e viabilidade de cumprimento do indicativo. Dificuldade na análise da economia gerada após implantação da solução.", "Consequência": "Não atendimento das expectativas de economia de recursos públicos.", "P": 5, "I": 5},
    {"Risco": "R6", "Causa": "Coleta insuficiente de preços ou falha de método para realizar a estimativa.",
     "Evento": "Estimativas de custos inadequadas.", "Consequência": "Utilização de parâmetro inadequado para análise da viabilidade da contratação; possibilidade de contratação por preços superfaturados ou ocorrência de deserção e dificuldade de justificar as estimativas.", "P": 1, "I": 5},
    {"Risco": "R7", "Causa": "Falta de abrangência da análise de viabilidade da contratação.",
     "Evento": "Não consideração de todos os aspectos necessários à análise de viabilidade da contratação.", "Consequência": "Certame fracassado ou contratação de fornecedor que não é capaz de entregar a solução ou solução que não produz os resultados necessários ao atendimento da demanda.", "P": 1, "I": 5},
    {"Risco": "R8", "Causa": "Declaração imprecisa do objeto.",
     "Evento": "Compreensão imprecisa da descrição, quantidade ou prazo.", "Consequência": "Contratação que não atenda à necessidade da organização.", "P": 1, "I": 5},
    {"Risco": "R9", "Causa": "Declaração imprecisa do objeto.",
     "Evento": "Inconformidade legal do edital.", "Consequência": "Impugnações ao edital; declaração de nulidade dos procedimentos; responsabilização de agente(s) de contratação e/ou gestores.", "P": 1, "I": 5},
    {"Risco": "R10", "Causa": "Definição de mecanismos que propiciem a ingerência da contratante na administração da contratada.",
     "Evento": "Caracterização de execução indireta ilegal.", "Consequência": "Prática de ilícito trabalhista ante os entendimentos contidos na Súmula nº 331/TST.", "P": 1, "I": 3},
    {"Risco": "R11", "Causa": "Subjetividade na definição dos resultados que serão mensurados para fins de remuneração da contratada.",
     "Evento": "Pagamentos sem que tenham sido realmente entregues resultados que atendem às necessidades da organização e/ou Pagamentos aquém do resultado atingir pelo fornecedor.", "Consequência": "Desperdício de recursos públicos e não atendimento das necessidades da organização ou prejuízo financeiro à contratada.", "P": 1, "I": 4},
    {"Risco": "R12", "Causa": "Empresas sem qualificação econômico-financeira e técnica-operacional para a execução do objeto participando da licitação.",
     "Evento": "Contratação de empresa incapaz de executar o serviço, as obrigações financeiras, fiscais, trabalhistas e previdenciárias relativas ao contrato.", "Consequência": "Rescisão contratual; necessidade de realização de contratação emergencial.", "P": 1, "I": 5},
    {"Risco": "R13", "Causa": "Licitante vencedora apresenta proposta com preços de alguns itens abaixo do mercado (subpreço) e de outros itens acima do mercado (sobrepreço), mas de forma que o valor global de sua proposta seja o menor.",
     "Evento": "Contratação de proposta que não vantajosa (jogo de planilhas).", "Consequência": "Dano ao erário em caso de utilização de quantidade maior dos itens com sobrepreço.", "P": 3, "I": 5},
    {"Risco": "R14", "Causa": "Utilização como critério de julgamento do menor preço global por grupo de itens (lote).",
     "Evento": "Ata em que o preço registrado global é o mais vantajoso, mas o preço registrado unitário de um ou mais itens pode não ser o menor ou compatível com os preços de mercado.", "Consequência": "Contratação por preços unitários acima do mercado, causando dano ao erário.", "P": 3, "I": 5},
    {"Risco": "R15", "Causa": "Responsável pela gestão e fiscalização do contrato não detém as competências multidisciplinares e/ou condições necessárias à execução da atividade.",
     "Evento": "Gestão e/ou fiscalização inadequada.", "Consequência": "Comprometimento do resultado do serviço prestado.", "P": 3, "I": 3},
    {"Risco": "R16", "Causa": "Alterações das condições econômico-financeiras do fornecedor.",
     "Evento": "Descumprimento das condições de habilitação e exigidas na licitação.", "Consequência": "Retorno de riscos que foram mitigados por meio dos critérios de habilitação e qualificação da licitação; descontinuidade contratual; pagamento de fornecedor em débito com a fazenda.", "P": 3, "I": 5},
    {"Risco": "R17", "Causa": "Falta de sistematização sobre o que deve ser verificado na fiscalização contratual.",
     "Evento": "Aceites provisórios e definitivos em objetos parcialmente executados ou não executados.", "Consequência": "Pagamento indevido e insatisfação dos usuários.", "P": 3, "I": 3},
    {"Risco": "R18", "Causa": "Elementos básicos do contrato não estão claros para as partes.",
     "Evento": "Diferenças de entendimentos e de expectativas entre as partes.", "Consequência": "Falhas na execução do contrato.", "P": 3, "I": 3},
    {"Risco": "R19", "Causa": "Inadimplência da contratada.",
     "Evento": "Descumprimento das obrigações trabalhistas, previdenciárias e para com o FGTS pela contratada.", "Consequência": "Responsabilização subsidiária da APF em ações judiciais promovidas pelos empregados alocados na execução do contrato; rescisão contratual; necessidade de contratação emergencial.", "P": 3, "I": 5},
    {"Risco": "R20", "Causa": "Declaração imprecisa do objeto.",
     "Evento": "Decorrente inadequação dos parâmetros de fiscalização e de gestão contratual definidos no edital e anexos.", "Consequência": "Dificuldade acentuada para a realização da fiscalização e da gestão contratual junto à contratada, mediante os parâmetros exigíveis.", "P": 1, "I": 5}
]


# Cria um DataFrame
df_riscos = pd.DataFrame(dados)

# Calcula a coluna (P) * (I)
df_riscos['(P) * (I)'] = df_riscos['P'] * df_riscos['I']

# Carrega a tabela do arquivo Excel
excel_file = 'tabela_de_riscos.xlsx'
wb = load_workbook(excel_file)
ws = wb.active

# Carrega o template do documento
doc = Document(TEMPLATE_MATRIZ_RISCOS)
print(f"Template loaded: {TEMPLATE_MATRIZ_RISCOS}")

# Adiciona uma quebra de página após a primeira página
doc.add_page_break()

# Adiciona uma nova seção em paisagem após a quebra de página
new_section = doc.add_section(WD_SECTION.NEW_PAGE)
new_section.orientation = WD_ORIENT.LANDSCAPE
new_section.page_width, new_section.page_height = new_section.page_height, new_section.page_width

# Função para inserir a tabela do Excel no documento Word
def insert_table_from_excel(doc, ws):
    table = doc.add_table(rows=ws.max_row, cols=ws.max_column)
    
    # Definindo os tamanhos das colunas conforme especificado
    col_widths = [Inches(1), Inches(2), Inches(2), Inches(4), Inches(1.5), Inches(1.5), Inches(1.5)]
    
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        for j, value in enumerate(row):
            cell = table.cell(i, j)
            cell.text = str(value)
            cell_font = cell.paragraphs[0].runs[0].font
            cell_font.size = Pt(10)
            if i == 0:  # Header row
                cell_font.bold = True
                shading_elm = parse_xml(r'<w:shd {} w:fill="BFBFBF"/>'.format(nsdecls('w')))
                cell._tc.get_or_add_tcPr().append(shading_elm)
            table.columns[j].width = col_widths[j]  # Ajustando a largura da coluna
                
    return table

# Insere a tabela na nova seção em paisagem logo após a quebra de página
insert_table_from_excel(doc, ws)

# Adiciona outra quebra de página após a tabela
doc.add_page_break()

# Adiciona uma nova seção em retrato para o restante do documento
new_section = doc.add_section(WD_SECTION.NEW_PAGE)
new_section.orientation = WD_ORIENT.PORTRAIT
new_section.page_width, new_section.page_height = new_section.page_height, new_section.page_width

# Função para inserir o conteúdo de outro documento Word
def insert_document(doc, template_path):
    template_doc = Document(template_path)
    for element in template_doc.element.body:
        doc.element.body.append(element)

# Insere o conteúdo do segundo template na nova seção
insert_document(doc, TEMPLATE_MATRIZ_PARTE2)

# Salva o documento final
output_file = 'Tabela_de_Riscos_Preenchida.docx'
doc.save(output_file)
print(f"Final document saved as {output_file}")

# Abre o documento gerado
os.startfile(output_file)
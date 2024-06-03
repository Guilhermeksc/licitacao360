#create_2_planejamento_button.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QIcon, QFont, QMovie
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
from database.utils.treeview_utils import load_images, create_button, save_dataframe_to_excel
from database.utils.utilidades import ler_arquivo_json, escrever_arquivo_json, inicializar_json_do_excel, sincronizar_json_com_dataframe
import pandas as pd
import subprocess
import win32com.client
import tempfile
import os
import sys
import datetime
from datetime import datetime
import fitz
import sqlite3

def status_sort_key(status):
    order = [
        'Concluído', 'Assinatura Contrato', 'Homologado', 'Em recurso',
        'Sessão Pública', 'Impugnado', 'Pré-Publicação', 'Recomendações AGU',
        'AGU', 'Nota Técnica', 'Montagem do Processo', 'IRP', 'Setor Responsável', 'Planejamento'
    ]
    return order.index(status) if status in order else len(order)

class ReportButton(QPushButton):
    openReportDialog = pyqtSignal()

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.clicked.connect(self.emitOpenReportDialogSignal)

    def emitOpenReportDialogSignal(self):
        self.openReportDialog.emit()

def status_sort_key(status):
    order = [
        'Concluído', 'Assinatura Contrato', 'Homologado', 'Em recurso',
        'Sessão Pública', 'Impugnado', 'Pré-Publicação', 'Recomendações AGU',
        'AGU', 'Nota Técnica', 'Montagem do Processo', 'IRP', 'Setor Responsável', 'Planejamento'
    ]
    try:
        return order.index(status)
    except ValueError:
        return len(order)
    
class ReportDialog(QDialog):
    def __init__(self, dataframe, icons_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relatório")
        self.setMinimumSize(980, 500)  # Define o tamanho mínimo do diálogo
        self.setLayout(QVBoxLayout())
        self.table_view = QTableView()
        self.layout().addWidget(self.table_view)
        self.model = QStandardItemModel()
        self.table_view.setModel(self.model)
        self.setObjectName("ReportDialog")
        self.setStyleSheet("""
            #ReportDialog {
                background-color: black;
                color: white;
                font-size: 12pt;
                }
                QTableView {
                    border: 1px solid #d3d3d3;
                    gridline-color: #d3d3d3;
                    background-color: #f0f0f0;
                    font-size: 12pt;
                }
                QTableView::item:selected {
                    background-color: #a8a8a8;
                    color: white;
                    font-size: 12pt;
                }
                QTableView::item:hover {
                    background-color: #f5f5f5;
                    color: black;
                }
                QHeaderView::section {
                    background-color: #e0e0e0;
                    padding: 4px;
                    border: 1px solid #d3d3d3;
                    font-size: 12pt;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    border: none;
                    background: none;
                }
            """)
        self.dataframe = dataframe  # Armazena o DataFrame passado como argumento
        self.icons_dir = Path(icons_dir)
        self.image_cache = {}
        self.image_cache = load_images(self.icons_dir, [
            "pdf64.png", "excel.png"
        ])
        # Configura os cabeçalhos das colunas
        self.model.setHorizontalHeaderLabels(["Número", "Objeto", "OM", "Status Anterior", "Dias", "Status Atual", "Dias", "Pregoeiro"])
        # Definir o tamanho da fonte do cabeçalho da tabela
        header = self.table_view.horizontalHeader()
        font = header.font()
        font.setPointSize(12)
        header.setFont(font)
    
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # Ajustar todas as colunas para preencher o espaço
        self.table_view.resizeColumnsToContents()  # Ajusta as colunas ao conteúdo
        self.table_view.verticalHeader().setVisible(False)
        self.load_data()
        self._create_buttons()  # Cria os botões

        QTimer.singleShot(1, self.adjustColumnWidth) 

    def adjustColumnWidth(self):
        header = self.table_view.horizontalHeader()
        # Configurar outras colunas para ter tamanhos fixos
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)  

        # Ajusta o tamanho de colunas fixas
        header.resizeSection(0, 110)
        header.resizeSection(2, 110)
        header.resizeSection(4, 60)
        header.resizeSection(6, 60)

    def showEvent(self, event):
        super().showEvent(event)

    def load_data(self):
        try:
            # Conectar ao banco de dados SQLite
            conn = sqlite3.connect(CONTROLE_DADOS)
            cursor = conn.cursor()

            # Consulta SQL para obter os dados da tabela controle_processos
            cursor.execute("SELECT id_processo, objeto, sigla_om, pregoeiro FROM controle_processos")
            process_rows = cursor.fetchall()

            for row in process_rows:
                chave_processo = row[0]  # id_processo
                objeto = row[1]
                sigla_om = row[2]
                pregoeiro = row[3]

                # Buscar os dados de status e dias na tabela controle_prazos
                cursor.execute("""
                SELECT etapa, dias_na_etapa FROM controle_prazos 
                WHERE chave_processo = ? 
                ORDER BY sequencial DESC
                """, (chave_processo,))
                prazos_rows = cursor.fetchall()

                if len(prazos_rows) >= 2:
                    # Pegar os dados do status atual e anterior
                    status_atual, dias_status_atual = prazos_rows[0]
                    status_anterior, dias_status_anterior = prazos_rows[1]
                elif len(prazos_rows) == 1:
                    # Somente status atual está disponível
                    status_atual, dias_status_atual = prazos_rows[0]
                    status_anterior, dias_status_anterior = "", ""
                else:
                    # Nenhum status disponível
                    status_atual, dias_status_atual = "", ""
                    status_anterior, dias_status_anterior = "", ""

                # Se o status atual for "Concluído", substituir dias_status_atual por "-"
                if status_atual == "Concluído":
                    dias_status_atual = "-"
                # Se o status atual for "Planejamento", substituir dias_status_atual e dias_status_anterior por "-"
                if status_atual == "Planejamento":
                    dias_status_atual = "-"
                    dias_status_anterior = "-"  # Aplicando também para o status anterior
                if status_anterior == "Planejamento":
                    dias_status_anterior = "-"  # Aplicando também para o status anterior
                # Adicionar os dados ao modelo
                self.model.appendRow([
                    QStandardItem(chave_processo),
                    QStandardItem(objeto if objeto is not None else ""),
                    QStandardItem(sigla_om if sigla_om is not None else ""),
                    QStandardItem(status_anterior),
                    QStandardItem(str(dias_status_anterior)),
                    QStandardItem(status_atual),
                    QStandardItem(str(dias_status_atual)),
                    QStandardItem(pregoeiro if pregoeiro is not None else ""),
                ])

            # Fechar a conexão com o banco de dados
            conn.close()
        except sqlite3.Error as e:
            print(f"Erro ao acessar o banco de dados: {e}")

    def _create_buttons(self):
        # Cria um layout horizontal para os botões
        buttons_layout = QHBoxLayout()
        self.layout().addLayout(buttons_layout)  # Adiciona o layout de botões ao layout principal do diálogo

        # Especificações dos botões
        button_specs = [
            ("Tabela Excel", self.image_cache['excel'], self.on_export_excel, "Exportar dados para Excel"),
            ("Relatório PDF", self.image_cache['pdf64'], self.on_export_pdf, "Exportar dados para PDF")
        ]

        # Iterar sobre as especificações dos botões e criar cada botão
        for text, icon, callback, tooltip in button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self)
            buttons_layout.addWidget(btn)  # Adiciona o botão ao layout de botões

    def create_excel(self, filename="relatorio.xlsx"):
        """
        Cria um arquivo Excel a partir dos dados do modelo, incluindo cabeçalhos personalizados e formatação.
        """
        # Cria um DataFrame dos dados
        data = []
        for row in range(self.model.rowCount()):
            row_data = []
            for column in range(self.model.columnCount()):
                item = self.model.item(row, column)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        df = pd.DataFrame(data, columns=[self.model.horizontalHeaderItem(i).text() for i in range(self.model.columnCount())])

        # Adiciona colunas temporárias com os índices de ordenação baseados em 'Status Atual' e 'Status Anterior'
        df['Status Index'] = df['Status Atual'].apply(status_sort_key)
        df['Previous Status Index'] = df['Status Anterior'].apply(status_sort_key)

        # Ordena o DataFrame pelas colunas de índice e depois remove essas colunas
        df.sort_values(['Status Index', 'Previous Status Index'], inplace=True)
        df.drop(columns=['Status Index', 'Previous Status Index'], inplace=True)

        # Continua a criação e formatação do Excel
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', startrow=4, index=False)

        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        # Configurações do formato de página e margens
        worksheet.set_landscape()  # Define o layout de página para paisagem
        worksheet.set_margins(left=0.79, right=0.39, top=0.39, bottom=0.39)  # Margens em polegadas (1 cm ≈ 0.39 inches, 2 cm ≈ 0.79 inches)
        worksheet.set_header('', options={'margin': 0})  # Cabeçalho com margem 0
        worksheet.set_footer('', options={'margin': 0})  # Rodapé com margem 0
                
        # Formatos para as células
        cabecalho_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font_size': 14
        })
        cabecalho2_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'italic': True, 
            'font_size': 12
        })

        date_format = workbook.add_format({
            'italic': True, 
            'font_size': 10,
            'align': 'right'
        })

        # Formatos com cores intercaladas
        light_gray_format = workbook.add_format({'bg_color': '#F2F2F2', 'align': 'center', 'valign': 'vcenter'})
        white_format = workbook.add_format({'bg_color': '#FFFFFF', 'align': 'center', 'valign': 'vcenter'})
                
        # Configurações do cabeçalho e data
        worksheet.merge_range('A1:H1', 'Centro de Intendência da Marinha em Brasília', cabecalho_format)
        worksheet.merge_range('A2:H2', '"Prontidão e Efetividade no Planalto Central"', cabecalho2_format)
        worksheet.merge_range('A3:H3', 'Controle do Plano de Contratações Anual (PCA) 2024', cabecalho_format)
        data_atual = datetime.now().strftime("%d/%m/%Y")
        worksheet.merge_range('A4:H4', f"Atualizado em: {data_atual}", date_format)
        
        # Configurações de altura das linhas para o cabeçalho
        worksheet.set_row(0, 20)
        worksheet.set_row(2, 30)
        worksheet.set_row(3, 20)  # Ajuste de altura para a linha da data
            # Ajustar a largura das colunas, considerando a nova coluna 'Nº'
        col_widths = [10, 30, 10, 20, 5, 20, 5, 15]
        for i, width in enumerate(col_widths):
            worksheet.set_column(i, i, width)
        # Aplicar formatação de conteúdo centralizado a partir da linha 5
        for row_num in range(5, 5 + len(df)):
            for col_num in range(8):  # Colunas A a H
                cell_format = light_gray_format if (row_num % 2 == 0) else white_format
                worksheet.write(row_num, col_num, df.iloc[row_num - 5, col_num], cell_format)
        
        # Fecha o arquivo Excel
        writer.close()
        return filename  # Retorna o nome do arquivo criado

    def open_excel_file(self, filename):
        """
        Abre um arquivo Excel específico, usando um comando adequado dependendo do sistema operacional.
        """
        if os.name == 'nt':  # Para Windows
            os.startfile(filename)
        else:  # Para macOS e Linux
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, filename])

    def on_export_excel(self):
        filename = self.create_excel()  # Cria o arquivo Excel
        self.open_excel_file(filename)  # Abre o arquivo Excel criado

    def excel_to_pdf(self, excel_file_path, pdf_file_path):
        """
        Converte um arquivo Excel em PDF.
        """
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False  # Executa em background
        try:
            doc = excel.Workbooks.Open(excel_file_path)
            doc.ExportAsFixedFormat(0, pdf_file_path)  # 0 indica que estamos exportando para PDF
        except Exception as e:
            print(f"Erro: {e}")
        finally:
            if doc is not None:
                doc.Close(False)
            excel.Quit()

    def adicionar_imagem_ao_pdf(self, pdf_path, left_image_path, right_image_path, watermark_image_path, image_size_cm=(2, 2)):
        pdf_path = str(pdf_path)
        left_image_path = str(left_image_path)
        right_image_path = str(right_image_path)
        watermark_image_path = str(watermark_image_path)  # Caminho para a imagem da marca d'água

        doc = fitz.open(pdf_path)
        numero_total_paginas = len(doc)  # Obter o número total de páginas
     
        for pagina_number, pagina in enumerate(doc):  # Iterar por todas as páginas
            page_width = pagina.rect.width
            page_height = pagina.rect.height
            texto_contador_paginas = f"- {pagina_number + 1} de {numero_total_paginas} -"  # Formatar o texto do contador

            # Configurar o texto para o contador de páginas
            text_rect = fitz.Rect(0, page_height - 40, page_width, page_height)  # Definir a posição do texto na parte inferior da página
            pagina.insert_textbox(text_rect, texto_contador_paginas, fontsize=11, align=1)  # Inserir o texto do contador
            
            # Inserir marca d'água centralizada em todas as páginas
            wm = fitz.open(watermark_image_path)  # Abrir imagem da marca d'água
            pix = wm[0].get_pixmap()  # Obter pixmap do primeiro documento da imagem
            scale = min(page_width / pix.width, page_height / pix.height) / 1.5  # Escala para reduzir o tamanho da marca d'água
            scaled_width = pix.width * scale
            scaled_height = pix.height * scale
            center_x = (page_width - scaled_width) / 2
            center_y = (page_height - scaled_height) / 2
            watermark_rect = fitz.Rect(center_x, center_y, center_x + scaled_width, center_y + scaled_height)
            
            pagina.insert_image(watermark_rect, filename=watermark_image_path)
            
            # Inserir imagens esquerda e direita apenas na primeira página
            if pagina_number == 0:
                # Calcular o tamanho da imagem em pontos
                image_size_pt = (image_size_cm[0] * 70 / 2.54, image_size_cm[1] * 70 / 2.54)
                
                # Calcular o deslocamento das imagens a partir das bordas em pontos
                offset_left_x_pt = 5 * 72 / 2.54
                offset_right_x_pt = page_width - (4 * 72 / 2.54) - image_size_pt[0]
                offset_y_pt = 1.3 * 72 / 2.54  # 1 cm do topo
                
                # Definir os retângulos onde as imagens serão inseridas
                left_rect = fitz.Rect(offset_left_x_pt, offset_y_pt, offset_left_x_pt + image_size_pt[0], offset_y_pt + image_size_pt[1])
                right_rect = fitz.Rect(offset_right_x_pt, offset_y_pt, offset_right_x_pt + image_size_pt[0], offset_y_pt + image_size_pt[1])
                
                # Inserir as imagens na primeira página
                pagina.insert_image(left_rect, filename=left_image_path)
                pagina.insert_image(right_rect, filename=right_image_path)
            
        # Salvar o documento modificado
        novo_pdf_path = pdf_path.replace('.pdf', '_com_modificacoes.pdf')
        doc.save(novo_pdf_path)
        doc.close()

        # Informar ao usuário sobre o salvamento do novo arquivo
        print(f"PDF modificado salvo como: {novo_pdf_path}")

        # Abrir o PDF automaticamente (Windows)
        try:
            os.startfile(novo_pdf_path)
        except Exception as e:
            print(f"Não foi possível abrir o arquivo PDF automaticamente. Erro: {e}")

    def on_export_pdf(self):
        """
        Exporta os dados para um arquivo PDF e abre o arquivo.
        """
        # Cria um arquivo Excel temporário
        temp_excel_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        excel_file_path = self.create_excel(temp_excel_file.name)
        
        # Define o caminho para o arquivo PDF de saída
        pdf_file_path = excel_file_path.replace('.xlsx', '.pdf')
        
        # Converte o arquivo Excel em PDF
        self.excel_to_pdf(excel_file_path, pdf_file_path)
        self.adicionar_imagem_ao_pdf(str(pdf_file_path), str(TUCANO_PATH), str(MARINHA_PATH), str(CEIMBRA_BG))
        # Tenta remover o arquivo Excel temporário
        try:
            os.remove(excel_file_path)
        except PermissionError as e:
            print(f"Não foi possível remover o arquivo temporário: {e}. O arquivo pode ainda estar sendo usado.")
        except Exception as e:
            print(f"Erro ao tentar remover o arquivo temporário: {e}")

        # Abre o arquivo PDF gerado
        if sys.platform == "win32":
            os.startfile(pdf_file_path)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, pdf_file_path])

        print(f"Arquivo PDF exportado e aberto: {pdf_file_path}")
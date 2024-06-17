from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
import pandas as pd
import os
from diretorios import *
from datetime import datetime
import win32com.client
import fitz
import time
import subprocess
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import numpy as np

colunasDesejadas = [
    'Tipo', 'Processo', 'empresa', 'Dias', 'Objeto',  'Setor', 'contrato_formatado',  
    'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto', 
    'link_contrato_inicial', 'link_termo_aditivo', 'link_portaria']

colunas = [
    'Processo', 'contrato_formatado', 'OM', 'Setor', 'empresa', 'Objeto', 'Vig. Fim', 'Dias', 'link_contrato_inicial']

class GerarTabelas(QDialog):
    def __init__(self, merged_data, parent=None):
        super().__init__(parent)
        self.merged_data = merged_data
        self.omComboBox = QComboBox(self)
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("Gerar Tabelas")
        layout = QVBoxLayout(self)

        # Adicionar ComboBox para seleção de OM
        layout.addWidget(QLabel("Escolha a OM:"))
        self.omComboBox.addItems(self.getUniqueOMs())
        layout.addWidget(self.omComboBox)
        
        btnTabelaGestores = QPushButton("Tabela Gestores e Fiscais", self)
        btnTabelaGestores.clicked.connect(self.gerarTabelaGestores)
        layout.addWidget(btnTabelaGestores)
       
        btnPlanilhaCompleta = QPushButton("Planilha Completa", self)
        btnPlanilhaCompleta.clicked.connect(self.gerarPlanilhaCompleta)
        layout.addWidget(btnPlanilhaCompleta)   

        btnGerarPastas = QPushButton("Gerar Pastas", self)
        btnGerarPastas.clicked.connect(self.gerartodasPastas)
        layout.addWidget(btnGerarPastas) 

        btnVerificarPDFs = QPushButton("Verificar nomes dos PDF", self)
        btnVerificarPDFs.clicked.connect(self.verificarPDFs)
        layout.addWidget(btnVerificarPDFs)

    def verificarPDFs(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Selecione a pasta a ser verificada", QDir.homePath())

        if dir_path:
            problema_encontrado = False
            log = []

            for subfolder in os.listdir(dir_path):
                subfolder_path = os.path.join(dir_path, subfolder)
                if os.path.isdir(subfolder_path):
                    for additional_folder in ['portaria_fiscalizacao', 'contrato_inicial', 'termo_aditivo']:
                        self.verificarPastaEspecifica(subfolder, subfolder_path, additional_folder, log, problema_encontrado)

            for subfolder in os.listdir(dir_path):
                subfolder_path = os.path.join(dir_path, subfolder)
                if os.path.isdir(subfolder_path):
                    for additional_folder in ['portaria_fiscalizacao', 'contrato_inicial', 'termo_aditivo']:
                        self.verificarPastaEspecifica(subfolder, subfolder_path, additional_folder, log, problema_encontrado)

            self.finalizarVerificacao(dir_path, problema_encontrado, log)

    def verificarPastaEspecifica(self, subfolder, subfolder_path, additional_folder, log, problema_encontrado):
        additional_folder_path = os.path.join(subfolder_path, additional_folder)
        if os.path.exists(additional_folder_path):
            pdf_files = [f for f in os.listdir(additional_folder_path) if f.lower().endswith('.pdf')]
            if len(pdf_files) > 1:
                self.deletarPDFsAntigos(additional_folder_path, pdf_files, subfolder, additional_folder, log)
            elif len(pdf_files) == 0:
                problema_encontrado = True
                log.append(f"Nenhum PDF encontrado em '{subfolder}/{additional_folder}'.")
            else:
                self.renomearPDF(additional_folder_path, pdf_files[0], additional_folder, log)
        else:
            problema_encontrado = True
            log.append(f"A pasta '{additional_folder}' não foi encontrada em '{subfolder_path}'.")

    def deletarPDFsAntigos(self, additional_folder_path, pdf_files, subfolder, additional_folder, log):
        pdf_files.sort(key=lambda x: os.path.getctime(os.path.join(additional_folder_path, x)), reverse=True)
        for file_to_delete in pdf_files[1:]:
            os.remove(os.path.join(additional_folder_path, file_to_delete))
        log.append(f"Mais de um PDF encontrado em '{subfolder}/{additional_folder}'. Apenas o mais recente foi mantido.")

    def renomearPDF(self, additional_folder_path, pdf_file, additional_folder, log):
        new_pdf_name = f"{additional_folder}.pdf"
        old_pdf_path = os.path.join(additional_folder_path, pdf_file)
        new_pdf_path = os.path.join(additional_folder_path, new_pdf_name)
        os.rename(old_pdf_path, new_pdf_path)
        log.append(f"Renomeado '{pdf_file}' para '{new_pdf_name}'.")

    def finalizarVerificacao(self, dir_path, problema_encontrado, log):
        if problema_encontrado:
            log_message = "\n".join(log)
            log_file_path = os.path.join(dir_path, "log_erros.txt")
            with open(log_file_path, 'w') as log_file:
                log_file.write(log_message)
            QMessageBox.information(self, "Sucesso", f"Todos os PDFs foram verificados com sucesso! O log de erros foi salvo em:\n{log_file_path}")
            subprocess.Popen(['notepad.exe', log_file_path])
        else:
            QMessageBox.information(self, "Sucesso", "Todos os PDFs foram verificados com sucesso!")

    def gerartodasPastas(self):
        # Abrir uma janela para o usuário escolher onde as pastas serão criadas
        dir_path = QFileDialog.getExistingDirectory(self, "Selecione a pasta de destino", QDir.homePath())

        if dir_path:  # Verifica se o usuário selecionou um diretório
            # Cria a pasta 'Atas_e_Contratos' dentro do diretório selecionado
            atas_contratos_dir = os.path.join(dir_path, "Atas_e_Contratos")
            os.makedirs(atas_contratos_dir, exist_ok=True)
            
            # Obtém os dados do modelo
            df = self.convertModelToDataFrame()
            
            # Itera sobre as linhas do DataFrame
            for index, row in df.iterrows():
                # Obtém o valor em 'Processo' e ajusta para substituir '/' por '_'
                processo = row['Processo'].replace('/', '-').replace(' ', '_')

                # Cria a pasta para o 'Processo' dentro de 'Atas_e_Contratos'
                processo_folder_path = os.path.join(atas_contratos_dir, processo)
                os.makedirs(processo_folder_path, exist_ok=True)

                # Obtém o valor formatado e ajusta para substituir '/' por '_'
                valor_formatado = row['Valor Formatado'].replace('/', '_')
                
                # Cria a subpasta 'Valor Formatado' dentro da pasta 'Processo'
                valor_formatado_path = os.path.join(processo_folder_path, valor_formatado)
                os.makedirs(valor_formatado_path, exist_ok=True)
                
                # Cria as pastas adicionais dentro da subpasta 'Valor Formatado'
                for additional_folder in ['portaria_fiscalizacao', 'contrato_inicial', 'termo_aditivo']:
                    additional_folder_path = os.path.join(valor_formatado_path, additional_folder)
                    os.makedirs(additional_folder_path, exist_ok=True)

            QMessageBox.information(self, "Sucesso", "Pastas geradas com sucesso!")

                            
    def getUniqueOMs(self):
        # Supondo que "OM" é uma coluna no seu DataFrame "merged_data"
        unique_oms = self.merged_data['OM'].unique().tolist()
        unique_oms.sort()  # Opcional: Ordenar a lista de OMs
        return unique_oms
    
    def getFilteredData(self, filterFunc=None):
        # Lista para armazenar os dados filtrados
        filteredData = []
        # Obter os nomes de todas as colunas no modelo
        allColumns = [self.model.headerData(i, Qt.Orientation.Horizontal) for i in range(self.model.columnCount())]
        # Filtrar índices das colunas desejadas baseado em allColumns e colunasDesejadas
        desiredColumnIndexes = [i for i, colName in enumerate(allColumns) if colName in colunasDesejadas]

        # Obter o número de linhas no modelo
        rowCount = self.model.rowCount()
        
        for row in range(rowCount):
            rowData = []
            includeRow = True
            for column in desiredColumnIndexes:  # Usar apenas índices das colunas desejadas
                index = self.model.index(row, column)
                data = self.model.data(index)
                if filterFunc and not filterFunc(row, column, data):
                    includeRow = False
                    break
                rowData.append(data)
            if includeRow:
                filteredData.append(rowData)
        # As colunas retornadas devem ser exatamente as 'colunasDesejadas'
        return filteredData, colunasDesejadas

    def ajustarDados(self, filteredData, columns):
        if 'Dias' in columns:
            diasIndex = columns.index('Dias')
            filteredData = [row[:diasIndex] + row[diasIndex+1:] for row in filteredData]
            newColumns = [col for col in columns if col != 'Dias']
        else:
            newColumns = columns
        return filteredData, newColumns

    def ajustarColunas(self, df, aba):
        # Renomeia as colunas com base na aba atual
        renomear_colunas = {
            'Dias': 'Dias p/\nVencer',
            'Setor': 'Setor Demandante',
            'empresa': 'Contratado'
        }
        df.rename(columns=renomear_colunas, inplace=True)

        if aba == 'Contratos':
            df.rename(columns={'contrato_formatado': 'Contrato'}, inplace=True)
        elif aba == 'Ata':
            df.rename(columns={'contrato_formatado': 'Ata'}, inplace=True)

        return df
    
    def excel_to_pdf(self, excel_file_path, pdf_file_path):
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False  # Executa em background
        try:
            doc = excel.Workbooks.Open(excel_file_path)
            doc.ExportAsFixedFormat(0, pdf_file_path)  # 0 indica que estamos exportando para PDF
        except Exception as e:
            print(f"Erro: {e}")
        finally:
            time.sleep(1)
            doc.Close(False)  # Fecha o documento sem salvar mudanças
            excel.Quit()  # Fecha a aplicação Excel
                    
    def gerarPlanilhaCompleta(self):
        df = self.merged_data  # exemplo simplificado

        df['Dias'] = pd.to_numeric(df['Dias'], errors='coerce').fillna(0).astype(int)
        # Supondo que merged_data é seu DataFrame
        print("Valores da coluna 'link_contrato_inicial':", self.merged_data['link_contrato_inicial'].to_list())

        df['link_contrato_inicial'] = df['link_contrato_inicial'].apply(lambda x: x if isinstance(x, str) else np.nan)
        # Supondo que merged_data é seu DataFrame
        print("Valores da coluna 'link_contrato_inicial':", self.merged_data['link_contrato_inicial'].to_list())

        df_contratos = df[df['Tipo'] == 'Contrato'][colunas].sort_values(by='Dias')
        df_ata = df[df['Tipo'] == 'Ata'][colunas].sort_values(by='Dias')
        print("Colunas de df_contratos:", df_contratos.columns.tolist())
        print("Colunas de df_ata:", df_ata.columns.tolist())
        filepath = os.path.join(CONTROLE_CONTRATOS_DIR, "Planilha_Completa.xlsx")
                
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            for name, df in [('Contratos', df_contratos), ('Ata', df_ata)]:
                df = self.ajustarColunas(df.copy(), name)
                df.insert(0, 'Nº', range(1, len(df) + 1))
                
                # Escreve os dados a partir da quinta linha
                df.to_excel(writer, sheet_name=name, index=False, startrow=4)  
                worksheet = writer.sheets[name]

                # Configurações de layout de página
                worksheet.set_landscape()  # Orientação paisagem
                worksheet.set_paper(9)  # Definir o tamanho do papel como A4
                worksheet.set_margins(left=0, right=0, top=0, bottom=0.7)  # Margens estreitas
                worksheet.fit_to_pages(1, 0)  # Ajustar para caber em uma página

                # Formatos para as células
                cabecalho_format = writer.book.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'bold': True,
                    'font_size': 14
                })

                header_format = writer.book.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'vcenter',  # Centraliza verticalmente
                    'align': 'center',    # Centraliza horizontalmente
                    'border': 1,
                    'bg_color': '#ADD8E6'  # Define a cor de fundo como azul claro
                })

                # Cria um novo formato para os links que centraliza o conteúdo
                link_format = writer.book.add_format({'font_color': 'blue', 'bold': True, 'underline': True})

                cell_format = writer.book.add_format({
                    'border': 1,
                    'align': 'center',
                    'bold': True, 
                    'valign': 'vcenter', 
                    'font_size': 10
                })
                title_format = writer.book.add_format({
                    'align': 'center', 
                    'bold': True, 
                    'valign': 'vcenter', 
                    'font_size': 14
                })

                date_format = writer.book.add_format({
                    'italic': True, 
                    'font_size': 10,
                    'align': 'right' 
                })

                # Aplicar o formato aos cabeçalhos das colunas
                for col_num, value in enumerate(df.columns):
                    worksheet.write(4, col_num, value, header_format)

                for row_num in range(5, len(df) + 5):
                    for col_num in range(len(df.columns)):
                        valor = df.iloc[row_num-5, col_num]
                        if pd.isnull(valor):
                            valor = ''  # Substitui NaN por uma string vazia ou outro valor apropriado
                        # Substitui valores infinitos por uma string vazia (ou outro valor). Isso assume que valores infinitos são raros ou inesperados.
                        elif isinstance(valor, float) and (valor == float("inf") or valor == float("-inf")):
                            valor = ''
                        worksheet.write(row_num, col_num, valor, cell_format)
                                    
                worksheet.merge_range('A1:K1', 'Centro de Intendência da Marinha em Brasília', cabecalho_format)
                worksheet.merge_range('A2:K2', '"Prontidão e Efetividade no Planalto Central"', cabecalho_format)
                titulo = "Controle de Contratos - 2024" if name == 'Contratos' else "Controle de Atas de Registro de Preços - 2024"
                worksheet.merge_range('A3:K3', titulo, title_format)  # Título agora na linha 3
                worksheet.set_row(0, 20)
                worksheet.set_row(1, 30)
                worksheet.set_row(2, 30)
                data_atual = datetime.now().strftime("%d/%m/%Y")
                worksheet.merge_range('A4:K4', f"Atualizado em: {data_atual}", date_format)  # Data agora na linha 4
                
                if 'link_contrato_inicial' in df.columns:
                    link_column_index = df.columns.get_loc('link_contrato_inicial')
                    for row, link in enumerate(df['link_contrato_inicial'], start=5):
                        # Verifica se o link é uma string e não está vazio
                        if isinstance(link, str) and link.startswith("http"):
                            worksheet.write_url(row, link_column_index, link, string='Ver Detalhes')
                        else:
                            # Opcional: Escreva um valor padrão ou deixe a célula em branco
                            worksheet.write(row, link_column_index, "Link indisponível", cell_format)

                                 
                # Ajustar a largura das colunas, considerando a nova coluna 'Nº'
                col_widths = [3, 10, 15, 9, 21, 30, 25, 10, 7, 10, 10]
                for i, width in enumerate(col_widths):
                    worksheet.set_column(i, i, width)

        # Converta para PDF ou adicione imagens, se necessário
        pdf_filepath = os.path.join(CONTROLE_CONTRATOS_DIR, "Planilha_Completa.pdf")
        self.excel_to_pdf(filepath, pdf_filepath)
        self.adicionar_imagem_ao_pdf(str(pdf_filepath), str(TUCANO_PATH), str(MARINHA_PATH), str(CEIMBRA_BG))

        QMessageBox.information(self, "Sucesso", "Planilha Completa gerada e convertida para PDF com sucesso!")

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
                image_size_pt = (image_size_cm[0] * 108 / 2.54, image_size_cm[1] * 108 / 2.54)
                
                # Calcular o deslocamento das imagens a partir das bordas em pontos
                offset_left_x_pt = 4 * 72 / 2.54
                offset_right_x_pt = page_width - (4 * 72 / 2.54) - image_size_pt[0]
                offset_y_pt = 0.1 * 72 / 2.54  # 1 cm do topo
                
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

    def convertModelToDataFrame(self):
        colunas = [self.model.headerData(i, Qt.Orientation.Horizontal) for i in range(self.model.columnCount())]
        dados = []
        for row in range(self.model.rowCount()):
            rowData = []
            for col in range(self.model.columnCount()):
                index = self.model.index(row, col)
                item = self.model.data(index)
                rowData.append(item if item is not None else "")
            dados.append(rowData)
        
        df = pd.DataFrame(dados, columns=colunas)
        
        # Imprimir o DataFrame após sua criação
        print("DataFrame antes das substituições:")
        print(df.head())  # Imprime as primeiras 5 linhas do DataFrame para uma visão geral
        
        # Substituir '' e 'nan' por '-' antes de retornar o DataFrame
        df.replace(to_replace=["", "nan"], value="-", inplace=True)
        
        # Imprimir o DataFrame após substituir '' e 'nan' por '-'
        print("\nDataFrame após substituir '' e 'nan' por '-':")
        print(df.head())  # Novamente, imprime as primeiras 5 linhas para visualização
        
        # Substituir NaN por '-' para cobrir todos os casos
        df.fillna("-", inplace=True)
        
        # Imprimir o DataFrame após preencher valores NaN
        print("\nDataFrame após preencher NaN com '-':")
        print(df.head())  # Uma última impressão para ver o estado final do DataFrame
        
        return df

    def gerarTabelaGestores(self):
        selectedOM = self.omComboBox.currentText()
        df = self.convertModelToDataFrame()
        
        # Filtrar por OM selecionada
        df_filtered = df[df['OM'] == selectedOM]
        
        # Filtrar por 'Dias' > 0, convertendo para numérico e lidando com não numéricos
        df_filtered = df_filtered[pd.to_numeric(df_filtered['Dias'], errors='coerce').fillna(0) > 0]
        
        # Se necessário, selecione apenas as colunas desejadas
        df_final = df_filtered[colunasDesejadas] if 'Dias' in df_filtered.columns else df_filtered
        
        # Salvar o DataFrame final em Excel
        self.saveFilteredDataToExcel(df_final, "Tabela_Gestores_Fiscais.xlsx")

    def saveFilteredDataToExcel(self, df, filename):
        # Mapeamento das colunas do DataFrame para os títulos desejados no Excel
        colunasOrdenadasEInfo = [
            ('contrato_formatado', 'Número'),
            ('Tipo', 'Tipo'),
            ('empresa', 'Empresa'),
            ('Objeto', 'Objeto'),
            ('Setor', 'Setor'),
            ('Posto_Gestor', 'Posto/Graduação Gestor'),
            ('Gestor', 'Gestor'),
            ('Posto_Gestor_Substituto', 'Posto/Graduação Gestor Substituto'),
            ('Gestor_Substituto', 'Gestor Substituto'),
            ('Posto_Fiscal', 'Posto/Graduação Fiscal'),
            ('Fiscal', 'Fiscal'),
            ('Posto_Fiscal_Substituto', 'Posto/Graduação Fiscal Substituto'),
            ('Fiscal_Substituto', 'Fiscal Substituto'),
        ]

        # Reordenar e renomear colunas conforme necessário
        colunasOriginais = [col[0] for col in colunasOrdenadasEInfo]
        novosTitulos = {col[0]: col[1] for col in colunasOrdenadasEInfo}
        
        # Filtrar apenas as colunas presentes no DataFrame
        colunasPresentes = [col for col in colunasOriginais if col in df.columns]
        
        # Remover 'Dias' da lista, se presente
        if 'Dias' in colunasPresentes:
            colunasPresentes.remove('Dias')
        
        # Reordenar o DataFrame conforme a ordem especificada
        df = df[colunasPresentes]
        
        # Renomear as colunas conforme os novos títulos
        df.rename(columns=novosTitulos, inplace=True)

        # Ordenação customizada para a coluna 'Tipo', se presente
        if 'Tipo' in df.columns:
            ordenacao_customizada = {'Contrato': 1, 'Ata': 2}
            df['Ordem_Tipo'] = df['Tipo'].map(ordenacao_customizada)
            df.sort_values('Ordem_Tipo', inplace=True)
            df.drop('Ordem_Tipo', axis=1, inplace=True)

        # Salvar o DataFrame no arquivo Excel
        filepath = os.path.join(CONTROLE_CONTRATOS_DIR, filename)  # Ajuste DIRETORIO_DESTINO conforme necessário
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Sheet1', index=False)
            worksheet = writer.sheets['Sheet1']
            
            # Ajustar a largura das colunas
            col_widths = [15, 10, 30, 25, 30, 25, 25, 25, 25, 25, 25, 25, 25]  # Ajuste conforme necessário
            for i, width in enumerate(col_widths[:len(df.columns)]):
                worksheet.set_column(i, i, width)

        QMessageBox.information(self, "Sucesso", f"Tabela '{filename}' gerada com sucesso!\nLocal: {filepath}")
        # Abrir o arquivo Excel automaticamente após a criação
        self.abrirArquivoExcel(filepath)

    def abrirArquivoExcel(self, filepath):
        try:
            if os.name == 'nt':  # Para Windows
                os.startfile(filepath)
            elif os.name == 'posix':  # Para macOS e Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', filepath], check=True)
        except Exception as e:
            QMessageBox.warning(self, "Erro ao abrir arquivo", f"Não foi possível abrir o arquivo automaticamente.\nErro: {e}")

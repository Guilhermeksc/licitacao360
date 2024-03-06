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

colunasDesejadas = ['Tipo', 'Fornecedor Formatado', 'Dias', 'Objeto',  'Setor', 'Valor Formatado',  'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 
    'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto']

colunas = [
    'Valor Formatado', 'Objeto', 'OM', 'Setor', 'Fornecedor Formatado', 'Valor Global', 'Vig. Fim', 'Dias']

class GerarTabelas(QDialog):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.omComboBox = QComboBox()  # ComboBox para escolher a OM
        self.table_view = QTableView()  # Adicione o atributo table_view
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

        # Adicionar botões ao layout
        layout.addWidget(btnTabelaGestores)
       
        # Adicionar botão "Planilha Completa"
        btnPlanilhaCompleta = QPushButton("Planilha Completa", self)
        btnPlanilhaCompleta.clicked.connect(self.gerarPlanilhaCompleta)
        layout.addWidget(btnPlanilhaCompleta)

        # Adicionar botão "Importar Tabela Gestores"
        btnImportarTabelaGestores = QPushButton("Importar Tabela Gestores", self)
        btnImportarTabelaGestores.clicked.connect(self.importarTabelaGestores)
        layout.addWidget(btnImportarTabelaGestores)

        # Adicionar a QTableView ao layout
        layout.addWidget(self.table_view)
    
    def importarTabelaGestores(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Importar Tabela Gestores", "", "Excel Files (*.xlsx *.xls)")
        if filePath:
            try:
                sicronizar_gestor_fiscal = pd.read_excel(filePath)
                
                # Supondo que `self.model` seja uma instância de `CustomTableModel` que possui um método `getDataFrame`
                dataframe_atual = self.model.getDataFrame()
                
                # Implementação da lógica de sincronização
                for index, row in sicronizar_gestor_fiscal.iterrows():
                    if row['Número'] in dataframe_atual['Valor Formatado'].values:
                        # Encontrar o índice no dataframe_atual onde existe correspondência
                        indices = dataframe_atual[dataframe_atual['Valor Formatado'] == row['Número']].index
                        for col in ['Posto/Graduação Gestor', 'Gestor', 'Posto/Graduação Gestor Substituto', 'Gestor Substituto', 'Posto/Graduação Fiscal', 'Fiscal', 'Posto/Graduação Fiscal Substituto', 'Fiscal Substituto']:
                            dataframe_atual.loc[indices, col] = row[col]
                
                # Atualizar o modelo com o DataFrame modificado
                self.model.setDataFrame(dataframe_atual)  # Supondo que existe um método `setDataFrame` para atualizar o DataFrame
                self.table_view.setModel(self.model)  # Atualize a QTableView com o novo modelo
                
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível importar o arquivo.\nErro: {e}")
                print(f"Não foi possível importar o arquivo.\nErro: {e}")
                
    def getUniqueOMs(self):
        omSet = set()
        for row in range(self.model.rowCount()):
            # Ajustar para coluna 11, considerando que a indexação começa em 0
            index = self.model.index(row, 11)  # Ajuste para coluna OM (coluna 11)
            omSet.add(self.model.data(index))
        return sorted(list(omSet))
    
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
            'Setor': 'Setor Demandante',
            'Fornecedor Formatado': 'Contratado'
        }
        df.rename(columns=renomear_colunas, inplace=True)

        if aba == 'Contratos':
            df.rename(columns={'Valor Formatado': 'Contrato'}, inplace=True)
        elif aba == 'Ata':
            df.rename(columns={'Valor Formatado': 'Ata'}, inplace=True)

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
        df = self.convertModelToDataFrame()
        df['Dias'] = pd.to_numeric(df['Dias'], errors='coerce').fillna(0).astype(int)
        df_contratos = df[df['Tipo'] == 'Contrato'][colunas].sort_values(by='Dias')
        df_ata = df[df['Tipo'] == 'Ata'][colunas].sort_values(by='Dias')

        # Adicionar colunas "Contrato Inicial" e "Termo Aditivo" com "Link" como placeholder
        df_contratos['Contrato Inicial'] = 'Link'
        df_contratos['Termo Aditivo'] = 'Link'
        df_ata['Contrato Inicial'] = 'Link'
        df_ata['Termo Aditivo'] = 'Link'

        filepath = os.path.join(CONTROLE_CONTRATOS_DIR, "Planilha_Completa.xlsx")

        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            for name, df in [('Contratos', df_contratos), ('Ata', df_ata)]:
                df = self.ajustarColunas(df.copy(), name)
                df.insert(0, 'Nº', range(1, len(df) + 1))
                
                # Comece a escrever os dados a partir da quinta linha (indexado como 4)
                df.to_excel(writer, sheet_name=name, index=False, startrow=4)  
                worksheet = writer.sheets[name]

                # Configurações de layout de página
                worksheet.set_landscape()  # Orientação paisagem
                worksheet.set_paper(9)  # Definir o tamanho do papel como A4
                worksheet.set_margins(left=0, right=0, top=0, bottom=0)  # Margens estreitas
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
                    'border': 1
                })

                # Cria um novo formato para os links que centraliza o conteúdo
                link_format = writer.book.add_format({
                    'valign': 'vcenter',  # Centraliza verticalmente
                    'align': 'center',    # Centraliza horizontalmente
                    'font_color': 'blue', # Opcional: Muda a cor da fonte para azul
                    'underline':  1       # Opcional: Sublinha o texto
                })

                cell_format = writer.book.add_format({'border': 1})
                title_format = writer.book.add_format({
                    'align': 'center', 
                    'bold': True, 
                    'valign': 'vcenter', 
                    'font_size': 14
                })

                date_format = writer.book.add_format({
                    'align': 'right', 
                    'italic': True, 
                    'font_size': 10
                })

                # Definir formatos para linhas ímpares e pares para alternar as cores de fundo
                even_row_format = writer.book.add_format({'bg_color': '#F2F2F2', 'border': 1})  # Cor cinza claro para linhas pares
                odd_row_format = writer.book.add_format({'border': 1})  # Sem cor de fundo para linhas ímpares (mantendo o formato padrão)

                # Aplicar o formato alternado a todas as linhas de dados, começando da linha 6 (índice 5) até o fim dos dados
                for row_num in range(5, len(df) + 5):
                    # Definir o formato da linha com base na paridade do número da linha
                    row_format = even_row_format if (row_num + 1) % 2 == 0 else odd_row_format
                    worksheet.set_row(row_num, None, row_format)

                # Aplicar o formato aos cabeçalhos das colunas
                for col_num, value in enumerate(df.columns):
                    worksheet.write(4, col_num, value, header_format)

                # Identificar índices das colunas de hiperlinks
                columns = df.columns.tolist()
                link_col_index_1 = columns.index('Contrato Inicial')
                link_col_index_2 = columns.index('Termo Aditivo')

                # Aplicar hiperlinks centralizados nas colunas específicas
                for row_num in range(5, len(df) + 5):
                    worksheet.write_url(row_num, link_col_index_1, 'https://www.com7dn.mb/sites/default/arquivos/obtencao/acordos%20adm/embarcacoes%20cfb/lc%20de%20souza%20embarca%C3%A7%C3%B5es%20-%202023.pdf', string='Link', cell_format=link_format)
                    worksheet.write_url(row_num, link_col_index_2, 'https://www.com7dn.mb/sites/default/arquivos/obtencao/portaria/Portaria-de-Fiscalizacao-de-Contrato%2058---FORTT-DO-BRASIL.pdf', string='Link', cell_format=link_format)

                # Aplicar bordas a todas as células de dados
                for row_num in range(5, len(df) + 5):
                    for col_num in range(len(df.columns)):
                        worksheet.write(row_num, col_num, df.iloc[row_num-5, col_num], cell_format)
                                    
                worksheet.merge_range('A1:K1', 'Centro de Intendência da Marinha em Brasília (CeIMBra)', cabecalho_format)
                worksheet.merge_range('A2:K2', '"Prontidão e Efetividade no Planalto Central"', cabecalho_format)
                titulo = "Controle de Contratos" if name == 'Contratos' else "Controle de Atas"
                worksheet.merge_range('A3:K3', titulo, title_format)  # Título agora na linha 3
                data_atual = datetime.now().strftime("%d/%m/%Y")
                worksheet.merge_range('A4:K4', f"Atualizado em: {data_atual}", date_format)  # Data agora na linha 4
                
                # Ajustar a largura das colunas, considerando a nova coluna 'Nº'
                col_widths = [3, 15, 21, 9, 30, 30, 15, 10, 4]
                for i, width in enumerate(col_widths):
                    worksheet.set_column(i, i, width)

        filepath = os.path.join(CONTROLE_CONTRATOS_DIR, "Planilha_Completa.xlsx")
        pdf_filepath = os.path.join(CONTROLE_CONTRATOS_DIR, "Planilha_Completa.pdf")

        # Chamada para a função excel_to_pdf para converter o arquivo Excel para PDF
        self.excel_to_pdf(filepath, pdf_filepath)

        TUCANO_PATH = DATABASE_DIR / "image" / "imagem_excel.png"

        # Verifica se o arquivo da imagem existe antes de prosseguir
        if not TUCANO_PATH.is_file():
            raise FileNotFoundError(f"O arquivo de imagem não foi encontrado em: {TUCANO_PATH}")

        MARINHA_PATH = DATABASE_DIR / "image" / "marinha.png"

        # Verifica se o arquivo da imagem existe antes de prosseguir
        if not MARINHA_PATH.is_file():
            raise FileNotFoundError(f"O arquivo de imagem não foi encontrado em: {MARINHA_PATH}")

        self.adicionar_imagem_ao_pdf(str(pdf_filepath), str(TUCANO_PATH), str(MARINHA_PATH))

        QMessageBox.information(self, "Sucesso", "Planilha Completa gerada e convertida para PDF com sucesso!")

    def adicionar_imagem_ao_pdf(self, pdf_path, left_image_path, right_image_path, image_size_cm=(2, 2)):
        pdf_path = str(pdf_path)
        left_image_path = str(left_image_path)
        right_image_path = str(right_image_path)

        doc = fitz.open(pdf_path)
        primeira_pagina = doc[0]
        page_width = primeira_pagina.rect.width

        # Calcular o tamanho da imagem em pontos
        image_size_pt = (image_size_cm[0] * 72 / 2.54, image_size_cm[1] * 72 / 2.54)
        
        # Calcular o deslocamento das imagens a partir das bordas em pontos
        offset_left_x_pt = 8 * 72 / 2.54
        offset_right_x_pt = page_width - (8 * 72 / 2.54) - image_size_pt[0]
        offset_y_pt = 0.1 * 72 / 2.54  # 1 cm do topo
        
        # Definir os retângulos onde as imagens serão inseridas
        left_rect = fitz.Rect(offset_left_x_pt, offset_y_pt, offset_left_x_pt + image_size_pt[0], offset_y_pt + image_size_pt[1])
        right_rect = fitz.Rect(offset_right_x_pt, offset_y_pt, offset_right_x_pt + image_size_pt[0], offset_y_pt + image_size_pt[1])
        
        # Inserir as imagens na primeira página
        primeira_pagina.insert_image(left_rect, filename=left_image_path)
        primeira_pagina.insert_image(right_rect, filename=right_image_path)
        
        # Salvar o documento modificado
        novo_pdf_path = pdf_path.replace('.pdf', '_com_imagens.pdf')
        doc.save(novo_pdf_path)
        doc.close()

        # Informar ao usuário sobre o salvamento do novo arquivo
        print(f"PDF modificado salvo como: {novo_pdf_path}")

        # Abrir o PDF automaticamente (Windows)
        try:
            os.startfile(novo_pdf_path)
        except Exception as e:
            QMessageBox.warning(self, "Erro ao abrir PDF", f"Não foi possível abrir o arquivo PDF automaticamente.\nErro: {e}")


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
        # Substituir '' e 'nan' por '-' antes de retornar o DataFrame
        df.replace(to_replace=["", "nan"], value="-", inplace=True)
        # Substituir NaN por '-' para cobrir todos os casos
        df.fillna("-", inplace=True)
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
            ('Valor Formatado', 'Número'),
            ('Tipo', 'Tipo'),
            ('Fornecedor Formatado', 'Empresa'),
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
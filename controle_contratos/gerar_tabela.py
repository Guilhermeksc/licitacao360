#gerar_tabela.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
import pandas as pd
import os
from diretorios import *
from datetime import datetime

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

    def gerarPlanilhaCompleta(self):
        df = self.convertModelToDataFrame()
        
        # Converter coluna "Dias" para inteiros, removendo os zeros à esquerda
        df['Dias'] = pd.to_numeric(df['Dias'], errors='coerce').fillna(0).astype(int)
        
        # Filtrar os dados para Contratos e Ata, e ordenar por 'Dias'
        df_contratos = df[df['Tipo'] == 'Contrato'][colunas].sort_values(by='Dias')
        df_ata = df[df['Tipo'] == 'Ata'][colunas].sort_values(by='Dias')

        # Caminho para salvar o arquivo
        filepath = os.path.join(CONTROLE_CONTRATOS_DIR, "Planilha_Completa.xlsx")

        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            # Salvar cada DataFrame em uma aba diferente
            for name, df in [('Contratos', df_contratos), ('Ata', df_ata)]:
                # Ajustar as colunas com base na aba
                df = self.ajustarColunas(df.copy(), name)

                df.insert(0, 'Nº', range(1, len(df) + 1))
                
                # Escreve os dados no Excel iniciando na linha 4, colocando o cabeçalho na linha 3
                df.to_excel(writer, sheet_name=name, index=False, startrow=2)
                worksheet = writer.sheets[name]
                
                # Formatos para as células
                header_format = writer.book.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'border': 1
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

                # Aplicar o formato aos cabeçalhos das colunas
                for col_num, value in enumerate(df.columns):
                    worksheet.write(2, col_num, value, header_format)

                # Aplicar bordas a todas as células de dados
                for row_num in range(3, len(df) + 3):
                    for col_num in range(len(df.columns)):
                        worksheet.write(row_num, col_num, df.iloc[row_num-3, col_num], cell_format)
                
                # Mesclar células para o título da planilha na primeira linha e escrever o título
                titulo = "Controle de Contratos" if name == 'Contratos' else "Controle de Atas"
                worksheet.merge_range('A1:I1', titulo, title_format)

                # Obter a data atual e formatá-la como string
                data_atual = datetime.now().strftime("%d/%m/%Y")
                # Mesclar células para a linha de data de atualização na segunda linha e escrever a data
                worksheet.merge_range('A2:I2', f"Atualizado em: {data_atual}", date_format)
                
                # Ajustar a largura das colunas, considerando a nova coluna 'Nº'
                col_widths = [3, 15, 21, 9, 30, 30, 15, 10, 4]
                for i, width in enumerate(col_widths):
                    worksheet.set_column(i, i, width)

        QMessageBox.information(self, "Sucesso", f"Planilha Completa gerada com sucesso!\nLocal: {filepath}")
        self.abrirArquivoExcel(filepath)

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
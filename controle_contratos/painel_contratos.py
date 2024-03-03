from PyQt6 import QtWidgets, QtGui, QtCore
from diretorios import *
from controle_contratos.atualizar_dados_contratos import AtualizarDadosContratos
from controle_contratos.utils_contratos import *
from controle_contratos.gerar_tabela import *
from datetime import datetime, timedelta
from num2words import num2words
from docxtpl import DocxTemplate
import comtypes.client
import os

colunas = [
    'Comprasnet', 'Tipo', 'Processo', 'NUP', 'CNPJ', 'Fornecedor Formatado', 
    'Dias', 'Valor Global', 'Objeto', 'OM', 'Setor', 'CP', 'MSG', 'Vig. Início',
    'Vig. Fim', 'Valor Formatado', 'Portaria', 'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 
    'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto', 'Natureza Continuada', 'Comentários', 'Termo Aditivo', 'Status0', 'Status1', 'Status2', 'Status3', 'Status4', 'Status5']

colunas_contratos = [
    'Número do instrumento', 'Fornecedor', 'Vig. Início', 'Vig. Fim', 'Valor Global']

colunas_adicionais = [
    'Número do instrumento', 'Objeto', 'OM', 'Tipo', 'Portaria', 'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto',  
    'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto', 'Vig. Fim Formatado', 'Valor Formatado', 'Natureza Continuada', 
    'Processo', 'NUP', 'Setor', 'CP', 'MSG', 'CNPJ', 'Fornecedor Formatado', 'Dias', 'Comentários', 'Termo Aditivo', 'Status0', 'Status1', 'Status2', 'Status3', 'Status4', 'Status5']

colunas_gestor_fiscal = [
    'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto',]

class ContratosWidget(QWidget):
    def __init__(self, colunas, parent=None):
        super().__init__(parent)
        self.colunas = colunas
        # Inicializa merged_data com dados carregados ou DataFrame vazio
        self.merged_data = DataProcessor.load_data(CONTRATOS_PATH, ADICIONAIS_PATH, colunas_contratos, colunas_adicionais)
        self.setupUI()
        self.loadAndConfigureModel()
        self.model.itemChanged.connect(self.onItemChanged)
        self.isSearchManagerConnected = False
        self.searchManager = SearchManager(self.proxyModel, self.searchField)

    def setupUI(self):
        self.layout = QVBoxLayout(self)
        self.setupSearchField()
        self.setupTableView()
        self.setupButtons()

    def setupTableView(self):
        self.table_view = QTableView(self)
        self.layout.addWidget(self.table_view)
        self.table_view.setItemDelegate(CellBorderDelegate())
        self.table_view.setStyleSheet("""
            QTableView {
                background-color: black;
                color: white;
            }
        """)
        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        altura_fixa = 20
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table_view.verticalHeader().setDefaultSectionSize(altura_fixa)
        self.table_view.verticalHeader().hide()
        self.table_view.clicked.connect(self.onTableViewClicked)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.doubleClicked.connect(self.abrirDialogoEditarInformacoesAdicionais)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.onTableViewRightClick)
        
        QTimer.singleShot(1, self.ajustarLarguraColunas)

        # Habilitar a ordenação
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)

    def setupButtons(self):
        # Adiciona os botões existentes
        self.buttons_layout = QHBoxLayout()
        buttons_info = [
            ("Gerar Tabela", self.abrirGerarTabelas),
            ("CP Alerta Prazo", self.abrirDialogoGerarDocumentosCP),  
            ("Mensagem Cobrança", self.abrirDialogoAlertaPrazo),

            ("Informações Adicionais", self.abrirDialogoEditarInformacoesAdicionais),
            ("Marcar/Desmarcar Todos", self.onTestToggleClicked),
            # ("Configurações", self.abrirDialogoConfiguracoes),
            ("Importar Tabela Gestores", self.abrirDialogoImportacao)
        ]
        for text, func in buttons_info:
            btn = QPushButton(text, self)
            if func:  # Verifica se uma função foi fornecida
                btn.clicked.connect(func)
            self.buttons_layout.addWidget(btn)
        
        # # Adiciona o ComboBox para seleção de filtro
        # self.filtroDiasComboBox = QComboBox(self)
        # self.filtroDiasComboBox.addItem("Filtrar Dias", None)  # Opção padrão
        # self.filtroDiasComboBox.addItem("Filtrar < 180 Dias", 180)
        # self.filtroDiasComboBox.addItem("Filtrar < 120 Dias", 120)
        # self.filtroDiasComboBox.addItem("Filtrar < 60 Dias", 60)
        # self.filtroDiasComboBox.addItem("Remover Filtro", -1)  # Usaremos -1 como indicador para remover o filtro
        
        # # Conecta o sinal de mudança do ComboBox ao método de filtragem
        # self.filtroDiasComboBox.currentIndexChanged.connect(self.aplicarFiltroDias)
        
        # self.buttons_layout.addWidget(self.filtroDiasComboBox)
        self.layout.addLayout(self.buttons_layout)

    def aplicarFiltroDias(self, index):
        # Obtém o valor associado à opção selecionada
        dias_limite = self.filtroDiasComboBox.itemData(index)
        
        if dias_limite is None or dias_limite == -1:
            self.proxyModel.setDiasLimite(None)  # Remove o filtro
        else:
            self.proxyModel.setDiasLimite(dias_limite) 

    def onTableViewRightClick(self, position):
        # Cria o menu de contexto
        menu = QMenu()

        # Adiciona as ações ao menu
        copy_cnpj_action = menu.addAction("Copiar CNPJ")
        copy_contract_num_action = menu.addAction("Copiar Nº do Contrato")
        # copy_pregao_num_action = menu.addAction("Copiar Nº do Pregão")
        copy_nup = menu.addAction("Copiar NUP")

        # Conecta as ações aos métodos correspondentes
        copy_cnpj_action.triggered.connect(lambda: self.copyDataToClipboard('CNPJ'))
        copy_contract_num_action.triggered.connect(lambda: self.copyDataToClipboard('Valor Formatado'))
        # copy_pregao_num_action.triggered.connect(lambda: self.copyDataToClipboard('Processo'))
        copy_nup.triggered.connect(lambda: self.copyDataToClipboard('NUP'))

        # Exibe o menu no ponto onde o clique com o botão direito foi realizado
        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def copyDataToClipboard(self, columnName):
        # Obtém o índice da linha e coluna selecionados
        index = self.table_view.currentIndex()
        if not index.isValid():
            return

        # Se estiver usando um proxy model, mapeia o índice para o modelo fonte
        sourceIndex = self.proxyModel.mapToSource(index) if hasattr(self.table_view.model(), 'mapToSource') else index

        # Ajusta para a coluna correta com base no nome da coluna fornecido
        # Adiciona 2 ao índice da coluna para compensar as colunas iniciais sem dados
        column = self.colunas.index(columnName) + 2
        dataIndex = self.model.index(sourceIndex.row(), column)

        # Obtém o valor da coluna especificada
        data = self.model.data(dataIndex)

        # Copia o valor para a área de transferência
        QApplication.clipboard().setText(data)
        # Mostra um tooltip indicando que o dado foi copiado
        self.showCopyTooltip(f"{columnName} copiado: {data}")

    def showCopyTooltip(self, message):
        cursorPos = QCursor.pos()  # Obter a posição atual do cursor
        # Corrige a chamada para usar msecShowTime em vez de timeout
        QToolTip.showText(cursorPos, message, msecShowTime=2500)  # Mostrar tooltip na posição do cursor por 1.5 segundos

        # A linha abaixo para esconder automaticamente o tooltip após o tempo não é estritamente necessária,
        # pois o msecShowTime já controla isso, mas pode ser mantida se houver comportamento inesperado.
        QTimer.singleShot(2500, QToolTip.hideText)

    def abrirDialogoImportacao(self):
        dialogo = QFileDialog(self)
        dialogo.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialogo.setNameFilter("Tabelas (*.xlsx *.csv)")
        if dialogo.exec():
            arquivo_selecionado = dialogo.selectedFiles()[0]
            self.importarDadosGestoresFiscais(arquivo_selecionado)

    def importarDadosGestoresFiscais(self, caminho_arquivo):
        try:
            # Ler o arquivo selecionado e criar um DataFrame
            if caminho_arquivo.endswith('.csv'):
                df = pd.read_csv(caminho_arquivo)
            elif caminho_arquivo.endswith('.xlsx'):
                df = pd.read_excel(caminho_arquivo)
            else:
                raise ValueError("Formato de arquivo não suportado.")
            
            # Renomear a coluna conforme especificado
            df.rename(columns={'Número': 'Valor Formatado'}, inplace=True)
            
            # Converter todas as colunas para o tipo 'object'
            df = df.astype(str)

            # Imprimir os nomes das colunas e seus tipos após a conversão
            print("Colunas df de caminho_arquivo após a conversão:")
            print(df.dtypes)

            # Sincronizar com o arquivo ADICIONAIS_PATH
            self.sincronizarComAdicionais(df)

            QMessageBox.information(self, "Sucesso", "Dados importados e sincronizados com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar dados: {e}")
            print(f"Erro ao importar dados: {e}")


    def sincronizarComAdicionais(self, df_novos_dados):
        # Carregar dados existentes
        adicionais_df = pd.read_csv(ADICIONAIS_PATH)
        adicionais_df = adicionais_df.astype(str)
        print("Colunas adicionais_df de ADICIONAIS_PATH:")
        print(adicionais_df.dtypes)
        # Colunas de interesse para sincronização
        colunas_gestor_fiscal = [
            'Posto Gestor', 'Gestor', 'Posto Gestor Substituto', 'Gestor Substituto',
            'Posto Fiscal', 'Fiscal', 'Posto Fiscal Substituto', 'Fiscal Substituto'
        ]

        # Assegurar que 'Valor Formatado' esteja presente e seja a chave para sincronização
        if 'Valor Formatado' in df_novos_dados.columns and 'Valor Formatado' in adicionais_df.columns:
            # Iterar sobre cada linha dos novos dados
            for index, row in df_novos_dados.iterrows():
                valor_formatado = row['Valor Formatado']
                
                # Encontrar a correspondência em adicionais_df baseado em 'Valor Formatado'
                if valor_formatado in adicionais_df['Valor Formatado'].values:
                    idx = adicionais_df.index[adicionais_df['Valor Formatado'] == valor_formatado].tolist()[0]
                    
                    # Atualizar as colunas de interesse em adicionais_df com os valores de df_novos_dados
                    for coluna in colunas_gestor_fiscal:
                        if coluna in df_novos_dados.columns:
                            adicionais_df.at[idx, coluna] = row[coluna]

        # Salvar os dados sincronizados de volta ao ADICIONAIS_PATH
        adicionais_df.to_csv(ADICIONAIS_PATH, index=False)

        # Atualizar a visualização, se necessário
        self.atualizarModeloDeDados()

        # Ajustar as larguras das colunas conforme necessário
        self.ajustarLarguraColunas()

    def abrirGerarTabelas(self):
        dialog = GerarTabelas(self.model, self)
        dialog.exec()

    def atualizarModeloDeDados(self):
        # Recarrega os dados e atualiza o modelo
        self.contratos_data = DataProcessor.load_data(CONTRATOS_PATH, ADICIONAIS_PATH, colunas_contratos, colunas_adicionais)
        self.model = CustomTableModel(self.contratos_data, colunas, ICONS_DIR)
        self.proxyModel.setSourceModel(self.model)
        self.table_view.setModel(self.proxyModel)
        # Reconecta o SearchManager aqui
        self.searchManager = SearchManager(self.proxyModel, self.searchField)

    def abrirDialogoDeAtualizacao(self):
        dialogo = AtualizarDadosContratos(self)
        dialogo.dadosContratosSalvos.connect(self.atualizarModeloDeDados)
        dialogo.exec()

    def onItemChanged(self, item):
        if item.column() == 1:  # Verifica se a mudança ocorreu na coluna dos checkboxes
            row = item.row()
            check_state = item.checkState() == Qt.CheckState.Checked
            print(f"Checkbox na linha {row} alterado para {'selecionado' if check_state else 'não selecionado'}")
            # Atualiza o DataFrame
            self.model.merged_data.at[row, 'Selecionado'] = check_state

    def setupSearchField(self):
        self.searchField = QLineEdit(self)
        self.searchField.setPlaceholderText("Buscar por nome da empresa ou outro dado...")
        self.layout.addWidget(self.searchField)

    def onHeaderClicked(self, logicalIndex):
        print("Antes da reordenação:")
        for i in range(self.model.rowCount()):
            item = self.model.item(i, 1)  # Assumindo que os checkboxes estejam na coluna 1
            if item:
                print(f"Linha {i}: {'selecionado' if item.checkState() == Qt.CheckState.Checked else 'não selecionado'}")
        
        sortOrder = self.table_view.horizontalHeader().sortIndicatorOrder()
        self.proxyModel.sort(logicalIndex, sortOrder)
        
        print("Depois da reordenação:")
        for i in range(self.model.rowCount()):
            item = self.model.item(i, 1)
            if item:
                print(f"Linha {i}: {'selecionado' if item.checkState() == Qt.CheckState.Checked else 'não selecionado'}")

    def loadAndConfigureModel(self):
        contratos_data = DataProcessor.load_data(CONTRATOS_PATH, ADICIONAIS_PATH, colunas_contratos, colunas_adicionais)
        self.model = CustomTableModel(contratos_data, colunas, ICONS_DIR)
        self.proxyModel = MultiColumnFilterProxyModel(contratos_data)  # Passando contratos_data

        self.proxyModel.setSourceModel(self.model)

        self.table_view.setModel(self.proxyModel)
        self.proxyModel.setColumnIndices(colunas)
        self.checkboxManager = CheckboxManager(self.model)
        self.searchField.textChanged.connect(self.onSearchTextChanged)

    def onSearchTextChanged(self, text):
        fornecedorIndex = colunas.index('Fornecedor Formatado') if 'Fornecedor Formatado' in colunas else -1
        if fornecedorIndex != -1:
            self.proxyModel.setFilterKeyColumn(fornecedorIndex)
            self.proxyModel.setFilterRegularExpression(QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption))
        else:
            print("Coluna 'Fornecedor Formatado' não encontrada nas colunas definidas.")

    def onTableViewClicked(self, index):
        if index.isValid():
            # Se estiver usando um proxy model, mapeia o índice para o modelo fonte
            sourceIndex = self.proxyModel.mapToSource(index) if hasattr(self.table_view.model(), 'mapToSource') else index
            checkboxIndex = self.model.index(sourceIndex.row(), 1)  # Ajuste para a coluna correta do checkbox
            
            item = self.model.itemFromIndex(checkboxIndex)
            if item and item.isCheckable():
                newState = not item.checkState() == Qt.CheckState.Checked
                item.setCheckState(Qt.CheckState.Checked if newState else Qt.CheckState.Unchecked)
                self.model.merged_data.at[sourceIndex.row(), 'Selecionado'] = newState
                print(f"Estado do checkbox na linha {sourceIndex.row()} atualizado para {'selecionado' if newState else 'não selecionado'}")

    def onSelectionChanged(self, selected, deselected):
        selected_rows = self.table_view.selectionModel().selectedRows()
        for index in selected_rows:
            row_data = self.model.dados.iloc[index.row()]
            print(row_data)

    def abrirDialogoEditarInformacoesAdicionais(self):
        selectionModel = self.table_view.selectionModel()
        if selectionModel.hasSelection():
            indice_linha = selectionModel.currentIndex().row()  # Obtém o índice da linha selecionada
            contrato_atual = self.obterContratoAtual()
            if contrato_atual:
                dialogo = AtualizarDadosContratos(contrato_atual, self.table_view, self)
                dialogo.indice_linha = indice_linha  # Passa o índice da linha para o diálogo
                dialogo.dadosContratosSalvos.connect(self.atualizarLinhaEspecifica)
                dialogo.exec()
        else:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um contrato para editar.")
        
    def atualizarLinhaEspecifica(self, dados_atualizados, indice_visual):
        coluna_mapeamento = {'Número do instrumento': 'Comprasnet'}  # Defina o mapeamento aqui conforme necessário
        if hasattr(self, 'proxyModel'):
            indice_linha_source = self.proxyModel.mapToSource(self.proxyModel.index(indice_visual, 0)).row()
        else:
            indice_linha_source = indice_visual

        for chave, valor in dados_atualizados.items():
            # Aplica o mapeamento para encontrar o nome correto da coluna
            coluna_mapeada = coluna_mapeamento.get(chave, chave)
            if coluna_mapeada in self.colunas:
                coluna_index = self.colunas.index(coluna_mapeada) + 2   # Assumindo que não há mais desalinhamento
                try:
                    item = self.model.item(indice_linha_source, coluna_index)
                    if item:
                        item.setText(str(valor))
                        # Notifica a mudança para atualizar a view
                        self.model.dataChanged.emit(self.model.index(indice_linha_source, coluna_index), self.model.index(indice_linha_source, coluna_index))
                except Exception as e:
                    print(f"Erro ao atualizar coluna '{chave}': {e}")
            else:
                print(f"Coluna '{chave}' não encontrada nas colunas definidas.")
        
        # Força a atualização do filtro no proxyModel, se necessário
        if hasattr(self, 'proxyModel'):
            self.proxyModel.invalidateFilter()

    def atualizarDadosTableView(self):
        contratos_data = DataProcessor.load_data(CONTRATOS_PATH, ADICIONAIS_PATH, colunas_contratos, colunas_adicionais)
        self.model = CustomTableModel(contratos_data, colunas, ICONS_DIR)
        self.table_view.setModel(self.model)
        self.ajustarLarguraColunas()  

    def abrirDialogoConfiguracoes(self):
        dialog = ConfiguracoesDialog(self.colunas, self.table_view, self)
        dialog.exec()

    def ajustarLarguraColunas(self):
        for i in range(self.table_view.model().columnCount()):
            self.table_view.resizeColumnToContents(i)

    def onTestToggleClicked(self):
        # Verifica o estado do primeiro checkbox para decidir se irá marcar ou desmarcar todos
        if self.model.rowCount() > 0:
            firstItemState = self.model.item(0, 1).checkState()
            # Se o primeiro item estiver marcado, desmarcar todos, e vice-versa
            newState = not (firstItemState == Qt.CheckState.Checked)
            self.checkboxManager.toggleAllCheckboxes(newState)

    def obterContratoAtual(self):
        selection = self.table_view.selectionModel().selectedIndexes()
        if selection:
            # Se estiver usando um proxy model, assegure-se de mapear para o source model
            model = self.table_view.model().sourceModel() if hasattr(self.table_view.model(), 'sourceModel') else self.table_view.model()

            index = selection[0]  # Índice da célula selecionada no proxy model
            sourceIndex = self.table_view.model().mapToSource(index) if hasattr(self.table_view.model(), 'mapToSource') else index

            contrato_atual = {}
            for coluna in range(model.columnCount()):
                indice = model.index(sourceIndex.row(), coluna)
                chave = model.headerData(coluna, Qt.Orientation.Horizontal)
                valor = model.data(indice, Qt.ItemDataRole.DisplayRole)
                # Checar se o valor é a string "nan" e substituir por ''
                if valor == "nan":
                    valor = ''
                contrato_atual[chave] = valor

            print("Contrato Atual:", contrato_atual)
            return contrato_atual
        else:
            return None

    def coletarDadosSelecionados(self):
        dados_selecionados = []
        for row in range(self.model.rowCount()):
            checkbox_item = self.model.item(row, 1)  # Assumindo que os checkboxes estejam na coluna 1
            if checkbox_item.checkState() == Qt.CheckState.Checked:
                dados_linha = {
                    'numero_comprasnet': self.model.item(row, 2).text(),
                    'tipo': self.model.item(row, 3).text(),
                    'processo': self.model.item(row, 4).text(),                
                    'nup': self.model.item(row, 5).text(),
                    'cnpj': self.model.item(row, 6).text(), 
                    'empresa': self.model.item(row, 7).text(),
                    'dias_para_vencer': self.model.item(row, 8).text(),
                    'valor_global': self.model.item(row, 9).text(), 
                    'objeto': self.model.item(row, 10).text(),                    
                    'om': self.model.item(row, 11).text(), 
                    'setor': self.model.item(row, 12).text(), 
                    'cp': self.model.item(row, 13).text(),
                    'msg': self.model.item(row, 14).text(),
                    'inicio_vigencia': self.model.item(row, 15).text(), 
                    'fim_vigencia': self.model.item(row, 16).text(),                
                    'numero_contrato': self.model.item(row, 17).text(),  
                    'portaria': self.model.item(row, 18).text(),
                    'gestor': self.model.item(row, 19).text(),
                    'fiscal': self.model.item(row, 20).text(),
                    'prazo_limite': DataProcessor.calcular_prazo_limite(self.model.item(row, 16).text())
                }
                dados_selecionados.append(dados_linha)
        return dados_selecionados

    def abrirDialogoAlertaPrazo(self):
        dados_selecionados = self.coletarDadosSelecionados()
        texto = self.prepararTextoAlertaPrazo(dados_selecionados)
        dialogo = MSGAlertaPrazo(texto)
        dialogo.exec()
        
    def prepararTextoAlertaPrazo(self, dados_selecionados):
        texto = "<p>ROTINA<br>"
        mes_atual = datetime.now().strftime("%b").upper()
        ano_atual = datetime.now().strftime('%Y')
        texto += f"R000000Z/<span style='color: blue;'>{mes_atual}</span>/<span style='color: blue;'>{ano_atual}</span><br>"
        texto += "DE NICITB<br>PARA SETDIS<br>GRNC<br>BT<br><br>"
        texto += "Renovação de Acordos Administrativos<br><br>"
        texto += "<br>ALFA - Contratos Administrativo<br><br><br>"        
        for idx, dados in enumerate(dados_selecionados, start=1):
            numero_extenso = DataProcessor.numero_para_extenso(idx)

            texto += (f"{numero_extenso} - <span style='color: blue;'>{dados['processo']}</span>:<br>"
                    f" Contrato Administrativo n° <span style='color: blue;'>{dados['numero_contrato']};</span><br>"
                    f" Nup: <span style='color: blue;'>{dados['nup']};</span><br>" 
                    f" Nome da Empresa: <span style='color: blue;'>{dados['empresa']}</span>, CNPJ: <span style='color: blue;'>{dados['cnpj']};</span><br>"
                    f" Objeto: <span style='color: blue;'>{dados['objeto']};</span><br>"
                    f" Valor global: <span style='color: blue;'>{dados['valor_global']}; e</span><br>"
                    f" Final da Vigência: <span style='color: blue;'>{dados['fim_vigencia']}.</span><br><br>"
                    # f" portaria <span style='color: blue;'>{dados['portaria']}</span> | gestor <span style='color: blue;'>{dados['gestor']}</span> | "
                    # f" fiscal <span style='color: blue;'>{dados['fiscal']}</span><br><br>"
                    # f"Prazo limite para encaminhamento da documentação: <span style='color: red;'>{dados['prazo_limite']}</span><br><br>"
                    )
        texto += "</p>BT"
        return texto


             # prazo_limite = calcular_prazo_limite(dados['fim_vigencia'])
            # texto += (f"{numero_extenso} - Contrato administrativo n° <span style='color: blue;'>{dados['numero_contrato']}</span>\n"
            #         f" tipo <span style='color: blue;'>{dados['tipo']}</span> | processo <span style='color: blue;'>{dados['processo']}</span> | "
            #         f" nup <span style='color: blue;'>{dados['nup']}</span> | cnpj <span style='color: blue;'>{dados['cnpj']}</span> | "
            #         f" empresa <span style='color: blue;'>{dados['empresa']}</span> | valor global <span style='color: blue;'>{dados['valor_global']}</span> | "
            #         f" dias para vencer <span style='color: blue;'>{dados['dias_para_vencer']}</span> | objeto <span style='color: blue;'>{dados['objeto']}</span> | "
            #         f" om <span style='color: blue;'>{dados['om']}</span> | setor <span style='color: blue;'>{dados['setor']}</span> | "
            #         f" início vigência <span style='color: blue;'>{dados['inicio_vigencia']}</span> | fim vigência <span style='color: blue;'>{dados['fim_vigencia']}</span> | "
            #         f" portaria <span style='color: blue;'>{dados['portaria']}</span> | gestor <span style='color: blue;'>{dados['gestor']}</span> | "
            #         f" fiscal <span style='color: blue;'>{dados['fiscal']}</span><br><br>"
            #         f"Prazo limite para encaminhamento da documentação: <span style='color: red;'>{dados['prazo_limite']}</span><br><br>"
                    # )
       
    def abrirDialogoGerarDocumentosCP(self):
        dialog = NumeroCPDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            numero_cp = dialog.getNumeroCP()
            if numero_cp.isdigit():  # Verifica se o input é um número
                numero_cp = int(numero_cp)
                dados_selecionados = self.coletarDadosSelecionados()
                # Adiciona o numero_cp a cada item em dados_selecionados
                for dados in dados_selecionados:
                    # Formata o numero_cp com dois dígitos e o adiciona aos dados
                    dados['numero_cp'] = str(numero_cp).zfill(2)
                    numero_cp += 1  # Incrementa para o próximo documento
                self.gerarDocumentosCP(dados_selecionados)
            else:
                QMessageBox.warning(self, "Erro", "Número da CP inválido.")

    def gerarDocumentosCP(self, dados_selecionados):
        progress_dialog = QProgressDialog("Convertendo documentos para PDF...", "Cancelar", 0, len(dados_selecionados), self)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.show()

        for i, dados in enumerate(dados_selecionados, start=1):
            if dados['tipo'] == 'Contrato':
                template_path = CP_CONTRATOS_DIR / "cp_contrato.docx"
            else:
                template_path = CP_CONTRATOS_DIR / "cp_ata.docx"

            doc = DocxTemplate(template_path)
            doc.render(dados)

            processo_formatado = dados['processo'].replace('/', '-')
            nome_arquivo = f"CP-30-{str(dados['numero_cp']).zfill(2)}-Renovacao {dados['tipo']} {processo_formatado}.docx"
            caminho_completo = CP_CONTRATOS_DIR / nome_arquivo

            if not caminho_completo.parent.exists():
                os.makedirs(caminho_completo.parent)

            doc.save(caminho_completo)
            print(f"Documento salvo: {caminho_completo}")

            # Atualiza a barra de progresso antes de iniciar a conversão para PDF
            progress_dialog.setValue(i - 1)  # i-1 porque i começa de 1
            progress_dialog.setLabelText(f"Convertendo documento {i} de {len(dados_selecionados)} para PDF...")

            # Verifica se a operação foi cancelada
            if progress_dialog.wasCanceled():
                break

            # Converte o arquivo DOCX para PDF
            pdf_path = caminho_completo.with_suffix('.pdf')
            # Supondo que docx_to_pdf é uma função que você definiu para fazer a conversão
            self.docx_to_pdf(caminho_completo, pdf_path)
            print(f"Versão PDF salva: {pdf_path}")

        progress_dialog.setValue(len(dados_selecionados))

    def docx_to_pdf(self, docx_path, pdf_path):
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False
        doc = word.Documents.Open(str(docx_path))  # Converte Path para string aqui
        doc.SaveAs2(str(pdf_path), FileFormat=17)  # Converte Path para string aqui
        doc.Close()
        word.Quit()
        
class MultiColumnFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, dados, parent=None):
        super().__init__(parent)
        self.merged_data = dados
        # Define as colunas que serão ocultas
        self.hidden_columns = set([
            'MSG', 'Vig. Início', 'Vig. Fim', 'Valor Formatado', 'Portaria', 'Posto_Gestor', 
            'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 
            'Fiscal_Substituto', 'Natureza Continuada', 'Comentários', 'Termo Aditivo', 'Status0', 'Status2', 
            'Status3', 'Status4', 'Status5'
        ])

        self.column_indices = {}

    def filterAcceptsRow(self, sourceRow, sourceParent):
        # Mantém a lógica original para filtragem de linhas
        columnCount = self.sourceModel().columnCount(sourceParent)
        for column in range(columnCount):
            index = self.sourceModel().index(sourceRow, column, sourceParent)
            data = self.sourceModel().data(index)
            if self.filterRegularExpression().match(data).hasMatch():
                return True
        return False

    def filterAcceptsColumn(self, sourceColumn, sourceParent):
        print(f"Verificando coluna: {sourceColumn}")  # Debug
        if sourceColumn < 2:
            return True

        # Trata explicitamente os índices 34 e 35 como ocultos
        if sourceColumn in [34, 35]:
            return False
        
        column_name = self.column_indices.get(sourceColumn)
        print(f"Nome da coluna: {column_name}")  # Debug
        if column_name in self.hidden_columns:
            print(f"Ocultando coluna: {column_name}")  # Debug
            return False
        print(f"Mostrando coluna: {column_name}")  # Debug
        return True

    def setColumnIndices(self, column_names):
        # Mapeia nomes de colunas para seus índices
        self.column_indices = {index: name for index, name in enumerate(column_names)}
        print("Mapeamento de índices para nomes de colunas:", self.column_indices)
        self.invalidateFilter()

    def setHiddenColumns(self, hidden_columns):
        # Permite atualizar o conjunto de colunas ocultas dinamicamente
        self.hidden_columns = set(hidden_columns)
        self.invalidateFilter()  # Atualiza o filtro para aplicar as mudanças

    def getDataFrame(self):
        # Retorna os dados originais armazenados em 'merged_data'
        return self.merged_data

class DataProcessor:
    @staticmethod
    def processar_fornecedor(fornecedor):
        match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})|(\d{3}\.\d{3}\.\d{3}-\d{2})', fornecedor)
        if match:
            identificacao = match.group()
            nome_fornecedor = fornecedor[match.end():].lstrip(" -")
            return pd.Series([identificacao, nome_fornecedor], index=['CNPJ', 'Fornecedor Formatado'])
        return pd.Series(["", fornecedor], index=['CNPJ', 'Fornecedor Formatado'])

    @staticmethod
    def ler_adicionais(adicionais_path, colunas_necessarias):
        if Path(adicionais_path).exists():
            adicionais_data = pd.read_csv(adicionais_path, dtype=str)
            adicionais_data = adicionais_data.astype(str)  # Assegura tipo object para todas as colunas
            adicionais_data = adicionais_data.reindex(columns=colunas_necessarias, fill_value="")
        else:
            adicionais_data = pd.DataFrame(columns=colunas_necessarias).astype(str)
        return adicionais_data

    @staticmethod
    def calcular_dias_para_vencer(data_fim):
        data_fim = pd.to_datetime(data_fim, format='%d/%m/%Y', errors='coerce')
        diferenca = (data_fim - pd.Timestamp.now()).days
        return diferenca

    @staticmethod
    def formatar_dias_p_vencer(valor):
        sinal = '-' if valor < 0 else ''
        return f"{sinal}{abs(valor):04d}"

    @staticmethod
    def formatar_numero_instrumento(numero):
        if pd.isna(numero) or numero == "":
            return ""
        numero = str(numero)
        partes = numero.split('/')
        numero_instrumento = partes[0].lstrip('0')
        dois_ultimos_digitos = partes[1][-2:]
        numero_formatado = f"87000/{dois_ultimos_digitos}-{numero_instrumento.zfill(3)}/00"
        return numero_formatado
    
    @staticmethod
    def load_data(contratos_path, adicionais_path, colunas_contratos, colunas_adicionais):
        contratos_data = pd.read_csv(contratos_path, dtype=str)
        adicionais_data = DataProcessor.ler_adicionais(adicionais_path, colunas_adicionais)

        resultado_processamento = contratos_data['Fornecedor'].apply(DataProcessor.processar_fornecedor).apply(pd.Series)
        resultado_processamento.rename(columns={0: 'CNPJ', 1: 'Fornecedor Formatado'}, inplace=True)
        contratos_data = pd.concat([contratos_data, resultado_processamento], axis=1)

        merged_data = pd.merge(contratos_data, adicionais_data, on='Número do instrumento', how='left')
        
        colunas_para_manter = ['CNPJ_x', 'Fornecedor Formatado_x']
        colunas_renomeadas = {coluna: coluna.rstrip('_x') for coluna in colunas_para_manter}
        merged_data.rename(columns=colunas_renomeadas, inplace=True)

        colunas_merged_final = colunas_contratos + [coluna for coluna in colunas_adicionais if coluna != 'Número do instrumento']
        merged_data = merged_data[[coluna for coluna in colunas_merged_final if coluna in merged_data.columns]]

        if 'Vig. Fim' in merged_data.columns:
            merged_data['Dias'] = merged_data['Vig. Fim'].apply(DataProcessor.calcular_dias_para_vencer).apply(DataProcessor.formatar_dias_p_vencer)

        adicionais_data.to_csv(adicionais_path, index=False)
        merged_data['Selecionado'] = False

        return merged_data
    
    @staticmethod
    def calcular_prazo_limite(fim_vigencia):
        data_fim_vigencia = datetime.strptime(fim_vigencia, "%d/%m/%Y")
        prazo_limite = data_fim_vigencia - timedelta(days=90)
        # Ajusta para o primeiro dia útil anterior se cair em um fim de semana
        while prazo_limite.weekday() > 4:  # 5 = sábado, 6 = domingo
            prazo_limite -= timedelta(days=1)
        return prazo_limite.strftime("%d/%m/%Y")
    
    @staticmethod
    def numero_para_extenso(numero):
        extenso = num2words(numero, lang='pt_BR')
        if numero == 1:
            extenso = extenso.replace('um', 'uno')
        return extenso.upper()
    
class CheckableItem(QStandardItem):
    def __init__(self, text="", checkState=Qt.CheckState.Unchecked):
        super().__init__(text)
        self.setCheckable(True)
        self.setCheckState(checkState)
        self.setEditable(False)

class CustomTableModel(QStandardItemModel):
    def __init__(self, dados, colunas, icons_dir, parent=None):
        super().__init__(parent)
        self.merged_data = dados
        self.icons_dir = icons_dir
        self.colunas = colunas
        self.setupModel()

    def setDataFrame(self, new_data):
        self.merged_data = new_data
        self.layoutChanged.emit()

    def setupModel(self):
        self.setHorizontalHeaderLabels(['', ''] + self.colunas)
        for i, row in self.merged_data.iterrows():
            self.setupRow(i, row)
        print(f"Número total de colunas configuradas: {self.columnCount()}")

    def setupRow(self, i, row):
        self.setupCheckboxItem(i, row)
        self.setupIconItem(i, row)
        self.setupDataItems(i, row)

    def setupCheckboxItem(self, i, row):
        checkbox_item = CheckableItem()
        checkbox_item.setCheckable(True)
        checkbox_item.setEditable(False)
        checkbox_item.setCheckState(Qt.CheckState.Checked if row['Selecionado'] else Qt.CheckState.Unchecked)
        self.setItem(i, 1, checkbox_item)

    def setupIconItem(self, i, row):
        try:
            dias_value = int(row.get('Dias', 180))
        except ValueError:
            dias_value = 180
        icon_path = self.icons_dir / ("unchecked.png" if dias_value < 180 else "checked.png")
        icon_item = QStandardItem(QIcon(str(icon_path)), "")
        self.setItem(i, 0, icon_item)

    def setupDataItems(self, i, row):
        for j, col in enumerate(self.colunas, start=2):
            item_value = self.formatItemValue(row, col)
            item = QStandardItem(item_value)
            item.setEditable(False)
            self.setItem(i, j, item)
            self.applyColorLogic(item, col, row)

    def formatItemValue(self, row, col):
        if col == "Comprasnet":
            return str(row["Número do instrumento"])
        return str(row[col]) if col in row and pd.notnull(row[col]) else ""

    def applyColorLogic(self, item, col, row):
        if col != 'Dias':
            item.setForeground(QBrush(QColor(Qt.GlobalColor.white)))
            return
        num_value = int(row[col])
        if num_value < 60:
            item.setForeground(QColor(Qt.GlobalColor.red))
        elif 60 <= num_value <= 180:
            item.setForeground(QColor("orange"))
        else:
            item.setForeground(QColor(Qt.GlobalColor.green))

    def getRowDataAsDict(self, row):
        """Retorna os dados da linha especificada como um dicionário."""
        return self.merged_data.iloc[row].to_dict()
    
    def getDataFrame(self):
        return self.merged_data
    
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 1:
            item = self.itemFromIndex(index)
            if item is not None:
                # Certifique-se de que o valor é do tipo Qt.CheckState
                if isinstance(value, Qt.CheckState):
                    item.setCheckState(value)
                elif isinstance(value, int):  # Se por acaso um int for passado, converta corretamente
                    value = Qt.CheckState.Checked if value == 2 else Qt.CheckState.Unchecked
                    item.setCheckState(value)
                self.dataChanged.emit(index, index, [role])
                return True
        return False
    
class ControleContratosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)  # Layout principal do widget
        self.inicializarUI()

    def inicializarUI(self):
        # Instancia ContratosWidget
        self.contratos_widget = ContratosWidget(colunas=colunas)
        self.layout.addWidget(self.contratos_widget)

    def criar_widgets_processos(self):
        # Cria o container_frame com cor de fundo preta
        container_frame = QFrame()
        container_frame.setFrameShape(QFrame.Shape.StyledPanel)
        container_frame.setPalette(QPalette(QColor(240, 240, 240)))  

        # Define o tamanho mínimo para o container_frame
        container_frame.setMinimumSize(600, 600)

        # Cria um QGridLayout para o container_frame
        self.blocks_layout = QGridLayout(container_frame)
        self.blocks_layout.setSpacing(5)  # Define o espaçamento entre os widgets
        self.blocks_layout.setContentsMargins(5, 0, 5, 0)  # Remove as margens internas
        
        # Cria uma QScrollArea e define suas propriedades para o container_frame
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container_frame)
        
        # Adiciona a QScrollArea ao layout principal do widget
        self.layout.addWidget(scroll_area)

class CheckboxManager:
    def __init__(self, model):
        self.model = model

    def toggleAllCheckboxes(self, checked):
        checkState = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 1)
            if item.isCheckable():
                item.setCheckState(checkState)

class SearchManager:
    def __init__(self, proxyModel, searchField):
        self.proxyModel = proxyModel
        self.searchField = searchField
        self.searchField.textChanged.connect(self.applySearchFilter)

    def applySearchFilter(self):
        searchText = self.searchField.text()
        self.proxyModel.setFilterRegularExpression(searchText)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        regex = QRegularExpression(self.searchField.text(), QRegularExpression.CaseInsensitiveOption)
        model = self.proxyModel.sourceModel()
        columns = range(model.columnCount())
        for column in columns:
            index = model.index(sourceRow, column, sourceParent)
            data = model.data(index)
            if regex.match(data).hasMatch():
                return True
        return False

class CellBorderDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.column() not in [0, 1]:
            self.drawCellBorder(painter, option)

    def drawCellBorder(self, painter, option):
        """Desenha bordas laterais para células, exceto para as primeiras duas colunas."""
        painter.save()
        pen = QPen(Qt.GlobalColor.gray, 0.5, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawLine(option.rect.topLeft(), option.rect.bottomLeft())
        painter.drawLine(option.rect.topRight(), option.rect.bottomRight())
        painter.restore()
#painel_contratos.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
from controle_contratos.atualizar_dados_contratos import AtualizarDadosContratos
from controle_contratos.utils_contratos import *

class CheckboxManager:
    def __init__(self, model, proxyModel):
        self.model = model
        self.proxyModel = proxyModel

    def updateCheckboxState(self, sourceIndex, newState):
        checkState = Qt.CheckState.Checked if newState else Qt.CheckState.Unchecked
        # Passa o checkState para o modelo de dados
        self.model.setData(sourceIndex, checkState, Qt.ItemDataRole.CheckStateRole)

    def addCheckboxes(self):
        for row in range(self.model.rowCount()):
            checkbox_item = QStandardItem()
            checkbox_item.setCheckable(True)
            checkbox_item.setEditable(False)
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)  # Define um estado inicial claro
            self.model.setItem(row, 1, checkbox_item)

    def toggleAllCheckboxes(self, checked):
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 1)  # Assume que a coluna 1 tem os checkboxes
            if item.isCheckable():
                item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

class ContratosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.searchField = QLineEdit(self)
        self.searchField.setPlaceholderText("Buscar por nome da empresa ou outro dado...")
        self.layout.addWidget(self.searchField)

        # Configura o QTableView e carrega os dados
        self.table_view = QTableView(self)
        self.layout.addWidget(self.table_view)

        # Aplica o delegate personalizado ao QTreeView para desenhar bordas nas células
        self.table_view.setItemDelegate(CellBorderDelegate())

        # Ajuste o estilo do QTableView conforme necessário
        self.table_view.setStyleSheet("""
            QTableView {
                background-color: black;
                color: white;
            }
        """)

        # Layout para os botões
        self.buttons_layout = QHBoxLayout()

        # Botão "Gerar Tabela"
        self.gerar_tabela_btn = QPushButton("Gerar Tabela", self)
        self.buttons_layout.addWidget(self.gerar_tabela_btn)
        self.gerar_tabela_btn.clicked.connect(self.gerarTabelaExcel)

        # Botão "CP Alerta Prazo"
        self.alerta_prazo_btn = QPushButton("CP Alerta Prazo", self)
        self.buttons_layout.addWidget(self.alerta_prazo_btn)

        # Botão "Mensagem Cobrança"
        self.mensagem_cobranca_btn = QPushButton("Mensagem Cobrança", self)
        self.buttons_layout.addWidget(self.mensagem_cobranca_btn)

        # Botão "Gerar Termo de Subrogação"
        self.termo_subrogacao_btn = QPushButton("Termo de Subrogação", self)
        self.buttons_layout.addWidget(self.termo_subrogacao_btn)

        # Botão "Gerar Termo de Subrogação"
        self.termo_encerramento_btn = QPushButton("Termo de Encerramento", self)
        self.buttons_layout.addWidget(self.termo_encerramento_btn)

        # Botão "Editar Informações Adicionais"
        self.editar_adicionais_btn = QPushButton("Informações Adicionais", self)
        self.buttons_layout.addWidget(self.editar_adicionais_btn)
        self.editar_adicionais_btn.clicked.connect(self.abrirDialogoEditarInformacoesAdicionais)

        # Adiciona o layout dos botões ao layout principal
        self.layout.addLayout(self.buttons_layout)
        
        self.colunas = ['Comprasnet', 'Tipo', 'Processo', 'NUP', 'CNPJ', 'Fornecedor', 'Dias', 'Valor Global', 'Objeto', 'OM', 'Setor', 'CP', 'MSG'] # Na classe ContratosWidget, atualize a definição das colunas para incluir os novos cabeçalhos.
        self.colunas_internas = ['Vig. Início', 'Vig. Fim', 'Valor Formatado', 'Portaria', 'Gestor', 'Fiscal'] # Colunas adicionais para uso interno

        # Carrega os dados e configura o modelo
        contratos_data = load_data(CONTRATOS_PATH, ADICIONAIS_PATH)        
        self.model = CustomTableModel(contratos_data, self.colunas, ICONS_DIR)

        self.proxyModel = MultiColumnFilterProxyModel(self)
        self.proxyModel.setSourceModel(self.model)
        self.proxyModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxyModel.setDynamicSortFilter(True)
        self.table_view.setModel(self.proxyModel)
        
        self.checkboxManager = CheckboxManager(self.model, self.proxyModel)

        self.checkboxManager.addCheckboxes()
        
        # Agora que o modelo foi definido, ajuste a altura das linhas
        self.ajustarAlturaLinhasEConfiguracoes()

        self.searchField.textChanged.connect(self.onSearchTextChanged)
        # Adiciona uma barra de rolagem vertical
        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Configura a política de tamanho do widget para expandir horizontalmente
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.test_toggle_btn = QPushButton("Marcar/Desmarcar Todos", self)
        self.test_toggle_btn.clicked.connect(self.onTestToggleClicked)
        self.buttons_layout.addWidget(self.test_toggle_btn)

        # Botão de Configurações
        self.configuracoes_btn = QPushButton("Configurações", self)
        self.buttons_layout.addWidget(self.configuracoes_btn)
        self.configuracoes_btn.clicked.connect(self.abrirDialogoConfiguracoes)

        # Adicione o botão à sua GUI e conecte-o à função acima
        self.botao_print = QPushButton("Tirar Print", self)
        self.buttons_layout.addWidget(self.botao_print)
        self.botao_print.clicked.connect(self.tirarPrintDasLinhasSelecionadas)

        QTimer.singleShot(1, self.ajustarLarguraColunas)
        self.table_view.hideColumn(15)  # Oculta 'Valor Formatado'
        self.table_view.hideColumn(16)  # Oculta 'Portaria'
        self.table_view.hideColumn(17)  # Oculta 'Gestor'
        self.table_view.hideColumn(18)  # Oculta 'Fiscal'
        self.table_view.clicked.connect(self.onItemClicked)        

    def tirarPrintDasLinhasSelecionadas(self):
        dados_selecionados = []
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 1)  # Supondo que os checkboxes estejam na coluna 1
            if item.checkState() == Qt.CheckState.Checked:
                dados_linha = {}
                for col in range(self.model.columnCount()):
                    indice = self.model.index(row, col)
                    chave = self.model.headerData(col, Qt.Orientation.Horizontal)
                    valor = self.model.data(indice, Qt.ItemDataRole.DisplayRole)
                    dados_linha[chave] = valor
                dados_selecionados.append(dados_linha)
        
        # Aqui você pode imprimir, salvar ou fazer o que precisar com os dados_selecionados
        print(dados_selecionados)  # Exemplo de impressão na console
        
    def ajustarAlturaLinhasEConfiguracoes(self):
        # Define a altura fixa de todas as linhas
        altura_fixa = 20
        for linha in range(self.model.rowCount()):
            self.table_view.setRowHeight(linha, altura_fixa)

        # Desabilita o redimensionamento manual das linhas
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        self.table_view.verticalHeader().setDefaultSectionSize(altura_fixa)

    def gerarTabelaExcel(self):
        filteredData = getFilteredData(self.proxyModel)
        colunas = [self.model.headerData(i, Qt.Orientation.Horizontal) for i in range(self.model.columnCount())]
        saveFilteredDataToExcel(filteredData, colunas)

    def onSearchTextChanged(self, text):
        print(f"Buscando por: {text}")
        self.proxyModel.setFilterKeyColumn(self.colunas.index('Fornecedor'))  # Certifique-se de que este índice está correto.
        self.proxyModel.setFilterRegularExpression(QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption))

    def onSelectionChanged(self, selected, deselected):
        selected_rows = self.table_view.selectionModel().selectedRows()
        for index in selected_rows:
            # Aqui, você pode acessar os dados da linha selecionada diretamente do DataFrame
            row_data = self.model.dados.iloc[index.row()]
            # Agora, você pode armazenar 'row_data' onde precisar para uso posterior
            print(row_data)  # Exemplo de acesso aos dados

    def abrirDialogoEditarInformacoesAdicionais(self):
        contrato_atual = self.obterContratoAtual()
        if contrato_atual:
            self.dialogo = AtualizarDadosContratos(contrato_atual, self)
            self.dialogo.dadosContratosSalvos.connect(self.atualizarDadosTableView)
            if self.dialogo.exec() == QDialog.DialogCode.Accepted:
                pass  # O diálogo foi fechado com sucesso
        else:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um contrato para editar.")

    def atualizarDadosTableView(self):
        contratos_data = load_data(CONTRATOS_PATH, ADICIONAIS_PATH)  # Recarrega os dados
        self.model = CustomTableModel(contratos_data, self.colunas, ICONS_DIR)  # Cria um novo modelo com os dados atualizados
        self.table_view.setModel(self.model)  # Atualiza o modelo do QTreeView
        self.ajustarLarguraColunas()  # Ajusta a largura das colunas, se necessário

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

    def onItemClicked(self, index):
        # Mapeia o índice clicado para o índice no modelo de dados original, se estiver usando um proxy model
        sourceIndex = self.proxyModel.mapToSource(index) if hasattr(self, 'proxyModel') else index

        # Identifica a linha onde o clique ocorreu
        row = sourceIndex.row()

        # Verifica e alterna o estado do checkbox na coluna específica (assumindo que o checkbox está na coluna 1)
        checkboxIndex = self.model.index(row, 1)  # Assumindo que os checkboxes estão na coluna 1
        item = self.model.itemFromIndex(checkboxIndex)
        if item:
            # Alterna o estado do checkbox
            newState = not (item.checkState() == Qt.CheckState.Checked)
            item.setCheckState(Qt.CheckState.Checked if newState else Qt.CheckState.Unchecked)

        # Adicionalmente, atualiza a seleção da linha para refletir a seleção do usuário
        # Isso pode ser feito alterando a seleção no selection model do QTableView
        self.table_view.selectionModel().select(self.proxyModel.mapFromSource(checkboxIndex),
                                                QItemSelectionModel.SelectionFlag.Rows | QItemSelectionModel.SelectionFlag.Toggle)

    def updateCheckboxState(self, index, newState):
        checkState = Qt.CheckState.Checked if newState else Qt.CheckState.Unchecked
        self.model.setData(index, checkState, Qt.ItemDataRole.CheckStateRole)

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
                contrato_atual[chave] = valor

            print("Contrato Atual:", contrato_atual)
            return contrato_atual
        else:
            return None


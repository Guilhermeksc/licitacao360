from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import sqlite3
from diretorios import DATABASE_DIR, ICONS_DIR
import xlsxwriter
import os
from pathlib import Path

CONTROLE_LIMITE_DISPENSA_DIR = DATABASE_DIR / "controle_limite_dispensa"
ARQUIVO_DADOS_PDM_CATSER = CONTROLE_LIMITE_DISPENSA_DIR / 'dados_pdm.db'

class CustomDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Configuração das cores do texto para cada coluna
        text_colors = {
            0: QColor('lightgreen'),  # Verde claro para colunas 0 e 1
            1: QColor('lightgreen'),
            2: QColor('lightcoral'),  # Laranja claro para colunas 2 e 3
            3: QColor('lightcoral'),
            4: QColor('lightblue'),   # Azul claro para colunas 4 e 5
            5: QColor('lightblue'),
            6: QColor('white'),       # Branco para colunas 6 e 7
            7: QColor('white'),
        }

        # Define a cor do texto para o painter
        painter.setPen(QPen(text_colors.get(index.column(), QColor('black'))))

        # Desenha o texto manualmente
        painter.drawText(option.rect.adjusted(2, 0, 0, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, index.data())

        # Adiciona uma linha cinza claro na lateral direita das colunas especificadas
        if index.column() in [1, 3, 5]:
            pen = QPen(QColor('lightgray'), 1)  # Define a cor e espessura da linha
            painter.setPen(pen)
            painter.drawLine(option.rect.topRight() + QPoint(-1, 0), option.rect.bottomRight() + QPoint(-1, 0))

class Worker(QThread):
    filteredDataSignal = pyqtSignal(pd.DataFrame)

    def __init__(self, data, searchTerm):
        super(Worker, self).__init__()
        self._data = data
        self._searchTerm = searchTerm.strip().split()
        self.batch_size = 10000  # Reduzido para tornar o carregamento mais suave

    def run(self):
        filtered_batch = pd.DataFrame()
        if self._searchTerm:
            for start_row in range(0, len(self._data), self.batch_size):
                QThread.msleep(100)  # Dá um tempo entre os lotes
                end_row = min(start_row + self.batch_size, len(self._data))
                batch = self._data.iloc[start_row:end_row]
                # Filtragem incremental
                filtered_batch = batch[batch.apply(lambda row: all(any(word.lower() in str(cell).lower() for cell in row) for word in self._searchTerm), axis=1)]
                if not filtered_batch.empty:
                    self.filteredDataSignal.emit(filtered_batch)
        else:
            self.filteredDataSignal.emit(self._data)

class PandasModel(QAbstractTableModel):
    adjustColumns = pyqtSignal()

    def __init__(self, data):
        super(PandasModel, self).__init__()
        self._data = data  # Dados originais
        self._filtered_data = data  # Dados filtrados

    def rowCount(self, parent=None):
        return self._filtered_data.shape[0]

    def columnCount(self, parent=None):
        return self._filtered_data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role == Qt.ItemDataRole.DisplayRole:
            return str(self._filtered_data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._filtered_data.columns[section]
        return None

    def filterData(self, searchTerm):
        if searchTerm:
            # Filtra os dados com base no termo de pesquisa
            self._filtered_data = self._data[self._data.apply(lambda row: row.astype(str).str.contains(searchTerm, case=False).any(), axis=1)]
        else:
            # Se não houver termo de pesquisa, exibe todos os dados
            self._filtered_data = self._data
        self.layoutChanged.emit()

    def updateData(self, newData):
        self._filtered_data = newData
        self.layoutChanged.emit()
        # Emitir sinal para ajustar colunas
        self.adjustColumns.emit()
            
class ConsultaPDMCatser(QWidget):
    def __init__(self, icon_dir=None, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Campo de busca
        self.searchField = QLineEdit(self)
        self.searchField.setPlaceholderText("Digite para buscar...")
        self.searchField.returnPressed.connect(self.startSearch)  # Conectar ao pressionamento da tecla Enter
        
        # Botão de Pesquisa
        self.searchButton = QPushButton("Pesquisar", self)
        self.searchButton.clicked.connect(self.startSearch)  # Conectar ao clique do botão
        
        # Layout para o campo de busca e o botão
        self.searchLayout = QHBoxLayout()
        self.searchLayout.addWidget(self.searchField)
        self.searchLayout.addWidget(self.searchButton)

        self.tableView = QTableView(self)
        self.displayData()  # Garante que o modelo seja criado antes de tentar usá-lo
        
        self.tableView.setModel(self.model)  # Agora esta linha é segura para ser chamada
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableView.horizontalHeader().customContextMenuRequested.connect(self.onHeaderRightClick)

                # self.tableView.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.model.adjustColumns.connect(self.adjustColumnHeights)
        self.tableView.setStyleSheet("""
            QTableView {
                background-color: black;      
            }
        """)
        self.layout.addLayout(self.searchLayout)  # Adiciona o layout do campo de busca e botão ao layout principal
        self.layout.addWidget(self.tableView)
        self.setLayout(self.layout)

        self.tableView.doubleClicked.connect(self.on_double_click)

    def saveColumnVisibility(self):
        settings = QSettings('SuaEmpresa', 'SeuApp')
        for i in range(self.tableView.model().columnCount()):
            settings.setValue(f'columnVisibility/{i}', not self.tableView.isColumnHidden(i))

    def restoreColumnVisibility(self):
        settings = QSettings('SuaEmpresa', 'SeuApp')
        for i in range(self.tableView.model().columnCount()):
            visibility = settings.value(f'columnVisibility/{i}', 'true')  # 'true' é o valor padrão se a configuração não existir
            self.tableView.setColumnHidden(i, visibility == 'false')

    def onHeaderRightClick(self, position):
        menu = QMenu(self)
        for i in range(self.tableView.model().columnCount()):
            action = QAction(self.tableView.model().headerData(i, Qt.Orientation.Horizontal), self)
            action.setCheckable(True)
            action.setChecked(not self.tableView.isColumnHidden(i))
            
            # Modificação aqui: Adicionamos self.saveColumnVisibility() à função lambda
            action.triggered.connect(lambda checked, i=i: (self.tableView.setColumnHidden(i, not checked), self.saveColumnVisibility()))
            menu.addAction(action)
        
        menu.exec(self.tableView.horizontalHeader().mapToGlobal(position))

    def on_double_click(self, index):
        # Obtém os detalhes da linha clicada
        row = index.row()
        modelo = index.model()
        padrao_desc_material = modelo.data(modelo.index(row, 4), Qt.ItemDataRole.DisplayRole)
        unnamed_6 = modelo.data(modelo.index(row, 5), Qt.ItemDataRole.DisplayRole)
        codigo_material_servico = modelo.data(modelo.index(row, 6), Qt.ItemDataRole.DisplayRole)
        unnamed_8 = modelo.data(modelo.index(row, 7), Qt.ItemDataRole.DisplayRole)

        # Chama a função para abrir o popup com esses detalhes
        self.open_popup(padrao_desc_material, unnamed_6, codigo_material_servico, unnamed_8)

    def open_popup(self, padrao_desc_material, unnamed_6, codigo_material_servico, unnamed_8):
        # Verifica se já existe um dialog aberto, se não, cria um novo
        if not hasattr(self, 'itemsDialog'):
            self.itemsDialog = ItemsDialog(self)

        # Adiciona o item ao diálogo
        self.itemsDialog.add_item(padrao_desc_material, unnamed_6, codigo_material_servico, unnamed_8)

        # Garante que o diálogo esteja visível
        if not self.itemsDialog.isVisible():
            self.itemsDialog.show()
        else:
            # Se já estiver visível, traz para frente
            self.itemsDialog.raise_()

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        add_to_items_action = context_menu.addAction("Inserir na relação de itens")
        action = context_menu.exec(self.mapToGlobal(event.pos()))
        if action == add_to_items_action:
            self.migrateSelectedItemsToItemsDialog()

    def migrateSelectedItemsToItemsDialog(self):
        selected_indexes = self.tableView.selectionModel().selectedRows()
        for index in selected_indexes:
            # Substitua os argumentos abaixo pelos reais valores das colunas que você deseja passar
            padrao_desc_material = index.sibling(index.row(), 4).data()
            unnamed_6 = index.sibling(index.row(), 5).data()
            codigo_material_servico = index.sibling(index.row(), 6).data()
            unnamed_8 = index.sibling(index.row(), 7).data()
            self.open_popup(padrao_desc_material, unnamed_6, codigo_material_servico, unnamed_8)

    def adjustColumnHeights(self):
        for row in range(self.model.rowCount()):
            self.tableView.setRowHeight(row, self.calculateRowHeight(row))

    def calculateRowHeight(self, row):
        minHeight = 20  # Defina a altura mínima desejada
        # Aqui, você implementaria a lógica para calcular a altura baseada no conteúdo.
        # Este é um placeholder para demonstrar onde essa lógica seria colocada.
        return minHeight

    def updateModelData(self, filteredData):
        """
        Atualiza os dados do modelo com os resultados filtrados, anexando-os aos dados existentes.
        """
        if not hasattr(self, 'initialLoad') or self.initialLoad:
            self.model._filtered_data = filteredData
            self.initialLoad = False
        else:
            self.model._filtered_data = pd.concat([self.model._filtered_data, filteredData], ignore_index=True)
        
        self.model.layoutChanged.emit()
        self.adjustRowHeights()

    def adjustRowHeights(self):
        minHeight = 20  # Defina a altura mínima que deseja para as linhas
        for row in range(self.model.rowCount()):
            self.tableView.setRowHeight(row, minHeight)

        # QTimer.singleShot(1, self.adjustColumnSizes)  # Ajusta o tamanho das colunas após a atualização dos dados

    def displayData(self):
        conn = sqlite3.connect(str(ARQUIVO_DADOS_PDM_CATSER))
        query = """
        SELECT DISTINCT `Grupo Material`, `Unnamed: 2`, `Classe Material`, `Unnamed: 4`, `Padrão Desc Material`, `Unnamed: 6`, `Codigo Material Serviço`, `Unnamed: 8`
        FROM dados_pdm
        ORDER BY `Grupo Material`
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        df.columns = ['Grupo', 'Descrição Grupo', 'Classe', 'Descrição Classe', 'PDM', 'Descrição PDM', 'CATMAT', 'Descrição CATMAT']

        # Modelo é criado e configurado aqui
        self.model = PandasModel(df)
        self.tableView.setModel(self.model)  # Associa o modelo à tableView
        self.tableView.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        # Agora que o modelo está configurado, podemos definir o delegate para as colunas
        custom_delegate = CustomDelegate(self.tableView)
        for column in range(self.model.columnCount()):
            self.tableView.setItemDelegateForColumn(column, custom_delegate)  # Configura o delegate personalizado para todas as colunas

        # Ajustar o tamanho das colunas imediatamente após definir o modelo
        QTimer.singleShot(1, self.adjustColumnSizes)
        self.restoreColumnVisibility()

    def adjustColumnSizes(self):
        for column, width in [(0, 45), (1, 120), (2, 50), (3, 200), (4, 50), (5, 220), (6, 55), (7, 200)]:
            self.tableView.setColumnWidth(column, width)

    def startSearch(self):
        searchTerm = self.searchField.text()
        self.initialLoad = True  # Restaura o indicador de carga inicial
        if searchTerm:
            # Interrompe qualquer thread de filtragem que possa estar em execução
            if hasattr(self, '_worker'):
                self._worker.terminate()
            
            self._worker = Worker(self.model._data, searchTerm)
            self._worker.filteredDataSignal.connect(self.updateModelData)
            self._worker.start()

class ItemsDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Configuração das cores do texto para cada coluna
        text_colors = {
            0: QColor('lightblue'), 
            1: QColor('lightblue'),
            2: QColor('white'),  
            3: QColor('white')
        }

        # Define a cor do texto para o painter
        painter.setPen(QPen(text_colors.get(index.column(), QColor('black'))))

        # Desenha o texto manualmente
        painter.drawText(option.rect.adjusted(2, 0, 0, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, index.data())

        # Adiciona uma linha cinza claro na lateral direita apenas para a coluna 1
        if index.column() == 1:
            pen = QPen(QColor('lightgray'), 1)  # Define a cor e espessura da linha
            painter.setPen(pen)
            painter.drawLine(option.rect.topRight() + QPoint(-1, 0), option.rect.bottomRight() + QPoint(-1, 0))

class ItemsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relação de itens")

        # Definir tamanho inicial do diálogo
        self.resize(800, 500)
        self.setMaximumWidth(1200)
        # Layout principal do diálogo
        self.layout = QVBoxLayout(self)

        # Tabela para exibir os itens
        self.tableView = QTableView(self)
        self.layout.addWidget(self.tableView)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setStyleSheet("""
            QTableView {
                background-color: black;      
            }
        """)
        # Modelo para a tabela
        self.model = QStandardItemModel()
        self.tableView.setModel(self.model)

        # Configuração das colunas
        self.model.setColumnCount(4)
        self.model.setHorizontalHeaderLabels(["PDM", "Descrição PDM", "CATMAT", "Descrição CATMAT"])

        # Definindo tamanhos das colunas
        column_widths = [50, 180, 55, 400]
        for column, width in enumerate(column_widths):
            self.tableView.setColumnWidth(column, width)

        # Configurar o delegate para a tabela
        self.delegate = ItemsDelegate()
        self.tableView.setItemDelegate(self.delegate)

        # Contador de itens
        self.itemCountLabel = QLabel("Total de itens: 0")
        self.layout.addWidget(self.itemCountLabel)

        # Lista para manter os itens adicionados
        self.items = []

        # Botão para limpar os dados
        self.clearButton = QPushButton("Limpar Dados", self)
        self.clearButton.clicked.connect(self.clearData)
        self.layout.addWidget(self.clearButton)

        # Botão para gerar a tabela
        self.generateTableButton = QPushButton("Gerar Tabela", self)
        self.generateTableButton.clicked.connect(self.generateTable)
        self.layout.addWidget(self.generateTableButton)

    def add_item(self, padrao_desc_material, unnamed_6, codigo_material_servico, unnamed_8):
        # Adiciona o item à lista
        item = [padrao_desc_material, unnamed_6, codigo_material_servico, unnamed_8]
        self.items.append(item)

        # Atualiza o modelo da tabela
        row = len(self.items) - 1
        for column, value in enumerate(item):
            item = QStandardItem(str(value))
            # Configura a quebra de texto para a célula individual
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)  # Desativa a edição de células
            self.model.setItem(row, column, item)

        # Atualiza o contador de itens
        self.itemCountLabel.setText(f"Total de itens: {len(self.items)}")
    def clearData(self):
        # Limpa os dados da tabela
        self.model.clear()  # Remove todos os itens
        self.model.setColumnCount(4)  # Restaura o número de colunas
        self.model.setHorizontalHeaderLabels(["PDM", "Descrição PDM", "CATMAT", "Descrição CATMAT"])  # Restaura os cabeçalhos das colunas
        self.items.clear()  # Limpa a lista de itens
        self.itemCountLabel.setText("Total de itens: 0")  # Reseta o contador de itens

    def generateTable(self):
        # Define o caminho na pasta Documentos do usuário
        documents_path = Path.home() / "Documents"
        reports_path = documents_path / "relatorio_automatizado"
        # Verifica se a pasta "relatorio_automatizado" existe, se não, cria
        reports_path.mkdir(exist_ok=True)

        # Define o nome do arquivo dentro da pasta especificada
        filename = reports_path / "relacao_ordenada.xlsx"

        # Cria o arquivo xlsx
        workbook = xlsxwriter.Workbook(str(filename))
        worksheet = workbook.add_worksheet()

        # Escreve o cabeçalho
        for col_num in range(self.model.columnCount()):
            # Obtém o rótulo do cabeçalho para cada coluna
            header = self.model.headerData(col_num, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            worksheet.write(0, col_num, header)

        # Escreve os dados da tabela
        for row in range(self.model.rowCount()):
            for col in range(self.model.columnCount()):
                item = self.model.item(row, col)
                if item is not None:
                    worksheet.write(row + 1, col, item.text())

        workbook.close()  # Fecha o arquivo

        # Abre o arquivo xlsx criado
        os.startfile(str(filename))
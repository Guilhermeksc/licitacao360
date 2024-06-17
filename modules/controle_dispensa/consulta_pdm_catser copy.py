from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import sqlite3
from diretorios import DATABASE_DIR, ICONS_DIR
from pathlib import Path
import os

CONTROLE_LIMITE_DISPENSA_DIR = DATABASE_DIR / "controle_limite_dispensa"
ARQUIVO_DADOS_PDM_CATSER = CONTROLE_LIMITE_DISPENSA_DIR / 'dados_pdm.db'

class Worker(QThread):
    # Sinal para enviar os dados filtrados de volta
    filteredDataSignal = pyqtSignal(pd.DataFrame)

    def __init__(self, data, searchTerm):
        super(Worker, self).__init__()
        self._data = data
        self._searchTerm = searchTerm.strip().split()  # Divide o termo de busca em palavras
        self.batch_size = 10000  # Define o tamanho do lote

    def run(self):
        if self._searchTerm:
            for start_row in range(0, len(self._data), self.batch_size):
                end_row = min(start_row + self.batch_size, len(self._data))
                batch = self._data.iloc[start_row:end_row]
                
                # Filtragem para linhas que contêm todas as palavras do termo de busca
                filtered_batch = batch[batch.apply(lambda row: all(any(word.lower() in str(cell).lower() for cell in row) for word in self._searchTerm), axis=1)]
                
                if not filtered_batch.empty:
                    self.filteredDataSignal.emit(filtered_batch)
                    QThread.msleep(100)  # Dá um tempo para a UI processar os dados e permanecer responsiva
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
        self.tableView.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.tableView.setStyleSheet("""
            QTableView {
                background-color: black;
                color: white;            
            }
        """)
        self.layout.addLayout(self.searchLayout)  # Adiciona o layout do campo de busca e botão ao layout principal
        self.layout.addWidget(self.tableView)
        self.setLayout(self.layout)

    def updateModelData(self, filteredData):
        """
        Atualiza os dados do modelo com os resultados filtrados, anexando-os aos dados existentes.
        """
        if not hasattr(self, 'initialLoad') or self.initialLoad:
            self.model._filtered_data = filteredData
            self.initialLoad = False
        else:
            # Anexa novos dados aos dados existentes
            self.model._filtered_data = pd.concat([self.model._filtered_data, filteredData], ignore_index=True)
        
        self.model._filtered_data = filteredData
        self.model.layoutChanged.emit()

        # Ajusta o tamanho das colunas para se adequarem ao conteúdo
        self.tableView.resizeColumnsToContents()
        QTimer.singleShot(1, self.resizeColumnsToContents)
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
        self.tableView.setModel(self.model)
        # Conectar o sinal para ajustar colunas após a atualização dos dados
        self.model.adjustColumns.connect(self.adjustColumnSizes)

        # Ajustar o tamanho das colunas imediatamente após definir o modelo
        self.adjustColumnSizes()

    def adjustColumnSizes(self):
        for column, width in [(0, 50), (1, 200), (2, 50), (3, 200), (4, 50), (5, 200), (6, 50), (7, 200), (8, 200)]:
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
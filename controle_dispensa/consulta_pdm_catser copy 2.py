
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import sqlite3
from diretorios import DATABASE_DIR, ICONS_DIR
from pathlib import Path
import sys

CONTROLE_LIMITE_DISPENSA_DIR = DATABASE_DIR / "controle_limite_dispensa"
ARQUIVO_DADOS_PDM_CATSER = CONTROLE_LIMITE_DISPENSA_DIR / 'dados_pdm.db'

class PDMCatserModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data[0]) if self._data else 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return ["Grupo Material", "Unnamed: 2", "Classe Material", "Unnamed: 4",
                        "Padrão Desc Material", "Unnamed: 6", "Codigo Material Serviço", "Unnamed: 8"][section]
        return None

class ConsultaPDMCatser(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)  # Passa o widget pai para o construtor da classe base
        self.setWindowTitle('Consulta PDM Catser')
        self.layout = QVBoxLayout()
        self.tableView = QTableView()
        self.layout.addWidget(self.tableView)
        self.setLayout(self.layout)
        self.initializeUI()

    def initializeUI(self):
        data = self.loadData()
        model = PDMCatserModel(data)
        self.tableView.setModel(model)
        
        QTimer.singleShot(1, self.setTableviewColumnWidth)
        
    def loadData(self):
        conn = sqlite3.connect(str(ARQUIVO_DADOS_PDM_CATSER))
        query = """
        SELECT DISTINCT `Grupo Material`, `Unnamed: 2`, `Classe Material`, `Unnamed: 4`, 
        `Padrão Desc Material`, `Unnamed: 6`, `Codigo Material Serviço`, `Unnamed: 8`
        FROM dados_pdm
        ORDER BY `Grupo Material`
        """
        result = conn.execute(query).fetchall()
        conn.close()
        return result

    def setTableviewColumnWidth(self):
        for i, width in enumerate([50, 200, 50, 200, 50, 200, 50, 200]):
            self.tableView.setColumnWidth(i, width)
        self.tableView.update()  # Esta chamada pode permanecer para garantir a atualização da interface
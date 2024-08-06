from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_pregao
from modules.contratos.utils import WidgetHelper
from diretorios import *
from datetime import datetime
import sqlite3
import pandas as pd

class AddItemDialog(QDialog):
    itemAdded = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Novo Item")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        self.layout = QVBoxLayout()
        
        self.numero_contrato_layout, self.numero_contrato_edit = WidgetHelper.create_line_edit("Número do Contrato")
        self.nup_layout, self.nup_edit = WidgetHelper.create_line_edit("NUP")
        self.valor_global_layout, self.valor_global_edit = WidgetHelper.create_line_edit("Valor Global")
        
        self.layout.addLayout(self.numero_contrato_layout)
        self.layout.addLayout(self.nup_layout)
        self.layout.addLayout(self.valor_global_layout)
        
        self.save_button = QPushButton("Salvar")
        self.cancel_button = QPushButton("Cancelar")
        
        self.save_button.clicked.connect(self.save_item)
        self.cancel_button.clicked.connect(self.reject)
        
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        
        self.layout.addLayout(self.button_layout)
        
        self.setLayout(self.layout)

    def save_item(self):
        item_data = {
            "numero_contrato": self.numero_contrato_edit.text(),
            "nup": self.nup_edit.text(),
            "valor_global": self.valor_global_edit.text()
        }
        
        # Emitir sinal com os dados do item
        self.itemAdded.emit(item_data)
        self.accept()

    def get_data(self):
        return {
            "numero_contrato": self.numero_contrato_edit.text(),
            "nup": self.nup_edit.text(),
            "valor_global": self.valor_global_edit.text()
        }
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import pandas as pd
import re
from pathlib import Path
from datetime import datetime, timedelta
from styles.styless import get_transparent_title_style
from diretorios import *

class ContratosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Configura o QTreeView e carrega os dados
        self.tree_view = QTreeView(self)
        self.layout.addWidget(self.tree_view)
        
        # Layout para os botões
        self.buttons_layout = QHBoxLayout()

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

        # Adiciona o layout dos botões ao layout principal
        self.layout.addLayout(self.buttons_layout)

        # Na classe ContratosWidget, atualize a definição das colunas para incluir os novos cabeçalhos.
        self.colunas = ['Comprasnet', 'Tipo', 'Processo', 'NUP', 'CNPJ', 'Fornecedor', 'Dias', 'Valor Global', 'Objeto', 'OM', 'Setor']

        # Colunas adicionais para uso interno
        self.colunas_internas = ['Vig. Início', 'Vig. Fim', 'Valor Formatado', 'Portaria', 'Gestor', 'Fiscal']

        contratos_data = load_data(CONTRATOS_PATH)
        model = CustomTableModel(contratos_data, self.colunas)
        self.tree_view.setModel(model)

        # Adiciona uma barra de rolagem vertical
        self.tree_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

class CustomTableModel(QStandardItemModel):
    def __init__(self, dados, colunas, colunas_internas=None, parent=None):
        super(CustomTableModel, self).__init__(parent)
        self.dados = dados
        self.colunas = colunas
        self.colunas_internas = colunas_internas if colunas_internas is not None else []
        self.setupModel()

    def setupModel(self):
        self.setHorizontalHeaderLabels(self.colunas)
        for i, row in self.dados.iterrows():
            # Add a checkbox item
            checkbox_item = QStandardItem()
            checkbox_item.setCheckable(True)
            checkbox_item.setEditable(False)
            self.setItem(i, 0, checkbox_item)
            
            # Now start populating from the second column onwards
            for j, col in enumerate(self.colunas[1:] + self.colunas_internas):  # Adjust the index by adding 1
                item = QStandardItem(str(row[col]) if col in row and pd.notnull(row[col]) else "")
                item.setEditable(False)  # Assuming you don't want the items to be editable
                self.setItem(i, j + 1, item)  # Adjust the index by adding 1 since the first column is for checkbox

def load_data(csv_path):
    data = pd.read_csv(csv_path)
    for index, row in data.iterrows():
        fornecedor = row['Fornecedor']
        match = re.search(r'/\d{4}-\d{2}', fornecedor)
        if match:
            posicao_hifen = match.end()
            row['CNPJ'] = fornecedor[:posicao_hifen].strip()
            row['Fornecedor'] = fornecedor[posicao_hifen + 1:].lstrip(" -")
        else:
            row['CNPJ'] = ""
            row['Fornecedor'] = ""
    return data


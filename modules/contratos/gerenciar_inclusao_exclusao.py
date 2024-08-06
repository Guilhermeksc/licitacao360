from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.contratos.utils import WidgetHelper, Dialogs
from diretorios import *
from datetime import datetime
import sqlite3
import pandas as pd
import logging
from modules.contratos.database_manager import DatabaseContratosManager, SqlModel

class GerenciarInclusaoExclusaoContratos(QDialog):
    def __init__(self, database_path, parent=None):
        super().__init__(parent)
        self.database_path = database_path
        self.setWindowTitle("Gerenciar Inclusão/Exclusão de Contratos")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)

        self.table_view = QTableView(self)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.layout.addWidget(self.table_view)

        self.database_manager = DatabaseContratosManager(self.database_path)
        self.model = self.init_model()
        self.table_view.setModel(self.model)
        
        self.load_data()

        form_layout = QFormLayout()
        self.contrato_ata_input = QLineEdit(self)
        self.empresa_input = QLineEdit(self)
        self.objeto_input = QLineEdit(self)
        self.valor_input = QLineEdit(self)
        
        form_layout.addRow("Contrato/Ata:", self.contrato_ata_input)
        form_layout.addRow("Empresa:", self.empresa_input)
        form_layout.addRow("Objeto:", self.objeto_input)
        form_layout.addRow("Valor:", self.valor_input)

        self.layout.addLayout(form_layout)

        button_layout = QHBoxLayout()

        self.incluir_button = QPushButton("Incluir", self)
        self.incluir_button.clicked.connect(self.incluir_item)
        button_layout.addWidget(self.incluir_button)

        self.excluir_button = QPushButton("Excluir", self)
        self.excluir_button.clicked.connect(self.excluir_item)
        button_layout.addWidget(self.excluir_button)

        self.salvar_button = QPushButton("Salvar", self)
        self.salvar_button.clicked.connect(self.salvar_alteracoes)
        button_layout.addWidget(self.salvar_button)

        self.layout.addLayout(button_layout)

    def init_model(self):
        sql_model = SqlModel(self.database_manager, self)
        model = sql_model.setup_model("controle_contratos", editable=True)
        return model

    def hide_unwanted_columns(self):
        visible_columns = {4, 7, 8, 9}
        for column in range(self.model.columnCount()):
            if column not in visible_columns:
                self.table_view.hideColumn(column)

    def load_data(self):
        try:
            conn = self.database_manager.connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM controle_contratos")
            results = cursor.fetchall()

            # Inserir os dados no modelo
            self.model.removeRows(0, self.model.rowCount())
            for row_data in results:
                row = self.model.record()
                row.setValue(4, row_data[4])
                row.setValue(7, row_data[7])
                row.setValue(8, row_data[8])
                row.setValue(9, row_data[9])
                self.model.insertRecord(-1, row)

            # Ajustar o redimensionamento das colunas
            self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.hide_unwanted_columns()

        except Exception as e:
            logging.error("Erro ao carregar dados do banco de dados: %s", e)
            Dialogs.warning(self, "Erro", f"Erro ao carregar dados do banco de dados: {e}")
        finally:
            self.database_manager.close_connection()

    def adicionar_linha_na_tabela(self, contrato, empresa, objeto, valor):
        if not contrato or not empresa or not objeto or not valor:
            Dialogs.warning(self, "Erro", "Todos os campos devem ser preenchidos.")
            return

        row = self.model.record()
        row.setValue("numero_contrato", contrato)
        row.setValue("empresa", empresa)
        row.setValue("objeto", objeto)
        row.setValue("valor_global", valor)

        if not self.model.insertRecord(-1, row):
            print("Erro ao inserir a linha no modelo:", self.model.lastError().text())
        else:
            print("Linha inserida com sucesso no modelo")

    def incluir_item(self):
        numero_contrato = self.contrato_ata_input.text()
        empresa = self.empresa_input.text()
        objeto = self.objeto_input.text()
        valor_global = self.valor_input.text()

        if numero_contrato and empresa and objeto and valor_global:
            self.adicionar_linha_na_tabela(numero_contrato, empresa, objeto, valor_global)
        else:
            Dialogs.warning(self, "Erro", "Todos os campos devem ser preenchidos para incluir um item.")

    def excluir_item(self):
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            Dialogs.warning(self, "Erro", "Nenhum item selecionado para excluir.")
            return
        for index in selected_indexes:
            self.model.removeRow(index.row())

    def salvar_alteracoes(self):
        try:
            conn = self.database_manager.connect_to_database()
            cursor = conn.cursor()

            data_to_save = []
            for row in range(self.model.rowCount()):
                record = self.model.record(row)
                numero_contrato = record.value("numero_contrato")
                empresa = record.value("empresa")
                objeto = record.value("objeto")
                valor_global = record.value("valor_global")

                if not numero_contrato or not empresa or not objeto or not valor_global:
                    logging.warning("Dados incompletos: contrato=%s, empresa=%s, objeto=%s, valor=%s",
                                    numero_contrato, empresa, objeto, valor_global)
                    continue

                data_to_save.append((numero_contrato, empresa, objeto, valor_global))

            cursor.execute("DELETE FROM controle_contratos")
            conn.commit()

            cursor.executemany(
                "INSERT INTO controle_contratos (numero_contrato, empresa, objeto, valor_global) VALUES (?, ?, ?, ?)",
                data_to_save
            )
            conn.commit()
            Dialogs.info(self, "Sucesso", "Alterações salvas com sucesso.")
        except Exception as e:
            logging.error("Erro ao salvar alterações no banco de dados: %s", e)
            Dialogs.warning(self, "Erro", f"Erro ao salvar alterações no banco de dados: {e}")
        finally:
            self.database_manager.close_connection()

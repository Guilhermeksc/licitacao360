from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import sqlite3
from pathlib import Path
import pandas as pd
import os

class ConfiguracoesDispensaDialog(QDialog):
    config_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.database_path = parent.database_path if parent else None
        self.setWindowTitle("Alterar Agentes Responsáveis")
        self.setStyleSheet("background-color: #050f41; color: white;")
        self.setFixedSize(1100, 600)
        self.layout = QVBoxLayout(self)

        header_widget = self.update_title_label_config()
        self.layout.addWidget(header_widget)
        self.initialize_ui()

    def update_title_label_config(self):
        html_text = (
            "Alterar Agentes Responsáveis<br>"
        )
        if not hasattr(self, 'titleLabel'):
            self.titleLabel = QLabel()
            self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
            self.titleLabel.setStyleSheet("color: white; font-size: 30px; font-weight: bold;")

        self.titleLabel.setText(html_text)

        if not hasattr(self, 'header_layout'):
            self.header_layout = QHBoxLayout()
            self.header_layout.addWidget(self.titleLabel)
            self.header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            pixmap = QPixmap(str(MARINHA_PATH)).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label = QLabel()
            self.image_label.setPixmap(pixmap)
            self.header_layout.addWidget(self.image_label)

            header_widget = QWidget()
            header_widget.setLayout(self.header_layout)
            header_widget.setFixedHeight(100)
            self.header_widget_config = header_widget

        return self.header_widget_config

    def initialize_ui(self):
        self.table_view = QTableView()
        self.table_view.setFont(QFont('Arial', 12))  # Aumenta o tamanho da fonte geral para 12
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Definindo o estilo da linha selecionada
        self.table_view.setStyleSheet("""
            QTableView::item:selected {
                background-color: #2a82da;  
                color: white; 
            }
        """)

        self.carregarAgentesResponsaveis()
        self.layout.addWidget(self.table_view)

        add_button = QPushButton("Adicionar")
        add_button.clicked.connect(self.adicionarAgente)
        gerar_Tabela_button = QPushButton("Gerar Tabela")
        gerar_Tabela_button.clicked.connect(self.gerarTabela)
        importar_tabela_button = QPushButton("Importar Tabela")
        importar_tabela_button.clicked.connect(self.importarTabela)
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.save_and_emit)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(gerar_Tabela_button)
        button_layout.addWidget(importar_tabela_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        self.layout.addLayout(button_layout)
        self.table_view.installEventFilter(self)  # Instalar filtro de evento para capturar a tecla 'Del'

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Delete:
            print("Tecla 'Delete' pressionada")
            self.excluirAgente()
        return super().eventFilter(source, event)

    def gerarTabela(self):
        try:
            # Conectar ao banco de dados
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nome, posto, funcao FROM controle_agentes_responsaveis")
                data = cursor.fetchall()
            
            # Converter os dados para um DataFrame do pandas
            df = pd.DataFrame(data, columns=["Nome", "Posto", "Função"])
            
            # Definir o caminho para salvar a planilha Excel
            excel_path = Path("controle_agentes_responsaveis.xlsx")
            
            # Salvar o DataFrame como um arquivo Excel usando pandas
            df.to_excel(excel_path, index=False)
            
            # Ajustar o tamanho das colunas usando openpyxl
            from openpyxl import load_workbook
            wb = load_workbook(excel_path)
            ws = wb.active

            # Ajustar o tamanho das colunas
            column_widths = {"A": 45, "B": 30, "C": 35}
            for col, width in column_widths.items():
                ws.column_dimensions[col].width = width

            # Salvar as alterações no arquivo Excel
            wb.save(excel_path)
            
            # Abrir o arquivo Excel criado
            os.startfile(excel_path)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar a tabela: {e}")

    def importarTabela(self):
        try:
            # Abrir o diálogo para selecionar o arquivo Excel
            file_dialog = QFileDialog()
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            file_dialog.setNameFilter("Arquivos Excel (*.xlsx)")
            if file_dialog.exec():
                file_path = file_dialog.selectedFiles()[0]

                # Ler o arquivo Excel usando pandas
                df = pd.read_excel(file_path)

                # Verificar se as colunas necessárias estão presentes
                required_columns = ["Nome", "Posto", "Função"]
                if not all(column in df.columns for column in required_columns):
                    raise Exception("O arquivo Excel deve conter as colunas: Nome, Posto, Função")

                # Conectar ao banco de dados
                with sqlite3.connect(self.database_path) as conn:
                    cursor = conn.cursor()
                    
                    # Deletar os valores existentes
                    cursor.execute("DELETE FROM controle_agentes_responsaveis")
                    
                    # Inserir os novos valores
                    for _, row in df.iterrows():
                        cursor.execute("INSERT INTO controle_agentes_responsaveis (nome, posto, funcao) VALUES (?, ?, ?)",
                                    (row["Nome"], row["Posto"], row["Função"]))
                    
                    conn.commit()

                # Recarregar a tabela na interface
                self.carregarAgentesResponsaveis()
                QMessageBox.information(self, "Sucesso", "Tabela importada com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar a tabela: {e}")

    def save_and_emit(self):
        print("Salvando configurações e emitindo sinal...")
        self.accept()
        self.config_updated.emit()

    def carregarAgentesResponsaveis(self):
        try:
            print("Tentando conectar ao banco de dados...")
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_agentes_responsaveis'")
                if cursor.fetchone() is None:
                    raise Exception("A tabela 'controle_agentes_responsaveis' não existe no banco de dados. Configure os Ordenadores de Despesa no Módulo 'Configurações'.")

                sql_query_agentes_responsaveis = "SELECT nome, posto, funcao FROM controle_agentes_responsaveis"
                cursor.execute(sql_query_agentes_responsaveis)
                agentes_responsaveis = cursor.fetchall()
                
                if agentes_responsaveis:
                    agentes_responsaveis = [list(row) for row in agentes_responsaveis]  # Converte tuplas em listas
                    self.table_model = AgentesResponsaveisTableModel(agentes_responsaveis, self.database_path)
                    self.table_view.setModel(self.table_model)
                    self.table_view.setItemDelegateForColumn(1, ComboBoxDelegate([
                        "Capitão de Mar e Guerra (IM)", "Capitão de Fragata (IM)", "Capitão de Corveta (IM)", 
                        "Capitão-Tenente (IM)", "Primeiro-Tenente (IM)", "Primeiro-Tenente (Rm2-T)", 
                        "Segundo-Tenente (IM)", "Segundo-Tenente (Rm2-T)"
                    ], self.table_view))
                    self.table_view.setItemDelegateForColumn(2, ComboBoxDelegate([
                        "Ordenador de Despesa", "Ordenador de Despesa Substituto", "Agente Fiscal", 
                        "Agente Fiscal Substituto", "Gerente de Crédito", "Operador de Dispensa Eletrônica",
                        "Responsável pela Demanda", "Encarregado da Divisão de x"
                    ], self.table_view))
                    self.table_view.setColumnWidth(0, 400)  # Define o tamanho da coluna do índice 0
                    self.table_view.setColumnWidth(1, 300)  # Define o tamanho da coluna do índice 1
                    self.table_view.setColumnWidth(2, 300)  # Define o tamanho da coluna do índice 2
                else:
                    QMessageBox.information(self, "Informação", "Nenhum agente responsável encontrado.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def adicionarAgente(self):
        self.table_model.addRow()

    def excluirAgente(self):
        selected_indexes = self.table_view.selectionModel().selectedRows()
        print(f"Índices selecionados: {selected_indexes}")  # Print para verificar os índices selecionados
        if selected_indexes:
            for index in sorted(selected_indexes, reverse=True):
                print(f"Excluindo linha: {index.row()}")  # Print para verificar a linha sendo excluída
                self.table_model.removeRow(index.row())
        else:
            print("Nenhuma linha selecionada")
            QMessageBox.information(self, "Informação", "Nenhuma linha selecionada.")

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, options, parent=None):
        super().__init__(parent)
        self.options = options

    def createEditor(self, parent, option, index):
        combo_box = QComboBox(parent)
        combo_box.setEditable(True)
        combo_box.addItems(self.options)
        combo_box.setFont(QFont('Arial', 12))
        
        # Definir um QListView para o QComboBox para controlar o estilo dos itens da lista
        list_view = QListView()
        list_view.setFont(QFont('Arial', 12))
        combo_box.setView(list_view)

        combo_box.setStyleSheet("""
            QComboBox QAbstractItemView {
                background-color: #2a82da;
                color: white;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox QAbstractItemView::item {
                color: black;
            }
            QComboBox::item:selected {
                background-color: #2a82da;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #050f41;
                color: white;
            }
            QLineEdit {
                background-color: #2a82da;
                color: white;
            }
        """)


        # Definir a fonte do line_edit diretamente
        line_edit = combo_box.lineEdit()
        line_edit.setFont(QFont('Arial', 12))

        return combo_box

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        if value:
            editor.setCurrentText(value)  # Chame setCurrentText no QComboBox

    def setModelData(self, editor, model, index):
        value = editor.currentText()  # Obtenha o texto atual do QComboBox
        model.setData(index, value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class AgentesResponsaveisTableModel(QAbstractTableModel):
    def __init__(self, data, database_path):
        super().__init__()
        self._data = data
        self._headers = ["Nome", "Posto", "Função"]
        self.database_path = database_path

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._headers)

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return self._data[index.row()][index.column()]

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
            if orientation == Qt.Orientation.Vertical:
                return section + 1

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            self._data[index.row()][index.column()] = value
            self.updateDatabase(index.row(), index.column(), value)
            self.dataChanged.emit(index, index, (Qt.ItemDataRole.EditRole,))
            return True
        return False

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def updateDatabase(self, row, column, value):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                headers = ['nome', 'posto', 'funcao']
                query = f"UPDATE controle_agentes_responsaveis SET {headers[column]} = ? WHERE rowid = ?"
                cursor.execute(query, (value, row + 1))  # rowid é 1-indexado
                conn.commit()
        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Erro ao atualizar o banco de dados: {e}")

    def addRow(self):
        self.beginInsertRows(QModelIndex(), self.rowCount(None), self.rowCount(None))
        self._data.append(["", "", ""])  # Adiciona uma linha vazia
        self.endInsertRows()

        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO controle_agentes_responsaveis (nome, posto, funcao) VALUES (?, ?, ?)", ("", "", ""))
                conn.commit()
        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Erro ao adicionar ao banco de dados: {e}")

    def removeRow(self, row, parent=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), row, row)
        self._data.pop(row)
        self.endRemoveRows()

        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM controle_agentes_responsaveis WHERE rowid = ?", (row + 1,))
                conn.commit()
        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Erro ao remover do banco de dados: {e}")
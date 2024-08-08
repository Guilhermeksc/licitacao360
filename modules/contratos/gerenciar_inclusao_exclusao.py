from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.contratos.utils import WidgetHelper, Dialogs
from diretorios import *
from datetime import datetime
import sqlite3
import pandas as pd
import os
import logging
from modules.contratos.database_manager import DatabaseContratosManager, SqlModel

class GerenciarInclusaoExclusaoContratos(QDialog):
    def __init__(self, icons_dir, database_path, parent=None):
        super().__init__(parent)
        self.icons_dir = icons_dir
        self.database_path = database_path
        self.setWindowTitle("Gerenciar Inclusão/Exclusão de Contratos")
        self.resize(800, 600)
        
        self.database_manager = DatabaseContratosManager(self.database_path)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        # Adicionando o layout horizontal para a barra de busca e o label
        search_layout = QHBoxLayout()
        
        self.search_label = QLabel("Localizar:", self)
        search_layout.addWidget(self.search_label)

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Buscar...")
        self.search_bar.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_bar)

        self.layout.addLayout(search_layout)

        self.table_view = QTableView(self)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.layout.addWidget(self.table_view)

        self.model = self.init_model()
        self.table_view.setModel(self.model)

        # Verificações de contagem de linhas
        model_row_count = self.model.rowCount()
        table_view_row_count = self.table_view.model().rowCount()
        print(f"Quantidade de linhas no model: {model_row_count}")
        print(f"Quantidade de linhas no table_view: {table_view_row_count}")

        form_layout = self.create_form_layout()
        self.layout.addLayout(form_layout)

        button_layout = self.create_button_layout()
        self.layout.addLayout(button_layout)
        
        # Adicionando o botão para gerar a tabela
        self.generate_table_button = QPushButton("Gerar Tabela", self)
        self.generate_table_button.clicked.connect(self.gerar_tabela)
        self.layout.addWidget(self.generate_table_button)

    def gerar_tabela(self):
        try:
            # Contar a quantidade de linhas no table_view (visíveis e invisíveis)
            table_view_row_count = self.model.rowCount()

            # Cria um DataFrame com os dados do modelo, incluindo linhas ocultas
            data = []
            for row in range(table_view_row_count):
                row_data = []
                for column in range(self.model.columnCount()):
                    item = self.model.index(row, column).data()
                    row_data.append(item)
                data.append(row_data)

            headers = [self.model.headerData(column, Qt.Orientation.Horizontal) for column in range(self.model.columnCount())]
            df = pd.DataFrame(data, columns=headers)

            # Contar a quantidade de linhas na tabela gerada
            generated_table_row_count = len(df)

            # Printar as quantidades de linhas
            print(f"Quantidade de linhas no table_view: {table_view_row_count}")
            print(f"Quantidade de linhas na tabela gerada: {generated_table_row_count}")

            # Define o caminho do arquivo Excel
            file_path = os.path.join(os.path.expanduser("~"), "tabela_dados.xlsx")

            # Salva o DataFrame em um arquivo Excel
            df.to_excel(file_path, index=False)

            # Abre o arquivo Excel
            os.startfile(file_path)
        except Exception as e:
            logging.error("Erro ao gerar a tabela Excel: %s", e)
            Dialogs.warning(self, "Erro", f"Erro ao gerar a tabela Excel: {e}")


    def filter_table(self, text):
        for row in range(self.model.rowCount()):
            match = False
            for column in range(self.model.columnCount()):
                item = self.model.index(row, column).data()
                if text.lower() in str(item).lower():
                    match = True
                    break
            self.table_view.setRowHidden(row, not match)

    def create_form_layout(self):
        form_layout = QFormLayout()
        self.contrato_ata_input = QLineEdit(self)
        self.empresa_input = QLineEdit(self)
        self.objeto_input = QLineEdit(self)
        self.valor_input = QLineEdit(self)

        form_layout.addRow("Contrato/Ata:", self.contrato_ata_input)
        form_layout.addRow("Empresa:", self.empresa_input)
        form_layout.addRow("Objeto:", self.objeto_input)
        form_layout.addRow("Valor:", self.valor_input)
        return form_layout

    def create_button_layout(self):
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

        self.excluir_database_button = QPushButton("Excluir Database", self)
        self.excluir_database_button.clicked.connect(self.excluir_database)
        button_layout.addWidget(self.excluir_database_button)

        self.carregar_tabela_button = QPushButton("Carregar Tabela", self)
        self.carregar_tabela_button.clicked.connect(self.carregar_tabela)
        button_layout.addWidget(self.carregar_tabela_button)

        return button_layout

    def init_model(self):
        sql_model = SqlModel(self.icons_dir, self.database_manager, self)
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

            self.model.removeRows(0, self.model.rowCount())
            for row_data in results:
                row = self.model.record()
                row.setValue(4, row_data[4])
                row.setValue(7, row_data[7])
                row.setValue(8, row_data[8])
                row.setValue(9, row_data[9])
                self.model.insertRecord(-1, row)

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

    def excluir_database(self):
        reply = QMessageBox.question(self, 'Confirmar Exclusão', 'Tem certeza que deseja excluir a tabela controle_contratos?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database_manager.execute_query("DROP TABLE IF EXISTS controle_contratos")
                QMessageBox.information(self, "Sucesso", "Tabela controle_contratos excluída com sucesso.")
            except Exception as e:
                QMessageBox.warning(self, "Erro ao excluir", f"Erro ao excluir a tabela: {str(e)}")

    def carregar_tabela(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.xls *.ods *.csv)")
        if filepath:
            try:
                if filepath.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)
                self.validate_and_process_data(df)
                df['status'] = 'Minuta'

                with self.database_manager as conn:
                    DatabaseContratosManager.create_table_controle_contratos(conn)

                self.database_manager.save_dataframe(df, 'controle_contratos')
                Dialogs.info(self, "Carregamento concluído", "Dados carregados com sucesso.")
            except Exception as e:
                logging.error("Erro ao carregar tabela: %s", e)
                Dialogs.warning(self, "Erro ao carregar", str(e))

    def validate_and_process_data(self, df):
        try:
            self.validate_columns(df)
            self.add_missing_columns(df)
            self.salvar_detalhes_uasg_sigla_nome(df)
        except ValueError as e:
            Dialogs.warning(self, "Erro de Validação", str(e))
        except Exception as e:
            Dialogs.error(self, "Erro Inesperado", str(e))

    def validate_columns(self, df):
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colunas obrigatórias faltando: {', '.join(missing_columns)}")

    def add_missing_columns(self, df):
        for col in self.required_columns:
            if col not in df.columns:
                df[col] = ""

    def salvar_detalhes_uasg_sigla_nome(self, df):
        with sqlite3.connect(self.database_om_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uasg, sigla_om, orgao_responsavel FROM controle_om")
            om_details = {row[0]: {'sigla_om': row[1], 'orgao_responsavel': row[2]} for row in cursor.fetchall()}
        df['sigla_om'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('sigla_om', ''))
        df['orgao_responsavel'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('orgao_responsavel', ''))
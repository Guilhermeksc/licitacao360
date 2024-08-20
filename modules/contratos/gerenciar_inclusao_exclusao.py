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
        self.model = parent.model
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

        # Adicionando o TableView
        self.table_view = QTableView(self)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.layout.addWidget(self.table_view)

        # Adicionando os botões
        self.layout.addLayout(self.create_button_layout())

    def load_data(self):
        # Configurar o proxy model para filtrar as colunas específicas
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.parent().model)
        self.proxy_model.setFilterKeyColumn(-1)  # Permite buscar em todas as colunas
        self.proxy_model.setDynamicSortFilter(True)

        # Conectar o modelo ao TableView antes de ocultar as colunas
        self.table_view.setModel(self.proxy_model)

        # Ocultar todas as colunas e mostrar apenas as desejadas (4, 7, 8, 9)
        self.hide_unwanted_columns()

        # Ajustar o redimensionamento das colunas
        self.table_view.resizeColumnsToContents()
        self.table_view.horizontalHeader().setStretchLastSection(True)

    def hide_unwanted_columns(self):
        # Função para ocultar colunas não desejadas
        for column in range(self.parent().model.columnCount()):
            if column not in [4, 7, 8, 9]:
                self.table_view.setColumnHidden(column, True)
            else:
                self.table_view.setColumnHidden(column, False)

    def filter_table(self, text):
        # Filtrar o TableView baseado no texto da barra de busca
        search_regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.proxy_model.setFilterRegularExpression(search_regex)

    def create_button_layout(self):
        button_layout = QHBoxLayout()
        
        self.excluir_button = QPushButton("Excluir", self)
        self.excluir_button.clicked.connect(self.excluir_item)
        button_layout.addWidget(self.excluir_button)

        self.excluir_database_button = QPushButton("Excluir Database", self)
        self.excluir_database_button.clicked.connect(self.excluir_database)
        button_layout.addWidget(self.excluir_database_button)

        self.carregar_tabela_button = QPushButton("Carregar Tabela", self)
        self.carregar_tabela_button.clicked.connect(self.carregar_tabela)
        button_layout.addWidget(self.carregar_tabela_button)

        # Adicionando o botão "Sincronizar CSV"
        self.sincronizar_csv_button = QPushButton("Sincronizar CSV", self)
        self.sincronizar_csv_button.clicked.connect(self.sincronizar_csv)
        button_layout.addWidget(self.sincronizar_csv_button)

        return button_layout

    def sincronizar_csv(self):
        # Abrir diálogo para selecionar o arquivo CSV
        filepath, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo CSV", "", "CSV Files (*.csv)")
        if not filepath:
            return

        # Ler o arquivo CSV
        try:
            df_csv = pd.read_csv(filepath)
        except Exception as e:
            QMessageBox.warning(self, "Erro ao abrir CSV", f"Não foi possível abrir o arquivo CSV: {str(e)}")
            return

        # Carregar dados do banco de dados
        with sqlite3.connect(self.database_path) as conn:
            df_db = pd.read_sql_query("SELECT * FROM controle_contratos", conn)

        # Iterar sobre cada linha do CSV para fazer a sincronização
        for index, row in df_csv.iterrows():
            numero_instrumento = row['Número do instrumento']
            
            # Verificar se existe correspondência
            if df_db['comprasnet_contratos'].str.contains(numero_instrumento).any():
                print(f"Correspondente encontrado: {numero_instrumento}")
                # Atualizar a linha existente no banco de dados
                with sqlite3.connect(self.database_path) as conn:
                    uasg_value = row['Unidade Gestora Atual'].split(' - ')[0]
                    fornecedor_info = row['Fornecedor']
                    parts = fornecedor_info.split(' - ')
                    if len(parts) >= 2:
                        cnpj = parts[0].strip()
                        empresa = ' - '.join(parts[1:]).strip()
                    else:
                        cnpj = fornecedor_info.strip()
                        empresa = fornecedor_info.strip()

                    numero_contrato = self.format_numero_contrato(numero_instrumento, uasg_value)
                    nup = row['Processo']
                    vigencia_inicial = row['Vig. Início']
                    vigencia_final = row['Vig. Fim']
                    valor_global = row['Valor Global']
                    atualizacao_comprasnet = row['Atualizado em']

                    # Montar a query de atualização
                    update_query = """
                        UPDATE controle_contratos
                        SET uasg = ?, cnpj = ?, empresa = ?, numero_contrato = ?, nup = ?, 
                            vigencia_inicial = ?, vigencia_final = ?, valor_global = ?, atualizacao_comprasnet = ?
                        WHERE comprasnet_contratos = ?
                    """
                    conn.execute(update_query, (uasg_value, cnpj, empresa, numero_contrato, nup, vigencia_inicial, vigencia_final, valor_global, atualizacao_comprasnet, numero_instrumento))
                    conn.commit()

                print(f"Item {numero_instrumento} atualizado no banco de dados.")
            else:
                print(f"Não encontrado: {numero_instrumento}")
                
                # Preparar os valores para inserção no banco de dados
                uasg_value = row['Unidade Gestora Atual'].split(' - ')[0]
                fornecedor_info = row['Fornecedor']
                parts = fornecedor_info.split(' - ')
                if len(parts) >= 2:
                    cnpj = parts[0].strip()
                    empresa = ' - '.join(parts[1:]).strip()
                else:
                    cnpj = fornecedor_info.strip()
                    empresa = fornecedor_info.strip()

                numero_contrato = self.format_numero_contrato(numero_instrumento, uasg_value)
                nup = row['Processo']
                vigencia_inicial = row['Vig. Início']
                vigencia_final = row['Vig. Fim']
                valor_global = row['Valor Global']
                atualizacao_comprasnet = row['Atualizado em']

                # Inserir a nova linha no banco de dados
                new_data = {
                    'comprasnet_contratos': numero_instrumento,
                    'uasg': uasg_value,
                    'cnpj': cnpj,
                    'empresa': empresa,
                    'numero_contrato': numero_contrato,
                    'nup': nup,
                    'vigencia_inicial': vigencia_inicial,
                    'vigencia_final': vigencia_final,
                    'valor_global': valor_global,
                    'atualizacao_comprasnet': atualizacao_comprasnet
                }

                with sqlite3.connect(self.database_path) as conn:
                    df_new = pd.DataFrame([new_data])
                    df_new.to_sql('controle_contratos', conn, if_exists='append', index=False)
                
                print(f"Item {numero_instrumento} adicionado ao banco de dados.")

    def format_numero_contrato(self, contrato, uasg):
        numero, ano = contrato.split('/')
        ano_formatado = ano[-2:]
        numero_formatado = numero.lstrip('0')  # Remove apenas os zeros à esquerda
        if len(numero_formatado) < 3:
            numero_formatado = numero_formatado.zfill(3)  # Garante que tenha pelo menos 3 dígitos
        numero_contrato = f'{uasg}/{ano_formatado}-{numero_formatado}/00'
        print(f"Original: {contrato} -> Formatado: {numero_contrato}")
        return numero_contrato

    def excluir_item(self):
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            Dialogs.warning(self, "Erro", "Nenhum item selecionado para excluir.")
            return

        # Excluir as linhas selecionadas
        for index in selected_indexes:
            self.model.removeRow(index.row())

        # Remover linhas vazias remanescentes
        self.remove_empty_rows()

        # Atualizar o layout do TableView
        self.table_view.model().layoutChanged.emit()

    def remove_empty_rows(self):
        """Remove any rows from the model that are completely empty."""
        for row in range(self.model.rowCount() - 1, -1, -1):  # Percorre de baixo para cima
            record = self.model.record(row)
            is_empty = all(not record.value(i) for i in range(record.count()))  # Verifica se todos os campos estão vazios
            if is_empty:
                self.model.removeRow(row)

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
                df['status'] = 'Aguardando'

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
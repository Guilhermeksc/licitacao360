from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.contratos.utils import WidgetHelper, Dialogs
from diretorios import *
from datetime import datetime
import tempfile
import pandas as pd
import sqlite3
from contextlib import contextmanager
import os
import logging
from modules.contratos.database_manager import DatabaseContratosManager, SqlModel
import requests

class RequestThread(QThread):
    data_received = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    save_json = pyqtSignal(object, str)

    def __init__(self, unidade_codigo):
        super().__init__()
        self.unidade_codigo = unidade_codigo

    def run(self):
        base_url = "https://contratos.comprasnet.gov.br"
        endpoint = f"/api/contrato/ug/{self.unidade_codigo}"
        url = base_url + endpoint
        print(f"Request endpoint: {url}")

        try:
            response = requests.get(url)
            print("Raw response content:", response.text)

            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                data = {"data": data}  # Certificando-se de que o dado é um dicionário conforme o formato esperado

            self.data_received.emit(data)
            self.save_json.emit(data, self.unidade_codigo)
        except requests.exceptions.HTTPError as http_err:
            error_message = f"HTTP error occurred: {http_err}"
            print(error_message)
            self.error_occurred.emit(error_message)
        except Exception as err:
            error_message = f"Other error occurred: {err}"
            print(error_message)
            self.error_occurred.emit(error_message)

class GerenciarInclusaoExclusaoContratos(QDialog):
    def __init__(self, icons_dir, database_path, required_columns, parent=None):
        super().__init__(parent)
        self.icons_dir = icons_dir
        self.database_path = database_path
        self.required_columns = required_columns  # Adiciona o parâmetro required_columns ao construtor
        self.setWindowTitle("Gerenciar Inclusão/Exclusão de Contratos")
        self.resize(800, 600)
        self.database_manager = DatabaseContratosManager(self.database_path)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.unidade_codigo_input = QLineEdit(self)
        self.unidade_codigo_input.setPlaceholderText("Digite o código da unidade (6 dígitos)")
        self.layout.addWidget(self.unidade_codigo_input)

        self.baixar_json_button = QPushButton("Baixar JSON", self)
        self.baixar_json_button.clicked.connect(self.baixar_json)
        self.layout.addWidget(self.baixar_json_button)

        # Adicionando os botões existentes
        self.layout.addLayout(self.create_button_layout())

    def create_button_layout(self):
        button_layout = QHBoxLayout()
        self.excluir_database_button = QPushButton("Excluir Database", self)
        self.excluir_database_button.clicked.connect(self.excluir_database)
        button_layout.addWidget(self.excluir_database_button)

        self.carregar_tabela_button = QPushButton("Carregar Tabela", self)
        self.carregar_tabela_button.clicked.connect(self.carregar_tabela)
        button_layout.addWidget(self.carregar_tabela_button)

        self.sincronizar_csv_button = QPushButton("Sincronizar CSV", self)
        self.sincronizar_csv_button.clicked.connect(self.sincronizar_csv)
        button_layout.addWidget(self.sincronizar_csv_button)

        return button_layout

    def baixar_json(self):
        unidade_codigo = self.unidade_codigo_input.text()
        if len(unidade_codigo) == 6 and unidade_codigo.isdigit():
            self.thread = RequestThread(unidade_codigo)
            self.thread.data_received.connect(self.on_data_received)
            self.thread.error_occurred.connect(self.on_error_occurred)
            self.thread.save_json.connect(self.save_json)
            self.thread.start()
        else:
            QMessageBox.warning(self, "Entrada Inválida", "Por favor, insira um código de unidade válido de 6 dígitos.")

    def on_data_received(self, data):
        QMessageBox.information(self, "Sucesso", "Dados recebidos com sucesso!")
        self.processar_dados_para_tabela(data)

    def on_error_occurred(self, error_message):
        QMessageBox.critical(self, "Erro", error_message)

    def save_json(self, data, unidade_codigo):
        """Salvar o JSON recebido no diretório base do projeto."""
        file_path = os.path.join(BASE_DIR, f"contratos_{unidade_codigo}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "Sucesso", f"Arquivo JSON salvo em {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar o arquivo JSON: {e}")

    def processar_dados_para_tabela(self, data):
        """Processa os dados JSON para criar uma tabela e salva em um banco de dados SQLite."""
        contratos_list = []
        for contrato in data["data"]:
            prorrogavel = "Sim" if contrato.get("prorrogavel") == "Sim" else "Não"
            custeio = "Sim" if contrato.get("custeio") == "Sim" else "Não"
            status = contrato.get('status') if contrato.get('status') is not None else "Seção de Contratos"
            
            # Definir "2040-01-01" como padrão se 'vigencia_fim' for None ou não existir
            vigencia_final = contrato.get("vigencia_fim")
            if not vigencia_final or pd.isna(vigencia_final):
                vigencia_final = "2040-01-01"

            contrato_info = {
                'status': status,  # Campos conforme necessário
                "id": contrato.get("id"),
                "id_processo": contrato.get("licitacao_numero"),
                "numero": contrato.get("numero"),
                "codigo": contrato["contratante"]["orgao"]["unidade_gestora"].get("codigo"),
                "nome_resumido": contrato["contratante"]["orgao"]["unidade_gestora"].get("nome_resumido"),
                "nome": contrato["contratante"]["orgao"]["unidade_gestora"].get("nome"),
                "cnpj_cpf_idgener": contrato["fornecedor"].get("cnpj_cpf_idgener"),
                "nome_fornecedor": contrato["fornecedor"].get("nome"),
                "tipo": contrato.get("tipo"),
                "subtipo": contrato.get("subtipo"),
                "prorrogavel": prorrogavel,
                "custeio": custeio,
                "situacao": contrato.get("situacao"),
                "categoria": contrato.get("categoria"),
                "processo": contrato.get("processo"),
                "objeto": contrato.get("objeto"),
                "amparo_legal": contrato.get("amparo_legal"),
                "modalidade": contrato.get("modalidade"),
                "licitacao_numero": contrato.get("licitacao_numero"),
                "data_assinatura": contrato.get("data_assinatura"),
                "data_publicacao": contrato.get("data_publicacao"),
                "vigencia_inicial": contrato.get("vigencia_inicio"),
                "vigencia_final": vigencia_final,  # Utilize o valor padrão aqui
                "valor_global": contrato.get("valor_global")
            }
            contratos_list.append(contrato_info)

        df = pd.DataFrame(contratos_list)

        for column in self.required_columns:
            if column not in df.columns:
                df[column] = None 

        # Reordenando as colunas de acordo com 'required_columns'
        df = df[self.required_columns]

        # excel_path = os.path.join(BASE_DIR, "contratos.xlsx")
        # df.to_excel(excel_path, index=False)

        # os.startfile(excel_path)  # Abre o arquivo Excel ao final
        # Convertendo 'vigencia_final' para datetime para ordenação
        df['vigencia_final'] = pd.to_datetime(df['vigencia_final'], format='%Y-%m-%d', errors='coerce')
        
        # Ordenando por 'vigencia_final' de forma decrescente
        df = df.sort_values(by='vigencia_final', ascending=False)

        # Convertendo 'vigencia_final' de volta para string antes de salvar
        df['vigencia_final'] = df['vigencia_final'].dt.strftime('%Y-%m-%d')

        # Chamando a função para salvar no banco de dados SQLite
        self.salvar_dados_no_sqlite(df)

    def salvar_dados_no_sqlite(self, df):
        """Salva o DataFrame no banco de dados SQLite, atualizando registros existentes e inserindo novos registros."""
        try:
            with sqlite3.connect(CONTROLE_CONTRATOS_DADOS) as conn:
                cursor = conn.cursor()
                
                # Certificando-se de que a coluna 'id' é uma PRIMARY KEY ou tem índice UNIQUE
                cursor.execute("PRAGMA table_info(controle_contratos);")
                columns_info = cursor.fetchall()
                id_column_info = next((col for col in columns_info if col[1] == 'id'), None)

                if id_column_info is None or id_column_info[5] != 1:  # Verificando se 'id' é PRIMARY KEY
                    QMessageBox.critical(self, "Erro", "A tabela 'controle_contratos' não possui 'id' como PRIMARY KEY.")
                    return

                # Definindo as colunas necessárias para inserir ou atualizar
                columns = [
                    'id', 'status', 'id_processo', 'numero', 'codigo', 'nome_resumido', 'nome', 
                    'cnpj_cpf_idgener', 'nome_fornecedor', 'tipo', 'subtipo', 'prorrogavel', 
                    'custeio', 'situacao', 'categoria', 'processo', 'objeto', 'amparo_legal', 
                    'modalidade', 'licitacao_numero', 'data_assinatura', 'data_publicacao', 
                    'vigencia_inicial', 'vigencia_final', 'valor_global'
                ]

                for _, row in df.iterrows():
                    # Converter a linha em uma tupla com apenas as colunas necessárias
                    row_data = tuple(row[col] for col in columns)
                    
                    # Verificar se o registro já existe
                    cursor.execute("SELECT COUNT(1) FROM controle_contratos WHERE id = ?", (row['id'],))
                    exists = cursor.fetchone()[0] > 0
                    
                    if exists:
                        # Se o registro existir, execute UPDATE
                        update_query = """
                        UPDATE controle_contratos SET
                            status = ?, id_processo = ?, numero = ?, codigo = ?, nome_resumido = ?, nome = ?, 
                            cnpj_cpf_idgener = ?, nome_fornecedor = ?, tipo = ?, subtipo = ?, prorrogavel = ?, 
                            custeio = ?, situacao = ?, categoria = ?, processo = ?, objeto = ?, amparo_legal = ?, 
                            modalidade = ?, licitacao_numero = ?, data_assinatura = ?, data_publicacao = ?, 
                            vigencia_inicial = ?, vigencia_final = ?, valor_global = ?
                        WHERE id = ?;
                        """
                        cursor.execute(update_query, row_data[1:] + (row['id'],))
                    else:
                        # Se o registro não existir, execute INSERT
                        insert_query = """
                        INSERT INTO controle_contratos (id, status, id_processo, numero, codigo, nome_resumido, nome, 
                            cnpj_cpf_idgener, nome_fornecedor, tipo, subtipo, prorrogavel, custeio, situacao, categoria, 
                            processo, objeto, amparo_legal, modalidade, licitacao_numero, data_assinatura, data_publicacao, 
                            vigencia_inicial, vigencia_final, valor_global)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """
                        cursor.execute(insert_query, row_data)
                
                conn.commit()
                QMessageBox.information(self, "Sucesso", "Dados salvos no banco de dados com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar no banco de dados: {e}")

    def hide_unwanted_columns(self):
        # Função para ocultar colunas não desejadas
        for column in range(self.parent().model.columnCount()):
            if column not in [4, 7, 8, 9]:
                self.table_view.setColumnHidden(column, True)
            else:
                self.table_view.setColumnHidden(column, False)

    def create_button_layout(self):
        button_layout = QHBoxLayout()
        self.excluir_database_button = QPushButton("Excluir Database", self)
        self.excluir_database_button.clicked.connect(self.excluir_database)
        button_layout.addWidget(self.excluir_database_button)

        return button_layout

    def excluir_database(self):
        reply = QMessageBox.question(self, 'Confirmar Exclusão', 'Tem certeza que deseja excluir a tabela controle_contratos?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database_manager.execute_query("DROP TABLE IF EXISTS controle_contratos")
                QMessageBox.information(self, "Sucesso", "Tabela controle_contratos excluída com sucesso.")
            except Exception as e:
                QMessageBox.warning(self, "Erro ao excluir", f"Erro ao excluir a tabela: {str(e)}")

    def format_numero_contrato(self, contrato, uasg):
        numero, ano = contrato.split('/')
        ano_formatado = ano[-2:]
        numero_formatado = numero.lstrip('0')  # Remove apenas os zeros à esquerda
        if len(numero_formatado) < 3:
            numero_formatado = numero_formatado.zfill(3)  # Garante que tenha pelo menos 3 dígitos
        numero_contrato = f'{uasg}/{ano_formatado}-{numero_formatado}/00'
        print(f"Original: {contrato} -> Formatado: {numero_contrato}")
        return numero_contrato
    
class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Estabelece uma conexão com o banco de dados."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path, timeout=10)  # Ajuste o timeout conforme necessário
        return self.connection

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.connection:
            self.connection.close()
            self.connection = None

    @contextmanager
    def transaction(self):
        """Gerencia uma transação de banco de dados."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()  # Confirma a transação se tudo correr bem
        except sqlite3.DatabaseError as e:
            conn.rollback()  # Reverte a transação em caso de erro
            QMessageBox.critical(None, "Erro", f"Erro ao acessar o banco de dados: {e}")
        finally:
            self.close()
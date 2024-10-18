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
from modules.atas.database_manager import DatabaseATASManager, SqlModel
import requests
import time
import re

def extrair_variaveis(numeroControlePNCPAta):
    padrao = r"(\d{14})-(\d)-(\d{6})/(\d{4})-(\d{6})"
    match = re.match(padrao, numeroControlePNCPAta)

    if match:
        cnpj = match.group(1)
        referencia = match.group(2)
        sequencial = match.group(3)
        ano = match.group(4)
        numero_ata = match.group(5)
        return {
            "CNPJ": cnpj,
            "referencia": referencia,
            "sequencial": sequencial,
            "ano": ano,
            "numero_ata": numero_ata
        }
    else:
        return None

class RequestThread(QThread):
    data_received = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    save_json = pyqtSignal(object, str)

    def __init__(self, unidade_codigo):
        super().__init__()
        self.unidade_codigo = unidade_codigo

    def run(self):
        base_url = "https://pncp.gov.br"
        endpoint = f"/api/consulta/v1/atas?dataInicial=20240101&dataFinal=20241015&cnpj=00394502000144&codigoUnidadeAdministrativa={self.unidade_codigo}&pagina=1"
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

class ConsultaAPIDialog(QDialog):
    def __init__(self, max_tentativas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tentando Obter Dados da API")
        self.setFixedSize(300, 100)
        self.layout = QVBoxLayout(self)

        self.label = QLabel(f"Tentativa 0/{max_tentativas}")
        self.layout.addWidget(self.label)

        # Tornar o diálogo modal e sobrepor as outras janelas
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

    def atualizar_tentativa(self, tentativa_atual, max_tentativas):
        self.label.setText(f"Tentativa {tentativa_atual}/{max_tentativas}")

    
class GerenciarInclusaoExclusaoATAS(QDialog):
    def __init__(self, icons_dir, database_path, required_columns, parent=None):
        super().__init__(parent)
        self.icons_dir = icons_dir
        self.database_path = database_path
        self.required_columns = required_columns
        self.setWindowTitle("Sincronizar Atas")
        self.setFixedSize(400, 300)  # Define o tamanho fixo da janela
        self.database_manager = DatabaseATASManager(self.database_path)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        # Adicionando o ícone e o label "Sincronizar"
        icon_confirm = QIcon(str(self.icons_dir / "synchronize.png"))
        sync_layout = QHBoxLayout()

        sync_icon_label = QLabel()
        sync_icon_label.setPixmap(icon_confirm.pixmap(80, 80))  # Adiciona o ícone ao QLabel

        sync_label = QLabel("Sincronizar")
        sync_label.setStyleSheet("font-size: 40px; font-weight: bold;")  # Define o tamanho da fonte para 40 e negrito

        sync_layout.addWidget(sync_icon_label)  # Adiciona o QLabel com o ícone ao layout
        sync_layout.addWidget(sync_label)  # Adiciona o QLabel "Sincronizar" ao layout
        sync_layout.addStretch()
        self.layout.addLayout(sync_layout)

        # Adicionando link para documentação da API
        link_label = QLabel('<a href="https://pncp.gov.br/pncp-consulta/v3/api-docs">Documentação da API</a>')
        link_label.setStyleSheet("font-size: 16px")
        link_label.setOpenExternalLinks(True)
        self.layout.addWidget(link_label)

        # Adicionando labels de informações da API
        get_label = QLabel('GET "{unidade_codigo}"')
        get_label.setStyleSheet("font-size: 16px")
        self.layout.addWidget(get_label)

        unidade_codigo_info_label = QLabel('"{unidade_codigo} = uasg"')
        unidade_codigo_info_label.setStyleSheet("font-size: 16px")
        self.layout.addWidget(unidade_codigo_info_label)

        # Layout horizontal para o label e o QLineEdit
        unidade_layout = QHBoxLayout()

        unidade_label = QLabel("Digite o número da UASG:")
        unidade_label.setStyleSheet("font-size: 16px")
        unidade_layout.addWidget(unidade_label)

        self.unidade_codigo_input = QLineEdit(self)
        self.unidade_codigo_input.setPlaceholderText("Digite o código da unidade (6 dígitos)")
        unidade_layout.addWidget(self.unidade_codigo_input)

        self.layout.addLayout(unidade_layout)  # Adiciona o layout horizontal ao layout principal

        # Botão para baixar JSON
        self.baixar_json_button = QPushButton("Sincronizar", self)
        self.baixar_json_button.clicked.connect(self.baixar_json)
        self.layout.addWidget(self.baixar_json_button)

        # Adicionando os botões existentes
        self.layout.addLayout(self.create_button_layout())

    def baixar_json(self):
        unidade_codigo = self.unidade_codigo_input.text()
        if len(unidade_codigo) == 6 and unidade_codigo.isdigit():
            data = self.tentar_consulta_api(unidade_codigo)
            if data:
                self.processar_dados_para_tabela(data)
        else:
            QMessageBox.warning(self, "Entrada Inválida", "Por favor, insira um código de unidade válido de 6 dígitos.")

    def tentar_consulta_api(self, unidade_codigo):
        max_tentativas = 10
        dialog = ConsultaAPIDialog(max_tentativas)
        dialog.show()

        for tentativa in range(1, max_tentativas + 1):
            dialog.atualizar_tentativa(tentativa, max_tentativas)
            QCoreApplication.processEvents()  # Atualiza a interface gráfica

            try:
                # Endpoint da API
                base_url = "https://pncp.gov.br"
                endpoint = f"/api/consulta/v1/atas?dataInicial=20240101&dataFinal=20241015&cnpj=00394502000144&codigoUnidadeAdministrativa={unidade_codigo}&pagina=1"
                url = base_url + endpoint
                response = requests.get(url)

                # Verifica se a resposta foi bem-sucedida
                if response.status_code == 200:
                    data = response.json()
                    dialog.close()
                    QMessageBox.information(self, "Sucesso", "Dados obtidos com sucesso!")
                    return data
                else:
                    raise requests.exceptions.RequestException(f"Erro HTTP: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"Erro na tentativa {tentativa}: {e}")
                time.sleep(2)  # Pausa entre as tentativas

        dialog.close()
        QMessageBox.critical(self, "Erro", "Não foi possível obter os dados da API após 10 tentativas.")
        return None

    def on_data_received(self, data):
        # QMessageBox.information(self, "Sucesso", "Dados recebidos com sucesso!")
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
        contratos_list = self.extrair_contratos(data)

        # Converter para DataFrame
        df = pd.DataFrame(contratos_list)

        # Garantir que todas as colunas necessárias estejam presentes
        df = self.verificar_e_adicionar_colunas(df)

        # Reordenar e formatar colunas
        df = self.reordenar_e_formatar_colunas(df)

        # Salvar no banco de dados SQLite
        self.salvar_dados_no_sqlite(df)

    def extrair_contratos(self, data):
        """Extrai as informações necessárias do JSON e formata para o banco de dados."""
        contratos_list = []
        for contrato in data.get("data", []):
            # Extrair variáveis do campo numeroControlePNCPAta
            variaveis = extrair_variaveis(contrato.get("numeroControlePNCPAta", ""))

            # Extrair os campos adicionais: critério de julgamento, tipo de licitação, vigência
            vigencia = contrato.get("vigenciaFim", "2016-01-01")

            if variaveis:
                contrato_info = {
                    'id_pncp': contrato.get("numeroControlePNCPAta"),
                    'sequencial_ata_pncp': variaveis["numero_ata"],
                    'numero_controle_ata': contrato.get("numeroAtaRegistroPreco"),
                    'sequencial_ano_pncp': variaveis["ano"],
                    'numero_controle_ano': contrato.get("anoAta"),
                    'status': contrato.get('status', "Seção de Contratos"),
                    'dias': (pd.to_datetime(contrato.get("vigenciaFim")) - pd.to_datetime(contrato.get("vigenciaInicio"))).days if contrato.get("vigenciaFim") else None,
                    'cnpj': variaveis["CNPJ"],
                    'referencia': variaveis["referencia"],
                    'sequencial': variaveis["sequencial"],
                    'vigencia_inicial': contrato.get("vigenciaInicio"),
                    'vigencia_final': vigencia,
                    'data_assinatura': contrato.get("dataAssinatura"),
                    'data_publicacao': contrato.get("dataPublicacaoPncp"),
                    'objeto': contrato.get("objetoContratacao"),
                    'codigo_unidade': contrato.get("codigoUnidadeOrgao"),
                    'nome_unidade': contrato.get("nomeUnidadeOrgao"),
                }
                contratos_list.append(contrato_info)
            else:
                print(f"Erro ao extrair variáveis de numeroControlePNCPAta: {contrato.get('numeroControlePNCPAta')}")
        
        return contratos_list

    def verificar_e_adicionar_colunas(self, df):
        """Verifica se todas as colunas necessárias estão presentes no DataFrame e as adiciona se necessário."""
        for column in self.required_columns:
            if column not in df.columns:
                df[column] = None
        return df

    def reordenar_e_formatar_colunas(self, df):
        """Reordena as colunas conforme necessário e converte vigência para data."""
        if 'vigencia_final' not in df.columns:
            df['vigencia_final'] = "2016-01-01"  # Definir valor padrão se a coluna não existir

        # Convertendo 'vigencia_final' para datetime e ordenando
        df['vigencia_final'] = pd.to_datetime(df['vigencia_final'], format='%Y-%m-%d', errors='coerce')
        df = df.sort_values(by='vigencia_final', ascending=False)
        
        # Convertendo 'vigencia_final' de volta para string antes de salvar
        df['vigencia_final'] = df['vigencia_final'].dt.strftime('%Y-%m-%d')
        return df

    def salvar_dados_no_sqlite(self, df):
        """Salva o DataFrame no banco de dados SQLite, atualizando registros existentes e inserindo novos registros."""
        try:
            with sqlite3.connect(CONTROLE_ATAS_DADOS) as conn:
                cursor = conn.cursor()
                for _, row in df.iterrows():
                    # Verificar se o registro já existe
                    cursor.execute("SELECT COUNT(1) FROM controle_atas WHERE id_pncp = ?", (row['id_pncp'],))
                    exists = cursor.fetchone()[0] > 0

                    if exists:
                        # Atualizar se já existe
                        update_query = """
                        UPDATE controle_atas SET
                            sequencial_ata_pncp = ?, numero_controle_ata = ?, sequencial_ano_pncp = ?, numero_controle_ano = ?,
                            status = ?, dias = ?, cnpj = ?, referencia = ?, sequencial = ?, 
                            vigencia_inicial = ?, vigencia_final = ?, data_assinatura = ?, data_publicacao = ?, 
                            objeto = ?, codigo_unidade = ?, nome_unidade = ?
                        WHERE id_pncp = ?;
                        """
                        cursor.execute(update_query, (
                            row['sequencial_ata_pncp'], row['numero_controle_ata'], row['sequencial_ano_pncp'], row['numero_controle_ano'],
                            row['status'], row['dias'], row['cnpj'], row['referencia'], row['sequencial'], 
                            row['vigencia_inicial'], row['vigencia_final'], row['data_assinatura'], row['data_publicacao'], 
                            row['objeto'], row['codigo_unidade'], row['nome_unidade'], row['id_pncp']
                        ))
                    else:
                        # Inserir se não existe
                        insert_query = """
                        INSERT INTO controle_atas (
                            id_pncp, sequencial_ata_pncp, numero_controle_ata, sequencial_ano_pncp, numero_controle_ano, 
                            status, dias, cnpj, referencia, sequencial, vigencia_inicial, vigencia_final, 
                            data_assinatura, data_publicacao, objeto, codigo_unidade, nome_unidade
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """
                        cursor.execute(insert_query, (
                            row['id_pncp'], row['sequencial_ata_pncp'], row['numero_controle_ata'], row['sequencial_ano_pncp'], 
                            row['numero_controle_ano'], row['status'], row['dias'], row['cnpj'], row['referencia'], 
                            row['sequencial'], row['vigencia_inicial'], row['vigencia_final'], row['data_assinatura'], 
                            row['data_publicacao'], row['objeto'], row['codigo_unidade'], row['nome_unidade']
                        ))
                conn.commit()
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
        reply = QMessageBox.question(self, 'Confirmar Exclusão', 'Tem certeza que deseja excluir a tabela controle_atas?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database_manager.execute_query("DROP TABLE IF EXISTS controle_atas")
                QMessageBox.information(self, "Sucesso", "Tabela controle_atas excluída com sucesso.")
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
import requests
import pandas as pd
import sqlite3
import logging
from PyQt6.QtWidgets import QMessageBox, QVBoxLayout, QLabel, QProgressBar, QDialog
from PyQt6.QtCore import QThread, pyqtSignal

class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Carregando")
        self.setModal(True)
        self.setFixedSize(300, 100)

        # Layout e widgets
        layout = QVBoxLayout()
        self.label = QLabel("Aguarde, a requisição está em andamento...")
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # Indeterminado
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

class DadosPregaoThread(QThread):
    finished = pyqtSignal(str)  # Sinal para indicar que a thread terminou, passando uma mensagem
    error = pyqtSignal(str)     # Sinal para indicar que houve um erro, passando a mensagem de erro

    def __init__(self, ui_manager, db_path, parent=None):
        super().__init__(parent)
        self.ui_manager = ui_manager
        self.db_path = db_path
        self.parent = parent

    def run(self):
        # Executa os passos da função visualizar_dados_pregao
        try:
            # Obtém os dados da linha selecionada
            dados_linha = obter_dados_linha_selecionada(self.ui_manager, self.parent)
            if not dados_linha:
                self.error.emit("Nenhuma linha foi selecionada.")
                return

            # Constrói a URL da API
            url_api = construir_url_api(dados_linha)

            # Faz a requisição à API
            dados_api = fazer_requisicao(url_api, self.parent)
            if dados_api:
                # Salva os dados no banco de dados
                salvar_dados_no_banco(dados_api, self.db_path, self.parent)
                self.finished.emit("Dados salvos com sucesso.")
            else:
                self.error.emit("Erro ao obter os dados da API.")
        except Exception as e:
            self.error.emit(str(e))

def obter_dados_linha_selecionada(ui_manager, parent):
    """Obtém os dados necessários da linha selecionada na tabela."""
    selected_row_data = ui_manager.selected_row_data
    if selected_row_data.empty:
        logging.warning("Nenhuma linha selecionada ou dados indisponíveis.")
        return None
    return selected_row_data.iloc[0].to_dict()

def construir_url_api(dados):
    """Constrói a URL para a requisição à API com base nos dados fornecidos."""
    cnpj = dados.get("CNPJ")
    sequencial_ano_pncp = dados.get("sequencial_ano_pncp")
    sequencial_ata_pncp = dados.get("sequencial")
    return f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{sequencial_ano_pncp}/{sequencial_ata_pncp}"

def fazer_requisicao(url, parent):
    """Realiza a requisição para a API e retorna os dados no formato JSON."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Levanta exceções para erros HTTP
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Erro ao fazer a requisição para {url}: {e}")
        return None

def salvar_dados_no_banco(dados, db_path, parent):
    """Salva os dados recebidos no banco de dados especificado."""
    try:
        # Nome da tabela no banco de dados
        table_name = "DADOS_PREGAO"

        # Achata a estrutura do JSON para incluir dados de 'orgaoEntidade' e 'unidadeOrgao'
        orgao_entidade = dados.pop("orgaoEntidade", {})
        unidade_orgao = dados.pop("unidadeOrgao", {})

        # Adiciona os campos de 'orgaoEntidade' ao nível principal
        for key, value in orgao_entidade.items():
            dados[f"orgaoEntidade_{key}"] = value

        # Adiciona os campos de 'unidadeOrgao' ao nível principal
        for key, value in unidade_orgao.items():
            dados[f"unidadeOrgao_{key}"] = value

        # Converte os dados para um DataFrame
        df = pd.json_normalize(dados)

        # Filtra as colunas desejadas
        colunas_desejadas = [
            'valorTotalEstimado', 'valorTotalHomologado', 'numeroControlePNCP', 'anoCompra', 
            'sequencialCompra', 'numeroCompra', 'processo', 'modalidadeNome', 'objetoCompra',
            'informacaoComplementar', 'srp', 'dataPublicacaoPncp', 'dataAberturaProposta', 
            'dataEncerramentoProposta', 'situacaoCompraId', 'situacaoCompraNome', 
            'existeResultado', 'dataInclusao', 'dataAtualizacao', 
            'unidadeOrgao_codigoUnidade', 'unidadeOrgao_nomeUnidade'
        ]

        # Filtra o DataFrame para manter apenas as colunas desejadas
        df_filtrado = df[colunas_desejadas]

        # Conexão com o banco de dados
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Criação da tabela, se não existir, com a coluna 'numeroControlePNCP' como chave primária
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    valorTotalEstimado REAL,
                    valorTotalHomologado REAL,
                    numeroControlePNCP TEXT PRIMARY KEY,
                    anoCompra INTEGER,
                    sequencialCompra INTEGER,
                    numeroCompra TEXT,
                    processo TEXT,
                    modalidadeNome TEXT,
                    objetoCompra TEXT,
                    informacaoComplementar TEXT,
                    srp BOOLEAN,
                    dataPublicacaoPncp TEXT,
                    dataAberturaProposta TEXT,
                    dataEncerramentoProposta TEXT,
                    situacaoCompraId INTEGER,
                    situacaoCompraNome TEXT,
                    existeResultado BOOLEAN,
                    dataInclusao TEXT,
                    dataAtualizacao TEXT,
                    unidadeOrgao_codigoUnidade TEXT,
                    unidadeOrgao_nomeUnidade TEXT
                )
            ''')

            # Inserção ou substituição dos dados no banco de dados
            for _, row in df_filtrado.iterrows():
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} (
                        valorTotalEstimado, valorTotalHomologado, numeroControlePNCP, anoCompra, 
                        sequencialCompra, numeroCompra, processo, modalidadeNome, objetoCompra, 
                        informacaoComplementar, srp, dataPublicacaoPncp, dataAberturaProposta, 
                        dataEncerramentoProposta, situacaoCompraId, situacaoCompraNome, 
                        existeResultado, dataInclusao, dataAtualizacao, 
                        unidadeOrgao_codigoUnidade, unidadeOrgao_nomeUnidade
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(row[col] for col in colunas_desejadas))

            # Confirma as alterações
            conn.commit()

        logging.info(f"Dados salvos na tabela {table_name} no banco de dados {db_path}.")
    except Exception as e:
        logging.error(f"Erro ao salvar os dados no banco de dados: {e}")
        raise

from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QStandardItem, QStandardItemModel
from PyQt6.QtCore import Qt
import sys
import requests
import pandas as pd

class ComprasnetContratosAPI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Consulta Contratos - Comprasnet')
        self.setGeometry(100, 100, 800, 600)
        
        # Configurar interface do usuário
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: transparent;")  # Define o fundo transparente

        main_layout = QVBoxLayout(self)

        # Layout de título
        main_layout.addLayout(self._create_title_layout())

        # Campo de entrada para unidade_codigo
        main_layout.addWidget(QLabel("Código da Unidade (unidade_codigo):"))
        self.unidade_codigo_input = QLineEdit(self)
        self.unidade_codigo_input.setPlaceholderText("Digite o código da unidade")
        main_layout.addWidget(self.unidade_codigo_input)

        # Botão de consulta
        self.consult_button = QPushButton('Consultar', self)
        self.consult_button.clicked.connect(self.make_request)
        main_layout.addWidget(self.consult_button)

        # TreeView para exibir os dados
        self.tree_view = QTreeView(self)
        self.tree_view.setHeaderHidden(False)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.tree_view.clicked.connect(self.on_tree_view_click)
        main_layout.addWidget(self.tree_view)

        # Configuração do modelo
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.tree_view.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def _create_title_layout(self):
        layout = QHBoxLayout()
        title_label = QLabel("Consulta Contratos por Unidade")
        title_label.setFont(self._get_title_font(30, bold=True))
        layout.addWidget(title_label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return layout

    def _get_title_font(self, size=14, bold=False):
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def make_request(self):
        # Dados de entrada
        unidade_codigo = self.unidade_codigo_input.text().strip()

        # Validação dos dados
        if not unidade_codigo:
            self._display_message("Erro: O código da unidade não pode estar vazio.")
            return

        # Construção da URL
        base_url = "https://contratos.comprasnet.gov.br"
        endpoint = f"/api/contrato/ug/{unidade_codigo}"
        url = base_url + endpoint
        print(f"Request endpoint: {url}")

        try:
            response = requests.get(url, headers={'accept': 'application/json', 'X-CSRF-TOKEN': ''})
            response.raise_for_status()
            data = response.json()
            self._populate_tree_view(data)
            self._save_to_csv(data, unidade_codigo)  # Salva os dados em um arquivo CSV
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Print do erro HTTP
            self._display_message(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"Other error occurred: {err}")  # Print do erro genérico
            self._display_message(f"Other error occurred: {err}")

    def _populate_tree_view(self, data):
        # Limpa o modelo anterior
        self.model.clear()

        # Define os cabeçalhos com base nos dados esperados
        headers = ['Fornecedor', 'Detalhes']
        self.model.setHorizontalHeaderLabels(headers)

        # Adiciona os dados ao modelo
        if isinstance(data, list):
            for contrato in data:
                # Obtém os detalhes do fornecedor
                fornecedor = contrato.get('fornecedor', {})
                fornecedor_info = f"{fornecedor.get('cnpj_cpf_idgener', '')} - {fornecedor.get('nome', '')}"
                parent_item = QStandardItem(fornecedor_info)

                # Adicionando os detalhes como filhos do item principal
                fornecedor_detail = QStandardItem(f"Tipo: {fornecedor.get('tipo', '')}")
                parent_item.appendRow(fornecedor_detail)

                # Adiciona outros detalhes do contrato como filhos
                for key, value in contrato.items():
                    if key == 'links':  # Adiciona subitens clicáveis para links
                        links_item = QStandardItem('Links')
                        for link_key, link_value in value.items():
                            child_link_item = QStandardItem(link_key)
                            child_link_item.setData(link_value, Qt.ItemDataRole.UserRole)  # Armazena o URL para requisição posterior
                            child_link_item.setData(contrato.get('numero', ''), Qt.ItemDataRole.UserRole + 1)  # Armazena o ID do contrato
                            links_item.appendRow(child_link_item)
                        parent_item.appendRow(links_item)
                    elif key != 'fornecedor':  # Excluindo o campo já exibido no item principal
                        child_item = QStandardItem(f"{key}: {value}")
                        parent_item.appendRow(child_item)
                
                self.model.appendRow(parent_item)
        else:
            self._display_message("Erro: A resposta da API não está no formato esperado.")

    def _save_to_csv(self, data, unidade_codigo):
        # Verifica se a resposta é uma lista e cria um DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
            file_name = f"consulta{unidade_codigo}.csv"
            df.to_csv(file_name, index=False)
            self._display_message(f"Dados salvos em {file_name}.")
            print(f"Dados salvos em {file_name}.")  # Print para confirmar o salvamento
        else:
            self._display_message("Erro ao salvar: A resposta da API não está no formato esperado para exportação.")

    def _display_message(self, message):
        # Exibe uma mensagem de erro ou informação usando uma caixa de mensagem
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle("Erro")
        msg_box.exec()

    def on_tree_view_click(self, index):
        # Método para lidar com cliques no QTreeView
        item = self.model.itemFromIndex(index)
        link_url = item.data(Qt.ItemDataRole.UserRole)
        contract_id = item.data(Qt.ItemDataRole.UserRole + 1)
        if link_url and contract_id:
            # Se o item possui um URL associado, faz a requisição
            print(f"Fetching data from: {link_url}")
            self.fetch_link_data(link_url, contract_id, item)

    def fetch_link_data(self, url, contract_id, parent_item):
        try:
            response = requests.get(url, headers={'accept': 'application/json'})
            response.raise_for_status()
            data = response.json()
            print(f"Data fetched from {url}: {data}")
            self._add_items_to_tree(data, parent_item)
            self._save_items_to_csv(data, contract_id)  # Salva os dados em um CSV
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            self._display_message(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"Other error occurred: {err}")
            self._display_message(f"Other error occurred: {err}")

    def _add_items_to_tree(self, data, parent_item):
        if isinstance(data, list):
            for item_data in data:
                item_str = ", ".join(f"{key}: {value}" for key, value in item_data.items())
                child_item = QStandardItem(item_str)
                parent_item.appendRow(child_item)
        else:
            self._display_message("Erro ao adicionar itens à árvore: Dados não estão no formato esperado.")

    def _save_items_to_csv(self, data, contract_id):
        # Verifica se a resposta é uma lista e cria um DataFrame para salvar os itens
        if isinstance(data, list):
            df = pd.DataFrame(data)
            file_name = f"itens_{contract_id}.csv"  # Garante que o nome seja correto
            df.to_csv(file_name, index=False)
            self._display_message(f"Dados dos itens salvos em {file_name}.")
            print(f"Dados dos itens salvos em {file_name}.")  # Print para confirmar o salvamento
        else:
            self._display_message("Erro ao salvar: A resposta da API dos itens não está no formato esperado para exportação.")

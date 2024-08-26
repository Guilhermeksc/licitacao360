from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QStandardItem, QStandardItemModel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import sys
import requests
import pandas as pd

class RequestThread(QThread):
    data_received = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    save_csv = pyqtSignal(list, str)

    def __init__(self, unidade_codigo):
        super().__init__()
        self.unidade_codigo = unidade_codigo

    def run(self):
        base_url = "https://contratos.comprasnet.gov.br"
        endpoint = f"/api/contrato/ug/{self.unidade_codigo}"
        url = base_url + endpoint
        print(f"Request endpoint: {url}")

        try:
            response = requests.get(url, headers={'accept': 'application/json', 'X-CSRF-TOKEN': ''})
            response.raise_for_status()
            data = response.json()
            self.data_received.emit(data)
            self.save_csv.emit(data, self.unidade_codigo)
        except requests.exceptions.HTTPError as http_err:
            error_message = f"HTTP error occurred: {http_err}"
            print(error_message)
            self.error_occurred.emit(error_message)
        except Exception as err:
            error_message = f"Other error occurred: {err}"
            print(error_message)
            self.error_occurred.emit(error_message)

class ComprasnetContratosAPI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Consulta Contratos - Comprasnet')
        self.setGeometry(100, 100, 800, 600)
        
        # Configurar interface do usuário
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: transparent;")

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self._create_title_layout())

        main_layout.addWidget(QLabel("Código da Unidade (unidade_codigo):"))
        self.unidade_codigo_input = QLineEdit(self)
        self.unidade_codigo_input.setPlaceholderText("Digite o código da unidade")
        main_layout.addWidget(self.unidade_codigo_input)

        self.consult_button = QPushButton('Consultar', self)
        self.consult_button.clicked.connect(self.on_consult_button_clicked)
        main_layout.addWidget(self.consult_button)

        self.tree_view = QTreeView(self)
        self.tree_view.setHeaderHidden(False)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.tree_view.clicked.connect(self.on_tree_view_click)
        main_layout.addWidget(self.tree_view)

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

    def on_consult_button_clicked(self):
        unidade_codigo = self.unidade_codigo_input.text().strip()
        if not unidade_codigo:
            self._display_message("Erro: O código da unidade não pode estar vazio.")
            return

        self.thread = RequestThread(unidade_codigo)
        self.thread.data_received.connect(self._populate_tree_view)
        self.thread.error_occurred.connect(self._display_message)
        self.thread.save_csv.connect(self._save_to_csv)
        self.thread.start()

    def _populate_tree_view(self, data):
        self.model.clear()
        headers = ['Consulta']
        self.model.setHorizontalHeaderLabels(headers)

        combinacoes_existentes = {}
        contratos_lista = []
        key_mapping = {
            'id': "ID Comprasnet Contratos",
            'receita_despesa': "Receita ou Despesa?",
            'numero': "Número do Contrato",
            'contratante': "Dados da UG Contratante",
            'codigo_tipo': "Código Tipo",
            'tipo': "Tipo",
            'subtipo': "Subtipo",
            'prorrogavel': "Prorrogável?",
            'situacao': "Ativo?",
            'justificativa_inativo': "Justificativa Inativo",
            'categoria': "Categoria",
            'subcategoria': "Subcategoria",
            'unidades_requisitantes': "Unidades Requisitantes",
            'processo': "Nup do Processo",
            'objeto': "Objeto",
            'amparo_legal': "Amparo Legal",
            'informacao_complementar': "Informação Complementar",
            'codigo_modalidade': "Código Modalidade",
            'modalidade': "Modalidade",
            'unidade_compra': "Unidade de Compra",
            'licitacao_numero': "Número da Licitação",
            'sistema_origem_licitacao': "Sistema de Origem da Licitação",
            'data_assinatura': "Data de Assinatura",
            'data_publicacao': "Data de Publicação",
            'data_proposta_comercial': "Data da Proposta Comercial",
            'vigencia_inicio': "Início da Vigência",
            'vigencia_fim': "Fim da Vigência",
            'valor_inicial': "Valor Inicial",
            'valor_global': "Valor Global",
            'num_parcelas': "Número de Parcelas",
            'valor_parcela': "Valor da Parcela",
            'valor_acumulado': "Valor Acumulado",
            'links': "Links"
        }

        # Lista de chaves que devem estar sob "Informações Complementares"
        informacoes_complementares_keys = [
            'id', 'receita_despesa', 'numero', 'contratante', 'codigo_tipo', 'tipo', 'subtipo', 'prorrogavel',
            'situacao', 'justificativa_inativo', 'categoria', 'subcategoria', 'unidades_requisitantes', 
            'amparo_legal', 'informacao_complementar', 'codigo_modalidade', 'sistema_origem_licitacao',
            'data_proposta_comercial', 'valor_inicial', 'num_parcelas', 'valor_parcela', 'valor_acumulado'
        ]

        if isinstance(data, list):
            for contrato in data:
                modalidade = contrato.get('modalidade', '')
                licitacao_numero = contrato.get('licitacao_numero', '')

                numero, ano = licitacao_numero.split('/')

                codigo_unidade_gestora = contrato.get('contratante', {}).get('orgao', {}).get('unidade_gestora', {}).get('codigo', '')

                contratos_lista.append((int(ano), modalidade, int(numero), codigo_unidade_gestora, contrato))

            contratos_lista.sort(key=lambda x: (-x[0], x[1], x[2]))

            for ano, modalidade, numero, codigo_unidade_gestora, contrato in contratos_lista:
                combinacao_info = f"{modalidade} - {numero:05d}/{ano} (UASG: {codigo_unidade_gestora})"

                if combinacao_info not in combinacoes_existentes:
                    main_parent_item = QStandardItem(combinacao_info)
                    self.model.appendRow(main_parent_item)
                    combinacoes_existentes[combinacao_info] = main_parent_item
                else:
                    main_parent_item = combinacoes_existentes[combinacao_info]

                fornecedor = contrato.get('fornecedor', {})
                fornecedor_info = f"{fornecedor.get('cnpj_cpf_idgener', '')} - {fornecedor.get('nome', '')}"
                fornecedor_item = QStandardItem(fornecedor_info)

                main_parent_item.appendRow(fornecedor_item)

                numero_contrato = QStandardItem(f"Número do Contrato: {contrato.get('numero', '')}")
                modalidade_contrato = QStandardItem(f"Modalidade: {contrato.get('modalidade', '')}")
                prorrogavel = QStandardItem(f"Prorrogável: {contrato.get('prorrogavel', '')}")
                processo_item = QStandardItem(f"Nup do Processo: {contrato.get('processo', '')}")
                objeto_item = QStandardItem(f"Objeto: {contrato.get('objeto', '')}")
                vigencia = QStandardItem(f"Vigência: {contrato.get('vigencia_inicio', '')} a {contrato.get('vigencia_fim', '')}")
                valor_global = QStandardItem(f"Valor Global: {contrato.get('valor_global', '')}")

                fornecedor_item.appendRow(processo_item)
                fornecedor_item.appendRow(objeto_item)
                fornecedor_item.appendRow(prorrogavel)

                fornecedor_item.appendRow(modalidade_contrato)
                fornecedor_item.appendRow(vigencia)
                fornecedor_item.appendRow(valor_global)                
                fornecedor_item.appendRow(numero_contrato)

                # Criar item de "Informações Complementares"
                informacoes_complementares_item = QStandardItem("Informações Complementares")

                for key, value in contrato.items():
                    if key == 'links':
                        links_item = QStandardItem('Links para consulta')
                        for link_key, link_value in value.items():
                            child_link_item = QStandardItem(link_key)
                            child_link_item.setData(link_value, Qt.ItemDataRole.UserRole)
                            child_link_item.setData(contrato.get('numero', ''), Qt.ItemDataRole.UserRole + 1)
                            links_item.appendRow(child_link_item)
                        fornecedor_item.appendRow(links_item)
                    elif key == 'contratante':
                        contratante_item = QStandardItem("Dados da UG")

                        orgao_origem = value.get('orgao_origem', {})
                        orgao_origem_item = QStandardItem("Órgão de Origem")
                        for subkey, subvalue in orgao_origem.items():
                            if subkey == 'unidade_gestora_origem':
                                for ug_key, ug_value in subvalue.items():
                                    subitem = QStandardItem(f"{ug_key.capitalize()}: {ug_value}")
                                    orgao_origem_item.appendRow(subitem)
                            else:
                                subitem = QStandardItem(f"{subkey.capitalize()}: {subvalue}")
                                orgao_origem_item.appendRow(subitem)

                        orgao = value.get('orgao', {})
                        orgao_item = QStandardItem("Órgão")
                        for subkey, subvalue in orgao.items():
                            if subkey == 'unidade_gestora':
                                for ug_key, ug_value in subvalue.items():
                                    subitem = QStandardItem(f"{ug_key.capitalize()}: {ug_value}")
                                    orgao_item.appendRow(subitem)
                            else:
                                subitem = QStandardItem(f"{subkey.capitalize()}: {subvalue}")
                                orgao_item.appendRow(subitem)

                        contratante_item.appendRow(orgao_origem_item)
                        contratante_item.appendRow(orgao_item)

                        fornecedor_item.appendRow(contratante_item)
                    elif key in informacoes_complementares_keys:
                        readable_key = key_mapping.get(key, key)
                        child_item = QStandardItem(f"{readable_key}: {value}")
                        informacoes_complementares_item.appendRow(child_item)

                # Adicionar "Informações Complementares" ao fornecedor
                fornecedor_item.appendRow(informacoes_complementares_item)

        else:
            self._display_message("Erro: A resposta da API não está no formato esperado.")

    def _save_to_csv(self, data, unidade_codigo):
        if isinstance(data, list):
            df = pd.DataFrame(data)
            file_name = f"consulta{unidade_codigo}.csv"
            df.to_csv(file_name, index=False)
            self._display_message(f"Dados salvos em {file_name}.")
            print(f"Dados salvos em {file_name}.")
        else:
            self._display_message("Erro ao salvar: A resposta da API não está no formato esperado para exportação.")

    def _display_message(self, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle("Erro")
        msg_box.exec()

    def on_tree_view_click(self, index):
        item = self.model.itemFromIndex(index)
        link_url = item.data(Qt.ItemDataRole.UserRole)
        contract_id = item.data(Qt.ItemDataRole.UserRole + 1)
        
        # Verificar se o item já foi carregado para evitar carregamento duplicado
        if item.hasChildren() and item.child(0).data(Qt.ItemDataRole.UserRole) is not None:
            print("Este item já foi carregado.")
            return

        if link_url and contract_id:
            print(f"Fetching data from: {link_url}")
            self.fetch_link_data(link_url, contract_id, item)

    def fetch_link_data(self, url, contract_id, parent_item):
        try:
            # Limpar itens filhos existentes antes de adicionar novos
            parent_item.removeRows(0, parent_item.rowCount())

            response = requests.get(url, headers={'accept': 'application/json'})
            response.raise_for_status()
            data = response.json()
            print(f"Data fetched from {url}: {data}")

            # Verificar se o link é para 'itens'
            if 'itens' in url:
                self._add_items_to_tree_specific(data, parent_item)
            else:
                self._add_items_to_tree(data, parent_item)

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            self._display_message(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"Other error occurred: {err}")
            self._display_message(f"Other error occurred: {err}")

    def _add_items_to_tree_specific(self, data, parent_item):
        """
        Método específico para adicionar itens do endpoint 'itens' no tree view.
        """
        if isinstance(data, list):
            for item_data in data:
                # Número do item de compra como item pai
                numero_item_compra = item_data.get('numero_item_compra', 'N/A')
                numero_item_compra_item = QStandardItem(f"Número do Item de Compra: {numero_item_compra}")
                
                # Adicionar detalhes como filhos de 'numero_item_compra'
                for key in ['tipo_id', 'tipo_material', 'grupo_id', 'catmatseritem_id', 'descricao_complementar', 'quantidade', 'valorunitario', 'valortotal']:
                    value = item_data.get(key, 'N/A')
                    detail_item = QStandardItem(f"{key.replace('_', ' ').capitalize()}: {value}")
                    numero_item_compra_item.appendRow(detail_item)

                # Adicionar 'numero_item_compra' ao item pai
                parent_item.appendRow(numero_item_compra_item)
        else:
            self._display_message("Erro ao adicionar itens à árvore: Dados não estão no formato esperado.")

    def _add_items_to_tree(self, data, parent_item):
        """
        Método genérico para adicionar itens no tree view.
        """
        if isinstance(data, list):
            for item_data in data:
                item_str = ", ".join(f"{key}: {value}" for key, value in item_data.items())
                child_item = QStandardItem(item_str)
                parent_item.appendRow(child_item)
        else:
            self._display_message("Erro ao adicionar itens à árvore: Dados não estão no formato esperado.")


    def _save_items_to_csv(self, data, contract_id):
        if isinstance(data, list):
            df = pd.DataFrame(data)
            file_name = f"itens_{contract_id}.csv"
            df.to_csv(file_name, index=False)
            self._display_message(f"Dados dos itens salvos em {file_name}.")
            print(f"Dados dos itens salvos em {file_name}.")
        else:
            self._display_message("Erro ao salvar: A resposta da API dos itens não está no formato esperado para exportação.")

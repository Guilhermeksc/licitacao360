from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys
import requests

from diretorios import ICONS_DIR
import pandas as pd
from pathlib import Path

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys
import requests


class ConsultaContratoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Consultar Contrato")
        self.setGeometry(300, 300, 400, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.label = QLabel("Digite o número do contrato:")
        layout.addWidget(self.label)

        # Adicionar campos para todos os parâmetros da API
        self.data_inicial_input = QLineEdit(self)
        self.data_inicial_input.setPlaceholderText("Data Inicial (Formato: AAAAMMDD)")
        self.data_inicial_input.setText("20240101")  # Texto padrão definido para 20240101
        layout.addWidget(self.data_inicial_input)

        self.data_final_input = QLineEdit(self)
        self.data_final_input.setPlaceholderText("Data Final (Formato: AAAAMMDD)")
        self.data_final_input.setText("20240901")
        layout.addWidget(self.data_final_input)

        self.codigo_modalidade_input = QLineEdit(self)
        self.codigo_modalidade_input.setPlaceholderText("Código Modalidade Contratação")
        self.codigo_modalidade_input.setText("8")
        layout.addWidget(self.codigo_modalidade_input)

        self.uf_input = QLineEdit(self)
        self.uf_input.setPlaceholderText("UF (Ex: DF)")
        self.uf_input.setText("DF")
        layout.addWidget(self.uf_input)

        self.codigo_cidade_input = QLineEdit(self)
        self.codigo_cidade_input.setPlaceholderText("Código Município IBGE")
        self.codigo_cidade_input.setText("5300108")
        layout.addWidget(self.codigo_cidade_input)

        self.cnpj_input = QLineEdit(self)
        self.cnpj_input.setPlaceholderText("CNPJ")
        self.cnpj_input.setText("00394502000144")
        layout.addWidget(self.cnpj_input)

        self.codigo_uasg_input = QLineEdit(self)        
        self.codigo_uasg_input.setPlaceholderText("Código Unidade Administrativa")
        self.codigo_uasg_input.setText("787010")
        layout.addWidget(self.codigo_uasg_input)

        self.id_usuario_input = QLineEdit(self)
        self.id_usuario_input.setPlaceholderText("ID Usuário")
        self.id_usuario_input.setText("3")
        layout.addWidget(self.id_usuario_input)

        self.num_pagina_input = QLineEdit(self)
        self.num_pagina_input.setPlaceholderText("Número da Página")
        layout.addWidget(self.num_pagina_input)

        self.consultar_button = QPushButton("Consultar", self)
        self.consultar_button.clicked.connect(self._consultar_contrato)
        layout.addWidget(self.consultar_button)

        self.resultado_label = QLabel("")
        layout.addWidget(self.resultado_label)

    def _consultar_contrato(self):
        # Coletar dados dos campos de entrada
        data_inicial = self.data_inicial_input.text().strip()
        data_final = self.data_final_input.text().strip()
        codigo_modalidade = self.codigo_modalidade_input.text().strip()
        uf = self.uf_input.text().strip()
        codigo_cidade = self.codigo_cidade_input.text().strip()
        cnpj = self.cnpj_input.text().strip()
        codigo_uasg = self.codigo_uasg_input.text().strip()
        id_usuario = self.id_usuario_input.text().strip()
        num_pagina = self.num_pagina_input.text().strip()

        # Validar entradas (opcionalmente você pode adicionar mais validações)
        if not all([data_inicial, data_final, codigo_modalidade, uf, codigo_cidade, cnpj, codigo_uasg, id_usuario, num_pagina]):
            self.resultado_label.setText("Por favor, preencha todos os campos.")
            return

        # Montar URL de consulta
        base_url = "https://pncp.gov.br/api/consulta"
        endpoint = f"/v1/contratacoes/publicacao?dataInicial={data_inicial}&dataFinal={data_final}&codigoModalidadeContratacao={codigo_modalidade}&uf={uf}&codigoMunicipioIbge={codigo_cidade}&cnpj={cnpj}&codigoUnidadeAdministrativa={codigo_uasg}&idUsuario={id_usuario}&pagina={num_pagina}"
        url = base_url + endpoint

        try:
            response = requests.get(url, headers={'accept': '*/*'})
            response.raise_for_status()
            data = response.json()
            self._display_result(data)
        except requests.exceptions.HTTPError as http_err:
            print(f"Erro HTTP: {http_err}")  # Print do erro no console
            self.resultado_label.setText(f"Erro HTTP: {http_err}")
        except Exception as err:
            print(f"Erro: {err}")  # Print do erro no console
            self.resultado_label.setText(f"Erro: {err}")

    def _display_result(self, data):
        # Exibir resultado na interface
        if data:
            self.resultado_label.setText(f"Resultado da consulta: {data}")
        else:
            self.resultado_label.setText("Nenhum dado encontrado.")

class ManipularPDFsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(ICONS_DIR)
        self.image_cache = self._load_images()
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: transparent;")  # Define o fundo transparente

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self._create_title_layout())

        # Adiciona o botão de "Consultar Contrato"
        consultar_button = QPushButton("Consultar Contrato", self)
        consultar_button.clicked.connect(self._open_consulta_contrato_dialog)
        main_layout.addWidget(consultar_button)

    def _open_consulta_contrato_dialog(self):
        dialog = ConsultaContratoDialog(self)
        dialog.exec()

    def _create_title_layout(self):
        layout = QHBoxLayout()
        icon_label = QLabel()
        icon = self.image_cache.get('pdf')
        if icon:
            scaled_icon = icon.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled_icon)
        title_label = QLabel("Edição de PDFs")
        title_label.setFont(self._get_title_font(30, bold=True))
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return layout

    def _get_title_font(self, size=14, bold=False):
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def _load_images(self):
        images = {
            'pdf': QPixmap(str(self.icons_dir / "pdf.png"))
        }
        return images
class PNCPConsultationApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Consulta Atas de Registro de Preço - PNCP')
        self.setGeometry(100, 100, 800, 600)
        
        # Configurar interface do usuário
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: transparent;")

        main_layout = QVBoxLayout(self)

        # Layout de título
        main_layout.addLayout(self._create_title_layout())

        # Campos de entrada
        main_layout.addWidget(QLabel("Data Inicial (Formato: AAAAMMDD):"))
        self.data_inicial_input = QLineEdit(self)
        self.data_inicial_input.setText("20240601")
        main_layout.addWidget(self.data_inicial_input)

        main_layout.addWidget(QLabel("Data Final (Formato: AAAAMMDD):"))
        self.data_final_input = QLineEdit(self)
        self.data_final_input.setText("20240820")
        main_layout.addWidget(self.data_final_input)

        main_layout.addWidget(QLabel("CNPJ:"))
        self.cnpj_input = QLineEdit(self)
        self.cnpj_input.setText("00394502000144")
        main_layout.addWidget(self.cnpj_input)

        main_layout.addWidget(QLabel("Código Unidade Administrativa:"))
        self.codigo_unidade_input = QLineEdit(self)
        self.codigo_unidade_input.setText("787010")
        main_layout.addWidget(self.codigo_unidade_input)

        main_layout.addWidget(QLabel("Número da Página:"))
        self.pagina_input = QLineEdit(self)
        self.pagina_input.setText("1")
        main_layout.addWidget(self.pagina_input)

        # Botão de consulta
        self.consult_button = QPushButton('Consultar', self)
        self.consult_button.clicked.connect(self.make_request)
        main_layout.addWidget(self.consult_button)

        # TreeView para exibir os dados
        self.tree_view = QTreeView(self)
        self.tree_view.setHeaderHidden(False)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.tree_view)

        # Configuração do modelo
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.tree_view.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def _create_title_layout(self):
        layout = QHBoxLayout()
        title_label = QLabel("Consulta Atas de Registro de Preço")
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
        data_inicial = self.data_inicial_input.text().strip()
        data_final = self.data_final_input.text().strip()
        cnpj = self.cnpj_input.text().strip()
        codigo_unidade = self.codigo_unidade_input.text().strip()
        pagina = self.pagina_input.text().strip()

        if not (data_inicial.isdigit() and data_final.isdigit() and len(data_inicial) == 8 and len(data_final) == 8):
            self._display_message("Erro: Datas devem estar no formato AAAAMMDD.")
            return

        if not cnpj.isdigit() or len(cnpj) != 14:
            self._display_message("Erro: CNPJ deve conter 14 dígitos.")
            return
        
        if not codigo_unidade.isdigit():
            self._display_message("Erro: Código Unidade Administrativa deve ser um número.")
            return

        if not pagina.isdigit():
            self._display_message("Erro: Número da página deve ser um número inteiro.")
            return

        base_url = "https://pncp.gov.br/api/consulta"
        endpoint = f"/v1/atas?dataInicial={data_inicial}&dataFinal={data_final}&cnpj={cnpj}&codigoUnidadeAdministrativa={codigo_unidade}&pagina={pagina}"
        url = base_url + endpoint
        try:
            response = requests.get(url, headers={'accept': '*/*'})
            response.raise_for_status()
            data = response.json()
            self._populate_tree_view(data)
        except requests.exceptions.HTTPError as http_err:
            self._display_message(f"HTTP error occurred: {http_err}")
        except Exception as err:
            self._display_message(f"Other error occurred: {err}")

    def _populate_tree_view(self, data):
        self.model.clear()

        headers = ['Número Controle PNCP Ata', 'Número Ata', 'Ano Ata', 'Cancelado', 'Data Assinatura', 'Vigência Início', 'Vigência Fim', 'Nome Órgão']
        self.model.setHorizontalHeaderLabels(headers)

        registros = []
        for registro in data.get('data', []):
            items = [
                QStandardItem(registro.get('numeroControlePNCPAta', '')),
                QStandardItem(registro.get('numeroAtaRegistroPreco', '')),
                QStandardItem(str(registro.get('anoAta', ''))),
                QStandardItem('Sim' if registro.get('cancelado') else 'Não'),
                QStandardItem(registro.get('dataAssinatura', '')),
                QStandardItem(registro.get('vigenciaInicio', '')),
                QStandardItem(registro.get('vigenciaFim', '')),
                QStandardItem(registro.get('nomeOrgao', ''))
            ]
            self.model.appendRow(items)
            registros.append({
                'Número Controle PNCP Ata': registro.get('numeroControlePNCPAta', ''),
                'Número Ata': registro.get('numeroAtaRegistroPreco', ''),
                'Ano Ata': registro.get('anoAta', ''),
                'Cancelado': 'Sim' if registro.get('cancelado') else 'Não',
                'Data Assinatura': registro.get('dataAssinatura', ''),
                'Vigência Início': registro.get('vigenciaInicio', ''),
                'Vigência Fim': registro.get('vigenciaFim', ''),
                'Nome Órgão': registro.get('nomeOrgao', '')
            })

        # Chama o método para salvar os dados em CSV
        self._save_to_csv(registros)

    def _save_to_csv(self, registros):
        if registros:
            df = pd.DataFrame(registros)
            file_name = 'consulta_atas.csv'
            df.to_csv(file_name, index=False)
            self._display_message(f"Dados salvos em {file_name}.")
            print(f"Dados salvos em {file_name}.")
        else:
            self._display_message("Nenhum dado disponível para salvar.")

    def _display_message(self, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle("Erro")
        msg_box.exec()

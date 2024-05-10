from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
global df_registro_selecionado
df_registro_selecionado = None
import sqlite3
from openpyxl.utils.dataframe import dataframe_to_rows
import locale
import re
from datetime import datetime
from planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_processos,extrair_chave_processo, carregar_dados_pregao

class EditarDadosDialog(QDialog):
    dados_atualizados = pyqtSignal()
    
    def __init__(self, parent=None, dados=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Dados")
        self.setFixedSize(900, 700)
        self.dados = dados or {}
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  # Configura o locale para português do Brasil
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = Path(load_config("database_path", str(CONTROLE_DADOS)))
        self.event_manager = EventManager()
        self.event_manager.controle_dir_updated.connect(self.handle_database_dir_update)
        self.database_manager = DatabaseManager(self.database_path)
        self.init_ui()
        self.init_combobox_data()

    def init_ui(self):
        self.groupBox = QGroupBox('Índices das Variáveis', self)
        self.scrollArea = QScrollArea()
        self.scrollContentWidget = QWidget()
        self.scrollLayout = QFormLayout(self.scrollContentWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollContentWidget)
        self.groupBoxLayout = QVBoxLayout(self.groupBox)
        self.groupBoxLayout.addWidget(self.scrollArea)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.groupBox)
        self.confirmar_button = QPushButton("Confirmar")
        self.confirmar_button.clicked.connect(self.confirmar_edicao)
        self.mainLayout.addWidget(self.confirmar_button)

        self.initialize_fields()

        self.groupBox.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 1px solid gray;
                border-radius: 10px;
                margin-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left; 
                padding: 0 3px;
                background-color: transparent;
            }
            QLabel, QLineEdit, QComboBox, QRadioButton, QDateEdit {
                font-size: 16px;
            }
            QLabel {
                font-weight: bold;
            }
            QLineEdit[readOnly="true"] {
                background-color: #cccccc;
            }
        """)

            
    def initialize_fields(self):
        # Grupo de RadioButton para Material ou Serviço
        self.group_material_servico = QButtonGroup(self)
        self.radio_material = QRadioButton("Material")
        self.radio_servico = QRadioButton("Serviço")
        self.group_material_servico.addButton(self.radio_material)
        self.group_material_servico.addButton(self.radio_servico)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.radio_material)
        radio_layout.addWidget(self.radio_servico)
        self.scrollLayout.addRow("Material ou Serviço:", radio_layout)

        # Define o estado padrão dos RadioButton
        material_servico = self.dados.get('material_servico', '')
        if material_servico and material_servico.strip().lower() == 'servico':
            self.radio_servico.setChecked(True)
        else:
            self.radio_material.setChecked(True)

        # Grupo de RadioButton para SRP
        self.group_srp = QButtonGroup(self)
        self.radio_srp_sim = QRadioButton("Sim")
        self.radio_srp_nao = QRadioButton("Não")
        self.group_srp.addButton(self.radio_srp_sim)
        self.group_srp.addButton(self.radio_srp_nao)

        srp_layout = QHBoxLayout()
        srp_layout.addWidget(self.radio_srp_sim)
        srp_layout.addWidget(self.radio_srp_nao)
        self.scrollLayout.addRow("Sistema de Registro de Preços (SRP):", srp_layout)

        # Define o estado padrão dos RadioButton para 'srp' com base no valor de 'tipo'
        tipo = self.dados.get('tipo', '')
        if tipo == 'Pregão Eletrônico':
            self.radio_srp_sim.setChecked(True)
        else:
            self.radio_srp_nao.setChecked(True)
        
        self.line_edits = {}
        # Configuração e formatação para 'valor_total'
        self.line_edit_valor_total = QLineEdit()
        valor_total = self.dados.get('valor_total', '')
        
        # Garante que valor_total seja uma string para a regex e replace
        if valor_total is None:
            valor_total = ''
        
        # Limpa a string antes de converter para float e formatar
        valor_total = re.sub(r'[^\d,]', '', valor_total).replace(',', '.')

        if valor_total:  # Verifica se a string convertida não está vazia
            try:
                valor_total = locale.currency(float(valor_total), grouping=True)
            except ValueError:  # Trata erros de conversão para float
                valor_total = locale.currency(0, grouping=True)
        else:
            valor_total = locale.currency(0, grouping=True)  # Define como "R$ 0,00" se estiver vazio
        
        self.line_edit_valor_total.setText(valor_total)
        self.scrollLayout.addRow("valor_total", self.line_edit_valor_total)

        # Configuração dos campos sigla_om, uasg e orgao_responsavel
        self.combo_sigla_om = QComboBox()
        self.line_edit_uasg = QLineEdit()
        self.line_edit_orgao = QLineEdit()

        # Definir os campos UASG e Orgao como somente leitura
        self.line_edit_uasg.setReadOnly(True)
        self.line_edit_orgao.setReadOnly(True)

        # Conectar o sinal de mudança de índice do combo box à função de atualização
        self.combo_sigla_om.currentIndexChanged.connect(self.update_dependent_fields)

        # Adicionar ao layout
        self.scrollLayout.addRow(QLabel('sigla_om'), self.combo_sigla_om)
        self.scrollLayout.addRow(QLabel('uasg'), self.line_edit_uasg)
        self.scrollLayout.addRow(QLabel('orgao_responsavel'), self.line_edit_orgao)
        # Adicionar campos 'setor_responsavel' e 'coordenador_planejamento'
        self.line_edit_setor_responsavel = QLineEdit(self.dados.get('setor_responsavel', ''))
        self.scrollLayout.addRow(QLabel('setor_responsavel'), self.line_edit_setor_responsavel)

        self.line_edit_coordenador_planejamento = QLineEdit(self.dados.get('coordenador_planejamento', ''))
        self.scrollLayout.addRow(QLabel('coordenador_planejamento'), self.line_edit_coordenador_planejamento)

        # Criação de sub-layouts para esquerda e direita
        self.date_edits = {}  # Dicionário para guardar os QDateEdit
        leftLayout = QFormLayout()
        rightLayout = QFormLayout()

        # Campos à esquerda incluindo 'objeto' com estilo específico
        leftFields = ["tipo", "numero", "ano", "id_processo", "nup", "objeto", "objeto_completo", "pregoeiro"]
        for field in leftFields:
            line_edit = QLineEdit()
            value = self.dados.get(field, '')
            line_edit.setText(value)
            if field in ["tipo", "numero", "ano", "id_processo"]:  # Estes campos são ReadOnly
                line_edit.setReadOnly(True)
            if field == "objeto":  # Aplica estilo específico para o campo 'objeto'
                line_edit.setStyleSheet("QLineEdit { color: darkblue; font-weight: bold; }")
            self.line_edits[field] = line_edit
            leftLayout.addRow(QLabel(field), line_edit)

        # Data da sessão à esquerda
        date_sessao_edit = QDateEdit()
        date_sessao_edit.setCalendarPopup(True)
        date_sessao_str = self.dados.get('data_sessao')
        valid_date = self.validate_and_convert_date(date_sessao_str)
        if valid_date:
            date_sessao_edit.setDate(valid_date)
        else:
            date_sessao_edit.setDate(QDate.currentDate())  # Somente define para hoje se a data for inválida
        leftLayout.addRow(QLabel('data_sessao'), date_sessao_edit)
        self.date_edits['data_sessao'] = date_sessao_edit

        # Campos à direita
        rightFields = ["item_pca", "portaria_PCA", 
                    "parecer_agu", "msg_irp", "num_irp", "om_participantes", 
                    "link_pncp", "link_portal_marinha"]
        for field in rightFields:
            line_edit = QLineEdit()
            value = self.dados.get(field, '')
            line_edit.setText(value)
            self.line_edits[field] = line_edit
            rightLayout.addRow(QLabel(field), line_edit)

        date_fields_right = ['data_limite_manifestacao_irp', 'data_limite_confirmacao_irp']
        for date_field in date_fields_right:
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_str = self.dados.get(date_field)
            valid_date = self.validate_and_convert_date(date_str)
            if valid_date:
                date_edit.setDate(valid_date)
            else:
                date_edit.setDate(QDate.currentDate())  # Somente define para hoje se a data for inválida
            rightLayout.addRow(QLabel(date_field), date_edit)
            self.date_edits[date_field] = date_edit

        # Adicionando sub-layouts ao layout principal horizontal
        horizontalLayout = QHBoxLayout()
        horizontalLayout.addLayout(leftLayout)
        horizontalLayout.addLayout(rightLayout)

        # Incluir o layout horizontal no layout principal do scroll
        self.scrollLayout.addRow(horizontalLayout)

    def validate_and_convert_date(self, date_str):
        """Valida e converte uma string de data para QDate."""
        try:
            # Tenta converter a string para datetime
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            # Converte datetime para QDate
            return QDate(parsed_date.year, parsed_date.month, parsed_date.day)
        except (ValueError, TypeError):
            # Retorna None se houver erro na conversão
            return None

    def init_combobox_data(self):
        # Conecta ao banco de dados e popula o QComboBox
        with self.database_manager as cursor:
            cursor.execute("SELECT sigla_om, uasg, orgao_responsavel FROM controle_om")
            rows = cursor.fetchall()

        # Índice inicial para definir qual item do ComboBox deve ser selecionado
        index_to_set = 0

        # Carrega os dados do banco de dados para o ComboBox
        for index, (sigla_om, uasg, orgao) in enumerate(rows):
            self.combo_sigla_om.addItem(sigla_om, (uasg, orgao))
            if sigla_om == self.dados['sigla_om']:
                index_to_set = index

        # Verifica se o valor de sigla_om do df_registro_selecionado foi encontrado no banco de dados
        if not any(sigla_om == self.dados['sigla_om'] for sigla_om, _, _ in rows):
            self.combo_sigla_om.addItem(self.dados['sigla_om'], (self.dados['uasg'], self.dados['orgao_responsavel']))
            index_to_set = self.combo_sigla_om.count() - 1

        # Define o item padrão do ComboBox com base nos dados do DataFrame
        self.combo_sigla_om.setCurrentIndex(index_to_set)
        self.update_dependent_fields()

    def update_dependent_fields(self):
        # Atualiza uasg e orgao_responsavel baseados na escolha de sigla_om
        current_data = self.combo_sigla_om.currentData()
        if current_data:
            # Converte explicitamente os valores para strings antes de configurar o texto
            self.line_edit_uasg.setText(str(current_data[0]))
            self.line_edit_orgao.setText(str(current_data[1]))

    def confirmar_edicao(self):
        # Implementação da lógica para atualizar os dados
        with self.database_manager as cursor:
        
            # Atualiza o dicionário com os valores dos line_edits regulares
            dados_atualizados = {coluna: line_edit.text().strip() for coluna, line_edit in self.line_edits.items()}

            dados_atualizados.update({date_col: date_edit.date().toString("yyyy-MM-dd").strip() for date_col, date_edit in self.date_edits.items()})
            # Determine o valor de material_servico com base no RadioButton selecionado
            material_servico = 'servico' if self.radio_servico.isChecked() else 'material'
            dados_atualizados['material_servico'] = material_servico.strip()

            # Adiciona 'sigla_om', 'uasg' e 'orgao_responsavel' ao dicionário de atualizações
            dados_atualizados['valor_total'] = self.line_edit_valor_total.text().strip()
            dados_atualizados['sigla_om'] = self.combo_sigla_om.currentText().strip()
            dados_atualizados['uasg'] = self.line_edit_uasg.text().strip()
            dados_atualizados['orgao_responsavel'] = self.line_edit_orgao.text().strip()

            # Cria a parte SET da consulta SQL dinamicamente
            set_part = ', '.join([f"{coluna} = ?" for coluna in dados_atualizados.keys()])
            
            # Prepara a lista de valores para a consulta (inclui os valores seguidos pelo id no final)
            valores = list(dados_atualizados.values())
            valores.append(self.dados['id'])  # Assume que 'self.dados' contém um campo 'id' com o ID do registro a ser atualizado
            
            # Constrói e executa a consulta SQL de UPDATE
            query = f"UPDATE controle_processos SET {set_part} WHERE id = ?"
            cursor.execute(query, valores)

        # Emite o sinal de dados atualizados e fecha a caixa de diálogo
        self.dados_atualizados.emit()
        self.accept()
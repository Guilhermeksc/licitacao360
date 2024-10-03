from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtGui import QColor
from diretorios import *
global df_registro_selecionado
df_registro_selecionado = None
import sqlite3
from openpyxl.utils.dataframe import dataframe_to_rows
import locale
import re
from datetime import datetime
from modules.planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_processos, carregar_dados_pregao
from database.utils.treeview_utils import load_images, create_button_2
from pathlib import Path
import pandas as pd
class TextEditDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QTextEdit(parent)
        editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        editor.setText(text)  # Apenas define o texto completo no editor

    def setModelData(self, editor, model, index):
        edited_text = editor.toPlainText().strip()
        model.setData(index, edited_text, Qt.ItemDataRole.DisplayRole)  # Define apenas o texto editado no modelo

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class EditarDadosDialog(QDialog):
    dados_atualizados = pyqtSignal()

    def __init__(self, icons_dir, parent=None, dados=None):
        super().__init__(parent)
        self.dados = dados or {}
        self.uasg = ''  # Valor inicial padrão
        self.orgao_responsavel = ''  # Valor inicial padrão
        self.line_edits = {}
        self.date_edits = {}
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  # Configura o locale para português do Brasil
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        self.icons_dir = Path(icons_dir)
        self.image_cache = load_images(self.icons_dir, ["confirm.png", "report.png", "prioridade.png", "emenda_parlamentar.png"])
        self.setupUI()
        self.init_combobox_data()
        self.move(0, 0)
        self.setModal(False)  # Definir o diálogo como não modal

    def setupUI(self):
        self.setWindowTitle("Editar Dados")
        self.setGeometry(300, 300, 900, 700)
        self.titleLabel = QLabel()
        self.update_title_label(self.dados.get('orgao_responsavel', ''), self.dados.get('uasg', ''))
        self.createFormLayout()
        self.applyStyleSheet()

    def update_title_label(self, orgao_responsavel, uasg):
        self.titleLabel.setText(
            f"{self.dados['tipo']} nº {self.dados['numero']}/{self.dados['ano']} - Edição de Dados<br>"
            f"<span style='font-size: 20px; '>OM RESPONSÁVEL: {orgao_responsavel} (UASG: {uasg})</span>"
        )
        self.titleLabel.setStyleSheet("font-size: 32px; font-weight: bold;")

    def createFormLayout(self):
        self.layout = QVBoxLayout(self)  
        self.layout.addLayout(self._create_header_layout(self.dados['tipo'], self.dados['numero'], self.dados['ano'], self.dados['id_processo']))        
        # Layout principal dentro do groupBox deve ser um QVBoxLayout para gerenciar o conteúdo verticalmente
        self.mainLayout = QVBoxLayout()
        self.boxLayout = QVBoxLayout()
        self.boxLinha1 = QHBoxLayout()

        # Criar os QFrames e definir suas propriedades de borda para frame1 e frame2
        self.frame1 = QFrame()
        self.frame1.setObjectName("frame1")
        self.frame1.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame1.setFrameShadow(QFrame.Shadow.Raised)
        self.frame1.setFixedWidth(450)  # Definir largura fixa
        self.vBoxLayout1 = QVBoxLayout(self.frame1)  # Colocar QVBoxLayout dentro do QFrame
        
        self.frame2 = QFrame()
        self.frame2.setObjectName("frame2")
        self.frame2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame2.setFrameShadow(QFrame.Shadow.Raised)
        self.frame2.setFixedWidth(450)  # Definir largura fixa
        self.vBoxLayout2 = QVBoxLayout(self.frame2)  # Colocar QVBoxLayout dentro do QFrame

        self.frame3 = QFrame()
        self.frame3.setObjectName("frame3")
        self.frame3.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame3.setFrameShadow(QFrame.Shadow.Raised)
        self.frame3.setFixedWidth(450)  # Definir largura fixa
        self.vBoxLayout3 = QVBoxLayout(self.frame3)  # Colocar QVBoxLayout dentro do QFrame

        # Adicionar os QFrames ao boxLinha1
        self.boxLinha1.addWidget(self.frame1)
        self.boxLinha1.addWidget(self.frame2)
        self.boxLinha1.addWidget(self.frame3)

        # Adicionar o boxLinha1 ao boxLayout
        self.boxLayout.addLayout(self.boxLinha1)

        # Criar o segundo QHBoxLayout para conter os próximos dois QFrames
        self.boxLinha2 = QHBoxLayout()
       
        self.frame4 = QFrame()
        self.frame4.setObjectName("frame4")
        self.frame4.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame4.setFrameShadow(QFrame.Shadow.Raised)
        self.frame4.setFixedWidth(450)  # Definir largura fixa
        self.vBoxLayout4 = QVBoxLayout(self.frame4)  # Colocar QVBoxLayout dentro do QFrame

        self.frame5 = QFrame()
        self.frame5.setObjectName("frame5")
        self.frame5.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame5.setFrameShadow(QFrame.Shadow.Raised)
        self.frame5.setFixedWidth(450)  # Definir largura fixa
        self.vBoxLayout5 = QVBoxLayout(self.frame5)  # Colocar QVBoxLayout dentro do QFrame

        self.frame6 = QFrame()
        self.frame6.setObjectName("frame6")
        self.frame6.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame6.setFrameShadow(QFrame.Shadow.Raised)
        self.frame6.setFixedWidth(450)  # Definir largura fixa
        self.vBoxLayout6 = QVBoxLayout(self.frame6)  # Colocar QVBoxLayout dentro do QFrame

        # Adicionar os QFrames ao boxLinha2
        self.boxLinha2.addWidget(self.frame4)
        self.boxLinha2.addWidget(self.frame5)
        self.boxLinha2.addWidget(self.frame6)

        # Adicionar o boxLinha2 ao boxLayout
        self.boxLayout.addLayout(self.boxLinha2)

        # Adicionar o boxLayout completo ao mainLayout
        self.layout.addLayout(self.boxLayout)

        # Adicionar métodos de componentes aos layouts verticais
        self.identificar_processo()
        self.item_pca()
        self.adicionar_checkboxes()
        self.material_servico()
        self.definir_srp()
        self.definir_objeto()
        self.inserir_valor_total()
        self.combo_uasg_om()
        self.definir_irp()
        self.definir_links()
        self.definir_comentarios()
        self.definir_pregoeiro_data_sessao_parecerAGU()
        
        # Spacer para manter tudo alinhado ao topo
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.mainLayout.addSpacerItem(self.spacer)

    def _create_header_layout(self, tipo, numero, ano, id_processo):
        header_layout = QHBoxLayout()
        
        # Configuração e estilização do titleLabel já definida no construtor/init
        header_layout.addWidget(self.titleLabel)
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Criação do botão de confirmação
        confirm_button = self.createConfirmButton()
        header_layout.addWidget(confirm_button)

        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))        
        
        # Configuração da imagem (se necessário)
        pixmap = QPixmap(str(MARINHA_PATH))
        pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        header_layout.addWidget(image_label)
        
        return header_layout

    def identificar_processo(self):
        # Criar o layout horizontal para 'ID do Processo' e 'NUP'
        detalhes_layout = QHBoxLayout()

        # Layout para 'ID do Processo'
        id_processo_label = QLabel("ID:")
        id_processo_edit = QLineEdit()
        id_processo_edit.setText(self.dados.get('id_processo', ''))
        id_processo_edit.setReadOnly(True)
        id_processo_edit.setFixedWidth(100)

        # Layout para 'NUP'
        nup_label = QLabel("NUP:")
        self.nup_edit = QLineEdit()
        self.nup_edit.setText(self.dados.get('nup', ''))
        self.nup_edit.setReadOnly(False)

        # Adicionar os widgets ao layout horizontal
        detalhes_layout.addWidget(id_processo_label)
        detalhes_layout.addWidget(id_processo_edit)
        detalhes_layout.addWidget(nup_label)
        detalhes_layout.addWidget(self.nup_edit)

        # Adicionar o layout horizontal ao layout vertical principal
        self.vBoxLayout1.addLayout(detalhes_layout)

    def item_pca(self):
        # Criar o layout horizontal para 'Item PCA' e 'Portaria PCA'
        pca_layout = QHBoxLayout()

        # Criar o label e o campo de edição para 'Item PCA'
        item_pca_label = QLabel("Item PCA:")
        self.item_pca_edit = QLineEdit()
        self.item_pca_edit.setText(self.dados.get('item_pca', ''))
        self.item_pca_edit.setReadOnly(False)
        self.item_pca_edit.setFixedWidth(70)
        self.line_edits['item_pca'] = self.item_pca_edit

        # Criar o label e o campo de edição para 'Portaria PCA'
        portaria_pca_label = QLabel("Portaria PCA:")
        self.portaria_pca_edit = QLineEdit()
        self.portaria_pca_edit.setText(self.dados.get('portaria_PCA', ''))
        self.portaria_pca_edit.setReadOnly(False)
        self.line_edits['portaria_PCA'] = self.portaria_pca_edit

        # Adicionar os widgets ao layout horizontal
        pca_layout.addWidget(item_pca_label)
        pca_layout.addWidget(self.item_pca_edit)
        pca_layout.addWidget(portaria_pca_label)
        pca_layout.addWidget(self.portaria_pca_edit)

        # Adicionar o layout horizontal ao layout vertical principal
        self.vBoxLayout1.addLayout(pca_layout)

    def adicionar_checkboxes(self):
        # Criar um layout horizontal para os checkboxes
        checkbox_layout = QHBoxLayout()

        # Criar os dois checkboxes com seus respectivos textos e ícones
        self.prioritario_checkbox = QCheckBox("Prioritário?")
        self.emenda_parlamentar_checkbox = QCheckBox("Emenda Parlamentar?")

        # Definir o tamanho da fonte
        font = QFont("Arial", 12)
        self.prioritario_checkbox.setFont(font)
        self.emenda_parlamentar_checkbox.setFont(font)

        # Adicionar ícones aos checkboxes
        self.prioritario_checkbox.setIcon(self.image_cache['prioridade'])
        self.emenda_parlamentar_checkbox.setIcon(self.image_cache['emenda_parlamentar'])

        # Carregar os valores do banco de dados e definir o estado dos checkboxes
        prioridade = self.dados.get('prioridade', False)
        emenda_parlamentar = self.dados.get('emenda_parlamentar', False)

        self.prioritario_checkbox.setChecked(prioridade)
        self.emenda_parlamentar_checkbox.setChecked(emenda_parlamentar)

        # Adicionar os checkboxes ao layout horizontal
        checkbox_layout.addWidget(self.prioritario_checkbox)
        checkbox_layout.addWidget(self.emenda_parlamentar_checkbox)

        # Adicionar o layout dos checkboxes ao layout vertical principal
        self.vBoxLayout1.addLayout(checkbox_layout)

    def material_servico(self):
        # Grupo de RadioButton para Material ou Serviço
        self.group_material_servico = QButtonGroup(self)
        self.radio_material = QRadioButton("Material")
        self.radio_servico = QRadioButton("Serviço")
        self.group_material_servico.addButton(self.radio_material)
        self.group_material_servico.addButton(self.radio_servico)

        # Layout para os RadioButtons
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.radio_material)
        radio_layout.addWidget(self.radio_servico)

        # Criando e configurando o QLabel
        label_material_servico = QLabel("Material ou Serviço:")
        label_material_servico.setFont(QFont("Arial", 14))  # Configura fonte, tamanho opcional

        # Layout horizontal que inclui o QLabel e os RadioButtons
        line_layout = QHBoxLayout()
        line_layout.addWidget(label_material_servico)
        line_layout.addLayout(radio_layout)

        # Adicionando o layout horizontal ao QVBoxLayout principal
        self.vBoxLayout1.addLayout(line_layout)

        # Define o estado padrão dos RadioButton
        material_servico = self.dados.get('material_servico', '')
        if material_servico and material_servico.strip().lower() == 'servico':
            self.radio_servico.setChecked(True)
        else:
            self.radio_material.setChecked(True)

    def definir_srp(self):
        # Grupo de RadioButton para SRP
        self.group_srp = QButtonGroup(self)
        self.radio_srp_sim = QRadioButton("Sim")
        self.radio_srp_nao = QRadioButton("Não")
        self.group_srp.addButton(self.radio_srp_sim)
        self.group_srp.addButton(self.radio_srp_nao)

        # Layout para os RadioButtons
        srp_layout = QHBoxLayout()
        srp_layout.addWidget(self.radio_srp_sim)
        srp_layout.addWidget(self.radio_srp_nao)

        # Criando e configurando o QLabel
        label_srp = QLabel("Sistema de Registro de Preços?")
        label_srp.setFont(QFont("Arial", 14))  # Configura fonte, tamanho opcional

        # Layout horizontal que inclui o QLabel e os RadioButtons
        line_layout = QHBoxLayout()
        line_layout.addWidget(label_srp)
        line_layout.addLayout(srp_layout)

        # Adicionando o layout horizontal ao QVBoxLayout principal
        self.vBoxLayout1.addLayout(line_layout)

        # Define o estado padrão dos RadioButton para 'srp' com base no valor existente
        srp = self.dados.get('srp')
        if srp is not None:
            srp = srp.strip().lower()  # Certifique-se de que o srp é uma string e não None antes de chamar strip
        else:
            srp = ''  # Defina srp como string vazia se for None

        if srp == 'sim':
            self.radio_srp_sim.setChecked(True)
        elif srp == 'não':
            self.radio_srp_nao.setChecked(True)
        else:
            # Nenhuma opção selecionada se não houver dados claros ou deixar uma opção padrão
            self.radio_srp_nao.setChecked(False)
            self.radio_srp_sim.setChecked(False)

    def inserir_valor_total(self):
        # Cria o RealLineEdit com o valor inicial formatado ou vazio
        valor_total = self.dados.get('valor_total', '')
        self.line_edit_valor_total = RealLineEdit(str(valor_total) if pd.notna(valor_total) else "")

        # Usar o layout correto
        label = QLabel("Valor Total:")
        label.setFont(QFont("Arial", 14))
        self.vBoxLayout4.addWidget(label)
        self.vBoxLayout4.addWidget(self.line_edit_valor_total)

    def definir_objeto(self):
        layout = QVBoxLayout()  # Layout principal para os componentes de objeto

        # Criando e configurando o QLineEdit para 'objeto'
        label_objeto = QLabel("Objeto:")
        self.line_edit_objeto = QLineEdit()
        self.line_edit_objeto.setText(self.dados.get('objeto', ''))
        self.line_edit_objeto.setReadOnly(False)
        # Aplicar estilo específico para o campo 'objeto'
        self.line_edit_objeto.setStyleSheet("QLineEdit { font-weight: bold; }")
        layout.addWidget(label_objeto)
        layout.addWidget(self.line_edit_objeto)
        self.line_edits['objeto'] = self.line_edit_objeto

        # Criando e configurando o QTextEdit para 'objeto_completo'
        label_objeto_completo = QLabel("Objeto Completo:")
        self.text_edit_objeto_completo = QTextEdit()
        self.text_edit_objeto_completo.setText(self.dados.get('objeto_completo', ''))
        self.text_edit_objeto_completo.setReadOnly(False)
        self.text_edit_objeto_completo.setFixedHeight(50)  # Define a altura para aproximadamente 2 linhas
        layout.addWidget(label_objeto_completo)
        layout.addWidget(self.text_edit_objeto_completo)
        self.line_edits['objeto_completo'] = self.text_edit_objeto_completo

        # Adicionar o layout ao layout principal da janela/dialogo
        self.vBoxLayout4.addLayout(layout)

    def connect_data_signals(self):
        # Conecte sinais de mudança relevantes ao slot handle_data_change
        self.nup_edit.textChanged.connect(self.handle_data_change)
        self.item_pca_edit.textChanged.connect(self.handle_data_change)
        self.portaria_pca_edit.textChanged.connect(self.handle_data_change)

    def handle_data_change(self):
        # Marca que os dados foram alterados e habilita o botão de salvar, por exemplo
        self.dados_modificados = True

    def combo_uasg_om(self):
        # Configuração dos campos sigla_om, uasg e orgao_responsavel
        self.combo_sigla_om = QComboBox()
        self.line_edit_uasg = QLineEdit()
        self.line_edit_orgao = QLineEdit()

        # Definir os campos UASG e Orgao como somente leitura
        self.line_edit_uasg.setReadOnly(True)
        self.line_edit_orgao.setReadOnly(True)

        # Ajustar políticas de tamanho para serem expansíveis
        self.combo_sigla_om.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.line_edit_uasg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Conectar o sinal de mudança de índice do combo box à função de atualização
        self.combo_sigla_om.currentIndexChanged.connect(self.on_combo_change)

        # Criando layouts verticais para cada grupo de label e widget
        sigla_layout = QVBoxLayout()
        sigla_layout.addWidget(QLabel('Sigla da OM Responsável pelo Planejamento:'))
        sigla_layout.addWidget(self.combo_sigla_om)

        # Criando um layout horizontal para agrupar os layouts verticais
        h_layout = QHBoxLayout()
        h_layout.addLayout(sigla_layout)

        # Adicionar o layout horizontal ao layout vertical principal
        self.vBoxLayout2.addLayout(h_layout)

        # Adicionar campos 'setor_responsavel' e 'coordenador_planejamento'
        self.line_edit_setor_responsavel = QLineEdit(self.dados.get('setor_responsavel', ''))
        self.vBoxLayout2.addWidget(QLabel('Setor Responsável pelo Planejamento:'))
        self.vBoxLayout2.addWidget(self.line_edit_setor_responsavel)
        self.line_edits['setor_responsavel'] = self.line_edit_setor_responsavel 

        self.line_edit_coordenador_planejamento = QLineEdit(self.dados.get('coordenador_planejamento', ''))
        self.vBoxLayout2.addWidget(QLabel('Coordenador da Equipe de Planejamento:'))
        self.vBoxLayout2.addWidget(self.line_edit_coordenador_planejamento)
        self.line_edits['coordenador_planejamento'] = self.line_edit_coordenador_planejamento 

    def definir_irp(self):
        # Layout principal para os componentes desta seção
        layout = QVBoxLayout()

        # QHBoxLayout para msg_irp e num_irp
        irp_text_layout = QHBoxLayout()
        
        # QVBoxLayout para 'msg_irp'
        msg_irp_layout = QHBoxLayout()
        label_msg_irp = QLabel("Data/Hora MSG:")
        self.line_edit_msg_irp = QLineEdit()
        self.line_edit_msg_irp.setText(self.dados.get('msg_irp', ''))
        msg_irp_layout.addWidget(label_msg_irp)
        msg_irp_layout.addWidget(self.line_edit_msg_irp)
        irp_text_layout.addLayout(msg_irp_layout)
        self.line_edits['msg_irp'] = self.line_edit_msg_irp

        # QVBoxLayout para 'num_irp'
        num_irp_layout = QHBoxLayout()
        label_num_irp = QLabel("Número IRP:")
        self.line_edit_num_irp = QLineEdit()
        self.line_edit_num_irp.setText(self.dados.get('num_irp', ''))
        num_irp_layout.addWidget(label_num_irp)
        num_irp_layout.addWidget(self.line_edit_num_irp)
        irp_text_layout.addLayout(num_irp_layout)
        self.line_edits['num_irp'] = self.line_edit_num_irp

        # Adicionar o QHBoxLayout de textos ao layout principal
        layout.addLayout(irp_text_layout)

        # QHBoxLayout para data_limite_manifestacao_irp e data_limite_confirmacao_irp
        irp_date_layout = QHBoxLayout()

        # Data fields that require date edit controls
        date_fields = {
            'data_limite_manifestacao_irp': "Limite para Manifestação",
            'data_limite_confirmacao_irp': "Limite para Confirmação"
        }

        for field, label_text in date_fields.items():
            date_layout = QHBoxLayout()
            label = QLabel(label_text + ':')
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_str = self.dados.get(field)
            valid_date = self.validate_and_convert_date(date_str)
            if valid_date:
                date_edit.setDate(valid_date)
            else:
                date_edit.setDate(QDate.currentDate())
            date_layout.addWidget(label)
            date_layout.addWidget(date_edit)
            irp_date_layout.addLayout(date_layout)
            self.date_edits[field] = date_edit  

        # Adicionar o QHBoxLayout de datas ao layout principal
        layout.addLayout(irp_date_layout)

        # Adicionando campo para OM Participantes
        om_participantes_layout = QVBoxLayout()
        label_om_participantes = QLabel("Organizações Participantes:")
        self.line_edit_om_participantes = QLineEdit()
        valor_om_participantes = self.dados.get('om_participantes', None) or ''
        self.line_edit_om_participantes.setText(valor_om_participantes)
        self.line_edit_om_participantes.setPlaceholderText("Exemplo: CeIMBra, CIAB, Com7ºDN, ERMB, HNBra, etc")

        om_participantes_layout.addWidget(label_om_participantes)
        om_participantes_layout.addWidget(self.line_edit_om_participantes)

        # Adicionar layout de OM Participantes ao layout principal
        layout.addLayout(om_participantes_layout)
        
        # Adicionar o layout completo ao layout principal da janela/dialogo
        self.vBoxLayout3.addLayout(layout)

    def definir_links(self):
        layout = QVBoxLayout()  # Layout principal para os componentes desta seção

        label_link_pncp = QLabel("Link PNCP:")
        self.line_edit_link_pncp = QLineEdit()
        self.line_edit_link_pncp.setText(self.dados.get('link_pncp', ''))
        layout.addWidget(label_link_pncp)
        layout.addWidget(self.line_edit_link_pncp)

        label_link_portal_marinha = QLabel("Link Portal de Licitações da Marinha:")
        self.line_edit_link_portal_marinha = QLineEdit()
        self.line_edit_link_portal_marinha.setText(self.dados.get('link_portal_marinha', ''))
        layout.addWidget(label_link_portal_marinha)
        layout.addWidget(self.line_edit_link_portal_marinha)
        # Adicionar o layout ao layout principal da janela/dialogo
        self.vBoxLayout5.addLayout(layout)

    def definir_pregoeiro_data_sessao_parecerAGU(self):
        layout = QVBoxLayout()  # Layout principal para os componentes desta seção

        label_parecer = QLabel("Parecer AGU:")
        self.line_edit_parecer = QLineEdit()
        self.line_edit_parecer.setText(self.dados.get('parecer_agu', ''))
        layout.addWidget(label_parecer)
        layout.addWidget(self.line_edit_parecer)
        
        # Criando e configurando QLineEdit para 'Pregoeiro'
        label_pregoeiro = QLabel("Pregoeiro:")
        self.line_edit_pregoeiro = QLineEdit()
        self.line_edit_pregoeiro.setText(self.dados.get('pregoeiro', ''))
        layout.addWidget(label_pregoeiro)
        layout.addWidget(self.line_edit_pregoeiro)

        # Criando e configurando QDateEdit para 'data_sessao'
        label_data_sessao = QLabel("Data da Sessão:")
        self.date_sessao_edit = QDateEdit()
        self.date_sessao_edit.setCalendarPopup(True)
        date_sessao_str = self.dados.get('data_sessao', '')
        valid_date = self.validate_and_convert_date(date_sessao_str)
        if valid_date:
            self.date_sessao_edit.setDate(valid_date)
        else:
            self.date_sessao_edit.setDate(QDate.currentDate())  # Define para hoje se a data for inválida
        self.date_edits['data_sessao'] = self.date_sessao_edit
    
        layout.addWidget(label_data_sessao)
        layout.addWidget(self.date_sessao_edit)
        # Adicionar o layout ao layout principal da janela/dialogo
        self.vBoxLayout4.addLayout(layout)

    def definir_comentarios(self):
        label = QLabel("Comentários:")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        self.listWidget_comentarios = QListWidget()
        self.listWidget_comentarios.setFont(QFont("Arial", 12))
        self.listWidget_comentarios.setWordWrap(True)
        self.listWidget_comentarios.setFixedWidth(430)

        delegate = TextEditDelegate()
        self.listWidget_comentarios.setItemDelegate(delegate)
        self.listWidget_comentarios.itemChanged.connect(self.salvar_comentarios_editados)

        comentarios = self.carregar_comentarios()
        for comentario in comentarios:
            item = QListWidgetItem(comentario)
            item.setIcon(QIcon(str(ICONS_DIR / "checked.png")))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.listWidget_comentarios.addItem(item)

        label_novo_comentario = QLabel("Campo de edição de Comentário:")
        label_novo_comentario.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.textEdit_novo_comentario = QTextEdit()
        self.textEdit_novo_comentario.setPlaceholderText("Adicione um novo comentário aqui...")
        self.textEdit_novo_comentario.setFont(QFont("Arial", 12))

        buttonsLayout = QHBoxLayout()

        # Caminhos para os ícones
        icon_add = QIcon(str(ICONS_DIR / "add_comment.png"))
        icon_exclude = QIcon(str(ICONS_DIR / "delete_comment.png"))

        self.button_adicionar_comentario = QPushButton("Adicionar Comentário")
        self.button_adicionar_comentario.setIcon(icon_add)
        self.button_excluir_comentario = QPushButton("Excluir Comentário")
        self.button_excluir_comentario.setIcon(icon_exclude)

        buttonsLayout.addWidget(self.button_adicionar_comentario)
        buttonsLayout.addWidget(self.button_excluir_comentario)

        button_font = QFont("Arial", 12)
        self.button_adicionar_comentario.setFont(button_font)
        self.button_excluir_comentario.setFont(button_font)
        
        self.button_adicionar_comentario.clicked.connect(self.adicionar_comentario)
        self.button_excluir_comentario.clicked.connect(self.excluir_comentario)

        self.vBoxLayout5.addWidget(label_novo_comentario)
        self.vBoxLayout5.addWidget(self.textEdit_novo_comentario)
        self.vBoxLayout5.addLayout(buttonsLayout)
        self.vBoxLayout6.addWidget(label)
        self.vBoxLayout6.addWidget(self.listWidget_comentarios)

    def salvar_comentarios_editados(self):
        comentarios = [self.listWidget_comentarios.item(i).text() for i in range(self.listWidget_comentarios.count())]
        comentarios_str = '|||'.join(comentarios)  # Concatena todos os comentários com "|||"
        print(f"Salvando os seguintes comentários no banco de dados {self.database_path}: {comentarios_str}")

        with DatabaseManager(self.database_path) as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE controle_processos SET comentarios = ? WHERE id = ?", (comentarios_str, self.dados['id']))
            connection.commit()
            print("Comentários salvos com sucesso.")

    def adicionar_comentario(self):
        novo_comentario = self.textEdit_novo_comentario.toPlainText().strip()
        if novo_comentario:
            item = QListWidgetItem(novo_comentario)
            item.setIcon(QIcon(str(ICONS_DIR / "checked.png")))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.listWidget_comentarios.addItem(item)
            self.textEdit_novo_comentario.clear()
            self.salvar_comentarios()

    def excluir_comentario(self):
        item = self.listWidget_comentarios.currentItem()
        if item:
            self.listWidget_comentarios.takeItem(self.listWidget_comentarios.row(item))
            # Reordenar comentários (neste caso, apenas manter os ícones e textos dos comentários)
            for index in range(self.listWidget_comentarios.count()):
                item = self.listWidget_comentarios.item(index)
                # Manter o ícone e o texto do comentário
                item.setIcon(QIcon(str(ICONS_DIR / "checked.png")))
            self.salvar_comentarios()

    def carregar_comentarios(self):
        with DatabaseManager(self.database_path) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT comentarios FROM controle_processos WHERE id_processo = ?", (self.dados['id_processo'],))
            row = cursor.fetchone()
            if row and row[0]:
                # Divide os comentários com base no delimitador "|||"
                return row[0].split("|||")
            return []

    def salvar_comentarios(self):
        # Esta função deve salvar apenas o texto dos comentários, sem os números.
        comentarios = [self.listWidget_comentarios.item(i).text() for i in range(self.listWidget_comentarios.count())]
        comentarios_str = '|||'.join(comentarios)  # Concatena todos os comentários com "|||"
        print(f"Salvando os seguintes comentários no banco de dados {self.database_path}: {comentarios_str}")

        with DatabaseManager(self.database_path) as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE controle_processos SET comentarios = ? WHERE id_processo = ?", (comentarios_str, self.dados['id_processo']))
            connection.commit()
            print("Comentários salvos com sucesso.")

    def createConfirmButton(self):
        icon_size = QSize(40, 40)  # Tamanho do ícone para todos os botões
        button_spec = ("Salvar Alterações", self.image_cache['confirm'], self.confirmar_edicao, "Confirmar Edição", icon_size)
        
        text, icon, callback, tooltip, icon_size = button_spec
        btn = create_button_2(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self, icon_size=icon_size)
        
        return btn

    def applyStyleSheet(self):
        style = """
            QGroupBox {
                font-size: 16px;
            }
            QLabel, QLineEdit, QComboBox, QRadioButton, QDateEdit, QTextEdit{
                font-size: 16px;
            }
        """
        self.setStyleSheet(style)

    def handle_database_dir_update(self, new_dir):
        global CONTROLE_DADOS
        CONTROLE_DADOS = new_dir
        save_config("CONTROLE_DADOS", str(new_dir))
        self.database_path = new_dir
        self.database_manager = DatabaseManager(new_dir)
        QMessageBox.information(self, "Atualização de Diretório", "Diretório do banco de dados atualizado para: " + str(new_dir))

    def gerar_relatorio(self):
        # Aqui você pode definir a lógica para gerar um relatório
        print("Gerando relatório...")  # Substitua por sua lógica de relatório
        
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
        with self.database_manager as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT sigla_om, uasg, orgao_responsavel FROM controle_om")
            rows = cursor.fetchall()

        index_to_set = 0
        for index, (sigla_om, uasg, orgao) in enumerate(rows):
            self.combo_sigla_om.addItem(sigla_om, (uasg, orgao))
            if sigla_om == self.dados['sigla_om']:
                index_to_set = index

        self.combo_sigla_om.setCurrentIndex(index_to_set)
        self.combo_sigla_om.currentIndexChanged.connect(self.on_combo_change)  # Conectar sinal

    def on_combo_change(self, index):
        current_data = self.combo_sigla_om.itemData(index)
        if current_data:
            self.uasg = current_data[0]  # Armazenar UASG
            self.orgao_responsavel = current_data[1]  # Armazenar Órgão Responsável
            self.update_title_label(self.orgao_responsavel, self.uasg)  # Atualiza o título conforme seleção

    def confirmar_edicao(self):
        print(f"Confirmando edição usando banco de dados em: {self.database_path}")
        with self.database_manager as connection:
            cursor = connection.cursor()

            # Diretamente coletar os valores dos QLineEdit e checkboxes
            dados_atualizados = {
                'nup': self.nup_edit.text().strip(),
                'objeto': self.line_edit_objeto.text().strip(),
                'objeto_completo': self.text_edit_objeto_completo.toPlainText().strip(),
                'valor_total': self.line_edit_valor_total.text().strip(),
                'uasg': self.uasg,
                'orgao_responsavel': self.orgao_responsavel,
                'sigla_om': self.combo_sigla_om.currentText().strip(),
                'msg_irp': self.line_edit_msg_irp.text().strip(),
                'num_irp': self.line_edit_num_irp.text().strip(),
                'item_pca': self.item_pca_edit.text().strip(),
                'portaria_PCA': self.portaria_pca_edit.text().strip(),
                'om_participantes': self.line_edit_om_participantes.text().strip(),
                'link_pncp': self.line_edit_link_pncp.text().strip(),
                'link_portal_marinha': self.line_edit_link_portal_marinha.text().strip(),
                'parecer_agu': self.line_edit_parecer.text().strip(),
                'pregoeiro': self.line_edit_pregoeiro.text().strip(),
                'setor_responsavel': self.line_edit_setor_responsavel.text().strip(),
                'coordenador_planejamento': self.line_edit_coordenador_planejamento.text().strip(),
                'prioridade': 1 if self.prioritario_checkbox.isChecked() else 0,  # Salvar o estado do checkbox de prioridade
                'emenda_parlamentar': 1 if self.emenda_parlamentar_checkbox.isChecked() else 0  # Salvar o estado do checkbox de emenda parlamentar
            }

            # Atualizações de data
            dados_atualizados.update({date_field: self.date_edits[date_field].date().toString("yyyy-MM-dd") for date_field in self.date_edits})
            dados_atualizados['material_servico'] = 'servico' if self.radio_servico.isChecked() else 'material'
            dados_atualizados['srp'] = 'Sim' if self.radio_srp_sim.isChecked() else 'Não'

            # Preparação da consulta SQL
            set_part = ', '.join([f"{coluna} = ?" for coluna in dados_atualizados.keys()])
            valores = list(dados_atualizados.values())
            valores.append(self.dados['id_processo'])  # ID do registro a ser atualizado

            query = f"UPDATE controle_processos SET {set_part} WHERE id_processo = ?"
            cursor.execute(query, valores)
            connection.commit()

        self.dados_atualizados.emit()
        self.accept()
        QMessageBox.information(self, "Atualização", "As alterações foram salvas com sucesso.")


class RealLineEdit(QLineEdit):
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setText(self.format_to_real(self.text()))

    def focusInEvent(self, event):
        # Remove the currency formatting when the user focuses on the widget
        self.setText(self.format_to_plain_number(self.text()))
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        # Add the currency formatting when the user leaves the widget
        self.setText(self.format_to_real(self.text()))
        super().focusOutEvent(event)
    
    def format_to_real(self, value):
        try:
            # Convert the plain number to real currency format
            value = float(value.replace('.', '').replace(',', '.').replace('R$', '').strip())
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except ValueError:
            # Retorna o valor original se a conversão falhar, mantendo valores não numéricos intactos
            return "R$ 0,00" if not value else value
    
    def format_to_plain_number(self, value):
        try:
            # Convert the real currency format to plain number
            value = float(value.replace('R$', '').replace('.', '').replace(',', '.').strip())
            return f"{value:.2f}".replace('.', ',')
        except ValueError:
            # Retorna o valor original se a conversão falhar, mantendo valores não numéricos intactos
            return value
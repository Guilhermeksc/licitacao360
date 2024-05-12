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
from planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_processos,extrair_chave_processo, carregar_dados_pregao

class EditarDadosDialog(QDialog):
    dados_atualizados = pyqtSignal()

    def __init__(self, parent=None, dados=None):
        super().__init__(parent)
        self.dados = dados or {}
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  # Configura o locale para português do Brasil
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        self.setupUI()
        self.init_combobox_data()

    def setupUI(self):
        self.setWindowTitle("Editar Dados")
        self.setObjectName("EditarDadosDialog")
        self.setStyleSheet("#EditarDadosDialog { background-color: #050f41; }")
        self.setGeometry(300, 300, 900, 700)
        self.titleLabel = QLabel()
        self.update_title_label(self.dados.get('orgao_responsavel', ''), self.dados.get('uasg', ''))
        self.createFormLayout()
        self.createButtons()
        self.applyStyleSheet()

    def update_title_label(self, orgao_responsavel, uasg):
        self.titleLabel.setText(
            f"{self.dados['tipo']} nº {self.dados['numero']}/{self.dados['ano']} - Edição de Dados<br>"
            f"<span style='font-size: 20px; color: #ADD8E6;'>OM RESPONSÁVEL: {orgao_responsavel} (UASG: {uasg})</span>"
        )
        self.titleLabel.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")

    def createFormLayout(self):
        self.layout = QVBoxLayout(self)  
        self.layout.addLayout(self._create_header_layout(self.dados['tipo'], self.dados['numero'], self.dados['ano'], self.dados['id_processo']))        
        self.groupBox = QGroupBox('Índices das Variáveis')
        self.layout.addWidget(self.groupBox)

        # Layout principal dentro do groupBox deve ser um QVBoxLayout para gerenciar o conteúdo verticalmente
        self.mainLayout = QVBoxLayout()
        self.groupBox.setLayout(self.mainLayout)

        # Criar QVBoxLayout para organizar as linhas de QHBoxLayouts
        self.boxLayout = QVBoxLayout()

        # Criar o primeiro QHBoxLayout para conter os primeiros dois QFrames
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
        self.mainLayout.addLayout(self.boxLayout)

        # Adicionar métodos de componentes aos layouts verticais
        self.identificar_processo()
        self.item_pca()
        self.material_servico()
        self.definir_srp()
        self.definir_objeto()
        self.inserir_valor_total()
        self.combo_uasg_om()
        self.definir_irp()
        self.definir_comentarios()
        self.definir_pregoeiro_data_sessao()
        
        # Spacer para manter tudo alinhado ao topo
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.mainLayout.addSpacerItem(self.spacer)

    def _create_header_layout(self, tipo, numero, ano, id_processo):
        header_layout = QHBoxLayout()
        
        # Configuração e estilização do titleLabel já definida no construtor/init
        header_layout.addWidget(self.titleLabel)
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Configuração da imagem (se necessário)
        pixmap = QPixmap(str(MARINHA_PATH))
        pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        header_layout.addWidget(image_label)
        
        return header_layout

    def identificar_processo(self):
        # Criar o layout vertical principal para esta seção
        processo_layout = QVBoxLayout()

        # Layout horizontal para 'Número', 'Ano' e 'ID do Processo'
        detalhes_layout = QHBoxLayout()

        id_layout = QVBoxLayout()
        id_processo_label = QLabel("ID do Processo:")
        id_processo_edit = QLineEdit()
        id_processo_edit.setText(self.dados.get('id_processo', ''))
        id_processo_edit.setReadOnly(True)
        id_processo_edit.setFixedWidth(200)
        id_layout.addWidget(id_processo_label)
        id_layout.addWidget(id_processo_edit)

        nup_layout = QVBoxLayout()
        nup_label = QLabel("NUP:")
        nup_edit = QLineEdit()
        nup_edit.setText(self.dados.get('nup', ''))
        nup_edit.setReadOnly(False)
        nup_edit.setFixedWidth(180)
        nup_layout.addWidget(nup_label)
        nup_layout.addWidget(nup_edit)

        detalhes_layout.addLayout(id_layout)
        detalhes_layout.addLayout(nup_layout)

        # Adicionar um QSpacerItem no final para empurrar tudo para a esquerda
        end_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        detalhes_layout.addSpacerItem(end_spacer)

        # Adicionar o layout horizontal ao layout vertical principal
        processo_layout.addLayout(detalhes_layout)

        # Adicionar o layout completo ao layout principal da janela/dialogo
        self.vBoxLayout1.addLayout(processo_layout)
    
    def item_pca(self):
        pca_layout = QHBoxLayout()

        item_pca_layout = QVBoxLayout()

        item_pca_label = QLabel("Item PCA:")
        item_pca_edit = QLineEdit()
        item_pca_edit.setText(self.dados.get('item_pca', ''))
        item_pca_edit.setReadOnly(False)
        item_pca_edit.setFixedWidth(70)
        item_pca_layout.addWidget(item_pca_label)
        item_pca_layout.addWidget(item_pca_edit)

        portaria_pca_layout = QVBoxLayout()

        portaria_pca_label = QLabel("Portaria PCA:")
        portaria_pca_edit = QLineEdit()
        portaria_pca_edit.setText(self.dados.get('portaria_pca', ''))
        portaria_pca_edit.setReadOnly(False)
        portaria_pca_layout.addWidget(portaria_pca_label)
        portaria_pca_layout.addWidget(portaria_pca_edit)

        pca_layout.addLayout(item_pca_layout)
        pca_layout.addLayout(portaria_pca_layout)

        self.vBoxLayout1.addLayout(pca_layout)

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

        # Define o estado padrão dos RadioButton para 'srp' com base no valor de 'tipo'
        tipo = self.dados.get('tipo', '')
        if tipo == 'Pregão Eletrônico':
            self.radio_srp_sim.setChecked(True)
        else:
            self.radio_srp_nao.setChecked(True)

    def inserir_valor_total(self):
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

        # Usar o layout correto
        label = QLabel("Valor Total:")
        label.setFont(QFont("Arial", 14))
        self.vBoxLayout4.addWidget(label)
        self.vBoxLayout4.addWidget(self.line_edit_valor_total)

    def definir_objeto(self):
        layout = QVBoxLayout()  # Layout principal para os componentes de objeto

        # Criando e configurando o QLineEdit para 'objeto'
        label_objeto = QLabel("Objeto:")
        line_edit_objeto = QLineEdit()
        line_edit_objeto.setText(self.dados.get('objeto', ''))
        line_edit_objeto.setReadOnly(False)
        # Aplicar estilo específico para o campo 'objeto'
        line_edit_objeto.setStyleSheet("QLineEdit { color: darkblue; font-weight: bold; }")
        layout.addWidget(label_objeto)
        layout.addWidget(line_edit_objeto)

        # Criando e configurando o QTextEdit para 'objeto_completo'
        label_objeto_completo = QLabel("Objeto Completo:")
        text_edit_objeto_completo = QTextEdit()
        text_edit_objeto_completo.setText(self.dados.get('objeto_completo', ''))
        text_edit_objeto_completo.setReadOnly(False)
        text_edit_objeto_completo.setFixedHeight(50)  # Define a altura para aproximadamente 2 linhas
        layout.addWidget(label_objeto_completo)
        layout.addWidget(text_edit_objeto_completo)

        # Adicionar o layout ao layout principal da janela/dialogo
        self.vBoxLayout4.addLayout(layout)
        
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

        self.line_edit_coordenador_planejamento = QLineEdit(self.dados.get('coordenador_planejamento', ''))
        self.vBoxLayout2.addWidget(QLabel('Coordenador da Equipe de Planejamento:'))
        self.vBoxLayout2.addWidget(self.line_edit_coordenador_planejamento)

        # Inicializar os dados do ComboBox após adicionar ao layout
        self.init_combobox_data()

    def definir_irp(self):
        # Layout principal para os componentes desta seção
        layout = QVBoxLayout()

        # QHBoxLayout para msg_irp e num_irp
        irp_text_layout = QHBoxLayout()
        
        # QVBoxLayout para 'msg_irp'
        msg_irp_layout = QVBoxLayout()
        label_msg_irp = QLabel("Mensagem IRP:")
        line_edit_msg_irp = QLineEdit()
        line_edit_msg_irp.setText(self.dados.get('msg_irp', ''))
        msg_irp_layout.addWidget(label_msg_irp)
        msg_irp_layout.addWidget(line_edit_msg_irp)
        irp_text_layout.addLayout(msg_irp_layout)

        # QVBoxLayout para 'num_irp'
        num_irp_layout = QVBoxLayout()
        label_num_irp = QLabel("Número IRP:")
        line_edit_num_irp = QLineEdit()
        line_edit_num_irp.setText(self.dados.get('num_irp', ''))
        num_irp_layout.addWidget(label_num_irp)
        num_irp_layout.addWidget(line_edit_num_irp)
        irp_text_layout.addLayout(num_irp_layout)

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
            date_layout = QVBoxLayout()
            label = QLabel(label_text + ':')
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_str = self.dados.get(field)
            valid_date = self.validate_and_convert_date(date_str)
            if valid_date:
                date_edit.setDate(valid_date)
            else:
                date_edit.setDate(QDate.currentDate())  # Define para hoje se a data for inválida

            date_layout.addWidget(label)
            date_layout.addWidget(date_edit)
            irp_date_layout.addLayout(date_layout)
            # self.date_edits[field] = date_edit  # Store date edit for future reference

        # Adicionar o QHBoxLayout de datas ao layout principal
        layout.addLayout(irp_date_layout)

        # Adicionando campo para OM Participantes
        om_participantes_layout = QVBoxLayout()
        label_om_participantes = QLabel("Organizações Participantes:")
        line_edit_om_participantes = QLineEdit()
        line_edit_om_participantes.setText(self.dados.get('om_participantes', ''))
        line_edit_om_participantes.setPlaceholderText("Exemplo: CeIMBra, CIAB, Com7ºDN, ERMB, HNBra, etc")
        om_participantes_layout.addWidget(label_om_participantes)
        om_participantes_layout.addWidget(line_edit_om_participantes)

        # Adicionar layout de OM Participantes ao layout principal
        layout.addLayout(om_participantes_layout)
        
        # Adicionar o layout completo ao layout principal da janela/dialogo
        self.vBoxLayout3.addLayout(layout)
            
    def definir_pregoeiro_data_sessao(self):
        layout = QVBoxLayout()  # Layout principal para os componentes desta seção

        # Criando e configurando QLineEdit para 'Pregoeiro'
        label_pregoeiro = QLabel("Pregoeiro:")
        line_edit_pregoeiro = QLineEdit()
        line_edit_pregoeiro.setText(self.dados.get('pregoeiro', ''))
        layout.addWidget(label_pregoeiro)
        layout.addWidget(line_edit_pregoeiro)

        # Criando e configurando QDateEdit para 'data_sessao'
        label_data_sessao = QLabel("Data da Sessão:")
        date_sessao_edit = QDateEdit()
        date_sessao_edit.setCalendarPopup(True)
        date_sessao_str = self.dados.get('data_sessao', '')
        valid_date = self.validate_and_convert_date(date_sessao_str)
        if valid_date:
            date_sessao_edit.setDate(valid_date)
        else:
            date_sessao_edit.setDate(QDate.currentDate())  # Define para hoje se a data for inválida

        layout.addWidget(label_data_sessao)
        layout.addWidget(date_sessao_edit)

        # Adicionar o layout ao layout principal da janela/dialogo
        self.vBoxLayout4.addLayout(layout)

    def definir_comentarios(self):
        label = QLabel("Comentários:")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        self.listWidget_comentarios = QListWidget()
        self.listWidget_comentarios.setFont(QFont("Arial", 12))

        comentarios = self.carregar_comentarios()
        for i, comentario in enumerate(comentarios, start=1):
            self.listWidget_comentarios.addItem(f"{i}º comentário: {comentario}")

        self.textEdit_novo_comentario = QTextEdit()
        self.textEdit_novo_comentario.setPlaceholderText("Adicione um novo comentário aqui...")
        self.textEdit_novo_comentario.setFont(QFont("Arial", 12))

        self.button_adicionar_comentario = QPushButton("Adicionar Comentário")
        self.button_adicionar_comentario.clicked.connect(self.adicionar_comentario)

        self.button_excluir_comentario = QPushButton("Excluir Comentário")
        self.button_excluir_comentario.clicked.connect(self.excluir_comentario)

        self.vBoxLayout5.addWidget(label)
        self.vBoxLayout5.addWidget(self.listWidget_comentarios)
        self.vBoxLayout5.addWidget(self.textEdit_novo_comentario)
        self.vBoxLayout5.addWidget(self.button_adicionar_comentario)
        self.vBoxLayout5.addWidget(self.button_excluir_comentario)

    def adicionar_comentario(self):
        novo_comentario = self.textEdit_novo_comentario.toPlainText().strip()
        if novo_comentario:
            num_comentarios = self.listWidget_comentarios.count()
            self.listWidget_comentarios.addItem(f"{num_comentarios + 1}º comentário: {novo_comentario}")
            self.textEdit_novo_comentario.clear()
            self.salvar_comentarios()

    def excluir_comentario(self):
        item = self.listWidget_comentarios.currentItem()
        if item:
            self.listWidget_comentarios.takeItem(self.listWidget_comentarios.row(item))
            # Reordenar comentários
            for index in range(self.listWidget_comentarios.count()):
                item = self.listWidget_comentarios.item(index)
                item.setText(f"{index + 1}º comentário: {item.text().split(': ', 1)[1]}")
            self.salvar_comentarios()

    def salvar_comentarios(self):
        comentarios = [self.listWidget_comentarios.item(i).text().split(': ', 1)[1] for i in range(self.listWidget_comentarios.count())]
        comentarios_str = '\n'.join(comentarios)
        with DatabaseManager(self.database_path) as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE controle_processos SET comentarios = ? WHERE id = ?", (comentarios_str, self.dados['comentarios']))
            connection.commit()  # Garante que as mudanças sejam salvas

    def carregar_comentarios(self):
        with DatabaseManager(self.database_path) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT comentarios FROM controle_processos WHERE id = ?", (self.dados['comentarios'],))
            row = cursor.fetchone()
            if row and row[0]:
                return row[0].split('\n')  # Assume que os comentários estão separados por nova linha
        return []  # Retorna uma lista vazia se não houver comentários ou a consulta falhar

    def createButtons(self):
        self.btnConfirmar = QPushButton("Confirmar")
        self.btnConfirmar.clicked.connect(self.confirmarEdicao)
        
        # Adiciona o botão ao mainLayout, abaixo do QHBoxLayout
        self.mainLayout.addWidget(self.btnConfirmar)

    def applyStyleSheet(self):

        style = """
            #frame1, #frame2, #frame3, #frame4, #frame5, #frame6 {
                border: 1px solid black;
                border-radius: 10px;
                background-color: white;
                
            }
            #EditarDadosDialog { 
                background-color: #050f41; 
            }
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
            QLabel, QLineEdit, QComboBox, QRadioButton, QDateEdit, QTextEdit{
                font-size: 16px;
            }
            QLabel {
                font-weight: bold;
            }
            QLineEdit[readOnly="true"] {
                background-color: #cccccc;
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

    def confirmarEdicao(self):
        # Implemente a lógica para confirmar a edição aqui
        pass

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
            self.update_title_label(current_data[1], current_data[0])  # Atualiza o título conforme seleção


#     def confirmar_edicao(self):
#         print(f"Confirmando edição usando banco de dados em: {self.database_path}")  # Debug para verificar o caminho do banco
#         # Implementação da lógica para atualizar os dados
#         with self.database_manager as connection:  # Assegurar que 'connection' é a conexão, não o cursor
#             cursor = connection.cursor()
            
#             # Atualiza o dicionário com os valores dos line_edits regulares
#             dados_atualizados = {coluna: line_edit.text().strip() for coluna, line_edit in self.line_edits.items()}
#             dados_atualizados.update({date_col: date_edit.date().toString("yyyy-MM-dd").strip() for date_col, date_edit in self.date_edits.items()})
            
#             # Determine o valor de material_servico com base no RadioButton selecionado
#             material_servico = 'servico' if self.radio_servico.isChecked() else 'material'
#             dados_atualizados['material_servico'] = material_servico.strip()

#             # Adiciona 'sigla_om', 'uasg' e 'orgao_responsavel' ao dicionário de atualizações
#             dados_atualizados['valor_total'] = self.line_edit_valor_total.text().strip()
#             dados_atualizados['sigla_om'] = self.combo_sigla_om.currentText().strip()
#             dados_atualizados['uasg'] = self.line_edit_uasg.text().strip()
#             dados_atualizados['orgao_responsavel'] = self.line_edit_orgao.text().strip()

#             # Cria a parte SET da consulta SQL dinamicamente
#             set_part = ', '.join([f"{coluna} = ?" for coluna in dados_atualizados.keys()])
            
#             # Prepara a lista de valores para a consulta (inclui os valores seguidos pelo id no final)
#             valores = list(dados_atualizados.values())
#             valores.append(self.dados['id'])  # Assume que 'self.dados' contém um campo 'id' com o ID do registro a ser atualizado
            
#             # Constrói e executa a consulta SQL de UPDATE
#             query = f"UPDATE controle_processos SET {set_part} WHERE id = ?"
#             cursor.execute(query, valores)
#             connection.commit()  # Garante que a transação seja confirmada

#         # Emite o sinal de dados atualizados e fecha a caixa de diálogo
#         self.dados_atualizados.emit()
#         self.accept()

# class EditarDadosDialog(QDialog):
#     dados_atualizados = pyqtSignal()
    
#     def __init__(self, parent=None, dados=None):
#         super().__init__(parent)
#         self.setWindowTitle("Editar Dados")
#         self.setFixedSize(900, 700)
#         self.dados = dados or {}
#         locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  # Configura o locale para português do Brasil
#         self.config_manager = ConfigManager(BASE_DIR / "config.json")
#         self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
#         self.event_manager = EventManager()
#         self.event_manager.controle_dir_updated.connect(self.handle_database_dir_update)
#         self.database_manager = DatabaseManager(self.database_path)
#         self.init_ui()
#         self.init_combobox_data()

#     def init_ui(self):
#         self.groupBox = QGroupBox('Índices das Variáveis', self)
#         self.scrollArea = QScrollArea()
#         self.scrollContentWidget = QWidget()
#         self.scrollLayout = QFormLayout(self.scrollContentWidget)
#         self.scrollArea.setWidgetResizable(True)
#         self.scrollArea.setWidget(self.scrollContentWidget)
#         self.groupBoxLayout = QVBoxLayout(self.groupBox)
#         self.groupBoxLayout.addWidget(self.scrollArea)
#         self.mainLayout = QVBoxLayout(self)
#         self.mainLayout.addWidget(self.groupBox)
#         self.confirmar_button = QPushButton("Confirmar")
#         self.confirmar_button.clicked.connect(self.confirmar_edicao)
#         self.mainLayout.addWidget(self.confirmar_button)

#         self.initialize_fields()


#         # Criação de sub-layouts para esquerda e direita
#         self.date_edits = {}  # Dicionário para guardar os QDateEdit
#         leftLayout = QFormLayout()
#         rightLayout = QFormLayout()

#         # Campos à esquerda incluindo 'objeto' com estilo específico
        # leftFields = ["tipo", "numero", "ano", "id_processo", "nup", "objeto", "objeto_completo", "pregoeiro"]
        # for field in leftFields:
        #     line_edit = QLineEdit()
        #     value = self.dados.get(field, '')
        #     line_edit.setText(value)
        #     if field in ["tipo", "numero", "ano", "id_processo"]:  # Estes campos são ReadOnly
        #         line_edit.setReadOnly(True)
            # if field == "objeto":  # Aplica estilo específico para o campo 'objeto'
            #     line_edit.setStyleSheet("QLineEdit { color: darkblue; font-weight: bold; }")
            # self.line_edits[field] = line_edit
#             leftLayout.addRow(QLabel(field), line_edit)

#         # Data da sessão à esquerda
#         date_sessao_edit = QDateEdit()
#         date_sessao_edit.setCalendarPopup(True)
#         date_sessao_str = self.dados.get('data_sessao')
#         valid_date = self.validate_and_convert_date(date_sessao_str)
#         if valid_date:
#             date_sessao_edit.setDate(valid_date)
#         else:
#             date_sessao_edit.setDate(QDate.currentDate())  # Somente define para hoje se a data for inválida
#         leftLayout.addRow(QLabel('data_sessao'), date_sessao_edit)
#         self.date_edits['data_sessao'] = date_sessao_edit

#         # Campos à direita
#         rightFields = ["item_pca", "portaria_PCA", 
#                     "parecer_agu", "msg_irp", "num_irp", "om_participantes", 
#                     "link_pncp", "link_portal_marinha"]
#         for field in rightFields:
#             line_edit = QLineEdit()
#             value = self.dados.get(field, '')
#             line_edit.setText(value)
#             self.line_edits[field] = line_edit
#             rightLayout.addRow(QLabel(field), line_edit)

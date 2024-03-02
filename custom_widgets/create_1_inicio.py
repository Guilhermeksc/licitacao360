# create_1_inicio.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from diretorios import IMAGE_PATH
from styles.styless import get_transparent_title_style
from custom_widgets.create_configuracoes_button import ConfiguracoesDialog

class InicioWidget(QWidget):
    planejamentoClicked = pyqtSignal()
    fasesProcessoClicked = pyqtSignal()
    infoProcessoClicked = pyqtSignal()
    documentosLicitacaoClicked = pyqtSignal()
    controleVigenciaClicked = pyqtSignal()
    checklistClicked = pyqtSignal()
    escalacaoPregoeirosClicked = pyqtSignal()
    numeradorCpClicked = pyqtSignal()
    mensagensPadronizadasClicked = pyqtSignal()
    registroFornecedoresClicked = pyqtSignal()
    seleniumAutomacaoClicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.button_style = """
            QPushButton {
                font-size: 16px;
                padding: 10px;
                background-color: rgba(0, 0, 0, 0.2);
                font-weight: bold;
                color: white;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                text-decoration: none;
            }
            QPushButton:hover {
                color: rgb(0, 255, 255);
                background-color: rgba(0, 0, 0, 0.8);
                border: 1px solid rgba(0, 255, 255, 0.8);
                text-decoration: underline;
            }
        """
        self.layout = QVBoxLayout(self)
        self.initialize_buttons()
        self.setup_image_and_buttons()
        self.setup_quick_access_buttons()

    def initialize_buttons(self):
        # Inicialização dos botões
        self.button_planejamento = self.create_button("Planejamento", self.planejamentoClicked)
        self.button_fases_do_processo = self.create_button("Fases do\nProcesso", self.fasesProcessoClicked)
        # self.button_info_processo = self.create_button("Informações\ndo Processo", self.infoProcessoClicked)
        # self.button_documentos_licitacao = self.create_button("Documentos\nLicitação", self.documentosLicitacaoClicked)
        # self.button_controle_vigencia = self.create_button("Controle de\nVigência", self.controleVigenciaClicked)
        # self.button_checklist = self.create_button("Check-list", self.checklistClicked)
        # self.button_escalacao_pregoeiros = self.create_button("Escalação de\nPregoeiros", self.escalacaoPregoeirosClicked)
        # self.button_numerador_cp = self.create_button("Numerador\nde CP", self.numeradorCpClicked)
        # self.button_mensagens_padronizadas = self.create_button("Mensagens\nPadronizadas", self.mensagensPadronizadasClicked)
        # self.button_registro_fornecedores = self.create_button("Registro de\nFornecedores", self.registroFornecedoresClicked)
        # self.button_slides_conges = self.create_button("Conselho de\nGestão", self.configuracoesClicked)
        self.button_configuracoes = self.create_button("Configurações", self.configuracoesClicked)
        # self.button_links_uteis = self.create_button("Links\nÚteis", self.configuracoesClicked)

    def configuracoesClicked(self):
        self.dialog = ConfiguracoesDialog(self)
        self.dialog.exec()
        
    def create_button(self, text, signal):
        button = QPushButton(text)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        button.setStyleSheet(self.button_style)
        button.clicked.connect(signal)  # Conectar o botão diretamente ao método
        return button
    
    def setup_image_and_buttons(self):
        v_layout = QVBoxLayout()

        # QLabel para o título
        self.label_title = QLabel("Centro de Intendência da Marinha em Brasília\n(CeIMBra)")
        self.label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_title.setStyleSheet(get_transparent_title_style())
        v_layout.addWidget(self.label_title)

        # QLabel para a imagem
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(IMAGE_PATH / "ceimbra2.png"))  # Verifique se o caminho está correto
        self.image_label.setPixmap(pixmap.scaled(603, 400, Qt.AspectRatioMode.KeepAspectRatio))
        v_layout.addWidget(self.image_label)

        # Layout Horizontal para adicionar o layout vertical e os botões
        h_layout = QHBoxLayout()
        h_layout.addLayout(v_layout)
        self.layout.addLayout(h_layout)

    def setup_quick_access_buttons(self):
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)  # Espaçamento entre os botões

        # Adicionar botões ao grid layout
        grid_layout.addWidget(self.button_planejamento, 2, 0)
        grid_layout.addWidget(self.button_fases_do_processo, 2, 1)
        # grid_layout.addWidget(self.button_info_processo, 0, 2)
        # grid_layout.addWidget(self.button_documentos_licitacao, 0, 3)
        # grid_layout.addWidget(self.button_controle_vigencia, 0, 4)

        # grid_layout.addWidget(self.button_checklist, 1, 0)
        # grid_layout.addWidget(self.button_escalacao_pregoeiros, 1, 1)
        # grid_layout.addWidget(self.button_numerador_cp, 1, 2)
        # grid_layout.addWidget(self.button_mensagens_padronizadas, 1, 3)
        # grid_layout.addWidget(self.button_registro_fornecedores, 1, 4)

        # grid_layout.addWidget(self.button_slides_conges, 2, 3)
        grid_layout.addWidget(self.button_configuracoes, 2, 4)
        # grid_layout.addWidget(self.button_links_uteis, 2, 5)

        # Adicionar o grid layout ao layout principal
        self.layout.addLayout(grid_layout)

    def add_buttons_to_layout(self, layout, buttons):
        for button in buttons:
            layout.addWidget(button)
            # Conectar cada botão ao seu sinal correspondente
            signal_name = button.text().replace(" ", "") + 'Clicked'
            signal = getattr(self, signal_name, None)
            if signal:
                button.clicked.connect(signal.emit)



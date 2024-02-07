import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import pandas as pd
import re
from pathlib import Path
from datetime import datetime, timedelta
from styles.styless import get_transparent_title_style
from diretorios import *
from controle_contratos.painel_contratos import ContratosWidget

ETAPAS_CONTRATOS = ['CP/MSG', 'SEÇÃO DE CONTRATOS', 'NOTA TÉCNICA', 'AGU', 'TRAMITAÇÃO']

class ControleContratosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)  # Layout principal do widget
        self.etapas = {}  # Inicializa o dicionário para armazenar as referências dos widgets de cada etapa
        self.criar_widgets_processos()  # Chama o método para criar os widgets do processo
        self.carregar_dados_processos('caminho_para_o_seu_arquivo.csv')  # Carrega os dados dos processos

    def criar_widgets_processos(self):
        # Cria o container_frame com cor de fundo preta
        container_frame = QFrame()
        container_frame.setFrameShape(QFrame.Shape.StyledPanel)
        container_frame.setPalette(QPalette(QColor(240, 240, 240)))  

        container_frame.setAutoFillBackground(True)

        # Define o tamanho mínimo para o container_frame
        container_frame.setMinimumSize(600, 600)

        # Cria um QGridLayout para o container_frame
        self.blocks_layout = QGridLayout(container_frame)
        self.blocks_layout.setSpacing(5)  # Define o espaçamento entre os widgets
        self.blocks_layout.setContentsMargins(5, 0, 5, 0)  # Remove as margens internas
        
        # Cria uma QScrollArea e define suas propriedades para o container_frame
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container_frame)
        
        # Adiciona a QScrollArea ao layout principal do widget
        self.layout.addWidget(scroll_area)
        
        # Adiciona as etapas (blocos internos) ao layout
        for etapa in ETAPAS_CONTRATOS:
            self.adicionar_etapa(etapa)
        
        # Calcula a próxima linha disponível após adicionar todos os blocos internos
        total_etapas = len(ETAPAS_CONTRATOS)
        colunas_por_linha = 5  # Ou o número que você está usando
        next_row = (total_etapas // colunas_por_linha) * 2
        if total_etapas % colunas_por_linha != 0:
            next_row += 2  # Ajusta para o caso de haver etapas que não preencham completamente a última linha
        
        # Instancia ContratosWidget
        self.contratos_widget = ContratosWidget()
        
        # Adiciona o ContratosWidget ao QGridLayout do container_frame
        # Isso o coloca na linha imediatamente após os últimos blocos internos
        # Utiliza o método addWidget(widget, row, column, rowspan, colspan) para abranger todas as colunas
        self.blocks_layout.addWidget(self.contratos_widget, next_row, 0, 1, colunas_por_linha)

    def adicionar_etapa(self, etapa):
        total_etapas = len(ETAPAS_CONTRATOS)
        colunas_por_linha = 5  # Ajuste conforme necessário para a distribuição desejada
        row, col = divmod(ETAPAS_CONTRATOS.index(etapa), colunas_por_linha)
        self.createListWidgetForEtapa(etapa, row, col)

    def createListWidgetForEtapa(self, etapa, row, col):
        # Criar e configurar o QLabel para o título da etapa
        label = QLabel(f"<b>{etapa}</b>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        label.setFont(font)
        label.setWordWrap(True)
        label.setStyleSheet("QLabel { color : Black; }") 
        
        # Corrige a política de tamanho usando QSizePolicy.Policy
        label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # Adicionar o QLabel ao layout
        self.blocks_layout.addWidget(label, row * 2, col)

        # Criar CustomListWidget
        list_widget = CustomListWidget(self)
        list_widget.setObjectName(etapa)
        
        # Também corrige aqui para CustomListWidget, se necessário
        list_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        self.blocks_layout.addWidget(list_widget, row * 2 + 1, col)

        self.etapas[etapa] = list_widget

    def carregar_dados_processos(self, caminho_csv):
        try:
            self.dados_processos = pd.read_csv(caminho_csv)
            # Atualizar dados nos widgets aqui, se necessário
        except FileNotFoundError:
            print(f"Arquivo {caminho_csv} não encontrado. Iniciando com dados vazios.")
            self.dados_processos = pd.DataFrame(columns=ETAPAS_CONTRATOS)

class CustomListWidget(QListWidget):
    def __init__(self, controle_contratos_widget, parent=None):
        super().__init__(parent)
        self.controle_contratos_widget = controle_contratos_widget
        self.setFont(QFont("Arial", 14))  # Definindo a fonte para calcular a altura por linha

        # Calcula a altura de uma linha assumindo um tamanho de fonte de 16 e um fator de espaçamento de linha
        altura_linha = QFontMetrics(self.font()).height() * 1
        altura_maxima = int(altura_linha * 5)  # Altura para 10 linhas

        # Define o tamanho mínimo e máximo para garantir um tamanho fixo para 10 linhas
        self.setMinimumHeight(altura_maxima)
        self.setMaximumHeight(altura_maxima)

class DetalhesContratoDialog(QDialog):
    def __init__(self, detalhes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mensagem Cobrança")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # Campo de texto editável
        self.textEdit = QTextEdit()
        self.textEdit.setText(detalhes)
        self.textEdit.setReadOnly(False)  # Se desejar que o texto seja editável, defina como False
        layout.addWidget(self.textEdit)

        # Botão para copiar o texto para a área de transferência
        self.btnCopy = QPushButton("Copiar", self)
        self.btnCopy.clicked.connect(self.copyTextToClipboard)
        layout.addWidget(self.btnCopy)

    def copyTextToClipboard(self):
        text = self.textEdit.toPlainText()
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", "Texto copiado para a área de transferência.")
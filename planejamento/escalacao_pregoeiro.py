from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import pandas as pd
from datetime import datetime
df_uasg = pd.read_excel(TABELA_UASG_DIR)
global df_registro_selecionado
df_registro_selecionado = None
import json

ESCALACAO_PREGOEIROS_DIR = DATABASE_DIR / "pregoeiros.json"

class EscalarPregoeiroDialog(QDialog):
    def __init__(self, df_licitacao_completo, mod, ano_pregao, num_pregao, parent=None):
        super().__init__(parent)
        self.df_licitacao_completo = df_licitacao_completo
        self.mod = mod
        self.ano_pregao = ano_pregao
        self.num_pregao = num_pregao
        self.setWindowTitle(f"Escalar pregoeiro para o {self.mod} {self.num_pregao}/{self.ano_pregao}\n\n")
        self.setFixedSize(QSize(600, 400))

        # Inicializa a interface do usuário
        self.init_ui()

    def init_ui(self):
        # Cria o layout principal
        main_layout = QHBoxLayout()

        # Cria contêineres QWidget para as colunas esquerda e direita
        leftContainer = QWidget()
        rightContainer = QWidget()
        leftContainer.setObjectName("leftContainer")
        rightContainer.setObjectName("rightContainer")

        # Define os layouts para os contêineres
        left_column_layout = QVBoxLayout(leftContainer)
        right_column_layout = QVBoxLayout(rightContainer)

        # Configura os widgets para a coluna da esquerda
        cp_layout = QHBoxLayout()
        self.cp_label = QLabel("Número da Comunicação Padronizada (CP):")
        self.cp_input = QLineEdit()
        self.cp_input.setValidator(QIntValidator())
        cp_layout.addWidget(self.cp_label)
        cp_layout.addWidget(self.cp_input)

        selecao_pregoeiro_layout = QHBoxLayout()
        self.label_pregoeiro = QLabel("Escolher pregoeiro:")
        self.pregoeiro_combobox = QComboBox()
        selecao_pregoeiro_layout.addWidget(self.label_pregoeiro)
        selecao_pregoeiro_layout.addWidget(self.pregoeiro_combobox)
        self.load_pregoeiros()

        self.calendar = QCalendarWidget()
        # Remove a coluna das semanas do calendário
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        
        self.calendar_label = QLabel("Escolha a data da sessão pública:")
        
        self.generate_cp_button = QPushButton("Gerar CP")
        self.generate_cp_button.clicked.connect(self.on_generate_cp)

        left_column_layout.addLayout(cp_layout)
        left_column_layout.addLayout(selecao_pregoeiro_layout)
        left_column_layout.addWidget(self.calendar_label)
        left_column_layout.addWidget(self.calendar)
        left_column_layout.addWidget(self.generate_cp_button)

        # Define o tamanho preferido para os contêineres
        leftContainer.setFixedSize(320, 380)
        rightContainer.setFixedSize(240, 380)

        self.pregoeiro_counter_label = QLabel()
        self.update_pregoeiro_count()
        right_column_layout.addWidget(self.pregoeiro_counter_label)
        
        # Botões para adicionar, remover e visualizar pregoeiros
        self.view_pregoeiros_button = QPushButton("Visualizar Pregoeiros")
        self.add_pregoeiro_button = QPushButton("Adicionar Pregoeiro")
        self.remove_pregoeiro_button = QPushButton("Remover Pregoeiro")

        # Conexão dos botões aos slots
        self.view_pregoeiros_button.clicked.connect(self.view_pregoeiros)
        self.add_pregoeiro_button.clicked.connect(self.show_add_pregoeiro_dialog)
        self.remove_pregoeiro_button.clicked.connect(self.show_remove_pregoeiro_dialog)

        # Adiciona os novos botões ao layout principal
        right_column_layout.addWidget(self.view_pregoeiros_button)
        right_column_layout.addWidget(self.add_pregoeiro_button)
        right_column_layout.addWidget(self.remove_pregoeiro_button)

        # Define o layout dos contêineres e adiciona-os ao layout principal
        leftContainer.setLayout(left_column_layout)
        rightContainer.setLayout(right_column_layout)
        main_layout.addWidget(leftContainer)
        main_layout.addWidget(rightContainer)

        self.setLayout(main_layout)

        # Aplica a folha de estilo
        estiloBorda = """
        QWidget#leftContainer, QWidget#rightContainer {
            border: 1px solid rgb(173, 173, 173);
        }
        """
        self.setStyleSheet(estiloBorda)

    def load_pregoeiros(self):
        pregoeiros = self.read_pregoeiros_from_file()
        # Verifica se todos os itens são strings
        pregoeiros = [p for p in pregoeiros if isinstance(p, str)]
        self.pregoeiro_combobox.clear()  # Limpa o combobox antes de adicionar novos itens
        self.pregoeiro_combobox.addItems(pregoeiros)


    def read_pregoeiros_from_file(self):
        ESCALACAO_PREGOEIROS_DIR = DATABASE_DIR / "pregoeiros.json"
        if not ESCALACAO_PREGOEIROS_DIR.exists():
            self.write_pregoeiros_to_file([])  # Cria o arquivo com uma lista vazia
            return []
        with open(ESCALACAO_PREGOEIROS_DIR, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get("pregoeiros", [])
        return []

    def view_pregoeiros(self):
        pregoeiros = self.read_pregoeiros_from_file()
        # Filtra a lista para garantir que todos os itens sejam strings
        pregoeiros_str = [str(p) for p in pregoeiros if isinstance(p, str)]
        QMessageBox.information(self, "Pregoeiros", "\n".join(pregoeiros_str))

    def show_add_pregoeiro_dialog(self):
        nome_pregoeiro, okPressed = QInputDialog.getText(self, "Adicionar Pregoeiro", "Nome do Pregoeiro:")
        if okPressed and nome_pregoeiro != '':
            self.add_pregoeiro(nome_pregoeiro)

    def add_pregoeiro(self, nome_pregoeiro):
        pregoeiros = self.read_pregoeiros_from_file()
        if nome_pregoeiro not in pregoeiros:
            pregoeiros.append(nome_pregoeiro)
            self.write_pregoeiros_to_file(pregoeiros)
            self.load_pregoeiros()  # Atualiza o combobox

    def show_remove_pregoeiro_dialog(self):
        pregoeiros = self.read_pregoeiros_from_file()
        if not pregoeiros:
            QMessageBox.information(self, "Remover Pregoeiro", "Não há pregoeiros para remover.")
            return

        nome_pregoeiro, okPressed = QInputDialog.getItem(self, "Remover Pregoeiro", 
                                                        "Selecione o pregoeiro para remover:", 
                                                        pregoeiros, 0, False)
        if okPressed and nome_pregoeiro:
            resposta = QMessageBox.question(self, "Confirmar Remoção", 
                                            f"Tem certeza que deseja remover o pregoeiro {nome_pregoeiro}?",
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                            QMessageBox.StandardButton.No)

            if resposta == QMessageBox.StandardButton.Yes:
                self.remove_pregoeiro(nome_pregoeiro)

    def remove_pregoeiro(self, nome_pregoeiro):
        pregoeiros = self.read_pregoeiros_from_file()
        if nome_pregoeiro in pregoeiros:
            pregoeiros.remove(nome_pregoeiro)
            self.write_pregoeiros_to_file(pregoeiros)
            self.load_pregoeiros()  # Atualiza o combobox

    def write_pregoeiros_to_file(self, pregoeiros):
        data = {"pregoeiros": pregoeiros}
        ESCALACAO_PREGOEIROS_DIR = DATABASE_DIR / "pregoeiros.json"
        with open(ESCALACAO_PREGOEIROS_DIR, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def update_pregoeiro_count(self):
        # Remove valores indesejados da contagem
        cleaned_series = self.df_licitacao_completo['pregoeiro'].replace(['-', '', ' ', None], pd.NA).dropna()
        pregoeiro_counts = cleaned_series.value_counts().to_dict()
        
        # Monta o texto para exibir com um título
        pregoeiro_text = "Contador de Escalações:\n" + '\n'.join([f"{key}: {value}" for key, value in pregoeiro_counts.items()])
        self.pregoeiro_counter_label.setText(pregoeiro_text)

    def on_generate_cp(self):
        cp_number = self.cp_input.text()
        session_date = self.calendar.selectedDate().toString("dd/MM/yyyy")
        QMessageBox.information(self, "Geração de CP", f"CP Número: {cp_number}\n"
                                                       f"Pregão {self.mod} {self.num_pregao}/{self.ano_pregao}\n\n"
                                                       f"Data da Sessão: {session_date}")
        self.accept()

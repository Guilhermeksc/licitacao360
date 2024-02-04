# create_etp_button.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
# Importe o modelo e o tokenizer
from transformers import GPT2LMHeadModel, GPT2Tokenizer

class ETP(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Carregar o modelo treinado
        self.tokenizer = GPT2Tokenizer.from_pretrained("caminho_do_modelo")
        self.model = GPT2LMHeadModel.from_pretrained("caminho_do_modelo")

        # Interface para entrada da pergunta
        self.question_input = QTextEdit()
        self.layout.addWidget(self.question_input)

        # Botão para gerar resposta
        self.generate_button = QPushButton("Gerar Resposta")
        self.generate_button.clicked.connect(self.generate_response)
        self.layout.addWidget(self.generate_button)

        # Área para exibir a resposta
        self.response_label = QLabel()
        self.layout.addWidget(self.response_label)

    def generate_response(self):
        question = self.question_input.toPlainText()
        inputs = self.tokenizer.encode(question, return_tensors='pt')
        response = self.model.generate(inputs)
        self.response_label.setText(self.tokenizer.decode(response[0]))

    def get_title(self):
        return "Manipular ETP"

    def get_content_widget(self):
        return self

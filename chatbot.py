from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QTextBrowser

class ChatBot(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.model, self.tokenizer = self.load_model()

    def initUI(self):
        self.setWindowTitle('ChatBot')
        self.layout = QVBoxLayout(self)

        self.chat_display = QTextBrowser(self)
        self.user_input = QLineEdit(self)
        self.user_input.returnPressed.connect(self.handle_user_input)

        self.layout.addWidget(self.chat_display)
        self.layout.addWidget(self.user_input)

    def load_model(self):
        tokenizer = AutoTokenizer.from_pretrained('path_to_your_model')
        model = AutoModelForCausalLM.from_pretrained('path_to_your_model')
        return model, tokenizer

    def handle_user_input(self):
        user_text = self.user_input.text()
        inputs = self.tokenizer.encode(user_text + self.tokenizer.eos_token, return_tensors='pt')
        response_ids = self.model.generate(inputs, max_length=1000, pad_token_id=self.tokenizer.eos_token_id)
        response = self.tokenizer.decode(response_ids[:, inputs.shape[-1]:][0], skip_special_tokens=True)
        self.chat_display.append(f"User: {user_text}")
        self.chat_display.append(f"Bot: {response}")
        self.user_input.clear()

app = QApplication([])
window = ChatBot()
window.show()
app.exec()

import sys
import configparser
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import ICONS_DIR, API_PATH
from pathlib import Path
from modules.web_scraping.macros.divulgacao_compras import DivulgacaoComprasMacro
import os
from openai import OpenAI

class APIManager:
    def __init__(self, config_path):
        self.config = configparser.ConfigParser()
        self.config_path = config_path
        if not self.config_path.exists():
            self.create_default_config()
        self.config.read(self.config_path)
        
    def create_default_config(self):
        self.config['DEFAULT'] = {'api_key': ''}
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
        
    def get_api_key(self):
        return self.config['DEFAULT'].get('api_key', '')
    
    def set_api_key(self, api_key):
        self.config['DEFAULT']['api_key'] = api_key
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

class APIRequestThread(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_key, model, object_text):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.object_text = object_text

    def run(self):
        try:
            # Inicializando o cliente OpenAI
            client = OpenAI(api_key=self.api_key)

            # Fazendo a requisição à API usando o cliente
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": self.object_text}]
            )
            # Acessando o conteúdo da resposta
            message_content = response.choices[0].message.content
            self.response_received.emit(message_content)
        except Exception as e:
            self.error_occurred.emit(f"Erro ao chamar a API: {str(e)}")

class ETPWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.icons_dir = Path(ICONS_DIR)
        self.image_cache = self._load_images()
        self.api_manager = APIManager(API_PATH)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: transparent;")
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self._create_title_layout())

        # Campo para a API
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Digite sua API aqui:")
        self.api_input.setText(self.api_manager.get_api_key())  # Preenche a API se já estiver salva
        main_layout.addWidget(self.api_input)

        # Checkbox para salvar a API
        self.save_api_checkbox = QCheckBox("Manter API salva")
        main_layout.addWidget(self.save_api_checkbox)

        # Botão para escolher o modelo GPT
        self.model_selection = QComboBox()
        self.model_selection.addItems(["gpt-3.5-turbo", "gpt-4"])
        main_layout.addWidget(self.model_selection)

        # Botão para escolher o modelo GPT
        self.question_selection = QComboBox()
        self.question_selection.addItems(["Descrição da Necessidade", "Requisitos da Contratação", "Levantamento de Mercado", "Descrição da solução como um todo"])
        main_layout.addWidget(self.question_selection)

        # Campo para o usuário digitar o objeto
        self.object_input = QTextEdit()
        self.object_input.setPlaceholderText("Digite o objeto aqui")
        main_layout.addWidget(self.object_input)

        # Botão para enviar a requisição à API
        send_button = QPushButton("Enviar para API")
        send_button.clicked.connect(self._send_request_to_api)
        main_layout.addWidget(send_button)

        # Campo para exibir a resposta da API
        self.response_output = QTextEdit()
        self.response_output.setPlaceholderText("A resposta da API aparecerá aqui")
        self.response_output.setReadOnly(True)
        main_layout.addWidget(self.response_output)

        self.loading_animation_timer = QTimer()
        self.loading_animation_timer.timeout.connect(self._update_loading_text)
        self.loading_text = "Aguarde a resposta"
        self.loading_dots = 0

    def _create_title_layout(self):
        layout = QHBoxLayout()
        icon_label = QLabel()
        icon = self.image_cache.get('graph')
        if icon:
            scaled_icon = icon.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled_icon)
        title_label = QLabel("Estudo Técnico Preliminar")
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
            'graph': QPixmap(str(self.icons_dir / "graph.png")),
            'firefox': QPixmap(str(self.icons_dir / "firefox.png")),
            'continue': QPixmap(str(self.icons_dir / "continue.png")),
            'close': QPixmap(str(self.icons_dir / "close.png"))
        }
        return images

    def _send_request_to_api(self):
        api_key = self.api_input.text().strip()
        if not api_key:
            self.response_output.setText("API Key não fornecida.")
            return

        # Verifica se o checkbox está marcado para salvar a API
        if self.save_api_checkbox.isChecked():
            self.api_manager.set_api_key(api_key)

        model = self.model_selection.currentText()
        object_text = self.object_input.toPlainText().strip()
        
        if not object_text:
            self.response_output.setText("Objeto não fornecido.")
            return

        # Adiciona o contexto fixo e o contexto do question_selection
        question_context = self.question_selection.currentText()
        context = (
            f"Atue como um especialista em licitações que está planejando uma contratação de {object_text}. "
            f"O órgão gerenciador da licitação é o Centro de Intendência da Marinha em Brasília (CEIMBRA) que é centralizador das organizações militares da marinha na área de jurisdição do Com7ºDN. "
            f"O interesse público deve ser preservado"
        )

        # Prepara o texto completo que será enviado para a API
        full_text = f"{context}\n Me ajude a construir a {question_context} para contratação de {object_text}"

        # Inicia a animação de "Aguarde a resposta..."
        self.loading_animation_timer.start(500)

        # Criando a thread para enviar a requisição
        self.api_thread = APIRequestThread(api_key, model, full_text)
        self.api_thread.response_received.connect(self._display_response)
        self.api_thread.error_occurred.connect(self._display_error)
        self.api_thread.start()


    def _update_loading_text(self):
        self.loading_dots = (self.loading_dots + 1) % 4
        self.response_output.setPlaceholderText(f"{self.loading_text}{'.' * self.loading_dots}")

    def _display_response(self, message_content):
        self.loading_animation_timer.stop()
        self.response_output.setPlaceholderText("")
        self.response_output.setText(message_content)

    def _display_error(self, error_message):
        self.loading_animation_timer.stop()
        self.response_output.setPlaceholderText("")
        self.response_output.setText(error_message)

    def _minimize_main_window(self):
        self.main_window.showMinimized()

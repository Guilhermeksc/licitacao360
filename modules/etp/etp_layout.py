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

# Substitua por sua API
API_KEY = "coloque a api aqui"

class APIRequestThread(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, object_text):
        super().__init__()
        self.api_key = API_KEY
        self.model = "gpt-3.5-turbo"
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

            # Acessando o conteúdo da resposta corretamente
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
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: transparent;")
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self._create_title_layout())

        # ComboBox para selecionar o tipo de pergunta
        self.question_selection = QComboBox()
        self.question_selection.addItems(["Justificativa para a Contratação", "Descrição da Necessidade", "Requisitos da Contratação", "Levantamento de Mercado", "Descrição da solução como um todo"])
        main_layout.addWidget(self.question_selection)

        # ComboBox para selecionar Material ou Serviço
        self.item_type_selection = QComboBox()
        self.item_type_selection.addItems(["Material", "Serviço"])
        main_layout.addWidget(self.item_type_selection)

        # Campo para o usuário digitar o objeto
        self.object_input = QLineEdit()
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
        self.response_output.setFontPointSize(14)  # Definir tamanho da fonte para 14
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
        object_text = self.object_input.text().strip()
        
        if not object_text:
            self.response_output.setText("Objeto não fornecido.")
            return

        # Adiciona o contexto fixo e o contexto do question_selection
        question_context = self.question_selection.currentText()
        item_type = self.item_type_selection.currentText()

        # Define o texto baseado no tipo de item selecionado
        if item_type == "Material":
            action_text = f"para aquisição de {object_text}"
        else:  # Serviço
            action_text = f"para contratação de empresa especializada em serviços de {object_text}"

        # Adiciona o contexto específico com base no question_selection
        if question_context == "Justificativa para a Contratação":
            context = (
                f"A justificativa para a contratação deve observar os princípios da IN 58, considerando os seguintes pontos:\n"
                f"I - Descrição do contexto e das razões que tornam a contratação indispensável para o atendimento dos interesses "
                f"públicos e institucionais do Banco Central do Brasil (BACEN).\n"
                f"II - Evidência de que a contratação é a solução mais adequada para o problema identificado ou para a necessidade "
                f"de melhoria nos processos, considerando a relação custo-benefício e a eficiência administrativa.\n"
                f"III - Consideração sobre o impacto que a ausência da contratação teria nos serviços, operações ou atividades, "
                f"incluindo possíveis prejuízos ao interesse público."
            )
        elif question_context == "Descrição da Necessidade":
            context = (
                f"A descrição da necessidade para esta contratação deve observar os termos da IN 58, abordando os seguintes pontos:\n"
                f"I - Descrição clara e detalhada do problema a ser resolvido, considerado sob a perspectiva do interesse público, "
                f"e como a solução proposta atende aos objetivos institucionais do Banco Central do Brasil (BACEN).\n"
                f"II - Indicação dos requisitos necessários para a contratação, especificando critérios mínimos de qualidade e desempenho, "
                f"bem como práticas de sustentabilidade, conforme estabelecido pelas leis ou regulamentações pertinentes. "
                f"Esses requisitos devem ser suficientes para a escolha da solução mais adequada."
            )
        elif question_context == "Requisitos da Contratação":
            context = (
                f"Os requisitos da contratação devem incluir especificações claras e detalhadas sobre os produtos ou serviços necessários, "
                f"observando critérios de qualidade, desempenho e sustentabilidade, conforme o disposto na IN 58. "
                f"Deve-se garantir que os requisitos sejam suficientes para orientar a escolha da solução mais adequada "
                f"e para assegurar o cumprimento das necessidades do Banco Central do Brasil (BACEN)."
            )
        elif question_context == "Levantamento de Mercado":
            context = (
                f"O levantamento de mercado deve ser realizado conforme a IN 58, identificando potenciais fornecedores ou prestadores de serviço. "
                f"Deve-se avaliar a capacidade do mercado em atender à demanda e verificar os preços praticados, "
                f"com base em cotações e dados disponíveis, assegurando a viabilidade da contratação sob o aspecto econômico-financeiro."
            )
        elif question_context == "Descrição da solução como um todo":
            context = (
                f"A descrição da solução deve abordar a totalidade da contratação, considerando todos os aspectos técnicos, operacionais e de desempenho. "
                f"Deve-se descrever como a solução proposta atenderá integralmente às necessidades do Banco Central do Brasil (BACEN), "
                f"com foco em resultados eficientes e sustentáveis, conforme as diretrizes da IN 58."
            )

        # Prepara o texto completo que será enviado para a API
        full_text = (
            f"Atue como um especialista em licitações que está planejando uma contratação de {object_text}.\n"
            f"{context}\nMe ajude a construir um texto para a {question_context} {action_text}"
        )  # Corrigido: full_text como uma única string

        # Inicia a animação de "Aguarde a resposta..."
        self.loading_animation_timer.start(500)

        # Criando a thread para enviar a requisição
        self.api_thread = APIRequestThread(full_text)
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
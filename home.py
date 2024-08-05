import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import qdarktheme
from diretorios import ICONS_DIR, IMAGE_PATH
from database.styles.styless import get_menu_button_style, get_menu_button_activated_style
from modules.atas.gerar_atas_contratos import GerarAtasWidget
from modules.planejamento.planejamento_button import ApplicationUI
from modules.dispensa_eletronica.classe_dispensa_eletronica import DispensaEletronicaWidget
from modules.contratos.classe_contratos import ContratosWidget
from modules.custom_selenium.selenium_automation import SeleniumAutomacao
from modules.matriz_de_riscos.classe_matriz import MatrizRiscosWidget
from menu_manager import MenuManager

class InicioWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: black;")  # Define o fundo preto

        self.layout = QVBoxLayout(self)
        self.layout.addStretch(1)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(IMAGE_PATH / "texto_inicio"))
        self.image_label.setPixmap(pixmap.scaled(1000, 625, Qt.AspectRatioMode.KeepAspectRatio))
        self.layout.addWidget(self.image_label)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.buttons = {}  # Inicializa self.buttons
        self.setup_ui()
        self.open_initial_page()

    def setup_ui(self):
        self.configure_window()
        self.setup_central_widget()
        self.setup_menu()
        self.setup_content_area()
        self.active_button = None

    def configure_window(self):
        self.setWindowTitle("Licitação 360")  # Define o título da janela
        self.resize(1050, 550)

    def setup_central_widget(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_layout = QHBoxLayout(self.central_widget)
        self.central_layout.setSpacing(0)
        self.central_layout.setContentsMargins(0, 0, 0, 0)

    def setup_menu(self):
        self.menu_manager = MenuManager(self)
        self.menu_manager.create_menus()

        menu_layout = QVBoxLayout()
        menu_layout.setSpacing(0)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        menu_buttons = [
            "Início",
            "Planejamento",
            "Atas",
            "Contratos",
            "ETP",
            "Matriz de Riscos",
            "Dispensa Eletrônica",
            "Selenium",
        ]

        for button_name in menu_buttons:
            button = self.create_menu_button(button_name)
            if button_name == "Início":
                button.clicked.connect(self.open_initial_page)
            else:
                button.clicked.connect(self.update_content_title)

            self.buttons[button_name] = button
            menu_layout.addWidget(button)

        menu_layout.addStretch(4)
        self.menu_widget = QWidget()
        self.menu_widget.setLayout(menu_layout)
        self.menu_widget.setFixedWidth(180)

        self.central_layout.addWidget(self.menu_widget)

    def create_menu_button(self, name):
        button = QPushButton(f" {name}")
        button.setStyleSheet(get_menu_button_style())
        return button

    def add_menu_image(self, layout):
        caminho_imagem = IMAGE_PATH / "licitacao360_brasil.png"
        licitacao_360_pixmap = QPixmap(str(caminho_imagem))
        licitacao_360_pixmap = licitacao_360_pixmap.scaled(175, 175)
        image_label = QLabel()
        image_label.setPixmap(licitacao_360_pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

    def setup_content_area(self):
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.content_image_label = QLabel(self.central_widget)
        self.content_layout.addWidget(self.content_image_label)
        self.content_image_label.hide()

        self.content_widget = QWidget()
        self.content_widget.setLayout(self.content_layout)
        self.content_widget.setMinimumSize(1050, 550)
        self.content_widget.setObjectName("contentWidget")
        self.central_layout.addWidget(self.content_widget)

        self.inicio_widget = InicioWidget(self)

    def open_initial_page(self):
        self.clear_content_area(keep_image_label=True)
        self.content_layout.addWidget(self.inicio_widget)
        self.set_active_button("Início")
        self.content_widget.setStyleSheet("""
            QWidget#contentWidget {
                border: 1px solid #000000;
                background-color: black;
            }
        """)

    def update_content_title(self, button=None):
        button = button or self.sender()
        if button:
            self.set_active_button(button.text().strip())
            self.change_content(button.text().strip())

    def change_content(self, content_name):
        content_actions = {
            "Planejamento": self.setup_planejamento,
            "Atas": self.setup_atas,
            "Contratos": self.setup_contratos,
            "Dispensa Eletrônica": self.setup_dispensa_eletronica,
            "Matriz de Riscos": self.setup_matriz_riscos,
            "Selenium": self.setup_selenium_automacao,
        }
        action = content_actions.get(content_name)
        if action:
            action()

    def setup_planejamento(self):
        self.clear_content_area()
        self.application_ui = ApplicationUI(self, str(ICONS_DIR))
        self.content_layout.addWidget(self.application_ui)

    def setup_atas(self):
        self.clear_content_area()
        self.atas_contratos_widget = GerarAtasWidget(str(ICONS_DIR), self)
        self.content_layout.addWidget(self.atas_contratos_widget)

    def setup_contratos(self):
        print("Setting up contratos...")
        self.clear_content_area()
        self.atas_contratos_widget = ContratosWidget(str(ICONS_DIR), self)
        self.content_layout.addWidget(self.atas_contratos_widget)
        print("Contratos widget added to layout")

    def setup_dispensa_eletronica(self):
        self.clear_content_area()
        self.dispensa_eletronica_widget = DispensaEletronicaWidget(str(ICONS_DIR), self)
        self.content_layout.addWidget(self.dispensa_eletronica_widget)

    def setup_matriz_riscos(self):
        self.clear_content_area()
        self.matriz_riscos_widget = MatrizRiscosWidget(self)
        self.content_layout.addWidget(self.matriz_riscos_widget)

    def setup_selenium_automacao(self):
        self.clear_content_area()
        self.selenium_widget = SeleniumAutomacao(self)
        self.content_layout.addWidget(self.selenium_widget)

    def clear_content_area(self, keep_image_label=False):
        for i in reversed(range(self.content_layout.count())):
            layout_item = self.content_layout.itemAt(i)
            widget = layout_item.widget()
            if widget:
                if widget is self.content_image_label:
                    if not keep_image_label:
                        widget.hide()
                else:
                    widget.setParent(None)

    def set_active_button(self, button_name):
        if self.active_button:
            self.reset_button_style(self.active_button)
        button = self.buttons.get(button_name)
        if button:
            button.setStyleSheet(get_menu_button_activated_style())
            self.active_button = button

    def reset_button_style(self, button):
        button.setStyleSheet(get_menu_button_style())

    def show_message(self, message):
        print(message)  # Aqui você pode substituir pelo método de exibição de mensagens na interface

def main():
    app = QApplication(sys.argv)

    # Apply dark theme.
    app.setStyleSheet(qdarktheme.load_stylesheet("dark"))

    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        raise e

if __name__ == "__main__":
    main()

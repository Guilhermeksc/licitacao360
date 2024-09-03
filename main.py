import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import qdarktheme
from diretorios import ICONS_DIR, IMAGE_PATH
from database.styles.styless import get_menu_button_style, get_menu_button_activated_style
from modules.atas.layout_gerar_atas import GerarAtasWidget
from modules.planejamento_novo.novo_planejamento_button import PlanejamentoWidget
from modules.dispensa_eletronica.classe_dispensa_eletronica import DispensaEletronicaWidget
from modules.contratos.classe_contratos import ContratosWidget
from modules.custom_selenium.selenium_automation import SeleniumAutomacao
from modules.matriz_de_riscos.classe_matriz import MatrizRiscosWidget
from modules.menu_superior.menu_manager import MenuManager
from modules.web_scraping.web_scrapping_initial import WebScrapingWidget
from modules.etp.etp_layout import ETPWidget
from modules.manipular_pdf.pdf import ManipularPDFsWidget, PNCPConsultationApp
from modules.api_comprasnet_contratos.consulta_atas import ComprasnetContratosAPI

from pathlib import Path

class InicioWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(ICONS_DIR)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        # Aplica o estilo CSS para bordas arredondadas ao QWidget
        self.setStyleSheet("""
            InicioWidget {
                border-radius: 15px;
                border: 1px solid #0081DB;
            }
        """)

        # Título do projeto
        self.title_label = QLabel("Licitação 360")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 30px; font-weight: bold;")
        
        # Sinopse do projeto
        self.synopsis_label = QLabel(
            "Licitação 360 é um projeto desenvolvido em Python para automatizar processos repetitivos relacionados "
            "a licitações e acordos administrativos. Com um foco na otimização e eficiência, o projeto oferece ferramentas "
            "para manipulação de documentos PDF, DOCX e XLSX, geração de relatórios, e automação de tarefas via RPA. "
            "O objetivo principal é melhorar a qualidade de vida no trabalho, minimizando erros e reduzindo a quantidade "
            "de cliques necessários para completar uma tarefa."
        )
        self.synopsis_label.setAlignment(Qt.AlignmentFlag.AlignJustify)
        self.synopsis_label.setWordWrap(True)
        self.synopsis_label.setStyleSheet("font-size: 16px; padding: 10px;")


        # Adiciona os widgets ao layout
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.synopsis_label)

        # Carregar ícones
        self.image_cache = self.load_initial_data()

        # Adiciona os módulos ao layout com seus respectivos ícones e descrições
        self.add_module("Atas", "Automação para criação de Atas de Registro de Preços.", "report.png")
        self.add_module("Contratos", "Gerenciamento de contratos administrativos.", "signature.png")
        self.add_module("Planejamento", "Ferramentas de planejamento para licitações.", "planning.png")
        self.add_module("Web Scraping", "Coleta automática de dados do Comprasnet.", "website_menu.png")
        self.add_module("RPA", "Automação de processos repetitivos via RPA.", "automation.png")
        self.add_module("Funcionalidades PDF", "Manipulação avançada de documentos PDF.", "pdf.png")
        self.add_module("API PNCP e ComprasnetContratos", "Consulta de dados do PNCP e ComprasnetContratos via API.", "api.png")

        # Contato
        self.contact_label = QLabel(
            'Para mais informações, entre em contato pelo e-mail: <a href="mailto:siqueira.campos@marinha.mil.br">siqueira.campos@marinha.mil.br</a>'
        )
        self.contact_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.contact_label.setOpenExternalLinks(True)
        self.contact_label.setStyleSheet("font-size: 16px; padding: 10px;")

        self.layout.addStretch(1)
        self.layout.addWidget(self.contact_label)

    def add_module(self, title, description, icon_name):
        """Adiciona um módulo com ícone, título e descrição alinhados corretamente."""
        icon = self.image_cache.get(icon_name.split('.')[0], QIcon())
        module_layout = QHBoxLayout()
        
        # Define espaçamento 0,0,0,0
        module_layout.setContentsMargins(0, 0, 0, 0)
        module_layout.setSpacing(0)
        
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(40, 40))
        
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(title_label)
        
        description_label = QLabel(description)
        description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignJustify)
        description_label.setWordWrap(True)
        description_label.setFixedWidth(800)
        description_label.setStyleSheet("font-size: 16px; padding-left: 5px;")
        title_layout.addWidget(description_label)
        
        module_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignRight)
        module_layout.addLayout(title_layout)
        
        module_widget = QWidget()
        module_widget.setLayout(module_layout)
        
        self.layout.addWidget(module_widget)
        
    def load_initial_data(self):
        image_file_names = [
            "report.png", "signature.png", "planning.png", 
            "website_menu.png", "automation.png", "pdf.png", "api.png"
        ]
        return self.load_images(self.icons_dir, image_file_names)
    

    def load_images(self, icons_dir, image_file_names):
        images = {}
        for image_file_name in image_file_names:
            image_path = icons_dir / image_file_name
            if not image_path.is_file():
                print(f"Image file not found: {image_path}")
                continue
            icon = QIcon(str(image_path))
            images[image_file_name.split('.')[0]] = icon
        return images

class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app 
        self.is_menu_visible = True
        self.buttons = {}
        self.setup_ui()
        self.open_initial_page()

    def setup_ui(self):
        self.configure_window()
        self.setup_central_widget()
        self.setup_menu()
        self.setup_content_area()
        self.active_button = None

    def configure_window(self):
        self.setWindowTitle("Licitação 360")

        # Adicionar ícone ao título
        icon_confirm = QIcon(str(ICONS_DIR / "brasil.png"))
        self.setWindowIcon(icon_confirm)
        # Define o título da janela
        self.resize(1050, 700)

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
            "Web Scraping",
            "Manipular PDF's",
            "API PNCP",
            "API Contratos"
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

    # def add_menu_image(self, layout):
    #     caminho_imagem = IMAGE_PATH / "licitacao360_brasil.png"
    #     licitacao_360_pixmap = QPixmap(str(caminho_imagem))
    #     licitacao_360_pixmap = licitacao_360_pixmap.scaled(175, 175)
    #     image_label = QLabel()
    #     image_label.setPixmap(licitacao_360_pixmap)
    #     image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    #     layout.addWidget(image_label)

    def setup_content_area(self):
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.content_image_label = QLabel(self.central_widget)
        self.content_layout.addWidget(self.content_image_label)
        self.content_image_label.hide()

        self.content_widget = QWidget()
        self.content_widget.setLayout(self.content_layout)
        self.content_widget.setMinimumSize(1050, 700)
        self.content_widget.setObjectName("contentWidget")
        self.central_layout.addWidget(self.content_widget)

        self.inicio_widget = InicioWidget(self)

    def open_initial_page(self):
        self.clear_content_area(keep_image_label=True)
        self.content_layout.addWidget(self.inicio_widget)
        self.set_active_button("Início")
        self.content_widget.setStyleSheet("""
            QWidget#contentWidget {
                border: 1px solid #E4E7EB;
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
            "ETP": self.setup_etp,
            "Selenium": self.setup_selenium_automacao,
            "Web Scraping": self.setup_webscraping,
            "Manipular PDF's": self.setup_manipular_pdfs,
            "API PNCP": self.setup_api_pncp,
            "API Contratos": self.setup_api_comprasnet_contratos
        }
        action = content_actions.get(content_name)
        if action:
            action()

    def setup_planejamento(self):
        self.clear_content_area()
        self.application_ui = PlanejamentoWidget(self, str(ICONS_DIR))
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

    def setup_etp(self):
        self.clear_content_area()
        self.etp_widget = ETPWidget(self)
        self.content_layout.addWidget(self.etp_widget)

    def setup_selenium_automacao(self):
        self.clear_content_area()
        self.selenium_widget = SeleniumAutomacao(self)
        self.content_layout.addWidget(self.selenium_widget)

    def setup_webscraping(self):
        self.clear_content_area()
        self.webscraping_widget = WebScrapingWidget(self)
        self.content_layout.addWidget(self.webscraping_widget)

    def setup_manipular_pdfs(self):
        self.clear_content_area()
        self.manipular_pdfs_widget = ManipularPDFsWidget(self)
        self.content_layout.addWidget(self.manipular_pdfs_widget)

    def setup_api_pncp(self):
        self.clear_content_area()
        self.pncp_widget = PNCPConsultationApp(self)
        self.content_layout.addWidget(self.pncp_widget)

    def setup_api_comprasnet_contratos(self):
        self.clear_content_area()
        self.comprasnet_contratos_widget = ComprasnetContratosAPI(self)
        self.content_layout.addWidget(self.comprasnet_contratos_widget)

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

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirmar Saída',
                                     "Você realmente deseja fechar o aplicativo?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    app = QApplication(sys.argv)

    # Apply dark theme.
    app.setStyleSheet(qdarktheme.load_stylesheet("dark"))

    try:
        window = MainWindow(app)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        raise e

if __name__ == "__main__":
    main()

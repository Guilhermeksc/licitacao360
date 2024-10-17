import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import qdarktheme
from diretorios import ICONS_DIR, IMAGE_PATH
from database.styles.styless import get_menu_button_style, get_menu_button_activated_style
from modules.pca.pca import PCAWidget
from modules.pncp.pncp import PNCPWidget
from modules.gerar_atas.layout_gerar_atas import GerarAtasWidget
from modules.planejamento_novo.antigo_planejamento_button import PlanejamentoWidget
from modules.dispensa_eletronica.classe_dispensa_eletronica import DispensaEletronicaWidget
from modules.matriz_de_riscos.classe_matriz import MatrizRiscosWidget
from modules.atas.classe_atas import AtasWidget
from modules.contratos.classe_contratos import ContratosWidget
from config.menu_superior.config.config_database import ConfigurarDatabaseDialog
from config.menu_superior.config.config_responsaveis import AgentesResponsaveisDialog
from config.menu_superior.config.config_om import OrganizacoesDialog
from config.menu_superior.config.config_template import TemplatesDialog
from pathlib import Path
import time
class InicioWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(ICONS_DIR)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

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

        # Agora cria um QHBoxLayout para os módulos e a imagem
        modules_and_image_layout = QHBoxLayout()

        # Layout à esquerda para os módulos
        self.modules_layout = QVBoxLayout()

        # Carregar ícones
        self.image_cache = self.load_initial_data()

        # Adiciona os módulos
        self.add_module("Atas", "Automação para criação de Atas de Registro de Preços.", "report.png")
        self.add_module("Contratos", "Gerenciamento de contratos administrativos.", "signature.png")
        self.add_module("Planejamento", "Ferramentas de planejamento para licitações.", "planning.png")
        self.add_module("Web Scraping", "Coleta automática de dados do Comprasnet.", "website_menu.png")
        self.add_module("RPA", "Automação de processos repetitivos via RPA.", "automation.png")
        self.add_module("Funcionalidades PDF", "Manipulação avançada de documentos PDF.", "pdf.png")
        self.add_module("API PNCP e ComprasnetContratos", "Consulta de dados do PNCP e ComprasnetContratos via API.", "api.png")

        # Adiciona o layout dos módulos à esquerda no layout horizontal
        modules_and_image_layout.addLayout(self.modules_layout)

        # Adiciona uma imagem à direita com smooth scaling
        self.image_tucano_label = QLabel()
        self.image_tucano = QPixmap(str(IMAGE_PATH / "marinha_logo.png"))
        
        # Redimensiona a imagem mantendo a qualidade com smooth scaling
        self.image_tucano_label.setPixmap(self.image_tucano.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.image_tucano_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Adiciona a imagem ao layout horizontal
        modules_and_image_layout.addWidget(self.image_tucano_label)

        # Adiciona o layout horizontal de módulos e imagem ao layout principal vertical
        self.layout.addLayout(modules_and_image_layout)

        # Adiciona um espaço flexível para empurrar o contato para o final
        self.layout.addStretch()

        # Contato
        self.contact_label = QLabel(
            'Para mais informações, entre em contato pelo e-mail: <a href="mailto:siqueira.campos@marinha.mil.br">siqueira.campos@marinha.mil.br</a>'
        )
        self.contact_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.contact_label.setOpenExternalLinks(True)
        self.contact_label.setStyleSheet("font-size: 16px; padding: 10px;")

        # Adiciona o contato ao final
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

        self.modules_layout.addWidget(module_widget)
        
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
        self.icon_config = QPixmap(str(ICONS_DIR / "setting_1.png"))
        self.icon_config_2 = QPixmap(str(ICONS_DIR / "setting_2.png"))        
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
        menu_layout = QVBoxLayout()
        menu_layout.setSpacing(0)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        menu_buttons = [
            "Início",
            "PCA",
            "Licitação",
            "Gerar Atas",
            "Atas",
            "Contratos",
            "Dispensa",
            "PNCP",
        ]

        for button_name in menu_buttons:
            button = self.create_menu_button(button_name)
            if button_name == "Início":
                button.clicked.connect(self.open_initial_page)
            else:
                button.clicked.connect(self.update_content_title)

            self.buttons[button_name] = button
            menu_layout.addWidget(button)

        # Adicionar um espaço expansivo após os botões para empurrar o botão de configuração para baixo
        spacer_above_config = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        menu_layout.addItem(spacer_above_config)

        # Cria um layout horizontal para o botão de configurações
        config_layout = QHBoxLayout()
        config_layout.setSpacing(0)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Adiciona o botão de configurações
        config_button = QPushButton()
        config_button.setIcon(QIcon(self.icon_config))
        config_button.setIconSize(QSize(40, 40))
        config_button.setStyleSheet("border: none;")
        config_button.setCursor(Qt.CursorShape.PointingHandCursor)
        config_button.setFixedSize(40, 40)

        # Alterações nos ícones ao passar o mouse e clicar
        config_button.installEventFilter(self)

        # Armazenar o config_button em self.buttons
        self.buttons['config_button'] = config_button

        # Adiciona o botão de configurações ao layout do botão
        config_layout.addWidget(config_button)

        # Adiciona o layout do botão de configurações ao layout principal
        menu_layout.addLayout(config_layout)

        # Adicionar um espaço pequeno abaixo do botão de configuração para deixá-lo afastado da borda inferior
        spacer_below_config = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        menu_layout.addItem(spacer_below_config)

        self.menu_widget = QWidget()
        self.menu_widget.setLayout(menu_layout)
        self.menu_widget.setFixedWidth(90)

        # Ajustar o fundo do menu para preto
        self.menu_widget.setStyleSheet("background-color: #13141F;")

        self.central_layout.addWidget(self.menu_widget)

        # Conecta o clique do botão de configuração ao menu personalizado
        config_button.clicked.connect(lambda: self.show_settings_menu(config_button))

    def create_menu_button(self, name):
        button = QPushButton(f" {name}")
        button.setStyleSheet(get_menu_button_style())
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def toggle_acordos_submenu(self):
        self.acordos_submenu_visible = not self.acordos_submenu_visible
        self.acordos_submenu_widget.setVisible(self.acordos_submenu_visible)
        # Opcional: mudar o estilo ou ícone do botão "Acordos" para indicar o estado

    def open_initial_page(self):
        self.clear_content_area(keep_image_label=True)
        # self.content_layout.addWidget(self.inicio_widget)  # Adicione seu widget de início aqui
        self.set_active_button("Início")

    def update_content_title(self, button=None):
        button = button or self.sender()
        if button:
            self.set_active_button(button.text().strip())
            self.change_content(button.text().strip())
            
    def create_settings_menu(self):
        # Cria o menu suspenso para o botão de configurações
        menu = QMenu()
        
        btn_database = QAction("Configurar Banco de Dados", self)
        btn_database.triggered.connect(self.show_configurar_database_dialog)
        menu.addAction(btn_database)
        
        btn_agentes = QAction("Agentes Responsáveis", self)
        btn_agentes.triggered.connect(self.show_agentes_responsaveis_dialog)
        menu.addAction(btn_agentes)
        
        btn_templates = QAction("Templates", self)
        btn_templates.triggered.connect(self.show_templates_dialog)
        menu.addAction(btn_templates)
        
        btn_organizacoes = QAction("Organizações", self)
        btn_organizacoes.triggered.connect(self.show_organizacoes_dialog)
        menu.addAction(btn_organizacoes)
        
        return menu

    def show_settings_menu(self, button):
        menu = self.create_settings_menu()

        # Aplicar estilo personalizado ao menu
        menu.setStyleSheet("""
            QMenu {
                background-color: #181928;  
            }
            QMenu::item {
                background-color: transparent; 
                padding: 8px 20px;  
                color: white; 
                border-radius: 5px;  
            }
            QMenu::item:selected {
                background-color: #5A5B6A; 
            }
        """)

        # Definir a posição e exibir o menu
        pos = button.mapToGlobal(QPoint(button.width(), 0))
        menu.exec(pos - QPoint(0, menu.sizeHint().height() - button.height()))

    def eventFilter(self, source, event):
        if isinstance(source, QPushButton):
            if event.type() == QEvent.Type.Enter:
                if source == self.buttons.get("config_button", None):
                    # Define a posição do tooltip centralizado ao lado direito do botão
                    tooltip_pos = source.mapToGlobal(QPoint(source.width() + 10, source.height() // 2))
                    tooltip_pos.setY(tooltip_pos.y() - 10)  # Ajusta o tooltip para ficar centralizado verticalmente
                    QToolTip.setFont(QFont("Arial", 10))  # Ajusta a fonte do tooltip
                    QToolTip.showText(tooltip_pos, "Configurações", source)

                source.setIcon(QIcon(self.icon_config_2))
            elif event.type() == QEvent.Type.Leave:
                if source == self.buttons.get("config_button", None):
                    QToolTip.hideText()

                source.setIcon(QIcon(self.icon_config))
            elif event.type() == QEvent.Type.MouseButtonPress:
                source.setIcon(QIcon(self.icon_config))
        return super().eventFilter(source, event)
        
    def create_menu_button(self, name):
        button = QPushButton(f" {name}")
        button.setStyleSheet(get_menu_button_style())
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

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

    def update_content_title(self, button=None):
        button = button or self.sender()
        if button:
            self.set_active_button(button.text().strip())
            self.change_content(button.text().strip())

    def change_content(self, content_name):
        content_actions = {
            "Licitação": self.setup_planejamento,
            "PCA": self.setup_pca,
            "Gerar Atas": self.setup_gerar_atas,
            "Atas": self.setup_atas,
            "Contratos": self.setup_contratos,
            "Dispensa": self.setup_dispensa_eletronica,
            "Matriz": self.setup_matriz_riscos,
            "PNCP": self.setup_pncp,
        }
        action = content_actions.get(content_name)
        if action:
            action()

    # Métodos para abrir os diálogos
    def show_configurar_database_dialog(self):
        dialog = ConfigurarDatabaseDialog(self)
        dialog.exec()

    def show_agentes_responsaveis_dialog(self):
        dialog = AgentesResponsaveisDialog(self)
        dialog.exec()

    def show_organizacoes_dialog(self):
        dialog = OrganizacoesDialog(self)
        dialog.exec()

    def show_templates_dialog(self):
        # Corrigir passando o pai correto para o diálogo
        dialog = TemplatesDialog(self.config_manager, self)
        dialog.exec()

    def setup_matriz_riscos(self):
        self.clear_content_area()
        self.matriz_riscos_widget = MatrizRiscosWidget(self)
        self.content_layout.addWidget(self.matriz_riscos_widget)

    def setup_planejamento(self):
        self.clear_content_area()
        self.application_ui = PlanejamentoWidget(self, str(ICONS_DIR))
        self.content_layout.addWidget(self.application_ui)

    def setup_pca(self):
        self.clear_content_area()
        self.pca_widget = PCAWidget(self)
        self.content_layout.addWidget(self.pca_widget)

    def setup_pncp(self):
        self.clear_content_area()
        self.pca_widget = PNCPWidget(self)
        self.content_layout.addWidget(self.pca_widget)

    def setup_gerar_atas(self):
        self.clear_content_area()
        self.atas_contratos_widget = GerarAtasWidget(str(ICONS_DIR), self)
        self.content_layout.addWidget(self.atas_contratos_widget)

    def setup_atas(self):
        self.clear_content_area()
        self.atas_widget = AtasWidget(str(ICONS_DIR), self)
        self.content_layout.addWidget(self.atas_widget)
        print("Contratos widget added to layout")

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

    # Aplicar o tema escuro
    app.setStyleSheet(qdarktheme.load_stylesheet("dark"))

    # Criar a splash screen e redimensionar a imagem com efeito suave
    splash_pix = QPixmap(str(IMAGE_PATH / "carregamento.png"))  # Substitua por sua imagem
    splash_pix = splash_pix.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)  # Redimensionar com transformação suave

    splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
    
    # Definir a fonte e a cor para o texto de carregamento
    font = QFont()
    font.setPointSize(12)
    splash.setFont(font)

    # Mostrar a splash screen
    splash.show()

    # Função para atualizar a barra de progresso
    def update_progress(value):
        splash.showMessage(
            f"Carregando... {value}%",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            Qt.GlobalColor.white  # Cor do texto
        )

    # Simular um tempo de carregamento com animação de barra de progresso
    for i in range(1, 101):
        QTimer.singleShot(i * 20, lambda value=i: update_progress(value))

    # Fechar a splash screen e mostrar a janela principal após a animação
    QTimer.singleShot(2000, lambda: splash.close())
    QTimer.singleShot(2000, lambda: MainWindow(app).show())

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
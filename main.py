import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import qdarktheme
from config.paths import ICONS_DIR, IMAGES_DIR, DATA_DISPENSA_ELETRONICA_PATH
from config.styles.styless import get_menu_button_style, get_menu_button_activated_style
from modules.widgets import *
from config.dialogs import * 


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.icons = load_icons()
        self.buttons = {}
        self.active_button = None
        self.setup_ui()
        self.open_initial_page()

    # ====== SETUP DA INTERFACE ======

    def setup_ui(self):
        """Configura a interface principal da aplicação."""
        self.configure_window()
        self.setup_central_widget()
        self.setup_menu()
        self.setup_content_area()

    def configure_window(self):
        """Configurações básicas da janela principal."""
        self.setWindowTitle("Licitação 360")
        self.setWindowIcon(self.icons["confirm"])
        self.resize(1050, 700)

    # ====== CENTRAL WIDGET E MENU ======

    def setup_central_widget(self):
        """Define o widget central e layout principal."""
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
            ("Início", self.open_initial_page),
            ("PCA", self.update_content_title),
            ("Licitação", self.update_content_title),
            ("Atas", self.update_content_title),
            ("Contratos", self.update_content_title),
            ("Dispensa", self.update_content_title),
            ("PNCP", self.update_content_title)
        ]

        for name, handler in menu_buttons:
            button = self.create_menu_button(name)
            button.clicked.connect(handler)
            self.buttons[name] = button
            menu_layout.addWidget(button)

        # Adiciona espaçadores e o botão de configurações
        menu_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        menu_layout.addLayout(self.create_config_button())
        menu_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

        # Widget de menu finalizado
        self.menu_widget = QWidget()
        self.menu_widget.setLayout(menu_layout)
        self.menu_widget.setFixedWidth(90)
        self.menu_widget.setStyleSheet("background-color: #13141F;")
        self.central_layout.addWidget(self.menu_widget)

    def create_menu_button(self, name):
        button = QPushButton(f" {name}")
        button.setStyleSheet(get_menu_button_style())
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    # ====== EVENTOS DE MENU ======

    def set_active_button(self, button_name):
        """Define o botão ativo e altera o estilo visual."""
        if self.active_button:
            self.reset_button_style(self.active_button)
        button = self.buttons.get(button_name)
        if button:
            button.setStyleSheet(get_menu_button_activated_style())
            self.active_button = button

    def update_content_title(self, button=None):
        """Atualiza o título do conteúdo com base no botão clicado."""
        button = button or self.sender()
        if button:
            self.set_active_button(button.text().strip())
            self.change_content(button.text().strip())

    def change_content(self, content_name):
        content_actions = {
            "Licitação": self.setup_planejamento,
            "PCA": self.setup_pca,
            "Atas": self.setup_atas,
            "Contratos": self.setup_contratos,
            "Dispensa": self.setup_dispensa_eletronica,
            "PNCP": self.setup_pncp,
        }
        action = content_actions.get(content_name)
        if action:
            action()

    def open_initial_page(self):
        """Abre a página inicial da aplicação."""
        self.clear_content_area(keep_image_label=True)
        self.content_layout.addWidget(self.inicio_widget)
        self.set_active_button("Início")

    # ====== CONFIGURAÇÕES ======

    def create_config_button(self):
        config_layout = QHBoxLayout()
        self.config_button = QPushButton()  # Define como atributo da classe
        self.config_button.setIcon(self.icons["setting_1"])
        self.config_button.setIconSize(QSize(40, 40))
        self.config_button.setStyleSheet("border: none;")
        self.config_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.config_button.setFixedSize(40, 40)
        
        # Instala o event filter para capturar o efeito de hover
        self.config_button.installEventFilter(self)
        self.config_button.clicked.connect(lambda: self.show_settings_menu(self.config_button))
        
        config_layout.addWidget(self.config_button)
        config_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return config_layout

    def show_settings_menu(self, button):
        menu = self.create_settings_menu()
        menu.setStyleSheet("""
            QMenu { background-color: #181928; }
            QMenu::item { background-color: transparent; padding: 8px 20px; color: white; border-radius: 5px; }
            QMenu::item:selected { background-color: #5A5B6A; }
        """)
        pos = button.mapToGlobal(QPoint(button.width(), 0))
        menu.exec(pos - QPoint(0, menu.sizeHint().height() - button.height()))

    def create_settings_menu(self):
        menu = QMenu()
        settings_options = {
            "Configurar Banco de Dados": self.show_configurar_database_dialog,
            "Agentes Responsáveis": self.show_agentes_responsaveis_dialog,
            "Templates": self.show_templates_dialog,
            "Organizações": self.show_organizacoes_dialog
        }
        for title, handler in settings_options.items():
            action = QAction(title, self)
            action.triggered.connect(handler)
            menu.addAction(action)
        return menu
    
    # ====== ÁREA DE CONTEÚDO ======

    def setup_content_area(self):
        """Configura a área principal para exibição do conteúdo."""
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_image_label = QLabel(self.central_widget)
        self.content_image_label.hide()
        self.content_layout.addWidget(self.content_image_label)

        self.content_widget = QWidget()
        self.content_widget.setLayout(self.content_layout)
        self.content_widget.setMinimumSize(1050, 700)
        self.central_layout.addWidget(self.content_widget)
        
        self.inicio_widget = InicioWidget(self)

    def clear_content_area(self, keep_image_label=False):
        """Remove todos os widgets da área de conteúdo, exceto a imagem opcional."""
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget and (widget is not self.content_image_label or not keep_image_label):
                widget.setParent(None)

    # ====== EVENTOS DE CONFIGURAÇÃO ======

    def eventFilter(self, source, event):
        # Verifica se o evento é para o config_button
        if source == self.config_button:
            if event.type() == QEvent.Type.Enter:  # Quando o mouse entra no botão
                self.config_button.setIcon(self.icons["setting_2"])
            elif event.type() == QEvent.Type.Leave:  # Quando o mouse sai do botão
                self.config_button.setIcon(self.icons["setting_1"])
        
        return super().eventFilter(source, event)
    
    def reset_button_style(self, button):
        button.setStyleSheet(get_menu_button_style())

    # ====== AÇÕES DOS DIÁLOGOS ======

    def show_configurar_database_dialog(self):
        ConfigurarDatabaseDialog(self).exec()

    def show_agentes_responsaveis_dialog(self):
        AgentesResponsaveisDialog(self).exec()

    def show_organizacoes_dialog(self):
        OrganizacoesDialog(self).exec()

    def show_templates_dialog(self):
        TemplatesDialog(self).exec()

    # ====== AÇÕES DO MENU ======

    def setup_content_widget(self, widget_class, *args):
        """Auxiliar para limpar a área de conteúdo e adicionar um novo widget."""
        self.clear_content_area()
        widget_instance = widget_class(*args)
        self.content_layout.addWidget(widget_instance)
        return widget_instance

    def setup_planejamento(self):
        self.application_ui = self.setup_content_widget(PlanejamentoWidget, self, str(ICONS_DIR))

    def setup_pca(self):
        self.pca_widget = self.setup_content_widget(PCAWidget, self)

    def setup_pncp(self):
        self.clear_content_area()
        self.pca_widget = PNCPWidget(self)
        self.content_layout.addWidget(self.pca_widget)

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
        
        # Instancia o modelo de Dispensa Eletrônica com o caminho do banco de dados
        self.dispensa_eletronica_model = DispensaEletronicaModel(DATA_DISPENSA_ELETRONICA_PATH)
        
        # Configura o modelo SQL
        sql_model = self.dispensa_eletronica_model.setup_model("controle_dispensas", editable=True)
        
        # Cria o widget de Dispensa Eletrônica e passa o modelo SQL e o caminho do banco de dados
        self.dispensa_eletronica_widget = DispensaEletronicaWidget(self.icons, sql_model, self.dispensa_eletronica_model.database_manager.db_path)

        # Cria o controlador e passa o widget e o modelo
        self.controller = DispensaEletronicaController(self.dispensa_eletronica_widget, self.dispensa_eletronica_model)

        # Adiciona o widget de Dispensa Eletrônica na área de conteúdo
        self.content_layout.addWidget(self.dispensa_eletronica_widget)

    def clear_content_area(self, keep_image_label=False):
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget and (widget is not self.content_image_label or not keep_image_label):
                widget.setParent(None)

    # ====== EVENTO DE FECHAMENTO DA JANELA ======

    def closeEvent(self, event):
        """Solicita confirmação ao usuário antes de fechar a janela."""
        reply = QMessageBox.question(
            self, 'Confirmar Saída', "Você realmente deseja fechar o aplicativo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        event.accept() if reply == QMessageBox.StandardButton.Yes else event.ignore()

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarktheme.load_stylesheet("dark"))
    MainWindow(app).show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

# def main():
#     app = QApplication(sys.argv)

#     # Aplicar o tema escuro
#     app.setStyleSheet(qdarktheme.load_stylesheet("dark"))

#     # Criar a splash screen e redimensionar a imagem com efeito suave
#     splash_pix = QPixmap(str(IMAGES_DIR / "carregamento.png"))  # Substitua por sua imagem
#     splash_pix = splash_pix.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)  # Redimensionar com transformação suave

#     splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
    
#     # Definir a fonte e a cor para o texto de carregamento
#     font = QFont()
#     font.setPointSize(12)
#     splash.setFont(font)

#     # Mostrar a splash screen
#     splash.show()

#     # Função para atualizar a barra de progresso
#     def update_progress(value):
#         splash.showMessage(
#             f"Carregando... {value}%",
#             Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
#             Qt.GlobalColor.white  # Cor do texto
#         )

#     # Simular um tempo de carregamento com animação de barra de progresso
#     for i in range(1, 101):
#         QTimer.singleShot(i * 20, lambda value=i: update_progress(value))

#     # Fechar a splash screen e mostrar a janela principal após a animação
#     QTimer.singleShot(2000, lambda: splash.close())
#     QTimer.singleShot(2000, lambda: MainWindow(app).show())

#     sys.exit(app.exec())

# if __name__ == "__main__":
#     main()
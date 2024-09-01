from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import Qt

from diretorios import ACANTO_IMAGE_PATH, BRASIL_IMAGE_PATH, ICONS_DIR, ConfigManager, CONFIG_FILE

from modules.menu_superior.config.config_database import ConfigurarDatabaseDialog
from modules.menu_superior.config.config_responsaveis import AgentesResponsaveisDialog
from modules.menu_superior.config.config_om import OrganizacoesDialog
from modules.menu_superior.config.config_template import TemplatesDialog

import qdarktheme

class MenuManager:
    def __init__(self, parent):
        self.parent = parent
        self.menu_bar = QMenuBar()
        self.menu_bar.setStyleSheet(self.get_menu_bar_style())
        self.container = QWidget()
        self.container.setLayout(self._create_header_layout())
        self.container.setFixedHeight(32)

        self.parent.setMenuWidget(self.container)
        # Estado atual do tema
        self.current_theme = "dark"
        self.config_manager = ConfigManager(CONFIG_FILE)

    def _create_header_layout(self):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        # Configuração da imagem
        pixmap = QPixmap(str(ACANTO_IMAGE_PATH))
        # brasil_pixmap = QPixmap(str(BRASIL_IMAGE_PATH))

        if pixmap.isNull():
            print("Failed to load image!")
        else:
            pass
        pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # Adicionar o QMenuBar ao layout
        header_layout.addWidget(self.menu_bar)

        # Espaço expansível
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Configuração da imagem
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(image_label)

        return header_layout

    def create_menus(self):
        self.settings_menu = self.menu_bar.addMenu("Configurações")
        self.utilities_menu = self.menu_bar.addMenu("Utilidades")
        self.about_menu = self.menu_bar.addMenu("Sobre")

        self.add_menu_action(self.utilities_menu, "Alternar Tema (Dark/Light)", self.toggle_theme)

        # Adicionando novas ações ao menu de utilidades
        self.add_menu_action(self.utilities_menu, "Esconder Menu Lateral", self.toggle_menu_visibility)

        # Adicionando atalhos
        self.utilities_menu.actions()[1].setShortcut("F10")

        self.add_menu_action(self.settings_menu, "Configurar Database", self.show_configurar_database_dialog)
        self.add_menu_action(self.settings_menu, "Agentes Responsáveis", self.show_agentes_responsaveis_dialog)
        self.add_menu_action(self.settings_menu, "Templates", self.show_templates_dialog)        
        self.add_menu_action(self.settings_menu, "Organizações", self.show_organizacoes_dialog)

        self.add_menu_action(self.utilities_menu, "Ferramentas", self.tools)
        self.add_menu_action(self.about_menu, "Sobre", self.about)

    # Métodos para abrir os diálogos
    def show_configurar_database_dialog(self):
        dialog = ConfigurarDatabaseDialog(self.parent)
        dialog.exec()

    def show_agentes_responsaveis_dialog(self):
        dialog = AgentesResponsaveisDialog(self.parent)
        dialog.exec()

    def show_organizacoes_dialog(self):
        dialog = OrganizacoesDialog(self.parent)
        dialog.exec()


    def show_templates_dialog(self):
        # Corrigir passando o pai correto para o diálogo
        dialog = TemplatesDialog(self.config_manager, self.parent)  # Supondo que self.parent seja o QMainWindow ou outro QWidget
        dialog.exec()


    def add_menu_action(self, menu, action_name, method):
        action = QAction(action_name, self.parent)
        action.triggered.connect(method)
        menu.addAction(action)

    def toggle_theme(self):
        if self.current_theme == "dark":
            self.current_theme = "light"
        else:
            self.current_theme = "dark"
        self.parent.app.setStyleSheet(qdarktheme.load_stylesheet(self.current_theme))

    def toggle_menu_visibility(self):
        if self.parent.is_menu_visible:
            self.parent.menu_widget.hide()
        else:
            self.parent.menu_widget.show()
        self.parent.is_menu_visible = not self.parent.is_menu_visible

    def extend_window_horizontally(self):
        screen_geometry = self.parent.screen().availableGeometry()
        self.parent.setGeometry(self.parent.geometry().x(), self.parent.geometry().y(), screen_geometry.width(), self.parent.geometry().height())

    def extend_window_vertically(self):
        screen_geometry = self.parent.screen().availableGeometry()
        self.parent.setGeometry(self.parent.geometry().x(), self.parent.geometry().y(), self.parent.geometry().width(), screen_geometry.height())

    def new_message(self):
        self.parent.show_message("Nova Mensagem selecionada")

    def homologacao(self):
        self.parent.show_message("Homologação selecionada")

    def suspensao(self):
        self.parent.show_message("Suspensão selecionada")

    def equipe_planejamento(self):
        self.parent.show_message("Equipe de Planejamento selecionada")

    def plano_contratacao_anual(self):
        self.parent.show_message("Plano de Contratação Anual (PCA) selecionado")

    def conges_menu(self):
        self.parent.show_message("Conselho de Gestão selecionado")

    def standard_communication(self):
        self.parent.show_message("Comunicação Padronizada selecionada")

    def preferences(self):
        self.parent.show_message("Configurações selecionadas")

    def tools(self):
        self.parent.show_message("Utilidades selecionadas")

    def about(self):
        self.parent.show_message("Sobre selecionado")

    @staticmethod
    def get_menu_bar_style():
        return """
            QMenuBar {
                background-color: transparent;
                font-weight: bold;
                font-size: 16px;
                text-align: left;
                border: 0px solid transparent; 
                border-radius: 0px;
                padding: 0px;
                margin: 0px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 40px;  
                margin: 0px;
                border: none;
            }
            QMenuBar::item:selected {  
                background-color: #d3d3d3;  
                color: black;
                border: 0px solid transparent; 
                border-radius: 0px;
                margin: 0px;
            }
        """
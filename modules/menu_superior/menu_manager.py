from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import Qt

from diretorios import ACANTO_IMAGE_PATH, BRASIL_IMAGE_PATH

from modules.menu_superior.config.config_database import ConfigurarDatabaseDialog
from modules.menu_superior.config.config_responsaveis import AgentesResponsaveisDialog
from modules.menu_superior.config.config_om import OrganizacoesDialog

import qdarktheme

class MenuManager:
    def __init__(self, parent):
        self.parent = parent
        self.menu_bar = QMenuBar()
        self.menu_bar.setStyleSheet(self.get_menu_bar_style())
        self.container = QWidget()
        self.container.setLayout(self._create_header_layout())
        self.parent.setMenuWidget(self.container)
        # Estado atual do tema
        self.current_theme = "dark"

    def _create_header_layout(self):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        # Configuração da imagem
        pixmap = QPixmap(str(ACANTO_IMAGE_PATH))
        brasil_pixmap = QPixmap(str(BRASIL_IMAGE_PATH))

        if pixmap.isNull():
            print("Failed to load image!")
        else:
            pass
        pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        brasil_pixmap = brasil_pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        image_label_equerda = QLabel()
        image_label_equerda.setPixmap(brasil_pixmap)
        image_label_equerda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(image_label_equerda)
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

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
        self.message_menu = self.menu_bar.addMenu("Mensagem")
        self.standard_communication_menu = self.menu_bar.addMenu("Comunicação Padronizada")
        self.conselho_gestao_menu = self.menu_bar.addMenu("Conselho de Gestão")
        self.settings_menu = self.menu_bar.addMenu("Configurações")
        self.utilities_menu = self.menu_bar.addMenu("Utilidades")
        self.about_menu = self.menu_bar.addMenu("Sobre")

        self.add_menu_action(self.utilities_menu, "Alternar Tema (Dark/Light)", self.toggle_theme)

        # Adicionando novas ações ao menu de utilidades
        self.add_menu_action(self.utilities_menu, "Esconder Menu Lateral", self.toggle_menu_visibility)

        # Adicionando atalhos
        self.utilities_menu.actions()[0].setShortcut("F10")

        self.add_menu_action(self.message_menu, "Nova Mensagem", self.new_message)
        self.add_menu_action(self.message_menu, "Homologação", self.homologacao)
        self.add_menu_action(self.message_menu, "Suspensão", self.suspensao)
        self.add_menu_action(self.message_menu, "Equipe de Planejamento", self.equipe_planejamento)
        self.add_menu_action(self.message_menu, "Plano de Contratação Anual (PCA)", self.plano_contratacao_anual)

        self.add_menu_action(self.standard_communication_menu, "Modelo de Comunicação", self.standard_communication)
        self.add_menu_action(self.conselho_gestao_menu, "Conselho de Gestão", self.conges_menu)
        self.add_menu_action(self.settings_menu, "Configurar Database", self.show_configurar_database_dialog)
        self.add_menu_action(self.settings_menu, "Agentes Responsáveis", self.show_agentes_responsaveis_dialog)
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
                border-radius: 0px;
                border: 1px solid transparent;
            }
            QMenuBar::item {
                background-color: transparent;
                font-size: 14px;
            }
            QMenu {
                font-size: 14px;            
            }
        """
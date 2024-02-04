# main.py

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QCalendarWidget, QHBoxLayout, 
    QStackedWidget, QLabel, QSpacerItem, QSizePolicy, QPushButton, QTreeView, QMessageBox
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QIcon, QFont
from PyQt6.QtCore import QSize, QDate, Qt
import qdarkstyle
from diretorios import *
from custom_widgets.create_2_planejamento_button import ApplicationUI
from custom_widgets.create_3_fases_button import ProcessosWidget
from custom_widgets.create_4_contagem_dias_button import ContagemDias
from custom_widgets.create_5_documentos_button import DocumentosWidget
from custom_widgets.create_8_pregoeiro_button import PregoeiroWidget
from custom_widgets.create_10_controle_vigencia_button import ContratosWidget
from custom_widgets.create_7_checklist_button import ChecklistWidget
from custom_widgets.create_9_atas_button import AtasWidget
from custom_widgets.create_configuracoes_button import ConfiguracoesWidget
import pandas as pd

class PageConfig:
    def __init__(self, text, icon_path, widget_class, *widget_args, custom_callback=None):
        self.text = text
        self.icon_path = str(icon_path)
        self.widget_class = widget_class
        self.widget_args = widget_args
        self.custom_callback = custom_callback

    def create_widget(self):
        return self.widget_class(*self.widget_args)

class App(QMainWindow):
    def create_button(self, text, icon_path=None, callback=None):
        button = QPushButton(text)
        
        # Define a fonte aqui
        font = QFont()
        font.setFamily("Arial")  # Use "Arial" como fonte alternativa
        font.setPointSize(14)  # Tamanho da fonte
        button.setFont(font)

        if icon_path:
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(24, 24))  # Ajuste o tamanho conforme necessário
        if callback:
            button.clicked.connect(callback)
        self.menu_layout.addWidget(button)
        return button

    def create_label(self, text, font_size=14, alignment=Qt.AlignmentFlag.AlignLeft):
        label = QLabel(text)
        font = QFont()
        font.setPointSize(font_size)
        label.setFont(font)
        label.setAlignment(alignment)
        return label

    def add_page(self, button_text, page_widget, icon_path=None, custom_callback=None):
        page_index = self.stack_layout.addWidget(page_widget)
        button = self.create_button(button_text, icon_path, self.change_page if custom_callback is None else custom_callback)
        button.page_index = page_index
        return page_index 

    def setup_ui(self):
        self.page_configs = [
            PageConfig("Início", ICONS_DIR / "home_menu.png", self.create_inicio_page),
            PageConfig("Planejamento", ICONS_DIR / "planning_menu.png", ApplicationUI, self, str(ICONS_DIR), str(DATABASE_DIR), str(LV_FINAL_DIR)),
            PageConfig("Fases do Processo", ICONS_DIR / "steps.png", ProcessosWidget, self),
            PageConfig("Informações do Processo", ICONS_DIR / "verify_menu.png", ContagemDias, self, str(DATABASE_DIR)),
            PageConfig("Documentos Licitação", ICONS_DIR / "docx_menu.png", DocumentosWidget, self),
            PageConfig("Dispensa Eletrônica", ICONS_DIR / "docx_menu.png", DocumentosWidget, self),
            PageConfig("Check-list", ICONS_DIR / "search_menu.png", ChecklistWidget, str(ICONS_DIR), self),
            PageConfig("Escalação de Pregoeiros", ICONS_DIR / "law_menu.png", PregoeiroWidget, self),
            PageConfig("Atas e Contratos", ICONS_DIR / "verify_menu.png", AtasWidget, str(ICONS_DIR), self),
            PageConfig("Controle de Vigência", ICONS_DIR / "contrato.png", ContratosWidget, self),
            # PageConfig("Calendário", ICONS_DIR / "calendar_menu.png", QWidget),
            PageConfig("Configurações", ICONS_DIR / "gear_menu.png", ConfiguracoesWidget, self)
        ]

        # Itera sobre a lista de configurações
        for config in self.page_configs:
            page_widget = config.create_widget()
            page_index = self.add_page(config.text, page_widget, config.icon_path, config.custom_callback)
            if config.text == "Início":
                self.index_da_pagina_inicio = page_index

    def create_page(self, widget_class, *args):
        return widget_class(*args)

    def __init__(self):
        super().__init__()
        self.menu_visible = True  # Adiciona esta linha para inicializar o atributo
        self.initialize_window()
        self.create_layouts()
        self.setup_ui()
        self.add_spacer_and_label()

    def initialize_window(self):
        self.setWindowTitle("Eagle Eye")
        self.setGeometry(0, 0, 1500, 700)
        stylesheet = qdarkstyle.load_stylesheet() + "QWidget { background-color: black; }"
        self.setStyleSheet(stylesheet)

    def create_layouts(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.outer_layout = QHBoxLayout(self.central_widget)

        self.menu_layout = QVBoxLayout()
        self.menu_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_layout.setSpacing(5)

        self.main_layout = QHBoxLayout()  
        self.main_layout.addLayout(self.menu_layout)

        self.stack_layout = QStackedWidget(self)
        self.main_layout.addWidget(self.stack_layout)
        self.outer_layout.addLayout(self.main_layout)

    def add_spacer_and_label(self):
        self.selecionado_label = QLabel("")
        self.selecionado_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        self.selecionado_label.setFont(font)
        self.menu_layout.addWidget(self.selecionado_label)

        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.menu_layout.addItem(spacer)
       
    def toggle_menu(self):
        self.menu_visible = not self.menu_visible
        for i in range(self.menu_layout.count()):
            widget = self.menu_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(self.menu_visible)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F1:
            # Simplesmente alterna a visibilidade do menu
            self.toggle_menu()
        elif event.key() == Qt.Key_F5:
            # Alterna o estado de tela cheia
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key_Escape:
            # Se o menu está oculto e o programa está em tela cheia, sai do modo tela cheia e mostra o menu
            if not self.menu_visible and self.isFullScreen():
                self.showNormal()
                self.toggle_menu()
        # Continua com o comportamento padrão do evento de tecla
        super().keyPressEvent(event)

    def change_page(self):
        button = self.sender()
        if hasattr(button, 'page_index'):
            # Muda para a página associada ao índice do botão
            self.stack_layout.setCurrentIndex(button.page_index)

    def create_image_label(self, image_path):
        label = QLabel()
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(QSize(800, 600), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
        label.setScaledContents(True)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return label
   
    def create_inicio_page(self):
        # Aqui você define como a página de início é criada
        inicio_page = QWidget()
        inicio_layout = QVBoxLayout(inicio_page)
        
        # Aqui, você pode adicionar o conteúdo da página de início
        # Por exemplo, uma imagem ou qualquer outro widget
        label = self.create_image_label(str(IMAGE_AGUIA_PATH))
        inicio_layout.addWidget(label)

        return inicio_page
    
    def show_inicio_page(self):
        # Muda para a página de início
        self.stack_layout.setCurrentIndex(self.index_da_pagina_inicio)

    def atualizar_label_selecionado(self):
        df_registro_selecionado = self.carregar_dados_pregao()
        if df_registro_selecionado is not None and not df_registro_selecionado.empty:
            num_pregao = df_registro_selecionado['num_pregao'].iloc[0]
            ano_pregao = df_registro_selecionado['ano_pregao'].iloc[0]
            self.selecionado_label.setText(f"\n PE {num_pregao}-{ano_pregao} \n Selecionado!")
        else:
            self.selecionado_label.setText("")

    def pregao_selecionado(self):
        self.atualizar_label_selecionado()

    def read_file(self, file_path, file_type='csv'):
        try:
            if file_type == 'csv':
                return pd.read_csv(file_path)
            # Adicionar mais condições para diferentes tipos de arquivos
        except Exception as e:
            QMessageBox.warning(None, "Erro", f"Erro ao ler o arquivo {file_path}: {e}")
            return None

    def carregar_dados_pregao(self):
        return self.read_file(ITEM_SELECIONADO_PATH, 'csv')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())  # Chamada correta
    ex = App()
    ex.show()
    sys.exit(app.exec())  

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys
import pandas as pd
from pathlib import Path
from diretorios import ICONS_DIR, IMAGE_PATH, DATABASE_DIR, LV_FINAL_DIR, ITEM_SELECIONADO_PATH, BASE_DIR
from styles.styless import (
    get_menu_button_style, get_menu_title_style, get_content_title_style, 
    get_menu_button_activated_style, get_updated_background
)
from custom_widgets.create_1_inicio import InicioWidget
from custom_widgets.create_2_planejamento_button import ApplicationUI
from custom_widgets.create_3_fases_button import ProcessosWidget
from custom_widgets.create_4_contagem_dias_button import ContagemDias
from custom_widgets.create_5_documentos_button import DocumentosWidget
from custom_widgets.create_7_checklist_button import ChecklistWidget
from custom_widgets.create_8_pregoeiro_button import PregoeiroWidget
from custom_widgets.create_9_atas_button import AtasWidget
from custom_widgets.create_10_controle_vigencia_button import ContratosWidget
from custom_widgets.create_11_numerador_button import NumeradorCP
from custom_widgets.create_12_msg_button import HallResponsaveis
from custom_widgets.create_13_registro_fornec_button import RegistroFornecedor
from custom_widgets.create_configuracoes_button import ConfiguracoesWidget
from custom_selenium.selenium_automation import SeleniumAutomacao

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.open_initial_page()

    def setup_ui(self):
        self.setWindowTitle("Sistema de Gestão de Licitações")
        self.resize(1500, 750)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Configurar a imagem de fundo
        self.background_label = QLabel(self.central_widget)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.setScaledContents(True)

        self.update_background()
        self.setup_menu()
        self.setup_content_area()

        self.active_button = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.update_background()

    def update_background(self):
        bg_image_path = IMAGE_PATH / "bg1.png"
        final_pixmap = get_updated_background(self.size(), bg_image_path)
        self.background_label.setPixmap(final_pixmap)

    def setup_menu(self):
        menu_layout = QVBoxLayout()
        menu_layout.setSpacing(0)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        menu_title = QLabel("Menu Principal")
        menu_title.setStyleSheet(get_menu_title_style())
        menu_layout.addWidget(menu_title)

        menu_buttons = [
            (" Início", ICONS_DIR / "x.png"),
            (" Planejamento", ICONS_DIR / "x.png"), 
            (" Fases do Processo", ICONS_DIR / "x.png"), 
            (" Informações do Processo", ICONS_DIR / "x.png"), 
            (" Documentos Licitação", ICONS_DIR / "x.png"), 
            (" Dispensa Eletrônica", ICONS_DIR / "x.png"), 
            (" Check-list", ICONS_DIR / "x.png"), 
            (" Escalação de Pregoeiros", ICONS_DIR / "x.png"), 
            (" Atas e Contratos", ICONS_DIR / "x.png"), 
            (" Controle de Vigência", ICONS_DIR / "x.png"), 
            (" Numerador de CP", ICONS_DIR / "x.png"),
            (" Mensagens Padronizadas", ICONS_DIR / "x.png"),   
            (" Registro de Fornecedores", ICONS_DIR / "x.png"),
            (" Selenium", ICONS_DIR / "x.png"),  
        ]

        self.buttons = {}
        icon_size = QSize(30, 30) 

        for button_name, icon_name in menu_buttons:
            button = QPushButton(button_name)
            icon_path = ICONS_DIR / icon_name
            button.setIcon(QIcon(str(icon_path)))
            button.setIconSize(icon_size)
            button.setStyleSheet(get_menu_button_style())

            if button_name.strip() == "Início":
                button.clicked.connect(self.open_initial_page)
            else:
                # Conectar outros botões à função update_content_title
                button.clicked.connect(self.update_content_title)

            self.buttons[button_name.strip()] = button
            menu_layout.addWidget(button)

        menu_widget = QWidget()
        menu_widget.setLayout(menu_layout)
        menu_widget.setFixedWidth(260)  # Definir a largura fixa para o menu lateral
        
        # Adicionar um QLabel para mostrar o pregão selecionado
        self.selecionado_label = QLabel("\n\n", self.central_widget)  # Use 'self' para torná-lo um atributo da classe
        self.selecionado_label.setStyleSheet(get_menu_title_style())
        menu_layout.addWidget(self.selecionado_label)

        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.addWidget(menu_widget)
        self.main_layout.update()  # Forçar a atualização do layout

    def atualizar_label_selecionado(self):
        df_registro_selecionado = self.carregar_dados_pregao()
        if df_registro_selecionado is not None and not df_registro_selecionado.empty:
            mod = df_registro_selecionado['mod'].iloc[0]
            num_pregao = df_registro_selecionado['num_pregao'].iloc[0]
            ano_pregao = df_registro_selecionado['ano_pregao'].iloc[0]
            self.selecionado_label.setText(f"\n {mod} {num_pregao}-{ano_pregao} \n Selecionado!")  # Agora 'self.selecionado_label' é reconhecido
        else:
            self.selecionado_label.setText("")

    def pregao_selecionado(self):
        self.atualizar_label_selecionado()

    def carregar_dados_pregao(self):
        # Carregar o arquivo CSV com os dados do pregão selecionado
        if ITEM_SELECIONADO_PATH.exists():
            df_registro_selecionado = pd.read_csv(ITEM_SELECIONADO_PATH)
            return df_registro_selecionado
        return None

    def setup_content_area(self):
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_image_label = QLabel(self.central_widget)
        self.content_layout.addWidget(self.content_image_label)
        self.content_image_label.hide()  # Ocultar inicialmente

        content_widget = QWidget()
        content_widget.setLayout(self.content_layout)
        content_widget.setMinimumSize(600, 600)
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet("""
            QWidget#contentWidget {
                background-color: rgba(0, 0, 0, 60);
                border: 1px solid #ffffff;
            }
        """)

        self.main_layout.addWidget(content_widget)

        self.inicio_widget = InicioWidget(self)
        self.inicio_widget.planejamentoClicked.connect(lambda: self.change_content("Planejamento"))
        self.inicio_widget.fasesProcessoClicked.connect(lambda: self.change_content("Fases do Processo"))
        self.inicio_widget.infoProcessoClicked.connect(lambda: self.change_content("Informações do Processo"))
        self.inicio_widget.documentosLicitacaoClicked.connect(lambda: self.change_content("Documentos Licitação"))
        self.inicio_widget.controleVigenciaClicked.connect(lambda: self.change_content("Controle de Vigência"))
        self.inicio_widget.checklistClicked.connect(lambda: self.change_content("Check-list"))
        self.inicio_widget.escalacaoPregoeirosClicked.connect(lambda: self.change_content("Escalação de Pregoeiros"))
        self.inicio_widget.numeradorCpClicked.connect(lambda: self.change_content("Numerador de CP"))
        self.inicio_widget.mensagensPadronizadasClicked.connect(lambda: self.change_content("Mensagens Padronizadas"))
        self.inicio_widget.registroFornecedoresClicked.connect(lambda: self.change_content("Registro de Fornecedores"))
        self.inicio_widget.seleniumAutomacaoClicked.connect(lambda: self.change_content("Selenium"))

    def change_content(self, content_name):
        content_actions = {
            "Planejamento": self.setup_planejamento,
            "Fases do Processo": self.setup_fases_do_processo,
            "Informações do Processo": self.setup_informacoes_do_processo,
            "Documentos Licitação": self.setup_documentos_licitacao,
            "Controle de Vigência": self.setup_controle_vigencia,
            "Check-list": self.setup_checklist,
            "Atas e Contratos": self.setup_atas_contratos,
            "Escalação de Pregoeiros": self.setup_escala_pregoeiros,
            "Numerador de CP": self.setup_numerador_cp,
            "Mensagens Padronizadas": self.setup_mensagens_padronizadas,
            "Registro de Fornecedores": self.setup_registro_fornecedores,
            "Selenium": self.setup_selenium_automacao,
        }
        action = content_actions.get(content_name)
        if action:
            action()
        self.update_menu_button_style(content_name)

    def update_content_title(self, button=None):
        if not button:
            button = self.sender()
        if button:
            if self.active_button:
                self.reset_button_style(self.active_button)
            self.set_active_button_style(button)
            self.active_button = button

            button_actions = {
                "Início": self.open_initial_page,
                "Fases do Processo": self.setup_fases_do_processo,
                "Planejamento": self.setup_planejamento,
                "Informações do Processo": self.setup_informacoes_do_processo,
                "Documentos Licitação": self.setup_documentos_licitacao,
                "Controle de Vigência": self.setup_controle_vigencia,
                "Check-list": self.setup_checklist,
                "Atas e Contratos": self.setup_atas_contratos,
                "Escalação de Pregoeiros": self.setup_escala_pregoeiros,
                "Numerador de CP": self.setup_numerador_cp,
                "Mensagens Padronizadas": self.setup_mensagens_padronizadas,
                "Registro de Fornecedores": self.setup_registro_fornecedores,
                "Selenium": self.setup_selenium_automacao,
            }
        
            action = button_actions.get(button.text().strip())
            if action:
                action()

    def setup_fases_do_processo(self):
        self.clear_content_area()
        self.processos_widget = ProcessosWidget(self)
        self.content_layout.addWidget(self.processos_widget)

    def open_initial_page(self):
        self.clear_content_area(keep_image_label=True)
        self.content_layout.addWidget(self.inicio_widget)        
        # Aplicar estilo ativo ao botão 'Início'
        if "Início" in self.buttons:
            self.set_active_button_style(self.buttons["Início"])

    def setup_planejamento(self):
        self.clear_content_area()
        self.application_ui = ApplicationUI(self, str(ICONS_DIR), str(DATABASE_DIR), str(LV_FINAL_DIR))
        self.application_ui.itemSelected.connect(self.pregao_selecionado)
        self.content_layout.addWidget(self.application_ui)

    def setup_informacoes_do_processo(self):
        self.clear_content_area()
        self.contagem_dias_widget = ContagemDias(self, str(DATABASE_DIR))
        self.content_layout.addWidget(self.contagem_dias_widget)

    def setup_documentos_licitacao(self):
        self.clear_content_area()
        self.gerar_documentos_widget = DocumentosWidget(self)
        self.content_layout.addWidget(self.gerar_documentos_widget)

    def setup_controle_vigencia(self):
        self.clear_content_area()
        self.controle_vigencia_widget = ContratosWidget(self)
        self.content_layout.addWidget(self.controle_vigencia_widget)
    
    def setup_checklist(self):
        self.clear_content_area()
        self.checklist_widget = ChecklistWidget(self, str(ICONS_DIR))
        self.content_layout.addWidget(self.checklist_widget)
    
    def setup_atas_contratos(self):
        self.clear_content_area()
        self.atas_contratos_widget = AtasWidget(str(ICONS_DIR), self)
        self.content_layout.addWidget(self.atas_contratos_widget)
    
    def setup_escala_pregoeiros(self):
        self.clear_content_area()
        dtypes_dict = {'num_pregao': str, 'ano_pregao': str}  # Substitua com os tipos de dados corretos
        self.escalar_pregoeiro_widget = PregoeiroWidget(self, dtypes=dtypes_dict, app=self)
        self.escalar_pregoeiro_widget.itemSelected.connect(self.pregao_selecionado)
        self.content_layout.addWidget(self.escalar_pregoeiro_widget)

    def setup_numerador_cp(self):
        self.clear_content_area()
        self.numerador_cp_widget = NumeradorCP(self)
        self.content_layout.addWidget(self.numerador_cp_widget)

    def setup_mensagens_padronizadas(self):
        self.clear_content_area()
        self.hall_responsaveis_widget = HallResponsaveis(self)
        self.content_layout.addWidget(self.hall_responsaveis_widget)
    
    def setup_registro_fornecedores(self):
        self.clear_content_area()
        self.registro_fornecedor_widget = RegistroFornecedor(self)
        self.content_layout.addWidget(self.registro_fornecedor_widget)

    def setup_selenium_automacao(self):
        self.clear_content_area()
        self.selenium_widget = SeleniumAutomacao(self)
        self.content_layout.addWidget(self.selenium_widget)

    def clear_content_area(self, keep_image_label=False):
        for i in reversed(range(self.content_layout.count())): 
            layout_item = self.content_layout.itemAt(i)
            if layout_item is not None:
                widget = layout_item.widget()
                if widget is not None:
                    if widget is self.content_image_label:
                        if not keep_image_label:
                            widget.hide()  # Oculta o QLabel da imagem
                    else:
                        widget.setParent(None)  # Remove outros widgets

    def reset_button_style(self, button):
        button.setStyleSheet(get_menu_button_style())

    def set_active_button_style(self, button):
        if self.active_button and self.active_button != button:
            self.reset_button_style(self.active_button)
        button.setStyleSheet(get_menu_button_activated_style())
        self.active_button = button

    def update_menu_button_style(self, button_name):
        if self.active_button:
            self.reset_button_style(self.active_button)
        if button_name in self.buttons:
            self.set_active_button_style(self.buttons[button_name])
            self.active_button = self.buttons[button_name]

# Executando a aplicação
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
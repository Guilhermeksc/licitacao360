from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    apply_widget_style_11, create_button, get_descricao_servico, copyToClipboard, 
                                    get_preposicao_tipo, create_sinopse_text, validate_and_convert_date, create_sigdem_layout)
from diretorios import *
import os

def create_etp_group(data, templatePath):
    # Cria o layout principal
    main_layout = QVBoxLayout()

    # Adiciona a label para o título
    titulo_label = QLabel("Estudo Técnico Preliminar (ETP)")
    titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    titulo_label.setStyleSheet("background-color: #202124; color: #8AB4F7; font-size: 18px; font-weight: bold")
    main_layout.addWidget(titulo_label)

    # Armazena o valor do título
    titulo = titulo_label.text()

    # Cria a barra de rolagem
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)

    # Cria o conteúdo da barra de rolagem
    scroll_content = QWidget()
    scroll_layout = QVBoxLayout(scroll_content)

    # Layout para Informações Básicas
    informacoes_basicas_layout = create_informacoes_basicas_layout(data)
    scroll_layout.addLayout(informacoes_basicas_layout)

    # Define o layout do conteúdo da barra de rolagem
    scroll_area.setWidget(scroll_content)

    # Adiciona a barra de rolagem ao layout principal
    main_layout.addWidget(scroll_area)

    # Layout para Sigdem e Menu (fora da barra de rolagem)
    sigdem_layout = create_sigdem_layout(data, titulo)
    menu_layout = create_menu_layout(templatePath)

    sigdem_menu_layout = QHBoxLayout()
    sigdem_menu_layout.addWidget(sigdem_layout)
    sigdem_menu_layout.addWidget(menu_layout)
    sigdem_menu_layout.setStretch(0, 4)
    sigdem_menu_layout.setStretch(1, 1)

    sigdem_menu_widget = QWidget()
    sigdem_menu_widget.setLayout(sigdem_menu_layout)
    sigdem_menu_widget.setFixedHeight(250)  # Define a altura fixa de 350

    main_layout.addWidget(sigdem_menu_widget)

    # Cria um widget para o grupo ETP e define o layout
    etp_group_widget = QWidget()
    etp_group_widget.setLayout(main_layout)

    return etp_group_widget

def create_informacoes_basicas_layout(data):
    layout = QVBoxLayout()

    # Criação dos campos conforme solicitado
    campos = [
        "DESCRIÇÃO DA NECESSIDADE",
        "LEVANTAMENTO DE MERCADO",
        "DEFINIÇÃO DO OBJETO",
        "PARCELAMENTO DO OBJETO DA CONTRATAÇÃO",
        "INSTRUMENTOS DE GOVERNANÇA - PCA, PLS E OUTROS",
        "JUSTIFICATIVA PARA A NÃO INCLUSÃO DE TODOS OS ELEMENTOS DO ETP",
        "DECLARAÇÃO DE VIABILIDADE"
    ]

    for campo in campos:
        label = QLabel(campo + ":")
        label.setStyleSheet("color: #8AB4F7; font-size: 16px")
        text_edit = QTextEdit()
        text_edit.setFixedHeight(100)  # Aproximadamente 5 linhas de altura
        layout.addWidget(label)
        layout.addWidget(text_edit)

    return layout

def create_menu_layout(templatePath):
    menu_group_box = QGroupBox("Menu")
    apply_widget_style_11(menu_group_box)
    menu_group_box.setFixedWidth(230)
    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    layout.setSpacing(10)

    icon_context = QIcon(str(ICONS_DIR / "context.png"))
    icon_text = QIcon(str(ICONS_DIR / "will.png"))
    icon_gerar_documento = QIcon(str(ICONS_DIR / "contract.png"))

    buttons = [
        create_button(
            text="Inserir Contexto", 
            icon=icon_context,
            tooltip_text="Inserir contexto",
            callback=lambda: print("Inserir Contexto clicked"),
            button_size=QSize(200, 50),
            icon_size=QSize(45, 45)
        ),
        create_button(
            text="     Gerar Texto   ",
            icon=icon_text,
            tooltip_text="Gerar texto",
            callback=lambda: print("Gerar Texto clicked"),
            button_size=QSize(200, 50),
            icon_size=QSize(45, 45)
        ),
        create_button(
            text=" Gerar Documento ",                   
            icon=icon_gerar_documento,
            callback=lambda: print("Gerar Texto clicked"),
            tooltip_text="Clique para gerar o ETP",
            button_size=QSize(200, 50),
            icon_size=QSize(45, 45)
        )
    ]

    layout.addStretch()
    for button in buttons:
        layout.addWidget(button)
    layout.addStretch()

    menu_group_box.setLayout(layout)
    return menu_group_box

def carregar_template(templatePath, objeto_text_edit):
    if os.path.exists(templatePath):
        with open(templatePath, 'r', encoding='utf-8') as file:
            template_content = file.read()
            objeto_text_edit.setText(template_content)
    else:
        QMessageBox.warning(None, "Aviso", "Template não encontrado no caminho especificado.")
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    apply_widget_style_11, create_button, get_descricao_servico, copyToClipboard, 
                                    get_preposicao_tipo, create_sinopse_text, validate_and_convert_date, create_sigdem_layout)
from diretorios import *
import os

def create_nt_group(data, templatePath):
    # Cria o layout principal
    main_layout = QVBoxLayout()

    # Adiciona a label para o título
    titulo_label = QLabel("Nota Técnica")
    titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    titulo_label.setStyleSheet("color: #8AB4F7; font-size: 18px; font-weight: bold")
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
    informacoes_basicas_layout = create_tr_layout(data)
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

    # Cria um widget para conter o layout sigdem_menu_layout
    sigdem_menu_widget = QWidget()
    sigdem_menu_widget.setLayout(sigdem_menu_layout)
    sigdem_menu_widget.setFixedHeight(250)  # Define a altura fixa de 350

    main_layout.addWidget(sigdem_menu_widget)

    # Cria um widget para o grupo MR e define o layout
    mr_group_widget = QWidget()
    mr_group_widget.setLayout(main_layout)

    return mr_group_widget

def create_tr_layout(data):
    # Cria um layout vertical principal
    layout = QVBoxLayout()

    # Label e QTextEdit para Endereço de Entrega
    endereco_layout = QHBoxLayout()
    endereco_label = QLabel("Endereço de Entrega:")
    apply_widget_style_11(endereco_label)
    endereco_text_edit = QTextEdit()
    endereco_text_edit.setMaximumHeight(60)
    apply_widget_style_11(endereco_text_edit)
    endereco_layout.addWidget(endereco_label)
    endereco_layout.addWidget(endereco_text_edit)
    layout.addLayout(endereco_layout)

    # Label e QLineEdit para Prazo para itens rejeitados
    prazo_rejeitados_layout = QHBoxLayout()
    prazo_rejeitados_label = QLabel("Prazo para itens rejeitados:")
    apply_widget_style_11(prazo_rejeitados_label)
    prazo_rejeitados_value = QLineEdit("30 (trinta) dias")
    apply_widget_style_11(prazo_rejeitados_value)
    prazo_rejeitados_layout.addWidget(prazo_rejeitados_label)
    prazo_rejeitados_layout.addWidget(prazo_rejeitados_value)
    layout.addLayout(prazo_rejeitados_layout)

    # Label e QLineEdit para Prazo máximo para o recebimento definitivo
    prazo_recebimento_layout = QHBoxLayout()
    prazo_recebimento_label = QLabel("Prazo máximo para o recebimento definitivo:")
    apply_widget_style_11(prazo_recebimento_label)
    prazo_recebimento_value = QLineEdit("30 (trinta) dias")
    apply_widget_style_11(prazo_recebimento_value)
    prazo_recebimento_layout.addWidget(prazo_recebimento_label)
    prazo_recebimento_layout.addWidget(prazo_recebimento_value)
    layout.addLayout(prazo_recebimento_layout)

    # Label e QComboBox para Índice de correção monetária
    correcao_layout = QHBoxLayout()
    correcao_label = QLabel("Índice de correção monetária:")
    apply_widget_style_11(correcao_label)
    correcao_combobox = QComboBox()
    correcao_combobox.addItems(["IPCA-E", "IGPM", "IPCA", "X", "Y", "Z"])
    apply_widget_style_11(correcao_combobox)
    correcao_layout.addWidget(correcao_label)
    correcao_layout.addWidget(correcao_combobox)
    layout.addLayout(correcao_layout)

    # Label e QComboBox para Forma de fornecimento
    fornecimento_layout = QHBoxLayout()
    fornecimento_label = QLabel("Forma de fornecimento:")
    apply_widget_style_11(fornecimento_label)
    fornecimento_combobox = QComboBox()
    fornecimento_combobox.addItems(["integral", "parcelado", "continuado"])
    apply_widget_style_11(fornecimento_combobox)
    fornecimento_layout.addWidget(fornecimento_label)
    fornecimento_layout.addWidget(fornecimento_combobox)
    layout.addLayout(fornecimento_layout)

    # Label e QLabel para Índices de Liquidez Geral (LG)
    liquidez_layout = QHBoxLayout()
    liquidez_label = QLabel("Índices de Liquidez Geral (LG):")
    apply_widget_style_11(liquidez_label)
    liquidez_value = QLineEdit("10%")
    apply_widget_style_11(liquidez_value)
    liquidez_layout.addWidget(liquidez_label)
    liquidez_layout.addWidget(liquidez_value)
    layout.addLayout(liquidez_layout)

    return layout

def create_menu_layout(templatePath):
    menu_group_box = QGroupBox("Menu")
    apply_widget_style_11(menu_group_box)
    menu_group_box.setFixedWidth(230)
    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    layout.setSpacing(10)

    icon_table = QIcon(str(ICONS_DIR / "table.png"))
    icon_gerar_documento = QIcon(str(ICONS_DIR / "contract.png"))

    buttons = [
        create_button(
            text=" Importar Tabela ",
            icon=icon_table,
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
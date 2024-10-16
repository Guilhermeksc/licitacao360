from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    apply_widget_style_11, create_button, create_layout, get_descricao_servico, copyToClipboard, 
                                    get_preposicao_tipo, create_sinopse_text, validate_and_convert_date, create_sigdem_layout)
from diretorios import *
import os

def create_tr_group(data, templatePath, parent_dialog):
    # Create the main layout
    main_layout = QVBoxLayout()

    # Add a label for the title
    titulo_label = QLabel("Termo de Referência (TR)")
    titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    titulo_label.setStyleSheet("color: #8AB4F7; font-size: 18px; font-weight: bold")
    main_layout.addWidget(titulo_label)

    # Store the title value
    titulo = titulo_label.text()

    # Create a scroll area
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)

    # Create the scroll area content
    scroll_content = QWidget()
    scroll_layout = QVBoxLayout(scroll_content)

    # Layout for Basic Information and Budget Classification
    informacoes_basicas_layout = QHBoxLayout()
    informacoes_basicas_layout.addLayout(create_tr_layout(data, parent_dialog))  # Left layout

    classificacao_orcamentaria_group = create_classificacao_orcamentaria_group(data, parent_dialog)  # Right widget
    informacoes_basicas_layout.addWidget(classificacao_orcamentaria_group)

    # Set the proportion between the layouts
    informacoes_basicas_layout.setStretch(0, 3)
    informacoes_basicas_layout.setStretch(1, 1)

    # Add the basic information layout to the scroll layout
    scroll_layout.addLayout(informacoes_basicas_layout)

    # Set the scroll content layout
    scroll_area.setWidget(scroll_content)

    # Add the scroll area to the main layout
    main_layout.addWidget(scroll_area)

    # Layout for Sigdem and Menu (outside the scroll area)
    sigdem_layout = create_sigdem_layout(data, titulo)
    menu_layout = create_menu_layout(templatePath)

    sigdem_menu_layout = QHBoxLayout()
    sigdem_menu_layout.addWidget(sigdem_layout)
    sigdem_menu_layout.addWidget(menu_layout)
    sigdem_menu_layout.setStretch(0, 4)
    sigdem_menu_layout.setStretch(1, 1)

    # Create a widget to contain the sigdem_menu_layout
    sigdem_menu_widget = QWidget()
    sigdem_menu_widget.setLayout(sigdem_menu_layout)
    sigdem_menu_widget.setFixedHeight(250)  # Set fixed height

    main_layout.addWidget(sigdem_menu_widget)

    # Create a widget for the TR group and set the layout
    tr_group_widget = QWidget()
    tr_group_widget.setLayout(main_layout)

    return tr_group_widget

def create_classificacao_orcamentaria_group(data, parent_dialog):
    classificacao_orcamentaria_group_box = QGroupBox("Classificação Orçamentária")
    apply_widget_style_11(classificacao_orcamentaria_group_box)
    classificacao_orcamentaria_group_box.setFixedWidth(350)
    classificacao_orcamentaria_layout = QVBoxLayout()

    # Set widgets as attributes of parent_dialog
    parent_dialog.acao_interna_edit = QLineEdit(data.get('acao_interna', ''))
    parent_dialog.fonte_recurso_edit = QLineEdit(data.get('fonte_recursos', ''))
    parent_dialog.natureza_despesa_edit = QLineEdit(data.get('natureza_despesa', ''))
    parent_dialog.unidade_orcamentaria_edit = QLineEdit(data.get('unidade_orcamentaria', ''))
    parent_dialog.ptres_edit = QLineEdit(data.get('ptres', ''))

    # Use the create_layout function
    classificacao_orcamentaria_layout.addLayout(create_layout("Ação Interna:", parent_dialog.acao_interna_edit, apply_style_fn=apply_widget_style_11))
    classificacao_orcamentaria_layout.addLayout(create_layout("Fonte de Recurso (FR):", parent_dialog.fonte_recurso_edit, apply_style_fn=apply_widget_style_11))
    classificacao_orcamentaria_layout.addLayout(create_layout("Natureza de Despesa (ND):", parent_dialog.natureza_despesa_edit, apply_style_fn=apply_widget_style_11))
    classificacao_orcamentaria_layout.addLayout(create_layout("Unidade Orçamentária (UO):", parent_dialog.unidade_orcamentaria_edit, apply_style_fn=apply_widget_style_11))
    classificacao_orcamentaria_layout.addLayout(create_layout("PTRES:", parent_dialog.ptres_edit, apply_style_fn=apply_widget_style_11))

    classificacao_orcamentaria_group_box.setLayout(classificacao_orcamentaria_layout)

    return classificacao_orcamentaria_group_box

def create_tr_layout(data, parent_dialog):
    # Create a main vertical layout
    layout = QVBoxLayout()

    # Label and QTextEdit for Delivery Address
    endereco_layout = QHBoxLayout()
    endereco_label = QLabel("Endereço de Entrega:")
    apply_widget_style_11(endereco_label)
    parent_dialog.endereco_text_edit = QTextEdit(data.get('endereco_entrega', ''))
    parent_dialog.endereco_text_edit.setMaximumHeight(60)
    apply_widget_style_11(parent_dialog.endereco_text_edit)
    endereco_layout.addWidget(endereco_label)
    endereco_layout.addWidget(parent_dialog.endereco_text_edit)
    layout.addLayout(endereco_layout)

    # Label and QLineEdit for Deadline for Rejected Items
    prazo_rejeitados_layout = QHBoxLayout()
    prazo_rejeitados_label = QLabel("Prazo para itens rejeitados:")
    apply_widget_style_11(prazo_rejeitados_label)
    parent_dialog.prazo_rejeitados_value = QLineEdit(data.get('prazo_itens_rejeitados', '30 (trinta) dias'))
    apply_widget_style_11(parent_dialog.prazo_rejeitados_value)
    prazo_rejeitados_layout.addWidget(prazo_rejeitados_label)
    prazo_rejeitados_layout.addWidget(parent_dialog.prazo_rejeitados_value)
    layout.addLayout(prazo_rejeitados_layout)

    # Label and QLineEdit for Maximum Deadline for Definitive Receipt
    prazo_recebimento_layout = QHBoxLayout()
    prazo_recebimento_label = QLabel("Prazo máximo para o recebimento definitivo:")
    apply_widget_style_11(prazo_recebimento_label)
    parent_dialog.prazo_recebimento_value = QLineEdit(data.get('prazo_recebimento_definitivo', '30 (trinta) dias'))
    apply_widget_style_11(parent_dialog.prazo_recebimento_value)
    prazo_recebimento_layout.addWidget(prazo_recebimento_label)
    prazo_recebimento_layout.addWidget(parent_dialog.prazo_recebimento_value)
    layout.addLayout(prazo_recebimento_layout)

    # Label and QComboBox for Monetary Correction Index
    correcao_layout = QHBoxLayout()
    correcao_label = QLabel("Índice de correção monetária:")
    apply_widget_style_11(correcao_label)
    parent_dialog.correcao_combobox = QComboBox()
    parent_dialog.correcao_combobox.addItems(["IPCA-E", "IGPM", "IPCA", "X", "Y", "Z"])
    parent_dialog.correcao_combobox.setCurrentText(data.get('indice_correcao_monetaria', 'IPCA-E'))
    apply_widget_style_11(parent_dialog.correcao_combobox)
    correcao_layout.addWidget(correcao_label)
    correcao_layout.addWidget(parent_dialog.correcao_combobox)
    layout.addLayout(correcao_layout)

    # Label and QComboBox for Supply Form
    fornecimento_layout = QHBoxLayout()
    fornecimento_label = QLabel("Forma de fornecimento:")
    apply_widget_style_11(fornecimento_label)
    parent_dialog.fornecimento_combobox = QComboBox()
    parent_dialog.fornecimento_combobox.addItems(["integral", "parcelado", "continuado"])
    parent_dialog.fornecimento_combobox.setCurrentText(data.get('forma_fornecimento', 'integral'))
    apply_widget_style_11(parent_dialog.fornecimento_combobox)
    fornecimento_layout.addWidget(fornecimento_label)
    fornecimento_layout.addWidget(parent_dialog.fornecimento_combobox)
    layout.addLayout(fornecimento_layout)

    # Label and QLineEdit for General Liquidity Indices (LG)
    liquidez_layout = QHBoxLayout()
    liquidez_label = QLabel("Índices de Liquidez Geral (LG):")
    apply_widget_style_11(liquidez_label)
    parent_dialog.liquidez_value = QLineEdit(data.get('indices_liquidez_geral', '10%'))
    apply_widget_style_11(parent_dialog.liquidez_value)
    liquidez_layout.addWidget(liquidez_label)
    liquidez_layout.addWidget(parent_dialog.liquidez_value)
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
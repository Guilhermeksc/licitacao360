from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    apply_widget_style_11, create_button, get_descricao_servico, copyToClipboard, 
                                    get_preposicao_tipo, create_sinopse_text, validate_and_convert_date, create_sigdem_layout)
from diretorios import *
import os

def create_edital_group(data, templatePath):
    # Cria o layout principal
    main_layout = QVBoxLayout()

    # Adiciona a label para o título
    titulo_label = QLabel("Edital")
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
    informacoes_basicas_layout = create_edital_layout(data)
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
    sigdem_menu_widget.setFixedHeight(250)

    main_layout.addWidget(sigdem_menu_widget)

    # Cria um widget para o grupo MR e define o layout
    mr_group_widget = QWidget()
    mr_group_widget.setLayout(main_layout)

    return mr_group_widget

def create_edital_layout(data):
    # Cria um layout vertical principal
    layout = QVBoxLayout()

    # Adiciona os layouts específicos ao layout principal
    layout.addLayout(create_criterio_julgamento_layout())
    layout.addLayout(create_modo_disputa_layout())
    layout.addLayout(create_meepp_layout())
    layout.addLayout(create_minuta_layout())
    layout.addLayout(create_item_grupo_layout())

    return layout

def create_criterio_julgamento_layout():
    criterio_julgamento_layout = QHBoxLayout()
    label_criterio_julgamento = QLabel("Critério de Julgamento")
    apply_widget_style_11(label_criterio_julgamento)
    comboBoxCriterioJulgamento = QComboBox()
    criterios = [
        "Menor preço por item",
        "Menor preço por grupo",
        "Menor preço global",
        "Maior desconto por item",
        "Maior desconto por grupo",
        "Maior desconto global"
    ]
    comboBoxCriterioJulgamento.addItems(criterios)
    comboBoxCriterioJulgamento.setCurrentIndex(0)
    apply_widget_style_11(comboBoxCriterioJulgamento)
    criterio_julgamento_layout.addWidget(label_criterio_julgamento)
    criterio_julgamento_layout.addWidget(comboBoxCriterioJulgamento)
    return criterio_julgamento_layout

def create_modo_disputa_layout():
    modo_disputa_layout = QHBoxLayout()
    label_modo_disputa = QLabel("Modo de Disputa")
    apply_widget_style_11(label_modo_disputa)
    comboBoxModoDisputa = QComboBox()
    modos = [
        "Aberto",
        "Aberto e Fechado",
        "Fechado e Aberto"
    ]
    comboBoxModoDisputa.addItems(modos)
    comboBoxModoDisputa.setCurrentIndex(0)
    apply_widget_style_11(comboBoxModoDisputa)
    modo_disputa_layout.addWidget(label_modo_disputa)
    modo_disputa_layout.addWidget(comboBoxModoDisputa)
    return modo_disputa_layout

def create_meepp_layout():
    meepp_layout = QHBoxLayout()
    label_meepp = QLabel("ME/EPP")
    apply_widget_style_11(label_meepp)
    radioSimMEEPP = QRadioButton("Sim")
    radioNaoMEEPP = QRadioButton("Não")
    radioSimMEEPP.setChecked(True)
    apply_widget_style_11(radioSimMEEPP)
    apply_widget_style_11(radioNaoMEEPP)
    radioGroupMEEPP = QButtonGroup()
    radioGroupMEEPP.addButton(radioSimMEEPP)
    radioGroupMEEPP.addButton(radioNaoMEEPP)
    meepp_layout.addWidget(label_meepp)
    meepp_layout.addWidget(radioSimMEEPP)
    meepp_layout.addWidget(radioNaoMEEPP)
    return meepp_layout

def create_minuta_layout():
    minuta_layout = QHBoxLayout()
    label_minuta = QLabel("Minuta")
    apply_widget_style_11(label_minuta)
    radioSimMinuta = QRadioButton("Sim")
    radioNaoMinuta = QRadioButton("Não")
    radioSimMinuta.setChecked(True)
    apply_widget_style_11(radioSimMinuta)
    apply_widget_style_11(radioNaoMinuta)
    minuta_layout.addWidget(label_minuta)
    minuta_layout.addWidget(radioSimMinuta)
    minuta_layout.addWidget(radioNaoMinuta)
    return minuta_layout

def create_item_grupo_layout():
    item_grupo_layout = QHBoxLayout()
    label_item_grupo = QLabel("Item ou Grupo")
    apply_widget_style_11(label_item_grupo)
    radioItem = QRadioButton("Item")
    radioItemUnico = QRadioButton("Item Único")
    radioGrupo = QRadioButton("Grupo")
    radioGrupoUnico = QRadioButton("Grupo Único")
    radioItem.setChecked(True)
    apply_widget_style_11(radioItem)
    apply_widget_style_11(radioItemUnico)
    apply_widget_style_11(radioGrupo)
    apply_widget_style_11(radioGrupoUnico)
    item_grupo_layout.addWidget(label_item_grupo)
    item_grupo_layout.addWidget(radioItem)
    item_grupo_layout.addWidget(radioItemUnico)
    item_grupo_layout.addWidget(radioGrupo)
    item_grupo_layout.addWidget(radioGrupoUnico)
    return item_grupo_layout

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
            text="  CP Pregoeiro  ",
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

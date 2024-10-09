from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    apply_widget_style_11, create_button, get_descricao_servico, copyToClipboard, 
                                    get_preposicao_tipo, create_sinopse_text, validate_and_convert_date, create_sigdem_layout)
from diretorios import *
import os

def create_matriz_risco_group(data, templatePath):
    # Cria o layout principal
    main_layout = QVBoxLayout()

    # Adiciona a label para o título
    titulo_label = QLabel("Matriz de Riscos (MR)")
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
    informacoes_basicas_layout = create_riscos_layout(data)
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

def create_riscos_layout(data):
    layout = QVBoxLayout()

    # Cria a instância do QTreeView e do modelo de dados
    tree_view = QTreeView()
    model = QStandardItemModel()

    # Aplica o estilo ao QTreeView para aumentar a fonte
    apply_widget_style_11(tree_view)

    # Define o cabeçalho
    model.setHorizontalHeaderLabels(["Fases da Contratação"])

    # Cria os itens pai
    planejamento_item = QStandardItem("Planejamento da Contratação")
    selecao_item = QStandardItem("Seleção do Fornecedor")
    gestao_item = QStandardItem("Gestão Contratual")

    # Adiciona os itens pai ao modelo
    model.appendRow(planejamento_item)
    model.appendRow(selecao_item)
    model.appendRow(gestao_item)

    # Configura o QTreeView
    tree_view.setModel(model)
    tree_view.setHeaderHidden(False)

    # Adiciona o QTreeView ao layout
    layout.addWidget(tree_view)

    # Função para atualizar os valores do QTreeView
    def atualizar_treeview():
        # Aqui você pode definir a lógica para atualizar os itens do QTreeView
        planejamento_item.appendRow(QStandardItem("Novo Risco no Planejamento"))
        selecao_item.appendRow(QStandardItem("Novo Risco na Seleção"))
        gestao_item.appendRow(QStandardItem("Novo Risco na Gestão"))

    # # Botão "Importar Tabela" deve chamar a função atualizar_treeview
    # importar_tabela_button = QPushButton("Importar Tabela")
    # importar_tabela_button.clicked.connect(atualizar_treeview)
    # layout.addWidget(importar_tabela_button)

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
from PyQt6.QtWidgets import * 
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    apply_widget_style_11, create_layout, create_button, add_separator_line, create_sigdem_layout)
from modules.dispensa_eletronica.formulario_excel import FormularioExcel
from diretorios import *
import os
import docx

def create_portaria_layout(data, templatePath):
    # Cria o layout principal
    main_layout = QVBoxLayout()

    # Adiciona a label para o título
    titulo_label = QLabel("Equipe de Planejamento")
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
    informacoes_basicas_layout = create_planejamento_layout(data, templatePath)
    scroll_layout.addWidget(informacoes_basicas_layout)

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
            text="Declaração Ciência",
            icon=icon_table,
            tooltip_text="Gerar texto",
            callback=lambda: print("Gerar Texto clicked"),
            button_size=QSize(200, 50),
            icon_size=QSize(45, 45)
        ),
        create_button(
            text=" Gerar Portaria ",                   
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

def create_planejamento_layout(data, templatePath):
    data = data
    portaria_widget = QWidget()
    apply_widget_style_11(portaria_widget)
    portaria_layout = QVBoxLayout()

    # Nº da Portaria
    numero_portaria_edit = QLineEdit()
    portaria_layout.addLayout(create_layout("Nº da Portaria:", numero_portaria_edit))

    add_separator_line(portaria_layout)

    # Coordenador do Planejamento
    coordenador_layout = QVBoxLayout()
    coordenador_layout.addWidget(QLabel("Coordenador do Planejamento"))
    coordenador_hbox = QHBoxLayout()
    posto_graduacao_edit = QLineEdit()
    nome_edit = QLineEdit()
    nome_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    coordenador_hbox.addWidget(QLabel("Posto/Graduação:"))
    coordenador_hbox.addWidget(posto_graduacao_edit)
    coordenador_hbox.addWidget(QLabel("Nome:"))
    coordenador_hbox.addWidget(nome_edit, 2)
    coordenador_layout.addLayout(coordenador_hbox)

    telefone_email_hbox = QHBoxLayout()
    telefone_edit = QLineEdit()
    email_edit = QLineEdit()
    email_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    telefone_email_hbox.addWidget(QLabel("Telefone:"))
    telefone_email_hbox.addWidget(telefone_edit)
    telefone_email_hbox.addWidget(QLabel("E-mail:"))
    telefone_email_hbox.addWidget(email_edit, 2)
    coordenador_layout.addLayout(telefone_email_hbox)

    portaria_layout.addLayout(coordenador_layout)
    add_separator_line(portaria_layout)

    # Membros da Equipe de Planejamento
    for i in range(2):
        membro_layout = QVBoxLayout()
        membro_layout.addWidget(QLabel(f"Membro da Equipe de Planejamento {i + 1}"))
        membro_hbox = QHBoxLayout()
        posto_graduacao_edit = QLineEdit()
        nome_edit = QLineEdit()
        nome_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        membro_hbox.addWidget(QLabel("Posto/Graduação:"))
        membro_hbox.addWidget(posto_graduacao_edit)
        membro_hbox.addWidget(QLabel("Nome:"))
        membro_hbox.addWidget(nome_edit, 2)
        membro_layout.addLayout(membro_hbox)

        telefone_email_hbox = QHBoxLayout()
        telefone_edit = QLineEdit()
        email_edit = QLineEdit()
        email_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        telefone_email_hbox.addWidget(QLabel("Telefone:"))
        telefone_email_hbox.addWidget(telefone_edit)
        telefone_email_hbox.addWidget(QLabel("E-mail:"))
        telefone_email_hbox.addWidget(email_edit, 2)
        membro_layout.addLayout(telefone_email_hbox)

        portaria_layout.addLayout(membro_layout)
        add_separator_line(portaria_layout)

    # Botão Gerar Portaria
    icon_gerar_portaria = QIcon(str(ICONS_DIR / "pdf.png"))

    gerar_portaria_button = create_button(
        "Gerar Portaria",
        icon=icon_gerar_portaria,
        callback=lambda: on_gerar_portaria_clicked(templatePath),
        tooltip_text="Clique para gerar a portaria",
        button_size=QSize(220, 50),
        icon_size=QSize(45, 45)
    )
    portaria_layout.addWidget(gerar_portaria_button, alignment=Qt.AlignmentFlag.AlignCenter)

    portaria_widget.setLayout(portaria_layout)
    return portaria_widget

def on_gerar_portaria_clicked(templatePath):
    # Abrindo o arquivo template_portaria.docx
    template_file = os.path.join(templatePath, "template_portaria.docx")
    if os.path.exists(template_file):
        doc = docx.Document(template_file)
        # Abrir o documento no editor padrão
        doc.save("gerada_portaria.docx")
        os.startfile("gerada_portaria.docx")
    else:
        print(f"Template não encontrado em {template_file}")

def create_frame_formulario_widget():
    formulario_widget = QWidget()
    apply_widget_style_11(formulario_widget)   
    formulario_widget.setFixedWidth(350)   
    formulario_layout = QVBoxLayout()

    # Adicionando os botões ao layout
    icon_excel_up = QIcon(str(ICONS_DIR / "excel_up.png"))
    icon_excel_down = QIcon(str(ICONS_DIR / "excel_down.png"))

    criar_formulario_button = create_button(
        "   Criar Formulário   ",
        icon=icon_excel_up,
        callback=FormularioExcel.criar_formulario,  # Chama o método do parent
        tooltip_text="Clique para criar o formulário",
        button_size=QSize(220, 50),
        icon_size=QSize(45, 45)
    )

    carregar_formulario_button = create_button(
        "Carregar Formulário",
        icon=icon_excel_down,
        callback=FormularioExcel.carregar_formulario,  # Chama o método do parent
        tooltip_text="Clique para carregar o formulário",
        button_size=QSize(220, 50),
        icon_size=QSize(45, 45)
    )

    formulario_layout.addWidget(criar_formulario_button, alignment=Qt.AlignmentFlag.AlignCenter)
    formulario_layout.addWidget(carregar_formulario_button, alignment=Qt.AlignmentFlag.AlignCenter)
    formulario_widget.setLayout(formulario_layout)

    return formulario_widget

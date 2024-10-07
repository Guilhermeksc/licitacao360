from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    apply_widget_style_11, create_layout, create_button, add_separator_line)
from modules.dispensa_eletronica.formulario_excel import FormularioExcel
from diretorios import *
import os
import docx

def create_planejamento_group(data, templatePath):
    planejamento_group_box = QGroupBox("Planejamento")
    apply_widget_style_11(planejamento_group_box)

    # Criação do layout horizontal principal
    main_layout = QHBoxLayout()

    # Layout da Portaria
    portaria_layout = QVBoxLayout()
    portaria_layout.addWidget(create_portaria_group(templatePath))

    # Layout Planejamento
    planejamento_layout = QVBoxLayout()

    # Classificação Orçamentária
    planejamento_layout.addWidget(create_classificacao_orcamentaria_group(data))

    # Formulário de Dados
    planejamento_layout.addWidget(create_frame_formulario_group())

    # Adicionando os layouts ao layout principal
    main_layout.addLayout(portaria_layout)
    main_layout.addLayout(planejamento_layout)

    planejamento_group_box.setLayout(main_layout)
    return planejamento_group_box

def create_portaria_group(templatePath):
    portaria_group_box = QGroupBox("Portaria")
    apply_widget_style_11(portaria_group_box)
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
    coordenador_hbox.addWidget(nome_edit,2)
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

    portaria_group_box.setLayout(portaria_layout)
    return portaria_group_box

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

def create_classificacao_orcamentaria_group(data):
    classificacao_orcamentaria_group_box = QGroupBox("Classificação Orçamentária")
    apply_widget_style_11(classificacao_orcamentaria_group_box)
    classificacao_orcamentaria_group_box.setFixedWidth(350)  
    classificacao_orcamentaria_layout = QVBoxLayout()

    acao_interna_edit = QLineEdit(data['uasg'])
    fonte_recurso_edit = QLineEdit(data['uasg'])
    natureza_despesa_edit = QLineEdit(data['uasg'])
    unidade_orcamentaria_edit = QLineEdit(data['uasg'])
    ptres_edit = QLineEdit(data['uasg'])

    # Utilizando a função create_layout fora da classe
    classificacao_orcamentaria_layout.addLayout(create_layout("Ação Interna:", acao_interna_edit, apply_style_fn=apply_widget_style_11))
    classificacao_orcamentaria_layout.addLayout(create_layout("Fonte de Recurso (FR):", fonte_recurso_edit, apply_style_fn=apply_widget_style_11))
    classificacao_orcamentaria_layout.addLayout(create_layout("Natureza de Despesa (ND):", natureza_despesa_edit, apply_style_fn=apply_widget_style_11))
    classificacao_orcamentaria_layout.addLayout(create_layout("Unidade Orçamentária (UO):", unidade_orcamentaria_edit, apply_style_fn=apply_widget_style_11))
    classificacao_orcamentaria_layout.addLayout(create_layout("PTRES:", ptres_edit, apply_style_fn=apply_widget_style_11))

    classificacao_orcamentaria_group_box.setLayout(classificacao_orcamentaria_layout)

    return classificacao_orcamentaria_group_box

def create_frame_formulario_group():
    formulario_group_box = QGroupBox("Formulário de Dados")
    apply_widget_style_11(formulario_group_box)   
    formulario_group_box.setFixedWidth(350)   
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
    formulario_group_box.setLayout(formulario_layout)

    return formulario_group_box

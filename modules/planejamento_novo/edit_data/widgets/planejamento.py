from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    apply_widget_style_11, create_layout, create_button, validate_and_convert_date)
from modules.dispensa_eletronica.formulario_excel import FormularioExcel
from diretorios import *
import os

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
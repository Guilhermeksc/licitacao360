from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    apply_widget_style_11, create_layout, create_button, add_separator_line)

def create_frame_pncp(data):
    pncp_group_box = QGroupBox("Consulta ao PNCP")
    apply_widget_style_11(pncp_group_box)

    # Aplicar o background preto ao QGroupBox
    pncp_group_box.setStyleSheet("""
        QGroupBox {
            font-size: 11pt;
        }
        QGroupBox * {
            font-size: 11pt;
        }
    """)
    pncp_layout = QVBoxLayout()
    # Converte os valores para strings (caso estejam como pandas Series)
    numero = str(data.get('numero', ''))
    ano = str(data.get('ano', ''))
    link_pncp = str(data.get('link_pncp', ''))
    uasg = str(data.get('uasg', ''))
    
    # Layout CNPJ Matriz
    cnpj_label = QLabel("CNPJ Matriz:")
    cnpj_label.setStyleSheet("background-color: #202124; color: #8AB4F7; font-size: 16px")
    cnpj_label.setFixedHeight(25)

    cnpj_matriz_edit = QLineEdit('00394502000144')

    # Criação do layout horizontal para "CNPJ Matriz"
    cnpj_layout = QHBoxLayout()
    cnpj_layout.addWidget(cnpj_label)
    cnpj_layout.addWidget(cnpj_matriz_edit)

    # Adiciona o layout de CNPJ ao layout principal
    pncp_layout.addLayout(cnpj_layout)

    # Layout Sequencial PNCP
    link_pncp_label = QLabel("Sequencial PNCP:")
    link_pncp_label.setStyleSheet("background-color: #202124; color: #8AB4F7; font-size: 16px")
    link_pncp_label.setFixedHeight(25)

    link_pncp_edit = QLineEdit(link_pncp)

    # Criação do layout horizontal para "Sequencial PNCP"
    link_pncp_layout = QHBoxLayout()
    link_pncp_layout.addWidget(link_pncp_label)
    link_pncp_layout.addWidget(link_pncp_edit)

    icon_link = QIcon(str(ICONS_DIR / "link.png"))
    link_pncp_button = create_button(
        "",
        icon=icon_link,
        callback=lambda: on_link_pncp_clicked(link_pncp_edit.text(), cnpj_matriz_edit.text(), ano),
        tooltip_text="Clique para acessar o Link da dispensa no Portal Nacional de Contratações Públicas (PNCP)",
        button_size=QSize(30, 30),
        icon_size=QSize(30, 30)
    )
    apply_widget_style_11(link_pncp_button)
    link_pncp_layout.addWidget(link_pncp_button)

    # Adicionando o layout do campo Sequencial PNCP
    pncp_layout.addLayout(link_pncp_layout)

    # Criando botão adicional "Consulta PNCP"
    icon_api = QIcon(str(ICONS_DIR / "api.png"))
    consulta_button = create_button(
        "Consultar PNCP",
        icon=icon_api,
        callback=lambda: on_consultar_pncp(numero, ano),  # Substitua esta função pelo seu callback
        tooltip_text="Consultar o PNCP com os dados fornecidos",
        button_size=QSize(220, 40),
        icon_size=QSize(40, 40)
    )
    apply_widget_style_11(consulta_button)

    # Criando um layout horizontal para centralizar o botão
    button_layout = QHBoxLayout()
    button_layout.addStretch()  # Adiciona espaço elástico à esquerda
    button_layout.addWidget(consulta_button)  # Adiciona o botão ao layout
    button_layout.addStretch()  # Adiciona espaço elástico à direita

    # Adiciona o layout com o botão centralizado ao layout principal
    pncp_layout.addLayout(button_layout)

    # Definindo o nome da tabela utilizando os dados extraídos de `data`
    table_name = f"DE{numero}{ano}{link_pncp}{uasg}"

    pncp_group_box.setLayout(pncp_layout)
    return pncp_group_box

def on_consultar_pncp(numero, ano):
    # Implemente a função de consulta ao PNCP
    pass

def on_link_pncp_clicked(link_pncp, cnpj, ano):
    # Montando a URL
    url = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{link_pncp}"

    # Abrindo o link no navegador padrão
    QDesktopServices.openUrl(QUrl(url))
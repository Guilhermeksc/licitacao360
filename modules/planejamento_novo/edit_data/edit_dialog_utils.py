
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *

class EditDataDialogUtils:
    @staticmethod
    def atualizar_status_label(status_label, icon_label, status_message, icon_path):
        status_label.setText(status_message)

        icon_folder = QIcon(icon_path)
        icon_pixmap = icon_folder.pixmap(30, 30)
        icon_label.setPixmap(icon_pixmap)
        status_label.setStyleSheet("font-size: 14px;")

    @staticmethod
    def update_title_label(df_registro_selecionado):
        data = EditDataDialogUtils.extract_registro_data(df_registro_selecionado)

        html_text = (
            f"{data['tipo']} {data['numero']}/{data['ano']} - {data['objeto']}<br>"
            f"<span style='font-size: 16px'>OM: {data['orgao_responsavel']} (UASG: {data['uasg']})</span>"
        )

        titleLabel = QLabel()
        titleLabel.setTextFormat(Qt.TextFormat.RichText)
        titleLabel.setStyleSheet("font-size: 26px; font-weight: bold;")
        titleLabel.setText(html_text)

        header_layout = QHBoxLayout()
        header_layout.addWidget(titleLabel)  # Adiciona o QLabel ao layout

        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setFixedHeight(80)

        return header_widget

    @staticmethod
    def create_navigation_layout(show_widget_callback, add_action_buttons_callback):
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(0)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        brasil_icon = QIcon(str(BRASIL_IMAGE_PATH))
        image_label_esquerda = QLabel()
        image_label_esquerda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label_esquerda.setPixmap(brasil_icon.pixmap(30, 30))

        nav_layout.addWidget(image_label_esquerda)

        # Lista de botões de navegação
        buttons = [
            ("Informações", "Informações"),
            ("IRP", "IRP"),
            ("Demandante", "Demandante"),
            ("Documentos", "Documentos"),
            ("Anexos", "Anexos"),
            ("PNCP", "PNCP"),
            ("Check-list", "Check-list"),
            ("Nota Técnica", "Nota Técnica"),
        ]

        button_style = EditDataDialogUtils.get_button_style()

        for text, name in buttons:
            button = QPushButton(text)
            button.clicked.connect(lambda _, n=name: show_widget_callback(n))
            button.setStyleSheet(button_style)  # Aplica o estilo ao botão
            nav_layout.addWidget(button)

        nav_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Adiciona os botões de ação, como o botão "Salvar"
        add_action_buttons_callback(nav_layout)

        nav_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        return nav_layout

    @staticmethod
    def get_button_style():
        return (
            "QPushButton {"
            "border: 1px solid #414242; background: #B0B0B0; color: black; font-weight: bold; font-size: 12pt;"
            "border-top-left-radius: 5px; border-top-right-radius: 5px; "
            "border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; "
            "border-bottom-color: #414242; }"
            "QPushButton:hover { background: #D0D0D0; font-weight: bold; color: black; }"
        )
    
    @staticmethod
    def extract_registro_data(df_registro_selecionado):
        if df_registro_selecionado.empty:
            print("DataFrame está vazio")
            return {}

        # Extrai dados do DataFrame e retorna um dicionário
        data = {
            'id_processo': df_registro_selecionado['id_processo'].iloc[0],
            'tipo': df_registro_selecionado['tipo'].iloc[0],
            'numero': df_registro_selecionado['numero'].iloc[0],
            'ano': df_registro_selecionado['ano'].iloc[0],
            'status': df_registro_selecionado['status'].iloc[0],
            'nup': df_registro_selecionado['nup'].iloc[0],
            'material_servico': df_registro_selecionado['material_servico'].iloc[0],
            'objeto': df_registro_selecionado['objeto'].iloc[0],
            'vigencia': df_registro_selecionado['vigencia'].iloc[0],
            'data_sessao': df_registro_selecionado['data_sessao'].iloc[0],
            'operador': df_registro_selecionado['operador'].iloc[0],
            'criterio_julgamento': df_registro_selecionado['criterio_julgamento'].iloc[0],
            'com_disputa': df_registro_selecionado['com_disputa'].iloc[0],
            'pesquisa_preco': df_registro_selecionado['pesquisa_preco'].iloc[0],
            'previsao_contratacao': df_registro_selecionado['previsao_contratacao'].iloc[0],
            'uasg': df_registro_selecionado['uasg'].iloc[0],
            'orgao_responsavel': df_registro_selecionado['orgao_responsavel'].iloc[0],
            'sigla_om': df_registro_selecionado['sigla_om'].iloc[0],
            'uf': df_registro_selecionado['uf'].iloc[0] if 'uf' in df_registro_selecionado.columns else None,
            'codigoMunicipioIbge': df_registro_selecionado['codigoMunicipioIbge'].iloc[0] if 'codigoMunicipioIbge' in df_registro_selecionado.columns else None,
            'setor_responsavel': df_registro_selecionado['setor_responsavel'].iloc[0],
            'responsavel_pela_demanda': df_registro_selecionado['responsavel_pela_demanda'].iloc[0],
            'ordenador_despesas': df_registro_selecionado['ordenador_despesas'].iloc[0],
            'agente_fiscal': df_registro_selecionado['agente_fiscal'].iloc[0],
            'gerente_de_credito': df_registro_selecionado['gerente_de_credito'].iloc[0],
            'cod_par': df_registro_selecionado['cod_par'].iloc[0],
            'prioridade_par': df_registro_selecionado['prioridade_par'].iloc[0],
            'cep': df_registro_selecionado['cep'].iloc[0],
            'endereco': df_registro_selecionado['endereco'].iloc[0],
            'email': df_registro_selecionado['email'].iloc[0],
            'telefone': df_registro_selecionado['telefone'].iloc[0],
            'dias_para_recebimento': df_registro_selecionado['dias_para_recebimento'].iloc[0],
            'horario_para_recebimento': df_registro_selecionado['horario_para_recebimento'].iloc[0],
            'valor_total': df_registro_selecionado['valor_total'].iloc[0],
            'acao_interna': df_registro_selecionado['acao_interna'].iloc[0],
            'fonte_recursos': df_registro_selecionado['fonte_recursos'].iloc[0],
            'natureza_despesa': df_registro_selecionado['natureza_despesa'].iloc[0],
            'unidade_orcamentaria': df_registro_selecionado['unidade_orcamentaria'].iloc[0],
            'programa_trabalho_resuminho': df_registro_selecionado['programa_trabalho_resuminho'].iloc[0],
            'atividade_custeio': df_registro_selecionado['atividade_custeio'].iloc[0],
            'comentarios': df_registro_selecionado['comentarios'].iloc[0],
            'justificativa': df_registro_selecionado['justificativa'].iloc[0],
            'link_pncp': df_registro_selecionado['link_pncp'].iloc[0],
        }

        return data

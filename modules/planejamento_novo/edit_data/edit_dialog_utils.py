
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
from datetime import datetime

def apply_widget_style_11(widget):
    widget.setStyleSheet("font-size: 11pt;") 

def create_button(text="", icon=None, callback=None, tooltip_text="", button_size=None, icon_size=None):
    btn = QPushButton(text)
    if icon:
        btn.setIcon(icon)
        btn.setIconSize(icon_size if icon_size else QSize(40, 40))
    if button_size:
        btn.setFixedSize(button_size)
    btn.setToolTip(tooltip_text)
    if callback:
        btn.clicked.connect(callback)  # Conecta o callback ao evento de clique
    return btn

def create_layout(label_text, widget, fixed_width=None, apply_style_fn=None):
    layout = QHBoxLayout()
    label = QLabel(label_text)
    
    # Aplica o estilo ao label, se uma função de estilo for fornecida
    if apply_style_fn:
        apply_style_fn(label)
    
    # Adiciona a largura fixa se especificada
    if fixed_width and isinstance(widget, QWidget):
        widget.setFixedWidth(fixed_width)
    
    # Aplica estilo apenas se o widget for uma instância de QWidget e a função de estilo foi passada
    if isinstance(widget, QWidget) and apply_style_fn:
        apply_style_fn(widget)
    
    layout.addWidget(label)
    layout.addWidget(widget)
    return layout


def validate_and_convert_date(date_str):
    """Valida e converte uma string de data para QDate."""
    try:
        # Tenta converter a string para datetime
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        # Converte datetime para QDate
        return QDate(parsed_date.year, parsed_date.month, parsed_date.day)
    except (ValueError, TypeError):
        # Retorna None se houver erro na conversão
        return None
    
def create_combo_box(current_text, items, fixed_width, fixed_height, style_fn=None):
    combo_box = QComboBox()
    combo_box.addItems(items)
    combo_box.setFixedWidth(fixed_width)
    combo_box.setFixedHeight(fixed_height)  # Define a altura fixa do ComboBox
    combo_box.setStyleSheet("QComboBox { font-size: 12px; }")  # Ajusta o estilo para melhor visualização
    if style_fn:
        style_fn(combo_box)  # Aplica o estilo se uma função de estilo for passada
    combo_box.setCurrentText(current_text)
    return combo_box

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
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titleLabel.setStyleSheet("font-size: 26px; font-weight: bold;")
        titleLabel.setText(html_text)

        header_layout = QHBoxLayout()
        header_layout.addWidget(titleLabel)

        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setFixedHeight(80)

        return header_widget, titleLabel


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

class RealLineEdit(QLineEdit):
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setText(self.format_to_real(self.text()))

    def focusInEvent(self, event):
        # Remove the currency formatting when the user focuses on the widget
        self.setText(self.format_to_plain_number(self.text()))
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        # Add the currency formatting when the user leaves the widget
        self.setText(self.format_to_real(self.text()))
        super().focusOutEvent(event)
    
    def format_to_real(self, value):
        try:
            # Convert the plain number to real currency format
            value = float(value.replace('.', '').replace(',', '.').strip())
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except ValueError:
            return value
    
    def format_to_plain_number(self, value):
        try:
            # Convert the real currency format to plain number
            value = float(value.replace('R$', '').replace('.', '').replace(',', '.').strip())
            return f"{value:.2f}".replace('.', ',')
        except ValueError:
            return value
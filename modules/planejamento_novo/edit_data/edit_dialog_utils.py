
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
from datetime import datetime
import pandas as pd

def create_sigdem_layout(data, titulo):
    grupoSIGDEM = QGroupBox("SIGDEM")
    apply_widget_style_11(grupoSIGDEM)
    layout = QVBoxLayout(grupoSIGDEM)

    # Campo Assunto
    labelAssunto = QLabel("No campo “Assunto”:")
    labelAssunto.setStyleSheet("color: #8AB4F7; font-size: 16px")
    layout.addWidget(labelAssunto)
    edital_text = f"{data.get('id_processo', '')} - {titulo} ({data.get('objeto', '')})"
    textEditAssunto = QTextEdit(edital_text)
    textEditAssunto.setStyleSheet("font-size: 12pt;")
    textEditAssunto.setMaximumHeight(60)
    layoutHAssunto = QHBoxLayout()
    layoutHAssunto.addWidget(textEditAssunto)
    icon_copy = QIcon(str(ICONS_DIR / "copy_1.png"))
    btnCopyAssunto = create_button(text="", icon=icon_copy, callback=lambda: copyToClipboard(textEditAssunto.toPlainText()), tooltip_text="Copiar texto para a área de transferência", button_size=QSize(40, 40), icon_size=QSize(25, 25))
    layoutHAssunto.addWidget(btnCopyAssunto)
    layout.addLayout(layoutHAssunto)

    # Campo Sinopse
    labelSinopse = QLabel("No campo “Sinopse”:")
    labelSinopse.setStyleSheet("color: #8AB4F7; font-size: 16px")
    layout.addWidget(labelSinopse)
    textEditSinopse = QTextEdit()
    textEditSinopse.setPlainText(create_sinopse_text(data, titulo))
    textEditSinopse.setStyleSheet("font-size: 12pt;")
    textEditSinopse.setMaximumHeight(140)
    layoutHSinopse = QHBoxLayout()
    layoutHSinopse.addWidget(textEditSinopse)
    btnCopySinopse = create_button(text="", icon=icon_copy, callback=lambda: copyToClipboard(textEditSinopse.toPlainText()), tooltip_text="Copiar texto para a área de transferência", button_size=QSize(40, 40), icon_size=QSize(25, 25))
    layoutHSinopse.addWidget(btnCopySinopse)
    layout.addLayout(layoutHSinopse)

    grupoSIGDEM.setLayout(layout)

    return grupoSIGDEM

def get_descricao_servico(data):
    return "aquisição de" if data.get('material_servico', '') == "Material" else "contratação de empresa especializada em"

def copyToClipboard(text):
    clipboard = QApplication.clipboard()
    clipboard.setText(text)

def get_preposicao_tipo(tipo):
    if tipo == "CC":
        return "à Concorrência (CC)"
    elif tipo == "PE":
        return "ao Pregão Eletrônico (PE)"
    elif tipo == "TJDL":
        return "ao  Termo de Justificativa para Dispensa de Licitação (TJDL)"
    elif tipo == "TJIL":
        return "ao  Termo de Justificativa para Inexibilidade de Licitação (TJIL)"
    elif tipo == "DE":
        return f"à {tipo}"
    else:
        return f"ao {tipo}"

def create_sinopse_text(data, titulo):
    tipo = data.get('tipo', '')
    preposicao_tipo = get_preposicao_tipo(tipo)
    return (
        f"{titulo} referente {preposicao_tipo} nº {data.get('numero', '')}/{data.get('ano', '')}, para {get_descricao_servico(data)} {data.get('objeto', '')}\n"
        f"Processo Administrativo NUP: {data.get('nup', '')}\n"
        f"Setor Demandante: {data.get('setor_responsavel', '')}"
    )

def add_separator_line(layout):
    """Adiciona um QFrame horizontal como linha separadora ao layout especificado."""
    separator_line = QFrame()
    separator_line.setFrameShape(QFrame.Shape.HLine)
    separator_line.setFrameShadow(QFrame.Shadow.Sunken)
    layout.addWidget(separator_line)

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
            ("Documentos", "Documentos"),
            ("Portaria", "Portaria"),
            ("IRP", "IRP"),
            ("DFD", "DFD"),
            ("ETP", "ETP"),
            ("MR", "MR"),
            ("TR", "TR"),
            ("Edital", "Edital"),
            ("Check-list", "Check-list"),
            ("Nota Técnica", "Nota Técnica"),
            ("AGU", "AGU"),
            ("PNCP", "PNCP"),
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
        
        # Helper function to safely get values from the DataFrame
        def get_value(df, column_name, default=None):
            try:
                value = df[column_name].iloc[0]
                if pd.isnull(value):
                    return default
                return value
            except (KeyError, IndexError):
                return default

        # Function to convert values to booleans
        def int_to_bool(value):
            return bool(value) if pd.notnull(value) else False

        # Build the data dictionary
        data = {
            'id_processo': get_value(df_registro_selecionado, 'id_processo'),
            'tipo': get_value(df_registro_selecionado, 'tipo'),
            'numero': get_value(df_registro_selecionado, 'numero'),
            'ano': get_value(df_registro_selecionado, 'ano'),
            'etapa': get_value(df_registro_selecionado, 'etapa'),
            'nup': get_value(df_registro_selecionado, 'nup'),
            'material_servico': get_value(df_registro_selecionado, 'material_servico'),
            'criterio_julgamento': get_value(df_registro_selecionado, 'criterio_julgamento'),
            'tipo_licitacao': get_value(df_registro_selecionado, 'tipo_licitacao'),
            'vigencia': get_value(df_registro_selecionado, 'vigencia'),
            'objeto': get_value(df_registro_selecionado, 'objeto'),
            'objeto_completo': get_value(df_registro_selecionado, 'objeto_completo', ''),
            'parecer_agu': get_value(df_registro_selecionado, 'parecer_agu'),
            'data_sessao': get_value(df_registro_selecionado, 'data_sessao'),
            'uasg': get_value(df_registro_selecionado, 'uasg'),
            'orgao_responsavel': get_value(df_registro_selecionado, 'orgao_responsavel'),
            'sigla_om': get_value(df_registro_selecionado, 'sigla_om'),
            'setor_responsavel': get_value(df_registro_selecionado, 'setor_responsavel'),
            'valor_total': get_value(df_registro_selecionado, 'valor_total'),
            'gerente_de_credito': get_value(df_registro_selecionado, 'gerente_de_credito'),
            'responsavel_pela_demanda': get_value(df_registro_selecionado, 'responsavel_pela_demanda'),
            'ordenador_despesas': get_value(df_registro_selecionado, 'ordenador_despesas'),
            'agente_fiscal': get_value(df_registro_selecionado, 'agente_fiscal'),
            'cod_par': get_value(df_registro_selecionado, 'cod_par'),
            'prioridade_par': get_value(df_registro_selecionado, 'prioridade_par'),
            'cep': get_value(df_registro_selecionado, 'cep'),
            'endereco': get_value(df_registro_selecionado, 'endereco'),
            'email': get_value(df_registro_selecionado, 'email'),
            'telefone': get_value(df_registro_selecionado, 'telefone'),
            'dias_para_recebimento': get_value(df_registro_selecionado, 'dias_para_recebimento'),
            'horario_para_recebimento': get_value(df_registro_selecionado, 'horario_para_recebimento'),
            'acao_interna': get_value(df_registro_selecionado, 'acao_interna'),
            'natureza_despesa': get_value(df_registro_selecionado, 'natureza_despesa'),
            'unidade_orcamentaria': get_value(df_registro_selecionado, 'unidade_orcamentaria'),
            'ptres': get_value(df_registro_selecionado, 'ptres'),
            'comentarios': get_value(df_registro_selecionado, 'comentarios'),
            'justificativa': get_value(df_registro_selecionado, 'justificativa'),
            'link_pncp': get_value(df_registro_selecionado, 'link_pncp'),
            'prioritario': int_to_bool(df_registro_selecionado['prioritario'].iloc[0]),
            'emenda_parlamentar': int_to_bool(df_registro_selecionado['emenda_parlamentar'].iloc[0]),
            'srp': int_to_bool(df_registro_selecionado['srp'].iloc[0]),
            'atividade_custeio': int_to_bool(df_registro_selecionado['atividade_custeio'].iloc[0]),
            'processo_parametrizado': int_to_bool(df_registro_selecionado['processo_parametrizado'].iloc[0]),

            # IRP
            'msg_irp': get_value(df_registro_selecionado, 'msg_irp'),
            'data_limite_manifestacao_irp': get_value(df_registro_selecionado, 'data_limite_manifestacao_irp'),
            'data_limite_confirmacao_irp': get_value(df_registro_selecionado, 'data_limite_confirmacao_irp'),
            'num_irp': get_value(df_registro_selecionado, 'num_irp'),           
        
        }

        return data


def to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('sim', 'true', 'yes', '1')
    return False

class TextEditDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QTextEdit(parent)
        editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        editor.setText(text)  # Apenas define o texto completo no editor

    def setModelData(self, editor, model, index):
        edited_text = editor.toPlainText().strip()
        model.setData(index, edited_text, Qt.ItemDataRole.DisplayRole)  # Define apenas o texto editado no modelo

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

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
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    apply_widget_style_11, validate_and_convert_date)
from diretorios import *
import os

def create_irp_group(data, templatePath, parent_dialog):
    irp_group_box = QGroupBox("Intenção de Registro de Preços (IRP)")
    apply_widget_style_11(irp_group_box)

    # Main layout
    main_layout = QHBoxLayout()

    # Left section
    irp_left_group_box = create_left_section(data, parent_dialog)
    main_layout.addWidget(irp_left_group_box)

    # Right section
    right_section_layout = create_right_section(data, templatePath)
    main_layout.addLayout(right_section_layout)

    irp_group_box.setLayout(main_layout)
    return irp_group_box


def create_left_section(data, parent_dialog):
    irp_left_group_box = QGroupBox("Dados")
    irp_left_group_layout = QVBoxLayout()
    irp_left_group_box.setMaximumWidth(300)

    # Dictionaries to collect widgets
    line_edits = {}
    date_edits = {}

    # Text layout
    irp_text_layout = create_irp_text_layout(data, line_edits, parent_dialog)
    irp_left_group_layout.addLayout(irp_text_layout)

    # Date layout
    irp_date_layout = create_irp_date_layout(data, date_edits, parent_dialog)
    irp_left_group_layout.addLayout(irp_date_layout)

    irp_left_group_box.setLayout(irp_left_group_layout)
    return irp_left_group_box


def create_right_section(data, templatePath):
    right_section_layout = QVBoxLayout()

    # Layout da direita (textViewerGroupBox)
    text_viewer_group_box = create_text_viewer_group_box(templatePath)
    right_section_layout.addWidget(text_viewer_group_box)

    # Adicionar botões abaixo do textViewerGroupBox
    buttons_layout = create_buttons_layout(data)
    right_section_layout.addLayout(buttons_layout)

    return right_section_layout

def create_irp_text_layout(data, line_edits, parent_dialog):
    irp_text_layout = QVBoxLayout()

    # MSG IRP
    msg_irp_layout = QHBoxLayout()
    label_msg_irp = QLabel("Data/Hora MSG:")
    line_edit_msg_irp = QLineEdit()
    line_edit_msg_irp.setText(data.get('msg_irp', ''))
    msg_irp_layout.addWidget(label_msg_irp)
    msg_irp_layout.addWidget(line_edit_msg_irp)
    irp_text_layout.addLayout(msg_irp_layout)
    line_edits['msg_irp'] = line_edit_msg_irp

    # Set as attributes
    parent_dialog.label_msg_irp = label_msg_irp
    parent_dialog.line_edit_msg_irp = line_edit_msg_irp

    # Número IRP
    num_irp_layout = QHBoxLayout()
    label_num_irp = QLabel("Número IRP:")
    line_edit_num_irp = QLineEdit()
    line_edit_num_irp.setText(data.get('num_irp', ''))
    num_irp_layout.addWidget(label_num_irp)
    num_irp_layout.addWidget(line_edit_num_irp)
    irp_text_layout.addLayout(num_irp_layout)
    line_edits['num_irp'] = line_edit_num_irp

    # Set as attributes
    parent_dialog.label_num_irp = label_num_irp
    parent_dialog.line_edit_num_irp = line_edit_num_irp

    return irp_text_layout


def create_irp_date_layout(data, date_edits, parent_dialog):
    irp_date_layout = QVBoxLayout()

    # Date fields with QCalendarWidget
    date_fields = {
        'data_limite_manifestacao_irp': "Limite para Manifestação",
        'data_limite_confirmacao_irp': "Limite para Confirmação"
    }

    for field, label_text in date_fields.items():
        date_layout = QVBoxLayout()
        label = QLabel(label_text + ':')
        calendar_widget = QCalendarWidget()
        date_str = data.get(field)
        valid_date = validate_and_convert_date(date_str)
        if valid_date:
            calendar_widget.setSelectedDate(valid_date)
        else:
            calendar_widget.setSelectedDate(QDate.currentDate())
        date_layout.addWidget(label)
        date_layout.addWidget(calendar_widget)
        irp_date_layout.addLayout(date_layout)
        date_edits[field] = calendar_widget

        # Set as attributes
        if field == 'data_limite_manifestacao_irp':
            parent_dialog.label_data_limite_manifestacao_irp = label
            parent_dialog.calendar_data_limite_manifestacao_irp = calendar_widget
        elif field == 'data_limite_confirmacao_irp':
            parent_dialog.label_data_limite_confirmacao_irp = label
            parent_dialog.calendar_data_limite_confirmacao_irp = calendar_widget

    return irp_date_layout


def create_variable_list_group_box(data):
    variableListGroupBox = QGroupBox("Índice de Variáveis")
    variableListLayout = QVBoxLayout()
    variableList = QListWidget()
    variableList.addItems(sorted(f"{{{{{key}}}}}" for key in data.keys()))
    variableList.setMaximumWidth(300)  # Limita o tamanho do QListWidget

    variableListLayout.addWidget(variableList)
    variableListGroupBox.setLayout(variableListLayout)
    variableListGroupBox.setMaximumWidth(300)  # Limita o tamanho do QGroupBox

    return variableListGroupBox

def create_model_editor_group_box():
    modelEditorGroupBox = QGroupBox("Campo para Edição do Modelo")
    modelEditorLayout = QVBoxLayout()
    modelEditor = QTextEdit()
    modelEditorLayout.addWidget(modelEditor)
    modelEditorGroupBox.setLayout(modelEditorLayout)
    return modelEditorGroupBox

def create_text_viewer_group_box(templatePath):
    """
    Cria um QGroupBox para visualização da mensagem baseada no último template carregado.
    """
    textViewerGroupBox = QGroupBox("Campo para Visualização da Mensagem")
    textViewerLayout = QVBoxLayout()

    # Criar QTextEdit para visualização do texto
    textViewer = QTextEdit()
    textViewer.setReadOnly(True)
    textViewerLayout.addWidget(textViewer)

    # Carregar o último template salvo
    loadLastTemplate(templatePath, textViewer)

    # Configurar o layout do QGroupBox
    textViewerGroupBox.setLayout(textViewerLayout)
    return textViewerGroupBox

def loadLastTemplate(templatePath, textViewer):
    try:
        if os.path.exists(templatePath):
            with open(templatePath, 'r', encoding='utf-8') as file:
                last_template = file.read()
            textViewer.setPlainText(last_template)
        else:
            textViewer.setPlainText("Digite o texto da mensagem aqui...")
    except Exception as e:
        QMessageBox.warning(None, "Erro ao carregar template", str(e))

def create_buttons_layout(data):
    buttons_layout = QHBoxLayout()
    icon_size = QSize(40, 40)  # Tamanho do ícone para todos os botões
    button_specs = [
        ("Copiar Mensagem", "copy.png", "Copia a mensagem para a área de transferência"),
        ("Editar MSG", "edit.png", "Editar a mensagem"),
        ("Manifestação IRP", "edit.png", "Editar a mensagem"),     
        ("Lançamento Comprasnet", "edit.png", "Editar a mensagem"),       
    ]

    for text, icon_name, tooltip in button_specs:
        icon = QIcon(icon_name)  # Ajuste de acordo com o caminho dos ícones
        btn = QPushButton(text)
        btn.setIcon(icon)
        btn.setIconSize(icon_size)
        btn.setToolTip(tooltip)
        buttons_layout.addWidget(btn)

        if text == "Editar MSG":
            btn.clicked.connect(lambda: open_edit_msg_dialog(data))

    return buttons_layout

def open_edit_msg_dialog(data):
    dialog = QDialog()
    dialog.setWindowTitle("Editar MSG")
    dialog_layout = QHBoxLayout()

    variable_list_group_box = create_variable_list_group_box(data)
    model_editor_group_box = create_model_editor_group_box()

    dialog_layout.addWidget(variable_list_group_box)
    dialog_layout.addWidget(model_editor_group_box)

    dialog.setLayout(dialog_layout)
    dialog.setMinimumSize(600, 400)
    dialog.exec()
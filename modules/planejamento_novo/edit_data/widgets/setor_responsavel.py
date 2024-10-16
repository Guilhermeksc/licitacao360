from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    apply_widget_style_11, create_button, create_layout, create_combo_box, get_descricao_servico, copyToClipboard, 
                                    get_preposicao_tipo, create_sinopse_text, validate_and_convert_date, create_sigdem_layout)
from diretorios import *
import os
import sqlite3
import logging


def create_dados_responsavel_contratacao_group(data, parent_dialog):
    setor_responsavel_group_box = QGroupBox("Divisão/Setor Responsável pela Demanda")
    apply_widget_style_11(setor_responsavel_group_box)
    setor_responsavel_layout = QVBoxLayout()

    # Layout OM e Divisão
    om_divisao_layout = create_om_divisao_layout(data, parent_dialog)
    setor_responsavel_layout.addLayout(om_divisao_layout)

    # Carrega sigla_om
    load_sigla_om(parent_dialog)

    # Layout PAR
    par_layout = create_par_layout(data, parent_dialog)
    setor_responsavel_layout.addLayout(par_layout)

    # Layout Endereço
    endereco_cep_layout = create_endereco_layout(data, parent_dialog)
    setor_responsavel_layout.addLayout(endereco_cep_layout)

    # Layout Contato
    email_telefone_layout = create_contato_layout(data, parent_dialog)
    setor_responsavel_layout.addLayout(email_telefone_layout)

    # Outros campos
    parent_dialog.dias_edit = QLineEdit("Segunda à Sexta")
    setor_responsavel_layout.addLayout(create_layout("Dias para Recebimento:", parent_dialog.dias_edit))

    parent_dialog.horario_edit = QLineEdit("09 às 11h20 e 14 às 16h30")
    setor_responsavel_layout.addLayout(create_layout("Horário para Recebimento:", parent_dialog.horario_edit))

    # Adicionando Justificativa
    justificativa_label = QLabel("Justificativa para a contratação:")
    justificativa_label.setStyleSheet("font-size: 12pt;")
    parent_dialog.justificativa_edit = QTextEdit(get_justification_text(parent_dialog, data))
    apply_widget_style_11(parent_dialog.justificativa_edit)
    setor_responsavel_layout.addWidget(justificativa_label)
    setor_responsavel_layout.addWidget(parent_dialog.justificativa_edit)

    setor_responsavel_group_box.setLayout(setor_responsavel_layout)
    return setor_responsavel_group_box

def load_sigla_om(parent_dialog):
    sigla_om = parent_dialog.sigla_om  # Use the instance variable
    try:
        with sqlite3.connect(parent_dialog.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT sigla_om FROM controle_om ORDER BY sigla_om")
            items = [row[0] for row in cursor.fetchall()]
            parent_dialog.om_combo.addItems(items)
            parent_dialog.om_combo.setCurrentText(sigla_om)
            parent_dialog.om_combo.currentTextChanged.connect(parent_dialog.on_om_changed)
    except Exception as e:
        QMessageBox.warning(parent_dialog, "Erro", f"Erro ao carregar OM: {e}")

def get_justification_text(parent_dialog, data):
    # Try to retrieve the current justification from the DataFrame
    try:
        current_justification = parent_dialog.df_registro_selecionado['justificativa'].iloc[0]
    except KeyError:
        logging.error("A coluna 'justificativa' não foi encontrada no DataFrame.")
        return generate_default_justification(parent_dialog, data)
    except IndexError:
        logging.warning("O DataFrame 'df_registro_selecionado' está vazio. Retornando justificativa padrão.")
        return generate_default_justification(parent_dialog, data)

    # Return the current justification if it exists; otherwise, build one based on material/service type
    if current_justification:
        return current_justification
    else:
        return generate_default_justification(parent_dialog, data)

def generate_default_justification(parent_dialog, data):
    material_servico = data.get('material_servico', '')
    objeto = data.get('objeto', '')
    setor_responsavel = parent_dialog.setor_responsavel_combo.currentText() if parent_dialog.setor_responsavel_combo else ''
    sigla_om = parent_dialog.sigla_om if parent_dialog.sigla_om else ''
    orgao_responsavel = data.get('orgao_responsavel', '')
    # Generate default justification based on material or service type
    if material_servico == 'Material':
        return (f"A aquisição de {objeto} se faz necessária para o atendimento das necessidades do(a) {setor_responsavel} do(a) {orgao_responsavel} ({sigla_om}). A disponibilidade e a qualidade dos materiais são essenciais para garantir a continuidade das operações e a eficiência das atividades desempenhadas pelo(a) {setor_responsavel}.")
    elif material_servico == 'Serviço':
        return (f"A contratação de empresa especializada na prestação de serviços de {objeto} é imprescindível para o atendimento das necessidades do(a) {setor_responsavel} do(a) {orgao_responsavel} ({sigla_om}).")
    return ""  # Return an empty string if none of the conditions above are met

def create_om_divisao_layout(data, parent_dialog):
    om_divisao_layout = QHBoxLayout()

    # Configuração da OM
    om_layout = QHBoxLayout()
    om_label = QLabel("OM:")
    apply_widget_style_11(om_label)

    parent_dialog.sigla_om = data.get('sigla_om', 'CeIMBra')
    if parent_dialog.df_registro_selecionado is not None and 'sigla_om' in parent_dialog.df_registro_selecionado.columns:
        if not parent_dialog.df_registro_selecionado['sigla_om'].empty:
            parent_dialog.sigla_om = parent_dialog.df_registro_selecionado['sigla_om'].iloc[0]
        else:
            parent_dialog.sigla_om = 'CeIMBra'

    parent_dialog.om_combo = create_combo_box(parent_dialog.sigla_om, [], 150, 35)
    om_layout.addWidget(om_label)
    om_layout.addWidget(parent_dialog.om_combo)

    # Adicionando o layout OM ao layout principal
    om_divisao_layout.addLayout(om_layout)

    # Configuração da Divisão
    divisao_label = QLabel("Divisão:")
    apply_widget_style_11(divisao_label)

    parent_dialog.setor_responsavel_combo = QComboBox()
    parent_dialog.setor_responsavel_combo.setEditable(True)

    # Adicionando as opções ao ComboBox
    divisoes = [
        "Divisão de Abastecimento",
        "Divisão de Finanças",
        "Divisão de Obtenção",
        "Divisão de Pagamento",
        "Divisão de Administração",
        "Divisão de Subsistência"
    ]
    parent_dialog.setor_responsavel_combo.addItems(divisoes)

    parent_dialog.setor_responsavel_combo.setCurrentText(data.get('setor_responsavel', ''))
    parent_dialog.setor_responsavel_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    om_divisao_layout.addWidget(divisao_label)
    om_divisao_layout.addWidget(parent_dialog.setor_responsavel_combo)

    return om_divisao_layout

def create_par_layout(data, parent_dialog):
    parent_dialog.par_edit = QLineEdit(str(data.get('cod_par', '')))
    parent_dialog.par_edit.setFixedWidth(150)
    parent_dialog.prioridade_combo = create_combo_box(
        data.get('prioridade_par', 'Necessário'),
        ["Necessário", "Urgente", "Desejável"],
        190, 35
    )

    par_layout = QHBoxLayout()

    par_label = QLabel("Meta do PAR:")
    prioridade_label = QLabel("Prioridade:")
    apply_widget_style_11(par_label)
    apply_widget_style_11(prioridade_label)

    par_layout.addWidget(par_label)
    par_layout.addWidget(parent_dialog.par_edit)
    par_layout.addWidget(prioridade_label)
    par_layout.addWidget(parent_dialog.prioridade_combo)

    return par_layout

def create_endereco_layout(data, parent_dialog):
    parent_dialog.endereco_edit = QLineEdit(data.get('endereco', ''))
    parent_dialog.endereco_edit.setFixedWidth(450)
    parent_dialog.cep_edit = QLineEdit(str(data.get('cep', '')))

    endereco_cep_layout = QHBoxLayout()
    endereco_label = QLabel("Endereço:")
    cep_label = QLabel("CEP:")
    apply_widget_style_11(endereco_label)
    apply_widget_style_11(cep_label)

    endereco_cep_layout.addWidget(endereco_label)
    endereco_cep_layout.addWidget(parent_dialog.endereco_edit)
    endereco_cep_layout.addWidget(cep_label)
    endereco_cep_layout.addWidget(parent_dialog.cep_edit)

    return endereco_cep_layout

def create_contato_layout(data, parent_dialog):
    parent_dialog.email_edit = QLineEdit(data.get('email', ''))
    parent_dialog.email_edit.setFixedWidth(400)
    parent_dialog.telefone_edit = QLineEdit(data.get('telefone', ''))

    email_telefone_layout = QHBoxLayout()
    email_telefone_layout.addLayout(create_layout("E-mail:", parent_dialog.email_edit))
    email_telefone_layout.addLayout(create_layout("Tel:", parent_dialog.telefone_edit))

    return email_telefone_layout


def create_menu_layout(templatePath):
    menu_group_box = QGroupBox("Menu")
    apply_widget_style_11(menu_group_box)
    menu_group_box.setFixedWidth(230)
    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    layout.setSpacing(10)

    icon_context = QIcon(str(ICONS_DIR / "context.png"))
    icon_text = QIcon(str(ICONS_DIR / "will.png"))
    icon_gerar_documento = QIcon(str(ICONS_DIR / "contract.png"))

    buttons = [
        create_button(
            text="Inserir Contexto", 
            icon=icon_context,
            tooltip_text="Inserir contexto",
            callback=lambda: print("Inserir Contexto clicked"),
            button_size=QSize(200, 50),
            icon_size=QSize(45, 45)
        ),
        create_button(
            text="     Gerar Texto   ",
            icon=icon_text,
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
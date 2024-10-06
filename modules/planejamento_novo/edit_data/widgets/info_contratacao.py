from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    EditDataDialogUtils, RealLineEdit, TextEditDelegate,
                                    create_combo_box, create_layout, create_button, 
                                    apply_widget_style_11, validate_and_convert_date)
from diretorios import *
from modules.planejamento.utilidades_planejamento import DatabaseManager

def create_contratacao_group(data, database_manager):
    contratacao_group_box = QGroupBox("Contratação")
    apply_widget_style_11(contratacao_group_box)
    contratacao_layout = QVBoxLayout()

    # Objeto e NUP
    contratacao_layout.addLayout(create_objeto_nup_layout(data))

    # Objeto Completo
    contratacao_layout.addLayout(create_objeto_completo_layout(data))

    add_separator_line(contratacao_layout)

    # Cria o layout horizontal para agrupar Material/Critério/Tipo e Data/Previsão
    material_previsao_layout = QHBoxLayout()
    # Material/Serviço e Critério de Julgamento
    material_previsao_layout.addLayout(create_material_criterio_tipo_layout(data))
    # Checkbox layouts e adição ao group box
    material_previsao_layout.addLayout(create_checkboxes(data))
    # Data da Sessão e Previsão de Contratação
    material_previsao_layout.addLayout(create_data_previsao_layout(data))

    # Adiciona o layout horizontal ao layout principal do grupo
    contratacao_layout.addLayout(material_previsao_layout)

    add_separator_line(contratacao_layout)

    # Definir Comentários
    contratacao_layout.addLayout(definir_comentarios(data, database_manager))

    contratacao_group_box.setLayout(contratacao_layout)

    return contratacao_group_box

def create_objeto_nup_layout(data):
    # Cria o layout horizontal para Objeto e NUP
    objeto_nup_layout = QHBoxLayout()

    # Objeto
    objeto_label = QLabel("Objeto:")
    objeto_edit = QLineEdit(data['objeto'])
    objeto_nup_layout.addWidget(objeto_label)
    objeto_nup_layout.addWidget(objeto_edit)

    # NUP
    nup_label = QLabel("NUP:")
    nup_edit = QLineEdit(data['nup'])
    nup_edit.setFixedWidth(180)
    objeto_nup_layout.addWidget(nup_label)
    objeto_nup_layout.addWidget(nup_edit)

    # Parecer AGU/NT
    parecer_agu_label = QLabel("Parecer AGU/NT:")
    parecer_agu_edit = QLineEdit(data.get('parecer_agu', ''))
    parecer_agu_edit.setFixedWidth(200)
    apply_widget_style_11(parecer_agu_edit)
    objeto_nup_layout.addWidget(parecer_agu_label)
    objeto_nup_layout.addWidget(parecer_agu_edit)

    return objeto_nup_layout

def create_objeto_completo_layout(data):
    # Cria o layout principal que ocupará o espaço disponível horizontalmente
    objeto_completo_layout = QHBoxLayout()

    # Valor Estimado
    valor_layout = QHBoxLayout()
    valor_edit = RealLineEdit(str(data.get('valor_total', "")))
    valor_edit.setFixedWidth(140)

    # Configurando o QLabel para o texto
    valor_label = QLabel("Valor Estimado:")

    # Adicionando os widgets ao layout
    valor_layout.addWidget(valor_label)
    valor_layout.addWidget(valor_edit)

    # Adiciona o layout do valor estimado ao layout principal
    objeto_completo_layout.addLayout(valor_layout)

    # Layout para o Objeto Completo
    objeto_completo_label = QLabel("Objeto Completo:")
    objeto_completo_edit = QTextEdit()
    objeto_completo_edit.setFixedHeight(60)
    
    # Removendo a altura fixa e ajustando para que o QTextEdit preencha todo o espaço disponível
    objeto_completo_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # Adiciona o label e o QTextEdit diretamente ao layout principal
    objeto_completo_layout.addWidget(objeto_completo_label)
    objeto_completo_layout.addWidget(objeto_completo_edit)

    # Expande o QTextEdit para empurrar o restante do conteúdo
    objeto_completo_layout.setStretch(1, 0)  # O label não expande
    objeto_completo_layout.setStretch(2, 1)  # O QTextEdit expande completamente

    return objeto_completo_layout

def create_material_criterio_tipo_layout(data):
    # Cria o layout horizontal para Material/Serviço, Critério de Julgamento e Tipo de Licitação
    material_criterio_tipo_layout = QVBoxLayout()

    etapas = (
        'Planejamento', 'Consolidação de Demanda', 'Montagem do Processo',
        'Nota Técnica', 'AGU', 'Recomendações AGU',
        'Pré-Publicação', 'Sessão Pública', 'Assinatura Contrato', 'Concluído'
    )

    # Etapa Atual
    etapa_atual_layout = QHBoxLayout()
    etapa_atual_label = QLabel("Etapa Atual:")
    apply_widget_style_11(etapa_atual_label)
    etapa_edit = create_combo_box(data.get('etapa_atual', 'Planejamento'),
                                etapas, 200, 30,
                                apply_widget_style_11)
    etapa_atual_layout.addWidget(etapa_atual_label)
    etapa_atual_layout.addWidget(etapa_edit)
    material_criterio_tipo_layout.addLayout(etapa_atual_layout)

    # Material/Serviço
    material_layout = QHBoxLayout()
    material_label = QLabel("Material/Serviço:")
    apply_widget_style_11(material_label)
    material_edit = create_combo_box(data.get('material_servico', 'Material'),
                                    ["Material", "Serviço"], 150, 30,
                                    apply_widget_style_11)
    material_layout.addWidget(material_label)
    material_layout.addWidget(material_edit)
    material_criterio_tipo_layout.addLayout(material_layout)

    # Critério de Julgamento
    criterio_layout = QHBoxLayout()
    criterio_label = QLabel("Critério Julgamento:")
    apply_widget_style_11(criterio_label)  # Aplicar estilo ao label
    criterio_edit = create_combo_box(data.get('criterio_julgamento', 'Menor Preço'),
                                    ["Menor Preço", "Maior Desconto"],
                                    150, 30,
                                    apply_widget_style_11)
    criterio_layout.addWidget(criterio_label)
    criterio_layout.addWidget(criterio_edit)
    material_criterio_tipo_layout.addLayout(criterio_layout)

    # Tipo de Licitação
    tipo_layout = QHBoxLayout()
    tipo_label = QLabel("Tipo:")
    apply_widget_style_11(tipo_label)  # Aplicar estilo ao label
    tipo_edit = create_combo_box(data.get('criterio_julgamento', 'Menor Preço'),
                                ["Compras", "Gêneros", "TI", "Serviços", "Obras", "Outros"],
                                150, 30,
                                apply_widget_style_11)
    tipo_layout.addWidget(tipo_label)
    tipo_layout.addWidget(tipo_edit)
    material_criterio_tipo_layout.addLayout(tipo_layout)

    # Vigência
    vigencia_layout = QHBoxLayout()
    vigencia_label = QLabel("Vigência:")
    apply_widget_style_11(tipo_label)  # Aplicar estilo ao label
    vigencia_edit = create_combo_box(data.get('vigencia', '12 (Doze) meses'),
                                ["6 (Seis) meses", "12 (Doze) meses", "24 (vinte e quatro) meses", "36 (trinta e seis) meses", "48 (quarenta e oito) meses"],
                                200, 30,
                                apply_widget_style_11)
    vigencia_layout.addWidget(vigencia_label)
    vigencia_layout.addWidget(vigencia_edit)
    material_criterio_tipo_layout.addLayout(vigencia_layout)

    return material_criterio_tipo_layout

def create_data_previsao_layout(data):
    # Cria o layout horizontal para Data da Sessão e Previsão de Contratação
    data_previsao_layout = QHBoxLayout()

    # Data da Sessão
    data_layout = QVBoxLayout()
    data_label = QLabel("Data da Sessão Pública:")
    apply_widget_style_11(data_label)
    data_edit = QCalendarWidget()
    # Removendo a coluna de semana do calendário
            
    data_sessao_str = data.get('data_sessao', '')
    if data_sessao_str:
        data_edit.setSelectedDate(QDate.fromString(data_sessao_str, "yyyy-MM-dd"))
    else:
        data_edit.setSelectedDate(QDate.currentDate())
    data_layout.addWidget(data_label)
    data_layout.addWidget(data_edit)
    data_previsao_layout.addLayout(data_layout)

    # Previsão Contratação
    previsao_contratacao_layout = QVBoxLayout()
    previsao_contratacao_label = QLabel("Previsão da Contratação:")
    apply_widget_style_11(previsao_contratacao_label)
    previsao_contratacao_edit = QCalendarWidget()
    # Removendo a coluna de semana do calendário
    
    
    previsao_contratacao_str = data.get('previsao_contratacao', '')
    if previsao_contratacao_str:
        previsao_contratacao_edit.setSelectedDate(QDate.fromString(previsao_contratacao_str, "yyyy-MM-dd"))
    else:
        previsao_contratacao_edit.setSelectedDate(QDate.currentDate())
    previsao_contratacao_layout.addWidget(previsao_contratacao_label)
    previsao_contratacao_layout.addWidget(previsao_contratacao_edit)
    data_previsao_layout.addLayout(previsao_contratacao_layout)

    return data_previsao_layout

def add_separator_line(layout):
    """Adiciona um QFrame horizontal como linha separadora ao layout especificado."""
    separator_line = QFrame()
    separator_line.setFrameShape(QFrame.Shape.HLine)
    separator_line.setFrameShadow(QFrame.Shadow.Sunken)
    layout.addWidget(separator_line)

def create_checkboxes(data):
    checkbox_style = """
        QCheckBox::indicator {
            width: 25px;
            height: 25px;
        }
    """

    checkboxes_layout = QVBoxLayout()

    # Checkbox para "Prioritário?"
    checkbox_prioritario = QCheckBox("Prioritário")
    checkbox_prioritario.setStyleSheet(checkbox_style)
    checkbox_prioritario.setChecked(data.get('pesquisa_preco', 'Não') == 'Sim')
    checkbox_prioritario.setIcon(QIcon(str(ICONS_DIR / "prioridade.png")))
    checkbox_prioritario.setIconSize(QSize(24, 24))
    checkboxes_layout.addWidget(checkbox_prioritario)

    # Checkbox para "Emenda Parlamentar?"
    checkbox_emenda = QCheckBox("Emenda Parlamentar")
    checkbox_emenda.setStyleSheet(checkbox_style)
    checkbox_emenda.setChecked(data.get('atividade_custeio', 'Não') == 'Sim')
    checkbox_emenda.setIcon(QIcon(str(ICONS_DIR / "subsidy.png")))
    checkbox_emenda.setIconSize(QSize(24, 24))
    checkboxes_layout.addWidget(checkbox_emenda)

    # Checkbox para "Registro de Preços?"
    checkbox_registro_precos = QCheckBox("SRP")
    checkbox_registro_precos.setStyleSheet(checkbox_style)
    checkbox_registro_precos.setChecked(data.get('registro_precos', 'Não') == 'Sim')
    checkbox_registro_precos.setIcon(QIcon(str(ICONS_DIR / "price-tag.png")))
    checkbox_registro_precos.setIconSize(QSize(24, 24))
    checkboxes_layout.addWidget(checkbox_registro_precos)

    # Checkbox para "Atividade de Custeio?"
    checkbox_atividade_custeio = QCheckBox("Atividade de Custeio")
    checkbox_atividade_custeio.setStyleSheet(checkbox_style)
    checkbox_atividade_custeio.setChecked(data.get('atividade_custeio', 'Não') == 'Sim')
    checkbox_atividade_custeio.setIcon(QIcon(str(ICONS_DIR / "verify_menu.png")))
    checkbox_atividade_custeio.setIconSize(QSize(24, 24))
    checkboxes_layout.addWidget(checkbox_atividade_custeio)

    # Checkbox para "Processo Parametrizado"
    checkbox_parametrizado = QCheckBox("Processo Parametrizado")
    checkbox_parametrizado.setStyleSheet(checkbox_style)
    checkbox_parametrizado.setChecked(data.get('atividade_custeio', 'Não') == 'Sim')
    checkbox_parametrizado.setIcon(QIcon(str(ICONS_DIR / "standard.png")))
    checkbox_parametrizado.setIconSize(QSize(24, 24))
    checkboxes_layout.addWidget(checkbox_parametrizado)

    return checkboxes_layout

def definir_comentarios(data, database_manager):
    label = QLabel("Comentários:")
    label.setFont(QFont("Arial", 14, QFont.Weight.Bold))

    listWidget_comentarios = QListWidget()
    listWidget_comentarios.setFont(QFont("Arial", 12))
    listWidget_comentarios.setWordWrap(True)
    # self.listWidget_comentarios.setFixedWidth(430)

    comentarios_vlayout = QVBoxLayout()
    comentarios_vlayout.addWidget(label)
    comentarios_vlayout.addWidget(listWidget_comentarios)
    listWidget_comentarios.setFixedWidth(700)

    delegate = TextEditDelegate()
    listWidget_comentarios.setItemDelegate(delegate)
    listWidget_comentarios.itemChanged.connect(lambda: salvar_comentarios_editados(data, listWidget_comentarios, database_manager))

    comentarios = carregar_comentarios(data, database_manager)
    for comentario in comentarios:
        item = QListWidgetItem(comentario)
        item.setIcon(QIcon(str(ICONS_DIR / "checked.png")))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        listWidget_comentarios.addItem(item)

    label_novo_comentario = QLabel("Campo de edição de Comentário:")
    label_novo_comentario.setFont(QFont("Arial", 14, QFont.Weight.Bold))
    textEdit_novo_comentario = QTextEdit()
    textEdit_novo_comentario.setPlaceholderText("Adicione um novo comentário aqui...")
    textEdit_novo_comentario.setFont(QFont("Arial", 12))

    edicao_vlayout = QVBoxLayout()
    edicao_vlayout.addWidget(label_novo_comentario)
    edicao_vlayout.addWidget(textEdit_novo_comentario)
    textEdit_novo_comentario.setPlaceholderText("Adicione um novo comentário aqui...")
    textEdit_novo_comentario.setFont(QFont("Arial", 12))

    buttonsLayout = QHBoxLayout()

    # Caminhos para os ícones
    icon_add = QIcon(str(ICONS_DIR / "add_comment.png"))
    icon_exclude = QIcon(str(ICONS_DIR / "delete_comment.png"))

    button_adicionar_comentario = QPushButton("Adicionar Comentário")
    button_adicionar_comentario.setIcon(icon_add)
    button_excluir_comentario = QPushButton("Excluir Comentário")
    button_excluir_comentario.setIcon(icon_exclude)

    buttonsLayout.addWidget(button_adicionar_comentario)
    buttonsLayout.addWidget(button_excluir_comentario)

    button_font = QFont("Arial", 12)
    button_adicionar_comentario.setFont(button_font)
    button_excluir_comentario.setFont(button_font)
    
    button_adicionar_comentario.clicked.connect(lambda: adicionar_comentario(data, textEdit_novo_comentario, listWidget_comentarios, database_manager))
    button_excluir_comentario.clicked.connect(lambda: excluir_comentario(data, listWidget_comentarios, database_manager))

    comentarios_layout = QHBoxLayout()
    comentarios_layout.addLayout(edicao_vlayout)
    comentarios_layout.addLayout(comentarios_vlayout)

    edicao_vlayout.addLayout(buttonsLayout)

    return comentarios_layout

def salvar_comentarios_editados(data, listWidget_comentarios, database_manager):
    comentarios = [listWidget_comentarios.item(i).text() for i in range(listWidget_comentarios.count())]
    comentarios_str = '|||'.join(comentarios)  # Concatena todos os comentários com "|||"

    with database_manager as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE controle_processos SET comentarios = ? WHERE id_processo = ?", (comentarios_str, data['id_processo']))
        connection.commit()
        print("Comentários salvos com sucesso.")

def adicionar_comentario(data, textEdit_novo_comentario, listWidget_comentarios, database_manager):
    novo_comentario = textEdit_novo_comentario.toPlainText().strip()
    if novo_comentario:
        item = QListWidgetItem(novo_comentario)
        item.setIcon(QIcon(str(ICONS_DIR / "checked.png")))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        listWidget_comentarios.addItem(item)
        textEdit_novo_comentario.clear()
        salvar_comentarios_editados(data, listWidget_comentarios, database_manager)

def excluir_comentario(data, listWidget_comentarios, database_manager):
    item = listWidget_comentarios.currentItem()
    if item:
        listWidget_comentarios.takeItem(listWidget_comentarios.row(item))
        # Reordenar comentários (neste caso, apenas manter os ícones e textos dos comentários)
        for index in range(listWidget_comentarios.count()):
            item = listWidget_comentarios.item(index)
            # Manter o ícone e o texto do comentário
            item.setIcon(QIcon(str(ICONS_DIR / "checked.png")))
        salvar_comentarios_editados(data, listWidget_comentarios, database_manager)

def carregar_comentarios(data, database_manager):
    with database_manager as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT comentarios FROM controle_processos WHERE id_processo = ?", (data['id_processo'],))
        row = cursor.fetchone()
        if row and row[0]:
            # Divide os comentários com base no delimitador "|||"
            return row[0].split("|||")
        return []

def salvar_comentarios(data, listWidget_comentarios, database_manager):
    # Esta função deve salvar apenas o texto dos comentários, sem os números.
    comentarios = [listWidget_comentarios.item(i).text() for i in range(listWidget_comentarios.count())]
    comentarios_str = '|||'.join(comentarios)  # Concatena todos os comentários com "|||"

    with database_manager as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE controle_processos SET comentarios = ? WHERE id_processo = ?", (comentarios_str, data['id_processo']))
        connection.commit()
        print("Comentários salvos com sucesso.")
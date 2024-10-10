from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    EditDataDialogUtils, RealLineEdit, TextEditDelegate,
                                    create_combo_box, add_separator_line, create_button, 
                                    apply_widget_style_11, validate_and_convert_date)
from modules.dispensa_eletronica.formulario_excel import FormularioExcel
from diretorios import *

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

def create_frame_formulario_group():
    formulario_group_box = QGroupBox("Formulário de Dados")
    apply_widget_style_11(formulario_group_box)   
    formulario_group_box.setFixedWidth(300)   
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

def definir_comentarios(data, database_manager):
    # Label para os comentários
    label = QLabel("Comentários:")
    label.setFont(QFont("Arial", 14, QFont.Weight.Bold))

    # Lista de comentários
    listWidget_comentarios = QListWidget()
    listWidget_comentarios.setFont(QFont("Arial", 12))
    listWidget_comentarios.setWordWrap(True)
    listWidget_comentarios.setFixedWidth(760)
    
    # Delegado para edição de texto
    delegate = TextEditDelegate()
    listWidget_comentarios.setItemDelegate(delegate)
    listWidget_comentarios.itemChanged.connect(lambda: salvar_comentarios_editados(data, listWidget_comentarios, database_manager))

    # Carregar comentários existentes
    comentarios = carregar_comentarios(data, database_manager)
    for comentario in comentarios:
        partes = comentario.split('<>', 2)
        if len(partes) == 3:
            _, icone_inicio, texto_comentario = partes
        else:
            icone_inicio, texto_comentario = "checked.png", comentario
        item = QListWidgetItem(texto_comentario)
        item.setIcon(QIcon(str(ICONS_DIR / icone_inicio)))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        listWidget_comentarios.addItem(item)

    # Botões para adicionar e excluir comentários
    icon_add = QIcon(str(ICONS_DIR / "add_comment.png"))
    icon_exclude = QIcon(str(ICONS_DIR / "delete_comment.png"))
    
    button_adicionar_comentario = QPushButton("Adicionar Comentário")
    button_adicionar_comentario.setIcon(icon_add)
    button_adicionar_comentario.setFont(QFont("Arial", 12))
    
    button_excluir_comentario = QPushButton("Excluir Comentário")
    button_excluir_comentario.setIcon(icon_exclude)
    button_excluir_comentario.setFont(QFont("Arial", 12))
    
    button_adicionar_comentario.clicked.connect(lambda: abrir_dialogo_adicionar_comentario(data, listWidget_comentarios, database_manager))
    button_excluir_comentario.clicked.connect(lambda: excluir_comentario(data, listWidget_comentarios, database_manager))

    # Layout para os botões e o label (horizontal layout)
    top_buttons_layout = QHBoxLayout()
    top_buttons_layout.addWidget(label)
    top_buttons_layout.addWidget(button_adicionar_comentario)
    top_buttons_layout.addWidget(button_excluir_comentario)
    top_buttons_layout.addStretch()  # Espaço flexível para alinhar corretamente

    # Layout de edição e botões de comentário (vertical layout)
    edicao_vlayout = QVBoxLayout()
    edicao_vlayout.addLayout(top_buttons_layout)
    edicao_vlayout.addWidget(listWidget_comentarios)

    # Layout final contendo o frame do formulário à esquerda e os comentários à direita
    comentarios_layout = QHBoxLayout()
    comentarios_layout.addWidget(create_frame_formulario_group())  # Chama a função de layout do formulário
    comentarios_layout.addLayout(edicao_vlayout)

    return comentarios_layout

def abrir_dialogo_adicionar_comentario(data, listWidget_comentarios, database_manager):
    dialog = QDialog()
    dialog.setWindowTitle("Adicionar Comentário")
    dialog.setModal(True)
    dialog_layout = QVBoxLayout()

    # TextEdit para adicionar comentário
    textEdit_novo_comentario = QTextEdit()
    textEdit_novo_comentario.setPlaceholderText("Adicione um novo comentário aqui...")
    textEdit_novo_comentario.setFont(QFont("Arial", 12))
    dialog_layout.addWidget(textEdit_novo_comentario)

    # Label para selecionar ícone
    label_selecionar_icone = QLabel("Selecionar ícone:")
    label_selecionar_icone.setFont(QFont("Arial", 14, QFont.Weight.Bold))
    dialog_layout.addWidget(label_selecionar_icone)

    # Ícones e Checkboxes
    icones = [
        ("Caveira", "head_skull.png"),
        ("Alerta", "alert.png"),
        ("Mensagem", "message_alert.png"),
        ("Prioridade", "prioridade.png"),
        ("Concluído", "concluido.png")
    ]
    
    checkboxes = []
    checkboxes_layout = QHBoxLayout()
    for texto, icone_nome in icones:
        checkbox_layout = QHBoxLayout()
        checkbox = QCheckBox(texto)
        checkbox.setFont(QFont("Arial", 12))
        checkbox.setAutoExclusive(True)  # Permitir apenas um checkbox selecionado
        label_icone = QLabel()
        label_icone.setPixmap(QPixmap(str(ICONS_DIR / icone_nome)).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        checkbox_layout.addWidget(label_icone)
        checkbox_layout.addWidget(checkbox)
        checkboxes_layout.addLayout(checkbox_layout)
        checkboxes.append((checkbox, icone_nome))
    
    dialog_layout.addLayout(checkboxes_layout)

    # Botões de Ação
    button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    button_box.accepted.connect(lambda: adicionar_comentario(data, textEdit_novo_comentario, listWidget_comentarios, database_manager, dialog, checkboxes))
    button_box.rejected.connect(dialog.reject)
    dialog_layout.addWidget(button_box)

    dialog.setLayout(dialog_layout)
    dialog.exec()

def adicionar_comentario(data, textEdit_novo_comentario, listWidget_comentarios, database_manager, dialog, checkboxes):
    novo_comentario = textEdit_novo_comentario.toPlainText().strip()
    if novo_comentario:
        # Verificar qual ícone foi selecionado
        icone_selecionado = None
        for checkbox, icone_nome in checkboxes:
            if checkbox.isChecked():
                icone_selecionado = icone_nome
                break
        
        if icone_selecionado is None:
            icone_selecionado = "checked.png"  # Padrão caso nenhum ícone seja selecionado
        
        comentario_formatado = f"<>{icone_selecionado}<>{novo_comentario}"
        item = QListWidgetItem(novo_comentario)
        item.setIcon(QIcon(str(ICONS_DIR / icone_selecionado)))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        listWidget_comentarios.addItem(item)
        salvar_comentarios_editados(data, listWidget_comentarios, database_manager)
    dialog.accept()

def carregar_comentarios(data, database_manager):
    with database_manager as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT comentarios FROM controle_processos WHERE id_processo = ?", (data['id_processo'],))
        row = cursor.fetchone()
        if row and row[0]:
            # Divide os comentários com base no delimitador "|||"
            comentarios = row[0].split("|||")
            return comentarios
        return []

def salvar_comentarios_editados(data, listWidget_comentarios, database_manager):
    comentarios = []
    for i in range(listWidget_comentarios.count()):
        item = listWidget_comentarios.item(i)
        icone_nome = item.icon().name() if not item.icon().isNull() else "checked.png"
        comentarios.append(f"<>{icone_nome}<>{item.text()}")
    comentarios_str = '|||'.join(comentarios)  # Concatena todos os comentários com "|||"

    with database_manager as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE controle_processos SET comentarios = ? WHERE id_processo = ?", (comentarios_str, data['id_processo']))
        connection.commit()
        print("Comentários salvos com sucesso.")

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
## modules/contratos/edit_dialog.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
import sqlite3
from diretorios import BRASIL_IMAGE_PATH, ICONS_DIR, CONTROLE_DADOS, load_config
import pandas as pd
from modules.contratos.utils import WidgetHelper
from datetime import datetime
from modules.planejamento.utilidades_planejamento import DatabaseManager

class StackWidgetManager:
    def __init__(self, parent, data_function):
        self.parent = parent
        self.data_function = data_function
        self.icons_dir = Path(ICONS_DIR)
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        self.stacked_widget = QStackedWidget(parent)
        self.stacked_widget.setStyleSheet(
            "QStackedWidget {"
            "border: 1px solid #414242; border-radius: 5px; "
            "border-bottom-left-radius: 5px; border-bottom-right-radius: 5px; }"
        )
        self.widgets = {}
        self.widget_creators = {
            "Informações": self.create_widget_informacoes_gerais,
            "Termo Aditivo": self.create_widget_termo_aditivo,
            "Gestão/Fiscalização": self.create_widget_gestao_fiscalizacao,
            "Status": self.create_widget_status,
        }
        self.line_edits = {}

    def add_widget(self, name, widget):
        self.stacked_widget.addWidget(widget)
        self.widgets[name] = widget

    def show_widget(self, name):
        if name in self.widgets:
            self.stacked_widget.setCurrentWidget(self.widgets[name])
        else:
            create_widget_function = self.widget_creators.get(name)
            if create_widget_function:
                create_widget_function()
                self.stacked_widget.setCurrentWidget(self.widgets[name])

    def get_widget(self):
        return self.stacked_widget

    def create_widget_informacoes_gerais(self):
        data = self.data_function()
        widget = QWidget()
        h_layout = QHBoxLayout(widget)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Containers
        left_container = QWidget()
        right_container = QWidget()

        # Left layout
        left_layout = QVBoxLayout(left_container)

        id_processo_layout, self.line_edits['id_processo'] = WidgetHelper.create_line_edit("ID Processo:", data.get('Processo', 'N/A'))
        
        # Criar combobox para contrato_ata
        contrato_ata_options = [
            "Contrato", "Ata"
        ]
        contrato_ata_layout, self.contrato_ata_combo_box = WidgetHelper.create_combo_box("Contrato/Ata:", contrato_ata_options, data.get('Tipo', 'Contrato'))
        
        numero_contrato_layout, self.line_edits['numero'] = WidgetHelper.create_line_edit("Número:", data.get('Contrato/Ata', 'N/A'))
        nup_layout, self.line_edits['processo'] = WidgetHelper.create_line_edit("NUP:", data.get('processo', 'N/A'))
        valor_global_layout, self.line_edits['valor_global'] = WidgetHelper.create_line_edit("Valor Global:", data.get('Valor', 'N/A'))
        cnpj_layout, self.line_edits['cnpj_cpf_idgener'] = WidgetHelper.create_line_edit("CNPJ:", data.get('cnpj_cpf_idgener', 'N/A'))
        fornecedor_layout, self.line_edits['nome_fornecedor'] = WidgetHelper.create_line_edit("Empresa:", data.get('Empresa', 'N/A'))
        objeto_layout, self.line_edits['objeto'] = WidgetHelper.create_line_edit("Objeto:", data.get('Objeto', 'N/A'))

        left_layout.addLayout(id_processo_layout)
        left_layout.addLayout(contrato_ata_layout)
        left_layout.addLayout(numero_contrato_layout)
        left_layout.addLayout(nup_layout)
        left_layout.addLayout(valor_global_layout)
        left_layout.addLayout(cnpj_layout)
        left_layout.addLayout(fornecedor_layout)
        left_layout.addLayout(objeto_layout)

        # Pode Renovar
        pode_renovar_layout, self.pode_renovar_buttons, self.pode_renovar_group = WidgetHelper.create_radio_buttons("Pode Renovar?", ["Sim", "Não"])
        pode_renovar_value = data.get('Renova?', 'Sim')
        if pode_renovar_value not in self.pode_renovar_buttons:
            pode_renovar_value = 'Não'
        self.pode_renovar_buttons[pode_renovar_value].setChecked(True)
        left_layout.addLayout(pode_renovar_layout)

        # Custeio
        custeio_layout, self.custeio_buttons, self.custeio_group = WidgetHelper.create_radio_buttons("Custeio?", ["Sim", "Não"])
        custeio_value = data.get('Custeio?', 'Sim')
        if custeio_value not in self.custeio_buttons:
            custeio_value = 'Não'
        self.custeio_buttons[custeio_value].setChecked(True)
        left_layout.addLayout(custeio_layout)

        # Natureza Continuada
        natureza_continuada_layout, self.natureza_continuada_buttons, self.natureza_continuada_group = WidgetHelper.create_radio_buttons("Natureza Continuada?", ["Sim", "Não"])
        natureza_continuada_value = data.get('natureza_continuada', 'Não')
        if natureza_continuada_value not in self.natureza_continuada_buttons:
            natureza_continuada_value = 'Não'
        self.natureza_continuada_buttons[natureza_continuada_value].setChecked(True)
        left_layout.addLayout(natureza_continuada_layout)

        # Material/Serviço
        material_servico_layout, self.material_servico_buttons, self.material_servico_group = WidgetHelper.create_radio_buttons("Material/Serviço:", ["Material", "Serviço"])
        material_servico_value = data.get('material_servico', 'Material')
        if material_servico_value not in self.material_servico_buttons:
            material_servico_value = 'Material'
        self.material_servico_buttons[material_servico_value].setChecked(True)
        left_layout.addLayout(material_servico_layout)

        # Layout direito
        right_layout = QVBoxLayout(right_container)
        inicial_layout, self.date_edit_inicial = WidgetHelper.create_date_edit("Início da Vigência:", data.get('vigencia_inicial', None))
        final_layout, self.date_edit_final = WidgetHelper.create_date_edit("Final da Vigência:", data.get('vigencia_final', None))

        # Adicionar ComboBox para "Sigla da OM" e campos para "UASG" e "Órgão"
        self.combo_sigla_om = QComboBox()
        self.line_edit_uasg = QLineEdit()
        self.line_edit_orgao = QLineEdit()
        self.line_edit_indicativo = QLineEdit()

        # Definir os campos UASG e Orgao como somente leitura
        self.line_edit_uasg.setReadOnly(True)
        self.line_edit_orgao.setReadOnly(True)
        self.line_edit_indicativo.setReadOnly(True)

        # Conectar o sinal de mudança de índice do combo box à função de atualização
        self.combo_sigla_om.currentIndexChanged.connect(self.on_combo_change)

        # Criando layouts verticais para cada grupo de label e widget
        sigla_layout = QVBoxLayout()
        sigla_label = QLabel('Sigla da OM Responsável pelo Planejamento:')
        sigla_label.setStyleSheet("font-size: 14px;")
        sigla_layout.addWidget(sigla_label)
        sigla_layout.addWidget(self.combo_sigla_om)
        self.combo_sigla_om.setStyleSheet("font-size: 14px;")  # Ajuste de estilo para o combo box

        uasg_layout = QVBoxLayout()
        uasg_label = QLabel('UASG:')
        uasg_label.setStyleSheet("font-size: 14px;")
        uasg_layout.addWidget(uasg_label)
        uasg_layout.addWidget(self.line_edit_uasg)
        self.line_edit_uasg.setStyleSheet("font-size: 14px;")  # Ajuste de estilo para o QLineEdit

        orgao_layout = QVBoxLayout()
        orgao_label = QLabel('Órgão Responsável:')
        orgao_label.setStyleSheet("font-size: 14px;")
        orgao_layout.addWidget(orgao_label)
        orgao_layout.addWidget(self.line_edit_orgao)
        self.line_edit_orgao.setStyleSheet("font-size: 14px;")  # Ajuste de estilo para o QLineEdit

        indicativo_layout = QVBoxLayout()
        indicativo_label = QLabel('Indicativo:')
        indicativo_label.setStyleSheet("font-size: 14px;")
        indicativo_layout.addWidget(indicativo_label)
        indicativo_layout.addWidget(self.line_edit_indicativo)
        self.line_edit_indicativo.setStyleSheet("font-size: 14px;")  # Ajuste de estilo para o QLineEdit

        # Adicionando os layouts verticais ao layout direito
        right_layout.addLayout(inicial_layout)
        right_layout.addLayout(final_layout)
        right_layout.addLayout(sigla_layout)
        right_layout.addLayout(uasg_layout)
        right_layout.addLayout(orgao_layout)
        right_layout.addLayout(indicativo_layout)
        right_layout.addStretch()
        
        # Inicializar dados do ComboBox
        self.init_combobox_data()

        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)

        h_layout.addWidget(left_container)
        h_layout.addWidget(line)
        h_layout.addWidget(right_container)

        self.add_widget("Informações", widget)

    def init_combobox_data(self):
        # Inicialize o DatabaseManager para carregar dados no combobox
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        data = self.data_function()

        with self.database_manager as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT sigla_om, uasg, orgao_responsavel, indicativo_om FROM controle_om")
            rows = cursor.fetchall()

        index_to_set = 0
        for index, (sigla_om, uasg, orgao, indicativo_om) in enumerate(rows):
            # Adiciona todos os valores necessários ao combo box como uma tupla
            self.combo_sigla_om.addItem(sigla_om, (str(uasg), str(orgao), str(indicativo_om)))  
            if sigla_om == data.get('Sigla OM', ''):
                index_to_set = index

        self.combo_sigla_om.setCurrentIndex(index_to_set)
        self.on_combo_change(index_to_set)

    def on_combo_change(self, index):
        current_data = self.combo_sigla_om.itemData(index)
        if current_data:
            self.line_edit_uasg.setText(current_data[0] if current_data[0] is not None else "") 
            self.line_edit_orgao.setText(current_data[1] if current_data[1] is not None else "")
            self.line_edit_indicativo.setText(current_data[2] if current_data[2] is not None else "")
            
    def create_widget_termo_aditivo(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Termo Aditivo teste"))
        self.add_widget("Termo Aditivo", widget)

    def create_widget_gestao_fiscalizacao(self):
        data = self.data_function()
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel(f"Posto: {data.get('posto_gestor', '')}"))
        layout.addWidget(QLabel(f"Gestor: {data.get('gestor', '')}"))
        layout.addWidget(QLabel(f"Posto: {data.get('posto_fiscal', '')}"))
        layout.addWidget(QLabel(f"Fiscal: {data.get('fiscal', '')}"))
        layout.addWidget(QLabel(f"Posto: {data.get('posto_fiscal_substituto', '')}"))
        layout.addWidget(QLabel(f"Fiscal Substituto: {data.get('fiscal_substituto', '')}"))
        layout.addWidget(QLabel(f"Posto: {data.get('posto_fiscal_administrativo', '')}"))
        layout.addWidget(QLabel(f"Fiscal Administrativo: {data.get('fiscal_administrativo', '')}"))

        self.add_widget("Gestão/Fiscalização", widget)

    def create_widget_status(self):
        data = self.data_function()
        widget = QWidget()
        layout = QVBoxLayout(widget)

        status_options = [
            "Ata Gerada", "Empresa", "SIGDEM", "Assinado", "Publicado", "Alerta Prazo",
            "Seção de Contratos", "Nota Técnica", "AGU", "Prorrogado"
        ]
        status_layout, self.status_combo_box = WidgetHelper.create_combo_box("Status:", status_options, data.get('status'))

        # Criar ícone para o botão de registro de status
        registrar_status_icon = QIcon(str(self.icons_dir / "registrar_status.png"))

        # Criar botão "Adicionar Registro"
        add_button_registrar_status = WidgetHelper.create_button(
            text="Adicionar Registro:",
            icon=registrar_status_icon,
            callback=self.on_add_record,  # Callback para o botão
            tooltip_text="Adicionar novo registro",
            button_size=QSize(200, 35),
            icon_size=QSize(40, 40)
        )

        # Criar ícone para o botão de comentários
        registrar_comentario_icon = QIcon(str(self.icons_dir / "registrar_comentario.png"))

        # Criar botão "Adicionar Comentário"
        add_button_registrar_comentario = WidgetHelper.create_button(
            text="Adicionar Comentário:",
            icon=registrar_comentario_icon,
            callback=self.on_add_comment,  # Callback para o botão de comentários
            tooltip_text="Adicionar novo comentário",
            button_size=QSize(200, 35),
            icon_size=QSize(40, 40)
        )

        # **Novo botão para excluir comentário**
        delete_button_comentario = WidgetHelper.create_button(
            text="Excluir Comentário",
            icon=QIcon(str(self.icons_dir / "delete.png")),
            callback=self.on_delete_comment,  # Callback para excluir o comentário
            tooltip_text="Excluir comentário selecionado",
            button_size=QSize(200, 35),
        )

        # Criar layout horizontal para combobox e botões
        h_layout = QHBoxLayout()
        h_layout.addStretch()  # Spacer no início
        h_layout.addLayout(status_layout)
        h_layout.addStretch()  # Spacer no fim

        # Adicionar o layout horizontal ao layout principal
        layout.addLayout(h_layout)

        layout.addWidget(add_button_registrar_status)
        # Adicionar visualizador de registros
        self.records_view = QListWidget(widget)
        self.records_view.itemDoubleClicked.connect(self.edit_record)
        layout.addWidget(self.records_view)

        # Criar layout horizontal para os botões de comentários
        comment_buttons_layout = QHBoxLayout()
        comment_buttons_layout.addWidget(add_button_registrar_comentario)
        comment_buttons_layout.addWidget(delete_button_comentario)

        # Adicionar o layout horizontal de botões de comentários ao layout principal
        layout.addLayout(comment_buttons_layout)
        
        # Adicionar visualizador de comentários
        self.comments_view = QListWidget(widget)
        self.comments_view.itemDoubleClicked.connect(self.edit_comment)
        layout.addWidget(self.comments_view)

        self.add_widget("Status", widget)

        # Carregar registros iniciais se houver
        if 'registro_status' in data:
            registros = data['registro_status'].split("\n")
            self.records_view.addItems(registros)

        if 'comentarios' in data:
            comentarios = data['comentarios'].split("\n")
            for comentario in comentarios:
                # Cria um item de lista com o comentário
                comment_item = QListWidgetItem(comentario)

                # Define o ícone para o item
                comment_icon = QIcon(str(self.icons_dir / "comment.png"))
                comment_item.setIcon(comment_icon)

                # Adiciona o item à lista de comentários
                self.comments_view.addItem(comment_item)

    # Método para excluir comentário selecionado
    def on_delete_comment(self):
        selected_items = self.comments_view.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.parent, "Excluir Comentário", "Nenhum comentário selecionado para excluir.")
            return
        
        for item in selected_items:
            self.comments_view.takeItem(self.comments_view.row(item))
        
        self.save_comments()  # Atualiza os comentários salvos

    def on_add_record(self):
        dialog = AddCommentDialog(self)
        if dialog.exec():
            comment = dialog.get_comment()
            if comment:
                timestamp = datetime.now().strftime("%d/%m/%Y")
                status = self.status_combo_box.currentText()
                record = f"{timestamp} ({status}) - {comment}"
                self.records_view.addItem(record)
                self.save_records()

    def on_add_comment(self):
        dialog = AddCommentDialog(self)
        if dialog.exec():
            comment = dialog.get_comment()
            if comment:
                # Cria um novo item com o comentário
                comment_item = QListWidgetItem(comment)
                
                # Define o ícone para o item
                comment_icon = QIcon(str(self.icons_dir / "comment.png"))
                comment_item.setIcon(comment_icon)
                
                # Adiciona o item à lista de comentários
                self.comments_view.addItem(comment_item)
                
                # Salva os comentários
                self.save_comments()

    def edit_comment(self, item):
        dialog = AddCommentDialog(self, initial_comment=item.text())
        if dialog.exec():
            comment = dialog.get_comment()
            if comment:
                # Atualiza o texto do item existente
                item.setText(comment)
                
                # Define o ícone novamente, caso necessário
                comment_icon = QIcon(str(self.icons_dir / "comment.png"))
                item.setIcon(comment_icon)
                
                # Salva os comentários atualizados
                self.save_comments()

    def edit_record(self, item):
        dialog = AddCommentDialog(self, initial_comment=item.text())
        if dialog.exec():
            comment = dialog.get_comment()
            if comment:
                timestamp = datetime.now().strftime("%d/%m/%Y")
                status = self.status_combo_box.currentText()
                record = f"{timestamp} ({status}) - {comment}"
                item.setText(record)
                self.save_records()

    def save_records(self):
        records = [self.records_view.item(i).text() for i in range(self.records_view.count())]
        records_text = "\n".join(records)
        # Implemente a lógica para salvar os registros (por exemplo, salvar no banco de dados ou em um arquivo)
        print("Registros salvos:", records_text)

    def save_comments(self):
        comments = [self.comments_view.item(i).text() for i in range(self.comments_view.count())]
        comments_text = "\n".join(comments)
        # Implemente a lógica para salvar os comentários (por exemplo, salvar no banco de dados ou em um arquivo)
        print("Comentários salvos:", comments_text)

class AddCommentDialog(QDialog):
    def __init__(self, parent=None, initial_comment=""):
        super().__init__(parent if isinstance(parent, QWidget) else None)
        self.setWindowTitle("Adicionar Comentário" if not initial_comment else "Editar Comentário")
        self.layout = QVBoxLayout(self)

        self.comment_edit = QTextEdit(self)
        self.comment_edit.setPlainText(initial_comment)
        self.layout.addWidget(QLabel("Escreva seu comentário:"))
        self.layout.addWidget(self.comment_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_comment(self):
        return self.comment_edit.toPlainText()

class AtualizarDadosContratos(QDialog):
    dadosContratosSalvos = pyqtSignal()

    def __init__(self, icons_dir, data_function, df_registro_selecionado, table_view=None, model=None, indice_linha=None, parent=None):
        super().__init__(parent)
        self.table_view = table_view
        self.model = model
        self.indice_linha = indice_linha
        self.icons_dir = Path(icons_dir)
        self.data_function = data_function  # Use data_function como um atributo da classe
        self.df_registro_selecionado = df_registro_selecionado  # Atribua o DataFrame ao atributo da classe
        self.setupUI()

    def setupUI(self):
        try:
            print("Iniciando setupUI...")
            self.setWindowTitle("Atualizar Dados do Contrato")
            self.setFixedSize(1200, 600)
            main_layout = QVBoxLayout(self)

            # Verificar se os dados estão sendo extraídos corretamente
            data = self.data_function()
            print("Dados para o contrato:", data)

            self.header_widget = self.update_title_label()
            main_layout.addWidget(self.header_widget)

            h_layout = QHBoxLayout()

            content_layout = QVBoxLayout()
            content_layout.setSpacing(0)

            nav_layout = QHBoxLayout()
            brasil_pixmap = QPixmap(str(BRASIL_IMAGE_PATH))
            brasil_pixmap = brasil_pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image_label_esquerda = QLabel()
            image_label_esquerda.setPixmap(brasil_pixmap)
            image_label_esquerda.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nav_layout.addWidget(image_label_esquerda)

            self.navigation_buttons = []
            self.add_navigation_button(nav_layout, "Informações", lambda: self.show_widget("Informações"))
            self.add_navigation_button(nav_layout, "Termo Aditivo", lambda: self.show_widget("Termo Aditivo"))
            self.add_navigation_button(nav_layout, "Gestão/Fiscalização", lambda: self.show_widget("Gestão/Fiscalização"))
            self.add_navigation_button(nav_layout, "Status", lambda: self.show_widget("Status"))
            nav_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)) 
            content_layout.addLayout(nav_layout)

            self.stack_manager = StackWidgetManager(self, self.data_function)

            # Exibir o widget "Informações" logo após o carregamento da interface
            self.show_widget("Informações")

            content_layout.addWidget(self.stack_manager.get_widget())

            h_layout.addLayout(content_layout)

            self.tree_view = QTreeView()
            self.tree_model = QStandardItemModel()
            self.tree_view.setModel(self.tree_model)
            self.populate_tree_view()
            h_layout.addWidget(self.tree_view)

            main_layout.addLayout(h_layout)
            self.setLayout(main_layout)

            print("setupUI concluído com sucesso.")
        except Exception as e:
            print(f"Erro no setupUI: {str(e)}")
            raise


    def populate_tree_view(self):
        data = self.data_function()  # Chame a função para obter os dados
        tipo = data.get('Tipo', 'Tipo Desconhecido')
        print(f"Tipo extraído: {tipo}")  # Adicionado para depuração

        root = QStandardItem(tipo)

        children = {
            'Valor Global': data.get('Valor', 'N/A'),
            'Link PNCP': data.get('link_pncp', 'N/A'),
            'Portaria': data.get('portaria', 'N/A'),
            'Vigência Inicial': data.get('vigencia_inicial', 'N/A'),
            'Vigência Final': data.get('vigencia_final', 'N/A'),
            'Número Contrato': data.get('Contrato/Ata', 'N/A')
        }

        for key, value in children.items():
            child = QStandardItem(f"{key}: {value}")
            root.appendRow(child)

        self.tree_model.appendRow(root)
        self.tree_model.setHorizontalHeaderLabels([f"Detalhes do {tipo}"])

    def add_navigation_button(self, layout, text, callback):
        button = QPushButton(text)
        button.setCheckable(True)
        button.setMinimumWidth(172)
        button.setStyleSheet(self.get_button_style())
        button.clicked.connect(callback)
        layout.addWidget(button)
        self.navigation_buttons.append(button)

    def get_button_style(self):
        return (
            "QPushButton {"
            "border: 1px solid #414242; background: #B0B0B0; color: black; font-weight: bold; font-size: 12pt;"
            "border-top-left-radius: 5px; border-top-right-radius: 5px; "
            "border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; "
            "border-bottom-color: #414242; }"
            "QPushButton:hover { background: #D0D0D0; font-weight: bold; color: black; }"
        )

    def update_button_styles(self, active_button):
        for button in self.navigation_buttons:
            if button == active_button:
                button.setStyleSheet(
                    "QPushButton { border: 1px solid #414242; background: #414242; font-weight: bold; color: white; "
                    "border-top-left-radius: 5px; border-top-right-radius: 5px; "
                    "border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; "
                    "border-bottom-color: #414242; font-size: 12pt; }"
                    "QPushButton:hover { background: #D0D0D0; font-weight: bold; color: black; }"
                )
            else:
                button.setStyleSheet(
                    "QPushButton { background: #B0B0B0; font-weight: bold; color: black; border: 1px solid #414242; "
                    "border-top-left-radius: 5px; border-top-right-radius: 5px; "
                    "border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; "
                    "border-bottom-color: #414242; font-size: 12pt; }"
                    "QPushButton:hover { background: #D0D0D0; font-weight: bold; color: black; }"
                )

    def show_widget(self, name):
        self.stack_manager.show_widget(name)
        self.update_button_styles(next(button for button in self.navigation_buttons if button.text() == name))

    def show_widget(self, name):
        self.stack_manager.show_widget(name)
        self.update_button_styles(next(button for button in self.navigation_buttons if button.text() == name))

    def update_title_label(self):
        data = self.data_function()  # Chame a função para obter os dados
        print("Dados extraídos para o título:", data)

        tipo = data.get('Tipo', 'N/A')
        numero_contrato = data.get('Contrato/Ata', 'N/A')
        objeto = data.get('Objeto', 'N/A')
        uasg = data.get('uasg', 'N/A')

        html_text = (
            f"{tipo} {numero_contrato} - {objeto}<br>"
        )

        if not hasattr(self, 'titleLabel'):
            self.titleLabel = QLabel()
            self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
            self.titleLabel.setStyleSheet("font-size: 26px; font-weight: bold;")

        self.titleLabel.setText(html_text)
        print("Título atualizado:", html_text)  # Adicionado print para depuração

        if not hasattr(self, 'header_layout'):
            self.header_layout = QHBoxLayout()

            self.header_layout.addWidget(self.titleLabel)
            self.header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            self.add_action_buttons(self.header_layout)

            header_widget = QWidget()
            header_widget.setLayout(self.header_layout)
            header_widget.setFixedHeight(55)
            self.header_widget = header_widget

        return self.header_widget

    def extract_registro_data(self):
        # Extrai os dados do DataFrame da linha selecionada
        data = self.df_registro_selecionado.iloc[0].to_dict()
        print("Dados extraídos do DataFrame:", data)  # Adicionado print para depuração
        return {
            'status': data.get('status', 'N/A'),
            'dias': data.get('Dias', 'N/A'),
            'prorrogavel': data.get('Renova?', 'N/A'),
            'custeio': data.get('Custeio?', 'N/A'),
            'numero': data.get('Contrato/Ata', 'N/A'),
            'tipo': data.get('Tipo', 'N/A'),
            'id_processo': data.get('Processo', 'N/A'),
            'nome_fornecedor': data.get('Empresa', 'N/A'),            
            'objeto': data.get('Objeto', 'N/A'),
            'valor_global': data.get('Valor', 'N/A'),
            'codigo': data.get('codigo', 'N/A'),
            'processo': data.get('processo', 'N/A'),
            'cnpj_cpf_idgener': data.get('cnpj_cpf_idgener', 'N/A'),
            'natureza_continuada': data.get('natureza_continuada', 'N/A'),
            'nome_resumido': data.get('nome_resumido', 'N/A'),
            'indicativo_om': data.get('indicativo_om', 'N/A'),
            'nome': data.get('nome', 'N/A'),
            'material_servico': data.get('material_servico', 'N/A'),
            'link_pncp': data.get('link_pncp', 'N/A'),
            'portaria': data.get('portaria', 'N/A'),
            'posto_gestor': data.get('posto_gestor', 'N/A'),
            'gestor': data.get('gestor', 'N/A'),
            'posto_fiscal': data.get('posto_fiscal', 'N/A'),
            'fiscal': data.get('fiscal', 'N/A'),
            'posto_fiscal_substituto': data.get('posto_fiscal_substituto', 'N/A'),
            'fiscal_substituto': data.get('fiscal_substituto', 'N/A'),
            'posto_fiscal_administrativo': data.get('posto_fiscal_administrativo', 'N/A'),
            'fiscal_administrativo': data.get('fiscal_administrativo', 'N/A'),
            'vigencia_inicial': data.get('vigencia_inicial', 'N/A'),
            'vigencia_final': data.get('vigencia_final', 'N/A'),
            'setor': data.get('setor', 'N/A'),
            'cp': data.get('cp', 'N/A'),
            'msg': data.get('msg', 'N/A'),
            'comentarios': data.get('comentarios', 'N/A'),
            'termo_aditivo': data.get('termo_aditivo', 'N/A'),
            'atualizacao_comprasnet': data.get('atualizacao_comprasnet', 'N/A'),
            'instancia_governanca': data.get('instancia_governanca', 'N/A'),
            'comprasnet_contratos': data.get('comprasnet_contratos', 'N/A'),
            'registro_status': data.get('registro_status', 'N/A')
        }

    def pagina_anterior(self):
        # Lógica para ir para a página anterior
        pass

    def pagina_proxima(self):
        # Lógica para ir para a próxima página
        pass

    def update_title_label_text(self, new_title):
        data = self.extract_registro_data()
        html_text = (
            f"{data['tipo']} {data['numero']} - {data['objeto']}<br>"
            f"<span style='font-size: 18px; color: #ADD8E6;'>(UASG: {data['uasg']})</span>"
        )
        self.titleLabel.setText(html_text)
        print(f"Título atualizado Novo: {html_text}")  # Adicionado print para depuração
    
    def add_action_buttons(self, layout):
        icon_confirm = QIcon(str(self.icons_dir / "confirm.png"))
        icon_x = QIcon(str(self.icons_dir / "cancel.png"))
        
        button_confirm = self.create_button(" Salvar", icon_confirm, self.save_changes, "Salvar dados", QSize(110, 40), QSize(40, 40))
        button_x = self.create_button(" Cancelar", icon_x, self.reject, "Cancelar alterações e fechar", QSize(110, 40), QSize(35, 35))
                
        layout.addWidget(button_confirm)
        layout.addWidget(button_x)

    def create_button(self, text="", icon=None, callback=None, tooltip_text="", button_size=None, icon_size=None):
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

    def setupLayout(self):
        # Configuração do layout do diálogo
        layout = QVBoxLayout()
        layout.addWidget(self.header_widget)
        layout.addWidget(self.tipoContratoRadio)
        self.setLayout(layout)

    def save_changes(self):
        try:
            # Verifique se o combo box de status foi criado e está acessível
            if hasattr(self.stack_manager, 'status_combo_box') and self.stack_manager.status_combo_box is not None:
                status_value = self.stack_manager.status_combo_box.currentText().strip()
            else:
                status_value = self.data_function().get('status', 'Seção de Contratos')  # Usar o valor da função

            # Coletar comentários reais
            if hasattr(self.stack_manager, 'comments_view') and self.stack_manager.comments_view is not None:
                comments = [self.stack_manager.comments_view.item(i).text() for i in range(self.stack_manager.comments_view.count())]
                comments_text = "\n".join(comments)
            else:
                comments_text = self.data_function().get('comentarios', '')

            # Coletar registros reais
            if hasattr(self.stack_manager, 'records_view') and self.stack_manager.records_view is not None:
                registro_texto = [self.stack_manager.records_view.item(i).text() for i in range(self.stack_manager.records_view.count())]
                registro_texto = "\n".join(registro_texto)
            else:
                registro_texto = self.data_function().get('registro_status', '')

            data = {
                'status': status_value,
                'prorrogavel': 'Sim' if self.stack_manager.pode_renovar_buttons['Sim'].isChecked() else 'Não',
                'custeio': 'Sim' if self.stack_manager.custeio_buttons['Sim'].isChecked() else 'Não',
                'numero': self.stack_manager.line_edits['numero'].text(),
                'tipo': self.stack_manager.contrato_ata_combo_box.currentText(),
                'id_processo': self.stack_manager.line_edits["id_processo"].text().strip(),
                'nome_fornecedor': self.stack_manager.line_edits["nome_fornecedor"].text().strip(),
                'objeto': self.stack_manager.line_edits["objeto"].text().strip(),
                'valor_global': self.stack_manager.line_edits["valor_global"].text().strip(),
                'codigo': self.stack_manager.line_edit_uasg.text().strip(),  # Usa o valor do campo de texto UASG
                'processo': self.stack_manager.line_edits["processo"].text().strip(),
                'cnpj_cpf_idgener': self.stack_manager.line_edits["cnpj_cpf_idgener"].text().strip(),
                'natureza_continuada': 'Sim' if self.stack_manager.natureza_continuada_buttons['Sim'].isChecked() else 'Não',
                'nome_resumido': self.stack_manager.combo_sigla_om.currentText().strip(),  # Usa o valor selecionado do combo box Sigla OM
                'indicativo_om': self.stack_manager.line_edit_indicativo.text().strip(),  # Corrigido
                'nome': self.stack_manager.line_edit_orgao.text().strip(),  # Corrigido
                'material_servico': 'Material' if self.stack_manager.material_servico_buttons['Material'].isChecked() else 'Serviço',
                'link_pncp': self._get_valid_value('link_pncp'),
                'portaria': self._get_valid_value('portaria'),
                'posto_gestor': self._get_valid_value('posto_gestor'),
                'gestor': self._get_valid_value('gestor'),
                'posto_gestor_substituto': self._get_valid_value('posto_gestor_substituto'),
                'gestor_substituto': self._get_valid_value('gestor_substituto'),
                'posto_fiscal': self._get_valid_value('posto_fiscal'),
                'fiscal': self._get_valid_value('fiscal'),
                'posto_fiscal_substituto': self._get_valid_value('posto_fiscal_substituto'),
                'fiscal_substituto': self._get_valid_value('fiscal_substituto'),
                'posto_fiscal_administrativo': self._get_valid_value('posto_fiscal_administrativo'),
                'fiscal_administrativo': self._get_valid_value('fiscal_administrativo'),
                'vigencia_inicial': self.stack_manager.date_edit_inicial.date().toString('dd/MM/yyyy'),
                'vigencia_final': self.stack_manager.date_edit_final.date().toString('dd/MM/yyyy'),
                'setor': self._get_valid_value('setor'),
                'cp': self._get_valid_value('cp'),
                'msg': self._get_valid_value('msg'),
                'comentarios': comments_text,  # Salva os comentários reais coletados
                'termo_aditivo': self._get_valid_value('termo_aditivo'),
                'atualizacao_comprasnet': self._get_valid_value('atualizacao_comprasnet'),
                'instancia_governanca': self._get_valid_value('instancia_governanca'),
                'comprasnet_contratos': self._get_valid_value('comprasnet_contratos'),
                'assinatura_contrato': None,
                'registro_status': registro_texto
            }
            # Obtém o valor da chave primária 'id' do registro que está sendo editado
            record_id = self.df_registro_selecionado.iloc[0]['id']

            if self.model:
                # Atualize o registro no banco de dados com base na chave primária 'id'
                if not self.model.update_record_by_primary_key('id', record_id, data):
                    QMessageBox.critical(self, "Erro", "Falha ao atualizar o registro no banco de dados.")
            else:
                QMessageBox.critical(self, "Erro", "Modelo de dados não está disponível para atualização.")
                return

            self.dadosContratosSalvos.emit()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao salvar as alterações: {str(e)}")

    def _get_valid_value(self, key):
        """Retorna o valor válido do campo ou o valor existente no DataFrame."""
        if key in self.stack_manager.line_edits:
            new_value = self.stack_manager.line_edits[key].text().strip()
            if new_value == '':
                return self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], key]
            return new_value
        else:
            # Se a chave não existe em line_edits, retorna o valor do DataFrame
            return self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], key]


    def save_comments(self):
        comments = [self.comments_view.item(i).text() for i in range(self.comments_view.count())]
        comments_text = "\n".join(comments)
        print("Comentários salvos:", comments_text)
        # Agora você pode salvar os comentários no banco de dados ou onde for necessário

    def save_records(self):
        records = [self.records_view.item(i).text() for i in range(self.records_view.count())]
        records_text = "\n".join(records)
        # Implemente a lógica para salvar os registros (por exemplo, salvar no banco de dados ou em um arquivo)
        print("Registros salvos:", records_text)

    def apply_widget_style(self, widget):
        widget.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px;")

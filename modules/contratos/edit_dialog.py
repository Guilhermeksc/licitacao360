## modules/contratos/edit_dialog.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
import sqlite3
from diretorios import BRASIL_IMAGE_PATH, ICONS_DIR
import pandas as pd
from modules.contratos.utils import WidgetHelper
from datetime import datetime
class StackWidgetManager:
    def __init__(self, parent, data_function):
        self.parent = parent
        self.data_function = data_function
        self.icons_dir = Path(ICONS_DIR)
        self.stacked_widget = QStackedWidget(parent)
        self.stacked_widget.setStyleSheet(
            "QStackedWidget {"
            "border: 1px solid #414242; border-radius: 5px; "
            "border-bottom-left-radius: 5px; border-bottom-right-radius: 5px; }"
        )
        self.widgets = {}
        self.widget_creators = {
            "Informações Gerais": self.create_widget_informacoes_gerais,
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
        h_layout = QHBoxLayout(widget)  # Criar um QHBoxLayout
        h_layout.setContentsMargins(0, 0, 0, 0)  # Definir margens para 0
        h_layout.setSpacing(0)  # Definir espaçamento entre os contêineres para 0

        # Widgets de contêiner para layouts esquerdo e direito
        left_container = QWidget()
        right_container = QWidget()

        # Layout esquerdo
        left_layout = QVBoxLayout(left_container)

        id_processo_layout, self.line_edits['id_processo'] = WidgetHelper.create_line_edit("ID Processo:", data.get('id_processo', ''))
        # Criar combobox para contrato_ata
        contrato_ata_options = [
            "Contrato", "Ata"
        ]
        contrato_ata_options, self.contrato_ata_combo_box = WidgetHelper.create_combo_box("Contrato/Ata:", contrato_ata_options, data.get('tipo'))
        numero_contrato_layout, self.line_edits['numero_contrato'] = WidgetHelper.create_line_edit("Número:", data.get('numero_contrato', ''))
        nup_layout, self.line_edits['nup'] = WidgetHelper.create_line_edit("NUP:", data.get('nup', ''))
        valor_global_layout, self.line_edits['valor_global'] = WidgetHelper.create_line_edit("Valor Global:", data.get('valor_global', ''))
        cnpj_layout, self.line_edits['cnpj'] = WidgetHelper.create_line_edit("CNPJ:", data.get('cnpj', ''))
        fornecedor_layout, self.line_edits['empresa'] = WidgetHelper.create_line_edit("Empresa:", data.get('empresa', ''))
        objeto_layout, self.line_edits['objeto'] = WidgetHelper.create_line_edit("Objeto:", data.get('objeto', ''))

        left_layout.addLayout(id_processo_layout)
        left_layout.addLayout(contrato_ata_options)
        left_layout.addLayout(numero_contrato_layout)
        left_layout.addLayout(nup_layout)
        left_layout.addLayout(valor_global_layout)
        left_layout.addLayout(cnpj_layout)
        left_layout.addLayout(fornecedor_layout)
        left_layout.addLayout(objeto_layout)

        # Pode Renovar
        pode_renovar_layout, self.pode_renovar_buttons, self.pode_renovar_group = WidgetHelper.create_radio_buttons("Pode Renovar?", ["Sim", "Não"])
        pode_renovar_value = data.get('Renova?', 'Sim')
        self.pode_renovar_buttons[pode_renovar_value].setChecked(True)
        left_layout.addLayout(pode_renovar_layout)

        # Custeio
        custeio_layout, self.custeio_buttons, self.custeio_group = WidgetHelper.create_radio_buttons("Custeio?", ["Sim", "Não"])
        custeio_value = data.get('Custeio?', 'Sim')
        self.custeio_buttons[custeio_value].setChecked(True)
        left_layout.addLayout(custeio_layout)

        # Natureza Continuada
        natureza_continuada_layout, self.natureza_continuada_buttons, self.natureza_continuada_group = WidgetHelper.create_radio_buttons("Natureza Continuada?", ["Sim", "Não"])

        # Obtém o valor de 'natureza_continuada' e define um valor padrão se estiver vazio ou inválido
        natureza_continuada_value = data.get('natureza_continuada', '').strip()
        if natureza_continuada_value not in self.natureza_continuada_buttons:
            natureza_continuada_value = 'Não'  # Valor padrão

        self.natureza_continuada_buttons[natureza_continuada_value].setChecked(True)
        left_layout.addLayout(natureza_continuada_layout)


        # Material/Serviço (Verificação adicional)
        material_servico_layout, self.material_servico_buttons, self.material_servico_group = WidgetHelper.create_radio_buttons("Material/Serviço:", ["Material", "Serviço"])
        material_servico_value = data.get('material_servico', 'Material')
        if material_servico_value not in self.material_servico_buttons:
            material_servico_value = 'Material'  # Define 'Material' como valor padrão

        self.material_servico_buttons[material_servico_value].setChecked(True)
        left_layout.addLayout(material_servico_layout)

        # Layout direito
        right_layout = QVBoxLayout(right_container)
        inicial_layout, self.date_edit_inicial = WidgetHelper.create_date_edit("Início da Vigência:", data.get('vigencia_inicial', None))
        final_layout, self.date_edit_final = WidgetHelper.create_date_edit("Final da Vigência:", data.get('vigencia_final', None))

        # Adicionar os QLabels para om, indicativo_om e om_extenso
        om_label = QLabel(f"OM: {data.get('om', 'N/A')}")
        indicativo_om_label = QLabel(f"Indicativo OM: {data.get('indicativo_om', 'N/A')}")
        om_extenso_label = QLabel(f"OM Extenso: {data.get('om_extenso', 'N/A')}")

        right_layout.addLayout(inicial_layout)
        right_layout.addLayout(final_layout)

        # Adiciona os labels no layout direito
        right_layout.addWidget(om_label)
        right_layout.addWidget(indicativo_om_label)
        right_layout.addWidget(om_extenso_label)

        # Adicionar linha central
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setFixedWidth(1)  # Definir a largura da linha

        # Adicionar os contêineres ao QHBoxLayout com políticas de redimensionamento
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        right_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        h_layout.addWidget(left_container)
        h_layout.addWidget(line)
        h_layout.addWidget(right_container)

        self.add_widget("Informações Gerais", widget)
        
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

        layout.addWidget(add_button_registrar_comentario)
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

    def __init__(self, icons_dir, df_registro_selecionado, table_view, model, indice_linha, parent=None):
        super().__init__(parent)
        self.df_registro_selecionado = df_registro_selecionado
        self.table_view = table_view
        self.model = model
        self.indice_linha = indice_linha
        self.icons_dir = Path(icons_dir)
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("Atualizar Dados do Contrato")
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout(self)

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
        self.add_navigation_button(nav_layout, "Informações Gerais", lambda: self.show_widget("Informações Gerais"))
        self.add_navigation_button(nav_layout, "Termo Aditivo", lambda: self.show_widget("Termo Aditivo"))
        self.add_navigation_button(nav_layout, "Gestão/Fiscalização", lambda: self.show_widget("Gestão/Fiscalização"))
        self.add_navigation_button(nav_layout, "Status", lambda: self.show_widget("Status"))
        nav_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)) 
        content_layout.addLayout(nav_layout)

        self.stack_manager = StackWidgetManager(self, self.extract_registro_data)

        content_layout.addWidget(self.stack_manager.get_widget())

        self.show_widget("Informações Gerais")

        h_layout.addLayout(content_layout)

        # Criar o QTreeView personalizado
        self.tree_view = QTreeView()
        self.tree_model = QStandardItemModel()
        self.tree_view.setModel(self.tree_model)
        self.populate_tree_view()
        h_layout.addWidget(self.tree_view)

        main_layout.addLayout(h_layout)
        self.setLayout(main_layout)

    def populate_tree_view(self):
        data = self.extract_registro_data()
        tipo = data.get('tipo', 'Tipo Desconhecido')
        print(f"Tipo extraído: {tipo}")  # Adicionado para depuração

        root = QStandardItem(tipo)

        children = {
            'Valor Global': data.get('valor_global', 'N/A'),
            'Link PNCP': data.get('link_pncp', 'N/A'),
            'Portaria': data.get('portaria', 'N/A'),
            'Vigência Inicial': data.get('vigencia_inicial', 'N/A'),
            'Vigência Final': data.get('vigencia_final', 'N/A'),
            'Número Contrato': data.get('numero_contrato', 'N/A')
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
        data = self.extract_registro_data()
        print("Dados extraídos para o título:", data)  # Adicionado print para depuração
        html_text = (
            f"{data['tipo']} {data['numero_contrato']} - {data['objeto']}<br>"
            f"<span style='font-size: 18px; '>(UASG: {data['uasg']})</span>"
        )
        if not hasattr(self, 'titleLabel'):
            self.titleLabel = QLabel()
            self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
            self.titleLabel.setStyleSheet("font-size: 26px; font-weight: bold;")

        self.titleLabel.setText(html_text)
        print("Título atualizado:", html_text)  # Adicionado print para depuração

        if not hasattr(self, 'header_layout'):
            self.header_layout = QHBoxLayout()

            # Botão Anterior
            icon_anterior = QIcon(str(self.icons_dir / "anterior.png"))
            btn_anterior = self.create_button(
                "Anterior", 
                icon_anterior, 
                self.pagina_anterior, 
                "Clique para navegar para a página anterior",
                QSize(100, 40), QSize(30, 30)
            )
            self.header_layout.addWidget(btn_anterior)

            self.header_layout.addWidget(self.titleLabel)
            self.header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            self.add_action_buttons(self.header_layout)

            # Botão Próximo
            icon_proximo = QIcon(str(self.icons_dir / "proximo.png"))
            btn_proximo = self.create_button(
                "Próximo", 
                icon_proximo, 
                self.pagina_proxima, 
                "Clique para navegar para a página próxima",
                QSize(100, 40), QSize(30, 30)
            )
            self.header_layout.addWidget(btn_proximo)

            header_widget = QWidget()
            header_widget.setLayout(self.header_layout)
            header_widget.setFixedHeight(80)
            self.header_widget = header_widget

        return self.header_widget

    def extract_registro_data(self):
        # Extrai os dados do DataFrame da linha selecionada
        data = self.df_registro_selecionado.iloc[0].to_dict()
        print("Dados extraídos do DataFrame:", data)  # Adicionado print para depuração
        return {
            'status': data.get('status', 'N/A'),
            'dias': data.get('Dias', 'N/A'),
            'pode_renovar': data.get('Renova?', 'N/A'),
            'custeio': data.get('Custeio?', 'N/A'),
            'numero_contrato': data.get('Contrato/Ata', 'N/A'),
            'tipo': data.get('Tipo', 'N/A'),
            'id_processo': data.get('Processo', 'N/A'),
            'empresa': data.get('Empresa', 'N/A'),            
            'objeto': data.get('Objeto', 'N/A'),
            'valor_global': data.get('Valor', 'N/A'),
            'uasg': data.get('uasg', 'N/A'),
            'nup': data.get('nup', 'N/A'),
            'cnpj': data.get('cnpj', 'N/A'),
            'natureza_continuada': data.get('natureza_continuada', 'N/A'),
            'om': data.get('om', 'N/A'),
            'indicativo_om': data.get('indicativo_om', 'N/A'),
            'om_extenso': data.get('om_extenso', 'N/A'),
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
            f"{data['tipo']} {data['numero_contrato']} - {data['objeto']}<br>"
            f"<span style='font-size: 18px; color: #ADD8E6;'>(UASG: {data['uasg']})</span>"
        )
        self.titleLabel.setText(html_text)
        print(f"Título atualizado: {html_text}")  # Adicionado print para depuração
    
    def add_action_buttons(self, layout):
        icon_confirm = QIcon(str(self.icons_dir / "confirm.png"))
        icon_x = QIcon(str(self.icons_dir / "cancel.png"))
        
        button_confirm = self.create_button(" Salvar", icon_confirm, self.save_changes, "Salvar dados", QSize(110, 50), QSize(40, 40))
        button_x = self.create_button(" Cancelar", icon_x, self.reject, "Cancelar alterações e fechar", QSize(110, 50), QSize(30, 30))
                
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
                # Se o status_combo_box não estiver disponível, mantenha o valor atual do database
                status_value = self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], 'status']
                if not status_value or status_value.strip() == "":
                    status_value = "Seção de Contratos"  # Valor padrão

            # Coletar comentários reais
            if hasattr(self.stack_manager, 'comments_view') and self.stack_manager.comments_view is not None:
                comments = [self.stack_manager.comments_view.item(i).text() for i in range(self.stack_manager.comments_view.count())]
                comments_text = "\n".join(comments)
            else:
                comments_text = self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], 'comentarios'] or ""

            # Coletar registros reais
            if hasattr(self.stack_manager, 'records_view') and self.stack_manager.records_view is not None:
                registro_texto = [self.stack_manager.records_view.item(i).text() for i in range(self.stack_manager.records_view.count())]
                registro_texto = "\n".join(registro_texto)
            else:
                registro_texto = self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], 'registro_status'] or ""

            
            data = {
                'status': status_value,
                'pode_renovar': 'Sim' if self.stack_manager.pode_renovar_buttons['Sim'].isChecked() else 'Não',
                'custeio': 'Sim' if self.stack_manager.custeio_buttons['Sim'].isChecked() else 'Não',
                'numero_contrato': self.stack_manager.line_edits['numero_contrato'].text(),
                'tipo': self.stack_manager.contrato_ata_combo_box.currentText(),
                'id_processo': self.stack_manager.line_edits["id_processo"].text().strip(),
                'empresa': self.stack_manager.line_edits["empresa"].text().strip(),
                'objeto': self.stack_manager.line_edits["objeto"].text().strip(),
                'valor_global': self.stack_manager.line_edits["valor_global"].text().strip(),
                'uasg': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'nup': self.stack_manager.line_edits["nup"].text().strip(),
                'cnpj': self.stack_manager.line_edits["cnpj"].text().strip(),
                'natureza_continuada': 'Sim' if self.stack_manager.natureza_continuada_buttons['Sim'].isChecked() else 'Não',
                'om': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'material_servico': 'Material' if self.stack_manager.material_servico_buttons['Material'].isChecked() else 'Serviço',
                'link_pncp': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'portaria': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'posto_gestor': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'gestor': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'posto_gestor_substituto': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'gestor_substituto': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'posto_fiscal': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'fiscal': 'Rodolfo',  # Exemplo de valor fixo, ajuste conforme necessário
                'posto_fiscal_substituto': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'fiscal_substituto': 'Vicenti',  # Exemplo de valor fixo, ajuste conforme necessário
                'posto_fiscal_administrativo': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'fiscal_administrativo': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'vigencia_inicial': self.stack_manager.date_edit_inicial.date().toString('dd/MM/yyyy'),
                'vigencia_final': self.stack_manager.date_edit_final.date().toString('dd/MM/yyyy'),
                'setor': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'cp': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'msg': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'comentarios': comments_text,  # Salva os comentários reais coletados
                'termo_aditivo': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'atualizacao_comprasnet': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'instancia_governanca': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'comprasnet_contratos': '',  # Exemplo de valor fixo, ajuste conforme necessário
                'assinatura_contrato': None,
                'registro_status': registro_texto
            }

            # Atualizar o DataFrame com os novos valores
            for key, value in data.items():
                self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], key] = value

            # Atualizar o modelo diretamente
            self.model.update_record(self.indice_linha, data)

            self.dadosContratosSalvos.emit()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao salvar as alterações: {str(e)}")

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

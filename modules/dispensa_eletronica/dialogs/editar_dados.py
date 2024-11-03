from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal, Qt
from modules.utils.add_button import add_button
from modules.dispensa_eletronica.dialogs.widget.info import InfoWidget
from modules.dispensa_eletronica.dialogs.widget.responsavel import SetorResponsavelWidget
from modules.dispensa_eletronica.dialogs.widget.documentos import DocumentosWidget
import pandas as pd
import sqlite3
from pathlib import Path    
from diretorios import load_config, CONTROLE_DADOS
from modules.planejamento.utilidades_planejamento import DatabaseManager

class EditDataDialog(QDialog):
    dados_atualizados = pyqtSignal()  # Sinal para indicar que os dados foram atualizados
    salvar_dados = pyqtSignal()

    def __init__(self, registro_selecionado, icons, parent=None):
        super().__init__(parent)
        self.icons = icons
        self.setWindowTitle("Editar Dados")
        self.setWindowIcon(self.icons.get("edit", None))
        self.setFixedSize(1250, 720)
        
        # Caminho do banco de dados e inicialização do gerenciador
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        
        # Recebe o registro selecionado e configura o layout
        self.registro_selecionado = registro_selecionado
        self.navigation_buttons = []

        # Configuração do layout principal
        self.init_ui()

    def init_ui(self):
        # Layout principal vertical para os componentes existentes
        layout_principal = QVBoxLayout()

        # Adicionando título e navegação
        layout_principal.addWidget(self.update_title_label())
        layout_principal.addLayout(self.create_navigation_layout())

        layout_principal.setSpacing(0)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        # Gerenciador de Stacked Widgets e Configuração
        self.stack_manager = QStackedWidget(self)
        self.setup_stacked_widgets()
        layout_principal.addWidget(self.stack_manager)

        # Cria o layout de agentes responsáveis e aplica borda lateral
        layout_agentes_responsaveis = self.create_agentes_responsaveis_layout()

        # Layout horizontal principal para conter ambos os layouts
        hlayout_main = QHBoxLayout()  # Não passe `self` aqui
        hlayout_main.addLayout(layout_principal)  # Adiciona o layout principal à esquerda
        hlayout_main.addWidget(layout_agentes_responsaveis)  # Adiciona o layout de agentes à direita

        # Define o layout principal como o layout horizontal
        self.setLayout(hlayout_main)

        # Mostra o widget inicial
        self.show_widget("Informações")

    def create_agentes_responsaveis_layout(self):
        # Frame para agentes responsáveis com borda lateral
        frame_agentes = QFrame()
        # Criação do layout principal para os agentes responsáveis
        agente_responsavel_layout = QVBoxLayout(frame_agentes)
        agente_responsavel_layout.setContentsMargins(10, 1, 10, 1)  # Define margens ao redor do layout

        # Criação dos ComboBox com ajuste de altura
        self.ordenador_combo = self.create_combo_box('', [], 260, 70)
        self.agente_fiscal_combo = self.create_combo_box('', [], 260, 70)
        self.gerente_credito_combo = self.create_combo_box('', [], 260, 65)
        self.responsavel_demanda_combo = self.create_combo_box('', [], 260, 65)
        self.operador_dispensa_combo = self.create_combo_box('', [], 260, 70)

        # Adicionando labels e ComboBox diretamente ao layout
        labels_combos = [
            ("Ordenador de Despesa:", self.ordenador_combo),
            ("Agente Fiscal:", self.agente_fiscal_combo),
            ("Gerente de Crédito:", self.gerente_credito_combo),
            ("Responsável pela Demanda:", self.responsavel_demanda_combo),
            ("Operador da Contratação:", self.operador_dispensa_combo)
        ]

        for label_text, combo_box in labels_combos:
            # Cria um layout vertical para a label e o ComboBox
            v_layout = QVBoxLayout()
            v_layout.setSpacing(0)  # Ajusta o espaçamento entre label e ComboBox
            v_layout.setContentsMargins(0, 0, 0, 0)  # Margens para o layout

            # Cria e estiliza a label
            label = QLabel(label_text)
            label.setStyleSheet("color: #8AB4F7; font-size: 16px")
            label.setContentsMargins(0, 0, 0, 0)  # Define margens para a label

            # Adiciona a label e o ComboBox ao layout vertical
            v_layout.addWidget(label)
            v_layout.addWidget(combo_box)

            # Adiciona o layout vertical ao layout principal
            agente_responsavel_layout.addLayout(v_layout)

        # Carrega os agentes responsáveis para popular os ComboBoxes com valores de teste
        self.carregarAgentesResponsaveis()

        return frame_agentes

    def create_combo_box(self, placeholder, items, width, height):
        combo_box = QComboBox()
        combo_box.setEditable(True)
        combo_box.setPlaceholderText(placeholder)
        combo_box.addItems(items)
        combo_box.setFixedWidth(width)
        combo_box.setFixedHeight(height)
        return combo_box

    def carregarAgentesResponsaveis(self):
        try:
            print("Tentando conectar ao banco de dados...")
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Verificar se a tabela existe
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_agentes_responsaveis'")
                if cursor.fetchone() is None:
                    raise Exception("A tabela 'controle_agentes_responsaveis' não existe no banco de dados. Configure os Ordenadores de Despesa no Módulo 'Configurações'.")

                print("Tabela 'controle_agentes_responsaveis' encontrada. Carregando dados...")
                
                # Carregar dados para cada ComboBox com base na função específica
                self.carregarDadosCombo(conn, cursor, "Ordenador de Despesa%", self.ordenador_combo)
                self.carregarDadosCombo(conn, cursor, "Agente Fiscal%", self.agente_fiscal_combo)
                self.carregarDadosCombo(conn, cursor, "Gerente de Crédito%", self.gerente_credito_combo)
                self.carregarDadosCombo(conn, cursor, "Operador%", self.operador_dispensa_combo)
                self.carregarDadosCombo(conn, cursor, "NOT LIKE", self.responsavel_demanda_combo)
                
                # Preencher comboboxes com os valores de `registro_selecionado` se disponíveis
                self.preencher_campos()

        except Exception as e:
            print(f"Erro ao carregar Ordenadores de Despesas: {e}")

    def carregarDadosCombo(self, conn, cursor, funcao_like, combo_widget):
        """
        Função para carregar dados no combobox baseado na função especificada.
        """
        if "NOT LIKE" in funcao_like:
            sql_query = """
                SELECT nome, posto, funcao FROM controle_agentes_responsaveis
                WHERE funcao NOT LIKE 'Ordenador de Despesa%' AND
                    funcao NOT LIKE 'Agente Fiscal%' AND
                    funcao NOT LIKE 'Gerente de Crédito%' AND
                    funcao NOT LIKE 'Operador%'
            """
        else:
            sql_query = f"SELECT nome, posto, funcao FROM controle_agentes_responsaveis WHERE funcao LIKE '{funcao_like}'"
        
        agentes_df = pd.read_sql_query(sql_query, conn)
        combo_widget.clear()
        for index, row in agentes_df.iterrows():
            texto_display = f"{row['nome']}\n{row['posto']}\n{row['funcao']}"
            combo_widget.addItem(texto_display, userData=row.to_dict())

    def preencher_campos(self):
        """
        Função para preencher os campos do diálogo com os dados do registro selecionado.
        """
        try:
            self.ordenador_combo.setCurrentText(str(self.registro_selecionado.get('ordenador_despesas', '')))
            self.agente_fiscal_combo.setCurrentText(str(self.registro_selecionado.get('agente_fiscal', '')))
            self.gerente_credito_combo.setCurrentText(str(self.registro_selecionado.get('gerente_de_credito', '')))
            self.responsavel_demanda_combo.setCurrentText(str(self.registro_selecionado.get('responsavel_pela_demanda', '')))
            self.operador_dispensa_combo.setCurrentText(str(self.registro_selecionado.get('operador', '')))        

        except KeyError as e:
            print(f"Erro ao preencher campos: {str(e)}")

    def update_title_label(self):
        title_label = QLabel("Editar Dados")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        return title_label

    def create_navigation_layout(self):
        nav_layout = QHBoxLayout()

        nav_layout.setSpacing(0)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        
        # Obtenha o ícone "brasil_icon" do dicionário icons
        brasil_icon = self.icons.get("brasil_2")
        
        # Cria um QLabel e adiciona o ícone como um QPixmap
        image_label_esquerda = QLabel()
        image_label_esquerda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Define o pixmap se o ícone foi encontrado
        if brasil_icon:
            image_label_esquerda.setPixmap(brasil_icon.pixmap(30, 30))
        else:
            print("Aviso: Ícone 'brasil_icon' não encontrado.")
        
        nav_layout.addWidget(image_label_esquerda)

        # Lista de botões de navegação
        buttons = [
            ("Informações", "Informações"),
            ("Setor Responsável", "Setor Responsável"),
            ("Documentos", "Documentos"),
            ("Anexos", "Anexos"),
            ("PNCP", "PNCP"),
        ]

        for text, name in buttons:
            self.add_navigation_button(nav_layout, text, lambda _, n=name: self.show_widget(n))

        nav_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        add_button("Salvar", "confirm", self.salvar_dados, nav_layout, self.icons, tooltip="Salvar os dados")
        nav_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        return nav_layout

    def show_widget(self, name):
        # Desmarcar todos os botões de navegação
        for button in self.navigation_buttons:
            button.setChecked(False)
        # Encontrar o botão correspondente e marcar
        for button in self.navigation_buttons:
            if button.text() == name:
                button.setChecked(True)
                self.update_button_styles(button)
                break
        # Mostrar o widget correspondente no QStackedWidget
        for i in range(self.stack_manager.count()):
            widget = self.stack_manager.widget(i)
            if widget.objectName() == name:
                self.stack_manager.setCurrentWidget(widget)
                break

    def add_navigation_button(self, layout, text, callback):
        button = QPushButton(text)
        button.setCheckable(True)
        button.setMinimumWidth(150)
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

    def setup_stacked_widgets(self):
        data = self.registro_selecionado

        # Configura os widgets com as novas classes
        widgets = {
            "Informações": self.stacked_widget_info(data),
            "Setor Responsável": self.stacked_widget_responsaveis(data),
            "Documentos": self.stacked_widget_responsaveis(data),
            "Anexos": self.stacked_widget_responsaveis(data),
            "PNCP": self.stacked_widget_responsaveis(data),
        }

        for name, widget in widgets.items():
            self.stack_manager.addWidget(widget)
            widget.setObjectName(name)

    def stacked_widget_responsaveis(self, data):
        # Cria um widget básico para o stack
        frame = QFrame()
        layout = QVBoxLayout()

        # Layout horizontal para agrupar os QGroupBox
        hbox_top_layout = QHBoxLayout()

        # Cria e adiciona o QGroupBox "Contratação" ao layout horizontal
        contratacao_group_box = self.create_contratacao_group(data)
        hbox_top_layout.addWidget(contratacao_group_box)

        # Adiciona o layout horizontal ao layout principal
        layout.addLayout(hbox_top_layout)
        frame.setLayout(layout)

        return frame
    
    def stacked_widget_info(self, data):
        # Cria um widget básico para o stack
        frame = QFrame()
        layout = QVBoxLayout()

        # Layout horizontal para agrupar os QGroupBox
        hbox_top_layout = QHBoxLayout()

        # Cria e adiciona o QGroupBox "Contratação" ao layout horizontal
        contratacao_group_box = self.create_contratacao_group(data)
        hbox_top_layout.addWidget(contratacao_group_box)

        # Cria um layout vertical para "Classificação Orçamentária" e "Formulário"
        layout_orcamentario_formulario = QVBoxLayout()

        # Cria e adiciona o QGroupBox "Classificação Orçamentária" ao layout vertical
        classificacao_orcamentaria_group_box = self.create_classificacao_orcamentaria_group()
        layout_orcamentario_formulario.addWidget(classificacao_orcamentaria_group_box)

        # Cria o "Formulário de Dados" e adiciona ao layout vertical
        formulario_group_box = self.create_frame_formulario_group(data)
        layout_orcamentario_formulario.addWidget(formulario_group_box)

        # Adiciona o layout vertical ao layout horizontal
        hbox_top_layout.addLayout(layout_orcamentario_formulario)

        # Adiciona o layout horizontal ao layout principal
        layout.addLayout(hbox_top_layout)
        frame.setLayout(layout)

        return frame

    def create_contratacao_group(self, data):
        group_box = QGroupBox("Contratação")
        layout = QVBoxLayout()

        # Adiciona widgets que utilizam `data`
        info_label = QLabel(f"ID Processo: {data[0]}")  # Exemplo de uso dos dados
        layout.addWidget(info_label)

        group_box.setLayout(layout)
        return group_box

    def create_classificacao_orcamentaria_group(self):
        group_box = QGroupBox("Classificação Orçamentária")
        layout = QVBoxLayout()

        # Adicione os campos específicos necessários
        layout.addWidget(QLabel("Orçamento: Preencha os detalhes aqui"))
        group_box.setLayout(layout)
        return group_box

    def create_frame_formulario_group(self, data):
        group_box = QGroupBox("Formulário de Dados")
        layout = QVBoxLayout()

        # Adiciona campos de formulário usando `data` conforme necessário
        campo1 = QLabel(f"Objeto: {data[1]}")
        layout.addWidget(campo1)

        group_box.setLayout(layout)
        return group_box


    def save_data(self):
        """Salva os dados editados e emite o sinal de atualização."""
        # Obtém os novos valores dos campos
        new_values = [field.text() for field in self.fields.values()]
        
        # Validação dos dados antes de atualizar
        if self.validate_data(new_values):
            # Atualiza os dados na linha selecionada
            self.registro_selecionado[:] = new_values
            self.dados_atualizados.emit()  # Emite o sinal para atualizar o modelo
            self.accept()  # Fecha o diálogo
        else:
            QMessageBox.warning(self, "Erro", "Verifique os valores inseridos.")

    def validate_data(self, data):
        """Valida os dados antes de salvar."""
        # Implementar regras de validação conforme necessário
        return all(data)  # Exemplo simples: verifica se todos os campos foram preenchidos

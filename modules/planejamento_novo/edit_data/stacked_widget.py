from modules.dispensa_eletronica.dados_api.api_consulta import PNCPConsultaThread, PNCPConsulta
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
from modules.planejamento.utilidades_planejamento import DatabaseManager
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
                                    EditDataDialogUtils, RealLineEdit, TextEditDelegate,
                                    create_combo_box, create_layout, create_button, 
                                    apply_widget_style_11, validate_and_convert_date)
from modules.planejamento_novo.edit_data.widgets.informacoes import create_contratacao_group
from modules.planejamento_novo.edit_data.widgets.autorizacao import AutorizacaoWidget
from modules.planejamento_novo.edit_data.widgets.setor_responsavel import create_dados_responsavel_contratacao_group
from modules.planejamento_novo.edit_data.widgets.irp import create_irp_group
from modules.planejamento_novo.edit_data.widgets.etp import create_etp_group
from modules.planejamento_novo.edit_data.widgets.mr import create_matriz_risco_group
from modules.planejamento_novo.edit_data.widgets.tr import create_tr_group
from modules.planejamento_novo.edit_data.widgets.edital import create_edital_group
from modules.planejamento_novo.edit_data.widgets.checklist import create_checklist_group
from modules.planejamento_novo.edit_data.widgets.nota_tecnica import create_nt_group
from modules.planejamento_novo.edit_data.widgets.portaria import create_portaria_layout
import pandas as pd
import sqlite3     
import logging

CONFIG_FILE = 'config.json'

def load_config_path_id():
    if not Path(CONFIG_FILE).exists():
        return {}
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)
    
class StackedWidgetManager:
    def __init__(self, parent, config_manager, df_registro_selecionado):
        self.parent = parent
        self.config_manager = config_manager
        self.df_registro_selecionado = df_registro_selecionado
        self.stack_manager = QStackedWidget(parent)
        self.config = load_config_path_id()  # Carrega a configuração aqui
        self.pasta_base = Path(self.config.get('pasta_base', str(Path.home() / 'Desktop')))  # Inicializa pasta_base
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        self.templatePathMSG = MSG_DIR_IRP / "last_template_msg_irp.txt"
        self.templatePath = PASTA_TEMPLATE
        self.setup_stacked_widgets()

    def setup_stacked_widgets(self):
        # Extrai dados do DataFrame selecionado
        data = EditDataDialogUtils.extract_registro_data(self.df_registro_selecionado)

        # Configura os widgets no StackedWidgetManager
        widgets = {
            "Informações": self.stacked_widget_info(data),
            "Documentos": self.stacked_widget_documentos(data),
            "Portaria": self.stacked_widget_portaria(data),
            "IRP": self.stacked_widget_irp(data),
            "DFD": self.stacked_widget_dfd(data),
            "ETP": self.stacked_widget_etp(data),
            "MR": self.stacked_widget_matriz_riscos(data),
            "TR": self.stacked_widget_tr(data),
            "Edital": self.stacked_widget_edital(data),
            "Check-list": self.stacked_widget_checklist(data),
            "Nota Técnica": self.stacked_widget_nt(data),
            "AGU": self.stacked_widget_nt(data),
            "PNCP": self.stacked_widget_pncp(data),
        }

        for name, widget in widgets.items():
            self.stack_manager.addWidget(widget)
            widget.setObjectName(name)

    def get_stacked_widget(self):

        return self.stack_manager       
     
    def stacked_widget_documentos(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        # Passa self.pasta_base e self.config para o widget de autorização
        autorizacao_widget = AutorizacaoWidget(data, self.templatePathMSG, self.pasta_base, self.config)
        autorizacao_group = autorizacao_widget.create_autorizacao_group()
        layout.addWidget(autorizacao_group)
        frame.setLayout(layout)
        return frame
    
    def stacked_widget_nt(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        nt_group = create_nt_group(data, self.templatePathMSG)
        layout.addWidget(nt_group)
        frame.setLayout(layout)
        return frame
    
    def stacked_widget_tr(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        tr_group = create_tr_group(data, self.templatePathMSG, self.parent)
        layout.addWidget(tr_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_edital(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        tr_group = create_edital_group(data, self.templatePathMSG)
        layout.addWidget(tr_group)
        frame.setLayout(layout)
        return frame
        
    def stacked_widget_matriz_riscos(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        matriz_riscos_group = create_matriz_risco_group(data, self.templatePathMSG)
        layout.addWidget(matriz_riscos_group)
        frame.setLayout(layout)
        return frame
    
    def stacked_widget_etp(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        etp_group = create_etp_group(data, self.templatePathMSG)
        layout.addWidget(etp_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_info(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        hbox_top_layout = QHBoxLayout()
        contratacao_group_box = create_contratacao_group(data, self.database_manager, self.parent)
        hbox_top_layout.addWidget(contratacao_group_box)
        layout.addLayout(hbox_top_layout)
        frame.setLayout(layout)
        return frame

    def stacked_widget_dfd(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        hbox_top_layout = QHBoxLayout()
        dados_responsavel_contratacao_group = create_dados_responsavel_contratacao_group(data, self.parent)
        hbox_top_layout.addWidget(dados_responsavel_contratacao_group)
        layout.addLayout(hbox_top_layout)
        frame.setLayout(layout)
        return frame

    def stacked_widget_portaria(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        hbox_top_layout = QHBoxLayout()
        planejamento_group_box = create_portaria_layout(data, self.templatePath)
        hbox_top_layout.addWidget(planejamento_group_box)
        layout.addLayout(hbox_top_layout)
        frame.setLayout(layout)
        return frame
        
    def stacked_widget_irp(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        irp_group = create_irp_group(data, self.templatePathMSG, self.parent)
        layout.addWidget(irp_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_checklist(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        irp_group = create_checklist_group(data, self.templatePath, self.config_manager)
        layout.addWidget(irp_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_anexos(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        anexos_group = self.parent.create_anexos_group()
        layout.addWidget(anexos_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_pncp(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        pncp_group = self.create_pncp_group(data)
        layout.addWidget(pncp_group)
        frame.setLayout(layout)
        return frame

    def create_frame_pncp(self, data):
        pncp_group_box = QGroupBox("Integração ao PNCP")
        apply_widget_style_11(pncp_group_box)   
        pncp_group_box.setFixedWidth(350)   
        pncp_layout = QVBoxLayout()

        numero = data.get('numero', '')
        ano = data.get('ano', '')
        link_pncp = data.get('link_pncp', '')
        uasg = data.get('uasg', '')
        cnpj_layout = QHBoxLayout()

        # Criação do campo de texto com o valor '00394502000144'
        self.cnpj_matriz_edit = QLineEdit('00394502000144')
        cnpj_layout.addLayout(create_layout("CNPJ Matriz:", self.cnpj_matriz_edit))

        # Adicionando o campo CNPJ ao layout principal antes do campo "Sequencial PNCP"
        pncp_layout.addLayout(cnpj_layout)

        # Layout Link PNCP
        link_pncp_layout = QHBoxLayout()

        self.link_pncp_edit = QLineEdit(link_pncp)
        link_pncp_layout.addLayout(create_layout("Sequencial PNCP:", self.link_pncp_edit))

        icon_link = QIcon(str(ICONS_DIR / "link.png"))
        link_pncp_button = create_button(
            "",
            icon=icon_link,
            callback=self.on_link_pncp_clicked,
            tooltip_text="Clique para acessar o Link da dispensa no Portal Nacional de Contratações Públicas (PNCP)",
            button_size=QSize(30, 30),
            icon_size=QSize(30, 30)
        )
        apply_widget_style_11(link_pncp_button)
        link_pncp_layout.addWidget(link_pncp_button)

        # Adicionando o layout do campo Sequencial PNCP
        pncp_layout.addLayout(link_pncp_layout)

        # Definindo o nome da tabela utilizando os dados extraídos de `data`
        self.table_name = f"{numero}{ano}{link_pncp}{uasg}"

        pncp_group_box.setLayout(pncp_layout)
        return pncp_group_box

    def on_link_pncp_clicked(self):
        cnpj = self.cnpj_matriz_edit.text()  # Valor do CNPJ Matriz
        ano = self.ano  # Valor do Ano
        sequencial_pncp = self.link_pncp_edit.text()  # Valor do Sequencial PNCP

        # Montando a URL
        url = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{sequencial_pncp}"

        # Abrindo o link no navegador padrão
        QDesktopServices.openUrl(QUrl(url))
    
    def create_utilidades_group(self):
        utilidades_layout = QHBoxLayout()
        utilidades_layout.setSpacing(0)
        utilidades_layout.setContentsMargins(0, 0, 0, 0)

        # Verifique se pasta_base está corretamente inicializada
        if not hasattr(self, 'pasta_base') or not isinstance(self.pasta_base, Path):
            # Acessar o `config` a partir do `self.parent` (EditDataDialog)
            self.pasta_base = Path(self.parent.config.get('pasta_base', str(Path.home() / 'Documentos')))  # Corrigido: acessar config pelo parent

        # Define um nome padrão para a pasta (ou modifique conforme necessário)
        self.nome_pasta = f'{self.parent.id_processo.replace("/", "-")} - {self.parent.objeto.replace("/", "-")}'

        # Botão para criar a estrutura de pastas e abrir a pasta
        icon_criar_pasta = QIcon(str(ICONS_DIR / "create-folder.png"))
        criar_pasta_button = create_button(
            "Criar e Abrir Pasta", 
            icon=icon_criar_pasta, 
            callback=self.criar_e_abrir_pasta,  # Chama a função que cria e abre a pasta
            tooltip_text="Clique para criar a estrutura de pastas e abrir", 
            button_size=QSize(210, 40), 
            icon_size=QSize(40, 40)
        )
        apply_widget_style_11(criar_pasta_button)
        utilidades_layout.addWidget(criar_pasta_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Botão para abrir o arquivo de registro
        icon_salvar_pasta = QIcon(str(ICONS_DIR / "zip-folder.png"))
        editar_registro_button = create_button("Local de Salvamento", icon=icon_salvar_pasta, callback=self.parent.consolidador.alterar_diretorio_base, tooltip_text="Clique para alterar o local de salvamento dos arquivos", button_size=QSize(210, 40), icon_size=QSize(40, 40))
        apply_widget_style_11(editar_registro_button)
        utilidades_layout.addWidget(editar_registro_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Botão para editar os modelos dos documentos
        icon_template = QIcon(str(ICONS_DIR / "template.png"))
        visualizar_pdf_button = create_button("Editar Modelos", icon=icon_template, callback=self.parent.consolidador.editar_modelo, tooltip_text="Clique para editar os modelos dos documentos", button_size=QSize(210, 40), icon_size=QSize(40, 40))
        apply_widget_style_11(visualizar_pdf_button)
        utilidades_layout.addWidget(visualizar_pdf_button, alignment=Qt.AlignmentFlag.AlignCenter)

        return utilidades_layout

    def criar_e_abrir_pasta(self):
        # Cria a estrutura de pastas
        self.consolidador.verificar_e_criar_pastas(self.pasta_base / self.nome_pasta)
        
        # Após criar, tenta abrir a pasta
        self.abrir_pasta(self.pasta_base / self.nome_pasta)
        self.status_atualizado.emit("Pastas encontradas", str(self.ICONS_DIR / "folder_v.png"))

    def abrir_pasta(self, pasta_path):
        if pasta_path.exists() and pasta_path.is_dir():
            # Abre a pasta no explorador de arquivos usando QDesktopServices
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(pasta_path)))
        else:
            QMessageBox.warning(self, "Erro", "A pasta selecionada não existe ou não é um diretório.")

    # Função para criar o layout e realizar as operações do grupo PNCP
    def create_pncp_group(self, data):
        # GroupBox para os dados integrados ao PNCP
        anexos_group_box = QGroupBox("Dados integrados ao PNCP")
        apply_widget_style_11(anexos_group_box)
        self.numero = data.get('numero', '')
        self.ano = data.get('ano', '')
        self.link_pncp = data.get('link_pncp', '')
        self.uasg = data.get('uasg', '')
        self.objeto = data.get('objeto', '')
        # Layout para o GroupBox
        layout = QVBoxLayout()
        icon_api = QIcon(str(ICONS_DIR / "api.png"))

        # Botão para realizar a consulta
        self.consulta_button = QPushButton("Consultar PNCP")
        self.consulta_button.setIcon(icon_api)  # Define o ícone no botão
        self.consulta_button.setIconSize(QSize(40, 40))  # Define o tamanho do ícone para 40x40
        self.consulta_button.clicked.connect(self.on_consultar_pncp)

        layout.addWidget(self.consulta_button)

        # Substituir QListView por QTreeView
        self.result_tree = QTreeView()
        self.result_model = QStandardItemModel()
        self.result_tree.setModel(self.result_model)
        self.result_model.setHorizontalHeaderLabels(['Informações'])
        layout.addWidget(self.result_tree)

        # Definir layout no GroupBox
        anexos_group_box.setLayout(layout)

        # Carregar dados do banco de dados CONTROLE_DADOS_PNCP
        self.load_tree_data()

        return anexos_group_box

    def load_tree_data(self):
        # Limpar o modelo antes de adicionar novos dados
        self.result_model.clear()
        self.result_model.setHorizontalHeaderLabels(['Informações'])

        table_name = f"DE{self.numero}{self.ano}{self.link_pncp}{self.uasg}"
        icon_homologado = QIcon(str(ICONS_DIR / "checked.png"))
        icon_nao_homologado = QIcon(str(ICONS_DIR / "alert.png"))

        conn = sqlite3.connect(CONTROLE_DADOS_PNCP)
        cursor = conn.cursor()

        try:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            table_exists = cursor.fetchone()

            if table_exists:
                root_text = f"{self.numero}/{self.ano} - {self.objeto}"
                root_item = QStandardItem(root_text)
                self.result_model.appendRow(root_item)

                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                for row in rows:
                    # Converter temResultado para um inteiro e verificar se é 1 (True) ou 0 (False)
                    tem_resultado = int(row[16]) if row[16] is not None else 0
                    
                    # Verificar o valor de 'temResultado' (True para 1, False para 0)
                    if tem_resultado == 1:  # se temResultado for True
                        resultado_text = "Homologado"
                    else:  # se temResultado for False
                        resultado_text = row[14] if row[14] else "Resultado indefinido"

                    item_text = f"Item {row[10]} - {row[4]} - {row[18]} ({resultado_text})"
                    numero_item = QStandardItem(item_text)

                    # Definir ícone com base no resultado
                    if tem_resultado == 1:  # True = Homologado
                        numero_item.setIcon(icon_homologado)
                    else:  # False = Não homologado
                        numero_item.setIcon(icon_nao_homologado)

                    root_item.appendRow([numero_item])

                    child_data = {
                        'Última verificação': row[2],
                        'CNPJ/CPF': row[7],
                        'Nome Razão Social': row[8],
                        'Número Controle PNCP': row[9],
                        'Benefício ME/EPP': row[17],
                        'Valor Unitário Estimado': row[21],
                        'Quantidade': row[12],
                        'Valor Unitário Homologado': row[22],
                        'Quantidade Homologada': row[13],
                    }

                    for key, value in child_data.items():
                        child_item = QStandardItem(f"{key}: {value}")
                        numero_item.appendRow([child_item])

                self.result_tree.expandAll()

            else:
                print(f"Tabela '{table_name}' não encontrada.")
        except sqlite3.Error as e:
            print(f"Erro ao carregar os dados: {e}")
        finally:
            conn.close()

    def on_consultar_pncp(self):
        # Desabilitar o botão enquanto a consulta está sendo feita
        self.consulta_button.setEnabled(False)

        # Criar uma instância de QProgressDialog para mostrar o progresso
        self.progress_dialog = QProgressDialog("Consultando dados no PNCP...", "Cancelar", 0, 0, self)
        self.progress_dialog.setWindowTitle("Progresso da Consulta")
        self.progress_dialog.setCancelButton(None)  # Remove o botão de cancelamento
        self.progress_dialog.setMinimumDuration(0)  # Mostra imediatamente
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)  # Bloqueia a janela até finalizar
        self.progress_dialog.show()

        # Cria a instância da thread de consulta
        self.thread = PNCPConsultaThread(self.numero, self.ano, self.link_pncp, self.uasg, self)

        # Conectar os sinais da thread para manipular o resultado
        self.thread.consulta_concluida.connect(self.on_consulta_concluida)
        self.thread.erro_consulta.connect(self.on_erro_consulta)
        
        # Conectar o sinal de progresso para exibir a mensagem na thread principal
        self.thread.progresso_consulta.connect(self.exibir_mensagem_progresso)

        # Iniciar a thread
        self.thread.start()

    def exibir_mensagem_progresso(self, mensagem):
        """Exibe as mensagens de progresso no diálogo de progresso."""
        self.progress_dialog.setLabelText(mensagem)

    def on_consulta_concluida(self, data_informacoes_lista, resultados_completos):
        """Ação a ser realizada quando a consulta for concluída com sucesso."""
        # Fechar a barra de progresso
        self.progress_dialog.close()

        if data_informacoes_lista and resultados_completos:
            # Criamos a instância de PNCPConsulta na thread principal
            self.consulta_pncp = PNCPConsulta(self.numero, self.ano, self.link_pncp, self.uasg, self)
            # Conectar o sinal 'dados_integrados' ao método 'load_tree_data'
            self.consulta_pncp.dados_integrados.connect(self.load_tree_data)
            self.consulta_pncp.exibir_dados_em_dialog(data_informacoes_lista, resultados_completos)
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum dado foi retornado.")

        # Reabilitar o botão de consulta
        self.consulta_button.setEnabled(True)

    def on_erro_consulta(self, mensagem):
        # Fechar a barra de progresso em caso de erro
        self.progress_dialog.close()

        QMessageBox.warning(self, "Erro", mensagem)
        self.consulta_button.setEnabled(True)
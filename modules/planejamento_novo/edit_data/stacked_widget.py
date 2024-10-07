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
from modules.planejamento_novo.edit_data.widgets.irp import create_irp_group
from modules.planejamento_novo.edit_data.widgets.checklist import create_checklist_group
from modules.planejamento_novo.edit_data.widgets.planejamento import create_planejamento_group, create_classificacao_orcamentaria_group, create_frame_formulario_group
import pandas as pd
import sqlite3     
import logging 
class StackedWidgetManager:
    def __init__(self, parent, config_manager, df_registro_selecionado):
        self.parent = parent
        self.config_manager = config_manager
        self.df_registro_selecionado = df_registro_selecionado
        self.stack_manager = QStackedWidget(parent)
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        self.material_servico = None  # Inicialize aqui ou no método apropriado
        self.objeto = None
        self.setor_responsavel = None
        self.orgao_responsavel = None
        self.sigla_om = None
        self.templatePathMSG = MSG_DIR_IRP / "last_template_msg_irp.txt"
        self.templatePath = PASTA_TEMPLATE
        self.setup_stacked_widgets()

    def setup_stacked_widgets(self):
        # Extrai dados do DataFrame selecionado
        data = EditDataDialogUtils.extract_registro_data(self.df_registro_selecionado)

        # Configura os widgets no StackedWidgetManager
        widgets = {
            "Informações": self.stacked_widget_info(data),
            "Planejamento": self.stacked_widget_planejamento(data),
            "IRP": self.stacked_widget_irp(data),
            "Demandante": self.stacked_widget_responsaveis(data),
            "Documentos": self.stacked_widget_documentos(data),
            "ETP": self.stacked_widget_etp(data),
            "MR": self.stacked_widget_matriz_riscos(data),
            "Anexos": self.stacked_widget_anexos(data),
            "PNCP": self.stacked_widget_pncp(data),
            "Check-list": self.stacked_widget_checklist(data),
            "Nota Técnica": self.stacked_widget_nt(data),
        }

        for name, widget in widgets.items():
            self.stack_manager.addWidget(widget)
            widget.setObjectName(name)

    def get_stacked_widget(self):
        return self.stack_manager

    def stacked_widget_info(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        hbox_top_layout = QHBoxLayout()
        contratacao_group_box = create_contratacao_group(data, self.database_manager)
        hbox_top_layout.addWidget(contratacao_group_box)
        layout.addLayout(hbox_top_layout)
        frame.setLayout(layout)
        return frame

    def stacked_widget_planejamento(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        hbox_top_layout = QHBoxLayout()
        planejamento_group_box = create_planejamento_group(data, self.templatePath)
        hbox_top_layout.addWidget(planejamento_group_box)
        layout.addLayout(hbox_top_layout)
        frame.setLayout(layout)
        return frame
        
    def stacked_widget_irp(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        irp_group = create_irp_group(data, self.templatePathMSG)
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

    def stacked_widget_responsaveis(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        dados_responsavel_contratacao_group = self.create_dados_responsavel_contratacao_group(data)
        layout.addWidget(dados_responsavel_contratacao_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_documentos(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        botao_documentos = self.parent.create_gerar_documentos_group()
        sigdem_group = self.parent.create_GrupoSIGDEM()
        utilidade_group = self.create_utilidades_group()
        layout.addLayout(botao_documentos)
        layout.addWidget(sigdem_group)
        layout.addLayout(utilidade_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_etp(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        anexos_group = self.parent.create_anexos_group()
        layout.addWidget(anexos_group)
        frame.setLayout(layout)
        return frame
    
    def stacked_widget_matriz_riscos(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        anexos_group = self.parent.create_anexos_group()
        layout.addWidget(anexos_group)
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

    def stacked_widget_nt(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        nt_group = self.create_pncp_group(data)
        layout.addWidget(nt_group)
        frame.setLayout(layout)
        return frame
            
    # def create_classificacao_orcamentaria_group(self, data):
    #     classificacao_orcamentaria_group_box = QGroupBox("Classificação Orçamentária")
    #     apply_widget_style_11(classificacao_orcamentaria_group_box)
    #     classificacao_orcamentaria_group_box.setFixedWidth(350)  
    #     classificacao_orcamentaria_layout = QVBoxLayout()

    #     acao_interna_edit = QLineEdit(data['uasg'])
    #     fonte_recurso_edit = QLineEdit(data['uasg'])
    #     natureza_despesa_edit = QLineEdit(data['uasg'])
    #     unidade_orcamentaria_edit = QLineEdit(data['uasg'])
    #     ptres_edit = QLineEdit(data['uasg'])

    #     # Utilizando a função create_layout fora da classe
    #     classificacao_orcamentaria_layout.addLayout(create_layout("Ação Interna:", acao_interna_edit, apply_style_fn=apply_widget_style_11))
    #     classificacao_orcamentaria_layout.addLayout(create_layout("Fonte de Recurso (FR):", fonte_recurso_edit, apply_style_fn=apply_widget_style_11))
    #     classificacao_orcamentaria_layout.addLayout(create_layout("Natureza de Despesa (ND):", natureza_despesa_edit, apply_style_fn=apply_widget_style_11))
    #     classificacao_orcamentaria_layout.addLayout(create_layout("Unidade Orçamentária (UO):", unidade_orcamentaria_edit, apply_style_fn=apply_widget_style_11))
    #     classificacao_orcamentaria_layout.addLayout(create_layout("PTRES:", ptres_edit, apply_style_fn=apply_widget_style_11))

    #     classificacao_orcamentaria_group_box.setLayout(classificacao_orcamentaria_layout)

    #     return classificacao_orcamentaria_group_box

    # def create_frame_formulario_group(self):
    #     formulario_group_box = QGroupBox("Formulário de Dados")
    #     apply_widget_style_11(formulario_group_box)   
    #     formulario_group_box.setFixedWidth(350)   
    #     formulario_layout = QVBoxLayout()

    #     # Adicionando os botões ao layout
    #     icon_excel_up = QIcon(str(ICONS_DIR / "excel_up.png"))
    #     icon_excel_down = QIcon(str(ICONS_DIR / "excel_down.png"))

    #     criar_formulario_button = create_button(
    #         "   Criar Formulário   ",
    #         icon=icon_excel_up,
    #         callback=self.parent.formulario_excel.criar_formulario,  # Chama o método do parent
    #         tooltip_text="Clique para criar o formulário",
    #         button_size=QSize(220, 50),
    #         icon_size=QSize(45, 45)
    #     )

    #     carregar_formulario_button = create_button(
    #         "Carregar Formulário",
    #         icon=icon_excel_down,
    #         callback=self.parent.formulario_excel.carregar_formulario,  # Chama o método do parent
    #         tooltip_text="Clique para carregar o formulário",
    #         button_size=QSize(220, 50),
    #         icon_size=QSize(45, 45)
    #     )

    #     formulario_layout.addWidget(criar_formulario_button, alignment=Qt.AlignmentFlag.AlignCenter)
    #     formulario_layout.addWidget(carregar_formulario_button, alignment=Qt.AlignmentFlag.AlignCenter)
    #     formulario_group_box.setLayout(formulario_layout)

    #     return formulario_group_box

    def create_dados_responsavel_contratacao_group(self, data):
        setor_responsavel_group_box = QGroupBox("Divisão/Setor Responsável pela Demanda")
        apply_widget_style_11(setor_responsavel_group_box)
        setor_responsavel_layout = QVBoxLayout()

        # Layout OM e Divisão
        om_divisao_layout = self.create_om_divisao_layout(data)
        setor_responsavel_layout.addLayout(om_divisao_layout)

        # Carrega sigla_om
        self.load_sigla_om()

        # Layout PAR
        par_layout = self.create_par_layout(data)
        setor_responsavel_layout.addLayout(par_layout)

        # Layout Endereço
        endereco_cep_layout = self.create_endereco_layout(data)
        setor_responsavel_layout.addLayout(endereco_cep_layout)

        # Layout Contato
        email_telefone_layout = self.create_contato_layout(data)
        setor_responsavel_layout.addLayout(email_telefone_layout)

        # Outros campos
        self.dias_edit = QLineEdit("Segunda à Sexta")
        setor_responsavel_layout.addLayout(create_layout("Dias para Recebimento:", self.dias_edit))

        self.horario_edit = QLineEdit("09 às 11h20 e 14 às 16h30")
        setor_responsavel_layout.addLayout(create_layout("Horário para Recebimento:", self.horario_edit))

        # Adicionando Justificativa
        justificativa_label = QLabel("Justificativa para a contratação:")
        justificativa_label.setStyleSheet("font-size: 12pt;")
        self.justificativa_edit = QTextEdit(self.get_justification_text())
        apply_widget_style_11(self.justificativa_edit)
        setor_responsavel_layout.addWidget(justificativa_label)
        setor_responsavel_layout.addWidget(self.justificativa_edit)

        setor_responsavel_group_box.setLayout(setor_responsavel_layout)
        return setor_responsavel_group_box

    def create_om_divisao_layout(self, data):
        om_divisao_layout = QHBoxLayout()

        # Configuração da OM
        om_layout = QHBoxLayout()
        om_label = QLabel("OM:")
        apply_widget_style_11(om_label)

        self.sigla_om = data.get('sigla_om', 'CeIMBra')
        if self.df_registro_selecionado is not None and 'sigla_om' in self.df_registro_selecionado.columns:
            if not self.df_registro_selecionado['sigla_om'].empty:
                self.sigla_om = self.df_registro_selecionado['sigla_om'].iloc[0]
            else:
                self.sigla_om = 'CeIMBra'

        self.om_combo = create_combo_box(self.sigla_om, [], 150, 35)
        om_layout.addWidget(om_label)
        om_layout.addWidget(self.om_combo)

        # Adicionando o layout OM ao layout principal
        om_divisao_layout.addLayout(om_layout)

        # Configuração da Divisão
        divisao_label = QLabel("Divisão:")
        apply_widget_style_11(divisao_label)

        self.setor_responsavel_combo = QComboBox()
        self.setor_responsavel_combo.setEditable(True)

        # Adicionando as opções ao ComboBox
        divisoes = [
            "Divisão de Abastecimento",
            "Divisão de Finanças",
            "Divisão de Obtenção",
            "Divisão de Pagamento",
            "Divisão de Administração",
            "Divisão de Subsistência"
        ]
        self.setor_responsavel_combo.addItems(divisoes)

        self.setor_responsavel_combo.setCurrentText(data.get('setor_responsavel', ''))
        self.setor_responsavel_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        om_divisao_layout.addWidget(divisao_label)
        om_divisao_layout.addWidget(self.setor_responsavel_combo)

        return om_divisao_layout

    def create_par_layout(self, data):
        self.par_edit = QLineEdit(str(data.get('cod_par', '')))
        self.par_edit.setFixedWidth(150)
        self.prioridade_combo = create_combo_box(
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
        par_layout.addWidget(self.par_edit)
        par_layout.addWidget(prioridade_label)
        par_layout.addWidget(self.prioridade_combo)

        return par_layout

    def create_endereco_layout(self, data):
        self.endereco_edit = QLineEdit(data.get('endereco', ''))
        self.endereco_edit.setFixedWidth(450)
        self.cep_edit = QLineEdit(str(data.get('cep', '')))

        endereco_cep_layout = QHBoxLayout()
        endereco_label = QLabel("Endereço:")
        cep_label = QLabel("CEP:")
        apply_widget_style_11(endereco_label)
        apply_widget_style_11(cep_label)

        endereco_cep_layout.addWidget(endereco_label)
        endereco_cep_layout.addWidget(self.endereco_edit)
        endereco_cep_layout.addWidget(cep_label)
        endereco_cep_layout.addWidget(self.cep_edit)

        return endereco_cep_layout

    def create_contato_layout(self, data):
        self.email_edit = QLineEdit(data.get('email', ''))
        self.email_edit.setFixedWidth(400)
        self.telefone_edit = QLineEdit(data.get('telefone', ''))

        email_telefone_layout = QHBoxLayout()
        email_telefone_layout.addLayout(create_layout("E-mail:", self.email_edit))
        email_telefone_layout.addLayout(create_layout("Tel:", self.telefone_edit))

        return email_telefone_layout

    def load_sigla_om(self):
        sigla_om = self.sigla_om  # Utilize a variável de instância
        try:
            with sqlite3.connect(self.parent.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT sigla_om FROM controle_om ORDER BY sigla_om")
                items = [row[0] for row in cursor.fetchall()]
                self.om_combo.addItems(items)
                self.om_combo.setCurrentText(sigla_om)
                self.om_combo.currentTextChanged.connect(self.on_om_changed)
        except Exception as e:
            QMessageBox.warning(self.parent, "Erro", f"Erro ao carregar OM: {e}")

    def on_om_changed(self):
        selected_om = self.om_combo.currentText()
        print(f"OM changed to: {selected_om}")
        try:
            with sqlite3.connect(self.parent.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT uasg, orgao_responsavel, uf, codigoMunicipioIbge FROM controle_om WHERE sigla_om = ?", (selected_om,))
                result = cursor.fetchone()
                if result:
                    uasg, orgao_responsavel, uf, codigoMunicipioIbge = result
                    index = self.df_registro_selecionado.index[0]
                    self.df_registro_selecionado.loc[index, 'uasg'] = uasg
                    self.df_registro_selecionado.loc[index, 'orgao_responsavel'] = orgao_responsavel
                    print(f"Updated DataFrame: uasg={uasg}, orgao_responsavel={orgao_responsavel}")
                    # Emite o sinal title_updated do parent
                    self.parent.title_updated.emit(f"{orgao_responsavel} (UASG: {uasg})")
                else:
                    print("Nenhum resultado encontrado para a OM selecionada.")
        except Exception as e:
            QMessageBox.warning(self.parent, "Erro", f"Erro ao carregar dados da OM: {e}")
            print(f"Error loading data for selected OM: {e}")

    def get_justification_text(self):
        # Tenta recuperar o valor atual da justificativa no DataFrame
        try:
            current_justification = self.df_registro_selecionado['justificativa'].iloc[0]
        except KeyError:
            logging.error("A coluna 'justificativa' não foi encontrada no DataFrame.")
            return self.generate_default_justification()  # Chama uma função para gerar uma justificativa padrão
        except IndexError:
            logging.warning("O DataFrame 'df_registro_selecionado' está vazio. Retornando justificativa padrão.")
            return self.generate_default_justification()  # Chama uma função para gerar uma justificativa padrão

        # Retorna o valor atual se ele existir, senão, constrói uma justificativa baseada no tipo de material/serviço
        if current_justification:  # Checa se existe uma justificativa
            return current_justification
        else:
            return self.generate_default_justification()  # Chama uma função para gerar uma justificativa padrão

    def generate_default_justification(self):
        # Gera justificativa padrão com base no tipo de material ou serviço
        if self.material_servico == 'Material':
            return (f"A aquisição de {self.objeto} se faz necessária para o atendimento das necessidades do(a) {self.setor_responsavel} do(a) {self.orgao_responsavel} ({self.sigla_om}). A disponibilidade e a qualidade dos materiais são essenciais para garantir a continuidade das operações e a eficiência das atividades desempenhadas pelo(a) {self.setor_responsavel}.")
        elif self.material_servico == 'Serviço':
            return (f"A contratação de empresa especializada na prestação de serviços de {self.objeto} é imprescindível para o atendimento das necessidades do(a) {self.setor_responsavel} do(a) {self.orgao_responsavel} ({self.sigla_om}).")
        return ""  # Retorna uma string vazia se nenhuma condição acima for satisfeita

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
        self.table_name = f"DE{numero}{ano}{link_pncp}{uasg}"

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
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento.utilidades_planejamento import DatabaseManager
from modules.dispensa_eletronica.documentos_cp_dfd_tr import PDFAddDialog, ConsolidarDocumentos, load_config_path_id
from modules.dispensa_eletronica.formulario_excel import FormularioExcel
from modules.planejamento_novo.edit_data.edit_dialog_utils import EditDataDialogUtils, create_combo_box, validate_and_convert_date, create_layout, create_button, apply_widget_style_11
from modules.planejamento_novo.edit_data.stacked_widget import StackedWidgetManager
from modules.planejamento_novo.edit_data.data_saver import DataSaver
from diretorios import *
from pathlib import Path
import pandas as pd
from pathlib import Path
import sqlite3
import webbrowser
from datetime import datetime

class EditDataDialogNovo(QDialog): 
    dados_atualizados = pyqtSignal()
    title_updated = pyqtSignal(str)
    status_atualizado = pyqtSignal(str, str)

    def __init__(self, df_registro_selecionado, icons_dir, parent=None):
        super().__init__(parent)
        self.df_registro_selecionado = df_registro_selecionado
        self.ICONS_DIR = Path(icons_dir)
        self.navigation_buttons = []
        self.consolidador = ConsolidarDocumentos(df_registro_selecionado)
        self._init_paths()
        self.data_saver = DataSaver(self.database_manager, self.df_registro_selecionado)  
        self.formulario_excel = FormularioExcel(self.df_registro_selecionado, self.pasta_base, self)
        self.set_registro_data()
        self.stacked_widget_manager = StackedWidgetManager(self, self.df_registro_selecionado)
        self._init_ui()
        self._init_connections()
        self.status_atualizado.connect(lambda msg, icon: EditDataDialogUtils.atualizar_status_label(self.status_label, self.icon_label, msg, icon))

    def set_registro_data(self):
        # Extrai os dados do DataFrame e armazena como atributos da classe
        data = EditDataDialogUtils.extract_registro_data(self.df_registro_selecionado)
        self.id_processo = data.get('id_processo')
        self.tipo = data.get('tipo')
        self.numero = data.get('numero')
        self.ano = data.get('ano')
        self.situacao = data.get('status')
        self.nup = data.get('nup')
        self.material_servico = data.get('material_servico')
        self.objeto = data.get('objeto')
        self.vigencia = data.get('vigencia')
        self.data_sessao = data.get('data_sessao')
        self.operador = data.get('operador')
        self.criterio_julgamento = data.get('criterio_julgamento')
        self.com_disputa = data.get('com_disputa')
        self.pesquisa_preco = data.get('pesquisa_preco')
        self.previsao_contratacao = data.get('previsao_contratacao')
        self.uasg = data.get('uasg')
        self.orgao_responsavel = data.get('orgao_responsavel')
        self.sigla_om = data.get('sigla_om')
        self.uf = data.get('uf')
        self.codigoMunicipioIbge = data.get('codigoMunicipioIbge')
        self.setor_responsavel = data.get('setor_responsavel')
        self.responsavel_pela_demanda = data.get('responsavel_pela_demanda')
        self.ordenador_despesas = data.get('ordenador_despesas')
        self.agente_fiscal = data.get('agente_fiscal')
        self.gerente_de_credito = data.get('gerente_de_credito')
        self.cod_par = data.get('cod_par')
        self.prioridade_par = data.get('prioridade_par')
        self.cep = data.get('cep')
        self.endereco = data.get('endereco')
        self.email = data.get('email')
        self.telefone = data.get('telefone')
        self.dias_para_recebimento = data.get('dias_para_recebimento')
        self.horario_para_recebimento = data.get('horario_para_recebimento')
        self.valor_total = data.get('valor_total')
        self.acao_interna = data.get('acao_interna')
        self.fonte_recursos = data.get('fonte_recursos')
        self.natureza_despesa = data.get('natureza_despesa')
        self.unidade_orcamentaria = data.get('unidade_orcamentaria')
        self.programa_trabalho_resuminho = data.get('programa_trabalho_resuminho')
        self.atividade_custeio = data.get('atividade_custeio')
        self.comentarios = data.get('comentarios')
        self.justificativa = data.get('justificativa')
        self.link_pncp = data.get('link_pncp')

    def _init_paths(self):
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        self.config = load_config_path_id()
        self.pasta_base = Path(self.config.get('pasta_base', str(Path.home() / 'Desktop')))

    def _init_ui(self):
        self.setWindowTitle("Editar Dados do Processo")
        icon_path = self.ICONS_DIR / "edit.png"
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            print(f"Icon not found: {icon_path}")
        self.setFixedSize(1400, 720)

        # Layout principal vertical para os componentes existentes
        layout_principal = QVBoxLayout()

        # Armazena o titleLabel como um atributo da classe
        self.header_widget, self.titleLabel = EditDataDialogUtils.update_title_label(self.df_registro_selecionado)
        layout_principal.addWidget(self.header_widget)

        # Criar o layout de navegação
        navigation_layout = EditDataDialogUtils.create_navigation_layout(self.show_widget, self.add_action_buttons)
        layout_principal.addLayout(navigation_layout)  # Adicionando o layout de navegação aqui

        # Adiciona o StackedWidget gerenciado pelo StackedWidgetManager
        layout_principal.addWidget(self.stacked_widget_manager.get_stacked_widget())

        layout_principal.setSpacing(0)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        # Cria o layout de agentes responsáveis e aplica borda lateral
        layout_agentes_responsaveis = self.create_agentes_responsaveis_layout()

        # Layout horizontal principal para conter ambos os layouts
        hlayout_main = QHBoxLayout(self)
        hlayout_main.addLayout(layout_principal)  # Adiciona o layout principal à esquerda
        hlayout_main.addWidget(layout_agentes_responsaveis)  # Adiciona o layout de agentes à direita

        # Define o layout principal como o layout horizontal
        self.setLayout(hlayout_main)

        # Mostra o widget inicial
        self.show_widget("Informações")

    def show_widget(self, name):
        # Desmarcar todos os botões de navegação
        for button in self.navigation_buttons:
            button.setChecked(False)

        # Encontrar o botão correspondente e marcar
        for button in self.navigation_buttons:
            if button.text() == name:
                button.setChecked(True)
                break

        # Mostrar o widget correspondente no QStackedWidget gerenciado pelo StackedWidgetManager
        stack_manager = self.stacked_widget_manager.get_stacked_widget()
        for i in range(stack_manager.count()):
            widget = stack_manager.widget(i)
            if widget.objectName() == name:
                stack_manager.setCurrentWidget(widget)
                break

    def _init_connections(self):
        self.title_updated.connect(self.update_title_label_text)
        
    def update_title_label_text(self, new_title):
        data = EditDataDialogUtils.extract_registro_data(self.df_registro_selecionado)
        html_text = (
            f"{data['tipo']} {data['numero']}/{data['ano']} - {data['objeto']}<br>"
            f"<span style='font-size: 16px'>OM: {new_title}</span>"
        )
        self.titleLabel.setText(html_text)
        print(f"Title updated: {html_text}")

    def add_action_buttons(self, layout):
        icon_confirm = QIcon(str(self.ICONS_DIR / "confirm.png"))

        # Chama a função externa create_button
        button_confirm = create_button(" Salvar", icon_confirm, self.save_changes, "Salvar dados", QSize(110, 30), QSize(30, 30))
        layout.addWidget(button_confirm)
        apply_widget_style_11(button_confirm)

    def save_changes(self):
        try:
            # Dados que serão atualizados
            data = {
                'status': self.situacao_edit.currentText(),
                'ordenador_despesas': self.ordenador_combo.currentText(),
                'agente_fiscal': self.agente_fiscal_combo.currentText(),
                'gerente_de_credito': self.gerente_credito_combo.currentText(),
                'responsavel_pela_demanda': self.responsavel_demanda_combo.currentText(),
                'nup': self.nup_edit.text().strip(),
                'material_servico': self.material_edit.currentText(),
                'objeto': self.objeto_edit.text().strip(),
                'vigencia': self.vigencia_edit.currentText(),
                'data_sessao': self.data_edit.date().toString("yyyy-MM-dd"),
                'previsao_contratacao': self.previsao_contratacao_edit.date().toString("yyyy-MM-dd"),
                'criterio_julgamento': self.criterio_edit.currentText(),
                'com_disputa': 'Sim' if self.radio_disputa_sim.isChecked() else 'Não',
                'pesquisa_preco': 'Sim' if self.radio_pesquisa_sim.isChecked() else 'Não',
                'setor_responsavel': self.setor_responsavel_combo.currentText(),
                'operador': self.operador_dispensa_combo.currentText(),
                'sigla_om': self.om_combo.currentText(),
                'uasg': self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], 'uasg'],
                'orgao_responsavel': self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], 'orgao_responsavel'],
                'cod_par': self.par_edit.text().strip(),
                'prioridade_par': self.prioridade_combo.currentText(),
                'cep': self.cep_edit.text().strip(),
                'endereco': self.endereco_edit.text().strip(),
                'email': self.email_edit.text().strip(),
                'telefone': self.telefone_edit.text().strip(),
                'dias_para_recebimento': self.dias_edit.text().strip(),
                'horario_para_recebimento': self.horario_edit.text().strip(),
                'justificativa': self.justificativa_edit.toPlainText().strip(),
                'valor_total': self.valor_edit.text().strip(),
                'acao_interna': self.acao_interna_edit.text().strip(),
                'fonte_recursos': self.fonte_recurso_edit.text().strip(),
                'natureza_despesa': self.natureza_despesa_edit.text().strip(),
                'unidade_orcamentaria': self.unidade_orcamentaria_edit.text().strip(),
                'programa_trabalho_resuminho': self.ptres_edit.text().strip(),
                'atividade_custeio': 'Sim' if self.radio_custeio_sim.isChecked() else 'Não',
                'link_pncp': self.link_pncp_edit.text().strip(),
            }

            # Salvar alterações usando a classe DataSaver
            self.data_saver.save_changes(data)
            self.dados_atualizados.emit()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao salvar as alterações: {str(e)}")

    def apply_widget_style_12(self, widget):
        widget.setStyleSheet("font-size: 12pt;") 

    def apply_widget_style_14(self, widget):
        widget.setStyleSheet("font-size: 14pt;") 
    
    def preencher_campos(self):
        try:
            self.situacao_edit.setCurrentText(str(self.df_registro_selecionado.at[0, 'status']))
            self.ordenador_combo.setCurrentText(str(self.df_registro_selecionado.at[0, 'ordenador_despesas']))
            self.agente_fiscal_combo.setCurrentText(str(self.df_registro_selecionado.at[0, 'agente_fiscal']))
            self.gerente_credito_combo.setCurrentText(str(self.df_registro_selecionado.at[0, 'gerente_de_credito']))
            self.responsavel_demanda_combo.setCurrentText(str(self.df_registro_selecionado.at[0, 'responsavel_pela_demanda']))
            self.nup_edit.setText(str(self.df_registro_selecionado.at[0, 'nup']))
            self.material_edit.setCurrentText(str(self.df_registro_selecionado.at[0, 'material_servico']))
            self.objeto_edit.setText(str(self.df_registro_selecionado.at[0, 'objeto']))
            self.vigencia_edit.setCurrentText(str(self.df_registro_selecionado.at[0, 'vigencia']))
            self.data_edit.setDate(QDate.fromString(str(self.df_registro_selecionado.at[0, 'data_sessao']), "yyyy-MM-dd"))
            self.previsao_contratacao_edit.setDate(QDate.fromString(str(self.df_registro_selecionado.at[0, 'previsao_contratacao']), "yyyy-MM-dd"))
            self.criterio_edit.setCurrentText(str(self.df_registro_selecionado.at[0, 'criterio_julgamento']))
            self.radio_disputa_sim.setChecked(str(self.df_registro_selecionado.at[0, 'com_disputa']) == 'Sim')
            self.radio_disputa_nao.setChecked(str(self.df_registro_selecionado.at[0, 'com_disputa']) == 'Não')
            self.radio_pesquisa_sim.setChecked(str(self.df_registro_selecionado.at[0, 'pesquisa_preco']) == 'Sim')
            self.radio_pesquisa_nao.setChecked(str(self.df_registro_selecionado.at[0, 'pesquisa_preco']) == 'Não')
            self.setor_responsavel_combo.setCurrentText(str(self.df_registro_selecionado.at[0, 'setor_responsavel']))
            self.operador_dispensa_combo.setCurrentText(str(self.df_registro_selecionado.at[0, 'operador']))
            self.om_combo.setCurrentText(str(self.df_registro_selecionado.at[0, 'sigla_om']))
            self.par_edit.setText(str(self.df_registro_selecionado.at[0, 'cod_par']))
            self.prioridade_combo.setCurrentText(str(self.df_registro_selecionado.at[0, 'prioridade_par']))
            self.cep_edit.setText(str(self.df_registro_selecionado.at[0, 'cep']))
            self.endereco_edit.setText(str(self.df_registro_selecionado.at[0, 'endereco']))
            self.email_edit.setText(str(self.df_registro_selecionado.at[0, 'email']))
            self.telefone_edit.setText(str(self.df_registro_selecionado.at[0, 'telefone']))
            self.dias_edit.setText(str(self.df_registro_selecionado.at[0, 'dias_para_recebimento']))
            self.horario_edit.setText(str(self.df_registro_selecionado.at[0, 'horario_para_recebimento']))
            self.justificativa_edit.setPlainText(str(self.df_registro_selecionado.at[0, 'justificativa']))
            self.valor_edit.setText(str(self.df_registro_selecionado.at[0, 'valor_total']))
            self.acao_interna_edit.setText(str(self.df_registro_selecionado.at[0, 'acao_interna']))
            self.fonte_recurso_edit.setText(str(self.df_registro_selecionado.at[0, 'fonte_recursos']))
            self.natureza_despesa_edit.setText(str(self.df_registro_selecionado.at[0, 'natureza_despesa']))
            self.unidade_orcamentaria_edit.setText(str(self.df_registro_selecionado.at[0, 'unidade_orcamentaria']))
            self.ptres_edit.setText(str(self.df_registro_selecionado.at[0, 'programa_trabalho_resuminho']))
            self.radio_custeio_sim.setChecked(str(self.df_registro_selecionado.at[0, 'atividade_custeio']) == 'Sim')
            self.radio_custeio_nao.setChecked(str(self.df_registro_selecionado.at[0, 'atividade_custeio']) == 'Não')
            self.link_pncp_edit.setText(str(self.df_registro_selecionado.at[0, 'link_pncp']))

        except KeyError as e:
            print(f"Erro ao preencher campos: {str(e)}")
    
    def create_utilidades_group(self):
        utilidades_layout = QHBoxLayout()
        utilidades_layout.setSpacing(0)
        utilidades_layout.setContentsMargins(0, 0, 0, 0)

        # Verifique se pasta_base está corretamente inicializada
        if not hasattr(self, 'pasta_base') or not isinstance(self.pasta_base, Path):
            self.pasta_base = Path(self.config.get('pasta_base', str(Path.home() / 'Documentos')))  # Exemplo de inicialização

        # Define um nome padrão para a pasta (ou modifique conforme necessário)
        self.nome_pasta = f'{self.id_processo.replace("/", "-")} - {self.objeto.replace("/", "-")}'

        # Botão para criar a estrutura de pastas e abrir a pasta
        icon_criar_pasta = QIcon(str(self.ICONS_DIR / "create-folder.png"))
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
        icon_salvar_pasta = QIcon(str(self.ICONS_DIR / "zip-folder.png"))
        editar_registro_button = create_button("Local de Salvamento", icon=icon_salvar_pasta, callback=self.consolidador.alterar_diretorio_base, tooltip_text="Clique para alterar o local de salvamento dos arquivos", button_size=QSize(210, 40), icon_size=QSize(40, 40))
        apply_widget_style_11(editar_registro_button)
        utilidades_layout.addWidget(editar_registro_button, alignment=Qt.AlignmentFlag.AlignCenter)
        # Botão para abrir o arquivo de registro
        icon_template = QIcon(str(self.ICONS_DIR / "template.png"))
        visualizar_pdf_button = create_button("Editar Modelos", icon=icon_template, callback=self.consolidador.editar_modelo, tooltip_text="Clique para editar os modelos dos documentos", button_size=QSize(210, 40), icon_size=QSize(40, 40))
        apply_widget_style_11(visualizar_pdf_button)
        utilidades_layout.addWidget(visualizar_pdf_button, alignment=Qt.AlignmentFlag.AlignCenter)

        return utilidades_layout
    
    def create_agentes_responsaveis_layout(self):
        # Frame para agentes responsáveis com borda lateral
        frame_agentes = QFrame()
        # Criação do layout principal para os agentes responsáveis
        agente_responsavel_layout = QVBoxLayout(frame_agentes)
        agente_responsavel_layout.setContentsMargins(10, 1, 10, 1)  # Define margens ao redor do layout

        # Criação dos ComboBox com ajuste de altura
        self.ordenador_combo = create_combo_box('', [], 260, 70)
        self.agente_fiscal_combo = create_combo_box('', [], 260, 70)
        self.gerente_credito_combo = create_combo_box('', [], 260, 65)
        self.responsavel_demanda_combo = create_combo_box('', [], 260, 65)
        self.operador_dispensa_combo = create_combo_box('', [], 260, 70)

        # Adicionando labels e ComboBox diretamente ao layout
        labels_combos = [
            ("Ordenador de Despesa:", self.ordenador_combo),
            ("Agente Fiscal:", self.agente_fiscal_combo),
            ("Gerente de Crédito:", self.gerente_credito_combo),
            ("Responsável pela Demanda:", self.responsavel_demanda_combo),
            ("Operador da Contratação:", self.operador_dispensa_combo)
        ]

        for label_text, combo_box in labels_combos:
            # Cria um layout horizontal para a label e o ComboBox
            h_layout = QVBoxLayout()
            h_layout.setSpacing(0)  # Ajusta o espaçamento entre label e ComboBox
            h_layout.setContentsMargins(0, 0, 0, 0)  # Margens para o layout

            # Cria e estiliza a label
            label = QLabel(label_text)
            label.setStyleSheet("color: #8AB4F7; font-size: 16px")
            label.setContentsMargins(0, 0, 0, 0)  # Define margens para a label

            # Adiciona a label e o ComboBox ao layout horizontal
            h_layout.addWidget(label)
            h_layout.addWidget(combo_box)

            # Adiciona o layout horizontal ao layout principal
            agente_responsavel_layout.addLayout(h_layout)

        # Carrega os agentes responsáveis para popular os ComboBoxes
        self.carregarAgentesResponsaveis()

        return frame_agentes

    def carregarAgentesResponsaveis(self):
        try:
            print("Tentando conectar ao banco de dados...")
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_agentes_responsaveis'")
                if cursor.fetchone() is None:
                    raise Exception("A tabela 'controle_agentes_responsaveis' não existe no banco de dados. Configure os Ordenadores de Despesa no Módulo 'Configurações'.")

                print("Tabela 'controle_agentes_responsaveis' encontrada. Carregando dados...")
                self.carregarDadosCombo(conn, cursor, "Ordenador de Despesa%", self.ordenador_combo)
                self.carregarDadosCombo(conn, cursor, "Agente Fiscal%", self.agente_fiscal_combo)
                self.carregarDadosCombo(conn, cursor, "Gerente de Crédito%", self.gerente_credito_combo)
                self.carregarDadosCombo(conn, cursor, "Operador%", self.operador_dispensa_combo)
                self.carregarDadosCombo(conn, cursor, "NOT LIKE", self.responsavel_demanda_combo)
                # Preencher comboboxes com os valores de df_registro_selecionado se disponíveis
                self.preencher_campos()

        except Exception as e:
            print(f"Erro ao carregar Ordenadores de Despesas: {e}")

    def preencher_combobox_selecionado(self, combo_widget, coluna):
        valor = self.df_registro_selecionado.get(coluna)
        if valor:
            index = combo_widget.findText(valor)
            if index != -1:
                combo_widget.setCurrentIndex(index)
                
    def carregarDadosCombo(self, conn, cursor, funcao_like, combo_widget):
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
            # print(f"Valores carregados no ComboBox: {combo_widget.count()} itens")
            
    def create_anexos_group(self):
        # Usar o id_processo armazenado na instância da classe
        id_display = self.id_processo if self.id_processo else 'ID não disponível'

        # GroupBox para Anexos
        anexos_group_box = QGroupBox(f"Anexos da {id_display}")
        apply_widget_style_11(anexos_group_box)

        # Layout principal do GroupBox
        anexo_layout = QVBoxLayout()
        
        self.anexos_dict = {}

        # Função auxiliar para adicionar seções de anexos
        def add_anexo_section(section_title, *anexos):
            section_label = QLabel(section_title)
            self.apply_widget_style_14(section_label)
            anexo_layout.addWidget(section_label)
            self.anexos_dict[section_title] = []

            for anexo in anexos:
                layout = QHBoxLayout()

                # Caminho e tooltip
                pasta_anexo = self.define_pasta_anexo(section_title, anexo)
                tooltip_text = self.define_tooltip_text(section_title, anexo)

                # Verificação de arquivo PDF
                icon_label = QLabel()
                icon = self.get_icon_for_anexo(pasta_anexo)
                icon_label.setPixmap(icon.pixmap(QSize(25, 25)))
                layout.addWidget(icon_label)
                layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

                # Botão para abrir a pasta
                btnabrirpasta = self.create_open_folder_button(pasta_anexo, tooltip_text)
                layout.addWidget(btnabrirpasta)

                # Label do anexo
                anexo_label = QLabel(anexo)
                self.apply_widget_style_12(anexo_label)
                layout.addWidget(anexo_label)
                layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
                layout.addStretch()

                self.anexos_dict[section_title].append((anexo, icon_label))
                anexo_layout.addLayout(layout)

        # Adiciona seções de anexos
        add_anexo_section("Documento de Formalização de Demanda (DFD)", "Anexo A - Relatório do Safin", "Anexo B - Especificações")
        add_anexo_section("Termo de Referência (TR)", "Anexo - Pesquisa de Preços")
        add_anexo_section("Declaração de Adequação Orçamentária", "Anexo - Relatório do PDM/CATSER")

        justificativa_label = QLabel("Justificativas relevantes")
        justificativa_label.setStyleSheet("font-size: 14pt;")  # Ajuste do tamanho da fonte
        anexo_layout.addWidget(justificativa_label)

        # Botões de Ação
        self.add_buttons_to_layout(anexo_layout)

        # Definição do layout final e do GroupBox
        anexos_group_box.setLayout(anexo_layout)

        return anexos_group_box

    def define_pasta_anexo(self, section_title, anexo):
        """Define o caminho da pasta de anexo baseado no título da seção e nome do anexo."""
        id_processo_modificado = self.id_processo.replace("/", "-")
        objeto_modificado = self.objeto.replace("/", "-")

        if section_title == "Documento de Formalização de Demanda (DFD)":
            if "Anexo A" in anexo:
                return self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'DFD' / 'Anexo A - Relatorio Safin'
            elif "Anexo B" in anexo:
                return self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'DFD' / 'Anexo B - Especificações e Quantidade'
        elif section_title == "Termo de Referência (TR)":
            return self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'TR' / 'Pesquisa de Preços'
        elif section_title == "Declaração de Adequação Orçamentária":
            return self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária' / 'Relatório do PDM-Catser'
        return None

    def define_tooltip_text(self, section_title, anexo):
        """Retorna o texto da tooltip para um anexo."""
        if section_title == "Documento de Formalização de Demanda (DFD)":
            if "Anexo A" in anexo:
                return "Abrir pasta Anexo A - Relatório do Safin"
            elif "Anexo B" in anexo:
                return "Abrir pasta Anexo B - Especificações e Quantidade"
        elif section_title == "Termo de Referência (TR)":
            return "Abrir pasta Pesquisa de Preços"
        elif section_title == "Declaração de Adequação Orçamentária":
            return "Abrir pasta Relatório do PDM-Catser"
        return "Abrir pasta"

    def get_icon_for_anexo(self, pasta_anexo):
        """Retorna o ícone correto baseado na existência de arquivos PDF."""
        icon_confirm = QIcon(str(self.ICONS_DIR / "concluido.png"))
        icon_x = QIcon(str(self.ICONS_DIR / "cancel.png"))
        if pasta_anexo and self.verificar_arquivo_pdf(pasta_anexo):
            return icon_confirm
        return icon_x

    def create_open_folder_button(self, pasta_anexo, tooltip_text):
        """Cria um botão para abrir a pasta com o tooltip especificado."""
        icon_abrir_pasta = QIcon(str(self.ICONS_DIR / "open-folder.png"))
        btnabrirpasta = create_button(
            "", icon=icon_abrir_pasta, callback=lambda _, p=pasta_anexo: self.abrir_pasta(p),
            tooltip_text=tooltip_text, button_size=QSize(25, 25), icon_size=QSize(25, 25)
        )
        btnabrirpasta.setToolTipDuration(0)
        return btnabrirpasta

    def add_buttons_to_layout(self, layout):
        """Adiciona os botões de 'Visualizar Anexos' e 'Atualizar Pastas' ao layout."""
        icon_browser = QIcon(str(ICONS_DIR / "browser.png"))
        add_pdf_button = create_button(
            " Visualizar Anexos",
            icon_browser,
            self.add_pdf_to_merger,
            "Visualizar anexos PDFs",
            QSize(220, 40), QSize(30, 30)
        )

        atualizar_button = create_button(
            "   Atualizar Pastas  ",
            QIcon(str(ICONS_DIR / "refresh.png")),
            self.atualizar_action,
            "Atualizar os dados",
            QSize(220, 40), QSize(30, 30)
        )

        button_layout_anexo = QHBoxLayout()
        button_layout_anexo.addStretch()
        button_layout_anexo.addWidget(add_pdf_button)
        button_layout_anexo.addStretch()

        button_layout_atualizar = QHBoxLayout()
        button_layout_atualizar.addStretch()
        button_layout_atualizar.addWidget(atualizar_button)
        button_layout_atualizar.addStretch()

        layout.addLayout(button_layout_anexo)
        layout.addLayout(button_layout_atualizar)

    def create_gerar_documentos_group(self):
        gerar_documentos_layout = QVBoxLayout()

        # Verifica se a estrutura de pastas existe
        pastas_existentes = self.consolidador.verificar_pastas(self.consolidador.pasta_base)

        # Criando layout horizontal para exibir o ícone e o status juntos
        status_layout = QHBoxLayout()

        # Define o ícone com base no status da verificação
        if pastas_existentes:
            self.status_label = QLabel("Pastas encontradas")  # Define status_label como atributo da classe
            self.status_label.setStyleSheet("font-size: 14px;")
            self.icon_label = QLabel()
            icon_folder = QIcon(str(ICONS_DIR / "folder_v.png"))  # Ícone de sucesso
        else:
            self.status_label = QLabel("Pastas não encontradas")  # Define status_label como atributo da classe
            self.status_label.setStyleSheet("font-size: 14px;")
            self.icon_label = QLabel()
            icon_folder = QIcon(str(ICONS_DIR / "folder_x.png"))  # Ícone de erro

        # Define o tamanho do ícone e adiciona ao QLabel
        icon_pixmap = icon_folder.pixmap(30, 30)
        self.icon_label.setPixmap(icon_pixmap)

        # Adiciona o ícone e a mensagem ao layout
        status_layout.addWidget(self.icon_label)
        status_layout.addWidget(self.status_label)

        # Adiciona o ícone e a mensagem ao layout com alinhamento à direita
        status_layout.addStretch()  # Isso empurra todo o conteúdo para a direita


        # Adiciona o layout de status ao layout principal
        gerar_documentos_layout.addLayout(status_layout)

        
        icon_pdf = QIcon(str(ICONS_DIR / "pdf.png"))
        icon_copy = QIcon(str(ICONS_DIR / "copy.png"))

        buttons_info = [
            ("          Autorização para Abertura      ", self.handle_gerar_autorizacao, self.handle_gerar_autorizacao_sidgem),
            (" Comunicação Padronizada e anexos", self.handle_gerar_comunicacao_padronizada, self.handle_gerar_comunicacao_padronizada_sidgem),
            ("              Aviso de Dispensa               ", self.handle_gerar_aviso_dispensa, self.handle_gerar_aviso_dispensa_sidgem)
        ]

        for text, visualizar_callback, sigdem_callback in buttons_info:
            button_layout = QHBoxLayout()

            visualizar_pdf_button = create_button(
                text,
                icon=icon_pdf,
                callback=visualizar_callback,
                tooltip_text="Clique para visualizar o PDF",
                button_size=QSize(310, 40),
                icon_size=QSize(40, 40)
            )
            apply_widget_style_11(visualizar_pdf_button)

            sigdem_button = create_button(
                "",
                icon=icon_copy,
                callback=sigdem_callback,
                tooltip_text="Clique para copiar",
                button_size=QSize(40, 40),
                icon_size=QSize(30, 30)
            )
            apply_widget_style_11(sigdem_button)

            button_layout.addWidget(visualizar_pdf_button)
            button_layout.addWidget(sigdem_button)

            gerar_documentos_layout.addLayout(button_layout)

        return gerar_documentos_layout

    def handle_gerar_autorizacao(self):
        self.assunto_text = f"{self.id_processo} - Abertura de Processo ({self.objeto})"
        self.sinopse_text = (
            f"Termo de Abertura referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel}"
        )
        self.update_text_fields()
        self.consolidador.gerar_autorizacao()

        # Emite o sinal passando a mensagem de status e o ícone de sucesso (folder_v.png)
        self.status_atualizado.emit("Pastas encontradas", str(self.ICONS_DIR / "folder_v.png"))

    def handle_gerar_autorizacao_sidgem(self):
        self.assunto_text = f"{self.id_processo} - Abertura de Processo ({self.objeto})"
        self.sinopse_text = (
            f"Termo de Abertura referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel}"
        )
        self.update_text_fields()

    def handle_gerar_comunicacao_padronizada(self):
        self.assunto_text = f"{self.id_processo} - Documentos de Planejamento ({self.objeto})"
        self.sinopse_text = (
            f"Documentos de Planejamento (DFD, TR e Declaração de Adequação Orçamentária) referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel}"
        )
        self.update_text_fields()
        self.consolidador.gerar_comunicacao_padronizada()

    def handle_gerar_comunicacao_padronizada_sidgem(self):
        self.assunto_text = f"{self.id_processo} - Documentos de Planejamento ({self.objeto})"
        self.sinopse_text = (
            f"Documentos de Planejamento (DFD, TR e Declaração de Adequação Orçamentária) referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel}"
        )
        self.update_text_fields()

    def handle_gerar_aviso_dispensa(self):
        self.assunto_text = f"{self.id_processo} - Aviso ({self.objeto})"
        self.sinopse_text = (
            f"Aviso referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel}"
        )
        self.update_text_fields()
        self.consolidador.gerar_aviso_dispensa()

    def handle_gerar_aviso_dispensa_sidgem(self):
        self.assunto_text = f"{self.id_processo} - Aviso ({self.objeto})"
        self.sinopse_text = (
            f"Aviso referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel}"
        )
        self.update_text_fields()

    def update_text_fields(self):
        self.textEditAssunto.setPlainText(self.assunto_text)
        self.textEditSinopse.setPlainText(self.sinopse_text)

    def create_GrupoSIGDEM(self):
        grupoSIGDEM = QGroupBox("SIGDEM")
        apply_widget_style_11(grupoSIGDEM)

        layout = QVBoxLayout(grupoSIGDEM)

        labelAssunto = QLabel("No campo “Assunto”:")
        labelAssunto.setStyleSheet("font-size: 12pt;")
        layout.addWidget(labelAssunto)
        
        # Usando os atributos da classe para preencher o texto
        self.textEditAssunto = QTextEdit(f"{self.id_processo} - Abertura de Processo ({self.objeto})")
        self.textEditAssunto.setStyleSheet("font-size: 12pt;")
        self.textEditAssunto.setMaximumHeight(60)
        layoutHAssunto = QHBoxLayout()
        layoutHAssunto.addWidget(self.textEditAssunto)
        
        icon_copy = QIcon(str(self.ICONS_DIR / "copy_1.png"))
        btnCopyAssunto = create_button(text="", icon=icon_copy, callback=lambda: self.copyToClipboard(self.textEditAssunto.toPlainText()), tooltip_text="Copiar texto para a área de transferência", button_size=QSize(40, 40), icon_size=QSize(25, 25))
        layoutHAssunto.addWidget(btnCopyAssunto)
        layout.addLayout(layoutHAssunto)

        labelSinopse = QLabel("No campo “Sinopse”:")
        labelSinopse.setStyleSheet("font-size: 12pt;")
        layout.addWidget(labelSinopse)
        
        # Usando os atributos da classe para preencher o texto
        self.textEditSinopse = QTextEdit(
            f"Termo de Abertura referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel}"
        )
        self.textEditSinopse.setStyleSheet("font-size: 12pt;")
        self.textEditSinopse.setMaximumHeight(140)
        
        layoutHSinopse = QHBoxLayout()
        layoutHSinopse.addWidget(self.textEditSinopse)
        
        btnCopySinopse = create_button(text="", icon=icon_copy, callback=lambda: self.copyToClipboard(self.textEditSinopse.toPlainText()), tooltip_text="Copiar texto para a área de transferência", button_size=QSize(40, 40), icon_size=QSize(25, 25))
        layoutHSinopse.addWidget(btnCopySinopse)
        layout.addLayout(layoutHSinopse)

        grupoSIGDEM.setLayout(layout)
        self.carregarAgentesResponsaveis()
        
        return grupoSIGDEM

    def get_descricao_servico(self):
        return "aquisição de" if self.material_servico == "Material" else "contratação de empresa especializada em"

    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QToolTip.showText(QCursor.pos(), "Texto copiado para a área de transferência.", msecShowTime=1500)

    def on_autorizacao_clicked(self):
        print("Botão Autorização clicado")  # Substitua esta função pela funcionalidade desejada

    def abrir_pasta(self, pasta):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pasta)))

    def verificar_subpasta(self):
        id_processo_modificado = self.id_processo.replace("/", "-")
        objeto_modificado = self.objeto.replace("/", "-")
        pastas_encontradas = []
        for subpasta in self.pasta_base.iterdir():
            if subpasta.is_dir() and id_processo_modificado in subpasta.name and objeto_modificado in subpasta.name:
                pastas_encontradas.append(subpasta.name)
                print(f"Pasta encontrada: {subpasta.name}")
        return pastas_encontradas

    def verificar_arquivo_pdf(self, pasta):
        arquivos_pdf = []
        if not pasta.exists():
            print(f"Pasta não encontrada: {pasta}")
            return None
        for arquivo in pasta.iterdir():
            if arquivo.suffix.lower() == ".pdf":
                arquivos_pdf.append(arquivo)
                # print(f"Arquivo PDF encontrado: {arquivo.name}")
        if arquivos_pdf:
            return max(arquivos_pdf, key=lambda p: p.stat().st_mtime)  # Retorna o PDF mais recente
        return None
    
    def verificar_e_criar_pastas(self, pasta_base):
        try:
            id_processo_modificado = self.id_processo.replace("/", "-")
            objeto_modificado = self.objeto.replace("/", "-")
            base_path = pasta_base / f'{id_processo_modificado} - {objeto_modificado}'

            pastas_necessarias = [
                pasta_base / '1. Autorizacao',
                pasta_base / '2. CP e anexos',
                pasta_base / '3. Aviso',
                pasta_base / '2. CP e anexos' / 'DFD',
                pasta_base / '2. CP e anexos' / 'DFD' / 'Anexo A - Relatorio Safin',
                pasta_base / '2. CP e anexos' / 'DFD' / 'Anexo B - Especificações e Quantidade',
                pasta_base / '2. CP e anexos' / 'TR',
                pasta_base / '2. CP e anexos' / 'TR' / 'Pesquisa de Preços',
                pasta_base / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária',
                pasta_base / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária' / 'Relatório do PDM-Catser',
                pasta_base / '2. CP e anexos' / 'Justificativas Relevantes',
            ]

            for pasta in pastas_necessarias:
                if not pasta.exists():
                    pasta.mkdir(parents=True)

        except (FileNotFoundError, PermissionError) as e:
            QMessageBox.critical(self, "Erro ao criar pastas", f"Não foi possível criar as pastas necessárias devido ao erro: {str(e)}. Por favor, selecione uma nova pasta base na aba 'Documentos'.")
            
        return pastas_necessarias

    def add_pdf_to_merger(self):
        cp_number = self.cp_edit.text()
        if cp_number:
            pastas_necessarias = self.verificar_e_criar_pastas(self.pasta_base)
            pdf_add_dialog = PDFAddDialog(self.df_registro_selecionado, self.ICONS_DIR, pastas_necessarias, self.pasta_base, self)
            if pdf_add_dialog.exec():
                print(f"Adicionar PDF para CP nº {cp_number}")
            else:
                print("Ação de adicionar PDF cancelada.")
        else:
            QMessageBox.warning(self, "Erro", "Por favor, insira um número de CP válido.")

    def atualizar_action(self):
        icon_confirm = QIcon(str(self.ICONS_DIR / "concluido.png"))
        icon_x = QIcon(str(self.ICONS_DIR / "cancel.png"))

        def atualizar_anexo(section_title, anexo, label):
            pasta_anexo = None
            id_processo_modificado = self.id_processo.replace("/", "-")
            objeto_modificado = self.objeto.replace("/", "-")

            if section_title == "Documento de Formalização de Demanda (DFD)":
                if "Anexo A" in anexo:
                    pasta_anexo = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'DFD' / 'Anexo A - Relatorio Safin'
                elif "Anexo B" in anexo:
                    pasta_anexo = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'DFD' / 'Anexo B - Especificações e Quantidade'
            elif section_title == "Termo de Referência (TR)":
                pasta_anexo = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'TR' / 'Pesquisa de Preços'
            elif section_title == "Declaração de Adequação Orçamentária":
                pasta_anexo = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária' / 'Relatório do PDM-Catser'

            if pasta_anexo:
                print(f"Verificando pasta: {pasta_anexo}")
                arquivos_pdf = self.verificar_arquivo_pdf(pasta_anexo)
                icon = icon_confirm if arquivos_pdf else icon_x
                label.setPixmap(icon.pixmap(QSize(25, 25)))
            else:
                print(f"Anexo não identificado: {anexo}")
                label.setPixmap(icon_x.pixmap(QSize(25, 25)))

        for section_title, anexos in self.anexos_dict.items():
            for anexo, icon_label in anexos:
                atualizar_anexo(section_title, anexo, icon_label)

        self.dados_atualizados.emit()
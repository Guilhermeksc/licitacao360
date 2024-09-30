from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento.utilidades_planejamento import DatabaseManager
from modules.dispensa_eletronica.documentos_cp_dfd_tr import PDFAddDialog, ConsolidarDocumentos, load_config_path_id
from modules.dispensa_eletronica.utils_dispensa_eletronica import RealLineEdit
from modules.dispensa_eletronica.dados_api.api_consulta import PNCPConsultaThread, PNCPConsulta
from modules.dispensa_eletronica.formulario_excel import FormularioExcel
from modules.planejamento_novo.edit_data.edit_dialog_utils import EditDataDialogUtils
from modules.planejamento_novo.edit_data.stacked_widget import StackedWidgetManager
from diretorios import *
from pathlib import Path
import pandas as pd
from pathlib import Path
import sqlite3
import webbrowser
from datetime import datetime

class EditDataDialog(QDialog):
    dados_atualizados = pyqtSignal()
    title_updated = pyqtSignal(str)
    status_atualizado = pyqtSignal(str, str)

    def __init__(self, df_registro_selecionado, icons_dir, parent=None):
        super().__init__(parent)
        self.df_registro_selecionado = df_registro_selecionado
        self.ICONS_DIR = Path(icons_dir)

        # Inicializações
        self.navigation_buttons = []
        self.consolidador = ConsolidarDocumentos(df_registro_selecionado)
        self._init_paths()
        self.formulario_excel = FormularioExcel(self.df_registro_selecionado, self.pasta_base, self)
        # Extrair os dados e armazenar como atributos da classe
        self.set_registro_data()

        # Inicializar o gerenciador do StackedWidget
        self.stacked_widget_manager = StackedWidgetManager(self, self.df_registro_selecionado)

        # Criar layout
        self._init_ui()
        self._init_connections()

        # Conectar o sinal ao método que atualiza o status_label
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
        layout_principal.addWidget(EditDataDialogUtils.update_title_label(self.df_registro_selecionado))

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
        formulario_group_box = self.create_frame_formulario_group()
        layout_orcamentario_formulario.addWidget(formulario_group_box)

        # Cria o "Formulário de Dados" e adiciona ao layout vertical
        pncp_group_box = self.create_frame_pncp()
        layout_orcamentario_formulario.addWidget(pncp_group_box)

        # Adiciona o layout vertical ao layout horizontal
        hbox_top_layout.addLayout(layout_orcamentario_formulario)

        # Adiciona o layout horizontal ao layout principal
        layout.addLayout(hbox_top_layout)
        frame.setLayout(layout)

        return frame

    def create_contratacao_group(self, data):
        contratacao_group_box = QGroupBox("Contratação")
        self.apply_widget_style(contratacao_group_box)
        contratacao_group_box.setFixedWidth(700)
        # Coluna da esquerda - Contratação
        contratacao_layout = QVBoxLayout()

        # Objeto
        self.objeto_edit = QLineEdit(data['objeto'])

        # Criando um layout horizontal para o campo de entrada de texto e o ícone
        objeto_layout = QHBoxLayout()

        objeto_label = QLabel("Objeto:")
        objeto_layout.addWidget(objeto_label)
        objeto_layout.addWidget(self.objeto_edit)

        # Aplicando estilo diretamente aos widgets dentro do layout
        self.apply_widget_style(self.objeto_edit)

        # Adicionando o layout horizontal diretamente ao layout principal de contratação
        contratacao_layout.addLayout(objeto_layout)

        # Configuração Situação
        situacao_layout = QHBoxLayout()
        situacao_label = QLabel("Situação:")
        self.apply_widget_style(situacao_label)
        self.situacao_edit = self.create_combo_box(data.get('status', 'Planejamento'), ["Planejamento", "Consolidar Demandas", "Montagem do Processo", "Nota Técnica", "AGU", "Recomendações AGU", "Sessão Pública",  "Assinatura Contrato", "Concluído"], 185, 35)
        situacao_layout.addWidget(situacao_label)
        situacao_layout.addWidget(self.situacao_edit)
        contratacao_layout.addLayout(situacao_layout)

        # Adiciona outros layouts ao layout de contratação
        self.nup_edit = QLineEdit(data['nup'])
        contratacao_layout.addLayout(self.create_layout("NUP:", self.nup_edit))

        # Configuração de Material/Serviço na mesma linha
        material_layout = QHBoxLayout()
        material_label = QLabel("Material/Serviço:")
        self.apply_widget_style(material_label)
        self.material_edit = self.create_combo_box(data.get('material_servico', 'Material'), ["Material", "Serviço"], 185, 35)
        material_layout.addWidget(material_label)
        material_layout.addWidget(self.material_edit)
        contratacao_layout.addLayout(material_layout)

        # Configuração da Data da Sessão na mesma linha
        data_layout = QHBoxLayout()
        data_label = QLabel("Data da Sessão Pública:")
        self.apply_widget_style(data_label)
        self.data_edit = QDateEdit()
        # self.data_edit.setFixedWidth(120)
        self.data_edit.setCalendarPopup(True)
        data_sessao_str = data.get('data_sessao', '')
        if data_sessao_str:
            self.data_edit.setDate(QDate.fromString(data_sessao_str, "yyyy-MM-dd"))
        else:
            self.data_edit.setDate(QDate.currentDate())
        data_layout.addWidget(data_label)
        data_layout.addWidget(self.data_edit)
        contratacao_layout.addLayout(data_layout)

        previsao_contratacao_layout = QHBoxLayout()
        previsao_contratacao_label = QLabel("Previsão da Contratação:")
        self.apply_widget_style(previsao_contratacao_label)
        self.previsao_contratacao_edit = QDateEdit()
        # self.previsao_contratacao_edit.setFixedWidth(120)
        self.previsao_contratacao_edit.setCalendarPopup(True)
        previsao_contratacao_str = data.get('previsao_contratacao', '')
        if previsao_contratacao_str:
            self.previsao_contratacao_edit.setDate(QDate.fromString(previsao_contratacao_str, "yyyy-MM-dd"))
        else:
            self.previsao_contratacao_edit.setDate(QDate.currentDate())
        previsao_contratacao_layout.addWidget(previsao_contratacao_label)
        previsao_contratacao_layout.addWidget(self.previsao_contratacao_edit)
        contratacao_layout.addLayout(previsao_contratacao_layout)

        # Vigência
        self.vigencia_edit = QComboBox()
        self.vigencia_edit.setEditable(True)
        for i in range(1, 13):
            self.vigencia_edit.addItem(f"{i} ({self.number_to_text(i)}) meses")
        vigencia = data.get('vigencia', '2 (dois) meses')
        self.vigencia_edit.setCurrentText(vigencia)
        contratacao_layout.addLayout(self.create_layout("Vigência:", self.vigencia_edit))

        # Configuração de Critério de Julgamento na mesma linha
        criterio_layout = QHBoxLayout()
        criterio_label = QLabel("Critério Julgamento:")
        self.apply_widget_style(criterio_label)
        self.criterio_edit = self.create_combo_box(data.get('criterio_julgamento', 'Menor Preço'), ["Menor Preço", "Maior Desconto"], 185, 35)
        criterio_layout.addWidget(criterio_label)
        criterio_layout.addWidget(self.criterio_edit)
        contratacao_layout.addLayout(criterio_layout)

        # Criando o ícone
        icon = QIcon(str(self.ICONS_DIR / "prioridade.png"))
        icon_pixmap = icon.pixmap(27, 27)  # Definindo o tamanho do ícone
        icon_label = QLabel()  # Criando o QLabel para o ícone
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(30, 30)

        # Layout horizontal para todos os checkboxes
        checkboxes_layout = QHBoxLayout()

        checkbox_style = """
            QCheckBox::indicator {
                width: 30px;
                height: 30px;
            }
        """
        
        # Checkbox para "Prioritário?" com ícone
        self.checkbox_prioritario = QCheckBox("Prioritário")
        self.checkbox_prioritario.setStyleSheet(checkbox_style)
        icon_prioritario = QIcon(str(self.ICONS_DIR / "prioridade.png"))
        self.checkbox_prioritario.setIcon(icon_prioritario)
        self.checkbox_prioritario.setIconSize(QSize(27, 27))
        pesquisa_preco_value = data.get('pesquisa_preco', 'Não')
        self.checkbox_prioritario.setChecked(pesquisa_preco_value == 'Sim')

        checkboxes_layout.addWidget(self.checkbox_prioritario)

        # Checkbox para "Emenda Parlamentar?" com ícone
        self.checkbox_emenda = QCheckBox("Emenda Parlamentar")
        self.checkbox_emenda.setStyleSheet(checkbox_style)
        icon_emenda = QIcon(str(self.ICONS_DIR / "subsidy.png"))
        self.checkbox_emenda.setIcon(icon_emenda)
        self.checkbox_emenda.setIconSize(QSize(27, 27))
        emenda_value = data.get('atividade_custeio', 'Não')
        self.checkbox_emenda.setChecked(emenda_value == 'Sim')

        checkboxes_layout.addWidget(self.checkbox_emenda)
        
        # Checkbox para "Registro de Preços?" com ícone
        self.checkbox_registro_precos = QCheckBox("SRP")
        self.checkbox_registro_precos.setStyleSheet(checkbox_style)        
        icon_registro_precos = QIcon(str(self.ICONS_DIR / "price-tag.png"))  # Substitua pelo ícone correto
        self.checkbox_registro_precos.setIcon(icon_registro_precos)
        self.checkbox_registro_precos.setIconSize(QSize(27, 27))
        registro_precos_value = data.get('registro_precos', 'Não')
        self.checkbox_registro_precos.setChecked(registro_precos_value == 'Sim')

        checkboxes_layout.addWidget(self.checkbox_registro_precos)

        # Checkbox para "Atividade de Custeio?" com ícone
        self.checkbox_atividade_custeio = QCheckBox("Atividade de Custeio")
        self.checkbox_atividade_custeio.setStyleSheet(checkbox_style)        
        icon_atividade_custeio = QIcon(str(self.ICONS_DIR / "custeio.png"))  # Substitua pelo ícone correto
        self.checkbox_atividade_custeio.setIcon(icon_atividade_custeio)
        self.checkbox_atividade_custeio.setIconSize(QSize(27, 27))
        atividade_custeio_value = data.get('atividade_custeio', 'Não')
        self.checkbox_atividade_custeio.setChecked(atividade_custeio_value == 'Sim')

        checkboxes_layout.addWidget(self.checkbox_atividade_custeio)

        # Adiciona o layout de checkboxes ao layout principal
        contratacao_layout.addLayout(checkboxes_layout)

        contratacao_group_box.setLayout(contratacao_layout)

        return contratacao_group_box

    def validate_and_convert_date(self, date_str):
        """Valida e converte uma string de data para QDate."""
        try:
            # Tenta converter a string para datetime
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            # Converte datetime para QDate
            return QDate(parsed_date.year, parsed_date.month, parsed_date.day)
        except (ValueError, TypeError):
            # Retorna None se houver erro na conversão
            return None
        
    def on_link_pncp_clicked(self):
        cnpj = self.cnpj_matriz_edit.text()  # Valor do CNPJ Matriz
        ano = self.ano  # Valor do Ano
        sequencial_pncp = self.link_pncp_edit.text()  # Valor do Sequencial PNCP

        # Montando a URL
        url = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{sequencial_pncp}"

        # Abrindo o link no navegador padrão
        QDesktopServices.openUrl(QUrl(url))

    def create_classificacao_orcamentaria_group(self):
        data = EditDataDialogUtils.extract_registro_data(self.df_registro_selecionado)
        classificacao_orcamentaria_group_box = QGroupBox("Classificação Orçamentária")
        self.apply_widget_style(classificacao_orcamentaria_group_box)
        classificacao_orcamentaria_group_box.setFixedWidth(350)  
        classificacao_orcamentaria_layout = QVBoxLayout()

        # Valor Estimado
        self.valor_edit = RealLineEdit(str(data['valor_total']) if pd.notna(data['valor_total']) else "")
        valor_layout = QHBoxLayout()
        valor_label = QLabel("Valor Estimado:")
        valor_layout.addWidget(valor_label)
        valor_layout.addWidget(self.valor_edit)

        # Criando o ícone
        icon_label_layout = QLabel()
        icon_valor = QIcon(str(self.ICONS_DIR / "emenda_parlamentar.png"))
        icon_pixmap_valor = icon_valor.pixmap(27, 27)  # Definindo o tamanho do ícone
        icon_label_layout.setPixmap(icon_pixmap_valor)
        icon_label_layout.setFixedSize(30, 30)

        # Adicionando o ícone ao layout
        valor_layout.addWidget(icon_label_layout, alignment=Qt.AlignmentFlag.AlignRight)

        classificacao_orcamentaria_layout.addLayout(valor_layout)

        self.acao_interna_edit = QLineEdit(data['acao_interna'])
        self.fonte_recurso_edit = QLineEdit(data['fonte_recursos'])
        self.natureza_despesa_edit = QLineEdit(data['natureza_despesa'])
        self.unidade_orcamentaria_edit = QLineEdit(data['unidade_orcamentaria'])
        self.ptres_edit = QLineEdit(data['programa_trabalho_resuminho'])

        classificacao_orcamentaria_layout.addLayout(self.create_layout("Ação Interna:", self.acao_interna_edit))
        classificacao_orcamentaria_layout.addLayout(self.create_layout("Fonte de Recurso (FR):", self.fonte_recurso_edit))
        classificacao_orcamentaria_layout.addLayout(self.create_layout("Natureza de Despesa (ND):", self.natureza_despesa_edit))
        classificacao_orcamentaria_layout.addLayout(self.create_layout("Unidade Orçamentária (UO):", self.unidade_orcamentaria_edit))
        classificacao_orcamentaria_layout.addLayout(self.create_layout("PTRES:", self.ptres_edit))
    
        classificacao_orcamentaria_group_box.setLayout(classificacao_orcamentaria_layout)

        return classificacao_orcamentaria_group_box


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
        
        button_confirm = self.create_button(" Salvar", icon_confirm, self.save_changes, "Salvar dados", QSize(110, 30), QSize(30, 30))
        layout.addWidget(button_confirm)
        self.apply_widget_style(button_confirm)
    
    def create_group_box(self, title, details):
        group_box = QGroupBox(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(details))
        group_box.setLayout(layout)
        return group_box

    def stacked_widget(self):
        # Preenche o formulário de documentos
        frame = QFrame()
        layout = QVBoxLayout()
        layout.addWidget(QLabel())
        frame.setLayout(layout)
        return frame
    
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
    
    def save_changes(self):
        try:
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

            # Verificar se as colunas 'uf' e 'codigoMunicipioIbge' estão presentes
            if 'uf' in self.df_registro_selecionado.columns:
                data['uf'] = self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], 'uf']
            
            if 'codigoMunicipioIbge' in self.df_registro_selecionado.columns:
                data['codigoMunicipioIbge'] = self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], 'codigoMunicipioIbge']

            # Atualizar o DataFrame com os novos valores
            for key, value in data.items():
                self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], key] = value

            # Atualizar banco de dados
            self.update_database(data)
            self.dados_atualizados.emit()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao salvar as alterações: {str(e)}")

    def update_database(self, data):
        try:
            with self.database_manager as connection:
                cursor = connection.cursor()

                # Apenas incluir colunas que realmente existem no banco de dados
                available_columns = self.get_available_columns(cursor)  # Função que retorna as colunas disponíveis no banco

                # Filtrar os dados com base nas colunas disponíveis
                filtered_data = {key: value for key, value in data.items() if key in available_columns}

                set_part = ', '.join([f"{key} = ?" for key in filtered_data.keys()])
                valores = list(filtered_data.values())
                valores.append(self.df_registro_selecionado['id_processo'].iloc[0])

                query = f"UPDATE controle_processos SET {set_part} WHERE id_processo = ?"
                cursor.execute(query, valores)
                connection.commit()

                QMessageBox.information(self, "Atualização", "As alterações foram salvas com sucesso.")
        
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar o banco de dados: {str(e)}")

    def get_available_columns(self, cursor):
        # Função que obtém as colunas existentes na tabela 'controle_dispensas'
        cursor.execute("PRAGMA table_info(controle_dispensas)")
        columns_info = cursor.fetchall()
        return [col[1] for col in columns_info]  # O segundo elemento em cada tupla é o nome da coluna

    def fill_frame_dados_do_setor_resposavel_contratacao(self):
        frame = QFrame(self)
        layout = QVBoxLayout()

        label_setor = QLabel("Setor Responsável")
        layout.addWidget(label_setor)

        frame.setLayout(layout)
        return frame

    def apply_widget_style(self, widget):
        widget.setStyleSheet("font-size: 11pt;") 

    def apply_widget_style_11(self, widget):
        widget.setStyleSheet("font-size: 11pt;") 

    def apply_widget_style_12(self, widget):
        widget.setStyleSheet("font-size: 12pt;") 

    def apply_widget_style_14(self, widget):
        widget.setStyleSheet("font-size: 14pt;") 

    def create_combo_box(self, current_text, items, fixed_width, fixed_height):
        combo_box = QComboBox()
        combo_box.addItems(items)
        combo_box.setFixedWidth(fixed_width)
        combo_box.setFixedHeight(fixed_height)  # Define a altura fixa do ComboBox
        combo_box.setStyleSheet("QComboBox { font-size: 12px; }")  # Ajusta o estilo para melhor visualização
        self.apply_widget_style(combo_box)
        combo_box.setCurrentText(current_text)
        return combo_box

    def create_layout(self, label_text, widget, fixed_width=None):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        self.apply_widget_style(label)
        
        # Adiciona a largura fixa se especificada
        if fixed_width and isinstance(widget, QWidget):
            widget.setFixedWidth(fixed_width)
        
        # Aplica estilo apenas se o widget for uma instância de QWidget
        if isinstance(widget, QWidget):
            self.apply_widget_style(widget)
        
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout
    
    def number_to_text(self, number):
        numbers_in_words = ["um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze"]
        return numbers_in_words[number - 1] 

    def create_frame_formulario_group(self):
        formulario_group_box = QGroupBox("Formulário de Dados")
        self.apply_widget_style(formulario_group_box)   
        formulario_group_box.setFixedWidth(350)   
        formulario_layout = QVBoxLayout()

        # Adicionando os botões ao layout
        icon_excel_up = QIcon(str(self.ICONS_DIR / "excel_up.png"))
        icon_excel_down = QIcon(str(self.ICONS_DIR / "excel_down.png"))

        criar_formulario_button = self.create_button(
            "   Criar Formulário   ", 
            icon=icon_excel_up, 
            callback=self.formulario_excel.criar_formulario, 
            tooltip_text="Clique para criar o formulário", 
            button_size=QSize(220, 50), 
            icon_size=QSize(45, 45)
        )

        carregar_formulario_button = self.create_button(
            "Carregar Formulário", 
            icon=icon_excel_down, 
            callback=self.formulario_excel.carregar_formulario, 
            tooltip_text="Clique para carregar o formulário", 
            button_size=QSize(220, 50), 
            icon_size=QSize(45, 45)
        )

        formulario_layout.addWidget(criar_formulario_button, alignment=Qt.AlignmentFlag.AlignCenter)
        formulario_layout.addWidget(carregar_formulario_button, alignment=Qt.AlignmentFlag.AlignCenter)
        formulario_group_box.setLayout(formulario_layout)

        return formulario_group_box

    def create_frame_pncp(self):
        data = EditDataDialogUtils.extract_registro_data(self.df_registro_selecionado)
        pncp_group_box = QGroupBox("Integração ao PNCP")
        self.apply_widget_style(pncp_group_box)   
        pncp_group_box.setFixedWidth(350)   
        pncp_layout = QVBoxLayout()

        cnpj_layout = QHBoxLayout()

        # Criação do campo de texto com o valor '00394502000144'
        self.cnpj_matriz_edit = QLineEdit('00394502000144')
        cnpj_layout.addLayout(self.create_layout("CNPJ Matriz:", self.cnpj_matriz_edit))

        # Adicionando o campo CNPJ ao layout principal antes do campo "Sequencial PNCP"
        pncp_layout.addLayout(cnpj_layout)

        # Layout Link PNCP
        link_pncp_layout = QHBoxLayout()

        self.link_pncp_edit = QLineEdit(data.get('link_pncp', ''))
        link_pncp_layout.addLayout(self.create_layout("Sequencial PNCP:", self.link_pncp_edit))

        icon_link = QIcon(str(self.ICONS_DIR / "link.png"))
        link_pncp_button = self.create_button(
            "",
            icon=icon_link,
            callback=self.on_link_pncp_clicked,
            tooltip_text="Clique para acessar o Link da dispensa no Portal Nacional de Contratações Públicas (PNCP)",
            button_size=QSize(30, 30),
            icon_size=QSize(30, 30)
        )
        self.apply_widget_style(link_pncp_button)
        link_pncp_layout.addWidget(link_pncp_button)

        # Adicionando o layout do campo Sequencial PNCP
        pncp_layout.addLayout(link_pncp_layout)

        pncp_group_box.setLayout(pncp_layout)

        return pncp_group_box

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
    
    """
    
    
    
    



    
    PARTE REFERENTE AS UTILIDADES
    
    






    """
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
        criar_pasta_button = self.create_button(
            "Criar e Abrir Pasta", 
            icon=icon_criar_pasta, 
            callback=self.criar_e_abrir_pasta,  # Chama a função que cria e abre a pasta
            tooltip_text="Clique para criar a estrutura de pastas e abrir", 
            button_size=QSize(210, 40), 
            icon_size=QSize(40, 40)
        )
        self.apply_widget_style(criar_pasta_button)
        utilidades_layout.addWidget(criar_pasta_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Botão para abrir o arquivo de registro
        icon_salvar_pasta = QIcon(str(self.ICONS_DIR / "zip-folder.png"))
        editar_registro_button = self.create_button("Local de Salvamento", icon=icon_salvar_pasta, callback=self.consolidador.alterar_diretorio_base, tooltip_text="Clique para alterar o local de salvamento dos arquivos", button_size=QSize(210, 40), icon_size=QSize(40, 40))
        self.apply_widget_style(editar_registro_button)
        utilidades_layout.addWidget(editar_registro_button, alignment=Qt.AlignmentFlag.AlignCenter)
        # Botão para abrir o arquivo de registro
        icon_template = QIcon(str(self.ICONS_DIR / "template.png"))
        visualizar_pdf_button = self.create_button("Editar Modelos", icon=icon_template, callback=self.consolidador.editar_modelo, tooltip_text="Clique para editar os modelos dos documentos", button_size=QSize(210, 40), icon_size=QSize(40, 40))
        self.apply_widget_style(visualizar_pdf_button)
        utilidades_layout.addWidget(visualizar_pdf_button, alignment=Qt.AlignmentFlag.AlignCenter)


        return utilidades_layout
    
    """
    
    
    
    



    
    PARTE REFERENTE AO GROUPO DOS AGENTES RESPONSAVEIS
    
    






    """

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

    # Função para criar o layout e realizar as operações do grupo PNCP
    def create_pncp_group(self):
        # GroupBox para os dados integrados ao PNCP
        anexos_group_box = QGroupBox("Dados integrados ao PNCP")
        self.apply_widget_style(anexos_group_box)

        # Layout para o GroupBox
        layout = QVBoxLayout()
        icon_api = QIcon(str(self.ICONS_DIR / "api.png"))

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
        icon_homologado = QIcon(str(self.ICONS_DIR / "checked.png"))
        icon_nao_homologado = QIcon(str(self.ICONS_DIR / "alert.png"))

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

    def on_erro_consulta(self, mensagem):
        """Manuseia o erro da consulta exibindo uma mensagem."""
        # Fechar a barra de progresso
        self.progress_dialog.close()

        # Exibir mensagem de erro
        QMessageBox.critical(self, "Erro na Consulta", mensagem)

        # Reabilitar o botão de consulta
        self.consulta_button.setEnabled(True)

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
            
    def create_anexos_group(self):
        # Usar o id_processo armazenado na instância da classe
        id_display = self.id_processo if self.id_processo else 'ID não disponível'

        # GroupBox para Anexos
        anexos_group_box = QGroupBox(f"Anexos da {id_display}")
        self.apply_widget_style(anexos_group_box)

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
        btnabrirpasta = self.create_button(
            "", icon=icon_abrir_pasta, callback=lambda _, p=pasta_anexo: self.abrir_pasta(p),
            tooltip_text=tooltip_text, button_size=QSize(25, 25), icon_size=QSize(25, 25)
        )
        btnabrirpasta.setToolTipDuration(0)
        return btnabrirpasta

    def add_buttons_to_layout(self, layout):
        """Adiciona os botões de 'Visualizar Anexos' e 'Atualizar Pastas' ao layout."""
        icon_browser = QIcon(str(self.ICONS_DIR / "browser.png"))
        add_pdf_button = self.create_button(
            " Visualizar Anexos",
            icon_browser,
            self.add_pdf_to_merger,
            "Visualizar anexos PDFs",
            QSize(220, 40), QSize(30, 30)
        )

        atualizar_button = self.create_button(
            "   Atualizar Pastas  ",
            QIcon(str(self.ICONS_DIR / "refresh.png")),
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
            icon_folder = QIcon(str(self.ICONS_DIR / "folder_v.png"))  # Ícone de sucesso
        else:
            self.status_label = QLabel("Pastas não encontradas")  # Define status_label como atributo da classe
            self.status_label.setStyleSheet("font-size: 14px;")
            self.icon_label = QLabel()
            icon_folder = QIcon(str(self.ICONS_DIR / "folder_x.png"))  # Ícone de erro

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

        
        icon_pdf = QIcon(str(self.ICONS_DIR / "pdf.png"))
        icon_copy = QIcon(str(self.ICONS_DIR / "copy.png"))

        buttons_info = [
            ("          Autorização para Abertura      ", self.handle_gerar_autorizacao, self.handle_gerar_autorizacao_sidgem),
            (" Comunicação Padronizada e anexos", self.handle_gerar_comunicacao_padronizada, self.handle_gerar_comunicacao_padronizada_sidgem),
            ("              Aviso de Dispensa               ", self.handle_gerar_aviso_dispensa, self.handle_gerar_aviso_dispensa_sidgem)
        ]

        for text, visualizar_callback, sigdem_callback in buttons_info:
            button_layout = QHBoxLayout()

            visualizar_pdf_button = self.create_button(
                text,
                icon=icon_pdf,
                callback=visualizar_callback,
                tooltip_text="Clique para visualizar o PDF",
                button_size=QSize(310, 40),
                icon_size=QSize(40, 40)
            )
            self.apply_widget_style(visualizar_pdf_button)

            sigdem_button = self.create_button(
                "",
                icon=icon_copy,
                callback=sigdem_callback,
                tooltip_text="Clique para copiar",
                button_size=QSize(40, 40),
                icon_size=QSize(30, 30)
            )
            self.apply_widget_style(sigdem_button)

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
        self.apply_widget_style(grupoSIGDEM)

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
        btnCopyAssunto = self.create_button(text="", icon=icon_copy, callback=lambda: self.copyToClipboard(self.textEditAssunto.toPlainText()), tooltip_text="Copiar texto para a área de transferência", button_size=QSize(40, 40), icon_size=QSize(25, 25))
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
        
        btnCopySinopse = self.create_button(text="", icon=icon_copy, callback=lambda: self.copyToClipboard(self.textEditSinopse.toPlainText()), tooltip_text="Copiar texto para a área de transferência", button_size=QSize(40, 40), icon_size=QSize(25, 25))
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

    def create_irp_group(self):
        data = EditDataDialogUtils.extract_registro_data(self.df_registro_selecionado)

        # Cria o QGroupBox para o grupo de IRP
        irp_group_box = QGroupBox("Dados relativos à Intenção de Registro de Preços (IRP)")
        self.apply_widget_style(irp_group_box)

        # Layout principal
        irp_layout = QVBoxLayout()

        # Inicializando dicionários de line_edits e date_edits se ainda não estiverem inicializados
        if not hasattr(self, 'line_edits'):
            self.line_edits = {}
        if not hasattr(self, 'date_edits'):
            self.date_edits = {}

        # Layout de texto (msg_irp e num_irp)
        irp_text_layout = QVBoxLayout()

        # QHBoxLayout para msg_irp
        msg_irp_layout = QHBoxLayout()
        label_msg_irp = QLabel("Data/Hora MSG:")
        self.line_edit_msg_irp = QLineEdit()
        self.line_edit_msg_irp.setText(data.get('msg_irp', ''))
        msg_irp_layout.addWidget(label_msg_irp)
        msg_irp_layout.addWidget(self.line_edit_msg_irp)
        irp_text_layout.addLayout(msg_irp_layout)
        self.line_edits['msg_irp'] = self.line_edit_msg_irp

        # QHBoxLayout para num_irp
        num_irp_layout = QHBoxLayout()
        label_num_irp = QLabel("Número IRP:")
        self.line_edit_num_irp = QLineEdit()
        self.line_edit_num_irp.setText(data.get('num_irp', ''))  # Corrigido para usar 'data' em vez de 'self.dados'
        num_irp_layout.addWidget(label_num_irp)
        num_irp_layout.addWidget(self.line_edit_num_irp)
        irp_text_layout.addLayout(num_irp_layout)
        self.line_edits['num_irp'] = self.line_edit_num_irp

        # Adicionar o QVBoxLayout de textos ao layout principal
        irp_layout.addLayout(irp_text_layout)

        # Layout para as datas (data_limite_manifestacao_irp e data_limite_confirmacao_irp)
        irp_date_layout = QVBoxLayout()

        # Campos de data com QDateEdit
        date_fields = {
            'data_limite_manifestacao_irp': "Limite para Manifestação",
            'data_limite_confirmacao_irp': "Limite para Confirmação"
        }

        for field, label_text in date_fields.items():
            date_layout = QVBoxLayout()
            label = QLabel(label_text + ':')
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_str = data.get(field)  # Corrigido para usar 'data' em vez de 'self.dados'
            valid_date = self.validate_and_convert_date(date_str)
            if valid_date:
                date_edit.setDate(valid_date)
            else:
                date_edit.setDate(QDate.currentDate())
            date_layout.addWidget(label)
            date_layout.addWidget(date_edit)
            irp_date_layout.addLayout(date_layout)
            self.date_edits[field] = date_edit

        # Adicionar o layout de datas ao layout principal
        irp_layout.addLayout(irp_date_layout)

        # Configurar o layout principal no QGroupBox
        irp_group_box.setLayout(irp_layout)

        return irp_group_box
    
    """
    
    
    
    



    
    PARTE REFERENTE AO GROUPO DO SETOR RESPONSÁVEL
    
    






    """

    def create_dados_responsavel_contratacao_group(self):
        data = EditDataDialogUtils.extract_registro_data(self.df_registro_selecionado)

        setor_responsavel_group_box = QGroupBox("Divisão/Setor Responsável pela Demanda")
        self.apply_widget_style(setor_responsavel_group_box)
        setor_responsavel_layout = QVBoxLayout()

        # Configuração da OM, Divisão, e CP na mesma linha
        om_divisao_layout = QHBoxLayout()

        # Configuração da OM
        om_layout = QHBoxLayout()
        om_label = QLabel("OM:")
        self.apply_widget_style(om_label)
        
        sigla_om = data.get('sigla_om', 'CeIMBra')
        if self.df_registro_selecionado is not None and 'sigla_om' in self.df_registro_selecionado.columns:
            sigla_om = self.df_registro_selecionado['sigla_om'].iloc[0] if not self.df_registro_selecionado['sigla_om'].empty else 'CeIMBra'

        self.om_combo = self.create_combo_box(sigla_om, [], 150, 35)
        om_layout.addWidget(om_label)
        om_layout.addWidget(self.om_combo)

        # Adicionando o layout OM ao layout principal
        om_divisao_layout.addLayout(om_layout)

        # Configuração da Divisão
        divisao_label = QLabel("Divisão:")
        self.apply_widget_style(divisao_label)

        # Criando o QComboBox editável
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

        # Definindo o texto atual com base nos dados fornecidos
        self.setor_responsavel_combo.setCurrentText(data['setor_responsavel'])

        # Definindo a política de tamanho para expandir e preencher o espaço disponível
        self.setor_responsavel_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Adicionando o QComboBox ao layout
        om_divisao_layout.addWidget(divisao_label)
        om_divisao_layout.addWidget(self.setor_responsavel_combo)

        # Adicionando o layout OM/Divisão/CP ao layout principal
        setor_responsavel_layout.addLayout(om_divisao_layout)
        
        self.load_sigla_om(sigla_om)  # Carregar os itens do combobox e definir o texto

        self.par_edit = QLineEdit(str(data.get('cod_par', '')))
        self.par_edit.setFixedWidth(150)
        self.prioridade_combo = self.create_combo_box(data.get('prioridade_par', 'Necessário'), ["Necessário", "Urgente", "Desejável"], 190, 35)
     
        
        par_layout = QHBoxLayout()

        par_label = QLabel("Meta do PAR:")
        prioridade_label = QLabel("Prioridade:")
        self.apply_widget_style(par_label)
        self.apply_widget_style(prioridade_label)
        par_layout.addWidget(par_label)
        par_layout.addWidget(self.par_edit)
        par_layout.addWidget(prioridade_label)
        par_layout.addWidget(self.prioridade_combo)
        setor_responsavel_layout.addLayout(par_layout)

        self.endereco_edit = QLineEdit(data['endereco'])
        self.endereco_edit.setFixedWidth(450)
        self.cep_edit = QLineEdit(str(data.get('cep', '')))
        endereco_cep_layout = QHBoxLayout()
        endereco_label = QLabel("Endereço:")
        cep_label = QLabel("CEP:")
        self.apply_widget_style(endereco_label)
        self.apply_widget_style(cep_label)
        endereco_cep_layout.addWidget(endereco_label)
        endereco_cep_layout.addWidget(self.endereco_edit)
        endereco_cep_layout.addWidget(cep_label)
        endereco_cep_layout.addWidget(self.cep_edit)
        setor_responsavel_layout.addLayout(endereco_cep_layout)

        self.email_edit = QLineEdit(data['email'])
        self.email_edit.setFixedWidth(400)
        self.telefone_edit = QLineEdit(data['telefone'])
        email_telefone_layout = QHBoxLayout()
        email_telefone_layout.addLayout(self.create_layout("E-mail:", self.email_edit))
        email_telefone_layout.addLayout(self.create_layout("Tel:", self.telefone_edit))
        setor_responsavel_layout.addLayout(email_telefone_layout)

        self.dias_edit = QLineEdit("Segunda à Sexta")
        setor_responsavel_layout.addLayout(self.create_layout("Dias para Recebimento:", self.dias_edit))

        self.horario_edit = QLineEdit("09 às 11h20 e 14 às 16h30")
        setor_responsavel_layout.addLayout(self.create_layout("Horário para Recebimento:", self.horario_edit))

        # Adicionando Justificativa
        justificativa_label = QLabel("Justificativa para a contratação:")
        justificativa_label.setStyleSheet("font-size: 12pt;")
        self.justificativa_edit = QTextEdit(self.get_justification_text())
        self.apply_widget_style(self.justificativa_edit)
        setor_responsavel_layout.addWidget(justificativa_label)
        setor_responsavel_layout.addWidget(self.justificativa_edit)
        # setor_responsavel_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        setor_responsavel_group_box.setLayout(setor_responsavel_layout)

        return setor_responsavel_group_box

    def get_justification_text(self):
        # Recupera o valor atual da justificativa no DataFrame
        current_justification = self.df_registro_selecionado['justificativa'].iloc[0]

        # Retorna o valor atual se ele existir, senão, constrói uma justificativa baseada no tipo de material/serviço
        if current_justification:  # Checa se existe uma justificativa
            return current_justification
        else:
            # Gera justificativa padrão com base no tipo de material ou serviço
            if self.material_servico == 'Material':
                return (f"A aquisição de {self.objeto} se faz necessária para o atendimento das necessidades do(a) {self.setor_responsavel} do(a) {self.orgao_responsavel} ({self.sigla_om}). A disponibilidade e a qualidade dos materiais são essenciais para garantir a continuidade das operações e a eficiência das atividades desempenhadas pelo(a) {self.setor_responsavel}.")
            elif self.material_servico == 'Serviço':
                return (f"A contratação de empresa especializada na prestação de serviços de {self.objeto} é imprescindível para o atendimento das necessidades do(a) {self.setor_responsavel} do(a) {self.orgao_responsavel} ({self.sigla_om}).")
            return ""  # Retorna uma string vazia se nenhuma condição acima for satisfeita

    def load_sigla_om(self, sigla_om):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT sigla_om FROM controle_om ORDER BY sigla_om")
                items = [row[0] for row in cursor.fetchall()]
                self.om_combo.addItems(items)
                self.om_combo.setCurrentText(sigla_om)  # Define o texto atual do combobox
                self.om_combo.currentTextChanged.connect(self.on_om_changed)
                print(f"Loaded sigla_om items: {items}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao carregar OM: {e}")
            print(f"Error loading sigla_om: {e}")

    def on_om_changed(self):
        selected_om = self.om_combo.currentText()
        print(f"OM changed to: {selected_om}")
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uasg, orgao_responsavel, uf, codigoMunicipioIbge FROM controle_om WHERE sigla_om = ?", (selected_om,))
            result = cursor.fetchone()
            if result:
                uasg, orgao_responsavel, uf, codigoMunicipioIbge = result
                index = self.df_registro_selecionado.index[0]
                self.df_registro_selecionado.loc[index, 'uasg'] = uasg
                self.df_registro_selecionado.loc[index, 'orgao_responsavel'] = orgao_responsavel
                print(f"Updated DataFrame: uasg={uasg}, orgao_responsavel={orgao_responsavel}")
                self.title_updated.emit(f"{orgao_responsavel} (UASG: {uasg})")
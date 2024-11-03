from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
from config.styles.styless import apply_table_custom_style
from database.utils.treeview_utils import load_images, create_button
from modules.planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_pregao, carregar_dados_dispensa
from modules.dispensa_eletronica.utilidades_dispensa_eletronica import ExportThread
from modules.dispensa_eletronica.sql_model import SqlModel, CustomTableView
from modules.dispensa_eletronica.dialogs.add_item import AddItemDialog
from modules.dispensa_eletronica.dialogs.salvar_tabela import SaveTableDialog
from modules.dispensa_eletronica.dialogs.graficos import GraficTableDialog
from modules.dispensa_eletronica.dialogs.gerar_tabela import TabelaResumidaManager
import pandas as pd
import os
import subprocess
import logging
import sqlite3
from modules.dispensa_eletronica.edit_dialog import EditDataDialog

class DispensaEletronicaWidget(QMainWindow):
    dataUpdated = pyqtSignal()

    def __init__(self, icons_dir, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(icons_dir)
        self.setup_managers()
        self.load_initial_data()
        self.model = self.init_model()
        self.ui_manager = UIManager(self, self.image_cache, self.config_manager, self.model)
        self.setup_ui()
        self.export_thread = None
        self.output_path = os.path.join(os.getcwd(), "controle_dispensa_eletronica.xlsx")
        self.dataUpdated.connect(self.refresh_model)

    def setup_managers(self):
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        self.event_manager = EventManager()

    def refresh_model(self):
        self.model.select()

    def setup_ui(self):
        self.setCentralWidget(self.ui_manager.main_widget)

    def load_initial_data(self):
        # print("Carregando dados iniciais...")
        self.image_cache = load_images(self.icons_dir, [
            "business.png", "aproved.png", "session.png", "deal.png", "emenda_parlamentar.png", "verify_menu.png", "archive.png",
            "plus.png", "import_de.png", "save_to_drive.png", "loading.png", "delete.png", "performance.png",
            "excel.png", "calendar.png", "report.png", "management.png", "image-processing.png"
        ])
        self.selectedIndex = None

    def init_model(self):
        # Inicializa e retorna o modelo SQL utilizando o DatabaseManager
        sql_model = SqlModel(self.database_manager, self)
        return sql_model.setup_model("controle_dispensas", editable=True)

    def on_add_item(self):
        dialog = AddItemDialog(self)
        if dialog.exec():
            item_data = dialog.get_data()
            # Add 'situacao' before saving
            item_data['situacao'] = 'Planejamento'
            self.save_to_database(item_data)

    def excluir_linha(self):
        selection_model = self.ui_manager.table_view.selectionModel()

        if selection_model.hasSelection():
            # Supondo que a coluna 0 é 'id_processo'
            index_list = selection_model.selectedRows(0)

            if not index_list:
                QMessageBox.warning(self, "Nenhuma Seleção", "Nenhuma linha selecionada.")
                return

            selected_id_processo = index_list[0].data()  # Pega o 'id_processo' da primeira linha selecionada
            print(f"Excluindo linha com id_processo: {selected_id_processo}")

            # Confirmar a exclusão
            if Dialogs.confirm(self, 'Confirmar exclusão', f"Tem certeza que deseja excluir o registro com ID Processo '{selected_id_processo}'?"):
                data_to_delete = {'id_processo': selected_id_processo}
                try:
                    self.save_to_database(data_to_delete, delete=True)  # Passa o dado a ser deletado com uma flag de exclusão
                    QMessageBox.information(self, "Sucesso", "Registro excluído com sucesso.")
                except Exception as e:
                    QMessageBox.warning(self, "Erro ao excluir", f"Erro ao excluir o registro: {str(e)}")
                    print(f"Erro ao excluir o registro: {str(e)}")
        else:
            QMessageBox.warning(self, "Nenhuma Seleção", "Por favor, selecione uma linha para excluir.")

    def salvar_graficos(self):
        dialog = GraficTableDialog(self)
        dialog.exec()

    def salvar_tabela(self):
        dialog = SaveTableDialog(self)
        dialog.exec()

    def salvar_tabela_completa(self):
        self.export_thread = ExportThread(self.model, self.output_path)
        self.export_thread.finished.connect(self.handle_export_finished)
        self.export_thread.start()

    def salvar_tabela_resumida(self):
        # Criar instância do TabelaResumidaManager
        tabela_manager = TabelaResumidaManager(self.model)
        
        # Carregar dados do modelo
        tabela_manager.carregar_dados()

        # Exportar para Excel
        output_path = os.path.join(os.getcwd(), "tabela_resumida.xlsx")
        tabela_manager.exportar_para_excel(output_path)

        # Abrir o arquivo Excel gerado
        tabela_manager.abrir_arquivo_excel(output_path)

    def salvar_print(self):

        tabela_manager = TabelaResumidaManager(self.model)
        
        # Carregar dados do modelo
        tabela_manager.carregar_dados()
        
        # Caminho para salvar a imagem da tabela
        output_image_path = os.path.join(os.getcwd(), "tabela_resumida.png")
        
        # Tirar o print da tabela e abrir a imagem
        tabela_manager.tirar_print_da_tabela(output_image_path)
                    
    def handle_export_finished(self, message):
        if 'successfully' in message:
            Dialogs.info(self, "Exportação de Dados", "Dados exportados com sucesso!")
            subprocess.run(f'start excel.exe "{self.output_path}"', shell=True, check=True)
        else:
            Dialogs.warning(self, "Exportação de Dados", message)

    def carregar_tabela(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.xls *.ods)")
        if filepath:
            try:
                df = pd.read_excel(filepath)
                self.validate_and_process_data(df)
                
                # Verifica se a coluna 'situacao' existe
                if 'situacao' in df.columns:
                    pass  # Mantém a coluna 'situacao' como está
                elif 'Status' in df.columns:
                    # Se a coluna 'Status' existir, renomeia para 'situacao'
                    df['situacao'] = df['Status']
                    df.drop(columns=['Status'], inplace=True)
                else:
                    # Se nenhuma das colunas existir, adiciona 'situacao' com valor padrão 'Planejamento'
                    df['situacao'] = 'Planejamento'

                # Lista de valores válidos para a coluna 'situacao'
                valid_situations = ["Planejamento", "Aprovado", "Sessão Pública", "Homologado", "Empenhado", "Concluído", "Arquivado"]

                # Verifica se os valores na coluna 'situacao' são válidos, senão, define como 'Planejamento'
                df['situacao'] = df['situacao'].apply(lambda x: x if x in valid_situations else 'Planejamento')

                self.save_to_database(df)
                Dialogs.info(self, "Carregamento concluído", "Dados carregados com sucesso.")
            except Exception as e:
                Dialogs.warning(self, "Erro ao carregar", str(e))

    def validate_and_process_data(self, df):
        required_columns = ['ID Processo', 'NUP', 'Objeto', 'uasg']
        if not all(col in df.columns for col in required_columns):
            missing_columns = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Faltando: {', '.join(missing_columns)}")
        df.rename(columns={'ID Processo': 'id_processo', 'NUP': 'nup', 'Objeto': 'objeto'}, inplace=True)
        self.desmembramento_id_processo(df)
        self.salvar_detalhes_uasg_sigla_nome(df)

    def desmembramento_id_processo(self, df):
        df[['tipo', 'numero', 'ano']] = df['id_processo'].str.extract(r'(\D+)(\d+)/(\d+)')
        df['tipo'] = df['tipo'].map({'DE ': 'Dispensa Eletrônica'}).fillna('Tipo Desconhecido')

    def salvar_detalhes_uasg_sigla_nome(self, df):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uasg, sigla_om, orgao_responsavel FROM controle_om")
            om_details = {row[0]: {'sigla_om': row[1], 'orgao_responsavel': row[2]} for row in cursor.fetchall()}
        df['sigla_om'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('sigla_om', ''))
        df['orgao_responsavel'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('orgao_responsavel', ''))
                
    def save_to_database(self, data, delete=False):
        with self.database_manager as conn:
            cursor = conn.cursor()
            if delete:
                cursor.execute("DELETE FROM controle_dispensas WHERE id_processo = ?", (data['id_processo'],))
            else:
                # Lista de valores válidos para a coluna 'situacao'
                valid_situations = ["Planejamento", "Aprovado", "Sessão Pública", "Homologado", "Empenhado", "Concluído", "Arquivado"]

                upsert_sql = '''
                INSERT INTO controle_dispensas (
                    id_processo, nup, objeto, uasg, tipo, numero, ano, sigla_om, setor_responsavel, 
                    material_servico, orgao_responsavel, situacao, data_sessao, operador, 
                    criterio_julgamento, com_disputa, pesquisa_preco, previsao_contratacao, 
                    responsavel_pela_demanda, ordenador_despesas, agente_fiscal, gerente_de_credito,
                    cod_par, prioridade_par, cep, endereco, email, telefone, dias_para_recebimento,
                    horario_para_recebimento, valor_total, acao_interna, fonte_recursos, natureza_despesa,
                    unidade_orcamentaria, ptres
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id_processo) DO UPDATE SET
                    nup=excluded.nup,
                    objeto=excluded.objeto,
                    uasg=excluded.uasg,
                    tipo=excluded.tipo,
                    numero=excluded.numero,
                    ano=excluded.ano,
                    sigla_om=excluded.sigla_om,
                    setor_responsavel=excluded.setor_responsavel,
                    material_servico=excluded.material_servico,
                    orgao_responsavel=excluded.orgao_responsavel,
                    situacao=excluded.situacao,
                    data_sessao=excluded.data_sessao,
                    operador=excluded.operador,
                    criterio_julgamento=excluded.criterio_julgamento,
                    com_disputa=excluded.com_disputa,
                    pesquisa_preco=excluded.pesquisa_preco,
                    previsao_contratacao=excluded.previsao_contratacao,
                    responsavel_pela_demanda=excluded.responsavel_pela_demanda, 
                    ordenador_despesas=excluded.ordenador_despesas, 
                    agente_fiscal=excluded.agente_fiscal, 
                    gerente_de_credito=excluded.gerente_de_credito,
                    cod_par=excluded.cod_par, 
                    prioridade_par=excluded.prioridade_par, 
                    cep=excluded.cep, 
                    endereco=excluded.endereco, 
                    email=excluded.email, 
                    telefone=excluded.telefone, 
                    dias_para_recebimento=excluded.dias_para_recebimento,
                    horario_para_recebimento=excluded.horario_para_recebimento, 
                    valor_total=excluded.valor_total, 
                    acao_interna=excluded.acao_interna, 
                    fonte_recursos=excluded.fonte_recursos, 
                    natureza_despesa=excluded.natureza_despesa,
                    unidade_orcamentaria=excluded.unidade_orcamentaria,
                    ptres=excluded.ptres
                '''

                def get_valid_situacao(value):
                    return value if value in valid_situations else 'Planejamento'

                if isinstance(data, pd.DataFrame):
                    # Atualiza 'situacao' para cada linha, se necessário
                    data['situacao'] = data['situacao'].apply(get_valid_situacao)
                    for _, row in data.iterrows():
                        cursor.execute(upsert_sql, (
                            row['id_processo'], row['nup'], row['objeto'], row['uasg'],
                            row.get('tipo', ''), row.get('numero', ''), row.get('ano', ''),
                            row.get('sigla_om', ''), row.get('setor_responsavel', ''), 
                            row.get('material_servico', ''), row.get('orgao_responsavel', ''),
                            row['situacao'], row.get('data_sessao', None), row.get('operador', ''),
                            row.get('criterio_julgamento', ''), row.get('com_disputa', 0),
                            row.get('pesquisa_preco', 0), row.get('previsao_contratacao', None), 
                            row.get('responsavel_pela_demanda', None), row.get('ordenador_despesas', None), 
                            row.get('agente_fiscal', None), row.get('gerente_de_credito', None), 
                            row.get('cod_par', None), row.get('prioridade_par', None), 
                            row.get('cep', None), row.get('endereco', None), 
                            row.get('email', None), row.get('telefone', None), 
                            row.get('dias_para_recebimento', None), row.get('horario_para_recebimento', None),
                            row.get('valor_total', None), row.get('acao_interna', None), 
                            row.get('fonte_recursos', None), row.get('natureza_despesa', None),  
                            row.get('unidade_orcamentaria', None), row.get('ptres', None),
                        ))                      
                else:
                    # Verifica 'situacao' diretamente no dicionário
                    data['situacao'] = get_valid_situacao(data.get('situacao', ''))
                    cursor.execute(upsert_sql, (
                        data['id_processo'], data['nup'], data['objeto'], data['uasg'],
                        data['tipo'], data['numero'], data['ano'],
                        data['sigla_om'], data.get('setor_responsavel', ''), 
                        data['material_servico'], data['orgao_responsavel'], data['situacao'],
                        data.get('data_sessao', None), data.get('operador', ''),
                        data.get('criterio_julgamento', ''), data.get('com_disputa', 0),
                        data.get('pesquisa_preco', 0), data.get('previsao_contratacao', None),
                        data.get('responsavel_pela_demanda', None), data.get('ordenador_despesas', None), 
                        data.get('agente_fiscal', None), data.get('gerente_de_credito', None), 
                        data.get('cod_par', None), data.get('prioridade_par', None), 
                        data.get('cep', None), data.get('endereco', None), 
                        data.get('email', None), data.get('telefone', None), 
                        data.get('dias_para_recebimento', None), data.get('horario_para_recebimento', None),
                        data.get('valor_total', None), data.get('acao_interna', None), 
                        data.get('fonte_recursos', None), data.get('natureza_despesa', None),  
                        data.get('unidade_orcamentaria', None), data.get('ptres', None),
                    ))
            conn.commit()
        self.dataUpdated.emit()

class UIManager:
    def __init__(self, parent, icons, config_manager, model):
        self.parent = parent
        self.icons = icons  # Agora isso é o dicionário de ícones passado
        self.config_manager = config_manager
        self.model = model
        self.main_widget = QWidget(parent)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.button_manager = ButtonManager(self.parent)
        self.init_ui()

    def init_ui(self):
        self.setup_search_bar()
        self.setup_table_view()
        self.parent.setCentralWidget(self.main_widget) 

    def setup_search_and_buttons_layout(self):
        # Configura a barra de busca
        self.search_bar = QLineEdit(self.parent)
        self.search_bar.setPlaceholderText("Digite para buscar...")
        self.search_bar.setStyleSheet("font-size: 14px;")

        def handle_text_change(text):
            regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.parent.proxy_model.setFilterRegularExpression(regex)

        self.search_bar.textChanged.connect(handle_text_change)

        # Adiciona a barra de busca ao QHBoxLayout
        self.search_buttons_layout.addWidget(self.search_bar)

        # Configura os botões e os adiciona ao QHBoxLayout
        self.buttons_layout = QHBoxLayout()
        self.button_manager.add_buttons_to_layout(self.search_buttons_layout)

        # Adiciona o QHBoxLayout que contém a barra de busca e os botões ao layout principal
        self.main_layout.addLayout(self.search_buttons_layout)

    def setup_search_bar(self):

        self.search_buttons_layout = QHBoxLayout()

        # Adicionar texto "Localizar:"
        search_label = QLabel("Localizar:")
        search_label.setStyleSheet("font-size: 14px;")
        self.search_buttons_layout .addWidget(search_label)

        self.search_bar = QLineEdit(self.parent)
        self.search_bar.setPlaceholderText("Digite para buscar...")
        self.search_bar.setStyleSheet("font-size: 14px;")

        def handle_text_change(text):
            regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.parent.proxy_model.setFilterRegularExpression(regex)

        self.search_bar.textChanged.connect(handle_text_change)
        self.search_buttons_layout.addWidget(self.search_bar)

        self.buttons_layout = QHBoxLayout()
        self.button_manager.add_buttons_to_layout(self.search_buttons_layout)
        self.main_layout.addLayout(self.search_buttons_layout)

    def setup_table_view(self):
        self.table_view = CustomTableView(main_app=self.parent, config_manager=self.config_manager, parent=self.main_widget)
        self.table_view.setModel(self.model)
        self.main_layout.addWidget(self.table_view)
        self.configure_table_model()
        self.table_view.verticalHeader().setVisible(False)
        self.adjust_columns()
        apply_table_custom_style(self.table_view)

        center_delegate = CenterAlignDelegate(self.table_view)
        for column in range(self.model.columnCount()):
            self.table_view.setItemDelegateForColumn(column, center_delegate)

        status_index = self.model.fieldIndex("situacao")
        self.table_view.setItemDelegateForColumn(status_index, CustomItemDelegate(self.icons, self.table_view, self.model))
        
        # Conecta o duplo clique para editar dados
        self.table_view.doubleClicked.connect(self.on_double_click)

    def on_double_click(self, index):
        # Mapeia o índice selecionado do proxy para o índice original do modelo
        source_index = self.parent.proxy_model.mapToSource(index)
        row = source_index.row()
        
        # Assumindo que a chave primária é a primeira coluna do modelo
        id_processo = self.model.data(self.model.index(row, 0))
        
        if id_processo:
            # Carrega os dados do registro selecionado usando o ID do processo
            df_registro_selecionado = carregar_dados_dispensa(id_processo, str(self.parent.database_path))
            
            if not df_registro_selecionado.empty:
                # Chama o método para editar dados
                self.editar_dados(df_registro_selecionado)
            else:
                QMessageBox.warning(self.parent, "Erro", "Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")
        else:
            QMessageBox.warning(self.parent, "Erro", "Nenhum ID de processo foi encontrado para a linha selecionada.")

    def editar_dados(self, df_registro_selecionado):
        dialog = EditDataDialog(df_registro_selecionado, self.parent.icons_dir)
        dialog.dados_atualizados.connect(self.parent.refresh_model)  # Conectar o sinal ao método de atualização
        dialog.exec()

    def configure_table_model(self):
        self.parent.proxy_model = QSortFilterProxyModel(self.parent)
        self.parent.proxy_model.setSourceModel(self.model)
        self.parent.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.parent.proxy_model.setFilterKeyColumn(-1)
        self.parent.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)
        self.table_view.setModel(self.parent.proxy_model)

        self.model.dataChanged.connect(self.table_view.update)

        if self.table_view.selectionModel():
            self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
            self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        self.update_column_headers()
        self.reorder_columns()
        self.hide_unwanted_columns()
            
    def adjust_columns(self):
        # Ajustar automaticamente as larguras das colunas ao conteúdo
        self.table_view.resizeColumnsToContents()
        QTimer.singleShot(1, self.apply_custom_column_sizes) 

    def apply_custom_column_sizes(self):
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(17, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)

        header.resizeSection(4, 150)        
        header.resizeSection(0, 130)
        header.resizeSection(5, 170)
        header.resizeSection(17, 100)
        header.resizeSection(10, 170)

    def linhaSelecionada(self, selected, deselected):
        if selected.indexes():
            proxy_index = selected.indexes()[0]
            source_index = self.parent.proxy_model.mapToSource(proxy_index)
            print(f"Linha selecionada: {source_index.row()}, Coluna: {source_index.column()}")

            df_registro_selecionado = carregar_dados_pregao(source_index.row(), self.parent.database_path)
            if not df_registro_selecionado.empty:
                logging.debug(f"Registro selecionado: {df_registro_selecionado.iloc[0].to_dict()}")
            else:
                logging.warning("Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")
                QMessageBox.warning(self.parent, "Erro", "Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")

    def update_column_headers(self):
        titles = {
            0: "ID Processo",
            5: "NUP",
            7: "Objeto",
            17: "OM",
            4: "Status",
        }
        for column, title in titles.items():
            self.model.setHeaderData(column, Qt.Orientation.Horizontal, title)

    def reorder_columns(self):
        new_order = [4, 0, 5, 7, 17]
        for i, col in enumerate(new_order):
            self.table_view.horizontalHeader().moveSection(self.table_view.horizontalHeader().visualIndex(col), i)

    def hide_unwanted_columns(self):
        visible_columns = {0, 5, 7, 17, 4}
        for column in range(self.model.columnCount()):
            if column not in visible_columns:
                self.table_view.hideColumn(column)

class ButtonManager:
    def __init__(self, parent):
        self.parent = parent
        self.buttons = []
        self.create_buttons()

    def create_buttons(self):
        button_specs = [
            ("  Adicionar", self.parent.image_cache['plus'], self.parent.on_add_item, "Adiciona um novo item ao banco de dados"),
            ("  Excluir", self.parent.image_cache['delete'], self.parent.excluir_linha, "Exclui um item selecionado"),
            ("  Tabelas", self.parent.image_cache['excel'], self.parent.salvar_tabela, "Salva o dataframe em um arquivo Excel"),
            ("  Gráficos", self.parent.image_cache['performance'], self.parent.salvar_graficos, "Carrega dados de uma tabela"),
            ("  ConGes", self.parent.image_cache['image-processing'], self.parent.salvar_print, "Abre o painel de controle do processo"),
        ]
        for text, icon, callback, tooltip in button_specs:
            btn = self.create_button(text, icon, callback, tooltip, self.parent)
            self.buttons.append(btn)

    def add_buttons_to_layout(self, layout):
        for btn in self.buttons:
            layout.addWidget(btn)

    def create_button(self, text, icon, callback, tooltip_text, parent, icon_size=QSize(30, 30)):
        btn = QPushButton(text, parent)
        if icon:
            btn.setIcon(QIcon(icon))
            btn.setIconSize(icon_size)
        if callback:
            btn.clicked.connect(callback)
        if tooltip_text:
            btn.setToolTip(tooltip_text)
        
        # Aplicando estilo ao botão
        btn.setStyleSheet("""
            font-size: 14px; 
            min-width: 85px; 
            min-height: 20px; 
            max-width: 140px; 
            max-height: 20px;
        """)
        
        return btn

class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, icons, parent=None, model=None):
        super().__init__(parent)
        self.icons = icons  # Dicionário de ícones
        self.model = model

    def paint(self, painter, option, index):
        if index.column() == 4:  # Verifica se é a coluna "Status"
            situacao = self.model.data(self.model.index(index.row(), self.model.fieldIndex('situacao')), Qt.ItemDataRole.DisplayRole)

            # Usando chaves que correspondem aos nomes sem extensão
            icon_key = {
                'Planejamento': 'business',
                'Aprovado': 'verify_menu',
                'Sessão Pública': 'session',
                'Homologado': 'deal',
                'Empenhado': 'emenda_parlamentar',
                'Concluído': 'aproved',
                'Arquivado': 'archive'
            }.get(situacao)

            # Desenha o ícone se a chave existir
            if icon_key and icon_key in self.icons:
                icon = self.icons[icon_key]
                icon_size = 24
                icon_x = option.rect.left() + 5
                icon_y = option.rect.top() + (option.rect.height() - icon_size) // 2
                icon_rect = QRect(int(icon_x), int(icon_y), icon_size, icon_size)
                icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)

                # Ajusta o retângulo para o texto para ficar ao lado do ícone
                text_rect = QRect(icon_rect.right() + 5, option.rect.top(), option.rect.width() - icon_size - 10, option.rect.height())
                option.rect = text_rect

        # Chama o método padrão para desenhar o texto ajustado
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setWidth(size.width() + 30)  # Ajusta o tamanho da célula para acomodar o ícone
        return size

class Dialogs:
    @staticmethod
    def info(parent, title, message):
        QMessageBox.information(parent, title, message)

    @staticmethod
    def warning(parent, title, message):
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def error(parent, title, message):
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def confirm(parent, title, message):
        reply = QMessageBox.question(parent, title, message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

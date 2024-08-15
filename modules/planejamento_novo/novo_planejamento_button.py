from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from pathlib import Path
from diretorios import *
from database.utils.treeview_utils import load_images, create_button, save_dataframe_to_excel
import pandas as pd
import os
from modules.planejamento.settings import SettingsDialog
from modules.planejamento.adicionar_itens import AddItemDialog
from modules.planejamento.editar_dados import EditarDadosDialog
from modules.planejamento.popup_relatorio import ReportDialog
from modules.planejamento.fluxoprocesso import FluxoProcessoDialog
from modules.planejamento.settings import SettingsDialog
from modules.planejamento.capa_edital import CapaEdital
from modules.planejamento.checklist import ChecklistWidget
from modules.planejamento.msg_planejamento import MSGIRP, MSGHomolog, MSGPublicacao
from modules.planejamento.dfd import GerarDFD, GerarManifestoIRP
from modules.planejamento.etp import GerarETP
from modules.planejamento.matriz_risco import GerarMR
from modules.planejamento.portaria_planejamento import GerarPortariaPlanejamento
from modules.planejamento.cp_agu import CPEncaminhamentoAGU
from modules.planejamento.escalar_pregoeiro import EscalarPregoeiroDialog
from modules.planejamento.autorizacao import AutorizacaoAberturaLicitacaoDialog
from modules.planejamento.edital import EditalDialog
from modules.planejamento_novo.utilidades import DatabaseManager, carregar_dados_processos, carregar_dados_pregao
from modules.planejamento_novo.custom import CustomItemDelegate, CenterAlignDelegate, load_and_map_icons
df_uasg = pd.read_excel(TABELA_UASG_DIR)
global df_registro_selecionado
df_registro_selecionado = None

from datetime import datetime
import logging
import sqlite3
from functools import partial

etapas = {
    'Planejamento': None,
    'Consolidar Demandas': None,
    'Montagem do Processo': None,
    'Nota Técnica': None,
    'AGU': None,
    'Recomendações AGU': None,
    'Pré-Publicação': None,
    'Sessão Pública': None,
    'Assinatura Contrato': None,
    'Concluído': None
}

class CustomTableView(QTableView):
    def __init__(self, main_app, config_manager, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.config_manager = config_manager

        # Ativar o menu de contexto
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

    def mouseDoubleClickEvent(self, event):
        selected_index = self.currentIndex()
        if not selected_index.isValid():
            return
        
        # Verifica se a coluna selecionada é "NUP" ou "Objeto"
        selected_column = selected_index.column()
        column_name = self.model().headerData(selected_column, Qt.Orientation.Horizontal)
        
        if column_name in ["NUP", "Objeto"]:
            # Permite a edição direta nessas colunas
            self.edit(selected_index)
        else:
            # Mapeia o índice do modelo proxy para o modelo original
            source_index = self.main_app.proxy_model.mapToSource(selected_index)
        
            # Obtém a linha selecionada do modelo original
            selected_row = source_index.row()
        
            # Carrega os dados da linha selecionada
            df_registro_selecionado = carregar_dados_pregao(selected_row, self.main_app.database_path)

            # Abre o diálogo de edição se houver dados selecionados
            if not df_registro_selecionado.empty:
                self.main_app.editar_dados(df_registro_selecionado)
        
        super().mouseDoubleClickEvent(event)

    def open_context_menu(self, position):
        index = self.indexAt(position)
        if index.isValid():
            # Abre o menu de contexto personalizado
            menu = TableMenu(self.main_app, index, model=self.model(), config_manager=self.config_manager)
            menu.exec(self.viewport().mapToGlobal(position))


class PlanejamentoWidget(QMainWindow):
    def __init__(self, app, icons_dir):
        super().__init__()
        self.app = app
        self.icons_dir = Path(icons_dir)
        self.icons = load_and_map_icons(self.icons_dir)  # Carrega os ícones
        self.setup_managers()
        self.load_icons()
        self.initialize_ui()  # Inicializa o modelo e a UI

    def initialize_ui(self):
        # Inicializa o modelo e a interface do usuário
        self.model = self.init_model()  # Inicializa e configura o modelo SQL
        self.ui_manager = UIManager(self, self.icons, self.config_manager, self.model)  # Passa os ícones para UIManager
        self.table_view = self.ui_manager.table_view  # Atribui table_view da UIManager para o ApplicationUI
        self.setup_signals()
        self.init_ui()

    def editar_dados(self, df_registro_selecionado):
        dialog = EditarDadosDialog(ICONS_DIR, parent=self, dados=df_registro_selecionado.iloc[0].to_dict())
        dialog.dados_atualizados.connect(self.atualizar_tabela)
        dialog.show()

    def setup_managers(self):
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        self.event_manager = EventManager()

    def open_carregar_tabela_dialog(self):
        dialog = CarregarTabelaDialog(self.database_manager, self)
        dialog.exec()

    def load_icons(self):
        # print("Carregando dados iniciais...")
        self.image_cache = load_images(self.icons_dir, [
            "plus.png", "save_to_drive.png", "loading.png", "delete.png", "contrato.png",
            "planification.png", "business.png", "deal.png", "law.png", "puzzle.png",
            "excel.png", "calendar.png", "report.png", "management.png", "data-processing.png"
        ])
        self.selectedIndex = None

    def init_model(self):
        # Inicializa e retorna o modelo SQL utilizando o DatabaseManager
        sql_model = SqlModel(self.database_manager, self)
        model = sql_model.setup_model("controle_processos", editable=True)
        return model
    
    def init_ui(self):
        self.setCentralWidget(self.ui_manager.main_widget)  # Define o widget central como o widget principal do UIManager
        self.ui_manager.configure_table_model()

    def setup_signals(self):
        self.event_manager.controle_dados_dir_updated.connect(self.handle_database_dir_update)

    def handle_database_dir_update(self, new_dir):
        self.database_manager.update_database_path(new_dir)
        self.ui_manager.update_ui_after_database_change()
        print("ApplicationUI inicializada.")

    def open_settings_dialog(self):
        dialog = SettingsDialog(config_manager=self.config_manager, parent=self)
        dialog.exec()

    def on_delete_item(self):
        selected_index = self.table_view.currentIndex()
        if not selected_index.isValid():
            QMessageBox.warning(self, "Seleção", "Nenhum item selecionado.")
            return

        # Obtém o ID do processo da linha selecionada
        id_processo = selected_index.sibling(selected_index.row(), 4).data()  # Assumindo que a coluna 4 é 'ID Processo'

        if id_processo is None:
            QMessageBox.warning(self, "Erro", "Não foi possível obter o ID do processo.")
            return

        reply = QMessageBox.question(self, "Confirmar exclusão", 
                                    "Você tem certeza que deseja excluir o item selecionado e todas as entradas correspondentes?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                    QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Exclui do controle_processos
            with self.database_manager as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM controle_processos WHERE id_processo = ?", (id_processo,))
                conn.commit()

            # Exclui do controle_prazos onde chave_processo é igual a id_processo
            with self.database_manager as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM controle_prazos WHERE chave_processo = ?", (id_processo,))
                conn.commit()

            self.init_model()  # Atualiza o modelo para refletir as mudanças
            QMessageBox.information(self, "Exclusão", "Os registros foram excluídos com sucesso.")

    def on_report(self):
        with self.database_manager as conn:
            # Atualiza etapas baseadas no último sequencial de controle_prazos
            self.database_manager.verificar_e_atualizar_etapas(conn)
            # Atualiza a contagem dos dias na última etapa
            self.database_manager.atualizar_dias_na_etapa(conn)
            # Atualiza a data final para a última etapa de cada chave_processo para hoje
            self.database_manager.atualizar_ultima_etapa_data_final(conn)
            # Verifica e popula controle_prazos se necessário
            self.database_manager.popular_controle_prazos_se_necessario()
        dialog = ReportDialog(self.model, self.icons_dir, parent=self)
        dialog.exec()

    def on_add_item(self):
        dialog = AddItemDialog(self)
        if dialog.exec():
            item_data = dialog.get_data()
            self.save_to_database(item_data)
            self.save_to_control_prazos(item_data['id_processo'])

    def save_to_control_prazos(self, id_processo):
        with self.database_manager as conn:
            cursor = conn.cursor()
            # Verificar se a chave já existe
            cursor.execute("SELECT COUNT(*) FROM controle_prazos WHERE chave_processo = ?", (id_processo,))
            if cursor.fetchone()[0] > 0:
                # Perguntar ao usuário se deseja sobrescrever
                reply = QMessageBox.question(self, "Confirmar Sobrescrita", 
                                            "Chave de processo já existe. Deseja sobrescrever?",
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                            QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    # Deletar as informações existentes
                    cursor.execute("DELETE FROM controle_prazos WHERE chave_processo = ?", (id_processo,))
                else:
                    return  # Não continuar se o usuário escolher não sobrescrever

            # Inserir novos dados
            today = datetime.today().strftime('%Y-%m-%d')
            cursor.execute('''
                INSERT INTO controle_prazos (chave_processo, etapa, data_inicial, sequencial)
                VALUES (?, ?, ?, ?)
            ''', (id_processo, "Planejamento", today, 1))
            conn.commit()
            
    def save_to_database(self, data):
        try:
            with self.database_manager as conn:
                cursor = conn.cursor()

                # Definir valores fixos para 'etapa' e 'pregoeiro'
                data['etapa'] = "Planejamento"
                data['pregoeiro'] = "-"

                # Verificar se o id_processo já existe
                cursor.execute(
                    '''
                    SELECT COUNT(*) FROM controle_processos 
                    WHERE id_processo = ?
                    ''', (data['id_processo'],)
                )
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Duplicidade", f"O processo com o ID '{data['id_processo']}' já existe.")
                    return

                # Inserir o novo registro se não houver duplicidade
                cursor.execute(
                    '''
                    INSERT INTO controle_processos (
                        tipo, numero, ano, objeto, sigla_om, material_servico, 
                        id_processo, nup, orgao_responsavel, uasg, etapa, pregoeiro) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (data['tipo'], data['numero'], data['ano'], data['objeto'], 
                        data['sigla_om'], data['material_servico'], data['id_processo'], 
                        data['nup'], data['orgao_responsavel'], data['uasg'], data['etapa'], 
                        data['pregoeiro'])
                )
                conn.commit()

            self.initialize_ui()  # Reconfigura o modelo e a UI
            
        except sqlite3.IntegrityError as e:
            print(f"Erro de integridade ao salvar no banco de dados: {e}")
            QMessageBox.critical(self, "Erro", "Erro ao adicionar o item ao banco de dados.")
        except Exception as e:
            print(f"Erro ao salvar no banco de dados: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar o item ao banco de dados: {e}")

    def salvar_tabela(self):
        # Cria um DataFrame vazio
        column_count = self.model.columnCount()
        headers = [self.model.headerData(i, Qt.Orientation.Horizontal) for i in range(column_count)]
        data = []

        # Preenche o DataFrame com os dados do modelo
        for row in range(self.model.rowCount()):
            row_data = []
            for column in range(column_count):
                index = self.model.index(row, column)
                row_data.append(self.model.data(index))
            data.append(row_data)

        df = pd.DataFrame(data, columns=headers)

        # Define o caminho inicial com o nome do arquivo pré-definido
        initial_path = os.path.join(os.path.expanduser("~"), "controle_processos.xlsx")
        
        # Abre um diálogo para que o usuário escolha o diretório e nome do arquivo
        excel_path, _ = QFileDialog.getSaveFileName(None, 'Salvar Tabela', initial_path, 'Excel Files (*.xlsx)')
        if not excel_path:
            return  # Usuário cancelou o diálogo de salvar

        # Salva o DataFrame como Excel usando openpyxl para ajustar as colunas
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
            
            # Ajusta as colunas ao conteúdo
            for column_cells in writer.sheets['Sheet1'].columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                writer.sheets['Sheet1'].column_dimensions[column_cells[0].column_letter].width = length

        # Abre o arquivo Excel
        os.startfile(excel_path)

    def update_database_file(self):
        # Abrir o diálogo para seleção do arquivo do banco de dados
        fileName, _ = QFileDialog.getOpenFileName(self, 
                                                "Selecione o arquivo do banco de dados", 
                                                str(CONTROLE_DADOS),  # Diretório inicial
                                                "Database Files (*.db)")
        print(f"Debug: Seleção de arquivo iniciada. Arquivo escolhido: {fileName}")
        
        if fileName:
            newPath = Path(fileName)
            print(f"Debug: Novo caminho escolhido: {newPath}")

            # Sempre atualiza, independente se o novo caminho é igual ao antigo
            print(f"Debug: Atualizando o caminho do banco de dados. Antigo: {CONTROLE_DADOS}, Novo: {newPath}")
            self.event_manager.update_database_dir(newPath)  # Chama a atualização mesmo se o caminho for o mesmo
            print("Debug: O caminho do banco de dados foi atualizado com sucesso.")
            QMessageBox.information(self, "Atualização bem-sucedida", "O arquivo do banco de dados foi atualizado com sucesso.")
        else:
            print("Debug: Nenhum arquivo foi escolhido.")
            QMessageBox.warning(self, "Carregamento Cancelado", "Nenhum arquivo de banco de dados foi selecionado.")

    def handle_database_dir_update(self, new_dir):
        # Atualiza o caminho do banco de dados
        self.database_path = new_dir
        self.database_manager = DatabaseManager(new_dir)
        # Reinicialize quaisquer funções ou métodos que dependem do database_path
        self.init_sql_model()  # Por exemplo, reinicialize o modelo SQL
        QMessageBox.information(self, "Atualização de Diretório", "Diretório do banco de dados atualizado para: " + str(new_dir))

    def on_control_process(self):
        print("Iniciando on_control_process...")
        with self.database_manager as conn:
            # Atualiza etapas baseadas no último sequencial de controle_prazos
            self.database_manager.verificar_e_atualizar_etapas(conn)
            # Atualiza a contagem dos dias na última etapa
            self.database_manager.atualizar_dias_na_etapa(conn)
            # Atualiza a data final para a última etapa de cada chave_processo para hoje
            self.database_manager.atualizar_ultima_etapa_data_final(conn)
            # Verifica e popula controle_prazos se necessário
            self.database_manager.popular_controle_prazos_se_necessario()

        # Carrega os dados de processos já com as etapas atualizadas
        df_processos = carregar_dados_processos(self.database_path)

        if not df_processos.empty:
            self.exibir_dialogo_process_flow()
        else:
            print("DataFrame de processos está vazio.")

    def exibir_dialogo_process_flow(self):
        df_processos = carregar_dados_processos(self.database_path)
        dialog = FluxoProcessoDialog(ICONS_DIR, etapas, df_processos, self.database_manager, self.database_path, self)
        dialog.updateRequired.connect(self.atualizarTableView)
        dialog.exec()  # Executa o diálogo e espera até que seja fechado
        self.initialize_ui()  # Inicializa a UI após o fechamento do diálogo
        
    def atualizarTableView(self):
        print("Atualizando TableView...")
        with self.database_manager as conn:
            # Atualiza etapas baseadas no último sequencial de controle_prazos
            self.database_manager.verificar_e_atualizar_etapas(conn)
            # Atualiza a data final para a última etapa de cada chave_processo para hoje
            self.database_manager.atualizar_ultima_etapa_data_final(conn)
        # Depois de atualizar os dados, re-inicialize o modelo SQL para refletir as mudanças
        self.resetModels()

    def resetModels(self):
        """Reseta o modelo de tabela SQL e o modelo de filtro proxy."""
        self.init_model()  # Reinicializa o modelo SQL
        self.proxy_model.setSourceModel(self.model)

        # Verifica se os dados foram recarregados corretamente
        if self.model.rowCount() == 0:
            print("DataFrame de processos está vazio após a atualização.")
        else:
            print("Dados no TableView foram atualizados.")
                
    def atualizar_tabela(self):
        # Verifica se o modelo da tabela é um QSqlTableModel
        if isinstance(self.model, QSqlTableModel):
            # Para QSqlTableModel, chame o método select() para atualizar os dados
            self.model.select()
        else:
            # Se não for um QSqlTableModel, talvez seja necessário realizar outras operações para atualizar a tabela
            print("O modelo da tabela não é um QSqlTableModel. Faça as operações de atualização apropriadas aqui.")

    def update_database(self):
        # Isso agora é um método público que pode ser chamado de SettingsDialog
        self.update_database_file()

    def save_to_control_prazos_batch(self, id_processos):
        with self.database_manager as conn:
            cursor = conn.cursor()
            today = datetime.today().strftime('%Y-%m-%d')

            for id_processo in id_processos:
                # Verificar se a chave já existe
                cursor.execute("SELECT COUNT(*) FROM controle_prazos WHERE chave_processo = ?", (id_processo,))
                if cursor.fetchone()[0] > 0:
                    # Se já existe, não sobrescrever (ou pode implementar uma lógica diferente se necessário)
                    continue

                # Inserir novos dados
                cursor.execute('''
                    INSERT INTO controle_prazos (chave_processo, etapa, data_inicial, sequencial)
                    VALUES (?, ?, ?, ?)
                ''', (id_processo, "Planejamento", today, 1))

            conn.commit()


class UIManager:
    def __init__(self, parent, icons, config_manager, model):
        self.parent = parent
        self.icons = icons
        self.config_manager = config_manager
        self.model = model
        self.main_widget = QWidget(parent)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.button_manager = ButtonManager(self.parent)
        self.init_ui()

    def init_ui(self):
        self.setup_search_and_buttons_layout()
        self.setup_table_view()
        self.parent.setCentralWidget(self.main_widget)

    def setup_search_and_buttons_layout(self):
        # Cria um QHBoxLayout para a barra de busca e botões
        self.search_buttons_layout = QHBoxLayout()

        # Adicionar texto "Localizar:"
        search_label = QLabel("Localizar:")
        search_label.setStyleSheet("font-size: 14px;")
        self.search_buttons_layout .addWidget(search_label)

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

    def setup_table_view(self):
        self.table_view = CustomTableView(main_app=self.parent, config_manager=self.config_manager, parent=self.main_widget)
        self.table_view.setModel(self.model)
        self.main_layout.addWidget(self.table_view)
        self.configure_table_model()
        self.table_view.verticalHeader().setVisible(False)
        self.adjust_columns()
        self.apply_custom_style()
        
        center_delegate = CenterAlignDelegate(self.table_view)
        for column in range(self.model.columnCount()):
            self.table_view.setItemDelegateForColumn(column, center_delegate)

        status_index = self.model.fieldIndex("etapa")
        self.table_view.setItemDelegateForColumn(status_index, CustomItemDelegate(self.icons, self.table_view))

    def configure_table_model(self):
        self.parent.proxy_model = QSortFilterProxyModel(self.parent)
        self.parent.proxy_model.setSourceModel(self.model)
        self.parent.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.parent.proxy_model.setFilterKeyColumn(-1)
        self.parent.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)
        self.table_view.setModel(self.parent.proxy_model)

        # Verifica se há dados na coluna 'etapa' antes de aplicar a ordenação inicial
        index_status = self.model.fieldIndex('etapa')
        if index_status != -1 and self.model.rowCount() > 0:
            etapa_data = [self.model.data(self.model.index(row, index_status)) for row in range(self.model.rowCount())]
            if any(etapa_data):  # Se houver algum dado na coluna 'etapa'
                self.initial_sort()

        self.model.dataChanged.connect(self.table_view.update)

        if self.table_view.selectionModel():
            self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
            self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
            self.table_view.selectionModel().selectionChanged.connect(self.linhaSelecionada)

        self.update_column_headers()
        self.hide_unwanted_columns()

    def initial_sort(self):
        index_status = self.model.fieldIndex('etapa')
        if index_status != -1:
            self.parent.proxy_model.sort(index_status, Qt.SortOrder.AscendingOrder)
            # print("Ordenação inicial por 'Etapa' aplicada.")
        else:
            print("Erro: Coluna 'Etapa' não encontrada para ordenação inicial.")
            
    def adjust_columns(self):
        # Ajustar automaticamente as larguras das colunas ao conteúdo
        self.table_view.resizeColumnsToContents()
        QTimer.singleShot(1, self.apply_custom_column_sizes) 

    def apply_custom_column_sizes(self):
        # print("Aplicando configurações de tamanho de coluna...")
        header = self.table_view.horizontalHeader()
        
        # Configurações específicas de redimensionamento para colunas selecionadas
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch) 
        # Definir tamanhos específicos onde necessário
        header.resizeSection(0, 250)
        header.resizeSection(1, 110)
        header.resizeSection(2, 200)
        header.resizeSection(4, 80)

    def apply_custom_style(self):
        # Aplica um estilo CSS personalizado ao tableView
        self.table_view.setStyleSheet("""
            QTableView {
                font-size: 16px;
            }
            QTableView::section {
                font-size: 16px;
                font-weight: bold; 
            }
            QHeaderView::section:horizontal {
                font-size: 16px;
                font-weight: bold;
            }
            QHeaderView::section:vertical {
                font-size: 16px;
            }
        """)

    def linhaSelecionada(self, selected, deselected):
        if selected.indexes():
            proxy_index = selected.indexes()[0]            
            source_index = self.parent.proxy_model.mapToSource(proxy_index)
           
            # Obtém a linha e a coluna no modelo original
            selected_row = source_index.row()
            selected_column = source_index.column()
            id_processo = self.parent.model.data(self.parent.model.index(source_index.row(), self.parent.model.fieldIndex('id_processo')))

            print(f"id_processo selecionado: {id_processo}")
            print(f"Linha selecionada: {selected_row}, Coluna: {selected_column}")

            # Carrega os dados usando a linha correta do modelo original
            df_registro_selecionado = carregar_dados_pregao(selected_row, self.parent.database_path)
            
            if not df_registro_selecionado.empty:
                logging.debug(f"Registro selecionado: {df_registro_selecionado.iloc[0].to_dict()}")
            else:
                logging.warning("Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")
                QMessageBox.warning(self.parent, "Erro", "Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")

    def update_column_headers(self):
        titles = {
            0: "Status",
            1: "ID Processo",
            2: "NUP",
            3: "Objeto",
            4: "UASG",
            6: "Pregoeiro"
        }
        for column, title in titles.items():
            self.model.setHeaderData(column, Qt.Orientation.Horizontal, title)

    def hide_unwanted_columns(self):
        visible_columns = {0, 1,2,3,4,6}
        for column in range(self.model.columnCount()):
            if column not in visible_columns:
                self.table_view.hideColumn(column)

class CustomSqlTableModel(QSqlTableModel):
    def __init__(self, parent=None, db=None, non_editable_columns=None, etapa_order=None):
        super().__init__(parent, db)
        self.non_editable_columns = non_editable_columns if non_editable_columns is not None else []
        self.etapa_order = etapa_order if etapa_order is not None else {}

    def flags(self, index):
        if index.column() in self.non_editable_columns:
            return super().flags(index) & ~Qt.ItemFlag.ItemIsEditable  # Remove a permissão de edição
        return super().flags(index)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # Verifica se a coluna deve ser não editável e ajusta o retorno para DisplayRole
        if role == Qt.ItemDataRole.DisplayRole and index.column() in self.non_editable_columns:
            return super().data(index, role)

        # Mantém a funcionalidade de ordenação personalizada para o UserRole
        if role == Qt.ItemDataRole.UserRole and self.headerData(index.column(), Qt.Orientation.Horizontal) == 'Status':
            etapa = super().data(index, Qt.ItemDataRole.DisplayRole)
            ordered_value = self.etapa_order.get(etapa, 999)  # Assume 999 as a high value for undefined stages
            return ordered_value

        return super().data(index, role)


class SqlModel:
    def __init__(self, database_manager, parent=None):
        self.database_manager = database_manager
        self.parent = parent
        self.etapa_order = {
            'Concluído': 0, 'Assinatura Contrato': 1, 
            'Sessão Pública': 2, 'Pré-Publicação': 3, 'Recomendações AGU': 4,
            'AGU': 5, 'Nota Técnica': 6, 'Montagem do Processo': 7, 'Consolidar Demandas': 8, 'Planejamento': 9
        }
        self.init_database()

    def init_database(self):
        if QSqlDatabase.contains("my_conn"):
            QSqlDatabase.removeDatabase("my_conn")
        self.db = QSqlDatabase.addDatabase('QSQLITE', "my_conn")
        self.db.setDatabaseName(str(self.database_manager.db_path))
        if not self.db.open():
            print("Não foi possível abrir a conexão com o banco de dados.")
        else:
            print("Conexão com o banco de dados aberta com sucesso.")
            self.create_table_if_not_exists()

    def create_table_if_not_exists(self):
        query = QSqlQuery(self.db)
        query.exec(
            '''
            CREATE TABLE IF NOT EXISTS controle_processos (
                etapa TEXT,
                id_processo PRIMARY KEY,
                nup TEXT,
                objeto TEXT,
                uasg TEXT,
                sigla_om TEXT,
                pregoeiro TEXT,
                tipo TEXT,
                numero TEXT,
                ano TEXT,
                objeto_completo TEXT,
                valor_total TEXT,
                orgao_responsavel TEXT,
                setor_responsavel TEXT,
                coordenador_planejamento TEXT,
                item_pca TEXT,
                portaria_PCA TEXT,
                data_sessao TEXT,
                data_limite_entrega_tr TEXT,
                nup_portaria_planejamento TEXT,
                srp TEXT,
                material_servico TEXT,
                parecer_agu TEXT,
                msg_irp TEXT,
                data_limite_manifestacao_irp TEXT,
                data_limite_confirmacao_irp TEXT,
                num_irp TEXT,
                om_participantes TEXT,
                link_pncp TEXT,
                link_portal_marinha TEXT,
                comentarios TEXT   
            )
            '''
        )
        if query.isActive():
            print("Tabela 'controle_processos' verificada/criada com sucesso.")
        else:
            print("Erro ao criar/verificar a tabela 'controle_processos':", query.lastError().text())
        # Verificar/criar tabela controle_prazos
        query.exec(
            '''
            CREATE TABLE IF NOT EXISTS controle_prazos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave_processo TEXT,
                etapa TEXT,
                data_inicial TEXT,
                data_final TEXT,
                dias_na_etapa INTEGER,
                comentario TEXT,
                sequencial INTEGER
            )
            '''
        )
        if query.isActive():
            print("Tabela 'controle_prazos' verificada/criada com sucesso.")
        else:
            print("Erro ao criar/verificar a tabela 'controle_prazos':", query.lastError().text())
                        
    def setup_model(self, table_name, editable=False):
        # Colunas 0, 1 e 4 não devem ser editáveis
        self.model = CustomSqlTableModel(
            parent=self.parent, 
            db=self.db, 
            non_editable_columns=[0, 1, 4],  # Adicione aqui as colunas não editáveis
            etapa_order=self.etapa_order
        )
        self.model.setTable(table_name)
        if editable:
            self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.model.select()
        return self.model

    def configure_columns(self, table_view, visible_columns):
        for column in range(self.model.columnCount()):
            header = self.model.headerData(column, Qt.Orientation.Horizontal)
            if column not in visible_columns:
                table_view.hideColumn(column)
            else:
                self.model.setHeaderData(column, Qt.Orientation.Horizontal, header)

class ButtonManager:
    def __init__(self, parent):
        self.parent = parent  # parent deveria ser uma instância de um QWidget ou classe derivada
        self.buttons = []
        self.create_buttons()

    def create_buttons(self):
        button_specs = [
            ("Adicionar", self.parent.image_cache['plus'], self.parent.on_add_item, "Adiciona um novo item ao banco de dados"),
            ("Salvar", self.parent.image_cache['excel'], self.parent.salvar_tabela, "Salva o dataframe em um arquivo excel('.xlsx')"),
            ("Excluir", self.parent.image_cache['delete'], self.parent.on_delete_item, "Exclui um item selecionado"),
            ("Controle", self.parent.image_cache['calendar'], self.parent.on_control_process, "Abre o painel de controle do processo"),
            ("Database", self.parent.image_cache['data-processing'], self.parent.open_carregar_tabela_dialog, "Abre o painel de controle do processo"),
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
            max-width: 120px; 
            max-height: 20px;
        """)
        
        return btn

class CarregarTabelaDialog(QDialog):
    def __init__(self, database_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Carregar Tabela e Gerenciar Database")
        self.database_manager = database_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Botão para carregar a tabela
        btn_carregar_tabela = QPushButton("Carregar Tabela")
        btn_carregar_tabela.clicked.connect(self.carregar_tabela)
        layout.addWidget(btn_carregar_tabela)

        # Botão para excluir o database
        btn_excluir_database = QPushButton("Excluir Database")
        btn_excluir_database.clicked.connect(self.excluir_tabela)
        layout.addWidget(btn_excluir_database)

        # Botão de fechar
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

    def carregar_tabela(self):
        # Abre um diálogo para selecionar o arquivo Excel
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecione a tabela Excel", "", "Excel Files (*.xlsx)")
        
        if not file_path:
            return  # Se o usuário cancelar, saia da função

        # Carrega o DataFrame do arquivo Excel
        df = pd.read_excel(file_path)

        # Verifica se os campos obrigatórios estão presentes
        campos_obrigatorios = ["tipo", "numero", "ano", "objeto", "uasg"]
        for campo in campos_obrigatorios:
            if campo not in df.columns:
                QMessageBox.warning(self, "Erro", f"O campo obrigatório '{campo}' não foi encontrado no arquivo Excel.")
                return

        # Preparar uma lista de dados para inserção em massa
        itens_para_inserir = []
        id_processos = []

        for index, row in df.iterrows():
            # Prepara o item_data com os valores necessários
            item_data = {
                'tipo': row['tipo'],
                'numero': f"{int(row['numero']):02}",
                'ano': row['ano'],
                'objeto': row['objeto'],
                'sigla_om': row.get('sigla_om', None),
                'material_servico': row.get('material_servico', None),
                'id_processo': f"{row['tipo']} {int(row['numero']):02}/{row['ano']}",
                'nup': row.get('nup', None),
                'orgao_responsavel': row.get('orgao_responsavel', None),
                'uasg': row['uasg'],
                'etapa': "Planejamento",
                'pregoeiro': "-"
            }

            # Adiciona o item à lista de itens para inserção
            itens_para_inserir.append(item_data)
            id_processos.append(item_data['id_processo'])

        # Desabilita atualizações na interface enquanto processa os itens
        self.parent().model.layoutAboutToBeChanged.emit()

        try:
            # Inserir todos os itens no banco de dados
            for item_data in itens_para_inserir:
                print(f"Processando id_processo: {item_data['id_processo']}")
                self.parent().save_to_database(item_data)

            # Inserir todos os id_processo no controle_prazos de uma vez
            self.parent().save_to_control_prazos_batch(id_processos)

            # Recriar o modelo e notificar a interface gráfica que o layout foi alterado
            self.parent().initialize_ui()
        finally:
            # Reabilita as atualizações na interface
            self.parent().model.layoutChanged.emit()

        QMessageBox.information(self, "Carregamento Completo", "Os dados foram carregados e salvos no banco de dados com sucesso.")

    def prepare_context(self, row):
        """
        Prepara o valor de id_processo e o valor para a coluna etapa.
        
        Args:
        row (pandas.Series): Uma linha do DataFrame contendo os dados do processo.

        Returns:
        tuple: Retorna uma tupla contendo (id_processo, etapa).
        """
        # Formata o valor de 'numero' para ter duas casas decimais
        numero_formatado = f"{int(row['numero']):02}"
        id_processo = f"{row['tipo']} {numero_formatado}/{row['ano']}"
        etapa = "Planejamento"
        return id_processo, etapa


    def excluir_tabela(self):
        reply = QMessageBox.question(self, "Confirmação", "Tem certeza que deseja excluir todos os registros das tabelas 'controle_processos' e 'controle_prazos'?", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                    QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.database_manager as conn:
                    cursor = conn.cursor()
                    # Exclui todos os registros de controle_processos
                    cursor.execute("DELETE FROM controle_processos")
                    # Exclui todos os registros de controle_prazos
                    cursor.execute("DELETE FROM controle_prazos")
                    conn.commit()
                    
                    # Atualiza o modelo da UI
                    self.parent().model.select()
                    self.parent().ui_manager.table_view.viewport().update()
                    
                    QMessageBox.information(self, "Sucesso", "Todos os registros das tabelas 'controle_processos' e 'controle_prazos' foram excluídos com sucesso.")
            except sqlite3.Error as e:
                print(f"Erro ao tentar excluir os registros das tabelas: {e}")
                QMessageBox.warning(self, "Erro", f"Não foi possível excluir os registros das tabelas: {e}")


class TableMenu(QMenu):
    def __init__(self, main_app, index, model=None, config_manager=None):
        super().__init__()
        self.main_app = main_app
        self.index = index
        self.config_manager = config_manager 
        self.model = model

        # Configuração do estilo do menu
        self.setStyleSheet("""
            QMenu {
                font-size: 14px;
                font-weight: bold;
            }
        """)

        # Opções do menu principal
        actions = [
            "Editar Dados do Processo",
            "1. Autorização para Abertura de Licitação",
            "2. Portaria de Equipe de Planejamento",
            "3. Documento de Formalização de Demanda (DFD)",
        ]
        
        for actionText in actions:
            action = QAction(actionText, self)
            action.triggered.connect(partial(self.trigger_action, actionText))
            self.addAction(action)

        # Submenu para "4. Intenção de Registro de Preços (IRP)"
        submenu_irp = QMenu("4. Intenção de Registro de Preços (IRP)", self)
        submenu_irp.setStyleSheet(self.styleSheet())
        opcoes_irp = [
            ("4.1. Manifesto de IRP da OM participante", self.openDialogIRPManifesto),
            ("4.2. Mensagem de Divulgação de IRP", self.abrirDialogoIRP),
            ("4.3. Lançar o IRP", self.abrirDialogoIRP),
            ("4.4. Conformidade do IRP (Local, R$, etc)", self.abrirDialogoIRP),
        ]
        for texto, funcao in opcoes_irp:
            sub_action = QAction(texto, submenu_irp)
            sub_action.triggered.connect(partial(self.trigger_sub_action, funcao))
            submenu_irp.addAction(sub_action)
        self.addMenu(submenu_irp)

        # Adicionando as opções do menu
        actions_2 = [
            "6. Estudo Técnico Preliminar (ETP)",
            "7. Termo de Referência (TR)",
            "8. Matriz de Riscos",
        ]

        for actionText in actions_2:
            action = QAction(actionText, self)
            action.triggered.connect(partial(self.trigger_action, actionText))
            self.addAction(action)

        # Submenu "10. Edital e Anexos"
        submenu_edital = QMenu("9. Edital e Anexos", self)
        submenu_edital.setStyleSheet(self.styleSheet())
        opcoes_edital = [
            ("9.1 Edital", self.openDialogEdital),
            ("9.2 Capa do Edital", self.openDialogCapaEdital),
            ("9.3 Contrato", self.openDialogContrato),
            ("9.4 Ata de Registro de Preços", self.openDialogAtaRegistro)
        ]
        for texto, funcao in opcoes_edital:
            sub_action = QAction(texto, submenu_edital)
            sub_action.triggered.connect(partial(self.trigger_sub_action, funcao))
            submenu_edital.addAction(sub_action)
        self.addMenu(submenu_edital)

        # Adicionando mais ações principais após o submenu
        actions_3 = [
            "10. Check-list",
            "11. Nota Técnica",
            "12. CP Encaminhamento AGU",
            "13. CP Recomendações AGU",
            "14. Escalar Pregoeiro",
            "15. Mensagem de Publicação",
            "16. Mensagem de Homologação",            
            "17. Gerar Relatório de Processo",
        ]
        for actionText in actions_3:
            action = QAction(actionText, self)
            action.triggered.connect(partial(self.trigger_action, actionText))
            self.addAction(action)

    def trigger_sub_action(self, funcao):
        if self.index.isValid():
            source_index = self.model.mapToSource(self.index)
            selected_row = source_index.row()
            df_registro_selecionado = carregar_dados_pregao(selected_row, str(self.main_app.database_path))
            if not df_registro_selecionado.empty:
                funcao(df_registro_selecionado)
            else:
                QMessageBox.warning(self, "Atenção", "Dados não encontrados.")

    def trigger_action(self, actionText):
        if self.index.isValid():
            if isinstance(self.model, QSortFilterProxyModel):
                source_index = self.model.mapToSource(self.index)
            else:
                source_index = self.index
            
            selected_row = source_index.row()
            df_registro_selecionado = carregar_dados_pregao(selected_row, str(self.main_app.database_path))                                    
            if not df_registro_selecionado.empty:
                if actionText == "Editar Dados do Processo":
                    self.editar_dados(df_registro_selecionado)
                elif actionText == "1. Autorização para Abertura de Licitação":
                    self.openDialogAutorizacao(df_registro_selecionado)
                elif actionText == "2. Portaria de Equipe de Planejamento":
                    self.openDialogPortariaPlanejamento(df_registro_selecionado)
                elif actionText == "3. Documento de Formalização de Demanda (DFD)":
                    self.openDialogDFD(df_registro_selecionado)
                elif actionText == "5. Mensagem de Divulgação de IRP":
                    self.abrirDialogoIRP(df_registro_selecionado)
                elif actionText == "6. Estudo Técnico Preliminar (ETP)":
                    self.openDialogETP(df_registro_selecionado)
                elif actionText == "8. Matriz de Riscos":
                    self.openDialogMatrizRiscos(df_registro_selecionado)
                elif actionText == "12. CP Encaminhamento AGU":
                    self.openDialogEncaminhamentoAGU(df_registro_selecionado)
                elif actionText == "14. Escalar Pregoeiro":
                    self.openDialogEscalarPregoeiro(df_registro_selecionado)
                elif actionText == "15. Mensagem de Publicação":
                    self.abrirDialogoPublicacao(df_registro_selecionado)
                elif actionText == "16. Mensagem de Homologação":
                    self.abrirDialogoHomologacao(df_registro_selecionado)
                elif actionText == "10. Check-list":
                    self.openChecklistDialog(df_registro_selecionado)
            else:
                QMessageBox.warning(self, "Atenção", "Nenhum registro selecionado ou dados não encontrados.")
        else:
            QMessageBox.warning(self, "Atenção", "Nenhuma linha selecionada.")

    # No final da classe TableMenu:
    def on_get_pregoeiro(self):
        id_processo = self.df_licitacao_completo['id_processo'].iloc[0]
        dialog = EscalarPregoeiroDialog(self.df_licitacao_completo, id_processo, self)
        dialog.exec()

    def openDialogIRPManifesto(self, df_registro_selecionado):
        dialog = GerarManifestoIRP(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def abrirDialogoIRP(self, df_registro_selecionado):
        if not df_registro_selecionado.empty:
            dados = df_registro_selecionado.iloc[0].to_dict()
            dialogo = MSGIRP(dados=dados, icons_dir=str(ICONS_DIR), parent=self)
            dialogo.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum registro selecionado.")

    def abrirDialogoPublicacao(self, df_registro_selecionado):
        if not df_registro_selecionado.empty:
            dados = df_registro_selecionado.iloc[0].to_dict()
            dialogo = MSGPublicacao(dados=dados, icons_dir=str(ICONS_DIR), parent=self)
            dialogo.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum registro selecionado.")

    def abrirDialogoHomologacao(self, df_registro_selecionado):
        if not df_registro_selecionado.empty:
            dados = df_registro_selecionado.iloc[0].to_dict()
            dialogo = MSGHomolog(dados=dados, icons_dir=str(ICONS_DIR), parent=self)
            dialogo.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum registro selecionado.")

    def editar_dados(self, df_registro_selecionado):
        dialog = EditarDadosDialog(ICONS_DIR, parent=self, dados=df_registro_selecionado.iloc[0].to_dict())
        dialog.dados_atualizados.connect(self.main_app.atualizar_tabela)
        dialog.show()

    def openChecklistDialog(self, df_registro_selecionado):
        dialog = QDialog(self)
        dialog.setWindowTitle("Check-list")
        dialog.resize(950, 800)
        dialog.setStyleSheet("background-color: black; color: white;")
        
        # Instancia o ChecklistWidget e passa o DataFrame como argumento
        checklist_widget = ChecklistWidget(parent=dialog, config_manager=self.config_manager, icons_path=self.main_app.icons_dir, df_registro_selecionado=df_registro_selecionado)

        layout = QVBoxLayout(dialog)
        layout.addWidget(checklist_widget)
        dialog.exec()

    def openDialogDFD(self, df_registro_selecionado):
        dialog = GerarDFD(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogAutorizacao(self, df_registro_selecionado):
        dialog = AutorizacaoAberturaLicitacaoDialog(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogPortariaPlanejamento(self, df_registro_selecionado):
        dialog = GerarPortariaPlanejamento(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogETP(self, df_registro_selecionado):
        dialog = GerarETP(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogMatrizRiscos(self, df_registro_selecionado):
        dialog = GerarMR(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogEncaminhamentoAGU(self, df_registro_selecionado):
        dialog = CPEncaminhamentoAGU(main_app=self.main_app, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogCapaEdital(self, df_registro_selecionado):
        dialog = CapaEdital(main_app=self.main_app, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogEdital(self, df_registro_selecionado):
        dialog = EditalDialog(main_app=self.main_app, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogContrato(self, df_registro_selecionado):
        pass

    def openDialogAtaRegistro(self, df_registro_selecionado):
        pass

    def openDialogEscalarPregoeiro(self, df_registro_selecionado):
        dialog = EscalarPregoeiroDialog(main_app=self.main_app, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()
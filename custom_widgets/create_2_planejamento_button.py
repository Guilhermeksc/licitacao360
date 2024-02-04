#create_2_planejamento_button.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QIcon, QFont, QMovie
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
from diretorios import *
from utils.treeview_utils import load_images, create_button, save_dataframe_to_excel
from utils.utilidades import ler_arquivo_json, escrever_arquivo_json, inicializar_json_do_excel, sincronizar_json_com_dataframe
import pandas as pd
import json
import os
import datetime
import openpyxl
df_uasg = pd.read_excel(TABELA_UASG_DIR)
global df_registro_selecionado
df_registro_selecionado = None

def ajustar_colunas_planilha(file_path):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    column_widths = {
        1: 10, 
        2: 10, 
        3: 25, 
        4: 35, 
        5: 0,
        6: 40, 
        7: 10, 
        8: 20, 
        9: 10,
        10: 20, 
        11: 20
    }

    for col_num, width in column_widths.items():
        if width > 0:
            column_letter = openpyxl.utils.get_column_letter(col_num)
            sheet.column_dimensions[column_letter].width = width

    workbook.save(file_path)

class ApplicationUI(QMainWindow):
    itemSelected = pyqtSignal(str, str, str)  # Sinal com dois argumentos de string

    NOME_COLUNAS = {
        'mod': 'Mod.',
        'num_pregao': 'N',
        'ano_pregao': 'Ano',
        'nup': 'NUP',
        'objeto': 'Objeto',
        'uasg': 'UASG',
        'orgao_responsavel': 'Órgão Responsável',
        'sigla_om': 'Sigla Órgão',
        'setor_responsavel': 'Demandante',
        'coordenador_planejamento': 'Coordenador',
        'etapa': 'Etapa',
        'pregoeiro': 'Pregoeiro',
    }

    dtypes = {
        'num_pregao': int,
        'ano_pregao': int,
        'mod': str,
        'nup': str,
        'objeto': str,
        'uasg': str,
        'orgao_responsavel': str,
        'sigla_om': str,
        'setor_responsavel': str,
        'coordenador_planejamento': str,
        'etapa': str,
        'pregoeiro': str
    }

    def __init__(self, app, icons_dir, database_dir, lv_final_dir):

        super().__init__()
        self.icons_dir = Path(icons_dir)
        self.database_dir = Path(database_dir)
        self.lv_final_dir = Path(lv_final_dir)
        self.app = app  # Armazenar a instância do App
        
        # Carregar df_uasg uma única vez aqui
        self.df_uasg = pd.read_excel(TABELA_UASG_DIR)
        
        self.columns_treeview = list(self.NOME_COLUNAS.keys())
        self.image_cache = {}
        inicializar_json_do_excel(CONTROLE_PROCESSOS_DIR, PROCESSOS_JSON_PATH)

        # Carregar os dados de licitação no início, removendo a inicialização redundante
        # self.df_licitacao_completo = pd.read_excel(CONTROLE_PROCESSOS_DIR, dtype={'num_pregao': 'Int64'}, converters={'num_pregao': lambda x: self.convert_to_int(x)})
        self.df_licitacao_completo = pd.read_excel(CONTROLE_PROCESSOS_DIR, converters={'num_pregao': lambda x: self.convert_to_int(x)})

        self.image_cache = load_images(self.icons_dir, [
            "plus.png", "save_to_drive.png", "loading.png", "delete.png", "excel.png"
        ])
        self.setup_ui()

    def convert_to_int(self, cell_value):
        try:
            return int(cell_value)
        except ValueError:
            return pd.NA  # or some default value or error handling pd.NA  # or a default value like 0 or -1 depending on your requirements

    def _get_image(self, image_file_name):
        # Método para obter imagens do cache ou carregar se necessário
        if image_file_name not in self.image_cache:
            image_path = self.icons_dir / image_file_name
            self.image_cache[image_file_name] = QIcon(str(image_path))  # Usando QIcon para compatibilidade com botões
        return self.image_cache[image_file_name]

    def setup_ui(self):
        self._setup_central_widget()
        self._setup_treeview()  # Configura o QTreeView
        self._adjust_column_widths() 
        self._setup_uasg_delegate()
        self._setup_buttons_layout()
        self.main_layout.addWidget(self.tree_view)
        self._load_data()

    def _setup_central_widget(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
    def _setup_buttons_layout(self):
        self.buttons_layout = QHBoxLayout()
        self._create_buttons()
        self.main_layout.addLayout(self.buttons_layout)
            
    def _create_buttons(self):
        self.buttons_layout = QHBoxLayout()
        self.button_specs = [
            ("Adicionar", self.image_cache['plus'], self.on_add_item, "Adiciona um novo item"),
            ("Salvar", self.image_cache['save_to_drive'], self.on_save_data, "Salva o dataframe em um arquivo excel('.xlsx')"),
            ("Carregar", self.image_cache['loading'], self.on_load_data, "Carrega o dataframe de um arquivo existente('.xlsx' ou '.odf')"),
            ("Excluir", self.image_cache['delete'], self.on_delete_item, "Adiciona um novo item"),
            ("Abrir Planilha Excel", self.image_cache['excel'], self.abrir_planilha_controle, "Abre a planilha de controle"),
        ]

        for text, icon, callback, tooltip in self.button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self)
            self.buttons_layout.addWidget(btn)  # Adicione o botão ao layout dos botões

    def abrir_planilha_controle(self):
        file_path = str(CONTROLE_PROCESSOS_DIR)  # Defina o caminho do arquivo aqui
        try:
            ajustar_colunas_planilha(file_path)
            os.startfile(file_path)
        except Exception as e:
            print(f"Erro ao abrir o arquivo: {e}")

    def _setup_treeview(self):
        # Cria uma nova instância do modelo
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([self.NOME_COLUNAS[col] for col in self.NOME_COLUNAS])

        # Configurações do QTreeView
        self.tree_view = QTreeView(self)
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIsDecorated(False)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.clicked.connect(self._on_item_click)
        self.tree_view.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.model.dataChanged.connect(self._on_item_changed)

        # Adiciona o QTreeView ao layout principal
        self.main_layout.addWidget(self.tree_view)

        # Ajusta as larguras das colunas
        self._adjust_column_widths()

    def _adjust_column_widths(self):
        header = self.tree_view.header()
        header.setStretchLastSection(True)

        # Configura todas as colunas para ajustar-se ao conteúdo
        for column in range(self.model.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

    def on_context_menu(self, point):
        # Obter o índice do item sob o cursor quando o menu de contexto é solicitado
        index = self.tree_view.indexAt(point)
        
        if index.isValid():
            # Chamar _on_item_click se o índice é válido
            self._on_item_click(index)

            # Criar o menu de contexto
            context_menu = QMenu(self.tree_view)

            # Configurar o estilo do menu de contexto
            context_menu.setStyleSheet("QMenu { font-size: 12pt; }")

            # Adicionar outras ações ao menu
            add_action = context_menu.addAction(QIcon(str(self.icons_dir / "add.png")), "Adicionar")
            edit_action = context_menu.addAction(QIcon(str(self.icons_dir / "engineering.png")), "Editar")
            delete_action = context_menu.addAction(QIcon(str(self.icons_dir / "delete.png")), "Excluir")
            view_action = context_menu.addAction(QIcon(str(self.icons_dir / "search.png")), "Visualizar")

            # Conectar ações a métodos
            add_action.triggered.connect(self.on_add_item)
            edit_action.triggered.connect(self.on_edit_item)
            delete_action.triggered.connect(self.on_delete_item)
            view_action.triggered.connect(self.on_view_item)

            # Executar o menu de contexto na posição do cursor
            context_menu.exec(self.tree_view.viewport().mapToGlobal(point))

    def on_add_item(self):
        # Encontrar o maior número de pregão e adicionar 1
        if not self.model.rowCount():
            novo_num_pregao = 1
        else:
            ultimo_num_pregao = max(int(self.model.item(row, self.columns_treeview.index('num_pregao')).text()) for row in range(self.model.rowCount()))
            novo_num_pregao = ultimo_num_pregao + 1

        # Obter o ano atual
        ano_atual = datetime.datetime.now().year

        # Definir o valor padrão para UASG
        uasg_valor_padrao = "787000"

        # Buscar os dados correspondentes em df_uasg
        uasg_data = self.df_uasg[self.df_uasg['uasg'].astype(str) == uasg_valor_padrao]
        if not uasg_data.empty:
            orgao_responsavel = uasg_data['orgao_responsavel'].iloc[0]
            sigla_om = uasg_data['sigla_om'].iloc[0]
        else:
            orgao_responsavel = "NaN"
            sigla_om = "NaN"
        
        valor_etapa_padrao = "Planejamento"
        mod_padrao = "PE"

        # Criar os valores predefinidos para exibição no QTreeView
        valores_treeview = [
            mod_padrao,
            novo_num_pregao,
            ano_atual,
            f"62055.XXXXXX/{ano_atual}-XX",
            "NaN",  # Objeto
            "787000",
            "NaN",  
        ]

        # Criar uma nova linha no QTreeView com esses valores
        items = [QStandardItem(str(valor)) for valor in valores_treeview]
        self.model.appendRow(items)

        # Criar um dicionário com todos os valores para o DataFrame
        novo_registro = {
            'mod': mod_padrao,
            'num_pregao': novo_num_pregao,
            'ano_pregao': ano_atual,
            'nup': f"62055.XXXXXX/{ano_atual}-XX",
            'objeto': "NaN",
            'uasg': "787000",
            'setor_responsavel': "NaN",
            'orgao_responsavel': orgao_responsavel,  # Colunas adicionais para o DataFrame
            'sigla_om': sigla_om,
            'etapa': valor_etapa_padrao,
            'pregoeiro': "NaN"
        }

        # Verificar se a coluna "etapa" existe no DataFrame, se não, adicioná-la
        if 'etapa' not in self.df_licitacao_completo.columns:
            self.df_licitacao_completo['etapa'] = pd.NA
            
        # Adicionar o novo registro ao DataFrame
        novo_df = pd.DataFrame([novo_registro])
        self.df_licitacao_completo = pd.concat([self.df_licitacao_completo, novo_df], ignore_index=True)

        # Salvar o DataFrame atualizado no arquivo Excel
        save_dataframe_to_excel(self.df_licitacao_completo, CONTROLE_PROCESSOS_DIR)
        sincronizar_json_com_dataframe(self.df_licitacao_completo, PROCESSOS_JSON_PATH)

    def on_edit_item(self):
        # Implementar lógica de edição aqui
        print("Editar item")
    
    def on_save_data(self):
        try:
            # Preencher automaticamente valores NaN na coluna 'etapa' com 'Planejamento'
            self.df_licitacao_completo['etapa'] = self.df_licitacao_completo['etapa'].fillna('Planejamento')

            # Salvar o DataFrame no arquivo Excel
            self.df_licitacao_completo.to_excel(CONTROLE_PROCESSOS_DIR, index=False)
            sincronizar_json_com_dataframe(self.df_licitacao_completo, PROCESSOS_JSON_PATH)

            QMessageBox.information(self, "Sucesso", "Dados salvos com sucesso!")
        except PermissionError:
            QMessageBox.warning(self, "Erro de Permissão", "Não foi possível salvar o arquivo. Por favor, feche o arquivo Excel e tente novamente.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao salvar o arquivo: {str(e)}")

    def on_load_data(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo", "", "Excel Files (*.xlsx *.xls);;ODF Files (*.odf)")
        if not file_name:
            return 
        try:
            loaded_df = pd.read_excel(file_name, dtype=self.dtypes)
            self.df_licitacao_completo = loaded_df
            self.model.clear()
            self.model.setHorizontalHeaderLabels([self.NOME_COLUNAS[col] for col in self.columns_treeview])

            # Preenche o QTreeView com os dados carregados
            for _, row in self.df_licitacao_completo.iterrows():
                items = [QStandardItem(str(row[col])) for col in self.columns_treeview]
                self.model.appendRow(items)

            # Chama a função para ajustar a largura das colunas
            self._adjust_column_widths()
            sincronizar_json_com_dataframe(self.df_licitacao_completo, PROCESSOS_JSON_PATH)

            QMessageBox.information(self, "Sucesso", "Dados carregados com sucesso do arquivo.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {e}")

    def on_delete_item(self):
        # Obter o índice do item selecionado
        current_index = self.tree_view.currentIndex()
        if not current_index.isValid():
            QMessageBox.warning(self, "Seleção", "Por favor, selecione um item para excluir.")
            return

        # Obter o número do pregão e o ano do pregão do item selecionado
        row = current_index.row()
        num_pregao = self.model.item(row, self.columns_treeview.index('num_pregao')).text()
        ano_pregao = self.model.item(row, self.columns_treeview.index('ano_pregao')).text()

        # Remover a linha do modelo QTreeView
        self.model.removeRow(row)

        # Atualizar o DataFrame
        self.df_licitacao_completo = self.df_licitacao_completo[
            ~((self.df_licitacao_completo['num_pregao'].astype(str) == num_pregao) &
            (self.df_licitacao_completo['ano_pregao'].astype(str) == ano_pregao))
        ]

        # Salvar o DataFrame atualizado no arquivo Excel
        save_dataframe_to_excel(self.df_licitacao_completo, CONTROLE_PROCESSOS_DIR)
        sincronizar_json_com_dataframe(self.df_licitacao_completo, PROCESSOS_JSON_PATH)

        QMessageBox.information(self, "Sucesso", "Item excluído com sucesso.")

    def on_view_item(self):
        # Implementar lógica de visualização aqui
        print("Visualizar item")

    def _setup_uasg_delegate(self):
        # Configuração do ComboBoxDelegate movida para este método
        uasg_items = [str(item) for item in self.df_uasg['uasg'].tolist()]
        self.uasg_delegate = ComboBoxDelegate(self.tree_view)
        self.uasg_delegate.setItems(uasg_items)
        self.tree_view.setItemDelegateForColumn(self.columns_treeview.index('uasg'), self.uasg_delegate)

        # Carrega os dados no QTreeView
        self._load_data_to_treeview()

    def _load_data_to_treeview(self):
        # Atualiza o modelo com dados atuais do DataFrame
        self.model.clear()  # Limpa o modelo atual
        self.model.setHorizontalHeaderLabels([self.NOME_COLUNAS[col] for col in self.columns_treeview])

        # Preenche o QTreeView com os dados do DataFrame
        for _, row in self.df_licitacao_completo.iterrows():
            items = [QStandardItem(str(row[col])) for col in self.columns_treeview]
            self.model.appendRow(items)

        # Ajusta as larguras das colunas após carregar os dados
        self._adjust_column_widths()

    def _on_item_changed(self, top_left_index, bottom_right_index, roles):
        if Qt.ItemDataRole.EditRole in roles:
            # Salvar a posição atual do scrollbar
            scrollbar = self.tree_view.verticalScrollBar()
            old_scroll_pos = scrollbar.value()

            row = top_left_index.row()
            column = top_left_index.column()
            column_name = self.columns_treeview[column]

            # Obter o valor atualizado
            new_value = str(self.model.itemFromIndex(top_left_index).text())

            # Atualizar o DataFrame se a coluna UASG foi alterada
            if column_name == 'uasg':
                uasg_data = self.df_uasg[self.df_uasg['uasg'].astype(str) == new_value]

                # Se encontrou a UASG correspondente, atualizar as colunas no DataFrame
                if not uasg_data.empty:
                    orgao_responsavel = uasg_data['orgao_responsavel'].iloc[0]
                    sigla_om = uasg_data['sigla_om'].iloc[0]

                    # Atualizar o DataFrame df_licitacao_completo
                    self.df_licitacao_completo.loc[
                        (self.df_licitacao_completo['num_pregao'].astype(str) == self.model.item(row, self.columns_treeview.index('num_pregao')).text()) &
                        (self.df_licitacao_completo['ano_pregao'].astype(str) == self.model.item(row, self.columns_treeview.index('ano_pregao')).text()),
                        ['orgao_responsavel', 'sigla_om']
                    ] = [orgao_responsavel, sigla_om]

            # Obter os valores de identificação únicos (num_pregao e ano_pregao)
            num_pregao = self.model.item(row, self.columns_treeview.index('num_pregao')).text()
            ano_pregao = self.model.item(row, self.columns_treeview.index('ano_pregao')).text()

            # Atualizar o DataFrame para todas as outras colunas
            self.df_licitacao_completo.loc[
                (self.df_licitacao_completo['num_pregao'].astype(str) == num_pregao) &
                (self.df_licitacao_completo['ano_pregao'].astype(str) == ano_pregao),
                column_name
            ] = new_value

            # Salvar o DataFrame atualizado no arquivo Excel
            save_dataframe_to_excel(self.df_licitacao_completo, CONTROLE_PROCESSOS_DIR)
            sincronizar_json_com_dataframe(self.df_licitacao_completo, PROCESSOS_JSON_PATH)

            self._load_data_to_treeview()

            # Restaurar a posição do scrollbar
            scrollbar.setValue(old_scroll_pos)

            # Garantir que a linha editada esteja visível
            self.tree_view.scrollTo(self.model.index(row, 0), QAbstractItemView.ScrollHint.PositionAtCenter)

    def _load_data(self):
        try:
            self.df_licitacao_completo = pd.read_excel(CONTROLE_PROCESSOS_DIR, dtype=self.dtypes)

            # Preencher automaticamente valores NaN na coluna 'etapa' com 'Planejamento'
            self.df_licitacao_completo['etapa'] = self.df_licitacao_completo['etapa'].fillna('Planejamento')

            for _, row in self.df_licitacao_completo.iterrows():
                items = [QStandardItem(str(row[col])) for col in self.NOME_COLUNAS]
                self.model.appendRow(items)
        except Exception as e:
            print(f"Ocorreu um erro ao carregar os dados: {e}")
        self.df_licitacao_exibicao = self.df_licitacao_completo[self.columns_treeview]
        self._populate_treeview()

    def _populate_treeview(self):
        """Populate the treeview with the loaded data."""
        self.model.removeRows(0, self.model.rowCount())
        for index, row in self.df_licitacao_exibicao.iterrows():
            items = [QStandardItem(str(row[col])) for col in self.columns_treeview]
            self.model.appendRow(items)

    def _on_item_click(self, index):
        # Obtenha os valores do item selecionado
        mod = self.model.item(index.row(), self.columns_treeview.index('mod')).text()
        num_pregao = self.model.item(index.row(), self.columns_treeview.index('num_pregao')).text()
        ano_pregao = self.model.item(index.row(), self.columns_treeview.index('ano_pregao')).text()

        print(f"Emitindo sinal para {mod} {num_pregao}/{ano_pregao}")  # Adicione isto para depuração
        self.itemSelected.emit(mod, num_pregao, ano_pregao)

        # Chama o método para processar e salvar o item selecionado
        selected_values = self._get_selected_item_values()
        if selected_values:
            self._process_selected_item(selected_values)

    def _get_selected_item_values(self):
        row = self.tree_view.currentIndex().row()
        if row == -1:
            return []  # Nenhuma linha selecionada

        values = []
        for col in range(self.model.columnCount()):
            item = self.model.item(row, col)
            if item is not None:
                values.append(item.text())
            else:
                values.append("")  # Se não houver item, adicione uma string vazia

        return values

    def _process_selected_item(self, selected_values):
        """Process the selected item."""
        # Recarregar os dados mais recentes do arquivo Excel
        self.df_licitacao_completo = pd.read_excel(CONTROLE_PROCESSOS_DIR, dtype=self.dtypes)

        mod, num_pregao, ano_pregao = selected_values[:3]

        # Filtra o DataFrame completo para encontrar a linha com o num_pregao e ano_pregao correspondentes
        registro_completo = self.df_licitacao_completo[
            (self.df_licitacao_completo['mod'].astype(str).str.strip() == mod) &            
            (self.df_licitacao_completo['num_pregao'].astype(str).str.strip() == num_pregao) &
            (self.df_licitacao_completo['ano_pregao'].astype(str).str.strip() == ano_pregao)
        ]

        if registro_completo.empty:
            # Se nenhum registro for encontrado, retorne False
            return False

        global df_registro_selecionado  # Declare o uso da variável global
        self.itemSelected.emit(mod, num_pregao, ano_pregao)

        df_registro_selecionado = pd.DataFrame(registro_completo)
        df_registro_selecionado.to_csv(ITEM_SELECIONADO_PATH, index=False, encoding='utf-8-sig')
        print(f"Registro salvo em {ITEM_SELECIONADO_PATH}")
        self.app.pregao_selecionado()

        return True

    def run(self):
        """Run the application."""
        self.show()
        self._adjust_column_widths()  

class ComboBoxDelegate(QItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []

    def setItems(self, items):
        self.items = [str(item) for item in items]  # Certifique-se de que todos os itens são strings

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.items)  # Adiciona itens ao editor
        return editor
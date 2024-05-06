from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from pathlib import Path
from gerar_atas_pasta.regex_termo_homolog import *
from gerar_atas_pasta.regex_sicaf import *
from gerar_atas_pasta.canvas_gerar_atas import *
from utils.treeview_utils import open_folder, load_images, create_button
from diretorios import *
import os
import pandas as pd
import pdfplumber
import webbrowser
from styles.styless import get_transparent_title_style

TXT_OUTPUT_PATH = DATABASE_DIR / "relacao_cnpj.txt"
NUMERO_ATA_GLOBAL = None
GERADOR_NUMERO_ATA = None
CSV_OUTPUT_PATH = DATABASE_DIR / "dados.csv"
tr_variavel_df_carregado = None

class DocumentTableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self._headers = headers

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._data.columns)

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def get_headers(self):
        return self._headers

class GerarAtasWidget(QWidget):
    def __init__(self, icons_dir, parent=None):
        super().__init__(parent)
        self.pdf_dir = PDF_DIR  # Já existente para PDF_DIR
        self.sicaf_dir = SICAF_DIR  # Adicionando para SICAF_DIR

        global_event_manager.pdf_dir_updated.connect(self.on_pdf_dir_updated)
        global_event_manager.sicaf_dir_updated.connect(self.on_sicaf_dir_updated)

        self.icons_dir = Path(icons_dir)

        self.image_cache = load_images(self.icons_dir, [
            "table.png", "data-processing.png", "performance.png", "data-collection.png", "data-collection2.png", "calendar.png", "report.png", "management.png"
        ])

        self.tr_variavel_df_carregado = None
        self.nome_arquivo_carregado = ""
        self.botoes = []  # Inicializando a lista de botões
        self.setup_ui()
        self.setMinimumSize(1200, 600)  # Define o tamanho mínimo da janela para 1200x600

        self.tr_df_carregado = None
        arquivo_salvo = self.load_file_path()
        try:
            if arquivo_salvo:
                self.tr_variavel_df_carregado = pd.read_excel(arquivo_salvo)
                self.nome_arquivo_carregado = os.path.basename(arquivo_salvo)
            else:
                raise FileNotFoundError
        except FileNotFoundError:
            self.nome_arquivo_carregado = ""
            print("Arquivo não encontrado.")

        self.progressDialog = None
        self.sicafDialog = None
        self.atasDialog = None

    def on_pdf_dir_updated(self, new_pdf_dir):
        # Atualiza a variável local com o novo caminho do diretório PDF
        self.pdf_dir = new_pdf_dir

    def on_sicaf_dir_updated(self, new_sicaf_dir):
        self.sicaf_dir = new_sicaf_dir

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.setup_buttons_layout()
        self.tableView = QTableView(self)
        initial_headers = []  # A lista de cabeçalhos iniciais vazia como exemplo
        self.model = DocumentTableModel(pd.DataFrame(), initial_headers)
        self.tableView.setModel(self.model)
        self.tableView.setStyleSheet("""
        QTableView {
            background-color: black;
            color: white;
            font-size: 12pt;
            border: 1px solid black;
        }
        QHeaderView::section {
            background-color: #333;
            padding: 4px;
            border: 0.5px solid #dcdcdc;
            color: white;
            font-size: 12pt;
        }
        """)
        QTimer.singleShot(1, self.adjust_columns)
        self.tableView.verticalHeader().setVisible(False)

        self.main_layout.addWidget(self.tableView)
        self.setup_buttons_down_layout()
        self.setLayout(self.main_layout)

    def adjust_columns(self):
        """Ajusta as larguras das colunas do QTableView."""
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Ajusta todas as colunas ao conteúdo
        headers = self.model.get_headers()

        # Identifica o índice para a coluna "Descrição Detalhada"
        descricao_detalhada_index = headers.index("Descrição Detalhada") if "Descrição Detalhada" in headers else -1
        descricao_index = headers.index("Descrição") if "Descrição" in headers else -1

        if descricao_detalhada_index != -1:
            header.setSectionResizeMode(descricao_detalhada_index, QHeaderView.ResizeMode.Fixed)  # Configura a coluna para um tamanho fixo
            self.tableView.setColumnWidth(descricao_detalhada_index, 150)  # Define a largura fixa
        if descricao_index != -1:
            header.setSectionResizeMode(descricao_index, QHeaderView.ResizeMode.Fixed)  # Configura a coluna para um tamanho fixo
            self.tableView.setColumnWidth(descricao_index, 150)  # Define a largura fixa

    def setup_buttons_layout(self):
        self.buttons_layout = QHBoxLayout()
        self.create_buttons()
        self.main_layout.addLayout(self.buttons_layout)

    def create_buttons(self):
        self.buttons_layout = QHBoxLayout()
        icon_size = QSize(40, 40)  # Tamanho do ícone para todos os botões
        self.button_specs = [
            ("Importar TR", self.image_cache['table'], self.import_tr, "Adiciona um novo item ao banco de dados", icon_size),
            ("Processar Homologação", self.image_cache['data-collection'], self.salvar_tabela, "Salva o dataframe em um arquivo excel('.xlsx')", icon_size),
            ("Processar SICAF", self.image_cache['data-collection2'], self.salvar_tabela, "Exclui um item selecionado", icon_size),
            ("Configurações", self.image_cache['management'], self.open_settings_dialog, "Abre as configurações da aplicação", icon_size),            
        ]

        for text, icon, callback, tooltip, icon_size in self.button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self, icon_size=icon_size)
            self.buttons_layout.addWidget(btn)

    def setup_buttons_down_layout(self):
        self.buttons_layout = QHBoxLayout()
        self.create_buttons_down()
        self.main_layout.addLayout(self.buttons_layout)

    def create_buttons_down(self):
        self.buttons_layout = QHBoxLayout()
        icon_size = QSize(40, 40)  # Tamanho do ícone para todos os botões
        self.button_specs = [
            ("Carregar DB", self.image_cache['table'], self.import_tr, "Adiciona um novo item ao banco de dados", icon_size),
            ("Gerar Ata/Contrato", self.image_cache['data-processing'], self.salvar_tabela, "Salva o dataframe em um arquivo excel('.xlsx')", icon_size),
            ("Indicador NORMCEIM", self.image_cache['performance'], self.salvar_tabela, "Exclui um item selecionado", icon_size),
            ("Itens", self.image_cache['management'], self.open_settings_dialog, "Abre as configurações da aplicação", icon_size),            
        ]

        for text, icon, callback, tooltip, icon_size in self.button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self, icon_size=icon_size)
            self.buttons_layout.addWidget(btn)

    def salvar_tabela(self):
        pass    

    def open_settings_dialog(self):
        pass

    def load_data(self):
        # Retorna um DataFrame vazio para inicialização
        return pd.DataFrame()
    
    def import_tr(self):
        self.selecionar_termo_de_referencia_e_carregar()
        if self.tr_df_carregado is not None:
            self.atualizar_modelo_com_dados()

    def selecionar_termo_de_referencia_e_carregar(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo", "", "Excel files (*.xlsx *.xls)")
        if arquivo:
            self.tr_df_carregado = pd.read_excel(arquivo)
            self.atualizar_modelo_com_dados()
            
    def button_clicked(self, index):
        if index == 0:  # Primeiro botão
            self.selecionar_termo_de_referencia_e_carregar()
        elif index == 1:  # Segundo botão
            convert_pdf_to_txt(self.pdf_dir, TXT_DIR, self.progress_bar_homolog)

    def selecionar_termo_de_referencia_e_carregar(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo", "", "Excel files (*.xlsx *.xls)")
        if arquivo:
            self.tr_df_carregado = pd.read_excel(arquivo)
            QMessageBox.information(self, "Arquivo Carregado", f"O arquivo '{os.path.basename(arquivo)}' foi carregado com sucesso!")

    def atualizar_modelo_com_dados(self):
        # Mapeia as colunas do DataFrame para as colunas esperadas no modelo
        mapeamento_colunas = {
            "Item": "item_num",
            "Catálogo": "catalogo",
            "Descrição": "descricao_tr",
            "Descrição Detalhada": "descricao_detalhada_tr",
            "UASG": "uasg",
            "Órgão Responsável": "orgao_responsavel",
            "Número": "num_pregao",
            "Ano": "ano_pregao",
            "SRP": "srp",
            "Objeto": "objeto",
            "Grupo": "grupo",
            "Valor Estimado": "valor_estimado",
            "Quantidade": "quantidade",
            "Unidade": "unidade",
            "Situação": "situacao",
            "Melhor Lance": "melhor_lance",
            "Valor Negociado": "valor_negociado",
            "Ordenador Despesa": "ordenador_despesa",
            "Empresa": "empresa",
            "CNPJ": "cnpj",
            "Marca Fabricante": "marca_fabricante",
            "Modelo Versão": "modelo_versao",
            "Valor Homologado do Item": "valor_homologado_item_unitario",
            "Valor Estimado Total do Item": "valor_estimado_total_do_item",
            "Valor Homologado Total do Item": "valor_homologado_total_item",
            "Percentual Desconto": "percentual_desconto"
        }
        # Preparar o DataFrame para ter todas as colunas mapeadas, com valores vazios para colunas faltantes
        for key, value in mapeamento_colunas.items():
            if value not in self.tr_df_carregado.columns:
                self.tr_df_carregado[value] = None  # Adiciona a coluna com valores vazios

        # As colunas para o modelo são baseadas nas chaves do mapeamento, garantindo a ordem
        headers = list(mapeamento_colunas.keys())
        colunas_modelo = list(mapeamento_colunas.values())

        # Cria um DataFrame apenas com as colunas mapeadas
        dados_filtrados = self.tr_df_carregado[colunas_modelo]
        self.model = DocumentTableModel(dados_filtrados, headers)
        self.tableView.setModel(self.model)
        self.adjust_columns()

    def save_file_path(self, file_path):
        settings = QSettings("SuaEmpresa", "SeuApp")
        settings.setValue("termo_referencia_arquivo", file_path)

    # Use QSettings para carregar o caminho do arquivo
    def load_file_path(self):
        settings = QSettings("SuaEmpresa", "SeuApp")
        return settings.value("termo_referencia_arquivo", "")

    def load_settings(self):
        settings = QSettings("SuaEmpresa", "SeuApp")
        self.nome_arquivo_carregado = settings.value("termo_referencia_arquivo", "")

    def reset_arquivo_carregado(self):
        self.nome_arquivo_carregado = ""
        self.tr_variavel_df_carregado = None
        # Aqui, você também pode salvar o estado resetado nas configurações, se necessário
        self.save_file_path("")

    def iniciar_processamento(self):
        # Verifica se o termo de referência foi carregado
        if self.tr_variavel_df_carregado is None:
            QMessageBox.warning(self, "Atenção", "Carregue o termo de referência antes de processar os termos de homologação!")
            return  # Interrompe a execução adicional deste método

        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        total_files = len(pdf_files)

        # Verifica se já existe um ProgressDialog aberto
        if self.progressDialog is None or not self.progressDialog.isVisible():
            # Se o arquivo foi carregado, cria o popup de progresso
            self.progressDialog = ProgressDialog(total_files, self.start_pdf_conversion, self.pdf_dir, self)
            self.progressDialog.show()
        else:
            # Opcional: Traga o diálogo existente para o primeiro plano
            self.progressDialog.raise_()
            self.progressDialog.activateWindow()

    def start_pdf_conversion(self):
        arquivo_salvo = self.load_file_path()
        if not arquivo_salvo or not os.path.exists(arquivo_salvo):
            QMessageBox.warning(self, "Erro", "Arquivo não encontrado. Por favor, carregue o termo de referência novamente.")
            return
        
        # Verifica se o termo de referência foi carregado
        if self.tr_variavel_df_carregado is None:
            QMessageBox.warning(self, "Atenção", "Carregue o termo de referência antes de processar os termos de homologação!")
            self.progressDialog.close()  # Fecha a janela de diálogo de progresso
            return  # Interrompe a execução adicional deste método

        # Se o arquivo foi carregado, inicia o processamento
        self.progressDialog.confirmButton.setDisabled(True)
        convert_pdf_to_txt(self.pdf_dir, TXT_DIR, self.progressDialog)
        self.save_to_dataframe()
        self.progressDialog.close()
        # Exibe uma mensagem de conclusão
        QMessageBox.information(self, "Conclusão", "O processamento dos dados foi concluído com sucesso!")

    def get_content_widget(self):
        return self

    def save_to_dataframe(self):
        # Inicializa um DataFrame vazio
        df = pd.DataFrame()
        df = self.create_dataframe_from_txt_files(str(TXT_DIR), padrao_1, padrao_grupo2, padrao_item2, padrao_3, padrao_4, df)
        
        # Verifica se o DataFrame carregado está disponível
        if self.tr_variavel_df_carregado is not None:
            tr_variavel_df = self.tr_variavel_df_carregado
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum DataFrame de termo de referência carregado.")
            return
        
        # Atualiza o DataFrame com as informações
        merged_df = pd.merge(df, tr_variavel_df, on='item_num', how='outer')

        # Imprime o DataFrame combinado no console
        print("DataFrame combinado:\n", merged_df)

        # Salva os DataFrames como arquivos
        EXCEL_OUTPUT_PATH = DATABASE_DIR / "relatorio.xlsx"
        merged_df.to_excel(EXCEL_OUTPUT_PATH, index=False, engine='openpyxl')
        merged_df.to_csv(CSV_OUTPUT_PATH, index=False, encoding='utf-8-sig')
        # Retorna o DataFrame combinado
        return merged_df

    def create_dataframe_from_txt_files(self, txt_directory: str, padrao_1: str, padrao_grupo2: str, padrao_item2: str, padrao_3: str, padrao_4: str, dataframe_licitacao: pd.DataFrame):
        txt_files = obter_arquivos_txt(txt_directory)
        all_data = []
        
        for txt_file in txt_files:
            content = ler_arquivos_txt(txt_file)
            uasg_pregao_data = extrair_uasg_e_pregao(content, padrao_1, padrao_srp, padrao_objeto)
            items_data = identificar_itens_e_grupos(content, padrao_grupo2, padrao_item2, padrao_3, padrao_4, dataframe_licitacao)
            
            for item in items_data:
                all_data.append({
                    **uasg_pregao_data,
                    **item
                })

        dataframe_licitacao = pd.DataFrame(all_data)
        
        # Verificação da coluna 'item_num'
        if "item_num" not in dataframe_licitacao.columns:
            raise ValueError("A coluna 'item_num' não foi encontrada no DataFrame.")
        
        dataframe_licitacao = dataframe_licitacao.sort_values(by="item_num")
        self.save_dataframe_as_excel(dataframe_licitacao, BASE_DIR / "excel.xlsx")
                                
        return dataframe_licitacao
    
    def save_dataframe_as_excel(self, df: pd.DataFrame, output_path: str):
        df.to_excel(output_path, index=False, engine='openpyxl')

    def processar_arquivos_txt(self):
        try:
            df = self.create_dataframe_from_txt_files(str(TXT_DIR), padrao_1, padrao_grupo2, padrao_item2, padrao_3, padrao_4, pd.DataFrame())
            QMessageBox.information(self, "Processamento Concluído", "DataFrame criado e salvo com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro durante o processamento: {str(e)}")
    
def obter_arquivos_txt(directory: str) -> list:
    """Retorna a lista de arquivos TXT em um diretório."""
    return [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.txt')]

def ler_arquivos_txt(file_path: str) -> str:
    """Lê o conteúdo de um arquivo TXT."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def save_to_excel(df, filepath):
    df.to_excel(filepath, index=False, engine='openpyxl')

def save_dataframe_as_excel(df: pd.DataFrame, output_path: str):
    df.to_excel(output_path, index=False, engine='openpyxl')

def convert_pdf_to_txt(pdf_dir, txt_dir, dialog):
    # Verifica se TXT_DIR existe. Se não, cria o diretório.
    if not txt_dir.exists():
        txt_dir.mkdir(parents=True, exist_ok=True)
    else:
        # Se TXT_DIR existir, deleta todos os arquivos dentro dele.
        for file in txt_dir.iterdir():
            if file.is_file():
                file.unlink()
    
    # Inicia o processo de conversão
    pdf_files = list(pdf_dir.glob("*.pdf"))
    total_files = len(pdf_files)
    
    for index, pdf_file in enumerate(pdf_files):
        with pdfplumber.open(pdf_file) as pdf:
            texts = [page.extract_text() for page in pdf.pages]
            all_text = ' '.join(texts).replace('\n', ' ').replace('\x0c', ' ')

            txt_file = txt_dir / f"{pdf_file.stem}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(all_text)
        
        dialog.update_progress(index + 1)

class ProgressDialog(QDialog):
    def __init__(self, total_files, confirm_callback, pdf_dir, parent=None):
        super().__init__(parent)
        self.parent = parent  # Mantém uma referência ao widget pai
        self.pdf_dir = pdf_dir  # Recebendo o diretório PDF
        self.setWindowTitle("Processando Arquivos PDF")
        self.setLayout(QVBoxLayout())
        global_event_manager.pdf_dir_updated.connect(self.on_pdf_dir_updated)

        # Define a fonte para todos os elementos
        fonte_padrao = QFont()
        fonte_padrao.setPointSize(14)

        # Adiciona o botão "Abrir Pasta"
        self.abrirPastaButtonHomolog = QPushButton("Abrir Pasta", self)
        self.abrirPastaButtonHomolog.setFont(fonte_padrao)
        self.abrirPastaButtonHomolog.clicked.connect(lambda: open_folder(self.pdf_dir))
        self.layout().addWidget(self.abrirPastaButtonHomolog)

        # Botão "Atualizar"
        self.atualizarButton = QPushButton("Atualizar", self)
        self.atualizarButton.setFont(fonte_padrao)
        self.atualizarButton.clicked.connect(self.atualizar_contagem_arquivos)
        self.layout().addWidget(self.atualizarButton)

        self.label = QLabel(f"{total_files} arquivos PDF encontrados. Deseja processá-los?")
        self.label.setFont(fonte_padrao)  # Aplica a fonte ao QLabel
        self.layout().addWidget(self.label)

        self.progressBar = QProgressBar(self)
        self.progressBar.setFont(fonte_padrao)  # Aplica a fonte ao QProgressBar
        self.progressBar.setMaximum(total_files)
        self.layout().addWidget(self.progressBar)

        self.confirmButton = QPushButton("Confirmar", self)
        self.confirmButton.setFont(fonte_padrao)  # Aplica a fonte ao QPushButton
        self.confirmButton.clicked.connect(confirm_callback)
        self.layout().addWidget(self.confirmButton)

        # Adiciona o botão de Acesso Rápido
        self.quickAccessButton = QPushButton("Acesso Rápido ao DataFrame", self)
        self.quickAccessButton.setFont(fonte_padrao)  # Aplica a fonte ao QPushButton
        self.quickAccessButton.clicked.connect(self.teste_rapido)
        self.layout().addWidget(self.quickAccessButton)

    def abrir_pasta_homolog(self):
        open_folder(self.pdf_dir)

    def on_pdf_dir_updated(self, new_pdf_dir):
        print(f"PDF_DIR atualizado para: {new_pdf_dir}")
        QMessageBox.information(self, "Atualização", f"PDF_DIR atualizado para: {new_pdf_dir}")
        self.pdf_dir = new_pdf_dir
        self.atualizar_contagem_arquivos()

    def atualizar_contagem_arquivos(self):
        # Atualiza a contagem de arquivos PDF
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        self.total_files = len(pdf_files)
        self.label.setText(f"{self.total_files} arquivos PDF encontrados. Deseja processá-los?")
        self.progressBar.setMaximum(self.total_files)

    def update_progress(self, value):
        self.progressBar.setValue(int(round(value)))

    def teste_rapido(self):
        if self.parent:  # Verifica se a referência ao widget pai está disponível
            self.parent.save_to_dataframe()
            # self.parent.exibir_dataframe_itens_homologados()
            self.close()  # Fecha o diálogo
            QMessageBox.information(self, "Conclusão", "O processamento dos dados foi concluído com sucesso!")

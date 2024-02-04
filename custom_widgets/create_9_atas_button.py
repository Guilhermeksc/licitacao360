#create_9_atas_button.py

from PyQt6.QtWidgets import QWidget, QLabel, QFileDialog, QSpacerItem, QMenu, QToolTip, QTreeView, QMessageBox, QVBoxLayout, QProgressBar, QPushButton, QHBoxLayout, QPushButton, QSizePolicy, QToolButton
from PyQt6.QtCore import Qt, QSize, QSettings, QModelIndex, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QStandardItemModel, QStandardItem, QFont, QCursor, QAction
from pathlib import Path
from gerar_atas_pasta.regex_termo_homolog import *
from gerar_atas_pasta.regex_sicaf import *
from gerar_atas_pasta.canvas_gerar_atas import *
from utils.treeview_utils import open_folder
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

class AtasWidget(QWidget):
    def __init__(self, icons_dir, parent=None):
        super().__init__(parent)
        self.pdf_dir = PDF_DIR  # Já existente para PDF_DIR
        self.sicaf_dir = SICAF_DIR  # Adicionando para SICAF_DIR

        global_event_manager.pdf_dir_updated.connect(self.on_pdf_dir_updated)
        global_event_manager.sicaf_dir_updated.connect(self.on_sicaf_dir_updated)

        self.icons_dir = Path(icons_dir)
        self.tr_variavel_df_carregado = None
        self.nome_arquivo_carregado = ""
        self.passo2Concluido = False  # Atributo para rastrear se o Passo 2 foi concluído
        self.botoes = []  # Inicializando a lista de botões
        self.setup_ui()
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

        self.atualizar_label_passo1()
        self.progressDialog = None
        self.sicafDialog = None
        self.atasDialog = None

    def on_pdf_dir_updated(self, new_pdf_dir):
        # Atualiza a variável local com o novo caminho do diretório PDF
        self.pdf_dir = new_pdf_dir

    def on_sicaf_dir_updated(self, new_sicaf_dir):
        self.sicaf_dir = new_sicaf_dir

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        header_layout = QVBoxLayout()

        # Criando um QHBoxLayout para o QLabel e o botão de reset
        label_reset_layout = QHBoxLayout()

        # Criando o QLabel para mostrar o arquivo carregado
        self.label_passo1 = QLabel("Arquivo Carregado:", self)
        fonte_label = QFont("Arial", 14, QFont.Weight.Normal)
        self.label_passo1.setFont(fonte_label)
        self.label_passo1.setStyleSheet(get_transparent_title_style())
        self.label_passo1.setAlignment(Qt.AlignmentFlag.AlignTop)
        label_reset_layout.addWidget(self.label_passo1)

        # Criando o botão de reset
        self.resetButton = QPushButton("Reset", self)
        self.resetButton.clicked.connect(self.reset_arquivo_carregado)
        self.resetButton.setFont(QFont("Arial", 14, QFont.Weight.Normal))
        self.resetButton.setFixedSize(self.resetButton.sizeHint())
        self.resetButton.hide()
        label_reset_layout.addWidget(self.resetButton)

        # Adiciona o QHBoxLayout ao QVBoxLayout do cabeçalho
        header_layout.addLayout(label_reset_layout)

        # Adiciona um espaçador para manter o cabeçalho no topo
        header_layout.addStretch(1)  # Experimente com diferentes valores, como 0 ou 1
        # Adiciona o QVBoxLayout do cabeçalho ao layout principal
        main_layout.addLayout(header_layout)
        
        button_size = QSize(330, 140)

        # Lista de funções correspondentes a cada botão
        button_functions = [
            self.selecionar_termo_de_referencia_e_carregar,
            self.iniciar_processamento,
            self.verificar_e_abrir_dialog_sicaf,
            self.verificar_e_abrir_dialog_atas,  # Nova função para o Passo 4
        ]

        # Textos para os botões
        textos_botao = [
            "Passo 1: Importar\nTermo de Referência",
            "Passo 2: Processar\nTermo de Homologação",
            "Passo 3:\nProcessar SICAF",
            "Passo 4:\nGerar Atas / Contratos",
        ]

        icon_paths = [
            "import_tr.png", "production.png", "production_red.png", "gerar_ata.png"
        ]

        for i, nome_botao in enumerate(textos_botao):
            button = self.createButton(nome_botao, icon_paths[i], button_functions[i], button_size)
            self.botoes.append(button)

            h_layout = QHBoxLayout()
            h_layout.addStretch()
            h_layout.addWidget(button)
            h_layout.addStretch()

            main_layout.addLayout(h_layout)

        self.atualizar_estado_botoes()
        main_layout.addStretch(1)  # Experimente com diferentes valores

        # Carrega as configurações após a criação dos widgets
        self.load_settings()

    def createButton(self, text, icon_filename, callback, size):
        button = QToolButton(self)
        button.setText(text)
        icon = QIcon(os.path.join(str(self.icons_dir), icon_filename))
        button.setIcon(icon)
        button.setIconSize(QSize(64, 64))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        button.clicked.connect(callback)
        button.setFont(QFont("Arial", 14, QFont.Weight.Normal))
        button.setFixedSize(size)

        # Estilo personalizado para o botão desabilitado
        button.setStyleSheet("""
        QToolButton {
            font-size: 16px;
            padding: 10px;
            background-color: rgba(0, 0, 0, 0.2);
            font-weight: bold;
            color: white;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-decoration: none;
        }
        QToolButton:hover {
            color: rgb(0, 255, 255);
            background-color: rgba(0, 0, 0, 0.8);
            border: 1px solid rgba(0, 255, 255, 0.8);
            text-decoration: underline;
        }
        QToolButton:disabled {
            background-color: rgba(0, 0, 0, 0.8);
            color: gray;
        }
        """)

        return button
    
    def verificar_e_abrir_dialog_sicaf(self):
        if not self.passo2Concluido:
            QMessageBox.information(self, "Ação Necessária", "Por favor, conclua o 'Passo 2: Processar Termo de Homologação' antes de prosseguir.")
        else:
            self.abrir_dialog_sicaf()

    def verificar_e_abrir_dialog_atas(self):
        if not self.passo2Concluido:
            QMessageBox.information(self, "Ação Necessária", "Por favor, conclua o 'Passo 2: Processar Termo de Homologação' antes de prosseguir com a geração de atas ou contratos.")
        else:
            self.abrir_dialog_atas()

    def abrir_dialog_atas(self):
        if self.atasDialog is None or not self.atasDialog.isVisible():
            self.atasDialog = AtasDialog(self)
            self.atasDialog.show()
        else:
            self.atasDialog.raise_()
            self.atasDialog.activateWindow()

    def button_clicked(self, index):
        if index == 0:  # Primeiro botão
            self.selecionar_termo_de_referencia_e_carregar()
        elif index == 1:  # Segundo botão
            convert_pdf_to_txt(self.pdf_dir, TXT_DIR, self.progress_bar_homolog)
        # ... (outros casos para outros botões)

    def selecionar_termo_de_referencia_e_carregar(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo", "", "Spreadsheet files (*.xlsx *.xls *.ods);;Excel files (*.xlsx *.xls);;LibreOffice files (*.ods)")
        if arquivo:
            self.tr_variavel_df_carregado = pd.read_excel(arquivo)
            nome_do_arquivo = os.path.basename(arquivo)
            self.nome_arquivo_carregado = nome_do_arquivo
            self.atualizar_label_passo1()
            self.save_file_path(arquivo)  # Salva o caminho do arquivo
            QMessageBox.information(self, "Arquivo Carregado", f"O arquivo '{nome_do_arquivo}' foi carregado com sucesso!")

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
        self.atualizar_label_passo1()  # Atualiza o QLabel do Passo 1

    def reset_arquivo_carregado(self):
        self.nome_arquivo_carregado = ""
        self.tr_variavel_df_carregado = None
        self.atualizar_label_passo1()
        # Aqui, você também pode salvar o estado resetado nas configurações, se necessário
        self.save_file_path("")

    def atualizar_label_passo1(self):
        texto_base = "Arquivo Carregado:"
        if self.nome_arquivo_carregado:
            self.label_passo1.setText(f"{texto_base} {self.nome_arquivo_carregado}")
            self.resetButton.show()  # Mostra o botão de reset
        else:
            self.label_passo1.setText(f"{texto_base} Nenhum Arquivo Selecionado!")
            self.resetButton.hide()  # Oculta o botão de reset

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

    def atualizar_estado_botoes(self):
        # Habilita ou desabilita o botão do Passo 3 com base no estado do Passo 2
        self.botoes[2].setEnabled(self.passo2Concluido)
        self.botoes[3].setEnabled(self.passo2Concluido)  # Botão do Passo 4

    def on_processamento_p2_concluido(self):
        # Chamado quando o processamento do Passo 2 for concluído
        self.passo2Concluido = True
        self.atualizar_estado_botoes()  # Atualiza o estado dos botões

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
        # self.exibir_dataframe_itens_homologados()
        self.progressDialog.close()
        self.on_processamento_p2_concluido()  # Chama a função após a conclusão do Passo 2
        # Exibe uma mensagem de conclusão
        QMessageBox.information(self, "Conclusão", "O processamento dos dados foi concluído com sucesso!")

    def get_title(self):
        return "Gerar Atas"

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

        # Salva os DataFrames como arquivos
        EXCEL_OUTPUT_PATH = DATABASE_DIR / "relatorio.xlsx"
        merged_df.to_excel(EXCEL_OUTPUT_PATH, index=False, engine='openpyxl')
        merged_df.to_csv(CSV_OUTPUT_PATH, index=False, encoding='utf-8-sig')
        salvar_txt_cnpj_empresa(merged_df, TXT_OUTPUT_PATH)
    
        # Gera relatórios adicionais
        DESERTO_FRACASSADO = gerar_relatorio_deserto_fracassado(merged_df)
        NAN_SITUACAO = gerar_relatorio_nan_situacao(merged_df)
        self.passo2Concluido = True  # Define como True após a conclusão

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
        dataframe_licitacao = dataframe_licitacao.sort_values(by="item_num")
        self.save_dataframe_as_excel(dataframe_licitacao, BASE_DIR / "excel.xlsx")
                                
        return dataframe_licitacao
    
    def save_dataframe_as_excel(self, df: pd.DataFrame, output_path: str):
        df.to_excel(output_path, index=False, engine='openpyxl')

    def exibir_dataframe_itens_homologados(self):
        df = pd.read_csv(CSV_OUTPUT_PATH)  # Substitua pelo caminho correto do arquivo
        popup = DataFramePopup(df, self)
        popup.exec_()  # Mostrar a janela de popup

    def processar_arquivos_txt(self):
        try:
            df = self.create_dataframe_from_txt_files(str(TXT_DIR), padrao_1, padrao_grupo2, padrao_item2, padrao_3, padrao_4, pd.DataFrame())
            QMessageBox.information(self, "Processamento Concluído", "DataFrame criado e salvo com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro durante o processamento: {str(e)}")
    
    def abrir_dialog_sicaf(self):
        if self.sicafDialog is None or not self.sicafDialog.isVisible():
            self.sicafDialog = SicafDialog(self.sicaf_dir, self)
            self.sicafDialog.show()
        else:
            self.sicafDialog.raise_()
            self.sicafDialog.activateWindow()

def salvar_txt_cnpj_empresa(df, output_path):
    # Drop duplicates by CNPJ column
    df_unique = df.drop_duplicates(subset='cnpj', keep='first')
    
    # Exclude rows where 'cnpj' or 'empresa' are 'N/A'
    df_filtered = df_unique[(df_unique['cnpj'] != 'N/A') & (df_unique['empresa'] != 'N/A')]
    
    # Sort the dataframe by CNPJ
    sicaf_df = df_filtered.sort_values(by='cnpj')
    
    # Save the CNPJ and Empresa data to a TXT file
    with open(output_path, 'w', encoding='utf-8') as f:
        for _, value in sicaf_df.iterrows():
            line = f"{value['cnpj']} - {value['empresa']}\n"
            f.write(line)

        # Writing the message about SICAF in the last line
        f.write(f'Salve o SICAF no diretório:\n{SICAF_DIR}.')

    return sicaf_df

def gerar_relatorio_deserto_fracassado(df):
    report = df[(df['situacao'] == "Deserto e Homologado") | (df['situacao'] == "Fracassado e Homologado")]
    DESERTO_FRACASSADO = DATABASE_DIR / "report_deserto_fracassado.xlsx"
    save_to_excel(report, DESERTO_FRACASSADO)
    return DESERTO_FRACASSADO

def gerar_relatorio_nan_situacao(df):
    report = df[df['situacao'].isna()]
    NAN_SITUACAO = DATABASE_DIR / "report_nan_situacao.xlsx"
    save_to_excel(report, NAN_SITUACAO)
    return NAN_SITUACAO

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

from PyQt6.QtWidgets import QDialog, QProgressBar, QLineEdit, QTreeWidget, QTreeWidgetItem, QHeaderView

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
            self.parent.on_processamento_p2_concluido()  # Chama a função após a conclusão do Passo 2
            QMessageBox.information(self, "Conclusão", "O processamento dos dados foi concluído com sucesso!")

class DataFramePopup(QDialog):
    def __init__(self, dataframe, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Itens Homologados")

        # Define o tamanho inicial do QDialog
        self.resize(1100, 600)  # Definindo a largura para 900 e a altura para um valor desejado (exemplo: 400)

        # Define o layout principal para o QDialog
        layout = QVBoxLayout(self)
        
        # Cria um QTreeView e adiciona ao layout
        self.treeView = QTreeView(self)
        layout.addWidget(self.treeView)

        # Define o tamanho da fonte para o QTreeView
        font = QFont()
        font.setPointSize(12)
        self.treeView.setFont(font)

        # Cria e define o modelo para o QTreeView
        self.model = self.create_grouped_model(dataframe)
        self.treeView.setModel(self.model)

        # Ajustar a largura das colunas
        for i in range(self.model.columnCount()):
            self.treeView.setColumnWidth(i, 350)

    def create_grouped_model(self, dataframe):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Item Num", "Descrição TR", "Situação"])

        # Create parent items for each category
        categories = {
            "Adjudicado e Homologado": QStandardItem("Adjudicado e Homologado"),
            "Deserto e Homologado": QStandardItem("Deserto e Homologado"),
            "Fracassado e Homologado": QStandardItem("Fracassado e Homologado"),
            "NaN": QStandardItem("Não Definido")
        }

        for category in categories.values():
            model.appendRow(category)

        # Add items to the corresponding parent item
        for _, row in dataframe.iterrows():
            item_num = QStandardItem(str(row['item_num']))  # Convert to string
            descricao_tr = QStandardItem(str(row['descricao_tr']))  # Convert to string if it's a float
            situacao = row['situacao']
            situacao_str = str(situacao) if not pd.isna(situacao) else "NaN"

            # Create a child item
            child = [item_num, descricao_tr, QStandardItem(situacao_str)]

            # Add the child item to the corresponding parent item
            categories[situacao_str].appendRow(child)

        return model

class AtasDialog(QDialog):
    NUMERO_ATA_GLOBAL = None  # Defina isso em algum lugar adequado dentro de sua classe

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Geração de Atas / Contratos")
        self.setFont(QFont('Arial', 14))
        layout = QVBoxLayout(self)

        # Primeiro crie a QLabel para o último contrato
        self.ultimo_contrato_label = QLabel("O último contrato gerado foi:")
        self.ultimo_contrato_label.setFont(QFont('Arial', 14))
        layout.addWidget(self.ultimo_contrato_label)

        self.label = QLabel("\nDigite o próximo Número de Controle de Atas/Contratos:\n")
        self.label.setFont(QFont('Arial', 14))
        layout.addWidget(self.label)

        # Cria um QHBoxLayout para a entrada e o botão
        entry_button_layout = QHBoxLayout()

        # Espaçador à esquerda
        left_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        entry_button_layout.addItem(left_spacer)

        # Agora crie o QLineEdit para a entrada de texto
        self.ataEntry = QLineEdit(self)
        self.ataEntry.setPlaceholderText("Digite um número até 4 dígitos")
        self.ataEntry.setMaxLength(4)

        self.ataEntry.setFixedWidth(self.ataEntry.fontMetrics().horizontalAdvance('0') * 6)

        entry_button_layout.addWidget(self.ataEntry)

        # Cria o botão Confirmar
        self.confirmButton = QPushButton("Confirmar", self)
        self.confirmButton.clicked.connect(self.confirmar_numero_ata)
        entry_button_layout.addWidget(self.confirmButton)

        # Espaçador à direita
        right_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        entry_button_layout.addItem(right_spacer)
      
        # Adiciona o QHBoxLayout da entrada e botão ao layout principal
        layout.addLayout(entry_button_layout)

        # Cria um QHBoxLayout para os botões Gerar Atas/Contratos e Gerar Documento
        buttons_layout = QHBoxLayout()

        self.label_espaco = QLabel("\n")
        layout.addWidget(self.label_espaco)

        # Botão para gerar atas ou contratos
        self.gerarButton = self.criar_botao_especial("Gerar\nAtas", str(ICONS_DIR / 'gerar_atas.png'))
        self.gerarButton.clicked.connect(self.gerar_atas_contratos)
        buttons_layout.addWidget(self.gerarButton)

        # Botão para gerar documento
        self.gerarDocumentoButton = self.criar_botao_especial("Gerar\nContratos", str(ICONS_DIR / 'gerar_contrato.png'))
        self.gerarDocumentoButton.clicked.connect(self.gerar_documento)
        buttons_layout.addWidget(self.gerarDocumentoButton)
        
        # Depois de criar self.ataEntry, agora você pode verificar e definir seu valor inicial
        ultimo_num_contrato = self.carregar_ultimo_contrato()
        if ultimo_num_contrato is not None:
            self.atualizar_ultimo_contrato_label(f"Nº {ultimo_num_contrato}")
            self.ataEntry.setText(str(ultimo_num_contrato + 1))
        else:
            self.ultimo_contrato_label.setText("O último número de ata/contrato gerado foi: Nenhum")
        
        # Adiciona o QHBoxLayout dos botões ao layout principal
        layout.addLayout(buttons_layout)
        
    def atualizar_ultimo_contrato_label(self, ultimo_num_contrato):
        self.ultimo_contrato_label.setText(f"O último número de ata/contrato gerado foi: {ultimo_num_contrato}")

    def salvar_ultimo_contrato(self, ultimo_num_contrato):
        with open(ULTIMO_CONTRATO_DIR, "w") as f:
            f.write(str(ultimo_num_contrato))  # Convertendo para string

    def carregar_ultimo_contrato(self):
        try:
            with open(ULTIMO_CONTRATO_DIR, "r") as f:
                return int(f.read().split('/')[-1])
        except (FileNotFoundError, ValueError):
            return None

    def confirmar_numero_ata(self):
        numero_ata = self.ataEntry.text()
        if numero_ata.isdigit() and len(numero_ata) <= 4:
            AtasDialog.NUMERO_ATA_GLOBAL = int(numero_ata)  # Atualiza o valor global
            QMessageBox.information(self, "Número Confirmado", f"Número da ata definido para: {numero_ata}")
        else:
            QMessageBox.warning(self, "Número Inválido", "Por favor, digite um número válido de até 4 dígitos.")
    
    def criar_botao_especial(self, text, icon_path):
        button = QToolButton(self)
        button.setText(text)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(64, 64))  # Defina o tamanho do ícone conforme necessário
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        button.setFixedSize(200, 160) 
        return button

    def gerar_atas_contratos(self):
        # Aqui chamamos a função iniciar_processo
        try:
            self.iniciar_processo()
        except ValueError as e:
            QMessageBox.critical(self, "Erro", str(e))

    def iniciar_processo(self):
        if AtasDialog.NUMERO_ATA_GLOBAL is None:
            raise ValueError("O número da ATA não foi definido!")

        # Chama as outras funções que dependem de NUMERO_ATA_GLOBAL
        criar_pastas_com_subpastas()
        ultimo_num_ata = processar_documentos(AtasDialog.NUMERO_ATA_GLOBAL)

        # Atualizar e salvar o último número da ATA
        self.salvar_ultimo_contrato(ultimo_num_ata)
        self.atualizar_ultimo_contrato_label(ultimo_num_ata)

    def gerar_documento(self):
        # Aqui chamamos a função iniciar_processo
        try:
            self.iniciar_contrato()
        except ValueError as e:
            QMessageBox.critical(self, "Erro", str(e))
        pass

    def iniciar_contrato(self):
        if AtasDialog.NUMERO_ATA_GLOBAL is None:
            raise ValueError("O número do Contrato não foi definido!")

        # Chama as outras funções que dependem de NUMERO_ATA_GLOBAL
        criar_pastas_com_subpastas()
        ultimo_num_contrato = processar_contrato(AtasDialog.NUMERO_ATA_GLOBAL)

        # Atualizar e salvar o último número do contrato
        self.salvar_ultimo_contrato(ultimo_num_contrato)
        self.atualizar_ultimo_contrato_label(ultimo_num_contrato)


from PyQt6.QtWidgets import QApplication, QTreeView, QMessageBox, QDialog
from PyQt6.QtCore import QAbstractTableModel, Qt
import pandas as pd
import sys

class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame()):
        super(PandasModel, self).__init__()
        self._df = df

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):  # Use Qt.ItemDataRole.DisplayRole
        if role == Qt.ItemDataRole.DisplayRole:  # Use Qt.ItemDataRole.DisplayRole
            return str(self._df.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:  # Use Qt.Orientation.Horizontal and Qt.ItemDataRole.DisplayRole
            return self._df.columns[col]
        return None
    
from PyQt6.QtWidgets import QDialog, QTreeView, QVBoxLayout
from PyQt6.QtGui import QFont
import traceback

class SicafDialog(QDialog):
    def __init__(self, sicaf_dir, parent=None):
        super().__init__(parent)
        self.sicaf_dir = sicaf_dir  # Recebe sicaf_dir como parâmetro
        global_event_manager.sicaf_dir_updated.connect(self.on_sicaf_dir_updated)

        self.setWindowTitle("Processamento SICAF")
        self.setLayout(QVBoxLayout())

        fonte_padrao = QFont()
        fonte_padrao.setPointSize(14)

        # Layout Horizontal para botões "Relatório SICAF" e Informação
        button_layout = QHBoxLayout()
        
        # Botão "Relatório SICAF"
        self.relatorioSicafButton = QPushButton("Relatório SICAF", self)
        self.relatorioSicafButton.setFont(fonte_padrao)
        self.relatorioSicafButton.clicked.connect(self.abrir_bloco_notas)
        button_layout.addWidget(self.relatorioSicafButton)

        # Botão de Informação
        info_icon_path = str(ICONS_DIR / 'info.png')
        tooltip_image_path = str(IMAGE_PATH / 'sicaf_info.png')

        # Redimensionar o ícone
        icon_size = QSize(32, 32)  # Substitua 32, 32 pelo tamanho desejado
        pixmap = QPixmap(info_icon_path).scaled(icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        info_icon = QIcon(pixmap)

        self.infoButton = QPushButton("", self)  # Removido o ícone do construtor
        self.infoButton.setIcon(info_icon)  # Define o ícone no botão
        self.infoButton.setIconSize(icon_size)  # Define o tamanho do ícone no botão

        # Configurar o tamanho do botão para combinar com o tamanho do ícone
        button_size = QSize(icon_size.width() + 10, icon_size.height() + 10)  # Adiciona uma margem ao tamanho do botão
        self.infoButton.setFixedSize(button_size)

        self.infoButton.setToolTip(f'<img src="{tooltip_image_path}" />')
        self.infoButton.clicked.connect(lambda: QToolTip.showText(self.infoButton.mapToGlobal(QPoint(0, 0)), self.infoButton.toolTip()))
        button_layout.addWidget(self.infoButton)

        self.layout().addLayout(button_layout)

        # Botão "Abrir Pasta"
        self.abrirPastaButton = QPushButton("Abrir Pasta", self)
        self.abrirPastaButton.setFont(fonte_padrao)
        self.abrirPastaButton.clicked.connect(lambda: open_folder(self.sicaf_dir))

        self.layout().addWidget(self.abrirPastaButton)

        # Label de informação
        self.label = QLabel("Deseja processar os dados do SICAF?")
        self.label.setFont(fonte_padrao)
        self.layout().addWidget(self.label)

        # Adiciona a barra de progresso
        self.progressBar = QProgressBar(self)
        self.progressBar.setFont(fonte_padrao)
        self.layout().addWidget(self.progressBar)

        # Botão de confirmação
        self.confirmButton = QPushButton("Confirmar", self)
        self.confirmButton.setFont(fonte_padrao)
        self.confirmButton.clicked.connect(self.iniciar_processamento_sicaf)
        self.layout().addWidget(self.confirmButton)

    def on_sicaf_dir_updated(self, new_sicaf_dir):
        self.sicaf_dir = new_sicaf_dir

    def abrir_bloco_notas(self):
        TXT_OUTPUT_PATH = DATABASE_DIR / "relacao_cnpj.txt"
        os.startfile(TXT_OUTPUT_PATH)

    def iniciar_processamento_sicaf(self):
        total_arquivos = len(list(self.sicaf_dir.glob("*.pdf")))
        self.progressBar.setMaximum(total_arquivos)

        try:
            df_final_ordered = processar_arquivos_sicaf(self, self.progressBar, self.update_progress)
            self.progressBar.setValue(self.progressBar.maximum())
            QMessageBox.information(self, "Processamento Concluído", "Os arquivos SICAF foram processados com sucesso.")
            self.exibir_resultado_sicaf(df_final_ordered)  # Chama a função para exibir o popup
        except Exception as e:
            traceback.print_exc()  # Imprime detalhes do erro no terminal
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro durante o processamento: {e}")

    def exibir_resultado_sicaf(self, df_final_ordered):
        # Chama o popup passando o DataFrame final
        popup = SicafTreeViewPopup(df_final_ordered, self)
        popup.exec()  # Exibe o popup

    def update_progress(self, value):
        # Converte o valor float para int antes de passar para setValue
        self.progressBar.setValue(int(round(value)))

class SicafTreeViewPopup(QDialog):
    def __init__(self, df_final_ordered, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualização dos Dados")
        self.df_filtered = df_final_ordered[df_final_ordered['item_num'] != -1]
        self.resize(1100, 600)

        # Cria um layout horizontal para os botões
        buttons_layout = QHBoxLayout()

        layout = QVBoxLayout(self)

        # Cria um layout horizontal para os botões
        buttons_layout = QHBoxLayout()

        # Adiciona botões para expandir e colapsar os itens
        btn_expand_all = QPushButton("Expandir", self)
        btn_collapse_all = QPushButton("Reduzir", self)
        btn_expand_all.clicked.connect(self.expand_all_items)
        btn_collapse_all.clicked.connect(self.collapse_all_items)

        # Adiciona os botões ao layout de botões
        buttons_layout.addWidget(btn_expand_all)
        buttons_layout.addWidget(btn_collapse_all)

        # Adiciona o layout de botões ao layout principal ANTES do QTreeView
        layout.addLayout(buttons_layout)

        # Cria e configura o QTreeView
        self.treeView = CustomTreeView(self)
        self.treeView.setFont(QFont("Arial", 12))
        self.model = self.create_model(df_final_ordered)
        self.treeView.setModel(self.model)
        layout.addWidget(self.treeView)

        for i in range(self.model.rowCount()):
            self.treeView.setFirstColumnSpanned(i, QModelIndex(), True)

        # Expandir todos os itens inicialmente
        self.treeView.expandAll()

    def expand_all_items(self):
        self.treeView.expandAll()

    def collapse_all_items(self):
        self.treeView.collapseAll()

    def create_model(self, dataframe):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['Dados'])

        # Carrega os ícones
        check_icon = QIcon(str(ICONS_DIR / 'checked.png'))
        alert_icon = QIcon(str(ICONS_DIR / 'unchecked.png'))

        empresa_items = {}  # Dicionário para itens da empresa

        for _, row in dataframe.iterrows():
            empresa_name = str(row['empresa']) if pd.notna(row['empresa']) else ""
            cnpj = str(row['cnpj']) if pd.notna(row['cnpj']) else ""
            situacao = str(row['situacao']) if pd.notna(row['situacao']) else "Não definido"

            is_situacao_only = not empresa_name and not cnpj
            chave_item_pai = f"{situacao}" if is_situacao_only else f"{cnpj} - {empresa_name}".strip(" -")

            infos_present = all(pd.notna(row[key]) for key in ['endereco', 'cep', 'municipio', 'telefone', 'email', 'responsavel_legal'])

            # Cria o item pai (nível 1) se ele ainda não existir
            if chave_item_pai not in empresa_items:
                item_pai = QStandardItem(chave_item_pai)
                if is_situacao_only:
                    item_pai.setIcon(alert_icon)
                else:
                    item_pai.setIcon(check_icon if infos_present else alert_icon)
                model.appendRow(item_pai)
                empresa_items[chave_item_pai] = {'item': item_pai, 'count': 0}

                if not is_situacao_only:
                    # Adiciona informações detalhadas da empresa como itens separados (nível 2)
                    infos = [
                        f"Endereço: {row['endereco']}",
                        f"CEP: {row['cep']}",
                        f"Município: {row['municipio']}",
                        f"Telefone: {row['telefone']}",
                        f"Email: {row['email']}",
                        f"Responsável Legal: {row['responsavel_legal']}"
                    ]
                    for info in infos:
                        info_item = QStandardItem(info)
                        item_pai.appendRow(info_item)

                    # Adiciona o item de itens como subitem do item pai
                    itens_item = QStandardItem("Item(ns)")
                    item_pai.appendRow(itens_item)
                    empresa_items[chave_item_pai]['itens_item'] = itens_item

            # Formata o item_info de acordo com a situação ou empresa específica
            if is_situacao_only:
                item_info = f"Item {row['item_num']} | {row['descricao_tr']}"
            else:
                valor_homologado_formatado = formatar_brl(row['valor_homologado_item_unitario'])
                item_info = f"Item {row['item_num']} | {row['descricao_tr']} | Valor unitário R$ {valor_homologado_formatado} | {situacao}"

            # Adiciona o item_info ao item pai ou ao subitem "Item(ns)"
            if is_situacao_only:
                empresa_items[chave_item_pai]['item'].appendRow([QStandardItem(item_info)])
            else:
                empresa_items[chave_item_pai]['itens_item'].appendRow([QStandardItem(item_info)])
            empresa_items[chave_item_pai]['count'] += 1

        # Atualiza o texto do item de itens para "Item" ou "Itens"
        for empresa in empresa_items.values():
            if 'itens_item' in empresa:  # Verifica se o subitem "Item(ns)" existe
                item_text = "Item" if empresa['count'] == 1 else "Itens"
                empresa['itens_item'].setText(item_text)

        return model

    def exibir_resultado_sicaf(self, df_final_ordered):
        if not df_final_ordered.empty:
            # Cria o popup e exibe
            self.popup = SicafTreeViewPopup(df_final_ordered, self)
            self.popup.exec_()  # Exibe o popup de forma modal
            
            # Agora expande todos os itens após a execução do popup para ver claramente o spanning
            self.popup.treeView.expandAll()

            # Faz com que os itens pais atravessem todas as colunas
            for i in range(self.popup.model.rowCount()):
                self.popup.treeView.setFirstColumnSpanned(i, self.popup.treeView.rootIndex(), True)

class CustomTreeView(QTreeView):
    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return

        item = self.model().itemFromIndex(index)
        if item and " - " in item.text():  # Supondo que o formato seja 'CNPJ - Nome'
            menu = QMenu(self)
            copyAction = QAction("Copiar CNPJ", self)
            copyAction.triggered.connect(lambda: self.copy_cnpj(item.text()))
            menu.addAction(copyAction)
            menu.exec(event.globalPos())

    def copy_cnpj(self, text):
        cnpj = text.split(' - ')[0]  # Extrai o CNPJ
        QApplication.clipboard().setText(cnpj)
        QToolTip.showText(QCursor.pos(), f"Copiado", self)


from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
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

class GerarAtasWidget(QWidget):
    def __init__(self, icons_dir, parent=None):
        super().__init__(parent)
        self.pdf_dir = PDF_DIR  # Já existente para PDF_DIR
        self.sicaf_dir = SICAF_DIR  # Adicionando para SICAF_DIR

        global_event_manager.pdf_dir_updated.connect(self.on_pdf_dir_updated)
        global_event_manager.sicaf_dir_updated.connect(self.on_sicaf_dir_updated)

        self.icons_dir = Path(icons_dir)
        self.tr_variavel_df_carregado = None
        self.nome_arquivo_carregado = ""
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
        ]

        # Textos para os botões
        textos_botao = [
            "Passo 1: Importar\nTermo de Referência",
            "Passo 2: Processar\nTermo de Homologação",
        ]

        icon_paths = [
            "import_tr.png", "production.png"
        ]

        for i, nome_botao in enumerate(textos_botao):
            button = self.createButton(nome_botao, icon_paths[i], button_functions[i], button_size)
            self.botoes.append(button)

            h_layout = QHBoxLayout()
            h_layout.addStretch()
            h_layout.addWidget(button)
            h_layout.addStretch()

            main_layout.addLayout(h_layout)

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

        # Imprime o DataFrame combinado no console
        print("DataFrame combinado:\n", merged_df)

        # Salva os DataFrames como arquivos
        EXCEL_OUTPUT_PATH = DATABASE_DIR / "relatorio.xlsx"
        merged_df.to_excel(EXCEL_OUTPUT_PATH, index=False, engine='openpyxl')
        merged_df.to_csv(CSV_OUTPUT_PATH, index=False, encoding='utf-8-sig')
        salvar_txt_cnpj_empresa(merged_df, TXT_OUTPUT_PATH)

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

from PyQt6.QtWidgets import *
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtCore import *
import pandas as pd
import sys
import os
import subprocess
from pathlib import Path
from diretorios import *
import pdfplumber

class PDFProcessingThread(QThread):
    progress_updated = pyqtSignal(int, int, str)
    processing_complete = pyqtSignal(list)

    def __init__(self, pdf_dir, txt_dir, parent=None):
        super().__init__(parent)
        self.pdf_dir = pdf_dir
        self.txt_dir = txt_dir

    def run(self):
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        total_files = len(pdf_files)
        all_data = []

        for index, pdf_file in enumerate(pdf_files):
            data = self.process_single_pdf(pdf_file)
            all_data.extend(data)
            self.progress_updated.emit(index + 1, total_files, pdf_file.name)

        self.processing_complete.emit(all_data)

    def process_single_pdf(self, pdf_file):
        text_content = self.extract_text_from_pdf(pdf_file)
        self.save_text_to_file(pdf_file, text_content)
        return [{'item_num': pdf_file.stem, 'text': text_content}]

    def extract_text_from_pdf(self, pdf_file):
        with pdfplumber.open(pdf_file) as pdf:
            texts = [page.extract_text() for page in pdf.pages if page.extract_text() is not None]
            all_text = ' '.join(texts).replace('\n', ' ').replace('\x0c', ' ')
        return all_text

    def save_text_to_file(self, pdf_file, text_content):
        txt_file = self.txt_dir / f"{pdf_file.stem}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(text_content)



class ProgressDialog(QDialog):
    def __init__(self, total_files, pdf_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processando PDFs")
        self.total_files = total_files
        self.pdf_dir = pdf_dir

        # Configura a barra de progresso
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(total_files)
        self.progress_bar.setValue(0)

        # Configura o layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Processando arquivos na pasta: {pdf_dir}"))
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        self.resize(400, 100)

    def update_progress(self, current, total, filename):
        self.progress_bar.setValue(current)
        self.setWindowTitle(f"Processando {current}/{total}: {filename}")


class GerarAtas:
    def __init__(self, parent=None, icons_dir=None):
        self.dialog = QDialog(parent)
        self.dialog.setWindowTitle("Gerar Atas")
        self.icons_dir = icons_dir
        self.parent = parent
        self.pdf_dir = Path(PDF_DIR)
        self.txt_dir = Path(TXT_DIR) 
        self.tr_variavel_df_carregado = None
        self.model = QStandardItemModel()
        self.setup_ui()
        self.dialog.show()

    def setup_ui(self):
        self.dialog.setLayout(self.create_main_layout())
        self.dialog.resize(1200, 600)

    def create_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.create_fixed_width_frame(200, self.create_button_layout(self.get_buttons())))
        main_layout.addWidget(self.create_central_frame(), 1)
        return main_layout

    def create_fixed_width_frame(self, width, layout):
        frame = QFrame()
        frame.setFixedWidth(width)
        frame.setLayout(layout)
        return frame

    def create_central_frame(self):
        self.central_stack = QStackedWidget()
        central_layout = QVBoxLayout()
        
        # Configura o layout do título
        title_layout = self.create_title_layout()
        central_layout.addLayout(title_layout)
        
        # Adiciona o QStackedWidget ao layout central
        central_layout.addWidget(self.central_stack)
        # Adiciona as visualizações específicas ao QStackedWidget
        self.term_reference_view = self.create_term_reference_view()
        self.homologacao_view = self.create_homologacao_view()
        self.sicaf_view = self.create_sicaf_view()
        self.ata_contrato_view = self.create_ata_contrato_view()
        self.database_view = self.create_database_view()
        self.salvar_tabela_view = self.create_salvar_tabela_view()
        self.indicadores_view = self.create_indicadores_view()

        # Adiciona as visualizações ao QStackedWidget
        self.central_stack.addWidget(self.term_reference_view)
        self.central_stack.addWidget(self.homologacao_view)
        self.central_stack.addWidget(self.sicaf_view)
        self.central_stack.addWidget(self.ata_contrato_view)
        self.central_stack.addWidget(self.database_view)
        self.central_stack.addWidget(self.salvar_tabela_view)
        self.central_stack.addWidget(self.indicadores_view)
        
        # Define a visualização inicial
        self.central_stack.setCurrentWidget(self.term_reference_view)

        central_frame = QFrame()
        central_frame.setLayout(central_layout)
        return central_frame

    def create_title_layout(self):
        title_layout = QHBoxLayout()
        self.titulo_label = QLabel("Termo de Referência", alignment=Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.titulo_label)
        self.carregar_button = self.create_button("Carregar", self.import_tr)
        self.tabela_vazia_button = self.create_button("Tabela Vazia", lambda: self.criar_tabela_vazia("tabela_vazia.xlsx"))
        return title_layout

    def create_button_layout(self, buttons):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for texto, funcao, _ in buttons:
            layout.addWidget(self.create_button(texto, funcao))
        return layout
    
    def create_term_reference_view(self):
        term_view_widget = QWidget()
        layout = QVBoxLayout(term_view_widget)

        # Adiciona a QTableView ao layout
        self.treeView = QTableView()
        self.treeView.setModel(self.model)
        layout.addWidget(self.treeView)

        # Cria o layout horizontal para os botões
        button_layout = QHBoxLayout()
        carregar_button = self.create_button("Carregar Tabela", self.import_tr)
        tabela_nova_button = self.create_button("Tabela Nova", lambda: criar_tabela_vazia("tabela_vazia.xlsx", self.dialog))

        # Adiciona os botões ao layout horizontal
        button_layout.addWidget(carregar_button)
        button_layout.addWidget(tabela_nova_button)

        # Adiciona o layout dos botões ao layout principal
        layout.addLayout(button_layout)

        return term_view_widget

    def create_homologacao_view(self):
        homologacao_view_widget = QWidget()
        layout = QVBoxLayout(homologacao_view_widget)
        
        # Adiciona o QTableView ao layout
        self.homologacao_table = QTableView()
        layout.addWidget(self.homologacao_table)
        
        # Cria o layout horizontal para os botões
        button_layout = QHBoxLayout()
        abrir_pastas_button = self.create_button("Abrir Pastas", self.abrir_pastas)
        analisar_termos_button = self.create_button("Analisar Termos de Homologação", self.processar_homologacao)
        
        # Adiciona os botões ao layout horizontal
        button_layout.addWidget(abrir_pastas_button)
        button_layout.addWidget(analisar_termos_button)
        
        # Adiciona o layout dos botões ao layout principal
        layout.addLayout(button_layout)
        
        print("create_homologacao_view foi chamado e o layout foi configurado.")  # Depuração
        
        return homologacao_view_widget

    def processar_homologacao(self):
        try:
            print("processar_homologacao foi chamado.")  # Depuração

            # Verifica se a pasta de PDFs existe
            if not self.pdf_dir or not self.pdf_dir.exists():
                QMessageBox.warning(self.dialog, "Erro", "Pasta de PDFs não encontrada.")
                return

            # Lista todos os arquivos PDF na pasta
            pdf_files = list(self.pdf_dir.glob("*.pdf"))
            total_files = len(pdf_files)
            if not pdf_files:
                QMessageBox.information(self.dialog, "Nenhum Arquivo", "Nenhum arquivo PDF encontrado na pasta.")
                return

            all_data = []

            # Processa cada arquivo PDF
            for index, pdf_file in enumerate(pdf_files):
                # Converte o PDF para texto e salva no diretório especificado
                data = self.convert_pdf_to_text_and_save(pdf_file)
                all_data.extend(data)
                print(f"Processado {index + 1}/{total_files}: {pdf_file.name}")

            # Conclui o processamento
            self.on_conversion_finished(all_data)

        except Exception as e:
            # Captura qualquer erro e mostra uma mensagem de erro
            print(f"Erro ao processar homologação: {e}")
            QMessageBox.critical(self.dialog, "Erro", f"Ocorreu um erro durante o processamento: {str(e)}")


    def convert_pdf_to_text_and_save(self, pdf_file):
        """
        Converte o conteúdo de um PDF em texto e salva em um arquivo .txt no diretório txt_dir.

        Args:
            pdf_file (Path): O caminho do arquivo PDF a ser processado.

        Returns:
            list: Lista contendo o dicionário com 'item_num' e 'text' extraído.
        """
        # Extrai o texto do PDF
        text_content = self.extract_text_from_pdf(pdf_file)
        # Salva o texto extraído em um arquivo .txt no diretório especificado
        self.save_text_to_file(pdf_file, text_content)
        # Retorna os dados extraídos em forma de lista de dicionários
        return [{'item_num': pdf_file.stem, 'text': text_content}]

    def extract_text_from_pdf(self, pdf_file):
        """
        Extrai o texto de um arquivo PDF.

        Args:
            pdf_file (Path): O caminho do arquivo PDF a ser processado.

        Returns:
            str: O conteúdo de texto extraído do PDF.
        """
        with pdfplumber.open(pdf_file) as pdf:
            texts = [page.extract_text() for page in pdf.pages if page.extract_text() is not None]
            all_text = ' '.join(texts).replace('\n', ' ').replace('\x0c', ' ')
        return all_text

    def save_text_to_file(self, pdf_file, text_content):
        """
        Salva o conteúdo de texto extraído em um arquivo .txt.

        Args:
            pdf_file (Path): O caminho do arquivo PDF original.
            text_content (str): O conteúdo de texto a ser salvo.
        """
        txt_file = self.txt_dir / f"{pdf_file.stem}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(text_content)

    def on_conversion_finished(self, extracted_data):
        """
        Método chamado quando o processamento de todos os PDFs for concluído.
        """
        print("on_conversion_finished foi chamado.")  # Depuração
        
        # Verifica se a interface ainda está aberta antes de exibir a mensagem
        if hasattr(self, 'dialog') and self.dialog is not None:
            QMessageBox.information(self.dialog, "Concluído", "O processamento dos PDFs foi concluído.")
        else:
            QMessageBox.information(None, "Concluído", "O processamento dos PDFs foi concluído.")
        
        # Faça algo com os dados extraídos, se necessário


    def create_sicaf_view(self):
        sicaf_view_widget = QWidget()
        layout = QVBoxLayout(sicaf_view_widget)
        layout.addWidget(QLabel("Visualização do SICAF"))
        return sicaf_view_widget

    def create_ata_contrato_view(self):
        ata_contrato_view_widget = QWidget()
        layout = QVBoxLayout(ata_contrato_view_widget)
        layout.addWidget(QLabel("Visualização de Ata / Contrato"))
        return ata_contrato_view_widget

    def create_database_view(self):
        database_view_widget = QWidget()
        layout = QVBoxLayout(database_view_widget)
        layout.addWidget(QLabel("Visualização do Database"))
        return database_view_widget

    def create_salvar_tabela_view(self):
        salvar_tabela_view_widget = QWidget()
        layout = QVBoxLayout(salvar_tabela_view_widget)
        layout.addWidget(QLabel("Visualização para Salvar Tabela"))
        return salvar_tabela_view_widget

    def create_indicadores_view(self):
        indicadores_view_widget = QWidget()
        layout = QVBoxLayout(indicadores_view_widget)
        layout.addWidget(QLabel("Visualização dos Indicadores"))
        return indicadores_view_widget

    def create_button(self, texto, funcao):
        botao = QPushButton(texto)
        botao.clicked.connect(funcao)
        print(f"Botão '{texto}' criado e conectado à função {funcao.__name__}.")  # Depuração
        return botao

    def switch_to_view(self, view_name):
        self.update_title(view_name)

    def create_dynamic_view(self, view_name):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(f"Layout dinâmico para {view_name}"))
        return widget

    def update_title(self, titulo):
        self.titulo_label.setText(titulo)

    def load_table_view(self):
        if self.tr_variavel_df_carregado is not None:
            atualizar_modelo_com_dados(self.model, self.treeView, self.tr_variavel_df_carregado)
        else:
            self.import_tr()

    def switch_to_view(self, view_name):
        # Atualiza o título e muda para a visualização correspondente
        self.update_title(view_name)
        view_mapping = {
            "Termo de Referência": self.term_reference_view,
            "Termo de Homologação": self.homologacao_view,
            "SICAF": self.sicaf_view,
            "Ata / Contrato": self.ata_contrato_view,
            "Database": self.database_view,
            "Salvar Tabela": self.salvar_tabela_view,
            "Indicadores": self.indicadores_view,
        }
        self.central_stack.setCurrentWidget(view_mapping.get(view_name, self.term_reference_view))

    def get_buttons(self):
        return [
            ("Termo de Referência", lambda: self.switch_to_view("Termo de Referência"), "Importe um arquivo .xlsx com 4 colunas."),
            ("Termo de Homologação", lambda: self.switch_to_view("Termo de Homologação"), "Baixe e mova os termos de homologação."),
            ("SICAF", lambda: self.switch_to_view("SICAF"), "Baixe e mova o SICAF."),
            ("Ata / Contrato", lambda: self.switch_to_view("Ata / Contrato"), "Gere as atas ou contratos."),
            ("Database", lambda: self.switch_to_view("Database"), "Salva ou carrega os dados do Database."),
            ("Salvar Tabela", lambda: self.switch_to_view("Salvar Tabela"), "Importe um arquivo .xlsx."),
            ("Indicadores", lambda: self.switch_to_view("Indicadores"), "Visualize os indicadores.")
        ]

    def import_tr(self):
        file_path = select_file(self.dialog, "Importar Termo de Referência")
        if not file_path:
            return

        df = load_file(file_path)
        if df is None or (erros := formatar_e_validar_dados(df)):
            QMessageBox.warning(self.dialog, "Erro", "\n".join(erros) if erros else "Formato não suportado.")
            return

        self.tr_variavel_df_carregado = df
        atualizar_modelo_com_dados(self.model, self.treeView, df)

    def abrir_pastas(self):
        if self.pdf_dir and os.path.isdir(self.pdf_dir):
            open_folder(self.pdf_dir)
        else:
            QMessageBox.warning(self.dialog, "Erro", "O diretório PDF não é válido ou não está definido.")

    def processar_sicaf(self):
        pass

    def abrir_dialog_atas(self):
        pass

    def update_database(self):
        pass

    def salvar_tabela(self):
        pass

    def indicadores_normceim(self):
        pass

# Funções auxiliares
def create_button(texto, funcao):
    botao = QPushButton(texto)
    botao.clicked.connect(funcao)
    return botao

def create_fixed_width_frame(width, layout):
    frame = QFrame()
    frame.setFixedWidth(width)
    frame.setLayout(layout)
    return frame

def add_or_remove_widget(layout, widget, add):
    if add and widget.parent() is None:
        layout.addWidget(widget)
    elif not add and widget.parent() is not None:
        layout.removeWidget(widget)
        widget.setParent(None)

def create_button_layout(buttons):
    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    for texto, funcao, _ in buttons:
        layout.addWidget(create_button(texto, funcao))
    return layout

def create_dynamic_view(view_name):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.addWidget(QLabel(f"Layout dinâmico para {view_name}"))
    return widget

def select_file(parent, title):
    file_path, _ = QFileDialog.getOpenFileName(parent, title, "", "Arquivos Excel (*.xlsx);;Arquivos LibreOffice (*.ods)")
    return file_path

def load_file(file_path):
    ext = Path(file_path).suffix.lower()
    return pd.read_excel(file_path, engine='odf' if ext == '.ods' else None) if ext in ['.xlsx', '.ods'] else None

def atualizar_modelo_com_dados(model, tree_view, df):
    model.clear()
    model.setHorizontalHeaderLabels(['Item', 'Catálogo', 'Descrição', 'Descrição Detalhada'])
    for _, row in df.iterrows():
        model.appendRow([create_item(value) for value in [row['item_num'], row['catalogo'], row['descricao_tr'], row['descricao_detalhada']]])
    tree_view.resizeColumnsToContents()
    tree_view.setColumnWidth(2, 150)

def create_item(value):
    item = QStandardItem(str(value))
    item.setEditable(False)
    return item

def formatar_e_validar_dados(df):
    required_columns = ['item_num', 'catalogo', 'descricao_tr', 'descricao_detalhada']
    return [f"Coluna {col} ausente" for col in required_columns if col not in df.columns]

def criar_tabela_vazia(arquivo_xlsx, dialog):
    df_vazio = pd.DataFrame({
        "item_num": range(1, 11),
        "catalogo": [""] * 10,
        "descricao_tr": [""] * 10,
        "descricao_detalhada": [""] * 10
    })
    try:
        df_vazio.to_excel(arquivo_xlsx, index=False)
        os.startfile(arquivo_xlsx)
    except PermissionError:
        QMessageBox.warning(dialog, "Arquivo Aberto", "A tabela 'tabela_vazia.xlsx' está aberta. Feche o arquivo antes de tentar salvá-la novamente.")

def open_folder(path):
    if sys.platform == 'win32':  # Para Windows
        os.startfile(path)
    elif sys.platform == 'darwin':  # Para macOS
        subprocess.Popen(['open', path])
    else:  # Para Linux e outros sistemas Unix-like
        subprocess.Popen(['xdg-open', path])
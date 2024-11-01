
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from pathlib import Path
from diretorios import *
import pdfplumber
from modules.atas.gerar_atas.utils import *

class ProcessamentoThread(QThread):
    progresso_atualizado = pyqtSignal(int)
    processamento_concluido = pyqtSignal()

    def __init__(self, gerar_atas_instance):
        super().__init__()
        self.gerar_atas_instance = gerar_atas_instance

    def run(self):
        pdf_files = self.gerar_atas_instance.verificar_e_listar_pdfs()
        if not pdf_files:
            self.processamento_concluido.emit()
            return

        total_files = len(pdf_files)
        for i, pdf_file in enumerate(pdf_files):
            try:
                # Processamento do PDF
                with pdfplumber.open(pdf_file) as pdf:
                    text = "".join(page.extract_text() or "" for page in pdf.pages)
                
                output_txt_file = self.gerar_atas_instance.txt_dir / f"{pdf_file.stem}.txt"
                with open(output_txt_file, "w", encoding="utf-8") as txt_file:
                    txt_file.write(text)
                
            except Exception as e:
                print(f"Erro ao processar {pdf_file.name}: {str(e)}")
                continue
            
            # Atualiza o progresso
            progresso = int((i + 1) / total_files * 100)
            self.progresso_atualizado.emit(progresso)

        self.processamento_concluido.emit()

class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processando PDFs")
        self.setFixedSize(300, 100)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.label = QLabel("Processando arquivos...")
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.close)

        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.cancel_button)

    def atualizar_progresso(self, valor):
        self.progress_bar.setValue(valor)
        
class GerarAtas(QWidget):
    def __init__(self, icons_dir=None):
        super().__init__()
        self.setWindowTitle("Gerar Atas")
        self.icons_dir = icons_dir
        self.pdf_dir = Path(PDF_DIR)
        self.txt_dir = Path(TXT_DIR)
        self.tr_variavel_df_carregado = None
        self.model = QStandardItemModel()
        self.setup_ui()
        self.show()  # Exibe o widget

    def setup_ui(self):
        self.setLayout(self.create_main_layout())
        self.resize(1200, 600)

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
        tabela_nova_button = self.create_button("Tabela Nova", lambda: criar_tabela_vazia("tabela_vazia.xlsx", self))

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
        iniciar_processamento_button = self.create_button("Iniciar Processamento", self.iniciar_processamento_thread)
        
        # Adiciona os botões ao layout horizontal
        button_layout.addWidget(abrir_pastas_button)
        button_layout.addWidget(iniciar_processamento_button)
        
        # Adiciona o layout dos botões ao layout principal
        layout.addLayout(button_layout)
        
        return homologacao_view_widget

    def iniciar_processamento_thread(self):
        # Cria o diálogo de progresso
        self.progress_dialog = ProgressDialog(self)
        self.progress_dialog.show()

        # Cria a thread de processamento
        self.thread = ProcessamentoThread(self)
        self.thread.progresso_atualizado.connect(self.progress_dialog.atualizar_progresso)
        self.thread.processamento_concluido.connect(self.progress_dialog.close)
        self.thread.processamento_concluido.connect(self.processamento_concluido)

        # Inicia a thread
        self.thread.start()

    def processamento_concluido(self):
        QMessageBox.information(self, "Processamento Concluído", "O processamento foi concluído com sucesso.")

    def verificar_e_listar_pdfs(self):
        """Verifica a existência da pasta de PDFs e retorna a lista de arquivos PDF."""
        if not self.pdf_dir or not self.pdf_dir.exists():
            QMessageBox.warning(self, "Erro", "Pasta de PDFs não encontrada.")
            return None

        # Lista todos os arquivos PDF na pasta
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        if not pdf_files:
            QMessageBox.information(self, "Nenhum Arquivo", "Nenhum arquivo PDF encontrado na pasta.")
            return None

        print(f"Total de arquivos PDF encontrados: {len(pdf_files)}")  # Depuração
        return pdf_files

    def iniciar_processamento(self):
        try:
            pdf_files = self.verificar_e_listar_pdfs()
            if pdf_files is None:
                return

            # Verifica se a pasta para salvar os arquivos de texto existe
            if not self.txt_dir.exists():
                self.txt_dir.mkdir(parents=True, exist_ok=True)

            # Processa cada arquivo PDF
            for pdf_file in pdf_files:
                try:
                    print(f"Iniciando o processamento do arquivo: {pdf_file}")  # Depuração
                    # Abre o PDF com pdfplumber
                    with pdfplumber.open(pdf_file) as pdf:
                        text = ""
                        # Concatena o texto de todas as páginas do PDF
                        for page in pdf.pages:
                            text += page.extract_text() or ""
                    
                    # Nome do arquivo de saída .txt
                    output_txt_file = self.txt_dir / f"{pdf_file.stem}.txt"
                    # Salva o texto extraído no arquivo .txt
                    with open(output_txt_file, "w", encoding="utf-8") as txt_file:
                        txt_file.write(text)
                    
                    print(f"Processamento concluído para o arquivo: {pdf_file}")  # Depuração

                except Exception as e:
                    print(f"Erro ao processar {pdf_file.name}: {str(e)}")  # Depuração
                    QMessageBox.warning(self, "Erro", f"Falha ao processar {pdf_file.name}: {str(e)}")
                    continue

            QMessageBox.information(self, "Processamento Concluído", "Todos os arquivos PDF foram convertidos para .txt com sucesso.")

        except Exception as e:
            print(f"Erro durante o processamento: {str(e)}")  # Depuração
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao iniciar o processamento: {str(e)}")

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
        file_path = select_file(self, "Importar Termo de Referência") 
        if not file_path:
            return

        df = load_file(file_path)
        if df is None or (erros := formatar_e_validar_dados(df)):
            QMessageBox.warning(self, "Erro", "\n".join(erros) if erros else "Formato não suportado.")  
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

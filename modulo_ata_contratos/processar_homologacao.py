from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from pathlib import Path
from gerar_atas_pasta.regex_termo_homolog import *
from gerar_atas_pasta.regex_sicaf import *
from gerar_atas_pasta.canvas_gerar_atas import *
from utils.treeview_utils import open_folder, load_images, create_button
from diretorios import *
import pdfplumber
from modulo_ata_contratos.data_utils import PDFProcessingThread

TXT_OUTPUT_PATH = DATABASE_DIR / "relacao_cnpj.txt"
NUMERO_ATA_GLOBAL = None
GERADOR_NUMERO_ATA = None

tr_variavel_df_carregado = None

class ProgressDialog(QDialog):
    processing_complete = pyqtSignal(list)

    def __init__(self, total_files, pdf_dir, parent=None):
        super().__init__(parent)
        self.pdf_dir = pdf_dir
        self.total_files = total_files
        self.parent = parent
        self.setup_ui()

    def set_conversion_callback(self, callback):
        self.confirmButton.clicked.connect(callback)

    def setup_ui(self):
        self.setWindowTitle("Processando Arquivos PDF")
        main_layout = QVBoxLayout()
        
        header_layout = self.cabecalho_layout()  # Cria o layout do cabeçalho
        main_layout.addLayout(header_layout)  # Adiciona o cabeçalho ao layout principal
        
        global_event_manager.pdf_dir_updated.connect(self.on_pdf_dir_updated)

        # Define a fonte para todos os elementos
        fonte_padrao = QFont()
        fonte_padrao.setPointSize(14)

        # Caminho para o ícone de pasta
        icon_folder = QIcon(str(ICONS_DIR / "folder128.png"))

        # Adiciona o botão "Abrir Pasta" utilizando create_button
        self.abrirPastaButtonHomolog = self.create_button("Abrir Pasta", icon_folder, lambda: open_folder(self.pdf_dir), "Abrir diretório de PDFs", QSize(40, 40))
        
        # Botão "Atualizar"
        self.atualizarButton = self.create_button("Atualizar", QIcon(str(ICONS_DIR / "refresh.png")), self.atualizar_contagem_arquivos, "Atualizar contagem de arquivos PDF", QSize(40, 40))
        
        # Layout horizontal para os botões "Abrir Pasta" e "Atualizar"
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.abrirPastaButtonHomolog)
        buttons_layout.addWidget(self.atualizarButton)
        main_layout.addLayout(buttons_layout)

        self.label = QLabel(f"{self.total_files} arquivos PDF encontrados. Deseja processá-los?")
        self.label.setFont(fonte_padrao)  # Aplica a fonte ao QLabel
        main_layout.addWidget(self.label)

        self.progressBar = QProgressBar(self)
        self.progressBar.setMaximum(100)
        main_layout.addWidget(self.progressBar)

        self.confirmButton = QPushButton("Iniciar Processamento", self)
        self.confirmButton.setFont(fonte_padrao)
        self.confirmButton.clicked.connect(self.start_conversion)
        main_layout.addWidget(self.confirmButton)
        
        self.setLayout(main_layout)  # Define o layout principal

    def start_conversion(self):
        self.confirmButton.setEnabled(False)
        self.processing_thread = PDFProcessingThread(self.pdf_dir, TXT_DIR)
        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.processing_complete.connect(self.on_conversion_finished)
        self.processing_thread.start()

    def update_progress(self, value):
        if self.isVisible():
            self.progressBar.setValue(int(value))

    def on_conversion_finished(self, extracted_data):
        self.processing_complete.emit(extracted_data)  # Emite o sinal com os dados extraídos
        QMessageBox.information(self, "Conclusão", "O processamento dos dados foi concluído com sucesso!")
        self.confirmButton.setEnabled(True)
        self.close()

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

    def cabecalho_layout(self):
        header_layout = QHBoxLayout()
        title_label = QLabel("Processar Termos de Homologação")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        pixmap = QPixmap(str(MARINHA_PATH))
        pixmap = pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        header_layout.addWidget(image_label)
        return header_layout

    def create_button(self, text, icon, callback, tooltip_text, icon_size=None):
        btn = QPushButton(text)
        btn.setIcon(icon)
        if icon_size is None:
            icon_size = QSize(40, 40)
        btn.setIconSize(icon_size)
        btn.clicked.connect(callback)
        btn.setToolTip(tooltip_text)
        fonte_btn = QFont()
        fonte_btn.setPointSize(14)  # Define o tamanho da fonte como 14
        btn.setFont(fonte_btn)
        
        return btn
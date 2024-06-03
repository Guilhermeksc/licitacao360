from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from pathlib import Path
from modulo_ata_contratos.regex_termo_homolog import *
from modulo_ata_contratos.regex_sicaf import *
from modulo_ata_contratos.canvas_gerar_atas import *
from database.utils.treeview_utils import open_folder, load_images, create_button
from diretorios import *
from modulo_ata_contratos.data_utils import PDFProcessingThread
import webbrowser

class ProgressDialog(QDialog):
    processing_complete = pyqtSignal(list)

    def __init__(self, total_files, pdf_dir, parent=None):
        super().__init__(parent)
        self.pdf_dir = pdf_dir
        self.total_files = total_files
        self.parent = parent
        self.processed_files = set()
        self.setup_ui()

    def update_processed_files(self, new_files):
        self.processed_files.update(new_files)

    def set_conversion_callback(self, callback):
        self.confirmButton.clicked.connect(callback)

    def setup_ui(self):
        self.setWindowTitle("Processando Arquivos PDF")
        self.setFixedSize(800, 300)
        main_layout = QVBoxLayout()

        header_layout = self.cabecalho_layout()
        main_layout.addLayout(header_layout)

        fonte_padrao = QFont()
        fonte_padrao.setPointSize(14)

        self.abrirPastaButtonHomolog = self.create_button("   Abrir Pasta", QIcon(str(ICONS_DIR / "folder128.png")), lambda: open_folder(self.pdf_dir), "Abrir diretório de PDFs", QSize(40, 40))
        self.atualizarButton = self.create_button("   Atualizar", QIcon(str(ICONS_DIR / "refresh.png")), self.atualizar_contagem_arquivos, "Atualizar contagem de arquivos PDF", QSize(40, 40))
        self.comprasnetButton = self.create_button("", QIcon(str(ICONS_DIR / "comprasnet.svg")), self.abrir_comprasnet, "Abrir Comprasnet", QSize(200, 40))

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.abrirPastaButtonHomolog)
        buttons_layout.addWidget(self.atualizarButton)
        buttons_layout.addWidget(self.comprasnetButton)
        main_layout.addLayout(buttons_layout)

        self.label = QLabel(f"{self.total_files} arquivos PDF encontrados no diretório, clique em 'Iniciar Processamento' para começar.")
        self.label.setFont(fonte_padrao)
        main_layout.addWidget(self.label)

        self.progressBar = CustomProgressBar(self)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)  # Inicializar com valor 0
        main_layout.addWidget(self.progressBar)

        self.progress_label = QLabel("")  # Apenas para mostrar o texto sem o percentual
        self.progress_label.setFont(QFont("Arial", 16))  # Aumentar a fonte do texto
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.confirmButton = self.create_button("Iniciar Processamento", QIcon(str(ICONS_DIR / "rpa.png")), self.start_conversion, "Iniciar o processamento para obtenção dos dados dos Termos de Homologação", QSize(40, 40))
        main_layout.addWidget(self.confirmButton)

        self.setLayout(main_layout)

    def start_conversion(self):
        self.confirmButton.setEnabled(False)
        self.processing_thread = PDFProcessingThread(self.pdf_dir, TXT_DIR)
        self.processing_thread.progress_updated.connect(lambda current, total, current_file: self.update_progress(current, total, current_file))
        self.processing_thread.processing_complete.connect(self.on_conversion_finished)
        self.processing_thread.start()

        # Remover `self.label` e adicionar `self.progress_label` ao layout
        self.layout().removeWidget(self.label)
        self.label.deleteLater()
        self.layout().insertWidget(2, self.progress_label)  # Inserir na mesma posição de `self.label`

    def update_progress(self, current, total, current_file):
        if self.isVisible():
            progress_percent = int((current / total) * 100)
            self.progressBar.setValue(progress_percent)
            self.progress_label.setText(f"Analisando \"{current_file}\"")  # Remover o percentual aqui

    def on_conversion_finished(self, extracted_data):
        self.processing_complete.emit(extracted_data)
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
        fonte_btn.setPointSize(14)
        btn.setFont(fonte_btn)
        return btn

    def abrir_comprasnet(self):
        webbrowser.open("https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras")

class CustomProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Arial", 16))  # Aumentar a fonte do percentual
        self.setTextVisible(False)  # Desativar o texto padrão do QProgressBar

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QColor(Qt.GlobalColor.black))
        rect = self.rect()
        font_metrics = self.fontMetrics()
        progress_percent = self.value()
        text = f"{progress_percent}%" if progress_percent >= 0 else ""
        text_width = font_metrics.horizontalAdvance(text)
        text_height = font_metrics.height()
        painter.drawText(int((rect.width() - text_width) / 2), int((rect.height() + text_height) / 2), text)
        painter.end()
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from pathlib import Path
from modulo_ata_contratos.regex_termo_homolog import *
from modulo_ata_contratos.regex_sicaf import *
from modulo_ata_contratos.canvas_gerar_atas import *
from database.utils.treeview_utils import open_folder, load_images, create_button
from diretorios import *
import pdfplumber
from modulo_ata_contratos.data_utils import PDFProcessingThread
import traceback
from modulo_ata_contratos.data_utils import DatabaseDialog
import webbrowser

TXT_OUTPUT_PATH = DATABASE_DIR / "relacao_cnpj.txt"
NUMERO_ATA_GLOBAL = None
GERADOR_NUMERO_ATA = None

class SICAFDialog(QDialog):
    processing_complete = pyqtSignal(object)

    def __init__(self, sicaf_dir, dataframe, parent=None):
        super(SICAFDialog, self).__init__(parent)
        self.sicaf_dir = sicaf_dir
        self.dataframe = dataframe
        self.df_final = None
        self.setWindowTitle("Processamento SICAF")
        self.setFixedSize(800, 300)
        self.setFont(QFont("Arial", 14))
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        fonte_padrao = QFont()
        fonte_padrao.setPointSize(14)
        layout.addLayout(self.cabecalho_layout())
        self.abrirPastaButton = self.create_button("   Abrir Pasta", QIcon(str(ICONS_DIR / "folder128.png")), lambda: open_folder(self.sicaf_dir), "Abrir diretório de PDFs", QSize(40, 40))
        self.atualizarButton = self.create_button("   Atualizar", QIcon(str(ICONS_DIR / "refresh.png")), self.atualizar_contagem_arquivos, "Atualizar contagem de arquivos PDF", QSize(40, 40))
        self.comprasnetButton = self.create_button("", QIcon(str(ICONS_DIR / "comprasnet.svg")), self.abrir_comprasnet, "Abrir Comprasnet", QSize(200, 40))
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.abrirPastaButton)
        buttons_layout.addWidget(self.atualizarButton)
        buttons_layout.addWidget(self.comprasnetButton)
        layout.addLayout(buttons_layout)

        self.label = QLabel("Deseja processar os dados do SICAF?")
        self.label.setFont(fonte_padrao)
        layout.addWidget(self.label)
        self.progressBar = QProgressBar(self)
        layout.addWidget(self.progressBar)
        self.confirmButton = self.create_button("Iniciar Processamento", QIcon(str(ICONS_DIR / "rpa.png")), self.iniciar_processamento_sicaf, "Iniciar o processamento para obtenção dos dados do SICAF", QSize(40, 40))
        layout.addWidget(self.confirmButton)

    def cabecalho_layout(self):
        header_layout = QHBoxLayout()
        title_label = QLabel("Processar Dados SICAF")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        pixmap = QPixmap(str(MARINHA_PATH))
        pixmap = pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        header_layout.addWidget(image_label)
        return header_layout

    def atualizar_contagem_arquivos(self):
        pdf_files = list(self.sicaf_dir.glob("*.pdf"))
        self.total_files = len(pdf_files)
        self.label.setText(f"{self.total_files} arquivos PDF encontrados. Deseja processá-los?")
        self.progressBar.setMaximum(self.total_files)

    def abrir_comprasnet(self):
        webbrowser.open("https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras")
        
    def iniciar_processamento_sicaf(self):
        total_arquivos = len(list(self.sicaf_dir.glob("*.pdf")))
        self.progressBar.setMaximum(total_arquivos)
        print(f"Total de arquivos PDF para processar: {total_arquivos}")

        try:
            print("DataFrame recebido para processamento no SICAFDialog:")
            print(self.dataframe)

            self.df_final = processar_arquivos_sicaf(self, self.progressBar, self.update_progress, self.dataframe)

            if isinstance(self.df_final, pd.DataFrame):
                print("DataFrame resultante do processamento:")
                print(self.df_final)

                if not self.df_final.empty:
                    self.processing_complete.emit(self.df_final)   # Emite o sinal com o DataFrame final
                    QMessageBox.information(self, "Processamento Concluído", "Os arquivos SICAF foram processados com sucesso.")
                else:
                    raise ValueError("DataFrame processado está vazio.")
            else:
                raise ValueError("Resultado do processamento não é um DataFrame.")
        except Exception as e:
            print(f"Erro durante o processamento: {e}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro durante o processamento: {e}")

    def update_progress(self, value):
        self.progressBar.setValue(int(round(value)))

    def closeEvent(self, event):
        if self.df_final is not None:
            self.processing_complete.emit(self.df_final)  # Assegure-se de emitir ao fechar
        super(SICAFDialog, self).closeEvent(event)

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
# class SICAFDialog(QDialog):
#     def __init__(self, sicaf_dir, parent=None):
#         super().__init__(parent)
#         self.sicaf_dir = sicaf_dir  # Recebe sicaf_dir como parâmetro
#         global_event_manager.sicaf_dir_updated.connect(self.on_sicaf_dir_updated)

#         self.setWindowTitle("Processamento SICAF")
#         self.setLayout(QVBoxLayout())

#         fonte_padrao = QFont()
#         fonte_padrao.setPointSize(14)

#         # Layout Horizontal para botões "Relatório SICAF" e Informação
#         button_layout = QHBoxLayout()
        
#         # Botão "Relatório SICAF"
#         self.relatorioSicafButton = QPushButton("Relatório SICAF", self)
#         self.relatorioSicafButton.setFont(fonte_padrao)
#         self.relatorioSicafButton.clicked.connect(self.abrir_bloco_notas)
#         button_layout.addWidget(self.relatorioSicafButton)

#         # Botão de Informação
#         info_icon_path = str(ICONS_DIR / 'info.png')
#         tooltip_image_path = str(IMAGE_PATH / 'sicaf_info_small.png')

#         # Redimensionar o ícone
#         icon_size = QSize(32, 32)  # Substitua 32, 32 pelo tamanho desejado
#         pixmap = QPixmap(info_icon_path).scaled(icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

#         info_icon = QIcon(pixmap)

#         self.infoButton = QPushButton("", self)  # Removido o ícone do construtor
#         self.infoButton.setIcon(info_icon)  # Define o ícone no botão
#         self.infoButton.setIconSize(icon_size)  # Define o tamanho do ícone no botão

#         # Configurar o tamanho do botão para combinar com o tamanho do ícone
#         button_size = QSize(icon_size.width() + 10, icon_size.height() + 10)  # Adiciona uma margem ao tamanho do botão
#         self.infoButton.setFixedSize(button_size)

#         self.infoButton.setToolTip(f'<img src="{tooltip_image_path}" />')
#         self.infoButton.clicked.connect(lambda: QToolTip.showText(self.infoButton.mapToGlobal(QPoint(0, 0)), self.infoButton.toolTip()))
#         button_layout.addWidget(self.infoButton)

#         self.layout().addLayout(button_layout)

#         # Botão "Abrir Pasta"
#         self.abrirPastaButton = QPushButton("Abrir Pasta", self)
#         self.abrirPastaButton.setFont(fonte_padrao)
#         self.abrirPastaButton.clicked.connect(lambda: open_folder(self.sicaf_dir))

#         self.layout().addWidget(self.abrirPastaButton)

#         # Label de informação
#         self.label = QLabel("Deseja processar os dados do SICAF?")
#         self.label.setFont(fonte_padrao)
#         self.layout().addWidget(self.label)

#         # Adiciona a barra de progresso
#         self.progressBar = QProgressBar(self)
#         self.progressBar.setFont(fonte_padrao)
#         self.layout().addWidget(self.progressBar)

#         # Botão de confirmação
#         self.confirmButton = QPushButton("Confirmar", self)
#         self.confirmButton.setFont(fonte_padrao)
#         self.confirmButton.clicked.connect(self.iniciar_processamento_sicaf)
#         self.layout().addWidget(self.confirmButton)

#     def on_sicaf_dir_updated(self, new_sicaf_dir):
#         self.sicaf_dir = new_sicaf_dir

#     def abrir_bloco_notas(self):
#         TXT_OUTPUT_PATH = DATABASE_DIR / "relacao_cnpj.txt"
#         os.startfile(TXT_OUTPUT_PATH)

#     def iniciar_processamento_sicaf(self):
#         total_arquivos = len(list(self.sicaf_dir.glob("*.pdf")))
#         self.progressBar.setMaximum(total_arquivos)

#         try:
#             df_final_ordered = processar_arquivos_sicaf(self, self.progressBar, self.update_progress)
#             self.progressBar.setValue(self.progressBar.maximum())
#             QMessageBox.information(self, "Processamento Concluído", "Os arquivos SICAF foram processados com sucesso.")
#         except Exception as e:
#             traceback.print_exc()  # Imprime detalhes do erro no terminal
#             QMessageBox.critical(self, "Erro", f"Ocorreu um erro durante o processamento: {e}")

#     def update_progress(self, value):
#         # Converte o valor float para int antes de passar para setValue
#         self.progressBar.setValue(int(round(value)))
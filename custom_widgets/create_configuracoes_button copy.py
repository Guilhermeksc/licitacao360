#create_configuracoes_button.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QMessageBox, QDialog
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QObject, pyqtSignal, QSize, QTranslator, QLocale

from diretorios import *

class ConfiguracoesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("Configurações do Sistema")
        layout.addWidget(label)

        # Botão para fechar a janela
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

class ConfiguracoesWidget(QWidget):
    pdf_dir_updated = pyqtSignal(Path)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)  # Mudando para QHBoxLayout

        # Definindo a fonte Arial, tamanho 14
        font = QFont("Arial", 18)
        # Label no topo
        label = QLabel("Opções de configuração.")
        label.setFont(font)
        self.layout.addWidget(label)

        # Carregar ícones
        icon_paths = [
            "import_tr.png", "production.png", "production_red.png", "gerar_ata.png"
        ]
        icons = [QIcon(str(ICONS_DIR / path)) for path in icon_paths]

        # Criar botões com ícones
        self.btn_update_pdf_dir = QPushButton("Atualizar Pasta - 'Termos de Homologação'")
        self.btn_update_pdf_dir.setFont(font)  # Aplicando a fonte ao botão
        self.btn_update_pdf_dir.setIcon(icons[1])
        self.btn_update_pdf_dir.setIconSize(QSize(64, 64))  # Define o tamanho do ícone
        self.btn_update_pdf_dir.clicked.connect(self.update_pdf_dir)
        self.layout.addWidget(self.btn_update_pdf_dir)

        self.btn_update_sicaf_dir = QPushButton("Atualizar Pasta - 'SICAF'")
        self.btn_update_sicaf_dir.setFont(font)  # Aplicando a fonte ao botão
        self.btn_update_sicaf_dir.setIcon(icons[1])
        self.btn_update_sicaf_dir.setIconSize(QSize(64, 64))
        self.btn_update_sicaf_dir.clicked.connect(self.update_sicaf_dir)
        self.layout.addWidget(self.btn_update_sicaf_dir)

        # Botão para atualizar PASTA_TEMPLATE
        self.btn_update_pasta_template = QPushButton("Atualizar Pasta - 'Template'")
        self.btn_update_pasta_template.setFont(font)  # Aplicando a fonte ao botão
        self.btn_update_pasta_template.setIcon(icons[1])
        self.btn_update_pasta_template.setIconSize(QSize(64, 64))
        self.btn_update_pasta_template.clicked.connect(lambda: update_dir("Selecione o novo diretório para PASTA_TEMPLATE", "PASTA_TEMPLATE", PASTA_TEMPLATE, self))
        self.layout.addWidget(self.btn_update_pasta_template)

        # Botão para atualizar RELATORIO_PATH
        self.btn_update_relatorio_path = QPushButton("Atualizar Pasta - 'Relatório'")
        self.btn_update_relatorio_path.setFont(font)  # Aplicando a fonte ao botão
        self.btn_update_relatorio_path.setIcon(icons[1])
        self.btn_update_relatorio_path.setIconSize(QSize(64, 64))
        self.btn_update_relatorio_path.clicked.connect(self.update_relatorio_path)
        self.layout.addWidget(self.btn_update_relatorio_path)

    def get_title(self):
        return "Configurações"

    def get_content_widget(self):
        return self
    
    font = QFont("Arial", 14)  
    def setup_pdf_dir_button(self):
        self.btn_update_pdf_dir = QPushButton("Atualizar Pasta PDF")
        self.btn_update_pdf_dir.clicked.connect(self.update_pdf_dir)
        self.layout.addWidget(self.btn_update_pdf_dir)
               
    def update_pdf_dir(self):
        global PDF_DIR
        new_dir = update_dir("Selecione o novo diretório para PDF_DIR", "PDF_DIR", PDF_DIR, self)
        if new_dir != PDF_DIR:
            # Criar e configurar a caixa de diálogo de confirmação
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle('Alteração de diretório')
            msgBox.setText(f'Diretório antigo:\n{PDF_DIR}\nDiretório atualizado:\n{new_dir}\n\nDeseja alterar?')
            msgBox.setIcon(QMessageBox.Icon.Question)

            # Configurar fonte
            font = msgBox.font()
            font.setPointSize(14)
            msgBox.setFont(font)

            # Adicionar botões Sim e Não
            yesButton = msgBox.addButton("Sim", QMessageBox.ButtonRole.YesRole)
            noButton = msgBox.addButton("Não", QMessageBox.ButtonRole.NoRole)

            # Exibir a caixa de diálogo e aguardar resposta
            msgBox.exec()

            # Verificar qual botão foi pressionado
            if msgBox.clickedButton() == yesButton:
                PDF_DIR = new_dir
                global_event_manager.update_pdf_dir(PDF_DIR)

                # Criar e configurar a caixa de diálogo de sucesso
                successBox = QMessageBox(self)
                successBox.setWindowTitle('Alteração realizada com sucesso!')
                successBox.setText(f'Diretório atualizado:\n{new_dir}')
                successBox.setIcon(QMessageBox.Icon.Information)

                # Configurar fonte
                font = successBox.font()
                font.setPointSize(14)
                successBox.setFont(font)

                # Exibir a caixa de diálogo de sucesso
                successBox.exec()

    def update_sicaf_dir(self):
        global SICAF_DIR
        new_dir = update_dir("Selecione o novo diretório para SICAF_DIR", "SICAF_DIR", SICAF_DIR, self)
        if new_dir != SICAF_DIR:
            # Criar e configurar a caixa de diálogo de confirmação
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle('Alteração de diretório')
            msgBox.setText(f'Diretório antigo:\n{SICAF_DIR}\nDiretório atualizado:\n{new_dir}\n\nDeseja alterar?')
            msgBox.setIcon(QMessageBox.Icon.Question)

            # Configurar fonte
            font = msgBox.font()
            font.setPointSize(14)
            msgBox.setFont(font)

            # Adicionar botões Sim e Não
            yesButton = msgBox.addButton("Sim", QMessageBox.ButtonRole.YesRole)
            noButton = msgBox.addButton("Não", QMessageBox.ButtonRole.NoRole)

            # Exibir a caixa de diálogo e aguardar resposta
            msgBox.exec()

            # Verificar qual botão foi pressionado
            if msgBox.clickedButton() == yesButton:
                SICAF_DIR = new_dir
                global_event_manager.update_pdf_dir(SICAF_DIR)

                # Criar e configurar a caixa de diálogo de sucesso
                successBox = QMessageBox(self)
                successBox.setWindowTitle('Alteração realizada com sucesso!')
                successBox.setText(f'Diretório atualizado:\n{new_dir}')
                successBox.setIcon(QMessageBox.Icon.Information)

                # Configurar fonte
                font = successBox.font()
                font.setPointSize(14)
                successBox.setFont(font)

                # Exibir a caixa de diálogo de sucesso
                successBox.exec()

    def update_relatorio_path(self):
        global RELATORIO_PATH
        new_dir = update_dir("Selecione o novo diretório para RELATORIO_PATH", "RELATORIO_PATH", RELATORIO_PATH, self)
        if new_dir != RELATORIO_PATH:
            # Criar e configurar a caixa de diálogo de confirmação
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle('Alteração de diretório')
            msgBox.setText(f'Diretório antigo:\n{RELATORIO_PATH}\nDiretório atualizado:\n{new_dir}\n\nDeseja alterar?')
            msgBox.setIcon(QMessageBox.Icon.Question)

            # Configurar fonte
            font = msgBox.font()
            font.setPointSize(14)
            msgBox.setFont(font)

            # Adicionar botões Sim e Não
            yesButton = msgBox.addButton("Sim", QMessageBox.ButtonRole.YesRole)
            noButton = msgBox.addButton("Não", QMessageBox.ButtonRole.NoRole)

            # Exibir a caixa de diálogo e aguardar resposta
            msgBox.exec()

            # Verificar qual botão foi pressionado
            if msgBox.clickedButton() == yesButton:
                RELATORIO_PATH = new_dir
                global_event_manager.update_pdf_dir(RELATORIO_PATH)

                # Criar e configurar a caixa de diálogo de sucesso
                successBox = QMessageBox(self)
                successBox.setWindowTitle('Alteração realizada com sucesso!')
                successBox.setText(f'Diretório atualizado:\n{new_dir}')
                successBox.setIcon(QMessageBox.Icon.Information)

                # Configurar fonte
                font = successBox.font()
                font.setPointSize(14)
                successBox.setFont(font)

                # Exibir a caixa de diálogo de sucesso
                successBox.exec()

    def on_pdf_dir_updated(self):
        # Código para atualizar qualquer parte do programa que dependa de PDF_DIR
        pass
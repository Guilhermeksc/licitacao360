#create_configuracoes_button.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QMessageBox, QDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QObject, pyqtSignal, QSize, QTranslator, QLocale
from pathlib import Path
import os
from diretorios import *

class ConfiguracoesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Criar e adicionar a instância de ConfiguracoesWidget
        self.configuracoes_widget = ConfiguracoesWidget(self)
        layout.addWidget(self.configuracoes_widget)

        # Botão para fechar a janela
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

class DiretoriosDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Diretórios Atuais")
        self.setFixedSize(500, 400)  # Define o tamanho fixo do QDialog
        self.setLayout(QVBoxLayout())
        self.listWidget = QListWidget(self)
        self.layout().addWidget(self.listWidget)

        # Adicionando diretórios e botões
        self.adicionar_item_diretorio("Termo de Homologação", PDF_DIR)
        self.adicionar_item_diretorio("SICAF das empresas", SICAF_DIR)
        self.adicionar_item_diretorio("Local dos 'Templates'", PASTA_TEMPLATE)
        self.adicionar_item_diretorio("Local dos 'Relatórios'", RELATORIO_PATH)

    def adicionar_item_diretorio(self, nome, diretorio):
        item = QListWidgetItem(self.listWidget)
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Cria o botão e define suas propriedades
        botao = QPushButton()
        botao.setIcon(QIcon(str(ICONS_DIR / "abrir_pasta.png")))
        botao.setIconSize(QSize(30, 30))
        botao.setFixedSize(40, 40)  # Define o tamanho fixo do botão
        botao.clicked.connect(lambda: os.startfile(str(diretorio)))

        label = QLabel(f"{nome}:\n{diretorio}")

        layout.addWidget(botao)
        layout.addWidget(label)

        widget.setLayout(layout)

        item.setSizeHint(widget.sizeHint())
        self.listWidget.addItem(item)
        self.listWidget.setItemWidget(item, widget)

class ConfiguracoesWidget(QWidget):
    pdf_dir_updated = pyqtSignal(Path)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)  # Mudando para QHBoxLayout

        # Definindo a fonte Arial, tamanho 14
        font = QFont("Arial", 14)

        # Carregar ícones
        icon_paths = [
            "import_tr.png", "production.png", "production_red.png", "gerar_ata.png"
        ]
        icons = [QIcon(str(ICONS_DIR / path)) for path in icon_paths]

        # Criar botões com ícones
        self.btn_update_pdf_dir = QPushButton("Atualizar Pasta - 'Termos de Homologação'")
        self.btn_update_pdf_dir.setFont(font)  # Aplicando a fonte ao botão
        self.btn_update_pdf_dir.setIcon(icons[1])
        self.btn_update_pdf_dir.setIconSize(QSize(32, 32)) 
        self.btn_update_pdf_dir.clicked.connect(self.update_pdf_dir)    
        self.layout.addWidget(self.btn_update_pdf_dir)

        self.btn_update_sicaf_dir = QPushButton("Atualizar Pasta - 'SICAF'")
        self.btn_update_sicaf_dir.setFont(font)  # Aplicando a fonte ao botão
        self.btn_update_sicaf_dir.setIcon(icons[1])
        self.btn_update_sicaf_dir.setIconSize(QSize(32, 32)) 
        self.btn_update_sicaf_dir.clicked.connect(self.update_sicaf_dir)
        self.layout.addWidget(self.btn_update_sicaf_dir)

        # Botão para atualizar PASTA_TEMPLATE
        self.btn_update_pasta_template = QPushButton("Atualizar Pasta - 'Template'")
        self.btn_update_pasta_template.setFont(font)  # Aplicando a fonte ao botão
        self.btn_update_pasta_template.setIcon(icons[1])
        self.btn_update_pasta_template.setIconSize(QSize(32, 32)) 
        self.btn_update_pasta_template.clicked.connect(lambda: update_dir("Selecione o novo diretório para PASTA_TEMPLATE", "PASTA_TEMPLATE", PASTA_TEMPLATE, self))
        self.layout.addWidget(self.btn_update_pasta_template)

        # Botão para atualizar RELATORIO_PATH
        self.btn_update_relatorio_path = QPushButton("Atualizar Pasta - 'Relatório'")
        self.btn_update_relatorio_path.setFont(font)  # Aplicando a fonte ao botão
        self.btn_update_relatorio_path.setIcon(icons[1])
        self.btn_update_relatorio_path.setIconSize(QSize(32, 32)) 
        self.btn_update_relatorio_path.clicked.connect(self.update_relatorio_path)
        self.layout.addWidget(self.btn_update_relatorio_path)

        self.btn_lista_diretorios = QPushButton("Lista de Diretórios")
        self.btn_lista_diretorios.setFont(font)
        self.btn_lista_diretorios.clicked.connect(self.mostrar_diretorios_atuais)
        self.layout.addWidget(self.btn_lista_diretorios)
        # Criar botões com ícones
        self.btn_update_pdf_dir = QPushButton("Atualizar Pasta - 'Database'")
        self.btn_update_pdf_dir.setFont(font)  # Aplicando a fonte ao botão
        self.btn_update_pdf_dir.setIcon(icons[1])
        self.btn_update_pdf_dir.setIconSize(QSize(32, 32)) 
        self.btn_update_pdf_dir.clicked.connect(self.update_pdf_dir)    
        self.layout.addWidget(self.btn_update_pdf_dir)

    def mostrar_diretorios_atuais(self):
        dialog = DiretoriosDialog(self)
        dialog.exec()

    def get_title(self):
        return "Configurações"

    def get_content_widget(self):
        return self
    
    def setup_pdf_dir_button(self):
        self.btn_update_pdf_dir = QPushButton("Atualizar Pasta 'Termos de Homologação'")
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

    def update_sicaf_dir(self):
        global CONTROLE_DADOS
        new_dir = update_dir("Selecione o novo diretório para CONTROLE_DADOS", "CONTROLE_DADOS", CONTROLE_DADOS, self)
        if new_dir != CONTROLE_DADOS:
            # Criar e configurar a caixa de diálogo de confirmação
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle('Alteração de diretório')
            msgBox.setText(f'Diretório antigo:\n{CONTROLE_DADOS}\nDiretório atualizado:\n{new_dir}\n\nDeseja alterar?')
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
                CONTROLE_DADOS = new_dir
                global_event_manager.update_database_dir(CONTROLE_DADOS)

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
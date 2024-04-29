from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import pandas as pd
import subprocess
from docxtpl import DocxTemplate
PLANEJAMENTO_DIR = BASE_DIR / "planejamento"
import sys
from datetime import datetime
import os
from win32com.client import Dispatch
import time
import sqlite3

class BaseDialog(QDialog):
    def __init__(self, main_app, df_registro, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.df_registro = df_registro
        self.setup()

    def setup(self):
        self.setWindowTitle(self.window_title)
        self.setFixedSize(self.fixed_size)
        self.layoutPrincipal = QHBoxLayout(self)
        self.widgetEsquerda = QWidget()
        self.widgetDireita = QWidget()
        self.layoutEsquerda = QVBoxLayout(self.widgetEsquerda)
        self.layoutDireita = QVBoxLayout(self.widgetDireita)
        self.createCommonWidgets()  # Criar widgets comuns a todas as subclasses
        self.createWidgets()        # Permitir que subclasses adicionem widgets específicos
        self.layoutPrincipal.addWidget(self.widgetEsquerda)
        self.layoutPrincipal.addWidget(self.widgetDireita)
        self.setLayout(self.layoutPrincipal)
        self.applyCommonStyles()

    def createCommonWidgets(self):
        # Criar widgets que são comuns para todos os diálogos
        self.grupoComum = QGroupBox("Configurações Comuns")
        layout = QVBoxLayout(self.grupoComum)
        commonLabel = QLabel("Label comum para todos os diálogos")
        layout.addWidget(commonLabel)
        self.layoutEsquerda.addWidget(self.grupoComum)

    def createWidgets(self):
        # Método para ser implementado nas subclasses com widgets específicos
        pass

    def createGroups(self):
        # Criar grupos de widgets com base nas configurações fornecidas
        for group_name, details in self.settings['groups'].items():
            group_box = QGroupBox(details['title'])
            layout = QVBoxLayout(group_box)
            for widget in details['widgets']:
                if widget['type'] == 'label':
                    label = QLabel(widget['text'])
                    layout.addWidget(label)
                elif widget['type'] == 'button':
                    button = QPushButton(widget['text'])
                    button.clicked.connect(widget['action'])
                    layout.addWidget(button)
                elif widget['type'] == 'lineedit':
                    line_edit = QLineEdit()
                    layout.addWidget(line_edit)
                elif widget['type'] == 'textedit':
                    text_edit = QTextEdit()
                    text_edit.setPlainText(widget['default_text'])
                    layout.addWidget(text_edit)
            if 'layout' in details:
                getattr(self, details['layout']).addWidget(group_box)
                
    def applyCommonStyles(self):
        self.setStyleSheet("""
            QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QDateEdit {
                font-size: 16px;
            }
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid gray;
                border-radius: 5px;
                margin-top: 0.5em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)

    def editTemplate(self, template_path):
        try:
            if sys.platform == "win32":
                subprocess.run(["start", "winword", str(template_path)], check=True, shell=True)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(template_path)], check=True)
            else:  # linux variants
                subprocess.run(["xdg-open", str(template_path)], check=True)
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir o documento: {e}")

    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        # Mostra a tooltip na posição atual do mouse
        QToolTip.showText(QCursor.pos(), "Texto copiado para a área de transferência.", msecShowTime=1500)

    def selecionarPasta(self):
        pasta_selecionada = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if pasta_selecionada:
            self.pasta = pasta_selecionada
            print(f"Pasta selecionada: {self.pasta}")
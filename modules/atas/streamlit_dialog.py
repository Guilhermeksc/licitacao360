from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import subprocess
import os
import sys
from diretorios import STREAMLIT_PATH
from pathlib import Path
import requests
class StreamlitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dashboard de Licitações")
        self.setMinimumSize(1024, 768)

        layout = QVBoxLayout(self)

        # Configurar o QWebEngineView
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)

        # Adicionar um botão para fechar o diálogo
        button_layout = QHBoxLayout()
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)
        button_layout.addStretch(1)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        # Iniciar o Streamlit em segundo plano
        self.start_streamlit()
            
    def start_streamlit(self):
        streamlit_url = "http://localhost:8501"
        
        # Verifica se o script Streamlit existe
        if not Path(STREAMLIT_PATH).exists():
            raise FileNotFoundError(f"O caminho {STREAMLIT_PATH} não foi encontrado.")
        
        # Executa o Streamlit usando o comando correto
        process = subprocess.Popen(["streamlit", "run", str(STREAMLIT_PATH), "--server.headless", "true"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        
        # Espera um curto período para garantir que o servidor Streamlit esteja rodando
        QTimer.singleShot(5000, lambda: self.check_streamlit_connection(streamlit_url, process))

    def check_streamlit_connection(self, streamlit_url, process):
        try:
            response = requests.get(streamlit_url)
            if response.status_code == 200:
                self.web_view.setUrl(QUrl(streamlit_url))
            else:
                raise ConnectionError("Não foi possível conectar ao servidor Streamlit.")
        except Exception as e:
            process.terminate()  # Encerrar o processo do Streamlit em caso de erro
            QMessageBox.critical(self, "Erro", f"Erro ao iniciar o Streamlit: {str(e)}")


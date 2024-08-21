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
        
        # Resolver o caminho do script Streamlit de forma adequada
        if hasattr(sys, '_MEIPASS'):
            # Caminho quando empacotado com PyInstaller
            streamlit_script = os.path.join(sys._MEIPASS, "streamlit", "streamlit_app.py")
        else:
            # Caminho durante o desenvolvimento
            streamlit_script = STREAMLIT_PATH

        # Verifique se o caminho do script existe
        if not Path(streamlit_script).exists():
            raise FileNotFoundError(f"O caminho {streamlit_script} não foi encontrado.")
        
        # Executar o Streamlit usando o caminho correto
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", streamlit_script, "--server.headless", "true"])

        # Esperar um curto período para garantir que o servidor Streamlit esteja rodando
        QTimer.singleShot(2000, lambda: self.web_view.setUrl(QUrl(streamlit_url)))
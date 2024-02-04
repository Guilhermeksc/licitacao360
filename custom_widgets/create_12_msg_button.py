import pandas as pd
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import QFile, QTextStream, QIODevice
from styles.styless import get_transparent_title_style
from diretorios import *
import re

class HallResponsaveis(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.create_layout()
        self.create_buttons()
        self.add_text_area()

    def create_layout(self):
        self.layout = QVBoxLayout(self)
        label = QLabel("Mensagens Padronizadas")
        label.setStyleSheet(get_transparent_title_style())
        self.layout.addWidget(label)

    def create_buttons(self):
        buttons = [
            ("Divulgação do\nIRP", "irp.txt"),
            ("Solicitação de\nSenha/Rede", "senharede.txt"),
            ("Informação de\nLicitação Divulgada", "licitacaodivulgada.txt"),
            ("Informação de\nLicitação Homologada", "licitacaohomologada.txt")
        ]
        buttons_layout = QHBoxLayout()
        for text, file_name in buttons:
            button = QPushButton(text)
            button.setStyleSheet("font-size: 12pt;")
            button.clicked.connect(lambda _, f=file_name: self.open_file(MENSAGEM_DIR / f))
            buttons_layout.addWidget(button)
        self.layout.addLayout(buttons_layout)

    def add_text_area(self):
        self.text_area = QTextEdit(self)
        self.layout.addWidget(self.text_area)
        self.text_area.textChanged.connect(self.salvar_texto_alterado)
        self.text_area.setStyleSheet("font-size: 12pt;")

    def get_title(self):
        return "Mensagens Padronizadas"

    def get_content_widget(self):
        return self
    
    def salvar_texto_alterado(self):
        text = self.text_area.toPlainText()
        self.salvar_texto_no_arquivo(text)

    def salvar_texto_no_arquivo(self, text):
        # Converter o caminho em um objeto Path para facilidade de manipulação
        local_para_salvar = Path(self.local_para_salvar)

        # Criar todas as pastas intermediárias necessárias
        local_para_salvar.parent.mkdir(parents=True, exist_ok=True)

        # Salvar o arquivo de texto
        with open(local_para_salvar, 'w', encoding='utf-8') as file:
            file.write(text)
            
    def open_file(self, file_path):
        # Ler o arquivo CSV
        df = pd.read_csv(ITEM_SELECIONADO_PATH)
        variables = df.to_dict('records')[0]
        base_file_name = file_path.stem

        relatorio_path = get_relatorio_path()
        num_pregao = variables['num_pregao']
        ano_pregao = variables['ano_pregao']
        nome_dir_principal = f"PE {num_pregao}-{ano_pregao}"
        path_dir_principal = relatorio_path / nome_dir_principal
        path_subpasta = path_dir_principal / "Mensagem SIGDEM"

        nome_do_arquivo = f"{base_file_name}.txt"
        local_para_salvar = path_subpasta / nome_do_arquivo
        self.local_para_salvar = str(local_para_salvar)  # Defina aqui

        # Verificar se o arquivo já existe
        if local_para_salvar.exists():
            with open(local_para_salvar, 'r', encoding='utf-8') as file:
                text = file.read()
        else:
            # Abrir o arquivo original se o específico não existir
            file = QFile(str(file_path))
            if file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
                stream = QTextStream(file)
                text = stream.readAll()

                # Substituir as variáveis no texto usando expressão regular
                for key, value in variables.items():
                    pattern = re.compile(r'\{\{\s*' + re.escape(key) + r'\s*\}\}')
                    text = pattern.sub(str(value), text)

        # Atualizar o texto na área de texto da interface e salvar o arquivo
        self.text_area.setPlainText(text)
        self.criar_pasta_e_salvar_txt(df, text, base_file_name)

    def criar_pasta_e_salvar_txt(self, df, text, base_file_name):
        relatorio_path = get_relatorio_path()
        num_pregao = df['num_pregao'].iloc[0]
        ano_pregao = df['ano_pregao'].iloc[0]

        # Criar nome e caminho da pasta principal
        nome_dir_principal = f"PE {num_pregao}-{ano_pregao}"
        path_dir_principal = relatorio_path / nome_dir_principal
        if not path_dir_principal.exists():
            path_dir_principal.mkdir(parents=True)

        # Criar subpasta "mensagem"
        path_subpasta = path_dir_principal / "Mensagem SIGDEM"
        if not path_subpasta.exists():
            path_subpasta.mkdir()

        # Definir o nome e o caminho do arquivo de texto
        nome_do_arquivo = f"{base_file_name}.txt"
        local_para_salvar = path_subpasta / nome_do_arquivo

        # Salvar o arquivo de texto
        with open(local_para_salvar, 'w', encoding='utf-8') as file:
            file.write(text)
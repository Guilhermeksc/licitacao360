from pathlib import Path
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QObject, pyqtSignal
import json

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
CONFIG_FILE = BASE_DIR / "config.json"

def load_config(key, default_value):
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get(key, default_value)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_value

def save_config(key, value):
    config = {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    config[key] = value
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def update_dir(title, key, default_value, parent=None):
    new_dir = QFileDialog.getExistingDirectory(parent, title)
    if new_dir:
        save_config(key, new_dir)
        return Path(new_dir)
    return default_value

ICONS_DIR = DATABASE_DIR / "icons"
DATABASE_DIR = Path(load_config("DATABASE_DIR", BASE_DIR / "database"))
PDF_DIR = Path(load_config("PDF_DIR", DATABASE_DIR / "pasta_pdf"))
SICAF_DIR = Path(load_config("SICAF_DIR", DATABASE_DIR / "pasta_sicaf"))
PASTA_TEMPLATE = Path(load_config("PASTA_TEMPLATE", DATABASE_DIR / "template"))
RELATORIO_PATH = Path(load_config("RELATORIO_PATH", DATABASE_DIR / "relatorio"))
LV_DIR = Path(load_config("LV_DIR", BASE_DIR / "Lista_de_Verificacao"))

TXT_DIR = PDF_DIR / "homolog_txt"
SICAF_TXT_DIR = SICAF_DIR / "sicaf_txt"
ATA_DIR = DATABASE_DIR / "atas"
TR_VAR_DIR = DATABASE_DIR / "tr_variavel.xlsx"
ULTIMO_CONTRATO_DIR = DATABASE_DIR / "ultimo_contrato.txt"

NOMES_INVALIDOS = ['N/A', None, 'None', 'nan', 'null']
TEMPLATE_PATH = DATABASE_DIR / 'template_ata.docx'
TEMPLATE_PATH_TEMP = BASE_DIR / 'database/template_ata_temp.docx'
TEMPLATE_CONTRATO_PATH = DATABASE_DIR / 'template_contrato.docx'
CSV_DIR = DATABASE_DIR / "dados.csv"
VARIAVEIS_DIR = DATABASE_DIR / "variaveis.xlsx"
XLSX_SICAF_PATH = DATABASE_DIR / "sicaf.xlsx"
CSV_SICAF_PATH = DATABASE_DIR / "sicaf.csv"
LV_FINAL_DIR = DATABASE_DIR / "Nova pasta"
LV_BASE_DIR = DATABASE_DIR / "Nova pasta"

WEBDRIVER_DIR = DATABASE_DIR / "selenium"
WEBDRIVER_FIREFOX_PATH = WEBDRIVER_DIR / "geckodriver.exe"
CONTROLE_PREGOEIROS_DIR = DATABASE_DIR / "controle_pregoeiros.xlsx"

CONTROLE_FASE_PROCESSO = DATABASE_DIR / "controle_processos_blocos.xlsx"

TREEVIEW_DATA_PATH =  DATABASE_DIR / "treeview_data.csv"
TEMPLATE_DIR = DATABASE_DIR / "template"
CP_DIR = TEMPLATE_DIR / "comunicacao_padronizada" 
GERAR_RELATORIO_DIR = TEMPLATE_DIR / "relatorio_controle_pregao" 

ESCALACAO_PREGOEIROS = DATABASE_DIR / "pregoeiros.json"
TEMPLATE_CHECKLIST = TEMPLATE_DIR / "checklist.docx"
TEMPLATE_AUTUACAO = TEMPLATE_DIR / "template_autuacao.docx"

IMAGE_PATH = DATABASE_DIR / "image"
MENSAGEM_DIR = DATABASE_DIR / "mensagem"
ITEM_SELECIONADO_PATH = DATABASE_DIR / "item_selecionado.csv"


BG_IMAGEM_PATH = IMAGE_PATH / "bg1.png"
CONTROLE_PROCESSOS_DIR = DATABASE_DIR / "controle_processos.xlsx"
CONTROLE_DISPENSA_DIR = DATABASE_DIR / "controle_dispensa.xlsx"

TABELA_UASG_DIR = DATABASE_DIR / "tabela_uasg.xlsx"

FONT_STYLE = ("Arial", 20, "bold")

URL_SAPIENS = 'https://sapiens.agu.gov.br/login'

PROCESSOS_JSON_PATH = DATABASE_DIR / "controle_processos.json"
TEMPLATE_PREGOEIRO = TEMPLATE_DIR / "template_cp_pregoeiro.docx"
ICONS_EDIT_DIR = ICONS_DIR  / "edit.gif"

#Diretórios do módulo Controle de Contratos
CONTRATOS_PATH = DATABASE_DIR / "Contratos.csv"
ADICIONAIS_PATH = DATABASE_DIR / "Dados_Adicionais.csv"
CONTROLE_CONTRATOS_DIR = BASE_DIR / "controle_contratos"
DATABASE_CONTRATOS = CONTROLE_CONTRATOS_DIR / "data_contratos"
SETORES_OM = DATABASE_CONTRATOS / "setores_om.xlsx"
CP_CONTRATOS_DIR = CONTROLE_CONTRATOS_DIR / "comunicacao_padronizada"

def get_relatorio_path():
    global RELATORIO_PATH
    # Atualize RELATORIO_PATH conforme necessário
    return RELATORIO_PATH

class ConfigManager(QObject):
    config_updated = pyqtSignal(str, Path)  # sinal emitido quando uma configuração é atualizada

    def __init__(self, config_file):
        super().__init__()
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def update_config(self, key, value):
        self.config[key] = value
        self.save_config()
        self.config_updated.emit(key, value)

    def get_config(self, key, default_value):
        return self.config.get(key, default_value)

class EventManager(QObject):
    pdf_dir_updated = pyqtSignal(Path)
    sicaf_dir_updated = pyqtSignal(Path)
    relatorio_path_updated = pyqtSignal(Path)

    def __init__(self):
        super().__init__()

    def update_pdf_dir(self, new_dir):
        print(f"Emitindo sinal de atualização de PDF_DIR: {new_dir}")
        self.pdf_dir_updated.emit(new_dir)

    def update_sicaf_dir(self, new_dir):
        self.sicaf_dir_updated.emit(new_dir)

    def update_relatorio_path(self, new_dir):
        global RELATORIO_PATH
        RELATORIO_PATH = new_dir
        self.relatorio_path_updated.emit(new_dir)

# Instância global do gerenciador de eventos
global_event_manager = EventManager()
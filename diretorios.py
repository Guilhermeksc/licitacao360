from pathlib import Path
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QObject, pyqtSignal
import json

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
CONFIG_FILE = BASE_DIR / "config.json"
# CONTROLE_DADOS = DATABASE_DIR / "controle_dados.db"
HOME_PATH = BASE_DIR / "home.py"
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

# Função atualizada para escolher arquivos
def update_file_path(title, key, default_value, parent=None, file_type="All Files (*)"):
    new_file, _ = QFileDialog.getOpenFileName(parent, title, str(default_value), file_type)
    if new_file:
        save_config(key, new_file)
        return Path(new_file)
    return default_value


MODULES_DIR = BASE_DIR / "modules"  # Diretório dos módulos
PLANEJAMENTO_DIR = MODULES_DIR / "planejamento"
TEMPLATE_PLANEJAMENTO_DIR = PLANEJAMENTO_DIR / "template"
DISPENSA_DIR = MODULES_DIR / "dispensa_eletronica"
JSON_DISPENSA_DIR = DISPENSA_DIR / "json"
FILE_PATH_DISPENSA = DISPENSA_DIR / "dispensa_eletronica.json"
TEMPLATE_DISPENSA_DIR = DISPENSA_DIR / "template"
ICONS_DIR = DATABASE_DIR / "icons"
ICONE = ICONS_DIR / "icone.ico"
CONTROLE_DADOS = Path(load_config("CONTROLE_DADOS", BASE_DIR / "database/controle_dados.db"))
DATABASE_DIR = Path(load_config("DATABASE_DIR", BASE_DIR / "database"))
PDF_DIR = Path(load_config("PDF_DIR", DATABASE_DIR / "pasta_pdf"))
SICAF_DIR = Path(load_config("SICAF_DIR", DATABASE_DIR / "pasta_sicaf"))
PASTA_TEMPLATE = Path(load_config("PASTA_TEMPLATE", DATABASE_DIR / "template"))
RELATORIO_PATH = Path(load_config("RELATORIO_PATH", DATABASE_DIR / "relatorio"))
LV_DIR = Path(load_config("LV_DIR", BASE_DIR / "Lista_de_Verificacao"))


CONTROLE_LIMITE_DISPENSA_DIR = DATABASE_DIR / "controle_limite_dispensa"
ARQUIVO_DADOS_PDM_CATSER = CONTROLE_LIMITE_DISPENSA_DIR / 'dados_pdm.db'

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

TREEVIEW_DATA_PATH =  DATABASE_DIR / "treeview_data.csv"
TEMPLATE_DIR = DATABASE_DIR / "template"
CP_DIR = TEMPLATE_DIR / "comunicacao_padronizada" 

ESCALACAO_PREGOEIROS = DATABASE_DIR / "pregoeiros.json"
TEMPLATE_CHECKLIST = TEMPLATE_DIR / "checklist.docx"
TEMPLATE_AUTUACAO = TEMPLATE_DIR / "template_autuacao.docx"

IMAGE_PATH = DATABASE_DIR / "image"

TUCANO_PATH = DATABASE_DIR / "image" / "imagem_excel.png"
MARINHA_PATH = DATABASE_DIR / "image" / "marinha.png"
CEIMBRA_BG = DATABASE_DIR / "image" / "ceimbra_bg.png"

MENSAGEM_DIR = DATABASE_DIR / "mensagem"
ITEM_SELECIONADO_PATH = DATABASE_DIR / "item_selecionado.csv"


BG_IMAGEM_PATH = IMAGE_PATH / "bg1.png"

TABELA_UASG_DIR = DATABASE_DIR / "tabela_uasg.xlsx"
ORDENADOR_DESPESAS_DIR = DATABASE_DIR / "ordenador_despesas.xlsx"

URL_SAPIENS = 'https://sapiens.agu.gov.br/login'

PROCESSOS_JSON_PATH = DATABASE_DIR / "controle_processos.json"
TEMPLATE_PREGOEIRO = TEMPLATE_DIR / "template_cp_pregoeiro.docx"
ICONS_EDIT_DIR = ICONS_DIR  / "edit.gif"

#Diretórios do módulo Controle de Contratos
CONTRATOS_PATH = DATABASE_DIR / "Contratos.csv"
ADICIONAIS_PATH = DATABASE_DIR / "Dados_Adicionais.csv"
NOVOS_DADOS_PATH = DATABASE_DIR / "novos_dados.csv"
CONTROLE_CONTRATOS_DIR = BASE_DIR / "controle_contratos"
TEMPLATE_PORTARIA_GESTOR = CONTROLE_CONTRATOS_DIR / "template_portaria_gestor_fiscal.docx"
DATABASE_CONTRATOS = CONTROLE_CONTRATOS_DIR / "data_contratos"
SETORES_OM = DATABASE_CONTRATOS / "setores_om.xlsx"
CP_CONTRATOS_DIR = CONTROLE_CONTRATOS_DIR / "comunicacao_padronizada"


#MATRIZ DE RISCOS

MATRIZ_RISCOS = MODULES_DIR / "matriz_de_riscos"
TEMPLATE_MATRIZ_RISCOS = MATRIZ_RISCOS / "template_matriz_riscos.docx"

def get_relatorio_path():
    global RELATORIO_PATH
    # Atualize RELATORIO_PATH conforme necessário
    return RELATORIO_PATH
# pyqt6 pandas pdfplumber docxtpl num2words matplotlib pywin32 pypdf2 reportlab openpyxl fitz frontend tools selenium comtypes xlsxwriter
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

    def save_config(self, key, value):
        self.config[key] = value
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
        self.config_updated.emit(key, Path(value))
        
    def update_config(self, key, value):
        # Aqui garantimos que ambos os parâmetros sejam passados corretamente para save_config
        self.save_config(key, value)
        self.config_updated.emit(key, Path(value))

    def get_config(self, key, default_value):
        return self.config.get(key, default_value)

class EventManager(QObject):
    controle_dados_dir_updated = pyqtSignal(Path)
    pdf_dir_updated = pyqtSignal(Path)
    sicaf_dir_updated = pyqtSignal(Path)
    relatorio_path_updated = pyqtSignal(Path)
    controle_dir_updated =  pyqtSignal(Path)
    
    def __init__(self):
        super().__init__()

    def update_database_dir(self, new_file):
        global CONTROLE_DADOS
        CONTROLE_DADOS = new_file
        save_config("CONTROLE_DADOS", str(new_file))
        self.controle_dir_updated.emit(new_file)

    def update_pdf_dir(self, new_dir):
        print(f"Emitindo sinal de atualização de PDF_DIR: {new_dir}")
        self.pdf_dir_updated.emit(new_dir)

    def update_controle_dados_dir(self, new_file):
        global CONTROLE_DADOS
        if new_file != CONTROLE_DADOS:
            CONTROLE_DADOS = new_file
            save_config("CONTROLE_DADOS", str(new_file))
            self.controle_dados_dir_updated.emit(new_file)
            print(f"CONTROLE_DADOS atualizado para {new_file}")

    def update_sicaf_dir(self, new_dir):
        self.sicaf_dir_updated.emit(new_dir)

    def update_relatorio_path(self, new_dir):
        global RELATORIO_PATH
        RELATORIO_PATH = new_dir
        self.relatorio_path_updated.emit(new_dir)

# Instância global do gerenciador de eventos
global_event_manager = EventManager()
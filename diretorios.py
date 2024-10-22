#diretorios.py

from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
import json

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
CONFIG_FILE = BASE_DIR / "config.json"
CONTROLE_CONTRATOS_DADOS = DATABASE_DIR / "controle_contrato.db"
# CONTROLE_ATAS_DADOS = DATABASE_DIR / "controle_atas.db"
CONTROLE_ASS_CONTRATOS_DADOS = DATABASE_DIR / "controle_assinatura.db"
HOME_PATH = BASE_DIR / "main.py"
CONTROLE_ATAS_DIR = DATABASE_DIR / "Atas"

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

def update_template_directory(parent=None):
    """
    Função para atualizar o diretório de PASTA_TEMPLATE.
    """
    global PASTA_TEMPLATE  # Declare global aqui, antes de qualquer uso ou modificação

    new_dir = update_dir("Selecione uma nova pasta para PASTA_TEMPLATE", "PASTA_TEMPLATE", PASTA_TEMPLATE, parent)
    if new_dir != PASTA_TEMPLATE:
        PASTA_TEMPLATE = new_dir
        QMessageBox.information(parent, "Sucesso", f"Diretório PASTA_TEMPLATE atualizado para: {new_dir}")
    else:
        QMessageBox.warning(parent, "Atenção", "Nenhum diretório foi selecionado. A configuração permanece inalterada.")


# Função atualizada para escolher arquivos
def update_file_path(title, key, default_value, parent=None, file_type="All Files (*)"):
    new_file, _ = QFileDialog.getOpenFileName(parent, title, str(default_value), file_type)
    if new_file:
        save_config(key, new_file)
        return Path(new_file)
    return default_value

# Diretórios de recursos
RESOURCES_DIR = BASE_DIR / "resources"

# Diretórios de ícones
ICONS_DIR = RESOURCES_DIR / "icons"
ICONE = ICONS_DIR / "icone.ico"

# Diretórios de imagens
IMAGE_PATH = RESOURCES_DIR / "image"
ACANTO_IMAGE_PATH = IMAGE_PATH / "acanto.png"
BRASIL_IMAGE_PATH = ICONS_DIR / "brasil_2.png"
TUCANO_PATH = IMAGE_PATH / "imagem_excel.png"
MARINHA_PATH = IMAGE_PATH / "marinha.png"
CEIMBRA_BG = IMAGE_PATH / "ceimbra_bg.png"

# Diretórios de templates
TEMPLATE_DIR = RESOURCES_DIR / "template"
CP_DIR = TEMPLATE_DIR / "comunicacao_padronizada" 
TEMPLATE_CHECKLIST = TEMPLATE_DIR / "checklist.docx"
TEMPLATE_AUTUACAO = TEMPLATE_DIR / "template_autuacao.docx"
TEMPLATE_PATH = TEMPLATE_DIR / 'template_ata.docx'

# Diretórios de mensagens
MSG_DIR = RESOURCES_DIR / "msg"
MSG_DIR_IRP = MSG_DIR / "irp"
MSG_CONTRATOS_DIR = MSG_DIR / "contratos"

MODULES_DIR = BASE_DIR / "modules"  # Diretório dos módulos
PLANEJAMENTO_DIR = MODULES_DIR / "planejamento"

PASTA_TEMPLATE = Path(load_config("PASTA_TEMPLATE", RESOURCES_DIR / "template"))

TEMPLATE_PLANEJAMENTO_DIR = PLANEJAMENTO_DIR / "template"
TEMPLATE_DISPENSA_DIR = PASTA_TEMPLATE / "template_dispensa"

DISPENSA_DIR = MODULES_DIR / "dispensa_eletronica"
JSON_DISPENSA_DIR = DISPENSA_DIR / "json"
FILE_PATH_DISPENSA = DISPENSA_DIR / "dispensa_eletronica.json"

CONTROLE_DADOS = Path(load_config("CONTROLE_DADOS", BASE_DIR / "database/controle_dados.db"))
CONTROLE_DADOS_PNCP = Path(load_config("CONTROLE_DADOS_PNCP", BASE_DIR / "database/controle_pncp.db"))
# CONTROLE_ATAS_DADOS = Path(load_config("CONTROLE_ATAS", BASE_DIR / "database/controle_atas.db"))
CONTROLE_CONTRATOS_DADOS = Path(load_config("CONTROLE_CONTRATOS", BASE_DIR / "database/controle_contrato.db"))                     
CONTROLE_CONTRATACAO_DIRETAS = Path(load_config("CONTROLE_CONTRATACAO_DIRETAS", BASE_DIR / "database/controle_contratacao_direta.db"))

ETP_DIR = MODULES_DIR / "etp"
API_PATH = ETP_DIR / "config.ini"

DATABASE_DIR = Path(load_config("DATABASE_DIR", BASE_DIR / "database"))
PDF_DIR = Path(load_config("PDF_DIR", DATABASE_DIR / "pasta_homologacao"))
SICAF_DIR = Path(load_config("SICAF_DIR", DATABASE_DIR / "pasta_sicaf"))
TXT_DIR = PDF_DIR / "homolog_txt"
SICAF_TXT_DIR = SICAF_DIR / "sicaf_txt"


RELATORIO_PATH = Path(load_config("RELATORIO_PATH", DATABASE_DIR / "relatorio"))
LV_DIR = Path(load_config("LV_DIR", BASE_DIR / "Lista_de_Verificacao"))


ATA_DIR = DATABASE_DIR / "atas"
TR_VAR_DIR = DATABASE_DIR / "tr_variavel.xlsx"
ULTIMO_CONTRATO_DIR = DATABASE_DIR / "ultimo_contrato.txt"

NOMES_INVALIDOS = ['N/A', None, 'None', 'nan', 'null']

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

ESCALACAO_PREGOEIROS = DATABASE_DIR / "pregoeiros.json"


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
DADOS_MATRIZ_RISCOS = MATRIZ_RISCOS / "dados"
TABELA_BASE_MATRIZ = DADOS_MATRIZ_RISCOS / "tabela_de_riscos.xlsx"

TEMPLATE_MATRIZ_RISCOS = MATRIZ_RISCOS / "template_matriz_riscos.docx"
TEMPLATE_MATRIZ_PARTE2 = MATRIZ_RISCOS / "template_matriz_parte2.docx"
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

    def update_controle_dados_pncp_dir(self, new_file):
        global CONTROLE_DADOS_PNCP
        if new_file != CONTROLE_DADOS_PNCP:
            CONTROLE_DADOS_PNCP = new_file
            save_config("CONTROLE_DADOS_PNCP", str(new_file))
            self.controle_dados_dir_updated.emit(new_file)
            print(f"CONTROLE_DADOS_PNCP atualizado para {new_file}")

    def update_contratacoes_diretas_database_dir(self, new_file):
        global CONTROLE_CONTRATACAO_DIRETAS
        CONTROLE_CONTRATACAO_DIRETAS = new_file
        save_config("CONTROLE_DADOS", str(new_file))
        self.controle_dir_updated.emit(new_file)

    def update_atas_dados_dir(self, new_file):
        global CONTROLE_ATAS_DADOS
        if new_file != CONTROLE_ATAS_DADOS:
            CONTROLE_ATAS_DADOS = new_file
            save_config("CONTROLE_DADOS", str(new_file))
            self.controle_dados_dir_updated.emit(new_file)
            print(f"CONTROLE_DADOS atualizado para {new_file}")

    def update_contratos_dados_dir(self, new_file):
        global CONTROLE_CONTRATOS_DADOS
        if new_file != CONTROLE_CONTRATOS_DADOS:
            CONTROLE_CONTRATOS_DADOS = new_file
            save_config("CONTROLE_DADOS", str(new_file))
            self.controle_dados_dir_updated.emit(new_file)
            print(f"CONTROLE_DADOS atualizado para {new_file}")

    def update_contratacoes_diretas_dados_dir(self, new_file):
        global CONTROLE_CONTRATACAO_DIRETAS
        if new_file != CONTROLE_CONTRATACAO_DIRETAS:
            CONTROLE_CONTRATACAO_DIRETAS = new_file
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
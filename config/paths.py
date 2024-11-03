from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
CONFIG_FILE = BASE_DIR / "config.json"

# Resources
RESOURCES_DIR = BASE_DIR / "resources"
TEMPLATE_DIR = RESOURCES_DIR / "templates"
ICONS_DIR = RESOURCES_DIR / "icons"
IMAGES_DIR = RESOURCES_DIR / "images"

# Modules
MODULES_DIR = BASE_DIR / "modules"
DISPENSA_ELETRONICA_DIR = MODULES_DIR / "dispensa_eletronica"
DATA_DISPENSA_ELETRONICA_PATH = DISPENSA_ELETRONICA_DIR / "controle_contratacao_direta.db"

CONTROLE_CONTRATOS_DADOS = DATABASE_DIR / "controle_contrato.db"
CONTROLE_ASS_CONTRATOS_DADOS = DATABASE_DIR / "controle_assinatura.db"
HOME_PATH = BASE_DIR / "main.py"
CONTROLE_ATAS_DIR = DATABASE_DIR / "Atas"
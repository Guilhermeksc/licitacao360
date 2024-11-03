# modules/widgets.py

# Utilidades
from modules.utils.icon_loader import load_icons

# Importações de views
from modules.pca.pca import PCAWidget
from modules.inicio.inicio import InicioWidget
from modules.pncp.pncp import PNCPWidget
from modules.planejamento_novo.antigo_planejamento_button import PlanejamentoWidget
from modules.dispensa_eletronica.views import DispensaEletronicaWidget
from modules.atas.classe_atas import AtasWidget
from modules.contratos.classe_contratos import ContratosWidget

# Importações de models
from modules.dispensa_eletronica.models import DispensaEletronicaModel
# from modules.pca.models import PCAModel  # Exemplo para PCA
# from modules.atas.models import AtasModel  # Exemplo para Atas

# Importações de controllers
from modules.dispensa_eletronica.controller import DispensaEletronicaController

__all__ = [
    # Views
    "PCAWidget",
    "InicioWidget",
    "PNCPWidget",
    "PlanejamentoWidget",
    "DispensaEletronicaWidget",
    "AtasWidget",
    "ContratosWidget",
    
    # Models
    "DispensaEletronicaModel",
    # "PCAModel",
    # "AtasModel",

    # Controllers
    "DispensaEletronicaController",

    # Utils
    "load_icons"
]
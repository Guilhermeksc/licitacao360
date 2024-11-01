# modules/widgets.py

from modules.pca.pca import PCAWidget
from modules.inicio.inicio import InicioWidget
from modules.pncp.pncp import PNCPWidget
from modules.planejamento_novo.antigo_planejamento_button import PlanejamentoWidget
from modules.dispensa_eletronica.classe_dispensa_eletronica import DispensaEletronicaWidget
from modules.matriz_de_riscos.classe_matriz import MatrizRiscosWidget
from modules.atas.classe_atas import AtasWidget
from modules.contratos.classe_contratos import ContratosWidget

__all__ = [
    "PCAWidget",
    "InicioWidget",
    "PNCPWidget",
    "PlanejamentoWidget",
    "DispensaEletronicaWidget",
    "MatrizRiscosWidget",
    "AtasWidget",
    "ContratosWidget",
]

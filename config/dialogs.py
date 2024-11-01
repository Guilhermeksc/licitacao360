# config/dialogs.py

from config.config_database import ConfigurarDatabaseDialog
from config.config_responsaveis import AgentesResponsaveisDialog
from config.config_om import OrganizacoesDialog
from config.config_template import TemplatesDialog
from config.icon_loader import load_icons

__all__ = [
    "ConfigurarDatabaseDialog",
    "AgentesResponsaveisDialog",
    "OrganizacoesDialog",
    "TemplatesDialog",
    "load_icons",
]

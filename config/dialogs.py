# config/dialogs.py

from config.config_database import ConfigurarDatabaseDialog
from config.config_responsaveis import AgentesResponsaveisDialog
from config.config_om import OrganizacoesDialog
from config.config_template import TemplatesDialog

__all__ = [
    "ConfigurarDatabaseDialog",
    "AgentesResponsaveisDialog",
    "OrganizacoesDialog",
    "TemplatesDialog",
]

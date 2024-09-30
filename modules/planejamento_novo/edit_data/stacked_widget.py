
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import EditDataDialogUtils

class StackedWidgetManager:
    def __init__(self, parent, df_registro_selecionado):
        self.parent = parent
        self.df_registro_selecionado = df_registro_selecionado
        self.stack_manager = QStackedWidget(parent)
        self.setup_stacked_widgets()

    def setup_stacked_widgets(self):
        # Extrai dados do DataFrame selecionado
        data = EditDataDialogUtils.extract_registro_data(self.df_registro_selecionado)

        # Configura os widgets no StackedWidgetManager
        widgets = {
            "Informações": self.stacked_widget_info(data),  # Use o método correto da própria classe
            "IRP": self.stacked_widget_irp(data),
            "Demandante": self.stacked_widget_responsaveis(data),
            "Documentos": self.stacked_widget_documentos(data),
            "Anexos": self.stacked_widget_anexos(data),
            "PNCP": self.stacked_widget_pncp(data),
            "Nota Técnica": self.stacked_widget_nt(data),
        }

        for name, widget in widgets.items():
            self.stack_manager.addWidget(widget)
            widget.setObjectName(name)

    def get_stacked_widget(self):
        return self.stack_manager

    def stacked_widget_irp(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        irp_group = self.parent.create_irp_group()
        layout.addWidget(irp_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_responsaveis(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        dados_responsavel_contratacao_group = self.parent.create_dados_responsavel_contratacao_group()
        layout.addWidget(dados_responsavel_contratacao_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_documentos(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        botao_documentos = self.parent.create_gerar_documentos_group()
        sigdem_group = self.parent.create_GrupoSIGDEM()
        utilidade_group = self.parent.create_utilidades_group()
        layout.addLayout(botao_documentos)
        layout.addWidget(sigdem_group)
        layout.addLayout(utilidade_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_anexos(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        anexos_group = self.parent.create_anexos_group()
        layout.addWidget(anexos_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_pncp(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        pncp_group = self.parent.create_pncp_group()
        layout.addWidget(pncp_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_nt(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        nt_group = self.parent.create_irp_group()
        layout.addWidget(nt_group)
        frame.setLayout(layout)
        return frame

    def stacked_widget_info(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        hbox_top_layout = QHBoxLayout()
        contratacao_group_box = self.parent.create_contratacao_group(data)
        hbox_top_layout.addWidget(contratacao_group_box)
        layout_orcamentario_formulario = QVBoxLayout()
        classificacao_orcamentaria_group_box = self.parent.create_classificacao_orcamentaria_group()
        layout_orcamentario_formulario.addWidget(classificacao_orcamentaria_group_box)
        formulario_group_box = self.parent.create_frame_formulario_group()
        layout_orcamentario_formulario.addWidget(formulario_group_box)
        pncp_group_box = self.parent.create_frame_pncp()
        layout_orcamentario_formulario.addWidget(pncp_group_box)
        hbox_top_layout.addLayout(layout_orcamentario_formulario)
        layout.addLayout(hbox_top_layout)
        frame.setLayout(layout)
        return frame

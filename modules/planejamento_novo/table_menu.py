from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import pandas as pd
from modules.planejamento.editar_dados import EditarDadosDialog
from modules.planejamento.capa_edital import CapaEdital
from modules.planejamento.checklist import ChecklistWidget
from modules.planejamento.msg_planejamento import MSGIRP, MSGHomolog, MSGPublicacao
from modules.planejamento.dfd import GerarDFD, GerarManifestoIRP
from modules.planejamento.etp import GerarETP
from modules.planejamento.matriz_risco import GerarMR
from modules.planejamento.portaria_planejamento import GerarPortariaPlanejamento
from modules.planejamento.cp_agu import CPEncaminhamentoAGU
from modules.planejamento.escalar_pregoeiro import EscalarPregoeiroDialog
from modules.planejamento.autorizacao import AutorizacaoAberturaLicitacaoDialog
from modules.planejamento.edital import EditalDialog
from modules.planejamento_novo.utilidades import carregar_dados_pregao
df_uasg = pd.read_excel(TABELA_UASG_DIR)
global df_registro_selecionado
df_registro_selecionado = None

from datetime import datetime
from functools import partial

class TableMenu(QMenu):
    def __init__(self, main_app, index, model=None, config_manager=None):
        super().__init__()
        self.main_app = main_app
        self.index = index
        self.config_manager = config_manager 
        self.model = model

        # Configuração do estilo do menu
        self.setStyleSheet("""
            QMenu {
                font-size: 14px;
                font-weight: bold;
            }
        """)

        # Opções do menu principal
        actions = [
            "Editar Dados do Processo",
            "1. Autorização para Abertura de Licitação",
            "2. Portaria de Equipe de Planejamento",
            "3. Documento de Formalização de Demanda (DFD)",
        ]
        
        for actionText in actions:
            action = QAction(actionText, self)
            action.triggered.connect(partial(self.trigger_action, actionText))
            self.addAction(action)

        # Submenu para "4. Intenção de Registro de Preços (IRP)"
        submenu_irp = QMenu("4. Intenção de Registro de Preços (IRP)", self)
        submenu_irp.setStyleSheet(self.styleSheet())
        opcoes_irp = [
            ("4.1. Manifesto de IRP da OM participante", self.openDialogIRPManifesto),
            ("4.2. Mensagem de Divulgação de IRP", self.abrirDialogoIRP),
            ("4.3. Lançar o IRP", self.abrirDialogoIRP),
            ("4.4. Conformidade do IRP (Local, R$, etc)", self.abrirDialogoIRP),
        ]
        for texto, funcao in opcoes_irp:
            sub_action = QAction(texto, submenu_irp)
            sub_action.triggered.connect(partial(self.trigger_sub_action, funcao))
            submenu_irp.addAction(sub_action)
        self.addMenu(submenu_irp)

        # Adicionando as opções do menu
        actions_2 = [
            "6. Estudo Técnico Preliminar (ETP)",
            "7. Termo de Referência (TR)",
            "8. Matriz de Riscos",
        ]

        for actionText in actions_2:
            action = QAction(actionText, self)
            action.triggered.connect(partial(self.trigger_action, actionText))
            self.addAction(action)

        # Submenu "10. Edital e Anexos"
        submenu_edital = QMenu("9. Edital e Anexos", self)
        submenu_edital.setStyleSheet(self.styleSheet())
        opcoes_edital = [
            ("9.1 Edital", self.openDialogEdital),
            ("9.2 Capa do Edital", self.openDialogCapaEdital),
            ("9.3 Contrato", self.openDialogContrato),
            ("9.4 Ata de Registro de Preços", self.openDialogAtaRegistro)
        ]
        for texto, funcao in opcoes_edital:
            sub_action = QAction(texto, submenu_edital)
            sub_action.triggered.connect(partial(self.trigger_sub_action, funcao))
            submenu_edital.addAction(sub_action)
        self.addMenu(submenu_edital)

        # Adicionando mais ações principais após o submenu
        actions_3 = [
            "10. Check-list",
            "11. Nota Técnica",
            "12. CP Encaminhamento AGU",
            "13. CP Recomendações AGU",
            "14. Escalar Pregoeiro",
            "15. Mensagem de Publicação",
            "16. Mensagem de Homologação",            
            "17. Gerar Relatório de Processo",
        ]
        for actionText in actions_3:
            action = QAction(actionText, self)
            action.triggered.connect(partial(self.trigger_action, actionText))
            self.addAction(action)

    def trigger_sub_action(self, funcao):
        if self.index.isValid():
            source_index = self.model.mapToSource(self.index)
            selected_row = source_index.row()
            df_registro_selecionado = carregar_dados_pregao(selected_row, str(self.main_app.database_path))
            if not df_registro_selecionado.empty:
                funcao(df_registro_selecionado)
            else:
                QMessageBox.warning(self, "Atenção", "Dados não encontrados.")

    def trigger_action(self, actionText):
        if self.index.isValid():
            if isinstance(self.model, QSortFilterProxyModel):
                source_index = self.model.mapToSource(self.index)
            else:
                source_index = self.index
            
            selected_row = source_index.row()
            df_registro_selecionado = carregar_dados_pregao(selected_row, str(self.main_app.database_path))                                    
            if not df_registro_selecionado.empty:
                if actionText == "Editar Dados do Processo":
                    self.editar_dados(df_registro_selecionado)
                elif actionText == "1. Autorização para Abertura de Licitação":
                    self.openDialogAutorizacao(df_registro_selecionado)
                elif actionText == "2. Portaria de Equipe de Planejamento":
                    self.openDialogPortariaPlanejamento(df_registro_selecionado)
                elif actionText == "3. Documento de Formalização de Demanda (DFD)":
                    self.openDialogDFD(df_registro_selecionado)
                elif actionText == "5. Mensagem de Divulgação de IRP":
                    self.abrirDialogoIRP(df_registro_selecionado)
                elif actionText == "6. Estudo Técnico Preliminar (ETP)":
                    self.openDialogETP(df_registro_selecionado)
                elif actionText == "8. Matriz de Riscos":
                    self.openDialogMatrizRiscos(df_registro_selecionado)
                elif actionText == "12. CP Encaminhamento AGU":
                    self.openDialogEncaminhamentoAGU(df_registro_selecionado)
                elif actionText == "14. Escalar Pregoeiro":
                    self.openDialogEscalarPregoeiro(df_registro_selecionado)
                elif actionText == "15. Mensagem de Publicação":
                    self.abrirDialogoPublicacao(df_registro_selecionado)
                elif actionText == "16. Mensagem de Homologação":
                    self.abrirDialogoHomologacao(df_registro_selecionado)
                elif actionText == "10. Check-list":
                    self.openChecklistDialog(df_registro_selecionado)
            else:
                QMessageBox.warning(self, "Atenção", "Nenhum registro selecionado ou dados não encontrados.")
        else:
            QMessageBox.warning(self, "Atenção", "Nenhuma linha selecionada.")

    # No final da classe TableMenu:
    def on_get_pregoeiro(self):
        id_processo = self.df_licitacao_completo['id_processo'].iloc[0]
        dialog = EscalarPregoeiroDialog(self.df_licitacao_completo, id_processo, self)
        dialog.exec()

    def openDialogIRPManifesto(self, df_registro_selecionado):
        dialog = GerarManifestoIRP(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def abrirDialogoIRP(self, df_registro_selecionado):
        if not df_registro_selecionado.empty:
            dados = df_registro_selecionado.iloc[0].to_dict()
            dialogo = MSGIRP(dados=dados, icons_dir=str(ICONS_DIR), parent=self)
            dialogo.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum registro selecionado.")

    def abrirDialogoPublicacao(self, df_registro_selecionado):
        if not df_registro_selecionado.empty:
            dados = df_registro_selecionado.iloc[0].to_dict()
            dialogo = MSGPublicacao(dados=dados, icons_dir=str(ICONS_DIR), parent=self)
            dialogo.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum registro selecionado.")

    def abrirDialogoHomologacao(self, df_registro_selecionado):
        if not df_registro_selecionado.empty:
            dados = df_registro_selecionado.iloc[0].to_dict()
            dialogo = MSGHomolog(dados=dados, icons_dir=str(ICONS_DIR), parent=self)
            dialogo.exec()
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum registro selecionado.")

    def editar_dados(self, df_registro_selecionado):
        dialog = EditarDadosDialog(ICONS_DIR, parent=self, dados=df_registro_selecionado.iloc[0].to_dict())
        dialog.dados_atualizados.connect(self.main_app.atualizar_tabela)
        dialog.show()

    def openChecklistDialog(self, df_registro_selecionado):
        dialog = QDialog(self)
        dialog.setWindowTitle("Check-list")
        dialog.resize(950, 800)
        dialog.setStyleSheet("background-color: black; color: white;")
        
        # Instancia o ChecklistWidget e passa o DataFrame como argumento
        checklist_widget = ChecklistWidget(parent=dialog, config_manager=self.config_manager, icons_path=self.main_app.icons_dir, df_registro_selecionado=df_registro_selecionado)

        layout = QVBoxLayout(dialog)
        layout.addWidget(checklist_widget)
        dialog.exec()

    def openDialogDFD(self, df_registro_selecionado):
        dialog = GerarDFD(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogAutorizacao(self, df_registro_selecionado):
        dialog = AutorizacaoAberturaLicitacaoDialog(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogPortariaPlanejamento(self, df_registro_selecionado):
        dialog = GerarPortariaPlanejamento(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogETP(self, df_registro_selecionado):
        dialog = GerarETP(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogMatrizRiscos(self, df_registro_selecionado):
        dialog = GerarMR(main_app=self, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogEncaminhamentoAGU(self, df_registro_selecionado):
        dialog = CPEncaminhamentoAGU(main_app=self.main_app, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogCapaEdital(self, df_registro_selecionado):
        dialog = CapaEdital(main_app=self.main_app, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogEdital(self, df_registro_selecionado):
        dialog = EditalDialog(main_app=self.main_app, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()

    def openDialogContrato(self, df_registro_selecionado):
        pass

    def openDialogAtaRegistro(self, df_registro_selecionado):
        pass

    def openDialogEscalarPregoeiro(self, df_registro_selecionado):
        dialog = EscalarPregoeiroDialog(main_app=self.main_app, config_manager=self.config_manager, df_registro=df_registro_selecionado)
        dialog.exec()
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_pregao
from modules.dispensa_eletronica.configuracao_dispensa_eletronica import ConfiguracoesDispensaDialog
from diretorios import *
import pandas as pd
import sqlite3
from docxtpl import DocxTemplate
import os
import subprocess
from pathlib import Path
import win32com.client

class EditDataDialog(QDialog):
    dados_atualizados = pyqtSignal()
    title_updated = pyqtSignal(str) 

    def __init__(self, df_registro_selecionado, icons_dir, parent=None):
        super().__init__(parent)
        self.df_registro_selecionado = df_registro_selecionado
        self.ICONS_DIR = Path(icons_dir)
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)
        
        self.setWindowTitle("Editar Dados do Processo")
        self.setObjectName("EditarDadosDialog")
        self.setStyleSheet("#EditarDadosDialog { background-color: #050f41; }")
        self.setFixedSize(1530, 780)  # Define o tamanho fixo da janela
        self.layout = QVBoxLayout(self)
        
        header_widget = self.update_title_label()
        self.layout.addWidget(header_widget)

        self.selected_tooltip = "Autorização para abertura do processo de Dispensa Eletrônica"
        self.selected_button = None

        self.frame4_group_box = None

        self.initialize_gerar_pdf_button()  # Inicializar o botão aqui
        
        self.setup_frames()
        
        self.move(QPoint(0, 0))

        # Conectar o sinal ao método de atualização do título
        self.title_updated.connect(self.update_title_label)
        self.title_updated.connect(self.update_pdf_button_text)
        
        # Emitir o sinal inicial para definir o texto do botão como "Autorização"
        self.title_updated.emit("Autorização para abertura do processo de Dispensa Eletrônica")

    def extract_registro_data(self):
        # Extrai dados do registro selecionado e armazena como atributos de instância
        self.id_processo = self.df_registro_selecionado['id_processo'].iloc[0]
        self.tipo = self.df_registro_selecionado['tipo'].iloc[0]
        self.numero = self.df_registro_selecionado['numero'].iloc[0]
        self.ano = self.df_registro_selecionado['ano'].iloc[0]
        self.nup = self.df_registro_selecionado['nup'].iloc[0]
        self.objeto = self.df_registro_selecionado['objeto'].iloc[0]
        self.objeto_completo = self.df_registro_selecionado['objeto_completo'].iloc[0]
        self.valor_total = self.df_registro_selecionado['valor_total'].iloc[0]
        self.uasg = self.df_registro_selecionado['uasg'].iloc[0]
        self.orgao_responsavel = self.df_registro_selecionado['orgao_responsavel'].iloc[0]
        self.sigla_om = self.df_registro_selecionado['sigla_om'].iloc[0]
        self.setor_responsavel = self.df_registro_selecionado['setor_responsavel'].iloc[0]
        self.operador = self.df_registro_selecionado['operador'].iloc[0]
        self.data_sessao = self.df_registro_selecionado['data_sessao'].iloc[0]
        self.material_servico = self.df_registro_selecionado['material_servico'].iloc[0]
        self.link_pncp = self.df_registro_selecionado['link_pncp'].iloc[0]
        self.link_portal_marinha = self.df_registro_selecionado['link_portal_marinha'].iloc[0]
        self.situacao = self.df_registro_selecionado['situacao'].iloc[0]
        self.cod_par = self.df_registro_selecionado['cod_par'].iloc[0]
        self.justificativa = self.df_registro_selecionado['justificativa'].iloc[0]
        self.email = self.df_registro_selecionado['email'].iloc[0]
        self.telefone = self.df_registro_selecionado['telefone'].iloc[0]
        self.endereco = self.df_registro_selecionado['endereco'].iloc[0]
        self.cep = self.df_registro_selecionado['cep'].iloc[0]
        self.previsao_contratacao = self.df_registro_selecionado['previsao_contratacao'].iloc[0]
        self.comunicacao_padronizada = self.df_registro_selecionado['comunicacao_padronizada'].iloc[0]
        self.acao_interna = self.df_registro_selecionado['acao_interna'].iloc[0]
        self.fonte_recursos = self.df_registro_selecionado['fonte_recursos'].iloc[0]
        self.natureza_despesa = self.df_registro_selecionado['natureza_despesa'].iloc[0]
        self.unidade_orcamentaria = self.df_registro_selecionado['unidade_orcamentaria'].iloc[0]
        self.programa_trabalho_resuminho = self.df_registro_selecionado['programa_trabalho_resuminho'].iloc[0]
        self.comentarios = self.df_registro_selecionado['comentarios'].iloc[0]

        data = {
            'id_processo': self.id_processo,
            'tipo': self.tipo,
            'numero': self.numero,
            'ano': self.ano,
            'nup': self.nup,
            'objeto': self.objeto,
            'objeto_completo': self.objeto_completo,
            'valor_total': self.valor_total,
            'uasg': self.uasg,
            'orgao_responsavel': self.orgao_responsavel,
            'sigla_om': self.sigla_om,
            'setor_responsavel': self.setor_responsavel,
            'operador': self.operador,
            'data_sessao': self.data_sessao,
            'material_servico': self.material_servico,
            'link_pncp': self.link_pncp,
            'link_portal_marinha': self.link_portal_marinha,
            'situacao': self.situacao,
            'cod_par': self.cod_par,
            'justificativa': self.justificativa,
            'email': self.email,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'cep': self.cep,
            'previsao_contratacao': self.previsao_contratacao,
            'comunicacao_padronizada': self.comunicacao_padronizada,
            'acao_interna': self.acao_interna,
            'fonte_recursos': self.fonte_recursos,
            'natureza_despesa': self.natureza_despesa,
            'unidade_orcamentaria': self.unidade_orcamentaria,
            'programa_trabalho_resuminho': self.programa_trabalho_resuminho,
            'comentarios': self.comentarios
        }

        return data

    def update_title_label(self):
        data = self.extract_registro_data()
        html_text = (
            f"{data['tipo']} nº {data['numero']}/{data['ano']} - {data['objeto']}<br>"
            f"<span style='font-size: 20px; color: #ADD8E6;'>OM: {data['orgao_responsavel']} (UASG: {data['uasg']})</span>"
        )
        if not hasattr(self, 'titleLabel'):
            self.titleLabel = QLabel()
            self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
            self.titleLabel.setStyleSheet("color: white; font-size: 30px; font-weight: bold;")

        self.titleLabel.setText(html_text)
        # print(f"Title updated: {html_text}")

        if not hasattr(self, 'header_layout'):
            self.header_layout = QHBoxLayout()
            self.header_layout.addWidget(self.titleLabel)
            self.header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            self.add_action_buttons(self.header_layout)
            pixmap = QPixmap(str(MARINHA_PATH)).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label = QLabel()
            self.image_label.setPixmap(pixmap)
            self.header_layout.addWidget(self.image_label)

            # Define uma altura fixa para o layout do cabeçalho
            header_widget = QWidget()
            header_widget.setLayout(self.header_layout)
            header_widget.setFixedHeight(100)  # Ajuste essa altura conforme necessário
            self.header_widget = header_widget

        return self.header_widget

    def add_action_buttons(self, layout):
        icon_confirm = QIcon(str(self.ICONS_DIR / "confirm.png"))
        icon_x = QIcon(str(self.ICONS_DIR / "cancel.png"))
        icon_config = QIcon(str(self.ICONS_DIR / "gear_menu.png"))
        
        button_confirm = self.create_button("  Salvar", icon_confirm, self.save_changes, "Salvar dados", QSize(130, 50), QSize(40, 40))
        button_x = self.create_button("  Cancelar", icon_x, self.reject, "Cancelar alterações e fechar", QSize(130, 50), QSize(30, 30))
        button_config = self.create_button(" Agentes Responsáveis", icon_config, self.open_config_dialog, "Alterar local de salvamento, entre outras configurações", QSize(200, 50), QSize(30, 30))
        
        layout.addWidget(button_confirm)
        layout.addWidget(button_x)
        layout.addWidget(button_config)
        self.apply_widget_style(button_confirm)
        self.apply_widget_style(button_x)
        self.apply_widget_style(button_config)

    def create_button(self, text, icon, callback, tooltip_text, button_size=None, icon_size=None):
        btn = QPushButton(text)
        btn.setIcon(icon)
        btn.setIconSize(icon_size if icon_size else QSize(40, 40))
        if button_size:
            btn.setFixedSize(button_size)
        btn.setToolTip(tooltip_text)
        btn.clicked.connect(callback)
        return btn

    def open_config_dialog(self):
        config_dialog = ConfiguracoesDispensaDialog(self)
        config_dialog.config_updated.connect(self.update_frame4_content)
        if config_dialog.exec():
            print("Configurações salvas")
        else:
            print("Configurações canceladas")


    def setup_frames(self):
        topRow = QHBoxLayout()
        self.frame1, self.frame1_layout = self.create_frame()
        self.frame2, self.frame2_layout = self.create_frame()
        self.frame_classificacao_orcamentaria, self.frame_classificacao_orcamentaria_layout = self.create_frame()
        topRow.addWidget(self.frame1)
        topRow.addWidget(self.frame2)
        topRow.addWidget(self.frame_classificacao_orcamentaria)
        self.layout.addLayout(topRow)  # Adiciona o QHBoxLayout com os dois frames ao layout principal

        linhaDeBaixo = QVBoxLayout()
        self.frame3, self.frame3_layout = self.create_frame()
        self.frame4, self.frame4_layout = self.create_frame()
        linhaDeBaixo.addWidget(self.frame3)
        linhaDeBaixo.addWidget(self.frame4)
        self.layout.addLayout(linhaDeBaixo)  # Adiciona o QVBoxLayout com os três frames ao layout principal

        # Preenche os frames com os campos apropriados
        self.fill_frame1()
        self.fill_frame2()
        self.fill_frame_classificacao_orcamentaria()
        self.fill_frame3()
        self.fill_frame4()

    def create_frame(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)  # Mantém o estilo do frame
        frame.setFrameShadow(QFrame.Shadow.Raised)     # Mantém a sombra para destacar o frame
        frame_layout = QVBoxLayout()  # Continua usando QVBoxLayout para organizar os widgets dentro do frame
        frame.setLayout(frame_layout)  # Define o layout do frame
        return frame, frame_layout    # Retorna tanto o frame quanto seu layout

    def apply_widget_style(self, widget):
        widget.setStyleSheet("font-size: 12pt;") 

    def fill_frame1(self):
        data = self.extract_registro_data()
        # Layouts detalhados
        detalhes_layout = QHBoxLayout()

        # Situação
        situacao_group_box = QGroupBox("Situação")
        situacao_layout = QVBoxLayout()
        self.situacao_edit = QComboBox()
        self.situacao_edit.addItems(["Planejamento", "Aprovado", "Sessão Publica", "Concluído"])
        self.situacao_edit.setCurrentText(data.get('situacao', 'Planejamento'))
        self.apply_widget_style(situacao_group_box)
        self.apply_widget_style(self.situacao_edit)
        self.situacao_edit.setFixedWidth(130)
        situacao_layout.addWidget(self.situacao_edit)
        situacao_group_box.setLayout(situacao_layout)
        situacao_group_box.setFixedWidth(150)
        detalhes_layout.addWidget(situacao_group_box)
        
        # Grupo para ID do Processo
        id_group_box = QGroupBox("ID")
        id_group_layout = QVBoxLayout()
        self.id_processo_edit = QLineEdit(data['id_processo'])
        self.apply_widget_style(id_group_box)
        self.apply_widget_style(self.id_processo_edit)
        self.id_processo_edit.setReadOnly(True)
        self.id_processo_edit.setFixedWidth(100)
        id_group_layout.addWidget(self.id_processo_edit)
        id_group_box.setLayout(id_group_layout)
        id_group_box.setFixedWidth(120)
        detalhes_layout.addWidget(id_group_box)

        # Grupo para NUP
        nup_group_box = QGroupBox("NUP")
        nup_group_layout = QVBoxLayout()
        self.nup_edit = QLineEdit(data['nup'])
        self.apply_widget_style(nup_group_box)
        self.apply_widget_style(self.nup_edit)
        self.nup_edit.setReadOnly(False)
        self.nup_edit.setFixedWidth(185)
        nup_group_layout.addWidget(self.nup_edit)
        nup_group_box.setLayout(nup_group_layout)
        nup_group_box.setFixedWidth(205)
        detalhes_layout.addWidget(nup_group_box)

        # Material/Serviço
        material_group_box = QGroupBox("Material/Serviço")
        material_layout = QVBoxLayout()
        self.material_edit = QComboBox()
        self.material_edit.addItems(["Material", "Serviço"])
        self.material_edit.setCurrentText(data.get('material_servico', 'Material'))
        self.apply_widget_style(material_group_box)
        self.apply_widget_style(self.material_edit)
        self.material_edit.setFixedWidth(120)
        material_layout.addWidget(self.material_edit)
        material_group_box.setLayout(material_layout)
        material_group_box.setFixedWidth(140)
        detalhes_layout.addWidget(material_group_box)

        om_group_box = QGroupBox("OM")
        om_layout = QVBoxLayout()
        self.om_combo = QComboBox()
        self.load_sigla_om()
        self.om_combo.setCurrentText(data.get('sigla_om', ''))
        self.apply_widget_style(om_group_box)
        self.apply_widget_style(self.om_combo)
        self.om_combo.setFixedWidth(120)
        om_layout.addWidget(self.om_combo)
        om_group_box.setLayout(om_layout)
        om_group_box.setFixedWidth(140)
        detalhes_layout.addWidget(om_group_box)

        # Adicionar o layout horizontal ao layout principal do frame
        self.frame1_layout.addLayout(detalhes_layout)

        # Novo layout horizontal para Objeto e Objeto Detalhado
        objeto_layout = QHBoxLayout()

        # Grupo para Objeto com dimensão fixa
        objeto_group_box = QGroupBox("Objeto Resumido")
        objeto_group_layout = QVBoxLayout()
        self.objeto_edit = QLineEdit(data['objeto'])
        self.apply_widget_style(objeto_group_box)
        self.apply_widget_style(self.objeto_edit)
        self.objeto_edit.setReadOnly(False)
        self.objeto_edit.setFixedWidth(250)
        objeto_group_layout.addWidget(self.objeto_edit)
        objeto_group_box.setLayout(objeto_group_layout)
        objeto_group_box.setFixedWidth(270)
        objeto_layout.addWidget(objeto_group_box)

        # Detalhes adicionais para Objeto Detalhado
        objeto_det_group_box = QGroupBox("Objeto Detalhado")
        objeto_det_layout = QVBoxLayout()
        self.objeto_det_edit = QLineEdit(data['objeto_completo'])
        self.apply_widget_style(objeto_det_group_box)
        self.apply_widget_style(self.objeto_det_edit)
        self.objeto_det_edit.setReadOnly(False)
        objeto_det_layout.addWidget(self.objeto_det_edit)
        objeto_det_group_box.setLayout(objeto_det_layout)
        objeto_layout.addWidget(objeto_det_group_box)

        # Adicionar o layout horizontal de objetos ao layout principal do frame
        self.frame1_layout.addLayout(objeto_layout)

        # Novo layout horizontal para Links
        link_layout = QHBoxLayout()

        # Detalhes adicionais para Link PNCp
        link_pncp_group_box = QGroupBox("Link PNCP")
        link_pncp_layout = QVBoxLayout()
        self.link_pncp_edit = QLineEdit(data['link_pncp'])
        self.apply_widget_style(link_pncp_group_box)
        self.apply_widget_style(self.link_pncp_edit)
        self.link_pncp_edit.setReadOnly(False)
        link_pncp_layout.addWidget(self.link_pncp_edit)
        link_pncp_group_box.setLayout(link_pncp_layout)
        link_layout.addWidget(link_pncp_group_box)

        # Detalhes adicionais para Link Portal Marinha
        link_portal_group_box = QGroupBox("Link Portal Marinha")
        link_portal_layout = QVBoxLayout()
        self.link_portal_edit = QLineEdit(data['link_portal_marinha'])
        self.apply_widget_style(link_portal_group_box)
        self.apply_widget_style(self.link_portal_edit)
        self.link_portal_edit.setReadOnly(False)
        link_portal_layout.addWidget(self.link_portal_edit)
        link_portal_group_box.setLayout(link_portal_layout)
        link_portal_group_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Define o tamanho expansível
        link_layout.addWidget(link_portal_group_box)

        # Adicionar o layout horizontal de links ao layout principal do frame
        self.frame1_layout.addLayout(link_layout)
        
        detalhes_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

    def fill_frame2(self):
        data = self.extract_registro_data()

        valor_layout = QVBoxLayout()
        valor_estimado_om_layout = QHBoxLayout()
        operador_data_layout = QHBoxLayout()
        material_situacao_layout = QHBoxLayout()

        valor_estimado_group_box = QGroupBox("Valor Estimado")
        valor_layout = QVBoxLayout()
        self.valor_edit = QLineEdit(str(data.get('valor_total', '')))
        self.apply_widget_style(valor_estimado_group_box)
        self.apply_widget_style(self.valor_edit)
        valor_layout.addWidget(self.valor_edit)
        valor_estimado_group_box.setLayout(valor_layout)
        self.valor_edit.editingFinished.connect(self.ajustar_valor_monetario)

        # Adicionando valor_estimado_group_box e om_group_box ao layout horizontal
        valor_estimado_om_layout.addWidget(valor_estimado_group_box)

        # Adicionando o layout horizontal à frame2_layout
        self.frame2_layout.addLayout(valor_estimado_om_layout)

        setor_responsavel_group_box = QGroupBox("Setor Responsável pela Demanda")
        setor_responsavel_layout = QVBoxLayout()
        self.setor_responsavel_edit = QLineEdit(data.get('setor_responsavel', ''))
        self.apply_widget_style(setor_responsavel_group_box)
        self.apply_widget_style(self.setor_responsavel_edit)
        setor_responsavel_layout.addWidget(self.setor_responsavel_edit)
        setor_responsavel_group_box.setLayout(setor_responsavel_layout)
        self.frame2_layout.addWidget(setor_responsavel_group_box)

        # Operador
        operador_group_box = QGroupBox("Operador")
        operador_layout = QVBoxLayout()
        self.operador_edit = QLineEdit(data.get('operador', ''))
        self.apply_widget_style(operador_group_box)
        self.apply_widget_style(self.operador_edit)
        self.operador_edit.setFixedWidth(180)
        operador_layout.addWidget(self.operador_edit)
        operador_group_box.setLayout(operador_layout)
        operador_data_layout.addWidget(operador_group_box)
                
        # Data da Sessão
        data_sessao_group_box = QGroupBox("Data da Sessão")
        data_sessao_layout = QVBoxLayout()
        self.data_edit = QDateEdit()
        self.data_edit.setCalendarPopup(True)
        # Configura a data inicial
        data_sessao_str = data.get('data_sessao', '')
        if data_sessao_str:
            self.data_edit.setDate(QDate.fromString(data_sessao_str, "yyyy-MM-dd"))
        else:
            self.data_edit.setDate(QDate.currentDate())
        self.apply_widget_style(data_sessao_group_box)
        self.apply_widget_style(self.data_edit)
        self.data_edit.setFixedWidth(120)
        data_sessao_layout.addWidget(self.data_edit)
        data_sessao_group_box.setLayout(data_sessao_layout)
        operador_data_layout.addWidget(data_sessao_group_box)

        # Adicionar o layout horizontal ao layout principal do frame2
        self.frame2_layout.addLayout(operador_data_layout)

    def fill_frame_classificacao_orcamentaria(self):
        data = self.extract_registro_data()

        classificacao_orcamentaria_group_box = QGroupBox("Classificação Orçamentária")
        self.apply_widget_style(classificacao_orcamentaria_group_box)
        classificacao_orcamentaria_layout = QVBoxLayout()

        # Ação Interna
        acao_interna_layout = QHBoxLayout()
        acao_interna_label = QLabel("Ação Interna:")
        self.acao_interna_edit = QLineEdit(data['acao_interna'])
        self.apply_widget_style(acao_interna_label)
        self.apply_widget_style(self.acao_interna_edit)
        acao_interna_layout.addWidget(acao_interna_label)
        acao_interna_layout.addWidget(self.acao_interna_edit)
        classificacao_orcamentaria_layout.addLayout(acao_interna_layout)

        # Fonte de Recurso (FR)
        fonte_recurso_layout = QHBoxLayout()
        fonte_recurso_label = QLabel("Fonte de Recurso (FR):")
        self.fonte_recurso_edit = QLineEdit(data['fonte_recursos'])
        self.apply_widget_style(fonte_recurso_label)
        self.apply_widget_style(self.fonte_recurso_edit)
        fonte_recurso_layout.addWidget(fonte_recurso_label)
        fonte_recurso_layout.addWidget(self.fonte_recurso_edit)
        classificacao_orcamentaria_layout.addLayout(fonte_recurso_layout)

        # Natureza de Despesa (ND)
        natureza_despesa_layout = QHBoxLayout()
        natureza_despesa_label = QLabel("Natureza de Despesa (ND):")
        self.natureza_despesa_edit = QLineEdit(data['natureza_despesa'])
        self.apply_widget_style(natureza_despesa_label)
        self.apply_widget_style(self.natureza_despesa_edit)
        natureza_despesa_layout.addWidget(natureza_despesa_label)
        natureza_despesa_layout.addWidget(self.natureza_despesa_edit)
        classificacao_orcamentaria_layout.addLayout(natureza_despesa_layout)

        # Unidade Orçamentária (UO)
        unidade_orcamentaria_layout = QHBoxLayout()
        unidade_orcamentaria_label = QLabel("Unidade Orçamentária (UO):")
        self.unidade_orcamentaria_edit = QLineEdit(data['unidade_orcamentaria'])
        self.apply_widget_style(unidade_orcamentaria_label)
        self.apply_widget_style(self.unidade_orcamentaria_edit)
        unidade_orcamentaria_layout.addWidget(unidade_orcamentaria_label)
        unidade_orcamentaria_layout.addWidget(self.unidade_orcamentaria_edit)
        classificacao_orcamentaria_layout.addLayout(unidade_orcamentaria_layout)

        # PTRES
        ptres_layout = QHBoxLayout()
        ptres_label = QLabel("PTRES:")
        self.ptres_edit = QLineEdit(data['programa_trabalho_resuminho'])
        self.apply_widget_style(ptres_label)
        self.apply_widget_style(self.ptres_edit)
        ptres_layout.addWidget(ptres_label)
        ptres_layout.addWidget(self.ptres_edit)
        classificacao_orcamentaria_layout.addLayout(ptres_layout)

        classificacao_orcamentaria_group_box.setLayout(classificacao_orcamentaria_layout)

        self.frame_classificacao_orcamentaria_layout.addWidget(classificacao_orcamentaria_group_box)

    def fill_frame3(self):
        self.frame3.setObjectName("fill_frame3")
        self.frame3.setStyleSheet("#fill_frame3 { background-color: #050f41; }")
        
        button_texts = [
            "   Abertura de Processo",
            "   Documentos de Planejamento",
            "   Aviso de Dispensa Eletrônica",
            "   Lista de Verificação"
        ]
        tooltips = [
            "Autorização para abertura do processo de Dispensa Eletrônica",
            "Documentos de Planejamento (CP, DFD, TR, etc.)",
            "Aviso de dispensa eletrônica",
            "Lista de Verificação"
        ]
        icon_files = ["1.png", "2.png", "3.png", "4.png"]
        button_callbacks = [
            self.create_callback("Autorização para abertura do processo de Dispensa Eletrônica", self.gerarAutorizacao),
            self.create_callback("Documentos de Planejamento (CP, DFD, TR, etc.)", self.gerar_documentos),
            self.create_callback("Aviso de dispensa eletrônica", self.gerar_aviso),
            self.create_callback("Lista de Verificação", self.gerar_lista)
        ]

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0) 
        
        for text, tooltip, icon_file, callback in zip(button_texts, tooltips, icon_files, button_callbacks):
            icon_path = self.ICONS_DIR / icon_file
            icon = QIcon(str(icon_path))
            button = self.create_button(text, icon, callback, tooltip, QSize(350, 40))
            self.apply_button_style(button, selected=(tooltip == self.selected_tooltip))
            button_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.frame3_layout.addLayout(button_layout)
        
        # Atualizar título inicialmente
        self.update_frame4_title()
        
        # Conectar sinal para atualizar texto do botão Gerar PDF
        self.title_updated.connect(self.update_pdf_button_text)
        
        # Emitir o sinal inicial para definir o texto do botão como "Autorização"
        self.title_updated.emit("Autorização para abertura do processo de Dispensa Eletrônica")

    def create_callback(self, tooltip, function):
        def callback():
            self.selected_tooltip = tooltip
            self.update_frame4_title()
            self.update_button_styles()
            self.update_frame4_content()
            self.update_text_edit_fields(tooltip)
            self.title_updated.emit(tooltip)  # Emitir sinal quando o botão é clicado
            
            # Desconectar qualquer função anterior e conectar a função específica
            try:
                self.gerar_pdf_button.clicked.disconnect()  
            except TypeError:
                pass  # Ignorar erro se não houver conexões anteriores
            self.gerar_pdf_button.clicked.connect(function)
            
        return callback

    def update_pdf_button_text(self, tooltip):
        text_map = {
            "Autorização para abertura do processo de Dispensa Eletrônica": "Autorização",
            "Documentos de Planejamento (CP, DFD, TR, etc.)": "Documentos",
            "Aviso de dispensa eletrônica": "Aviso",
            "Lista de Verificação": "Lista de Verificação"
        }
        new_text = text_map.get(tooltip, "Gerar PDF")
        self.gerar_pdf_button.setText(f"  {new_text}")

    def update_frame4_title(self):
        if self.frame4_group_box:  # Verifica se frame4_group_box foi inicializado
            self.frame4_group_box.setTitle(self.selected_tooltip)

    def update_button_styles(self):
        for button in self.frame3.findChildren(QPushButton):
            self.apply_button_style(button, selected=(button.toolTip() == self.selected_tooltip))
                
    def apply_button_style(self, button, selected=False):
        if selected:
            button.setStyleSheet("""
                QPushButton, QPushButton::tooltip {
                    font-size: 14pt; 
                }
                QPushButton {
                    background-color: white;
                    color: black;
                    border: none;  
                    border-radius: 5px;  
                    padding: 5px;  
                }
                QPushButton:hover {  
                    background-color: #A0A4B1;
                    border: 1px solid #0078D4;  
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton, QPushButton::tooltip {
                    font-size: 14pt; 
                }
                QPushButton {
                    background-color: #2D2F33;
                    color: white;
                    border: none;  
                    border-radius: 5px;  
                    padding: 5px;  
                }
                QPushButton:hover {  
                    background-color: #A0A4B1;
                    border: 1px solid #0078D4;  
                }
            """)

    def fill_frame4(self):
        self.frame4.setObjectName("fill_frame4")
        self.frame4.setStyleSheet("#fill_frame4 { background-color: #050f41; }")

        self.frame4_group_box_layout = QHBoxLayout()
        self.frame4.setLayout(self.frame4_group_box_layout)

        self.frame4.setFixedWidth(1505)
        self.frame4.setFixedHeight(340)

        self.frame4_layout.setContentsMargins(0, 0, 0, 0)
        self.frame4_layout.addLayout(self.frame4_group_box_layout)

        self.frame4_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.update_frame4_content()

    def setupGrupoSIGDEM(self, layout_direita):
        grupoSIGDEM = QGroupBox("SIGDEM")
        grupoSIGDEM.setStyleSheet("""
                QGroupBox {
                    border: 1px solid white;
                    border-radius: 5px;
                    margin-top: 5px;
                    font: 12pt 'Arial';
                    color: white;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 3px;
                }
            """)
        layout = QVBoxLayout(grupoSIGDEM)

        # Campo "Assunto"
        labelAssunto = QLabel("No campo “Assunto”, deverá constar:")
        labelAssunto.setStyleSheet("color: white; font-size: 12pt;")
        layout.addWidget(labelAssunto)
        self.textEditAssunto = QTextEdit()
        self.textEditAssunto.setStyleSheet("font-size: 12pt;")
        self.textEditAssunto.setPlainText(f"{self.id_processo} – Autorização para Abertura de Processo de Dispensa Eletrônica")
        self.textEditAssunto.setMaximumHeight(60)

        icon_copy = QIcon(str(self.ICONS_DIR / "copy_1.png"))  # Caminho para o ícone de Word
        btnCopyAssunto = self.create_button("Copiar", icon_copy, lambda: self.copyToClipboard(self.textEditAssunto.toPlainText()), "Copiar texto para a área de transferência", QSize(80, 40), QSize(25, 25))

        layoutHAssunto = QHBoxLayout()
        layoutHAssunto.addWidget(self.textEditAssunto)
        layoutHAssunto.addWidget(btnCopyAssunto)
        layout.addLayout(layoutHAssunto)

        # Campo "Sinopse"
        labelSinopse = QLabel("No campo “Sinopse”, deverá constar:")
        labelSinopse.setStyleSheet("color: white; font-size: 12pt;")
        layout.addWidget(labelSinopse)
        self.textEditSinopse = QTextEdit()
        self.textEditSinopse.setStyleSheet("font-size: 12pt;")
        descricao_servico = "aquisição de" if self.material_servico == "Material" else "contratação de empresa especializada em"
        sinopse_text = (f"Termo de Abertura referente à {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
                        f"Processo Administrativo NUP: {self.nup}\n"
                        f"Setor Demandante: {self.setor_responsavel}")
        self.textEditSinopse.setPlainText(sinopse_text)
        self.textEditSinopse.setMaximumHeight(140)
        btnCopySinopse = self.create_button("Copiar", icon_copy, lambda: self.copyToClipboard(self.textEditSinopse.toPlainText()), "Copiar texto para a área de transferência", QSize(80, 40), QSize(25, 25))
        layoutHSinopse = QHBoxLayout()
        layoutHSinopse.addWidget(self.textEditSinopse)
        layoutHSinopse.addWidget(btnCopySinopse)
        layout.addLayout(layoutHSinopse)

        # Campo "Temporalidade"
        labelTemporalidade = QLabel("Temporalidade: 004")
        labelTemporalidade.setStyleSheet("color: white; font-size: 12pt;")
        layout.addWidget(labelTemporalidade)  

        labelTramitacao = QLabel("Tramitação: 33>30>02>SEC01>01>30>Setor Demandante")
        labelTramitacao.setStyleSheet("color: white; font-size: 12pt;")
        layout.addWidget(labelTramitacao)

        layout_direita.addWidget(grupoSIGDEM)

    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QToolTip.showText(QCursor.pos(), "Texto copiado para a área de transferência.", msecShowTime=1500)

    def update_frame4_content(self):
        for i in reversed(range(self.frame4_group_box_layout.count())):
            widget_to_remove = self.frame4_group_box_layout.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.setParent(None)

        layout_esquerda = QVBoxLayout()
        layout_centro = QVBoxLayout()
        layout_direita = QVBoxLayout()

        esquerda_widget = QWidget()
        centro_widget = QWidget()
        direita_widget = QWidget()

        esquerda_widget.setLayout(layout_esquerda)
        centro_widget.setLayout(layout_centro)
        direita_widget.setLayout(layout_direita)

        esquerda_widget.setFixedWidth(320)
        centro_widget.setFixedWidth(600)

        self.frame4_group_box_layout.addWidget(esquerda_widget)
        self.frame4_group_box_layout.addWidget(centro_widget)
        self.frame4_group_box_layout.addWidget(direita_widget)

        if self.selected_tooltip == "Autorização para abertura do processo de Dispensa Eletrônica":
            self.add_common_widgets(layout_esquerda)
            # Adiciona o texto central específico
            authorization_text = """
                Instruções<br><br>
                Após aprovado pelo Ordenador de Despesas a situação deverá ser alterada de "Planejamento" para <span style="color: red;">"Aprovado"</span><br><br>
                Após publicado no PNCP a situação deverá ser alterada de "Aprovado" para <span style="color: red;">"Sessão Pública"</span><br><br>
                Após a homologação situação deverá ser alterada de "Sessão Pública" para <span style="color: red;">"Homologado"</span><br><br>
                Após a o empenho a situação deverá ser alterada de "Homologado" para <span style="color: red;">"Concluído"</span>
            """
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setHtml(authorization_text)
            text_edit.setStyleSheet("background-color: #050f41; color: white; font-size: 12pt;")
            layout_centro.addWidget(text_edit)
        elif self.selected_tooltip == "Documentos de Planejamento (CP, DFD, TR, etc.)":
            self.add_common_widgets(layout_esquerda)
            text_edit = QTextEdit()
            text_edit.setStyleSheet("color: white; font-size: 14pt; background-color: #1e2a56;")
            layout_centro.addWidget(text_edit)
        elif self.selected_tooltip == "Aviso de dispensa eletrônica":
            self.add_common_widgets(layout_esquerda)
        elif self.selected_tooltip == "Lista de Verificação":
            self.add_common_widgets(layout_esquerda)

        self.carregarAgentesResponsaveis()
        self.setupGrupoSIGDEM(layout_direita)

    def carregarAgentesResponsaveis(self):
        try:
            print("Tentando conectar ao banco de dados...")
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_agentes_responsaveis'")
                if cursor.fetchone() is None:
                    raise Exception("A tabela 'controle_agentes_responsaveis' não existe no banco de dados. Configure os Ordenadores de Despesa no Módulo 'Configurações'.")

                print("Tabela 'controle_agentes_responsaveis' encontrada. Carregando dados...")
                # Carregar dados para comboboxes específicos
                self.carregarDadosCombo(conn, cursor, "Ordenador de Despesa%", self.ordenador_combo)
                self.carregarDadosCombo(conn, cursor, "Agente Fiscal%", self.agente_fiscal_combo)
                self.carregarDadosCombo(conn, cursor, "Gerente de Crédito%", self.gerente_credito_combo)
                # Carregar dados para o combobox de responsável pela demanda, excluindo os outros cargos
                self.carregarDadosCombo(conn, cursor, "NOT LIKE", self.responsavel_demanda_combo)

                # Print para verificar o valor corrente e dados associados ao item selecionado
                current_text = self.ordenador_combo.currentText()
                current_data = self.ordenador_combo.currentData(Qt.ItemDataRole.UserRole)
                print(f"Current ordenador_combo Text: {current_text}")
                print(f"Current ordenador_combo Data: {current_data}")

        except Exception as e:
            print(f"Erro ao carregar Ordenadores de Despesas: {e}")

    def carregarDadosCombo(self, conn, cursor, funcao_like, combo_widget):
        if "NOT LIKE" in funcao_like:
            sql_query = """
                SELECT nome, posto, funcao FROM controle_agentes_responsaveis
                WHERE funcao NOT LIKE 'Ordenador de Despesa%' AND
                    funcao NOT LIKE 'Agente Fiscal%' AND
                    funcao NOT LIKE 'Gerente de Crédito%'
            """
        else:
            sql_query = f"SELECT nome, posto, funcao FROM controle_agentes_responsaveis WHERE funcao LIKE '{funcao_like}'"
        
        agentes_df = pd.read_sql_query(sql_query, conn)
        for index, row in agentes_df.iterrows():
            texto_display = f"{row['nome']}\n{row['posto']}\n{row['funcao']}"
            # Armazena um dicionário no UserRole para cada item adicionado ao ComboBox  
            data_dict = {'nome': row['nome'], 'posto': row['posto'], 'funcao': row['funcao']}
            combo_widget.addItem(row['nome'], data_dict)

    def update_text_edit_fields(self, tooltip):
        descricao_servico = "aquisição de" if self.material_servico == "Material" else "contratação de empresa especializada em"
        sinopse_text_map = {
            "Autorização para abertura do processo de Dispensa Eletrônica": (
                f"Termo de Abertura referente à {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
                f"Processo Administrativo NUP: {self.nup}\n"
                f"Setor Demandante: {self.setor_responsavel}"
            ),
            "Documentos de Planejamento (CP, DFD, TR, etc.)": (
                f"Documentos de Planejamento referente à {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
                f"Processo Administrativo NUP: {self.nup}\n"
                f"Setor Demandante: {self.setor_responsavel}"
            ),
            "Aviso de dispensa eletrônica": (
                f"Aviso referente à {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
                f"Processo Administrativo NUP: {self.nup}\n"
                f"Setor Demandante: {self.setor_responsavel}"
            ),
            "Lista de Verificação": (
                f"Lista de Verificação referente à {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
                f"Processo Administrativo NUP: {self.nup}\n"
                f"Setor Demandante: {self.setor_responsavel}"
            )
        }
        assunto_text_map = {
            "Autorização para abertura do processo de Dispensa Eletrônica": f"{self.id_processo} – Autorização para Abertura de Processo de Dispensa Eletrônica",
            "Documentos de Planejamento (CP, DFD, TR, etc.)": f"{self.id_processo} – Documentos de Planejamento",
            "Aviso de dispensa eletrônica": f"{self.id_processo} – Aviso de Dispensa Eletrônica",
            "Lista de Verificação": f"{self.id_processo} – Lista de Verificação"
        }

        self.textEditAssunto.setPlainText(assunto_text_map.get(tooltip, ""))
        self.textEditSinopse.setPlainText(sinopse_text_map.get(tooltip, ""))

    def add_common_widgets(self, parent_layout):
        def create_group_box_with_combo(title):
            group_box = QGroupBox(title)
            layout = QVBoxLayout()
            combo = QComboBox()
            combo.setFixedHeight(30)
            # Criando e aplicando o delegate
            delegate = ItemDelegate()
            combo.setItemDelegate(delegate)
            
            # Aplicar folha de estilo CSS ao QComboBox
            combo.setStyleSheet("""
                QComboBox {
                    background-color: white; 
                    border: 1px solid gray;
                    border-radius: 3px;     
                    padding: 1px 18px 1px 3px; 
  
                }
            """)
            layout.addWidget(combo)
            group_box.setLayout(layout)
            group_box.setFixedHeight(60)
            group_box.setFixedWidth(300)

            # Aplicar folha de estilo CSS ao QGroupBox
            group_box.setStyleSheet("""
                QGroupBox {
                    border: 1px solid white;
                    border-radius: 5px;
                    margin-top: 5px;
                    font: 12pt 'Arial';
                    color: white;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 3px;
                }
            """)
            return group_box, combo

        # Criar e adicionar comboboxes com estilos personalizados
        ordenador_group_box, self.ordenador_combo = create_group_box_with_combo("Ordenador de Despesas")
        parent_layout.addWidget(ordenador_group_box)

        agente_fiscal_group_box, self.agente_fiscal_combo = create_group_box_with_combo("Agente Fiscal")
        parent_layout.addWidget(agente_fiscal_group_box)

        gerente_credito_group_box, self.gerente_credito_combo = create_group_box_with_combo("Gerente de Credito da Ação Interna")
        parent_layout.addWidget(gerente_credito_group_box)

        responsavel_demanda_group_box, self.responsavel_demanda_combo = create_group_box_with_combo("Responsável pela Demanda")
        parent_layout.addWidget(responsavel_demanda_group_box)

        # Layout para centralizar o botão
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.gerar_pdf_button, alignment=Qt.AlignmentFlag.AlignCenter)
        parent_layout.addLayout(button_layout)

    def initialize_gerar_pdf_button(self):
        icon_pdf = QIcon(str(self.ICONS_DIR / "pdf.png"))
        self.gerar_pdf_button = self.create_button("  Autorização", icon_pdf, self.gerarAutorizacao, "Gerar PDF", QSize(300, 65), QSize(50, 50))
        self.apply_dark_red_style(self.gerar_pdf_button)

    def apply_dark_red_style(self, button):
        button.setStyleSheet("""
            QPushButton, QPushButton::tooltip {
                font-size: 16pt;
                font-weight: bold; 
            }
            QPushButton {
                background-color: #8B0000;
                color: white;
                border: none;  
                border-radius: 5px;  
                padding: 5px;  
            }
            QPushButton:hover {  
                background-color: #A52A2A; 
                border: 1px solid #FF6347;
            }
        """)

    def gerarDocumento(self):
        print("Gerando autorização...")

    def gerar_documentos(self):
        print("Gerando documentos...")

    def gerar_aviso(self):
        print("Gerando aviso...")

    def gerar_lista(self):
        print("Gerando lista de verificação...")

    def teste(self):
        print("Teste")

    def add_date_edit(self, layout, label_text, data_key):
        label = QLabel(label_text)
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_str = self.df_registro_selecionado.get(data_key, "")
        date = QDate.fromString(date_str, "yyyy-MM-dd") if date_str else QDate.currentDate()
        date_edit.setDate(date)
        layout.addWidget(label)
        layout.addWidget(date_edit)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        self.layout.addLayout(buttons_layout)  # Consistentemente adiciona os botões usando um layout

    def load_sigla_om(self):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT sigla_om FROM controle_om ORDER BY sigla_om")
                items = [row[0] for row in cursor.fetchall()]
                self.om_combo.addItems(items)
                self.om_combo.currentTextChanged.connect(self.on_om_changed)
                print(f"Loaded sigla_om items: {items}")  # Print para verificar os itens carregados
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao carregar OM: {e}")
            print(f"Error loading sigla_om: {e}")  # Print para verificar erros

    def on_om_changed(self):
        selected_om = self.om_combo.currentText()
        print(f"OM changed to: {selected_om}")
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uasg, orgao_responsavel FROM controle_om WHERE sigla_om = ?", (selected_om,))
            result = cursor.fetchone()
            if result:
                uasg, orgao_responsavel = result
                index = self.df_registro_selecionado.index[0]
                self.df_registro_selecionado.loc[index, 'uasg'] = uasg
                self.df_registro_selecionado.loc[index, 'orgao_responsavel'] = orgao_responsavel
                print(f"Updated DataFrame: uasg={uasg}, orgao_responsavel={orgao_responsavel}")
                self.title_updated.emit(f"{orgao_responsavel} (UASG: {uasg})")  # Emite o sinal com o novo título
                            
    def save_changes(self):
        data = {
            'nup': self.nup_edit.text().strip(),
            'objeto': self.objeto_edit.text().strip(),
            'objeto_completo': self.objeto_det_edit.text().strip(),
            'valor_total': self.valor_edit.text().strip(),
            'setor_responsavel': self.setor_responsavel_edit.text().strip(),
            'operador': self.operador_edit.text().strip(),
            'data_sessao': self.data_edit.date().toString("yyyy-MM-dd"),
            'link_pncp': self.link_pncp_edit.text().strip(),
            'link_portal_marinha': self.link_portal_edit.text().strip(),
            'material_servico': self.material_edit.currentText(),
            'situacao': self.situacao_edit.currentText(),
            'sigla_om': self.om_combo.currentText(),
            'uasg': self.df_registro_selecionado.loc[self.df_registro_selecionado.index[0], 'uasg'],  # Inclui uasg
            'orgao_responsavel': self.df_registro_selecionado.loc[self.df_registro_selecionado.index[0], 'orgao_responsavel'],
            'acao_interna': self.acao_interna_edit.text().strip(),
            'fonte_recursos': self.fonte_recurso_edit.text().strip(),
            'natureza_despesa': self.natureza_despesa_edit.text().strip(),
            'unidade_orcamentaria': self.unidade_orcamentaria_edit.text().strip(),
            'programa_trabalho_resuminho': self.ptres_edit.text().strip(),
        }

        with self.database_manager as connection:
            cursor = connection.cursor()
            set_part = ', '.join([f"{key} = ?" for key in data.keys()])
            valores = list(data.values())
            valores.append(self.df_registro_selecionado['id_processo'].iloc[0])

            query = f"UPDATE controle_dispensas SET {set_part} WHERE id_processo = ?"
            cursor.execute(query, valores)
            connection.commit()

        self.dados_atualizados.emit()
        QMessageBox.information(self, "Atualização", "As alterações foram salvas com sucesso.")
        # Remover o fechamento do diálogo para mantê-lo aberto
        # self.accept()

    def formatar_brl(self, valor):
        try:
            if valor is None or pd.isna(valor) or valor == '':
                return "R$ 0,00"  # Retorna string formatada se não for um valor válido
            valor_formatado = f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return valor_formatado
        except Exception as e:
            print(f"Erro ao formatar valor: {valor} - Erro: {str(e)}")
            return "R$ 0,00"

    def ajustar_valor_monetario(self):
        valor_texto = self.valor_edit.text().replace('R$', '').strip()
        try:
            valor_float = float(valor_texto.replace('.', '').replace(',', '.'))
            valor_formatado = self.formatar_brl(valor_float)
            self.valor_edit.setText(valor_formatado)
        except ValueError as e:
            print(f"Erro ao converter valor: {valor_texto} - Erro: {str(e)}")
            QMessageBox.warning(self, "Valor Inválido", "Por favor, informe um valor numérico válido.")
            self.valor_edit.setText("R$ 0,00")  # Define um valor padrão

    def gerarAutorizacao(self):
        # Gera o documento no formato DOCX e obtém o caminho do arquivo gerado
        docx_path = self.gerarDocumento("docx")
        
        # Verifica se um caminho foi retornado e, em caso afirmativo, abre o documento
        if docx_path:
            self.abrirDocumento(docx_path)
        
        return docx_path
    
    def abrirDocumento(self, docx_path):
        try:
            # Convertendo o caminho para um objeto Path se ainda não for
            docx_path = Path(docx_path) if not isinstance(docx_path, Path) else docx_path
            
            # Definindo o caminho do arquivo PDF usando with_suffix
            pdf_path = docx_path.with_suffix('.pdf')

            # Convertendo DOCX para PDF usando o Microsoft Word
            word = win32com.client.Dispatch("Word.Application")
            doc = word.Documents.Open(str(docx_path))
            doc.SaveAs(str(pdf_path), FileFormat=17)  # 17 é o valor do formato PDF
            doc.Close()
            word.Quit()

            # Verificando se o arquivo PDF foi criado com sucesso
            if pdf_path.exists():
                # Abrindo o PDF gerado
                os.startfile(pdf_path)  # 'startfile' abre o arquivo com o aplicativo padrão no Windows
                print(f"Documento PDF aberto: {pdf_path}")
            else:
                raise FileNotFoundError(f"O arquivo PDF não foi criado: {pdf_path}")

        except Exception as e:
            print(f"Erro ao abrir ou converter o documento: {e}")
            QMessageBox.warning(None, "Erro", f"Erro ao abrir ou converter o documento: {e}")

    def gerarDocumento(self, tipo="docx"):
        if self.df_registro_selecionado is None:
            QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
            print("Nenhum registro selecionado.")
            return

        try:
            # Define os caminhos para salvar o documento
            template_filename = f"template_autorizacao_dispensa.{tipo}"
            template_path = TEMPLATE_DISPENSA_DIR / template_filename
            if not template_path.exists():
                QMessageBox.warning(None, "Erro de Template", f"O arquivo de template não foi encontrado: {template_path}")                
                print(f"O arquivo de template não foi encontrado: {template_path}")
                return
            nome_pasta = f"{self.df_registro_selecionado['id_processo'].iloc[0].replace('/', '-')} - {self.df_registro_selecionado['objeto'].iloc[0]}"
            pasta_base = Path.home() / 'Desktop' / nome_pasta / "1. Autorizacao para abertura de Processo Administrativo"
            
            print(f"Caminho do template: {template_path}")
            print(f"Pasta base para salvar documentos: {pasta_base}")

            # Cria as pastas se não existirem
            pasta_base.mkdir(parents=True, exist_ok=True)  # Cria a pasta se não existir
            save_path = pasta_base / f"{self.df_registro_selecionado['id_processo'].iloc[0].replace('/', '-')} - Autorizacao para abertura de Processo Administrativo.{tipo}"
            print(f"Caminho completo para salvar o documento: {save_path}")
            doc = DocxTemplate(str(template_path))
            context = self.df_registro_selecionado.to_dict('records')[0]
            descricao_servico = "aquisição de" if self.material_servico == "Material" else "contratação de empresa especializada em"
            ordenador_de_despesas = self.ordenador_combo.currentData(Qt.ItemDataRole.UserRole)

            context.update({
                'descricao_servico': descricao_servico,
                'ordenador_de_despesas': f"{ordenador_de_despesas['nome']}\n{ordenador_de_despesas['posto']}\n{ordenador_de_despesas['funcao']}"

            })

            print("Contexto para renderização:", context)
            doc.render(context)
            doc.save(str(save_path))
            return str(save_path)

        except Exception as e:
            QMessageBox.warning(None, "Erro", f"Erro ao gerar ou salvar o documento: {e}")
            print(f"Erro ao gerar ou salvar o documento: {e}")

class ItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()

        # Aplica um estilo de fundo diferente dependendo do estado do item
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor(200, 200, 200))  # Cor de seleção
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(220, 220, 220))  # Cor ao passar o mouse
        else:
            painter.fillRect(option.rect, QColor(255, 255, 255))  # Cor padrão

        text_option = QTextOption(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        text_option.setWrapMode(QTextOption.WrapMode.WordWrap)
        painter.setPen(QPen(Qt.GlobalColor.black))
        rect = QRectF(option.rect.adjusted(5, 0, -5, 0))
        
        data = index.data(Qt.ItemDataRole.UserRole)
        # Converte o dicionário em uma string formatada
        display_text = f"{data['nome']}\n{data['posto']}\n{data['funcao']}" if isinstance(data, dict) else "Informação não disponível"
        
        painter.drawText(rect, display_text, text_option)

        painter.restore()

    def sizeHint(self, option, index):
        # Customiza o tamanho do item baseado no conteúdo
        size = super().sizeHint(option, index)
        size.setHeight(60)  # Ajusta a altura para acomodar o texto multi-linha
        return size

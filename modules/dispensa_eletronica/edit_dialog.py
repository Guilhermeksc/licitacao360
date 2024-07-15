from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_pregao
from modules.dispensa_eletronica.configuracao_dispensa_eletronica import ConfiguracoesDispensaDialog
from modules.dispensa_eletronica.documentos_cp_dfd_tr import DocumentDetailsWidget, PDFAddDialog, ConsolidarDocumentos
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
        self.document_details_widget = None
        self.consolidador = ConsolidarDocumentos(df_registro_selecionado)
        self.ICONS_DIR = Path(icons_dir)
        self.database_path = Path(load_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))
        self.database_manager = DatabaseManager(self.database_path)

        self.setWindowTitle("Editar Dados do Processo")
        self.setObjectName("EditarDadosDialog")
        self.setStyleSheet("#EditarDadosDialog { background-color: #050f41; }")
        self.setFixedSize(1530, 780)  # Define o tamanho fixo da janela
        self.layout = QVBoxLayout(self)

        self.painel_layout = QVBoxLayout()  # Inicializa painel_layout antes de setup_frames

        self.setup_frames()

        self.move(QPoint(0, 0))
        # Conecte o sinal title_updated ao método update_title_label
        self.title_updated.connect(self.update_title_label_text)

    def create_frame(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)  # Mantém o estilo do frame
        frame.setFrameShadow(QFrame.Shadow.Raised)     # Mantém a sombra para destacar o frame
        frame_layout = QVBoxLayout()  # Continua usando QVBoxLayout para organizar os widgets dentro do frame
        frame.setLayout(frame_layout)  # Define o layout do frame
        return frame, frame_layout    # Retorna tanto o frame quanto seu layout

    def create_combo_box(self, current_text, items, fixed_width):
        combo_box = QComboBox()
        combo_box.addItems(items)
        combo_box.setCurrentText(current_text)
        combo_box.setFixedWidth(fixed_width)
        self.apply_widget_style(combo_box)
        return combo_box

    def create_layout(self, label_text, widget, fixed_width=None):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        self.apply_widget_style(label)
        if fixed_width:
            widget.setFixedWidth(fixed_width)
        self.apply_widget_style(widget)
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout
    
    def apply_widget_style(self, widget):
        widget.setStyleSheet("font-size: 12pt;") 

    def apply_widget_style_11(self, widget):
        widget.setStyleSheet("font-size: 11pt;") 

    def apply_widget_style_10(self, widget):
        widget.setStyleSheet("font-size: 10pt;") 

    def setup_frames(self):
        layout_principal = QVBoxLayout()
        header_widget = self.update_title_label()
        layout_principal.addWidget(header_widget)
        
        self.frame_secundario, self.frame_secundario_layout = self.create_frame()
        layout_principal.addWidget(self.frame_secundario)
        self.layout.addLayout(layout_principal)

        self.fill_frame_dados_secundarios()

    def create_contratacao_group(self, data):
        contratacao_group_box = QGroupBox("Contratação")
        self.apply_widget_style(contratacao_group_box)
        contratacao_group_box.setFixedWidth(340)  
        contratacao_layout = QVBoxLayout()
        contratacao_layout.setSpacing(1)

        # Configuração Situação
        situacao_layout = QHBoxLayout()     
        situacao_label = QLabel("Situação:")
        self.apply_widget_style(situacao_label)
        self.situacao_edit = self.create_combo_box(data.get('situacao', 'Planejamento'), ["Planejamento", "Aprovado", "Sessão Publica", "Concluído"], 150)
        situacao_layout.addWidget(situacao_label)
        situacao_layout.addWidget(self.situacao_edit)        
        contratacao_layout.addLayout(situacao_layout)
        
        # Adiciona outros layouts ao layout de contratação
        self.nup_edit = QLineEdit(data['nup'])
        contratacao_layout.addLayout(self.create_layout("NUP:", self.nup_edit))

        # Configuração de Material/Serviço na mesma linha
        material_layout = QHBoxLayout()
        material_label = QLabel("Material/Serviço:")
        self.apply_widget_style(material_label)
        self.material_edit = self.create_combo_box(data.get('material_servico', 'Material'), ["Material", "Serviço"], 150)
        material_layout.addWidget(material_label)
        material_layout.addWidget(self.material_edit)
        contratacao_layout.addLayout(material_layout)

        # Objeto
        self.objeto_edit = QLineEdit(data['objeto'])
        contratacao_layout.addLayout(self.create_layout("Objeto:", self.objeto_edit))

        # Configuração da Data da Sessão na mesma linha
        data_layout = QHBoxLayout()
        data_label = QLabel("Data da Sessão:")
        self.apply_widget_style(data_label)
        self.data_edit = QDateEdit()
        self.data_edit.setFixedWidth(150)
        self.data_edit.setCalendarPopup(True)
        data_sessao_str = data.get('data_sessao', '')
        if data_sessao_str:
            self.data_edit.setDate(QDate.fromString(data_sessao_str, "yyyy-MM-dd"))
        else:
            self.data_edit.setDate(QDate.currentDate())
        data_layout.addWidget(data_label)
        data_layout.addWidget(self.data_edit)
        contratacao_layout.addLayout(data_layout)

        # Vigência
        self.vigencia_edit = QLineEdit(data.get('vigencia', '12 (doze) meses'))
        contratacao_layout.addLayout(self.create_layout("Vigência:", self.vigencia_edit))

        # Configuração de Critério de Julgamento na mesma linha
        criterio_layout = QHBoxLayout()
        criterio_label = QLabel("Critério Julgamento:")
        self.apply_widget_style(criterio_label)
        self.criterio_edit = self.create_combo_box(data.get('criterio_julgamento', 'Menor Preço'), ["Menor Preço", "Maior Desconto"], 150)
        criterio_layout.addWidget(criterio_label)
        criterio_layout.addWidget(self.criterio_edit)
        contratacao_layout.addLayout(criterio_layout)

        # Configuração de Com Disputa na mesma linha
        disputa_layout = QHBoxLayout()
        disputa_label = QLabel("Com disputa?")
        self.apply_widget_style(disputa_label)
        self.radio_disputa_sim = QRadioButton("Sim")
        self.radio_disputa_nao = QRadioButton("Não")
        com_disputa_value = data.get('com_disputa', 'Não')
        self.radio_disputa_sim.setChecked(com_disputa_value == 'Sim')
        self.radio_disputa_nao.setChecked(com_disputa_value != 'Sim')
        disputa_layout.addWidget(disputa_label)
        disputa_layout.addWidget(self.radio_disputa_sim)
        disputa_layout.addWidget(self.radio_disputa_nao)
        contratacao_layout.addLayout(disputa_layout)

        # Pesquisa de Preço Concomitante
        pesquisa_concomitante_layout = QHBoxLayout()
        pesquisa_concomitante_label = QLabel("Pesquisa Concomitante?")
        self.apply_widget_style(pesquisa_concomitante_label)
        self.radio_pesquisa_sim = QRadioButton("Sim")
        self.radio_pesquisa_nao = QRadioButton("Não")
        pesquisa_preco_value = data.get('pesquisa_preco', 'Não')
        self.radio_pesquisa_sim.setChecked(pesquisa_preco_value == 'Sim')
        self.radio_pesquisa_nao.setChecked(pesquisa_preco_value != 'Sim')
        pesquisa_concomitante_layout.addWidget(pesquisa_concomitante_label)
        pesquisa_concomitante_layout.addWidget(self.radio_pesquisa_sim)
        pesquisa_concomitante_layout.addWidget(self.radio_pesquisa_nao)
        contratacao_layout.addLayout(pesquisa_concomitante_layout)

        contratacao_group_box.setLayout(contratacao_layout)
        return contratacao_group_box

    def fill_frame_dados_secundarios(self):
        data = self.extract_registro_data()
        detalhes_layout = QVBoxLayout()

        hbox_top_layout = QHBoxLayout()  # Layout horizontal para os três QGroupBox
        # Preenche os QGroupBox e os adiciona ao layout horizontal
        contratacao_group_box = self.create_contratacao_group(data)        
        dados_do_setor_responsavel_contratacao_group_box = self.fill_frame_dados_do_setor_resposavel_contratacao()
        sigdem_group = self.setupGrupoSIGDEM()
        agentes_responsaveis_group = self.fill_frame_agentes_responsaveis()

        hbox_top_layout.addWidget(contratacao_group_box)
        hbox_top_layout.addWidget(dados_do_setor_responsavel_contratacao_group_box)
        hbox_top_layout.addWidget(sigdem_group)
        hbox_top_layout.addWidget(agentes_responsaveis_group)

        # Adiciona o layout horizontal ao layout principal
        detalhes_layout.addLayout(hbox_top_layout)

        hbox_down_layout = QHBoxLayout()  # Layout horizontal para os três QGroupBox
        # Preenche os QGroupBox e os adiciona ao layout horizontal
        classificacao_orcamentaria_group_box = self.fill_frame_classificacao_orcamentaria()
        comunicacao_padronizada_group = self.fill_frame_comunicacao_padronizada()
        lista_verificacao_group = self.fill_frame_criar_documentos()
        formulario_group = self.fill_frame_formulario()

        hbox_down_layout.addWidget(classificacao_orcamentaria_group_box)
        hbox_down_layout.addWidget(comunicacao_padronizada_group)
        hbox_down_layout.addWidget(lista_verificacao_group)
        hbox_down_layout.addWidget(formulario_group)

        # Adiciona o layout horizontal ao layout principal
        detalhes_layout.addLayout(hbox_down_layout)

        self.frame_secundario_layout.addLayout(detalhes_layout)

    def fill_frame_comunicacao_padronizada(self):
        data = self.extract_registro_data()

        # GroupBox Comunicação Padronizada (CP)
        comunicacao_padronizada_group_box = QGroupBox("Comunicação Padronizada (CP)")
        self.apply_widget_style(comunicacao_padronizada_group_box)
        
        comunicacao_padronizada_layout = QVBoxLayout()
        comunicacao_padronizada_layout.setSpacing(1)
        
        # Campo Comunicação Padronizada nº
        self.cp_edit = QLineEdit(data.get('comunicacao_padronizada', ''))
        cp_layout = self.create_layout("CP nº", self.cp_edit)
        
        icon_anexo = QIcon(str(self.ICONS_DIR / "anexar.png"))
        add_pdf_button = self.create_button(
            " Selecionar Anexos", 
            icon_anexo, 
            self.add_pdf_to_merger, 
            "Selecionar arquivos PDFs para aplicar o Merge",
            QSize(220, 40), QSize(30, 30)
        )
        
        self.apply_widget_style(add_pdf_button)
        cp_layout.addWidget(add_pdf_button)
        cp_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))  
        
        # Campo Do: Responsável
        self.responsavel_edit = QLineEdit(data.get('do_resposavel', 'Responsável pela Demanda'))
        responsavel_layout = self.create_layout("Do:", self.responsavel_edit)
        
        # Campo Ao: Encarregado de Obtenção
        self.encarregado_obtencao_edit = QLineEdit(data.get('ao_responsavel', 'Encarregado da Divisão de Obtenção'))
        encarregado_obtencao_layout = self.create_layout("Ao:", self.encarregado_obtencao_edit)

        self.anexos_edit = QTextEdit("A) DFD\nB) TR\nC) Adequação Orçamentária")
        anexos_edit_layout = self.create_layout("Anexos:", self.anexos_edit)

        # Adiciona os layouts dos campos ao layout principal
        comunicacao_padronizada_layout.addLayout(cp_layout)
        comunicacao_padronizada_layout.addLayout(responsavel_layout)
        comunicacao_padronizada_layout.addLayout(encarregado_obtencao_layout)
        comunicacao_padronizada_layout.addLayout(anexos_edit_layout)
        
        comunicacao_padronizada_group_box.setLayout(comunicacao_padronizada_layout)
        
        # Layout Link PNCP
        link_pncp_layout = QHBoxLayout()
        link_pncp_layout.setSpacing(1)
        
        self.link_pncp_edit = QLineEdit(data['link_pncp'])
        link_pncp_layout.addLayout(self.create_layout("Link PNCP:", self.link_pncp_edit))
        
        icon_link = QIcon(str(self.ICONS_DIR / "link.png"))
        link_pncp_button = self.create_button("", icon=icon_link, callback=self.on_autorizacao_clicked, tooltip_text="Clique para autorização", button_size=QSize(40, 40), icon_size=QSize(30, 30))
        self.apply_widget_style(link_pncp_button)
        link_pncp_layout.addWidget(link_pncp_button)
        
        # Widget principal que contém o layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(comunicacao_padronizada_group_box)
        main_layout.addLayout(link_pncp_layout)

        return main_widget

    def add_pdf_to_merger(self):
        cp_number = self.cp_edit.text()
        if cp_number:
            pdf_add_dialog = PDFAddDialog(self.df_registro_selecionado, ICONS_DIR, self)
            if pdf_add_dialog.exec():
                print(f"Adicionar PDF para CP nº {cp_number}")
                # Aqui você pode adicionar a lógica para manipular o PDF com os dados do diálogo
            else:
                print("Ação de adicionar PDF cancelada.")
        else:
            QMessageBox.warning(self, "Erro", "Por favor, insira um número de CP válido.")

    def on_cp_clicked(self):
        # Implementação do callback para o botão CP
        pass

    def create_layout(self, label_text, widget, fixed_width=None):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        self.apply_widget_style(label)
        if fixed_width:
            widget.setFixedWidth(fixed_width)
        self.apply_widget_style(widget)
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout

    def fill_frame_criar_documentos(self):
        gerar_documentos_group_box = QGroupBox("Criar Documentos")
        self.apply_widget_style(gerar_documentos_group_box)
        gerar_documentos_group_box.setFixedWidth(270)  
        gerar_documentos_layout = QVBoxLayout()
        gerar_documentos_layout.setSpacing(1)

        # Botão Autorização
        icon_pdf = QIcon(str(self.ICONS_DIR / "pdf.png"))
        autorizacao_button = self.create_button("          Autorização            ", icon=icon_pdf, callback=self.on_autorizacao_clicked, tooltip_text="Clique para autorização", button_size=QSize(220, 40), icon_size=QSize(30, 30))
        self.apply_widget_style(autorizacao_button)
        gerar_documentos_layout.addWidget(autorizacao_button, alignment=Qt.AlignmentFlag.AlignCenter)

        cp_button = self.create_button("                 CP                  ", icon=icon_pdf, callback=self.on_autorizacao_clicked, tooltip_text="Clique para gerar o Aviso de Dispensa", button_size=QSize(220, 40), icon_size=QSize(30, 30))
        self.apply_widget_style(cp_button)
        gerar_documentos_layout.addWidget(cp_button, alignment=Qt.AlignmentFlag.AlignCenter)

        dfd_button = self.create_button("               DFD                 ", icon=icon_pdf, callback=self.on_autorizacao_clicked, tooltip_text="Clique para gerar o Aviso de Dispensa", button_size=QSize(220, 40), icon_size=QSize(30, 30))
        self.apply_widget_style(dfd_button)
        gerar_documentos_layout.addWidget(dfd_button, alignment=Qt.AlignmentFlag.AlignCenter)

        dec_button = self.create_button("Declaração Orçamentária", icon=icon_pdf, callback=self.on_autorizacao_clicked, tooltip_text="Clique para gerar a Declaração de Adequação Orçamentária", button_size=QSize(220, 40), icon_size=QSize(30, 30))
        self.apply_widget_style(dec_button)
        gerar_documentos_layout.addWidget(dec_button, alignment=Qt.AlignmentFlag.AlignCenter)

        declaracao_orcamentaria_button = self.create_button("   Termo de Referência   ", icon=icon_pdf, callback=self.on_autorizacao_clicked, tooltip_text="Clique para gerar a Declaração de Adequação Orçamentária", button_size=QSize(220, 40), icon_size=QSize(30, 30))
        self.apply_widget_style(declaracao_orcamentaria_button)
        gerar_documentos_layout.addWidget(declaracao_orcamentaria_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        aviso_dispensa_button = self.create_button("    Aviso de Dispensa     ", icon=icon_pdf, callback=self.on_autorizacao_clicked, tooltip_text="Clique para gerar o Aviso de Dispensa", button_size=QSize(220, 40), icon_size=QSize(30, 30))
        self.apply_widget_style(aviso_dispensa_button)
        gerar_documentos_layout.addWidget(aviso_dispensa_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        gerar_documentos_group_box.setLayout(gerar_documentos_layout)
        return gerar_documentos_group_box

    def fill_frame_formulario(self):
        formulario_group_box = QGroupBox("Formulário de Dados")
        self.apply_widget_style(formulario_group_box)   
        formulario_group_box.setFixedWidth(270)     
        formulario_layout = QVBoxLayout()
        formulario_layout.setSpacing(1)

        # Adicionando os botões ao layout
        icon_excel_up = QIcon(str(self.ICONS_DIR / "excel_up.png"))
        icon_excel_down = QIcon(str(self.ICONS_DIR / "excel_down.png"))

        criar_formulario_button = self.create_button(
            "   Criar Formulário   ", 
            icon=icon_excel_up, 
            callback=self.criar_formulario, 
            tooltip_text="Clique para criar o formulário", 
            button_size=QSize(220, 40), 
            icon_size=QSize(35, 35)
        )

        carregar_formulario_button = self.create_button(
            "Carregar Formulário", 
            icon=icon_excel_down, 
            callback=self.carregar_formulario, 
            tooltip_text="Clique para carregar o formulário", 
            button_size=QSize(220, 40), 
            icon_size=QSize(35, 35)
        )

        # Load da Imagem
        caminho_imagem = IMAGE_PATH / "licitacao_360.png" 
        licitacao_360_pixmap = QPixmap(str(caminho_imagem))  
        licitacao_360_pixmap = licitacao_360_pixmap.scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        image_label = QLabel()
        image_label.setPixmap(licitacao_360_pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Adiciona os botões ao layout
        formulario_layout.addWidget(criar_formulario_button, alignment=Qt.AlignmentFlag.AlignCenter)
        formulario_layout.addWidget(carregar_formulario_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Adiciona o espaçador vertical
        formulario_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Adiciona a imagem ao layout
        formulario_layout.addWidget(image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        formulario_group_box.setLayout(formulario_layout)

        return formulario_group_box

    def criar_formulario(self):
        pass

    def carregar_formulario(self):
        pass

    def setupGrupoSIGDEM(self):       
        grupoSIGDEM = QGroupBox("SIGDEM")
        self.apply_widget_style(grupoSIGDEM)
        grupoSIGDEM.setFixedWidth(270)  
        layout = QVBoxLayout(grupoSIGDEM)

        # Campo "Assunto"
        labelAssunto = QLabel("No campo “Assunto”, deverá constar:")
        labelAssunto.setStyleSheet("font-size: 12pt;")
        layout.addWidget(labelAssunto)
        self.textEditAssunto = QTextEdit()
        self.textEditAssunto.setStyleSheet("font-size: 12pt;")
        assunto_text = f"{self.id_processo} - Abertura de Dispensa Eletrônica"
        self.textEditAssunto.setPlainText(assunto_text)
        self.textEditAssunto.setMaximumHeight(60)

        icon_copy = QIcon(str(self.ICONS_DIR / "copy_1.png"))  # Caminho para o ícone de Word
        btnCopyAssunto = self.create_button(text="", icon=icon_copy, callback=lambda: self.copyToClipboard(self.textEditAssunto.toPlainText()), tooltip_text="Copiar texto para a área de transferência", button_size=QSize(40, 40), icon_size=QSize(25, 25))

        layoutHAssunto = QHBoxLayout()
        layoutHAssunto.addWidget(self.textEditAssunto)
        layoutHAssunto.addWidget(btnCopyAssunto)
        layout.addLayout(layoutHAssunto)

        # Campo "Sinopse"
        labelSinopse = QLabel("No campo “Sinopse”, deverá constar:")
        labelSinopse.setStyleSheet("font-size: 12pt;")
        layout.addWidget(labelSinopse)
        self.textEditSinopse = QTextEdit()
        self.textEditSinopse.setStyleSheet("font-size: 12pt;")
        sinopse_text = self.get_sinopse_text()
        self.textEditSinopse.setPlainText(sinopse_text)
        self.textEditSinopse.setMaximumHeight(140)
        btnCopySinopse = self.create_button(text="", icon=icon_copy, callback=lambda: self.copyToClipboard(self.textEditSinopse.toPlainText()), tooltip_text="Copiar texto para a área de transferência", button_size=QSize(40, 40), icon_size=QSize(25, 25))
        layoutHSinopse = QHBoxLayout()
        layoutHSinopse.addWidget(self.textEditSinopse)
        layoutHSinopse.addWidget(btnCopySinopse)
        layout.addLayout(layoutHSinopse)

        icon_info_sigdem = QIcon(str(self.ICONS_DIR / "info_sigdem.png"))
        info_sigdem_button = self.create_button("Informações SIGDEM", icon=icon_info_sigdem, callback=self.on_autorizacao_clicked, tooltip_text="Clique para gerar a Declaração de Adequação Orçamentária", button_size=QSize(220, 40), icon_size=QSize(30, 30))
        self.apply_widget_style(info_sigdem_button)
        layout.addWidget(info_sigdem_button, alignment=Qt.AlignmentFlag.AlignCenter)

        grupoSIGDEM.setLayout(layout)
        self.carregarAgentesResponsaveis()
        
        return grupoSIGDEM
    
    def get_sinopse_text(self):
        descricao_servico = "aquisição de" if self.material_servico == "Material" else "contratação de empresa especializada em"
        base_text = (
            f"Termo de Abertura referente à {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel}"
        )
        return base_text

    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QToolTip.showText(QCursor.pos(), "Texto copiado para a área de transferência.", msecShowTime=1500)

    def fill_frame_agentes_responsaveis(self):
        agente_responsavel_group_box = QGroupBox("Agentes Responsáveis")
        self.apply_widget_style(agente_responsavel_group_box)
        agente_responsavel_group_box.setFixedWidth(270)    
        agente_responsavel_layout = QVBoxLayout()
        agente_responsavel_layout.setSpacing(1) 
        agente_responsavel_layout.setContentsMargins(5, 1, 5, 1)  # Ajusta as margens internas

        self.ordenador_combo = self.create_combo_box('', [], 260)
        self.agente_fiscal_combo = self.create_combo_box('', [], 260)
        self.gerente_credito_combo = self.create_combo_box('', [], 260)
        self.responsavel_demanda_combo = self.create_combo_box('', [], 260)
        self.responsavel_demanda_combo2 = self.create_combo_box('', [], 260)

        agente_responsavel_layout.addLayout(self.create_layout_combobox_label("Ordenador de Despesa:", self.ordenador_combo))
        agente_responsavel_layout.addLayout(self.create_layout_combobox_label("Agente Fiscal:", self.agente_fiscal_combo))
        agente_responsavel_layout.addLayout(self.create_layout_combobox_label("Gerente de Crédito:", self.gerente_credito_combo))
        agente_responsavel_layout.addLayout(self.create_layout_combobox_label("Responsável pela Demanda:", self.responsavel_demanda_combo))
        agente_responsavel_layout.addLayout(self.create_layout_combobox_label("Operador da Contratação:", self.responsavel_demanda_combo2))

        icon_editar = QIcon(str(self.ICONS_DIR / "editar_responsaveis.png"))
        editar_responsaveis_button = self.create_button("Editar Responsáveis", icon=icon_editar, callback=self.on_autorizacao_clicked, tooltip_text="Clique para gerar a Declaração de Adequação Orçamentária", button_size=QSize(220, 40), icon_size=QSize(30, 30))
        self.apply_widget_style(editar_responsaveis_button)
        agente_responsavel_layout.addWidget(editar_responsaveis_button, alignment=Qt.AlignmentFlag.AlignCenter)

        agente_responsavel_group_box.setLayout(agente_responsavel_layout)
        self.carregarAgentesResponsaveis()
        
        return agente_responsavel_group_box

    def create_layout_combobox_label(self, label_text, combobox, fixed_width=None):
        layout = QVBoxLayout()
        label = QLabel(label_text)
        self.apply_widget_style(label)
        if fixed_width:
            combobox.setFixedWidth(fixed_width)
        self.apply_widget_style(combobox)
        layout.addWidget(label)
        layout.addWidget(combobox)
        layout.setSpacing(1)  # Define o espaçamento entre widgets no layout como 1 pixel
        layout.setContentsMargins(0, 0, 0, 0)  # Ajusta as margens internas do layout para zero
        return layout

    def fill_frame_classificacao_orcamentaria(self):
        data = self.extract_registro_data()
        classificacao_orcamentaria_group_box = QGroupBox("Classificação Orçamentária")
        self.apply_widget_style(classificacao_orcamentaria_group_box)
        classificacao_orcamentaria_group_box.setFixedWidth(340)  
        classificacao_orcamentaria_layout = QVBoxLayout()
        classificacao_orcamentaria_layout.setSpacing(1)  # Define o espaçamento entre os widgets

        # Valor Estimado
        self.valor_edit = QLineEdit(str(data['valor_total']) if pd.notna(data['valor_total']) else "")
        classificacao_orcamentaria_layout.addLayout(self.create_layout("Valor Estimado:", self.valor_edit))

        self.acao_interna_edit = QLineEdit(data['acao_interna'])
        self.fonte_recurso_edit = QLineEdit(data['fonte_recursos'])
        self.natureza_despesa_edit = QLineEdit(data['natureza_despesa'])
        self.unidade_orcamentaria_edit = QLineEdit(data['unidade_orcamentaria'])
        self.ptres_edit = QLineEdit(data['programa_trabalho_resuminho'])

        classificacao_orcamentaria_layout.addLayout(self.create_layout("Ação Interna:", self.acao_interna_edit))
        classificacao_orcamentaria_layout.addLayout(self.create_layout("Fonte de Recurso (FR):", self.fonte_recurso_edit))
        classificacao_orcamentaria_layout.addLayout(self.create_layout("Natureza de Despesa (ND):", self.natureza_despesa_edit))
        classificacao_orcamentaria_layout.addLayout(self.create_layout("Unidade Orçamentária (UO):", self.unidade_orcamentaria_edit))
        classificacao_orcamentaria_layout.addLayout(self.create_layout("PTRES:", self.ptres_edit))
        
        # Atividade de Custeio
        atividade_custeio_layout = QHBoxLayout()
        custeio_label = QLabel("Atividade de Custeio:")
        self.apply_widget_style(custeio_label)
        self.radio_custeio_sim = QRadioButton("Sim")
        self.radio_custeio_nao = QRadioButton("Não")
        atividade_custeio_value = data.get('atividade_custeio', 'Não')
        self.radio_custeio_sim.setChecked(atividade_custeio_value == 'Sim')
        self.radio_custeio_nao.setChecked(atividade_custeio_value != 'Sim')
        atividade_custeio_layout.addWidget(custeio_label)
        atividade_custeio_layout.addWidget(self.radio_custeio_sim)
        atividade_custeio_layout.addWidget(self.radio_custeio_nao)
        classificacao_orcamentaria_layout.addLayout(atividade_custeio_layout)

        classificacao_orcamentaria_group_box.setLayout(classificacao_orcamentaria_layout)
        return classificacao_orcamentaria_group_box

    def fill_frame_dados_do_setor_resposavel_contratacao(self):
        data = self.extract_registro_data()

        setor_responsavel_group_box = QGroupBox("Divisão/Setor Responsável pela Demanda")
        self.apply_widget_style(setor_responsavel_group_box)
        setor_responsavel_layout = QVBoxLayout()

        # Configuração da OM e Divisão na mesma linha
        om_divisao_layout = QHBoxLayout()
        om_layout = QHBoxLayout()
        om_label = QLabel("OM:")
        self.apply_widget_style(om_label)
        self.om_combo = self.create_combo_box(data.get('sigla_om', ''), [], 105)
        self.load_sigla_om()
        om_layout.addWidget(om_label)
        om_layout.addWidget(self.om_combo)

        divisao_label = QLabel("Divisão:")
        self.apply_widget_style(divisao_label)
        self.setor_responsavel_edit = QLineEdit(data['setor_responsavel'])
        om_divisao_layout.addLayout(om_layout)
        om_divisao_layout.addWidget(divisao_label)
        om_divisao_layout.addWidget(self.setor_responsavel_edit)
        setor_responsavel_layout.addLayout(om_divisao_layout)

        self.par_edit = QLineEdit(str(data.get('cod_par', '')))
        self.par_edit.setFixedWidth(120)
        self.prioridade_combo = self.create_combo_box(data.get('prioridade_par', 'Necessário'), ["Necessário", "Urgente", "Desejável"], 190)
        par_layout = QHBoxLayout()
        par_label = QLabel("Meta do PAR:")
        prioridade_label = QLabel("Prioridade:")
        self.apply_widget_style(par_label)
        self.apply_widget_style(prioridade_label)
        par_layout.addWidget(par_label)
        par_layout.addWidget(self.par_edit)
        par_layout.addWidget(prioridade_label)
        par_layout.addWidget(self.prioridade_combo)
        setor_responsavel_layout.addLayout(par_layout)

        self.endereco_edit = QLineEdit(data['endereco'])
        self.endereco_edit.setFixedWidth(250)
        self.cep_edit = QLineEdit(str(data.get('cep', '')))
        endereco_cep_layout = QHBoxLayout()
        endereco_label = QLabel("Endereço:")
        cep_label = QLabel("CEP:")
        self.apply_widget_style(endereco_label)
        self.apply_widget_style(cep_label)
        endereco_cep_layout.addWidget(endereco_label)
        endereco_cep_layout.addWidget(self.endereco_edit)
        endereco_cep_layout.addWidget(cep_label)
        endereco_cep_layout.addWidget(self.cep_edit)
        setor_responsavel_layout.addLayout(endereco_cep_layout)

        self.email_edit = QLineEdit(data['email'])
        self.email_edit.setFixedWidth(260)
        self.telefone_edit = QLineEdit(data['telefone'])
        email_telefone_layout = QHBoxLayout()
        email_telefone_layout.addLayout(self.create_layout("E-mail:", self.email_edit))
        email_telefone_layout.addLayout(self.create_layout("Tel:", self.telefone_edit))
        setor_responsavel_layout.addLayout(email_telefone_layout)

        self.dias_edit = QLineEdit("Segunda à Sexta")
        setor_responsavel_layout.addLayout(self.create_layout("Dias para Recebimento:", self.dias_edit))

        self.horario_edit = QLineEdit("09 às 11h20 e 14 às 16h30")
        setor_responsavel_layout.addLayout(self.create_layout("Horário para Recebimento:", self.horario_edit))

        # Adicionando Justificativa
        justificativa_label = QLabel("Justificativa para a contratação:")
        justificativa_label.setStyleSheet("font-size: 12pt;")
        self.justificativa_edit = QTextEdit(self.get_justification_text())
        self.apply_widget_style(self.justificativa_edit)
        setor_responsavel_layout.addWidget(justificativa_label)
        setor_responsavel_layout.addWidget(self.justificativa_edit)

        setor_responsavel_group_box.setLayout(setor_responsavel_layout)

        return setor_responsavel_group_box

    def get_justification_text(self):
        # Recupera o valor atual da justificativa no DataFrame
        current_justification = self.df_registro_selecionado['justificativa'].iloc[0]

        # Retorna o valor atual se ele existir, senão, constrói uma justificativa baseada no tipo de material/serviço
        if current_justification:  # Checa se existe uma justificativa
            return current_justification
        else:
            # Gera justificativa padrão com base no tipo de material ou serviço
            if self.material_servico == 'Material':
                return (f"A aquisição de {self.objeto} se faz necessária para o atendimento das necessidades do(a) {self.setor_responsavel} do(a) {self.orgao_responsavel} ({self.sigla_om}). A disponibilidade e a qualidade dos materiais são essenciais para garantir a continuidade das operações e a eficiência das atividades desempenhadas pelo(a) {self.setor_responsavel}.")
            elif self.material_servico == 'Serviço':
                return (f"A contratação de empresa especializada na prestação de serviços de {self.objeto} é imprescindível para o atendimento das necessidades do(a) {self.setor_responsavel} do(a) {self.orgao_responsavel} ({self.sigla_om}).")
            return ""  # Retorna uma string vazia se nenhuma condição acima for satisfeita

    def extract_registro_data(self):
        # Extrai dados do registro selecionado e armazena como atributos de instância
        self.id_processo = self.df_registro_selecionado['id_processo'].iloc[0]
        self.tipo = self.df_registro_selecionado['tipo'].iloc[0]
        self.numero = self.df_registro_selecionado['numero'].iloc[0]
        self.ano = self.df_registro_selecionado['ano'].iloc[0]
        self.situacao = self.df_registro_selecionado['situacao'].iloc[0]
        self.nup = self.df_registro_selecionado['nup'].iloc[0]
        self.material_servico = self.df_registro_selecionado['material_servico'].iloc[0]
        self.objeto = self.df_registro_selecionado['objeto'].iloc[0]
        self.vigencia = self.df_registro_selecionado['vigencia'].iloc[0]
        self.data_sessao = self.df_registro_selecionado['data_sessao'].iloc[0] 
        self.operador = self.df_registro_selecionado['operador'].iloc[0]
        self.com_disputa = self.df_registro_selecionado['com_disputa'].iloc[0]
        self.uasg = self.df_registro_selecionado['uasg'].iloc[0]
        self.orgao_responsavel = self.df_registro_selecionado['orgao_responsavel'].iloc[0]
        self.sigla_om = self.df_registro_selecionado['sigla_om'].iloc[0]
        self.setor_responsavel = self.df_registro_selecionado['setor_responsavel'].iloc[0]
        self.responsavel_pela_demanda = self.df_registro_selecionado['responsavel_pela_demanda'].iloc[0]
        self.ordenador_despesas = self.df_registro_selecionado['ordenador_despesas'].iloc[0]
        self.agente_fiscal = self.df_registro_selecionado['agente_fiscal'].iloc[0]
        self.gerente_de_credito = self.df_registro_selecionado['gerente_de_credito'].iloc[0]
        self.cod_par = self.df_registro_selecionado['cod_par'].iloc[0]
        self.prioridade_par = self.df_registro_selecionado['prioridade_par'].iloc[0]
        self.cep = self.df_registro_selecionado['cep'].iloc[0]
        self.endereco = self.df_registro_selecionado['endereco'].iloc[0]
        self.email = self.df_registro_selecionado['email'].iloc[0]
        self.telefone = self.df_registro_selecionado['telefone'].iloc[0]
        self.dias_para_recebimento = self.df_registro_selecionado['dias_para_recebimento'].iloc[0]
        self.horario_para_recebimento = self.df_registro_selecionado['horario_para_recebimento'].iloc[0]
        self.valor_total = self.df_registro_selecionado['valor_total'].iloc[0]
        self.acao_interna = self.df_registro_selecionado['acao_interna'].iloc[0]
        self.fonte_recursos = self.df_registro_selecionado['fonte_recursos'].iloc[0]
        self.natureza_despesa = self.df_registro_selecionado['natureza_despesa'].iloc[0]
        self.unidade_orcamentaria = self.df_registro_selecionado['unidade_orcamentaria'].iloc[0]
        self.programa_trabalho_resuminho = self.df_registro_selecionado['programa_trabalho_resuminho'].iloc[0]
        self.atividade_custeio = self.df_registro_selecionado['atividade_custeio'].iloc[0]
        self.comentarios = self.df_registro_selecionado['comentarios'].iloc[0]
        self.justificativa = self.df_registro_selecionado['justificativa'].iloc[0]
        self.link_pncp = self.df_registro_selecionado['link_pncp'].iloc[0]
        self.link_portal_marinha = self.df_registro_selecionado['link_portal_marinha'].iloc[0]
        self.previsao_contratacao = self.df_registro_selecionado['previsao_contratacao'].iloc[0]
        self.comunicacao_padronizada = self.df_registro_selecionado['comunicacao_padronizada'].iloc[0]
        self.do_resposavel = self.df_registro_selecionado['do_resposavel'].iloc[0]
        self.ao_responsavel = self.df_registro_selecionado['ao_responsavel'].iloc[0]

        data = {
            'id_processo': self.id_processo,
            'tipo': self.tipo,
            'numero': self.numero,
            'ano': self.ano,
            'situacao': self.situacao,
            'nup': self.nup,
            'material_servico': self.material_servico,
            'objeto': self.objeto,
            'vigencia': self.vigencia,
            'data_sessao': self.data_sessao,
            'operador': self.operador,
            'com_disputa': self.com_disputa,
            'uasg': self.uasg,
            'orgao_responsavel': self.orgao_responsavel,
            'sigla_om': self.sigla_om,
            'setor_responsavel': self.setor_responsavel,
            'responsavel_pela_demanda': self.responsavel_pela_demanda,
            'ordenador_despesas': self.ordenador_despesas,
            'agente_fiscal': self.agente_fiscal,
            'gerente_de_credito': self.gerente_de_credito,
            'cod_par': self.cod_par,
            'prioridade_par': self.prioridade_par,
            'cep': self.cep,
            'endereco': self.endereco,
            'email': self.email,
            'telefone': self.telefone,
            'dias_para_recebimento': self.dias_para_recebimento,
            'horario_para_recebimento': self.horario_para_recebimento,
            'valor_total': self.valor_total,
            'acao_interna': self.acao_interna,
            'fonte_recursos': self.fonte_recursos,
            'natureza_despesa': self.natureza_despesa,
            'unidade_orcamentaria': self.unidade_orcamentaria,
            'programa_trabalho_resuminho': self.programa_trabalho_resuminho,
            'atividade_custeio': self.atividade_custeio,
            'comentarios': self.comentarios,
            'justificativa': self.justificativa,
            'link_pncp': self.link_pncp,
            'link_portal_marinha': self.link_portal_marinha,
            'previsao_contratacao': self.previsao_contratacao,
            'comunicacao_padronizada': self.comunicacao_padronizada,
            'do_resposavel': self.do_resposavel,
            'ao_responsavel': self.ao_responsavel
        }

        return data

    def save_changes(self):
        data = {
            'situacao': self.situacao_edit.currentText(),
            'ordenador_despesas': self.ordenador_combo.currentText(),
            'agente_fiscal': self.agente_fiscal_combo.currentText(),
            'gerente_de_credito': self.gerente_credito_combo.currentText(),
            'responsavel_pela_demanda': self.responsavel_demanda_combo.currentText(),           
            'nup': self.nup_edit.text().strip(),
            'material_servico': self.material_edit.currentText(),
            'objeto': self.objeto_edit.text().strip(),
            'vigencia': self.vigencia_edit.text().strip() if isinstance(self.vigencia_edit, QLineEdit) else '12 (doze) meses',
            'data_sessao': self.data_edit.date().toString("yyyy-MM-dd") if isinstance(self.data_edit, QDateEdit) else '',
            'com_disputa': 'Sim' if self.radio_disputa_sim.isChecked() else 'Não',
            'setor_responsavel': self.setor_responsavel_edit.text().strip(),
            'operador': self.operador_edit.text().strip(),
            'sigla_om': self.om_combo.currentText(),
            'uasg': self.df_registro_selecionado.loc[self.df_registro_selecionado.index[0], 'uasg'],  # Inclui uasg
            'orgao_responsavel': self.df_registro_selecionado.loc[self.df_registro_selecionado.index[0], 'orgao_responsavel'],
            'cod_par': self.par_edit.text().strip(),  
            'prioridade_par': self.prioridade_combo.currentText(),
            'cep': self.cep_edit.text().strip(),
            'endereco': self.endereco_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'telefone': self.telefone_edit.text().strip(),
            'dias_para_recebimento': self.dias_edit.text().strip(),
            'horario_para_recebimento': self.horario_edit.text().strip(),            
            'valor_total': self.valor_edit.text().strip(),
            'acao_interna': self.acao_interna_edit.text().strip(),
            'fonte_recursos': self.fonte_recurso_edit.text().strip(),
            'natureza_despesa': self.natureza_despesa_edit.text().strip(),
            'unidade_orcamentaria': self.unidade_orcamentaria_edit.text().strip(),
            'programa_trabalho_resuminho': self.ptres_edit.text().strip(),           
            'atividade_custeio': 'Sim' if self.radio_custeio_sim.isChecked() else 'Não',
        }
        self.update_database(data)

    def update_database(self, data):
        with self.database_manager as connection:
            cursor = connection.cursor()
            set_part = ', '.join([f"{key} = ?" for key in data.keys()])
            valores = list(data.values())
            valores.append(self.df_registro_selecionado['id_processo'].iloc[0])
            query = f"UPDATE controle_dispensas SET {set_part} WHERE id_processo = ?"
            cursor.execute(query, valores)
            connection.commit()
            QMessageBox.information(self, "Atualização", "As alterações foram salvas com sucesso.")

    def update_title_label(self):
        data = self.extract_registro_data()
        html_text = (
            f"{data['tipo']} {data['numero']}/{data['ano']} - {data['objeto']}<br>"
            f"<span style='font-size: 18px; color: #333333;'>OM: {data['orgao_responsavel']} (UASG: {data['uasg']})</span>"
        )
        if not hasattr(self, 'titleLabel'):
            self.titleLabel = QLabel()
            self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
            self.titleLabel.setStyleSheet("font-size: 26px; font-weight: bold;")

        self.titleLabel.setText(html_text)

        if not hasattr(self, 'header_layout'):
            self.header_layout = QHBoxLayout()
            self.header_layout.addWidget(self.titleLabel)
            self.header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            self.add_action_buttons(self.header_layout)

            header_widget = QWidget()
            header_widget.setLayout(self.header_layout)
            header_widget.setFixedHeight(80)
            self.header_widget = header_widget

        return self.header_widget

    def update_title_label_text(self, new_title):
        data = self.extract_registro_data()
        html_text = (
            f"{data['tipo']} {data['numero']}/{data['ano']} - {data['objeto']}<br>"
            f"<span style='font-size: 18px; color: #333333;'>OM: {new_title}</span>"
        )
        self.titleLabel.setText(html_text)
        print(f"Title updated: {html_text}")
    
    def add_action_buttons(self, layout):
        icon_confirm = QIcon(str(self.ICONS_DIR / "confirm.png"))
        icon_x = QIcon(str(self.ICONS_DIR / "cancel.png"))
        
        button_confirm = self.create_button(" Salvar", icon_confirm, self.save_changes, "Salvar dados", QSize(110, 50), QSize(40, 40))
        button_x = self.create_button(" Cancelar", icon_x, self.reject, "Cancelar alterações e fechar", QSize(110, 50), QSize(30, 30))
                
        layout.addWidget(button_confirm)
        layout.addWidget(button_x)

        self.apply_widget_style(button_confirm)
        self.apply_widget_style(button_x)


    def create_button(self, text="", icon=None, callback=None, tooltip_text="", button_size=None, icon_size=None):
        btn = QPushButton(text)
        if icon:
            btn.setIcon(icon)
            btn.setIconSize(icon_size if icon_size else QSize(40, 40))
        if button_size:
            btn.setFixedSize(button_size)
        btn.setToolTip(tooltip_text)
        if callback:
            btn.clicked.connect(callback)  # Conecta o callback ao evento de clique
        return btn

    def on_autorizacao_clicked(self):
        print("Botão Autorização clicado")  # Substitua esta função pela funcionalidade desejada

    def open_editar_responsaveis_dialog(self):
        config_dialog = ConfiguracoesDispensaDialog(self)
        # config_dialog.config_updated.connect(self.update_frame4_content)
        if config_dialog.exec():
            print("Configurações salvas")
        else:
            print("Configurações canceladas")

    def importar_tabela(self):
        pass

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
        combo_widget.clear()
        for index, row in agentes_df.iterrows():
            texto_display = f"{row['nome']}\n{row['posto']}\n{row['funcao']}"
            # Armazena um dicionário no UserRole para cada item adicionado ao ComboBox  
            combo_widget.addItem(texto_display, userData=row.to_dict())    

    def load_sigla_om(self):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT sigla_om FROM controle_om ORDER BY sigla_om")
                items = [row[0] for row in cursor.fetchall()]
                self.om_combo.addItems(items)
                self.om_combo.currentTextChanged.connect(self.on_om_changed)
                print(f"Loaded sigla_om items: {items}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao carregar OM: {e}")
            print(f"Error loading sigla_om: {e}")

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
                self.title_updated.emit(f"{orgao_responsavel} (UASG: {uasg})")

    def apply_dark_red_style(self, button):
        button.setStyleSheet("""
            QPushButton, QPushButton::tooltip {
                font-size: 14pt;
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
        button.update()  # Força a atualização do widget

class EditDataDialog2(QDialog):
    dados_atualizados = pyqtSignal()
    title_updated = pyqtSignal(str) 
    button_changed = pyqtSignal(str)

    def __init__(self, df_registro_selecionado, icons_dir, parent=None):
        super().__init__(parent)
        self.df_registro_selecionado = df_registro_selecionado
        self.document_details_widget = None 
        self.consolidador = ConsolidarDocumentos(df_registro_selecionado)
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

        self.selected_button = "Abertura de Processo"  # Inicializa com o botão padrão selecionado

        self.frame4_group_box = None

        self.painel_layout = QVBoxLayout()  # Inicializa painel_layout antes de setup_frames

        # Conectar o sinal ao método de atualização do layout
        self.button_changed.connect(self.update_painel_layout)
        
        self.setup_frames()
        
        self.move(QPoint(0, 0))
        
        self.update_painel_layout(self.selected_button)  # Atualização inicial

    def extract_registro_data(self):
        # Extrai dados do registro selecionado e armazena como atributos de instância
        self.id_processo = self.df_registro_selecionado['id_processo'].iloc[0]
        self.tipo = self.df_registro_selecionado['tipo'].iloc[0]
        self.numero = self.df_registro_selecionado['numero'].iloc[0]
        self.ano = self.df_registro_selecionado['ano'].iloc[0]
        self.situacao = self.df_registro_selecionado['situacao'].iloc[0]
        self.nup = self.df_registro_selecionado['nup'].iloc[0]
        self.material_servico = self.df_registro_selecionado['material_servico'].iloc[0]
        self.objeto = self.df_registro_selecionado['objeto'].iloc[0]
        self.vigencia = self.df_registro_selecionado['vigencia'].iloc[0]
        self.data_sessao = self.df_registro_selecionado['data_sessao'].iloc[0] 
        self.operador = self.df_registro_selecionado['operador'].iloc[0]
        self.com_disputa = self.df_registro_selecionado['com_disputa'].iloc[0]
        self.uasg = self.df_registro_selecionado['uasg'].iloc[0]
        self.orgao_responsavel = self.df_registro_selecionado['orgao_responsavel'].iloc[0]
        self.sigla_om = self.df_registro_selecionado['sigla_om'].iloc[0]
        self.setor_responsavel = self.df_registro_selecionado['setor_responsavel'].iloc[0]
        self.responsavel_pela_demanda = self.df_registro_selecionado['responsavel_pela_demanda'].iloc[0]
        self.ordenador_despesas = self.df_registro_selecionado['ordenador_despesas'].iloc[0]
        self.agente_fiscal = self.df_registro_selecionado['agente_fiscal'].iloc[0]
        self.gerente_de_credito = self.df_registro_selecionado['gerente_de_credito'].iloc[0]
        self.cod_par = self.df_registro_selecionado['cod_par'].iloc[0]
        self.prioridade_par = self.df_registro_selecionado['prioridade_par'].iloc[0]
        self.cep = self.df_registro_selecionado['cep'].iloc[0]
        self.endereco = self.df_registro_selecionado['endereco'].iloc[0]
        self.email = self.df_registro_selecionado['email'].iloc[0]
        self.telefone = self.df_registro_selecionado['telefone'].iloc[0]
        self.dias_para_recebimento = self.df_registro_selecionado['dias_para_recebimento'].iloc[0]
        self.horario_para_recebimento = self.df_registro_selecionado['horario_para_recebimento'].iloc[0]
        self.valor_total = self.df_registro_selecionado['valor_total'].iloc[0]
        self.acao_interna = self.df_registro_selecionado['acao_interna'].iloc[0]
        self.fonte_recursos = self.df_registro_selecionado['fonte_recursos'].iloc[0]
        self.natureza_despesa = self.df_registro_selecionado['natureza_despesa'].iloc[0]
        self.unidade_orcamentaria = self.df_registro_selecionado['unidade_orcamentaria'].iloc[0]
        self.programa_trabalho_resuminho = self.df_registro_selecionado['programa_trabalho_resuminho'].iloc[0]
        self.atividade_custeio = self.df_registro_selecionado['atividade_custeio'].iloc[0]
        self.comentarios = self.df_registro_selecionado['comentarios'].iloc[0]
        self.justificativa = self.df_registro_selecionado['justificativa'].iloc[0]
        self.link_pncp = self.df_registro_selecionado['link_pncp'].iloc[0]
        self.link_portal_marinha = self.df_registro_selecionado['link_portal_marinha'].iloc[0]
        self.previsao_contratacao = self.df_registro_selecionado['previsao_contratacao'].iloc[0]
        self.comunicacao_padronizada = self.df_registro_selecionado['comunicacao_padronizada'].iloc[0]
        self.do_resposavel = self.df_registro_selecionado['do_resposavel'].iloc[0]
        self.ao_responsavel = self.df_registro_selecionado['ao_responsavel'].iloc[0]

        data = {
            'id_processo': self.id_processo,
            'tipo': self.tipo,
            'numero': self.numero,
            'ano': self.ano,
            'situacao': self.situacao,
            'nup': self.nup,
            'material_servico': self.material_servico,
            'objeto': self.objeto,
            'vigencia': self.vigencia,
            'data_sessao': self.data_sessao,
            'operador': self.operador,
            'com_disputa': self.com_disputa,
            'uasg': self.uasg,
            'orgao_responsavel': self.orgao_responsavel,
            'sigla_om': self.sigla_om,
            'setor_responsavel': self.setor_responsavel,
            'responsavel_pela_demanda': self.responsavel_pela_demanda,
            'ordenador_despesas': self.ordenador_despesas,
            'agente_fiscal': self.agente_fiscal,
            'gerente_de_credito': self.gerente_de_credito,
            'cod_par': self.cod_par,
            'prioridade_par': self.prioridade_par,
            'cep': self.cep,
            'endereco': self.endereco,
            'email': self.email,
            'telefone': self.telefone,
            'dias_para_recebimento': self.dias_para_recebimento,
            'horario_para_recebimento': self.horario_para_recebimento,
            'valor_total': self.valor_total,
            'acao_interna': self.acao_interna,
            'fonte_recursos': self.fonte_recursos,
            'natureza_despesa': self.natureza_despesa,
            'unidade_orcamentaria': self.unidade_orcamentaria,
            'programa_trabalho_resuminho': self.programa_trabalho_resuminho,
            'atividade_custeio': self.atividade_custeio,
            'comentarios': self.comentarios,
            'justificativa': self.justificativa,
            'link_pncp': self.link_pncp,
            'link_portal_marinha': self.link_portal_marinha,
            'previsao_contratacao': self.previsao_contratacao,
            'comunicacao_padronizada': self.comunicacao_padronizada,
            'do_resposavel': self.do_resposavel,
            'ao_responsavel': self.ao_responsavel
        }

        return data

    def save_changes(self):
        data = {
            'situacao': self.situacao_edit.currentText(),
            'ordenador_despesas': self.ordenador_combo.currentText(),
            'agente_fiscal': self.agente_fiscal_combo.currentText(),
            'gerente_de_credito': self.gerente_credito_combo.currentText(),
            'responsavel_pela_demanda': self.responsavel_demanda_combo.currentText(),           
            'nup': self.nup_edit.text().strip(),
            'material_servico': self.material_edit.currentText(),
            'objeto': self.objeto_edit.text().strip(),
            'vigencia': self.vigencia_edit.text().strip() if isinstance(self.vigencia_edit, QLineEdit) else '12 (doze) meses',
            'data_sessao': self.data_edit.date().toString("yyyy-MM-dd") if isinstance(self.data_edit, QDateEdit) else '',
            'com_disputa': 'Sim' if self.radio_disputa_sim.isChecked() else 'Não',
            'setor_responsavel': self.setor_responsavel_edit.text().strip(),
            'operador': self.operador_edit.text().strip(),
            'sigla_om': self.om_combo.currentText(),
            'uasg': self.df_registro_selecionado.loc[self.df_registro_selecionado.index[0], 'uasg'],  # Inclui uasg
            'orgao_responsavel': self.df_registro_selecionado.loc[self.df_registro_selecionado.index[0], 'orgao_responsavel'],
            'cod_par': self.par_edit.text().strip(),  
            'prioridade_par': self.prioridade_combo.currentText(),
            'cep': self.cep_edit.text().strip(),
            'endereco': self.endereco_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'telefone': self.telefone_edit.text().strip(),
            'dias_para_recebimento': self.dias_edit.text().strip(),
            'horario_para_recebimento': self.horario_edit.text().strip(),            
            'valor_total': self.valor_edit.text().strip(),
            'acao_interna': self.acao_interna_edit.text().strip(),
            'fonte_recursos': self.fonte_recurso_edit.text().strip(),
            'natureza_despesa': self.natureza_despesa_edit.text().strip(),
            'unidade_orcamentaria': self.unidade_orcamentaria_edit.text().strip(),
            'programa_trabalho_resuminho': self.ptres_edit.text().strip(),           
            'atividade_custeio': 'Sim' if self.radio_custeio_sim.isChecked() else 'Não',
        }

        # Adiciona valores de self.document_details_widget apenas se estiverem presentes
        if hasattr(self, 'document_details_widget') and self.document_details_widget:
            data['comunicacao_padronizada'] = self.document_details_widget.cp_edit.text().strip()
            data['do_resposavel'] = self.document_details_widget.responsavel_edit.text().strip()
            data['ao_responsavel'] = self.document_details_widget.encarregado_obtencao_edit.text().strip()
        else:
            # Define valores padrão ou os valores já presentes no registro selecionado
            data['comunicacao_padronizada'] = self.df_registro_selecionado['comunicacao_padronizada'].iloc[0]
            data['do_resposavel'] = self.df_registro_selecionado['do_resposavel'].iloc[0]
            data['ao_responsavel'] = self.df_registro_selecionado['ao_responsavel'].iloc[0]

        with self.database_manager as connection:
            cursor = connection.cursor()
            set_part = ', '.join([f"{key} = ?" for key in data.keys()])
            valores = list(data.values())
            valores.append(self.df_registro_selecionado['id_processo'].iloc[0])

            query = f"UPDATE controle_dispensas SET {set_part} WHERE id_processo = ?"
            cursor.execute(query, valores)
            connection.commit()

        # Atualiza o DataFrame em memória
        for key, value in data.items():
            self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], key] = value

        self.dados_atualizados.emit()
        QMessageBox.information(self, "Atualização", "As alterações foram salvas com sucesso.")

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
            pixmap = QPixmap(str(MARINHA_PATH)).scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label = QLabel()
            self.image_label.setPixmap(pixmap)
            self.header_layout.addWidget(self.image_label)

            # Define uma altura fixa para o layout do cabeçalho
            header_widget = QWidget()
            header_widget.setLayout(self.header_layout)
            header_widget.setFixedHeight(80)  # Ajuste essa altura conforme necessário
            self.header_widget = header_widget

        return self.header_widget

    def add_action_buttons(self, layout):
        icon_confirm = QIcon(str(self.ICONS_DIR / "confirm.png"))
        icon_x = QIcon(str(self.ICONS_DIR / "cancel.png"))
        icon_config = QIcon(str(self.ICONS_DIR / "excel.png"))
        icon_responsaveis = QIcon(str(self.ICONS_DIR / "responsaveis.png"))
        
        button_confirm = self.create_button("  Salvar", icon_confirm, self.save_changes, "Salvar dados", QSize(115, 50), QSize(40, 40))
        button_x = self.create_button("  Cancelar", icon_x, self.reject, "Cancelar alterações e fechar", QSize(115, 50), QSize(30, 30))
        button_config = self.create_button(" Importar", icon_config, self.importar_tabela, "Alterar local de salvamento, entre outras configurações", QSize(115, 50), QSize(30, 30))
        button_responsaveis = self.create_button("Responsáveis", icon_responsaveis, self.open_editar_responsaveis_dialog, "Alterar local de salvamento, entre outras configurações", QSize(135, 50), QSize(30, 30))
                
        layout.addWidget(button_confirm)
        layout.addWidget(button_x)
        layout.addWidget(button_config)
        layout.addWidget(button_responsaveis)
        self.apply_widget_style(button_confirm)
        self.apply_widget_style(button_x)
        self.apply_widget_style(button_config)
        self.apply_widget_style(button_responsaveis)

    def importar_tabela(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Opções de Tabela")
        layout = QVBoxLayout(dialog)

        # Botões para as opções
        btn_generate = QPushButton("Gerar Tabela")
        btn_import = QPushButton("Importar Tabela")

        btn_generate.clicked.connect(self.gerar_tabela)  # Supondo que essa função exista
        btn_import.clicked.connect(self.carregar_tabela)  # Supondo que essa função exista

        layout.addWidget(btn_generate)
        layout.addWidget(btn_import)

        dialog.setLayout(layout)
        dialog.exec()

    def gerar_tabela(self):
        try:
            data = self.extract_registro_data()  # Extrai os dados
            df = pd.DataFrame(list(data.items()), columns=['Campo', 'Valor'])

            # Define o caminho do arquivo XLSX
            xlsx_path = os.path.join(os.path.expanduser("~"), "Desktop", f"Dados_Registro_{self.df_registro_selecionado['numero'].iloc[0]}_{self.df_registro_selecionado['ano'].iloc[0]}.xlsx")

            # Cria o arquivo XLSX
            with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)

                # Ajuste do tamanho das colunas no workbook
                workbook = writer.book
                worksheet = writer.sheets['Sheet1']
                worksheet.column_dimensions['A'].width = 40  # Largura da coluna A ajustada para 200 pixels / aproximadamente 20 caracteres
                worksheet.column_dimensions['B'].width = 60  # Largura da coluna B ajustada para 300 pixels / aproximadamente 30 caracteres

            # Abre o arquivo XLSX criado
            os.startfile(xlsx_path)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Ocorreu um erro ao gerar ou abrir o arquivo XLSX: {str(e)}")

    def carregar_tabela(self):
        # Abre um QFileDialog para selecionar o arquivo Excel
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo Excel", os.path.expanduser("~"), "Excel Files (*.xlsx)")

        if not file_path:
            return  # O usuário cancelou a seleção do arquivo

        try:
            # Lê o arquivo Excel para um DataFrame
            df = pd.read_excel(file_path)

            # Converte DataFrame para dicionário onde as chaves são os campos e os valores são os dados correspondentes
            data = dict(zip(df['Campo'], df['Valor']))

            # Abre a conexão com o banco de dados e atualiza os registros
            with self.database_manager as connection:
                cursor = connection.cursor()
                set_part = ', '.join([f"{key} = ?" for key in data.keys()])
                valores = list(data.values())
                valores.append(self.df_registro_selecionado['id_processo'].iloc[0])

                query = f"UPDATE controle_dispensas SET {set_part} WHERE id_processo = ?"
                cursor.execute(query, valores)
                connection.commit()

            QMessageBox.information(self, "Sucesso", "Dados importados e atualizados com sucesso no banco de dados.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Ocorreu um erro ao carregar ou atualizar dados: {str(e)}")

    def create_button(self, text, icon=None, callback=None, tooltip_text="", button_size=None, icon_size=None):
        btn = QPushButton(text)
        if icon:
            btn.setIcon(icon)
            btn.setIconSize(icon_size if icon_size else QSize(40, 40))
        if button_size:
            btn.setFixedSize(button_size)
        btn.setToolTip(tooltip_text)
        if callback:
            btn.clicked.connect(callback)  # Conecta o callback ao evento de clique
        return btn

    def open_editar_responsaveis_dialog(self):
        config_dialog = ConfiguracoesDispensaDialog(self)
        # config_dialog.config_updated.connect(self.update_frame4_content)
        if config_dialog.exec():
            print("Configurações salvas")
        else:
            print("Configurações canceladas")

    def open_config_dialog(self):
        config_dialog = ConfiguracoesDispensaDialog(self)
        config_dialog.config_updated.connect(self.update_frame4_content)
        if config_dialog.exec():
            print("Configurações salvas")
        else:
            print("Configurações canceladas")

    def setup_frames(self):
        topRow = QHBoxLayout()
        self.frame_agentes_responsaveis, self.frame_agentes_responsaveis_layout = self.create_frame()
        self.frame1, self.frame1_layout = self.create_frame()
        self.frame2, self.frame2_layout = self.create_frame()
        self.frame_classificacao_orcamentaria, self.frame_classificacao_orcamentaria_layout = self.create_frame()
        topRow.addWidget(self.frame_agentes_responsaveis)
        topRow.addWidget(self.frame1)
        topRow.addWidget(self.frame2)
        topRow.addWidget(self.frame_classificacao_orcamentaria)
        self.layout.addLayout(topRow)  # Adiciona o QHBoxLayout com os dois frames ao layout principal

        linhaDeBaixo = QVBoxLayout()
        self.frame4, self.frame4_layout = self.create_frame("CustomStyledFrame")

        linhaDeBaixo.addWidget(self.frame4)
        self.layout.addLayout(linhaDeBaixo)  # Adiciona o QVBoxLayout com os três frames ao layout principal

        # Preenche os frames com os campos apropriados
        self.fill_frame_agentes_responsaveis()
        self.fill_frame1()
        self.fill_frame2()
        self.fill_frame_classificacao_orcamentaria()
        self.fill_frame4()
        self.reapply_special_button_style()

    def create_frame(self, object_name=None):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)  # Mantém o estilo do frame
        frame.setFrameShadow(QFrame.Shadow.Raised)     # Mantém a sombra para destacar o frame
        if object_name:
            frame.setObjectName(object_name)  # Define o nome do objeto para o frame
            frame.setStyleSheet(f"""
                #{object_name} {{
                    background-color: #050f41;
                }}
            """)  # Aplica o estilo com fundo e borda somente ao frame com esse nome de objeto
        frame_layout = QVBoxLayout()  # Continua usando QVBoxLayout para organizar os widgets dentro do frame
        frame.setLayout(frame_layout)  # Define o layout do frame
        return frame, frame_layout    # Retorna tanto o frame quanto seu layout

    def apply_widget_style(self, widget):
        widget.setStyleSheet("font-size: 12pt;") 

    def fill_frame_agentes_responsaveis(self):
        data = self.extract_registro_data()
        # Define o layout e o grupo para os agentes responsáveis
        agente_responsavel = QVBoxLayout()

        situacao_layout = QHBoxLayout()
        situacao_label = QLabel("Situação:")
        self.situacao_edit = QComboBox()
        self.situacao_edit.setFixedWidth(210)
        self.situacao_edit.addItems(["Planejamento", "Aprovado", "Sessão Publica", "Concluído"])
        self.situacao_edit.setCurrentText(data.get('situacao', 'Planejamento'))
        self.apply_widget_style(situacao_label)
        self.apply_widget_style(self.situacao_edit)
        situacao_layout.addWidget(situacao_label)
        situacao_layout.addWidget(self.situacao_edit)

        # Adicionar o layout de situação ao grupo de contratação
        agente_responsavel.addLayout(situacao_layout)

        
        agente_responsavel_group_box = QGroupBox("Agentes Responsáveis")
        self.apply_widget_style(agente_responsavel_group_box)
        agente_responsavel_layout = QVBoxLayout()

        # Cria as labels e ComboBoxes para cada agente responsável
        ordenador_despesa_label = QLabel("Ordenador de Despesas:")
        self.ordenador_combo = QComboBox()
        self.ordenador_combo.setFixedWidth(260)
        agente_fiscal_label = QLabel("Agente Fiscal:")
        self.agente_fiscal_combo = QComboBox()
        self.agente_fiscal_combo.setFixedWidth(260)
        gerente_de_credito_label = QLabel("Gerente de Crédito:")
        self.gerente_credito_combo = QComboBox()
        self.gerente_credito_combo.setFixedWidth(260)
        responsavel_pela_demanda_label = QLabel("Responsável pela Demanda:")
        self.responsavel_demanda_combo = QComboBox()
        self.responsavel_demanda_combo.setFixedWidth(260)
        # Adiciona as labels e ComboBoxes ao layout
        agente_responsavel_layout.addWidget(ordenador_despesa_label)
        agente_responsavel_layout.addWidget(self.ordenador_combo)
        agente_responsavel_layout.addWidget(agente_fiscal_label)
        agente_responsavel_layout.addWidget(self.agente_fiscal_combo)
        agente_responsavel_layout.addWidget(gerente_de_credito_label)
        agente_responsavel_layout.addWidget(self.gerente_credito_combo)
        agente_responsavel_layout.addWidget(responsavel_pela_demanda_label)
        agente_responsavel_layout.addWidget(self.responsavel_demanda_combo)
        
        agente_responsavel_group_box.setLayout(agente_responsavel_layout)

        # Adiciona o grupo ao layout principal do frame
        agente_responsavel.addWidget(agente_responsavel_group_box)
        self.frame_agentes_responsaveis_layout.addLayout(agente_responsavel)
        # Carrega os dados nos ComboBoxes
        self.carregarAgentesResponsaveis()

    def fill_frame1(self):
        data = self.extract_registro_data()
        # Layout principal para detalhes
        detalhes_layout = QHBoxLayout()

        # Grupo de Contratação
        contratacao_group_box = QGroupBox("Contratação")
        self.apply_widget_style(contratacao_group_box)
        contratacao_layout = QVBoxLayout()
        contratacao_group_box.setLayout(contratacao_layout)

        # NUP
        nup_layout = QHBoxLayout()
        nup_label = QLabel("NUP:")
        self.nup_edit = QLineEdit(data['nup'])
        self.apply_widget_style(self.nup_edit)
        self.nup_edit.setReadOnly(False)
        nup_layout.addWidget(nup_label)
        nup_layout.addWidget(self.nup_edit)
        # Adicionar o layout de situação ao grupo de contratação
        contratacao_layout.addLayout(nup_layout)

        # Material/Serviço
        material_layout = QHBoxLayout()
        material_label = QLabel("Material/Serviço:")
        self.material_edit = QComboBox()
        self.material_edit.addItems(["Material", "Serviço"])
        self.material_edit.setCurrentText(data.get('material_servico', 'Material'))
        self.apply_widget_style(material_label)
        self.apply_widget_style(self.material_edit)
        material_layout.addWidget(material_label)
        material_layout.addWidget(self.material_edit)
        contratacao_layout.addLayout(material_layout)

        # Objeto
        objeto_layout = QHBoxLayout()
        objeto_label = QLabel("Objeto:")
        self.objeto_edit = QLineEdit(data['objeto'])
        self.objeto_edit.setFixedWidth(250)
        self.apply_widget_style(self.objeto_edit)
        self.objeto_edit.setReadOnly(False)
        objeto_layout.addWidget(objeto_label)
        objeto_layout.addWidget(self.objeto_edit)
        contratacao_layout.addLayout(objeto_layout)

        # Vigência da Contratação
        vigencia_layout = QHBoxLayout()
        vigencia_label = QLabel("Vigência:")
        self.vigencia_edit = QLineEdit()
        vigencia_value = data.get('vigencia', '12 (doze) meses')
        if vigencia_value is None:
            vigencia_value = '12 (doze) meses'
        print(f"Vigência value: {vigencia_value}") 
        self.vigencia_edit.setText(vigencia_value)
        self.apply_widget_style(self.vigencia_edit)
        self.vigencia_edit.setReadOnly(False)
        vigencia_layout.addWidget(vigencia_label)
        vigencia_layout.addWidget(self.vigencia_edit)
        contratacao_layout.addLayout(vigencia_layout)

        # Data da Sessão em linha própria
        data_sessao_layout = QHBoxLayout()
        data_sessao_label = QLabel("Data da Sessão:")
        self.data_edit = QDateEdit()
        self.data_edit.setCalendarPopup(True)
        data_sessao_str = data.get('data_sessao', '')
        if data_sessao_str:
            self.data_edit.setDate(QDate.fromString(data_sessao_str, "yyyy-MM-dd"))
        else:
            self.data_edit.setDate(QDate.currentDate())
        self.apply_widget_style(data_sessao_label)
        self.apply_widget_style(self.data_edit)
        data_sessao_layout.addWidget(data_sessao_label)
        data_sessao_layout.addWidget(self.data_edit)
        contratacao_layout.addLayout(data_sessao_layout)

        # Operador
        operador_layout = QHBoxLayout()
        operador_label = QLabel("Operador:")
        self.operador_edit = QLineEdit(data['operador'])
        self.apply_widget_style(operador_label)
        self.apply_widget_style(self.operador_edit)
        operador_layout.addWidget(operador_label)
        operador_layout.addWidget(self.operador_edit)
        contratacao_layout.addLayout(operador_layout)

        # Com Disputa
        disputa_layout = QHBoxLayout()
        disputa_label = QLabel("Com disputa?")
        self.radio_disputa_sim = QRadioButton("Sim")
        self.radio_disputa_nao = QRadioButton("Não")
        com_disputa_value = data.get('com_disputa', 'Não')  # Define 'Não' como padrão
        self.radio_disputa_sim.setChecked(com_disputa_value == 'Sim')
        self.radio_disputa_nao.setChecked(com_disputa_value != 'Sim')  # Marca 'Não' se não for 'Sim'
        disputa_layout.addWidget(disputa_label)
        disputa_layout.addWidget(self.radio_disputa_sim)
        disputa_layout.addWidget(self.radio_disputa_nao)
        contratacao_layout.addLayout(disputa_layout)

        criterio_layout = QHBoxLayout()
        criterio_label = QLabel("Critédio de Julgamento:")
        self.criterio_edit = QComboBox()
        self.criterio_edit.addItems(["Menor Preço", "Maior Desconto"])
        # self.criterio_edit.setCurrentText(data.get('material_servico', 'Menor Preço'))
        self.apply_widget_style(criterio_label)
        self.apply_widget_style(self.criterio_edit)
        criterio_layout.addWidget(criterio_label)
        criterio_layout.addWidget(self.criterio_edit)
        contratacao_layout.addLayout(criterio_layout)

        # Adicionar o grupo de contratação ao layout de detalhes
        detalhes_layout.addWidget(contratacao_group_box)
        # Adicionar o layout de detalhes ao layout principal do frame
        self.frame1_layout.addLayout(detalhes_layout)
        
        detalhes_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

    def fill_frame2(self):
        data = self.extract_registro_data()

        setor_responsavel_group_box = QGroupBox("Divisão/Setor Responsável pela Demanda")
        self.apply_widget_style(setor_responsavel_group_box)
        setor_responsavel_layout = QVBoxLayout()

        sigla_layout = QHBoxLayout()
        self.om_combo = QComboBox()
        self.load_sigla_om()
        self.om_combo.setCurrentText(data.get('sigla_om', ''))
        self.apply_widget_style(self.om_combo)
        self.om_combo.setFixedWidth(120)
        sigla_layout.addWidget(self.om_combo)

        divisao_secao_label = QLabel("Divisão:")
        self.setor_responsavel_edit = QLineEdit(data['setor_responsavel'])
        self.apply_widget_style(divisao_secao_label)
        self.apply_widget_style(self.setor_responsavel_edit)
        sigla_layout.addWidget(divisao_secao_label)
        sigla_layout.addWidget(self.setor_responsavel_edit)
        setor_responsavel_layout.addLayout(sigla_layout)

        par_layout = QHBoxLayout()
        par_label = QLabel("PAR/Prioridade:")
        self.par_edit = QLineEdit(str(data.get('cod_par', '')))
        self.par_edit.setFixedWidth(90)
        self.apply_widget_style(par_label)
        self.apply_widget_style(self.par_edit)
        par_layout.addWidget(par_label)
        par_layout.addWidget(self.par_edit)
        
        # Adicionando QLabel e QComboBox para Prioridade
        self.prioridade_combo = QComboBox()
        self.prioridade_combo.addItems(["Necessário", "Urgente", "Desejável"])
        self.prioridade_combo.setFixedWidth(100)
        self.apply_widget_style(self.prioridade_combo)
        par_layout.addWidget(self.prioridade_combo)

        cep_label = QLabel("CEP:")
        self.cep_edit = QLineEdit(str(data.get('cep', '')))
        self.cep_edit.setFixedWidth(120)
        self.apply_widget_style(cep_label)
        self.apply_widget_style(self.cep_edit)
        par_layout.addWidget(cep_label)
        par_layout.addWidget(self.cep_edit)
        
        setor_responsavel_layout.addLayout(par_layout)

        # Endereço
        endereco_layout = QHBoxLayout()
        endereco_label = QLabel("Endereço:")
        self.endereco_edit = QLineEdit(data['endereco'])
        self.apply_widget_style(endereco_label)
        self.apply_widget_style(self.endereco_edit)
        endereco_layout.addWidget(endereco_label)
        endereco_layout.addWidget(self.endereco_edit)
        setor_responsavel_layout.addLayout(endereco_layout)

        # E-mail
        email_telefone_layout = QHBoxLayout()
        email_label = QLabel("E-mail:")
        self.email_edit = QLineEdit(data['email'])
        self.email_edit.setFixedWidth(250)
        self.apply_widget_style(email_label)
        self.apply_widget_style(self.email_edit)
        email_telefone_layout.addWidget(email_label)
        email_telefone_layout.addWidget(self.email_edit)

        # Telefone
        telefone_label = QLabel("Tel:")
        self.telefone_edit = QLineEdit(data['telefone'])
        self.telefone_edit.setFixedWidth(120)
        self.apply_widget_style(telefone_label)
        self.apply_widget_style(self.telefone_edit)
        email_telefone_layout.addWidget(telefone_label)
        email_telefone_layout.addWidget(self.telefone_edit)
        setor_responsavel_layout.addLayout(email_telefone_layout)

        setor_responsavel_group_box.setLayout(setor_responsavel_layout)

        # Dias e horário para Recebimento
        dias_layout = QHBoxLayout()
        dias_label = QLabel("Dias para Recebimento:")
        self.dias_edit = QLineEdit("Segunda à Sexta")
        self.apply_widget_style(dias_label)
        self.apply_widget_style(self.dias_edit)
        dias_layout.addWidget(dias_label)
        dias_layout.addWidget(self.dias_edit)
        setor_responsavel_layout.addLayout(dias_layout)

        horario_layout = QHBoxLayout()
        horario_label = QLabel("Horário para Recebimento:")
        self.horario_edit = QLineEdit("09 às 11h20 e 14 às 16h30")
        self.apply_widget_style(horario_label)
        self.apply_widget_style(self.horario_edit)
        horario_layout.addWidget(horario_label)
        horario_layout.addWidget(self.horario_edit)
        setor_responsavel_layout.addLayout(horario_layout)

        pesquisa_preco_layout = QHBoxLayout()
        pesquisa_preco_label = QLabel("Pesquisa de Preço Concomitante?")
        self.radio_pesquisa_sim = QRadioButton("Sim")
        self.radio_pesquisa_nao = QRadioButton("Não")
        pesquisa_preco_value = data.get('pesquisa_preco', 'Não')  # Define 'Não' como padrão
        self.radio_pesquisa_sim.setChecked(pesquisa_preco_value == 'Sim')
        self.radio_pesquisa_nao.setChecked(pesquisa_preco_value != 'Sim')  # Marca 'Não' se não for 'Sim'
        pesquisa_preco_layout.addWidget(pesquisa_preco_label)
        pesquisa_preco_layout.addWidget(self.radio_pesquisa_sim)
        pesquisa_preco_layout.addWidget(self.radio_pesquisa_nao)
        setor_responsavel_layout.addLayout(pesquisa_preco_layout)
        
        setor_responsavel_group_box.setLayout(setor_responsavel_layout)

        self.frame2_layout.addWidget(setor_responsavel_group_box)
        self.carregarAgentesResponsaveis()
        
    def fill_frame_classificacao_orcamentaria(self):
        data = self.extract_registro_data()

        classificacao_orcamentaria_group_box = QGroupBox("Classificação Orçamentária")
        self.apply_widget_style(classificacao_orcamentaria_group_box)
        classificacao_orcamentaria_layout = QVBoxLayout()

        # Ação Interna
        valor_estimado_layout = QHBoxLayout()
        valor_estimado_label = QLabel("Valor Estimado:")
        valor_total = data['valor_total'] if pd.notna(data['valor_total']) else ""
        self.valor_edit = QLineEdit(str(valor_total))
        self.apply_widget_style(valor_estimado_label)
        self.apply_widget_style(self.valor_edit)
        valor_estimado_layout.addWidget(valor_estimado_label)
        valor_estimado_layout.addWidget(self.valor_edit)
        classificacao_orcamentaria_layout.addLayout(valor_estimado_layout)

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

        custeio_layout = QHBoxLayout()
        custeio_label = QLabel("Atividade de Custeio?")
        self.radio_custeio_sim = QRadioButton("Sim")
        self.radio_custeio_nao = QRadioButton("Não")
        atividade_custeio_value = data.get('atividade_custeio', 'Não')  # Define 'Não' como padrão
        self.radio_custeio_sim.setChecked(atividade_custeio_value == 'Sim')
        self.radio_custeio_nao.setChecked(atividade_custeio_value != 'Sim')  # Marca 'Não' se não for 'Sim'
        custeio_layout.addWidget(custeio_label)
        custeio_layout.addWidget(self.radio_custeio_sim)
        custeio_layout.addWidget(self.radio_custeio_nao)
        classificacao_orcamentaria_layout.addLayout(custeio_layout)

        classificacao_orcamentaria_group_box.setLayout(classificacao_orcamentaria_layout)

        self.frame_classificacao_orcamentaria_layout.addWidget(classificacao_orcamentaria_group_box)

    def create_callback(self, tooltip, function):
        def callback():
            self.selected_button = tooltip.strip()  # Atualiza o botão selecionado
            self.update_button_styles()  # Atualiza os estilos dos botões
            self.title_updated.emit(tooltip)  # Emite um sinal com o título atualizado
            self.button_changed.emit(tooltip)  # Emite um sinal de mudança de botão
            function()  # Chama a função associada
        return callback

    def update_button_styles(self):
        # Debugging: Verificar o valor de self.selected_button
        print(f"Botão selecionado atual: '{self.selected_button}'")
        # Percorrer todos os widgets no layout do menu e aplicar o estilo adequado
        for i in range(self.menu_layout.count()):
            widget = self.menu_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                # Usar strip() para garantir que não há espaços extras
                selected = (widget.text().strip() == self.selected_button.strip())
                self.apply_button_style(widget, selected)
                print(f"Estilo aplicado em '{widget.text()}': {'Selecionado' if selected else 'Não selecionado'}")
                widget.update()  # Forçar a atualização do estilo do widget

    def fill_frame4(self):
        self.menu_layout = QVBoxLayout()
        self.sigdem_layout = QVBoxLayout()

        button_texts = [
            "Abertura de Processo",
            "Documentos",
            "Aviso de Dispensa",
            "Lista de Verificação",
            "Dados Adicionais",
            "Configurações"
        ]

        for text in button_texts:
            button = self.create_button(
                text,
                callback=lambda checked, text=text: self.button_clicked(text) if not checked else None,  # Corrigido para garantir que o sinal seja capturado corretamente
                button_size=QSize(270, 35)
            )
            self.apply_button_style(button, selected=(text == self.selected_button))
            self.menu_layout.addWidget(button)

        icon_pdf = QIcon(str(self.ICONS_DIR / "pdf.png"))
        self.special_button = self.create_button("Selecionar Opção", icon=icon_pdf, button_size=QSize(270, 60))
        self.special_button.setIconSize(QSize(48, 48))  # Configura o tamanho do ícone
        self.apply_dark_red_style(self.special_button)
        self.menu_layout.addWidget(self.special_button)

        self.update_special_button(self.selected_button)
        self.reapply_special_button_style()

        h_layout = QHBoxLayout()
        h_layout.addLayout(self.menu_layout, 1)
        h_layout.addLayout(self.painel_layout, 2)
        h_layout.addLayout(self.sigdem_layout, 1)
        self.frame4_layout.addLayout(h_layout)

    def button_clicked(self, text):
        if isinstance(text, str):
            cleaned_text = text.strip()
            self.selected_button = cleaned_text
            self.update_special_button(cleaned_text)
            self.update_painel_layout(cleaned_text)
            self.update_button_styles()
            self.reapply_special_button_style()  # Garante que o estilo seja reaplicado após atualizações
            print(f"Botão '{cleaned_text}' clicado.")
        else:
            print("Tipo de dado inválido recebido: ", type(text))

    def update_special_button(self, selected_button):
        icon_pdf = QIcon(str(self.ICONS_DIR / "pdf.png"))  # Carrega o ícone de PDF
        special_button_texts = {
            "Abertura de Processo": ("Gerar Autorização", self.gerarAutorizacao),
            "Documentos": ("Gerar Documentos", self.gerar_documentos),
            "Aviso de Dispensa": ("Gerar Aviso", self.gerar_aviso),
            "Lista de Verificação": ("Gerar LV", self.gerar_lista),
            "Dados Adicionais": ("Dados Adicionais", self.gerar_lista),
            "Configurações": ("Configurações", self.gerar_configuracoes)
        }
        if selected_button in special_button_texts:
            text, action = special_button_texts[selected_button]
            self.special_button.setText(text)
            self.special_button.setIcon(icon_pdf)  # Configura o ícone do botão
            self.special_button.setIconSize(QSize(48, 48))  # Define o tamanho do ícone
            self.special_button.disconnect()
            self.special_button.clicked.connect(action)
            self.apply_dark_red_style(self.special_button)
            self.reapply_special_button_style()
            print(f"Botão especial configurado para '{text}' com a ação e ícone associados.")
        else:
            print(f"Erro: Texto '{selected_button}' não encontrado no mapeamento de botões especiais.")

    def update_button_styles(self):
        # Este método presume que você mantém o rastreamento do botão selecionado em algum lugar, como self.selected_button
        for i in range(self.menu_layout.count()):
            widget = self.menu_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                selected = (widget.text().strip() == self.selected_button.strip())
                self.apply_button_style(widget, selected)
                print(f"Estilo aplicado em '{widget.text()}': {'Selecionado' if selected else 'Não selecionado'}")

    def reapply_special_button_style(self):
        if hasattr(self, 'special_button'):
            self.apply_dark_red_style(self.special_button)
            print("Estilo vermelho escuro reaplicado ao botão especial.")

    def update_painel_layout(self, selected_button):
        print(f"Atualizando layout para o botão '{selected_button}'.")
        self.clear_layout(self.painel_layout)
        self.clear_layout(self.sigdem_layout)

        if selected_button == "Abertura de Processo":
            self.add_autorizacao_text(self.painel_layout)
        elif selected_button == "Documentos":
            self.add_document_details(self.painel_layout)
        elif selected_button == "Aviso de Dispensa":
            self.add_aviso_dispensation(self.painel_layout)
        elif selected_button == "Lista de Verificação":
            self.add_lista_verificacao(self.painel_layout)
        elif selected_button == "Configurações":
            self.add_configurations(self.painel_layout)

        # Atualize o layout direito com setupGrupoSIGDEM, se aplicável
        self.setupGrupoSIGDEM(self.sigdem_layout, selected_button)

    def clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            widget_to_remove = layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.deleteLater()

    def add_autorizacao_text(self, layout):
        authorization_text = """
            <strong>Instruções para alteração da "Situação" do processo:</strong><br><br>
            Após aprovado pelo Ordenador de Despesas, alterar de <span style="color: orange;">"Planejamento"</span> para <span style="color: orange;">"Aprovado"</span><br>
            Após publicado no PNCP, alterar de <span style="color: orange;">"Aprovado"</span> para <span style="color: orange;">"Sessão Pública"</span><br>
            Após a homologação, alterar de <span style="color: orange;">"Sessão Pública"</span> para <span style="color: orange;">"Homologado"</span><br>
            Após o empenho, alterar de <span style="color: orange;">"Homologado"</span> para <span style="color: orange;">"Concluído"</span>
        """

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(authorization_text)
        text_edit.setStyleSheet("background-color: #050f41; color: white; font-size: 12pt;")
        layout.addWidget(text_edit)

    def add_document_details(self, layout):
        self.document_details_widget = DocumentDetailsWidget(
            self.df_registro_selecionado, 
            self.ordenador_combo.currentData(Qt.ItemDataRole.UserRole), 
            self.responsavel_demanda_combo.currentData(Qt.ItemDataRole.UserRole),
            parent=self
        )
        layout.addWidget(self.document_details_widget)

    def get_document_details(self):
        if self.document_details_widget:
            details = {
                'cp_number': self.document_details_widget.cp_edit.text(),
                'encarregado_obtencao': self.document_details_widget.encarregado_obtencao_edit.text(),
                'responsavel': self.document_details_widget.responsavel_edit.text()
            }
            return details
        return {"cp_number": "", "encarregado_obtencao": "", "responsavel": ""}

    def gerar_documentos(self):
        numero = self.df_registro_selecionado['numero'].iloc[0]
        ano = self.df_registro_selecionado['ano'].iloc[0]
        json_file_name = f"DE_{numero}-{ano}_file_paths.json"
        json_file_path = JSON_DISPENSA_DIR / json_file_name

        # Verifica se o arquivo JSON existe
        if not json_file_path.exists():
            QMessageBox.warning(self, "Arquivo não encontrado", f"O arquivo de controle dos anexos não foi encontrado, por favor selecione os anexos.")
            return

        # Carrega o arquivo JSON
        with open(json_file_path, 'r', encoding='utf-8') as file:
            contents = json.load(file)

        error_messages = []
        
        # Verifica os arquivos PDF listados
        for item in contents:
            if 'children' in item:
                for child in item['children']:
                    pdf_path = child['text'].split(' || ')[-1]
                    if pdf_path.endswith('.pdf'):
                        if not Path(pdf_path).exists():
                            error_messages.append(f"O arquivo PDF não existe: {pdf_path}")
                    else:
                        error_messages.append(f"Não há PDF vinculado ao anexo '{child['text'].split(' - ')[0]}'")

        if error_messages:
            error_report = '\n'.join(error_messages)
            QMessageBox.warning(self, "Erro ao verificar PDFs", error_report)

        document_details = self.get_document_details()
        ordenador_de_despesas = self.ordenador_combo.currentData(Qt.ItemDataRole.UserRole)
        responsavel_pela_demanda = self.responsavel_demanda_combo.currentData(Qt.ItemDataRole.UserRole)
        
        # Continuação do processo...
        self.consolidador.gerar_comunicacao_padronizada(ordenador_de_despesas, responsavel_pela_demanda, document_details)

    def add_aviso_dispensation(self, layout):
        aviso_text = """
            Instruções para Aviso de Dispensa
        """
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(aviso_text)
        text_edit.setStyleSheet("background-color: #050f41; color: white; font-size: 12pt;")
        layout.addWidget(text_edit)
    
    def add_lista_verificacao(self, layout):
        lista_text = """
            Instruções para Lista de Verificação
        """
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(lista_text)
        text_edit.setStyleSheet("background-color: #050f41; color: white; font-size: 12pt;")
        layout.addWidget(text_edit)
    
    def add_configurations(self, layout):
        configurations_text = """
            Configurações do Sistema
        """
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(configurations_text)
        text_edit.setStyleSheet("background-color: #050f41; color: white; font-size: 12pt;")
        layout.addWidget(text_edit)
                
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

    def setupGrupoSIGDEM(self, layout_direita, selected_button):
        self.clear_layout(layout_direita)  # Adicione esta linha para limpar o layout antes de adicionar novos widgets
        
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
        assunto_text = self.get_assunto_text(selected_button)
        self.textEditAssunto.setPlainText(assunto_text)
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
        sinopse_text = self.get_sinopse_text(selected_button)
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

    def get_assunto_text(self, selected_button):
        if selected_button == "Abertura de Processo":
            return f"{self.id_processo} – Autorização para Abertura de Processo de Dispensa Eletrônica"
        elif selected_button == "Documentos":
            return f"{self.id_processo} – Documentos de Planejamento"
        elif selected_button == "Aviso de Dispensa":
            return f"{self.id_processo} – Aviso de Dispensa Eletrônica"
        elif selected_button == "Lista de Verificação":
            return f"{self.id_processo} – Lista de Verificação"
        else:
            return ""

    def get_sinopse_text(self, selected_button):
        descricao_servico = "aquisição de" if self.material_servico == "Material" else "contratação de empresa especializada em"
        base_text = (
            f"Termo de Abertura referente à {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel}"
        )
        return base_text

    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QToolTip.showText(QCursor.pos(), "Texto copiado para a área de transferência.", msecShowTime=1500)

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
        combo_widget.clear()
        for index, row in agentes_df.iterrows():
            texto_display = f"{row['nome']}\n{row['posto']}\n{row['funcao']}"
            # Armazena um dicionário no UserRole para cada item adicionado ao ComboBox  
            combo_widget.addItem(texto_display, userData=row.to_dict())    

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
        button.update()  # Força a atualização do widget

    def gerar_aviso(self):
        print("Gerando aviso...")

    def gerar_lista(self):
        print("Gerando lista de verificação...")

    def gerar_configuracoes(self):
        print("Gerando configurações...")
        
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

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import re
import locale
from modules.planejamento.utilidades_planejamento import DatabaseManager, carregar_dados_pregao
from diretorios import *
import pandas as pd
import sqlite3

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
        self.setFixedSize(1250, 800)  # Define o tamanho fixo da janela
        self.layout = QVBoxLayout(self)
        
        header_layout = self.update_title_label()
        self.layout.addLayout(header_layout)
        self.setup_frames()

        self.move(QPoint(0, 0))

        # Conectar o sinal ao método de atualização do título
        self.title_updated.connect(self.update_title_label)
        
    def extract_registro_data(self):
        # Extrai dados do registro selecionado
        data = {
            'id_processo': self.df_registro_selecionado['id_processo'].iloc[0],  # Assume que 'id_processo' é a primeira coluna
            'tipo': self.df_registro_selecionado['tipo'].iloc[0],
            'numero': self.df_registro_selecionado['numero'].iloc[0],
            'ano': self.df_registro_selecionado['ano'].iloc[0],
            'nup': self.df_registro_selecionado['nup'].iloc[0],
            'objeto': self.df_registro_selecionado['objeto'].iloc[0],
            'objeto_completo': self.df_registro_selecionado['objeto_completo'].iloc[0],
            'valor_total': self.df_registro_selecionado['valor_total'].iloc[0],
            'uasg': self.df_registro_selecionado['uasg'].iloc[0],
            'orgao_responsavel': self.df_registro_selecionado['orgao_responsavel'].iloc[0],
            'setor_responsavel': self.df_registro_selecionado['setor_responsavel'].iloc[0],
            'operador': self.df_registro_selecionado['operador'].iloc[0],
            'data_sessao': self.df_registro_selecionado['data_sessao'].iloc[0],
            'material_servico': self.df_registro_selecionado['material_servico'].iloc[0],
            'link_pncp': self.df_registro_selecionado['link_pncp'].iloc[0],
            'link_portal_marinha': self.df_registro_selecionado['link_portal_marinha'].iloc[0],
            'comentarios': self.df_registro_selecionado['comentarios'].iloc[0]
        }
        return data
    
    def update_title_label(self):
        data = self.extract_registro_data()
        html_text = (
            f"{data['tipo']} nº {data['numero']}/{data['ano']} - Edição de Dados<br>"
            f"<span style='font-size: 20px; color: #ADD8E6;'>OM RESPONSÁVEL: {data['orgao_responsavel']} (UASG: {data['uasg']})</span>"
        )
        if not hasattr(self, 'titleLabel'):
            self.titleLabel = QLabel()
            self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
            self.titleLabel.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")

        self.titleLabel.setText(html_text)
        print(f"Title updated: {html_text}")

        if not hasattr(self, 'header_layout'):
            self.header_layout = QHBoxLayout()
            self.header_layout.addWidget(self.titleLabel)
            self.header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            self.add_action_buttons(self.header_layout)
            pixmap = QPixmap(str(MARINHA_PATH)).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label = QLabel()
            self.image_label.setPixmap(pixmap)
            self.header_layout.addWidget(self.image_label)

        return self.header_layout

    def add_action_buttons(self, layout):
        icon_confirm = QIcon(str(self.ICONS_DIR / "confirm.png"))
        icon_x = QIcon(str(self.ICONS_DIR / "cancel.png"))
        
        button_confirm = self.create_button("  Salvar", icon_confirm, self.save_changes, "Salvar dados", QSize(130, 50), QSize(40, 40))
        button_x = self.create_button("  Cancelar", icon_x, self.reject, "Cancelar alterações e fechar", QSize(130, 50), QSize(30, 30))
        
        layout.addWidget(button_confirm)
        layout.addWidget(button_x)
        self.apply_widget_style(button_confirm)
        self.apply_widget_style(button_x)

    def create_button(self, text, icon, callback, tooltip_text, button_size=None, icon_size=None):
        btn = QPushButton(text)
        btn.setIcon(icon)
        btn.setIconSize(icon_size if icon_size else QSize(40, 40))
        if button_size:
            btn.setFixedSize(button_size)
        btn.setToolTip(tooltip_text)
        btn.clicked.connect(callback)
        return btn

    def setup_frames(self):
        # Configura os layouts horizontais para os frames
        topRow = QHBoxLayout()
        self.frame1, self.frame1_layout = self.create_frame()
        self.frame2, self.frame2_layout = self.create_frame()
        topRow.addWidget(self.frame1)
        topRow.addWidget(self.frame2)
        self.layout.addLayout(topRow)  # Adiciona o QHBoxLayout com os dois frames ao layout principal

        linhaDeBaixo = QVBoxLayout()
        self.frame3, self.frame3_layout = self.create_frame()
        self.frame4, self.frame4_layout = self.create_frame()
        linhaDeBaixo.addWidget(self.frame3)
        linhaDeBaixo.addWidget(self.frame4)
        self.layout.addLayout(linhaDeBaixo)  # Adiciona o QHBoxLayout com os três frames ao layout principal

        # Preenche os frames com os campos apropriados
        self.fill_frame1()
        self.fill_frame2()
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
        widget.setStyleSheet("font-size: 14pt;") 

    def fill_frame1(self):
        data = self.extract_registro_data()
        # Layouts detalhados
        detalhes_layout = QHBoxLayout()

        # Grupo para ID do Processo
        id_group_box = QGroupBox("ID")
        id_group_layout = QVBoxLayout()
        self.id_processo_edit = QLineEdit(data['id_processo'])
        self.apply_widget_style(id_group_box)
        self.apply_widget_style(self.id_processo_edit)
        self.id_processo_edit.setReadOnly(True)
        self.id_processo_edit.setFixedWidth(120)
        id_group_layout.addWidget(self.id_processo_edit)
        id_group_box.setLayout(id_group_layout)
        detalhes_layout.addWidget(id_group_box)

        # Grupo para NUP
        nup_group_box = QGroupBox("NUP")
        nup_group_layout = QVBoxLayout()
        self.nup_edit = QLineEdit(data['nup'])
        self.apply_widget_style(nup_group_box)
        self.apply_widget_style(self.nup_edit)
        self.nup_edit.setReadOnly(False)
        self.nup_edit.setFixedWidth(230)
        nup_group_layout.addWidget(self.nup_edit)
        nup_group_box.setLayout(nup_group_layout)
        detalhes_layout.addWidget(nup_group_box)

        # Grupo para Objeto
        objeto_group_box = QGroupBox("Objeto")
        objeto_group_layout = QVBoxLayout()
        self.objeto_edit = QLineEdit(data['objeto'])
        self.apply_widget_style(objeto_group_box)
        self.apply_widget_style(self.objeto_edit)
        self.objeto_edit.setReadOnly(False)
        self.objeto_edit.setFixedWidth(280)
        objeto_group_layout.addWidget(self.objeto_edit)
        objeto_group_box.setLayout(objeto_group_layout)
        detalhes_layout.addWidget(objeto_group_box)

        # Adicionar o layout horizontal ao layout principal do frame
        self.frame1_layout.addLayout(detalhes_layout)

        # Detalhes adicionais para Objeto Detalhado
        objeto_det_group_box = QGroupBox("Objeto Detalhado")
        objeto_det_layout = QVBoxLayout()
        self.objeto_det_edit = QLineEdit(data['objeto_completo'])
        self.apply_widget_style(objeto_det_group_box)
        self.apply_widget_style(self.objeto_det_edit)
        self.objeto_det_edit.setReadOnly(False)
        objeto_det_layout.addWidget(self.objeto_det_edit)
        objeto_det_group_box.setLayout(objeto_det_layout)
        self.frame1_layout.addWidget(objeto_det_group_box)

        # Detalhes adicionais para Link PNCp
        link_pncp_group_box = QGroupBox("Link PNCP")
        link_pncp_layout = QVBoxLayout()
        self.link_pncp_edit = QLineEdit(data['link_pncp'])
        self.apply_widget_style(link_pncp_group_box)
        self.apply_widget_style(self.link_pncp_edit)
        self.link_pncp_edit.setReadOnly(False)
        link_pncp_layout.addWidget(self.link_pncp_edit)
        link_pncp_group_box.setLayout(link_pncp_layout)
        self.frame1_layout.addWidget(link_pncp_group_box)

        # Detalhes adicionais para Link Portal Marinha
        link_portal_group_box = QGroupBox("Link Portal Marinha")
        link_portal_layout = QVBoxLayout()
        self.link_portal_edit = QLineEdit(data['link_portal_marinha'])
        self.apply_widget_style(link_portal_group_box)
        self.apply_widget_style(self.link_portal_edit)
        self.link_portal_edit.setReadOnly(False)
        link_portal_layout.addWidget(self.link_portal_edit)
        link_portal_group_box.setLayout(link_portal_layout)
        self.frame1_layout.addWidget(link_portal_group_box)
        
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

        # Adicionando valor_estimado_group_box e om_group_box ao layout horizontal
        valor_estimado_om_layout.addWidget(valor_estimado_group_box)
        valor_estimado_om_layout.addWidget(om_group_box)

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
        self.operador_edit.setFixedWidth(220)
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
        self.data_edit.setFixedWidth(220)
        data_sessao_layout.addWidget(self.data_edit)
        data_sessao_group_box.setLayout(data_sessao_layout)
        operador_data_layout.addWidget(data_sessao_group_box)

        # Adicionar o layout horizontal ao layout principal do frame2
        self.frame2_layout.addLayout(operador_data_layout)

        # Material/Serviço
        material_group_box = QGroupBox("Material/Serviço")
        material_layout = QVBoxLayout()
        self.material_edit = QComboBox()
        self.material_edit.addItems(["Material", "Serviço"])
        self.material_edit.setCurrentText(data.get('material_servico', 'Material'))
        self.apply_widget_style(material_group_box)
        self.apply_widget_style(self.material_edit)
        self.material_edit.setFixedWidth(220)
        material_layout.addWidget(self.material_edit)
        material_group_box.setLayout(material_layout)
        material_situacao_layout.addWidget(material_group_box)

        # Situação
        situacao_group_box = QGroupBox("Situação")
        situacao_layout = QVBoxLayout()
        self.situacao_edit = QComboBox()
        self.situacao_edit.addItems(["Planejamento", "Aprovado", "Sessão Publica", "Concluído"])
        self.situacao_edit.setCurrentText(data.get('situacao', 'Planejamento'))
        self.apply_widget_style(situacao_group_box)
        self.apply_widget_style(self.situacao_edit)
        self.situacao_edit.setFixedWidth(220)
        situacao_layout.addWidget(self.situacao_edit)
        situacao_group_box.setLayout(situacao_layout)
        material_situacao_layout.addWidget(situacao_group_box)

        # Adicionar o layout horizontal ao layout principal do frame2
        self.frame2_layout.addLayout(material_situacao_layout)

    def fill_frame3(self):
        # Define o fundo específico para frame3
        self.frame3.setObjectName("fill_frame3")
        self.frame3.setStyleSheet("#fill_frame3 { background-color: #050f41; }")
        
        # Adiciona o título antes dos botões
        html_text = "Gerar Documentos:"
        title_label = QLabel(html_text)
        title_label.setTextFormat(Qt.TextFormat.RichText)
        title_label.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        self.frame3_layout.addWidget(title_label)
        
        button_texts = [
            "Abertura de Processo",
            "Documentos de Planejamento",
            "Aviso de Dispensa Eletrônica"
        ]
        tooltips = [
            "Autorização para abertura do processo de Dispensa Eletrônica",
            "Documentos de Planejamento (CP, DFD, TR, etc.)",
            "Aviso de dispensa eletrônica"
        ]
        button_callbacks = [self.teste, self.teste, self.teste]  # Substitua por funções específicas

        button_layout = QHBoxLayout()
        
        for text, tooltip, callback in zip(button_texts, tooltips, button_callbacks):
            button = self.create_button(text, QIcon(), callback, tooltip, QSize(400, 50))
            self.apply_button_style(button)
            button_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.frame3_layout.addLayout(button_layout)


    def apply_button_style(self, widget):
        widget.setStyleSheet("""
            QPushButton, QPushButton::tooltip {
                font-size: 14pt; 
            }
            QPushButton {
                background-color: #B4B7C6;
                border: none;  
                border-radius: 5px;  
                padding: 5px;  
            }
            QPushButton:hover {  
                background-color: #A0A4B1;
                border: 1px solid #0078D4;  
            }
        """)

    def teste(self):
        print("Teste")

    def fill_frame4(self):
        # Define o fundo específico para frame4
        self.frame4.setObjectName("fill_frame4")
        self.frame4.setStyleSheet("#fill_frame4 { background-color: #050f41; }")
        
        # Criação de um QTextEdit com 4 linhas
        text_edit = QTextEdit()
        text_edit.setFixedHeight(100)  # Aproximadamente 4 linhas de altura
        text_edit.setStyleSheet("color: white; font-size: 14pt; background-color: #1e2a56;")
        
        self.frame4_layout.addWidget(text_edit)


    def fill_frame5(self):
        # Criar botão com ícone
        button = self.create_button("", QIcon(str(self.ICONS_DIR / "pdf128.png")), self.teste, "Aviso de dispensa eletrônica", QSize(100, 100), QSize(80, 80))
        self.frame5_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Criar label abaixo do botão
        label = QLabel("Aviso de dispensa eletrônica")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame5_layout.addWidget(label)
        self.apply_button_style(button)  # Aplica o estilo ao botão
        self.apply_widget_style(label)   # Aplica o estilo ao rótulo

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
            'orgao_responsavel': self.df_registro_selecionado.loc[self.df_registro_selecionado.index[0], 'orgao_responsavel']  # Inclui orgao_responsavel
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
        self.accept()

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



from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import pandas as pd
import subprocess
from docxtpl import DocxTemplate
from modules.planejamento.utilidades_planejamento import remover_caracteres_especiais
import sys
import shutil
import tempfile
import os
from win32com.client import Dispatch
import time
import sqlite3

import traceback
import logging

class AutorizacaoAberturaLicitacaoDialog(QDialog):
    def __init__(self, main_app, config_manager, df_registro, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.config_manager = config_manager 
        self.df_registro = df_registro

        if self.df_registro.empty or self.df_registro is None:
            QMessageBox.warning(self, "Dados Insuficientes", "Não há dados disponíveis para criar o documento.")
            self.close()
            return

        if 'id_processo' in self.df_registro.columns and not pd.isnull(self.df_registro['id_processo'].iloc[0]):
            self.setup_dialog()
        else:
            QMessageBox.critical(self, "Erro", "Dados essenciais estão faltando no registro fornecido.")
            self.close()
            return
        
        self.setup_ui()
        self.aplicar_estilos()
        self.setLayout(self.layoutPrincipal)
        
        self.config_manager.config_updated.connect(self.update_save_location)
        self.pasta_base = Path(self.config_manager.get_config('save_location', str(Path.home() / 'Desktop')))

    def setup_dialog(self):
        try:
            id_processo_original = self.df_registro['id_processo'].iloc[0]
            self.id_processo = id_processo_original.replace('/', '-')

            # Mapeamento do tipo
            tipo_map = {
                "PE": "Pregão Eletrônico",
                "CC": "Concorrência",
                "TJDL": "Termo de Justificativa de Dispensa de Licitação",
                "TJIL": "Termo de Justificativa de Inexigibilidade de Licitação"
            }

            # Aplica o mapeamento ao tipo no DataFrame
            self.df_registro['tipo'] = self.df_registro['tipo'].replace(tipo_map)

            self.tipo = self.df_registro['tipo'].iloc[0]
            self.numero = self.df_registro['numero'].iloc[0]
            self.ano = self.df_registro['ano'].iloc[0]
            self.objeto = self.df_registro['objeto'].iloc[0]
            self.nup = self.df_registro['nup'].iloc[0]
            self.item_pca = self.df_registro['item_pca'].iloc[0]
            self.setor_responsavel = self.df_registro['setor_responsavel'].iloc[0]
            self.coordenador_planejamento = self.df_registro['coordenador_planejamento'].iloc[0]
            self.uasg = self.df_registro['uasg'].iloc[0]
            self.sigla_om = self.df_registro['sigla_om'].iloc[0]
            self.material_servico = self.df_registro['material_servico'].iloc[0]
            self.pregoeiro = self.df_registro['pregoeiro'].iloc[0]
            self.setWindowTitle("Autorização para abertura de processo administrativo")
            self.setFixedSize(1250, 550)
            self.setup_ui()  # Setup the UI components
        except KeyError as e:
            QMessageBox.critical(self, "Erro de Dados", f"Faltam dados obrigatórios: {e}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Erro Inesperado", f"Um erro inesperado ocorreu: {str(e)}")
            return    
        
    def update_save_location(self, key, new_path):
        if key == 'save_location':
            self.pasta_base = new_path
            print(f"Local de salvamento atualizado para: {self.pasta_base}")

    def cabecalho_layout(self):
        try:
            header_layout = QHBoxLayout()
            title_text = f"{self.tipo} nº {self.numero}/{self.ano}"
            objeto_text = f"Objeto: {self.objeto}"
            title_label = QLabel(f"<div style='font-size: 32px; font-weight: bold;'>{title_text}</div>"
                                f"<div style='font-size: 22px; font-style: italic;'>{objeto_text}</div>")
            header_layout.addWidget(title_label)
            header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            self.add_action_buttons(header_layout)
            pixmap = QPixmap(str(MARINHA_PATH))
            pixmap = pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            header_layout.addWidget(image_label)
            return header_layout
        except Exception as e:
            print(f"Erro ao construir o cabeçalho: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao construir o cabeçalho: {e}")
            return None

    def setup_ui(self):
        self.setWindowTitle("Autorização para Abertura de Processo Administrativo")
        self.setFixedSize(1250, 550)

        self.layoutPrincipal = QVBoxLayout()
        self.layoutPrincipal.addLayout(self.cabecalho_layout())

        # Configuração dos layouts de widgets lado a lado
        horizontal_layout = QHBoxLayout()
        self.widgetEsquerda = QWidget()
        self.widgetDireita = QWidget()

        self.widgetEsquerda.setFixedSize(430, 420)
        self.widgetDireita.setFixedSize(800, 420)

        self.layoutEsquerda = QVBoxLayout(self.widgetEsquerda)
        self.layoutDireita = QVBoxLayout(self.widgetDireita)

        horizontal_layout.addWidget(self.widgetEsquerda)
        horizontal_layout.addWidget(self.widgetDireita)

        self.layoutPrincipal.addLayout(horizontal_layout)  # Adiciona abaixo do cabeçalho

        self.createGroups()
        self.addWidgetsToLeftLayout()
        self.addWidgetsToRightLayout()
        self.applyWidgetStyles()

    def add_action_buttons(self, layout):
        # Caminhos para os ícones
        icon_word = QIcon(str(ICONS_DIR / "word.png"))  # Caminho para o ícone de Word
        icon_pdf = QIcon(str(ICONS_DIR / "pdf64.png"))  # Caminho para o ícone de PDF

        # Botões
        button_gerar_word = self.create_button("  Gerar DOCX  ", icon_word, self.gerarDocx, "Gerar arquivo Word")
        button_gerar_pdf = self.create_button("  Gerar PDF  ", icon_pdf, self.gerarPdf, "Gerar arquivo PDF")

        # Adicionando os botões ao layout
        layout.addWidget(button_gerar_word)
        layout.addWidget(button_gerar_pdf)

    def create_button(self, text, icon, callback, tooltip_text, icon_size=None):
        btn = QPushButton(text)
        btn.setIcon(icon)
        # Define o tamanho do ícone com um valor padrão de QSize(40, 40) se nenhum tamanho for especificado
        if icon_size is None:
            icon_size = QSize(40, 40)
        btn.setIconSize(icon_size)
        btn.clicked.connect(callback)
        btn.setToolTip(tooltip_text)
        return btn

    def aplicar_estilos(self):
        self.setStyleSheet("""
            QLabel, QPushButton, QLineEdit, QTextEdit {
                font-size: 16px;
            }
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid gray;
                border-radius: 5px;
                margin-top: 0.5em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)

    def createGroups(self):
        self.grupoAutoridade = QGroupBox("Autoridade Competente")
        self.grupoSelecaoPasta = QGroupBox("Local de Salvamento do Arquivo")
        self.grupoEdicaoTemplate = QGroupBox("Edição do Modelo")
        self.grupoSIGDEM = QGroupBox("SIGDEM")

        # Aqui, você pode configurar o layout de cada grupo e adicionar os widgets específicos.
        # Por exemplo:
        self.setupGrupoAutoridade()
        self.setupGrupoSelecaoPasta()
        self.setupGrupoEdicaoTemplate()
        self.setupGrupoSIGDEM()

    def setupGrupoAutoridade(self):
        layout = QVBoxLayout(self.grupoAutoridade)
        labelOD = QLabel("Selecionar o Ordenador de Despesa:")
        
        self.ordenadordespesasComboBox = QComboBox()
        self.ordenadordespesasComboBox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.ordenadordespesasComboBox.setFixedHeight(30)  # Define a altura para o ComboBox
        self.ordenadordespesasComboBox.setStyleSheet("QComboBox { font-size: 18px; height: 30px; }")  # Aplique o estilo diretamente
        
        self.carregarOrdenadorDespesas()
        
        layout.addWidget(labelOD)
        vertical_spacer = QSpacerItem(5, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(vertical_spacer)
        layout.addWidget(self.ordenadordespesasComboBox)
        layout.addItem(vertical_spacer)
        
        self.ordenadordespesasComboBox.updateGeometry()
        self.update()



    def setupGrupoSelecaoPasta(self):
        layout = QVBoxLayout(self.grupoSelecaoPasta)
        labelPasta = QLabel("Selecionar pasta para salvar o arquivo:")
        layout.addWidget(labelPasta)

        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        icon_folder = QIcon(str(ICONS_DIR / "folder128.png"))  # Ajuste o ícone conforme necessário
        botaoSelecionarPasta = self.create_button("  Selecionar Pasta  ", icon_folder, self.selecionarPasta, "Escolha uma pasta para salvar os arquivos")
        button_layout.addWidget(botaoSelecionarPasta)
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        layout.addLayout(button_layout)
        vertical_spacer = QSpacerItem(5, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(vertical_spacer)

    def setupGrupoEdicaoTemplate(self):
        layout = QVBoxLayout(self.grupoEdicaoTemplate)
        labelEdicao = QLabel("Editar o arquivo modelo de Autorização:")
        layout.addWidget(labelEdicao)

        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        iconPathEdit = QIcon(str(ICONS_DIR / "text.png"))  # Caminho para o ícone de Word
        botaoEdicaoTemplate = self.create_button("    Editar Modelo   ", iconPathEdit, self.editarTemplate, "Clique para abrir o arquivo modelo de Autorização para edição")
        button_layout.addWidget(botaoEdicaoTemplate)
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        layout.addLayout(button_layout)
        vertical_spacer = QSpacerItem(5, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(vertical_spacer)

    def setupGrupoSIGDEM(self):
        layout = QVBoxLayout(self.grupoSIGDEM)

        # Mapa de abreviações
        abrev_map = {
            "Pregão Eletrônico": "PE",
            "Concorrência": "CC",
            "Dispensa Eletrônica": "DE",
            "Termo de Justificativa de Dispensa de Licitação": "TJDL",
            "Termo de Justificativa de Inexigibilidade de Licitação": "TJIL"
        }

        # Obtenção da abreviação para self.tipo
        tipo_abreviado = abrev_map.get(self.tipo, self.tipo)  # Retorna self.tipo se não houver abreviação

        # Campo "Assunto"
        labelAssunto = QLabel("No campo “Assunto”, deverá constar:")
        layout.addWidget(labelAssunto)
        textEditAssunto = QTextEdit()
        textEditAssunto.setPlainText(f"{tipo_abreviado} {self.numero}/{self.ano} – Autorização para Abertura de Processo Administrativo")
        textEditAssunto.setMaximumHeight(50)

        icon_copy = QIcon(str(ICONS_DIR / "copy_1.png"))  # Caminho para o ícone de Word
        btnCopyAssunto = self.create_button("Copiar", icon_copy, lambda: self.copyToClipboard(textEditAssunto.toPlainText()), "Copiar texto para a área de transferência", QSize(25, 25))

        layoutHAssunto = QHBoxLayout()
        layoutHAssunto.addWidget(textEditAssunto)
        layoutHAssunto.addWidget(btnCopyAssunto)
        layout.addLayout(layoutHAssunto)

        # Campo "Sinopse"
        labelSinopse = QLabel("No campo “Sinopse”, deverá constar:")
        layout.addWidget(labelSinopse)
        textEditSinopse = QTextEdit()

        # Definir descrição com base em material_servico
        descricao_servico = "aquisição de" if self.material_servico == "material" else "contratação de empresa especializada em"
        sinopse_text = (f"Termo de Abertura referente ao {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
                        f"Processo Administrativo NUP: {self.nup}\n"
                        f"Item do PCA: {self.item_pca}")
        textEditSinopse.setPlainText(sinopse_text)
        textEditSinopse.setMaximumHeight(100)
        btnCopySinopse = self.create_button("Copiar", icon_copy, lambda: self.copyToClipboard(textEditSinopse.toPlainText()), "Copiar texto para a área de transferência", QSize(25, 25))
        layoutHSinopse = QHBoxLayout()
        layoutHSinopse.addWidget(textEditSinopse)
        layoutHSinopse.addWidget(btnCopySinopse)
        layout.addLayout(layoutHSinopse)

         # Campo "Observações"
        labelObservacoes = QLabel("No campo “Observações”, deverá constar:")
        layout.addWidget(labelObservacoes)
        textEditObservacoes = QTextEdit()
        textEditObservacoes.setPlainText(f"Setor Demandante: {self.setor_responsavel}\n"
                                         f"Coordenador da Equipe de Planejamento: {self.coordenador_planejamento}\n"
                                         f"OM Líder: {self.uasg} - {self.sigla_om}")
        textEditObservacoes.setMaximumHeight(100)
        btnCopyObservacoes = self.create_button("Copiar", icon_copy, lambda: self.copyToClipboard(textEditObservacoes.toPlainText()), "Copiar texto para a área de transferência", QSize(25, 25))
        layoutHObservacoes = QHBoxLayout()
        layoutHObservacoes.addWidget(textEditObservacoes)
        layoutHObservacoes.addWidget(btnCopyObservacoes)
        layout.addLayout(layoutHObservacoes)

         # Campo "Temporalidade"
        labelTemporalidade = QLabel("Temporalidade: 004")
        layout.addWidget(labelTemporalidade)  

        labelTramitacao = QLabel("Tramitação: 30>02>MSG>30>Setor Demandante")
        layout.addWidget(labelTramitacao)  


    def addWidgetsToLeftLayout(self):
        self.layoutEsquerda.addWidget(self.grupoAutoridade)
        self.layoutEsquerda.addWidget(self.grupoSelecaoPasta)
        self.layoutEsquerda.addWidget(self.grupoEdicaoTemplate)
        # self.layoutEsquerda.addWidget(self.grupoCriacaoDocumento)

    def addWidgetsToRightLayout(self):
        self.layoutDireita.addWidget(self.grupoSIGDEM)

    def applyWidgetStyles(self):
        estiloBorda = "QGroupBox { border: 1px solid gray; border-radius: 5px; margin-top: 0.5em; } " \
                      "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }"
        self.grupoAutoridade.setStyleSheet(estiloBorda)
        self.grupoSelecaoPasta.setStyleSheet(estiloBorda)
        self.grupoEdicaoTemplate.setStyleSheet(estiloBorda)
        # self.grupoCriacaoDocumento.setStyleSheet(estiloBorda)
        self.grupoSIGDEM.setStyleSheet(estiloBorda)

    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        # Mostra a tooltip na posição atual do mouse
        QToolTip.showText(QCursor.pos(), "Texto copiado para a área de transferência.", msecShowTime=1500)

    def editarTemplate(self):
        template_path = TEMPLATE_PLANEJAMENTO_DIR / "template_autorizacao.docx"

        if sys.platform == "win32":
            os.startfile(template_path)  # Abrir o documento
        else:
            subprocess.run(["xdg-open", str(template_path)])  # Abrir o documento no Linux ou MacOS

    def carregarOrdenadorDespesas(self):
        # Tentar conectar ao banco de dados e carregar a tabela controle_agentes_responsaveis
        try:
            with sqlite3.connect(CONTROLE_DADOS) as conn:
                # Verificar se a tabela existe
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_agentes_responsaveis'")
                exists = cursor.fetchone()

                if not exists:
                    raise Exception("A tabela 'controle_agentes_responsaveis' não existe no banco de dados. Configure os Ordenadores de Despesa no Módulo 'Configurações'.")

                # Carregar apenas os dados relevantes da tabela em um DataFrame
                sql_query = """
                SELECT * FROM controle_agentes_responsaveis
                WHERE funcao LIKE 'Ordenador de Despesa%' OR funcao LIKE 'Ordenador de Despesa Substituto%'
                """
                self.ordenador_despesas_df = pd.read_sql_query(sql_query, conn)

            # Adicionar os itens ao comboBox
            self.ordenadordespesasComboBox.clear()  # Limpar o comboBox antes de adicionar novos itens
            for index, row in self.ordenador_despesas_df.iterrows():
                texto_display = f"{row['nome']}\n{row['posto']}\n{row['funcao']}"
                self.ordenadordespesasComboBox.addItem(texto_display, userData=row.to_dict())

        except Exception as e:
            print(f"Erro ao carregar Ordenadores de Despesas: {e}")

    def selecionarPasta(self):
        pasta_selecionada = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if pasta_selecionada:
            self.pasta_base = pasta_selecionada
            print(f"Pasta selecionada: {self.pasta_base}")

    def gerarDocumento(self, tipo="docx"):
        if self.df_registro is None:
            QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
            return None

        template_path = TEMPLATE_PLANEJAMENTO_DIR / f"template_autorizacao.{tipo}"
        objeto = remover_caracteres_especiais(self.df_registro['objeto'].iloc[0])
        id_processo_original = self.df_registro['id_processo'].iloc[0]
        id_processo_novo = id_processo_original.replace('/', '-')

        nome_pasta = f"{id_processo_novo} - {objeto}"
        subpasta_autorizacao = "1. Autorizacao para abertura de Processo Administrativo"

        pasta_destino = os.path.join(self.pasta_base, nome_pasta)
        subpasta_destino = os.path.join(pasta_destino, subpasta_autorizacao)

        # Verifica e cria a pasta principal se necessário
        if not os.path.exists(pasta_destino):
            try:
                os.makedirs(pasta_destino)
            except Exception as e:
                QMessageBox.warning(None, "Erro", f"Não foi possível criar a pasta destino: {e}")
                return None

        # Verifica e cria a subpasta se necessário
        if not os.path.exists(subpasta_destino):
            try:
                os.makedirs(subpasta_destino)
            except Exception as e:
                QMessageBox.warning(None, "Erro", f"Não foi possível criar a subpasta de autorização: {e}")
                return None

        nome_arquivo = f"{id_processo_novo} - Autorizacao para abertura de Processo Administrativo.{tipo}"
        save_path = os.path.join(subpasta_destino, nome_arquivo)

        # Carregar e renderizar o template DOCX
        try:
            doc = DocxTemplate(template_path)
            nome_selecionado = self.ordenadordespesasComboBox.currentText()
            valor_completo = self.ordenadordespesasComboBox.currentData(Qt.ItemDataRole.UserRole)

            descricao_servico = "aquisição de" if self.material_servico == "material" else "contratação de empresa especializada em"
            data = {
                **self.df_registro.to_dict(orient='records')[0],
                'ordenador_de_despesas': f"{valor_completo['nome']}\n{valor_completo['posto']}\n{valor_completo['funcao']}",
                'descricao_servico': descricao_servico  # Adicionando a descrição do serviço
            }
            doc.render(data)
            doc.save(save_path)
        except Exception as e:
            QMessageBox.warning(None, "Erro", f"Erro ao gerar ou salvar o documento: {e}")
            return None

        return save_path

    def abrirDocumento(self, path):
        pasta_destino = os.path.dirname(path)  # Obter a pasta onde o arquivo está localizado

        if sys.platform == "win32":
            os.startfile(path)  # Abrir o documento
            os.startfile(pasta_destino)  # Abrir a pasta no Windows Explorer
        else:
            subprocess.run(["xdg-open", path])  # Abrir o documento no Linux ou MacOS
            subprocess.run(["xdg-open", pasta_destino])  # Abrir a pasta no gerenciador de arquivos do sistema

    def gerarDocx(self):
        docx_path = self.gerarDocumento("docx")
        if docx_path:
            self.abrirDocumento(docx_path)
        return docx_path

    def gerarPdf(self):
        docx_path = self.gerarDocumento("docx")
        if docx_path is None or not os.path.isfile(docx_path):  # Checa se o arquivo realmente existe
            QMessageBox.warning(None, "Erro", "O arquivo DOCX não existe ou não pode ser acessado.")
            return None

        try:
            # Certifica que está usando o caminho absoluto
            absolute_docx_path = os.path.abspath(docx_path).replace('/', '\\')
            print(f"Caminho absoluto do DOCX: {absolute_docx_path}")

            time.sleep(1)  # Delay para garantir que o arquivo esteja acessível

            word = Dispatch("Word.Application")
            word.visible = False

            # Tenta abrir o documento DOCX
            doc = word.Documents.Open(absolute_docx_path)

            # Define o nome e caminho do PDF
            pdf_name = f"{os.path.splitext(os.path.basename(absolute_docx_path))[0]}.pdf"
            pasta_destino = os.path.dirname(docx_path)  # Pasta onde o DOCX foi salvo
            pdf_path = os.path.join(pasta_destino, pdf_name).replace('/', '\\')
            print(f"Caminho de destino do PDF: {pdf_path}")

            # Exporta para PDF
            doc.SaveAs(pdf_path, FileFormat=17)

            doc.Close(SaveChanges=0)
            word.Quit()

            print(f"Arquivo PDF gerado com sucesso: {pdf_path}")

            # Verifica se o arquivo PDF foi criado
            if not os.path.isfile(pdf_path):
                raise Exception("O arquivo PDF não foi encontrado após a tentativa de criação.")

            self.abrirDocumento(pdf_path)

            return pdf_path
        except Exception as e:
            QMessageBox.warning(None, "Erro", f"Erro ao gerar documento PDF: {e}")
            print(f"Erro ao gerar documento PDF: {e}")
            return None
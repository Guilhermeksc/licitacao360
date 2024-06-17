from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import pandas as pd
import subprocess
from docxtpl import DocxTemplate
import sys
import shutil
import tempfile
import time
import os
from win32com.client import Dispatch
from modules.planejamento.utilidades_planejamento import remover_caracteres_especiais
import sqlite3


class EditalDialog(QDialog):
    def __init__(self, main_app, config_manager, df_registro, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.config_manager = config_manager 

        self.df_registro = df_registro

        # Certifique-se de que df_registro tem pelo menos um registro
        if not self.df_registro.empty:
            id_processo_original = self.df_registro['id_processo'].iloc[0]
            self.id_processo = id_processo_original.replace('/', '-')
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

        self.setWindowTitle("Edital")
        self.setFixedSize(850, 510)
        self.pasta = ''

        self.layoutPrincipal = QHBoxLayout()

        # Criando QWidget para encapsular os layouts de esquerda e direita
        self.widgetEsquerda = QWidget()
        self.widgetDireita = QWidget()

        # Definindo tamanhos fixos para os widgets encapsulados
        self.widgetEsquerda.setFixedSize(330, 500)
        self.widgetDireita.setFixedSize(500, 400)

        self.layoutEsquerda = QVBoxLayout(self.widgetEsquerda)  # Layout para o lado esquerdo
        self.layoutDireita = QVBoxLayout(self.widgetDireita)  # Layout para o lado direito

        self.setupUi()
        self.setStyleSheet("""
            QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QRadioButton{
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

        # Adicionar os widgets encapsulados ao layout principal
        self.layoutPrincipal.addWidget(self.widgetEsquerda)
        self.layoutPrincipal.addWidget(self.widgetDireita)

        self.setLayout(self.layoutPrincipal)  
        self.config_manager.config_updated.connect(self.update_save_location)

        self.pasta_base = Path(self.config_manager.get_config('save_location', str(Path.home() / 'Desktop')))
        
    def update_save_location(self, key, new_path):
        if key == 'save_location':
            self.pasta_base = new_path
            print(f"Local de salvamento atualizado para: {self.pasta_base}")

    def setupUi(self):
        settings = QSettings("SuaOrganizacao", "SeuAplicativo")
        self.createGroups()
        self.addWidgetsToLeftLayout()
        self.addWidgetsToRightLayout()
        self.applyWidgetStyles()

    def createGroups(self):
        self.grupoAutoridade = QGroupBox("Autoridade Competente")
        self.grupoMinuta = QGroupBox("Minuta")
        self.grupoItemGrupo = QGroupBox("Item ou Grupo")
        self.grupoSelecaoPasta = QGroupBox("Local de Salvamento do Arquivo")
        self.grupoEdicaoTemplate = QGroupBox("Edição do Modelo do Edital")
        self.grupoCriacaoDocumento = QGroupBox("Gerar Edital")
        self.grupoSIGDEM = QGroupBox("SIGDEM")

        # Aqui, você pode configurar o layout de cada grupo e adicionar os widgets específicos.
        # Por exemplo:
        self.setupGrupoAutoridade()
        self.setupGrupoMinuta()
        self.setupGrupoItem()
        self.setupGrupoSelecaoPasta()
        self.setupGrupoEdicaoTemplate()
        self.setupGrupoCriacaoDocumento()
        self.setupGrupoSIGDEM()

    def setupGrupoAutoridade(self):
        layout = QVBoxLayout(self.grupoAutoridade)
        self.ordenadordespesasComboBox = QComboBox()
        self.carregarOrdenadorDespesas()
        layout.addWidget(self.ordenadordespesasComboBox)

    def setupGrupoMinuta(self):
        layout = QHBoxLayout()
        self.radioSim = QRadioButton("Sim")
        self.radioNao = QRadioButton("Não")
        self.radioSim.setChecked(True)  # Define 'Sim' como selecionado por padrão
        
        layout.addWidget(self.radioSim)
        layout.addWidget(self.radioNao)
        self.grupoMinuta.setLayout(layout)

    def setupGrupoItem(self):
        # Criação de layouts verticais e horizontais
        layoutPrincipal = QVBoxLayout()
        layoutItens = QHBoxLayout()
        layoutGrupos = QHBoxLayout()
        
        # Criação dos RadioButtons
        self.radioItem = QRadioButton("Item")
        self.radioItemUnico = QRadioButton("Item Único")
        self.radioGrupo = QRadioButton("Grupo")
        self.radioGrupoUnico = QRadioButton("Grupo Único")
        
        # Definindo 'Item' como selecionado por padrão
        self.radioItem.setChecked(True)
        
        # Adicionando os RadioButtons aos layouts horizontais correspondentes
        layoutItens.addWidget(self.radioItem)
        layoutItens.addWidget(self.radioItemUnico)
        
        layoutGrupos.addWidget(self.radioGrupo)
        layoutGrupos.addWidget(self.radioGrupoUnico)
        
        # Adicionando os layouts horizontais ao layout vertical principal
        layoutPrincipal.addLayout(layoutItens)
        layoutPrincipal.addLayout(layoutGrupos)
        
        # Configurando o layout do grupo de itens
        self.grupoItemGrupo.setLayout(layoutPrincipal)

    def setupGrupoSelecaoPasta(self):
        layout = QVBoxLayout(self.grupoSelecaoPasta)
        labelPasta = QLabel("Selecionar pasta para salvar o Edital:")
        iconPathFolder = ICONS_DIR / "abrir_pasta.png"
        botaoSelecionarPasta = QPushButton("  Selecionar Pasta")
        botaoSelecionarPasta.setIcon(QIcon(str(iconPathFolder)))
        botaoSelecionarPasta.clicked.connect(self.selecionarPasta)
        layout.addWidget(labelPasta)
        layout.addWidget(botaoSelecionarPasta)

    def setupGrupoEdicaoTemplate(self):
        layout = QVBoxLayout(self.grupoEdicaoTemplate)
        labelEdicao = QLabel("Editar o arquivo modelo de Autorização:")
        iconPathEdit = ICONS_DIR / "text.png"
        botaoEdicaoTemplate = QPushButton("  Editar Modelo")
        botaoEdicaoTemplate.setIcon(QIcon(str(iconPathEdit)))
        botaoEdicaoTemplate.clicked.connect(self.editarTemplate)
        layout.addWidget(labelEdicao)
        layout.addWidget(botaoEdicaoTemplate)

    def setupGrupoCriacaoDocumento(self):
        layout = QVBoxLayout(self.grupoCriacaoDocumento)
        botoesLayout = QHBoxLayout()
        iconPathDocx = ICONS_DIR / "word.png"
        iconPathPdf = ICONS_DIR / "pdf64.png"
        botaoDocx = QPushButton("  Docx")
        botaoDocx.setIcon(QIcon(str(iconPathDocx)))
        botaoDocx.clicked.connect(self.gerarDocx)
        botaoPdf = QPushButton("  Pdf")
        botaoPdf.setIcon(QIcon(str(iconPathPdf)))
        botaoPdf.clicked.connect(self.gerarPdf)
        botoesLayout.addWidget(botaoDocx)
        botoesLayout.addWidget(botaoPdf)
        layout.addLayout(botoesLayout)

    def setupGrupoSIGDEM(self):
        layout = QVBoxLayout(self.grupoSIGDEM)

        # Mapa de abreviações
        abrev_map = {
            "Pregão Eletrônico": "PE",
            "Concorrência": "CC",
            "Dispensa Eletrônica": "DE",
            "Termo de Justificativa de Dispensa Eletrônica": "TJDL",
            "Termo de Justificativa de Inexigibilidade de Licitação": "TJIL"
        }

        # Obtenção da abreviação para self.tipo
        tipo_abreviado = abrev_map.get(self.tipo, self.tipo)  # Retorna self.tipo se não houver abreviação

        # Campo "Assunto"
        labelAssunto = QLabel("No campo “Assunto”, deverá constar:")
        layout.addWidget(labelAssunto)
        textEditAssunto = QTextEdit()
        textEditAssunto.setPlainText(f"{tipo_abreviado} {self.numero}/{self.ano} – Edital")
        textEditAssunto.setMaximumHeight(50)
        btnCopyAssunto = QPushButton("Copiar")
        btnCopyAssunto.clicked.connect(lambda: self.copyToClipboard(textEditAssunto.toPlainText()))
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
        sinopse_text = (f"Edital referente ao {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
                        f"Processo Administrativo NUP: {self.nup}\n"
                        f"Item do PCA: {self.item_pca}")
        textEditSinopse.setPlainText(sinopse_text)
        textEditSinopse.setMaximumHeight(100)
        btnCopySinopse = QPushButton("Copiar")
        btnCopySinopse.clicked.connect(lambda: self.copyToClipboard(textEditSinopse.toPlainText()))
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
        btnCopyObservacoes = QPushButton("Copiar")
        btnCopyObservacoes.clicked.connect(lambda: self.copyToClipboard(textEditObservacoes.toPlainText()))
        layoutHObservacoes = QHBoxLayout()
        layoutHObservacoes.addWidget(textEditObservacoes)
        layoutHObservacoes.addWidget(btnCopyObservacoes)
        layout.addLayout(layoutHObservacoes)

    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        # Mostra a tooltip na posição atual do mouse
        QToolTip.showText(QCursor.pos(), "Texto copiado para a área de transferência.", msecShowTime=1500)

    def addWidgetsToLeftLayout(self):
        self.layoutEsquerda.addWidget(self.grupoAutoridade)
        self.layoutEsquerda.addWidget(self.grupoMinuta)
        self.layoutEsquerda.addWidget(self.grupoItemGrupo)
        self.layoutEsquerda.addWidget(self.grupoSelecaoPasta)
        self.layoutEsquerda.addWidget(self.grupoEdicaoTemplate)
        self.layoutEsquerda.addWidget(self.grupoCriacaoDocumento)

    def addWidgetsToRightLayout(self):
        self.layoutDireita.addWidget(self.grupoSIGDEM)

    def applyWidgetStyles(self):
        estiloBorda = "QGroupBox { border: 1px solid gray; border-radius: 5px; margin-top: 0.5em; } " \
                      "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }"
        self.grupoAutoridade.setStyleSheet(estiloBorda)
        self.grupoMinuta.setStyleSheet(estiloBorda)
        self.grupoItemGrupo.setStyleSheet(estiloBorda)
        self.grupoSelecaoPasta.setStyleSheet(estiloBorda)
        self.grupoEdicaoTemplate.setStyleSheet(estiloBorda)
        self.grupoCriacaoDocumento.setStyleSheet(estiloBorda)
        self.grupoSIGDEM.setStyleSheet(estiloBorda)

    def editarTemplate(self):
        template_path = TEMPLATE_PLANEJAMENTO_DIR / "template_edital.docx"
        try:
            if sys.platform == "win32":
                subprocess.run(["start", "winword", str(template_path)], check=True, shell=True)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(template_path)], check=True)
            else:  # linux variants
                subprocess.run(["xdg-open", str(template_path)], check=True)
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir o documento: {e}")
            
    def carregarOrdenadorDespesas(self):
        # Tentar conectar ao banco de dados e carregar a tabela controle_agentes_responsaveis
        try:
            with sqlite3.connect(CONTROLE_DADOS) as conn:
                # Verificar se a tabela existe
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_agentes_responsaveis'")
                exists = cursor.fetchone()

                if not exists:
                    raise Exception("A tabela 'controle_agentes_responsaveis' não existe no banco de dados. Configure os Ordenadores de Despesas no Módulo 'Configurações'.")

                # Carregar apenas os dados relevantes da tabela em um DataFrame
                sql_query = """
                SELECT * FROM controle_agentes_responsaveis
                WHERE funcao LIKE 'Ordenador de Despesas%' OR funcao LIKE 'Ordenador de Despesas Substituto%'
                """
                self.ordenador_despesas_df = pd.read_sql_query(sql_query, conn)

            # Adicionar os itens ao comboBox
            self.ordenadordespesasComboBox.clear()  # Limpar o comboBox antes de adicionar novos itens
            for index, row in self.ordenador_despesas_df.iterrows():
                texto_display = f"{row['nome']}\n{row['funcao']}\n{row['posto']}"
                self.ordenadordespesasComboBox.addItem(texto_display, userData=row.to_dict())

        except Exception as e:
            print(f"Erro ao carregar Ordenadores de Despesas: {e}")

    def selecionarPasta(self):
        self.pasta = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if self.pasta:
            print(f"Pasta selecionada: {self.pasta}")
    
    def gerarDocumento(self, tipo="docx"):
        if self.df_registro is None:
            QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
            return None

        template_path = TEMPLATE_PLANEJAMENTO_DIR / f"template_edital.{tipo}"
        objeto = remover_caracteres_especiais(self.df_registro['objeto'].iloc[0])
        id_processo_original = self.df_registro['id_processo'].iloc[0]
        id_processo_novo = id_processo_original.replace('/', '-')

        nome_pasta = f"{id_processo_novo} - {objeto}"
        subpasta_autorizacao = f"{id_processo_novo} - Edital"
        
        pasta_destino = os.path.join(self.pasta_base, nome_pasta)
        subpasta_destino = os.path.join(pasta_destino, subpasta_autorizacao)

        # Verifica se a pasta principal existe e cria se necessário
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        # Verifica se a subpasta existe e cria se necessário
        if not os.path.exists(subpasta_destino):
            os.makedirs(subpasta_destino)

        # Formatar o nome do arquivo
        nome_arquivo = f"{id_processo_novo} - Edital.{tipo}"
        save_path = os.path.join(subpasta_destino, nome_arquivo)

        doc = DocxTemplate(template_path)

        nome_selecionado = self.ordenadordespesasComboBox.currentText()
        valor_completo = self.ordenadordespesasComboBox.currentData(Qt.ItemDataRole.UserRole)

        descricao_servico = "aquisição de" if self.material_servico == "material" else "contratação de empresa especializada em"
        minuta = "MINUTA" if self.radioSim.isChecked() else ""
        item_ou_grupo = self.resolveItemOuGrupo()

        data = {
            **self.df_registro.to_dict(orient='records')[0],
            'ordenador_de_despesas': f"{valor_completo['nome']}\n{valor_completo['funcao']}\n{valor_completo['posto']}",
            'descricao_servico': descricao_servico,
            'minuta': minuta,
            'item_ou_grupo': item_ou_grupo
        }

        doc.render(data)
        doc.save(save_path)

        return save_path

    def abrirDocumento(self, path):
        pasta_destino = os.path.dirname(path)  # Obter a pasta onde o arquivo está localizado

        if sys.platform == "win32":
            os.startfile(path)  # Abrir o documento
            os.startfile(pasta_destino)  # Abrir a pasta no Windows Explorer
        else:
            subprocess.run(["xdg-open", path])  # Abrir o documento no Linux ou MacOS
            subprocess.run(["xdg-open", pasta_destino])  # Abrir a pasta no gerenciador de arquivos do sistema

    def resolveItemOuGrupo(self):
        if self.radioItem.isChecked():
            return "A licitação será dividida em itens, conforme tabela constante do Termo de Referência, facultando-se ao licitante a participação em quantos itens forem de seu interesse."
        elif self.radioItemUnico.isChecked():
            return "A licitação será realizada em único item."
        elif self.radioGrupo.isChecked():
            return "A licitação será dividida em grupos, formados por um ou mais itens, conforme tabela constante do Termo de Referência, facultando-se ao licitante a participação em quantos grupos forem de seu interesse, devendo oferecer proposta para todos os itens que os compõem."
        else:
            return "A licitação será realizada em grupo único, conforme tabela constante no Termo de Referência, devendo o licitante oferecer proposta para todos os itens que o compõem."

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


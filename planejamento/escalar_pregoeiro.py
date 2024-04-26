from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import pandas as pd
import subprocess
from docxtpl import DocxTemplate
PLANEJAMENTO_DIR = BASE_DIR / "planejamento"
import sys
import shutil
import tempfile
import os
from win32com.client import Dispatch

class EscalarPregoeiroDialog(QDialog):
    def __init__(self, main_app, df_registro, parent=None):
        super().__init__(parent)
        self.main_app = main_app
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
            self.pregoeiro = self.df_registro['pregoeiro'].iloc[0]

        self.setWindowTitle("Escalação de Pregoeiro")
        self.setFixedSize(850, 410)
        self.pasta = ''

        self.layoutPrincipal = QHBoxLayout()

        # Criando QWidget para encapsular os layouts de esquerda e direita
        self.widgetEsquerda = QWidget()
        self.widgetDireita = QWidget()

        # Definindo tamanhos fixos para os widgets encapsulados
        self.widgetEsquerda.setFixedSize(330, 400)
        self.widgetDireita.setFixedSize(500, 400)

        self.layoutEsquerda = QVBoxLayout(self.widgetEsquerda)  # Layout para o lado esquerdo
        self.layoutDireita = QVBoxLayout(self.widgetDireita)  # Layout para o lado direito

        self.setupUi()
        self.setStyleSheet("""
            QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit {
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

    def setupUi(self):
        settings = QSettings("SuaOrganizacao", "SeuAplicativo")
        self.createGroups()
        self.addWidgetsToLeftLayout()
        self.addWidgetsToRightLayout()
        self.applyWidgetStyles()

    def createGroups(self):
        self.grupoNumeroCP = QGroupBox("Número da CP")
        self.grupoSelecaoPasta = QGroupBox("Local de Salvamento do Arquivo")
        self.grupoEdicaoTemplate = QGroupBox("Edição do Modelo da CP")
        self.grupoCriacaoDocumento = QGroupBox("Gerar CP")
        self.grupoSIGDEM = QGroupBox("SIGDEM")

        # Aqui, você pode configurar o layout de cada grupo e adicionar os widgets específicos.
        self.setupGrupoNumeroCP()
        self.setupGrupoSelecaoPasta()
        self.setupGrupoEdicaoTemplate()
        self.setupGrupoCriacaoDocumento()
        self.setupGrupoSIGDEM()

    def setupGrupoNumeroCP(self):
        layout = QVBoxLayout(self.grupoNumeroCP)
        label = QLabel("Digite o número da CP:")
        self.cp_input = QLineEdit()  # Widget de entrada para o número da CP
        layout.addWidget(label)
        layout.addWidget(self.cp_input)

    def setupGrupoSelecaoPasta(self):
        layout = QVBoxLayout(self.grupoSelecaoPasta)
        labelPasta = QLabel("Selecionar pasta para salvar o arquivo:")
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
        textEditAssunto.setPlainText(f"{tipo_abreviado} {self.numero}/{self.ano} – Escalação de Pregoeiro")
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
        sinopse_text = (f"Escalação de Pregoeiro ({self.pregoeiro}) referente ao {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
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
        self.layoutEsquerda.addWidget(self.grupoNumeroCP)
        self.layoutEsquerda.addWidget(self.grupoSelecaoPasta)
        self.layoutEsquerda.addWidget(self.grupoEdicaoTemplate)
        self.layoutEsquerda.addWidget(self.grupoCriacaoDocumento)

    def addWidgetsToRightLayout(self):
        self.layoutDireita.addWidget(self.grupoSIGDEM)

    def applyWidgetStyles(self):
        estiloBorda = "QGroupBox { border: 1px solid gray; border-radius: 5px; margin-top: 0.5em; } " \
                      "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }"
        self.grupoNumeroCP.setStyleSheet(estiloBorda)
        self.grupoSelecaoPasta.setStyleSheet(estiloBorda)
        self.grupoEdicaoTemplate.setStyleSheet(estiloBorda)
        self.grupoCriacaoDocumento.setStyleSheet(estiloBorda)
        self.grupoSIGDEM.setStyleSheet(estiloBorda)

    def editarTemplate(self):
        template_path = PLANEJAMENTO_DIR / "template_cp_pregoeiro.docx"
        try:
            if sys.platform == "win32":
                subprocess.run(["start", "winword", str(template_path)], check=True, shell=True)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(template_path)], check=True)
            else:  # linux variants
                subprocess.run(["xdg-open", str(template_path)], check=True)
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir o documento: {e}")

    def selecionarPasta(self):
        self.pasta = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if self.pasta:
            print(f"Pasta selecionada: {self.pasta}")

    def gerarDocx(self):
        try:
            # Verifica se um registro foi selecionado na tabela
            if self.df_registro is None:
                QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
                return

            # Continua com o processo de geração do documento
            template_path = PLANEJAMENTO_DIR / "template_cp_pregoeiro.docx"
            # Substituição de '/' por '-' em 'id_processo'
            id_processo_original = self.df_registro['id_processo'].iloc[0]
            id_processo = id_processo_original.replace('/', '-')
            salvar_nome = f"{id_processo} - Escalacao de Pregoeiro.docx"
            save_path = os.path.join(self.pasta, salvar_nome)
            doc = DocxTemplate(template_path)

            # Lógica específica para material_servico
            descricao_servico = "aquisição de" if self.material_servico == "material" else "contratação de empresa especializada em"
            numero_cp = self.cp_input.text().strip()

            data = {
                **self.df_registro.to_dict(orient='records')[0],
                'numero_cp': numero_cp,
                'descricao_servico': descricao_servico  # Adicionando a descrição do serviço
            }

            doc.render(data)
            doc.save(save_path)

            # Abrir o arquivo DOCX gerado com o sistema operacional
            if sys.platform == "win32":
                os.startfile(save_path)
            else:
                subprocess.run(["xdg-open", save_path])

            return save_path
        except Exception as e:
            QMessageBox.warning(None, "Erro", f"Erro ao gerar documento DOCX: {e}")
            return None

    def gerarPdf(self):
        try:
            # Gerar o arquivo DOCX
            docx_path = self.gerarDocx()
            if docx_path is None:
                raise Exception("Falha na geração do arquivo DOCX.")

            # Inicializar o cliente COM do Microsoft Word
            word = Dispatch("Word.Application")
            word.visible = False  # Executar em background

            # Abrir o documento DOCX
            doc = word.Documents.Open(docx_path)

            # Definir o caminho do PDF
            pdf_path = docx_path.replace('.docx', '.pdf')

            # Exportar para PDF
            doc.SaveAs(pdf_path, FileFormat=17)  # FileFormat=17 para PDF

            # Fechar o documento Word sem salvar
            doc.Close(SaveChanges=0)

            # Fechar o aplicativo Word
            word.Quit()

            print(f"Arquivo PDF gerado com sucesso: {pdf_path}")
            return pdf_path
        except Exception as e:
            QMessageBox.warning(None, "Erro", f"Erro ao gerar documento PDF: {e}")
            return None

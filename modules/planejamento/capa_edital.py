from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import pandas as pd
import subprocess
from docxtpl import DocxTemplate
import sys
from datetime import datetime
import os
from win32com.client import Dispatch
import time
import sqlite3
import locale
from num2words import num2words

import re
from modules.planejamento.utilidades_planejamento import remover_caracteres_especiais

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def formatar_valor_monetario(valor):
    if pd.isna(valor):  # Verifica se o valor é NaN e ajusta para string vazia
        valor = ''
    # Limpa a string e converte para float
    valor = re.sub(r'[^\d,]', '', str(valor)).replace(',', '.')
    valor_float = float(valor) if valor else 0
    # Formata para a moeda local sem usar locale
    valor_monetario = f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    # Converte para extenso
    valor_extenso = num2words(valor_float, lang='pt_BR', to='currency')
    return valor_monetario, valor_extenso
class CapaEdital(QDialog):
    def __init__(self, main_app, config_manager, df_registro, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.config_manager = config_manager 
        self.df_registro = df_registro

        # Inicializando as variáveis de seleção
        self.criterio_julgamento = "Menor preço por item"
        self.modo_disputa = "Aberto"
        self.preferencia_meepp = "Sim"

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

        self.setWindowTitle("Capa do Edital")
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
            QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QDateEdit, QRadioButton{
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
        self.grupoCriterioJulgamento = QGroupBox("Critério de Julgamento")
        self.grupoModoDisputa = QGroupBox("Modo de Disputa")
        self.grupoMEEPP = QGroupBox("Preferência ME/EPP/Equiparadas")
        self.grupoSelecaoPasta = QGroupBox("Local de Salvamento do Arquivo")
        self.grupoEdicaoTemplate = QGroupBox("Edição do Modelo da CP")
        self.grupoCriacaoDocumento = QGroupBox("Gerar CP")
        self.grupoSIGDEM = QGroupBox("SIGDEM")

        # Aqui, você pode configurar o layout de cada grupo e adicionar os widgets específicos.
        self.setupCriterioJulgamento()
        self.setupModoDisputa()
        self.setupMEEPP()
        self.setupGrupoSelecaoPasta()
        self.setupGrupoEdicaoTemplate()
        self.setupGrupoCriacaoDocumento()
        self.setupGrupoSIGDEM()

    def setupCriterioJulgamento(self):
        layout = QVBoxLayout(self.grupoCriterioJulgamento)
        self.comboBoxCriterioJulgamento = QComboBox()
        criterios = [
            "Menor preço por item",
            "Menor preço por grupo",
            "Menor preço global",
            "Maior desconto por item",
            "Maior desconto por grupo",
            "Maior desconto global"
        ]
        self.comboBoxCriterioJulgamento.addItems(criterios)
        self.comboBoxCriterioJulgamento.setCurrentIndex(0)  # Define 'menor preço por item' como pré-definido
        self.comboBoxCriterioJulgamento.currentIndexChanged.connect(self.atualizarCriterioJulgamento)
        layout.addWidget(self.comboBoxCriterioJulgamento)

    def setupModoDisputa(self):
        layout = QVBoxLayout(self.grupoModoDisputa)
        self.comboBoxModoDisputa = QComboBox()
        modos = [
            "Aberto",
            "Aberto e Fechado",
            "Fechado e Aberto"
        ]
        self.comboBoxModoDisputa.addItems(modos)
        self.comboBoxModoDisputa.setCurrentIndex(0)  # Define 'aberto' como pré-definido
        self.comboBoxModoDisputa.currentIndexChanged.connect(self.atualizarModoDisputa)
        layout.addWidget(self.comboBoxModoDisputa)

    def setupMEEPP(self):
        layout = QHBoxLayout(self.grupoMEEPP)
        self.radioSim = QRadioButton("Sim")
        self.radioNao = QRadioButton("Não")
        self.radioSim.setChecked(True)  # Define 'Sim' como pré-definido
        radioGroup = QButtonGroup(self)
        radioGroup.addButton(self.radioSim)
        radioGroup.addButton(self.radioNao)
        layout.addWidget(self.radioSim)
        layout.addWidget(self.radioNao)
        radioGroup.buttonClicked.connect(self.atualizarMEEPP)

    def setupGrupoSelecaoPasta(self):
        layout = QVBoxLayout(self.grupoSelecaoPasta)
        iconPathFolder = ICONS_DIR / "abrir_pasta.png"
        botaoSelecionarPasta = QPushButton("  Selecionar Pasta")
        botaoSelecionarPasta.setIcon(QIcon(str(iconPathFolder)))
        botaoSelecionarPasta.clicked.connect(self.selecionarPasta)
        layout.addWidget(botaoSelecionarPasta)

    def setupGrupoEdicaoTemplate(self):
        layout = QVBoxLayout(self.grupoEdicaoTemplate)
        iconPathEdit = ICONS_DIR / "text.png"
        botaoEdicaoTemplate = QPushButton("  Editar Modelo")
        botaoEdicaoTemplate.setIcon(QIcon(str(iconPathEdit)))
        botaoEdicaoTemplate.clicked.connect(self.editarTemplate)
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
        textEditAssunto.setPlainText(f"{tipo_abreviado} {self.numero}/{self.ano} – Capa do Edital")
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
        sinopse_text = (f"Capa do Edital referente ao {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
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
        self.layoutEsquerda.addWidget(self.grupoCriterioJulgamento)
        self.layoutEsquerda.addWidget(self.grupoModoDisputa)
        self.layoutEsquerda.addWidget(self.grupoMEEPP)
        self.layoutEsquerda.addWidget(self.grupoSelecaoPasta)
        self.layoutEsquerda.addWidget(self.grupoEdicaoTemplate)
        self.layoutEsquerda.addWidget(self.grupoCriacaoDocumento)

    def addWidgetsToRightLayout(self):
        self.layoutDireita.addWidget(self.grupoSIGDEM)

    def applyWidgetStyles(self):
        estiloBorda = "QGroupBox { border: 1px solid gray; border-radius: 5px; margin-top: 0.5em; } " \
                      "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }"
        self.grupoCriterioJulgamento.setStyleSheet(estiloBorda)
        self.grupoModoDisputa.setStyleSheet(estiloBorda)
        self.grupoMEEPP.setStyleSheet(estiloBorda)
        self.grupoSelecaoPasta.setStyleSheet(estiloBorda)
        self.grupoEdicaoTemplate.setStyleSheet(estiloBorda)
        self.grupoCriacaoDocumento.setStyleSheet(estiloBorda)
        self.grupoSIGDEM.setStyleSheet(estiloBorda)

    def editarTemplate(self):
        template_path = TEMPLATE_PLANEJAMENTO_DIR / "template_capa_edital.docx"
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
        pasta_selecionada = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if pasta_selecionada:
            self.pasta_base = pasta_selecionada
            print(f"Pasta selecionada: {self.pasta_base}")

    def formatar_data_brasileira(self, data_iso):
        """Converte data de formato ISO (AAAA-MM-DD) para formato brasileiro (DD/MM/AAAA)."""
        data_obj = datetime.strptime(data_iso, '%Y-%m-%d')
        return data_obj.strftime('%d/%m/%Y')

    def atualizarCriterioJulgamento(self):
        self.criterio_julgamento = self.comboBoxCriterioJulgamento.currentText()

    def atualizarModoDisputa(self):
        self.modo_disputa = self.comboBoxModoDisputa.currentText()

    def atualizarMEEPP(self):
        self.preferencia_meepp = "Sim" if self.radioSim.isChecked() else "Não"

    def gerarDocumento(self, tipo="docx"):
        if self.df_registro is None:
            QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
            return None

        if 'data_sessao' not in self.df_registro.columns:
            QMessageBox.warning(None, "Dado Ausente", "A coluna 'data_sessao' não está presente no registro.")
            return None

        data_sessao_iso = self.df_registro['data_sessao'].iloc[0]
        if data_sessao_iso is None or data_sessao_iso == '':
            QMessageBox.warning(None, "Data Ausente", "Data da sessão está ausente ou inválida. Por favor, defina um valor para a data da sessão antes de prosseguir.")
            return None

        try:
            data_sessao = datetime.strptime(data_sessao_iso, '%Y-%m-%d').strftime('%d/%m/%Y')
        except ValueError as e:
            QMessageBox.warning(None, "Formato de Data Inválido", f"O valor da data ('{data_sessao_iso}') não está no formato esperado 'AAAA-MM-DD'. Por favor, corrija e tente novamente.")
            return None

        template_path = TEMPLATE_PLANEJAMENTO_DIR / f"template_capa_edital.{tipo}"
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
        nome_arquivo = f"{id_processo_novo} - Capa do Edital.{tipo}"
        save_path = os.path.join(subpasta_destino, nome_arquivo)

        doc = DocxTemplate(template_path)
        descricao_servico = "Aquisição de" if self.material_servico == "material" else "Contratação de empresa especializada em"
        data_sessao_iso = self.df_registro['data_sessao'].iloc[0]
        if pd.isnull(data_sessao_iso):
            QMessageBox.warning(None, "Data Ausente", "Data da sessão está ausente ou inválida.")
            return None
        # Converte a data de formato ISO (AAAA-MM-DD) para formato brasileiro (DD/MM/AAAA)
        data_sessao = datetime.strptime(data_sessao_iso, '%Y-%m-%d').strftime('%d/%m/%Y')

        valor_total = self.df_registro['valor_total'].iloc[0] if not pd.isna(self.df_registro['valor_total'].iloc[0]) else ''
        valor_monetario, valor_extenso = formatar_valor_monetario(valor_total)
        
        data = {
            **self.df_registro.to_dict(orient='records')[0],
            'descricao_servico': descricao_servico,
            'data_sessao': data_sessao, 
            'valor_total': valor_monetario,
            'valor_total_extenso': valor_extenso,
            'criterio_julgamento': self.criterio_julgamento,
            'modo_disputa': self.modo_disputa,
            'preferencia_meepp': self.preferencia_meepp
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

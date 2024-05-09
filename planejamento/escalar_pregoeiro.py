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
from planejamento.utilidades_planejamento import remover_caracteres_especiais

class EscalarPregoeiroDialog(QDialog):
    def __init__(self, main_app, config_manager, df_registro, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.config_manager = config_manager 

        self.df_registro = df_registro

        # Certifique-se de que df_registro tem pelo menos um registro
        if not self.df_registro.empty:
            self.id = self.df_registro['id'].iloc[0]
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

        self.setWindowTitle("Designação de Pregoeiro")
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
            QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QDateEdit {
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
        self.grupoNumeroCP = QGroupBox("Número da CP")
        self.grupoDataSessao = QGroupBox("Data da Sessão Pública")
        self.grupoSelecaoPasta = QGroupBox("Local de Salvamento do Arquivo")
        self.grupoEdicaoTemplate = QGroupBox("Edição do Modelo da CP")
        self.grupoCriacaoDocumento = QGroupBox("Gerar CP")
        self.grupoSIGDEM = QGroupBox("SIGDEM")

        # Aqui, você pode configurar o layout de cada grupo e adicionar os widgets específicos.
        self.setupGrupoNumeroCP()
        self.setupGrupoDataSessao()
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

    def setupGrupoDataSessao(self):
        layout = QVBoxLayout(self.grupoDataSessao)
        self.dataSessaoEdit = QDateEdit(calendarPopup=True)
        self.dataSessaoEdit.setDisplayFormat("dd/MM/yyyy")  # Configura o formato de exibição da data
        self.dataSessaoEdit.setDate(QDate.currentDate())    

        # Configurar a data inicial baseada no DataFrame
        data_sessao_str = self.df_registro.get('data_sessao', pd.Series([QDate.currentDate().toString("yyyy-MM-dd")])).iloc[0]
        data_sessao = QDate.fromString(data_sessao_str, "yyyy-MM-dd")
        if data_sessao.isValid():
            self.dataSessaoEdit.setDate(data_sessao)
        else:
            # Calcula 10 dias úteis a partir de hoje
            current_date = QDate.currentDate()
            for _ in range(10):
                current_date = current_date.addDays(1)
                while current_date.dayOfWeek() > 5:  # Pula fins de semana
                    current_date = current_date.addDays(1)
            self.dataSessaoEdit.setDate(current_date)
        
        # Conectar o sinal de mudança de data ao método de salvamento
        self.dataSessaoEdit.dateChanged.connect(self.salvarDataSessao)

        layout.addWidget(self.dataSessaoEdit)
        self.grupoDataSessao.setLayout(layout)

    def salvarDataSessao(self):
        """Salva a nova data da sessão no banco de dados sempre que o QDateEdit é alterado."""
        # Certificar-se que o ID está no tipo correto (int ou str, conforme esperado)
        try:
            # Tentando converter para int se for string e precisa ser int
            process_id = int(self.id)
            print(f"ID do processo formatado como inteiro: {process_id}")
        except ValueError:
            process_id = self.id  # Se falhar, usar como está
            print(f"ID do processo usado como string: {process_id}")

        data_sessao = self.dataSessaoEdit.date().toString("yyyy-MM-dd")
        print(f"Tentando salvar a data: {data_sessao} para o processo: {process_id}")

        try:
            conn = sqlite3.connect(str(CONTROLE_DADOS))
            cursor = conn.cursor()

            query = "UPDATE controle_processos SET data_sessao = ? WHERE id = ?"
            cursor.execute(query, (data_sessao, process_id))
            conn.commit()

            # Verifica se a atualização teve efeito
            cursor.execute("SELECT data_sessao FROM controle_processos WHERE id = ?", (process_id,))
            saved_date = cursor.fetchone()
            if saved_date:
                print(f"Data salva no banco de dados: {saved_date[0]}")
            else:
                print("Nenhum registro encontrado com o ID fornecido.")

            conn.close()
            QMessageBox.information(self, "Salvar Data", "Data da sessão pública atualizada com sucesso.")
        except Exception as e:
            print(f"Erro ao tentar salvar a data no banco de dados: {e}")
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao tentar salvar a data: {str(e)}")


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
        textEditAssunto.setPlainText(f"{tipo_abreviado} {self.numero}/{self.ano} – Designação de Pregoeiro")
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
        sinopse_text = (f"Designação de Pregoeiro ({self.pregoeiro}) referente ao {self.tipo} nº {self.numero}/{self.ano}, para {descricao_servico} {self.objeto}\n"
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
        self.layoutEsquerda.addWidget(self.grupoDataSessao)
        self.layoutEsquerda.addWidget(self.grupoSelecaoPasta)
        self.layoutEsquerda.addWidget(self.grupoEdicaoTemplate)
        self.layoutEsquerda.addWidget(self.grupoCriacaoDocumento)

    def addWidgetsToRightLayout(self):
        self.layoutDireita.addWidget(self.grupoSIGDEM)

    def applyWidgetStyles(self):
        estiloBorda = "QGroupBox { border: 1px solid gray; border-radius: 5px; margin-top: 0.5em; } " \
                      "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }"
        self.grupoNumeroCP.setStyleSheet(estiloBorda)
        self.grupoDataSessao.setStyleSheet(estiloBorda)
        self.grupoSelecaoPasta.setStyleSheet(estiloBorda)
        self.grupoEdicaoTemplate.setStyleSheet(estiloBorda)
        self.grupoCriacaoDocumento.setStyleSheet(estiloBorda)
        self.grupoSIGDEM.setStyleSheet(estiloBorda)

    def editarTemplate(self):
        template_path = TEMPLATE_PLANEJAMENTO_DIR / "template_cp_pregoeiro.docx"
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

    def formatar_data_brasileira(self, data_iso):
        """Converte data de formato ISO (AAAA-MM-DD) para formato brasileiro (DD/MM/AAAA)."""
        data_obj = datetime.strptime(data_iso, '%Y-%m-%d')
        return data_obj.strftime('%d/%m/%Y')

    def gerarDocumento(self, tipo="docx"):
        if self.df_registro is None:
            QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
            return None

        template_path = TEMPLATE_PLANEJAMENTO_DIR / f"template_cp_pregoeiro.{tipo}"
        objeto = remover_caracteres_especiais(self.df_registro['objeto'].iloc[0])
        id_processo_original = self.df_registro['id_processo'].iloc[0]
        id_processo_novo = id_processo_original.replace('/', '-')

        data_sessao = self.dataSessaoEdit.date().toString("yyyy-MM-dd")
        data_sessao = self.formatar_data_brasileira(data_sessao)

        nome_pasta = f"{id_processo_novo} - {objeto}"
        subpasta_autorizacao = f"{id_processo_novo} - Designacao de Pregoeiro"
        
        pasta_destino = os.path.join(self.pasta_base, nome_pasta)
        subpasta_destino = os.path.join(pasta_destino, subpasta_autorizacao)

        # Verifica se a pasta principal existe e cria se necessário
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        # Verifica se a subpasta existe e cria se necessário
        if not os.path.exists(subpasta_destino):
            os.makedirs(subpasta_destino)

        nome_arquivo = f"{id_processo_novo} - Designação de Pregoeiro.{tipo}"
        save_path = os.path.join(subpasta_destino, nome_arquivo)

        doc = DocxTemplate(template_path)

        # Lógica específica para material_servico
        descricao_servico = "aquisição de" if self.material_servico == "material" else "contratação de empresa especializada em"
        numero_cp = self.cp_input.text().strip()

        data = {
            **self.df_registro.to_dict(orient='records')[0],
            'numero_cp': numero_cp,
            'data_sessao': data_sessao,  # Usando a data formatada
            'descricao_servico': descricao_servico  # Adicionando a descrição do serviço
        }

        doc.render(data)
        doc.save(save_path)

        return save_path

    def abrirDocumento(self, path):
        if sys.platform == "win32":
            os.startfile(path)
        else:
            subprocess.run(["xdg-open", path])

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
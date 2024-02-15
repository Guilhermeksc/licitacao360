#painel_contratos.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
from controle_contratos.atualizar_dados_contratos import AtualizarDadosContratos
from controle_contratos.utils_contratos import *
from datetime import datetime, timedelta
from num2words import num2words
from docxtpl import DocxTemplate
import comtypes.client
import os

class CheckboxManager:
    def __init__(self, model):
        self.model = model

    def toggleAllCheckboxes(self, checked):
        checkState = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 1)
            if item.isCheckable():
                item.setCheckState(checkState)

class ContratosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        self.colunas = ['Comprasnet', 'Tipo', 'Processo', 'NUP', 'CNPJ', 'Fornecedor Formatado', 'Dias', 'Valor Global', 'Objeto', 'OM', 'Setor', 'CP', 'MSG', 'Vig. Início', 'Vig. Fim', 'Valor Formatado', 'Portaria', 'Gestor', 'Fiscal', 'Natureza Continuada']
        self.loadAndConfigureModel()

    def setupUI(self):
        self.layout = QVBoxLayout(self)
        self.setupSearchField()
        self.setupTableView()
        self.setupButtons()

    def setupSearchField(self):
        self.searchField = QLineEdit(self)
        self.searchField.setPlaceholderText("Buscar por nome da empresa ou outro dado...")
        self.layout.addWidget(self.searchField)

    def setupTableView(self):
        self.table_view = QTableView(self)
        self.layout.addWidget(self.table_view)
        self.table_view.setItemDelegate(CellBorderDelegate())
        self.table_view.setStyleSheet("""
            QTableView {
                background-color: black;
                color: white;
            }
        """)
        self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Configura a altura fixa das linhas e a política de redimensionamento do cabeçalho vertical
        altura_fixa = 20
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table_view.verticalHeader().setDefaultSectionSize(altura_fixa)
        self.table_view.verticalHeader().hide()
        self.table_view.clicked.connect(self.onTableViewClicked)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        # self.table_view.setSelectionMode(QTableView.SelectionMode.MultiSelection)33
        self.table_view.doubleClicked.connect(self.abrirDialogoEditarInformacoesAdicionais)

        QTimer.singleShot(1, self.ajustarLarguraColunas)

    def setupButtons(self):
        buttons_info = [
            ("Gerar Tabela", self.gerarTabelaExcel),
            ("CP Alerta Prazo", self.abrirDialogoGerarDocumentosCP),  
            ("Mensagem Cobrança", self.abrirDialogoAlertaPrazo),
            ("Termo de Subrogação", None),
            ("Termo de Encerramento", None),
            ("Informações Adicionais", self.abrirDialogoEditarInformacoesAdicionais),
            ("Marcar/Desmarcar Todos", self.onTestToggleClicked),
            ("Configurações", self.abrirDialogoConfiguracoes)]
        self.buttons_layout = QHBoxLayout()
        for text, func in buttons_info:
            btn = QPushButton(text, self)
            if func:  # Verifica se uma função foi fornecida
                btn.clicked.connect(func)
            self.buttons_layout.addWidget(btn)
        self.layout.addLayout(self.buttons_layout)

    def loadAndConfigureModel(self):
        contratos_data = load_data(CONTRATOS_PATH, ADICIONAIS_PATH)
        # Certifique-se de que contratos_data é o DataFrame ou estrutura de dados esperada por MultiColumnFilterProxyModel
        colunas = ['Comprasnet', 'Tipo', 'Processo', 'NUP', 'CNPJ', 'Fornecedor Formatado', 'Dias', 'Valor Global', 'Objeto', 'OM', 'Setor', 'CP', 'MSG', 'Vig. Início', 'Vig. Fim', 'Valor Formatado', 'Portaria', 'Gestor', 'Fiscal', 'Natureza Continuada']
        self.model = CustomTableModel(contratos_data, colunas, ICONS_DIR)
        self.proxyModel = MultiColumnFilterProxyModel(contratos_data)  # Passando contratos_data
        self.proxyModel.setSourceModel(self.model)
        self.table_view.setModel(self.proxyModel)
        self.checkboxManager = CheckboxManager(self.model)
        self.searchField.textChanged.connect(self.onSearchTextChanged)
        
    def gerarTabelaExcel(self):
        filteredData = getFilteredData(self.proxyModel)
        colunas = [self.model.headerData(i, Qt.Orientation.Horizontal) for i in range(self.model.columnCount())]
        saveFilteredDataToExcel(filteredData, colunas)

    def onSearchTextChanged(self, text):
        # Agora 'colunas' está definido, então podemos usá-lo sem causar AttributeError
        fornecedorIndex = self.colunas.index('Fornecedor') if 'Fornecedor' in self.colunas else -1
        if fornecedorIndex != -1:
            self.proxyModel.setFilterKeyColumn(fornecedorIndex)
            self.proxyModel.setFilterRegularExpression(QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption))
        else:
            print("Coluna 'Fornecedor' não encontrada nas colunas definidas.")

    def onTableViewClicked(self, index):
        if index.isValid():
            checkboxIndex = self.model.index(index.row(), 1)  # Coluna dos checkboxes
            item = self.model.itemFromIndex(checkboxIndex)
            if item and item.isCheckable():
                # Alternar o estado do checkbox
                newState = not item.checkState() == Qt.CheckState.Checked
                # Usar setData para atualizar o estado do checkbox
                self.model.setData(checkboxIndex, Qt.CheckState.Checked if newState else Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)

    def onSelectionChanged(self, selected, deselected):
        selected_rows = self.table_view.selectionModel().selectedRows()
        for index in selected_rows:
            # Aqui, você pode acessar os dados da linha selecionada diretamente do DataFrame
            row_data = self.model.dados.iloc[index.row()]
            # Agora, você pode armazenar 'row_data' onde precisar para uso posterior
            print(row_data)  # Exemplo de acesso aos dados

    def abrirDialogoEditarInformacoesAdicionais(self):
        contrato_atual = self.obterContratoAtual()
        if contrato_atual:
            self.dialogo = AtualizarDadosContratos(contrato_atual, self)
            self.dialogo.dadosContratosSalvos.connect(self.atualizarDadosTableView)
            if self.dialogo.exec() == QDialog.DialogCode.Accepted:
                pass  # O diálogo foi fechado com sucesso
        else:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um contrato para editar.")

    def atualizarDadosTableView(self):
        contratos_data = load_data(CONTRATOS_PATH, ADICIONAIS_PATH)  # Recarrega os dados
        self.model = CustomTableModel(contratos_data, self.colunas, ICONS_DIR)  # Cria um novo modelo com os dados atualizados
        self.table_view.setModel(self.model)  # Atualiza o modelo do QTreeView
        self.ajustarLarguraColunas()  # Ajusta a largura das colunas, se necessário

    def abrirDialogoConfiguracoes(self):
        dialog = ConfiguracoesDialog(self.colunas, self.table_view, self)
        dialog.exec()

    def ajustarLarguraColunas(self):
        for i in range(self.table_view.model().columnCount()):
            self.table_view.resizeColumnToContents(i)

    def onTestToggleClicked(self):
        # Verifica o estado do primeiro checkbox para decidir se irá marcar ou desmarcar todos
        if self.model.rowCount() > 0:
            firstItemState = self.model.item(0, 1).checkState()
            # Se o primeiro item estiver marcado, desmarcar todos, e vice-versa
            newState = not (firstItemState == Qt.CheckState.Checked)
            self.checkboxManager.toggleAllCheckboxes(newState)

    def obterContratoAtual(self):
        selection = self.table_view.selectionModel().selectedIndexes()
        if selection:
            # Se estiver usando um proxy model, assegure-se de mapear para o source model
            model = self.table_view.model().sourceModel() if hasattr(self.table_view.model(), 'sourceModel') else self.table_view.model()

            index = selection[0]  # Índice da célula selecionada no proxy model
            sourceIndex = self.table_view.model().mapToSource(index) if hasattr(self.table_view.model(), 'mapToSource') else index

            contrato_atual = {}
            for coluna in range(model.columnCount()):
                indice = model.index(sourceIndex.row(), coluna)
                chave = model.headerData(coluna, Qt.Orientation.Horizontal)
                valor = model.data(indice, Qt.ItemDataRole.DisplayRole)
                contrato_atual[chave] = valor

            print("Contrato Atual:", contrato_atual)
            return contrato_atual
        else:
            return None

    def coletarDadosSelecionados(self):
        dados_selecionados = []
        for row in range(self.model.rowCount()):
            checkbox_item = self.model.item(row, 1)  # Assumindo que os checkboxes estejam na coluna 1
            if checkbox_item.checkState() == Qt.CheckState.Checked:
                dados_linha = {
                    'numero_comprasnet': self.model.item(row, 2).text(),
                    'tipo': self.model.item(row, 3).text(),
                    'processo': self.model.item(row, 4).text(),                
                    'nup': self.model.item(row, 5).text(),
                    'cnpj': self.model.item(row, 6).text(), 
                    'empresa': self.model.item(row, 7).text(),
                    'dias_para_vencer': self.model.item(row, 8).text(),
                    'valor_global': self.model.item(row, 9).text(), 
                    'objeto': self.model.item(row, 10).text(),                    
                    'om': self.model.item(row, 11).text(), 
                    'setor': self.model.item(row, 12).text(), 
                    'cp': self.model.item(row, 13).text(),
                    'msg': self.model.item(row, 14).text(),
                    'inicio_vigencia': self.model.item(row, 15).text(), 
                    'fim_vigencia': self.model.item(row, 16).text(),                
                    'numero_contrato': self.model.item(row, 17).text(),  
                    'portaria': self.model.item(row, 18).text(),
                    'gestor': self.model.item(row, 19).text(),
                    'fiscal': self.model.item(row, 20).text(),
                    'prazo_limite': calcular_prazo_limite(self.model.item(row, 16).text())
                }
                dados_selecionados.append(dados_linha)
        return dados_selecionados

    def abrirDialogoAlertaPrazo(self):
        dados_selecionados = self.coletarDadosSelecionados()
        texto = self.prepararTextoAlertaPrazo(dados_selecionados)
        dialogo = MSGAlertaPrazo(texto)
        dialogo.exec()
        
    def prepararTextoAlertaPrazo(self, dados_selecionados):
        texto = "<p>ROTINA<br>"
        mes_atual = datetime.now().strftime("%b").upper()
        ano_atual = datetime.now().strftime('%Y')
        texto += f"R000000Z/<span style='color: blue;'>{mes_atual}</span>/<span style='color: blue;'>{ano_atual}</span><br>"
        texto += "DE NICITB<br>PARA SETDIS<br>GRNC<br>BT<br><br>"
        texto += "Renovação de Acordos Administrativos<br><br>"
        texto += "\nALFA - Contratos Administrativo<br><br>\n"        
        for idx, dados in enumerate(dados_selecionados, start=1):
            numero_extenso = numero_para_extenso(idx)
            # prazo_limite = calcular_prazo_limite(dados['fim_vigencia'])
            texto += (f"{numero_extenso} - Contrato administrativo n° <span style='color: blue;'>{dados['numero_contrato']}</span>\n"
                    f" tipo <span style='color: blue;'>{dados['tipo']}</span> | processo <span style='color: blue;'>{dados['processo']}</span> | "
                    f" nup <span style='color: blue;'>{dados['nup']}</span> | cnpj <span style='color: blue;'>{dados['cnpj']}</span> | "
                    f" empresa <span style='color: blue;'>{dados['empresa']}</span> | valor global <span style='color: blue;'>{dados['valor_global']}</span> | "
                    f" dias para vencer <span style='color: blue;'>{dados['dias_para_vencer']}</span> | objeto <span style='color: blue;'>{dados['objeto']}</span> | "
                    f" om <span style='color: blue;'>{dados['om']}</span> | setor <span style='color: blue;'>{dados['setor']}</span> | "
                    f" cp <span style='color: blue;'>{dados['cp']}</span> | msg <span style='color: blue;'>{dados['msg']}</span> | "
                    f" início vigência <span style='color: blue;'>{dados['inicio_vigencia']}</span> | fim vigência <span style='color: blue;'>{dados['fim_vigencia']}</span> | "
                    f" portaria <span style='color: blue;'>{dados['portaria']}</span> | gestor <span style='color: blue;'>{dados['gestor']}</span> | "
                    f" fiscal <span style='color: blue;'>{dados['fiscal']}</span><br><br>"
                    f"Prazo limite para renovação: <span style='color: red;'>{dados['prazo_limite']}</span><br><br>"
                    )
        texto += "</p>BT"
        return texto
    
    def abrirDialogoGerarDocumentosCP(self):
        dialog = NumeroCPDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            numero_cp = dialog.getNumeroCP()
            if numero_cp.isdigit():  # Verifica se o input é um número
                numero_cp = int(numero_cp)
                dados_selecionados = self.coletarDadosSelecionados()
                # Adiciona o numero_cp a cada item em dados_selecionados
                for dados in dados_selecionados:
                    # Formata o numero_cp com dois dígitos e o adiciona aos dados
                    dados['numero_cp'] = str(numero_cp).zfill(2)
                    numero_cp += 1  # Incrementa para o próximo documento
                self.gerarDocumentosCP(dados_selecionados)
            else:
                QMessageBox.warning(self, "Erro", "Número da CP inválido.")

    def gerarDocumentosCP(self, dados_selecionados):
        progress_dialog = QProgressDialog("Convertendo documentos para PDF...", "Cancelar", 0, len(dados_selecionados), self)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.show()

        for i, dados in enumerate(dados_selecionados, start=1):
            if dados['tipo'] == 'Contrato':
                template_path = CP_CONTRATOS_DIR / "cp_contrato.docx"
            else:
                template_path = CP_CONTRATOS_DIR / "cp_ata.docx"

            doc = DocxTemplate(template_path)
            doc.render(dados)

            processo_formatado = dados['processo'].replace('/', '-')
            nome_arquivo = f"CP-30-{str(dados['numero_cp']).zfill(2)}-Renovacao {dados['tipo']} {processo_formatado}.docx"
            caminho_completo = CP_CONTRATOS_DIR / nome_arquivo

            if not caminho_completo.parent.exists():
                os.makedirs(caminho_completo.parent)

            doc.save(caminho_completo)
            print(f"Documento salvo: {caminho_completo}")

            # Atualiza a barra de progresso antes de iniciar a conversão para PDF
            progress_dialog.setValue(i - 1)  # i-1 porque i começa de 1
            progress_dialog.setLabelText(f"Convertendo documento {i} de {len(dados_selecionados)} para PDF...")

            # Verifica se a operação foi cancelada
            if progress_dialog.wasCanceled():
                break

            # Converte o arquivo DOCX para PDF
            pdf_path = caminho_completo.with_suffix('.pdf')
            # Supondo que docx_to_pdf é uma função que você definiu para fazer a conversão
            self.docx_to_pdf(caminho_completo, pdf_path)
            print(f"Versão PDF salva: {pdf_path}")

        progress_dialog.setValue(len(dados_selecionados))

    def docx_to_pdf(self, docx_path, pdf_path):
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False
        doc = word.Documents.Open(str(docx_path))  # Converte Path para string aqui
        doc.SaveAs2(str(pdf_path), FileFormat=17)  # Converte Path para string aqui
        doc.Close()
        word.Quit()
        
def calcular_prazo_limite(fim_vigencia):
    data_fim_vigencia = datetime.strptime(fim_vigencia, "%d/%m/%Y")
    prazo_limite = data_fim_vigencia - timedelta(days=90)

    # Ajusta para o primeiro dia útil anterior se cair em um fim de semana
    while prazo_limite.weekday() > 4:  # 5 = sábado, 6 = domingo
        prazo_limite -= timedelta(days=1)

    return prazo_limite.strftime("%d/%m/%Y")

def numero_para_extenso(numero):
    # Converte o número para extenso em português
    extenso = num2words(numero, lang='pt_BR')
    # Substitui 'um' por 'uno' se for o caso
    if numero == 1:
        extenso = extenso.replace('um', 'uno')
    # Converte para maiúsculas
    return extenso.upper()


class MSGAlertaPrazo(QDialog):
    def __init__(self, detalhes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mensagem Cobrança")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # Campo de texto editável
        self.textEdit = QTextEdit()
        self.textEdit.setText(detalhes)
        self.textEdit.setReadOnly(False)  # Se desejar que o texto seja editável, defina como False
        layout.addWidget(self.textEdit)

        # Botão para copiar o texto para a área de transferência
        self.btnCopy = QPushButton("Copiar", self)
        self.btnCopy.clicked.connect(self.copyTextToClipboard)
        layout.addWidget(self.btnCopy)

    def copyTextToClipboard(self):
        text = self.textEdit.toPlainText()
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", "Texto copiado para a área de transferência.")

class NumeroCPDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Número da CP")
        self.layout = QVBoxLayout(self)

        self.label = QLabel("Informe o número da próxima CP:")
        self.layout.addWidget(self.label)

        self.lineEdit = QLineEdit(self)
        self.layout.addWidget(self.lineEdit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def getNumeroCP(self):
        return self.lineEdit.text()
#atualizar_dados_contratos.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import pandas as pd
from datetime import datetime
from pathlib import Path
from diretorios import *

class AtualizarDadosContratos(QDialog):
    dadosContratosSalvos = pyqtSignal(dict, int)

    def __init__(self, contrato_atual, table_view, parent=None):
        super().__init__(parent)
        self.contrato_atual = contrato_atual
        self.table_view = table_view
        self.camposDinamicos = {}
        self.status_labels = ["CP Enviada", "MSG Enviada", "Seção de Contratos", 
                              "Assessoria Jurídica", "CJACM", "Assinatura SIGDEM"]
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle(f"Atualizar Dados do Contrato nº {self.contrato_atual.get('Valor Formatado', '')}")
        self.setFixedSize(1040, 500)
        self.criarLayouts()
        self.criarWidgets()
        self.organizarLayouts()
        self.conectarSinais()

    def criarLayouts(self):
        self.mainLayout = QVBoxLayout()
        self.leftLayout = QVBoxLayout()
        self.centerLayout = QVBoxLayout()
        self.rightcenterLayout = QVBoxLayout()
        self.rightLayout = QVBoxLayout()
        self.buttonsLayout = QHBoxLayout()

    def criarWidgets(self):
        self.criarWidgetsEsquerda()
        self.criarWidgetsCentro()
        self.criarWidgetsCentroDireita()
        self.criarWidgetsDireita()
        self.criarBotoes()

    def criarWidgetsEsquerda(self):
        self.leftLayout.addWidget(QLabel(f"ID Comprasnet Contratos: {self.contrato_atual.get('Comprasnet', '')}"))
        self.leftLayout.addWidget(QLabel(f"Início da Vigência: {self.contrato_atual.get('Vig. Início', '')}"))
        self.leftLayout.addWidget(QLabel(f"Final da Vigência: {self.contrato_atual.get('Vig. Fim', '')}"))
        self.leftLayout.addWidget(QLabel(f"Fornecedor: {self.contrato_atual.get('Fornecedor Formatado', '')}"))
        self.leftLayout.addWidget(QLabel(f"CNPJ: {self.contrato_atual.get('CNPJ', '')}"))
        self.leftLayout.addWidget(QLabel(f"Valor Global: {self.contrato_atual.get('Valor Global', '')}"))

        # OM: [QLabel] seguido por [QComboBox] na linha abaixo
        omLabel = QLabel('OM:')
        self.leftLayout.addWidget(omLabel)
        self.omComboBox = QComboBox()

        try:
            tabela_uasg_df = pd.read_excel(TABELA_UASG_DIR)
            self.omComboBox.addItems(tabela_uasg_df['sigla_om'].tolist())
        except Exception as e:
            print(f"Erro ao carregar tabela UASG: {e}")

        self.leftLayout.addWidget(self.omComboBox)

        valor_om_atual = str(self.contrato_atual.get('OM', ''))

        if valor_om_atual in tabela_uasg_df['sigla_om'].values:
            index_om = tabela_uasg_df['sigla_om'].tolist().index(valor_om_atual)
            self.omComboBox.setCurrentIndex(index_om)

        # Setor Responsável: [QLabel] seguido por [QComboBox] na linha abaixo
        setorResponsavelLabel = QLabel('Setor Responsável:')
        self.leftLayout.addWidget(setorResponsavelLabel)
        self.setorResponsavelComboBox = QComboBox()
        self.leftLayout.addWidget(self.setorResponsavelComboBox)

        # Carrega os setores responsáveis baseados na seleção inicial de OM
        self.atualizarSetoresResponsaveis()
        # Após carregar os setores responsáveis no setorResponsavelComboBox
        valor_setor_atual = str(self.contrato_atual.get('Setor', ''))
        index_setor = self.obterIndicePorTexto(self.setorResponsavelComboBox, valor_setor_atual)
        if index_setor is not None:
            self.setorResponsavelComboBox.setCurrentIndex(index_setor)

        # Tipo: [QLabel] seguido por [QRadioButton Contrato] e [QRadioButton Ata] na linha abaixo
        tipoLabel = QLabel('Tipo:')
        self.leftLayout.addWidget(tipoLabel)
        tipoLayout = QHBoxLayout()
        self.tipoGroup = QButtonGroup(self)
        self.tipoContratoRadio = QRadioButton("Contrato")
        self.tipoAtaRadio = QRadioButton("Ata")
        self.tipoGroup.addButton(self.tipoContratoRadio)
        self.tipoGroup.addButton(self.tipoAtaRadio)
        tipoLayout.addWidget(self.tipoContratoRadio)
        tipoLayout.addWidget(self.tipoAtaRadio)
        self.leftLayout.addLayout(tipoLayout)

        # Natureza Continuada: [QLabel] seguido por [QRadioButton Sim] e [QRadioButton Não] na linha abaixo
        naturezaLabel = QLabel('Natureza Continuada:')
        self.leftLayout.addWidget(naturezaLabel)
        naturezaLayout = QHBoxLayout()
        self.naturezaContinuadaGroup = QButtonGroup(self)
        self.naturezaContinuadaSimRadio = QRadioButton("Sim")
        self.naturezaContinuadaNaoRadio = QRadioButton("Não")
        self.naturezaContinuadaGroup.addButton(self.naturezaContinuadaSimRadio)
        self.naturezaContinuadaGroup.addButton(self.naturezaContinuadaNaoRadio)
        naturezaLayout.addWidget(self.naturezaContinuadaSimRadio)
        naturezaLayout.addWidget(self.naturezaContinuadaNaoRadio)
        self.leftLayout.addLayout(naturezaLayout)

        self.leftLayout.setAlignment(Qt.AlignmentFlag.AlignTop) # Alinha o conteúdo do bloco da esquerda ao topo

        # Inicializa os estados dos botões de rádio
        self.tipoContratoRadio.setChecked(self.contrato_atual.get('Tipo', '') != 'Ata')
        self.tipoAtaRadio.setChecked(self.contrato_atual.get('Tipo', '') == 'Ata')
        self.naturezaContinuadaSimRadio.setChecked(self.contrato_atual.get('Natureza Continuada', '') == 'Sim')
        self.naturezaContinuadaNaoRadio.setChecked(self.contrato_atual.get('Natureza Continuada', '') != 'Sim')

        termoAditivoLabel = QLabel('Termo Aditivo:')
        self.leftLayout.addWidget(termoAditivoLabel)
        self.termoAditivoComboBox = QComboBox()
        self.leftLayout.addWidget(self.termoAditivoComboBox)

        self.tipoContratoRadio.toggled.connect(self.atualizarNaturezaContinuada)
        self.tipoAtaRadio.toggled.connect(self.atualizarNaturezaContinuada)
        self.omComboBox.currentIndexChanged.connect(self.atualizarSetoresResponsaveis)

        self.tipoContratoRadio.toggled.connect(self.atualizarTermosRenovacao)
        self.tipoAtaRadio.toggled.connect(self.atualizarTermosRenovacao)
        # Atualiza os termos de renovação com base no tipo de documento selecionado
        self.atualizarTermosRenovacao()

    def atualizarTermosRenovacao(self):
        # Limpa os itens existentes no comboBox
        self.termoAditivoComboBox.clear()

        # Verifica qual botão de rádio está selecionado e atualiza os termos de renovação
        if self.tipoContratoRadio.isChecked():
            termosRenovacao = ['Contrato Inicial', '1º Termo Aditivo', '2º Termo Aditivo', '3º Termo Aditivo', '4º Termo Aditivo', '5º Termo Aditivo']
        elif self.tipoAtaRadio.isChecked():
            termosRenovacao = ['Ata Inicial', '1º Termo Aditivo', '2º Termo Aditivo', '3º Termo Aditivo', '4º Termo Aditivo', '5º Termo Aditivo']

        # Adiciona os termos de renovação atualizados ao comboBox
        self.termoAditivoComboBox.addItems(termosRenovacao)

        # Define o valor pré-selecionado com base no valor do 'Termo Aditivo' do contrato atual
        valor_termo_aditivo_atual = self.contrato_atual.get('Termo Aditivo', '')
        if valor_termo_aditivo_atual in termosRenovacao:
            index = self.termoAditivoComboBox.findText(valor_termo_aditivo_atual)
            self.termoAditivoComboBox.setCurrentIndex(index)
        
    def criarWidgetsCentro(self):
        # Adicionando novas informações para "Processo", "NUP", e "Objeto"
        self.centerLayout.addWidget(QLabel("Processo:"))
        self.processoComboBox = QComboBox()
        self.processoComboBox.addItems(["PE", "DE", "TJIL", "TJDL", "ACT"])
        # Define o valor atual do processoComboBox com base no contrato_atual
        valor_processo_atual = str(self.contrato_atual.get('Processo', ''))
        index_processo = self.obterIndicePorTexto(self.processoComboBox, valor_processo_atual.split()[0] if valor_processo_atual else "")
        if index_processo is not None:
            self.processoComboBox.setCurrentIndex(index_processo)
        
        self.processoLineEdit = QLineEdit()
        self.anoLineEdit = QLineEdit(str(datetime.now().year))
        self.anoLineEdit.setFixedWidth(50)  # Limita o tamanho do QLineEdit do ano
        processoLayout = QHBoxLayout()
        processoLayout.addWidget(self.processoComboBox)
        processoLayout.addWidget(self.processoLineEdit)
        processoLayout.addWidget(self.anoLineEdit)
        self.centerLayout.addLayout(processoLayout)

        self.centerLayout.addWidget(QLabel("NUP:"))
        self.nupLineEdit = QLineEdit(str(self.contrato_atual.get('NUP', '')))  # Conversão para string aqui
        self.nupLineEdit.setPlaceholderText("00000.00000/0000-00")
        self.centerLayout.addWidget(self.nupLineEdit)

        self.centerLayout.addWidget(QLabel("Número do Contrato/Ata:"))
        self.numeroContratoAtaEdit = QLineEdit(str(self.contrato_atual.get('Valor Formatado', '')))  # Conversão para string aqui
        self.numeroContratoAtaEdit.setPlaceholderText("00000/00-000/00")
        self.centerLayout.addWidget(self.numeroContratoAtaEdit)

        self.centerLayout.addWidget(QLabel("Objeto:"))
        self.objetoLineEdit = QLineEdit(str(self.contrato_atual.get('Objeto', '')))
        self.centerLayout.addWidget(self.objetoLineEdit)

        self.centerLayout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Alinha o conteúdo do bloco da direita ao topo

        # Define o valor dos campos de processo com base no contrato_atual
        if valor_processo_atual:
            processo_split = valor_processo_atual.split()
            if len(processo_split) >= 2:
                processo_numero = processo_split[1].split('/')[0]
                if len(processo_numero) == 1:  # Adiciona zero à esquerda para números de 1 a 9
                    processo_numero = '0' + processo_numero
                self.processoLineEdit.setText(processo_numero)
                self.anoLineEdit.setText(processo_split[1].split('/')[1])
        self.centerLayout.setAlignment(Qt.AlignmentFlag.AlignTop) # Alinha o conteúdo do bloco da esquerda ao topo
                
        self.comentariosTextEdit = CustomTextEdit()
        
        self.centerLayout.addWidget(QLabel("Comentários:"))
        comentarios = str(self.contrato_atual.get('Comentários', '')).strip()
        if comentarios and not comentarios.startswith("- "):
            comentarios = "- " + comentarios[0].upper() + comentarios[1:]
        elif not comentarios or comentarios in ['-Nan', '-']:
            comentarios = ""
        self.comentariosTextEdit.setPlaceholderText("Digite seus comentários aqui...")
        self.comentariosTextEdit.setPlainText(comentarios)
        
        # Configuração do tamanho mínimo como antes
        fontMetrics = self.comentariosTextEdit.fontMetrics()
        lineHeight = fontMetrics.lineSpacing()
        self.comentariosTextEdit.setMinimumHeight(lineHeight * 5)

        # Adiciona o QTextEdit ao layout
        self.centerLayout.addWidget(self.comentariosTextEdit)

    def criarWidgetsCentroDireita(self):
        self.rightcenterLayout.addWidget(QLabel("Status:"))
        self.statusGroup = QButtonGroup(self)
        self.statusGroup.setExclusive(True)

        self.statusLabelsOriginal = {}
        self.lineEditMapping = {}

        status_labels = ["CP Enviada", "MSG Enviada", "Seção de Contratos", "Assessoria Jurídica", "CJACM", "Assinatura SIGDEM"]
        status_keys = ["Status0", "Status1", "Status2", "Status3", "Status4", "Status5"]

        for i, label in enumerate(status_labels):
            radioButton = QRadioButton(label)
            self.statusGroup.addButton(radioButton)
            self.rightcenterLayout.addWidget(radioButton)

            self.statusLabelsOriginal[radioButton] = label

            lineEdit = None
            if label in ["CP Enviada", "MSG Enviada"]:
                lineEdit = QLineEdit()
                placeholder = "Ex: 30-15/2024" if label == "CP Enviada" else "Ex: R-151612Z/FEV/2024"
                lineEdit.setPlaceholderText(placeholder)
                self.rightcenterLayout.addWidget(lineEdit)
                self.lineEditMapping[radioButton] = lineEdit

            statusKey = status_keys[i]
            print(f"Checking {statusKey} in contrato_atual")
            if statusKey in self.contrato_atual and self.contrato_atual[statusKey]:
                valorStatus = self.contrato_atual[statusKey]
                print(f"Found {statusKey}: {valorStatus}")
                radioButton.setChecked(True)
                if lineEdit:
                    _, data = valorStatus.split(' em ', 1)
                    lineEdit.setText(data)
                # Adiciona o texto atualizado ao radioButton (correção para persistir o status)
                radioButton.setText(f"{label} em {data}")

            # Conecta o sinal de alteração do radioButton a uma função de manipulação
            radioButton.toggled.connect(lambda checked, rb=radioButton, sk=status_keys[i]: self.marcarStatus(rb, sk, checked) if checked else None)

        self.calendar = QCalendarWidget()
        self.calendar.activated.connect(self.atualizarStatusLabel)
        self.calendar.setGridVisible(True)
        self.rightcenterLayout.addWidget(self.calendar)


    def marcarStatus(self, radioButton, statusKey, checked):
        if checked:
            formattedDate = self.calendar.selectedDate().toString("dd/MM/yyyy")
            originalLabel = self.statusLabelsOriginal[radioButton]
            updatedStatus = f"{originalLabel} em {formattedDate}"
            print(f"Updating {statusKey} to {updatedStatus}")
            self.contrato_atual[statusKey] = updatedStatus
            # Atualiza o texto do radioButton para refletir a mudança
            radioButton.setText(updatedStatus)


    def salvarStatus(self):
        statusSelecionado = None
        dataSelecionada = None

        # Verifica qual botão está marcado e guarda a informação do status mais recente
        for label in reversed(self.statusLabelsOriginal.values()):
            for radioButton in self.statusGroup.buttons():
                if radioButton.isChecked() and self.statusLabelsOriginal[radioButton] == label:
                    statusSelecionado = label
                    # Supondo que você tenha uma maneira de obter a data selecionada para este status
                    dataSelecionada = self.calendar.selectedDate().toString("dd/MM/yyyy")
                    break
            if statusSelecionado:
                break

        if statusSelecionado:
            # Formata o status com a data selecionada
            statusFinal = f"{statusSelecionado} em {dataSelecionada}"
            # Salva o status no dicionário ou modelo de dados
            self.contrato_atual['Status'] = statusFinal
            print(f"Status atualizado: {statusFinal}")
        else:
            print("Nenhum status selecionado.")

    def atualizarStatusLabel(self, date):
        selectedButton = self.statusGroup.checkedButton()
        if selectedButton:
            formattedDate = date.toString("dd/MM/yyyy")
            originalLabel = self.statusLabelsOriginal[selectedButton]
            selectedButton.setText(f"{originalLabel} em {formattedDate}")

    def reiniciarStatus(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Icon.Question)
        msgBox.setWindowTitle("Reiniciar Status")
        msgBox.setText("Deseja reiniciar o status?")

        # Cria botões customizados
        apenasSelecionadoButton = msgBox.addButton("Apenas Selecionado", QMessageBox.ButtonRole.YesRole)
        todosStatusButton = msgBox.addButton(" Todos os Status  ", QMessageBox.ButtonRole.NoRole)


        # Executa a caixa de mensagem e obtém a resposta do usuário
        msgBox.exec()

        # Verifica qual botão foi pressionado
        if msgBox.clickedButton() == apenasSelecionadoButton:
            # Reinicia apenas o QRadioButton selecionado
            selectedButton = self.statusGroup.checkedButton()
            if selectedButton:
                originalLabel = self.statusLabelsOriginal[selectedButton]
                selectedButton.setText(originalLabel)
                # Desmarca o QRadioButton selecionado
                self.statusGroup.setExclusive(False)
                selectedButton.setChecked(False)
                self.statusGroup.setExclusive(True)
        elif msgBox.clickedButton() == todosStatusButton:
            # Reinicia todos os QRadioButton para seus valores originais
            for button, label in self.statusLabelsOriginal.items():
                button.setText(label)
            # Desmarca qualquer QRadioButton selecionado
            self.statusGroup.setExclusive(False)
            if self.statusGroup.checkedButton():
                self.statusGroup.checkedButton().setChecked(False)
            self.statusGroup.setExclusive(True)


    def criarWidgetsDireita(self):
        self.rightLayout.addWidget(QLabel("Portaria da Equipe de Fiscalização:"))
        self.portariaEdit = QLineEdit(str(self.contrato_atual.get('Portaria', '')))
        self.rightLayout.addWidget(self.portariaEdit)

        self.rightLayout.addWidget(QLabel("Gestor:"))
        self.gestorEdit = QLineEdit(str(self.contrato_atual.get('Gestor', '')))
        self.rightLayout.addWidget(self.gestorEdit)

        self.rightLayout.addWidget(QLabel("Gestor Substituto:"))
        self.gestorSubstitutoEdit = QLineEdit(str(self.contrato_atual.get('Gestor Substituto', '')))
        self.rightLayout.addWidget(self.gestorSubstitutoEdit)

        self.rightLayout.addWidget(QLabel("Fiscal:"))
        self.fiscalEdit = QLineEdit(str(self.contrato_atual.get('Fiscal', '')))
        self.rightLayout.addWidget(self.fiscalEdit)

        self.rightLayout.addWidget(QLabel("Fiscal Substituto:"))
        self.fiscalSubstitutoEdit = QLineEdit(str(self.contrato_atual.get('Fiscal Substituto', '')))
        self.rightLayout.addWidget(self.fiscalSubstitutoEdit)

        self.rightLayout.setAlignment(Qt.AlignmentFlag.AlignTop) # Alinha o conteúdo do bloco da esquerda ao topo

    def criarBotoes(self):
        # Criação do botão Reiniciar
        self.reiniciarButton = QPushButton('Reiniciar')
        self.reiniciarButton.clicked.connect(self.reiniciarStatus)  # Supondo que você tenha um método chamado reiniciarStatus para lidar com o evento de clique

        # Botão Salvar
        self.saveButton = QPushButton('Salvar')

        # Botão Cancelar
        self.cancelButton = QPushButton('Cancelar')

        # Adicionando os botões ao layout dos botões
        self.buttonsLayout.addWidget(self.reiniciarButton)  # Adiciona o botão Reiniciar ao layout
        self.buttonsLayout.addWidget(self.saveButton)
        self.buttonsLayout.addWidget(self.cancelButton)

    def ajustarTamanhosLayouts(self):
        # Cria widgets contêineres para os layouts de esquerda, centro e direita
        leftContainer = QWidget()
        centerContainer = QWidget()
        rightcenterContainer = QWidget()
        rightContainer = QWidget()

        # Define um nome de objeto único para cada contêiner
        leftContainer.setObjectName("leftContainer")
        centerContainer.setObjectName("centerContainer")
        rightcenterContainer.setObjectName("rightCenterContainer")
        rightContainer.setObjectName("rightContainer")

        # Define os layouts para os contêineres
        leftContainer.setLayout(self.leftLayout)
        centerContainer.setLayout(self.centerLayout)
        rightcenterContainer.setLayout(self.rightcenterLayout)
        rightContainer.setLayout(self.rightLayout)

        # Aplica a folha de estilo para adicionar bordas somente aos contêineres externos usando os nomes de objeto
        estiloBorda = """
        QWidget#leftContainer, QWidget#centerContainer, QWidget#rightCenterContainer, QWidget#rightContainer {
            border: 1px solid rgb(173, 173, 173);
        }
        """
        self.setStyleSheet(estiloBorda)  # Aplica a folha de estilo ao nível do diálogo ou widget pai

        # Define o tamanho preferido para os contêineres
        leftContainer.setFixedSize(250, 450)
        centerContainer.setFixedSize(250, 450)
        rightcenterContainer.setFixedSize(250, 450)
        rightContainer.setFixedSize(250, 450)

        # Adiciona os contêineres ao layout horizontal
        self.leftCenterRightLayout.addWidget(leftContainer)
        self.leftCenterRightLayout.addWidget(centerContainer)
        self.leftCenterRightLayout.addWidget(rightcenterContainer)
        self.leftCenterRightLayout.addWidget(rightContainer)

    def organizarLayouts(self):
        self.leftCenterRightLayout = QHBoxLayout()
        self.ajustarTamanhosLayouts()
        self.mainLayout.addLayout(self.leftCenterRightLayout)
        self.mainLayout.addLayout(self.buttonsLayout)
        self.setLayout(self.mainLayout)

    def conectarSinais(self):
        self.saveButton.clicked.connect(self.salvar)
        self.cancelButton.clicked.connect(self.reject)

    def obterIndicePorTexto(self, comboBox, texto):
        for i in range(comboBox.count()):
            if comboBox.itemText(i) == texto:
                return i
        return None

    def atualizarSetoresResponsaveis(self):
        sigla_om_selecionada = self.omComboBox.currentText()
        try:
            setores_om_df = pd.read_excel(SETORES_OM)
            # Garantindo que estamos acessando a coluna correta usando a sigla OM como chave
            if sigla_om_selecionada in setores_om_df.columns:
                setores = setores_om_df[sigla_om_selecionada].dropna()  # Remove valores nulos
                setores_str = setores.apply(lambda x: str(x) if not pd.isnull(x) else '').tolist()  # Converte para string e lista
                self.setorResponsavelComboBox.clear()
                self.setorResponsavelComboBox.addItems(setores_str)
            else:
                # Se a sigla OM não estiver nas colunas, permite entrada manual
                self.setorResponsavelComboBox.clear()
                self.setorResponsavelComboBox.setEditable(True)
        except Exception as e:
            print(f"Erro ao carregar setores de OM: {e}")
            self.setorResponsavelComboBox.clear()
            self.setorResponsavelComboBox.setEditable(True)
            
    def atualizarNaturezaContinuada(self):
        # Se o botão de rádio "Contrato" estiver marcado, seleciona automaticamente "Sim" para Natureza Continuada
        if self.tipoContratoRadio.isChecked():
            self.naturezaContinuadaSimRadio.setChecked(True)
        # Se o botão de rádio "Ata" estiver marcado, seleciona automaticamente "Não" para Natureza Continuada
        elif self.tipoAtaRadio.isChecked():
            self.naturezaContinuadaNaoRadio.setChecked(True)

    def getUpdatedData(self):
        # Retorna o dicionário 'contrato_atual' com as atualizações aplicadas
        return self.contrato_atual
            
    def salvar(self):
        print("Dados do contrato atual antes das alterações:", self.contrato_atual)

        self.salvarStatus()
        tipo_selecionado = "Contrato" if self.tipoContratoRadio.isChecked() else "Ata"
        natureza_continuada_selecionada = "Sim" if self.naturezaContinuadaSimRadio.isChecked() else "Não"

        # Obter texto do QTextEdit de comentários
        comentarios = self.comentariosTextEdit.toPlainText().strip()
        # Inicializa as variáveis para os valores de CP e MSG
        valor_cp = ""
        valor_msg = ""

        # Localiza os QLineEdit para CP e MSG usando os QRadioButton mapeados
        for radioButton, lineEdit in self.lineEditMapping.items():
            if self.statusLabelsOriginal[radioButton] == "CP Enviada":
                valor_cp = lineEdit.text().strip()
            elif self.statusLabelsOriginal[radioButton] == "MSG Enviada":
                valor_msg = lineEdit.text().strip()

        # Obtem o prefixo do processo a partir da seleção no processoComboBox e formata o valor do processo
        processo_prefixo = self.processoComboBox.currentText()
        if processo_prefixo:
            processo_codigo = processo_prefixo.split()[0]
            numero_processo = self.processoLineEdit.text().strip()
            ano_processo = self.anoLineEdit.text().strip()
            valor_processo_formatado = f"{processo_codigo} {numero_processo}/{ano_processo}"
        else:
            valor_processo_formatado = ""

        # Define os campos adicionais com o valor do processo formatado
        campos_adicionais = {
            'Processo': valor_processo_formatado,
            'NUP': self.nupLineEdit.text().strip(),
            'Valor Formatado': self.numeroContratoAtaEdit.text().strip(),
            'Objeto': self.objetoLineEdit.text().strip(),
            'OM': self.omComboBox.currentText().strip(),
            'Setor': self.setorResponsavelComboBox.currentText().strip(),
            'CP': valor_cp,
            'MSG': valor_msg,
            'Portaria': self.portariaEdit.text().strip(),
            'Gestor': self.gestorEdit.text().strip(),
            'Gestor Substituto': self.gestorSubstitutoEdit.text().strip(),
            'Fiscal': self.fiscalEdit.text().strip(),
            'Fiscal Substituto': self.fiscalSubstitutoEdit.text().strip(),
            'Tipo': tipo_selecionado,
            'Natureza Continuada': natureza_continuada_selecionada,
            'Número do instrumento': self.contrato_atual['Comprasnet'],
            'Comentários': comentarios,
            'Termo Aditivo': self.termoAditivoComboBox.currentText().strip(),
            'Status0': self.contrato_atual.get('Status0', ''),
            'Status1': self.contrato_atual.get('Status1', ''),
            'Status2': self.contrato_atual.get('Status2', ''),
            'Status3': self.contrato_atual.get('Status3', ''),
            'Status4': self.contrato_atual.get('Status4', ''),
            'Status5': self.contrato_atual.get('Status5', '')
        }


        try:
            df_adicionais = pd.read_csv(ADICIONAIS_PATH, dtype='object')
            df_adicionais = df_adicionais.astype('object')

            # Verifica se o registro já existe
            indice = df_adicionais.index[df_adicionais['Número do instrumento'] == campos_adicionais['Número do instrumento']].tolist()
            if indice:
                indice = indice[0]
                for campo, valor in campos_adicionais.items():
                    df_adicionais.at[indice, campo] = str(valor)
            else:
                # Adiciona uma nova linha com os dados do contrato atual se não encontrar um registro correspondente
                novo_registro = pd.DataFrame([campos_adicionais], columns=df_adicionais.columns)
                df_adicionais = pd.concat([df_adicionais, novo_registro], ignore_index=True, sort=False).fillna(pd.NA)

            df_adicionais.to_csv(ADICIONAIS_PATH, index=False, encoding='utf-8')
            QMessageBox.information(self, "Sucesso", "Dados do contrato atualizados com sucesso.")
            self.dadosContratosSalvos.emit(campos_adicionais, self.indice_linha)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar os dados do contrato: {e}")

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super(CustomTextEdit, self).__init__(parent)
        self.setPlainText("1 - ")  # Inicia com "1 - "
        self.last_line_count = 1  # Inicializa o last_line_count aqui
        self.textChanged.connect(self.handleTextChange)

    def keyPressEvent(self, event: QKeyEvent):
        cursor = self.textCursor()
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Inserir nova numeração somente se o cursor estiver no final da linha
            if cursor.atBlockEnd():
                next_line_number = self.toPlainText().count('\n') + 1
                cursor.insertText(f"\n{next_line_number} - ")
            else:
                cursor.insertText("\n")
            event.accept()
        else:
            super(CustomTextEdit, self).keyPressEvent(event)

    def handleTextChange(self):
        """Chamado quando o texto é alterado."""
        current_line_count = self.toPlainText().count('\n') + 1
        if current_line_count != self.last_line_count:
            # Renumerar apenas se o número de linhas mudou
            self.renumberLines()
        self.last_line_count = current_line_count

    def renumberLines(self):
        """Renumerar todas as linhas para manter a sequência correta."""
        text = self.toPlainText()
        lines = text.split('\n')
        corrected_lines = []
        for i, line in enumerate(lines, start=1):
            parts = line.split(' - ', 1)
            if len(parts) > 1:
                corrected_lines.append(f"{i} - {parts[1]}")
            else:
                corrected_lines.append(f"{i} - ")

        cursor_position = self.textCursor().position()
        self.blockSignals(True)
        self.setPlainText("\n".join(corrected_lines))
        self.blockSignals(False)

        # Restaurar a posição do cursor
        cursor = self.textCursor()
        cursor.setPosition(min(cursor_position, len(self.toPlainText())))
        self.setTextCursor(cursor)
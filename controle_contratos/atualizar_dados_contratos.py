#atualizar_dados_contratos.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import pandas as pd
from datetime import datetime
from pathlib import Path
from diretorios import *
import re
from docxtpl import DocxTemplate
import comtypes.client
import os

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
                
        self.comentariosTextEdit = CustomTextEdit(self)
        self.centerLayout.addWidget(QLabel("Comentários:"))
        comentarios = str(self.contrato_atual.get('Comentários', '')).strip()
        self.comentariosTextEdit.setPlainText(comentarios)

        # Adiciona o QTextEdit ao layout
        self.centerLayout.addWidget(self.comentariosTextEdit)

    def criarWidgetsCentroDireita(self):
        self.rightcenterLayout.addWidget(QLabel("Status:"))
        self.statusGroup = QButtonGroup(self)
        self.statusGroup.setExclusive(True)

        self.statusLabelsOriginal = {}

        # Inicializa lineEditCP e lineEditMSG antes de criar os widgets
        self.lineEditCP = QLineEdit()
        self.lineEditMSG = QLineEdit()
        
        # Carrega os valores de CP e MSG do contrato atual, se existirem
        valor_cp_atual = self.contrato_atual.get('CP', '').strip()
        valor_msg_atual = self.contrato_atual.get('MSG', '').strip()
        self.lineEditCP.setText(valor_cp_atual)
        self.lineEditMSG.setText(valor_msg_atual)
        
        status_labels = ["CP Enviada", "MSG Enviada", "Seção de Contratos", "Assessoria Jurídica", "CJACM", "Assinatura SIGDEM"]
        status_keys = ["Status0", "Status1", "Status2", "Status3", "Status4", "Status5"]

        for i, label in enumerate(status_labels):
            radioButton = QRadioButton(label)
            self.statusGroup.addButton(radioButton)
            self.rightcenterLayout.addWidget(radioButton)

            self.statusLabelsOriginal[radioButton] = label

            # Conecta o sinal de alteração do radioButton a uma função de manipulação
            radioButton.toggled.connect(lambda checked, rb=radioButton, sk=status_keys[i]: self.marcarStatus(rb, sk, checked) if checked else None)

            if label == "CP Enviada":
                placeholder = "Digite o nº da CP, Ex: 30-15/2024"
                self.lineEditCP.setPlaceholderText(placeholder)
                self.rightcenterLayout.addWidget(self.lineEditCP)

            elif label == "MSG Enviada":
                placeholder = "Digite a MSG, Ex: R-151612Z/FEV/2024"
                self.lineEditMSG.setPlaceholderText(placeholder)
                self.rightcenterLayout.addWidget(self.lineEditMSG)
            # Parte ajustada para lidar com a atualização dos valores
                
            statusKey = f"Status{i}"
            if statusKey in self.contrato_atual:
                valorStatus = self.contrato_atual[statusKey]
                if ' em ' in valorStatus:
                    status, data = valorStatus.split(' em ', 1)
                    radioButton.setChecked(True)
                    radioButton.setText(valorStatus)  # Atualiza com o valor que inclui a data
                    
        self.calendar = QCalendarWidget()
        self.calendar.activated.connect(self.atualizarStatusLabel)
        self.calendar.setGridVisible(True)
        self.rightcenterLayout.addWidget(self.calendar)

    def marcarStatus(self, radioButton, statusKey, checked):
        if checked:
            originalLabel = self.statusLabelsOriginal[radioButton]
            # Verifica se já existe uma data definida para o status
            if statusKey in self.contrato_atual and ' em ' in self.contrato_atual[statusKey]:
                # Extrai a data existente
                _, existingDate = self.contrato_atual[statusKey].split(' em ', 1)
                updatedStatus = f"{originalLabel} em {existingDate}"  # Mantém a data existente
            else:
                # Se não houver data definida, não atualiza a data neste ponto
                updatedStatus = originalLabel  # Mantém apenas o label original

            print(f"Updating {statusKey} to {updatedStatus}")
            self.contrato_atual[statusKey] = updatedStatus
            # Atualiza o texto do radioButton para refletir a mudança
            radioButton.setText(updatedStatus)

    def desmarcarTodosBotoes(self):
        # Desmarca todos os botões de rádio no grupo statusGroup
        for button in self.statusGroup.buttons():
            button.setChecked(False)

    def salvarStatus(self):
        self.desmarcarTodosBotoes()  # Desmarca todos os botões antes de salvar o status

        for i, radioButton in enumerate(self.statusGroup.buttons()):
            originalLabel = self.statusLabelsOriginal[radioButton]
            statusKey = f"Status{i}"

            # Se o status atual no dicionário já contém uma data, mantenha essa informação.
            if ' em ' in self.contrato_atual.get(statusKey, ''):
                statusAtualComData = self.contrato_atual[statusKey]
            else:
                statusAtualComData = originalLabel  # Mantém apenas o label sem adicionar uma nova data.

            self.contrato_atual[statusKey] = statusAtualComData

            # Atualiza o texto do radioButton se estiver marcado para refletir a mudança.
            if radioButton.isChecked():
                radioButton.setText(statusAtualComData)

            print(f"{statusKey}: {self.contrato_atual[statusKey]}")

    def atualizarStatusLabel(self, date):
        selectedButton = self.statusGroup.checkedButton()
        if selectedButton:
            formattedDate = date.toString("dd/MM/yyyy")
            originalLabel = self.statusLabelsOriginal[selectedButton]
            print(f"Data selecionada: {formattedDate}")
            print(f"Botão selecionado antes da atualização: {selectedButton.text()}")
            
            # Atualiza o status no dicionário com a nova data
            updated = False
            for i, radioButton in enumerate(self.statusGroup.buttons()):
                if radioButton == selectedButton:
                    statusKey = f"Status{i}"
                    self.contrato_atual[statusKey] = f"{originalLabel} em {formattedDate}"
                    print(f"{statusKey} atualizado para: {self.contrato_atual[statusKey]}")
                    updated = True
                    break
            
            # Confirmação de que a atualização ocorreu
            if updated:
                # Atualiza o texto do botão selecionado
                selectedButton.setText(f"{originalLabel} em {formattedDate}")
                print(f"Botão selecionado após atualização: {selectedButton.text()}")
            else:
                print("Atualização de status falhou. O botão selecionado não corresponde a nenhum status conhecido.")

    def reiniciarStatus(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Icon.Question)
        msgBox.setWindowTitle("Reiniciar Status")
        msgBox.setText("Deseja reiniciar o status?")

        apenasSelecionadoButton = msgBox.addButton("Apenas Selecionado", QMessageBox.ButtonRole.YesRole)
        todosStatusButton = msgBox.addButton("Todos os Status", QMessageBox.ButtonRole.NoRole)

        response = msgBox.exec()

        if msgBox.clickedButton() == apenasSelecionadoButton:
            self.reiniciarStatusSelecionado()
        elif msgBox.clickedButton() == todosStatusButton:
            self.reiniciarTodosStatus()

    def reiniciarStatusSelecionado(self):
        selectedButton = self.statusGroup.checkedButton()
        if selectedButton:
            statusKey = self.findStatusKeyForButton(selectedButton)
            if statusKey:
                self.contrato_atual[statusKey] = ''
                selectedButton.setText(self.statusLabelsOriginal[selectedButton])
                
                # Limpa o QLineEdit se o status selecionado for "CP Enviada" ou "MSG Enviada"
                label = self.statusLabelsOriginal[selectedButton]
                if label == "CP Enviada":
                    self.lineEditCP.clear()
                elif label == "MSG Enviada":
                    self.lineEditMSG.clear()

    def reiniciarTodosStatus(self):
        for radioButton in self.statusGroup.buttons():
            statusKey = self.findStatusKeyForButton(radioButton)
            if statusKey:
                self.contrato_atual[statusKey] = ''
                radioButton.setText(self.statusLabelsOriginal[radioButton])
        
        # Limpa ambos os QLineEdit já que todos os status estão sendo reiniciados
        self.lineEditCP.clear()
        self.lineEditMSG.clear()

    def findStatusKeyForButton(self, button):
        for statusKey, radioButton in enumerate(self.statusGroup.buttons()):
            if button == radioButton:
                return f"Status{statusKey}"
        return None

    def adicionarTitulo(self, titulo, layout):
        # Cria e adiciona um QLabel como título ao layout vertical
        layout.addWidget(QLabel(titulo))

    def adicionarCampoDuplo(self, chave1, chave2, layout, placeholder1="", placeholder2=""):
        hLayout = QHBoxLayout()

        # Cria os QLineEdit para as chaves fornecidas
        edit1 = QLineEdit(str(self.contrato_atual.get(chave1, '')))
        edit2 = QLineEdit(str(self.contrato_atual.get(chave2, '')))

        # Configura o texto de placeholder para os edits, se fornecido
        if placeholder1:
            edit1.setPlaceholderText(placeholder1)
        if placeholder2:
            edit2.setPlaceholderText(placeholder2)

        hLayout.addWidget(edit1)
        hLayout.addWidget(edit2)

        # Configura a proporção do espaço que cada widget ocupa no layout, se necessário
        hLayout.setStretch(0, 1)
        hLayout.setStretch(1, 3)

        layout.addLayout(hLayout)

        return edit1, edit2

    def criarWidgetsDireita(self):
        # Adiciona títulos e campos ao layout vertical principal
        self.adicionarTitulo("Equipe de Fiscalização:", self.rightLayout)
        self.portariaEdit = self.adicionarCampo("Nº da portaria:", 'Portaria', self.rightLayout)
        self.adicionarTitulo("Posto e Nome do Gestor:", self.rightLayout)
        self.postoGestorEdit, self.gestorEdit = self.adicionarCampoDuplo('Posto_Gestor', 'Gestor', self.rightLayout, "CT (AA)", "Nome Completo")
        self.adicionarTitulo("Posto e Nome do Gestor Substituto:", self.rightLayout)
        self.postoGestorSubstitutoEdit, self.gestorSubstitutoEdit = self.adicionarCampoDuplo('Posto_Gestor_Substituto', 'Gestor_Substituto', self.rightLayout, "1ºTEN(RM2-T)", "Nome Completo")
        self.adicionarTitulo("Posto e Nome do Fiscal:", self.rightLayout)
        self.postoFiscalEdit, self.fiscalEdit = self.adicionarCampoDuplo('Posto_Fiscal', 'Fiscal', self.rightLayout, "SO-MO", "Nome Completo")
        self.adicionarTitulo("Posto e Nome do Fiscal Substituto:", self.rightLayout)
        self.postoFiscalSubstitutoEdit, self.fiscalSubstitutoEdit = self.adicionarCampoDuplo('Posto_Fiscal_Substituto', 'Fiscal_Substituto', self.rightLayout, "1ºSG-AD", "Nome Completo")


        self.rightLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def adicionarCampo(self, label, chave, layout):
        hLayout = QHBoxLayout()
        hLayout.addWidget(QLabel(label))
        edit = QLineEdit(str(self.contrato_atual.get(chave, '')))
        hLayout.addWidget(edit)
        layout.addLayout(hLayout)
        return edit

    def abrirTemplatePortaria(self):
        template_path = TEMPLATE_PORTARIA_GESTOR  # Definir o caminho do template conforme necessário
        gerador = GeradorPortaria(self.contrato_atual, template_path)
        print(self.contrato_atual)
        gerador.gerar_portaria()
        
    def criarBotoes(self):
        # Botão Salvar
        self.saveButton = QPushButton('Salvar Alterações')

        # Botão Cancelar
        self.cancelButton = QPushButton('Cancelar')

        # Criação do botão Reiniciar
        self.reiniciarButton = QPushButton('Reiniciar Status')
        self.reiniciarButton.clicked.connect(self.reiniciarStatus)  # Supondo que você tenha um método chamado reiniciarStatus para lidar com o evento de clique

        # Botão Portaria
        self.portariaButton = QPushButton('Atualizar Portaria')
        self.portariaButton.clicked.connect(self.abrirTemplatePortaria)

        # Adicionando os botões ao layout dos botões
        self.buttonsLayout.addWidget(self.saveButton)
        self.buttonsLayout.addWidget(self.cancelButton)
        self.buttonsLayout.addWidget(self.reiniciarButton)  # Adiciona o botão Reiniciar ao layout
        self.buttonsLayout.addWidget(self.portariaButton)

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
            'CP': self.lineEditCP.text().strip(),
            'MSG': self.lineEditMSG.text().strip(),
            'Portaria': self.portariaEdit.text().strip(),
            'Posto_Gestor': self.postoGestorEdit.text().strip(),
            'Gestor': self.gestorEdit.text().strip(),
            'Posto_Gestor_Substituto': self.postoGestorSubstitutoEdit.text().strip(),            
            'Gestor_Substituto': self.gestorSubstitutoEdit.text().strip(),
            'Posto_Fiscal': self.postoFiscalEdit.text().strip(),
            'Fiscal': self.fiscalEdit.text().strip(),
            'Posto_Fiscal_Substituto': self.postoFiscalSubstitutoEdit.text().strip(),
            'Fiscal_Substituto': self.fiscalSubstitutoEdit.text().strip(),
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
            
            # self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar os dados do contrato: {e}")

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super(CustomTextEdit, self).__init__(parent)
        self.setPlaceholderText("Digite seus comentários aqui...")
        self.setMinimumHeight(self.fontMetrics().lineSpacing() * 5)

        # self.setPlainText("1 - ")  # Inicia com "1 - "
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

class WorkerThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        try:
            word = comtypes.client.CreateObject('Word.Application')
            doc = word.Documents.Open(str(self.input_path))
            doc.SaveAs2(str(self.output_path), FileFormat=17)  # wdFormatPDF = 17
            doc.Close()
            word.Quit()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class GeradorPortaria:
    def __init__(self, contrato_atual, template_path, parent=None):
        self.contrato_atual = contrato_atual
        self.template_path = template_path
        self.parent = parent

    def gerar_portaria(self):
        try:
            doc = DocxTemplate(self.template_path)
            doc.render(self.contrato_atual)
            nome_arquivo_safe = f"portaria_{self.contrato_atual['Comprasnet']}.docx".replace("/", "_")
            documento_saida = self.template_path.parent / nome_arquivo_safe
            doc.save(documento_saida)
            
            output_path = documento_saida.with_suffix('.pdf')
            self.converter_para_pdf(documento_saida, output_path)
        except Exception as e:
            QMessageBox.critical(self.parent, "Erro", f"Erro ao gerar a portaria: {e}")

    def converter_para_pdf(self, input_path, output_path):
        # Mostra um QProgressDialog
        progress_dialog = QProgressDialog("Convertendo para PDF...", "Cancelar", 0, 0, self.parent)
        progress_dialog.setCancelButton(None)  # Desabilita o botão cancelar
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.show()

        # Cria e inicia a thread de trabalho
        self.thread = WorkerThread(input_path, output_path)
        self.thread.finished.connect(lambda: self.conversao_concluida(progress_dialog, output_path))
        self.thread.error.connect(lambda e: self.mostrar_erro(progress_dialog, e))
        self.thread.start()

    def conversao_concluida(self, progress_dialog, output_path):
        progress_dialog.close()
        os.startfile(output_path)  # Abre o documento PDF após a conversão

    def mostrar_erro(self, progress_dialog, error_message):
        progress_dialog.close()
        QMessageBox.critical(self.parent, "Erro na Conversão", error_message)
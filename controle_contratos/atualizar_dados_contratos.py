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
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle(f"Atualizar Dados do Contrato nº {self.contrato_atual.get('Valor Formatado', '')}")
        self.setFixedSize(800, 390)
        self.criarLayouts()
        self.criarWidgets()
        self.organizarLayouts()
        self.conectarSinais()

    def criarLayouts(self):
        self.mainLayout = QVBoxLayout()
        self.leftLayout = QVBoxLayout()
        self.centerLayout = QVBoxLayout()
        self.rightLayout = QVBoxLayout()
        self.buttonsLayout = QHBoxLayout()

    def criarWidgets(self):
        self.criarWidgetsEsquerda()
        self.criarWidgetsCentro()
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

        self.tipoContratoRadio.toggled.connect(self.atualizarNaturezaContinuada)
        self.tipoAtaRadio.toggled.connect(self.atualizarNaturezaContinuada)
        self.omComboBox.currentIndexChanged.connect(self.atualizarSetoresResponsaveis)

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

        self.centerLayout.addWidget(QLabel("Comunicação Padronizada:"))
        self.CPLineEdit = QLineEdit(str(self.contrato_atual.get('CP', '')))
        self.CPLineEdit.setPlaceholderText("Ex: 30-15/2024")
        self.centerLayout.addWidget(self.CPLineEdit)

        self.centerLayout.addWidget(QLabel("Mensagem:"))
        self.MSGLineEdit = QLineEdit(str(self.contrato_atual.get('MSG', '')))
        self.MSGLineEdit.setPlaceholderText("Ex: R-151612Z/FEV/2024")
        self.centerLayout.addWidget(self.MSGLineEdit)

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
        self.saveButton = QPushButton('Salvar')
        self.cancelButton = QPushButton('Cancelar')
        self.buttonsLayout.addWidget(self.saveButton)
        self.buttonsLayout.addWidget(self.cancelButton)

    def ajustarTamanhosLayouts(self):
        # Cria widgets contêineres para os layouts de esquerda, centro e direita
        leftContainer = QWidget()
        centerContainer = QWidget()
        rightContainer = QWidget()

        # Define um nome de objeto único para cada contêiner
        leftContainer.setObjectName("leftContainer")
        centerContainer.setObjectName("centerContainer")
        rightContainer.setObjectName("rightContainer")

        # Define os layouts para os contêineres
        leftContainer.setLayout(self.leftLayout)
        centerContainer.setLayout(self.centerLayout)
        rightContainer.setLayout(self.rightLayout)

        # Aplica a folha de estilo para adicionar bordas somente aos contêineres externos usando os nomes de objeto
        estiloBorda = """
        QWidget#leftContainer, QWidget#centerContainer, QWidget#rightContainer {
            border: 1px solid rgb(173, 173, 173);
        }
        """
        self.setStyleSheet(estiloBorda)  # Aplica a folha de estilo ao nível do diálogo ou widget pai

        # Define o tamanho preferido para os contêineres
        leftContainer.setFixedSize(250, 340)
        centerContainer.setFixedSize(250, 340)
        rightContainer.setFixedSize(250, 340)

        # Adiciona os contêineres ao layout horizontal
        self.leftCenterRightLayout.addWidget(leftContainer)
        self.leftCenterRightLayout.addWidget(centerContainer)
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

        tipo_selecionado = "Contrato" if self.tipoContratoRadio.isChecked() else "Ata"
        natureza_continuada_selecionada = "Sim" if self.naturezaContinuadaSimRadio.isChecked() else "Não"

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
            'CP': self.CPLineEdit.text().strip(),
            'MSG': self.MSGLineEdit.text().strip(),
            'Portaria': self.portariaEdit.text().strip(),
            'Gestor': self.gestorEdit.text().strip(),
            'Gestor Substituto': self.gestorSubstitutoEdit.text().strip(),
            'Fiscal': self.fiscalEdit.text().strip(),
            'Fiscal Substituto': self.fiscalSubstitutoEdit.text().strip(),
            'Tipo': tipo_selecionado,
            'Natureza Continuada': natureza_continuada_selecionada,
            'Número do instrumento': self.contrato_atual['Comprasnet']
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
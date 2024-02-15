#atualizar_dados_contratos.py

import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import pandas as pd
from datetime import datetime
from pathlib import Path
from diretorios import *

class AtualizarDadosContratos(QDialog):
    dadosContratosSalvos = pyqtSignal()
    def __init__(self, contrato_atual, table_view, parent=None):
        super().__init__(parent)
        self.camposDinamicos = {} 
        self.setWindowTitle("Atualizar Dados do Contrato")
        self.setFixedSize(600, 500)
        self.contrato_atual = contrato_atual
        self.table_view = table_view

        mainLayout = QVBoxLayout()
        leftLayout = QVBoxLayout()
        rightLayout = QVBoxLayout()

        # Início e Fim da Vigência no lado esquerdo
        self.inicioVigenciaLabel = QLabel(f"Início da Vigência: {contrato_atual.get('Vig. Início', '')}")
        self.fimVigenciaLabel = QLabel(f"Final da Vigência: {contrato_atual.get('Vig. Fim', '')}")
        leftLayout.addWidget(self.inicioVigenciaLabel)
        leftLayout.addWidget(self.fimVigenciaLabel)
        
        # Informações adicionais abaixo do Fim da Vigência
        leftLayout.addWidget(QLabel(f"Fornecedor: {contrato_atual.get('Fornecedor', '')}"))
        leftLayout.addWidget(QLabel(f"CNPJ: {contrato_atual.get('CNPJ', '')}"))
        leftLayout.addWidget(QLabel(f"Valor Global: {contrato_atual.get('Valor Global', '')}"))
        leftLayout.addWidget(QLabel(f"Número do Contrato/Ata: {contrato_atual.get('Valor Formatado', '')}"))

        # OM: [QLabel] seguido por [QComboBox] na linha abaixo
        omLabel = QLabel('OM:')
        leftLayout.addWidget(omLabel)
        self.omComboBox = QComboBox()
        try:
            tabela_uasg_df = pd.read_excel(TABELA_UASG_DIR)
            self.omComboBox.addItems(tabela_uasg_df['sigla_om'].tolist())
        except Exception as e:
            print(f"Erro ao carregar tabela UASG: {e}")
        leftLayout.addWidget(self.omComboBox)
        valor_om_atual = str(contrato_atual.get('OM', ''))
        if valor_om_atual in tabela_uasg_df['sigla_om'].values:
            index_om = tabela_uasg_df['sigla_om'].tolist().index(valor_om_atual)
            self.omComboBox.setCurrentIndex(index_om)

        # Setor Responsável: [QLabel] seguido por [QComboBox] na linha abaixo
        setorResponsavelLabel = QLabel('Setor Responsável:')
        leftLayout.addWidget(setorResponsavelLabel)
        self.setorResponsavelComboBox = QComboBox()
        leftLayout.addWidget(self.setorResponsavelComboBox)

        # Carrega os setores responsáveis baseados na seleção inicial de OM
        self.atualizarSetoresResponsaveis()
        # Após carregar os setores responsáveis no setorResponsavelComboBox
        valor_setor_atual = str(contrato_atual.get('Setor', ''))
        index_setor = self.obterIndicePorTexto(self.setorResponsavelComboBox, valor_setor_atual)
        if index_setor is not None:
            self.setorResponsavelComboBox.setCurrentIndex(index_setor)

        # Tipo: [QLabel] seguido por [QRadioButton Contrato] e [QRadioButton Ata] na linha abaixo
        tipoLabel = QLabel('Tipo:')
        leftLayout.addWidget(tipoLabel)
        tipoLayout = QHBoxLayout()
        self.tipoGroup = QButtonGroup(self)
        self.tipoContratoRadio = QRadioButton("Contrato")
        self.tipoAtaRadio = QRadioButton("Ata")
        self.tipoGroup.addButton(self.tipoContratoRadio)
        self.tipoGroup.addButton(self.tipoAtaRadio)
        tipoLayout.addWidget(self.tipoContratoRadio)
        tipoLayout.addWidget(self.tipoAtaRadio)
        leftLayout.addLayout(tipoLayout)

        # Natureza Continuada: [QLabel] seguido por [QRadioButton Sim] e [QRadioButton Não] na linha abaixo
        naturezaLabel = QLabel('Natureza Continuada:')
        leftLayout.addWidget(naturezaLabel)
        naturezaLayout = QHBoxLayout()
        self.naturezaContinuadaGroup = QButtonGroup(self)
        self.naturezaContinuadaSimRadio = QRadioButton("Sim")
        self.naturezaContinuadaNaoRadio = QRadioButton("Não")
        self.naturezaContinuadaGroup.addButton(self.naturezaContinuadaSimRadio)
        self.naturezaContinuadaGroup.addButton(self.naturezaContinuadaNaoRadio)
        naturezaLayout.addWidget(self.naturezaContinuadaSimRadio)
        naturezaLayout.addWidget(self.naturezaContinuadaNaoRadio)
        leftLayout.addLayout(naturezaLayout)

        leftLayout.setAlignment(Qt.AlignmentFlag.AlignTop) # Alinha o conteúdo do bloco da esquerda ao topo

        # Adicionando novas informações para "Processo", "NUP", e "Objeto"
        rightLayout.addWidget(QLabel("Processo:"))
        self.processoComboBox = QComboBox()
        self.processoComboBox.addItems(["PE", "DE", "TJIL", "TJDL", "ACT"])
        # Define o valor atual do processoComboBox com base no contrato_atual
        valor_processo_atual = str(contrato_atual.get('Processo', ''))
        index_processo = self.obterIndicePorTexto(self.processoComboBox, valor_processo_atual)
        if index_processo is not None:
            self.processoComboBox.setCurrentIndex(index_processo)
        
        self.processoLineEdit = QLineEdit()
        self.anoLineEdit = QLineEdit(str(datetime.now().year))
        self.anoLineEdit.setFixedWidth(50)  # Limita o tamanho do QLineEdit do ano
        processoLayout = QHBoxLayout()
        processoLayout.addWidget(self.processoComboBox)
        processoLayout.addWidget(self.processoLineEdit)
        processoLayout.addWidget(self.anoLineEdit)
        rightLayout.addLayout(processoLayout)

        rightLayout.addWidget(QLabel("NUP:"))
        self.nupLineEdit = QLineEdit(str(contrato_atual.get('NUP', '')))  # Conversão para string aqui
        self.nupLineEdit.setPlaceholderText("00000.00000/0000-00")
        rightLayout.addWidget(self.nupLineEdit)

        rightLayout.addWidget(QLabel("Objeto:"))
        self.objetoLineEdit = QLineEdit(str(contrato_atual.get('Objeto', '')))
        rightLayout.addWidget(self.objetoLineEdit)

        rightLayout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Alinha o conteúdo do bloco da direita ao topo

        # Conecta os sinais
        self.tipoContratoRadio.toggled.connect(self.atualizarNaturezaContinuada)
        self.tipoAtaRadio.toggled.connect(self.atualizarNaturezaContinuada)

        # Botões Salvar e Cancelar
        buttonsLayout = QHBoxLayout()
        self.saveButton = QPushButton('Salvar')
        self.saveButton.clicked.connect(self.salvar)
        self.cancelButton = QPushButton('Cancelar')
        self.cancelButton.clicked.connect(self.reject)
        buttonsLayout.addWidget(self.saveButton)
        buttonsLayout.addWidget(self.cancelButton)

        # Inicializa os estados dos botões de rádio
        self.tipoContratoRadio.setChecked(contrato_atual.get('Tipo', '') != 'Ata')
        self.tipoAtaRadio.setChecked(contrato_atual.get('Tipo', '') == 'Ata')
        self.naturezaContinuadaSimRadio.setChecked(contrato_atual.get('Natureza Continuada', '') == 'Sim')
        self.naturezaContinuadaNaoRadio.setChecked(contrato_atual.get('Natureza Continuada', '') != 'Sim')

        # Adicionando novas labels e QLineEdit ao layout da direita conforme necessário
        self.adicionarCamposComplementares(rightLayout)

        # Organiza os layouts
        infoLayout = QHBoxLayout()
        infoLayout.addLayout(leftLayout)
        infoLayout.addLayout(rightLayout)
        mainLayout.addLayout(infoLayout)
        mainLayout.addLayout(buttonsLayout)

        self.setLayout(mainLayout)
        self.omComboBox.currentIndexChanged.connect(self.atualizarSetoresResponsaveis)

    def obterIndicePorTexto(self, comboBox, texto):
        """
        Função auxiliar para obter o índice de um item em um QComboBox pelo texto.
        Retorna o índice se encontrar o texto, ou None caso contrário.
        """
        for index in range(comboBox.count()):
            if comboBox.itemText(index) == texto:
                return index
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
            
    def adicionarCamposComplementares(self, layout):
        campos = [("Comunicação Padronizada:", "CP"), ("Mensagem:", "MSG"), 
                ("Portaria da Equipe de Fiscalização:", "Portaria"), ("Gestor:", "Gestor"), ("Fiscal:", "Fiscal")]
        for campo, coluna in campos:
            label = QLabel(campo)
            layout.addWidget(label)
            valorInicial = f"CP nº {self.contrato_atual.get(coluna, '')}-" if campo == "Comunicação Padronizada:" else str(self.contrato_atual.get(coluna, ''))
            lineEdit = QLineEdit(valorInicial)
            layout.addWidget(lineEdit)
            self.camposDinamicos[coluna] = lineEdit  # Armazena a referência do QLineEdit no dicionário

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
            'OM': self.omComboBox.currentText().strip(),
            'Setor': self.setorResponsavelComboBox.currentText().strip(),
            'CP': self.camposDinamicos['CP'].text().replace('CP nº ', '').strip('-').strip(),
            'MSG': self.camposDinamicos['MSG'].text().strip(),
            'Portaria': self.camposDinamicos['Portaria'].text().strip(),
            'Gestor': self.camposDinamicos['Gestor'].text().strip(),
            'Fiscal': self.camposDinamicos['Fiscal'].text().strip()
        }

        self.contrato_atual.update(campos_adicionais)
        self.contrato_atual['Tipo'] = tipo_selecionado
        self.contrato_atual['Natureza Continuada'] = natureza_continuada_selecionada

        try:
            df_adicionais = pd.read_csv(ADICIONAIS_PATH, dtype='object')
            # Converte todas as colunas para object para evitar conversões automáticas
            df_adicionais = df_adicionais.astype('object')

            # Verifica e cria novas colunas se necessário
            for campo in campos_adicionais.keys():
                if campo not in df_adicionais.columns:
                    df_adicionais[campo] = pd.NA

            indice = df_adicionais.index[df_adicionais['Número do instrumento'] == self.contrato_atual['Comprasnet']].tolist()
            if indice:
                indice = indice[0]
                for campo, valor in self.contrato_atual.items():
                    df_adicionais.at[indice, campo] = str(valor)  # Converte todos os valores para string

                df_adicionais.to_csv(ADICIONAIS_PATH, index=False, encoding='utf-8')
                QMessageBox.information(self, "Sucesso", "Dados do contrato atualizados com sucesso.")
                
                self.dadosContratosSalvos.emit()
                self.accept()  # Fecha a janela após salvar com sucessou
            else:
                QMessageBox.warning(self, "Aviso", "Registro correspondente não encontrado.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar os dados do contrato: {e}")


    # def salvar(self):
    #     # Mostra 'contrato_atual' antes das alterações
    #     print("contrato_atual antes das alterações:", self.contrato_atual)

    #     # Coleta os valores dos grupos de botões de rádio
    #     tipo_selecionado = "Contrato" if self.tipoContratoRadio.isChecked() else "Ata"
    #     natureza_continuada_selecionada = "Sim" if self.naturezaContinuadaSimRadio.isChecked() else "Não"

    #     # Atualiza o dicionário 'contrato_atual' com os valores coletados
    #     self.contrato_atual['Tipo'] = tipo_selecionado
    #     self.contrato_atual['Natureza Continuada'] = natureza_continuada_selecionada
        
        # # Obtem o prefixo do processo a partir da seleção no processoComboBox
        # processo_prefixo = self.processoComboBox.currentText()
        # if processo_prefixo:
        #     # Extrai o código do processo (ex: "PE" de "Pregão Eletrônico (PE)")
        #     processo_codigo = processo_prefixo.split()[0]
            
        #     # Obtem o número do processo e o ano dos QLineEdit
        #     numero_processo = self.processoLineEdit.text().strip()
        #     ano_processo = self.anoLineEdit.text().strip()
            
        #     # Formata o valor do processo como 'Prefixo Número/Ano'
        #     valor_processo_formatado = f"{processo_codigo} {numero_processo}/{ano_processo}"
        # else:
        #     valor_processo_formatado = ""

    # #     # Prepara os campos adicionais para atualização
    #     campos_adicionais = {
    #         'Processo': valor_processo_formatado,
    #         'NUP': str(self.nupLineEdit.text()),
    #         'OM': str(self.omComboBox.currentText()),
    #         'Setor': str(self.setorResponsavelComboBox.currentText()),
    #         'CP': str(self.camposDinamicos['CP'].text().replace('CP nº ', '').strip('-')),
    #         'MSG': str(self.camposDinamicos['MSG'].text()),
    #         'Portaria': str(self.camposDinamicos['Portaria'].text()),
    #         'Gestor': str(self.camposDinamicos['Gestor'].text()),
    #         'Fiscal': str(self.camposDinamicos['Fiscal'].text())
    #     }

    #     for campo, valor in campos_adicionais.items():
    #         self.contrato_atual[campo] = valor

    #     # Mostra 'contrato_atual' após as alterações
    #     print("contrato_atual após as alterações:", self.contrato_atual)

    #     try:
    #         # Carrega o arquivo CSV existente
    #         df_adicionais = pd.read_csv(ADICIONAIS_PATH)

    #         # Encontra o índice do registro a ser atualizado
    #         indice = df_adicionais.index[df_adicionais['Número do instrumento'] == self.contrato_atual['Comprasnet']].tolist()
    #         if not indice:
    #             QMessageBox.warning(self, "Aviso", "Registro correspondente não encontrado. Atualização não realizada.")
    #             return

    #         indice = indice[0]  # Assume que 'Número do instrumento' é único, portanto usa o primeiro índice encontrado

    #         # Atualiza o DataFrame com os novos valores, incluindo 'Tipo' e 'Natureza Continuada'
    #         df_adicionais.at[indice, 'Tipo'] = tipo_selecionado
    #         df_adicionais.at[indice, 'Natureza Continuada'] = natureza_continuada_selecionada

    #             # Atualiza o DataFrame com os novos valores, incluindo tipo e natureza continuada
    #         for campo, valor in self.contrato_atual.items():
    #             df_adicionais.at[indice, campo] = str(valor)

    #         # Salva o DataFrame atualizado de volta para o arquivo CSV
    #         df_adicionais.to_csv(ADICIONAIS_PATH, index=False, sep=',', encoding='utf-8')
    #         QMessageBox.information(self, "Sucesso", "Dados atualizados com sucesso.")
    #         self.dadosContratosSalvos.emit()
    #         self.accept()  # Fecha a janela após salvar com sucesso
    #     except Exception as e:
    #         QMessageBox.critical(self, "Erro", f"Erro ao salvar dados: {e}")

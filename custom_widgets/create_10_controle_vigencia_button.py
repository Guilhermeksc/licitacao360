# create_contratos_button.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor, QBrush, QTextOption
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QDate
from diretorios import *
import pandas as pd
import re
from pathlib import Path
from datetime import datetime, timedelta
from styles.styless import get_transparent_title_style

class DetalhesContratoDialog(QDialog):
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

def calcular_prazo_limite(data_fim):
    data_fim_obj = datetime.strptime(data_fim, "%d/%m/%Y")
    prazo_limite = data_fim_obj - timedelta(days=90)

    # Ajusta para o primeiro dia útil anterior se cair em um fim de semana
    while prazo_limite.weekday() > 4:  # 5 = sábado, 6 = domingo
        prazo_limite -= timedelta(days=1)

    return prazo_limite.strftime("%d/%m/%Y")

def formatar_mensagem_contrato(numero_contrato, cnpj, nome_empresa, prazo_limite, fim_vigencia, valor_global):
    mes_atual = datetime.now().strftime("%b").upper()
    ano_atual = datetime.now().strftime("%Y")

    # Usar HTML para formatar o texto e aplicar cor às variáveis
    mensagem = (
        "ROTINA<br>"
        f"R000000Z/<span style='color: blue;'>{mes_atual}</span>/<span style='color: blue;'>{ano_atual}</span><br>"
        "DE NICITB<br>"
        "PARA SETDIS<br>"
        "GRNC<br>"
        "BT<br><br>"
        "Renovação de Contrato Administrativo<br><br>"
        f"VTD proximidade de termo final da vigência do contrato administrativo n° <span style='color: blue;'>{numero_contrato}</span>, de natureza continuada, "
        f"firmado com a empresa <span style='color: blue;'>{nome_empresa}</span>, inscrita no CNPJ: <span style='color: blue;'>{cnpj}</span>, com o valor global de <span style='color: blue;'>{valor_global}</span>, "
        "cujo objeto é xxxxxxxx, CNS PSB:<br><br>"
        "ALFA - INF intenção, ou não, de iniciar os procedimentos para a prorrogação<br>"
        "contratual;<br><br>"
        "BRAVO - Havendo interesse em prorrogar o REF contrato, PTC NEC ENC subsídios<br>"
        f"para referida renovação ao CeIMBra, até <span style='color: blue;'>{prazo_limite}</span>; e<br><br>"
        "CHARLIE - Informações adicionais:<br><br>"
        "UNO - Gestora do contrato: POSTO (ESPECIALIDADE) NOME; e<br><br>"
        f"DOIS - Término da vigência contratual: <span style='color: blue;'>{fim_vigencia}</span> BT"
    )

    return mensagem

# Ler o arquivo CSV
def ler_dados_contratos():
    if Path(CONTRATOS_PATH).exists():
        return pd.read_csv(CONTRATOS_PATH, usecols=lambda column: column not in ['Processo', 'Setor'])
    else:
        return pd.DataFrame()

def ler_dados_adicionais():
    if ADICIONAIS_PATH.exists():
        df = pd.read_csv(ADICIONAIS_PATH)

        return df
    else:
        # Incluir as novas colunas ao criar o DataFrame vazio
        return pd.DataFrame(columns=['Número do instrumento', 'Objeto', 'OM', 'Tipo', 'Natureza', 'Portaria', 'Gestor', 'Fiscal'])

def formatar_numero_instrumento(numero):
    partes = numero.split('/')
    numero_instrumento = partes[0].lstrip('0')  # Remove zeros à esquerda
    dois_ultimos_digitos = partes[1][-2:]  # Pega os dois últimos dígitos de partes[1]
    numero_formatado = f"87000/{dois_ultimos_digitos}-{numero_instrumento.zfill(3)}/00"
    return numero_formatado

def mesclar_dados_contratos():
    contratos_df = ler_dados_contratos()
    adicionais_df = ler_dados_adicionais()

    # Adicione uma coluna 'Valor Formatado' ao contratos_df antes da mesclagem
    contratos_df['Valor Formatado'] = contratos_df['Número do instrumento'].apply(formatar_numero_instrumento)

    # Use o argumento 'suffixes' em pd.merge para definir sufixos customizados se houver colunas com o mesmo nome
    dados_mesclados_df = pd.merge(contratos_df, adicionais_df, on='Número do instrumento', how='left', suffixes=('', '_adicional'))

    print("Colunas em dados_mesclados:", dados_mesclados_df.columns)  # Diagnóstico
    return dados_mesclados_df

class ContratosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        label_controle_vigencia = QLabel("Vigência de Contratos")
        label_controle_vigencia.setStyleSheet(get_transparent_title_style())
        self.layout.addWidget(label_controle_vigencia)

        # Checkbox para selecionar todos
        self.selectAllCheckbox = QCheckBox()
        self.selectAllLabel = QLabel("Selecionar Todos")
        self.selectAllLayout = QHBoxLayout()
        self.selectAllLayout.addWidget(self.selectAllLabel)
        self.selectAllLayout.addWidget(self.selectAllCheckbox)
        self.layout.addLayout(self.selectAllLayout)
        
        # Configura o QTreeView e carrega os dados
        self.tree_view = QTreeView(self)
        self.layout.addWidget(self.tree_view)
        
        self.selectAllCheckbox.stateChanged.connect(self.selectAllChanged)
        self.carregarDados()

        self.tree_view.clicked.connect(self.toggleCheckbox)

        # Layout para os botões
        self.buttons_layout = QHBoxLayout()

        # Botão "CP Alerta Prazo"
        self.alerta_prazo_btn = QPushButton("CP Alerta Prazo", self)
        self.buttons_layout.addWidget(self.alerta_prazo_btn)

        # Botão "Mensagem Cobrança"
        self.mensagem_cobranca_btn = QPushButton("Mensagem Cobrança", self)
        self.buttons_layout.addWidget(self.mensagem_cobranca_btn)

        # Botão "Gerar Termo de Subrogação"
        self.termo_subrogacao_btn = QPushButton("Termo de Subrogação", self)
        self.buttons_layout.addWidget(self.termo_subrogacao_btn)
        self.termo_subrogacao_btn.clicked.connect(self.gerarTermoSubrogacao)

        # Botão "Gerar Termo de Subrogação"
        self.termo_encerramento_btn = QPushButton("Termo de Encerramento", self)
        self.buttons_layout.addWidget(self.termo_encerramento_btn)
        self.termo_encerramento_btn.clicked.connect(self.gerarTermoEncerramento)

        # Botão "Editar Informações Adicionais"
        self.editar_adicionais_btn = QPushButton("Informações Adicionais", self)
        self.buttons_layout.addWidget(self.editar_adicionais_btn)
        self.editar_adicionais_btn.clicked.connect(self.editar_adicionais)

        # Conectar o sinal de duplo clique do QTreeView à função editar_adicionais
        self.tree_view.doubleClicked.connect(self.editar_adicionais)

        # Adiciona o layout dos botões ao layout principal
        self.layout.addLayout(self.buttons_layout)

        self.mensagem_cobranca_btn.clicked.connect(self.exibirDetalhesContrato)

        # Defina os cabeçalhos das colunas aqui para uso no modelo e na visualização
        self.colunas = ['Número do instrumento', 'Fornecedor', 'Dias p. Vencer', 'Valor Global', 'Objeto', 'OM', 'Tipo', 'Portaria', 'Gestor', 'Fiscal']
        # Defina colunas adicionais para uso interno, que não serão exibidas no QTreeView
        self.colunas_internas = ['Vig. Início', 'Vig. Fim', 'Valor Formatado']

    def toggleCheckbox(self, index):
        if not index.isValid():
            return  # Se o índice não for válido, apenas retorne
        
        model = self.tree_view.model()
        item = model.item(index.row(), 0)  # 0 é o índice da coluna dos checkboxes
        
        if item is not None and item.isCheckable():
            # Alternar o estado do checkbox
            if item.checkState() == Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                item.setCheckState(Qt.CheckState.Checked)

    def selectAllChanged(self):
        state = self.selectAllCheckbox.checkState()
        model = self.tree_view.model()
        for row in range(model.rowCount()):
            item = model.item(row, 0)  # A primeira coluna onde o checkbox está localizado
            if item:  # Verificar se o item não é None
                item.setCheckState(state)
            else:
                print(f"Item não encontrado na linha {row}, coluna 0")
            
    def gerarTermoSubrogacao(self):
        try:
            # Aqui você coloca o código para gerar o termo de subrogação
            # Pode ser a lógica que transforma os dados do CSV em um documento Word
            # Utilize a biblioteca python-docx para criar e salvar o documento
            # Por exemplo:
            # doc = Document()
            # doc.add_paragraph('Seu texto aqui')
            # doc.save('termo_subrogacao.docx')
            
            QMessageBox.information(self, "Sucesso", "Termo de Subrogação gerado com sucesso.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def gerarTermoEncerramento(self):
        try:
            # Aqui você coloca o código para gerar o termo de subrogação
            # Pode ser a lógica que transforma os dados do CSV em um documento Word
            # Utilize a biblioteca python-docx para criar e salvar o documento
            # Por exemplo:
            # doc = Document()
            # doc.add_paragraph('Seu texto aqui')
            # doc.save('termo_subrogacao.docx')
            
            QMessageBox.information(self, "Sucesso", "Termo de Encerramento gerado com sucesso.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def exibirDetalhesContrato(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            row = index.row()
            numero_contrato = self.model.item(row, self.colunas.index('Número do instrumento')).text()
            fornecedor = self.model.item(row, self.colunas.index('Fornecedor')).text()
            
            # Ajuste para extrair 'Vig. Fim' corretamente
            vig_fim_index = self.colunas.index('Vig. Fim') if 'Vig. Fim' in self.colunas else None
            vig_fim = self.model.item(row, vig_fim_index).text() if vig_fim_index is not None else ''
            
            # Ajuste para extrair 'Valor Global' corretamente
            valor_global_index = self.colunas.index('Valor Global') if 'Valor Global' in self.colunas else None
            valor_global = self.model.item(row, valor_global_index).text() if valor_global_index is not None else ''

            # Verifique se vig_fim é uma data válida antes de chamar calcular_prazo_limite
            if vig_fim:
                try:
                    prazo_limite = calcular_prazo_limite(vig_fim)
                except ValueError:
                    prazo_limite = "Data inválida"
            else:
                prazo_limite = "Data não definida"

            # Usar expressão regular para encontrar a posição do hífen após o CNPJ
            match = re.search(r'/\d{4}-\d{2}', fornecedor)
            if match:
                posicao_hifen = match.end()
                cnpj = fornecedor[:posicao_hifen].strip()
                nome_empresa = fornecedor[posicao_hifen + 1:].lstrip(" -")  # Remover hífen e espaços no início
            else:
                cnpj = nome_empresa = ""

            detalhes = formatar_mensagem_contrato(numero_contrato, cnpj, nome_empresa, prazo_limite, vig_fim, valor_global)
            dialog = DetalhesContratoDialog(detalhes, self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Seleção", "Por favor, selecione um contrato para exibir os detalhes.")

    def carregarDados(self):
        # Mescla os dados de contratos com os adicionais
        dados_mesclados = mesclar_dados_contratos()
        
        # Calcula 'Dias p. Vencer'
        dados_mesclados['Dias p. Vencer'] = dados_mesclados['Vig. Fim'].apply(self.calcular_dias_para_vencer).astype(int)

        # Valor formatado do contrato
        dados_mesclados['Valor Formatado'] = dados_mesclados['Número do instrumento'].apply(formatar_numero_instrumento)

        # Formata a coluna 'Dias p. Vencer' para ordenação, lidando corretamente com valores negativos
        def formatar_dias_p_vencer(valor):
            sinal = '-' if valor < 0 else ''
            return f"{sinal}{abs(valor):04d}"
        dados_mesclados['Dias p. Vencer'] = dados_mesclados['Dias p. Vencer'].apply(formatar_dias_p_vencer)

        # Ordena os dados por 'Dias p. Vencer'
        dados_mesclados = dados_mesclados.sort_values(by='Dias p. Vencer')

        # Cabeçalhos das colunas (sem incluir 'Vig. Início' e 'Vig. Fim' para exibição)
        self.colunas = ['Número do instrumento', 'Fornecedor', 'Dias p. Vencer', 'Valor Global', 'Processo', 'Objeto', 'OM', 'Setor', 'Tipo', 'Portaria', 'Gestor', 'Fiscal']

        # Configura o modelo personalizado com as colunas atualizadas
        self.model = CustomTableModel(dados_mesclados, self.colunas)
        self.tree_view.setModel(self.model)
        self.tree_view.setSortingEnabled(True)

        # Ajusta as larguras das colunas após o modelo estar totalmente carregado
        self.tree_view.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Definir a cor de fundo para preto
        palette = self.tree_view.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(Qt.GlobalColor.black))
        self.tree_view.setPalette(palette)

    def editar_adicionais(self, index=None):
        index = index or self.tree_view.currentIndex()
        if index.isValid():
            numero_instrumento = self.model.item(index.row(), self.colunas.index('Número do instrumento')).text()
            print("Número do instrumento selecionado:", numero_instrumento)  # Diagnóstico
       
            adicionais_df = ler_dados_adicionais()
            resultado_adicional = adicionais_df.loc[adicionais_df['Número do instrumento'] == numero_instrumento]
            
            dados_mesclados = mesclar_dados_contratos()
            linha_atual = dados_mesclados[dados_mesclados['Número do instrumento'] == numero_instrumento]
            
            # Diagnóstico: Imprimir os dataframes filtrados
            print("Dados Mesclados para o instrumento selecionado:", linha_atual)
            print("Dados Adicionais para o instrumento selecionado:", resultado_adicional)
        
            if not linha_atual.empty:
                print("Linha atual:", linha_atual)  # Diagnóstico
                vig_inicio = linha_atual.iloc[0]['Vig. Início']
                vig_fim = linha_atual.iloc[0]['Vig. Fim']
                valor_formatado = linha_atual.iloc[0]['Valor Formatado']  # Certifique-se de obter 'Valor Formatado' corretamente
            else:
                vig_inicio = ''
                vig_fim = ''
                valor_formatado = ''
            
            # Use resultado_adicional para criar registro_atual
            if not resultado_adicional.empty:
                registro_atual = resultado_adicional.iloc[0].to_dict()
                registro_atual['Vig. Início'] = vig_inicio
                registro_atual['Vig. Fim'] = vig_fim
                registro_atual['Valor Formatado'] = valor_formatado  # Inclua 'Valor Formatado' aqui
            else:
                registro_atual = {
                    'Número do instrumento': numero_instrumento,
                    'Vig. Início': vig_inicio,
                    'Vig. Fim': vig_fim,
                    'Valor Formatado': valor_formatado,
                    'OM': '', 'Tipo': '', 'Portaria': '', 'Gestor': '', 'Fiscal': ''
                }

            print("Registro Atual antes de abrir o diálogo:", registro_atual)  # Diagnóstico

            dialog = AtualizarDadosContratos(registro_atual, dados_mesclados)  # Passe dados_mesclados aqui
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                registro_atualizado = dialog.getUpdatedData()
                adicionais_df = adicionais_df[adicionais_df['Número do instrumento'] != numero_instrumento]
                adicionais_df = pd.concat([adicionais_df, pd.DataFrame([registro_atualizado])], ignore_index=True)
                adicionais_df.to_csv(ADICIONAIS_PATH, index=False)
                self.carregarDados()
            else:
                QMessageBox.warning(self, "Seleção", "Por favor, selecione um contrato para editar as informações adicionais.")

    @staticmethod
    def calcular_dias_para_vencer(data_fim):
        data_atual = QDate.currentDate()
        data_fim = QDate.fromString(data_fim, "dd/MM/yyyy")
        return data_atual.daysTo(data_fim)
    
class CustomTableModel(QStandardItemModel):
    def __init__(self, dados, colunas, parent=None):
        super(CustomTableModel, self).__init__(parent)
        self.dados = dados
        self.colunas = [col for col in colunas if col not in ['Processo', 'Setor']]
        self.setupModel()


    def setupModel(self):
        self.setHorizontalHeaderLabels([''] + self.colunas)
        for i, row in self.dados.iterrows():
            checkbox_item = QStandardItem()
            checkbox_item.setCheckable(True)
            self.setItem(i, 0, checkbox_item) 

            for j, col in enumerate(self.colunas):
                item = QStandardItem(str(row[col]))

                # Configuração de cores para a coluna 'Dias p. Vencer'
                if col == 'Dias p. Vencer':
                    num_value = int(row[col])
                    if num_value < 60:
                        item.setForeground(QColor(Qt.GlobalColor.red))
                    elif 60 <= num_value <= 180:
                        item.setForeground(QColor("orange"))
                    else:
                        item.setForeground(QColor(Qt.GlobalColor.green))
                else:
                    # Cor branca para as demais colunas
                    item.setForeground(QBrush(QColor(Qt.GlobalColor.white)))

                self.setItem(i, j + 1, item) 

class AtualizarDadosContratos(QDialog):
    def __init__(self, registro_atual, dados_mesclados, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Atualizar Dados do Contrato/Ata")
        self.registro_atual = registro_atual
        self.dados_mesclados = dados_mesclados  # Adicione uma referência aos dados mesclados
        self.setupUI()
    
    def setupUI(self):
        layout = QVBoxLayout(self)

        # Encontre os dados mesclados correspondentes ao registro atual
        numero_instrumento = self.registro_atual['Número do instrumento']
        contrato_atual = self.dados_mesclados[self.dados_mesclados['Número do instrumento'] == numero_instrumento]
        
        if contrato_atual.empty:
            # Se não houver dados correspondentes, use valores vazios
            contrato_atual = pd.DataFrame({'Vig. Início': '', 'Vig. Fim': '', 'Valor Formatado': '', 'Objeto': ''}, index=[0])
        else:
            # Se houver dados correspondentes, pegue a primeira linha
            contrato_atual = contrato_atual.iloc[0]

        # Adiciona labels para 'Vig. Início' e 'Vig. Fim'
        self.inicioVigenciaLabel = QLabel(f"Início da Vigência: {contrato_atual.get('Vig. Início', '')}")
        self.fimVigenciaLabel = QLabel(f"Final da Vigência: {contrato_atual.get('Vig. Fim', '')}")
        layout.addWidget(self.inicioVigenciaLabel)
        layout.addWidget(self.fimVigenciaLabel)

        # Adiciona campo para 'Número do Contrato/Ata' (Valor Formatado)
        self.valorFormatadoField = QLineEdit(self)
        valor_formatado = contrato_atual.get('Valor Formatado', '').iloc[0]  # Obtenha o valor correto da Series
        self.valorFormatadoField.setText(str(valor_formatado))
        layout.addWidget(QLabel('Número do Contrato/Ata:'))
        layout.addWidget(self.valorFormatadoField)

        # Adiciona campo para 'Objeto'
        self.objetoField = QLineEdit(self)
        self.objetoField.setText(str(contrato_atual.get('Objeto', '').iloc[0]))  # Obtenha o valor correto da Series
        layout.addWidget(QLabel('Objeto:'))
        layout.addWidget(self.objetoField)


        # Carregar valores para o ComboBox 'OM'
        self.omComboBox = QComboBox(self)
        tabela_uasg_df = pd.read_excel(TABELA_UASG_DIR)
        self.omComboBox.addItems(tabela_uasg_df['sigla_om'].tolist())
        self.omComboBox.setCurrentText(self.registro_atual.get('OM', 'Com7ºDN'))  # 'Com7ºDN' como padrão se não houver valor
        layout.addWidget(QLabel('OM:'))
        layout.addWidget(self.omComboBox)

        # RadioButton para 'Tipo'
        self.tipoGroup = QButtonGroup(self)
        
        self.tipoContratoRadio = QRadioButton("Contrato")
        self.tipoAtaRadio = QRadioButton("Ata")
        
        self.tipoGroup.addButton(self.tipoContratoRadio)
        self.tipoGroup.addButton(self.tipoAtaRadio)
        
        layout.addWidget(QLabel('Tipo:'))
        layout.addWidget(self.tipoContratoRadio)
        layout.addWidget(self.tipoAtaRadio)

        # Definir o estado dos botões de rádio
        if self.registro_atual.get('Tipo', '') == 'Ata':
            self.tipoAtaRadio.setChecked(True)
        else:
            # Seleciona 'Contrato' por padrão
            self.tipoContratoRadio.setChecked(True)

        # RadioButton para 'Natureza Continuada'
        self.naturezaContinuadaGroup = QButtonGroup(self)
        self.naturezaContinuadaSimRadio = QRadioButton("Sim")
        self.naturezaContinuadaNaoRadio = QRadioButton("Não")
        self.naturezaContinuadaGroup.addButton(self.naturezaContinuadaSimRadio)
        self.naturezaContinuadaGroup.addButton(self.naturezaContinuadaNaoRadio)
        layout.addWidget(QLabel('Natureza Continuada:'))
        layout.addWidget(self.naturezaContinuadaSimRadio)
        layout.addWidget(self.naturezaContinuadaNaoRadio)
        
        # Conectar sinais dos botões de rádio 'Tipo' para alterar 'Natureza Continuada'
        self.tipoContratoRadio.toggled.connect(self.atualizarNaturezaContinuada)
        self.tipoAtaRadio.toggled.connect(self.atualizarNaturezaContinuada)
        
        # Definir o estado inicial dos botões de rádio 'Natureza Continuada'
        self.atualizarNaturezaContinuada()

        self.portariaField = QLineEdit(self)
        self.portariaField.setText(str(self.registro_atual.get('Portaria', '')))
        layout.addWidget(QLabel('Portaria:'))
        layout.addWidget(self.portariaField)

        self.gestorField = QLineEdit(self)
        self.gestorField.setText(str(self.registro_atual.get('Gestor', '')))
        layout.addWidget(QLabel('Gestor:'))
        layout.addWidget(self.gestorField)

        self.fiscalField = QLineEdit(self)
        self.fiscalField.setText(str(self.registro_atual.get('Fiscal', '')))
        layout.addWidget(QLabel('Fiscal:'))
        layout.addWidget(self.fiscalField)

        # Cria botões de salvar e cancelar
        self.buttonsLayout = QHBoxLayout()
        self.saveButton = QPushButton('Salvar')
        self.saveButton.clicked.connect(self.salvar)
        self.cancelButton = QPushButton('Cancelar')
        self.cancelButton.clicked.connect(self.cancelar)
        self.buttonsLayout.addWidget(self.saveButton)
        self.buttonsLayout.addWidget(self.cancelButton)
        layout.addLayout(self.buttonsLayout)

    def atualizarNaturezaContinuada(self):
        # Se o tipo for 'Contrato', marcar 'Sim' para 'Natureza Continuada'
        # Se o tipo for 'Ata', marcar 'Não' para 'Natureza Continuada'
        if self.tipoContratoRadio.isChecked():
            self.naturezaContinuadaSimRadio.setChecked(True)
        elif self.tipoAtaRadio.isChecked():
            self.naturezaContinuadaNaoRadio.setChecked(True)

    def salvar(self):
        # Atualiza o registro_atual com os valores dos campos
        self.registro_atual['Objeto'] = self.objetoField.text()
        self.registro_atual['OM'] = self.omComboBox.currentText()
        self.registro_atual['Tipo'] = 'Contrato' if self.tipoContratoRadio.isChecked() else 'Ata'
        self.registro_atual['Natureza Continuada'] = 'Sim' if self.naturezaContinuadaSimRadio.isChecked() else 'Não'
        self.registro_atual['Portaria'] = self.portariaField.text()
        self.registro_atual['Gestor'] = self.gestorField.text()
        self.registro_atual['Fiscal'] = self.fiscalField.text()

        # Atualiza o registro_atual com o valor do campo 'Valor Formatado'
        self.registro_atual['Valor Formatado'] = self.valorFormatadoField.text()

        # Sinaliza que os dados foram salvos e fecha o diálogo
        self.accept()

    def cancelar(self):
        # Fecha o diálogo sem salvar
        self.reject()

    def getUpdatedData(self):
        # Retorna o registro atualizado
        return self.registro_atual

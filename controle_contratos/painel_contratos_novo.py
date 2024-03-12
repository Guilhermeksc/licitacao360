from PyQt6 import QtWidgets, QtGui, QtCore
from diretorios import *
from controle_contratos.atualizar_dados_contratos import AtualizarDadosContratos
from controle_contratos.utils_contratos import *
from controle_contratos.gerar_tabela import *
from controle_contratos.gerar_tabela import *
from datetime import datetime, timedelta
from num2words import num2words
from docxtpl import DocxTemplate
import comtypes.client
import os
import re

colunas_contratos = [
    'Número do instrumento', 'Fornecedor', 'Vig. Início', 'Vig. Fim', 'Valor Global']

colunas_adicionais = [    
    'Processo', 'contrato_formatado', 'Termo Aditivo', 'NUP', 'Objeto', 'cnpj_cpf', 'empresa', 'Valor Global', 'Vig. Fim', 'Dias', 
    'OM', 'Setor', 'material_servico', 'Tipo', 'Natureza Continuada', 'Comentários',           
    'Portaria', 'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto', 
    'Status0', 'Status1', 'Status2', 'Status3', 'Status4', 'Status5', 'Status6', 
    'NUP_portaria', 'ordenador_despesas', 
    'base_url', 'link_contrato_inicial', 'link_termo_aditivo', 'link_portaria', 
    'Fornecedor', 'Vig. Início', 'Número do instrumento', 'Status Icon', 'CP', 'MSG', 'fornecedor_corrigido', 'Selected'
]

colunas_gestor_fiscal = [
    'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto',]

icon_mapping = {
    'Status5': ICONS_DIR / "icon_signature.png",
    'Status4': ICONS_DIR / "icon_law_agu.png",
    'Status3': ICONS_DIR / "icon_law.png",
    'Status2': ICONS_DIR / "icon_tick.png",
    'Status1': ICONS_DIR / "icon_send.png",
    'Status0': ICONS_DIR / "icon_send.png",
    'Alert': ICONS_DIR / "icon_warning.png",
    'Warning': ICONS_DIR / "icon_alerta_amarelo.png",
    'Checked': ICONS_DIR / "checked.png"
}

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, data=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._data = data
        # Adiciona uma coluna ao DataFrame para armazenar o estado dos checkboxes
        if 'Selected' not in self._data.columns:
            self._data['Selected'] = False  # Assume que inicialmente todos não estão checados


    def rowCount(self, parent=QtCore.QModelIndex()):
        return self._data.shape[0]

    def columnCount(self, parent=QtCore.QModelIndex()):
        # Assume 2 colunas adicionais para ícones e checkboxes
        return self._data.shape[1] + 2

    def data(self, index, role=QtCore.Qt.ItemDataRole):
        if not index.isValid():
            return None

        # Tratamento especial para coluna 'Portaria' para ícones de NaN
        if index.column() == 18:
            if role == Qt.ItemDataRole.DecorationRole:
                # Verifica se o valor em 'Portaria' é NaN
                if pd.isna(self._data.iloc[index.row(), index.column() - 2]):  # Ajustando o índice para corresponder ao DataFrame
                    icon_path = icon_mapping.get('Alert')
                    if icon_path:
                        return QIcon(str(icon_path))
            elif role == Qt.ItemDataRole.DisplayRole:
                # Retorna um valor vazio para o DisplayRole quando o valor é NaN, evitando exibir o texto 'nan'
                if pd.isna(self._data.iloc[index.row(), index.column() - 2]):
                    return ""
                
        if index.column() == 1:
            if role == QtCore.Qt.ItemDataRole.CheckStateRole:
                checked = self._data.iloc[index.row(), -1]  # Assume que a última coluna contém o estado do checkbox
                return QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked

        if index.column() == 0 and role == QtCore.Qt.ItemDataRole.DecorationRole:
            status_value = self._data.iloc[index.row(), self._data.columns.get_loc('Status Icon')]
            icon_path = icon_mapping.get(status_value, None)
            if icon_path:
                # Converte Path para string para compatibilidade
                icon = QtGui.QIcon(str(icon_path))
                if icon.isNull():
                    print(f"Erro ao carregar ícone: {icon_path}")  # Ponto de diagnóstico
                else:
                    return icon
            else:
                print(f"Ícone não encontrado para status: {status_value}")  # Ponto de diagnóstico

        # Nova lógica para exibição de texto formatado na coluna 'Dias'
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            # Ajusta o índice para as colunas do DataFrame considerando as colunas adicionais à esquerda
            if index.column() >= 2:
                coluna_df = index.column() - 2  # Ajuste para corresponder ao índice correto no DataFrame
                value = self._data.iloc[index.row(), coluna_df]
                if self._data.columns[coluna_df] == "Dias":  # Se a coluna for 'Dias'
                    return "{:4}".format(value)  # Formata com espaços à esquerda
                return str(value)
            # Retorna None para as colunas de índice 0 e 1, pois são tratadas separadamente para ícones e checkboxes
            return None

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                if section >= 2:
                    return str(self._data.columns[section - 2])
                elif section == 0:
                    return ""
                elif section == 1:
                    return ""
            else:
                return str(section + 1)
        return None

    def setData(self, index, value, role):
        if index.column() == 1 and role == QtCore.Qt.ItemDataRole.CheckStateRole:
            self._data.iloc[index.row(), -1] = not self._data.iloc[index.row(), -1]  # Inverte o estado do checkbox
            self.dataChanged.emit(index, index, [role])  # Notifica a view da mudança
            return True
        return False

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 1:
            # Adiciona a flag de ItemIsUserCheckable para permitir a interação com o checkbox
            flags |= QtCore.Qt.ItemFlag.ItemIsUserCheckable
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable  # Garante que a coluna é editável
        return flags

    def sort(self, column, order):
        col_name = self._data.columns[column]
        self.sort_order = order
        if self.sort_order == Qt.SortOrder.AscendingOrder:
            self._data = self._data.sort_values(by=col_name, ascending=True)
        else:
            self._data = self._data.sort_values(by=col_name, ascending=False)
        self.layoutChanged.emit()  # Sinaliza que os dados foram alterados

class ContratosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        self.load_data()
        self.setup_model()
        self.colunas = colunas_adicionais 

    def setup_model(self):
        # Defina e configure o seu modelo aqui, por exemplo:
        self.model = QStandardItemModel(self)
        # Defina as colunas e os dados do modelo

        # Defina o proxyModel após a definição do model
        self.proxyModel = QSortFilterProxyModel(self)
        self.proxyModel.setSourceModel(self.model)
        
    def setupUI(self):
        self.layout = QVBoxLayout(self)      
        self.setupSearchField()
        self.tableView = QTableView(self)
        self.layout.addWidget(self.tableView)
        self.tableView.setItemDelegate(CellBorderDelegate(self.tableView))
        self.tableView.setStyleSheet("""
            QTableView {
                background-color: black;
                color: white;
            }
        """)
        self.tableView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        altura_fixa = 20
        self.tableView.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.tableView.verticalHeader().setDefaultSectionSize(altura_fixa)
        self.tableView.verticalHeader().hide()
        self.tableView.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.tableView.setSortingEnabled(True)
        # self.tableView.clicked.connect(self.onTableViewClicked)  # Conecta o sinal clicked
        self.tableView.pressed.connect(self.handleRowPressed)

        self.tableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.tableView.customContextMenuRequested.connect(self.onTableViewRightClick)
        QTimer.singleShot(1, self.ajustarLarguraColunas)
        self.setLayout(self.layout)

    def onTableViewRightClick(self, position):
        menu = QMenu()
        copy_cnpj_action = menu.addAction("Copiar CNPJ")
        copy_contract_num_action = menu.addAction("Copiar Nº do Contrato")
        copy_nup = menu.addAction("Copiar NUP")
        copy_cnpj_action.triggered.connect(lambda: self.copyDataToClipboard('cnpj_cpf'))
        copy_contract_num_action.triggered.connect(lambda: self.copyDataToClipboard('contrato_formatado'))
        copy_nup.triggered.connect(lambda: self.copyDataToClipboard('NUP'))
        menu.exec(self.tableView.viewport().mapToGlobal(position))

    def copyDataToClipboard(self, columnName):
        index = self.tableView.currentIndex()
        if not index.isValid():
            return
        sourceIndex = self.proxyModel.mapToSource(index)  # Use apenas o proxyModel diretamente
        if not sourceIndex.isValid():
            return
        print(f"Source row: {sourceIndex.row()}, Source column: {sourceIndex.column()}")  # Adiciona um print para o índice de origem
        # Corrija os índices das colunas para corresponder ao modelo de origem
        if columnName == 'cnpj_cpf':
            column = 5
        elif columnName == 'contrato_formatado':
            column = 1
        elif columnName == 'NUP':
            column = 3
        else:
            return
        dataIndex = self.model.index(sourceIndex.row(), column)
        print(f"Data index row: {dataIndex.row()}, Data index column: {dataIndex.column()}")  # Adiciona um print para o índice de dados
        data = self.model.data(dataIndex)
        QApplication.clipboard().setText(data)
        # Mostra um tooltip indicando que o dado foi copiado
        self.showCopyTooltip(f"{columnName} copiado: {data}")


    def showCopyTooltip(self, message):
        cursorPos = QCursor.pos()  # Obter a posição atual do cursor
        QToolTip.showText(cursorPos, message, msecShowTime=2500)  # Mostrar tooltip na posição do cursor por 1.5 segundos

    def handleRowPressed(self, index):
        if index.isValid():
            # Verifica se o clique ocorreu na coluna do checkbox
            if index.column() == 1:
                # Obtém o modelo de dados
                model = self.tableView.model()
                # Obtém o índice da célula do checkbox para a linha clicada
                checkbox_index = model.index(index.row(), 1)
                # Obtém o valor atual do checkbox
                current_state = model.data(checkbox_index, Qt.ItemDataRole.CheckStateRole)
                # Inverte o valor do checkbox
                new_state = not current_state
                # Define o novo estado do checkbox
                model.setData(checkbox_index, new_state, Qt.ItemDataRole.EditRole)
            else:
                # Se o clique não ocorreu na coluna do checkbox, então seleciona a linha
                selection_model = self.tableView.selectionModel()
                selection_model.select(index, QItemSelectionModel.SelectionFlag.Select)
            
    def ajustarLarguraColunas(self):
        for i in range(self.tableView.model().columnCount()):
            self.tableView.resizeColumnToContents(i)

    def load_data(self):
        merged_data = DataProcessor.load_data()
        model = PandasModel(merged_data)
        self.searchManager = SearchManager(model, self.searchField)
        self.tableView.setModel(self.searchManager.proxyModel)
        indices_colunas_visiveis = [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 18]

        for column in range(model.columnCount()):
            self.tableView.setColumnHidden(column, column not in indices_colunas_visiveis)

        self.tableView.setSortingEnabled(True)



    def onTableViewClicked(self, index):
        if index.isValid():
            # Obtém o modelo de dados
            model = self.tableView.model()
            # Obtém o proxy model do searchManager
            proxy_model = self.searchManager.proxyModel
            # Mapeia o índice para o modelo fonte, se estiver usando um proxy model
            source_index = proxy_model.mapToSource(index) if hasattr(model, 'mapToSource') else index
            # Obtém o índice da célula do checkbox para a linha clicada
            checkbox_index = model.index(source_index.row(), 1)  # Ajuste para a coluna correta do checkbox
            # Obtém o valor atual do checkbox
            current_state = model.data(checkbox_index, Qt.ItemDataRole.CheckStateRole)
            # Inverte o valor do checkbox
            new_state = not current_state
            # Define o novo estado do checkbox
            model.setData(checkbox_index, new_state, Qt.ItemDataRole.EditRole)
            
    def setupSearchField(self):
        self.searchField = QLineEdit(self)
        self.searchField.setPlaceholderText("Buscar por nome da empresa ou outro dado...")
        self.layout.addWidget(self.searchField)

class ControleContratosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)  # Layout principal do widget
        self.inicializarUI()

    def inicializarUI(self):
        # Instancia ContratosWidget
        self.contratos_widget = ContratosWidget(self)
        self.layout.addWidget(self.contratos_widget)

    def criar_widgets_processos(self):
        # Cria o container_frame com cor de fundo preta
        container_frame = QFrame()
        container_frame.setFrameShape(QFrame.Shape.StyledPanel)
        container_frame.setPalette(QPalette(QColor(240, 240, 240)))  

        # Define o tamanho mínimo para o container_frame
        container_frame.setMinimumSize(600, 600)

        # Cria um QGridLayout para o container_frame
        self.blocks_layout = QGridLayout(container_frame)
        self.blocks_layout.setSpacing(5)  # Define o espaçamento entre os widgets
        self.blocks_layout.setContentsMargins(5, 0, 5, 0)  # Remove as margens internas
        
        # Cria uma QScrollArea e define suas propriedades para o container_frame
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container_frame)
        
        # Adiciona a QScrollArea ao layout principal do widget
        self.layout.addWidget(scroll_area)

class CustomFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        # Obtenha o número de colunas no modelo de dados
        columnCount = self.sourceModel().columnCount()
        searchText = self.filterRegularExpression().pattern()
        regex = QRegularExpression(searchText, QRegularExpression.PatternOption.CaseInsensitiveOption)
        
        # Verifique cada coluna para uma correspondência com a expressão regular
        for column in range(columnCount):
            index = self.sourceModel().index(sourceRow, column, sourceParent)
            if index.isValid():
                data = self.sourceModel().data(index, Qt.ItemDataRole.DisplayRole)
                if regex.match(data).hasMatch():
                    return True
        return False

class SearchManager:
    def __init__(self, model, searchField):
        self.model = model  # O modelo de dados original (PandasModel)
        self.searchField = searchField
        self.proxyModel = CustomFilterProxyModel()  # Use a subclassificação personalizada aqui
        self.proxyModel.setSourceModel(self.model)
        self.searchField.textChanged.connect(self.applySearchFilter)

    def applySearchFilter(self):
        searchText = self.searchField.text()
        regExp = QRegularExpression(searchText)
        regExp.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.proxyModel.setFilterRegularExpression(regExp)

class DataProcessor:
    @staticmethod
    def determine_icon_status(dias):
        if dias < 60:
            return 'Alert'
        elif dias < 180:
            return 'Warning'
        else:
            return 'Checked'
        
    @staticmethod
    def processar_fornecedor(fornecedor):
        match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})|(\d{3}\.\d{3}\.\d{3}-\d{2})', fornecedor)
        if match:
            identificacao = match.group()
            nome_fornecedor = fornecedor[match.end():].lstrip(" -")
            return pd.Series([identificacao, nome_fornecedor], index=['CNPJ', 'Fornecedor Formatado'])
        return pd.Series(["", fornecedor], index=['CNPJ', 'Fornecedor Formatado'])

    @staticmethod
    def ler_adicionais(adicionais_path, colunas_necessarias):
        adicionais_path = Path(adicionais_path)
        if adicionais_path.exists():
            adicionais_data = pd.read_csv(adicionais_path, dtype=str)
            adicionais_data = adicionais_data.reindex(columns=colunas_necessarias, fill_value="")
        else:
            adicionais_data = pd.DataFrame(columns=colunas_necessarias)
        return adicionais_data

    @staticmethod
    def calcular_dias_para_vencer(data_fim):
        data_fim = pd.to_datetime(data_fim, format='%d/%m/%Y', errors='coerce')
        diferenca = (data_fim - pd.Timestamp.now()).days
        return diferenca

    @staticmethod
    def formatar_dias_p_vencer(valor):
        if pd.isna(valor):
            return 'N/D'  # Ou qualquer valor padrão que você considerar apropriado
        else:
            valor = int(valor)  # Converte 'valor' para int apenas se não for NaN
            sinal = '-' if valor < 0 else ''
            return f"{sinal}{abs(valor):04d}"
    
    @staticmethod
    def formatar_numero_instrumento(numero):
        if pd.isna(numero) or numero == "":
            return ""
        numero = str(numero)
        partes = numero.split('/')
        numero_instrumento = partes[0].lstrip('0')
        dois_ultimos_digitos = partes[1][-2:]
        numero_formatado = f"87000/{dois_ultimos_digitos}-{numero_instrumento.zfill(3)}/00"
        return numero_formatado
    
    @staticmethod
    def load_data():
        contratos_path = Path(CONTRATOS_PATH)  # Certifique-se de que CONTRATOS_PATH é definido anteriormente
        adicionais_path = Path(ADICIONAIS_PATH)  # Certifique-se de que ADICIONAIS_PATH é definido anteriormente

        colunas_totais = colunas_contratos + colunas_adicionais
        
        contratos_data = pd.read_csv(contratos_path, usecols=colunas_contratos, dtype=str)

        # Verifica se o arquivo de adicionais existe; se não, cria um DataFrame vazio com as colunas totais
        if adicionais_path.exists():
             adicionais_data = pd.read_csv(adicionais_path, dtype=str)
        else:
             adicionais_data = pd.DataFrame(columns=colunas_totais)

        # Realiza a mesclagem dos dados, priorizando as informações de contratos_data
        merged_data = pd.merge(adicionais_data, contratos_data, on=colunas_contratos, how='right')
        
        # Assegura que todas as colunas adicionais estejam presentes após a mesclagem, mesmo que vazias
        for coluna in colunas_adicionais:
             if coluna not in merged_data.columns:
                 merged_data[coluna] = ""

        merged_data[['cnpj_cpf', 'empresa']] = merged_data['Fornecedor'].apply(DataProcessor.processar_fornecedor)
        merged_data['contrato_formatado'] = merged_data['Número do instrumento'].apply(DataProcessor.formatar_numero_instrumento)
        # Calcula 'Dias' com base na coluna 'Vig. Fim'
        merged_data['Dias'] = merged_data['Vig. Fim'].apply(DataProcessor.calcular_dias_para_vencer).apply(DataProcessor.formatar_dias_p_vencer)
        
        # adicionais_data.rename(columns={'Vig. Fim Formatado': 'vig_fim_formatado'}, inplace=True)
        # Adicionando as novas colunas no início do DataFrame
        merged_data['Dias'] = pd.to_numeric(merged_data['Dias'], errors='coerce').fillna(180).astype(int)

        # Aplica a lógica para definir o status do ícone
        merged_data['Status Icon'] = merged_data['Dias'].apply(DataProcessor.determine_icon_status)

        # Verifica se a coluna 'Selected' já existe antes de tentar inseri-la
        if 'Selected' not in merged_data.columns:
             merged_data.insert(1, 'Selected', False)
        else:
             merged_data['Selected'] = False

        # Assegura que todas as colunas listadas estejam presentes; caso contrário, pode lançar uma exceção
        merged_data = merged_data.reindex(columns=colunas_adicionais)

        # Salvar o DataFrame atualizado, se necessário
        merged_data.to_csv(adicionais_path, index=False)

        return merged_data
    
    @staticmethod
    def calcular_prazo_limite(fim_vigencia):
        data_fim_vigencia = datetime.strptime(fim_vigencia, "%d/%m/%Y")
        prazo_limite = data_fim_vigencia - timedelta(days=90)
        # Ajusta para o primeiro dia útil anterior se cair em um fim de semana
        while prazo_limite.weekday() > 4:  # 5 = sábado, 6 = domingo
            prazo_limite -= timedelta(days=1)
        return prazo_limite.strftime("%d/%m/%Y")
    
    @staticmethod
    def numero_para_extenso(numero):
        extenso = num2words(numero, lang='pt_BR')
        if numero == 1:
            extenso = extenso.replace('um', 'uno')
        return extenso.upper()
    
    @staticmethod
    def atualizarMergedData(merged_data, novos_dados):
        # Supõe que 'novos_dados' é um DataFrame com as colunas necessárias
        # Concatena os dados, evitando duplicatas e retorna o DataFrame atualizado
        return pd.concat([merged_data, novos_dados]).drop_duplicates().reset_index(drop=True)

class CellBorderDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.column() not in [0, 1]:
            self.drawCellBorder(painter, option)

    def drawCellBorder(self, painter, option):
        painter.save()
        pen = QPen(Qt.GlobalColor.gray, 0.5, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawLine(option.rect.topLeft(), option.rect.bottomLeft())
        painter.drawLine(option.rect.topRight(), option.rect.bottomRight())
        painter.restore()
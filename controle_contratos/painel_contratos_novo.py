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
    'Status Icon', 'Selected', 
    'Processo', 'NUP', 'material_servico', 'Objeto', 'cnpj_cpf', 'empresa', 'Valor Global', 'Vig. Fim', 'Dias', 
    'OM', 'Setor', 'Tipo', 'Natureza Continuada', 'Comentários', 
    'Termo Aditivo', 'contrato_formatado', 
    'Portaria', 'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto', 
    'CP', 'MSG', 'fornecedor_corrigido', 
    'Status0', 'Status1', 'Status2', 'Status3', 'Status4', 'Status5', 'Status6', 
    'NUP_portaria', 'ordenador_despesas', 
    'base_url', 'link_contrato_inicial', 'link_termo_aditivo', 'link_portaria', 
    'Fornecedor', 'Vig. Início', 'Número do instrumento'
]

colunas_gestor_fiscal = [
    'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto',]

class PandasModel(QAbstractTableModel):
    def __init__(self, data=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._data = data
        self.sort_order = Qt.SortOrder.AscendingOrder  # Inicializa com ordenação ascendente

    def rowCount(self, parent=QModelIndex()):
        return self._data.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role == Qt.ItemDataRole.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._data.columns[section]
        return None

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

    def setupUI(self):
        self.layout = QVBoxLayout(self)      
        self.setupSearchField()
        self.tableView = QTableView(self)
        self.layout.addWidget(self.tableView)
        self.setLayout(self.layout)        

    def load_data(self):
        merged_data = DataProcessor.load_data()
        model = PandasModel(merged_data)
        self.searchManager = SearchManager(model, self.searchField)  # Instanciar o SearchManager aqui
        self.tableView.setModel(model)
        self.tableView.setSortingEnabled(True)

    def load_data(self):
        merged_data = DataProcessor.load_data()
        model = PandasModel(merged_data)

        # Configura o SearchManager com o modelo de dados
        self.searchManager = SearchManager(model, self.searchField)

        # Define o modelo proxy como o modelo da tableView
        self.tableView.setModel(self.searchManager.proxyModel)

        # Habilita a ordenação por cliques no cabeçalho na tableView
        # Note que agora a ordenação será gerenciada pelo proxyModel
        self.tableView.setSortingEnabled(True)

        # Conecta a mudança de texto no campo de busca para aplicar o filtro
        self.searchField.textChanged.connect(self.searchManager.applySearchFilter)

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
                data = self.sourceModel().data(index)
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
    icon_mapping = {
        'Alert': "icon_warning.png",
        'Warning': "icon_alerta_amarelo.png",
        'Checked': "checked.png"
    }

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

    # @staticmethod
    # def load_data():
    #     contratos_path = Path(CONTRATOS_PATH)  # Certifique-se de que CONTRATOS_PATH é definido anteriormente
    #     novos_dados_path = Path(NOVOS_DADOS_PATH)
    #     adicionais_path = Path(ADICIONAIS_PATH)
    # colunas_necessarias = [
    # 'Número do instrumento', 'Tipo', 'Processo', 'NUP', 'Objeto', 'OM', 'Setor', 'Natureza Continuada', 'Comentários', 'Termo Aditivo'
    # ]
    #     contratos_data = pd.read_csv(contratos_path, usecols=colunas_contratos, dtype=str)
    #     novos_dados = pd.read_csv(novos_dados_path, usecols=colunas_necessarias, dtype=str)
    #     atualizar_dados_novos = pd.merge(contratos_data, novos_dados, on='Número do instrumento', how='left')
    #     print(atualizar_dados_novos) 
    #     atualizar_dados_novos.to_csv(adicionais_path, index=False)
    #     return atualizar_dados_novos
    
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
        # merged_data['Dias'] = pd.to_numeric(merged_data['Dias'], errors='coerce').fillna(180).astype(int)
        merged_data['Dias'] = pd.to_numeric(merged_data['Dias'], errors='coerce').fillna(0).astype(int)

        # Aplica a lógica para definir o status do ícone
        merged_data['Status Icon'] = merged_data['Dias'].apply(DataProcessor.determine_icon_status)

        # Verifica se a coluna 'Selected' já existe antes de tentar inseri-la
        if 'Selected' not in merged_data.columns:
             merged_data.insert(1, 'Selected', False)
        else:
             merged_data['Selected'] = False

        # # Reordenando as colunas conforme solicitado
        colunas_ordenadas = [
            'Status Icon', 'Selected', 
            'Processo', 'contrato_formatado', 'Termo Aditivo', 'NUP', 'Objeto', 'cnpj_cpf', 'empresa', 'Valor Global', 'Vig. Fim', 'Dias', 
            'OM', 'Setor', 'material_servico', 'Tipo', 'Natureza Continuada', 'Comentários',           
            'Portaria', 'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto', 
            'CP', 'MSG', 'fornecedor_corrigido', 
            'Status0', 'Status1', 'Status2', 'Status3', 'Status4', 'Status5', 'Status6', 
            'NUP_portaria', 'ordenador_despesas', 
            'base_url', 'link_contrato_inicial', 'link_termo_aditivo', 'link_portaria', 
            'Fornecedor', 'Vig. Início', 'Número do instrumento'
        ]

        # Assegura que todas as colunas listadas estejam presentes; caso contrário, pode lançar uma exceção
        merged_data = merged_data.reindex(columns=colunas_ordenadas)

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
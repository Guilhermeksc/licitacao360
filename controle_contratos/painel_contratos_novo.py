from PyQt6 import QtWidgets, QtGui, QtCore
from diretorios import *
from controle_contratos.atualizar_dados_contratos import AtualizarDadosContratos
from controle_contratos.utils_contratos import *
from controle_contratos.gerar_tabela import *
from controle_contratos.gerar_tabela import *
from controle_contratos.dataprocessor import DataProcessor
from datetime import datetime, timedelta
from num2words import num2words
from docxtpl import DocxTemplate
import comtypes.client
import os
import re

colunas_contratos = [
    'Número do instrumento', 'Fornecedor', 'Vig. Início', 'Vig. Fim', 'Valor Global']

colunas_adicionais = [
    'Dias', 'Objeto', 'OM', 'Setor', 'Tipo', 'contrato_formatado', 'Natureza Continuada', 
    'Portaria', 'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto', 
    'Processo', 'NUP',  'CP', 'MSG', 'cnpj_cpf', 'empresa', 'fornecedor_corrigido', 'Termo Aditivo', 
    'Status0', 'Status1', 'Status2', 'Status3', 'Status4', 'Status5', 'Status6',
    'material_servico', 'NUP_portaria', 'ordenador_despesas', 
    'link_contrato_inicial', 'link_termo_aditivo', 'link_portaria', 'Comentários']

colunas_gestor_fiscal = [
    'Posto_Gestor', 'Gestor', 'Posto_Gestor_Substituto', 'Gestor_Substituto', 'Posto_Fiscal', 'Fiscal', 'Posto_Fiscal_Substituto', 'Fiscal_Substituto',]

class PandasModel(QAbstractTableModel):
    def __init__(self, data=pd.DataFrame(), parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return self._data.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._data.columns[section]
        return None

class ContratosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        self.load_data()

    def setupUI(self):
        self.layout = QVBoxLayout(self)
        self.tableView = QTableView(self)
        self.layout.addWidget(self.tableView)
        self.setLayout(self.layout)

    def load_data(self):
        merged_data = DataProcessor.load_data()
        model = PandasModel(merged_data)
        self.tableView.setModel(model)
    
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

class DataProcessor:
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

        # Salva o DataFrame atualizado no caminho de ADICIONAIS_PATH
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
    

        # contratos_data[['cnpj_cpf', 'empresa']] = contratos_data['Fornecedor'].apply(DataProcessor.processar_fornecedor)
        # contratos_data['contrato_formatado'] = contratos_data['Número do instrumento'].apply(DataProcessor.formatar_numero_instrumento)
        # # Calcula 'Dias' com base na coluna 'Vig. Fim'
        # adicionais_data_enriquecido['Dias'] = adicionais_data_enriquecido['Vig. Fim'].apply(DataProcessor.calcular_dias_para_vencer).apply(DataProcessor.formatar_dias_p_vencer)
        
        # adicionais_data.rename(columns={'Vig. Fim Formatado': 'vig_fim_formatado'}, inplace=True)
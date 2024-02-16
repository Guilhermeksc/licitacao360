#utils_contratos.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import numpy as np
import pandas as pd
import re
from diretorios import *
from datetime import datetime

class ConfiguracoesDialog(QDialog):
    COLUMN_OFFSET = 2
    SETTINGS_KEY = "ConfiguracoesDialog/ColumnVisibility"

    def __init__(self, colunas, tree_view, parent=None):
        super().__init__(parent)
        self.tree_view = tree_view
        self.colunas = colunas
        self.setWindowTitle("Configurações de Colunas")
        self.layout = QVBoxLayout(self)

        self.initUI()  # Inicializa a interface do usuário
        self.load_settings()  # Carrega as configurações salvas

    def initUI(self):
        """Inicializa os componentes da interface do usuário."""
        # Botões para configurações pré-definidas
        self.initPredefinedConfigButtons()

        # QListWidget para seleção personalizada das colunas
        self.initListWidget()

        # Botão de aplicar configurações personalizadas
        self.btn_apply_custom = QPushButton("Aplicar Configuração Personalizada", self)
        self.btn_apply_custom.clicked.connect(self.apply_custom_config)
        self.layout.addWidget(self.btn_apply_custom)

    def initPredefinedConfigButtons(self):
        """Inicializa os botões para as configurações pré-definidas."""
        self.btn_modulo_gestor_fiscal = QPushButton("Módulo Gestor/Fiscal", self)
        self.btn_modulo_gestor_fiscal.clicked.connect(self.apply_gestor_fiscal_config)
        self.layout.addWidget(self.btn_modulo_gestor_fiscal)

        self.btn_modulo_renovacao_contratos = QPushButton("Módulo Renovação de Contratos", self)
        self.btn_modulo_renovacao_contratos.clicked.connect(self.apply_renovacao_contratos_config)
        self.layout.addWidget(self.btn_modulo_renovacao_contratos)

        self.btn_show_all_columns = QPushButton("Mostrar todas as colunas", self)
        self.btn_show_all_columns.clicked.connect(self.show_all_columns)
        self.layout.addWidget(self.btn_show_all_columns)

    def initListWidget(self):
        """Inicializa o QListWidget para seleção personalizada das colunas."""
        self.list_widget = QListWidget(self)
        self.populate_list_widget(self.colunas, self.tree_view)
        self.layout.addWidget(self.list_widget)

    def apply_gestor_fiscal_config(self):
        indices = [1, 2, 3, 5, 6, 7, 8, 9, 14, 15, 16, 17, 18]
        self.apply_column_visibility(indices)
        self.save_settings(indices)

    def apply_renovacao_contratos_config(self):
        indices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.apply_column_visibility(indices)
        self.save_settings(indices)

    def apply_column_visibility(self, visible_indices):
        for i in range(self.tree_view.model().columnCount()):
            self.tree_view.setColumnHidden(i, i + self.COLUMN_OFFSET not in visible_indices)

    def apply_custom_config(self):
        """Aplica a configuração personalizada selecionada pelo usuário."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            is_visible = item.checkState() == Qt.CheckState.Checked
            column_index = item.data(Qt.ItemDataRole.UserRole)
            self.tree_view.setColumnHidden(column_index, not is_visible)
        # Não esqueça de salvar a configuração personalizada após aplicá-la
        self.save_custom_config()

    def save_custom_config(self):
        """Salva as configurações personalizadas do usuário."""
        selected_indices = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                column_index = item.data(Qt.ItemDataRole.UserRole)
                selected_indices.append(column_index - self.COLUMN_OFFSET)  # Ajuste conforme necessário
        # Salva os índices das colunas visíveis como configuração personalizada
        settings = QSettings()
        settings.setValue(self.SETTINGS_KEY, selected_indices)

    def save_settings(self, visible_indices):
        settings = QSettings()
        settings.setValue(self.SETTINGS_KEY, visible_indices)

    def load_settings(self):
        settings = QSettings()
        if settings.contains(self.SETTINGS_KEY):
            visible_indices = settings.value(self.SETTINGS_KEY, type=list)
            self.apply_column_visibility(visible_indices)
        else:
            self.apply_column_visibility(range(len(self.colunas)))  # Mostra todas as colunas por padrão

    def show_all_columns(self):
        # Atualiza todos os itens na lista para o estado marcado (Checked)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.CheckState.Checked)
        
        # Atualiza a visibilidade de todas as colunas para visível
        for i in range(self.tree_view.model().columnCount()):
            self.tree_view.setColumnHidden(i + self.COLUMN_OFFSET, False)
        
        # Salva a configuração de todas as colunas visíveis
        self.save_settings(list(range(len(self.colunas))))

    def populate_list_widget(self, colunas, tree_view):
        for index, coluna in enumerate(colunas):
            item = QListWidgetItem(coluna)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if not tree_view.isColumnHidden(index + self.COLUMN_OFFSET) else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, index + self.COLUMN_OFFSET)
            self.list_widget.addItem(item)

    def aplicarConfiguracoes(self):
        selected_indices = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            column_index = item.data(Qt.ItemDataRole.UserRole)
            is_checked = item.checkState() == Qt.CheckState.Checked
            self.tree_view.setColumnHidden(column_index - self.COLUMN_OFFSET, not is_checked)
            if is_checked:
                selected_indices.append(column_index - self.COLUMN_OFFSET)
        self.save_settings(selected_indices)
        self.accept()

class CellBorderDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        
        # Não desenha bordas para as colunas de índice 0 e 1
        if index.column() not in [0, 1]:
            painter.save()
            
            # Configura a cor e o estilo da borda
            pen = QPen(Qt.GlobalColor.gray, 0.5, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            
            # Coordenadas para as bordas laterais
            left_line_start = option.rect.topLeft()
            left_line_end = option.rect.bottomLeft()
            right_line_start = option.rect.topRight()
            right_line_end = option.rect.bottomRight()
            
            # Desenha linhas apenas nas laterais (direita e esquerda) da célula
            painter.drawLine(left_line_start, left_line_end)
            painter.drawLine(right_line_start, right_line_end)
            
            painter.restore()

class MultiColumnFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, dados, parent=None):
        super().__init__(parent)
        self.merged_data = dados

    def filterAcceptsRow(self, sourceRow, sourceParent):
        # Obtenha o número total de colunas no modelo de dados
        columnCount = self.sourceModel().columnCount(sourceParent)
        
        # Verifique cada coluna para a correspondência do texto de busca
        for column in range(columnCount):
            # Obtenha o índice do item na linha e coluna atual
            index = self.sourceModel().index(sourceRow, column, sourceParent)
            # Obtenha o valor do item
            data = self.sourceModel().data(index)
            
            # Compare o valor do item com a expressão regular de filtro
            if self.filterRegularExpression().match(data).hasMatch():
                return True  # Aceita a linha se qualquer coluna corresponder
        
        return False  # Rejeita a linha se nenhuma coluna corresponder
    
    def getDataFrame(self):
        return self.merged_data
    
def getFilteredData(model):
    # Lista para armazenar os dados filtrados
    filteredData = []
    
    # Obter o número de linhas no modelo de proxy
    rowCount = model.rowCount()
    
    # Iterar sobre cada linha para extrair os dados
    for row in range(rowCount):
        rowData = []
        for column in range(model.columnCount()):
            index = model.index(row, column)
            # Obter dados da célula do modelo de proxy
            data = model.data(index)
            rowData.append(data)
        filteredData.append(rowData)
    
    return filteredData

def saveFilteredDataToExcel(filteredData, columns, filePath='filtered_data.xlsx'):
    # Criar um DataFrame com os dados filtrados
    df = pd.DataFrame(filteredData, columns=columns)
    
    # Salvar o DataFrame como um arquivo Excel
    df.to_excel(filePath, index=False)

class CheckableItem(QStandardItem):
    def __init__(self, text="", checkState=Qt.CheckState.Unchecked):
        super().__init__(text)
        self.setCheckable(True)
        self.setCheckState(checkState)
        self.setEditable(False)

class CustomTableModel(QStandardItemModel):
    def __init__(self, dados, colunas, icons_dir, parent=None):
        super().__init__(parent)
        self.merged_data = dados
        self.icons_dir = icons_dir
        self.colunas = colunas
        self.setupModel()

    def setupModel(self):
        self.setHorizontalHeaderLabels(['', ''] + self.colunas)

        for i, row in self.merged_data.iterrows():
            # Criação ou atualização dos CheckableItems aqui
            checkbox_item = CheckableItem()
            checkbox_item.setCheckable(True)
            checkbox_item.setEditable(False)
            
            # Define o estado do checkbox baseado na coluna "Selecionado"
            check_state = Qt.CheckState.Checked if row['Selecionado'] else Qt.CheckState.Unchecked
            checkbox_item.setCheckState(check_state)
            
            self.setItem(i, 1, checkbox_item)
            try:
                dias_value = int(row.get('Dias', 180))
            except ValueError:
                dias_value = 180
            
            if dias_value < 180:
                icon_path = self.icons_dir / "unchecked.png"
                icon_item = QStandardItem(QIcon(str(icon_path)), "")
                self.setItem(i, 0, icon_item)
            else:
                status_item = QStandardItem(" ")
                self.setItem(i, 0, status_item)

            for j, col in enumerate(self.colunas, start=2):
                if col == "Comprasnet":
                    item_value = str(row["Número do instrumento"])
                elif col in ['Valor Formatado', 'Portaria', 'Gestor', 'Fiscal']:
                    item_value = str(row[col]) if col in row and pd.notnull(row[col]) else ""
                else:
                    item_value = str(row[col]) if pd.notnull(row[col]) else ""
                
                # Para as demais colunas, continuamos a usar QStandardItem
                item = QStandardItem(item_value)
                item.setEditable(False)
                self.setItem(i, j, item)

                # Sua lógica para colorir os itens baseados em 'Dias'
                if col == 'Dias':
                    num_value = int(row[col])
                    if num_value < 60:
                        item.setForeground(QColor(Qt.GlobalColor.red))
                    elif 60 <= num_value <= 180:
                        item.setForeground(QColor("orange"))
                    else:
                        item.setForeground(QColor(Qt.GlobalColor.green))
                else:
                    item.setForeground(QBrush(QColor(Qt.GlobalColor.white)))

    def getRowDataAsDict(self, row):
        """Retorna os dados da linha especificada como um dicionário."""
        return self.merged_data.iloc[row].to_dict()
    
    def getDataFrame(self):
        return self.merged_data()
    
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 1:
            item = self.itemFromIndex(index)
            if item is not None:
                # Certifique-se de que o valor é do tipo Qt.CheckState
                if isinstance(value, Qt.CheckState):
                    item.setCheckState(value)
                elif isinstance(value, int):  # Se por acaso um int for passado, converta corretamente
                    value = Qt.CheckState.Checked if value == 2 else Qt.CheckState.Unchecked
                    item.setCheckState(value)
                self.dataChanged.emit(index, index, [role])
                return True
        return False

colunas_contratos = [
    'Número do instrumento', 'Fornecedor', 'Vig. Início', 'Vig. Fim', 'Valor Global']

colunas_adicionais = [
    'Número do instrumento', 'Objeto', 'OM', 'Tipo', 'Portaria', 'Gestor', 'Gestor Substituto',
    'Fiscal', 'Fiscal Substituto', 'Vig. Fim Formatado', 'Valor Formatado', 'Natureza Continuada', 
    'Processo', 'NUP', 'Setor', 'CP', 'MSG', 'CNPJ', 'Fornecedor Formatado', 'Dias']

def processar_fornecedor(fornecedor):
    match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})|(\d{3}\.\d{3}\.\d{3}-\d{2})', fornecedor)
    if match:
        identificacao = match.group()
        nome_fornecedor = fornecedor[match.end():].lstrip(" -")
        return pd.Series([identificacao, nome_fornecedor], index=['CNPJ', 'Fornecedor Formatado'])
    return pd.Series(["", fornecedor], index=['CNPJ', 'Fornecedor Formatado'])

# Função para tratar a leitura de adicionais_path
def ler_adicionais(adicionais_path, colunas_necessarias):
    if Path(adicionais_path).exists():
        adicionais_data = pd.read_csv(adicionais_path, dtype=str)
        adicionais_data = adicionais_data.astype(str)  # Assegura tipo object para todas as colunas
        adicionais_data = adicionais_data.reindex(columns=colunas_necessarias, fill_value="")
    else:
        adicionais_data = pd.DataFrame(columns=colunas_necessarias).astype(str)
    return adicionais_data

# Função para calcular o valor de dias
def calcular_dias(vig_fim):
    hoje = pd.to_datetime('today')
    vig_fim = pd.to_datetime(vig_fim, errors='coerce', dayfirst=True)
    return (vig_fim - hoje).days if vig_fim else np.nan

def calcular_dias_para_vencer(data_fim):
    # Converte a string para datetime no formato esperado
    data_fim = pd.to_datetime(data_fim, format='%d/%m/%Y', errors='coerce')
    # Calcula a diferença em dias diretamente, sem usar .dt.days em um Timedelta
    diferenca = (data_fim - pd.Timestamp.now()).days
    return diferenca

def formatar_dias_p_vencer(valor):
    sinal = '-' if valor < 0 else ''
    return f"{sinal}{abs(valor):04d}"

def formatar_numero_instrumento(numero):
    if pd.isna(numero) or numero == "":
        return ""
    numero = str(numero)
    partes = numero.split('/')
    numero_instrumento = partes[0].lstrip('0')  # Remove zeros à esquerda
    dois_ultimos_digitos = partes[1][-2:]  # Pega os dois últimos dígitos de partes[1]
    numero_formatado = f"87000/{dois_ultimos_digitos}-{numero_instrumento.zfill(3)}/00"
    return numero_formatado

def load_data(contratos_path, adicionais_path, colunas_contratos, colunas_adicionais):

    contratos_data = pd.read_csv(contratos_path, dtype=str)
    print("Contratos data:")
    print(contratos_data.dtypes)
    print(contratos_data.columns)
    
    # Carrega os dados adicionais
    adicionais_data = ler_adicionais(adicionais_path, colunas_adicionais)
    print("Adicionais data inicial:")
    print(adicionais_data.dtypes)

    print("adicionais_data.columns:")
    print(adicionais_data.columns)

    # Aplicação da função processar_fornecedor para cada entrada na coluna 'Fornecedor'
    resultado_processamento = contratos_data['Fornecedor'].apply(processar_fornecedor).apply(pd.Series)
    resultado_processamento.rename(columns={0: 'CNPJ', 1: 'Fornecedor Formatado'}, inplace=True)
    contratos_data = pd.concat([contratos_data, resultado_processamento], axis=1)

    # Mesclando contratos_data com adicionais_data
    merged_data = pd.merge(contratos_data, adicionais_data, on='Número do instrumento', how='left')

    # Removendo potenciais colunas duplicadas após o merge
    colunas_para_manter = ['CNPJ_x', 'Fornecedor Formatado_x']
    colunas_renomeadas = {coluna: coluna.rstrip('_x') for coluna in colunas_para_manter}
    merged_data.rename(columns=colunas_renomeadas, inplace=True)

    # Selecionando colunas específicas para o resultado final, removendo colunas duplicadas
    colunas_merged_final = colunas_contratos + [coluna for coluna in colunas_adicionais if coluna != 'Número do instrumento']
    merged_data = merged_data[[coluna for coluna in colunas_merged_final if coluna in merged_data.columns]]

    # Atualizando a coluna 'Dias'
    if 'Vig. Fim' in merged_data.columns:
        merged_data['Dias'] = merged_data['Vig. Fim'].apply(calcular_dias_para_vencer).apply(formatar_dias_p_vencer)
      
    # Salvamento dos dados adicionais atualizados, se necessário
    adicionais_data.to_csv(adicionais_path, index=False)

    # Adicionando a coluna "Selecionado" com valor padrão False
    merged_data['Selecionado'] = False

    return merged_data

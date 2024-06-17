from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import sqlite3
from diretorios import DATABASE_DIR, ICONS_DIR
from pathlib import Path
import os
import sys
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

CONTROLE_LIMITE_DISPENSA_DIR = DATABASE_DIR / "controle_limite_dispensa"

class LimiteDispensa(QWidget):
    def __init__(self, icon_dir=None, parent=None):
        super().__init__(parent)
        self.icon_dir = icon_dir
        self.setup_ui()
        # Define um arquivo SQLite padrão para carregar inicialmente no QTreeView
        # Exemplo: '/caminho/para/seu/arquivo/dados_pdm.db'
        arquivo_padrao_db = CONTROLE_LIMITE_DISPENSA_DIR / 'dados_pdm.db'
        
        # Verifica se o arquivo padrão existe antes de tentar carregá-lo
        if arquivo_padrao_db.exists():
            self.update_tree_view(arquivo_padrao_db)
        else:
            print(f"Arquivo padrão não encontrado: {arquivo_padrao_db}")

    def setup_ui(self):
        # Cria o layout principal que organiza tudo verticalmente
        self.main_layout = QVBoxLayout(self)

        # Cria e configura a QLabel e o QComboBox
        self.label_om = QLabel("Escolher OM:")
      
        # Configura a QLabel com cor branca, texto em negrito e tamanho de fonte 16
        self.label_om.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        # Adiciona a QLabel e o QComboBox ao layout
        self.main_layout.addWidget(self.label_om)

        # Botões superiores
        top_buttons_layout = QHBoxLayout()
        self.combo_box_om = QComboBox()
        top_buttons_layout.addWidget(self.combo_box_om)
        # self.btn_pdm = QPushButton("PDM")
        # self.btn_catser = QPushButton("CATSER")
        # top_buttons_layout.addWidget(self.btn_pdm)
        # top_buttons_layout.addWidget(self.btn_catser)
        self.btn_generate_report = QPushButton("Gerar Relatório")
        self.btn_generate_report.clicked.connect(self.generate_report)
        top_buttons_layout.addWidget(self.btn_generate_report)

        # Botões SQLite
        # bottom_sqlite_layout = QHBoxLayout()
        self.btn_sqlite_pdm = QPushButton("SQLITE PDM")
        self.btn_sqlite_pdm.clicked.connect(self.on_import_sqlite_pdm_clicked)
        # self.btn_sqlite_catser = QPushButton("SQLITE CATSER")
        top_buttons_layout.addWidget(self.btn_sqlite_pdm)
        # bottom_sqlite_layout.addWidget(self.btn_sqlite_catser)

        # Botões de importação
        # bottom_buttons_layout = QHBoxLayout()
        self.btn_import_pdm = QPushButton("Importar dados PDM")
        self.btn_import_pdm.clicked.connect(self.on_import_pdm_clicked)
        # self.btn_import_catser = QPushButton("Importar dados CATSER")
        top_buttons_layout.addWidget(self.btn_import_pdm)
        # bottom_buttons_layout.addWidget(self.btn_import_catser)

        # Adiciona todos os layouts ao layout principal
        self.main_layout.addLayout(top_buttons_layout)
        # self.main_layout.addLayout(bottom_sqlite_layout)
        # self.main_layout.addLayout(bottom_buttons_layout)

        # Configuração do QTreeView
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.main_layout.addWidget(self.tree_view)
        self.tree_view.setStyleSheet(f"""
            QTreeView {{
                background-color: black;
                color: white;
            }}
        """)


        self.tree_view.setItemDelegate(ColorDelegate())
        self.populate_combobox()

    def generate_report(self):
        # Lista para armazenar dados das linhas
        report_data = []
        headers = [self.model.headerData(i, Qt.Orientation.Horizontal) for i in range(self.model.columnCount())]
        report_data.append(headers)
        
        # Percorre cada linha do modelo
        for row in range(self.model.rowCount()):
            total_empenhado_item = self.model.item(row, 7)  # Acessa a coluna 'Total Empenhado'
            if total_empenhado_item is not None:
                valor = convert_currency_to_float(total_empenhado_item.text())
                if valor > 0:
                    # Coleta os dados da linha se 'Total Empenhado' > R$ 0,00
                    line_data = [self.model.item(row, column).text() for column in range(self.model.columnCount())]
                    report_data.append(line_data)
            
        # Criação do DataFrame principal
        df_report = pd.DataFrame(report_data[1:], columns=report_data[0])
        
        # Conversão da coluna 'Total Empenhado' para valores numéricos
        df_report['Total Empenhado'] = df_report['Total Empenhado'].apply(lambda x: convert_currency_to_float(x))

        # Sumário por grupo
        df_group_summary = df_report.groupby(['Grupo', 'Descrição Grupo'])['Total Empenhado'].sum().reset_index()
        df_group_summary['Total Empenhado'] = df_group_summary['Total Empenhado'].apply(lambda x: f'R$ {x:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Criação do DataFrame de sumário por classe
        df_class_summary = df_report.groupby(['Grupo', 'Descrição Grupo', 'Classe', 'Descrição Classe'])['Total Empenhado'].sum().reset_index()
        df_class_summary['Total Empenhado'] = df_class_summary['Total Empenhado'].apply(lambda x: f'R$ {x:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))

        # Adiciona linhas com o valor total ao df_report e df_group_summary
        total_report_value = df_report['Total Empenhado'].sum()
        total_report_value_formatted = f'R$ {total_report_value:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
        total_report_row_df = pd.DataFrame([{'Grupo': 'Valor Total no Relatório:', 'Descrição Grupo': '', 'Classe': '', 'Descrição Classe': '', 'Total Empenhado': total_report_value_formatted}])
        df_report = pd.concat([df_report, total_report_row_df], ignore_index=True)

        total_group_value = df_group_summary['Total Empenhado'].apply(lambda x: convert_currency_to_float(x)).sum()
        total_group_value_formatted = f'R$ {total_group_value:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
        total_group_row_df = pd.DataFrame([{'Grupo': 'Valor Total nos Grupos:', 'Descrição Grupo': '', 'Total Empenhado': total_group_value_formatted}])
        df_group_summary = pd.concat([df_group_summary, total_group_row_df], ignore_index=True)

        # Calcula o valor total de 'Total Empenhado' para todas as classes e adiciona ao df_class_summary
        total_value = df_class_summary['Total Empenhado'].apply(lambda x: convert_currency_to_float(x)).sum()
        total_value_formatted = f'R$ {total_value:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
        total_row_df = pd.DataFrame([{'Grupo': 'Valor Total:', 'Descrição Grupo': '', 'Classe': '', 'Descrição Classe': '', 'Total Empenhado': total_value_formatted}])
        df_class_summary = pd.concat([df_class_summary, total_row_df], ignore_index=True)

        # Caminho para salvar o arquivo Excel
        report_path = Path.home() / "relatorio_total_empenhado.xlsx"

        # Uso de ExcelWriter com o motor 'openpyxl' para escrever múltiplas abas
        with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
            df_report.to_excel(writer, sheet_name='Relatório', index=False)
            df_group_summary.to_excel(writer, sheet_name='Grupo', index=False)
            df_class_summary.to_excel(writer, sheet_name='Classe', index=False)

            # Obtém o objeto workbook do writer
            workbook = writer.book

            # Ajusta as larguras das colunas para a aba "Relatório"
            widths_relatorio = [8, 40, 8, 40, 8, 40, 20, 20]
            adjust_report_column_widths(workbook['Relatório'], widths_relatorio)

            # Ajusta as larguras das colunas para a aba "Grupo"
            widths_grupo = [8, 40, 20]
            adjust_report_column_widths(workbook['Grupo'], widths_grupo)

            # Ajusta as larguras das colunas para a aba "Classe"
            widths_classe = [8, 40, 8, 40, 20]
            adjust_report_column_widths(workbook['Classe'], widths_classe)

        # Informa ao usuário sobre a geração do relatório
        QMessageBox.information(self, "Relatório Gerado", f"Relatório gerado com sucesso!\nLocalização: {report_path}")

        # Abre o arquivo Excel gerado
        try:
            os.startfile(report_path)  # Funciona apenas no Windows
        except AttributeError:
            # Alternativa para MacOS e Linux
            os.system(f'open "{report_path}"') if sys.platform == "darwin" else os.system(f'xdg-open "{report_path}"')

    def showEvent(self, event):
        super().showEvent(event)
        # Definindo o tamanho das colunas após o widget ser exibido
        column_widths = [50, 200, 50, 220, 50, 350, 100, 100]  # Ajuste os valores conforme necessário
        for i, width in enumerate(column_widths):
            self.tree_view.setColumnWidth(i, width)

    def populate_combobox(self):
        self.RELATORIO_POR_OM_DIR = CONTROLE_LIMITE_DISPENSA_DIR / "relatorio_por_om"
        
        if not self.RELATORIO_POR_OM_DIR.exists():
            print(f"O diretório {self.RELATORIO_POR_OM_DIR} não existe.")
            return
        
        self.om_to_file_map = {}  # Dicionário para mapear a OM para o caminho do arquivo
        
        for file_path in self.RELATORIO_POR_OM_DIR.glob('*.xlsx'):
            df = pd.read_excel(file_path, header=None, nrows=2, usecols=[0])
            if df.shape[0] > 1:
                valor = df.iat[1, 0]
                self.combo_box_om.addItem(valor)
                self.om_to_file_map[valor] = file_path  # Armazena o caminho do arquivo
                
        self.combo_box_om.currentIndexChanged.connect(self.on_om_selected)  # Conecta a seleção a uma função

    def on_om_selected(self, index):
        selected_om = self.combo_box_om.itemText(index)
        selected_file_path = self.om_to_file_map[selected_om]
        
        # Mostrar MessageBox informando a mudança
        QMessageBox.information(self, "Seleção de OM", f"OM {selected_om} selecionada. Carregando dados...")

        # Carrega os dados do arquivo XLSX selecionado e atualiza o QTreeView
        self.update_tree_view_with_xlsx_data(selected_file_path)
        self.ordenar_itens_modelo()
        self.adjust_column_widths()   # Ajusta o tamanho das colunas

    def adjust_column_widths(self):
        # Define o tamanho das colunas
        column_widths = [50, 200, 50, 220, 50, 350, 100, 100]
        for i, width in enumerate(column_widths):
            self.tree_view.setColumnWidth(i, width)

    def update_tree_view_with_xlsx_data(self, xlsx_path):
        df_xlsx = pd.read_excel(xlsx_path, usecols=["Código PDM", "Valor Empenhado"], skiprows=2)
        df_xlsx['Código PDM'] = df_xlsx['Código PDM'].apply(lambda x: str(x).rstrip('.0'))
        pdm_to_valor = {row["Código PDM"]: convert_currency_to_float(row["Valor Empenhado"]) for _, row in df_xlsx.iterrows()}
        print("Dados carregados do XLSX:", pdm_to_valor)

        limite_disponivel_base = 59906.02  # Valor base para 'Limite Disponível'

        for row in range(self.model.rowCount()):
            pdm_item = self.model.item(row, 4)  # Assumindo que 'PDM' é a 5ª coluna
            if pdm_item and pdm_item.text() in pdm_to_valor:
                valor_empenhado = pdm_to_valor[pdm_item.text()]
                # Atualiza a coluna 'Total Empenhado' com o valor do XLSX
                total_empenhado_item = self.model.item(row, 7) or QStandardItem()  # Coluna 'Total Empenhado'
                total_empenhado_item.setText(f"R$ {valor_empenhado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                self.model.setItem(row, 7, total_empenhado_item)

                # Calcula o novo valor para 'Limite Disponível'
                novo_limite = limite_disponivel_base - valor_empenhado
                # Verifica se o novo limite é menor que 0 para ajustar a exibição
                limite_display = max(novo_limite, 0)
                # Atualiza a coluna 'Limite Disponível'
                limite_disponivel_item = self.model.item(row, 6) or QStandardItem()  # Coluna 'Limite Disponível'
                limite_disponivel_item.setText(f"R$ {limite_display:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                self.model.setItem(row, 6, limite_disponivel_item)

    def on_import_sqlite_pdm_clicked(self):
        # Abre o diálogo para escolher o arquivo SQLite
        file_name, _ = QFileDialog.getOpenFileName(self, "Importar dados PDM", "", "SQLite Files (*.db *.sqlite);;All Files (*)")
        if file_name:
            self.update_tree_view(file_name)

    def update_tree_view(self, file_path):
        db_path = str(CONTROLE_LIMITE_DISPENSA_DIR / 'dados_pdm.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        self.model.beginResetModel()

        query = """
        SELECT DISTINCT `Grupo Material`, `Unnamed: 2`, `Classe Material`, `Unnamed: 4`, `Padrão Desc Material`, `Unnamed: 6`
        FROM dados_pdm
        ORDER BY `Grupo Material`
        """
        cursor.execute(query)
        items = cursor.fetchall()
    
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Grupo', 'Descrição Grupo', 'Classe', 'Descrição Classe', 'PDM', 'Descrição PDM', 'Limite Disponível', 'Total Empenhado'])

        for item in items:
            grupo_material, unnamed_2, classe_material, unnamed_4, padrão_desc_material, unnamed_6 = item
            
            # Cria itens pais e adiciona todos os campos como itens separados na mesma linha
            row_items = [
                QStandardItem(f"{grupo_material}"),
                QStandardItem(f"{unnamed_2}"),
                QStandardItem(f"{classe_material}"),
                QStandardItem(f"{unnamed_4}"),
                QStandardItem(f"{padrão_desc_material}"),
                QStandardItem(f"{unnamed_6}"),
                QStandardItem("R$ 59.906,02"),  # Valor exemplo para Limite Disponível
                QStandardItem("R$ 0,00"),       # Valor exemplo para Total Empenhado
            ]
            self.model.appendRow(row_items)
            # print("Item SQLite - PDM: ", padrão_desc_material)  # Exemplo para um item específico
            # Adiciona um item filho fictício para garantir que o item pai seja expansível
            fictitious_child = QStandardItem("Carregando...")
            row_items[0].appendRow(fictitious_child)
            
            # Exemplo de armazenar uma chave no primeiro item para uso futuro ao carregar os itens filhos
            row_items[0].setData((grupo_material, unnamed_2, classe_material, unnamed_4, padrão_desc_material, unnamed_6), Qt.ItemDataRole.UserRole)

        self.model.endResetModel()
        conn.close()

    def on_import_sqlite_pdm_clicked(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Importar dados PDM", "", "SQLite Files (*.db *.sqlite);;All Files (*)")
        if file_name:
            self.update_tree_view(file_name)

    def on_import_pdm_clicked(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Importar dados PDM", "", "Excel Files (*.xlsx *.xls);;All Files (*)")
        if file_name:
            self.import_and_process_data(file_name)

    def import_and_process_data(self, file_path):
        df = pd.read_excel(file_path, skiprows=5)  # Ajuste conforme necessário
        
        # Verifica se o diretório existe. Se não, cria o diretório.
        if not CONTROLE_LIMITE_DISPENSA_DIR.exists():
            os.makedirs(CONTROLE_LIMITE_DISPENSA_DIR)
        
        # Agora, salvando o arquivo dados_pdm.db no diretório especificado
        db_path = CONTROLE_LIMITE_DISPENSA_DIR / 'dados_pdm.db'
        conn = sqlite3.connect(db_path)
        df.to_sql('dados_pdm', conn, if_exists='replace', index=False)
        conn.close()

    def ordenar_itens_modelo(self):
        # Passo 1: Coletar dados
        dados_para_ordenacao = []
        for row in range(self.model.rowCount()):
            itens_linha = [self.model.item(row, col).text() for col in range(self.model.columnCount())]
            valor_empenhado = convert_currency_to_float(itens_linha[7].replace("R$ ", ""))
            dados_para_ordenacao.append((valor_empenhado, itens_linha))
        
        # Passo 2: Limpar o modelo
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Grupo', 'Descrição Grupo', 'Classe', 'Descrição Classe', 'PDM', 'Descrição PDM', 'Limite Disponível', 'Total Empenhado'])

        # Passo 3: Reconstruir o modelo com os itens na nova ordem
        dados_ordenados = sorted(dados_para_ordenacao, key=lambda x: (-x[0], x[1]))
        for _, itens_linha in dados_ordenados:
            nova_linha_itens = [QStandardItem(item) for item in itens_linha]
            self.model.appendRow(nova_linha_itens)

class ColorDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        
        # Configurações padrão para todos os itens
        option.backgroundBrush = QColor(0, 0, 0)  # Fundo preto
        # Define a cor da fonte com base na coluna e no nível de profundidade do item
        if index.model().itemFromIndex(index).parent():  # Se o item tem um pai, é um item filho
            option.palette.setColor(QPalette.ColorRole.Text, QColor(192, 192, 192))  # Cor da fonte amarelo
        else:
            # Lógica para itens de nível superior baseada na coluna
            if index.column() in (0, 1, 2, 3):  # Colunas 'Grupo', 'Descrição Grupo', 'Classe', 'Descrição Classe'
                option.palette.setColor(QPalette.ColorRole.Text, QColor(192, 192, 192))  # Fonte cinza claro
            elif index.column() in (4, 5):  # Colunas 'PDM', 'Descrição PDM'
                option.palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))  # Fonte branca
            elif index.column() == 6:  # Coluna 'Limite Disponível'
                valor_texto = index.model().itemFromIndex(index).text()
                valor = convert_currency_to_float(valor_texto)
                # Aplica a cor da fonte com base no valor
                if valor == 59906.02:
                    color = QColor(0, 190, 255)  # Azul
                elif 59906.02 > valor > 20000:
                    color = QColor(0, 255, 0)  # Verde
                elif 20000 >= valor > 5000:
                    color = QColor(255, 255, 0)  # Amarelo
                elif 5000 >= valor > 1000:
                    color = QColor(255, 165, 0)  # Laranja
                elif valor <= 1000:
                    color = QColor(255, 0, 0)  # Vermelho
                option.palette.setColor(QPalette.ColorRole.Text, color)


def convert_currency_to_float(value):
    if isinstance(value, str):
        value = value.replace("R$", "").replace(".", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return 0.0


def adjust_report_column_widths(worksheet, widths):
    for col_num, width in enumerate(widths, start=1):  # Enumera a partir de 1, pois as colunas do Excel começam em 1
        worksheet.column_dimensions[get_column_letter(col_num)].width = width
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import sqlite3
from diretorios import *
from modules.atas.regex_termo_homolog import *
from modules.atas.regex_sicaf import *
from modules.atas.canvas_gerar_atas import *
import os
import pdfplumber
import locale
from decimal import Decimal
from modules.planejamento.utilidades_planejamento import DatabaseManager
import re

try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')  # Alternativa para Windows
    except locale.Error:
        print("Localidade não suportada. A formatação de moeda pode não funcionar corretamente.")


class PDFProcessingThread(QThread):
    progress_updated = pyqtSignal(int, int, str)
    processing_complete = pyqtSignal(list)

    def __init__(self, pdf_dir, txt_dir, buffer_size=10):
        super().__init__()
        self.pdf_dir = Path(pdf_dir)
        self.txt_dir = Path(txt_dir)
        self.buffer_size = buffer_size
        self.buffer = []

    def run(self):
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        total_files = len(pdf_files)
        all_data = []
        for index, pdf_file in enumerate(pdf_files):
            data = self.process_single_pdf(pdf_file)
            all_data.extend(data)
            self.progress_updated.emit(index + 1, total_files, pdf_file.name)
        self.processing_complete.emit(all_data)

    def process_single_pdf(self, pdf_file):
        text_content = self.extract_text_from_pdf(pdf_file)
        self.save_text_to_file(pdf_file, text_content)
        return [{'item_num': pdf_file.stem, 'text': text_content}]

    def extract_text_from_pdf(self, pdf_file):
        with pdfplumber.open(pdf_file) as pdf:
            texts = [page.extract_text() for page in pdf.pages]
            all_text = ' '.join(texts).replace('\n', ' ').replace('\x0c', ' ')
        return all_text

    def save_text_to_file(self, pdf_file, text_content):
        txt_file = self.txt_dir / f"{pdf_file.stem}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(text_content)

class DatabaseDialog(QDialog):
    def __init__(self, parent=None, dataframe=None, callback=None):
        super().__init__(parent)
        self.dataframe = dataframe
        self.db_manager = DatabaseManager(CONTROLE_DADOS)
        self.callback = callback
        self.setup_ui()
        self.setFixedSize(600, 350)

    def cabecalho_layout(self):
        header_layout = QHBoxLayout()
        title_label = QLabel("<div style='font-size: 32px; font-weight: bold;'>Gerenciamento do Database</div>")
        header_layout.addWidget(title_label)
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        pixmap = QPixmap(str(IMAGE_PATH / "acanto"))
        pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        header_layout.addWidget(image_label)
        
        return header_layout

    def setup_ui(self):
        self.setWindowTitle("Gerenciamento de Dados")
        self.setFont(QFont('Arial', 16))

        layout = QVBoxLayout(self)
        
        layout.addLayout(self.cabecalho_layout())

        self.info_label = QLabel("Escolha uma opção:")
        self.info_label.setFont(QFont('Arial', 16))
        layout.addWidget(self.info_label)

        self.add_action_buttons(layout)

        self.table_combobox = QComboBox()
        self.table_combobox.setFont(QFont('Arial', 14))
        layout.addWidget(self.table_combobox)
        
        self.setLayout(layout)

    def add_action_buttons(self, layout):
        icon_load = QIcon(str(ICONS_DIR / "processing.png"))
        icon_delete = QIcon(str(ICONS_DIR / "delete.png"))

        self.load_button = self.create_button("Carregar", icon_load, self.load_data, "Carregar dados de uma tabela do banco de dados")
        self.delete_button = self.create_button("Excluir Database", icon_delete, self.populate_and_show_delete_options, "Excluir uma tabela selecionada do banco de dados")

        layout.addWidget(self.load_button)
        layout.addWidget(self.delete_button)

    def create_button(self, text, icon, callback, tooltip_text, icon_size=None):
        btn = QPushButton(text)
        btn.setIcon(icon)
        btn.setFont(QFont('Arial', 14))
        if icon_size is None:
            icon_size = QSize(40, 40)
        btn.setIconSize(icon_size)
        btn.clicked.connect(callback)
        btn.setToolTip(tooltip_text)
        return btn

    def populate_and_show_delete_options(self):
        tables = self.db_manager.execute_query("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT IN ('controle_agentes_responsaveis', 'controle_om', 'controle_prazos', 'controle_processos', 'sqlite_sequence');
        """)
        
        self.table_combobox.clear()
        if tables:
            self.table_combobox.addItems([table[0] for table in tables])
        else:
            QMessageBox.warning(self, "Aviso", "Nenhuma tabela elegível foi encontrada.")
            return
        
        self.delete_button.setText("Confirmar Exclusão")
        self.delete_button.clicked.disconnect()
        self.delete_button.clicked.connect(self.confirm_deletion)

    def confirm_deletion(self):
        selected_table = self.table_combobox.currentText()
        if selected_table:
            confirm = QMessageBox.question(self, "Confirmar Exclusão", f"Tem certeza que deseja excluir a tabela '{selected_table}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    self.db_manager.execute_query(f'DROP TABLE IF EXISTS "{selected_table}"')
                    QMessageBox.information(self, "Sucesso", f"Tabela '{selected_table}' excluída com sucesso!")
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao excluir a tabela: {e}")
                finally:
                    self.populate_and_show_delete_options()  # Re-populate list and reset state

            
    # def save_data(self):
    #     if isinstance(self.dataframe, pd.DataFrame) and not self.dataframe.empty:
    #         print("Salvando DataFrame com as colunas:", self.dataframe.columns)
    #         name, ok = QInputDialog.getText(self, "Salvar DataFrame", "Digite o nome da tabela:")
    #         if ok and name:
    #             with self.db_manager as conn:
    #                 self.dataframe.to_sql(name, conn, if_exists='replace', index=False)
    #             QMessageBox.information(self, "Sucesso", "DataFrame salvo com sucesso!")
    #             self.accept()  # Fecha o diálogo após salvar com sucesso
    #     else:
    #         QMessageBox.critical(self, "Erro", "Nenhum DataFrame válido disponível para salvar ou o objeto não é um DataFrame.")

    def load_data(self):
        with self.db_manager as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cur.fetchall()]

        if not tables:
            QMessageBox.warning(self, "Aviso", "Nenhuma tabela foi encontrada.")
            return

        # Padrão para capturar 1 a 5 dígitos seguidos de um ano (4 dígitos) entre hífens
        pattern = re.compile(r"(\d{1,5})-(\d{4})-")
        
        # Filtrar as tabelas que seguem o padrão
        pe_tables = [table for table in tables if pattern.search(table)]

        item, ok = QInputDialog.getItem(self, "Carregar DataFrame", "Selecione a tabela:", pe_tables, 0, False)
        if ok and item:
            safe_table_name = f'"{item}"'  # Protege o nome da tabela
            with self.db_manager as conn:
                df = pd.read_sql(f"SELECT * FROM {safe_table_name}", conn)
            if self.callback:
                match = pattern.search(item)
                extracted_pe = match.group(1) if match else "Desconhecido"  # Captura apenas a primeira parte (os dígitos)
                self.callback(df, extracted_pe)  # Passa o DataFrame e o valor extraído do padrão
            QMessageBox.information(self, "Sucesso", f"DataFrame '{item}' carregado com sucesso!")
            self.close()  # Fecha o diálogo após carregar com sucesso

def format_currency(value):
    """ Função para formatar valores monetários. """
    return f"R$ {value:,.2f}".replace(',', 'temp').replace('.', ',').replace('temp', '.')
    
def atualizar_modelo_com_dados(model, df, mapeamento_colunas, treeview):
    print("Atualizando a tabela com os dados do DataFrame...")
    # Mapear as colunas do DataFrame para os nomes das colunas na tabela
    df_renamed = df.rename(columns={v: k for k, v in mapeamento_colunas.items() if v in df.columns})

    # Reordenar as colunas de acordo com a ordem dos cabeçalhos do modelo
    ordered_cols = [col for col in model.get_headers() if col in df_renamed.columns]
    df_final = df_renamed[ordered_cols]

    print("Carregando dados no modelo...")
    model.load_data(df_final)
    print("Modelo de dados carregado. Resetando a tabela...")
    treeview.setModel(model)
    treeview.reset()

def adjustar_colunas(tableView, model, colunas_escondidas):
    print("Ajustando as colunas do QTableView...")
    header = tableView.horizontalHeader()
    for i in range(model.columnCount()):
        header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    for desc_key in colunas_escondidas:
        column_index = model.get_headers().index(desc_key) if desc_key in model.get_headers() else -1
        if column_index != -1:
            tableView.setColumnHidden(column_index, True)
    print("Colunas ajustadas no QTableView.")

def load_file_path():
    settings = QSettings("SuaEmpresa", "SeuApp")
    return settings.value("termo_referencia_arquivo", "")

def create_dataframe_from_txt_files(extracted_data):
    all_data = []

    for item in extracted_data:
        content = item['text']
        uasg_pregao_data = extrair_uasg_e_pregao(content, padrao_1, padrao_srp, padrao_objeto)
        items_data = identificar_itens_e_grupos(content, padrao_grupo2, padrao_item2, padrao_3, padrao_4, pd.DataFrame())
        
        for item_data in items_data:
            all_data.append({
                **uasg_pregao_data,
                **item_data
            })

    dataframe_licitacao = pd.DataFrame(all_data)
    if "item_num" not in dataframe_licitacao.columns:
        raise ValueError("A coluna 'item_num' não foi encontrada no DataFrame.")
    
    return dataframe_licitacao.sort_values(by="item_num")

def save_to_dataframe(extracted_data, tr_variavel_df_carregado, database_dir, existing_dataframe=None):
    df_extracted = create_dataframe_from_txt_files(extracted_data)
    df_extracted['item_num'] = pd.to_numeric(df_extracted['item_num'], errors='coerce').astype('Int64')
    
    if tr_variavel_df_carregado is not None:
        tr_variavel_df_carregado['item_num'] = pd.to_numeric(tr_variavel_df_carregado['item_num'], errors='coerce').astype('Int64')
        merged_df = pd.merge(tr_variavel_df_carregado, df_extracted, on='item_num', how='outer', suffixes=('_x', '_y'))

        for column in merged_df.columns:
            if column.endswith('_y'):
                col_x = column[:-2] + '_x'
                if col_x in merged_df.columns:
                    merged_df[col_x] = merged_df[col_x].combine_first(merged_df[column])
                merged_df.drop(columns=[column], inplace=True)
                merged_df.rename(columns={col_x: col_x[:-2]}, inplace=True)

        # Reordenando as colunas
        column_order = ['grupo', 'item_num', 'catalogo', 'descricao_tr', 'unidade', 'quantidade', 'valor_estimado', 
                        'valor_homologado_item_unitario', 'percentual_desconto', 'valor_estimado_total_do_item', 'valor_homologado_total_item',
                        'marca_fabricante', 'modelo_versao', 'situacao', 'descricao_detalhada', 'uasg', 'orgao_responsavel', 'num_pregao', 'ano_pregao', 
                        'srp', 'objeto', 'melhor_lance', 'valor_negociado', 'ordenador_despesa', 'empresa', 'cnpj',
                        'endereco', 'cep', 'municipio', 'telefone', 'email', 'responsavel_legal' 
                        ]
        merged_df = merged_df.reindex(columns=column_order)

        if existing_dataframe is not None:
            final_df = pd.concat([existing_dataframe, merged_df]).drop_duplicates(subset='item_num').reset_index(drop=True)
        else:
            final_df = merged_df

        final_df.to_csv(database_dir / "dados.csv", index=False)
        return final_df
    else:
        QMessageBox.warning(None, "Aviso", "Nenhum DataFrame de termo de referência carregado.")
        return None


def obter_arquivos_txt(directory: str) -> list:
    return [str(file) for file in Path(directory).glob("*.txt")]

def ler_arquivos_txt(file_path: str) -> str:
    """Lê o conteúdo de um arquivo TXT."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def save_to_excel(df, filepath):
    df.to_excel(filepath, index=False, engine='openpyxl')

def save_dataframe_as_excel(df: pd.DataFrame, output_path: str):
    df.to_excel(output_path, index=False, engine='openpyxl')

def convert_pdf_to_txt(pdf_dir, txt_dir, dialog):
    if not txt_dir.exists():
        txt_dir.mkdir(parents=True, exist_ok=True)
    else:
        for file in txt_dir.iterdir():
            if file.is_file():
                file.unlink()

    pdf_files = list(pdf_dir.glob("*.pdf"))
    total_files = len(pdf_files)

    for index, pdf_file in enumerate(pdf_files):
        with pdfplumber.open(pdf_file) as pdf:
            texts = [page.extract_text() for page in pdf.pages]
            all_text = ' '.join(texts).replace('\n', ' ').replace('\x0c', ' ')
            txt_file = txt_dir / f"{pdf_file.stem}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(all_text)

        # Atualiza a barra de progresso através do diálogo
        progress = (index + 1) / total_files * 100
        dialog.update_progress(progress)


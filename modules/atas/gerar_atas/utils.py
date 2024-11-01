
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import pandas as pd
import sys
import os
import subprocess
from pathlib import Path

# Funções auxiliares
def create_button(texto, funcao):
    botao = QPushButton(texto)
    botao.clicked.connect(funcao)
    return botao

def create_fixed_width_frame(width, layout):
    frame = QFrame()
    frame.setFixedWidth(width)
    frame.setLayout(layout)
    return frame

def add_or_remove_widget(layout, widget, add):
    if add and widget.parent() is None:
        layout.addWidget(widget)
    elif not add and widget.parent() is not None:
        layout.removeWidget(widget)
        widget.setParent(None)

def create_button_layout(buttons):
    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    for texto, funcao, _ in buttons:
        layout.addWidget(create_button(texto, funcao))
    return layout

def create_dynamic_view(view_name):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.addWidget(QLabel(f"Layout dinâmico para {view_name}"))
    return widget

def select_file(parent, title):
    file_path, _ = QFileDialog.getOpenFileName(parent, title, "", "Arquivos Excel (*.xlsx);;Arquivos LibreOffice (*.ods)")
    return file_path

def load_file(file_path):
    ext = Path(file_path).suffix.lower()
    return pd.read_excel(file_path, engine='odf' if ext == '.ods' else None) if ext in ['.xlsx', '.ods'] else None

def atualizar_modelo_com_dados(model, tree_view, df):
    model.clear()
    model.setHorizontalHeaderLabels(['Item', 'Catálogo', 'Descrição', 'Descrição Detalhada'])
    for _, row in df.iterrows():
        model.appendRow([create_item(value) for value in [row['item_num'], row['catalogo'], row['descricao_tr'], row['descricao_detalhada']]])
    tree_view.resizeColumnsToContents()
    tree_view.setColumnWidth(2, 150)

def create_item(value):
    item = QStandardItem(str(value))
    item.setEditable(False)
    return item

def formatar_e_validar_dados(df):
    required_columns = ['item_num', 'catalogo', 'descricao_tr', 'descricao_detalhada']
    return [f"Coluna {col} ausente" for col in required_columns if col not in df.columns]

def criar_tabela_vazia(arquivo_xlsx, dialog):
    df_vazio = pd.DataFrame({
        "item_num": range(1, 11),
        "catalogo": [""] * 10,
        "descricao_tr": [""] * 10,
        "descricao_detalhada": [""] * 10
    })
    try:
        df_vazio.to_excel(arquivo_xlsx, index=False)
        os.startfile(arquivo_xlsx)
    except PermissionError:
        QMessageBox.warning(dialog, "Arquivo Aberto", "A tabela 'tabela_vazia.xlsx' está aberta. Feche o arquivo antes de tentar salvá-la novamente.")

def open_folder(path):
    if sys.platform == 'win32':  # Para Windows
        os.startfile(path)
    elif sys.platform == 'darwin':  # Para macOS
        subprocess.Popen(['open', path])
    else:  # Para Linux e outros sistemas Unix-like
        subprocess.Popen(['xdg-open', path])
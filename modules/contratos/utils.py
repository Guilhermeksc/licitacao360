## módulo incluido em modules/contratos/utils.py ##

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import pandas as pd
import sqlite3

class WidgetHelper:
    @staticmethod
    def create_line_edit(label_text, initial_value=""):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        line_edit = QLineEdit(str(initial_value))  # Convertendo para string
        copy_button = QPushButton("Copiar")
        
        # Estilo
        label.setStyleSheet("font-size: 14px;")
        line_edit.setStyleSheet("font-size: 14px;")
        copy_button.setStyleSheet("font-size: 14px;")
        
        # Função de copiar
        copy_button.clicked.connect(lambda: QGuiApplication.clipboard().setText(line_edit.text()))
        
        # Adicionar widgets ao layout
        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(copy_button)
        
        return layout, line_edit

    @staticmethod
    def create_radio_buttons(label_text, options):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 14px;")
        layout.addWidget(label)
        button_group = QButtonGroup()
        buttons = {}
        for option in options:
            button = QRadioButton(option)
            button.setStyleSheet("font-size: 14px;")
            button_group.addButton(button)
            layout.addWidget(button)
            buttons[option] = button
        return layout, buttons, button_group

    @staticmethod
    def create_date_edit(label_text, initial_value=None):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 14px;")
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setStyleSheet("font-size: 14px;")
        if initial_value:
            date_edit.setDate(QDate.fromString(initial_value, 'dd/MM/yyyy'))
        layout.addWidget(label)
        layout.addWidget(date_edit)
        return layout, date_edit

    @staticmethod
    def create_combo_box(label_text, options, initial_value=None):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 14px;")
        combo_box = QComboBox()
        combo_box.addItems(options)
        combo_box.setStyleSheet("font-size: 14px;")
        if initial_value:
            index = combo_box.findText(initial_value)
            if index != -1:
                combo_box.setCurrentIndex(index)
        layout.addWidget(label)
        layout.addWidget(combo_box)
        return layout, combo_box
    
    @staticmethod
    def create_button(text="", icon=None, callback=None, tooltip_text="", button_size=None, icon_size=None):
        btn = QPushButton(text)
        if icon:
            btn.setIcon(QIcon(icon))
            btn.setIconSize(icon_size if icon_size else QSize(40, 40))
        if button_size:
            btn.setFixedSize(button_size)
        btn.setToolTip(tooltip_text)
        btn.setStyleSheet("font-size: 14px;")  # Ajuste do tamanho da fonte
        if callback:
            btn.clicked.connect(callback)  # Conecta o callback ao evento de clique
        return btn

class ColorDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        value = index.data()
        if value is not None:
            try:
                days = int(value)
                if days < 30:
                    color = QColor(255, 0, 0)  # Red
                elif 31 <= days <= 90:
                    color = QColor(255, 165, 0)  # Orange
                elif 91 <= days <= 159:
                    color = QColor(255, 255, 0)  # Yellow
                else:
                    color = QColor(0, 255, 0)  # Green

                option.palette.setColor(QPalette.ColorRole.Text, color)
            except ValueError:
                pass
        
        # Centraliza o texto
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        super().paint(painter, option, index)
        
class ExportThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, model, filepath):
        super().__init__()
        self.model = model
        self.filepath = filepath

    def run(self):
        try:
            df = self.model_to_dataframe(self.model)
            df.to_excel(self.filepath, index=False)
            self.finished.emit('Completed successfully!')
        except Exception as e:
            self.finished.emit(f"Failed: {str(e)}")

    def model_to_dataframe(self, model):
        headers = [model.headerData(i, Qt.Orientation.Horizontal) for i in range(model.columnCount())]
        data = [
            [model.data(model.index(row, col)) for col in range(model.columnCount())]
            for row in range(model.rowCount())
        ]
        return pd.DataFrame(data, columns=headers)
    
def carregar_dados_contratos(index, caminho_banco_dados):
    """
    Carrega os dados de contrato do banco de dados SQLite especificado pelo caminho_banco_dados.

    Parâmetros:
    - index: O índice da linha selecionada na QTableView.
    - caminho_banco_dados: O caminho para o arquivo do banco de dados SQLite.
    
    Retorna:
    - Um dicionário contendo os dados do registro selecionado.
    """
    try:
        connection = sqlite3.connect(caminho_banco_dados)
        
        # Recupere o número do contrato com base no índice da linha
        cursor = connection.cursor()
        cursor.execute("SELECT numero_contrato FROM controle_contratos LIMIT 1 OFFSET ?", (index,))
        resultado = cursor.fetchone()
        
        if resultado is None:
            raise Exception("Nenhum contrato encontrado para o índice fornecido.")
        
        numero_contrato = resultado[0]
        
        # Carrega os dados do contrato específico
        query = f"SELECT * FROM controle_contratos WHERE numero_contrato='{numero_contrato}'"
        df_registro_selecionado = pd.read_sql_query(query, connection)
        connection.close()

        if not df_registro_selecionado.empty:
            return df_registro_selecionado.iloc[0].to_dict()  # Retorna o primeiro registro como dicionário
        else:
            return {}
    except Exception as e:
        print(f"Erro ao carregar dados do banco de dados: {e}")
        return {}  # Retorna um dicionário vazio em caso de erro


class Dialogs:
    @staticmethod
    def info(parent, title, message):
        QMessageBox.information(parent, title, message)

    @staticmethod
    def warning(parent, title, message):
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def error(parent, title, message):
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def confirm(parent, title, message):
        reply = QMessageBox.question(parent, title, message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

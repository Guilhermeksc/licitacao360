# create_pdf_button.py


from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QPushButton
import sqlite3
from styles.styless import get_transparent_title_style

class RegistroFornecedor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Título
        label_registro_fornecedor = QLabel("Registro de Fornecedores")
        label_registro_fornecedor.setStyleSheet(get_transparent_title_style())
        self.layout.addWidget(label_registro_fornecedor)

        # ComboBox para seleção da linha de fornecimento
        self.combo_box = QComboBox()
        self.combo_box.addItems(["Material de construção", "Material de expediente", "Material de limpeza", "Gêneros alimentícios", "Materiais de informática"])
        self.layout.addWidget(self.combo_box)

        # Tabela para exibir os fornecedores
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5) # Exemplo: ID, Nome, Linha, Contato, Endereço
        self.table_widget.setHorizontalHeaderLabels(["ID", "Nome", "Linha de Fornecimento", "Contato", "Endereço"])
        self.layout.addWidget(self.table_widget)

        # Botão para atualizar os dados
        self.load_button = QPushButton("Carregar Dados")
        self.load_button.clicked.connect(self.load_data)
        self.layout.addWidget(self.load_button)

    def load_data(self):
        # Carregar dados do banco de dados baseado na linha de fornecimento selecionada
        selected_line = self.combo_box.currentText()
        
        # Aqui você faria a consulta ao SQLite3 e preencheria a tabela
        # Exemplo: SELECT * FROM fornecedores WHERE linha_fornecimento = selected_line

    def get_title(self):
        return "Registro de Fornecedores"

    def get_content_widget(self):
        return self

# # Supondo que você ainda queira usar uma MainWindow para exibir este widget:
# import sys
# from PyQt6.QtWidgets import QApplication, QMainWindow

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Relação de Fornecedores")
#         self.setCentralWidget(RegistroFornecedor())

# def main():
#     app = QApplication(sys.argv)
#     main_window = MainWindow()
#     main_window.show()
#     sys.exit(app.exec())

# if __name__ == "__main__":
#     main()


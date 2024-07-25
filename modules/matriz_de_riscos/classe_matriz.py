from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.matriz_de_riscos.tabela_de_riscos import TabelaDeRiscos
from modules.matriz_de_riscos.mapa_calor import HeatmapGenerator
import pandas as pd
from diretorios import *
import os

class MatrizRiscosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.data_manager = DataManager(self)
        self.tree_view_manager = TreeViewManager(self.tree_view)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Título
        title_label = self.create_label("Matriz de Riscos", font_size=30, bold=True, color="white", alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Layout horizontal para combobox e botões
        h_layout = QHBoxLayout()

        # Layout para Label e Botões
        label_buttons_layout = QVBoxLayout()

        escolha_processo_layout = QHBoxLayout()
        combobox_label = self.create_label("Escolha o processo:", font_size=20, color="white")
        escolha_processo_layout.addWidget(combobox_label)

        self.combobox_processo = QComboBox()
        self.combobox_processo.addItems(["PE 01/2024", "PE 02/2024", "PE 03/2024", "PE 04/2024"])
        self.combobox_processo.setStyleSheet("font-size: 20px;")
        escolha_processo_layout.addWidget(self.combobox_processo)

        label_buttons_layout.addLayout(escolha_processo_layout)

        escolha_padrao_matriz_layout = QHBoxLayout()
        combobox_label = self.create_label("Escolha o tipo de Matriz:", font_size=20, color="white")
        escolha_padrao_matriz_layout.addWidget(combobox_label)

        self.combobox_matriz = QComboBox()
        self.combobox_matriz.addItems(["Material de Consumo", "Material Permanente", "Serviços Comuns", "Serviços de Engenharia", "Serviços de Mão de Obra", "Obras"])
        self.combobox_matriz.setStyleSheet("font-size: 20px;")
        escolha_padrao_matriz_layout.addWidget(self.combobox_matriz)

        label_buttons_layout.addLayout(escolha_padrao_matriz_layout)

        carregar_dados_riscos_layout = QHBoxLayout()

        load_button_label = self.create_label("Escolha o arquivo para carregar os dados:", font_size=20, color="white")
        carregar_dados_riscos_layout.addWidget(load_button_label)

        load_button = self.create_button("Carregar Dados", font_size=20, callback=self.load_data)
        carregar_dados_riscos_layout.addWidget(load_button)

        label_buttons_layout.addLayout(carregar_dados_riscos_layout)

        h_layout.addLayout(label_buttons_layout)

        # Botão "Gerar Matriz" à direita no h_layout
        generate_button = self.create_button("Gerar Matriz", font_size=20, callback=self.generate_matrix)
        h_layout.addWidget(generate_button)

        # Botão "Gerar Mapa de Calor" à direita no h_layout
        heatmap_button = self.create_button("Gerar Mapa de Calor", font_size=20, callback=self.generate_heatmap)
        h_layout.addWidget(heatmap_button)

        main_layout.addLayout(h_layout)

        # Layout vertical para as fases
        fases_layout = QVBoxLayout()
        fases_layout.setContentsMargins(0, 50, 0, 0)
        fases_layout.setSpacing(0)

        self.tree_view = QTreeView()
        self.tree_view_manager = TreeViewManager(self.tree_view)

        fases_layout.addWidget(self.tree_view)
        main_layout.addLayout(fases_layout)
        self.setLayout(main_layout)


    def create_label(self, text, font_size=12, bold=False, color="black", alignment=None):
        label = QLabel(text)
        style = f"font-size: {font_size}px; color: {color};"
        if bold:
            style += " font-weight: bold;"
        label.setStyleSheet(style)
        if alignment:
            label.setAlignment(alignment)
        return label

    def create_button(self, text, font_size=12, callback=None):
        button = QPushButton(text)
        button.setStyleSheet(f"font-size: {font_size}px;")
        if callback:
            button.clicked.connect(callback)
        return button

    def load_data(self):
        dados = self.data_manager.load_data()
        if not dados.empty:
            self.tree_view_manager.populate_treeview(dados)

    def generate_matrix(self):
        if hasattr(self.data_manager, 'dados') and not self.data_manager.dados.empty:
            dados = self.data_manager.dados.to_dict(orient='records')
            print("Usando os dados carregados pelo usuário.")
        else:
            print("Dados não carregados pelo usuário. Carregando a matriz base.")
            dados = pd.read_excel(TABELA_BASE_MATRIZ).to_dict(orient='records')
            print(f"Dados carregados automaticamente: {dados}")
        tabela_de_riscos = TabelaDeRiscos(TEMPLATE_MATRIZ_RISCOS, TEMPLATE_MATRIZ_PARTE2, dados)
        tabela_de_riscos.gerar_documento()

    def generate_heatmap(self):
        if hasattr(self.data_manager, 'dados') and not self.data_manager.dados.empty:
            heatmap_generator = HeatmapGenerator(self.data_manager.dados)
            image_path = heatmap_generator.generate_heatmap()
            print(f"Mapa de calor gerado: {image_path}")
            # Abrir a imagem gerada
            if os.path.exists(image_path):
                os.startfile(image_path)
        else:
            QMessageBox.warning(self, "Aviso", "Por favor, carregue os dados primeiro.")

class DataManager:
    def __init__(self, parent):
        self.parent = parent
        self.dados = pd.DataFrame()

    def load_data(self):
        initial_dir = str(BASE_DIR)
        file_name, _ = QFileDialog.getOpenFileName(self.parent, "Selecione a tabela", initial_dir, "Arquivos de Tabela (*.xlsx *.ods)")
        if file_name:
            self.dados = pd.read_excel(file_name)
            print(f"Arquivo selecionado: {file_name}")
        return self.dados

class TreeViewManager:
    def __init__(self, tree_view):
        self.tree_view = tree_view
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setStyleSheet("""
            QTreeView {
                background: transparent;
                border-top: 2px solid white;
                color: white;
            }
            QTreeView::item {
                color: black;
                font-size: 18px;
                font-weight: bold;
            }
            QTreeView::item:hover {
                background-color: white;
            }
        """)
        self.tree_view.expanded.connect(self.expand_all_children)
        self.tree_view.clicked.connect(self.toggle_expand_collapse)

    def populate_treeview(self, dados):
        self.model.clear()
        fases = ["Planejamento da Contratação", "Seleção do Fornecedor", "Gestão e Fiscalização do Contrato"]
        fase_items = {fase: QStandardItem(fase) for fase in fases}
        for fase_item in fase_items.values():
            fase_item.setEditable(False)
            fase_item.setForeground(QBrush(QColor("white")))
            fase_item.setFont(QFont("Arial", 20, QFont.Weight.Bold))

        for _, dado in dados.iterrows():
            fase_item = fase_items.get(dado["Fase"])
            if fase_item:
                risco_item = QStandardItem(dado["Risco"])
                risco_item.setEditable(False)
                risco_item.setFont(QFont("Arial", 16))

                causa_item = QStandardItem(f"Causa: {dado['Causa']}")
                causa_item.setEditable(False)
                causa_item.setFont(QFont("Arial", 12))

                evento_item = QStandardItem(f"Evento: {dado['Evento']}")
                evento_item.setEditable(False)
                evento_item.setFont(QFont("Arial", 12))

                consequencia_item = QStandardItem(f"Consequência: {dado['Consequência']}")
                consequencia_item.setEditable(False)
                consequencia_item.setFont(QFont("Arial", 12))

                risco_item.appendRow(causa_item)
                risco_item.appendRow(evento_item)
                risco_item.appendRow(consequencia_item)
                fase_item.appendRow(risco_item)

        for item in fase_items.values():
            self.model.appendRow(item)

    def expand_all_children(self, index):
        def recursive_expand(index):
            if self.model.hasChildren(index):
                for row in range(self.model.rowCount(index)):
                    child_index = self.model.index(row, 0, index)
                    self.tree_view.expand(child_index)
                    recursive_expand(child_index)
        recursive_expand(index)

    def toggle_expand_collapse(self, index):
        if self.tree_view.isExpanded(index):
            self.tree_view.collapse(index)
        else:
            self.tree_view.expand(index)



# Teste da classe MatrizRiscosWidget
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("Teste Matriz de Riscos")
    main_window.setGeometry(100, 100, 800, 600)

    matriz_riscos_widget = MatrizRiscosWidget()
    main_window.setCentralWidget(matriz_riscos_widget)

    main_window.show()
    sys.exit(app.exec())
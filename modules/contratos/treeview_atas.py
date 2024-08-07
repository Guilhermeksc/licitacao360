from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.contratos.database_manager import DatabaseContratosManager, SqlModel
import sqlite3
from diretorios import load_config, CONTROLE_CONTRATOS_DADOS, IMAGE_PATH, ICONS_DIR
from pathlib import Path
import time

class TreeViewAtasDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualização das Atas de Registro de Preços (ARP)")
        self.setFixedWidth(800)
        self.setMinimumHeight(600)
        self.layout = QVBoxLayout(self)

        self.icons_dir = Path(str(ICONS_DIR))
        self.icon_existe = QIcon(str(self.icons_dir / "checked.png"))
        self.icon_nao_existe = QIcon(str(self.icons_dir / "cancel.png"))

        caminho_imagem = Path(str(IMAGE_PATH / "titulo360superior.png"))
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Controle de Atas de Registro de Preços")
        title_font = QFont()
        title_font.setPointSize(16)
        title_label.setFont(title_font)
        
        image_label = QLabel()
        pixmap = QPixmap(str(caminho_imagem))
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(image_label)

        self.layout.addLayout(header_layout)

        self.tree_view = QTreeView(self)
        self.tree_view.setStyleSheet("""
            QTreeView::item:hover { background-color: transparent; }
            QTreeView::item:selected { background-color: transparent; }
        """)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Detalhes do Contrato"])
        self.tree_view.setModel(self.model)
        self.layout.addWidget(self.tree_view)

        font = QFont()
        font.setPointSize(14)
        self.tree_view.setFont(font)

        self.database_manager = self.init_database_manager()
        data = self.load_data(self.database_manager)
        self.populate_tree_view(data)
        self.close_database_connections()

        self.tree_view.expanded.connect(self.expand_all_children)
        self.tree_view.collapsed.connect(self.collapse_all_children)

    def expand_all_children(self, index):
        item = self.model.itemFromIndex(index)
        if item:
            for row in range(item.rowCount()):
                child_index = item.child(row).index()
                self.tree_view.expand(child_index)
    
    def collapse_all_children(self, index):
        item = self.model.itemFromIndex(index)
        if item:
            for row in range(item.rowCount()):
                child_index = item.child(row).index()
                self.tree_view.collapse(child_index)

    def init_database_manager(self):
        database_path = Path(load_config("CONTROLE_CONTRATOS_DADOS", str(CONTROLE_CONTRATOS_DADOS)))
        return DatabaseContratosManager(database_path)

    def load_data(self, database_manager):
        try:
            conn = database_manager.connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM controle_contratos")
            results = cursor.fetchall()
            conn.close()
            return results
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            return []

    def populate_tree_view(self, data):
        unique_combinations = {}
        for row in data:
            uasg = row[10]
            id_processo = row[6]
            numero_contrato = row[4]
            empresa = row[7]
            objeto = row[8]
            valor_global = row[9]
            link_pncp = row[18]
            assinatura_contrato = row[40] if row[40] is not None else "Não"

            parent_text = f"{id_processo} (UASG: {uasg})"
            if parent_text not in unique_combinations:
                unique_combinations[parent_text] = []

            child_text = f"{numero_contrato} - {empresa}"
            unique_combinations[parent_text].append((child_text, objeto, valor_global, link_pncp, assinatura_contrato))

        for parent_text, children in unique_combinations.items():
            parent_item = QStandardItem(parent_text)
            for child_text, objeto, valor_global, link_pncp, assinatura_contrato in children:
                child_item = QStandardItem(child_text)
                objeto_item = QStandardItem(f"Objeto: {objeto}")
                valor_global_item = QStandardItem(f"Valor Global: {valor_global}")
                link_pncp_item = QStandardItem(f"Link PNCP: {link_pncp}")

                child_item.appendRow(objeto_item)
                child_item.appendRow(valor_global_item)
                child_item.appendRow(link_pncp_item)

                assinatura_item = QStandardItem("")
                child_item.appendRow(assinatura_item)
                parent_item.appendRow(child_item)

                conferido_widget = QWidget()
                conferido_layout = QHBoxLayout()
                font = QFont()
                font.setPointSize(14)
                label = QLabel("Assinado?")
                label.setFont(font)
                sim_radio = QRadioButton("Sim")
                sim_radio.setFont(font)
                nao_radio = QRadioButton("Não")
                nao_radio.setFont(font)
                conferido_layout.addWidget(label)
                conferido_layout.addWidget(sim_radio)
                conferido_layout.addWidget(nao_radio)
                conferido_layout.addStretch()
                conferido_widget.setLayout(conferido_layout)
                
                if assinatura_contrato == "Sim":
                    sim_radio.setChecked(True)
                else:
                    nao_radio.setChecked(True)

                index = self.model.indexFromItem(assinatura_item)
                if index.isValid():
                    self.tree_view.setIndexWidget(index, conferido_widget)

                sim_radio.toggled.connect(lambda checked, item=child_item, contrato=numero_contrato: self.handle_radio_button_change(checked, item, contrato))

            self.model.appendRow(parent_item)
            self.tree_view.setFirstColumnSpanned(self.model.indexFromItem(parent_item).row(), self.tree_view.rootIndex(), True)

    def handle_radio_button_change(self, checked, item, contrato):
        self.update_icon_and_db(item, checked, contrato)

    def update_icon_and_db(self, item, checked, contrato):
        if checked:
            item.setIcon(self.icon_existe)
        else:
            item.setIcon(self.icon_nao_existe)

    def close_database_connections(self):
        self.database_manager.close_connection()
        source_model = self.tree_view.model()
        if hasattr(source_model, 'database_manager'):
            source_model.database_manager.close_connection()
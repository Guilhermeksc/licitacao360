from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.contratos.database_manager import DatabaseContratosManager, SqlModel
from modules.contratos.utils import Dialogs
import sqlite3
from diretorios import load_config, CONTROLE_CONTRATOS_DADOS, CONTROLE_ASS_CONTRATOS_DADOS, IMAGE_PATH, ICONS_DIR
from pathlib import Path
import logging
from functools import partial
import pandas as pd

class TreeViewContratosDialog(QDialog):
    def __init__(self, database_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualização das Contratos")
        self.setFixedWidth(1000)
        self.setMinimumHeight(750)
        self.database_path = database_path 
        self.database_manager = DatabaseContratosManager(self.database_path)
        self.database_manager_assinatura = self.init_database_manager_assinatura()
        self.icons_dir = Path(str(ICONS_DIR))
        self.icon_existe = QIcon(str(self.icons_dir / "checked.png"))
        self.icon_nao_existe = QIcon(str(self.icons_dir / "cancel.png"))
        self.icon_alert = QIcon(str(self.icons_dir / "alert.png"))
        self.init_ui()
        self.populate_tree_view(self.load_data())

    def init_database_manager_assinatura(self):
        database_path = Path(load_config("CONTROLE_CONTRATOS_DADOS", str(CONTROLE_ASS_CONTRATOS_DADOS)))
        db_manager = DatabaseContratosManager(database_path)
        db_manager.create_table_controle_assinatura()  # Garante que a tabela seja criada
        return db_manager
    
    def check_initial_status(self, numero_contrato):
        try:
            conn = self.database_manager_assinatura.connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT assinatura_contrato FROM controle_assinaturas WHERE numero_contrato = ?", (numero_contrato,))
            result = cursor.fetchone()
            if result:
                assinatura_contrato = result[0]
                checked = assinatura_contrato == "Sim"
                return checked, assinatura_contrato
            else:
                return False, "Não"
        except sqlite3.Error as e:
            logging.error(f"Erro ao verificar assinatura_contrato no banco de dados: {e}")
            return False, "Não"
        finally:
            self.database_manager_assinatura.close_connection()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.setup_header()
        self.setup_tree_view()

    def setup_header(self):
        header_layout = QHBoxLayout()
        title_label = QLabel("Controle de Contratos")
        title_font = QFont()
        title_font.setPointSize(16)
        title_label.setFont(title_font)

        image_label = QLabel()
        pixmap = QPixmap(str(IMAGE_PATH / "titulo360superior.png"))
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(image_label)

        self.layout.addLayout(header_layout)

    def setup_tree_view(self):
        self.tree_view = QTreeView(self)
        self.tree_view.setStyleSheet("""
            QTreeView::item:hover { background-color: transparent; }
            QTreeView::item:selected { background-color: transparent; }
        """)
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.layout.addWidget(self.tree_view)

        font = QFont()
        font.setPointSize(14)
        self.tree_view.setFont(font)

    def load_data(self):
        try:
            conn = self.database_manager.connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM controle_contratos")
            results = cursor.fetchall()

            col_names = [desc[0] for desc in cursor.description]

            if results:
                df = pd.DataFrame(results, columns=col_names)
                print("Dados retornados do banco de dados:")
                print(df)
                return df
            return pd.DataFrame(columns=col_names)
        except Exception as e:
            logging.error("Erro ao carregar dados do banco de dados: %s", e)
            Dialogs.warning(self, "Erro", f"Erro ao carregar dados do banco de dados: {e}")
            return pd.DataFrame()
        finally:
            self.database_manager.close_connection()

    def update_assinatura_contrato(self, numero_contrato, assinatura_contrato):
        try:
            if self.database_manager_assinatura.connection:
                print("Conexão aberta encontrada. Fechando conexão...")
                self.database_manager_assinatura.close_connection()
            else:
                print("Nenhuma conexão aberta encontrada.")
            
            conn = self.database_manager_assinatura.connect_to_database()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO controle_assinaturas (numero_contrato, assinatura_contrato) 
                VALUES (?, ?)
                ON CONFLICT(numero_contrato) 
                DO UPDATE SET assinatura_contrato = ?
            """, (numero_contrato, assinatura_contrato, assinatura_contrato))
            conn.commit()
            print(f"Assinatura atualizada com sucesso para {numero_contrato}: {assinatura_contrato}")
        except sqlite3.Error as e:
            logging.error(f"Erro ao atualizar assinatura_contrato no banco de dados: {e}")
            Dialogs.warning(self, "Erro", f"Erro ao atualizar assinatura_contrato no banco de dados: {e}")
        finally:
            self.database_manager_assinatura.close_connection()

    def populate_tree_view(self, data):
        unique_combinations = self.organize_data(data)
        self.create_tree_items(unique_combinations)

    def organize_data(self, data):
        unique_combinations = {}
        parent_status = {}

        for index, row in data.iterrows():
            try:
                tipo = row.iloc[5] if len(row) > 5 else "Desconhecido"
                if tipo != "Contrato":
                    continue

                uasg = str(row.iloc[10]) if len(row) > 10 else "Desconhecido"
                try:
                    if '.' in uasg:
                        uasg = uasg.split('.')[0]
                except Exception as e:
                    logging.error(f"Erro ao formatar UASG na linha {index}: {e}")
                
                id_processo = row.iloc[6] if len(row) > 6 else "Desconhecido"
                numero_contrato = row.iloc[4] if len(row) > 4 else "Desconhecido"
                empresa = row.iloc[7] if len(row) > 7 else "Desconhecido"
                objeto = row.iloc[8] if len(row) > 8 else "Desconhecido"
                valor_global = row.iloc[9] if len(row) > 9 else "Desconhecido"
                link_pncp = row.iloc[18] if len(row) > 18 else "Desconhecido"
                checked, assinatura_contrato = self.check_initial_status(numero_contrato)

                parent_text = f"{id_processo} (UASG: {uasg})"
                if parent_text not in unique_combinations:
                    unique_combinations[parent_text] = []
                    parent_status[parent_text] = {"Sim": 0, "Não": 0}

                icon = self.icon_existe if assinatura_contrato == "Sim" else self.icon_nao_existe
                child_text = f"{numero_contrato} - {empresa}"
                unique_combinations[parent_text].append((icon, child_text, objeto, valor_global, link_pncp, assinatura_contrato, numero_contrato))

                if assinatura_contrato == "Sim":
                    parent_status[parent_text]["Sim"] += 1
                else:
                    parent_status[parent_text]["Não"] += 1

            except Exception as e:
                logging.error(f"Erro ao acessar índices da linha {index}: {e}")
                print(f"Erro ao acessar índices da linha {index}: {e}")
                continue
        
        for parent_text, status in parent_status.items():
            if status["Não"] == 0:
                parent_icon = self.icon_existe
            elif status["Sim"] == 0:
                parent_icon = self.icon_nao_existe
            else:
                parent_icon = self.icon_alert
            unique_combinations[parent_text] = (parent_icon, unique_combinations[parent_text])

        return unique_combinations

    def create_tree_items(self, unique_combinations):
        parent_font = QFont()
        parent_font.setPointSize(14)
        child_font = QFont()
        child_font.setPointSize(12)

        for parent_text, (parent_icon, children) in unique_combinations.items():
            parent_item = QStandardItem(parent_icon, parent_text)
            parent_item.setFont(parent_font)

            # Contadores
            sim_count = sum(1 for _, _, _, _, _, assinatura_contrato, _ in children if assinatura_contrato == "Sim")
            nao_count = sum(1 for _, _, _, _, _, assinatura_contrato, _ in children if assinatura_contrato == "Não")
            tram_count = sum(1 for _, _, _, _, _, assinatura_contrato, _ in children if assinatura_contrato in ["Gestor", "Empresa", "Ordenador de Despesas"])
            total_atas = len(children)
            
            # Texto do contador
            contador_text = f"Total de Contratos: {total_atas}\nContratos assinados: {sim_count}\nContratos não assinados: {nao_count}\nnContratos em tramitação: {tram_count}"
            contador_item = QStandardItem(contador_text)
            contador_item.setFont(child_font)
            parent_item.appendRow(contador_item)

            for icon, child_text, _, _, _, assinatura_contrato, numero_contrato in children:
                child_item = QStandardItem(icon, child_text)
                child_item.setFont(child_font)

                # Criar e adicionar o widget de assinatura
                assinatura_widget = self.create_assinatura_widget(assinatura_contrato, numero_contrato, child_item)
                child_item.appendRow(QStandardItem())
                self.tree_view.setIndexWidget(self.model.indexFromItem(child_item.child(child_item.rowCount() - 1)), assinatura_widget)
                    
                parent_item.appendRow(child_item)

            self.model.appendRow(parent_item)
        self.model.setHorizontalHeaderLabels(["Atas de Registro de Preços"])

    def create_assinatura_widget(self, assinatura_contrato, numero_contrato, item):
        _, assinatura_contrato = self.check_initial_status(numero_contrato)
        assinatura_widget = QWidget()
        assinatura_layout = QVBoxLayout()
        assinatura_layout.setContentsMargins(0, 0, 0, 0)
        
        assinatura_label = QLabel("Assinatura:")
        assinatura_nao = QRadioButton("Não")
        assinatura_empresa = QRadioButton("Empresa")
        assinatura_gestor = QRadioButton("Gestor")
        assinatura_ordenador = QRadioButton("Ordenador de Despesas")
        assinatura_sim = QRadioButton("Sim")
        
        font = QFont()
        font.setPointSize(12)
        assinatura_label.setFont(font)
        assinatura_nao.setFont(font)
        assinatura_empresa.setFont(font)
        assinatura_gestor.setFont(font)
        assinatura_ordenador.setFont(font)
        assinatura_sim.setFont(font)
        
        if assinatura_contrato == "Ordenador de Despesas":
            assinatura_ordenador.setChecked(True)
            item.setIcon(QIcon(str(self.icons_dir / "alert.png")))  # Ícone específico
        elif assinatura_contrato == "Empresa":
            assinatura_empresa.setChecked(True)
            item.setIcon(QIcon(str(self.icons_dir / "alert.png")))  # Ícone específico
        elif assinatura_contrato == "Gestor":
            assinatura_gestor.setChecked(True)
            item.setIcon(QIcon(str(self.icons_dir / "alert.png")))  # Ícone específico
        elif assinatura_contrato == "Sim":
            assinatura_sim.setChecked(True)
            item.setIcon(self.icon_existe)
        else:
            assinatura_nao.setChecked(True)
            item.setIcon(self.icon_nao_existe)
        
        assinatura_layout.addWidget(assinatura_label)
        assinatura_layout.addWidget(assinatura_nao)
        assinatura_layout.addWidget(assinatura_empresa)
        assinatura_layout.addWidget(assinatura_gestor)
        assinatura_layout.addWidget(assinatura_ordenador)
        assinatura_layout.addWidget(assinatura_sim)
        assinatura_layout.addStretch()
        assinatura_widget.setLayout(assinatura_layout)
        
        assinatura_nao.toggled.connect(partial(self.update_icon_and_db, item, "Não", numero_contrato))
        assinatura_empresa.toggled.connect(partial(self.update_icon_and_db, item, "Empresa", numero_contrato))
        assinatura_gestor.toggled.connect(partial(self.update_icon_and_db, item, "Gestor", numero_contrato))
        assinatura_ordenador.toggled.connect(partial(self.update_icon_and_db, item, "Ordenador de Despesas", numero_contrato))
        assinatura_sim.toggled.connect(partial(self.update_icon_and_db, item, "Sim", numero_contrato))

        return assinatura_widget

    def update_icon_and_db(self, item, assinatura_contrato, numero_contrato):
        self.update_assinatura_contrato(numero_contrato, assinatura_contrato)
        if assinatura_contrato == "Ordenador de Despesas":
            icon = QIcon(str(self.icons_dir / "alert.png"))  # Ícone específico
        elif assinatura_contrato == "Empresa":
            icon = QIcon(str(self.icons_dir / "alert.png"))  # Ícone específico
        elif assinatura_contrato == "Gestor":
            icon = QIcon(str(self.icons_dir / "alert.png"))  # Ícone específico
        elif assinatura_contrato == "Sim":
            icon = self.icon_existe
        else:
            icon = self.icon_nao_existe
        item.setIcon(icon)
        
        # Atualizar ícone do parent
        parent_item = item.parent()
        if parent_item:
            sim_count = 0
            nao_count = 0
            tram_count = 0
            total_atas = 0
            for row in range(1, parent_item.rowCount()):  # Começamos de 1 para pular o contador
                child_item = parent_item.child(row)
                child_icon = child_item.icon()
                
                # Verifica o status do ícone para determinar a contagem
                if child_icon.cacheKey() == self.icon_existe.cacheKey():
                    sim_count += 1
                elif child_icon.cacheKey() == self.icon_nao_existe.cacheKey():
                    nao_count += 1
                
                # Conta as atas em tramitação com base no status
                child_status = self.get_assinatura_status(child_item)
                if child_status in ["Empresa", "Gestor", "Ordenador de Despesas"]:
                    tram_count += 1

                # Independente do status, soma ao total_atas
                total_atas += 1

            if nao_count == 0:
                parent_icon = self.icon_existe
            elif sim_count == 0:
                parent_icon = self.icon_nao_existe
            else:
                parent_icon = self.icon_alert

            parent_item.setIcon(parent_icon)
            
            # Atualizar o contador
            contador_text = f"Total de Contratos: {total_atas}\nContratos assinados: {sim_count}\nContratos não assinados: {nao_count}\nnContratos em tramitação: {tram_count}"
            contador_item = parent_item.child(0)
            contador_item.setText(contador_text)

    def get_assinatura_status(self, item):
        """Retorna o status atual da assinatura (Empresa, Gestor, Ordenador de Despesas, Sim, Não)."""
        assinatura_widget = self.tree_view.indexWidget(self.model.indexFromItem(item.child(item.rowCount() - 1)))
        if assinatura_widget is not None:
            for radio_button in assinatura_widget.findChildren(QRadioButton):
                if radio_button.isChecked():
                    return radio_button.text()
        return "Não"

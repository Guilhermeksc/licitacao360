# modules/menu_superior/config/config_database.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QMessageBox, QScrollArea
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from pathlib import Path
import json
import openpyxl
import os

from diretorios import *
from database.utils.treeview_utils import load_images

class ConfigurarDatabaseDialog(QDialog):
    controle_dados_dir_updated = pyqtSignal(Path)

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.database_path = Path(CONTROLE_DADOS)
        self.config_file = CONFIG_FILE
        self.icons_dir = Path(ICONS_DIR)
        self.image_cache = self._load_images()
        self.pasta_base = Path(self._load_config('save_location', str(Path.home() / 'Desktop')))
        self.parent_app = parent
        self.setWindowTitle("Configurações")
        self.setFixedSize(800, 650)
        self.directory_labels = {}

        self.global_to_module_map = self._create_global_to_module_map()

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self._create_title_layout())

        modules = [
            ("Planejamento de Licitações", self.update_controle_processos_dir),
            ("Dados PNCP", self.update_controle_atas_dir),
            ("Contratos", self.update_controle_contratos_dir),
            ("Dispensa Eletrônica", self.update_controle_contratacoes_diretas_dir),
        ]

        for module_name, callback in modules:
            main_layout.addWidget(self._create_module_group_box(module_name, callback))

    def _load_images(self):
        return load_images(self.icons_dir, ["database.png", "excel_up.png", "excel_down.png", "folder128.png"])

    def _create_global_to_module_map(self):
        return {
            "CONTROLE_DADOS": "Planejamento de Licitações",
            "CONTROLE_DADOS_PNCP": "Dados PNCP",
            "CONTROLE_CONTRATOS": "Contratos",
            "CONTROLE_CONTRATACAO_DIRETAS": "Dispensa Eletrônica",
        }

    def _create_module_group_box(self, module_name, update_callback):
        group_box = QGroupBox(f"Módulo {module_name}")
        group_box.setFont(self._get_title_font())
        group_box.setStyleSheet("QGroupBox::title { padding-top: -15px; }")

        layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        button_layout.addLayout(self._create_label_button_layout("Selecionar arquivo .db", "database.png", update_callback))
        button_layout.addLayout(self._create_label_button_layout("Gerar Tabela Vazia", "excel_down.png", lambda: self.generate_empty_table(module_name)))
        button_layout.addLayout(self._create_label_button_layout("Importar Tabela", "excel_up.png"))
        current_directory = self.get_directory_for_module(module_name)
        button_layout.addLayout(self._create_label_button_layout("Abrir Pasta", "folder128.png", lambda: self.open_directory(current_directory)))

        layout.addLayout(button_layout)
        layout.addWidget(self._create_directory_label(current_directory, module_name))

        group_box.setLayout(layout)
        return group_box

    def _create_directory_label(self, current_directory, module_name):
        title_label = QLabel("Diretório atual:")
        title_label.setFont(self._get_title_font(12))

        directory_label = QLabel(str(current_directory))
        directory_label.setFont(self._get_title_font(12))
        self.directory_labels[module_name] = directory_label

        scroll_area = QScrollArea()
        scroll_area.setWidget(directory_label)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFixedHeight(40)

        # Retorne o QScrollArea diretamente, que é um QWidget
        return scroll_area

    def _create_label_button_layout(self, label_text, icon_name, callback=None):
        layout = QHBoxLayout()

        label = QLabel(label_text)
        label.setFixedHeight(30)
        label.setFont(self._get_title_font(12))

        button = QPushButton()
        icon = self.image_cache.get(icon_name.split('.')[0])
        if icon:
            button.setIcon(icon)
        icon_size = QSize(40, 40)
        button.setIconSize(icon_size)
        button.setFixedSize(icon_size)

        if callback:
            button.clicked.connect(callback)

        layout.addWidget(label)
        layout.addWidget(button)
        layout.addStretch()
        return layout

    def _create_title_layout(self):
        layout = QHBoxLayout()
        icon_label = QLabel()
        icon = self.image_cache.get('database')
        if icon:
            icon_label.setPixmap(icon.pixmap(64, 64))
        title_label = QLabel("Gerenciador de Dados")
        title_label.setFont(self._get_title_font(30, bold=True))
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        return layout

    def _get_title_font(self, size=14, bold=False):
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def _load_config(self, key, default_value):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            return config.get(key, default_value)
        except (FileNotFoundError, json.JSONDecodeError):
            return default_value

    def get_directory_for_module(self, module_name):
        directories = {
            "Planejamento de Licitações": CONTROLE_DADOS,
            "Dados PNCP": CONTROLE_DADOS_PNCP,
            "Contratos": CONTROLE_CONTRATOS_DADOS,
            "Dispensa Eletrônica": CONTROLE_CONTRATACAO_DIRETAS,
        }
        return directories.get(module_name, "Diretório não encontrado")

    def open_directory(self, file_path):
        try:
            directory_path = file_path.parent
            os.startfile(directory_path)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir a pasta: {str(e)}")

    def generate_empty_table(self, module_name):
        table_definitions = {
            "Planejamento de Licitações": ("planejamento.xlsx", ["ID", "Nome", "Data"]),
            "Atas": ("atas.xlsx", ["ID", "Número da Ata", "Data"]),
            "Contratos": ("contratos.xlsx", ["ID", "Número do Contrato", "Valor"]),
            "Dispensa Eletrônica": ("dispensa.xlsx", ["ID", "Descrição", "Valor"]),
        }

        if module_name not in table_definitions:
            QMessageBox.warning(self, "Erro", f"Definição de tabela não encontrada para o módulo: {module_name}")
            return

        file_name, columns = table_definitions[module_name]
        file_path = self.pasta_base / file_name

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = module_name

        for col_num, column_title in enumerate(columns, start=1):
            sheet.cell(row=1, column=col_num, value=column_title)

        workbook.save(file_path)
        QMessageBox.information(self, "Sucesso", f"Tabela '{file_name}' criada com sucesso no módulo '{module_name}'.")

        os.startfile(file_path)

    def update_controle_processos_dir(self):
        self._update_directory("CONTROLE_DADOS", "Selecione o novo arquivo para CONTROLE_DADOS")

    def update_controle_atas_dir(self):
        self._update_directory_pncp("CONTROLE_DADOS_PNCP", "Selecione o novo arquivo para CONTROLE_DADOS_PNCP")

    def update_controle_contratos_dir(self):
        self._update_directory("CONTROLE_CONTRATOS", "Selecione o novo arquivo para CONTROLE_CONTRATOS")

    def update_controle_contratacoes_diretas_dir(self):
        self._update_directory("CONTROLE_CONTRATACAO_DIRETAS", "Selecione o novo arquivo para CONTROLE_CONTRATACAO_DIRETAS")

    def _update_directory(self, global_var_name, dialog_title):
        new_file = update_file_path(dialog_title, global_var_name, globals()[global_var_name], self, "Database files (*.db)")
        if new_file != globals()[global_var_name]:
            if self._confirm_update(global_var_name, new_file):
                globals()[global_var_name] = new_file
                global_event_manager.update_controle_dados_dir(new_file)
                self._show_success_dialog(new_file)

                module_name = self.global_to_module_map.get(global_var_name)
                if module_name:
                    self.directory_labels[module_name].setText(str(new_file))

    def _update_directory_pncp(self, global_var_name, dialog_title):
        new_file = update_file_path(dialog_title, global_var_name, globals()[global_var_name], self, "Database files (*.db)")
        if new_file != globals()[global_var_name]:
            if self._confirm_update(global_var_name, new_file):
                globals()[global_var_name] = new_file
                global_event_manager.update_controle_dados_pncp_dir(new_file)
                self._show_success_dialog(new_file)

                module_name = self.global_to_module_map.get(global_var_name)
                if module_name:
                    self.directory_labels[module_name].setText(str(new_file))

    def _confirm_update(self, old_value, new_value):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle('Alteração de diretório')
        msgBox.setText(f'Diretório antigo:\n{old_value}\nDiretório atualizado:\n{new_value}\n\nDeseja alterar?')
        msgBox.setIcon(QMessageBox.Icon.Question)
        msgBox.addButton("Sim", QMessageBox.ButtonRole.YesRole)
        msgBox.addButton("Não", QMessageBox.ButtonRole.NoRole)
        msgBox.exec()
        return msgBox.clickedButton().text() == "Sim"

    def _show_success_dialog(self, new_file):
        successBox = QMessageBox(self)
        successBox.setWindowTitle('Alteração realizada com sucesso!')
        successBox.setText(f'Diretório atualizado:\n{new_file}')
        successBox.setIcon(QMessageBox.Icon.Information)
        successBox.exec()

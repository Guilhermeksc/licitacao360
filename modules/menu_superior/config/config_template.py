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

class TemplatesDialog(QDialog):
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
        self.setWindowTitle("Templates")
        self.setFixedSize(800, 650)
        self.directory_labels = {}

        self.global_to_module_map = self._create_global_to_module_map()

        self._setup_ui()

    def _create_module_group_box(self, module_name, callback):
        """
        Cria um QGroupBox para um módulo específico, incluindo o rótulo do diretório atual e um botão para atualizar o diretório.
        """
        group_box = QGroupBox(module_name)
        group_box_layout = QVBoxLayout()

        # Obtém o diretório atual associado ao módulo
        current_directory = self.get_directory_for_module(module_name)

        # Cria o layout para o rótulo e o botão
        label_button_layout = self._create_label_button_layout(f"Diretório {module_name}", "folder128.png", callback)

        # Adiciona o layout do rótulo e botão ao layout do QGroupBox
        group_box_layout.addLayout(label_button_layout)

        # Adiciona o QScrollArea com o rótulo do diretório ao layout do QGroupBox
        directory_label = self._create_directory_label(current_directory, module_name)
        group_box_layout.addWidget(directory_label)

        group_box.setLayout(group_box_layout)
        return group_box
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self._create_title_layout())

        modules = [
            ("Templates", self.update_template_dir),
        ]

        for module_name, callback in modules:
            main_layout.addWidget(self._create_module_group_box(module_name, callback))

    def _load_images(self):
        return load_images(self.icons_dir, ["templates.png", "folder128.png"])

    def _create_global_to_module_map(self):
        return {
            "PASTA_TEMPLATE": "Templates",
        }

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
            "Templates": PASTA_TEMPLATE,
        }
        return directories.get(module_name, "Diretório não encontrado")

    def open_directory(self, file_path):
        try:
            directory_path = file_path.parent
            os.startfile(directory_path)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir a pasta: {str(e)}")

    # Atualize a função update_template_dir na classe TemplatesDialog
    def update_template_dir(self):
        """
        Chama a função update_template_directory do diretorios.py para atualizar o diretório.
        """
        update_template_directory(self)
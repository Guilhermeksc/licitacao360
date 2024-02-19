#utils_contratos.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import numpy as np
import pandas as pd
import re
from diretorios import *
from datetime import datetime

class ConfiguracoesDialog(QDialog):
    COLUMN_OFFSET = 2
    SETTINGS_KEY = "ConfiguracoesDialog/ColumnVisibility"

    def __init__(self, colunas, tree_view, parent=None):
        super().__init__(parent)
        self.tree_view = tree_view
        self.colunas = colunas
        self.setWindowTitle("Configurações de Colunas")
        self.layout = QVBoxLayout(self)

        self.initUI()  # Inicializa a interface do usuário
        self.load_settings()  # Carrega as configurações salvas

    def initUI(self):
        """Inicializa os componentes da interface do usuário."""
        # Botões para configurações pré-definidas
        self.initPredefinedConfigButtons()

        # QListWidget para seleção personalizada das colunas
        self.initListWidget()

        # Botão de aplicar configurações personalizadas
        self.btn_apply_custom = QPushButton("Aplicar Configuração Personalizada", self)
        self.btn_apply_custom.clicked.connect(self.apply_custom_config)
        self.layout.addWidget(self.btn_apply_custom)

    def initPredefinedConfigButtons(self):
        """Inicializa os botões para as configurações pré-definidas."""
        self.btn_modulo_gestor_fiscal = QPushButton("Módulo Gestor/Fiscal", self)
        self.btn_modulo_gestor_fiscal.clicked.connect(self.apply_gestor_fiscal_config)
        self.layout.addWidget(self.btn_modulo_gestor_fiscal)

        self.btn_modulo_renovacao_contratos = QPushButton("Módulo Renovação de Contratos", self)
        self.btn_modulo_renovacao_contratos.clicked.connect(self.apply_renovacao_contratos_config)
        self.layout.addWidget(self.btn_modulo_renovacao_contratos)

        self.btn_show_all_columns = QPushButton("Mostrar todas as colunas", self)
        self.btn_show_all_columns.clicked.connect(self.show_all_columns)
        self.layout.addWidget(self.btn_show_all_columns)

    def initListWidget(self):
        """Inicializa o QListWidget para seleção personalizada das colunas."""
        self.list_widget = QListWidget(self)
        self.populate_list_widget(self.colunas, self.tree_view)
        self.layout.addWidget(self.list_widget)

    def apply_gestor_fiscal_config(self):
        indices = [1, 2, 3, 5, 6, 7, 8, 9, 14, 15, 16, 17, 18]
        self.apply_column_visibility(indices)
        self.save_settings(indices)

    def apply_renovacao_contratos_config(self):
        indices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.apply_column_visibility(indices)
        self.save_settings(indices)

    def apply_column_visibility(self, visible_indices):
        for i in range(self.tree_view.model().columnCount()):
            self.tree_view.setColumnHidden(i, i + self.COLUMN_OFFSET not in visible_indices)

    def apply_custom_config(self):
        """Aplica a configuração personalizada selecionada pelo usuário."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            is_visible = item.checkState() == Qt.CheckState.Checked
            column_index = item.data(Qt.ItemDataRole.UserRole)
            self.tree_view.setColumnHidden(column_index, not is_visible)
        # Não esqueça de salvar a configuração personalizada após aplicá-la
        self.save_custom_config()

    def save_custom_config(self):
        """Salva as configurações personalizadas do usuário."""
        selected_indices = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                column_index = item.data(Qt.ItemDataRole.UserRole)
                selected_indices.append(column_index - self.COLUMN_OFFSET)  # Ajuste conforme necessário
        # Salva os índices das colunas visíveis como configuração personalizada
        settings = QSettings()
        settings.setValue(self.SETTINGS_KEY, selected_indices)

    def save_settings(self, visible_indices):
        settings = QSettings()
        settings.setValue(self.SETTINGS_KEY, visible_indices)

    def load_settings(self):
        settings = QSettings()
        if settings.contains(self.SETTINGS_KEY):
            visible_indices = settings.value(self.SETTINGS_KEY, type=list)
            self.apply_column_visibility(visible_indices)
        else:
            self.apply_column_visibility(range(len(self.colunas)))  # Mostra todas as colunas por padrão

    def show_all_columns(self):
        # Atualiza todos os itens na lista para o estado marcado (Checked)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.CheckState.Checked)
        
        # Atualiza a visibilidade de todas as colunas para visível
        for i in range(self.tree_view.model().columnCount()):
            self.tree_view.setColumnHidden(i + self.COLUMN_OFFSET, False)
        
        # Salva a configuração de todas as colunas visíveis
        self.save_settings(list(range(len(self.colunas))))

    def populate_list_widget(self, colunas, tree_view):
        for index, coluna in enumerate(colunas):
            item = QListWidgetItem(coluna)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if not tree_view.isColumnHidden(index + self.COLUMN_OFFSET) else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, index + self.COLUMN_OFFSET)
            self.list_widget.addItem(item)

    def aplicarConfiguracoes(self):
        selected_indices = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            column_index = item.data(Qt.ItemDataRole.UserRole)
            is_checked = item.checkState() == Qt.CheckState.Checked
            self.tree_view.setColumnHidden(column_index - self.COLUMN_OFFSET, not is_checked)
            if is_checked:
                selected_indices.append(column_index - self.COLUMN_OFFSET)
        self.save_settings(selected_indices)
        self.accept()

class MSGAlertaPrazo(QDialog):
    def __init__(self, detalhes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mensagem Cobrança")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # Campo de texto editável
        self.textEdit = QTextEdit()
        self.textEdit.setText(detalhes)
        self.textEdit.setReadOnly(False)  # Se desejar que o texto seja editável, defina como False
        layout.addWidget(self.textEdit)

        # Botão para copiar o texto para a área de transferência
        self.btnCopy = QPushButton("Copiar", self)
        self.btnCopy.clicked.connect(self.copyTextToClipboard)
        layout.addWidget(self.btnCopy)

    def copyTextToClipboard(self):
        text = self.textEdit.toPlainText()
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", "Texto copiado para a área de transferência.")

class NumeroCPDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Número da CP")
        self.layout = QVBoxLayout(self)

        self.label = QLabel("Informe o número da próxima CP:")
        self.layout.addWidget(self.label)

        self.lineEdit = QLineEdit(self)
        self.layout.addWidget(self.lineEdit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def getNumeroCP(self):
        return self.lineEdit.text()
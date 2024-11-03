from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame
from PyQt6.QtCore import pyqtSignal
import pandas as pd
import sqlite3
from pathlib import Path

class AgentesResponsaveisWidget(QFrame):
    """
    Widget responsável por configurar e gerenciar o layout e dados dos agentes responsáveis.
    """
    def __init__(self, database_path, registro_selecionado, parent=None):
        super().__init__(parent)
        self.database_path = database_path
        self.registro_selecionado = registro_selecionado

        # Inicialização dos ComboBoxes
        self.ordenador_combo = self.create_combo_box()
        self.agente_fiscal_combo = self.create_combo_box()
        self.gerente_credito_combo = self.create_combo_box()
        self.responsavel_demanda_combo = self.create_combo_box()
        self.operador_dispensa_combo = self.create_combo_box()

        # Configuração do layout do widget
        self.init_ui()
        self.carregarAgentesResponsaveis()

    def init_ui(self):
        # Layout principal para agentes responsáveis
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 1, 10, 1)  # Define margens ao redor do layout

        # Criação de labels e ComboBoxes
        labels_combos = [
            ("Ordenador de Despesa:", self.ordenador_combo),
            ("Agente Fiscal:", self.agente_fiscal_combo),
            ("Gerente de Crédito:", self.gerente_credito_combo),
            ("Responsável pela Demanda:", self.responsavel_demanda_combo),
            ("Operador da Contratação:", self.operador_dispensa_combo)
        ]

        # Adicionando cada label e combo box ao layout
        for label_text, combo_box in labels_combos:
            v_layout = QVBoxLayout()
            label = QLabel(label_text)
            label.setStyleSheet("color: #8AB4F7; font-size: 16px")
            v_layout.addWidget(label)
            v_layout.addWidget(combo_box)
            layout.addLayout(v_layout)

    def create_combo_box(self, placeholder='', width=260, height=70):
        combo_box = QComboBox()
        combo_box.setEditable(True)
        combo_box.setPlaceholderText(placeholder)
        combo_box.setFixedWidth(width)
        combo_box.setFixedHeight(height)
        return combo_box

    def carregarAgentesResponsaveis(self):
        try:
            print("Tentando conectar ao banco de dados...")
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()

                # Verificar se a tabela existe
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_agentes_responsaveis'")
                if cursor.fetchone() is None:
                    raise Exception("A tabela 'controle_agentes_responsaveis' não existe no banco de dados. Configure os Ordenadores de Despesa no Módulo 'Configurações'.")

                print("Tabela 'controle_agentes_responsaveis' encontrada. Carregando dados...")

                # Carregar dados para cada ComboBox com base na função específica
                self.carregarDadosCombo(conn, cursor, "Ordenador de Despesa%", self.ordenador_combo)
                self.carregarDadosCombo(conn, cursor, "Agente Fiscal%", self.agente_fiscal_combo)
                self.carregarDadosCombo(conn, cursor, "Gerente de Crédito%", self.gerente_credito_combo)
                self.carregarDadosCombo(conn, cursor, "Operador%", self.operador_dispensa_combo)
                self.carregarDadosCombo(conn, cursor, "NOT LIKE", self.responsavel_demanda_combo)

                # Preencher ComboBoxes com valores do registro selecionado
                self.preencher_campos()

        except Exception as e:
            print(f"Erro ao carregar Ordenadores de Despesas: {e}")

    def carregarDadosCombo(self, conn, cursor, funcao_like, combo_widget):
        """
        Função para carregar dados no combobox baseado na função especificada.
        """
        if "NOT LIKE" in funcao_like:
            sql_query = """
                SELECT nome, posto, funcao FROM controle_agentes_responsaveis
                WHERE funcao NOT LIKE 'Ordenador de Despesa%' AND
                    funcao NOT LIKE 'Agente Fiscal%' AND
                    funcao NOT LIKE 'Gerente de Crédito%' AND
                    funcao NOT LIKE 'Operador%'
            """
        else:
            sql_query = f"SELECT nome, posto, funcao FROM controle_agentes_responsaveis WHERE funcao LIKE '{funcao_like}'"
        
        agentes_df = pd.read_sql_query(sql_query, conn)
        combo_widget.clear()
        for _, row in agentes_df.iterrows():
            texto_display = f"{row['nome']}\n{row['posto']}\n{row['funcao']}"
            combo_widget.addItem(texto_display, userData=row.to_dict())

    def preencher_campos(self):
        """
        Função para preencher os ComboBoxes com os valores do registro selecionado.
        """
        try:
            # Verifica se `registro_selecionado` é uma lista e utiliza índices
            if isinstance(self.registro_selecionado, list):
                self.ordenador_combo.setCurrentText(str(self.registro_selecionado[0]))  # Ajuste o índice conforme o layout da lista
                self.agente_fiscal_combo.setCurrentText(str(self.registro_selecionado[1]))  # Ajuste conforme o índice
                self.gerente_credito_combo.setCurrentText(str(self.registro_selecionado[2]))
                self.responsavel_demanda_combo.setCurrentText(str(self.registro_selecionado[3]))
                self.operador_dispensa_combo.setCurrentText(str(self.registro_selecionado[4]))

        except IndexError as e:
            print(f"Erro ao preencher campos: índice fora do intervalo - {str(e)}")


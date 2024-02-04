import sys
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QInputDialog, QDialog, QLabel, QTableView, 
    QLineEdit, QPushButton, QHeaderView, QComboBox, QMessageBox,
    QHBoxLayout, QListWidget, QFileDialog, QTableWidgetItem, QTableWidget,
    QToolButton, QStyledItemDelegate, QCalendarWidget, QSizePolicy
)
from PyQt6.QtCore import QAbstractTableModel, Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPixmap, QBrush, QColor
from diretorios import *
import os
from docxtpl import DocxTemplate
import pandas as pd
import sqlite3

from styles.styless import get_transparent_title_style

df_uasg = pd.read_excel(TABELA_UASG_DIR)
global df_registro_selecionado
df_registro_selecionado = None

nomes_pregoeiros = None

class CenterIconDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if icon:
            pixmap_size = QSize(30, 30)  # Tamanho padrão, ajuste conforme necessário
            pixmap = icon.pixmap(icon.actualSize(pixmap_size))

            # Calculando as coordenadas para centralizar o ícone
            x = option.rect.center().x() - pixmap.width() / 2 + 10  # Adiciona 2 pixels à direita
            y = option.rect.center().y() - pixmap.height() / 2 + 6  # Adiciona 2 pixels para baixo

            # Arredonda as coordenadas para evitar problemas com tipos de dados
            x = round(x)
            y = round(y)

            painter.drawPixmap(x, y, pixmap)
        else:
            super().paint(painter, option, index)

class TableModel(QAbstractTableModel):
    def __init__(self, nomes_pregoeiros, filepath):
        super().__init__()
        self.nomes_pregoeiros = nomes_pregoeiros
        self.processos_info = []
        self.load_processos_from_excel(filepath)

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            column = index.column()
            pregoeiro = self.nomes_pregoeiros[row]

            if column == 0:
                return None  # Retorna None para a coluna oculta
            pregoeiro = self.nomes_pregoeiros[row]
            return '' if column in pregoeiro["processos_escalados"] else ''

        elif role == Qt.ItemDataRole.DecorationRole:
            row = index.row()
            column = index.column()
            pregoeiro = self.nomes_pregoeiros[row]

            # Suponha que processos_escalados seja uma lista de números de colunas
            if column in pregoeiro["processos_escalados"]:
                icon_path = ICONS_DIR / "select_2.svg"  # Caminho do ícone
                return QIcon(QPixmap(str(icon_path)))

            # Caso não haja ícone para a célula atual, retorne None
            return None

        return None
    
    def rowCount(self, index):
        return len(self.nomes_pregoeiros)

    def columnCount(self, index):
        return len(self.processos_info) + 1  # Adiciona 1 para a coluna extra

    def load_processos_from_excel(self, filepath):
        df = pd.read_excel(filepath)
        self.processos_info = list(zip(df['num_pregao'], df['ano_pregao'], df['objeto']))  # Inclua 'objeto'

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Vertical:
            if section < len(self.nomes_pregoeiros):
                pregoeiro = self.nomes_pregoeiros[section]

                if role == Qt.ItemDataRole.DisplayRole:
                    nome_com_impedimento = pregoeiro["nome"]
                    impedimento = pregoeiro.get("impedimento")
                    if impedimento:
                        nome_com_impedimento += f" ({impedimento})"
                    return nome_com_impedimento
                
                elif role == Qt.ItemDataRole.ForegroundRole:
                    if pregoeiro.get("impedimento"):
                        return QBrush(QColor("red"))

        elif orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                if section == 0:
                    return ""  # Coluna adicional, sem dados correspondentes
                elif section <= len(self.processos_info):
                    num_pregao, ano_pregao, objeto = self.processos_info[section - 1]
                    return f"{num_pregao}\n{ano_pregao}"
                else:
                    return "Sem Dados"

        return None
    
class PregoeiroWidget(QWidget):
    itemSelected = pyqtSignal(str, str)

    def __init__(self, parent=None, dtypes=None, app=None):
        super().__init__(parent)
        self.app = app
        self.dtypes = dtypes if dtypes is not None else {}
        self.nomes_pregoeiros = self.load_pregoeiros()
        self.processos_pregoeiros = {}
        self.model = None
        self.initialize_model()
        self.setup_ui()
        self.processo_selecionado = None
        self.adjust_column_widths_to_content()


    def _on_item_click(self, index):
        clicked_column = index.column()

        # Certifique-se de que não estamos lidando com a coluna oculta
        if clicked_column > 0:
            # Obtendo o cabeçalho da coluna clicada
            header_value = self.model.headerData(clicked_column, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            
            # Dividindo os valores de num_pregao e ano_pregao
            if header_value and "\n" in header_value:
                num_pregao, ano_pregao = header_value.split("\n")
                print(f"Emitindo sinal para PE {num_pregao}/{ano_pregao}")
                self.itemSelected.emit(num_pregao, ano_pregao)

                # Chama o método para processar e salvar o item selecionado
                self._process_selected_item([num_pregao, ano_pregao])

    def _get_selected_item_values(self):
        row = self.tree_view.currentIndex().row()
        if row == -1:
            return []  # Nenhuma linha selecionada

        values = []
        for col in range(self.model.columnCount()):
            item = self.model.item(row, col)
            if item is not None:
                values.append(item.text())
            else:
                values.append("")  # Se não houver item, adicione uma string vazia

        return values

    def _process_selected_item(self, selected_values):
        """Process the selected item."""
        # Recarregar os dados mais recentes do arquivo Excel
        self.df_licitacao_completo = pd.read_excel(CONTROLE_PROCESSOS_DIR, dtype=self.dtypes)

        num_pregao, ano_pregao = selected_values[:2] 

        # Filtra o DataFrame completo para encontrar a linha com o num_pregao e ano_pregao correspondentes
        registro_completo = self.df_licitacao_completo[
            (self.df_licitacao_completo['num_pregao'].astype(str).str.strip() == num_pregao) &
            (self.df_licitacao_completo['ano_pregao'].astype(str).str.strip() == ano_pregao)
        ]

        if registro_completo.empty:
            # Se nenhum registro for encontrado, retorne False
            return False

        global df_registro_selecionado  # Declare o uso da variável global
        self.itemSelected.emit(num_pregao, ano_pregao)

        df_registro_selecionado = pd.DataFrame(registro_completo)
        df_registro_selecionado.to_csv(ITEM_SELECIONADO_PATH, index=False, encoding='utf-8-sig')
        print(f"Registro salvo em {ITEM_SELECIONADO_PATH}")
        self.app.pregao_selecionado()

        return True

    def initialize_model(self):
        self.model = TableModel(self.nomes_pregoeiros, CONTROLE_PROCESSOS_DIR)

    def adjust_column_widths_to_content(self):
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def update_model_and_resize(self):
        # Este método pode ser chamado sempre que você atualizar os dados do modelo
        self.model.layoutChanged.emit()
        self.adjust_column_widths_to_content() 

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        label_controle_pregoeiros = QLabel("Controle de Escalação de Pregoeiros")
        label_controle_pregoeiros.setStyleSheet(get_transparent_title_style())
        self.layout.addWidget(label_controle_pregoeiros)
        self.add_table_view()
       
        # Configuração do layout
        self.layout.addWidget(self.tableView)  # Adiciona a tabela diretamente ao layout
        self.add_control_buttons()

    def initialize_model(self):
        self.model = TableModel(self.nomes_pregoeiros, CONTROLE_PROCESSOS_DIR)
        self.model.rowsInserted.connect(self.adjust_table_height)
        self.model.rowsRemoved.connect(self.adjust_table_height)

    def adjust_table_height(self):
        row_count = self.model.rowCount(None)
        header_height = self.tableView.horizontalHeader().height()
        row_height = self.tableView.rowHeight(0) if row_count > 0 else 0
        scrollbar_extra = 20  # Valor extra para acomodar a barra de rolagem

        # Ajuste a altura mínima da tabela para a altura calculada mais o valor extra
        table_height = (row_count * row_height) + header_height + scrollbar_extra
        self.tableView.setMinimumHeight(table_height)
        self.tableView.setMaximumHeight(table_height)

    def add_table_view(self):
        self.tableView = QTableView()
        if self.model:
            self.tableView.setModel(self.model)
            self.tableView.setItemDelegate(CenterIconDelegate())
            
            self.tableView.setAlternatingRowColors(True)

            self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self.tableView.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self.tableView.hideColumn(0)
            self.tableView.clicked.connect(self.on_table_clicked)
            self.tableView.clicked.connect(self._on_item_click)
            self.tableView.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

        # Definindo a política da barra de rolagem para sempre visível
        self.tableView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.tableView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Ajuste da política de tamanho para que a tabela não expanda desnecessariamente
        self.tableView.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        # Calcule a altura necessária para mostrar todas as linhas mais o cabeçalho
        row_count = self.model.rowCount(None)
        header_height = self.tableView.horizontalHeader().height()
        row_height = self.tableView.rowHeight(0)  # Altura de uma linha (assumindo que são todas iguais)
        scrollbar_extra = 20  # Valor extra para acomodar a barra de rolagem

        # Ajuste a altura mínima da tabela para a altura calculada mais o valor extra
        table_height = (row_count * row_height) + header_height + scrollbar_extra
        self.tableView.setMinimumHeight(table_height)
        self.adjust_table_height()

    def add_control_buttons(self):
        titles = ["Escalar Pregoeiro", "Adicionar Pregoeiro", "Alterar Pregoeiro", "Remover Pregoeiro", "Importar Dados de Pregoeiros", "Controle de Escalas", "Reset"]  # Lista de todos os títulos dos botões
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.create_button_pregoeiro("Escalar", self.escalar_funcionario, "recruitment.png"))
        buttons_layout.addWidget(self.create_button_pregoeiro("Adicionar", self.open_add_pregoeiro_dialog, "plus.png"))
        buttons_layout.addWidget(self.create_button_pregoeiro("Alterar", self.alterar_pregoeiro, "switch.png"))
        buttons_layout.addWidget(self.create_button_pregoeiro("Remover ", self.open_remove_pregoeiro_dialog, "delete.png"))
        buttons_layout.addWidget(self.create_button_pregoeiro("Importar", self.importar_dados_pregoeiros, "save_to_drive.png"))
        buttons_layout.addWidget(self.create_button_pregoeiro("Controle", self.show_escala_panel, "search_menu.png"))
        buttons_layout.addWidget(
            self.create_button_pregoeiro("Gerar CP", self.chamar_gerar_documento, "pdf.png")
        )
        buttons_layout.addWidget(self.create_button_pregoeiro("Reset", self.reset_marcadores, "reset.png"))
        buttons_layout.addStretch() 
        # Adiciona o layout horizontal ao layout principal
        self.layout.addLayout(buttons_layout)

    def gerar_documento_pregoeiro(self, template_path, item_selecionado_df, save_path):
        numero_cp = self.obter_numero_cp()
        data_sessao = self.selecionar_data_sessao()

        if numero_cp is None or data_sessao is None:
            print("Número da CP ou data da sessão não fornecidos.")
            return

        # Confirmar a criação do documento
        resposta = QMessageBox.question(self, "Confirmar Criação", 
                                        "Deseja criar um documento com o número de CP " + numero_cp + "?", 
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if resposta == QMessageBox.StandardButton.Yes:
            # Criar o documento e inserir no banco de dados
            self.inserir_novo_documento(numero_cp, item_selecionado_df)

        doc = DocxTemplate(template_path)

        for _, row in item_selecionado_df.iterrows():
            context = {
                'objeto': row['objeto'],
                'num_pregao': row['num_pregao'],
                'ano_pregao': row['ano_pregao'],
                'pregoeiro': row['pregoeiro'],
                'numero_cp': numero_cp,
                'data_sessao': data_sessao
            }
            doc.render(context)

            file_name = f"PE {row['num_pregao']}-{row['ano_pregao']} - Designacao de pregoeiro.docx"
            full_path = save_path / file_name
            doc.save(full_path)

            # # Opcional: Abrir o arquivo
            os.startfile(full_path)

    def inserir_novo_documento(self, numero_cp, item_selecionado_df):
        if not item_selecionado_df.empty:
            num_pregao = item_selecionado_df['num_pregao'].iloc[0]
            ano_pregao = item_selecionado_df['ano_pregao'].iloc[0]

            # Formatar o assunto
            assunto = f"Designação de Pregoeiro para o Pregão Eletrônico {num_pregao}/{ano_pregao}"

            # Supondo que 'destinatario' seja outra coluna que você deseja usar
            # Se não houver essa coluna, você precisará ajustar esta parte
            destinatario = item_selecionado_df.get('destinatario', pd.Series(['']))[0]

            # Conectar ao banco de dados e inserir os dados
            conn = sqlite3.connect('comunicacoes_padronizadas.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO cps (numero, assunto, destinatario) VALUES (?, ?, ?)', 
                           (numero_cp, assunto, destinatario))
            conn.commit()
            conn.close()
        else:
            print("DataFrame está vazio.")

    def obter_numero_cp(self):
        # Sugerir o próximo número de CP disponível
        numero_cp_sugerido = self.app.numerador_cp_widget.proximo_numero_cp()

        numero_cp, ok_pressed = QInputDialog.getText(
            self, "Número da CP", "Digite o número da CP:", text=numero_cp_sugerido
        )
        if ok_pressed and numero_cp != '':
            return numero_cp
        return None

    def selecionar_data_sessao(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Data da Sessão")
        layout = QVBoxLayout(dialog)

        calendario = QCalendarWidget(dialog)
        layout.addWidget(calendario)

        botao_ok = QPushButton("OK", dialog)
        botao_ok.clicked.connect(dialog.accept)
        layout.addWidget(botao_ok)

        dialog.setLayout(layout)
        result = dialog.exec()

        # Usar o valor correto aqui
        if result == QDialog.DialogCode.Accepted:
            return calendario.selectedDate().toString("dd/MM/yyyy")
        return None

    def chamar_gerar_documento(self):
        # Carregar o DataFrame do arquivo CSV
        item_selecionado_df = self.carregar_item_selecionado(ITEM_SELECIONADO_PATH)

        # Verificar se o DataFrame foi carregado corretamente
        if item_selecionado_df is not None:
            self.gerar_documento_pregoeiro(TEMPLATE_PREGOEIRO, item_selecionado_df, RELATORIO_PATH)
        else:
            print("Erro ao carregar os dados do item selecionado.")

    def carregar_item_selecionado(self, filepath):
        try:
            df = pd.read_csv(filepath)
            return df
        except Exception as e:
            print(f"Erro ao carregar o arquivo: {e}")
            return None

    def create_button_pregoeiro(self, title, callback, icon_name):
        button = QToolButton()
        button.setText(title)
        button.clicked.connect(callback)

        # Definir fonte e tamanho da fonte
        font = QFont()
        font.setPointSize(14)
        button.setFont(font)

        # Definir política de tamanho expansível
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.setSizePolicy(size_policy)

        # Definir altura fixa
        button.setFixedHeight(70)  # Altura fixa de 40 pixels

        # Definir estilo CSS para bordas arredondadas e outros estilos
        button.setStyleSheet("""
            QToolButton {
                border: 1px solid #8f8f91;
                border-radius: 5px;  /* Borda arredondada */
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #f6f7fa, stop:1 #dadbde);
                padding: 5px;
            }
            QToolButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #dadbde, stop:1 #f6f7fa);
            }
            QToolButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #dadbde, stop:1 #a6a6a6);
            }
        """)

        # Carregar ícone
        icon_path = os.path.join(ICONS_DIR, icon_name)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QSize(32, 32))
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        else:
            print(f"Ícone não encontrado: {icon_path}")

        return button
  
    def on_table_clicked(self, index):
        self.processo_selecionado = index.column()
        # Aqui, você pode capturar as informações do pregão
        pregao_info = self.model.processos_info[self.processo_selecionado - 1]  # Ajuste o índice conforme necessário
        self.selected_pregao_info = {
            "num_pregao": pregao_info[0],
            "ano_pregao": pregao_info[1],
            "objeto": pregao_info[2],
            "pregoeiro": self.get_pregoeiro_for_processo(self.processo_selecionado)
        }

    def get_pregoeiro_for_processo(self, processo):
        # Implemente a lógica para obter o nome do pregão associado ao processo
        pass

    def on_header_clicked(self, section):
        fake_index = self.model.index(0, section)
        self._on_item_click(fake_index)
        self.processo_selecionado = section

    def create_button(self, title, callback):
        button = QPushButton(title)
        button.clicked.connect(callback)
        return button

    def reset_marcadores(self):
        confirmation = QMessageBox.question(
            self,
            "Confirmação",
            "Tem certeza de que deseja resetar os marcadores e os contadores de escalas para todos os pregoeiros?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirmation == QMessageBox.StandardButton.Yes:
            for pregoeiro in self.nomes_pregoeiros:
                pregoeiro["processos_escalados"] = []  # Zera os marcadores "x"
                pregoeiro["cont_escalas"] = 0  # Zera o contador de escalas
        
            self.model.layoutChanged.emit()
            self.save_pregoeiros()  # Salve os dados atualizados no arquivo JSON

    def open_add_pregoeiro_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Pregoeiro")

        dialog_layout = QVBoxLayout()

        nome_input = QLineEdit()
        nome_input.setPlaceholderText("Nome do novo pregoeiro")
        dialog_layout.addWidget(nome_input)

        antiguidade_input = QLineEdit()
        antiguidade_input.setPlaceholderText("Antiguidade do novo pregoeiro")
        dialog_layout.addWidget(antiguidade_input)

        marcador_escalas_input = QLineEdit()
        marcador_escalas_input.setPlaceholderText("Marcador de escalas do novo pregoeiro")
        dialog_layout.addWidget(marcador_escalas_input)

        add_button = QPushButton("Adicionar")
        add_button.clicked.connect(lambda: self.add_pregoeiro(nome_input.text(), antiguidade_input.text(), marcador_escalas_input.text()))
        dialog_layout.addWidget(add_button)

        dialog.setLayout(dialog_layout)
        dialog.exec()

    def add_pregoeiro(self, nome, antiguidade, marcador_escalas):
        if nome:
            novo_pregoeiro = {
                "nome": nome,
                "antiguidade": int(antiguidade),
                "cont_escalas": 0,
                "processos_escalados": [],
                "marcador_escalas": marcador_escalas  # Adicione o marcador de escalas
            }
            self.nomes_pregoeiros.append(novo_pregoeiro)

            for pregoeiro in self.nomes_pregoeiros:
                if pregoeiro["nome"] != nome and pregoeiro["antiguidade"] >= int(antiguidade):
                    pregoeiro["antiguidade"] += 1

            self.nomes_pregoeiros.sort(key=lambda x: x["antiguidade"])
            
            self.model.layoutChanged.emit()
            self.save_pregoeiros()  # Salve os dados atualizados no arquivo JSON
            self.adjust_table_height()

    def open_remove_pregoeiro_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Remover Pregoeiro")

        dialog_layout = QVBoxLayout()

        pregoeiro_combo = QComboBox()
        for pregoeiro in self.nomes_pregoeiros:
            pregoeiro_combo.addItem(pregoeiro["nome"])
        dialog_layout.addWidget(pregoeiro_combo)

        remove_button = QPushButton("Remover")
        remove_button.clicked.connect(lambda: self.remove_pregoeiro(pregoeiro_combo.currentText()))
        dialog_layout.addWidget(remove_button)

        dialog.setLayout(dialog_layout)
        dialog.exec()
        
    def remove_pregoeiro(self, nome):
        for pregoeiro in self.nomes_pregoeiros:
            if pregoeiro["nome"] == nome:
                self.nomes_pregoeiros.remove(pregoeiro)
                self.model.layoutChanged.emit()
                self.save_pregoeiros()  # Salve os dados atualizados no arquivo JSON
                self.adjust_table_height()
                break

    def atualizar_mapeamento_pregoeiros(self):
        # Limpar o mapeamento atual
        self.processos_pregoeiros.clear()

        # Reconstruir o mapeamento com base em self.nomes_pregoeiros
        for pregoeiro in self.nomes_pregoeiros:
            for num_pregao in pregoeiro["processos_escalados"]:
                self.processos_pregoeiros[num_pregao] = pregoeiro["nome"]

    def alterar_pregoeiro(self):
        if self.processo_selecionado:
            dialog = CustomDialog(self.nomes_pregoeiros, self)
            if dialog.exec():
                novo_pregoeiro = dialog.pregoeiro_combo.currentText()

                # Remover processo do pregoeiro atual e ajustar o contador
                for pregoeiro in self.nomes_pregoeiros:
                    if self.processo_selecionado in pregoeiro["processos_escalados"]:
                        pregoeiro["processos_escalados"].remove(self.processo_selecionado)
                        pregoeiro["cont_escalas"] -= 1  # Decrementar o contador
                        break

                # Adicionar processo ao novo pregoeiro e ajustar o contador
                for pregoeiro in self.nomes_pregoeiros:
                    if pregoeiro["nome"] == novo_pregoeiro:
                        pregoeiro["processos_escalados"].append(self.processo_selecionado)
                        pregoeiro["cont_escalas"] += 1  # Incrementar o contador
                        break

                self.model.layoutChanged.emit()
                self.atualizar_mapeamento_pregoeiros()
                self.save_pregoeiros()  # Salvar alterações
                self.processo_selecionado = None  # Resetar o processo selecionado
                self.atualizar_escala_panel()  # Atualizar o painel de escalas
                self.salvar_pregoeiros_no_excel() 
        else:
            QMessageBox.warning(self, "Erro", "Nenhum processo selecionado.")

    def adjust_column_widths(self, column_widths):
        for column, width in column_widths.items():
            self.tableView.setColumnWidth(column, width)

    def get_text_width(self, text):
        fm = self.tableView.fontMetrics()
        return fm.horizontalAdvance(text)

    def escalar_funcionario(self):
        if self.processo_selecionado:
            try:
                sucesso = selecionar_para_escala(self.nomes_pregoeiros, self.processo_selecionado, self.processos_pregoeiros)
                if sucesso:
                    # Atualizações após a escalação bem-sucedida
                    self.model.layoutChanged.emit()
                    self.save_pregoeiros()
                    self.processo_selecionado = None  # Resetar o processo selecionado
                    self.atualizar_escala_panel()  # Atualizar o painel de escalas
                    self.salvar_pregoeiros_no_excel()  # Salva as alterações no arquivo Excel
                else:
                    QMessageBox.warning(self, "Erro de Escalação", "Já existe pregoeiro escalado para este processo")
            except ValueError:
                pass
        else:
            QMessageBox.warning(self, "Erro", "Nenhum processo selecionado.")

    def salvar_pregoeiros_no_excel(self):
        try:
            df = pd.read_excel(CONTROLE_PROCESSOS_DIR)
            df['pregoeiro'] = df['num_pregao'].map(self.processos_pregoeiros).fillna(df['pregoeiro'])
            df.to_excel(CONTROLE_PROCESSOS_DIR, index=False)
        except Exception as e:
            print(f"Erro ao salvar no Excel: {e}")
        
    def atualizar_escala_panel(self):
        if hasattr(self, 'escala_panel') and self.escala_panel.isVisible():
            self.escala_panel.update_panel(self.nomes_pregoeiros)

    def obter_proximo_processo_disponivel(self):
        import random
        return random.randint(1, self.model.num_processes)

    def get_title(self):
        return "Pregoeiros"

    def get_content_widget(self):
        return self

    def load_pregoeiros(self):
        # Implementação para carregar os dados dos pregoeiros
        try:
            with open(ESCALACAO_PREGOEIROS, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print("Arquivo não encontrado. Retornando lista vazia.")
            return []
        
    def save_pregoeiros(self):
        # Salva dados dos pregoeiros em um arquivo JSON
        with open(ESCALACAO_PREGOEIROS, "w") as file:
            json.dump(self.nomes_pregoeiros, file)

    def importar_dados_pregoeiros(self):
        # Importa dados dos pregoeiros de um arquivo Excel
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Abrir arquivo de Pregoeiros", "", "Excel Files (*.xlsx *.ods)"
        )
        if filepath:
            self.carregar_dados_pregoeiros(filepath)

    def carregar_dados_pregoeiros(self, filepath):
        try:
            if filepath.endswith('.xlsx'):
                df = pd.read_excel(filepath)
            elif filepath.endswith('.ods'):
                df = pd.read_excel(filepath, engine='odf')
            else:
                QMessageBox.warning(self, "Formato de Arquivo Inválido", "Por favor, selecione um arquivo .xlsx ou .ods")
                return

            self.nomes_pregoeiros = []
            for _, row in df.iterrows():
                self.nomes_pregoeiros.append({
                    "nome": row["nome"],
                    "antiguidade": row["antiguidade"],
                    "cont_escalas": row.get("cont_escalas", 0),  # Use o valor do arquivo, se presente, senão 0
                    "processos_escalados": []
                })
            
            # Atualize o modelo com os novos dados
            self.model = TableModel(self.nomes_pregoeiros, self.model.num_processes)
            self.tableView.setModel(self.model)
            self.model.layoutChanged.emit()

        except Exception as e:
            QMessageBox.warning(self, "Erro de Leitura", f"Erro ao ler o arquivo: {e}")
        if hasattr(self, 'info_panel'):
            self.info_panel.update_panel(self.nomes_pregoeiros)

    def show_escala_panel(self):
        # Cria uma nova instância de EscalaPanel toda vez que o botão é clicado
        escala_panel = EscalaPanel(self.nomes_pregoeiros, self)
        escala_panel.resize(300, 400)  # Ajuste as dimensões conforme necessário
        escala_panel.show()

def selecionar_para_escala(nomes_pregoeiros, processo_escolhido, processos_pregoeiros):

    # Verifica se o processo já está escalado para algum pregoeiro
    for pregoeiro in nomes_pregoeiros:
        if processo_escolhido in pregoeiro["processos_escalados"]:
            # Processo já escalado, não escalar novamente
            return False

    # Ordena os pregoeiros por número de escalas e antiguidade
    nomes_pregoeiros_ordenados = sorted(nomes_pregoeiros, key=lambda x: (x["cont_escalas"], x["antiguidade"]))

    for pregoeiro in nomes_pregoeiros_ordenados:
        # Verifica se o pregoeiro tem algum impedimento
        if "impedimento" in pregoeiro and pregoeiro["impedimento"]:
            continue  # Pula este pregoeiro e continua com o próximo

        if processo_escolhido not in pregoeiro["processos_escalados"]:
            pregoeiro["cont_escalas"] += 1
            pregoeiro["processos_escalados"].append(processo_escolhido)
            processos_pregoeiros[processo_escolhido] = pregoeiro["nome"]  # Adiciona o mapeamento
            return True

    return False


class EscalaPanel(QDialog):
    def __init__(self, nomes_pregoeiros, parent=None):
        super().__init__(parent)
        self.nomes_pregoeiros = nomes_pregoeiros

        self.setWindowTitle("Escala de Pregoeiros")
        self.layout = QVBoxLayout(self)

        self.table = QTableWidget(self)
        self.table.setColumnCount(4)  # Quatro colunas: Nome, Antiguidade, Escalas e Impedimentos
        self.table.setHorizontalHeaderLabels(["Nome", "Antiguidade", "Escalas", "Impedimentos"])
        self.layout.addWidget(self.table)

        self.btn_add_impedimento = QPushButton("Adicionar Impedimento", self)
        self.btn_add_impedimento.clicked.connect(self.on_add_impedimento_clicked)
        self.layout.addWidget(self.btn_add_impedimento)

        self.btn_remove_impedimento = QPushButton("Remover Impedimento", self)
        self.btn_remove_impedimento.clicked.connect(self.on_remove_impedimento_clicked)
        self.layout.addWidget(self.btn_remove_impedimento)

        self.update_panel(nomes_pregoeiros)

        # Configurar tabela para não permitir edição
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                # Configurar as colunas para se ajustarem ao conteúdo
        header = self.table.horizontalHeader()
        for column in range(self.table.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

        # Definir um tamanho mínimo inicial baseado em uma estimativa
        self.setMinimumSize(400, 600)  
        # Redimensionar a janela para se ajustar ao conteúdo e, em seguida, fixar o tamanho
        self.adjustSize()
        self.setFixedSize(self.size())

    def update_panel(self, nomes_pregoeiros):
        self.table.setRowCount(len(nomes_pregoeiros))
        for row, pregoeiro in enumerate(nomes_pregoeiros):
            self.table.setItem(row, 0, QTableWidgetItem(pregoeiro['nome']))
            self.table.setItem(row, 1, QTableWidgetItem(str(pregoeiro['antiguidade'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(pregoeiro['cont_escalas'])))
            impedimento = pregoeiro.get('impedimento', '')
            self.table.setItem(row, 3, QTableWidgetItem(impedimento))

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def on_add_impedimento_clicked(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um pregoeiro primeiro.")
            return

        options = ["Férias", "Missão", "Atestado Médico", "Outro"]
        choice, ok = QInputDialog.getItem(self, "Selecionar Impedimento", "Escolha o impedimento:", options, 0, False)

        if ok and choice:
            # Aqui você pode atualizar as informações do pregoeiro com o impedimento escolhido
            # Por exemplo, atualizando um campo no dicionário de pregoeiros ou em um banco de dados
            pregoeiro = self.nomes_pregoeiros[selected_row]
            pregoeiro['impedimento'] = choice
        self.update_panel(self.nomes_pregoeiros)  # Atualizar tabela após remoção do impedimento

    def on_remove_impedimento_clicked(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um pregoeiro primeiro.")
            return

        # Usando self.nomes_pregoeiros para garantir que estamos acessando a variável da classe
        pregoeiro = self.nomes_pregoeiros[selected_row]
        if 'impedimento' in pregoeiro:
            del pregoeiro['impedimento']
            # Atualize a interface do usuário conforme necessário
            QMessageBox.information(self, "Impedimento Removido", f"Impedimento removido para {pregoeiro['nome']}.")
        else:
            QMessageBox.warning(self, "Nenhum Impedimento", "Este pregoeiro não possui impedimento registrado.")

        self.update_panel(self.nomes_pregoeiros)  # Atualizar tabela após remoção do impedimento

class CustomDialog(QDialog):
    def __init__(self, nomes_pregoeiros, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Pregoeiro")
        self.nomes_pregoeiros = nomes_pregoeiros

        layout = QVBoxLayout(self)

        self.pregoeiro_combo = QComboBox()
        self.pregoeiro_combo.addItems([p["nome"] for p in nomes_pregoeiros])
        layout.addWidget(self.pregoeiro_combo)

        self.escalar_proximo_button = QPushButton("Escalar Próximo")
        self.escalar_proximo_button.clicked.connect(self.escalar_proximo)
        layout.addWidget(self.escalar_proximo_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

    def escalar_proximo(self):
        # Filtrar pregoeiros sem impedimento e com menor contador de escalas
        pregoeiros_disponiveis = [p for p in self.nomes_pregoeiros if 'impedimento' not in p or not p['impedimento']]
        if not pregoeiros_disponiveis:
            QMessageBox.warning(self, "Nenhum Pregoeiro Disponível", "Todos os pregoeiros estão impedidos.")
            return

        pregoeiro_com_menor_contador = min(pregoeiros_disponiveis, key=lambda x: x["cont_escalas"])
        self.pregoeiro_combo.setCurrentText(pregoeiro_com_menor_contador["nome"])

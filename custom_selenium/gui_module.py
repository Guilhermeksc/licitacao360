from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from styles.styless import get_transparent_title_style
from datetime import datetime
import json
import pandas as pd
import os
import locale
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
from pathlib import Path

class JSONDialog(QDialog):
    def __init__(self, parent=None):
        super(JSONDialog, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.model = QStandardItemModel()  # Modelo de dados para a QTableView

        # Botão para carregar o arquivo JSON
        self.load_json_button = QPushButton("Carregar JSON", self)
        self.load_json_button.clicked.connect(self.load_json)
        self.layout.addWidget(self.load_json_button)

        # TableView para mostrar os dados JSON
        self.json_table_view = QTableView(self)
        self.layout.addWidget(self.json_table_view)

        # Botão para gerar a tabela Excel
        self.generate_table_button = QPushButton("Gerar Tabela", self)
        self.generate_table_button.clicked.connect(self.generate_excel_table)
        self.layout.addWidget(self.generate_table_button)

        # Botão para confirmar a entrada
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.setWindowTitle("Converter arquivo JSON para tabela")

    def load_json(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo JSON", "", "Arquivos JSON (*.json)")
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as file:
                self.json_data = json.load(file)

                # Aplicar a conversão das unidades de medida aqui
                for item in self.json_data:
                    if 'unidade' in item and 'nomeUnidadeMedida' in item['unidade']:
                        # Aqui você precisa ajustar para que corresponda à estrutura exata dos seus dados
                        unidade_convertida = self.convert_unidade_medida(item['unidade']['nomeUnidadeMedida'])
                        item['unidade']['nomeUnidadeMedida'] = unidade_convertida  # Atualizar o item com a unidade convertida

                self.update_table_view()
            print("Arquivo JSON carregado com sucesso!")

    def update_table_view(self):
        self.model.clear()  # Limpa o modelo existente
        for item in self.json_data:
            row = []
            for key, value in item.items():
                cell = QStandardItem(str(value))
                row.append(cell)
            self.model.appendRow(row)
        self.json_table_view.setModel(self.model)

    def generate_excel_table(self):
        if self.json_data is not None:
            self.convert_json_to_excel()
            print("Tabela Excel gerada com sucesso!")
        else:
            print("Nenhum dado JSON carregado para gerar a tabela.")

    def convert_json_to_excel(self):
        df = pd.DataFrame(self.json_data)

        # Renomear as colunas conforme especificado
        df.rename(columns={
            'sequencial': 'item_num',
            'nome': 'descricao_detalhada',
            'carrinhoCaracteristicas': 'caracteristicas',
            'id': 'catalogo',
            'carrinhoNome': 'descricao_tr',
            'unidade': 'unidade_fornecimento'
        }, inplace=True)

        # Ajustar a coluna 'caracteristicas': remover '#' e o último '|'
        df['caracteristicas'] = df['caracteristicas'].str.replace('#', '').str.rstrip('|')
        # Extrair 'nomeUnidadeMedida' de 'unidade_fornecimento'
        df['unidade_fornecimento'] = df['unidade_fornecimento'].apply(lambda x: x['nomeUnidadeMedida'])
        df['unidade_fornecimento'] = df['unidade_fornecimento'].apply(self.convert_unidade_medida)

        # Adicionar colunas vazias
        df['valor_unitario'] = ''
        df['quantidade_estimada'] = ''
        df['valor_total_do_item'] = ''

        # Reordenar as colunas e remover a coluna 'tipo'
        colunas_desejadas = ['item_num', 'catalogo', 'descricao_tr', 'descricao_detalhada', 'caracteristicas', 'unidade_fornecimento', 'valor_unitario', 'quantidade_estimada', 'valor_total_do_item']
        df = df[colunas_desejadas]

        # Gerar um nome de arquivo único usando um timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"tabela_conversao_{timestamp}.xlsx"

        # Preparar o ExcelWriter com o engine xlsxwriter
        writer = pd.ExcelWriter(nome_arquivo, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Sheet1')

        # Ajustar o tamanho das colunas
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        # Ajuste das larguras de coluna
        # Aproximação: 1 unidade de largura no Excel equivale aproximadamente a 6 pixels.
        # Portanto, para 60px, usamos 10 como valor aproximado, e para 20px, usamos cerca de 3.3.
        worksheet.set_column('C:C', 25)  # Para 'descricao_tr', supondo que seja a coluna B
        worksheet.set_column('F:F', 25)  # Para 'unidade_fornecimento', supondo que seja a coluna F
        # Ajustar todas as outras colunas para 20px (aprox. 3.3 de largura no Excel)
        worksheet.set_column('A:B', 10)
        worksheet.set_column('D:E', 20)
        worksheet.set_column('G:Z', 10)  # Ajusta as colunas até a Z, ajuste conforme necessário

        # Salvar o arquivo Excel
        writer.close()

        # Abrir o arquivo Excel
        try:
            os.startfile(nome_arquivo)
        except Exception as e:
            print(f"Não foi possível abrir o arquivo: {e}")

    def convert_unidade_medida(self, unidade):

        # Dicionário de mapeamento das abreviações para os nomes completos
        mapeamento = {
            'G': 'Grama',
            'UN': 'Unidade',
            'FL': 'Folha',
            'ML': 'Mililitro',
            'L': 'Litro'
        }
        
        # Dividir o valor em quantidade e unidade
        partes = unidade.split()
        if len(partes) > 1:  # Verifica se há unidade para converter
            quantidade, unidade_abrev = partes[:-1], partes[-1]
            # Converter a unidade, se estiver no dicionário de mapeamento
            unidade_completa = mapeamento.get(unidade_abrev, unidade_abrev)
            # Reconstruir a string com a unidade convertida
            return ' '.join(quantidade + [unidade_completa])
        else:
            return unidade  # Retorna o valor original se não houver unidade para converter

class AlteracaoIRPDialog(QDialog):
    def __init__(self, parent=None):
        super(AlteracaoIRPDialog, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # Layout horizontal para Nº da IRP e Ano
        self.irp_num_layout = QHBoxLayout()
        self.irp_num_input = QLineEdit(self)
        self.irp_num_input.setPlaceholderText("Nº da IRP")
        self.irp_num_layout.addWidget(self.irp_num_input)

        self.ano_irp_input = QLineEdit(self)
        self.ano_irp_input.setText(str(datetime.now().year))  # Ano atual
        self.irp_num_layout.addWidget(self.ano_irp_input)
        self.layout.addLayout(self.irp_num_layout)

        # Botão para carregar o arquivo da tabela
        self.load_table_button = QPushButton("Carregar Tabela", self)
        self.load_table_button.clicked.connect(self.load_table)
        self.layout.addWidget(self.load_table_button)

        # Modelo e TableView para exibir dados
        self.model = QStandardItemModel(self)  
        self.tableView = QTableView(self)
        self.tableView.setModel(self.model)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Correção aplicada aqui
        self.layout.addWidget(self.tableView)

        # ComboBox para o número inicial do item
        self.item_inicio_combo = QComboBox(self)
        self.layout.addWidget(self.item_inicio_combo)  # Adiciona a ComboBox ao layout

        # Botão para confirmar a entrada
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.table_data = None  # DataFrame para armazenar dados da tabela
        self.setWindowTitle("Carregue a table para atualizar o IRP")
        
    def load_table(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.ods)")
        if file_name:
            self.table_data = pd.read_excel(file_name)
            self.model.clear()
            self.model.setHorizontalHeaderLabels(self.table_data.columns)

            for index, row in self.table_data.iterrows():
                items = [QStandardItem(str(cell)) for cell in row]
                self.model.appendRow(items)

            # Preencher a ComboBox com os números dos itens
            self.item_inicio_combo.clear()  # Limpa os itens antigos
            item_nums = self.table_data['item_num'].astype(str).tolist()  # Converte os números dos itens para string
            self.item_inicio_combo.addItems(item_nums)  # Adiciona os números dos itens à ComboBox

            QMessageBox.information(self, "Carregamento Concluído", "Tabela carregada com sucesso!")

    def get_irp_number(self):
        irp_num = self.irp_num_input.text().strip()
        ano_irp = self.ano_irp_input.text()
        return irp_num + ano_irp

    def get_item_inicio(self):
        return self.item_inicio_combo.currentText()  # Retorna o item selecionado na ComboBox

    def accept(self):
        super().accept()
        item_selecionado = self.get_item_inicio()
        print(f"Item selecionado: {item_selecionado}")

class AnaliseParticipantesIRPDialog(QDialog):
    def __init__(self, parent=None):
        super(AnaliseParticipantesIRPDialog, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # Layout horizontal para Nº da IRP e Ano
        self.irp_num_layout = QHBoxLayout()
        self.irp_num_input = QLineEdit(self)
        self.irp_num_input.setPlaceholderText("Nº da IRP")
        self.irp_num_layout.addWidget(self.irp_num_input)

        self.ano_irp_input = QLineEdit(self)
        self.ano_irp_input.setText(str(datetime.now().year))  # Ano atual
        self.irp_num_layout.addWidget(self.ano_irp_input)
        self.layout.addLayout(self.irp_num_layout)

        # Botão para carregar o arquivo da tabela
        self.load_table_button = QPushButton("Carregar Tabela", self)
        self.load_table_button.clicked.connect(self.load_table)
        self.layout.addWidget(self.load_table_button)

        # Modelo e TableView para exibir dados
        self.model = QStandardItemModel(self)  
        self.tableView = QTableView(self)
        self.tableView.setModel(self.model)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Correção aplicada aqui
        self.layout.addWidget(self.tableView)

        # ComboBox para o número inicial do item
        self.item_inicio_combo = QComboBox(self)
        self.layout.addWidget(self.item_inicio_combo)  # Adiciona a ComboBox ao layout

        # Botão para confirmar a entrada
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.table_data = None  # DataFrame para armazenar dados da tabela
        self.setWindowTitle("Carregue a table para atualizar o IRP")
        
    def load_table(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.ods)")
        if file_name:
            self.table_data = pd.read_excel(file_name)
            self.model.clear()
            self.model.setHorizontalHeaderLabels(self.table_data.columns)

            for index, row in self.table_data.iterrows():
                items = [QStandardItem(str(cell)) for cell in row]
                self.model.appendRow(items)

            # Preencher a ComboBox com os números dos itens
            self.item_inicio_combo.clear()  # Limpa os itens antigos
            item_nums = self.table_data['item_num'].astype(str).tolist()  # Converte os números dos itens para string
            self.item_inicio_combo.addItems(item_nums)  # Adiciona os números dos itens à ComboBox

            QMessageBox.information(self, "Carregamento Concluído", "Tabela carregada com sucesso!")

    def get_irp_number(self):
        irp_num = self.irp_num_input.text().strip()
        ano_irp = self.ano_irp_input.text()
        return irp_num + ano_irp

    def get_item_inicio(self):
        return self.item_inicio_combo.currentText()  # Retorna o item selecionado na ComboBox

    def accept(self):
        super().accept()
        item_selecionado = self.get_item_inicio()
        print(f"Item selecionado: {item_selecionado}")

class DivulgacaoComprasDialog(QDialog):
    def __init__(self, parent=None):
        super(DivulgacaoComprasDialog, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # Layout horizontal para Nº da Licitação e Ano
        self.licitacao_layout = QHBoxLayout()
        self.licitacao_num_input = QLineEdit(self)
        self.licitacao_num_input.setPlaceholderText("Nº da Licitação")
        self.licitacao_layout.addWidget(self.licitacao_num_input)  # Correção aqui

        self.licitacao_ano_input = QLineEdit(self)
        self.licitacao_ano_input.setText(str(datetime.now().year))  # Ano atual
        self.licitacao_layout.addWidget(self.licitacao_ano_input)  # Correção aqui
        self.layout.addLayout(self.licitacao_layout)  # Adiciona o layout horizontal ao layout principal

        # Botão para carregar o arquivo da tabela
        self.load_table_button = QPushButton("Carregar Tabela", self)
        self.load_table_button.clicked.connect(self.load_table)
        self.layout.addWidget(self.load_table_button)

        # Modelo e TableView para exibir dados
        self.model = QStandardItemModel(self)  
        self.tableView = QTableView(self)
        self.tableView.setModel(self.model)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Correção aplicada aqui
        self.layout.addWidget(self.tableView)

        # Label para instrução de escolha do item inicial
        self.item_inicio_label = QLabel("Escolha a partir de qual item o fluxo se iniciará:")
        self.layout.addWidget(self.item_inicio_label)  # Adiciona a Label ao layout

        # ComboBox para o número inicial do item
        self.item_inicio_combo = QComboBox(self)
        self.layout.addWidget(self.item_inicio_combo)  # Adiciona a ComboBox ao layout

        # Botão para confirmar a entrada
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.table_data = None  # DataFrame para armazenar dados da tabela
        self.setWindowTitle("Carregue a tabela para atualizar o IRP")
        
    def load_table(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.ods)")
        if file_name:
            self.table_data = pd.read_excel(file_name)
            self.model.clear()
            self.model.setHorizontalHeaderLabels(self.table_data.columns)

            for index, row in self.table_data.iterrows():
                items = [QStandardItem(str(cell)) for cell in row]
                self.model.appendRow(items)

            # Preencher a ComboBox com os números dos itens
            self.item_inicio_combo.clear()  # Limpa os itens antigos
            item_nums = self.table_data['item_num'].astype(str).tolist()  # Converte os números dos itens para string
            self.item_inicio_combo.addItems(item_nums)  # Adiciona os números dos itens à ComboBox

            QMessageBox.information(self, "Carregamento Concluído", "Tabela carregada com sucesso!")

    def get_licitacao_number(self):
        licitacao_num = self.licitacao_num_input.text().strip()
        licitacao_ano = self.licitacao_ano_input.text()
        return licitacao_num + licitacao_ano

    def get_item_inicio(self):
        return self.item_inicio_combo.currentText()  # Retorna o item selecionado na ComboBox

    def accept(self):
        super().accept()
        item_selecionado = self.get_item_inicio()
        print(f"Item selecionado: {item_selecionado}")

class ParticipantsDialog(QDialog):
    def __init__(self, data, parent=None):
        super(ParticipantsDialog, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.table_view = QTableView(self)
        self.model = QStandardItemModel(self)
        self.table_view.setModel(self.model)
        self.layout.addWidget(self.table_view)
        
        # Configura os cabeçalhos e preenche a tabela com os dados
        self.model.setHorizontalHeaderLabels([str(col) for col in data.columns])
        for index, row in data.iterrows():
            items = [QStandardItem(str(cell)) for cell in row]
            self.model.appendRow(items)
        
        self.setWindowTitle("Órgãos Participantes")
        self.resize(800, 600)  # Ajuste o tamanho conforme necessário

class ParticipantesIRPDialog(QDialog):
    def __init__(self, parent=None):
        super(ParticipantesIRPDialog, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.settings_file = 'settings.json'
        self.last_opened_file = None # Último arquivo carregado

        # Layout horizontal para Nº da Licitação e Ano
        self.licitacao_layout = QHBoxLayout()
        self.licitacao_num_input = QLineEdit(self)
        self.licitacao_num_input.setPlaceholderText("Nº da Licitação")
        self.licitacao_layout.addWidget(self.licitacao_num_input)  # Correção aqui
        
        # Conectar o sinal de texto alterado ao método de salvamento das configurações
        self.licitacao_num_input.textChanged.connect(self.save_settings)

        self.licitacao_ano_input = QLineEdit(self)
        self.licitacao_ano_input.setText(str(datetime.now().year))  # Ano atual
        self.licitacao_layout.addWidget(self.licitacao_ano_input)  # Correção aqui
        self.layout.addLayout(self.licitacao_layout)  # Adiciona o layout horizontal ao layout principal

        # Botão para carregar o arquivo da tabela
        self.load_table_button = QPushButton("Carregar Tabela", self)
        self.load_table_button.clicked.connect(self.load_table)
        self.layout.addWidget(self.load_table_button)

        # Botão para conferir os órgãos participantes
        self.check_participants_button = QPushButton("Conferir Órgãos Participantes", self)
        self.check_participants_button.clicked.connect(self.check_participantes)
        self.layout.addWidget(self.check_participants_button)
        
        # Modelo e TableView para exibir dados
        self.model = QStandardItemModel(self)  
        self.tableView = QTableView(self)
        self.tableView.setModel(self.model)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Correção aplicada aqui
        self.layout.addWidget(self.tableView)

        # Label para instrução de escolha do item inicial
        self.item_inicio_label = QLabel("Escolha a partir de qual item o fluxo se iniciará:")
        self.layout.addWidget(self.item_inicio_label)  # Adiciona a Label ao layout

        # ComboBox para o número inicial do item
        self.item_inicio_combo = QComboBox(self)
        self.layout.addWidget(self.item_inicio_combo)  # Adiciona a ComboBox ao layout

        # Botão para confirmar a entrada
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.table_data = None  # DataFrame para armazenar dados da tabela
        self.setWindowTitle("Conferência dos Orgãos Participantes")

        self.load_settings()

    def check_participantes(self):
        if self.table_data_participantes is not None:
            # Cria e exibe a nova janela de diálogo com os dados da tabela
            dialog = ParticipantsDialog(self.table_data_participantes, self)
            dialog.exec()

        else:
            QMessageBox.warning(self, "Aviso", "Nenhuma aba de participantes carregada.")

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as file:
                settings = json.load(file)
                self.licitacao_num_input.setText(settings.get('licitacao_num', ''))
                self.last_opened_file = settings.get('last_opened_file', '')
                if self.last_opened_file and Path(self.last_opened_file).exists():
                    self.load_table(self.last_opened_file)
                else:
                    QMessageBox.warning(self, "Aviso", "O último arquivo carregado foi deletado ou está aberto em outro programa.")

    def save_settings(self):
        settings = {
            'licitacao_num': self.licitacao_num_input.text(),
            'last_opened_file': self.last_opened_file
        }
        with open(self.settings_file, 'w') as file:
            json.dump(settings, file, indent=4)
    
    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def load_table(self, file_name=None):
        if not file_name:
            file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.ods)")
        if file_name:
            self.last_opened_file = file_name
            self.save_settings()  # Salvar configurações após carregar um novo arquivo
            try:
                # Carrega a primeira aba por padrão
                self.table_data = pd.read_excel(file_name)

                # Tentativa de carregar a aba "Participantes"
                try:
                    self.table_data_participantes = pd.read_excel(file_name, sheet_name='Participantes')
                    # Após carregar os dados em ParticipantesIRPDialog
                    # self.selenium_automation_instance.table_data_participantes = self.table_data_participantes

                except ValueError as e:
                    QMessageBox.critical(self, "Erro de Carregamento", f"Aba 'Participantes' não encontrada. Detalhes do erro: {e}")
                    self.table_data_participantes = None

                self.model.clear()
                self.model.setHorizontalHeaderLabels(self.table_data.columns)
                
                for index, row in self.table_data.iterrows():
                    items = [QStandardItem(str(cell)) for cell in row]
                    self.model.appendRow(items)

                # Preencher a ComboBox com os números dos itens
                self.item_inicio_combo.clear()  # Limpa os itens antigos
                item_nums = self.table_data['item_num'].astype(str).tolist()  # Converte os números dos itens para string
                self.item_inicio_combo.addItems(item_nums)  # Adiciona os números dos itens à ComboBox

                QMessageBox.information(self, "Carregamento Concluído", "Tabela carregada com sucesso!")

            except Exception as e:
                QMessageBox.critical(self, "Erro de Carregamento", f"Erro ao carregar o arquivo da tabela. Detalhes do erro: {e}")
                self.table_data = None
                self.table_data_participantes = None
        else:
            QMessageBox.warning(self, "Carregamento Cancelado", "Nenhum arquivo foi selecionado.")

    def get_licitacao_number(self):
        licitacao_num = self.licitacao_num_input.text().strip()
        licitacao_ano = self.licitacao_ano_input.text()
        return licitacao_num + licitacao_ano

    def get_item_inicio(self):
        return self.item_inicio_combo.currentText()  # Retorna o item selecionado na ComboBox

    def accept(self):
        super().accept()
        item_selecionado = self.get_item_inicio()
        print(f"Item selecionado: {item_selecionado}")
        self.save_settings()
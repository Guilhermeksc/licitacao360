import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, 
    QLineEdit, QMessageBox, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from diretorios import *
from styles.styless import get_transparent_title_style
import os
import time
from docxtpl import DocxTemplate
import shutil
import csv

def read_csv_data(csv_path):
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            try:
                data = next(reader, None)
                if data:
                    data = {key.lstrip('\ufeff'): value for key, value in data.items()}
                return data
            except StopIteration:
                print(f"Arquivo CSV vazio: {csv_path}")
                return None  # ou return {} se preferir um dicionário vazio
    except FileNotFoundError:
        print(f"Arquivo CSV não encontrado: {csv_path}")
        return None
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")
        return None

def replace_variables_in_document(template_path, context):
    # Carregar o template do documento usando docxtpl
    doc = DocxTemplate(template_path)
    
    # Renderizar o documento com o contexto
    doc.render(context)
    
    # Retornar o documento para ser salvo fora desta função
    return doc

class CPItemWidget(QWidget):
    def __init__(self, numero, assunto, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)

        self.numero_label = QLabel(numero)
        self.layout.addWidget(self.numero_label)

        self.assunto_edit = QLineEdit(assunto)
        self.assunto_edit.editingFinished.connect(self.on_editing_finished)
        self.layout.addWidget(self.assunto_edit)

        self.numero = numero  # Armazenar o número para uso posterior

    def on_editing_finished(self):
        # Aqui, você pode emitir um sinal ou chamar uma função para atualizar o banco de dados
        novo_assunto = self.assunto_edit.text()
        print(f"Assunto atualizado para '{novo_assunto}' para {self.numero}")
        # Emita um sinal ou chame uma função para atualizar o banco de dados

class NumeradorCP(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_db()
        self.init_ui()

    def set_font_size(self, widget, size=12):
        font = QFont()
        font.setPointSize(size)
        widget.setFont(font)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        label_registro_cp = QLabel("Numerador de Comunicação Padronizada (CP)")
        label_registro_cp.setStyleSheet(get_transparent_title_style())
        self.layout.addWidget(label_registro_cp)

        self.init_table()
        self.add_input_fields()
        self.add_buttons()

        self.load_cps()

    def init_table(self):
        self.cp_table = QTableWidget(0, 3)
        self.cp_table.setHorizontalHeaderLabels(['Número', 'Assunto', 'Destinatário'])
        header = self.cp_table.horizontalHeader()
        
        # Coluna 0 (Número) - ajustar ao conteúdo
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        # Colunas 1 (Assunto) e 2 (Destinatário) - estiramento flexível
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.layout.addWidget(self.cp_table)
        self.cp_table.itemChanged.connect(self.on_item_changed)
        self.set_font_size(self.cp_table)

    def add_input_fields(self):
        self.assunto_input = QLineEdit()
        self.assunto_input.setPlaceholderText("Assunto da CP")
        self.layout.addWidget(self.assunto_input)

        self.destinatario_input = QLineEdit()
        self.destinatario_input.setPlaceholderText("Destinatário da CP")
        self.layout.addWidget(self.destinatario_input)

    def add_buttons(self):
        add_button = QPushButton("Adicionar CP")
        add_button.clicked.connect(self.add_cp)
        self.layout.addWidget(add_button)
        self.set_font_size(add_button)

        buttons_layout = QHBoxLayout()
        button_labels = ['Emissão de\nparecer CJACM', 'Atendimento das\nrecomendações da CJACM', 'CP Teste\n1', 'CP Teste\n2']
        button_actions = {
            'Emissão de\nparecer CJACM': ('cp_parecer_agu.docx', 'Emissão de parecer CJACM', 'AGU'),
            'Atendimento das\nrecomendações da CJACM': ('cp_recomendacoes_agu.docx', 'Atendimento das recomendações da CJACM', 'AGU'),
            'CP Teste\n1': ('cp_teste_1.docx', 'Teste 1', 'Chefe'),
            'CP Teste\n2': ('cp_teste_2.docx', 'Teste 2', 'ViceDiretor'),
        }

        for label in button_labels:
            button = QPushButton(label)
            buttons_layout.addWidget(button)
            self.set_font_size(button)

            # Conectar cada botão à função de criação de documento
            template_name, assunto, destinatario = button_actions[label]
            button.clicked.connect(lambda _, t=template_name, a=assunto, d=destinatario: self.create_document(t, a, d))
        self.layout.addLayout(buttons_layout)

    def on_item_changed(self, item):
        row = item.row()
        column = item.column()

        # Verificar se a coluna editada é a do assunto
        if column == 1:
            numero_item = self.cp_table.item(row, 0)  # Coluna 0 é o número
            novo_assunto = item.text()

            if numero_item:
                numero = numero_item.text()
                # Atualizar o banco de dados
                self.cursor.execute('UPDATE cps SET assunto = ? WHERE numero = ?', (novo_assunto, numero))
                self.conn.commit()

    def init_db(self):
        self.conn = sqlite3.connect('comunicacoes_padronizadas.db')
        self.cursor = self.conn.cursor()
        
        # Criar a tabela cps se ela não existir
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS cps 
                               (numero TEXT, assunto TEXT)''')

        # Tentar adicionar a coluna destinatario se ela não existir
        # Note que isso falhará silenciosamente se a coluna já existir, o que é o comportamento desejado
        try:
            self.cursor.execute('''ALTER TABLE cps ADD COLUMN destinatario TEXT''')
        except sqlite3.OperationalError:
            pass  # Ignora o erro se a coluna já existir

        self.conn.commit()

    def add_cp(self):
        assunto = self.assunto_input.text()
        destinatario = self.destinatario_input.text()
        if assunto and destinatario:
            numero = self.generate_cp_number()

            # Verificar se o número já existe no banco de dados
            self.cursor.execute('SELECT COUNT(*) FROM cps WHERE numero = ?', (numero,))
            if self.cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Número Duplicado", "Um documento com este número já existe.")
                return  # Interromper a adição da nova CP

            # Se o número for único, insira no banco de dados
            self.cursor.execute('INSERT INTO cps (numero, assunto, destinatario) VALUES (?, ?, ?)', 
                                (numero, assunto, destinatario))
            self.conn.commit()
            self.load_cps()  # Recarregar a lista para mostrar o novo item
            self.assunto_input.clear()
            self.destinatario_input.clear()
        else:
            QMessageBox.warning(self, "Aviso", "O assunto e o destinatário da CP não podem estar vazios.")

    def proximo_numero_cp(self):
        # Obter o próximo número de CP disponível
        self.cursor.execute('SELECT COUNT(*) FROM cps')
        count = self.cursor.fetchone()[0]
        return f"30-{count + 1:02d}"
    
    def generate_cp_number(self):
        while True:
            self.cursor.execute('SELECT COUNT(*) FROM cps')
            count = self.cursor.fetchone()[0]
            numero_potencial = f"30-{count + 1:02d}"
            
            # Verificar se o número já existe no banco de dados
            self.cursor.execute('SELECT COUNT(*) FROM cps WHERE numero = ?', (numero_potencial,))
            if self.cursor.fetchone()[0] == 0:
                # Se o número não existe, é único e pode ser usado
                return numero_potencial

    def load_cps(self):
        self.cp_table.setRowCount(0)
        self.cursor.execute('SELECT numero, assunto, destinatario FROM cps')
        for numero, assunto, destinatario in self.cursor.fetchall():
            row = self.cp_table.rowCount()
            self.cp_table.insertRow(row)
            self.cp_table.setItem(row, 0, QTableWidgetItem(numero))
            self.cp_table.setItem(row, 1, QTableWidgetItem(assunto))
            self.cp_table.setItem(row, 2, QTableWidgetItem(destinatario))

    def create_document(self, template_name, assunto, destinatario):
        new_document_path = None
        try:
            numero_cp = self.generate_cp_number()
            item_selecionado = read_csv_data(ITEM_SELECIONADO_PATH)
            if item_selecionado is None:
                raise ValueError("Nenhum dado encontrado no CSV.")

            context = item_selecionado
            context['numero_cp'] = numero_cp
            context['assunto'] = assunto
            context['destinatario'] = destinatario

            template_path = CP_DIR / template_name
            if not os.path.exists(template_path):
                print(f"Template não encontrado: {template_path}")
                return None

            doc = DocxTemplate(template_path)
            doc.render(context)

            new_document_name = f"CP-{numero_cp}-{template_name}"
            new_document_path = RELATORIO_PATH / new_document_name
            doc.save(new_document_path)

            self.cursor.execute('INSERT INTO cps (numero, assunto, destinatario) VALUES (?, ?, ?)', 
                                (numero_cp, assunto, destinatario))
            self.conn.commit()
            self.load_cps()
            print("Documento inserido com sucesso e tabela atualizada.")

        except Exception as e:
            print(f"Erro ao inserir no banco de dados: {e}")
        finally:
            return new_document_path


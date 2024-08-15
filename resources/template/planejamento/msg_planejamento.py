from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
from datetime import datetime
from modules.planejamento.utilidades_planejamento import formatar_valor_monetario
import re
import os
from database.utils.treeview_utils import load_images, create_button
import datetime

class MSGIRP(QDialog):
    def __init__(self, dados, icons_dir, parent=None):
        super().__init__(parent)
        self.dados = dados
        self.icons_dir = Path(icons_dir)
        self.templatePath = PLANEJAMENTO_DIR / "last_template_msg_irp.txt"
        self.setWindowTitle("Mensagem de Intenção de Registro de Preços")
        self.resize(1500, 800)

        self.image_cache = load_images(self.icons_dir, ["apply.png", "copy.png"])

        self.setObjectName("AlertaPrazoDialog")

        self.setStyleSheet("""
            #AlertaPrazoDialog {
                background-color: black;
                color: white;
                font-size: 12pt;
            }
            QDialog {
                font-size: 12pt;
            }
            QTextEdit, QListWidget {
                background-color: white; 
                color: black;
                font-size: 12pt;
            }
            QGroupBox {
                border: 2px solid gray;
                border-radius: 5px;
                margin-top: 0.5em;
                font-size: 14pt;
                font-weight: bold;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)

        self.mainLayout = QVBoxLayout(self)

        # Configuração dos GroupBoxes e seus layouts
        self.setupGroupBoxes()

        # Configuração dos botões
        self.setupButtonsLayout()

        self.loadLastTemplate()

    def setupGroupBoxes(self):
        groupBoxLayout = QHBoxLayout()  # Layout horizontal para os GroupBoxes
        
        self.variableListGroupBox = QGroupBox("Índice de Variáveis")
        variableListLayout = QVBoxLayout()
        self.variableList = QListWidget()
        self.variableList.addItems(sorted(f"{{{{{key}}}}}" for key in self.dados.keys()))
        self.variableList.setMaximumWidth(300)  # Limita o tamanho do QListWidget

        variableListLayout.addWidget(self.variableList)
        self.variableListGroupBox.setLayout(variableListLayout)
        self.variableListGroupBox.setMaximumWidth(300)  # Limita o tamanho do QGroupBox

        groupBoxLayout.addWidget(self.variableListGroupBox)

        # Conectar o evento itemDoubleClicked ao método insertVariable
        self.variableList.itemDoubleClicked.connect(self.insertVariable)

        # Grupo para o editor de modelo
        self.modelEditorGroupBox = QGroupBox("Campo para Edição do Modelo")
        modelEditorLayout = QVBoxLayout()
        self.modelEditor = QTextEdit()
        modelEditorLayout.addWidget(self.modelEditor)
        self.modelEditorGroupBox.setLayout(modelEditorLayout)
        groupBoxLayout.addWidget(self.modelEditorGroupBox)

        # Grupo para o visualizador de texto
        self.textViewerGroupBox = QGroupBox("Campo para Visualização da Mensagem")
        textViewerLayout = QVBoxLayout()
        self.textViewer = QTextEdit()
        self.textViewer.setReadOnly(True)
        textViewerLayout.addWidget(self.textViewer)
        self.textViewerGroupBox.setLayout(textViewerLayout)
        groupBoxLayout.addWidget(self.textViewerGroupBox)

        self.mainLayout.addLayout(groupBoxLayout) 

    def setupButtonsLayout(self):
        self.buttons_layout = QHBoxLayout()
        self.createButtons()
        self.mainLayout.addLayout(self.buttons_layout)  # Adiciona o layout dos botões ao layout principal

    def createButtons(self):
        icon_size = QSize(40, 40)  # Tamanho do ícone para todos os botões
        self.button_specs = [
            ("Aplicar Modelo", self.image_cache['apply'], self.applyTemplate, "Aplica o modelo atual", icon_size),
            ("Copiar Mensagem", self.image_cache['copy'], self.copyTextToClipboard, "Copia a mensagem para a área de transferência", icon_size),
        ]

        for text, icon, callback, tooltip, icon_size in self.button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self, icon_size=icon_size)
            self.buttons_layout.addWidget(btn)

    def applyTemplate(self):
        user_template = self.modelEditor.toPlainText()
        self.textViewer.setHtml(self.renderTemplate(user_template, self.dados))

    def loadLastTemplate(self):
        try:
            if os.path.exists(self.templatePath):
                with open(self.templatePath, 'r', encoding='utf-8') as file:
                    last_template = file.read()
                self.modelEditor.setPlainText(last_template)
            else:
                self.modelEditor.setPlainText("Digite o texto da mensagem aqui...")
            self.applyTemplate()  # Aplica o modelo após carregar
        except Exception as e:
            QMessageBox.warning(self, "Erro ao carregar template", str(e))

    def closeEvent(self, event):
        try:
            current_template = self.modelEditor.toPlainText()
            with open(self.templatePath, 'w', encoding='utf-8') as file:
                file.write(current_template)
        except Exception as e:
            QMessageBox.warning(self, "Erro ao salvar template", str(e))
        super().closeEvent(event)
            
    def renderTemplate(self, template, data):
        # Método atualizado para incluir a lógica de descrição de serviço e conversão de datas
        tipo_servico = data.get("material_servico", "").lower()

        if tipo_servico == "material":
            descricao_servico = "aquisição de"
        else:
            descricao_servico = "contratação de empresa especializada em"
        
        data['material_servico'] = descricao_servico

        data['data_limite_manifestacao_irp'] = self.format_date(data.get('data_limite_manifestacao_irp', ''))
        data['data_limite_confirmacao_irp'] = self.format_date(data.get('data_limite_confirmacao_irp', ''))

        now = datetime.datetime.now()
        mes_atual = now.strftime("%b").upper()
        ano_atual = now.strftime('%Y')
        header = f"R000000Z/<span style='color: blue;'>{mes_atual}</span>/<span style='color: blue;'>{ano_atual}</span><br>"

        template = template.replace('\n', '<br>')

        rendered_text = header + template
        for key, value in data.items():
            rendered_text = re.sub(rf"{{{{\s*{key}\s*}}}}", f"<span style='color: blue;'>{value}</span>", rendered_text)
        return rendered_text

    def format_date(self, date_str):
        # Converter a data de 'YYYY-MM-DD' para 'DDMMMYYYY', tratando dados nulos ou incorretos
        if date_str:
            try:
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                return date_obj.strftime('%d%b%Y').upper()
            except ValueError:
                # Log the error or handle it as needed
                print(f"Data incorreta fornecida: {date_str}")
        return None  # Retorna None ou qualquer valor padrão que deseje

    def copyTextToClipboard(self):
        text = self.textViewer.toPlainText()
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", "Texto copiado para a área de transferência.")

    def insertVariable(self, item):
        cursor = self.modelEditor.textCursor()  # Get the current cursor from QTextEdit
        
        # Se o cursor não estiver ativo ou a posição for zero (início do texto)
        if not cursor or cursor.position() == 0:
            cursor.movePosition(QTextCursor.MoveOperation.End)  # Move o cursor para o final do texto
        
        cursor.insertText(item.text())  # Insert text at cursor's current position
        
        # Move o cursor para logo após o texto inserido
        cursor.setPosition(cursor.position() + len(item.text()))
        
        self.modelEditor.setTextCursor(cursor)  # Set the cursor back to the QTextEdit
        self.modelEditor.setFocus()  # Foca no editor após inserção


class MSGHomolog(QDialog):
    def __init__(self, dados, icons_dir, parent=None):
        super().__init__(parent)
        self.dados = dados
        self.icons_dir = Path(icons_dir)
        self.templatePath = PLANEJAMENTO_DIR / "last_template_homolog.txt"
        self.setWindowTitle("Mensagem de Homologação")
        self.resize(1500, 800)

        self.image_cache = load_images(self.icons_dir, ["apply.png", "copy.png"])

        self.setObjectName("AlertaPrazoDialog")

        self.setStyleSheet("""
            #AlertaPrazoDialog {
                background-color: black;
                color: white;
                font-size: 12pt;
            }
            QDialog {
                font-size: 12pt;
            }
            QTextEdit, QListWidget {
                background-color: white; 
                color: black;
                font-size: 12pt;
            }
            QGroupBox {
                border: 2px solid gray;
                border-radius: 5px;
                margin-top: 0.5em;
                font-size: 14pt;
                font-weight: bold;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)

        self.mainLayout = QVBoxLayout(self)

        # Configuração dos GroupBoxes e seus layouts
        self.setupGroupBoxes()

        # Configuração dos botões
        self.setupButtonsLayout()

        self.loadLastTemplate()

    def setupGroupBoxes(self):
        groupBoxLayout = QHBoxLayout()  # Layout horizontal para os GroupBoxes
        
        self.variableListGroupBox = QGroupBox("Índice de Variáveis")
        variableListLayout = QVBoxLayout()
        self.variableList = QListWidget()
        self.variableList.addItems(sorted(f"{{{{{key}}}}}" for key in self.dados.keys()))
        self.variableList.setMaximumWidth(300)  # Limita o tamanho do QListWidget

        variableListLayout.addWidget(self.variableList)
        self.variableListGroupBox.setLayout(variableListLayout)
        self.variableListGroupBox.setMaximumWidth(300)  # Limita o tamanho do QGroupBox

        groupBoxLayout.addWidget(self.variableListGroupBox)

        # Conectar o evento itemDoubleClicked ao método insertVariable
        self.variableList.itemDoubleClicked.connect(self.insertVariable)

        # Grupo para o editor de modelo
        self.modelEditorGroupBox = QGroupBox("Campo para Edição do Modelo")
        modelEditorLayout = QVBoxLayout()
        self.modelEditor = QTextEdit()
        modelEditorLayout.addWidget(self.modelEditor)
        self.modelEditorGroupBox.setLayout(modelEditorLayout)
        groupBoxLayout.addWidget(self.modelEditorGroupBox)

        # Grupo para o visualizador de texto
        self.textViewerGroupBox = QGroupBox("Campo para Visualização da Mensagem")
        textViewerLayout = QVBoxLayout()
        self.textViewer = QTextEdit()
        self.textViewer.setReadOnly(True)
        textViewerLayout.addWidget(self.textViewer)
        self.textViewerGroupBox.setLayout(textViewerLayout)
        groupBoxLayout.addWidget(self.textViewerGroupBox)

        self.mainLayout.addLayout(groupBoxLayout) 

    def setupButtonsLayout(self):
        self.buttons_layout = QHBoxLayout()
        self.createButtons()
        self.mainLayout.addLayout(self.buttons_layout)  # Adiciona o layout dos botões ao layout principal

    def createButtons(self):
        icon_size = QSize(40, 40)  # Tamanho do ícone para todos os botões
        self.button_specs = [
            ("Aplicar Modelo", self.image_cache['apply'], self.applyTemplate, "Aplica o modelo atual", icon_size),
            ("Copiar Mensagem", self.image_cache['copy'], self.copyTextToClipboard, "Copia a mensagem para a área de transferência", icon_size),
        ]

        for text, icon, callback, tooltip, icon_size in self.button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self, icon_size=icon_size)
            self.buttons_layout.addWidget(btn)

    def applyTemplate(self):
        user_template = self.modelEditor.toPlainText()
        self.textViewer.setHtml(self.renderTemplate(user_template, self.dados))

    def loadLastTemplate(self):
        try:
            if os.path.exists(self.templatePath):
                with open(self.templatePath, 'r', encoding='utf-8') as file:
                    last_template = file.read()
                self.modelEditor.setPlainText(last_template)
            else:
                self.modelEditor.setPlainText("Digite o texto da mensagem aqui...")
            self.applyTemplate()  # Aplica o modelo após carregar
        except Exception as e:
            QMessageBox.warning(self, "Erro ao carregar template", str(e))

    def closeEvent(self, event):
        try:
            current_template = self.modelEditor.toPlainText()
            with open(self.templatePath, 'w', encoding='utf-8') as file:
                file.write(current_template)
        except Exception as e:
            QMessageBox.warning(self, "Erro ao salvar template", str(e))
        super().closeEvent(event)
        
    def renderTemplate(self, template, data):
        mes_atual = datetime.now().strftime("%b").upper()
        ano_atual = datetime.now().strftime('%Y')
        header = f"R000000Z/<span style='color: blue;'>{mes_atual}</span>/<span style='color: blue;'>{ano_atual}</span><br>"
        # Substitui quebras de linha por <br> para HTML
        template = template.replace('\n', '<br>')

        rendered_text = header + template
        for key, value in data.items():
            rendered_text = re.sub(rf"{{{{\s*{key}\s*}}}}", f"<span style='color: blue;'>{value}</span>", rendered_text)
        return rendered_text

    def copyTextToClipboard(self):
        text = self.textViewer.toPlainText()
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", "Texto copiado para a área de transferência.")

    def insertVariable(self, item):
        cursor = self.modelEditor.textCursor()  # Get the current cursor from QTextEdit
        
        # Se o cursor não estiver ativo ou a posição for zero (início do texto)
        if not cursor or cursor.position() == 0:
            cursor.movePosition(QTextCursor.MoveOperation.End)  # Move o cursor para o final do texto
        
        cursor.insertText(item.text())  # Insert text at cursor's current position
        
        # Move o cursor para logo após o texto inserido
        cursor.setPosition(cursor.position() + len(item.text()))
        
        self.modelEditor.setTextCursor(cursor)  # Set the cursor back to the QTextEdit
        self.modelEditor.setFocus()  # Foca no editor após inserção


class MSGPublicacao(QDialog):
    def __init__(self, dados, icons_dir, parent=None):
        super().__init__(parent)
        self.dados = dados
        self.icons_dir = Path(icons_dir)
        self.templatePath = PLANEJAMENTO_DIR / "last_template_publicacao.txt"
        self.setWindowTitle("Mensagem de Publicação de Edital")
        self.resize(1500, 800)

        self.image_cache = load_images(self.icons_dir, ["apply.png", "copy.png"])

        self.setObjectName("AlertaPrazoDialog")

        self.setStyleSheet("""
            #AlertaPrazoDialog {
                background-color: black;
                color: white;
                font-size: 12pt;
            }
            QDialog {
                font-size: 12pt;
            }
            QTextEdit, QListWidget {
                background-color: white; 
                color: black;
                font-size: 12pt;
            }
            QGroupBox {
                border: 2px solid gray;
                border-radius: 5px;
                margin-top: 0.5em;
                font-size: 14pt;
                font-weight: bold;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)

        self.mainLayout = QVBoxLayout(self)

        # Configuração dos GroupBoxes e seus layouts
        self.setupGroupBoxes()

        # Configuração dos botões
        self.setupButtonsLayout()

        self.loadLastTemplate()

    def setupGroupBoxes(self):
        groupBoxLayout = QHBoxLayout()  # Layout horizontal para os GroupBoxes
        
        self.variableListGroupBox = QGroupBox("Índice de Variáveis")
        variableListLayout = QVBoxLayout()
        self.variableList = QListWidget()
        self.variableList.addItems(sorted(f"{{{{{key}}}}}" for key in self.dados.keys()))
        self.variableList.setMaximumWidth(300)  # Limita o tamanho do QListWidget

        variableListLayout.addWidget(self.variableList)
        self.variableListGroupBox.setLayout(variableListLayout)
        self.variableListGroupBox.setMaximumWidth(300)  # Limita o tamanho do QGroupBox

        groupBoxLayout.addWidget(self.variableListGroupBox)

        # Conectar o evento itemDoubleClicked ao método insertVariable
        self.variableList.itemDoubleClicked.connect(self.insertVariable)

        # Grupo para o editor de modelo
        self.modelEditorGroupBox = QGroupBox("Campo para Edição do Modelo")
        modelEditorLayout = QVBoxLayout()
        self.modelEditor = QTextEdit()
        modelEditorLayout.addWidget(self.modelEditor)
        self.modelEditorGroupBox.setLayout(modelEditorLayout)
        groupBoxLayout.addWidget(self.modelEditorGroupBox)

        # Grupo para o visualizador de texto
        self.textViewerGroupBox = QGroupBox("Campo para Visualização da Mensagem")
        textViewerLayout = QVBoxLayout()
        self.textViewer = QTextEdit()
        self.textViewer.setReadOnly(True)
        textViewerLayout.addWidget(self.textViewer)
        self.textViewerGroupBox.setLayout(textViewerLayout)
        groupBoxLayout.addWidget(self.textViewerGroupBox)

        self.mainLayout.addLayout(groupBoxLayout) 

    def setupButtonsLayout(self):
        self.buttons_layout = QHBoxLayout()
        self.createButtons()
        self.mainLayout.addLayout(self.buttons_layout)  # Adiciona o layout dos botões ao layout principal

    def createButtons(self):
        icon_size = QSize(40, 40)  # Tamanho do ícone para todos os botões
        self.button_specs = [
            ("Aplicar Modelo", self.image_cache['apply'], self.applyTemplate, "Aplica o modelo atual", icon_size),
            ("Copiar Mensagem", self.image_cache['copy'], self.copyTextToClipboard, "Copia a mensagem para a área de transferência", icon_size),
        ]

        for text, icon, callback, tooltip, icon_size in self.button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self, icon_size=icon_size)
            self.buttons_layout.addWidget(btn)

    def applyTemplate(self):
        user_template = self.modelEditor.toPlainText()
        self.textViewer.setHtml(self.renderTemplate(user_template, self.dados))

    def loadLastTemplate(self):
        try:
            if os.path.exists(self.templatePath):
                with open(self.templatePath, 'r', encoding='utf-8') as file:
                    last_template = file.read()
                self.modelEditor.setPlainText(last_template)
            else:
                self.modelEditor.setPlainText("Digite o texto da mensagem aqui...")
            self.applyTemplate()  # Aplica o modelo após carregar
        except Exception as e:
            QMessageBox.warning(self, "Erro ao carregar template", str(e))

    def closeEvent(self, event):
        try:
            current_template = self.modelEditor.toPlainText()
            with open(self.templatePath, 'w', encoding='utf-8') as file:
                file.write(current_template)
        except Exception as e:
            QMessageBox.warning(self, "Erro ao salvar template", str(e))
        super().closeEvent(event)
        
    def renderTemplate(self, template, data):
        mes_atual = datetime.now().strftime("%b").upper()
        ano_atual = datetime.now().strftime('%Y')
        header = f"R000000Z/<span style='color: blue;'>{mes_atual}</span>/<span style='color: blue;'>{ano_atual}</span><br>"
        # Substitui quebras de linha por <br> para HTML
        template = template.replace('\n', '<br>')

        rendered_text = header + template
        for key, value in data.items():
            rendered_text = re.sub(rf"{{{{\s*{key}\s*}}}}", f"<span style='color: blue;'>{value}</span>", rendered_text)
        return rendered_text

    def copyTextToClipboard(self):
        text = self.textViewer.toPlainText()
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", "Texto copiado para a área de transferência.")

    def insertVariable(self, item):
        cursor = self.modelEditor.textCursor()  # Get the current cursor from QTextEdit
        
        # Se o cursor não estiver ativo ou a posição for zero (início do texto)
        if not cursor or cursor.position() == 0:
            cursor.movePosition(QTextCursor.MoveOperation.End)  # Move o cursor para o final do texto
        
        cursor.insertText(item.text())  # Insert text at cursor's current position
        
        # Move o cursor para logo após o texto inserido
        cursor.setPosition(cursor.position() + len(item.text()))
        
        self.modelEditor.setTextCursor(cursor)  # Set the cursor back to the QTextEdit
        self.modelEditor.setFocus()  # Foca no editor após inserção



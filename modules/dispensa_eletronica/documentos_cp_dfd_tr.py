import sys
import string
import json
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import fitz  # PyMuPDF
from docxtpl import DocxTemplate

class DocumentDetailsWidget(QWidget):
    def __init__(self, df_registro_selecionado, parent=None):
        super().__init__(parent)
        self.df_registro_selecionado = df_registro_selecionado
        
        # Configurando layout principal
        main_layout = QVBoxLayout(self)
        
        # Adicionando QLineEdit "CP nº" e botão "Adicionar PDF"
        cp_layout = QHBoxLayout()
        cp_label = QLabel("CP nº")
        cp_label.setStyleSheet("color: white; font-size: 12pt;")
        self.cp_edit = QLineEdit()
        self.cp_edit.setStyleSheet("font-size: 12pt;")
        cp_layout.addWidget(cp_label)
        cp_layout.addWidget(self.cp_edit)
            
        main_layout.addLayout(cp_layout)
        
        # Adicionando "Meta do PAR" na mesma linha do cp_layout
        par_label = QLabel("Meta do PAR:")
        par_label.setStyleSheet("color: white; font-size: 12pt;")
        self.par_edit = QLineEdit()
        self.par_edit.setText(self.get_value('cod_par'))
        self.par_edit.setStyleSheet("font-size: 12pt;")
        cp_layout.addWidget(par_label)
        cp_layout.addWidget(self.par_edit)

        # Adicionando "Prioridade" na mesma linha do cp_layout
        prioridade_label = QLabel("Prioridade:")
        prioridade_label.setStyleSheet("color: white; font-size: 12pt;")
        self.prioridade_edit = QLineEdit()
        self.prioridade_edit.setText(self.get_value('cod_par'))
        self.prioridade_edit.setStyleSheet("font-size: 12pt;")
        cp_layout.addWidget(prioridade_label)
        cp_layout.addWidget(self.prioridade_edit)

        # Adicionando outros campos
        self.add_label_edit_pair(main_layout, "Do:", "Responsável pela demanda")
        self.add_label_edit_pair(main_layout, "Ao:", "Encarregado da Divisão de Obtenção")
        self.add_label_edit_pair(main_layout, "Endereço:", self.get_value('endereco'))
        
        # Adicionando CEP, E-mail e Telefone na mesma linha
        contact_layout = QHBoxLayout()
        self.add_label_edit_pair(contact_layout, "CEP:", self.get_value('cep'))
        self.add_label_edit_pair(contact_layout, "E-mail:", self.get_value('email'))
        self.add_label_edit_pair(contact_layout, "Telefone:", self.get_value('telefone'))
        main_layout.addLayout(contact_layout)
        
        # Adicionando campo "Justificativa" como QTextEdit
        self.add_label_textedit_pair(main_layout, "Justificativa:", self.get_value('justificativa'))
        
        editar_anexos_layout = QHBoxLayout()
        add_pdf_button = QPushButton("Adicionar PDF")
        add_pdf_button.setStyleSheet("font-size: 12pt; padding: 5px;")
        add_pdf_button.clicked.connect(self.add_pdf_to_merger)
        editar_anexos_layout.addWidget(add_pdf_button)
        main_layout.addLayout(editar_anexos_layout)

    def add_label_edit_pair(self, layout, label_text, placeholder_text):
        layout_pair = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("color: white; font-size: 12pt;")
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder_text)
        line_edit.setStyleSheet("""
            QLineEdit {
                font-size: 12pt;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: #f0f0f0;
            }
        """)
        layout_pair.addWidget(label)
        layout_pair.addWidget(line_edit)
        layout.addLayout(layout_pair)
    
    def add_label_textedit_pair(self, layout, label_text, text):
        layout_pair = QVBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("color: white; font-size: 12pt;")
        text_edit = QTextEdit()
        text_edit.setText(text)
        text_edit.setStyleSheet("font-size: 12pt;")
        layout_pair.addWidget(label)
        layout_pair.addWidget(text_edit)
        layout.addLayout(layout_pair)
    
    def get_value(self, column_name):
        value = self.df_registro_selecionado[column_name].iloc[0]
        return str(value) if value is not None else ""
    
    def get_value(self, column_name):
        value = self.df_registro_selecionado[column_name].iloc[0]
        return str(value) if value is not None else ""
    
    def add_pdf_to_merger(self):
        cp_number = self.cp_edit.text()
        if cp_number:
            print(f"Adicionar PDF para CP nº {cp_number}")
            # Implementação do método de adicionar PDF
        else:
            QMessageBox.warning(self, "Erro", "Por favor, insira um número de CP válido.")

    def add_pdf_to_merger(self):
        cp_number = self.cp_edit.text()
        if cp_number:
            pdf_add_dialog = PDFAddDialog(self.df_registro_selecionado, ICONS_DIR, self)
            if pdf_add_dialog.exec():
                print(f"Adicionar PDF para CP nº {cp_number}")
                # Aqui você pode adicionar a lógica para manipular o PDF com os dados do diálogo
            else:
                print("Ação de adicionar PDF cancelada.")
        else:
            QMessageBox.warning(self, "Erro", "Por favor, insira um número de CP válido.")

class PDFAddDialog(QDialog):

    def __init__(self, df_registro_selecionado, icons_dir, parent=None):
        super().__init__(parent)
        self.df_registro_selecionado = df_registro_selecionado
        self.ICONS_DIR = Path(icons_dir)
        self.icon_existe = QIcon(str(self.ICONS_DIR / "checked.png"))
        self.icon_nao_existe = QIcon(str(self.ICONS_DIR / "cancel.png"))
        self.id_processo = df_registro_selecionado['id_processo'].iloc[0]
        self.tipo = df_registro_selecionado['tipo'].iloc[0]
        self.ano = df_registro_selecionado['ano'].iloc[0]
        self.numero = df_registro_selecionado['numero'].iloc[0]
        self.setWindowTitle('Adicionar PDF')
        self.setup_ui()
        self.load_file_paths()

    def setup_ui(self):
        self.setFixedSize(1100, 600) 
        layout = QVBoxLayout(self)
        
        # Add the header with title
        header_widget = self.create_header()
        layout.addWidget(header_widget)

        # data_view
        self.data_view = QTreeWidget()
        self.data_view.setHeaderHidden(True)
        self.data_view.setStyleSheet("""
            QTreeWidget::item { 
                height: 40px;
                font-size: 14px;
            }
        """)  # Ajusta a altura das linhas e o tamanho da fonte
        layout.addWidget(self.data_view)

        # Add initial items with sublevels
        self.add_initial_items()

        # Add buttons to add and delete anexos and sublevels
        button_layout = QHBoxLayout()

        add_button = QPushButton("Adicionar Anexo")
        add_button.setStyleSheet("font-size: 14px;")  # Aplica o estilo ao botão
        add_button.clicked.connect(self.add_anexo)
        button_layout.addWidget(add_button)

        add_sublevel_button = QPushButton("Adicionar Subnível")
        add_sublevel_button.setStyleSheet("font-size: 14px;")  # Aplica o estilo ao botão
        add_sublevel_button.clicked.connect(self.add_sublevel)
        button_layout.addWidget(add_sublevel_button)

        delete_button = QPushButton("Deletar")
        delete_button.setStyleSheet("font-size: 14px;")  # Aplica o estilo ao botão
        delete_button.clicked.connect(self.delete_item)
        button_layout.addWidget(delete_button)

        # File selection button
        file_button = QPushButton("Selecionar Arquivo")
        file_button.setStyleSheet("font-size: 14px;")  # Aplica o estilo ao botão
        file_button.clicked.connect(self.select_pdf_file)
        button_layout.addWidget(file_button)
        
        reset_button = QPushButton("Resetar")
        reset_button.setStyleSheet("font-size: 14px;")
        reset_button.clicked.connect(self.reset_data)
        button_layout.addWidget(reset_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def reset_data(self):
        # Cria uma caixa de mensagem de confirmação
        reply = QMessageBox.question(self, 'Confirmar Reset',
                                    "Tem certeza de que deseja resetar todos os dados e restaurar os valores padrão? Essa decisão é irreversível.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            file_dir = DISPENSA_DIR / "json"
            file_path = file_dir / f'DE_{self.numero}-{self.ano}_file_paths.json'
            if file_path.exists():
                file_path.unlink()
            self.data_view.clear()
            self.add_initial_items()
            print("Dados resetados para padrão inicial e arquivo JSON deletado.")
        else:
            print("Ação de resetar cancelada.")

    def select_pdf_file(self):
        selected_item = self.data_view.currentItem()
        if selected_item:
            file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar PDF", "", "PDF Files (*.pdf)")
            if file_path:
                selected_item.setText(0, f'{selected_item.text(0).split(" - ")[0]} - {file_path}')
                selected_item.setIcon(0, self.icon_existe)
                self.save_file_paths()
            else:
                selected_item.setIcon(0, self.icon_nao_existe)

    def save_file_paths(self):
        items = []
        for i in range(self.data_view.topLevelItemCount()):
            parent_item = self.data_view.topLevelItem(i)
            item_data = {
                'text': parent_item.text(0),
                'children': []
            }
            for j in range(parent_item.childCount()):
                child_item = parent_item.child(j)
                child_data = {
                    'text': child_item.text(0)
                }
                item_data['children'].append(child_data)
            items.append(item_data)

        file_dir = DISPENSA_DIR / "json"
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / f'DE_{self.numero}-{self.ano}_file_paths.json'
        with open(file_path, 'w') as file:
            json.dump(items, file)

    def load_file_paths(self):
        file_dir = DISPENSA_DIR / "json"
        file_path = file_dir / f'DE_{self.numero}-{self.ano}_file_paths.json'
        if file_path.exists():
            with open(file_path, 'r') as file:
                items = json.load(file)
                self.data_view.clear()  # Limpa itens existentes antes de carregar
                for item in items:
                    parent_item = QTreeWidgetItem(self.data_view, [item['text']])
                    parent_item.setFont(0, QFont('SansSerif', 14))
                    for child in item['children']:
                        child_item = QTreeWidgetItem(parent_item, [child['text']])
                        child_item.setFont(0, QFont('SansSerif', 14))
                        # Definir ícones se necessário baseado em mais lógica
                        child_item.setIcon(0, self.icon_existe if ' - ' in child['text'] else self.icon_nao_existe)
                    parent_item.setExpanded(True)


    def create_header(self):
        html_text = f"{self.tipo} nº {self.numero}/{self.ano}<br>"
        
        self.titleLabel = QLabel()
        self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
        self.titleLabel.setStyleSheet("color: black; font-size: 30px; font-weight: bold;")
        self.titleLabel.setText(html_text)

        self.header_layout = QHBoxLayout()
        self.header_layout.addWidget(self.titleLabel)

        header_widget = QWidget()
        header_widget.setLayout(self.header_layout)

        return header_widget

    def add_initial_items(self):
        # Verifica se o arquivo JSON já existe e carrega os itens a partir dele
        file_dir = DISPENSA_DIR / "json"
        file_path = file_dir / f'DE_{self.numero}-{self.ano}_file_paths.json'
        if file_path.exists():
            return  # Se existe, não adiciona os itens iniciais; load_file_paths cuidará de carregar os dados

        # Caso contrário, adiciona os itens iniciais como fallback
        initial_items = {
            "Anexo A - Documento de Formalização de Demanda": [
                "Relatório do SAFIN",
                "Especificação e Quantidade do Material"
            ],
            "Anexo B - Termo de Referência": [
                "Pesquisa de Preços"
            ],
            "Anexo C - Declaração de Adequação Orçamentária": [
                "Relatório do PDM/Catser"
            ]
        }
        for parent_text, children in initial_items.items():
            parent_item = QTreeWidgetItem(self.data_view, [parent_text])
            parent_item.setFont(0, QFont('SansSerif', 14))
            for child_text in children:
                child_item = QTreeWidgetItem(parent_item, [child_text])
                child_item.setIcon(0, self.icon_nao_existe)
                child_item.setForeground(0, QBrush(QColor(0, 0, 0)))
                child_item.setFont(0, QFont('SansSerif', 14))
            parent_item.setExpanded(True)


    def add_anexo(self):
        text, ok = QInputDialog.getText(self, 'Adicionar Anexo', 'Digite o nome do anexo:')
        if ok and text:
            current_count = self.data_view.topLevelItemCount()
            new_anexo = f"Anexo {chr(65 + current_count)} - {text}"
            new_anexo_item = QTreeWidgetItem(self.data_view, [new_anexo])
            new_anexo_item.setFont(0, QFont('SansSerif', 14))
            new_anexo_item.setIcon(0, self.icon_nao_existe)
            self.save_file_paths()  # Salva as mudanças após adicionar um novo anexo

    def add_sublevel(self):
        selected_item = self.data_view.currentItem()
        if selected_item is None:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um anexo para adicionar um subnível.")
            return

        text, ok = QInputDialog.getText(self, 'Adicionar Subnível', 'Digite o nome do subnível:')
        if ok and text:
            sublevel_item = QTreeWidgetItem(selected_item, [text])
            sublevel_item.setFont(0, QFont('SansSerif', 14))
            sublevel_item.setIcon(0, self.icon_nao_existe)
            selected_item.setExpanded(True)
            self.save_file_paths() 

    def delete_item(self):
        selected_item = self.data_view.currentItem()
        if selected_item is None:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um item para deletar.")
            return

        item_text = selected_item.text(0)
        reply = QMessageBox.question(self, 'Confirmação de Deleção',
                                    f'Tem certeza que deseja deletar "{item_text}"?',
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            parent_item = selected_item.parent()
            if parent_item is None:
                index = self.data_view.indexOfTopLevelItem(selected_item)
                self.data_view.takeTopLevelItem(index)
            else:
                parent_item.removeChild(selected_item)
            self.save_file_paths() 

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_item()
        else:
            super().keyPressEvent(event)


# class TreeItem:
#     def __init__(self, data, parent=None):
#         self.parentItem = parent
#         self.itemData = data
#         self.childItems = []

#     def appendChild(self, item):
#         self.childItems.append(item)

#     def child(self, row):
#         return self.childItems[row]

#     def childCount(self):
#         return len(self.childItems)

#     def columnCount(self):
#         return len(self.itemData)

#     def data(self, column):
#         try:
#             return self.itemData[column]
#         except IndexError:
#             return None

#     def parent(self):
#         return self.parentItem

#     def row(self):
#         if self.parentItem:
#             return self.parentItem.childItems.index(self)
#         return 0

# class TreeModel(QAbstractItemModel):
#     def __init__(self, title, data, parent=None):
#         super(TreeModel, self).__init__(parent)
#         self.rootItem = TreeItem((title,))
#         self.setupModelData(data, self.rootItem)

#     def getItemLevel(self, index):
#         level = 0
#         while index.parent().isValid():
#             index = index.parent()
#             level += 1
#         return level

#     def columnCount(self, parent):
#         if parent.isValid():
#             return parent.internalPointer().columnCount()
#         return self.rootItem.columnCount()

#     def data(self, index, role):
#         if not index.isValid():
#             return None
#         item = index.internalPointer()
#         text = item.data(index.column())
#         level = self.getItemLevel(index)
#         if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
#             if level == 1:
#                 parts = text.split(' - ')
#                 if len(parts) == 2:
#                     if parts[1] == "Arquivo não definido":
#                         formatted_text = f"{parts[0]} - <span style='color:red;'>{parts[1]}</span>"
#                         print(f"Formatted text for 'Arquivo não definido': {formatted_text}")
#                         return formatted_text
#                     else:
#                         formatted_text = f"{parts[0]} - <span style='color:green;'>{parts[1]}</span>"
#                         print(f"Formatted text for file path: {formatted_text}")
#                         return formatted_text
#             return text
#         return None

#     def setData(self, index, value, role):
#         if index.isValid() and role == Qt.ItemDataRole.EditRole:
#             item = index.internalPointer()
#             item.itemData[0] = value
#             self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
#             return True
#         return False

#     def flags(self, index):
#         if not index.isValid():
#             return Qt.ItemFlag.ItemIsEnabled
#         return QAbstractItemModel.flags(self, index) | Qt.ItemFlag.ItemIsEditable

#     def headerData(self, section, orientation, role):
#         if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
#             return self.rootItem.data(section)
#         return None

#     def index(self, row, column, parent):
#         if not self.hasIndex(row, column, parent):
#             return QModelIndex()

#         if not parent.isValid():
#             parentItem = self.rootItem
#         else:
#             parentItem = parent.internalPointer()

#         childItem = parentItem.child(row)
#         if childItem:
#             return self.createIndex(row, column, childItem)
#         return QModelIndex()

#     def parent(self, index):
#         if not index.isValid():
#             return QModelIndex()

#         childItem = index.internalPointer()
#         parentItem = childItem.parent()

#         if parentItem == self.rootItem:
#             return QModelIndex()

#         return self.createIndex(parentItem.row(), 0, parentItem)

#     def rowCount(self, parent):
#         if parent.column() > 0:
#             return 0

#         if not parent.isValid():
#             parentItem = self.rootItem
#         else:
#             parentItem = parent.internalPointer()

#         return parentItem.childCount()

#     def setupModelData(self, data, parent):
#         for section, items in data.items():
#             sectionItem = TreeItem([section], parent)
#             parent.appendChild(sectionItem)
#             for item, path in items:
#                 itemItem = TreeItem([f"{item} - {path}"], sectionItem)
#                 sectionItem.appendChild(itemItem)

# class ButtonDelegate(QStyledItemDelegate):
#     def __init__(self, parent=None):
#         super(ButtonDelegate, self).__init__(parent)
#         self.parent = parent
#         self.icon_cancel = QIcon(str(parent.ICONS_DIR / "cancel.png"))
#         self.icon_search = QIcon(str(parent.ICONS_DIR / "localizar_pdf.png"))

#     def paint(self, painter, option, index):
#         if not index.isValid():
#             return

#         item = index.internalPointer()
#         level = self.parent.treeModel.getItemLevel(index)
#         text = item.data(index.column())
#         if level == 1:  # Apply formatting only to level 2 items
#             parts = text.split(' - ')
#             if len(parts) == 2:
#                 if parts[1] == "Arquivo não definido":
#                     formatted_text = f"{parts[0]} - <span style='color:red;'>{parts[1]}</span>"
#                 else:
#                     formatted_text = f"{parts[0]} - <span style='color:green;'>{parts[1]}</span>"
#                 option.widget.style().drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter)
#                 text_option = QTextOption()
#                 text_option.setWrapMode(QTextOption.WrapMode.WordWrap)
#                 painter.save()
#                 painter.setFont(option.font)
#                 painter.setPen(QColor(option.palette.color(QPalette.ColorRole.Text)))
#                 painter.translate(option.rect.left(), option.rect.top())
#                 text_document = QTextDocument()
#                 text_document.setHtml(formatted_text)
#                 text_document.drawContents(painter)
#                 painter.restore()

#                 # Draw buttons
#                 button_width = 25
#                 button_height = 25
#                 spacing = 5
#                 remove_button_rect = QRect(int(option.rect.right() - button_width * 2 - spacing),
#                                            int(option.rect.top() + (option.rect.height() - button_height) / 2),
#                                            button_width,
#                                            button_height)
#                 select_button_rect = QRect(int(option.rect.right() - button_width - spacing),
#                                            int(option.rect.top() + (option.rect.height() - button_height) / 2),
#                                            button_width,
#                                            button_height)
#                 self.icon_cancel.paint(painter, remove_button_rect, Qt.AlignmentFlag.AlignCenter)
#                 self.icon_search.paint(painter, select_button_rect, Qt.AlignmentFlag.AlignCenter)

#             else:
#                 super().paint(painter, option, index)
#         else:
#             # Paint without HTML formatting for level 1 items
#             option.widget.style().drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter)
#             painter.save()
#             painter.setFont(option.font)
#             painter.setPen(QColor(option.palette.color(QPalette.ColorRole.Text)))
#             painter.drawText(option.rect, Qt.AlignmentFlag.AlignLeft, text)
#             painter.restore()

#     def createEditor(self, parent, option, index):
#         if self.parent.treeModel.getItemLevel(index) == 1:
#             item = index.internalPointer()
#             editor = TreeWidgetItem(item.data(0), self.icon_cancel, self.icon_search, parent)
#             editor.removeButton.clicked.connect(lambda: self.removeItem(index))
#             editor.selectButton.clicked.connect(lambda: self.selectFile(editor, index))
#             return editor
#         return super().createEditor(parent, option, index)

#     def setEditorData(self, editor, index):
#         if self.parent.treeModel.getItemLevel(index) == 1:
#             item = index.internalPointer()
#             editor.setText(item.data(0))
#         else:
#             super().setEditorData(editor, index)

#     def setModelData(self, editor, model, index):
#         if self.parent.treeModel.getItemLevel(index) == 1:
#             model.setData(index, editor.textLabel.text(), Qt.ItemDataRole.EditRole)
#         else:
#             super().setModelData(editor, model, index)

#     def updateEditorGeometry(self, editor, option, index):
#         editor.setGeometry(option.rect)

#     def removeItem(self, index):
#         self.parent.treeModel.removeRow(index.row(), index.parent())

#     def selectFile(self, editor, index):
#         file_dialog = QFileDialog(self.parent)
#         file_path, _ = file_dialog.getOpenFileName(filter="PDF files (*.pdf)")
#         if file_path:
#             # Update the text in the editor
#             current_text = editor.textLabel.text()
#             parts = current_text.split(' - ')
#             if len(parts) == 2:
#                 new_text = f"{parts[0]} - <span style='color:green;'>{file_path}</span>"
#                 editor.setText(new_text)
#                 # Update the model data
#                 self.parent.treeModel.setData(index, new_text, Qt.ItemDataRole.EditRole)
                
# class TreeWidgetItem(QWidget):
#     def __init__(self, text, icon_cancel, icon_search, parent=None):
#         super(TreeWidgetItem, self).__init__(parent)
#         layout = QHBoxLayout(self)
#         self.textLabel = QLabel(self)
#         self.textLabel.setTextFormat(Qt.TextFormat.RichText)  # Enable RichText
#         self.setText(text)
        
#         self.removeButton = QPushButton()
#         self.removeButton.setIcon(icon_cancel)
#         self.removeButton.setFixedSize(25, 25)
        
#         self.selectButton = QPushButton()
#         self.selectButton.setIcon(icon_search)
#         self.selectButton.setFixedSize(25, 25)
        
#         layout.addWidget(self.textLabel)
#         layout.addWidget(self.removeButton)
#         layout.addWidget(self.selectButton)
#         layout.setContentsMargins(0, 0, 0, 0)
#         self.setLayout(layout)

#     def setText(self, text):
#         parts = text.split(' - ')
#         if len(parts) == 2:
#             if parts[1] == "Arquivo não definido":
#                 formatted_text = f"{parts[0]} - <span style='color:red;'>{parts[1]}</span>"
#                 print(f"Setting text for 'Arquivo não definido': {formatted_text}")
#                 self.textLabel.setText(formatted_text)
#             else:
#                 formatted_text = f"{parts[0]} - <span style='color:green;'>{parts[1]}</span>"
#                 print(f"Setting text for file path: {formatted_text}")
#                 self.textLabel.setText(formatted_text)
#         else:
#             self.textLabel.setText(text)

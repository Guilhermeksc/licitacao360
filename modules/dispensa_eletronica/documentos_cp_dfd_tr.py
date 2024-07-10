import sys
import string
import json
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import fitz
from docxtpl import DocxTemplate
import pandas as pd

class DocumentDetailsWidget(QWidget):
    def __init__(self, df_registro_selecionado, parent=None):
        super().__init__(parent)
        self.df_registro_selecionado = df_registro_selecionado
        
        # Configurando layout principal
        main_layout = QVBoxLayout(self)
        
        # Adicionando QLineEdit "CP nº" e botão "Adicionar PDF"
        cp_layout = QHBoxLayout()
        cp_label = QLabel("Comunicação Padronizada nº")
        cp_label.setStyleSheet("color: white; font-size: 12pt;")
        self.cp_edit = QLineEdit(self.get_value('comunicacao_padronizada', ''))
        self.cp_edit.setStyleSheet("""
            QLineEdit {
                font-size: 12pt;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: #f0f0f0;
            }
        """)
        
        cp_layout.addWidget(cp_label)
        cp_layout.addWidget(self.cp_edit)
            
        main_layout.addLayout(cp_layout)
        
        responsavel_layout = QHBoxLayout()
        responsavel_label = QLabel("Do:")
        responsavel_label.setStyleSheet("color: white; font-size: 12pt;")
        self.responsavel_edit = QLineEdit(self.get_value('do_resposavel', 'Responsável pela Demanda'))
        self.responsavel_edit.setStyleSheet("""
            QLineEdit {
                font-size: 12pt;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: #f0f0f0;
            }
        """)
        responsavel_layout.addWidget(responsavel_label)
        responsavel_layout.addWidget(self.responsavel_edit)
        main_layout.addLayout(responsavel_layout)

        encarregado_obtencao_layout = QHBoxLayout()
        encarregado_obtencao_label = QLabel("Ao:")
        encarregado_obtencao_label.setStyleSheet("color: white; font-size: 12pt;")
        self.encarregado_obtencao_edit = QLineEdit(self.get_value('ao_responsavel', 'Encarregado da Divisão de Obtenção'))
        self.encarregado_obtencao_edit.setStyleSheet("""
            QLineEdit {
                font-size: 12pt;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: #f0f0f0;
            }
        """)
        encarregado_obtencao_layout.addWidget(encarregado_obtencao_label)
        encarregado_obtencao_layout.addWidget(self.encarregado_obtencao_edit)
        main_layout.addLayout(encarregado_obtencao_layout)
        
        anexos_layout = QHBoxLayout()
        anexos_label = QLabel("Anexos:")
        anexos_label.setStyleSheet("color: white; font-size: 12pt;")
        add_pdf_button = QPushButton("Selecionar o Anexos")
        add_pdf_button.setStyleSheet("font-size: 12pt; padding: 5px;")
        add_pdf_button.clicked.connect(self.add_pdf_to_merger)
        anexos_layout.addWidget(anexos_label)
        anexos_layout.addWidget(add_pdf_button)
            
        main_layout.addLayout(anexos_layout)  

        # Adicionando campo "Justificativa" como QTextEdit
        self.add_label_textedit_pair(main_layout, "Justificativa:", self.get_value('justificativa'))

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
    
    def get_value(self, column_name, default_value=''):
        value = self.df_registro_selecionado[column_name].iloc[0]
        return str(value) if value else default_value
    
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
        self.setFixedSize(1500, 780)  # Tamanho ajustado para acomodar todos os componentes

        # Layout principal vertical
        main_layout = QVBoxLayout(self)

        # Layout para a visualização, slider e QTreeWidget
        view_and_slider_and_tree_layout = QHBoxLayout()
        # Layout vertical para a visualização do PDF e botões de navegação
        pdf_view_layout = QVBoxLayout()

        # DraggableGraphicsView para visualizar o PDF
        self.pdf_view = DraggableGraphicsView()
        self.scene = QGraphicsScene()
        self.pdf_view.setScene(self.scene)
        self.pdf_view.setFixedSize(550, 730)  # Tamanho da visualização do PDF
        pdf_view_layout.addWidget(self.pdf_view)

        # Botões de navegação de páginas abaixo da visualização do PDF
        navigation_widget = QWidget()
        nav_buttons_layout = QHBoxLayout(navigation_widget)
        
        self.prev_page_button = QPushButton("← Página Anterior")
        self.prev_page_button.clicked.connect(self.prev_page)

        # Inicializa o QLabel para o contador de páginas
        self.page_label = QLabel("1 de 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("font-size: 14px; margin: 5px;")

        self.next_page_button = QPushButton("Próxima Página →")
        self.next_page_button.clicked.connect(self.next_page)

        # Adiciona os botões e o QLabel ao layout de navegação
        nav_buttons_layout.addWidget(self.prev_page_button)
        nav_buttons_layout.addWidget(self.page_label, 1)  # O argumento 1 faz com que o QLabel expanda para preencher o espaço
        nav_buttons_layout.addWidget(self.next_page_button)

        # Define o tamanho máximo para o widget de navegação
        navigation_widget.setMaximumWidth(540)

        # Adiciona o widget de navegação ao layout principal
        pdf_view_layout.addWidget(navigation_widget)

        # Adiciona o layout da visualização do PDF ao layout horizontal
        view_and_slider_and_tree_layout.addLayout(pdf_view_layout)
        
        # Slider de Zoom ao lado da visualização
        self.zoom_slider = QSlider(Qt.Orientation.Vertical)
        self.zoom_slider.setMinimum(10)  # 10% do zoom original
        self.zoom_slider.setMaximum(200)  # 200% do zoom original
        self.zoom_slider.setValue(100)  # Valor inicial do zoom (100%)
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.zoom_slider.setTickInterval(10)
        self.zoom_slider.valueChanged.connect(self.adjust_zoom)
        view_and_slider_and_tree_layout.addWidget(self.zoom_slider)

        # Layout vertical para o QTreeWidget e seus botões
        tree_layout = QVBoxLayout()

        # Cria e adiciona o cabeçalho acima do QTreeWidget
        header_widget = self.create_header()
        tree_layout.addWidget(header_widget)

        # QTreeWidget para exibir dados
        self.data_view = QTreeWidget()
        self.data_view.setHeaderHidden(True)
        self.data_view.setStyleSheet("""
            QTreeWidget::item { 
                height: 40px;
                font-size: 14px;
            }
        """)
        self.data_view.itemClicked.connect(self.display_pdf)
        tree_layout.addWidget(self.data_view)

        # Botões relacionados ao QTreeWidget abaixo dele
        tree_buttons_layout = QHBoxLayout()
        add_button = QPushButton("Adicionar Anexo")
        add_button.setStyleSheet("font-size: 14px;")
        add_button.clicked.connect(self.add_anexo)
        tree_buttons_layout.addWidget(add_button)

        add_sublevel_button = QPushButton("Adicionar Subnível")
        add_sublevel_button.setStyleSheet("font-size: 14px;")
        add_sublevel_button.clicked.connect(self.add_sublevel)
        tree_buttons_layout.addWidget(add_sublevel_button)

        delete_button = QPushButton("Deletar")
        delete_button.setStyleSheet("font-size: 14px;")
        delete_button.clicked.connect(self.delete_item)
        tree_buttons_layout.addWidget(delete_button)

        file_button = QPushButton("Selecionar Arquivo")
        file_button.setStyleSheet("font-size: 14px;")
        file_button.clicked.connect(self.select_pdf_file)
        tree_buttons_layout.addWidget(file_button)

        reset_button = QPushButton("Resetar")
        reset_button.setStyleSheet("font-size: 14px;")
        reset_button.clicked.connect(self.reset_data)
        tree_buttons_layout.addWidget(reset_button)

        # Adiciona o layout dos botões ao layout do QTreeWidget
        tree_layout.addLayout(tree_buttons_layout)

        # Adiciona o layout do QTreeWidget ao layout horizontal principal
        view_and_slider_and_tree_layout.addLayout(tree_layout)

        # Adiciona o layout combinado ao layout principal
        main_layout.addLayout(view_and_slider_and_tree_layout)

        # Configura o layout geral da janela
        self.setLayout(main_layout)

    def create_header(self):
        html_text = f"Anexos da {self.tipo} nº {self.numero}/{self.ano}<br>"
        
        self.titleLabel = QLabel()
        self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
        self.titleLabel.setStyleSheet("color: black; font-size: 30px; font-weight: bold;")
        self.titleLabel.setText(html_text)

        self.header_layout = QHBoxLayout()
        self.header_layout.addWidget(self.titleLabel)

        header_widget = QWidget()
        header_widget.setLayout(self.header_layout)

        return header_widget
    
    def adjust_zoom(self, value):
        # Calcula o fator de escala baseado no valor do slider
        scale_factor = value / 100.0
        # Reseta a transformação atual e aplica o novo zoom
        self.pdf_view.resetTransform()
        self.pdf_view.scale(scale_factor, scale_factor)

    def display_pdf(self, item, column):
        full_text = item.text(column)
        if " || " in full_text:
            file_path = full_text.split(" || ", 1)[1]
        else:
            file_path = full_text
        if file_path.endswith('.pdf'):
            self.load_pdf(file_path)

    def load_pdf(self, file_path):
        print("Tentando abrir o arquivo PDF:", file_path)  # Confirma o caminho do arquivo antes de tentar abrir
        try:
            self.document = fitz.open(file_path)  # Abre o documento e guarda em self.document
            self.current_page = 0  # Define a primeira página como a atual
            self.show_page(self.current_page)  # Mostra a primeira página
        except Exception as e:
            print("Erro ao abrir o arquivo PDF:", e)  # Printa o erro caso não consiga abrir o arquivo

    def show_page(self, page_number):
        if self.document:
            page = self.document.load_page(page_number)
            mat = fitz.Matrix(5.0, 5.0)  # Ajuste para a escala desejada
            pix = page.get_pixmap(matrix=mat)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            self.scene.clear()
            self.scene.addPixmap(pixmap)
            # Atualiza o contador de páginas
            self.page_label.setText(f"{page_number + 1} de {self.document.page_count}")

    def next_page(self):
        if self.document and self.current_page < self.document.page_count - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def prev_page(self):
        if self.document and self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

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
                selected_item.setText(0, f'{selected_item.text(0).split(" || ")[0]} || {file_path}')
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
                self.data_view.clear()
                for item in items:
                    parent_item = QTreeWidgetItem(self.data_view, [item['text']])
                    parent_item.setFont(0, QFont('SansSerif', 14))
                    for child in item['children']:
                        child_item = QTreeWidgetItem(parent_item, [child['text']])
                        child_item.setFont(0, QFont('SansSerif', 14))
                        file_path = child_item.text(0).split(" || ")[-1]
                        if Path(file_path).exists():
                            child_item.setIcon(0, self.icon_existe)
                        else:
                            child_item.setIcon(0, self.icon_nao_existe)
                    parent_item.setExpanded(True)

    def create_header(self):
        html_text = f"Anexos da {self.tipo} nº {self.numero}/{self.ano}<br>"
        
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
            new_anexo = f"Anexo {chr(65 + current_count)} || {text}"
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

class DraggableGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self._panning = False
        self._last_mouse_position = QPoint()
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)  # Zoom focalizado no cursor do mouse

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._panning = True
            self._last_mouse_position = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.pos() - self._last_mouse_position
            self._last_mouse_position = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:  # Verifica se o Ctrl está pressionado
            factor = 1.15 if event.angleDelta().y() > 0 else 0.85  # Ajusta o fator de zoom baseado na direção do scroll
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)  # Processa o evento normalmente se o Ctrl não estiver pressionado

class ConsolidarDocumentos:
    def __init__(self, df_registro_selecionado):
        self.df_registro_selecionado = df_registro_selecionado

    def gerar_comunicacao_padronizada(self, ordenador_de_despesas, responsavel_pela_demanda, document_details):
        if self.df_registro_selecionado.empty:
            QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
            print("Nenhum registro selecionado.")
            return

        try:
            # Assume a existência de uma variável 'TEMPLATE_DISPENSA_DIR' e 'tipo'
            template_filename = f"template_cp.docx"  # Assumindo um tipo padrão
            template_path = TEMPLATE_DISPENSA_DIR / template_filename
            if not template_path.exists():
                QMessageBox.warning(None, "Erro de Template", f"O arquivo de template não foi encontrado: {template_path}")
                print(f"O arquivo de template não foi encontrado: {template_path}")
                return

            nome_pasta = f"{self.df_registro_selecionado['id_processo'].iloc[0].replace('/', '-')} - {self.df_registro_selecionado['objeto'].iloc[0]}"
            pasta_base = Path.home() / 'Desktop' / nome_pasta / "2. Comunicacao Padronizada"
            pasta_base.mkdir(parents=True, exist_ok=True)  # Garante a criação da pasta

            save_path = pasta_base / f"{self.df_registro_selecionado['id_processo'].iloc[0].replace('/', '-')} - Cp.docx"
            print(f"Caminho completo para salvar o documento: {save_path}")

            doc = DocxTemplate(str(template_path))
            context = self.df_registro_selecionado.to_dict('records')[0]
            descricao_servico = "aquisição de" if self.df_registro_selecionado['material_servico'].iloc[0] == "Material" else "contratação de empresa especializada em"

            context.update({
                'descricao_servico': descricao_servico,
                'ordenador_de_despesas': f"{ordenador_de_despesas['nome']}\n{ordenador_de_despesas['posto']}\n{ordenador_de_despesas['funcao']}",
                'responsavel_pela_demanda': f"{responsavel_pela_demanda['nome']}\n{responsavel_pela_demanda['posto']}\n{responsavel_pela_demanda['funcao']}",
                'cp_number': document_details['cp_number'],
                'encarregado_obtencao': document_details['encarregado_obtencao'],
                'responsavel': document_details['responsavel']
            })

            print("Contexto para renderização:", context)
            doc.render(context)
            doc.save(str(save_path))
            print("Documento gerado com sucesso:", save_path)
            return str(save_path)

        except Exception as e:
            QMessageBox.warning(None, "Erro", f"Erro ao gerar ou salvar o documento: {e}")
            print(f"Erro ao gerar ou salvar o documento: {e}")
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
import win32com.client
import os
from PyPDF2 import PdfMerger

class DocumentDetailsWidget(QWidget):
    def __init__(self, df_registro_selecionado, ordenador_de_despesas, responsavel_pela_demanda, parent=None):
        super().__init__(parent)
        self.df_registro_selecionado = df_registro_selecionado
        self.consolidador = ConsolidarDocumentos(df_registro_selecionado) 
        self.material_servico = df_registro_selecionado['material_servico'].iloc[0]
        self.objeto = df_registro_selecionado['objeto'].iloc[0]
        self.setor_responsavel = df_registro_selecionado['setor_responsavel'].iloc[0]
        self.orgao_responsavel = df_registro_selecionado['orgao_responsavel'].iloc[0]
        self.ordenador_de_despesas = ordenador_de_despesas
        self.responsavel_pela_demanda = responsavel_pela_demanda
        self.sigla_om = df_registro_selecionado['sigla_om'].iloc[0]
        self.ICONS_DIR = Path(ICONS_DIR)
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
        self.cp_edit.setFixedWidth(80)
        cp_layout.addWidget(cp_label)
        cp_layout.addWidget(self.cp_edit)
        cp_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))      
        
        icon_anexo = QIcon(str(self.ICONS_DIR / "anexar.png"))
        add_pdf_button = self.create_button(
            "  Selecionar os Anexos", 
            icon_anexo, 
            self.add_pdf_to_merger, 
            "Selecionar arquivos PDFs para aplicar o Merge", 
            QSize(300, 50), 
            QSize(40, 40)
        )

        add_pdf_button.setStyleSheet("font-size: 14pt; font-weight: bold")
        cp_layout.addWidget(add_pdf_button)
        cp_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))  
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
        responsavel_layout.addWidget(encarregado_obtencao_label)
        responsavel_layout.addWidget(self.encarregado_obtencao_edit)
        main_layout.addLayout(responsavel_layout)
        
        justificativa_layout = QVBoxLayout()
        justificativa_label = QLabel("Justificativa:")
        justificativa_label.setStyleSheet("color: white; font-size: 12pt;")
        self.justificativa_edit = QTextEdit(self.get_justification_text())
        self.justificativa_edit.setStyleSheet("""
            QTextEdit {
                font-size: 12pt;
                background-color: white;
            }
            QTextEdit:hover {
                background-color: #f0f0f0;
            }
        """)
        justificativa_layout.addWidget(justificativa_label)
        justificativa_layout.addWidget(self.justificativa_edit)

        main_layout.addLayout(justificativa_layout)

        # Adicionando os botões "CP", "DFD", "TR" e "Adequação Orçamentária" em um QHBoxLayout
        buttons_layout = QHBoxLayout()

        icon_pdf = QIcon(str(self.ICONS_DIR / "pdf.png"))
        
        button_cp = self.create_button("  CP", icon_pdf, self.on_cp_clicked, "Gerar Comunicação Padronizada", QSize(150, 50))
        button_dfd = self.create_button("  DFD", icon_pdf, self.on_dfd_clicked, "Gerar Documento de Formalização de Demanda", QSize(150, 50))
        button_tr = self.create_button("  TR", icon_pdf, self.on_tr_clicked, "Gerar Termo de Referência", QSize(150, 50))
        button_adeq_orc = self.create_button("Adequação Orçamentária", icon_pdf, self.on_adeq_orc_clicked, "Gerar Adequação Orçamentária", QSize(250, 50))
        button_cp.setStyleSheet("font-size: 12pt;")
        button_dfd.setStyleSheet("font-size: 12pt;")
        button_tr.setStyleSheet("font-size: 12pt;")
        button_adeq_orc.setStyleSheet("font-size: 12pt;")

        buttons_layout.addWidget(button_cp)
        buttons_layout.addWidget(button_dfd)
        buttons_layout.addWidget(button_tr)
        buttons_layout.addWidget(button_adeq_orc)

        main_layout.addLayout(buttons_layout)

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

    def on_cp_clicked(self):
        # Implementação do callback para o botão CP
        pass

    def on_dfd_clicked(self):
        justificativa_text = self.justificativa_edit.toPlainText()

        # Acessando os atributos diretamente de self
        ordenador_de_despesas = self.ordenador_de_despesas
        responsavel_pela_demanda = self.responsavel_pela_demanda

        result = self.consolidador.gerar_documento_de_formalizacao_de_demanda(
            ordenador_de_despesas, responsavel_pela_demanda, justificativa_text
        )
        if result:
            QMessageBox.information(self, "Sucesso", f"Documento gerado com sucesso em: {result}")
        else:
            QMessageBox.warning(
                self, "Erro ao Gerar", "Falha ao gerar o documento. Verifique os logs para mais detalhes."
            )


    def on_tr_clicked(self):
        result = self.consolidador.gerar_termo_de_referencia(self.ordenador_de_despesas, self.responsavel_pela_demanda)
        if result:
            QMessageBox.information(self, "Sucesso", f"Documento gerado com sucesso em: {result}")
        else:
            QMessageBox.warning(self, "Erro ao Gerar", "Falha ao gerar o documento. Verifique os logs para mais detalhes.")

    def on_adeq_orc_clicked(self):
        # Implementação do callback para o botão Adequação Orçamentária
        pass
    
    def create_button(self, text, icon=None, callback=None, tooltip_text="", button_size=None, icon_size=None):
        btn = QPushButton(text)
        if icon:
            btn.setIcon(icon)
            btn.setIconSize(icon_size if icon_size else QSize(40, 40))
        if button_size:
            btn.setFixedSize(button_size)
        btn.setToolTip(tooltip_text)
        if callback:
            btn.clicked.connect(callback)  # Conecta o callback ao evento de clique
        return btn
    
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
    
    def get_justification_text(self):
        # Recupera o valor atual da justificativa no DataFrame
        current_justification = self.df_registro_selecionado['justificativa'].iloc[0]

        # Retorna o valor atual se ele existir, senão, constrói uma justificativa baseada no tipo de material/serviço
        if current_justification:  # Checa se existe uma justificativa
            return current_justification
        else:
            # Gera justificativa padrão com base no tipo de material ou serviço
            if self.material_servico == 'Material':
                return (f"A aquisição de {self.objeto} se faz necessária para o atendimento das necessidades do(a) {self.setor_responsavel} do(a) {self.orgao_responsavel} ({self.sigla_om}). A disponibilidade e a qualidade dos materiais são essenciais para garantir a continuidade das operações e a eficiência das atividades desempenhadas pelo(a) {self.setor_responsavel}.")
            elif self.material_servico == 'Serviço':
                return (f"A contratação de empresa especializada na prestação de serviços de {self.objeto} é imprescindível para o atendimento das necessidades do(a) {self.setor_responsavel} do(a) {self.orgao_responsavel} ({self.sigla_om}).")
            return ""  # Retorna uma string vazia se nenhuma condição acima for satisfeita

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

CONFIG_FILE = 'config.json'

def load_config():
    if not Path(CONFIG_FILE).exists():
        return {}
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

class ConsolidarDocumentos:
    def __init__(self, df_registro_selecionado):
        self.df_registro_selecionado = df_registro_selecionado
        self.config = load_config()
        self.pasta_base = Path(self.config.get('pasta_base', str(Path.home() / 'Desktop')))
    
    def alterar_diretorio_base(self):
        new_dir = QFileDialog.getExistingDirectory(None, "Selecione o Novo Diretório Base", str(Path.home()))
        if new_dir:
            self.pasta_base = Path(new_dir)
            self.config['pasta_base'] = str(self.pasta_base)
            save_config(self.config)
            QMessageBox.information(None, "Diretório Base Alterado", f"O novo diretório base foi alterado para: {self.pasta_base}")

    def abrir_pasta_base(self):
        try:
            os.startfile(self.pasta_base)
        except Exception as e:
            print(f"Erro ao abrir a pasta base: {e}")
            QMessageBox.warning(None, "Erro", f"Erro ao abrir a pasta base: {e}")

    def abrirDocumento(self, docx_path):
        try:
            pdf_path = self.convert_to_pdf(docx_path)
            os.startfile(pdf_path)
            print(f"Documento PDF aberto: {pdf_path}")
        except Exception as e:
            print(f"Erro ao abrir ou converter o documento: {e}")
            QMessageBox.warning(None, "Erro", f"Erro ao abrir ou converter o documento: {e}")

    def salvarPDF(self, docx_path):
        try:
            pdf_path = self.convert_to_pdf(docx_path)
            print(f"Documento PDF salvo: {pdf_path}")
            return pdf_path
        except Exception as e:
            print(f"Erro ao converter o documento: {e}")
            QMessageBox.warning(None, "Erro", f"Erro ao converter o documento: {e}")
            return None

    def convert_to_pdf(self, docx_path):
        docx_path = Path(docx_path) if not isinstance(docx_path, Path) else docx_path
        pdf_path = docx_path.with_suffix('.pdf')
        word = win32com.client.Dispatch("Word.Application")
        doc = None
        try:
            doc = word.Documents.Open(str(docx_path))
            doc.SaveAs(str(pdf_path), FileFormat=17)
        except Exception as e:
            raise e
        finally:
            if doc is not None:
                doc.Close()
            word.Quit()
        if not pdf_path.exists():
            raise FileNotFoundError(f"O arquivo PDF não foi criado: {pdf_path}")
        return pdf_path

    def prepare_context(self, data):
        context = {key: (str(value) if value is not None else 'Não especificado') for key, value in data.items()}
        descricao_servico = "aquisição de" if data['material_servico'] == "Material" else "contratação de empresa especializada em"
        context.update({'descricao_servico': descricao_servico})
        return context

    def gerarDocumento(self, template_type, subfolder_name, file_description):
        if self.df_registro_selecionado.empty:
            QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
            return

        template_filename = f"template_{template_type}.docx"
        template_path, save_path = self.setup_document_paths(template_filename, subfolder_name, file_description)

        self.verificar_e_criar_pastas(self.pasta_base / self.nome_pasta)

        if not template_path.exists():
            QMessageBox.warning(None, "Erro de Template", f"O arquivo de template não foi encontrado: {template_path}")
            return

        with open(str(template_path), 'rb') as template_file:
            doc = DocxTemplate(template_file)
            context = self.df_registro_selecionado.to_dict('records')[0]
            context = self.prepare_context(context)
            doc.render(context)
            doc.save(str(save_path))
        return save_path

    def setup_document_paths(self, template_filename, subfolder_name, file_description):
        template_path = TEMPLATE_DISPENSA_DIR / template_filename
        id_processo = self.df_registro_selecionado['id_processo'].iloc[0].replace('/', '-')
        objeto = self.df_registro_selecionado['objeto'].iloc[0]
        self.nome_pasta = f"{id_processo} - {objeto}"
        if 'pasta_base' not in self.config:
            self.alterar_diretorio_base()
        pasta_base = Path(self.config['pasta_base']) / self.nome_pasta / subfolder_name
        pasta_base.mkdir(parents=True, exist_ok=True)
        save_path = pasta_base / f"{id_processo} - {file_description}.docx"
        return template_path, save_path

    def verificar_e_criar_pastas(self, pasta_base):
        pastas_necessarias = [
            pasta_base / '1. Autorizacao',
            pasta_base / '2. CP e anexos',
            pasta_base / '3. Aviso',
            pasta_base / '2. CP e anexos' / 'DFD',
            pasta_base / '2. CP e anexos' / 'DFD' / 'Anexo A - Relatorio Safin',
            pasta_base / '2. CP e anexos' / 'DFD' / 'Anexo B - Especificações e Quantidade',
            pasta_base / '2. CP e anexos' / 'TR',
            pasta_base / '2. CP e anexos' / 'TR' / 'Pesquisa de Preços',
            pasta_base / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária'
        ]
        for pasta in pastas_necessarias:
            if not pasta.exists():
                pasta.mkdir(parents=True)

    def gerar_e_abrir_documento(self, template_type, subfolder_name, file_description):
        docx_path = self.gerarDocumento(template_type, subfolder_name, file_description)
        if docx_path:
            self.abrirDocumento(docx_path)

    def gerar_autorizacao(self):
        self.gerar_e_abrir_documento("autorizacao_dispensa", "1. Autorizacao", "Autorizacao para abertura de Processo Administrativo")

    def gerar_comunicacao_padronizada(self):
        pdf_paths = []
        docx_cp_path = self.gerarDocumento("cp", "2. CP e anexos", "Comunicacao Padronizada")
        if docx_cp_path:
            pdf_path = self.salvarPDF(docx_cp_path)
            if pdf_path:
                pdf_paths.append(pdf_path)
        
        docx_dfd_path = self.gerarDocumento("dfd", "2. CP e anexos/DFD", "Documento de Formalizacao de Demanda")
        if docx_dfd_path:
            pdf_path = self.salvarPDF(docx_dfd_path)
            if pdf_path:
                self.add_cover_to_pdf(pdf_path, TEMPLATE_DISPENSA_DIR / "dfd.pdf")
                pdf_paths.append(pdf_path)

        pdf_path = self.get_latest_pdf(self.pasta_base / self.nome_pasta / '2. CP e anexos' / 'DFD' / 'Anexo A - Relatorio Safin')
        if pdf_path:
            self.add_cover_to_pdf(pdf_path, TEMPLATE_DISPENSA_DIR / "anexo-a-dfd.pdf")
            pdf_paths.append(pdf_path)
        else:
            QMessageBox.warning(None, "Erro", "Arquivo PDF não encontrado: Anexo A - Relatorio Safin")

        pdf_path = self.get_latest_pdf(self.pasta_base / self.nome_pasta / '2. CP e anexos' / 'DFD' / 'Anexo B - Especificações e Quantidade')
        if pdf_path:
            self.add_cover_to_pdf(pdf_path, TEMPLATE_DISPENSA_DIR / "anexo-b-dfd.pdf")
            pdf_paths.append(pdf_path)
        else:
            QMessageBox.warning(None, "Erro", "Arquivo PDF não encontrado: Anexo B - Especificações e Quantidade")
        
        docx_tr_path = self.gerarDocumento("tr", "2. CP e anexos/TR", "Termo de Referencia")
        if docx_tr_path:
            pdf_path = self.salvarPDF(docx_tr_path)
            if pdf_path:
                self.add_cover_to_pdf(pdf_path, TEMPLATE_DISPENSA_DIR / "tr.pdf")
                pdf_paths.append(pdf_path)

        pdf_path = self.get_latest_pdf(self.pasta_base / self.nome_pasta / '2. CP e anexos' / 'TR' / 'Pesquisa de Preços')
        if pdf_path:
            self.add_cover_to_pdf(pdf_path, TEMPLATE_DISPENSA_DIR / "anexo-tr.pdf")
            pdf_paths.append(pdf_path)
        else:
            QMessageBox.warning(None, "Erro", "Arquivo PDF não encontrado: Pesquisa de Preços")

        docx_dec_adeq_path = self.gerarDocumento("dec_adeq", "2. CP e anexos/Declaracao de Adequação Orçamentária", "Declaracao de Adequação Orçamentária")
        if docx_dec_adeq_path:
            pdf_path = self.salvarPDF(docx_dec_adeq_path)
            if pdf_path:
                pdf_paths.append(pdf_path)

        pdf_path = self.get_latest_pdf(self.pasta_base / self.nome_pasta / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária' / 'Relatório do PDM-Catser')
        if pdf_path:
            self.add_cover_to_pdf(pdf_path, TEMPLATE_DISPENSA_DIR / "anexo-dec-adeq.pdf")
            pdf_paths.append(pdf_path)
        else:
            QMessageBox.warning(None, "Erro", "Arquivo PDF não encontrado: Declaracao de Adequação Orçamentária")

        self.concatenar_e_abrir_pdfs(pdf_paths)

    def add_cover_to_pdf(self, pdf_path, cover_path):
        try:
            merger = PdfMerger()
            merger.append(str(cover_path))
            merger.append(str(pdf_path))
            merged_pdf_path = pdf_path.parent / (pdf_path.stem + "_with_cover.pdf")
            merger.write(str(merged_pdf_path))
            merger.close()
            os.remove(pdf_path)  # Remove the old PDF without cover
            merged_pdf_path.rename(pdf_path)  # Rename the new PDF with cover to the original name
            print(f"Capa adicionada ao PDF: {pdf_path}")
        except Exception as e:
            print(f"Erro ao adicionar capa ao PDF: {e}")
            QMessageBox.warning(None, "Erro", f"Erro ao adicionar capa ao PDF: {e}")

    def concatenar_e_abrir_pdfs(self, pdf_paths):
        if not pdf_paths:
            QMessageBox.warning(None, "Erro", "Nenhum PDF foi gerado para concatenar.")
            return

        output_pdf_path = self.pasta_base / self.nome_pasta / "2. CP e anexos" / "Documentos_Concatenados.pdf"
        merger = PdfMerger()

        try:
            for pdf_path in pdf_paths:
                merger.append(str(pdf_path))

            merger.write(str(output_pdf_path))
            merger.close()

            os.startfile(output_pdf_path)
            print(f"PDF concatenado salvo e aberto: {output_pdf_path}")
        except Exception as e:
            print(f"Erro ao concatenar os PDFs: {e}")
            QMessageBox.warning(None, "Erro", f"Erro ao concatenar os PDFs: {e}")

    def get_latest_pdf(self, directory):
        pdf_files = list(directory.glob("*.pdf"))
        if not pdf_files:
            return None
        latest_pdf = max(pdf_files, key=os.path.getmtime)
        return latest_pdf

    def gerar_documento_de_formalizacao_de_demanda(self):
        self.gerarDocumento("dfd", "2. CP e anexos/DFD", "Documento de Formalizacao de Demanda")

    def gerar_declaracao_orcamentaria(self):
        self.gerarDocumento("declaracao_orcamentaria", "2. CP e anexos/Declaracao de Adequação Orçamentária", "Declaracao Orcamentaria")

    def gerar_termo_de_referencia(self):
        self.gerarDocumento("tr", "2. CP e anexos/TR", "Termo de Referencia")

    def gerar_aviso_dispensa(self):
        self.gerar_e_abrir_documento("aviso_dispensa", "3. Aviso", "Aviso de Dispensa")

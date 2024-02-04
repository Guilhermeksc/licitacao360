from PyQt6.QtWidgets import QToolButton, QTreeWidget, QFileDialog, QSizePolicy, QFileDialog, QMenu, QTreeWidgetItem, QApplication, QWidget, QDial, QVBoxLayout, QAbstractItemView, QHeaderView, QMessageBox, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QMimeData, QByteArray, QDataStream, QIODevice, QItemSelectionModel, QSize
from PyQt6.QtGui import QDrag, QFont, QIcon
from diretorios import *
import os
import pandas as pd
from utils.treeview_utils import load_images, create_button, save_dataframe_to_excel, open_folder
import PyPDF2
from PyPDF2 import PdfWriter, PdfReader, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black
import io
from functools import partial
from docxtpl import DocxTemplate
import string
from datetime import datetime
from num2words import num2words
import webbrowser

GLOBAL_SPLIT_DIR = None

class DraggableTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super(DraggableTreeWidget, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.previous_values = {}  # Dicionário para armazenar os valores anteriores
        self.itemChanged.connect(self.onItemChanged)
        self.itemDoubleClicked.connect(self.onItemDoubleClicked)

    def onItemChanged(self, item, column):
        # Verificar se a coluna editada é a coluna "Fim"
        if column == 4:
            try:
                inicio = int(item.text(3))
                fim = int(item.text(4))
                qnt_pag = fim - inicio + 1
                if qnt_pag < 1:
                    raise ValueError("O número de fim é menor que o de início")
                item.setText(5, str(qnt_pag))
                self.ajustar_itens()
            except ValueError as e:
                QMessageBox.critical(self, "Erro de Validação", str(e))
                # Reverter para o valor anterior se houver um erro
                item.setText(4, self.previous_values.get(id(item), ""))
                self.clearSelection()
        self.save_data_to_csv()

    def onItemDoubleClicked(self, item, column):
        # Verifique se a coluna clicada é uma das que devem ser editáveis
        editable_columns = [1, 2, 4]  # "Identificação", "SAPIENS" e "Fim"
        if column in editable_columns:
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

            self.editItem(item, column)
            if column == 4:  # Armazenar o valor anterior apenas para a coluna "Fim"
                self.previous_values[id(item)] = item.text(column)
        else:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def dropEvent(self, event):
        # Obter a posição onde o item será solto
        pointer_position = event.position().toPoint()
        target_item = self.itemAt(pointer_position)
        
        if not target_item:
            # Se o destino não for um item (por exemplo, espaço vazio), ignore o evento
            event.ignore()
            return

        # Obter o item arrastado
        dragged_item = self.currentItem()

        if dragged_item == target_item:
            # Se o item arrastado for solto sobre si mesmo, ignore o evento
            event.ignore()
            return

        # Salvar as informações do item arrastado
        item_data = self.mimeData(self.selectedItems())
        parent_item = dragged_item.parent() if dragged_item.parent() else self.invisibleRootItem()
        index = parent_item.indexOfChild(dragged_item)
        parent_item.takeChild(index)
        # Descobrir onde inserir o item arrastado
        parent_of_target = target_item.parent() if target_item.parent() else self.invisibleRootItem()
        index_of_target = parent_of_target.indexOfChild(target_item)
        # Inserir o item arrastado na nova posição
        parent_of_target.insertChild(index_of_target, dragged_item)
        # Redefinir os dados do item arrastado (se necessário)
        self.clearSelection()
        self.selectionModel().select(self.indexFromItem(dragged_item), QItemSelectionModel.SelectionFlag.Select)

        # Aceitar o evento de soltar
        self.ajustar_itens()
        # Chamar atualizar_idx para reordenar os números
        self.atualizar_idx()
        self.save_data_to_csv()
        event.accept()
        
    def ajustar_itens(self):
        inicio_atual = 1
        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            try:
                qnt_pag_text = item.text(5)
                qnt_pag = int(qnt_pag_text) if qnt_pag_text else 2  # Default to 2 if empty
            except ValueError:
                qnt_pag = 2  # Default to 2 if conversion fails
            fim_atual = inicio_atual + qnt_pag - 1
            
            item.setText(3, str(inicio_atual))  # Atualiza a coluna 'Início'
            item.setText(4, str(fim_atual))     # Atualiza a coluna 'Fim'
            
            inicio_atual = fim_atual + 1

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Delete:

            selected_items = self.selectedItems()
            for item in selected_items:
                parent = item.parent() or self.invisibleRootItem()
                parent.removeChild(item)
            self.atualizar_idx()  # Atualizar os índices após a exclusão
            self.ajustar_itens()  # Adicionado para recalcular as colunas Início e Fim
        else:
            super().keyPressEvent(event)
        self.save_data_to_csv()

    def atualizar_idx(self):
        for idx in range(self.topLevelItemCount()):
            item = self.topLevelItem(idx)
            item.setText(0, f"{idx + 1:02}") 

    def collect_data(self):
        # Coletar os dados dos itens do QTreeWidget e retornar como um DataFrame
        data = []
        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            row_data = [item.text(column) for column in range(self.columnCount())]
            data.append(row_data)
        columns = [self.headerItem().text(i) for i in range(self.columnCount())]
        df = pd.DataFrame(data, columns=columns)
        return df

    def save_data_to_csv(self):
        # Salvar os dados coletados em um arquivo CSV
        df = self.collect_data()
        df.to_csv(TREEVIEW_DATA_PATH, index=False)

class ChecklistWidget(QWidget):
    def __init__(self, parent, icons_path):
        super().__init__(parent)
        self.icons_dir = ICONS_DIR
        self.icon_cache = {
            'pdf64.png': QIcon(os.path.join(self.icons_dir, 'pdf64.png')),
            'rotate.png': QIcon(os.path.join(self.icons_dir, 'rotate.png')),
            'folder128.png': QIcon(os.path.join(self.icons_dir, 'folder128.png')),
            'save.png': QIcon(os.path.join(self.icons_dir, 'save.png')),
            'import.png': QIcon(os.path.join(self.icons_dir, 'import.png')),
            'plus128.png': QIcon(os.path.join(self.icons_dir, 'plus128.png')),
        }
        self.layout = QVBoxLayout(self)
        # Criar o DraggableTreeWidget e adicioná-lo ao layout
        self.tree = DraggableTreeWidget(self)
        self.font = QFont()  # Crie uma fonte para usar no tree e no cabeçalho
        self.font.setPointSize(12)  # Define o tamanho da fonte para 12

        self.tree.setFont(self.font)  # Define a fonte para o tree
        self.tree.setColumnCount(6)  # Definir a quantidade de colunas
        self.tree.setHeaderLabels(["Nº", "Identificação", "SAPIENS", "Início", "Fim", "Págs"])
        # Ajustar as colunas para ocupar o espaço disponível
        self.header = self.tree.header()  # Aqui você define o atributo 'header'
        self.header.setFont(self.font)  # Define a fonte para o cabeçalho
        # Agora você pode aplicar o estilo diretamente depois de definir a fonte
        self.header.setStyleSheet("QHeaderView::section { font-size: 12pt; }")
        # Defina a largura inicial das colunas
        self.tree.setColumnWidth(1, 750)  # Largura inicial para a primeira coluna
        self.tree.setColumnWidth(2, 200)  # Largura inicial para a segunda coluna
        # Adicionar a árvore ao layout
        self.layout.addWidget(self.tree)
        # Adicione os botões abaixo do treeview
        self.setupBottomButtons()
        # Carregar os dados no treeview
        self.load_data()
        # Habilitar o menu de contexto e conectar ao slot personalizado
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)


        self.tree.customContextMenuRequested.connect(self.on_context_menu)
        self.lv_split_final_dir = None

    def setupBottomButtons(self):
        # Layout horizontal para os botões inferiores
        self.bottom_buttons_layout = QHBoxLayout()
        
        # Definições dos botões
        button_definitions = [
        ('Sapiens', 'sapiens.png', self.abrir_link_sapiens, "Carregar o link do Sapiens"),
        ('Atualizar', 'rotate.png', self.resetar_treeview, "Atualizar a visualização"),
        ('Numerar', 'pdf64.png', numerar_pdf_gui, "Numerar o PDF"),
        ('Abrir', 'pdf64.png', self.abrir_pdf_processo, "Selecione um PDF para abrir"),
        ('Processar', 'pdf64.png', processar_pdf_na_integra_e_gerar_documentos, "Processar o PDF"),
        ('Importar', 'import.png', self.onLoadItems, "Importar dados"),
        ('Salvar', 'save.png', self.onSaveItems, "Salvar as alterações"),
        ('Abrir', 'folder128.png', self.abrir_pasta_existente, "Abrir a pasta do item"),
    ]

        for text, icon_filename, callback, tooltip in button_definitions:
            button = self.createButton(text, icon_filename, callback, tooltip)
            self.bottom_buttons_layout.addWidget(button)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Adicione o layout dos botões inferiores ao layout principal
        self.layout.addLayout(self.bottom_buttons_layout)

    def abrir_pdf_processo(self):
        # Definir o caminho inicial para a área de trabalho do usuário
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

        # Abrir a caixa de diálogo para escolher o arquivo PDF
        filepath, _ = QFileDialog.getOpenFileName(
            self,  # parent
            "Selecione um arquivo PDF",  # título
            desktop_path,  # diretório inicial
            "Arquivos PDF (*.pdf);;Todos os arquivos (*.*)"  # filtro de arquivos
        )

        if filepath:
            # Tentar abrir o arquivo PDF com o leitor padrão do sistema
            try:
                if os.name == 'nt':  # para Windows
                    os.startfile(filepath)
                elif os.name == 'posix':  # para macOS e Linux
                    subprocess.call(('open', filepath))
                else:
                    # Se o sistema operacional não for reconhecido, exibir uma mensagem
                    print("Sistema operacional não suportado para abrir arquivos diretamente.")
            except Exception as e:
                print(f"Erro ao abrir o arquivo: {e}")

    def abrir_link_sapiens(self):
        url = "https://supersapiens.agu.gov.br/auth/login"
        webbrowser.open(url)

    def createButton(self, text, icon_filename, callback, tooltip):
        button = QToolButton()
        font = button.font()  # Obter a fonte atual do botão
        font.setPointSize(14)  # Definir o tamanho da fonte para 14, por exemplo
        button.setFont(font)  # Aplicar a fonte atualizada ao botão
        button.setText(text)
        icon = QIcon(os.path.join(self.icons_dir, icon_filename))
        button.setIcon(icon)
        button.setIconSize(QSize(64, 64)) 
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        button.setToolTip(tooltip)  # Adiciona o tooltip aqui
        button.clicked.connect(callback)
        return button

    def onProcessarPDF(self):
        # Método chamado quando o botão "Processar PDF" é clicado
        pass

    def abrir_pasta_existente(self, *args, **kwargs):
        global GLOBAL_SPLIT_DIR
        if GLOBAL_SPLIT_DIR and os.path.isdir(GLOBAL_SPLIT_DIR):
            open_folder(GLOBAL_SPLIT_DIR)
        else:
            print("A pasta não foi encontrada ou ainda não foi criada.")


    def onSaveItems(self):
        # Pedir ao usuário para escolher o local e o nome do arquivo para salvar
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Arquivo", "", "Arquivos CSV (*.csv);;Todos os Arquivos (*)"
        )

        if filepath:
            # Verificar se o caminho tem a extensão .csv, se não, adicionar
            if not filepath.endswith('.csv'):
                filepath += '.csv'

            try:
                # Carregar o dataframe de TREEVIEW_DATA_PATH e salvá-lo no local escolhido
                df = pd.read_csv(TREEVIEW_DATA_PATH)
                df.to_csv(filepath, index=False)
                print(f"Arquivo salvo com sucesso: {filepath}")
            except Exception as e:
                print(f"Erro ao salvar o arquivo: {e}")

    def onLoadItems(self):
        # Pedir ao usuário para escolher o arquivo para carregar
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Carregar Arquivo", "", "Arquivos CSV (*.csv);;Todos os Arquivos (*)"
        )

        if filepath:
            try:
                # Carregar o dataframe do arquivo escolhido
                dataframe_carregado = pd.read_csv(filepath)

                # Atualizar TREEVIEW_DATA_PATH com o novo dataframe
                dataframe_carregado.to_csv(TREEVIEW_DATA_PATH, index=False)

                # Aqui você pode atualizar a sua interface com o dataframe carregado
                # ...

                print(f"Arquivo carregado com sucesso: {filepath}")
            except Exception as e:
                print(f"Erro ao carregar o arquivo: {e}")    

    def showEvent(self, event):
        # Este método é chamado automaticamente quando o widget é exibido
        super().showEvent(event)
        self.header.setFont(self.font)

    def add_item(self, identificacao, sapiens, inicio, fim):
        # Calcular a quantidade de páginas
        qnt_pag = int(fim) - int(inicio) + 1
        # Criar um novo item com os dados especificados
        item = QTreeWidgetItem([identificacao, sapiens, inicio, fim, str(qnt_pag)])
        self.tree.addTopLevelItem(item)

    def get_title(self):
        return "Check-list"

    def get_content_widget(self):
        return self
    
    def adjust_column_sizes(self):
        self.header.setStretchLastSection(False)

        # Ajustar as colunas para um tamanho específico ou baseado no conteúdo
        self.header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta ao conteúdo da coluna Nº
        self.header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # A primeira coluna com texto esticado
        self.header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta ao conteúdo da coluna SAPIENS
        self.header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta ao conteúdo da coluna Início
        self.header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta ao conteúdo da coluna Fim
        self.header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)   

    def load_data(self):
        # Dados a serem inseridos no treeview
        dados = [
            ("Capa de Abertura do Pregão Eletrônico e Termo de Autuação", "termo_autuacao", "1", "4"),
            ("Autorização para Abertura de Processo", "termo_abertura", "5", "6"),
            ("Documento de Formalização da Demanda (DFD)", "dfd", "7", "16"),
            ("Comprovação da Divulgação da Intenção do Registro de Preços", "termo_irp", "17", "18"),
            ("Despacho", "Despacho", "19", "20"),
            ("Portaria nº 221-2023 Com7°DN de Designação de Ordenador de Despesas", "portaria_od", "21", "23"),
            ("Portaria nº 92-2023 Com7°DN de Designação de Militares para Comissão de Licitação", "portaria_comissao", "24", "27"),
            ("Portaria nº XX-2023 Com7°DN de Designação de Equipe de Planejamento", "portaria_plan", "28", "31"),
            ("Termo de Referência", "tr", "32", "51"),
            ("Estudo Técnico Preliminar (ETP)", "etp", "52", "68"),
            ("Matriz de Gerenciamento de Riscos", "mr", "69", "79"),
            ("Pesquisa de Preços", "pesquisa_precos", "80", "137"),   
            ("Minuta do Edital", "minuta_edital", "138", "164"),
            ("Minuta do Contrato", "minuta_contrato", "165", "173"),
            ("Minuta da Ata de Registro de Preços", "minuta_arp", "174", "183"),
            ("Lista de Verificação", "checklist", "184", "190"),    
            ("Despacho", "despacho", "191", "192"),
            ("Nota Técnica", "nota_tecnica", "193", "200"),
            ("Comunicação Padronizada", "termo", "201", "202"),
            ("Despacho de Encaminhamento para AGU", "termo", "203", "204"),
        ]
        
        # Verificar se o arquivo TREEVIEW_DATA_PATH existe
        if os.path.exists(TREEVIEW_DATA_PATH):
            df = pd.read_csv(TREEVIEW_DATA_PATH, usecols=['Identificação', 'SAPIENS', 'Início', 'Fim'])
            dados_from_file = df.values.tolist()
        else:
            dados_from_file = dados  # Use a lista padrão de dados se o arquivo não existir
        
        # Adicionar os itens ao treeview
        for idx, (identificacao, sapiens, inicio, fim) in enumerate(dados_from_file, 1):  # Começar a contar do 1
            try:
                qnt_pag = int(fim) - int(inicio) + 1
            except ValueError:
                # Handle the case where "fim" or "inicio" cannot be converted to integers
                qnt_pag = 0  # or some other appropriate default value
            item = QTreeWidgetItem([f"{idx:02}", identificacao, sapiens, str(inicio), str(fim), str(qnt_pag)])
            # Não defina as colunas como editáveis aqui
            self.tree.addTopLevelItem(item)
        
        # Após adicionar todos os itens, ajustar o tamanho das colunas
        self.adjust_column_sizes()

    def get_default_data(self):
        # Retorna a lista de dados padrão
        return [
            ("Capa de Abertura do Pregão Eletrônico e Termo de Autuação", "termo_autuacao", "1", "4"),
            ("Autorização para Abertura de Processo", "termo_abertura", "5", "6"),
            ("Documento de Formalização da Demanda (DFD)", "dfd", "7", "16"),
            ("Comprovação da Divulgação da Intenção do Registro de Preços", "termo_irp", "17", "18"),
            ("Despacho", "Despacho", "19", "20"),
            ("Portaria nº 221-2023 Com7°DN de Designação de Ordenador de Despesas", "portaria_od", "21", "23"),
            ("Portaria nº 92-2023 Com7°DN de Designação de Militares para Comissão de Licitação", "portaria_comissao", "24", "27"),
            ("Portaria nº XX-2023 Com7°DN de Designação de Equipe de Planejamento", "portaria_plan", "28", "31"),
            ("Termo de Referência", "tr", "32", "51"),
            ("Estudo Técnico Preliminar (ETP)", "etp", "52", "68"),
            ("Matriz de Gerenciamento de Riscos", "mr", "69", "79"),
            ("Pesquisa de Preços", "pesquisa_precos", "80", "137"),   
            ("Minuta do Edital", "minuta_edital", "138", "164"),
            ("Minuta do Contrato", "minuta_contrato", "165", "173"),
            ("Minuta da Ata de Registro de Preços", "minuta_arp", "174", "183"),
            ("Lista de Verificação", "checklist", "184", "190"),    
            ("Despacho", "despacho", "191", "192"),
            ("Nota Técnica", "nota_tecnica", "193", "200"),
            ("Comunicação Padronizada", "termo", "201", "202"),
            ("Despacho de Encaminhamento para AGU", "termo", "203", "204"),
        ]
        
    def resetar_treeview(self):
        # Carrega a lista de dados padrão no treeview
        self.tree.clear()
        dados_to_load = self.get_default_data()
        for idx, (identificacao, sapiens, inicio, fim) in enumerate(dados_to_load, 1):  # Começar a contar do 1
            qnt_pag = int(fim) - int(inicio) + 1
            item = QTreeWidgetItem([f"{idx:02}", identificacao, sapiens, str(inicio), str(fim), str(qnt_pag)])
            self.tree.addTopLevelItem(item)
        self.adjust_column_sizes()

    def _on_item_click(self, index):
        # Your code here to handle the item click event
        pass   

    def inserir_item(self, identificacao="Despacho", marcador_sapiens="Termo"):
        tree = self.tree
        # Verifique se há uma linha selecionada
        selected_items = tree.selectedItems()
        
        if selected_items:
            last_item = selected_items[-1]  # Get the last selected item
        elif tree.topLevelItemCount() > 0:
            last_item = tree.topLevelItem(tree.topLevelItemCount() - 1)
        else:
            last_item = None

        if last_item:
            last_fim_value = int(last_item.text(4)) if last_item.text(4) else 0
            insert_position = tree.indexOfTopLevelItem(last_item) + 1
        else:
            last_fim_value = 0
            insert_position = 0

        inicio = last_fim_value + 1
        fim = inicio + 1  # Since you want to add 2 pages
        num_paginas = 2  # This is fixed as per your requirement

        # Create a new QTreeWidgetItem and insert it into the tree
        new_item = QTreeWidgetItem([str(insert_position), identificacao, marcador_sapiens, str(inicio), str(fim), str(num_paginas)])
        tree.insertTopLevelItem(insert_position, new_item)
        
        tree.atualizar_idx()
        tree.save_data_to_csv()
        tree.ajustar_itens()

        
    def on_context_menu(self, point):
        index = self.tree.indexAt(point)
        if not index.isValid():
            return

        if index.isValid():
            context_menu = QMenu(self.tree)
            context_menu.setStyleSheet("QMenu { font-size: 12pt; }")

            # Add other actions to the menu
            despacho_action = context_menu.addAction(QIcon(os.path.join(self.icons_dir, "plus.png")), "Despacho")
            comunicacao_action = context_menu.addAction(QIcon(os.path.join(self.icons_dir, "plus.png")), "Comunicação Padronizada")
            desmembramento_action = context_menu.addAction(QIcon(os.path.join(self.icons_dir, "plus.png")), "Termo de Desmembramento")

            add_action = context_menu.addAction(QIcon(os.path.join(self.icons_dir, "plus.png")), "Adicionar outro ")
            edit_action = context_menu.addAction(QIcon(os.path.join(self.icons_dir, "engineering.png")), "Editar")
            delete_action = context_menu.addAction(QIcon(os.path.join(self.icons_dir, "delete.png")), "Excluir")
            view_action = context_menu.addAction(QIcon(os.path.join(self.icons_dir, "search.png")), "Visualizar")

            # Connect actions to methods
            despacho_action.triggered.connect(partial(self.inserir_item, identificacao="Despacho", marcador_sapiens="Termo"))
            comunicacao_action.triggered.connect(partial(self.inserir_item, identificacao="Comunicação Padronizada nº", marcador_sapiens="Comunicação"))  
            desmembramento_action.triggered.connect(partial(self.inserir_item, identificacao="Termo de Desentranhamento", marcador_sapiens="Termo"))

            add_action.triggered.connect(self.onProcessarPDF)
            edit_action.triggered.connect(self.onProcessarPDF)  
            delete_action.triggered.connect(self.onProcessarPDF)
            view_action.triggered.connect(self.onProcessarPDF)  

            # Execute the context menu at the cursor's position
            context_menu.exec(self.tree.viewport().mapToGlobal(point))

import webbrowser

def numerar_pdf_gui():
    arquivo_entrada, _ = QFileDialog.getOpenFileName(caption="Selecione o arquivo PDF de entrada", filter="PDF Files (*.pdf)")
    
    # Se nenhum arquivo for selecionado, retorne
    if not arquivo_entrada:
        return None

    # Construir o nome do arquivo de saída baseado no arquivo de entrada
    base, ext = os.path.splitext(arquivo_entrada)
    arquivo_saida = base + "_numerado" + ext
    
    numerar_pdf_com_pypdf2(arquivo_entrada, arquivo_saida)

    # Abrir o arquivo no navegador padrão do usuário
    webbrowser.open(arquivo_saida)

def numerar_pdf_com_pypdf2(arquivo_entrada, output_pdf_path):
    # arquivo_entrada = filedialog.askopenfilename(title="Selecione o arquivo PDF de entrada")
    # Crie um novo PdfFileWriter object
    output = PdfWriter()
    input_pdf = PdfReader(open(arquivo_entrada, "rb"))

    # Processo de numeração
    for i in range(len(input_pdf.pages)):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        width = input_pdf.pages[i].mediabox[2]
        height = input_pdf.pages[i].mediabox[3]

        # Aqui, estamos colocando o número no canto superior direito.
        can = canvas.Canvas(packet, pagesize=(width, height))
        can.setFont("Helvetica", 14)
        can.setFillColor(black)  # Definindo a cor da fonte para preto
        can.drawString(float(width) - 30, float(height) - 30, str(i + 1))

        can.save()

        # Mova o buffer de posição para o início e crie um novo objeto PDF a partir dele
        packet.seek(0)
        new_pdf = PdfReader(packet)

        # Combine as páginas
        page = input_pdf.pages[i]
        page.merge_page(new_pdf.pages[0])

        output.add_page(page)

    # Escreva a saída
    with open(output_pdf_path, "wb") as output_file_handle:
        output.write(output_file_handle)

def load_treeview_data():
    return pd.read_csv(TREEVIEW_DATA_PATH)

from datetime import datetime
from num2words import num2words

def split_pdf_using_dataframe(arquivo_numerado, database_dir):
    # Caminho para o arquivo CSV com o item selecionado
    item_selecionado_path = Path(database_dir) / "item_selecionado.csv"
    
    # Lê o arquivo CSV para obter num_pregao e ano_pregao
    try:
        df_item_selecionado = pd.read_csv(item_selecionado_path)
        num_pregao = df_item_selecionado['num_pregao'].iloc[0]
        ano_pregao = df_item_selecionado['ano_pregao'].iloc[0]
    except Exception as e:
        print(f"Ocorreu um erro ao ler {item_selecionado_path}: {e}")
        return "Erro ao ler o arquivo do item selecionado."

    # Assegure-se de que num_pregao e ano_pregao são strings seguras para nomes de arquivos
    safe_num_pregao = str(num_pregao).replace('/', '-')
    safe_ano_pregao = str(ano_pregao).replace('/', '-')

    # Static directory to keep track of the latest output directory
    split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR = Path(database_dir) / 'relatorio' / f"PE {safe_num_pregao}-{safe_ano_pregao} - Processo Completo"
    split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR.mkdir(parents=True, exist_ok=True)
        
    df = pd.read_csv(TREEVIEW_DATA_PATH)
    
    # Use the numerated PDF file as input
    pdf_file_path = arquivo_numerado
    
    with open(pdf_file_path, "rb") as original_pdf_file:
        original_pdf = PyPDF2.PdfReader(original_pdf_file)
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            start_page = int(row["Início"]) - 1
            end_page = int(row["Fim"])
            if row["Início"] == row["Fim"]:
                output_filename = split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR / f"{idx:02} - {row['Identificação']} (Fl. {row['Início']}).pdf"
            else:
                output_filename = split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR / f"{idx:02} - {row['Identificação']} (Fls {row['Início']} a {row['Fim']}).pdf"
            new_pdf = PyPDF2.PdfWriter()
            for page_num in range(start_page, end_page):
                page = original_pdf.pages[page_num]
                new_pdf.add_page(page)
            with open(output_filename, "wb") as output_pdf_file:
                new_pdf.write(output_pdf_file)
    return split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR

def substituir_variaveis_docx(lv_split_final_dir):
    # Lendo o arquivo CSV
    df = pd.read_csv(TREEVIEW_DATA_PATH)
    
    # Inicializando o template DOCX
    doc = DocxTemplate(TEMPLATE_CHECKLIST)
    
    # Dicionário para mapear as variáveis para os valores
    context = {}
    
    # Lista de variáveis para substituir
    variaveis = ["abertura", "port_od", "port_comissao", "port_plan", "dfd", "etp", "mr", "tr", "pesquisa_precos", "minuta_edital"]
    
    for var in variaveis:
        subset_df = df[df["SAPIENS"] == var]
        
        # Check if subset is not empty
        if not subset_df.empty:
            row = subset_df.iloc[0]
            inicio, fim = row["Início"], row["Fim"]
            
            # Formatando o texto com base nos valores de "Início" e "fim"
            if inicio == fim:
                context[var] = f"Fl. {inicio}"
            else:
                context[var] = f"Fls. {inicio} a {fim}"
        else:
            print(f"Entrada não encontrada para variável: {var}")
            context[var] = "N/A"
    
    # Substituindo as variáveis no documento
    doc.render(context)
    
    # Determinando o nome do arquivo modificado
    arquivo_saida = split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR / (TEMPLATE_CHECKLIST.name.replace(".docx", "_modificado.docx"))
    
    # Salvando o documento modificado
    doc.save(arquivo_saida)

def substituir_marcadores_com_relacao(docx_path, lv_split_final_dir):
    # Carregar os dados do arquivo CSV
    df = load_treeview_data()
    
    # Processar os dados para criar a relação de documentos
    relacao_documentos = []
    for idx, row in enumerate(df.iterrows(), 1):
        if idx == len(df) - 1:  # Se for a penúltima linha
            terminacao = "; e"
        elif idx == len(df):  # Se for a última linha
            terminacao = "."
        else:
            terminacao = ";"

        if row[1]["Início"] == row[1]["Fim"]:
            relacao = f"{string.ascii_lowercase[idx-1]}) {row[1]['Identificação']} (Fl. {row[1]['Início']}){terminacao}"
        else:
            relacao = f"{string.ascii_lowercase[idx-1]}) {row[1]['Identificação']} (Fls. {row[1]['Início']} a {row[1]['Fim']}){terminacao}"
        relacao_documentos.append(relacao)

    relacao_documentos_str = "\n".join(relacao_documentos)
    
    # Obter o último valor de "Fim"
    ultima_folha = df["Fim"].iloc[-1]
    quantidade_folhas = f"{ultima_folha} ({num2words(ultima_folha, lang='pt_BR')}) folhas"
    
    # Obter a data atual no formato desejado
    hoje = datetime.now().strftime("%d/%m/%Y")
    
    # Carregar dados do item selecionado
    df_item_selecionado = pd.read_csv(ITEM_SELECIONADO_PATH)
    num_pregao = df_item_selecionado['num_pregao'].iloc[0]
    ano_pregao = df_item_selecionado['ano_pregao'].iloc[0]
    nup = df_item_selecionado['nup'].iloc[0]
    objeto = df_item_selecionado['objeto'].iloc[0]
    
    # Carregar e processar o template
    doc = DocxTemplate(docx_path)
    context = {
        'relacao_documentos': relacao_documentos_str,
        'quantidade_folhas': quantidade_folhas,
        'hoje': hoje,
        'num_pregao': num_pregao,
        'ano_pregao': ano_pregao,
        'nup': nup,
        'objeto': objeto
    }
    doc.render(context)
    
    output_path = split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR / f"PE {num_pregao}-{ano_pregao} - Relação de Documentos.docx"
    doc.save(output_path)
    return output_path

def processar_pdf_na_integra_e_gerar_documentos():
    global GLOBAL_SPLIT_DIR

    arquivo_numerado, _ = QFileDialog.getOpenFileName(caption="Selecione o arquivo PDF numerado", filter="PDF Files (*.pdf)")
    if not arquivo_numerado:
        return

    GLOBAL_SPLIT_DIR = split_pdf_using_dataframe(arquivo_numerado, DATABASE_DIR)

    substituir_marcadores_com_relacao(TEMPLATE_AUTUACAO, GLOBAL_SPLIT_DIR)
    substituir_variaveis_docx(GLOBAL_SPLIT_DIR)
    mensagem = "Todas as operações foram concluídas com sucesso!"
    print(mensagem)
    
    open_folder(GLOBAL_SPLIT_DIR)



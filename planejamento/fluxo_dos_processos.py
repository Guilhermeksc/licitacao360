from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import pandas as pd
import datetime
from datetime import datetime
from planejamento.utilidades_planejamento import extrair_chave_processo
df_uasg = pd.read_excel(TABELA_UASG_DIR)
global df_registro_selecionado
from bs4 import BeautifulSoup
import json
from datetime import datetime
import json
from pathlib import Path
import sqlite3

class CustomCalendarWidget(QCalendarWidget):
    def __init__(self, *args, **kwargs):
        super(CustomCalendarWidget, self).__init__(*args, **kwargs)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setStyleSheet("""
            QCalendarWidget QAbstractItemView {
                selection-background-color: yellow;
            }
        """)

class AlterarDatasDialog(QDialog):
    def __init__(self, listWidget, json_path):
        super().__init__()
        self.setWindowTitle("Alterar Datas")
        self.listWidget = listWidget              
        self.calendarios_inicio = []  # Lista para manter referências aos calendários de início
        self.calendarios_fim = []  # Lista para manter referências aos calendários de fim
        
        self.setupUi()

    def setupUi(self):
        layout = QVBoxLayout(self)

        processoSelecionado = self.listWidget.currentItem().text()
        chave_processo = extrair_chave_processo(processoSelecionado)  # Supondo que a função esteja definida em outro lugar

        with open(self.json_path, 'r', encoding='utf-8') as file:
            self.processos_json = json.load(file)

        if chave_processo in self.processos_json:
            scrollArea = QScrollArea()
            scrollWidget = QWidget()
            scrollLayout = QVBoxLayout(scrollWidget)
            scrollArea.setWidgetResizable(True)
            scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            scrollArea.setWidget(scrollWidget)

            for etapa in self.processos_json[chave_processo]['historico']:
                groupBox = QGroupBox(etapa['etapa'])
                vbox = QHBoxLayout(groupBox)

                # Layout para Data-Início
                hBoxInicio = QVBoxLayout()
                dataInicioLabel = QLabel('Data-Início')
                calendarWidgetInicio = CustomCalendarWidget(self)
                calendarWidgetInicio.clicked.connect(lambda date, cw=calendarWidgetInicio: self.atualizarDataInicio(date, cw))
                if etapa['data_inicial']:
                    data_inicio = QDate.fromString(etapa['data_inicial'], "dd-MM-yyyy")
                    calendarWidgetInicio.setSelectedDate(data_inicio)
                hBoxInicio.addWidget(dataInicioLabel)
                hBoxInicio.addWidget(calendarWidgetInicio)
                self.calendarios_inicio.append(calendarWidgetInicio)

                # Layout para Data-Fim
                hBoxFim = QVBoxLayout()
                dataFimLabel = QLabel('Data-Fim')
                calendarWidgetFinal = CustomCalendarWidget(self)
                calendarWidgetFinal.clicked.connect(lambda date, cw=calendarWidgetFinal: self.atualizarDataFim(date, cw))
                if etapa['data_final']:
                    data_fim = QDate.fromString(etapa['data_final'], "dd-MM-yyyy")
                    calendarWidgetFinal.setSelectedDate(data_fim)
                hBoxFim.addWidget(dataFimLabel)
                hBoxFim.addWidget(calendarWidgetFinal)
                self.calendarios_fim.append(calendarWidgetFinal)

                vbox.addLayout(hBoxInicio)
                vbox.addLayout(hBoxFim)
                scrollLayout.addWidget(groupBox)

            layout.addWidget(scrollArea)
        else:
            QMessageBox.warning(self, "Processo não encontrado", "O processo selecionado não foi encontrado no arquivo JSON.")

        btnSave = QPushButton("Salvar Alterações", self)
        btnSave.clicked.connect(self.salvarAlteracoes)
        layout.addWidget(btnSave)

    def atualizarDataInicio(self, date, cw):
        processoSelecionado = self.listWidget.currentItem().text()
        chave_processo = extrair_chave_processo(processoSelecionado)
        index = self.calendarios_inicio.index(cw)
        nova_data_inicio = date.toString("dd-MM-yyyy")

        # Atualizar a data_inicial no dicionário de processos_json
        self.processos_json[chave_processo]['historico'][index]['data_inicial'] = nova_data_inicio
        
        # Chamar método para ajustar datas subsequentes
        self.ajustarCalendarios()

    def atualizarDataFim(self, date, cw):
        processoSelecionado = self.listWidget.currentItem().text()
        chave_processo = extrair_chave_processo(processoSelecionado)
        index = self.calendarios_fim.index(cw)
        nova_data_fim = date.toString("dd-MM-yyyy")

        self.processos_json[chave_processo]['historico'][index]['data_final'] = nova_data_fim

        # Chamar método para ajustar datas subsequentes
        self.ajustarCalendarios()

    def ajustarCalendarios(self):
        # Atualiza os widgets de calendário baseados em processos_json
        processoSelecionado = self.listWidget.currentItem().text()
        chave_processo = extrair_chave_processo(processoSelecionado)
        historico = self.processos_json[chave_processo]['historico']

        for i, etapa in enumerate(historico[:-1]):  # Ignora a última etapa pois não há subsequente a comparar
            data_final_atual = QDate.fromString(etapa['data_final'], "dd-MM-yyyy")
            data_inicial_proxima = QDate.fromString(historico[i + 1]['data_inicial'], "dd-MM-yyyy")

            # Se a data_final for maior ou igual a data_inicial do subsequente, não faz nada
            if data_final_atual >= data_inicial_proxima:
                continue
            else:
                # Ajusta a data_inicial do próximo sequencial para ser igual a data_final do atual
                nova_data_inicial = data_final_atual.addDays(1).toString("dd-MM-yyyy")
                historico[i + 1]['data_inicial'] = nova_data_inicial
                if self.calendarios_inicio and i + 1 < len(self.calendarios_inicio):
                    self.calendarios_inicio[i + 1].setSelectedDate(data_final_atual.addDays(1))

        # Atualiza os widgets de calendário para refletir as possíveis mudanças
        for i, calendarWidgetInicio in enumerate(self.calendarios_inicio):
            if i < len(historico):
                etapa = historico[i]
                data_inicial = QDate.fromString(etapa['data_inicial'], "dd-MM-yyyy")
                calendarWidgetInicio.setSelectedDate(data_inicial)
        
        for i, calendarWidgetFinal in enumerate(self.calendarios_fim):
            if i < len(historico):
                etapa = historico[i]
                if etapa['data_final']:
                    data_final = QDate.fromString(etapa['data_final'], "dd-MM-yyyy")
                    calendarWidgetFinal.setSelectedDate(data_final)


    def salvarAlteracoes(self):
        # Chama a revisão de datas para garantir a consistência
        self.processos_json_manager.revisar_datas_processos()
        # Salva o JSON atualizado
        self.processos_json_manager.escrever_arquivo_json(self.processos_json_manager.processos_json)
        QMessageBox.information(self, "Alterações Salvas", "As alterações foram salvas com sucesso.")

class CustomListWidget(QListWidget):
    itemMoved = pyqtSignal(str, str)  # Sinal para movimentação de itens entre etapas
    allListWidgets = []  # Lista estática para manter todas as instâncias

    def __init__(self, parent=None):
        super().__init__(parent)
        CustomListWidget.allListWidgets.append(self)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setMinimumSize(QSize(190, 250))
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Configura para seleção única
        self.setStyleSheet("""
            QListWidget {
                border: 2px solid white;
                border-radius: 4px; 
                background-color: white;
            }
            QListWidget::item:selected {
                background-color: #a8d3ff;
            }
        """)
        self.previousSelectedWidget = None 

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:
            return  # Se nenhum item foi clicado, não faz nada

        # Extrai o HTML do texto do item
        html_texto_item = item.text()
        
        # Usa BeautifulSoup para parsear o HTML
        soup = BeautifulSoup(html_texto_item, 'lxml')
        
        # Encontra o primeiro span, que contém o texto desejado
        span = soup.find('span', style=lambda value: 'font-weight:600' in value)
        if not span:
            return  # Se não encontrar o span, não faz nada
        
        # O texto do span é o título desejado
        titulo_menu = span.get_text()

        contextMenu = QMenu(self)
        tituloAction = QAction(titulo_menu, self)
        tituloAction.setEnabled(False)  # Desabilita a ação para que não seja clicável
        contextMenu.addAction(tituloAction)  # Adiciona o "título" como o primeiro item do menu
        contextMenu.addSeparator()  # Opcional: adiciona um separador para diferenciar o "título" das opções

        alterarDatasAction = QAction('Alterar Datas', self)
        gerarRelatorioAction = QAction('Gerar Relatório', self)
        contextMenu.addAction(alterarDatasAction)
        contextMenu.addAction(gerarRelatorioAction)

        action = contextMenu.exec(QCursor.pos())  # Usa a posição do cursor para o menu
        if action == alterarDatasAction:
            self.abrirDialogoAlterarDatas()
        elif action == gerarRelatorioAction:
            pass  # Implementação futura

    def abrirDialogoAlterarDatas(self):
        dialog = AlterarDatasDialog(self, PROCESSOS_JSON_PATH)
        dialog.exec()

    def mousePressEvent(self, event):      
        super().mousePressEvent(event)
        currentItem = self.currentItem()
        if currentItem:
            currentWidget = self.itemWidget(currentItem)
            if currentWidget and event.button() == Qt.MouseButton.LeftButton:

                self.startDrag(Qt.DropAction.MoveAction)

    def addFormattedTextItem(self, id_processo, objeto):
        formattedText = f"""<html>
        <head/>
        <body>
            <p style='text-align: center;'>
                <span style='font-weight:600; font-size:14pt;'>{id_processo}</span><br/>
                <span style='font-size:10pt;'>{objeto}</span>
            </p>
        </body>
        </html>"""      
        item = QListWidgetItem()
        self.addItem(item)
        
        item.setSizeHint(QSize(0, 45))  # Ajuste a altura conforme necessário
        item.setText(formattedText) 

        label = QLabel(formattedText)

        label.setStyleSheet("background-color: white;")
        
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.setItemWidget(item, label)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            currentWidget = self.itemWidget(item)
            if currentWidget:
                print("Item selecionado para arrastar: ", item.text())  # Debug print
                print("Tipo do item: ", type(item))  # Debug print
                print("Tipo do widget do item: ", type(currentWidget))  # Debug print

                # Configura o mimeData para conter o texto do item
                mimeData = QMimeData()
                itemData = {"text": item.text(), "origin": self.objectName()}  # Usar o objectName como identificador da etapa
                mimeData.setText(json.dumps(itemData))  # Convertendo o dicionário para string JSON
                print("MimeData configurado: ", mimeData.text())  # Debug print
            
                # Cria o drag
                drag = QDrag(self)
                drag.setMimeData(mimeData)
            
                # Cria um pixmap para ser arrastado
                pixmap = QPixmap(currentWidget.size())
                currentWidget.render(pixmap)
                drag.setPixmap(pixmap)
                drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
                print("Pixmap criado e configurado para arrastar")  # Debug print
            
                # Debug print: Iniciando o drag realmente
                print("Drag iniciado")
                
                result = drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
                # Debug print: Resultado do drag
                print(f"Drag finalizado com ação: {result}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()


    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasText():
            itemData = json.loads(mimeData.text())
            originStage = itemData["origin"]
            destinationStage = self.objectName()  # A etapa de destino é o QListWidget atual
            newItemText = itemData["text"]  # Texto do item extraído do JSON

            print(f"Origem: {originStage}, Destino: {destinationStage}, Item: {newItemText}")

            # Extrair chave do processo do texto do item
            chave_processo = extrair_chave_processo(newItemText)

            # Verificar se a chave do processo já existe na etapa de destino
            alreadyExists = False
            for i in range(self.count()):
                existingItemText = self.item(i).text()
                existingItemKey = extrair_chave_processo(existingItemText)
                if chave_processo == existingItemKey:
                    alreadyExists = True
                    break
                    
            if not alreadyExists:
                # Adiciona o item à lista de destino se não for uma duplicata
                label = QLabel(newItemText)
                label.setStyleSheet("background-color: white;")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                item = QListWidgetItem(newItemText)
                self.addItem(item)
                item.setSizeHint(QSize(0, 45))
                self.setItemWidget(item, label)
                
                self.itemMoved.emit(newItemText, self.objectName())  # Emitir sinal com o texto do item e o nome da nova etapa
                self.sortItems()  # Organizar itens, se necessário
                print("Item adicionado e ordenado.")
            else:
                # Ação para item duplicado, por exemplo, mostrar uma mensagem ao usuário
                print("O processo já existe na etapa de destino.")

            event.acceptProposedAction()  # Confirma a ação de drop
      
class ProcessFlowDialog(QDialog):
    def __init__(self, etapas, df_processos, database_manager, parent=None):
        super().__init__(parent)
        self.etapas = etapas
        self.df_processos = df_processos
        self.database_manager = database_manager
        self.setWindowTitle("Painel de Fluxo dos Processos")
        self.setFixedSize(QSize(1490, 750))
        self.setStyleSheet("""
            QDialog {
                background-color: #050f41;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        headerLayout = QHBoxLayout()
        titleLabel = QLabel("Controle do Fluxo dos Processos")
        titleLabel.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")  # Ajuste conforme necessário
        headerLayout.addWidget(titleLabel)
        
        headerLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        pixmap = QPixmap(str(MARINHA_PATH))
        pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label = QLabel()  # Este é o QLabel que deve conter a imagem
        image_label.setPixmap(pixmap)
        headerLayout.addWidget(image_label)  # Adiciona o QLabel correto que contém a imagem
        
        layout.addLayout(headerLayout)
        
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Metade das etapas para cada layout
        metade_etapas = len(self.etapas) // 2

        # Iterar sobre cada etapa para criar e adicionar um CustomListWidget correspondente
        for index, (etapa, _) in enumerate(self.etapas.items()):
            group_box = self._create_group_box(etapa)
            list_widget = group_box.findChild(CustomListWidget)  # Encontra o CustomListWidget dentro do QGroupBox
            list_widget.setObjectName(etapa)  # Define o nome da etapa como objectName do QListWidget
            self.etapas[etapa] = list_widget 
            # Distribui os groupboxes entre os dois layouts
            if index < metade_etapas:
                top_layout.addWidget(group_box)
            else:
                bottom_layout.addWidget(group_box)

        # Adiciona os layouts de metade superior e inferior ao layout principal
        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)

        # Conectar sinais de cada CustomListWidget ao slot onItemMoved após a criação de todos
        self._connect_item_moved_signals()

    def _create_group_box(self, etapa):
        group_box = QGroupBox(etapa)
        font = QFont()
        font.setBold(True)  # Define a fonte para negrito
        font.setPointSize(13)  # Define o tamanho da fonte para 14
        group_box.setFont(font)  # Aplica a fonte ao título do QGroupBox
        group_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid white;
                border-radius: 10px;
            }
            QGroupBox::title {
                font-weight: bold; 
                font-size: 14px; 
                color: white;
            }
        """)
            
        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(1, 25, 1, 4)

        # Ajustado para refletir a refatoração sugerida
        list_widget = CustomListWidget(parent=self)
        list_widget.setObjectName(etapa) 
        print(f"Definindo objectName para list_widget: {list_widget.objectName()}")

        self._populate_list_widget(list_widget)

        layout.addWidget(list_widget)

        return group_box
        
    def _populate_list_widget(self, list_widget):
        print(f"Preenchendo {list_widget.objectName()}...")

        with self.database_manager as conn:
            # Primeiro, atualiza as etapas na tabela controle_processos com base nas informações mais recentes de controle_prazos
            self.database_manager.verificar_e_atualizar_etapas(conn)

            cursor = conn.cursor()

            # Consulta atualizada para preencher o list_widget com base nas etapas atualizadas
            cursor.execute('''
                SELECT cpz.chave_processo, cp.objeto, cpz.sequencial
                FROM controle_prazos cpz
                INNER JOIN (
                    SELECT chave_processo, MAX(sequencial) AS max_sequencial
                    FROM controle_prazos
                    GROUP BY chave_processo
                ) AS max_cpz ON cpz.chave_processo = max_cpz.chave_processo AND cpz.sequencial = max_cpz.max_sequencial
                INNER JOIN controle_processos cp ON cpz.chave_processo = cp.id_processo
                WHERE cpz.etapa = ?
                ORDER BY cpz.chave_processo
            ''', (list_widget.objectName(),))

            processos = cursor.fetchall()

        for processo in processos:
            chave_processo, objeto, ultimo_sequencial = processo
            print(f"Processo: {chave_processo}, Objeto: {objeto}, Último Sequencial: {ultimo_sequencial}")

            # Processamento da chave_processo para formatá-la corretamente antes de adicionar ao list_widget
            partes = chave_processo.split()
            mod = partes[0]
            num_pregao, ano_pregao = partes[1].split('/')
            id_processo = f"{mod} {num_pregao}/{ano_pregao}"

            # Adiciona o item formatado ao list_widget de forma única
            list_widget.addFormattedTextItem(id_processo=id_processo, objeto=objeto)

    def _connect_item_moved_signals(self):
        for list_widget in CustomListWidget.allListWidgets:
            if list_widget.parent() is not None:
                list_widget.itemMoved.connect(self.onItemMoved)
            else:
                print("Widget não está mais válido:", list_widget)

    def onItemMoved(self, itemText, newListWidgetName):
        chave_processo = extrair_chave_processo(itemText)
        comentario = f"Movido para a etapa: {newListWidgetName}"
        print(f"Item movido: {chave_processo}, para: {newListWidgetName}, comentário: {comentario}")
        if chave_processo:
            # Agora usamos DatabaseManager para inserir o novo registro
            data_atual_str = datetime.today().strftime("%Y-%m-%d")
            self.database_manager.inserir_controle_prazo(chave_processo, newListWidgetName, data_atual_str, comentario)

import re

def extract_info(html_text):
    # Ajustando a expressão regular para considerar espaços e quebras de linha
    match = re.search(r"<span style='font-weight:600; font-size:14pt;'>(.*?)</span><br/>\s*<span style='font-size:10pt;'>(.*?)</span>", html_text, re.DOTALL)
    if match:
        id_processo = match.group(1).strip()
        objeto = match.group(2).strip()
        # Extrai o número do pregão da id_processo para ordenação
        num_match = re.search(r'\d+', id_processo)
        number = int(num_match.group(0)) if num_match else 0
        print(f"Modalidade: {id_processo}, Objeto: {objeto}, Número: {number}")
        return id_processo, objeto, number
    else:
        print("Não foi possível extrair informações com a expressão regular.")
    return "", "", 0

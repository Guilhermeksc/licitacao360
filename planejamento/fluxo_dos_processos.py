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

class ProcessosJSONManager:
    def __init__(self, arquivo_json_path):
        self.arquivo_json_path = Path(arquivo_json_path)
        self.processos_json = self.ler_arquivo_json()
        self.revisar_datas_processos()
        self.calcular_dias_na_etapa()
        self.escrever_arquivo_json(self.processos_json)

    def ler_arquivo_json(self):
        try:
            with open(self.arquivo_json_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Arquivo {self.arquivo_json_path} não encontrado. Criando um novo arquivo.")
            return {}

    def escrever_arquivo_json(self, dados):
        print(json.dumps(dados, ensure_ascii=False, indent=4))  # Para depuração
        with open(self.arquivo_json_path, 'w', encoding='utf-8') as file:
            json.dump(dados, file, ensure_ascii=False, indent=4)
        print(f"Arquivo JSON {self.arquivo_json_path} atualizado com sucesso.")

    def revisar_datas_processos(self):
        formato_data = "%d-%m-%Y"
        for processo, dados in self.processos_json.items():
            historico = dados['historico']
            for i in range(len(historico) - 1):
                data_inicial_atual = datetime.strptime(historico[i]['data_inicial'], formato_data) if historico[i]['data_inicial'] else datetime.min
                data_final_atual = datetime.strptime(historico[i]['data_final'], formato_data) if historico[i]['data_final'] else data_inicial_atual
                data_inicial_proxima = datetime.strptime(historico[i + 1]['data_inicial'], formato_data)

                if data_final_atual > data_inicial_proxima:
                    historico[i]['data_final'] = historico[i + 1]['data_inicial']
                
                # Garante que data_inicial não seja maior que data_final
                if data_inicial_atual > data_final_atual:
                    historico[i]['data_final'] = historico[i]['data_inicial']
                    
                # Atualiza a data inicial da próxima etapa se necessário
                if i < len(historico) - 2:
                    historico[i + 1]['data_inicial'] = max(data_final_atual, data_inicial_proxima).strftime(formato_data)

    def calcular_dias_na_etapa(self):
        for processo, dados in self.processos_json.items():
            historico = dados['historico']
            for etapa in historico:
                if etapa['data_inicial'] and etapa['data_final']:
                    # Converter strings de data para objetos datetime
                    data_inicial = datetime.strptime(etapa['data_inicial'], "%d-%m-%Y")
                    data_final = datetime.strptime(etapa['data_final'], "%d-%m-%Y")
                    # Calcular a diferença em dias
                    etapa['dias_na_etapa'] = (data_final - data_inicial).days
                else:
                    # Se a data_inicial é None (ou seja, não definida), assumir 0 dias
                    etapa['dias_na_etapa'] = 0

        print("Atualização dos dias nas etapas concluída.")

    def atualizar_processo(self, chave_processo, nova_etapa, comentario):
        print(f"Atualizando processo {chave_processo} para a etapa {nova_etapa}")
        processos_json = self.ler_arquivo_json()
        data_atual_str = datetime.today().strftime("%d-%m-%Y")
        historico = processos_json.setdefault(chave_processo, {"historico": []})["historico"]

        # Ajustar data_final de cada etapa para ser igual à data_inicial da próxima etapa
        for i in range(len(historico) - 1):
            historico[i]["data_final"] = historico[i + 1]["data_inicial"]
        
        # Atualizar a data_final da última etapa para hoje se for None
        if historico and historico[-1]["data_final"] is None:
            historico[-1]["data_final"] = data_atual_str
        
        # Recalcular dias_na_etapa para todas as etapas com base nas datas ajustadas
        for etapa in historico:
            if etapa["data_inicial"]:
                data_inicial = datetime.strptime(etapa["data_inicial"], "%d-%m-%Y")
                data_final = datetime.strptime(etapa["data_final"], "%d-%m-%Y")
                etapa["dias_na_etapa"] = (data_final - data_inicial).days
            else:
                etapa["dias_na_etapa"] = 0  # Caso data_inicial seja None

        # Adicionar a nova etapa ao final do histórico
        historico.append({
            "etapa": nova_etapa,
            "data_inicial": data_atual_str,
            "data_final": None,
            "dias_na_etapa": 0,
            "comentario": comentario,
            "sequencial": len(historico) + 1
        })

        self.escrever_arquivo_json(processos_json)
        print(f"Processo {chave_processo} atualizado com sucesso para a etapa {nova_etapa}.")

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
        self.json_path = json_path
        self.processos_json_manager = ProcessosJSONManager(json_path)  # Cria a instância de ProcessosJSONManager
        self.processos_json = self.processos_json_manager.processos_json                
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
        # Redefinir o estilo do widget anteriormente selecionado, se houver
        if self.previousSelectedWidget is not None:
            self.previousSelectedWidget.setStyleSheet("""
                background-color: white;
                border: 0.8px solid transparent; 
            """)
        
        super().mousePressEvent(event)
        currentItem = self.currentItem()
        if currentItem:
            currentWidget = self.itemWidget(currentItem)
            if currentWidget and event.button() == Qt.MouseButton.LeftButton:

                self.startDrag(Qt.DropAction.MoveAction)

    def addFormattedTextItem(self, modalidade, objeto):
        formattedText = f"""<html>
        <head/>
        <body>
            <p style='text-align: center;'>
                <span style='font-weight:600; font-size:14pt;'>{modalidade}</span><br/>
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

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasText():
            itemData = json.loads(mimeData.text())
            originStage = itemData["origin"]
            destinationStage = self.objectName()  # A etapa de destino é o QListWidget atual
            newItemText = itemData["text"]  # Texto do item extraído do JSON

            # Log de debug
            print(f"Item movido de {originStage} para {destinationStage}")

            # Certifique-se de que a lógica de processamento abaixo use `newItemText`
            # que é o texto do item, ao invés da string JSON completa
            source = event.source()
            if source != self:
                if not self.findItems(newItemText, Qt.MatchFlag.MatchExactly):
                    # Cria um novo QLabel com o texto do item
                    label = QLabel(newItemText)
                    label.setStyleSheet("background-color: white;")
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Cria um novo QListWidgetItem e adiciona o QLabel a ele
                    item = QListWidgetItem(newItemText)
                    self.addItem(item)
                    item.setSizeHint(QSize(0, 45))  # Ajuste a altura conforme necessário
                    self.setItemWidget(item, label)
                    
                    event.acceptProposedAction()
                    self.itemMoved.emit(newItemText, self.objectName())  # Emitir sinal com o texto do item e o nome da nova etapa
                    self.sortItems()  # Utiliza a ordenação padrão do QListWidget, considerar a implementação customizada se necessário
                else:
                    event.ignore()

    def sortListItems(self):
        items = [self.item(i).text() for i in range(self.count())]

        def extract_info(text):
            parts = text.split(' ')
            if len(parts) > 2 and '/' in parts[2]:
                mod = parts[0]
                number, year = parts[2].split('/')
                return mod, int(number), year
            return "", 0, ""  # Retorna valores padrão se o formato não for o esperado

        items.sort(key=lambda x: extract_info(x)[1])  # Ordena pelo número do pregão (parte central da tupla retornada por extract_info)

        self.clear()  # Limpa a lista
        for item in items:
            mod, number, year = extract_info(item)
            if number > 0:
                formatted_number = f"{mod} {int(number):02d}/{year}"
                self.addItem(formatted_number)
            else:
                self.addItem(item)  # Adiciona itens não formatados como estão
      
class ProcessFlowDialog(QDialog):
    def __init__(self, etapas, df_processos, parent=None):
        super().__init__(parent)
        self.etapas = etapas
        self.df_processos = df_processos  # Dados dos processos agora são passados como um parâmetro
        self.setWindowTitle("Painel de Fluxo dos Processos")
        self.setFixedSize(QSize(1490, 750))
        self.setStyleSheet("""
            QDialog {
                background-color: #050f41;
            }
        """)
        self.manager_json = ProcessosJSONManager(PROCESSOS_JSON_PATH)
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

        self._populate_list_widget(list_widget, PROCESSOS_JSON_PATH)
        print(f"PROCESSOS_JSON_PATH: {PROCESSOS_JSON_PATH}")

        layout.addWidget(list_widget)

        return group_box

    def _populate_list_widget(self, list_widget, caminho_json):
        # print(f"Populando list_widget: {list_widget.objectName()} com dados de: {caminho_json}")
        with open(caminho_json, 'r', encoding='utf-8') as file:
            processos_json = json.load(file)

        for chave_processo, dados_processo in processos_json.items():
            ultima_etapa = dados_processo['historico'][-1]['etapa']
            print(f"Processo {chave_processo} na última etapa {ultima_etapa}")
            if ultima_etapa == list_widget.objectName():
                print(f"Adicionando {chave_processo} ao widget {list_widget.objectName()}")

                # Correção na descompactação aqui
                partes = chave_processo.split()
                mod = partes[0]
                num_pregao, ano_pregao = partes[1].split('/')
                modalidade = f"{mod} {num_pregao}/{ano_pregao}"
                print(f"Adicionando {chave_processo} ao widget {list_widget.objectName()}")

                objeto = dados_processo['objeto']
                
                # Assume que addFormattedTextItem é um método que você definiu
                # para adicionar itens formatados ao list_widget
                list_widget.addFormattedTextItem(
                    modalidade=modalidade,
                    objeto=objeto
                )

    def _connect_item_moved_signals(self):
        # Este método conecta o sinal itemMoved de cada CustomListWidget a um slot adequado
        for list_widget in CustomListWidget.allListWidgets:
            list_widget.itemMoved.connect(self.onItemMoved)

    def onItemMoved(self, itemText, newListWidgetName):
        chave_processo = extrair_chave_processo(itemText)
        comentario = "Movido para a etapa: " + newListWidgetName
        print(f"Item movido: {chave_processo}, para: {newListWidgetName}, comentário: {comentario}")
        if chave_processo:
            # Instancia ProcessosJSONManager e chama atualizar_processo
            manager = ProcessosJSONManager(PROCESSOS_JSON_PATH)
            manager.atualizar_processo(chave_processo, newListWidgetName, comentario)

        # Lógica para remover o item da lista original segue como antes
        for listWidget in CustomListWidget.allListWidgets:
            if listWidget.objectName() != newListWidgetName:
                items = listWidget.findItems(itemText, Qt.MatchFlag.MatchExactly)
                for item in items:
                    row = listWidget.row(item)
                    listWidget.takeItem(row)
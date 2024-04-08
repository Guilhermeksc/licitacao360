from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
from utils.treeview_utils import load_images, create_button, save_dataframe_to_excel
import pandas as pd
import os
import datetime
from datetime import datetime
import openpyxl
from planejamento.popup_relatorio import ReportDialog
from planejamento.escalacao_pregoeiro import EscalarPregoeiroDialog
from planejamento.autorizacao import AutorizacaoAberturaLicitacaoDialog
from planejamento.utilidades_planejamento import inicializar_json_do_excel, carregar_dados_processos, carregar_ou_criar_arquivo_json, extrair_chave_processo
df_uasg = pd.read_excel(TABELA_UASG_DIR)
global df_registro_selecionado
df_registro_selecionado = None
from bs4 import BeautifulSoup
import json
from datetime import datetime

class ProcessosJSONManager:
    def __init__(self, arquivo_json_path):
        self.arquivo_json_path = arquivo_json_path

    def ler_arquivo_json(self):
        try:
            with open(self.arquivo_json_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def escrever_arquivo_json(self, dados):
        with open(self.arquivo_json_path, 'w', encoding='utf-8') as file:
            json.dump(dados, file, ensure_ascii=False, indent=4)
        print(f"Arquivo JSON {self.arquivo_json_path} atualizado com sucesso.")

    def atualizar_processo(self, chave_processo, nova_etapa, comentario):
        print(f"Atualizando processo {chave_processo} para a etapa {nova_etapa}")
        processos_json = self.ler_arquivo_json()
        data_atual = datetime.today().strftime("%d-%m-%Y")
        historico = processos_json.setdefault(chave_processo, {"historico": []})["historico"]

        if historico:
            # Atualiza a data_final da última entrada, se existir
            if historico[-1]["data_final"] is None:
                historico[-1]["data_final"] = data_atual
                print(f"Atualizando data_final do último registro de {chave_processo} para {data_atual}")
        else:
            print(f"Nenhum histórico encontrado para {chave_processo}, criando o primeiro registro.")

        historico.append({
            "etapa": nova_etapa,
            "data_inicial": data_atual,
            "data_final": None,
            "dias_na_etapa": 0,
            "comentario": comentario,
            "sequencial": len(historico) + 1
        })
        self.escrever_arquivo_json(processos_json)
        print(f"Processo {chave_processo} atualizado com sucesso para a etapa {nova_etapa}.")


etapas = {
    'Planejamento': None,
    'Setor Responsável': None,
    'IRP': None,
    'Edital': None,
    'Nota Técnica': None,
    'AGU': None,
    'Recomendações AGU': None,
    'Divulgado': None,
    'Impugnado': None,
    'Sessão Pública': None,
    'Em recurso': None,
    'Homologado': None,
    'Assinatura Contrato': None,
    'Concluído': None
}

class AlterarDatasDialog(QDialog):
    def __init__(self, listWidget, json_path):
        super().__init__()
        self.setWindowTitle("Alterar Datas")
        self.listWidget = listWidget
        self.json_path = json_path
        self.processos_json = {}  # Dicionário para armazenar os dados do processo carregados do JSON
        self.setupUi()

    def setupUi(self):
        layout = QVBoxLayout(self)

        processoSelecionado = self.listWidget.currentItem().text()
        chave_processo = extrair_chave_processo(processoSelecionado)

        # Carregar dados do arquivo JSON
        with open(self.json_path, 'r', encoding='utf-8') as file:
            self.processos_json = json.load(file)

        # Verificar se o processo selecionado existe no JSON
        if chave_processo in self.processos_json:
            scrollArea = QScrollArea()
            scrollWidget = QWidget()
            scrollLayout = QVBoxLayout(scrollWidget)
            scrollArea.setWidgetResizable(True)
            scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            scrollArea.setWidget(scrollWidget)

            for etapa in self.processos_json[chave_processo]['historico']:
                groupBox = QGroupBox(etapa['etapa'])
                vbox = QVBoxLayout(groupBox)

                etapaLabel = QLabel(etapa['etapa'])
                calendarWidgetInicio = QCalendarWidget(self)
                calendarWidgetFinal = QCalendarWidget(self)
                
                if etapa['data_inicial']:
                    data_inicio = QDate.fromString(etapa['data_inicial'], "dd-MM-yyyy")
                    calendarWidgetInicio.setSelectedDate(data_inicio)
                if etapa['data_final']:
                    data_fim = QDate.fromString(etapa['data_final'], "dd-MM-yyyy")
                    calendarWidgetFinal.setSelectedDate(data_fim)

                vbox.addWidget(etapaLabel)
                vbox.addWidget(calendarWidgetInicio)
                vbox.addWidget(calendarWidgetFinal)
                scrollLayout.addWidget(groupBox)

            layout.addWidget(scrollArea)
        else:
            QMessageBox.warning(self, "Processo não encontrado", "O processo selecionado não foi encontrado no arquivo JSON.")

        btnSave = QPushButton("Salvar Alterações", self)
        btnSave.clicked.connect(self.salvarAlteracoes)
        layout.addWidget(btnSave)

    def salvarAlteracoes(self):
        # Implemente a lógica para salvar as alterações aqui
        with open(self.json_path, 'w', encoding='utf-8') as file:
            json.dump(self.processos_json, file, ensure_ascii=False, indent=4)
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

    def addFormattedTextItem(self, mod, num_pregao, ano_pregao, objeto):
        formattedText = f"""<html>
        <head/>
        <body>
            <p style='text-align: center;'>
                <span style='font-weight:600; font-size:14pt;'>{mod} {num_pregao}/{ano_pregao}</span><br/>
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
                
                print(f"Adicionando {chave_processo} ao widget {list_widget.objectName()}")

                objeto = dados_processo['objeto']
                
                # Assume que addFormattedTextItem é um método que você definiu
                # para adicionar itens formatados ao list_widget
                list_widget.addFormattedTextItem(
                    mod=mod,
                    num_pregao=num_pregao,
                    ano_pregao=ano_pregao,
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
                    
class ContextMenu(QMenu):
    def __init__(self, main_app, index, model=None):
        super().__init__()
        self.main_app = main_app
        self.index = index
        self.model = model

        # Opções do menu
        actions = [
            "Autorização para Abertura de Licitação",
            "Portaria de Equipe de Planejamento",
            "Documento de Formalização de Demanda (DFD)",
            "Declaração de Adequação Orçamentária",
            "Mensagem de Divulgação de IRP",
            "Mensagem de Publicação",
            "Mensagem de Homologação",
            "Capa do Edital"
        ]
        
        # Conectando ações
        for actionText in actions:
            action = QAction(actionText, self)
            action.triggered.connect(lambda checked, a=actionText: self.openDialog(a))
            self.addAction(action)
    
    def openDialog(self, actionText):
        if actionText == "Autorização para Abertura de Licitação":
            index = self.index  # Utilize o índice armazenado para acessar os dados
            model = index.model()  # Modelo da tree_view
            mod = model.data(model.index(index.row(), 0))  # Ajuste os números de índice conforme necessário
            num_pregao = model.data(model.index(index.row(), 1))
            ano_pregao = model.data(model.index(index.row(), 2))
            item_pca = model.data(model.index(index.row(), 3))
            portaria_PCA = model.data(model.index(index.row(), 4))

            # Exemplo de como você poderia criar a instância de AutorizacaoAberturaLicitacaoDialog
            dialog = AutorizacaoAberturaLicitacaoDialog(main_app=self, df_registro=df_registro_selecionado, mod="mod", num_pregao="num_pregao", ano_pregao="ano_pregao", item_pca="item_pca", portaria_PCA="portaria_PCA")
            dialog.exec()
        else:
            # Placeholder para outras ações
            msgBox = QMessageBox()
            msgBox.setWindowTitle(actionText)
            msgBox.setText(f"Ação selecionada: {actionText}")
            msgBox.exec()

def ajustar_colunas_planilha(file_path):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    column_widths = {
        1: 10, 
        2: 10, 
        3: 25, 
        4: 35, 
        5: 0,
        6: 40, 
        7: 10, 
        8: 20, 
        9: 10,
        10: 20, 
        11: 20
    }

    for col_num, width in column_widths.items():
        if width > 0:
            column_letter = openpyxl.utils.get_column_letter(col_num)
            sheet.column_dimensions[column_letter].width = width

    workbook.save(file_path)

class ApplicationUI(QMainWindow):
    itemSelected = pyqtSignal(str, str, str)  # Sinal com dois argumentos de string

    NOME_COLUNAS = {
        'mod': 'Mod.',
        'num_pregao': 'N',
        'ano_pregao': 'Ano',
        'item_pca': 'Item PCA',
        'portaria_PCA': 'Portaria_PCA',	
        'data_sessao': 'Data Sessão',
        'nup': 'NUP',
        'objeto': 'Objeto',
        'uasg': 'UASG',
        'orgao_responsavel': 'Órgão Responsável',
        'sigla_om': 'Sigla Órgão',
        'setor_responsavel': 'Demandante',
        'coordenador_planejamento': 'Coordenador',
        'etapa': 'Etapa',
        'pregoeiro': 'Pregoeiro',
    }

    dtypes = {
        'mod': str,
        'num_pregao': int,
        'ano_pregao': int,
        'item_pca': str,
        'portaria_PCA': str,	
        'data_sessao': str,
        'nup': str,
        'objeto': str,
        'uasg': str,
        'orgao_responsavel': str,
        'sigla_om': str,
        'setor_responsavel': str,
        'coordenador_planejamento': str,
        'etapa': str,
        'pregoeiro': str
    }

    def __init__(self, app, icons_dir, database_dir, lv_final_dir):

        super().__init__()
        self.icons_dir = Path(icons_dir)
        self.database_dir = Path(database_dir)
        self.lv_final_dir = Path(lv_final_dir)
        self.app = app  # Armazenar a instância do App
        
        # Carregar df_uasg uma única vez aqui
        self.df_uasg = pd.read_excel(TABELA_UASG_DIR)     
        self.columns_treeview = list(self.NOME_COLUNAS.keys())
        self.image_cache = {}
        inicializar_json_do_excel(CONTROLE_PROCESSOS_DIR, PROCESSOS_JSON_PATH)

        # Carregar os dados de licitação no início, removendo a inicialização redundante
        self.df_licitacao_completo = pd.read_excel(CONTROLE_PROCESSOS_DIR, converters={'num_pregao': lambda x: self.convert_to_int(x)})
        # print("Valores de índices em df_licitacao_completo:")
        # for index in self.df_licitacao_completo.index:
        #     print(f"Índice: {index}, Valor: {self.df_licitacao_completo.loc[index].to_dict()}")

        self.image_cache = load_images(self.icons_dir, [
            "plus.png", "save_to_drive.png", "loading.png", "delete.png", "excel.png", "website_menu.png"
        ])
        self.setup_ui()
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.openContextMenu)

    def openContextMenu(self, position):
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        contextMenu = ContextMenu(self, index, self.model)
        contextMenu.exec(self.tree_view.viewport().mapToGlobal(position))
        
    def convert_to_int(self, cell_value):
        try:
            return int(cell_value)
        except ValueError:
            return pd.NA  # or some default value or error handling pd.NA  # or a default value like 0 or -1 depending on your requirements

    def _get_image(self, image_file_name):
        # Método para obter imagens do cache ou carregar se necessário
        if image_file_name not in self.image_cache:
            image_path = self.icons_dir / image_file_name
            self.image_cache[image_file_name] = QIcon(str(image_path))  # Usando QIcon para compatibilidade com botões
        return self.image_cache[image_file_name]

    def setup_ui(self):
        self._setup_central_widget()
        self._setup_treeview()  # Configura o QTreeView
        self._adjust_column_widths() 
        self._setup_uasg_delegate()
        self._setup_buttons_layout()
        self.main_layout.addWidget(self.tree_view)
        self._load_data()

    def _setup_central_widget(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
    def _setup_buttons_layout(self):
        self.buttons_layout = QHBoxLayout()
        self._create_buttons()
        self.main_layout.addLayout(self.buttons_layout)
            
    def _create_buttons(self):
        self.buttons_layout = QHBoxLayout()
        self.button_specs = [
            ("  Adicionar", self.image_cache['plus'], self.on_add_item, "Adiciona um novo item"),
            ("  Salvar", self.image_cache['save_to_drive'], self.on_save_data, "Salva o dataframe em um arquivo excel('.xlsx')"),
            ("  Carregar", self.image_cache['loading'], self.on_load_data, "Carrega o dataframe de um arquivo existente('.xlsx' ou '.odf')"),
            ("  Excluir", self.image_cache['delete'], self.on_delete_item, "Adiciona um novo item"),
            ("  Controle do Processo", self.image_cache['website_menu'], self.on_control_process, "Abre o painel de controle do processo"),            
            ("  Escalar Pregoeiro", self.image_cache['delete'], self.on_get_pregoeiro, "Escala um novo pregoeiro para o pregão selecionado"),
            ("  Abrir Planilha Excel", self.image_cache['excel'], self.abrir_planilha_controle, "Abre a planilha de controle"),
            ("    Relatório", self.image_cache['website_menu'], self.on_generate_report, "Gera um relatório dos dados")
        ]

        for text, icon, callback, tooltip in self.button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self)
            self.buttons_layout.addWidget(btn)  # Adicione o botão ao layout dos botões

    def on_get_pregoeiro(self):
        index = self.tree_view.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Seleção", "Por favor, selecione um item da lista.")
            return

        # Supondo que você tem um modelo padrão onde:
        # - mod é na coluna 0
        # - num_pregao é na coluna 1
        # - ano_pregao é na coluna 2
        # Ajuste os índices das colunas conforme a estrutura do seu modelo
        mod_index = self.tree_view.model().index(index.row(), 0)
        num_pregao_index = self.tree_view.model().index(index.row(), 1)
        ano_pregao_index = self.tree_view.model().index(index.row(), 2)

        mod = self.tree_view.model().data(mod_index)
        num_pregao = self.tree_view.model().data(num_pregao_index)
        ano_pregao = self.tree_view.model().data(ano_pregao_index)

        # Agora, você pode passar esses valores para o diálogo
        dialog = EscalarPregoeiroDialog(self.df_licitacao_completo, mod, ano_pregao, num_pregao, self)
        dialog.exec()

    def on_generate_report(self):
        dialog = ReportDialog(self.df_licitacao_completo, self.icons_dir, self)
        dialog.exec()

    def abrir_planilha_controle(self):
        file_path = str(CONTROLE_PROCESSOS_DIR)  # Defina o caminho do arquivo aqui
        try:
            ajustar_colunas_planilha(file_path)
            os.startfile(file_path)
        except Exception as e:
            print(f"Erro ao abrir o arquivo: {e}")

    def _setup_treeview(self):
        # Cria uma nova instância do modelo
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([self.NOME_COLUNAS[col] for col in self.NOME_COLUNAS])

        # Configurações do QTreeView
        self.tree_view = QTreeView(self)
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIsDecorated(False)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.clicked.connect(self._on_item_click)
        self.tree_view.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.model.dataChanged.connect(self._on_item_changed)

        # Configuração para tratar o clique com o botão direito
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.onCustomContextMenuRequested)

        # Adiciona o QTreeView ao layout principal
        self.main_layout.addWidget(self.tree_view)

        # Ajusta as larguras das colunas
        self._adjust_column_widths()

    def onCustomContextMenuRequested(self, position):
        # Seleciona a linha antes de mostrar o menu de contexto
        index = self.tree_view.indexAt(position)
        if index.isValid():
            self.tree_view.selectionModel().select(index, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
            self._on_item_click(index)  # Chamada para a função que trata a seleção de item
            # Aqui você pode implementar a abertura do menu de contexto se necessário
            
    def _adjust_column_widths(self):
        header = self.tree_view.header()
        header.setStretchLastSection(True)

        # Configura todas as colunas para ajustar-se ao conteúdo
        for column in range(self.model.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

    def on_context_menu(self, point):
        # Obter o índice do item sob o cursor quando o menu de contexto é solicitado
        index = self.tree_view.indexAt(point)
        
        if index.isValid():
            # Chamar _on_item_click se o índice é válido
            self._on_item_click(index)

            # Criar o menu de contexto
            context_menu = QMenu(self.tree_view)

            # Configurar o estilo do menu de contexto
            context_menu.setStyleSheet("QMenu { font-size: 12pt; }")

            # Adicionar outras ações ao menu
            add_action = context_menu.addAction(QIcon(str(self.icons_dir / "add.png")), "Adicionar")
            edit_action = context_menu.addAction(QIcon(str(self.icons_dir / "engineering.png")), "Editar")
            delete_action = context_menu.addAction(QIcon(str(self.icons_dir / "delete.png")), "Excluir")
            view_action = context_menu.addAction(QIcon(str(self.icons_dir / "search.png")), "Visualizar")

            # Conectar ações a métodos
            add_action.triggered.connect(self.on_add_item)
            edit_action.triggered.connect(self.on_edit_item)
            delete_action.triggered.connect(self.on_delete_item)
            view_action.triggered.connect(self.on_view_item)

            # Executar o menu de contexto na posição do cursor
            context_menu.exec(self.tree_view.viewport().mapToGlobal(point))

    def on_add_item(self):
        # Encontrar o maior número de pregão e adicionar 1
        if not self.model.rowCount():
            novo_num_pregao = 1
        else:
            ultimo_num_pregao = max(int(self.model.item(row, self.columns_treeview.index('num_pregao')).text()) for row in range(self.model.rowCount()))
            novo_num_pregao = ultimo_num_pregao + 1

        # Obter o ano atual
        ano_atual = datetime.datetime.now().year

        # Definir o valor padrão para UASG
        uasg_valor_padrao = "787000"

        # Buscar os dados correspondentes em df_uasg
        uasg_data = self.df_uasg[self.df_uasg['uasg'].astype(str) == uasg_valor_padrao]
        if not uasg_data.empty:
            orgao_responsavel = uasg_data['orgao_responsavel'].iloc[0]
            sigla_om = uasg_data['sigla_om'].iloc[0]
        else:
            orgao_responsavel = "NaN"
            sigla_om = "NaN"
        
        valor_etapa_padrao = "Planejamento"
        mod_padrao = "PE"

        # Criar os valores predefinidos para exibição no QTreeView
        valores_treeview = [
            mod_padrao,
            novo_num_pregao,
            ano_atual,
            f"62055.XXXXXX/{ano_atual}-XX",
            "NaN",  # Objeto
            "787000",
            "NaN",  
        ]

        # Criar uma nova linha no QTreeView com esses valores
        items = [QStandardItem(str(valor)) for valor in valores_treeview]
        self.model.appendRow(items)

        # Criar um dicionário com todos os valores para o DataFrame
        novo_registro = {
            'mod': mod_padrao,
            'num_pregao': novo_num_pregao,
            'ano_pregao': ano_atual,
            'nup': f"62055.XXXXXX/{ano_atual}-XX",
            'objeto': "NaN",
            'uasg': "787000",
            'setor_responsavel': "NaN",
            'orgao_responsavel': orgao_responsavel,  # Colunas adicionais para o DataFrame
            'sigla_om': sigla_om,
            'etapa': valor_etapa_padrao,
            'pregoeiro': "-"
        }

        # Verificar se a coluna "etapa" existe no DataFrame, se não, adicioná-la
        if 'etapa' not in self.df_licitacao_completo.columns:
            self.df_licitacao_completo['etapa'] = pd.NA
            
        # Adicionar o novo registro ao DataFrame
        novo_df = pd.DataFrame([novo_registro])
        self.df_licitacao_completo = pd.concat([self.df_licitacao_completo, novo_df], ignore_index=True)

        # Salvar o DataFrame atualizado no arquivo Excel
        save_dataframe_to_excel(self.df_licitacao_completo, CONTROLE_PROCESSOS_DIR)

    def on_edit_item(self):
        # Implementar lógica de edição aqui
        print("Editar item")
    
    def on_save_data(self):
        try:
            # Preencher automaticamente valores NaN na coluna 'etapa' com 'Planejamento'
            self.df_licitacao_completo['etapa'] = self.df_licitacao_completo['etapa'].fillna('Planejamento')

            # Salvar o DataFrame no arquivo Excel
            self.df_licitacao_completo.to_excel(CONTROLE_PROCESSOS_DIR, index=False)

            QMessageBox.information(self, "Sucesso", "Dados salvos com sucesso!")
        except PermissionError:
            QMessageBox.warning(self, "Erro de Permissão", "Não foi possível salvar o arquivo. Por favor, feche o arquivo Excel e tente novamente.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao salvar o arquivo: {str(e)}")

    def on_load_data(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo", "", "Excel Files (*.xlsx *.xls);;ODF Files (*.odf)")
        if not file_name:
            return 
        try:
            loaded_df = pd.read_excel(file_name, dtype=self.dtypes)
            self.df_licitacao_completo = loaded_df
            self.model.clear()
            self.model.setHorizontalHeaderLabels([self.NOME_COLUNAS[col] for col in self.columns_treeview])

            # Preenche o QTreeView com os dados carregados
            for _, row in self.df_licitacao_completo.iterrows():
                items = [QStandardItem(str(row[col])) for col in self.columns_treeview]
                self.model.appendRow(items)

            # Chama a função para ajustar a largura das colunas
            self._adjust_column_widths()

            QMessageBox.information(self, "Sucesso", "Dados carregados com sucesso do arquivo.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {e}")

    def on_delete_item(self):
        # Obter o índice do item selecionado
        current_index = self.tree_view.currentIndex()
        if not current_index.isValid():
            QMessageBox.warning(self, "Seleção", "Por favor, selecione um item para excluir.")
            return

        # Obter o número do pregão e o ano do pregão do item selecionado
        row = current_index.row()
        num_pregao = self.model.item(row, self.columns_treeview.index('num_pregao')).text()
        ano_pregao = self.model.item(row, self.columns_treeview.index('ano_pregao')).text()

        # Remover a linha do modelo QTreeView
        self.model.removeRow(row)

        # Atualizar o DataFrame
        self.df_licitacao_completo = self.df_licitacao_completo[
            ~((self.df_licitacao_completo['num_pregao'].astype(str) == num_pregao) &
            (self.df_licitacao_completo['ano_pregao'].astype(str) == ano_pregao))
        ]

        # Salvar o DataFrame atualizado no arquivo Excel
        save_dataframe_to_excel(self.df_licitacao_completo, CONTROLE_PROCESSOS_DIR)

        QMessageBox.information(self, "Sucesso", "Item excluído com sucesso.")

    def on_view_item(self):
        # Implementar lógica de visualização aqui
        print("Visualizar item")

    def _setup_uasg_delegate(self):
        # Configuração do ComboBoxDelegate movida para este método
        uasg_items = [str(item) for item in self.df_uasg['uasg'].tolist()]
        self.uasg_delegate = ComboBoxDelegate(self.tree_view)
        self.uasg_delegate.setItems(uasg_items)
        self.tree_view.setItemDelegateForColumn(self.columns_treeview.index('uasg'), self.uasg_delegate)

        # Carrega os dados no QTreeView
        self._load_data_to_treeview()

    def _load_data_to_treeview(self):
        # Atualiza o modelo com dados atuais do DataFrame
        self.model.clear()  # Limpa o modelo atual
        self.model.setHorizontalHeaderLabels([self.NOME_COLUNAS[col] for col in self.columns_treeview])

        # Preenche o QTreeView com os dados do DataFrame
        for _, row in self.df_licitacao_completo.iterrows():
            items = [QStandardItem(str(row[col])) for col in self.columns_treeview]
            self.model.appendRow(items)

        # Ajusta as larguras das colunas após carregar os dados
        self._adjust_column_widths()

    def _on_item_changed(self, top_left_index, bottom_right_index, roles):
        if Qt.ItemDataRole.EditRole in roles:
            # Salvar a posição atual do scrollbar
            scrollbar = self.tree_view.verticalScrollBar()
            old_scroll_pos = scrollbar.value()

            row = top_left_index.row()
            column = top_left_index.column()
            column_name = self.columns_treeview[column]

            # Obter o valor atualizado
            new_value = str(self.model.itemFromIndex(top_left_index).text())

            # Atualizar o DataFrame se a coluna UASG foi alterada
            if column_name == 'uasg':
                uasg_data = self.df_uasg[self.df_uasg['uasg'].astype(str) == new_value]

                # Se encontrou a UASG correspondente, atualizar as colunas no DataFrame
                if not uasg_data.empty:
                    orgao_responsavel = uasg_data['orgao_responsavel'].iloc[0]
                    sigla_om = uasg_data['sigla_om'].iloc[0]

                    # Atualizar o DataFrame df_licitacao_completo
                    self.df_licitacao_completo.loc[
                        (self.df_licitacao_completo['num_pregao'].astype(str) == self.model.item(row, self.columns_treeview.index('num_pregao')).text()) &
                        (self.df_licitacao_completo['ano_pregao'].astype(str) == self.model.item(row, self.columns_treeview.index('ano_pregao')).text()),
                        ['orgao_responsavel', 'sigla_om']
                    ] = [orgao_responsavel, sigla_om]

            # Obter os valores de identificação únicos (num_pregao e ano_pregao)
            num_pregao = self.model.item(row, self.columns_treeview.index('num_pregao')).text()
            ano_pregao = self.model.item(row, self.columns_treeview.index('ano_pregao')).text()

            # Atualizar o DataFrame para todas as outras colunas
            self.df_licitacao_completo.loc[
                (self.df_licitacao_completo['num_pregao'].astype(str) == num_pregao) &
                (self.df_licitacao_completo['ano_pregao'].astype(str) == ano_pregao),
                column_name
            ] = new_value

            # Salvar o DataFrame atualizado no arquivo Excel
            save_dataframe_to_excel(self.df_licitacao_completo, CONTROLE_PROCESSOS_DIR)

            self._load_data_to_treeview()

            # Restaurar a posição do scrollbar
            scrollbar.setValue(old_scroll_pos)

            # Garantir que a linha editada esteja visível
            self.tree_view.scrollTo(self.model.index(row, 0), QAbstractItemView.ScrollHint.PositionAtCenter)

    def _load_data(self):
        try:
            self.df_licitacao_completo = pd.read_excel(CONTROLE_PROCESSOS_DIR, dtype=self.dtypes)

            # Preencher automaticamente valores NaN na coluna 'etapa' com 'Planejamento'
            self.df_licitacao_completo['etapa'] = self.df_licitacao_completo['etapa'].fillna('Planejamento')

            for _, row in self.df_licitacao_completo.iterrows():
                items = [QStandardItem(str(row[col])) for col in self.NOME_COLUNAS]
                self.model.appendRow(items)
        except Exception as e:
            print(f"Ocorreu um erro ao carregar os dados: {e}")
        self.df_licitacao_exibicao = self.df_licitacao_completo[self.columns_treeview]
        self._populate_treeview()

    def _populate_treeview(self):
        """Populate the treeview with the loaded data."""
        self.model.removeRows(0, self.model.rowCount())
        for index, row in self.df_licitacao_exibicao.iterrows():
            items = [QStandardItem(str(row[col])) for col in self.columns_treeview]
            self.model.appendRow(items)

    def _on_item_click(self, index):
        # Obtenha os valores do item selecionado
        mod = self.model.item(index.row(), self.columns_treeview.index('mod')).text()
        num_pregao = self.model.item(index.row(), self.columns_treeview.index('num_pregao')).text()
        ano_pregao = self.model.item(index.row(), self.columns_treeview.index('ano_pregao')).text()

        print(f"Emitindo sinal para {mod} {num_pregao}/{ano_pregao}")  # Adicione isto para depuração
        self.itemSelected.emit(mod, num_pregao, ano_pregao)

        # Chama o método para processar e salvar o item selecionado
        selected_values = self._get_selected_item_values()
        if selected_values:
            self._process_selected_item(selected_values)

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

        mod, num_pregao, ano_pregao = selected_values[:3]

        # Filtra o DataFrame completo para encontrar a linha com o num_pregao e ano_pregao correspondentes
        registro_completo = self.df_licitacao_completo[
            (self.df_licitacao_completo['mod'].astype(str).str.strip() == mod) &            
            (self.df_licitacao_completo['num_pregao'].astype(str).str.strip() == num_pregao) &
            (self.df_licitacao_completo['ano_pregao'].astype(str).str.strip() == ano_pregao)
        ]

        if registro_completo.empty:
            # Se nenhum registro for encontrado, retorne False
            return False

        global df_registro_selecionado  # Declare o uso da variável global
        self.itemSelected.emit(mod, num_pregao, ano_pregao)

        df_registro_selecionado = pd.DataFrame(registro_completo)
        df_registro_selecionado.to_csv(ITEM_SELECIONADO_PATH, index=False, encoding='utf-8-sig')

        # Configurações opcionais para limitar o número de linhas e colunas impressas, se necessário
        pd.set_option('display.max_columns', 10)  # Ajuste conforme necessário
        pd.set_option('display.max_rows', 10)     # Ajuste conforme necessário

        print(f"Registro salvo em {ITEM_SELECIONADO_PATH}")
        print("Valores de df_registro_selecionado:")
        print(df_registro_selecionado.to_string())

        self.app.pregao_selecionado()

        return True

    def run(self):
        """Run the application."""
        self.show()
        self._adjust_column_widths()  

    def on_control_process(self):
        # Carregar os dados dos processos antes de criar a dialog
        df_processos = carregar_dados_processos(CONTROLE_PROCESSOS_DIR)
        if not df_processos.empty:
            carregar_ou_criar_arquivo_json(df_processos, PROCESSOS_JSON_PATH)
        
            self.dialog = ProcessFlowDialog(etapas, df_processos, self)
            self.dialog.show()  # Mostra o diálogo
        else:
            self.dialog.raise_()  # Traz o diálogo para o primeiro plano se já estiver aberto
            self.dialog.activateWindow()

class ComboBoxDelegate(QItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []

    def setItems(self, items):
        self.items = [str(item) for item in items]  # Certifique-se de que todos os itens são strings

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.items)  # Adiciona itens ao editor
        return editor
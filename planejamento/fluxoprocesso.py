
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import pathlib
import json
import sqlite3
from datetime import datetime
import re
from functools import partial

class FluxoProcessoDialog(QDialog):
    dialogClosed = pyqtSignal()

    def __init__(self, etapas, df_processos, database_manager, database_path, parent=None):
        super().__init__(parent)
        self.etapas = etapas
        self.df_processos = df_processos
        self.database_manager = database_manager
        self.existing_items = {}  # Dicionário para rastrear itens adicionados por QListWidget
        self.database_path = database_path 
        self.setWindowTitle("Painel de Fluxo dos Processos")
        self.setStyleSheet("QDialog { background-color: #050f41; }")
        self._setup_ui()
        # self.showMaximized()
        self.showFullScreen()
    def closeEvent(self, event):
        # Emitir sinal quando o diálogo for fechado
        self.dialogClosed.emit()
        super().closeEvent(event)
        
    def _populate_list_widget(self, list_widget):
        print(f"Preenchendo {list_widget.objectName()}...")
        with self.database_manager as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cpz.chave_processo, cp.objeto FROM controle_prazos cpz
                INNER JOIN (SELECT chave_processo, MAX(sequencial) AS max_sequencial FROM controle_prazos GROUP BY chave_processo) max_cpz
                ON cpz.chave_processo = max_cpz.chave_processo AND cpz.sequencial = max_cpz.max_sequencial
                INNER JOIN controle_processos cp ON cpz.chave_processo = cp.id_processo
                WHERE cpz.etapa = ? ORDER BY cpz.chave_processo''', (list_widget.objectName(),))
            
            results = cursor.fetchall()
            results.sort(key=lambda x: parse_id_processo(x[0]))

            list_widget.clear()  # Limpa todos os itens antes de repopular
            for chave_processo, objeto in results:
                # Diretamente adicionar todos os itens
                list_widget.addFormattedTextItem(chave_processo, objeto)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        header_layout = self._create_header_layout()
        layout.addLayout(header_layout)
        self._add_process_stages_to_layout(layout)

    def _create_header_layout(self):
        header_layout = QHBoxLayout()
        titleLabel = QLabel("Controle do Fluxo dos Processos")
        titleLabel.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        header_layout.addWidget(titleLabel)
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        pixmap = QPixmap(str(MARINHA_PATH))
        pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label = QLabel()  # Este é o QLabel que deve conter a imagem
        image_label.setPixmap(pixmap)
        header_layout.addWidget(image_label)  # Adiciona o QLabel correto que contém a imagem
        
        return header_layout

    def _add_process_stages_to_layout(self, layout):
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()
        metade_etapas = len(self.etapas) // 2
        for index, etapa in enumerate(self.etapas.keys()):
            group_box = self._create_group_box(etapa)
            if index < metade_etapas:
                top_layout.addWidget(group_box)
            else:
                bottom_layout.addWidget(group_box)
        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)

    def _create_group_box(self, etapa):
        group_box = QGroupBox(etapa)
        group_box.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        group_box.setStyleSheet("QGroupBox { border: 1px solid white; border-radius: 10px; } QGroupBox::title { font-weight: bold; font-size: 14px; color: white; }")
        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(1, 25, 1, 4)
        list_widget = CustomListWidget(parent=self, database_path=self.database_path)  # Passa o caminho do banco de dados aqui
        list_widget.setObjectName(etapa)
        self._populate_list_widget(list_widget)
        layout.addWidget(list_widget)
        return group_box

class CustomListWidget(QListWidget):
    etapas = {
        'Planejamento': None,
        'Setor Responsável': None,
        'IRP': None,
        'Montagem do Processo': None,
        'Nota Técnica': None,
        'AGU': None,
        'Recomendações AGU': None,
        'Pré-Publicação': None,
        'Impugnado': None,
        'Sessão Pública': None,
        'Em recurso': None,
        'Homologado': None,
        'Assinatura Contrato': None,
        'Concluído': None
    }

    def __init__(self, parent=None, database_path=None):
        super().__init__(parent)
        self.database_path = database_path
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setMinimumSize(QSize(190, 250))
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setStyleSheet("""
            QListWidget {
                border: 2px solid white;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                background-color: white;
                border: none;
            }
            QListWidget::item:selected {
                background-color: #a8d3ff;
            }
        """)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.effect_timer = QTimer(self)
        self.effect_timer.setInterval(100)  # 1 milisegundo
        self.effect_timer.setSingleShot(True)
        self.effect_timer.timeout.connect(self.clearClickEffect)

    def showContextMenu(self, position):
        contextMenu = QMenu(self)
        alterar_datas_action = contextMenu.addAction("Alterar Datas")
        gerar_relatorio_action = contextMenu.addAction("Gerar Relatório")
        action = contextMenu.exec(self.mapToGlobal(position))
        
        if action == alterar_datas_action:
            self.alterarDatas()
        elif action == gerar_relatorio_action:
            self.gerarRelatorio()

    def parseDatabaseIdFromItem(self, item):
        # Implemente esta função conforme a necessidade de extrair o ID
        text = item.text()
        try:
            database_id = int(text.split(' ')[0])  # Exemplo de extração do ID
        except ValueError:
            database_id = None
        return database_id

    def alterarDatas(self):
        if not self.database_path:
            QMessageBox.warning(self, "Erro", "Caminho do banco de dados não configurado.")
            return
        dialog = AlterarDatasDialog(self, self.database_path)
        dialog.exec()

    def gerarRelatorio(self):
        # Implementar a lógica de geração de relatórios aqui
        print("Gerar Relatório acionado")

    def addFormattedTextItem(self, id_processo, objeto):
        formattedText = f"<html><head/><body><p style='text-align: center;'><span style='font-weight:600; font-size:14pt;'>{id_processo}</span><br/><span style='font-size:10pt;'>{objeto}</span></p></body></html>"
        item = QListWidgetItem()
        item.setText(formattedText)
        item.setSizeHint(QSize(0, 45))  # Ajuste a altura conforme necessário
        label = QLabel(formattedText)
        label.setStyleSheet("background-color: white;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.addItem(item)
        self.setItemWidget(item, label)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        item = self.itemAt(event.position().toPoint())

        if event.button() == Qt.MouseButton.LeftButton:
            if item:
                self.applyClickEffect(item)
                self.startDrag(Qt.DropAction.MoveAction)

        elif event.button() == Qt.MouseButton.RightButton:
            if item:
                self.setCurrentItem(item)  # Certifica-se de que o item esteja selecionado ao clicar com o botão direito
                self.applyRightClickEffect(item)
                self.effect_timer.start()

    def applyRightClickEffect(self, item):
        widget = self.itemWidget(item)
        if widget:
            widget.setStyleSheet("background-color: #00fbff; border: 1px solid #000080;")

    def clearClickEffect(self):
        item = self.currentItem()
        if item:
            widget = self.itemWidget(item)
            if widget:
                widget.setStyleSheet("background-color: white;")

    def applyClickEffect(self, item):
        # Encontre o QLabel associado ao QListWidgetItem e mude seu estilo
        if item:
            widget = self.itemWidget(item)
            if widget:
                # Altera a cor de fundo para amarelo e adiciona uma borda azul marinho
                widget.setStyleSheet("background-color: #FFFF00; border: 1px solid #000080;")

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            currentWidget = self.itemWidget(item)
            if currentWidget:
                mimeData = QMimeData()
                itemData = {
                    "formattedText": item.text(),  # ou outra propriedade que deseje transmitir
                    "objeto": currentWidget.text(),
                    "origin": self.objectName()
                }
                mimeData.setText(json.dumps(itemData))

                drag = QDrag(self)
                pixmap = QPixmap(currentWidget.size())
                currentWidget.render(pixmap)
                drag.setMimeData(mimeData)
                drag.setPixmap(pixmap)
                drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
                drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            itemData = json.loads(event.mimeData().text())
            formattedText = itemData["formattedText"]  # O texto HTML completo
            id_processo = extrair_id_processo(formattedText)  # Extrai id_processo do HTML
            objeto = extrair_objeto(formattedText)  # Extrair objeto do HTML, implementar esta função similarmente

            origin = itemData["origin"]
            nova_etapa = self.objectName()

            if origin != nova_etapa:
                self.addFormattedTextItem(id_processo, objeto)  # Usa id_processo e objeto extraídos
                event.source().takeItem(event.source().currentRow())  # Remove o item da lista original
                etapa_manager = EtapaManager(str(CONTROLE_DADOS))
                etapa_manager.registrar_etapa(id_processo, nova_etapa, "Comentário opcional")

            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

class EtapaManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def registrar_etapa(self, chave_processo, nova_etapa, comentario=''):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            # Obter a última etapa registrada para esse processo
            cursor.execute('''
                SELECT data_final FROM controle_prazos
                WHERE chave_processo = ? AND sequencial = (
                    SELECT MAX(sequencial) FROM controle_prazos WHERE chave_processo = ?
                )
            ''', (chave_processo, chave_processo))
            result = cursor.fetchone()
            today_str = datetime.today().strftime('%Y-%m-%d')
            
            # Determina a data_inicial da nova etapa
            if result and result[0]:
                data_inicial = result[0]
            else:
                # Atualiza data_final da última etapa, se não definida
                cursor.execute('''
                    UPDATE controle_prazos
                    SET data_final = ?
                    WHERE chave_processo = ? AND sequencial = (
                        SELECT MAX(sequencial) FROM controle_prazos WHERE chave_processo = ?
                    ) AND data_final IS NULL
                ''', (today_str, chave_processo, chave_processo))
                data_inicial = today_str
            
            # Inserir a nova etapa
            cursor.execute('''
                INSERT INTO controle_prazos (chave_processo, etapa, data_inicial, data_final, dias_na_etapa, comentario, sequencial)
                VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT MAX(sequencial) FROM controle_prazos WHERE chave_processo = ?) + 1, 1))
            ''', (chave_processo, nova_etapa, data_inicial, today_str, 0, comentario, chave_processo))
            
            conn.commit()
        finally:
            conn.close()

    def atualizar_dias_na_etapa(self):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE controle_prazos
                SET dias_na_etapa = julianday('now') - julianday(data_inicial)
            ''')
            conn.commit()
        finally:
            conn.close()

def extrair_id_processo(texto_html):
    # Usa expressão regular para extrair o texto dentro do primeiro <span> após <p>
    match = re.search(r"<p[^>]*><span[^>]*>(.*?)</span>", texto_html)
    if match:
        return match.group(1)
    return None

def extrair_objeto(texto_html):
    # Extrai o texto do objeto, que aparece após a id_processo no HTML
    match = re.search(r"<br/><span[^>]*>(.*?)</span></p>", texto_html)
    if match:
        return match.group(1)
    return None

def parse_id_processo(id_processo):
    """
    Espera uma string no formato '{mod} {num_pregao}/{ano_pregao}' e retorna uma tupla (ano_pregao, num_pregao)
    para ordenação.
    """
    try:
        parts = id_processo.split(' ')[-1]  # Pega a parte '{num_pregao}/{ano_pregao}'
        num_pregao, ano_pregao = parts.split('/')
        return (int(ano_pregao), int(num_pregao))  # Retorna uma tupla para ordenação
    except (IndexError, ValueError):
        return (0, 0)  # Em caso de falha na parse, retorna uma tupla que coloca este item no início

class CustomCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setStyleSheet("""
            QCalendarWidget QAbstractItemView {
                selection-background-color: yellow;
                selection-color: black;
            }
        """)

def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()

class AlterarDatasDialog(QDialog):
    def __init__(self, listWidget, db_path):
        super().__init__()
        self.setFixedWidth(800)
        self.setMinimumHeight(400)  # Define a altura mínima do diálogo
        self.listWidget = listWidget
        self.db_path = db_path
        self.calendarios = []  # Lista para guardar referências aos widgets de calendário
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QLabel, QPushButton, QComboBox, QDateEdit {
                font-size: 16px;
            }
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid gray;
                border-radius: 5px;
                margin-top: 0.5em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        if self.layout() is not None:
            clear_layout(self.layout())  # Limpeza do layout existente
            QWidget().setLayout(self.layout())  # Desvincula o layout antigo

        layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setWidget(scroll_widget)

        processoSelecionado = self.listWidget.currentItem().text()
        self.chave_processo = self.extrair_id_processo(processoSelecionado)
        self.setWindowTitle(f"Alterar Datas do {self.chave_processo}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sequencial, etapa, data_inicial, data_final FROM controle_prazos WHERE chave_processo = ?", (self.chave_processo,))
        etapas = cursor.fetchall()

        for sequencial, etapa, data_inicial, data_final in etapas:
            groupBox = QGroupBox(f"{etapa} ({sequencial})", self)
            groupBox.setFixedSize(750, 100)
            hbox = QHBoxLayout(groupBox)
            comboBox = QComboBox()
            comboBox.addItems([
                'Planejamento', 'Setor Responsável', 'IRP', 'Montagem do Processo',
                'Nota Técnica', 'AGU', 'Recomendações AGU', 'Pré-Publicação', 'Impugnado',
                'Sessão Pública', 'Em recurso', 'Homologado', 'Assinatura Contrato', 'Concluído'
            ])

            comboBox.setCurrentText(etapa)
            comboBox.currentTextChanged.connect(lambda text, gb=groupBox: self.update_groupbox_title(text, gb))
            comboBox.currentTextChanged.connect(lambda text, seq=sequencial: self.update_current_choice(seq, text))

            # Vertical layouts for date labels and edits
            vLayoutInicio = QVBoxLayout()
            labelInicio = QLabel('Data-Início:')
            dateEditInicio = self.create_date_edit(data_inicial)
            dateEditInicio.dateChanged.connect(lambda date, seq=sequencial: self.update_previous_end_date(date, seq))

            vLayoutInicio.addWidget(labelInicio)
            vLayoutInicio.addWidget(dateEditInicio)

            vLayoutFim = QVBoxLayout()
            labelFim = QLabel('Data-Fim:')
            dateEditFim = self.create_date_edit(data_final)
            dateEditFim.dateChanged.connect(lambda date, seq=sequencial: self.update_next_start_date(date, seq))

            vLayoutFim.addWidget(labelFim)
            vLayoutFim.addWidget(dateEditFim)

            # Days counter setup
            vLayoutDias = QVBoxLayout()
            labelContadorDias = QLabel('Contagem de Dias:')
            labelDias = QLabel('0')  # Days count label
            labelDias.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Correção aqui para centralizar o texto horizontalmente
            vLayoutDias.addWidget(labelContadorDias)
            vLayoutDias.addWidget(labelDias)
            vLayoutDias.addStretch(1)  # Mantém os widgets alinhados ao topo

            def update_days_count(label, date1, date2):
                delta = (date2.date().toPyDate() - date1.date().toPyDate()).days
                label.setText(str(delta))

            # Connect signals
            dateEditInicio.dateChanged.connect(lambda _, lbl=labelDias, de1=dateEditInicio, de2=dateEditFim: update_days_count(lbl, de1, de2))
            dateEditFim.dateChanged.connect(lambda _, lbl=labelDias, de1=dateEditInicio, de2=dateEditFim: update_days_count(lbl, de1, de2))
            update_days_count(labelDias, dateEditInicio, dateEditFim)  # Initial update


            btnDelete = QPushButton("Excluir", self)
            btnDelete.clicked.connect(self.make_delete_handler(sequencial))  # Utiliza a função make_delete_handler

            hbox.addWidget(comboBox)
            hbox.addLayout(vLayoutInicio)
            hbox.addLayout(vLayoutFim)
            hbox.addLayout(vLayoutDias)
            hbox.addWidget(btnDelete)
            scroll_layout.addWidget(groupBox)

            # Atualiza self.calendarios com os widgets corretos
            self.calendarios.append((sequencial, comboBox, dateEditInicio, dateEditFim, etapa))  # Note que 'etapa' é a escolha inicial

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        btnSave = QPushButton("Salvar Alterações", self)
        btnSave.clicked.connect(self.save_changes)
        layout.addWidget(btnSave)


        conn.close()
        update_days_count(labelDias, dateEditInicio, dateEditFim)
        
    def update_next_start_date(self, date, sequencial):
        index = next((i for i, v in enumerate(self.calendarios) if v[0] == sequencial), None)
        try:
            if index is not None and index + 1 < len(self.calendarios):
                next_date_edit = self.calendarios[index + 1][2]
                next_date_edit.setDate(date)
        except RuntimeError as e:
            print(f"Erro ao tentar acessar um QDateEdit que foi deletado: {e}")

    def update_previous_end_date(self, date, sequencial):
        index = next((i for i, v in enumerate(self.calendarios) if v[0] == sequencial), None)
        if index is not None and index > 0:
            self.calendarios[index - 1][3].setDate(date)
            
    def update_current_choice(self, sequencial, text):
        for index, entry in enumerate(self.calendarios):
            if entry[0] == sequencial:
                self.calendarios[index] = (entry[0], entry[1], entry[2], entry[3], text)
                
    def update_groupbox_title(self, text, groupBox):
        groupBox.setTitle(f"Etapa Alterada: {text}")
        
    def make_delete_handler(self, sequencial):
        def delete_handler():
            # Cria uma mensagem de confirmação antes de proceder com a exclusão
            response = QMessageBox.question(self, 'Confirmar Exclusão', 
                                            f'Tem certeza de que deseja excluir o sequencial {sequencial}?',
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                            QMessageBox.StandardButton.No)

            if response == QMessageBox.StandardButton.Yes:
                print(f"Deletando etapa com sequencial: {sequencial}")
                self.delete_etapa(sequencial)
            else:
                print("Exclusão cancelada.")

        return delete_handler

    def delete_etapa(self, sequencial):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM controle_prazos WHERE sequencial = ? AND chave_processo = ?", (sequencial, self.chave_processo))
            if cursor.rowcount > 0:
                self.calendarios = [entry for entry in self.calendarios if entry[0] != sequencial]
                print("Exclusão realizada com sucesso.")
            else:
                print("Nenhuma linha foi alterada.")
            conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao excluir etapa: {e}")
            conn.rollback()
        finally:
            conn.close()
            self.setup_ui()  # Recria a UI após a atualização da lista

    def create_date_edit(self, date_str):
        dateEdit = QDateEdit(self)
        dateEdit.setCalendarPopup(True)
        dateEdit.setDisplayFormat("yyyy-MM-dd")
        if date_str:
            dateEdit.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
        return dateEdit

    def reorder_sequencial(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT sequencial FROM controle_prazos WHERE chave_processo = ? ORDER BY sequencial", (self.chave_processo,))
        sequenciais = [seq[0] for seq in cursor.fetchall()]
        for i, sequencial in enumerate(sequenciais, start=1):
            if sequencial != i:
                cursor.execute("UPDATE controle_prazos SET sequencial = ? WHERE sequencial = ? AND chave_processo = ?", (i, sequencial, self.chave_processo))
        conn.commit()

    def save_changes(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            for sequencial, comboBox, dateEditInicio, dateEditFim, etapa_atual in self.calendarios:
                data_inicial = dateEditInicio.date().toString("yyyy-MM-dd")
                data_final = dateEditFim.date().toString("yyyy-MM-dd")
                cursor.execute(
                    "UPDATE controle_prazos SET etapa = ?, data_inicial = ?, data_final = ? WHERE sequencial = ? AND chave_processo = ?",
                    (etapa_atual, data_inicial, data_final, sequencial, self.chave_processo)
                )
            conn.commit()
        except sqlite3.Error as e:
            print("Erro ao salvar alterações:", e)
            conn.rollback()
        finally:
            conn.close()
        self.accept()

    def extrair_id_processo(self, texto_html):
        import re
        match = re.search(r"<p[^>]*><span[^>]*>(.*?)</span>", texto_html)
        if match:
            return match.group(1)
        return None


from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
from pathlib import Path
import json
import sqlite3
from datetime import datetime
import re
from functools import partial
from utils.treeview_utils import load_images, create_button_2
from utils.treeview_utils import load_images, create_button, save_dataframe_to_excel
import pandas as pd
import os
import sys
import subprocess
import win32com.client
import tempfile
import fitz
from planejamento.utilidades_planejamento import DatabaseManager
import time
from win32com.client import Dispatch, DispatchEx
import traceback

class FluxoProcessoDialog(QDialog):
    updateRequired = pyqtSignal()  # Sinal para notificar a ApplicationUI

    def __init__(self, icons_dir, etapas, df_processos, database_manager, database_path, parent=None):
        super().__init__(parent)
        self.etapas = etapas
        self.df_processos = df_processos
        self.database_manager = database_manager
        self.existing_items = {}  # Dicionário para rastrear itens adicionados por QListWidget
        self.database_path = database_path
        self.icons_dir = Path(icons_dir)
        self.image_cache = load_images(self.icons_dir, ["excel.png", "pdf64.png"])
        self.setWindowTitle("Painel de Fluxo dos Processos")
        self.setStyleSheet("QDialog { background-color: #050f41; }")
        self._setup_ui()
        self.showMaximized()
        # self.showFullScreen()

    def closeEvent(self, event):
        # Emitir sinal quando o diálogo for fechado
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
        self.add_action_buttons(header_layout)
        
        pixmap = QPixmap(str(MARINHA_PATH))
        pixmap = pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        header_layout.addWidget(image_label)
        
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

    def add_action_buttons(self, layout):
        # Caminhos para os ícones
        icon_excel = QIcon(str(ICONS_DIR / "excel.png"))
        icon_pdf = QIcon(str(ICONS_DIR / "pdf64.png"))

        # Botões
        button_gerar_excel = create_button_2("Gerar Relatório Excel", icon_excel, self.generate_excel, "Gerar arquivo Excel", self)
        layout.addWidget(button_gerar_excel)  # Adiciona diretamente ao layout do cabeçalho

        button_gerar_pdf = create_button_2("Gerar Relatório PDF", icon_pdf, self.generate_pdf, "Gerar arquivo PDF", self)
        layout.addWidget(button_gerar_pdf)  # Adiciona diretamente ao layout do cabeçalho
            
    def generate_excel(self):
        # Cria uma instância de ReportDialog com o DataFrame necessário
        report_dialog = ReportDialog(self.df_processos, str(self.icons_dir), self)
        # Chama a função de exportação para Excel
        report_dialog.on_export_excel()

    def generate_pdf(self):
        # Cria uma instância de ReportDialog com o DataFrame necessário
        report_dialog = ReportDialog(self.df_processos, str(self.icons_dir), self)
        # Chama a função de exportação para PDF
        report_dialog.on_export_pdf()

    def _create_group_box(self, etapa):
        group_box = QGroupBox(etapa)
        group_box.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        group_box.setStyleSheet("QGroupBox { border: 1px solid white; border-radius: 10px; } QGroupBox::title { font-weight: bold; font-size: 14px; color: white; }")
        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(1, 25, 1, 4)
        list_widget = CustomListWidget(parent=self, database_path=self.database_path)
        list_widget.setObjectName(etapa)
        self._populate_list_widget(list_widget)
        list_widget.updateRequired.connect(self.updateRequired.emit)  # Conecta o sinal ao método que emite o sinal do diálogo
        layout.addWidget(list_widget)
        return group_box
    
class CustomListWidget(QListWidget):
    updateRequired = pyqtSignal()
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
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.database_path = self.load_database_path()
        self.database_manager = DatabaseManager(self.database_path)
        self.config_manager.config_updated.connect(self.on_config_updated)

    def load_database_path(self):
        return Path(self.config_manager.get_config("CONTROLE_DADOS", str(CONTROLE_DADOS)))

    def on_config_updated(self, key, path):
        if key == "CONTROLE_DADOS":
            self.database_path = path
            print(f"Database path atualizado para: {self.database_path}")

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
                self.updateRequired.emit()
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

class ReportButton(QPushButton):
    openReportDialog = pyqtSignal()

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.clicked.connect(self.emitOpenReportDialogSignal)

    def emitOpenReportDialogSignal(self):
        self.openReportDialog.emit()

def status_sort_key(status):
    order = [
        'Concluído', 'Assinatura Contrato', 'Homologado', 'Em recurso',
        'Sessão Pública', 'Impugnado', 'Pré-Publicação', 'Recomendações AGU',
        'AGU', 'Nota Técnica', 'Montagem do Processo', 'IRP', 'Setor Responsável', 'Planejamento'
    ]
    try:
        return order.index(status)
    except ValueError:
        return len(order)
    
class ReportDialog(QDialog):
    def __init__(self, dataframe, icons_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relatório")
        self.setMinimumSize(980, 500)  # Define o tamanho mínimo do diálogo
        self.setLayout(QVBoxLayout())
        self.table_view = QTableView()
        self.layout().addWidget(self.table_view)
        self.model = QStandardItemModel()
        self.table_view.setModel(self.model)
        self.setObjectName("ReportDialog")
        self.setStyleSheet("""
            #ReportDialog {
                background-color: black;
                color: white;
                font-size: 12pt;
                }
                QTableView {
                    border: 1px solid #d3d3d3;
                    gridline-color: #d3d3d3;
                    background-color: #f0f0f0;
                    font-size: 12pt;
                }
                QTableView::item:selected {
                    background-color: #a8a8a8;
                    color: white;
                    font-size: 12pt;
                }
                QTableView::item:hover {
                    background-color: #f5f5f5;
                    color: black;
                }
                QHeaderView::section {
                    background-color: #e0e0e0;
                    padding: 4px;
                    border: 1px solid #d3d3d3;
                    font-size: 12pt;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    border: none;
                    background: none;
                }
            """)
        self.dataframe = dataframe  # Armazena o DataFrame passado como argumento
        self.icons_dir = Path(icons_dir)
        self.image_cache = {}
        self.image_cache = load_images(self.icons_dir, [
            "pdf64.png", "excel.png"
        ])
        # Configura os cabeçalhos das colunas
        self.model.setHorizontalHeaderLabels(["Número", "Objeto", "Valor Estimado", "OM", "Status Anterior", 
                                              "Dias", "Status Atual", "Dias", "Pregoeiro", "data_limite_manifestacao_irp", "data_limite_confirmacao_irp",
                                              "num_irp", "data_sessao", "Comentário"])
        # Definir o tamanho da fonte do cabeçalho da tabela
        header = self.table_view.horizontalHeader()
        font = header.font()
        font.setPointSize(12)
        header.setFont(font)
    
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # Ajustar todas as colunas para preencher o espaço
        self.table_view.resizeColumnsToContents()  # Ajusta as colunas ao conteúdo
        self.table_view.verticalHeader().setVisible(False)
        self.load_data()
        self._create_buttons()  # Cria os botões

        QTimer.singleShot(1, self.adjustColumnWidth) 

        self.table_view.hideColumn(9)
        self.table_view.hideColumn(10)
        self.table_view.hideColumn(11)
        self.table_view.hideColumn(12)
        self.table_view.hideColumn(13)

    def adjustColumnWidth(self):
        header = self.table_view.horizontalHeader()
        # Configurar outras colunas para ter tamanhos fixos
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)  
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(12, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(13, QHeaderView.ResizeMode.Fixed)
        # Ajusta o tamanho de colunas fixas
        header.resizeSection(0, 110)
        header.resizeSection(2, 110)
        header.resizeSection(3, 110)
        header.resizeSection(5, 60)
        header.resizeSection(6, 60)


    def showEvent(self, event):
        super().showEvent(event)

    def load_data(self):
        try:
            # Conectar ao banco de dados SQLite
            conn = sqlite3.connect(CONTROLE_DADOS)
            cursor = conn.cursor()

            # Consulta SQL para obter os dados da tabela controle_processos
            cursor.execute("SELECT id_processo, objeto, valor_total, sigla_om, pregoeiro, data_limite_manifestacao_irp, data_limite_confirmacao_irp, num_irp, data_sessao, comentarios FROM controle_processos")
            process_rows = cursor.fetchall()

            for row in process_rows:
                chave_processo = row[0]  # id_processo
                objeto = row[1]
                valor_total = row[2]
                sigla_om = row[3]
                pregoeiro = row[4]
                data_limite_manifestacao_irp = row[5]
                data_limite_confirmacao_irp = row[6]
                num_irp = row[7]
                data_sessao = row[8]
                comentarios = row[9]
                
                # Buscar os dados de status e dias na tabela controle_prazos
                cursor.execute("""
                SELECT etapa, dias_na_etapa FROM controle_prazos 
                WHERE chave_processo = ? 
                ORDER BY sequencial DESC
                """, (chave_processo,))
                prazos_rows = cursor.fetchall()

                if len(prazos_rows) >= 2:
                    # Pegar os dados do status atual e anterior
                    status_atual, dias_status_atual = prazos_rows[0]
                    status_anterior, dias_status_anterior = prazos_rows[1]
                elif len(prazos_rows) == 1:
                    # Somente status atual está disponível
                    status_atual, dias_status_atual = prazos_rows[0]
                    status_anterior, dias_status_anterior = "", ""
                else:
                    # Nenhum status disponível
                    status_atual, dias_status_atual = "", ""
                    status_anterior, dias_status_anterior = "", ""
                
                if valor_total == "R$ 0,00":
                    valor_total = ""

                if status_anterior == "":
                    status_anterior = "-"

                # Se o status atual for "Concluído", substituir dias_status_atual por "-"
                if status_atual == "Concluído":
                    dias_status_atual = "-"
                # Se o status atual for "Planejamento", substituir dias_status_atual e dias_status_anterior por "-"
                if status_atual == "Planejamento":
                    dias_status_atual = "-"
                    dias_status_anterior = "-"  # Aplicando também para o status anterior

                if status_anterior == "Planejamento":
                    dias_status_anterior = "-"  # Aplicando também para o status anterior
                # Adicionar os dados ao modelo
                self.model.appendRow([
                    QStandardItem(chave_processo),
                    QStandardItem(objeto if objeto is not None else ""),
                    QStandardItem(str(valor_total) if valor_total is not None else ""),
                    QStandardItem(sigla_om if sigla_om is not None else ""),
                    QStandardItem(status_anterior),
                    QStandardItem(str(dias_status_anterior)),
                    QStandardItem(status_atual),
                    QStandardItem(str(dias_status_atual)),
                    QStandardItem(pregoeiro if pregoeiro is not None else ""),
                    QStandardItem(data_limite_manifestacao_irp if data_limite_manifestacao_irp is not None else ""),
                    QStandardItem(data_limite_confirmacao_irp if data_limite_confirmacao_irp is not None else ""),
                    QStandardItem(num_irp if num_irp is not None else ""),
                    QStandardItem(data_sessao if data_sessao is not None else ""),
                    QStandardItem(comentarios if comentarios is not None else "")
                ])

            # Fechar a conexão com o banco de dados
            conn.close()
        except sqlite3.Error as e:
            print(f"Erro ao acessar o banco de dados: {e}")

    def _create_buttons(self):
        # Cria um layout horizontal para os botões
        buttons_layout = QHBoxLayout()
        self.layout().addLayout(buttons_layout)  # Adiciona o layout de botões ao layout principal do diálogo

        # Especificações dos botões
        button_specs = [
            ("Tabela Excel", self.image_cache['excel'], self.on_export_excel, "Exportar dados para Excel"),
            ("Relatório PDF", self.image_cache['pdf64'], self.on_export_pdf, "Exportar dados para PDF")
        ]

        # Iterar sobre as especificações dos botões e criar cada botão
        for text, icon, callback, tooltip in button_specs:
            btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self)
            buttons_layout.addWidget(btn)  # Adiciona o botão ao layout de botões

    def create_excel(self, filename="relatorio.xlsx"):
        """
        Cria um arquivo Excel a partir dos dados do modelo, incluindo cabeçalhos personalizados e formatação.
        """
        # Cria um DataFrame dos dados
        data = []
        columns_to_omit = {9, 10, 11, 12, 13}
        for row in range(self.model.rowCount()):
            row_data = []
            for column in range(self.model.columnCount()):
                if column not in columns_to_omit:
                    item = self.model.item(row, column)
                    row_data.append(item.text() if item else "")
            data.append(row_data)

        # Definir colunas omitindo as colunas 9, 10, 11, 12 e 13
        columns = [self.model.horizontalHeaderItem(i).text() for i in range(self.model.columnCount()) if i not in columns_to_omit]
        df = pd.DataFrame(data, columns=columns)

        # Adiciona colunas temporárias com os índices de ordenação baseados em 'Status Atual' e 'Status Anterior'
        df['Status Index'] = df['Status Atual'].apply(status_sort_key)
        df['Previous Status Index'] = df['Status Anterior'].apply(status_sort_key)

        # Ordena o DataFrame pelas colunas de índice e depois remove essas colunas
        df.sort_values(['Status Index', 'Previous Status Index'], inplace=True)
        df.drop(columns=['Status Index', 'Previous Status Index'], inplace=True)

        # Continua a criação e formatação do Excel
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', startrow=4, index=False)

        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        # Configurações do formato de página e margens
        worksheet.set_landscape()  # Define o layout de página para paisagem
        worksheet.set_margins(left=0.05, right=0.05, top=0.3, bottom=0.39)  # Margens em polegadas (1 cm ≈ 0.39 inches, 2 cm ≈ 0.79 inches)
        worksheet.set_header('', options={'margin': 0})  # Cabeçalho com margem 0
        worksheet.set_footer('', options={'margin': 0})  # Rodapé com margem 0
                
        # Formatos para as células
        cabecalho_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font_size': 14
        })
        cabecalho2_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'italic': True, 
            'font_size': 12
        })

        date_format = workbook.add_format({
            'italic': True, 
            'font_size': 10,
            'align': 'right'
        })

        # Formatos com cores intercaladas
        light_gray_format = workbook.add_format({'bg_color': '#F2F2F2', 'align': 'center', 'valign': 'vcenter'})
        white_format = workbook.add_format({'bg_color': '#FFFFFF', 'align': 'center', 'valign': 'vcenter'})
        comment_format = workbook.add_format({'align': 'left', 'valign': 'top', 'text_wrap': True})
 
        # Configurações do cabeçalho e data
        worksheet.merge_range('A1:I1', 'Centro de Intendência da Marinha em Brasília', cabecalho_format)
        worksheet.merge_range('A2:I2', '"Prontidão e Efetividade no Planalto Central"', cabecalho2_format)
        worksheet.merge_range('A3:I3', 'Controle do Plano de Contratações Anual (PCA) 2024', cabecalho_format)
        data_atual = datetime.now().strftime("%d/%m/%Y")
        worksheet.merge_range('A4:I4', f"Atualizado em: {data_atual}", date_format)
        
        # Configurações de altura das linhas para o cabeçalho
        worksheet.set_row(0, 20)
        worksheet.set_row(2, 30)
        worksheet.set_row(3, 20)  # Ajuste de altura para a linha da data
            # Ajustar a largura das colunas, considerando a nova coluna 'Nº'
        col_widths = [11, 29, 15, 9, 20, 4, 20, 4, 15]
        for i, width in enumerate(col_widths):
            worksheet.set_column(i, i, width)
        # Aplicar formatação de conteúdo centralizado a partir da linha 5
        for row_num in range(5, 5 + len(df)):
            for col_num in range(9):  # Colunas A a I
                cell_format = light_gray_format if (row_num % 2 == 0) else white_format
                worksheet.write(row_num, col_num, df.iloc[row_num - 5, col_num], cell_format)

        comentario_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font_size': 14,
            'top': 2  # Borda superior espessa
        })
        
        # Adicionar "Informações Relevantes"
        last_row = 5 + len(df)
        last_row += 1
        worksheet.merge_range(f'A{last_row+1}:I{last_row+1}', 'Informações Relevantes', comentario_format)

        for row in range(self.model.rowCount()):
            chave_processo = self.model.item(row, 0).text()
            objeto = self.model.item(row, 1).text()
            data_limite_manifestacao_irp = self.model.item(row, 9).text()
            data_limite_confirmacao_irp = self.model.item(row, 10).text()
            num_irp = self.model.item(row, 11).text()
            data_sessao = self.model.item(row, 12).text()

            if data_limite_manifestacao_irp:
                try:
                    data_limite_manifestacao_irp = datetime.strptime(data_limite_manifestacao_irp, "%Y-%m-%d").strftime("%d/%m/%Y")
                except ValueError:
                    data_limite_manifestacao_irp = None  # Ignora datas inválidas

            # Lógica para data_limite_confirmacao_irp
            if data_limite_confirmacao_irp:
                try:
                    data_limite_confirmacao_irp_dt = datetime.strptime(data_limite_confirmacao_irp, "%Y-%m-%d")
                    data_limite_confirmacao_irp = data_limite_confirmacao_irp_dt.strftime("%d/%m/%Y")
                    if data_limite_confirmacao_irp_dt > datetime.now():
                        last_row += 1
                        worksheet.write(last_row, 0, chave_processo, comment_format)
                        worksheet.merge_range(last_row, 1, last_row, 8, 
                                            f"IRP nº {num_irp} ({objeto}) | Data limite para manifestação: {data_limite_manifestacao_irp} | Data final para confirmação: {data_limite_confirmacao_irp}", 
                                            comment_format)
                except ValueError:
                    pass  # Ignora datas inválidas

        last_row += 1

        # Lógica para data_sessao
        for row in range(self.model.rowCount()):
            chave_processo = self.model.item(row, 0).text()
            data_sessao = self.model.item(row, 12).text()

            if data_sessao:
                try:
                    data_sessao_dt = datetime.strptime(data_sessao, "%Y-%m-%d")
                    data_sessao = data_sessao_dt.strftime("%d/%m/%Y")
                    if data_sessao_dt > datetime.now():
                        last_row += 1
                        worksheet.write(last_row, 0, chave_processo, comment_format)
                        worksheet.merge_range(last_row, 1, last_row, 8, 
                                            f"Data da abertura da sessão pública: {data_sessao}", 
                                            comment_format)
                except ValueError:
                    pass  # Ignora datas inválidas

        # Pular uma linha após "Informações Relevantes"
        last_row += 1

        # Adicionar "Comentários"
        last_row += 1
        worksheet.merge_range(f'A{last_row+1}:I{last_row+1}', 'Comentários Adicionais', comentario_format)

        # Iterar sobre os dados e adicionar comentários
        for row in range(self.model.rowCount()):
            chave_processo = self.model.item(row, 0).text()
            comentarios = self.model.item(row, 13).text().replace('|||', '\n')  # Substituir "|||" por "\n" para quebra de linha
            if comentarios:
                last_row += 1
                worksheet.write(last_row, 0, chave_processo, comment_format)
                worksheet.merge_range(last_row, 1, last_row, 8, comentarios, comment_format)
                num_lines = comentarios.count('\n') + 1  # Número de linhas de comentários
                worksheet.set_row(last_row, 15 * num_lines, comment_format)  # Ajustar altura da linha para o número de linhas de comentários

        # Fecha o arquivo Excel
        writer.close()
        return filename  # Retorna o nome do arquivo criado

    def open_excel_file(self, filename):
        """
        Abre um arquivo Excel específico, usando um comando adequado dependendo do sistema operacional.
        """
        if os.name == 'nt':  # Para Windows
            os.startfile(filename)
        else:  # Para macOS e Linux
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, filename])

    def on_export_excel(self):
        filename = self.create_excel()  # Cria o arquivo Excel
        self.open_excel_file(filename)  # Abre o arquivo Excel criado

    def adicionar_imagem_ao_pdf(self, pdf_path, left_image_path, right_image_path, watermark_image_path, image_size_cm=(2, 2)):
        print("Iniciando a adição de imagens ao PDF...")
        pdf_path = str(pdf_path)
        left_image_path = str(left_image_path)
        right_image_path = str(right_image_path)
        watermark_image_path = str(watermark_image_path)  # Caminho para a imagem da marca d'água

        doc = fitz.open(pdf_path)
        numero_total_paginas = len(doc)  # Obter o número total de páginas
        print(f"PDF aberto. Total de páginas: {numero_total_paginas}")  

        for pagina_number, pagina in enumerate(doc):  # Iterar por todas as páginas
            page_width = pagina.rect.width
            page_height = pagina.rect.height
            texto_contador_paginas = f"- {pagina_number + 1} de {numero_total_paginas} -"  # Formatar o texto do contador

            # Configurar o texto para o contador de páginas
            text_rect = fitz.Rect(0, page_height - 40, page_width, page_height)  # Definir a posição do texto na parte inferior da página
            pagina.insert_textbox(text_rect, texto_contador_paginas, fontsize=11, align=1)  # Inserir o texto do contador
            
            # Inserir marca d'água centralizada em todas as páginas
            wm = fitz.open(watermark_image_path)  # Abrir imagem da marca d'água
            pix = wm[0].get_pixmap()  # Obter pixmap do primeiro documento da imagem
            scale = min(page_width / pix.width, page_height / pix.height) / 1.5  # Escala para reduzir o tamanho da marca d'água
            scaled_width = pix.width * scale
            scaled_height = pix.height * scale
            center_x = (page_width - scaled_width) / 2
            center_y = (page_height - scaled_height) / 2
            watermark_rect = fitz.Rect(center_x, center_y, center_x + scaled_width, center_y + scaled_height)
            
            pagina.insert_image(watermark_rect, filename=watermark_image_path)
            
            # Inserir imagens esquerda e direita apenas na primeira página
            if pagina_number == 0:
                # Calcular o tamanho da imagem em pontos
                image_size_pt = (image_size_cm[0] * 70 / 2.54, image_size_cm[1] * 70 / 2.54)
                
                # Calcular o deslocamento das imagens a partir das bordas em pontos
                offset_left_x_pt = 2 * 72 / 2.54
                offset_right_x_pt = page_width - (2.9 * 72 / 2.54) - image_size_pt[0]
                offset_y_pt = 0.9 * 72 / 2.54  # 1 cm do topo
                
                # Definir os retângulos onde as imagens serão inseridas
                left_rect = fitz.Rect(offset_left_x_pt, offset_y_pt, offset_left_x_pt + image_size_pt[0], offset_y_pt + image_size_pt[1])
                right_rect = fitz.Rect(offset_right_x_pt, offset_y_pt, offset_right_x_pt + image_size_pt[0], offset_y_pt + image_size_pt[1])
                
                # Inserir as imagens na primeira página
                pagina.insert_image(left_rect, filename=left_image_path)
                pagina.insert_image(right_rect, filename=right_image_path)
            
        # Salvar o documento modificado
        novo_pdf_path = pdf_path.replace('.pdf', '_com_modificacoes.pdf')
        doc.save(novo_pdf_path)
        doc.close()

        # Informar ao usuário sobre o salvamento do novo arquivo
        print(f"PDF modificado salvo como: {novo_pdf_path}")

        # Abrir o PDF automaticamente (Windows)
        try:
            os.startfile(novo_pdf_path)
        except Exception as e:
            print(f"Não foi possível abrir o arquivo PDF automaticamente. Erro: {e}")

    def on_export_pdf(self):
        xlsx_path = self.create_excel()

        if xlsx_path is None or not os.path.isfile(xlsx_path):
            self.show_message("Erro", "O arquivo XLSX não existe ou não pode ser acessado.")
            return

        absolute_xlsx_path = os.path.abspath(xlsx_path).replace('/', '\\')
        pdf_path = f"{os.path.splitext(absolute_xlsx_path)[0]}.pdf"

        if os.path.exists(pdf_path):
            reply = self.show_custom_message("Arquivo Existente", "Um arquivo PDF já existe. Deseja substituí-lo?")
            if reply == QMessageBox.StandardButton.No:
                return

        # Inicia a thread e o progress dialog
        self.progress_dialog = QProgressDialog("Exportando PDF...", "Cancelar", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)  # Começa imediatamente
        self.progress_dialog.setStyleSheet("QProgressDialog, QProgressBar, QPushButton { font-size: 16pt; background: none; color: none; }")  # Ajusta o tamanho da fonte para todos os componentes relevantes, removendo estilos específicos de cores

        self.thread = ExportPdfThread(absolute_xlsx_path, pdf_path)
        self.thread.progress.connect(self.progress_dialog.setValue)
        self.thread.finished.connect(self.on_pdf_exported)
        self.thread.start()
        # Conecta o cancelamento do progress dialog com uma ação
        self.progress_dialog.canceled.connect(self.thread.terminate)  # Encerra a thread se o usuário cancelar

    def on_pdf_exported(self, pdf_path, error):
        if error:
            self.show_message("Erro", f"Erro ao gerar documento PDF: {error}")
        else:
            self.show_message("Sucesso", f"Arquivo PDF gerado com sucesso: {pdf_path}")
            # Definir os caminhos das imagens
            left_image_path = str(TUCANO_PATH)
            right_image_path = str(MARINHA_PATH)
            watermark_image_path = str(CEIMBRA_BG)
            # Chamar a função para adicionar imagens ao PDF e obter o novo caminho do PDF
            novo_pdf_path = self.adicionar_imagem_ao_pdf(pdf_path, left_image_path, right_image_path, watermark_image_path)
            if novo_pdf_path:
                self.open_pdf_document(novo_pdf_path)
            else:
                print("Falha ao obter o caminho do novo PDF.")

    def show_message(self, title, text):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setStyleSheet("QMessageBox { font-size: 16pt; }")  # Define o estilo diretamente no QMessageBox
        msg_box.exec()

    def show_custom_message(self, title, text):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setStyleSheet("QMessageBox { font-size: 16pt; }")  # Ajusta o tamanho da fonte para 16
        return msg_box.exec()

    def open_pdf_document(self, pdf_path):
        if sys.platform == 'win32':
            os.startfile(pdf_path)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, pdf_path])
            
class ExportPdfThread(QThread):
    finished = pyqtSignal(str, str)  # Sinal para informar o resultado
    progress = pyqtSignal(int)  # Sinal para atualizar o progresso

    def __init__(self, xlsx_path, pdf_path):
        super().__init__()
        self.xlsx_path = xlsx_path
        self.pdf_path = pdf_path

    def run(self):
        try:
            self.progress.emit(10)  # Inicia o progresso
            excel = DispatchEx('Excel.Application')
            excel.Visible = False
            excel.DisplayAlerts = False

            wb = excel.Workbooks.Open(self.xlsx_path)
            self.progress.emit(50)  # Meio do progresso
            wb.SaveAs(self.pdf_path, FileFormat=57)

            wb.Close(SaveChanges=0)
            excel.Quit()
            self.progress.emit(100)  # Completa o progresso

            self.finished.emit(self.pdf_path, '')
        except Exception as e:
            self.finished.emit('', str(e))
            if 'excel' in locals():
                excel.Quit()
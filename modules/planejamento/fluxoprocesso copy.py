from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import pathlib
import json
import sqlite3
from datetime import datetime

class FluxoProcessoDialog(QDialog):
    def __init__(self, etapas, df_processos, database_manager, parent=None):
        super().__init__(parent)
        self.etapas = etapas
        self.df_processos = df_processos
        self.database_manager = database_manager
        
        self.setWindowTitle("Painel de Fluxo dos Processos")
        self.setFixedSize(QSize(1490, 750))
        self.setStyleSheet("QDialog { background-color: #050f41; }")
        self._setup_ui()

    def _populate_list_widget(self, list_widget):
        print(f"Preenchendo {list_widget.objectName()}...")
        with self.database_manager as conn:
            self.database_manager.verificar_e_atualizar_etapas(conn)
            cursor = conn.cursor()
            cursor.execute('''SELECT cpz.chave_processo, cp.objeto, cpz.sequencial FROM controle_prazos cpz
                              INNER JOIN (SELECT chave_processo, MAX(sequencial) AS max_sequencial FROM controle_prazos GROUP BY chave_processo) max_cpz
                              ON cpz.chave_processo = max_cpz.chave_processo AND cpz.sequencial = max_cpz.max_sequencial
                              INNER JOIN controle_processos cp ON cpz.chave_processo = cp.modalidade
                              WHERE cpz.etapa = ? ORDER BY cpz.chave_processo''', (list_widget.objectName(),))
            for chave_processo, objeto, _ in cursor.fetchall():
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
        list_widget = CustomListWidget(parent=self)
        list_widget.setObjectName(etapa)
        self._populate_list_widget(list_widget)
        layout.addWidget(list_widget)
        return group_box

class CustomListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
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

    def addFormattedTextItem(self, modalidade, objeto):
        formattedText = f"<html><head/><body><p style='text-align: center;'><span style='font-weight:600; font-size:14pt;'>{modalidade}</span><br/><span style='font-size:10pt;'>{objeto}</span></p></body></html>"
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
        if event.button() == Qt.MouseButton.LeftButton and self.currentItem():
            self.startDrag(Qt.DropAction.MoveAction)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            currentWidget = self.itemWidget(item)
            if currentWidget:
                mimeData = QMimeData()
                itemData = {
                    "modalidade": item.text(),  # ou outra propriedade que deseje transmitir
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
            html_texto = itemData["modalidade"]  # O texto HTML que inclui modalidade e objeto
            modalidade = extrair_modalidade(html_texto)  # Extrai modalidade do HTML
            objeto = itemData["objeto"]
            origin = itemData["origin"]
            nova_etapa = self.objectName()

            if origin != nova_etapa:
                self.addFormattedTextItem(modalidade, objeto)
                event.source().takeItem(event.source().currentRow())  # Remove o item da lista original
                etapa_manager = EtapaManager(str(CONTROLE_DADOS))
                etapa_manager.registrar_etapa(modalidade, nova_etapa, "Comentário opcional")

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
            data_inicial = result[0] if result else datetime.today().strftime('%Y-%m-%d')
            
            # Inserir a nova etapa
            cursor.execute('''
                INSERT INTO controle_prazos (chave_processo, etapa, data_inicial, data_final, dias_na_etapa, comentario, sequencial)
                VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT MAX(sequencial) FROM controle_prazos WHERE chave_processo = ?) + 1, 1))
            ''', (chave_processo, nova_etapa, data_inicial, datetime.today().strftime('%Y-%m-%d'), 0, comentario, chave_processo))
            
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

import re
def extrair_modalidade(texto_html):
    # Usa expressão regular para extrair o texto dentro do primeiro <span> após <p>
    match = re.search(r"<p[^>]*><span[^>]*>(.*?)</span>", texto_html)
    if match:
        return match.group(1)
    return None
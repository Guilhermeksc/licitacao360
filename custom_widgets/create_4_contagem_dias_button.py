from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import json
from pathlib import Path
from diretorios import *
from styles.styless import get_transparent_title_style
from utils.utilidades import (
    formatar_data, NoScrollDateEdit, NoScrollComboBox, 
    CustomHeaderView
)
from docxtpl import DocxTemplate
import subprocess
import os
import platform
import webbrowser
from datetime import datetime, timedelta
from PyQt6.QtCore import pyqtSignal
import pandas as pd

def atualizar_etapa_especifica_excel(processo, etapa_atual, controle_processos_path):
    # Carregar o DataFrame do arquivo Excel
    df_controle_processos = pd.read_excel(controle_processos_path)

    # Extrair o número do pregão e o ano do identificador do processo
    num_pregao, ano_pregao = processo.split(' ')[1].split('/')

    # Atualizar a etapa apenas para o processo específico
    df_controle_processos.loc[
        (df_controle_processos['num_pregao'] == int(num_pregao)) & 
        (df_controle_processos['ano_pregao'] == int(ano_pregao)), 
        'etapa'
    ] = etapa_atual

    # Salvar as alterações de volta no arquivo Excel
    df_controle_processos.to_excel(controle_processos_path, index=False)

def atualizar_etapa_atual(processo_identificador, etapa_atual, processos_json_path, controle_processos_path):
    # Carregar o conteúdo do arquivo JSON com codificação utf-8
    with open(processos_json_path, 'r+', encoding='utf-8') as file:
        dados = json.load(file)

        # Verifica se o identificador do processo existe nos dados
        if processo_identificador in dados:
            # Atualizar a etapa_atual para o processo específico
            dados[processo_identificador]['etapa_atual'] = etapa_atual
            # Chamar a função para atualizar no Excel
            atualizar_etapa_especifica_excel(processo_identificador, etapa_atual, controle_processos_path)

        # Salvar as alterações de volta no arquivo JSON
        file.seek(0)
        json.dump(dados, file, indent=4)
        file.truncate()


ETAPAS_DISPONIVEIS = [
    'Planejamento',
    'Setor Responsável', 
    'IRP', 
    'Edital', 
    'Nota Técnica', 
    'CJACM',
    'Devolvido por Nota', 
    'Recomendações AGU', 
    'Provisionamento',
    'Sessão Pública', 
    'Impugnado', 
    'Homologado',
    'Assinatura Contrato',
    'Suspenso',
    'Concluído',
    'Cancelado'
]

etapas = {
    'Planejamento': 'Planejamento',
    'Setor Responsável': 'Setor\nResp.', 
    'IRP': 'IRP', 
    'Edital': 'Edital', 
    'Nota Técnica': 'Nota\nTéc.', 
    'CJACM': 'AGU',
    'Devolvido por Nota': 'Devol\nNota', 
    'Recomendações AGU': 'Recom.', 
    'Provisionamento': 'Provis.',
    'Sessão Pública': 'Sessão\nPública', 
    'Impugnado': 'Impug-\nnado', 
    'Homologado': 'Homo-\nlogado',
    'Assinatura Contrato': 'Assin\nContr',
    'Concluído': 'Con-\ncluído', 
    'Suspenso': 'Sus-\npenso', 
    'Cancelado': 'Can-\ncelado', 
}

class DragDropTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def dropEvent(self, event):
        pointer_position = event.position().toPoint()
        target_index = self.indexAt(pointer_position)

        if not target_index.isValid():
            event.ignore()
            return

        dragged_row = self.currentRow()
        target_row = target_index.row()

        if dragged_row == target_row:
            event.ignore()
            return

        print(f"Antes da movimentação - Linha arrastada: {dragged_row}, Linha alvo: {target_row}")
        self.imprimir_dados_da_tabela()

        dragged_row_data = self.row_data(dragged_row)

        self.removeRow(dragged_row)

        # Ajustar o índice de destino
        if dragged_row < target_row:
            self.insertRow(target_row)  # Inserir abaixo se arrastar para baixo
        else:
            self.insertRow(target_row)  # Inserir acima se arrastar para cima

        # Correção para recriar widgets
        new_row_index = target_row if dragged_row < target_row else target_row
        self.set_row_data(new_row_index, dragged_row_data)

        self.setCurrentCell(new_row_index, 0)

        self.viewport().update()

        print(f"Após a movimentação - Linha arrastada: {dragged_row}, Linha alvo: {new_row_index}")
        self.imprimir_dados_da_tabela()

        # Atualiza as datas após o arrastar e soltar
        self.parent().verificar_e_atualizar_dias_etapas(str(PROCESSOS_JSON_PATH))


    def row_data(self, row):
        """Retorna os dados de uma linha especificada."""
        data = []
        for col in range(self.columnCount()):
            if self.cellWidget(row, col):
                widget = self.cellWidget(row, col)
                # Salvar o estado do widget (por exemplo, texto atual para QComboBox)
                if isinstance(widget, QComboBox):
                    data.append(widget.currentText())
                elif isinstance(widget, QDateEdit):
                    data.append(widget.date().toString('dd-MM-yyyy'))
            else:
                data.append(self.item(row, col).text() if self.item(row, col) else "")
        return data

    def set_row_data(self, row, data):
        """Define os dados para uma linha especificada."""
        for col, value in enumerate(data):
            if col == 0:  # Coluna 'Etapa' com QComboBox
                combo_box = QComboBox()
                combo_box.addItems(ETAPAS_DISPONIVEIS)
                combo_box.setCurrentText(value)
                self.setCellWidget(row, col, combo_box)
            elif col in [1, 2]:  # Colunas 'Data Inicial' e 'Data Final' com QDateEdit
                date_edit = QDateEdit()
                date_edit.setCalendarPopup(True)
                date_edit.setDate(datetime.strptime(value, '%d-%m-%Y').date() if value else datetime.today().date())
                self.setCellWidget(row, col, date_edit)
            else:
                self.setItem(row, col, QTableWidgetItem(value))
            
    def imprimir_dados_da_tabela(self):
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                widget = self.cellWidget(row, col)
                if widget:
                    if isinstance(widget, QComboBox):
                        row_data.append(widget.currentText())
                    elif isinstance(widget, QDateEdit):
                        row_data.append(widget.date().toString('dd-MM-yyyy'))
                else:
                    row_data.append(self.item(row, col).text() if self.item(row, col) else "")
            print(f"Linha {row}: {row_data}")

class ContagemDias(QWidget):
    def __init__(self, parent=None, database_dir=None):
        super().__init__(parent)
        label_fases = QLabel("Informações do Processo")
        label_fases.setStyleSheet(get_transparent_title_style())
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(label_fases)  # Adicione a label ao layout

        self.tableView = QTableView()
        self.layout.addWidget(self.tableView)

        # Substitua o cabeçalho padrão pelo personalizado
        custom_header = CustomHeaderView(Qt.Orientation.Horizontal, etapas, self.tableView)
        self.tableView.setHorizontalHeader(custom_header)

        self.carregar_dados()
        self.verificar_e_atualizar_dias_etapas(str(PROCESSOS_JSON_PATH))  # Passando o caminho do arquivo como string
    
        # Mapeamento de colunas para etapas
        self.coluna_para_etapa = {i: etapa for i, etapa in enumerate(etapas.keys())}

        # Conectar o evento de clique da célula
        self.tableView.clicked.connect(self.mostrar_detalhes_contagem_dias)

        # Adiciona esta linha para conectar o evento de clique do cabeçalho vertical
        self.tableView.verticalHeader().sectionClicked.connect(self.mostrar_detalhes_contagem_dias)

    def verificar_e_atualizar_dias_etapas(self, file_path):
        with open(file_path, 'r+', encoding='utf-8') as file:
            processos_json = json.load(file)
            atualizado = False

            for processo, dados in processos_json.items():
                historico = dados.get('historico', [])
                for i, registro in enumerate(historico):
                    data_inicial_str = registro.get('data_inicial')
                    data_final_str = registro.get('data_final')
                    ultima_etapa = i == len(historico) - 1

                    if data_inicial_str:
                        data_inicial = datetime.strptime(data_inicial_str, '%d-%m-%Y').date()
                        data_final = data_final_str and datetime.strptime(data_final_str, '%d-%m-%Y').date()
                        if ultima_etapa or not data_final:
                            data_final = datetime.today().date()  # Atualiza para a data atual se for a última etapa
                            registro['data_final'] = data_final.strftime('%d-%m-%Y')
                            atualizado = True

                        dias_calculados = (data_final - data_inicial).days
                        if dias_calculados != registro['dias_na_etapa']:
                            registro['dias_na_etapa'] = dias_calculados
                            atualizado = True

            if atualizado:
                file.seek(0)
                json.dump(processos_json, file, indent=4, ensure_ascii=False)
                file.truncate()

    def atualizarDados(self):
        self.carregar_dados()
        self.tableView.setModel(self.model)

    def carregar_dados(self):
        if not os.path.exists(str(PROCESSOS_JSON_PATH)):
            self.processos_json = {}
            with open(str(PROCESSOS_JSON_PATH), 'w', encoding='utf-8') as file:
                json.dump(self.processos_json, file, ensure_ascii=False, indent=4)
        else:
            with open(str(PROCESSOS_JSON_PATH), 'r', encoding='utf-8') as file:
                self.processos_json = json.load(file)

        # Inicialize o dicionário dias_por_etapa para todas as etapas disponíveis
        dias_por_etapa = {etapa: 0 for etapa in ETAPAS_DISPONIVEIS}
        self.model = QStandardItemModel()

        # Cabeçalhos incluem todas as etapas disponíveis e a coluna "Total Dias"
        cabecalhos = [etapas.get(etapa, etapa) for etapa in ETAPAS_DISPONIVEIS] + ["Total\nDias"]
        self.model.setHorizontalHeaderLabels(cabecalhos)

        rotulos_linhas = []
        fonte = QFont()
        fonte.setBold(True)
        fonte.setPointSize(14)

        for processo, info in self.processos_json.items():
            # Reseta a contagem de dias para cada processo
            dias_por_etapa = {etapa: 0 for etapa in ETAPAS_DISPONIVEIS}
            total_dias = 0

            if 'historico' in info:
                for registro_historico in info['historico']:
                    etapa = registro_historico.get('etapa')
                    if etapa not in ETAPAS_DISPONIVEIS:
                        print(f"Etapa desconhecida: {etapa}")
                        continue
                    else:
                        print(f"Etapa desconhecida: {etapa}")
                    data_inicial_str = registro_historico.get('data_inicial')
                    data_final_str = registro_historico.get('data_final')
                    dias_na_etapa = registro_historico.get('dias_na_etapa', 0)

                    if data_final_str is None and data_inicial_str:
                        try:
                            data_inicial = formatar_data(data_inicial_str)
                            dias_na_etapa_atual = (datetime.today().date() - data_inicial).days
                        except ValueError as e:
                            print(f"Erro ao processar data inicial para o processo {processo}: {e}")
                    else:
                        dias_na_etapa_atual = dias_na_etapa

                    # Acumular dias para cada etapa
                    dias_por_etapa[etapa] = dias_por_etapa.get(etapa, 0) + dias_na_etapa_atual

                    total_dias += dias_na_etapa_atual

            # Criar itens da tabela com os dias acumulados para cada etapa
            row_items = [QStandardItem(str(dias_por_etapa[etapa])) for etapa in ETAPAS_DISPONIVEIS]
            for item in row_items:
                item.setFont(fonte)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_total = QStandardItem(str(total_dias))
            item_total.setFont(fonte)
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            row_items.append(item_total)

            self.model.appendRow(row_items)
            rotulos_linhas.append(processo)

        self.model.setVerticalHeaderLabels(rotulos_linhas)
        self.tableView.setModel(self.model)
        
        # Ocultar colunas específicas
        colunas_para_ocultar = ['Planejamento', 'Concluído', 'Cancelado']
        for etapa in colunas_para_ocultar:
            coluna_index = ETAPAS_DISPONIVEIS.index(etapa)
            self.tableView.hideColumn(coluna_index)

        # Configuração do modo de redimensionamento para Stretch
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Configurar a altura fixa para todas as linhas
        altura_fixa = 30  # Defina a altura desejada aqui
        for i in range(self.model.rowCount()):
            self.tableView.setRowHeight(i, altura_fixa)

        # Desabilitar o redimensionamento das linhas pelo usuário
        self.tableView.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        # Configuração do modo de redimensionamento para Stretch para o cabeçalho horizontal
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Estilo da tabela com cores alternadas
        self.tableView.setAlternatingRowColors(True)

    def mostrar_detalhes(self, index):
        # Verificar se o argumento é um QModelIndex
        if isinstance(index, QModelIndex):
            row = index.row()
        elif isinstance(index, int):
            # No caso de um clique no cabeçalho vertical, o índice é o número da linha
            row = index
        else:
            return  # Caso não seja nem QModelIndex nem int, retorna

        # Aqui, 'row' representa o número da linha clicada
        processo_selecionado = self.model.verticalHeaderItem(row).text()
        with open(str(PROCESSOS_JSON_PATH), 'r', encoding='utf-8') as file:
            processos_json = json.load(file)
            if processo_selecionado in processos_json:
                dialog = DetalhesProcessoDialog({'processo': processo_selecionado, 'dados': processos_json[processo_selecionado]}, self)
                dialog.etapa_atualizada.connect(self.atualizar_interface)
                dialog.exec()  

    def mostrar_detalhes_contagem_dias(self, index):
        # Verificar se o argumento é um QModelIndex
        if isinstance(index, QModelIndex):
            row = index.row()
        elif isinstance(index, int):
            # No caso de um clique no cabeçalho vertical, o índice é o número da linha
            row = index
        else:
            return  # Caso não seja nem QModelIndex nem int, retorna

        # Aqui, 'row' representa o número da linha clicada
        processo_selecionado = self.model.verticalHeaderItem(row).text()
        with open(str(PROCESSOS_JSON_PATH), 'r', encoding='utf-8') as file:
            processos_json = json.load(file)
            if processo_selecionado in processos_json:
                dialog = DetalhesProcessoDialog({'processo': processo_selecionado, 'dados': processos_json[processo_selecionado]}, self)
                dialog.exec()  

    def atualizar_interface(self):
        # Função para atualizar a interface gráfica do ProcessosWidget
        self.preencher_blocos()

class AdicionarEtapaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Adicionar Nova Etapa")
        layout = QVBoxLayout(self)

        # Formulário para entrada de dados
        form_layout = QFormLayout()
        self.combo_box_etapa = QComboBox()
        self.combo_box_etapa.addItems(ETAPAS_DISPONIVEIS)
        self.data_inicial_edit = QDateEdit()
        self.data_inicial_edit.setCalendarPopup(True)
        self.data_final_edit = QDateEdit()
        self.data_final_edit.setCalendarPopup(True)
        self.comentario_edit = QTextEdit()  # Campo de texto para comentário

        form_layout.addRow("Etapa:", self.combo_box_etapa)
        form_layout.addRow("Data Inicial:", self.data_inicial_edit)
        form_layout.addRow("Data Final:", self.data_final_edit)
        form_layout.addRow("Comentário:", self.comentario_edit)  # Adiciona o campo de comentário ao formulário

        layout.addLayout(form_layout)

        # Botões
        botoes_layout = QHBoxLayout()
        botao_confirmar = QPushButton("Confirmar")
        botao_cancelar = QPushButton("Cancelar")
        botoes_layout.addWidget(botao_confirmar)
        botoes_layout.addWidget(botao_cancelar)

        layout.addLayout(botoes_layout)

        botao_confirmar.clicked.connect(self.accept)
        botao_cancelar.clicked.connect(self.reject)

    def get_data(self):
        return {
            "etapa": self.combo_box_etapa.currentText(),
            "data_inicial": self.data_inicial_edit.date().toString('dd-MM-yyyy'),
            "data_final": self.data_final_edit.date().toString('dd-MM-yyyy'),
            "comentario": self.comentario_edit.toPlainText()  # Obter o texto do campo de comentário para QTextEdit
        }

    def set_initial_dates(self, data_inicial, data_final):
        if data_inicial:
            # Converte QDate para string antes de usar strptime
            data_inicial_str = data_inicial.toString('dd-MM-yyyy')
            self.data_inicial_edit.setDate(datetime.strptime(data_inicial_str, '%d-%m-%Y').date())
        if data_final:
            # Converte QDate para string antes de usar strptime
            data_final_str = data_final.toString('dd-MM-yyyy')
            self.data_final_edit.setDate(datetime.strptime(data_final_str, '%d-%m-%Y').date())
        
class DetalhesProcessoDialog(QDialog):
    etapa_atualizada = pyqtSignal()

    def __init__(self, processo_info, parent=None):
        super().__init__(parent)
        # Verifica se os dados de entrada estão no formato correto
        if not isinstance(processo_info, dict) or 'processo' not in processo_info or 'dados' not in processo_info:
            raise ValueError("Dados do processo não estão no formato esperado.")

        self.processo_info = processo_info  # Inicialize o atributo aqui
        self.updating_dates = False  # Variável de controle para atualização de datas

        self.resize(700, 400)  # Define o tamanho inicial da janela

        # Extrair num_pregao e ano_pregao
        num_pregao, ano_pregao = processo_info['processo'].split(' ')[1].split('/')

        # Configurar o título da janela
        self.setWindowTitle(f"Detalhes do Pregão Eletrônico nº {num_pregao}/{ano_pregao}")

        self.main_layout = QVBoxLayout(self)

        # Adicionar informações do processo
        self.main_layout.addWidget(QLabel(f"Nup: {processo_info['dados']['nup']}"))
        self.main_layout.addWidget(QLabel(f"Objeto: {processo_info['dados']['objeto']}"))
        self.main_layout.addWidget(QLabel(f"UASG: {processo_info['dados']['uasg']}"))
        self.main_layout.addWidget(QLabel(f"OM: {processo_info['dados']['orgao_responsavel']} - {processo_info['dados']['sigla_om']}"))
        self.main_layout.addWidget(QLabel(f"Setor Responsável pela Demanda: {processo_info['dados']['setor_responsavel']}"))
        self.main_layout.addWidget(QLabel(f"Etapa Atual: {processo_info['dados']['etapa_atual']}"))

        self.criar_tabela_historico(processo_info)
        self.criar_botoes()

        self.tabela_historico_data = [self.get_row_data(i) for i in range(self.tabela_historico.rowCount())]
        self.setLayout(self.main_layout)
        
    def criar_tabela_historico(self, processo_info):
        self.tabela_historico = DragDropTableWidget(self)
        self.configurar_tabela_historico()
        self.preencher_tabela_historico(processo_info)

    def configurar_tabela_historico(self):
        self.tabela_historico.setColumnCount(5)
        self.tabela_historico.setHorizontalHeaderLabels(['Etapa', 'Data Inicial', 'Data Final', 'Dias', 'Comentário'])
        
        # Definir o tamanho fixo para algumas colunas e ajustar outras automaticamente
        self.tabela_historico.setColumnWidth(0, 140)  # 'Etapa'
        self.tabela_historico.setColumnWidth(1, 90)  # 'Data Inicial'
        self.tabela_historico.setColumnWidth(2, 90)  # 'Data Final'
        self.tabela_historico.setColumnWidth(3, 30)  # 'Dias'

        # Configurar a última coluna para se ajustar automaticamente
        header = self.tabela_historico.horizontalHeader()
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.main_layout.addWidget(self.tabela_historico)

    def preencher_tabela_historico(self, processo_info):
        self.tabela_historico.setRowCount(0)
        for index, historico in enumerate(processo_info['dados']['historico']):
            self.adicionar_linha_historico(index, historico)

    def adicionar_linha_historico(self, index, historico):
        self.tabela_historico.insertRow(index)

        # Criar um QComboBox para a coluna 'Etapa'
        combo_box_etapa = NoScrollComboBox()
        combo_box_etapa.addItems(ETAPAS_DISPONIVEIS)
        etapa_atual = historico.get('etapa', 'Desconhecida')
        combo_box_etapa.setCurrentText(etapa_atual)
        self.tabela_historico.setCellWidget(index, 0, combo_box_etapa)

        # Adicionar QDateEdit para 'Data Inicial' e 'Data Final'
        self.adicionar_date_edit(index, 1, historico.get('data_inicial'))
        self.adicionar_date_edit(index, 2, historico.get('data_final'))

        # Adicionar campo para 'Dias na Etapa' e 'Comentário'
        self.tabela_historico.setItem(index, 3, QTableWidgetItem(str(historico.get('dias_na_etapa', ''))))
        comentario = historico.get('comentario', '')
        if isinstance(comentario, dict):
            comentario = json.dumps(comentario)
        self.tabela_historico.setItem(index, 4, QTableWidgetItem(comentario))

        # Atualizar a contagem de dias na tabela
        self.atualizar_dias_na_tabela(index)

    def criar_botoes(self):
        botoes_layout = QHBoxLayout()
        botao_adicionar_etapa = QPushButton("Adicionar Etapa")
        botao_excluir_etapa = QPushButton("Excluir Etapa")
        botao_salvar_alteracoes = QPushButton("Salvar alterações")  # Criar botão de salvar alterações
        botao_gerar_relatorio = QPushButton("Gerar Relatório")

        # Conectar os botões às suas respectivas funções
        botao_adicionar_etapa.clicked.connect(self.adicionar_etapa)
        botao_excluir_etapa.clicked.connect(self.excluir_etapa)
        botao_salvar_alteracoes.clicked.connect(self.salvar_alteracoes)  # Conectar ao método salvar_alteracoes
        botao_gerar_relatorio.clicked.connect(self.gerar_relatorio)

        # Adicionar os botões ao layout
        botoes_layout.addWidget(botao_adicionar_etapa)
        botoes_layout.addWidget(botao_excluir_etapa)
        botoes_layout.addWidget(botao_salvar_alteracoes)
        botoes_layout.addWidget(botao_gerar_relatorio)
        
        self.layout().addLayout(botoes_layout)

    def get_row_data(self, row_index):
        row_data = {}
        for col in range(self.tabela_historico.columnCount()):
            if self.tabela_historico.item(row_index, col) is not None:
                row_data[col] = self.tabela_historico.item(row_index, col).text()
            else:
                widget = self.tabela_historico.cellWidget(row_index, col)
                if isinstance(widget, QComboBox):
                    row_data[col] = widget.currentText()
                elif isinstance(widget, QDateEdit):
                    row_data[col] = widget.date().toString('dd-MM-yyyy')
                # Adicione mais condições aqui para outros tipos de widgets, se necessário
        return row_data

    def set_row_data(self, row_index, row_data):
        """Define os dados de uma linha específica da tabela."""
        for col, text in row_data.items():
            self.tabela_historico.setItem(row_index, col, QTableWidgetItem(text))

    def atualizar_dias_na_tabela(self, row):
        print(f"Atualizando dias para a linha {row}")
        data_inicial_widget = self.tabela_historico.cellWidget(row, 1)
        data_final_widget = self.tabela_historico.cellWidget(row, 2)

        if data_inicial_widget and data_final_widget:
            data_inicial = data_inicial_widget.date().toPyDate()
            data_final = data_final_widget.date().toPyDate()

            print(f"Data inicial: {data_inicial}, Data final: {data_final}")

            dias = (data_final - data_inicial).days
            print(f"Dias calculados: {dias}")
            self.tabela_historico.setItem(row, 3, QTableWidgetItem(str(dias)))

    def adicionar_date_edit(self, row, column, date_input):
        date_edit = NoScrollDateEdit()
        date_edit.setCalendarPopup(True)

        # Se a entrada for None, use a data atual como padrão
        if date_input is None:
            date = QDate.currentDate()
        # Verifica se a entrada é uma string e converte para QDate, se necessário
        elif isinstance(date_input, str):
            date = QDate.fromString(date_input, 'dd-MM-yyyy')
        else:
            date = date_input  # Se já for um objeto QDate, usa diretamente

        date_edit.setDate(date)
        date_edit.dateChanged.connect(lambda new_date: self.on_date_changed(row, column, new_date))
        self.tabela_historico.setCellWidget(row, column, date_edit)

    def on_date_changed(self, row, column, new_date):
        if self.updating_dates:
            return

        self.updating_dates = True
        # self.validar_e_corrigir_datas(row)
        self.atualizar_datas_adjacentes(row, column)
        self.validar_e_ajustar_todas_as_datas()  # Chamar após alterações de data individuais

        self.tabela_historico.viewport().update()
        self.updating_dates = False

    def validar_e_corrigir_datas(self, row, exibir_mensagem=False):
        data_atual = QDate.currentDate()
        ultima_linha = row == self.tabela_historico.rowCount() - 1

        data_inicial_widget = self.tabela_historico.cellWidget(row, 1)
        data_final_widget = self.tabela_historico.cellWidget(row, 2)

        if data_inicial_widget and data_final_widget:
            data_inicial = data_inicial_widget.date().toPyDate()
            data_final = data_final_widget.date().toPyDate()

            # Restrições para a última linha
            if ultima_linha:
                # A data final da última linha não pode ultrapassar a data atual
                if data_final > data_atual.toPyDate():
                    data_final_widget.setDate(data_atual)
                    data_final = data_atual.toPyDate()

                # A data inicial da última linha pode ser anterior, mas não anterior à data final da penúltima linha
                if row > 0:
                    data_final_penultima = self.tabela_historico.cellWidget(row - 1, 2).date().toPyDate()
                    if data_inicial < data_final_penultima:
                        data_inicial_widget.setDate(QDate(data_final_penultima.year, data_final_penultima.month, data_final_penultima.day))
                        data_inicial = data_final_penultima

            # Restrições para outras linhas
            else:
                if data_final < data_inicial:
                    if exibir_mensagem:
                        QMessageBox.warning(self, "Erro de Data", "A data final não pode ser anterior à data inicial.")
                    data_final_widget.setDate(data_inicial_widget.date())
                    data_final = data_inicial

            # Atualizar contagem de dias
            dias = (data_final - data_inicial).days
            self.tabela_historico.setItem(row, 3, QTableWidgetItem(str(dias)))

        # Verificar e corrigir a linha anterior, se necessário
        if row > 0:
            data_final_anterior_widget = self.tabela_historico.cellWidget(row - 1, 2)
            if data_final_anterior_widget and data_final_anterior_widget.date().toPyDate() > data_inicial:
                data_final_anterior_widget.setDate(data_inicial_widget.date())
                self.atualizar_dias_na_tabela(row - 1)

        # Verificar e corrigir a linha seguinte, se necessário
        if row < self.tabela_historico.rowCount() - 1:
            data_inicial_proxima_widget = self.tabela_historico.cellWidget(row + 1, 1)
            if data_inicial_proxima_widget and data_inicial_proxima_widget.date().toPyDate() < data_final:
                data_inicial_proxima_widget.setDate(data_final_widget.date())
                self.atualizar_dias_na_tabela(row + 1)

    def validar_e_ajustar_todas_as_datas(self):
        for row in range(self.tabela_historico.rowCount()):
            # Ajustar datas para cada linha
            self.validar_e_corrigir_datas(row)

            # Ajustar data final da linha para ser igual à data inicial da próxima linha
            if row < self.tabela_historico.rowCount() - 1:
                data_final_widget = self.tabela_historico.cellWidget(row, 2)
                data_inicial_proxima_widget = self.tabela_historico.cellWidget(row + 1, 1)
                if data_final_widget and data_inicial_proxima_widget:
                    data_final_widget.setDate(data_inicial_proxima_widget.date())
                    self.atualizar_dias_na_tabela(row)

    def atualizar_datas_adjacentes(self, row, column):
        # Data final alterada: atualizar a data inicial da linha seguinte
        if column == 2 and row < self.tabela_historico.rowCount() - 1:
            data_final_atual = self.tabela_historico.cellWidget(row, 2).date()
            data_inicial_proxima_widget = self.tabela_historico.cellWidget(row + 1, 1)
            if data_inicial_proxima_widget:
                data_inicial_proxima_widget.setDate(data_final_atual)
                self.validar_e_corrigir_datas(row + 1)

        # Data inicial alterada: atualizar a data final da linha anterior
        elif column == 1 and row > 0:
            data_inicial_atual = self.tabela_historico.cellWidget(row, 1).date()
            data_final_anterior_widget = self.tabela_historico.cellWidget(row - 1, 2)
            if data_final_anterior_widget:
                data_final_anterior_widget.setDate(data_inicial_atual)
                self.validar_e_corrigir_datas(row - 1)

    def adicionar_etapa(self):
        selected_row = self.tabela_historico.currentRow()
        data_final_selecionada = QDate.currentDate()

        if selected_row != -1 and selected_row < self.tabela_historico.rowCount() - 1:
            data_final_widget = self.tabela_historico.cellWidget(selected_row, 2)
            if data_final_widget:
                data_final_selecionada = data_final_widget.date()

        dialog = AdicionarEtapaDialog(self)
        dialog.set_initial_dates(data_final_selecionada, data_final_selecionada)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            nova_etapa_data = dialog.get_data()
            self.updating_dates = True

            data_inicial_nova_etapa = QDate.fromString(nova_etapa_data['data_inicial'], 'dd-MM-yyyy')
            data_final_nova_etapa = QDate.fromString(nova_etapa_data['data_final'], 'dd-MM-yyyy')

            nova_linha = selected_row + 1 if selected_row != -1 else self.tabela_historico.rowCount()
            self.tabela_historico.insertRow(nova_linha)

            # Verifica se a nova linha é a última linha da tabela
            if nova_linha == self.tabela_historico.rowCount() - 1:
                # Atualiza a etapa no arquivo Excel
                processo = self.processo_info['processo']  # Presumindo que 'processo_info' contém o identificador do processo
                etapa_atual = nova_etapa_data['etapa']
                atualizar_etapa_atual(processo, etapa_atual, str(PROCESSOS_JSON_PATH), str(CONTROLE_PROCESSOS_DIR))

            combo_box_etapa = NoScrollComboBox()
            combo_box_etapa.addItems(ETAPAS_DISPONIVEIS)
            combo_box_etapa.setCurrentText(nova_etapa_data['etapa'])
            self.tabela_historico.setCellWidget(nova_linha, 0, combo_box_etapa)

            self.adicionar_date_edit(nova_linha, 1, data_inicial_nova_etapa)
            self.adicionar_date_edit(nova_linha, 2, data_final_nova_etapa)
            self.tabela_historico.setItem(nova_linha, 3, QTableWidgetItem('0'))
            self.tabela_historico.setItem(nova_linha, 4, QTableWidgetItem(nova_etapa_data['comentario']))
            self.atualizar_dias_na_tabela(nova_linha)
            self.validar_e_ajustar_todas_as_datas()  # Verifica e ajusta todas as datas da tabela

            self.updating_dates = False

        self.tabela_historico.viewport().update()

    def excluir_etapa(self):
        linha_selecionada = self.tabela_historico.currentRow()
        if linha_selecionada != -1:
            self.tabela_historico.removeRow(linha_selecionada)
            self.validar_e_ajustar_todas_as_datas()  # Adicionado após a exclusão de uma etapa
        else:
            QMessageBox.warning(self, "Seleção", "Por favor, selecione uma etapa para excluir.")

    def salvar_alteracoes(self):
        # Extrair o identificador do processo (ex: "PE 20/2023")
        processo_identificador = self.processo_info['processo']

        # Construir a nova lista de histórico com base nos dados da tabela
        novo_historico = []
        for i in range(self.tabela_historico.rowCount()):
            row_data = self.get_row_data(i)
            etapa = row_data[0]
            data_inicial = row_data[1]
            data_final = row_data[2]
            dias_na_etapa = int(row_data[3])
            comentario = row_data[4]

            novo_historico.append({
                "etapa": etapa,
                "data_inicial": data_inicial,
                "data_final": data_final,
                "dias_na_etapa": dias_na_etapa,
                "comentario": comentario,
                "sequencial": i + 1  # Sequencial atualizado com base na posição na tabela
            })

        # Carregar o arquivo JSON existente
        with open(str(PROCESSOS_JSON_PATH), 'r+', encoding='utf-8') as file:
            processos_json = json.load(file)

            # Verificar se o processo existe no arquivo JSON e atualizar o histórico
            if processo_identificador in processos_json:
                processos_json[processo_identificador]['historico'] = novo_historico

                # Retornar ao início do arquivo e sobrescrever com os dados atualizados
                file.seek(0)
                json.dump(processos_json, file, indent=4, ensure_ascii=False)
                file.truncate()

        QMessageBox.information(self, "Salvo", "As alterações foram salvas com sucesso.")
        self.etapa_atualizada.emit()

    def gerar_relatorio(self):
        # Carregar o template
        template_path = os.path.join(GERAR_RELATORIO_DIR, 'relatorio_pregao.docx')
        doc = DocxTemplate(template_path)

        # Preparar os dados do processo
        dados_processo = self.processo_info['dados']
        info_processo = f"""
        Nup: {dados_processo['nup']}
        Objeto: {dados_processo['objeto']}
        UASG: {dados_processo['uasg']}
        OM: {dados_processo['orgao_responsavel']} - {dados_processo['sigla_om']}
        Setor Responsável pela Demanda: {dados_processo['setor_responsavel']}
        Etapa Atual: {dados_processo['etapa_atual']}
        """

        # Preparar os dados da tabela histórico
        contagem_dias_tabela = ""
        for historico in dados_processo['historico']:
            contagem_dias_tabela += f"Etapa: {historico['etapa']}, Data Inicial: {historico['data_inicial']}, Data Final: {historico['data_final']}, Dias: {historico['dias_na_etapa']}, Comentário: {historico['comentario']}\n"

        # Preencher o template com os dados
        context = {
            'info_processo': info_processo,
            'contagem_dias_tabela': contagem_dias_tabela
        }
        doc.render(context)

        # Normalizar o nome do arquivo para evitar caracteres não permitidos
        nome_processo_normalizado = self.processo_info['processo'].replace('/', '_')

        # Caminho do diretório onde o arquivo será salvo
        output_dir = os.path.join(GERAR_RELATORIO_DIR, nome_processo_normalizado)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Caminho completo do arquivo de saída DOCX
        output_path_docx = os.path.join(output_dir, f"relatorio_pregao_preenchido_{nome_processo_normalizado}.docx")

        # Salvar o documento .docx
        doc.save(output_path_docx)

        # Abrir o arquivo DOCX
        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', output_path_docx))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(output_path_docx)
        else:                                   # Linux variants
            subprocess.call(('xdg-open', output_path_docx))

        return output_path_docx
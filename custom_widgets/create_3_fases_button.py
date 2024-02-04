# create_3_fases_button.py
#teste git
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QMimeData, QDateTime, QDate
from PyQt6.QtGui import *
import pandas as pd
import numpy as np
from diretorios import *
import json
from pathlib import Path
from utils.utilidades import ler_arquivo_json, escrever_arquivo_json, inicializar_json_do_excel
from styles.styless import get_transparent_title_style
from datetime import datetime
from custom_widgets.create_4_contagem_dias_button import DetalhesProcessoDialog

class CustomListWidget(QListWidget):
    def __init__(self, processos_widget, parent=None):
        super().__init__(parent)
        self.processos_widget = processos_widget
        self.setMinimumSize(135, 100) 
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAcceptDrops(True)
        self.setFont(QFont("Arial", 16))

    def manageSelection(self):
        # Desmarca todos os itens exceto o item selecionado
        for i in range(self.count()):
            item = self.item(i)
            if item != self.currentItem():
                item.setSelected(False)

    def startDrag(self, supportedActions):
        
        drag = QDrag(self)
        mime_data = QMimeData()

        selected_item = self.currentItem()
        if selected_item:
            mime_data.setText(selected_item.text())
            drag.setMimeData(mime_data)

            # Criar um QPixmap do tamanho do widget
            pixmap = QPixmap(self.viewport().size())
            self.viewport().render(pixmap)

            # Recortar a parte do QPixmap que corresponde ao item
            rect = self.visualItemRect(selected_item)
            cropped_pixmap = pixmap.copy(rect)

            # Ajustar o hotspot para a posição do cursor dentro do item
            cursor_pos = self.viewport().mapFromGlobal(QCursor.pos())
            hotspot = cursor_pos - rect.topLeft()
            drag.setPixmap(cropped_pixmap)
            drag.setHotSpot(hotspot)

            drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.source() != self and event.mimeData().hasText():
            print("dropEvent chamado")
            new_item_text = event.mimeData().text()
            
            # Extrair informações do item para atualizar o DataFrame
            mod, num_pregao, ano_pregao = self.processos_widget.extrair_informacoes_item(new_item_text)
            
            # Adicionar o item ao novo CustomListWidget
            self.addItem(new_item_text)
            
            # Remover o item do CustomListWidget original
            source_list_widget = event.source()
            source_item = source_list_widget.currentItem()
            row = source_list_widget.row(source_item)
            source_list_widget.takeItem(row)
            
            print("Item sendo adicionado:", new_item_text)
            nova_etapa = self.objectName()
            print("Nova Etapa:", nova_etapa)

            # Atualizar a etapa do processo no DataFrame
            # self.processos_widget.atualizar_etapa_processo(mod, num_pregao, ano_pregao, nova_etapa)
            
            # Chamada à função que estava faltando
            self.processos_widget.processar_mudanca_etapa(new_item_text, nova_etapa)

            event.acceptProposedAction()

            # Reordenar os itens na lista
            self.sortListItems()




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

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        exibir_detalhes_action = context_menu.addAction("Exibir Detalhes")
        action = context_menu.exec(self.mapToGlobal(event.pos()))

        if action == exibir_detalhes_action:
            item_selecionado = self.currentItem()
            if item_selecionado:
                mod, num_pregao, ano_pregao = self.processos_widget.extrair_informacoes_item(item_selecionado.text())
                processo_info = self.processos_widget.obter_info_processo(mod, num_pregao, ano_pregao)
                if processo_info:
                    detalhes_dialog = DetalhesProcessoDialog(processo_info, self.processos_widget)
                    detalhes_dialog.etapa_atualizada.connect(self.processos_widget.atualizar_visualizacao)
                    detalhes_dialog.exec()

ETAPAS = [
    'Planejamento', 'Setor Responsável', 'IRP', 'Edital', 'Nota Técnica', 'CJACM', 
    'Recomendações AGU', 'Provisionamento', 'Impugnado', 'Sessão Pública', 'Em recurso', 
    'Homologado', 'Assinatura Contrato', 'Concluído'
]

class ProcessosWidget(QWidget):
    def atualizar_visualizacao(self):
        """Recarrega os dados e atualiza a visualização."""
        self.df_processos = self.carregar_dados_processos(CONTROLE_PROCESSOS_DIR, CONTROLE_DISPENSA_DIR)

        self.preencher_blocos()

    def createListWidgetForEtapa(self, etapa, row, col):
        # Criar e configurar o QLabel para o título da etapa
        label = QLabel(f"<b>{etapa}</b>")  # Usar diretamente o valor de 'etapa'
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)  # Ajustar o tamanho da fonte conforme necessário
        label.setFont(font)
        label.setWordWrap(True)  # Habilitar quebra de linha no título, se necessário

        # Adicionar o QLabel ao layout
        self.blocks_layout.addWidget(label, row * 2, col)

        # Criar CustomListWidget
        list_widget = CustomListWidget(self)
        list_widget.setObjectName(etapa)  # Atribuir o nome da etapa como identificador
        self.blocks_layout.addWidget(list_widget, row * 2 + 1, col)
        self.etapas[etapa] = list_widget

    def __init__(self, parent=None, controle_processos_path=None, controle_dispensa_path=None):
        super().__init__(parent)
        # Cria a label
        label_fases = QLabel("Fases do Processo")
        label_fases.setStyleSheet(get_transparent_title_style())
        
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(label_fases)  # Adicione a label ao layout
        self.current_selection = None
        self.df_processos = self.carregar_dados_processos(controle_processos_path, controle_dispensa_path)
        self.criar_widgets_processos()
        self.preencher_blocos()  # Certifique-se de que este método é chamado
        # Certifique-se de que controle_processos_path é o caminho correto do arquivo JSON
        self.verificar_e_atualizar_dias_etapas(str(PROCESSOS_JSON_PATH))

    def verificar_e_atualizar_dias_etapas(self, file_path):
        with open(file_path, 'r+', encoding='utf-8') as file:
            processos_json = json.load(file)
            atualizado = False

            for processo, dados in processos_json.items():
                for registro in dados.get('historico', []):
                    data_inicial_str = registro.get('data_inicial')
                    data_final_str = registro.get('data_final')
                    data_final_atual = data_final_str if data_final_str else datetime.today().strftime('%d-%m-%Y')

                    if data_inicial_str:
                        data_inicial = datetime.strptime(data_inicial_str, '%d-%m-%Y').date()
                        data_final = datetime.strptime(data_final_atual, '%d-%m-%Y').date()
                        dias_calculados = (data_final - data_inicial).days
                        if dias_calculados != registro['dias_na_etapa']:
                            registro['dias_na_etapa'] = dias_calculados
                            atualizado = True

            if atualizado:
                file.seek(0)
                json.dump(processos_json, file, indent=4, ensure_ascii=False)
                file.truncate()
                
    def showEvent(self, event):
        # Chama a função de atualização de dados toda vez que o widget é mostrado
        self.df_processos = self.carregar_dados_processos(CONTROLE_PROCESSOS_DIR, CONTROLE_DISPENSA_DIR)
        self.preencher_blocos()  # Atualiza os list widgets com os dados mais recentes
        super().showEvent(event)  # Chama o método de evento de exibição padrão

    def criar_widgets_processos(self):
        container_widget = QWidget()
        self.blocks_layout = QGridLayout(container_widget)
        self.etapas = {}

        for etapa in ETAPAS:
            self.adicionar_etapa(etapa)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setWidget(container_widget)
        self.layout.addWidget(scroll_area)

    def adicionar_etapa(self, etapa):
        row, col = self.calcular_posicao_grid(etapa)  # Chamada corrigida
        label = self.criar_label_etapa(etapa)
        list_widget = CustomListWidget(self)
        list_widget.setObjectName(etapa)
        self.blocks_layout.addWidget(label, row * 2, col)
        self.blocks_layout.addWidget(list_widget, row * 2 + 1, col)
        self.etapas[etapa] = list_widget

    def calcular_posicao_grid(self, etapa):
        # Calcular a posição no grid baseado no índice da etapa
        index = ETAPAS.index(etapa)  # Acesso correto à lista ETAPAS
        return index // 7, index % 7

    @staticmethod
    def criar_label_etapa(titulo):
        label = QLabel(f"<b>{titulo}</b>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Arial", 14))
        label.setWordWrap(True)
        
        return label
    
    def preencher_blocos(self):
        for list_widget in self.etapas.values():
            list_widget.clear()

        try:
            for etapa, list_widget in self.etapas.items():
                etapa_processos = self.df_processos[self.df_processos['etapa'] == etapa]

                for _, processo in etapa_processos.iterrows():
                    num_pregao = str(processo['num_pregao']).zfill(2)
                    ano_pregao = processo['ano_pregao']
                    mod = processo['mod']  # Supondo que 'mod' é uma coluna no seu DataFrame
                    texto = f"{mod} {num_pregao}/{ano_pregao}"  # Formato correto
                    item = QListWidgetItem(texto)
                    list_widget.addItem(item)

                list_widget.sortListItems()

        except KeyError as e:
            error_dialog = QMessageBox()
            error_dialog.setWindowTitle("Erro")
            error_dialog.setText(f"Erro: {e}. Feche o arquivo e tente novamente!!!")
            error_dialog.exec()

    def on_processo_selected(self, item):
        # Se já existe uma seleção e ela não é a atual, desmarcá-la
        if self.current_selection and self.current_selection is not item:
            self.current_selection.setSelected(False)

        # Atualiza a seleção atual
        self.current_selection = item
        selected_text = item.text()
        # Lógica para lidar com a seleção

    def manage_selection(self, item, list_widget):
        # Desmarca a seleção em todos os QListWidgets exceto o atual
        for etapa, lw in self.etapas.items():
            if lw != list_widget:
                # Encontra e desmarca o item selecionado em outros QListWidgets
                selected_items = lw.selectedItems()
                if selected_items:
                    selected_items[0].setSelected(False)

        # Atualiza a seleção atual
        self.current_selection = item
        self.on_processo_selected(item)

    def salvar_alteracoes_excel(self):
        try:
            self.df_processos.to_excel(CONTROLE_PROCESSOS_DIR, index=False)
            print("Alterações salvas com sucesso.")
        except Exception as e:
            QMessageBox.warning(self, 'Erro ao Salvar', f'Erro ao salvar as alterações no arquivo Excel: {e}')
            print(f"Erro ao salvar alterações: {e}")

    def solicitar_comentario(self):
        texto, ok = QInputDialog.getText(self, "Comentário sobre a Mudança de Etapa", 
                                        "Insira um comentário sobre a mudança:")
        return texto if ok else "Sem comentários fornecidos."

    def processar_mudanca_etapa(self, item_text, nova_etapa):
        mod, num_pregao, ano_pregao = self.extrair_informacoes_item(item_text)  # Desempacotar três valores
        chave_processo = f"{mod} {num_pregao}/{ano_pregao}"  # Usar 'mod' na chave

        processos_json = ler_arquivo_json(PROCESSOS_JSON_PATH)

        # Inicialize a chave do processo se ela não existir
        if chave_processo not in processos_json:
            processos_json[chave_processo] = {"etapas": {}, "historico": []}

        etapa_anterior = processos_json[chave_processo].get("etapa_atual", "Setor Responsável")

        dialogo_confirmado = False

        if nova_etapa == "IRP":
            dialogo_irp = DialogoIRP(self)
            if dialogo_irp.exec() == QDialog.DialogCode.Accepted:
                dados_irp = dialogo_irp.get_data()
                comentario = dados_irp  # ou algum campo específico de dados_irp
                dialogo_confirmado = True
            else:
                print("Operação cancelada pelo usuário.")
                self.atualizar_listas()  # Chama a função de atualização
                return  # Sai da função, não atualiza nada
        else:
            texto, ok = QInputDialog.getText(self, "Comentário sobre a Mudança de Etapa", "Insira um comentário sobre a mudança:")
            if ok:
                comentario = texto
                dialogo_confirmado = True
            else:
                print("Operação cancelada pelo usuário.")
                self.atualizar_listas()  # Chama a função de atualização
                return  # Sai da função, não atualiza nada

        if dialogo_confirmado:
            historico = processos_json[chave_processo].setdefault("historico", [])
            data_atual = datetime.today().date()

            # Atualiza a 'data final' da etapa anterior e calcula sua duração
            if historico:
                etapa_anterior_info = historico[-1]
                etapa_anterior_info["data_final"] = data_atual.strftime("%d-%m-%Y")
                data_inicial_anterior = datetime.strptime(etapa_anterior_info["data_inicial"], "%d-%m-%Y").date()
                etapa_anterior_info["dias_na_etapa"] = (data_atual - data_inicial_anterior).days

            # Adiciona uma nova entrada para a nova etapa
            historico.append({
                "etapa": nova_etapa,
                "data_inicial": data_atual.strftime("%d-%m-%Y"),
                "data_final": None,  # A ser preenchido quando a etapa mudar
                "dias_na_etapa": 0,  # Inicia com zero
                "comentario": comentario,
                "sequencial": len(historico) + 1
            })
            
            # Atualiza a etapa do processo e salva no Excel
            self.atualizar_etapa_processo(mod, num_pregao, ano_pregao, nova_etapa)  # Passe 'mod' como argumento adicional
            self.salvar_alteracoes_excel()
            self.atualizar_listas()  

            processos_json[chave_processo]["etapa_atual"] = nova_etapa
            escrever_arquivo_json(PROCESSOS_JSON_PATH, processos_json)

    def atualizar_listas(self):
        self.df_processos = self.carregar_dados_processos(CONTROLE_PROCESSOS_DIR, CONTROLE_DISPENSA_DIR)
        for etapa, list_widget in self.etapas.items():
            list_widget.clear() # Limpar a lista atual
            # Preencher cada lista com os dados atualizados
            for _, processo in self.df_processos[self.df_processos['etapa'] == etapa].iterrows():
                num_pregao = str(processo['num_pregao']).zfill(2)
                ano_pregao = processo['ano_pregao']
                mod = processo['mod']  # Supondo que 'mod' é uma coluna no seu DataFrame
                texto = f"{mod} {num_pregao}/{ano_pregao}"  # Usando 'mod' em vez de 'PE'
                item = QListWidgetItem(texto)
                list_widget.addItem(item)

    def atualizar_etapa_processo(self, mod, num_pregao, ano_pregao, nova_etapa):
        print(f"Atualizando etapa para {mod} {num_pregao}/{ano_pregao} para {nova_etapa}")
        condição = (self.df_processos['mod'] == mod) & \
                (self.df_processos['num_pregao'] == num_pregao) & \
                (self.df_processos['ano_pregao'] == ano_pregao)
        self.df_processos.loc[condição, 'etapa'] = nova_etapa
        print(f"DataFrame após atualização:\n{self.df_processos.loc[condição]}")

    def extrair_informacoes_item(self, item_text):
        partes = item_text.split(' ')
        mod = partes[0]
        num_pregao, ano_pregao = partes[1].split('/')
        num_pregao = int(num_pregao)
        ano_pregao = int(ano_pregao)
        return mod, num_pregao, ano_pregao
    
    def carregar_dados_processos(self, controle_processos_path, controle_dispensa_path):
        try:
            df_processos = pd.read_excel(controle_processos_path or CONTROLE_PROCESSOS_DIR)
            df_dispensa = pd.read_excel(controle_dispensa_path or CONTROLE_DISPENSA_DIR)

            # Preencher valores NaN na coluna 'etapa' com 'Setor Responsável' em ambos os DataFrames
            df_processos['etapa'] = df_processos['etapa'].fillna('Setor Responsável')
            df_dispensa['etapa'] = df_dispensa['etapa'].fillna('Setor Responsável')

            # Concatenar os DataFrames
            df_combinado = pd.concat([df_processos, df_dispensa], ignore_index=True)

            # Remover duplicatas, se necessário (ajuste conforme necessário)
            df_combinado = df_combinado.drop_duplicates(subset=['mod', 'num_pregao', 'ano_pregao'])

            if not df_combinado.empty:
                return df_combinado
            else:
                raise ValueError("Os arquivos Excel estão vazios ou não foram carregados corretamente.")
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Erro ao ler os arquivos Excel: {e}')
            return pd.DataFrame()


    def inicializar_json_do_excel(self, caminho_excel, caminho_json):
        if caminho_excel is None:
            print("Caminho do arquivo Excel não fornecido.")
            return
        df = pd.read_excel(caminho_excel)
        processos_json = {}

        for _, row in df.iterrows():
            chave_processo = f"PE {row['num_pregao']}/{row['ano_pregao']}"
            processos_json[chave_processo] = {
                "nup": row["nup"],
                "objeto": row["objeto"],
                "uasg": row["uasg"],
                "orgao_responsavel": row["orgao_responsavel"],
                "sigla_om": row["sigla_om"],
                "setor_responsavel": row["setor_responsavel"],
                "etapas": {}
            }

        with open(caminho_json, 'w', encoding='utf-8') as file:
            json.dump(processos_json, file, indent=4, ensure_ascii=False)

    def obter_info_processo(self, mod, num_pregao, ano_pregao):
        chave_processo = f"{mod} {num_pregao}/{ano_pregao}"  # Usando 'mod' na chave
        processos_json = ler_arquivo_json(PROCESSOS_JSON_PATH)
        processo_info = processos_json.get(chave_processo, None)
        if processo_info:
            return {"processo": chave_processo, "dados": processo_info}
        return None


class DialogoIRP(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        font = QFont()
        font.setPointSize(12)  # Definindo o tamanho da fonte para 12

        # Campo de entrada para o número do IRP
        self.numero_irp_edit = QLineEdit(self)
        self.numero_irp_edit.setFont(font)  # Configurando a fonte
        label_numero_irp = QLabel("1º Informe o número do IRP:")
        label_numero_irp.setFont(font)  # Configurando a fonte
        layout.addWidget(label_numero_irp)
        layout.addWidget(self.numero_irp_edit)

        # Calendário para a data limite da manifestação do IRP
        self.data_manifestacao_calendar = QCalendarWidget(self)
        label_manifestacao = QLabel("2º Informe a data limite da manifestação do IRP:")
        label_manifestacao.setFont(font)  # Configurando a fonte
        layout.addWidget(label_manifestacao)
        layout.addWidget(self.data_manifestacao_calendar)

        # Calendário para a data limite de confirmação do IRP
        self.data_confirmacao_calendar = QCalendarWidget(self)
        label_confirmacao = QLabel("3º Informe a data limite para confirmação do IRP:")
        label_confirmacao.setFont(font)  # Configurando a fonte
        layout.addWidget(label_confirmacao)
        layout.addWidget(self.data_confirmacao_calendar)

        # Configuração das datas padrão
        data_atual = QDate.currentDate()
        oito_dias_uteis = np.busday_offset(data_atual.toString("yyyy-MM-dd"), 8, roll='forward')
        tres_dias_uteis_apos_oito = np.busday_offset(oito_dias_uteis, 3, roll='forward')

        self.data_manifestacao_calendar.setSelectedDate(QDate.fromString(str(oito_dias_uteis), "yyyy-MM-dd"))
        self.data_confirmacao_calendar.setSelectedDate(QDate.fromString(str(tres_dias_uteis_apos_oito), "yyyy-MM-dd"))

        # Campo de entrada para a data/hora da mensagem de divulgação
        self.datahora_msg_divulgacao = QLineEdit(self)
        self.datahora_msg_divulgacao.setFont(font)  # Configurando a fonte
        label_datahora_msg = QLabel("4º Informe o datahora da MSG da divulgação:")
        label_datahora_msg.setFont(font)  # Configurando a fonte
        layout.addWidget(label_datahora_msg)
        layout.addWidget(self.datahora_msg_divulgacao)

        # Botões Confirmar e Cancelar
        botoes_layout = QHBoxLayout()
        self.botao_confirmar = QPushButton("Confirmar", self)
        self.botao_cancelar = QPushButton("Cancelar", self)
        self.botao_confirmar.setFont(font)  # Configurando a fonte
        self.botao_cancelar.setFont(font)  # Configurando a fonte
        botoes_layout.addWidget(self.botao_confirmar)
        botoes_layout.addWidget(self.botao_cancelar)
        layout.addLayout(botoes_layout)

        # Conectar sinais dos botões
        self.botao_confirmar.clicked.connect(self.accept)
        self.botao_cancelar.clicked.connect(self.reject)

    def get_data(self):
        return {
            "numero_irp": self.numero_irp_edit.text(),
            "data_manifestacao": self.data_manifestacao_calendar.selectedDate().toString("dd-MM-yyyy"),
            "data_confirmacao": self.data_confirmacao_calendar.selectedDate().toString("dd-MM-yyyy"),
            "datahora_msg_divulgacao": self.datahora_msg_divulgacao.text()  # Alterado para usar text()
        }

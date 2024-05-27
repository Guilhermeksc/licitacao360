from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from pathlib import Path
from gerar_atas_pasta.regex_termo_homolog import *
from gerar_atas_pasta.regex_sicaf import *
from gerar_atas_pasta.canvas_gerar_atas import *
from utils.treeview_utils import open_folder, load_images, create_button
from diretorios import *
import os
import pandas as pd
import pdfplumber
from modulo_ata_contratos.processar_homologacao import ProgressDialog
from modulo_ata_contratos.utils import create_button, load_icons, apply_standard_style, animate_blink, start_color_blink, update_background_color, start_blink_effect, stop_blink_effect
from modulo_ata_contratos.data_utils import DatabaseDialog, DocumentTableModel, PDFProcessingThread, atualizar_modelo_com_dados, save_to_dataframe, load_file_path, obter_arquivos_txt, ler_arquivos_txt

TXT_OUTPUT_PATH = DATABASE_DIR / "relacao_cnpj.txt"
NUMERO_ATA_GLOBAL = None
GERADOR_NUMERO_ATA = None
CSV_OUTPUT_PATH = DATABASE_DIR / "dados.csv"
tr_variavel_df_carregado = None

class GerarAtasWidget(QWidget):
    def __init__(self, icons_dir, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(icons_dir)
        self.buttons = {}
        self.tr_variavel_df_carregado = None 
        self.pdf_dir = Path(PDF_DIR)
        self.txt_dir = Path(TXT_DIR) 
        self.sicaf_dir = Path(SICAF_DIR)
        self.mapeamento_colunas = {
            "Item": "item_num",
            "Catálogo": "catalogo",
            "Descrição": "descricao_tr",
            "Descrição Detalhada": "descricao_detalhada",
            "UASG": "uasg",
            "Órgão Responsável": "orgao_responsavel",
            "Número": "num_pregao",
            "Ano": "ano_pregao",
            "SRP": "srp",
            "Objeto": "objeto",
            "Grupo": "grupo",
            "Valor Estimado": "valor_estimado",
            "Quantidade": "quantidade",
            "Unidade": "unidade",
            "Situação": "situacao",
            "Melhor Lance": "melhor_lance",
            "Valor Negociado": "valor_negociado",
            "Ordenador Despesa": "ordenador_despesa",
            "Empresa": "empresa",
            "CNPJ": "cnpj",
            "Marca Fabricante": "marca_fabricante",
            "Modelo Versão": "modelo_versao",
            "Valor Homologado": "valor_homologado_item_unitario",
            "Valor Estimado Total": "valor_estimado_total_do_item",
            "Valor Homologado Total": "valor_homologado_total_item",
            "Desconto (%)": "percentual_desconto"
        }

        self.setup_ui()
        self.progressDialog = ProgressDialog(self.pdf_dir, self)
        self.setup_pdf_processing_thread()
        self.current_dataframe = None
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.setup_alert_label()
        self.setup_buttons()
        self.setup_table()
        self.setLayout(self.main_layout)
        self.setMinimumSize(1200, 600)

    def setup_alert_label(self):
        icon_path = str(self.icons_dir / 'alert.png')  # Obtenha o caminho completo para o ícone
        # Utilize HTML para formatar parte do texto como negrito e sublinhado
        text = (f"<img src='{icon_path}' style='vertical-align: middle;' width='24' height='24'> "
                "Pressione '<b><u>Importar TR</u></b>' para adicionar os dados 'Catálogo', "
                "'Descrição' e 'Descrição Detalhada' do Termo de Referência. "
                f"<img src='{icon_path}' style='vertical-align: middle;' width='24' height='24'>")
        self.alert_label = QLabel(text)
        self.alert_label.setStyleSheet("color: white; font-size: 14pt; padding: 5px;")
        self.alert_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.alert_label)
        start_color_blink(self, self.alert_label)

    def setup_buttons(self):
        self.buttons_layout = QHBoxLayout()
        self.icons = load_icons(self.icons_dir)
        button_definitions = [
            ("Importar TR", 'stats', self.import_tr, "Adiciona um novo item ao banco de dados", True),
            ("Processar Homologação", 'data-collection', self.iniciar_processamento, "Salva o dataframe em um arquivo excel('.xlsx')", False),
            ("Processar SICAF", 'data-collection2', self.salvar_tabela, "Exclui um item selecionado", False),
            ("Database", 'data-processing', self.update_database, "Salva ou Carrega os dados do Database", False),            
            ("Configurações", 'management', self.open_settings_dialog, "Abre as configurações da aplicação", False),
        ]
        for name, icon_key, callback, tooltip, animate in button_definitions:
            icon = self.icons.get(icon_key, None)
            button = create_button(name, icon, callback, tooltip, QSize(40, 40), None, animate)
            self.buttons[name] = button
            self.buttons_layout.addWidget(button)
            if name == "Importar TR" and animate:
                start_blink_effect(button, interval_ms=100)
        self.main_layout.addLayout(self.buttons_layout)

    def setup_table(self):
        headers = list(self.mapeamento_colunas.keys())
        self.model = DocumentTableModel(headers)
        self.tableView = QTableView()
        self.tableView.setModel(self.model)
        self.main_layout.addWidget(self.tableView)
        self.tableView.setStyleSheet("QTableView { background-color: black; color: white; gridline-color: white; }")
        self.tableView.verticalHeader().setStyleSheet("color: white;") 

    def setup_pdf_processing_thread(self):
        self.processing_thread = PDFProcessingThread(self.pdf_dir, self.txt_dir)
        # Conectar apenas uma vez, no construtor
        self.processing_thread.progress_updated.connect(self.progressDialog.update_progress)
        self.processing_thread.processing_complete.connect(self.progressDialog.on_conversion_finished)

    def import_tr(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo", "", "Excel files (*.xlsx *.xls)")
        if arquivo:
            self.tr_variavel_df_carregado = pd.read_excel(arquivo)
            QMessageBox.information(self, "Arquivo Carregado", f"O arquivo '{QFileInfo(arquivo).fileName()}' foi carregado com sucesso!")
            atualizar_modelo_com_dados(self.model, self.tr_variavel_df_carregado, self.mapeamento_colunas, self.tableView)
            self.tableView.resizeColumnsToContents()
            # Atualizar o texto da alert_label
            icon_path = str(self.icons_dir / 'alert.png')
            new_text = (f"<img src='{icon_path}' style='vertical-align: middle;' width='24' height='24'> "
                        "Salve os Termos de Homologação na pasta correta e pressione '<b><u>Processar Homologação</u></b>' para processar os dados. "
                        f"<img src='{icon_path}' style='vertical-align: middle;' width='24' height='24'>")
            self.alert_label.setText(new_text)
            start_color_blink(self, self.alert_label)   
             
            # Mover o efeito de "blink" para o botão "Processar Homologação"
            stop_blink_effect(self.buttons["Importar TR"])
            start_blink_effect(self.buttons["Processar Homologação"])

    def iniciar_processamento(self):
        if not self.pdf_dir.exists():
            QMessageBox.warning(self, "Erro", "Pasta de PDFs não encontrada.")
            return
        total_files = len(list(self.pdf_dir.glob("*.pdf")))
        self.progressDialog = ProgressDialog(total_files, self.pdf_dir, self)
        self.progressDialog.processing_complete.connect(self.finalize_processing)
        self.progressDialog.show()

    def finalize_processing(self, extracted_data):
        self.current_dataframe = save_to_dataframe(extracted_data, self.tr_variavel_df_carregado, DATABASE_DIR, CSV_OUTPUT_PATH)
        if self.current_dataframe is not None:
            print("DataFrame resultante:\n", self.current_dataframe)
            self.update_table_with_dataframe(self.current_dataframe)
            print("Tabela atualizada com sucesso.")
        else:
            QMessageBox.warning(self, "Erro", "Falha ao salvar os dados.")

    def salvar_tabela(self):
        pass
    def open_settings_dialog(self):
        pass
    def generate_ata(self):
        pass

    def update_database(self):
        # Sempre permite abrir o diálogo, independente da presença de um DataFrame
        dialog = DatabaseDialog(self, self.current_dataframe, self.update_table_with_dataframe)
        dialog.exec()

    def update_progress(self, value):
        if self.progressDialog.isVisible():
            self.progressDialog.progressBar.setValue(value)
        else:
            # Caso a barra de progresso não esteja visível, você pode optar por mostrá-la aqui
            self.progressDialog.show()
            self.progressDialog.progressBar.setValue(value)

    def update_table_with_dataframe(self, dataframe):
        print("Atualizando a tabela com os dados do DataFrame...")
        headers_map = {v: k for k, v in self.mapeamento_colunas.items()}
        self.model.load_data(dataframe, headers_map)
        self.tableView.reset()
        self.tableView.resizeColumnsToContents()  # Ajusta as colunas para se adequarem ao conteúdo
        print("Tabela atualizada com sucesso.")

        # Lista de cabeçalhos das colunas que devem ser escondidas
        colunas_escondidas = ["Descrição Detalhada", "UASG", "Órgão Responsável", "Unidade", "Número", "Ano", "SRP", "Objeto", 
                            "Ordenador Despesa", "Melhor Lance", "Valor Negociado"]

        # Itera sobre todos os cabeçalhos e esconde as colunas especificadas
        for header in self.model.get_headers():
            if header in colunas_escondidas:
                column_index = self.model.get_headers().index(header)
                self.tableView.setColumnHidden(column_index, True)

        
# class GerarAtasWidget(QWidget):
#     def __init__(self, icons_dir, parent=None):
#         super().__init__(parent)

#         self.mapeamento_colunas = {
#             "Item": "item_num",
#             "Catálogo": "catalogo",
#             "Descrição": "descricao_tr",
#             "Descrição Detalhada": "descricao_detalhada_tr",
#             "UASG": "uasg",
#             "Órgão Responsável": "orgao_responsavel",
#             "Número": "num_pregao",
#             "Ano": "ano_pregao",
#             "SRP": "srp",
#             "Objeto": "objeto",
#             "Grupo": "grupo",
#             "Valor Estimado": "valor_estimado",
#             "Quantidade": "quantidade",
#             "Unidade": "unidade",
#             "Situação": "situacao",
#             "Melhor Lance": "melhor_lance",
#             "Valor Negociado": "valor_negociado",
#             "Ordenador Despesa": "ordenador_despesa",
#             "Empresa": "empresa",
#             "CNPJ": "cnpj",
#             "Marca Fabricante": "marca_fabricante",
#             "Modelo Versão": "modelo_versao",
#             "Valor Homologado do Item": "valor_homologado_item_unitario",
#             "Valor Estimado Total do Item": "valor_estimado_total_do_item",
#             "Valor Homologado Total do Item": "valor_homologado_total_item",
#             "Percentual Desconto": "percentual_desconto"
#         }
        
#         self.pdf_dir = PDF_DIR  # Já existente para PDF_DIR
#         self.sicaf_dir = SICAF_DIR  # Adicionando para SICAF_DIR

#         global_event_manager.pdf_dir_updated.connect(self.on_pdf_dir_updated)
#         global_event_manager.sicaf_dir_updated.connect(self.on_sicaf_dir_updated)

#         self.icons_dir = Path(icons_dir)

#         self.image_cache = load_images(self.icons_dir, [
#             "stats.png", "table.png", "data-processing.png", "performance.png", 
#             "data-collection.png", "data-collection2.png", "calendar.png", 
#             "report.png", "management.png", "alert.png", "relatorio.png"
#         ])

#         self.tr_variavel_df_carregado = None
#         self.nome_arquivo_carregado = ""
#         self.botoes = []  # Inicializando a lista de botões
#         self.setup_ui()
#         self.setMinimumSize(1200, 600)  # Define o tamanho mínimo da janela para 1200x600

#         self.tr_df_carregado = None
#         arquivo_salvo = self.load_file_path()
#         try:
#             if arquivo_salvo:
#                 self.tr_variavel_df_carregado = pd.read_excel(arquivo_salvo)
#                 self.nome_arquivo_carregado = os.path.basename(arquivo_salvo)
#             else:
#                 raise FileNotFoundError
#         except FileNotFoundError:
#             self.nome_arquivo_carregado = ""
#             print("Arquivo não encontrado.")

#         self.progressDialog = None
#         self.sicafDialog = None
#         self.atasDialog = None

#         headers = list(self.mapeamento_colunas.keys())
#         self.model = DocumentTableModel(headers)
#         self.tableView.setModel(self.model)

#     def on_pdf_dir_updated(self, new_pdf_dir):
#         # Atualiza a variável local com o novo caminho do diretório PDF
#         self.pdf_dir = new_pdf_dir

#     def on_sicaf_dir_updated(self, new_sicaf_dir):
#         self.sicaf_dir = new_sicaf_dir

#     def setup_ui(self):
#         self.main_layout = QVBoxLayout(self)
#         self.setup_alert_label()
#         self.setup_buttons_layout()
#         self.update_button_highlight()
#         self.start_color_blink()

#         self.tableView = QTableView(self)
#         self.model = DocumentTableModel(list(self.mapeamento_colunas.keys()))
#         self.tableView.setModel(self.model)
#         self.tableView.setStyleSheet("""
#         QTableView {
#             background-color: black;
#             color: white;
#             font-size: 12pt;
#             border: 1px solid black;
#         }
#         QHeaderView::section {
#             background-color: #333;
#             padding: 4px;
#             border: 0.5px solid #dcdcdc;
#             color: white;
#             font-size: 12pt;
#         }
#         """)
#         QTimer.singleShot(1, self.adjust_columns)
#         self.tableView.verticalHeader().setVisible(False)

#         self.main_layout.addWidget(self.tableView)
#         self.setup_buttons_down_layout()
#         self.setLayout(self.main_layout)

#     def adjust_columns(self):
#         """Ajusta as larguras das colunas do QTableView."""
#         header = self.tableView.horizontalHeader()
#         for i in range(self.model.columnCount()):
#             header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

#         # Ajusta especificamente a coluna "Descrição" para se adaptar ao conteúdo
#         descricao_index = self.model.get_headers().index("Descrição") if "Descrição" in self.model.get_headers() else -1
#         if descricao_index != -1:
#             header.setSectionResizeMode(descricao_index, QHeaderView.ResizeMode.ResizeToContents)

#         # Oculta a coluna "Descrição Detalhada"
#         descricao_detalhada_index = self.model.get_headers().index("Descrição Detalhada") if "Descrição Detalhada" in self.model.get_headers() else -1
#         if descricao_detalhada_index != -1:
#             self.tableView.setColumnHidden(descricao_detalhada_index, True)

#     def setup_alert_label(self):
#         self.alert_label = QLabel("Pressione 'Importar TR' para adicionar os dados 'Catálogo', 'Descrição' e 'Descrição Detalhada'  do Termo de Referência.")
#         self.alert_label.setStyleSheet("color: white; font-size: 14pt; padding: 5px;")
#         self.alert_label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
#         self.main_layout.addWidget(self.alert_label)
#         self.update_button_highlight()  

#     def start_color_blink(self):
#         # Animação que alterna as cores de fundo entre azul marinho e preto
#         self.color_animation = QVariantAnimation(self)
#         self.color_animation.setStartValue(QColor(0, 0, 128))  # Azul marinho
#         self.color_animation.setEndValue(QColor(0, 0, 0))  # Preto
#         self.color_animation.setDuration(1000)  # Duração de 1 segundo
#         self.color_animation.setLoopCount(-1)  # Loop infinito
#         self.color_animation.setEasingCurve(QEasingCurve.Type.InOutSine)  # Efeito suave de entrada e saída
#         self.color_animation.valueChanged.connect(self.update_background_color)
#         self.color_animation.start()

#     def update_background_color(self, color):
#         # Aplica a cor de fundo animada à label
#         self.alert_label.setStyleSheet(f"background-color: {color.name()}; color: white; font-size: 14pt; padding: 5px;")

#     def setup_buttons_layout(self):
#         self.buttons_layout = QHBoxLayout()
#         self.create_buttons()
#         self.main_layout.addLayout(self.buttons_layout)

#     def create_buttons(self):
#         buttons_layout = QHBoxLayout()  # Cria uma nova instância local
#         icon_size = QSize(40, 40)  # Tamanho do ícone para todos os botões

#         # Criar e adicionar botões individualmente à lista de botões e ao layout
#         import_tr_button = self.create_button("Importar TR", self.image_cache['stats'], self.import_tr, "Adiciona um novo item ao banco de dados", icon_size)
#         self.botoes.append(import_tr_button)
#         buttons_layout.addWidget(import_tr_button)

#         process_homolog_button = self.create_button("Processar Homologação", self.image_cache['data-collection'], self.iniciar_processamento, "Salva o dataframe em um arquivo excel('.xlsx')", icon_size)
#         self.botoes.append(process_homolog_button)
#         buttons_layout.addWidget(process_homolog_button)

#         process_sicaf_button = self.create_button("Processar SICAF", self.image_cache['data-collection2'], self.salvar_tabela, "Exclui um item selecionado", icon_size)
#         self.botoes.append(process_sicaf_button)
#         buttons_layout.addWidget(process_sicaf_button)

#         settings_button = self.create_button("Configurações", self.image_cache['management'], self.open_settings_dialog, "Abre as configurações da aplicação", icon_size)
#         self.botoes.append(settings_button)
#         buttons_layout.addWidget(settings_button)

#         # Adiciona o layout dos botões ao layout principal
#         self.main_layout.addLayout(buttons_layout)  # Adiciona a nova instância ao layout principal

#     def iniciar_processamento(self):
#         # Verifica se o termo de referência foi carregado
#         if self.tr_variavel_df_carregado is None:
#             QMessageBox.warning(self, "Atenção", "Carregue o termo de referência antes de processar os termos de homologação!")
#             return  # Interrompe a execução adicional deste método

#         pdf_files = list(self.pdf_dir.glob("*.pdf"))
#         total_files = len(pdf_files)

#         # Verifica se já existe um ProgressDialog aberto
#         if self.progressDialog is None or not self.progressDialog.isVisible():
#             # Se o arquivo foi carregado, cria o popup de progresso
#             self.progressDialog = ProgressDialog(total_files, self.start_pdf_conversion, self.pdf_dir, self)
#             self.progressDialog.show()
#         else:
#             # Opcional: Traga o diálogo existente para o primeiro plano
#             self.progressDialog.raise_()
#             self.progressDialog.activateWindow()

#     def create_button(self, text, icon, callback, tooltip_text, icon_size=QSize(40, 40)):
#         btn = QPushButton(text, self)
#         if icon:
#             btn.setIcon(QIcon(icon))
#             btn.setIconSize(icon_size)  # Define o tamanho do ícone
#         btn.clicked.connect(callback)
#         btn.setToolTip(tooltip_text)
#         btn.setObjectName(text.replace(" ", "_") + "_Button")  # Nomeia o objeto para referência fácil

#         # Estilo inicial padrão
#         btn.setStyleSheet("""
#         QPushButton {
#             background-color: black;
#             color: white;
#             font-size: 14pt;
#             min-height: 35px;
#             padding: 5px;      
#         }
#         QPushButton:hover {
#             background-color: white;
#             color: black;
#         }
#         QPushButton:pressed {
#             background-color: #ddd;
#             color: black;
#         }
#         """)
#         return btn

#     def update_button_highlight(self):
#         # Resetar os estilos de todos os botões para o padrão
#         for btn in self.botoes:
#             btn.setStyleSheet("""
#             QPushButton {
#                 background-color: black;
#                 color: white;
#                 font-size: 14pt;
#                 min-height: 35px;
#                 padding: 5px;
#             }
#             QPushButton:hover {
#                 background-color: white;
#                 color: black;
#             }
#             QPushButton:pressed {
#                 background-color: #ddd;
#                 color: black;
#             }
#             """)

#         # Encontrar e destacar o botão correspondente
#         if "Importar TR" in self.alert_label.text():
#             button_to_highlight = self.findChild(QPushButton, "Importar_TR_Button")
#         elif "Processar Homologação" in self.alert_label.text():
#             button_to_highlight = self.findChild(QPushButton, "Processar_Homologação_Button")
#         else:
#             return  # Se não for um dos casos, não fazer nada

#         if button_to_highlight:
#             button_to_highlight.setStyleSheet("""
#             QPushButton {
#                 background-color: #000020;
#                 color: white;
#                 font-size: 14pt;
#                 min-height: 35px;
#                 padding: 5px;
#                 border: 1px solid white;
#             }
#             QPushButton:hover {
#                 background-color: #0000CD;
#                 color: white;
#             }
#             QPushButton:pressed {
#                 background-color: #00008B;
#                 color: white;
#             }
#             """)


#     def setup_buttons_down_layout(self):
#         self.buttons_layout = QHBoxLayout()
#         self.create_buttons_down()
#         self.main_layout.addLayout(self.buttons_layout)

#     def create_buttons_down(self):
#         self.buttons_layout = QHBoxLayout()
#         icon_size = QSize(40, 40)  # Tamanho do ícone para todos os botões
#         self.button_specs = [
#             ("Carregar DB", self.image_cache['table'], self.import_tr, "Adiciona um novo item ao banco de dados", icon_size),
#             ("Gerar Ata/Contrato", self.image_cache['data-processing'], self.salvar_tabela, "Salva o dataframe em um arquivo excel('.xlsx')", icon_size),
#             ("Indicador NORMCEIM", self.image_cache['performance'], self.salvar_tabela, "Exclui um item selecionado", icon_size),
#             ("Relatório", self.image_cache['relatorio'], self.open_settings_dialog, "Abre as configurações da aplicação", icon_size),            
#         ]

#         for text, icon, callback, tooltip, icon_size in self.button_specs:
#             btn = create_button(text=text, icon=icon, callback=callback, tooltip_text=tooltip, parent=self, icon_size=icon_size)
#             self.buttons_layout.addWidget(btn)

#     def salvar_tabela(self):
#         pass    

#     def open_settings_dialog(self):
#         pass

#     def load_data(self):
#         # Retorna um DataFrame vazio para inicialização
#         return pd.DataFrame()
    
#     def import_tr(self):
#         arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo", "", "Excel files (*.xlsx *.xls)")
#         if arquivo:
#             self.tr_df_carregado = pd.read_excel(arquivo)
#             QMessageBox.information(self, "Arquivo Carregado", f"O arquivo '{os.path.basename(arquivo)}' foi carregado com sucesso!")
#             self.atualizar_modelo_com_dados()
#             self.alert_label.setText("Salve os Termos de Homologação na pasta correta e pressione 'Processar Homologação' para processar os dados.")
#             self.update_button_highlight()  # Atualiza o destaque para o próximo botão relevante
            
#     def button_clicked(self, index):
#         if index == 0:  # Primeiro botão
#             self.selecionar_termo_de_referencia_e_carregar()
#         elif index == 1:  # Segundo botão
#             convert_pdf_to_txt(self.pdf_dir, TXT_DIR, self.progress_bar_homolog)

#     def selecionar_termo_de_referencia_e_carregar(self):
#         arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo", "", "Excel files (*.xlsx *.xls)")
#         if arquivo:
#             self.tr_df_carregado = pd.read_excel(arquivo)
#             QMessageBox.information(self, "Arquivo Carregado", f"O arquivo '{os.path.basename(arquivo)}' foi carregado com sucesso!")

#     def atualizar_modelo_com_dados(self):
#         if self.tr_df_carregado is not None:
#             # Verifica se todas as colunas mapeadas estão no DataFrame e adiciona se faltarem
#             for key, value in self.mapeamento_colunas.items():
#                 if value not in self.tr_df_carregado.columns:
#                     self.tr_df_carregado[value] = pd.NA  # Utiliza pd.NA para suportar tipos de dados adequados

#             # Cria um novo DataFrame apenas com as colunas mapeadas
#             dados_filtrados = self.tr_df_carregado[list(self.mapeamento_colunas.values())]
#             self.model = DocumentTableModel(headers=list(self.mapeamento_colunas.keys()), dados_filtrados=dados_filtrados)
#             self.tableView.setModel(self.model)
#             self.adjust_columns()

#     def save_file_path(self, file_path):
#         settings = QSettings("SuaEmpresa", "SeuApp")
#         settings.setValue("termo_referencia_arquivo", file_path)

#     # Use QSettings para carregar o caminho do arquivo
#     def load_file_path(self):
#         settings = QSettings("SuaEmpresa", "SeuApp")
#         return settings.value("termo_referencia_arquivo", "")

#     def load_settings(self):
#         settings = QSettings("SuaEmpresa", "SeuApp")
#         self.nome_arquivo_carregado = settings.value("termo_referencia_arquivo", "")

#     def reset_arquivo_carregado(self):
#         self.nome_arquivo_carregado = ""
#         self.tr_variavel_df_carregado = None
#         # Aqui, você também pode salvar o estado resetado nas configurações, se necessário
#         self.save_file_path("")

#     def iniciar_processamento(self):
#         # Verifica se o termo de referência foi carregado
#         if self.tr_variavel_df_carregado is None:
#             QMessageBox.warning(self, "Atenção", "Carregue o termo de referência antes de processar os termos de homologação!")
#             return  # Interrompe a execução adicional deste método

#         pdf_files = list(self.pdf_dir.glob("*.pdf"))
#         total_files = len(pdf_files)

#         # Verifica se já existe um ProgressDialog aberto
#         if self.progressDialog is None or not self.progressDialog.isVisible():
#             # Se o arquivo foi carregado, cria o popup de progresso
#             self.progressDialog = ProgressDialog(total_files, self.start_pdf_conversion, self.pdf_dir, self)
#             self.progressDialog.show()
#         else:
#             # Opcional: Traga o diálogo existente para o primeiro plano
#             self.progressDialog.raise_()
#             self.progressDialog.activateWindow()

#     def start_pdf_conversion(self):
#         arquivo_salvo = self.load_file_path()
#         if not arquivo_salvo or not os.path.exists(arquivo_salvo):
#             QMessageBox.warning(self, "Erro", "Arquivo não encontrado. Por favor, carregue o termo de referência novamente.")
#             return
        
#         # Verifica se o termo de referência foi carregado
#         if self.tr_variavel_df_carregado is None:
#             QMessageBox.warning(self, "Atenção", "Carregue o termo de referência antes de processar os termos de homologação!")
#             self.progressDialog.close()  # Fecha a janela de diálogo de progresso
#             return  # Interrompe a execução adicional deste método

#         # Se o arquivo foi carregado, inicia o processamento
#         self.progressDialog.confirmButton.setDisabled(True)
#         convert_pdf_to_txt(self.pdf_dir, TXT_DIR, self.progressDialog)
#         self.save_to_dataframe()
#         self.progressDialog.close()
#         # Exibe uma mensagem de conclusão
#         QMessageBox.information(self, "Conclusão", "O processamento dos dados foi concluído com sucesso!")

#     def get_content_widget(self):
#         return self

#     def save_to_dataframe(self):
#         # Inicializa um DataFrame vazio
#         df = pd.DataFrame()
#         df = self.create_dataframe_from_txt_files(str(TXT_DIR), padrao_1, padrao_grupo2, padrao_item2, padrao_3, padrao_4, df)
        
#         # Verifica se o DataFrame carregado está disponível
#         if self.tr_variavel_df_carregado is not None:
#             tr_variavel_df = self.tr_variavel_df_carregado
#         else:
#             QMessageBox.warning(self, "Aviso", "Nenhum DataFrame de termo de referência carregado.")
#             return
        
#         # Atualiza o DataFrame com as informações
#         merged_df = pd.merge(df, tr_variavel_df, on='item_num', how='outer')

#         # Imprime o DataFrame combinado no console
#         print("DataFrame combinado:\n", merged_df)

#         # Salva os DataFrames como arquivos
#         EXCEL_OUTPUT_PATH = DATABASE_DIR / "relatorio.xlsx"
#         merged_df.to_excel(EXCEL_OUTPUT_PATH, index=False, engine='openpyxl')
#         merged_df.to_csv(CSV_OUTPUT_PATH, index=False, encoding='utf-8-sig')
#         # Retorna o DataFrame combinado
#         return merged_df

#     def create_dataframe_from_txt_files(self, txt_directory: str, padrao_1: str, padrao_grupo2: str, padrao_item2: str, padrao_3: str, padrao_4: str, dataframe_licitacao: pd.DataFrame):
#         txt_files = obter_arquivos_txt(txt_directory)
#         all_data = []
        
#         for txt_file in txt_files:
#             content = ler_arquivos_txt(txt_file)
#             uasg_pregao_data = extrair_uasg_e_pregao(content, padrao_1, padrao_srp, padrao_objeto)
#             items_data = identificar_itens_e_grupos(content, padrao_grupo2, padrao_item2, padrao_3, padrao_4, dataframe_licitacao)
            
#             for item in items_data:
#                 all_data.append({
#                     **uasg_pregao_data,
#                     **item
#                 })

#         dataframe_licitacao = pd.DataFrame(all_data)
        
#         # Verificação da coluna 'item_num'
#         if "item_num" not in dataframe_licitacao.columns:
#             raise ValueError("A coluna 'item_num' não foi encontrada no DataFrame.")
        
#         dataframe_licitacao = dataframe_licitacao.sort_values(by="item_num")
#         self.save_dataframe_as_excel(dataframe_licitacao, BASE_DIR / "excel.xlsx")
                                
#         return dataframe_licitacao
    
#     def save_dataframe_as_excel(self, df: pd.DataFrame, output_path: str):
#         df.to_excel(output_path, index=False, engine='openpyxl')

#     def processar_arquivos_txt(self):
#         try:
#             df = self.create_dataframe_from_txt_files(str(TXT_DIR), padrao_1, padrao_grupo2, padrao_item2, padrao_3, padrao_4, pd.DataFrame())
#             QMessageBox.information(self, "Processamento Concluído", "DataFrame criado e salvo com sucesso.")
#         except Exception as e:
#             QMessageBox.critical(self, "Erro", f"Ocorreu um erro durante o processamento: {str(e)}")
    

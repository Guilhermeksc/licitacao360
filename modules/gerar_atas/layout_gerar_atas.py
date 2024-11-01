from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from pathlib import Path
from modules.gerar_atas.regex_termo_homolog import *
from modules.gerar_atas.regex_sicaf import *
from modules.gerar_atas.processar_homologacao import ProgressDialog
from modules.gerar_atas.processar_sicaf import SICAFDialog
from modules.gerar_atas.relatorio_indicadores import RelatorioIndicadores
from modules.gerar_atas.utils import create_button, load_icons, apply_standard_style, limpar_quebras_de_linha
from modules.gerar_atas.data_utils import DatabaseDialog, PDFProcessingThread, atualizar_modelo_com_dados, save_to_dataframe, load_file_path, obter_arquivos_txt, ler_arquivos_txt
from modules.gerar_atas.canvas_gerar_atas import criar_pastas_com_subpastas, abrir_pasta, gerar_soma_valor_homologado, inserir_relacao_empresa, inserir_relacao_itens, adicione_texto_formatado
from modules.gerar_atas.dialog_gerar_atas import AtasDialog
from diretorios import *
import pandas as pd
import numpy as np
from modules.planejamento.utilidades_planejamento import DatabaseManager
from openpyxl import load_workbook
import random

NUMERO_ATA_GLOBAL = None
GERADOR_NUMERO_ATA = None

class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cnpj = ""

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return

        item = self.model().itemFromIndex(index)
        if item and " - " in item.text():
            # Usar QTextDocument para extrair texto puro a partir do HTML
            doc = QTextDocument()
            doc.setHtml(item.text())
            plain_text = doc.toPlainText()

            # Extração do CNPJ sem HTML
            if " - " in plain_text:
                self.cnpj = plain_text.split(' - ')[0]

            menu = QMenu(self)
            copyAction = QAction(f"Copiar CNPJ {self.cnpj}", self)
            copyAction.triggered.connect(lambda: self.copy_cnpj(plain_text))
            menu.addAction(copyAction)
            menu.exec(event.globalPos())

    def copy_cnpj(self, text):
        if " - " in text:
            self.cnpj = text.split(' - ')[0]  # Extrai o CNPJ
        QApplication.clipboard().setText(self.cnpj)
        QToolTip.showText(QCursor.pos(), f"CNPJ {self.cnpj} copiado para área de transferência", self)

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid() and event.button() == Qt.MouseButton.LeftButton:
            # Expande ou colapsa o item clicado
            self.setExpanded(index, not self.isExpanded(index))
            
            # Se o item foi expandido, expanda também o primeiro nível de subitens
            if self.isExpanded(index):
                model = self.model()
                numRows = model.rowCount(index)
                for row in range(numRows):
                    childIndex = model.index(row, 0, index)
                    self.setExpanded(childIndex, True)
                    # Colapsa todos os subníveis abaixo do primeiro nível
                    self.collapseAllChildren(childIndex)

        super().mousePressEvent(event)

    def collapseAllChildren(self, parentIndex):
        """Recursivamente colapsa todos os subníveis de um dado índice."""
        model = self.model()
        numRows = model.rowCount(parentIndex)
        for row in range(numRows):
            childIndex = model.index(row, 0, parentIndex)
            self.collapseAllChildren(childIndex)
            self.setExpanded(childIndex, False)
class GerarAtasWidget(QWidget):
    def __init__(self, icons_dir, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(icons_dir)
        self.buttons = {}
        self.tr_variavel_df_carregado = None 
        # Diretórios configurados
        self.pdf_dir = Path(PDF_DIR)
        self.txt_dir = Path(TXT_DIR)
        self.sicaf_dir = Path(SICAF_DIR)
        self.sicaf_txt_dir = Path(SICAF_TXT_DIR)
            
        self.mapeamento_colunas = self.obter_mapeamento_colunas()
        self.current_dataframe = None
        self.pe_pattern = None
        self.setup_ui()
        self.progressDialog = ProgressDialog(self.pdf_dir, self)
        self.setup_pdf_processing_thread()        
        self.db_manager = DatabaseManager(CONTROLE_DADOS)

    def verificar_ou_criar_diretorios(self, diretorios):
        for diretorio in diretorios:
            if not diretorio.exists():
                diretorio.mkdir(parents=True, exist_ok=True)

    def obter_mapeamento_colunas(self):
        return {
            "Grupo": "grupo",
            "Item": "item_num",
            "Catálogo": "catalogo",
            "Descrição": "descricao_tr",
            "Descrição Detalhada": "descricao_detalhada",
            "Unidade": "unidade",
            "Quantidade": "quantidade",
            "Valor Estimado": "valor_estimado",
            "Valor Homologado": "valor_homologado_item_unitario",
            "Desconto (%)": "percentual_desconto",
            "Valor Estimado Total": "valor_estimado_total_do_item",
            "Valor Homologado Total": "valor_homologado_total_item",
            "Marca Fabricante": "marca_fabricante",
            "Modelo Versão": "modelo_versao",
            "UASG": "uasg",
            "Órgão Responsável": "orgao_responsavel",
            "Número": "num_pregao",
            "Ano": "ano_pregao",
            "SRP": "srp",
            "Objeto": "objeto",
            "Situação": "situacao",
            "Melhor Lance": "melhor_lance",
            "Valor Negociado": "valor_negociado",
            "Ordenador Despesa": "ordenador_despesa",
            "Empresa": "empresa",
            "CNPJ": "cnpj",
            "Endereço": "endereco",
            "CEP": "cep",
            "Município": "municipio",
            "Telefone": "telefone",
            "Email": "email",
            "Responsável Legal": "responsavel_legal"
        }
    
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        # Configurar o alerta com tamanho mínimo
        self.setup_alert_label()

        # Configurar os botões
        self.setup_buttons_up()

        # Adicionar um widget vazio que atuará como um espaçador no topo
        spacer_top = QWidget()
        spacer_top.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.main_layout.addWidget(spacer_top)

        # Definir a mensagem aleatória
        self.message_label = QLabel(self.obter_mensagem_aleatoria())
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("font-size: 16pt; font-style: italic; padding: 20px;")

        # Definir um tamanho fixo para a área onde o message_label ou treeView será exibido
        self.fixed_area_widget = QWidget()
        self.fixed_area_layout = QVBoxLayout(self.fixed_area_widget)
        self.fixed_area_layout.addWidget(self.message_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Garantir que o fixed_area_widget ocupe o máximo de espaço disponível
        self.main_layout.addWidget(self.fixed_area_widget)
        self.fixed_area_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Adicionar um widget vazio que atuará como um espaçador na parte inferior
        spacer_bottom = QWidget()
        spacer_bottom.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.main_layout.addWidget(spacer_bottom)

        # Setup da parte inferior dos botões
        self.setup_buttons_down()

        self.setLayout(self.main_layout)
        self.setMinimumSize(1000, 580)

    def obter_mensagem_aleatoria(self):
        # Mensagens possíveis
        mensagens = [
            "Simplicidade é o último degrau da sabedoria\n(Khalil Gibran)",
            "Explícito é melhor que implícito.\n\nSimples é melhor que complexo.\n\nComplexo é melhor que complicado.\n\n(Zen do Python)",
            "Special cases aren't special enough to break the rules.\n\nAlthough practicality beats purity.\n\nErrors should never pass silently.\n\n(Zen of Python)",
            "Diante da ambiguidade, recuse a tentação de adivinhar.\n\nDeve haver uma — e preferencialmente apenas uma — maneira óbvia de fazer algo.\n\n(Zen do Python)",
            "Agora é melhor do que nunca.\n\nEmbora nunca frequentemente seja melhor do que agora.\n\nSe a implementação é difícil de explicar, é uma má ideia.\n\nSe a implementação é fácil de explicar, pode ser uma boa ideia.\n\n(Zen do Python)",
        ]
        
        # Probabilidades associadas a cada mensagem
        probabilidades = [0.2, 0.2, 0.2, 0.2, 0.2]  # Ajuste as probabilidades conforme necessário

        # Seleciona uma mensagem com base nas probabilidades
        return random.choices(mensagens, probabilidades)[0]

    def setup_treeview(self):
        # Remover ou ocultar a mensagem quando o treeView for exibido
        if hasattr(self, 'message_label') and self.message_label:
            self.message_label.hide()

        # Verificar se o modelo já foi inicializado
        if not hasattr(self, 'model') or self.model is None:
            self.model = QStandardItemModel()  # Inicializando o modelo se ainda não foi inicializado

        # Criar e configurar o treeView
        self.treeView = CustomTreeView()
        self.treeView.setModel(self.model)

        # Verificar se o fixed_area_layout existe e é válido antes de tentar modificar
        if hasattr(self, 'fixed_area_layout') and self.fixed_area_layout is not None:
            while self.fixed_area_layout.count():
                widget_to_remove = self.fixed_area_layout.takeAt(0).widget()
                if widget_to_remove is not None:
                    widget_to_remove.deleteLater()

        # Adicionar o treeView na área fixa
        self.fixed_area_layout.addWidget(self.treeView)

        self.treeView.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.treeView.setAnimated(True)  # Facilita a visualização da expansão/colapso
        self.treeView.setUniformRowHeights(True)  # Uniformiza a altura das linhas      
        self.treeView.setItemsExpandable(True)  # Garantir que o botão para expandir esteja visível
        self.treeView.setExpandsOnDoubleClick(False)  # Evita a expansão por duplo clique
        self.setup_treeview_styles()

    def setup_alert_label(self):
        icon_path = str(self.icons_dir / 'alert.png')
        text = (f"<img src='{icon_path}' style='vertical-align: middle;' width='24' height='24'> "
                "Pressione '<b><u>Termo de Referência</u></b>' para adicionar os dados 'Catálogo', "
                "'Descrição' e 'Descrição Detalhada' do Termo de Referência. "
                f"<img src='{icon_path}' style='vertical-align: middle;' width='24' height='24'>")
        self.alert_label = QLabel(text)
        self.alert_label.setStyleSheet("font-size: 12pt; padding: 5px;")
        self.alert_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.alert_label)
        self.atasDialog = None

    def setup_buttons_generic(self, button_definitions):
        buttons_layout = QHBoxLayout()
        self.icons = load_icons(self.icons_dir)
        for name, icon_key, callback, tooltip, animate in button_definitions:
            icon = self.icons.get(icon_key, None)
            button = create_button(name, icon, callback, tooltip, QSize(30, 30), QSize(120, 30), None)
            self.buttons[name] = button
            buttons_layout.addWidget(button)
        return buttons_layout

    def setup_buttons_up(self):
        button_definitions = self.obter_definicoes_botoes()
        self.main_layout.addLayout(self.setup_buttons_generic(button_definitions))

    def setup_buttons_down(self):
        button_definitions = self.obter_definicoes_botoes_embaixo()
        self.main_layout.addLayout(self.setup_buttons_generic(button_definitions))

    def obter_definicoes_botoes(self):
        return [
            ("Tabela Vazia", 'add-task', self.tabela_vazia, "Importe um arquivo .xlsx com 4 colunas com índice 'item_num', 'catalogo', 'descricao_tr' e 'descricao_detalada'.", True),
            ("Termo de Referência", 'priority', self.import_tr, "Importe um arquivo .xlsx com 4 colunas com índice 'item_num', 'catalogo', 'descricao_tr' e 'descricao_detalada'.", True),
            ("Termo de Homologação", 'data-collection', self.processar_homologacao, "Faça o download dos termos de homologação e mova para a pasta de processamento dos Termos de Homologação", False),
            ("SICAF", 'sicaf', self.processar_sicaf, "Faça o download do SICAF (Nível I - Credenciamento) e mova para a pasta de processamento do SICAF", False),
        ]

    def obter_definicoes_botoes_embaixo(self):
        return [
            ("Ata / Contrato", 'verify_menu', self.abrir_dialog_atas, "Com o database concluíodo é possível gerar as atas ou contratos", False),
            ("Database", 'data-processing', self.update_database, "Salva ou Carrega os dados do Database", False),
            ("Salvar Tabela", 'table', self.salvar_tabela, "Importe um arquivo .xlsx com 4 colunas com índice 'item_num', 'catalogo', 'descricao_tr' e 'descricao_detalada'.", True),
            ("Indicadores", 'dashboard', self.indicadores_normceim, "Visualize os indicadores do relatório", False),
            # ("Indicadores", 'dashboard', self.dashboard_indicadores, "Visualize os indicadores do relatório", False),

        ]

    def tabela_vazia(self):
        # Definindo o nome do arquivo XLSX
        arquivo_xlsx = str(self.sicaf_dir / "tabela_vazia.xlsx")

        # Definindo as colunas da tabela
        colunas = [
            "item_num", "catalogo", "descricao_tr", "descricao_detalhada", 
        ]

        # Criando um DataFrame com a coluna item_num numerada até a linha 10
        df_vazio = pd.DataFrame({
            "item_num": range(1, 11),
            "catalogo": [""] * 10,
            "descricao_tr": [""] * 10,
            "descricao_detalhada": [""] * 10
        })

        try:
            # Tentar abrir o arquivo em modo exclusivo para escrita para verificar se ele está em uso
            with open(arquivo_xlsx, 'w') as f:
                pass  # O arquivo pode ser aberto e escrito

            # Salvando o DataFrame como um arquivo XLSX
            df_vazio.to_excel(arquivo_xlsx, index=False)

            # Ajustando a largura das colunas usando openpyxl
            workbook = load_workbook(arquivo_xlsx)
            worksheet = workbook.active

            worksheet.column_dimensions['A'].width = 15  # item_num
            worksheet.column_dimensions['B'].width = 15  # catalogo
            worksheet.column_dimensions['C'].width = 30  # descricao_tr
            worksheet.column_dimensions['D'].width = 100  # descricao_detalhada

            workbook.save(arquivo_xlsx)

            # Abrindo o arquivo XLSX gerado
            os.startfile(arquivo_xlsx)

        except PermissionError:
            # Se houver um PermissionError, significa que o arquivo está aberto em outra aplicação
            QMessageBox.warning(self, "Arquivo Aberto", "A tabela 'tabela_vazia.xlsx' está aberta. Feche o arquivo antes de tentar salvá-lo novamente.")
        
    def setup_treeview_styles(self):
        header = self.treeView.header()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def setup_pdf_processing_thread(self):
        if not self.pdf_dir.exists() or not self.txt_dir.exists():
            QMessageBox.critical(self, "Erro", "Diretório de PDF ou TXT não encontrado.")
            return
        self.processing_thread = PDFProcessingThread(self.pdf_dir, self.txt_dir)
        self.processing_thread.progress_updated.connect(self.progressDialog.update_progress)
        self.processing_thread.processing_complete.connect(self.progressDialog.on_conversion_finished)

    def import_tr(self):
        # Verifica se o QLabel ainda existe e não foi deletado antes de tentar escondê-lo
        if hasattr(self, 'message_label') and self.message_label:
            try:
                self.message_label.hide()
            except RuntimeError:
                self.message_label = None  # Marca como None se for deletado

        # Abrir um diálogo de arquivo para selecionar o arquivo
        file_path, _ = QFileDialog.getOpenFileName(self, "Importar Termo de Referência", "", 
                                                    "Arquivos Excel (*.xlsx);;Arquivos LibreOffice (*.ods)")
        if not file_path:
            return  # Se o usuário cancelar, não faça nada

        # Verifica a extensão do arquivo para usar o método adequado
        ext = Path(file_path).suffix.lower()

        if ext == '.xlsx':
            # Para arquivos Excel (.xlsx)
            df = pd.read_excel(file_path)
        elif ext == '.ods':
            # Para arquivos LibreOffice (.ods)
            df = pd.read_excel(file_path, engine='odf')
        else:
            QMessageBox.warning(self, "Formato não suportado", "Formato de arquivo não suportado.")
            return

        # Formatar e validar os dados (se necessário)
        erros = self.formatar_e_validar_dados(df)
        if erros:
            QMessageBox.critical(self, "Erro de Validação", "\n".join(erros))
            return

        # Atualizar o DataFrame carregado
        self.tr_variavel_df_carregado = df

        # Atualizar a visualização da tabela com os dados importados
        self.atualizar_modelo_com_dados(df)

        # Atualizar o alerta para informar o usuário que o Termo de Referência foi carregado
        self.atualizar_alerta_apos_importar_tr()

        # Exibir uma mensagem informando que o arquivo foi importado com sucesso
        QMessageBox.information(self, "Importação Concluída", f"Arquivo {Path(file_path).name} importado com sucesso.")


    def formatar_e_validar_dados(self, df):
        erros = []

        # Verificar se as colunas obrigatórias estão presentes
        colunas_obrigatorias = ["item_num", "catalogo", "descricao_tr", "descricao_detalhada"]
        for coluna in colunas_obrigatorias:
            if coluna not in df.columns:
                erros.append(f"A coluna obrigatória '{coluna}' está faltando no arquivo.")

        # Se houver erros nas colunas obrigatórias, retornar imediatamente
        if erros:
            return erros

        # Remover quebras de linha e espaços extras
        for col in colunas_obrigatorias:
            df[col] = df[col].apply(lambda x: " ".join(str(x).replace("\n", " ").split()) if pd.notnull(x) else x)

        # Verificar se item_num é inteiro e sequencial
        df['item_num'] = pd.to_numeric(df['item_num'], errors='coerce')

        if df['item_num'].isnull().any():
            erros.append("A coluna 'item_num' contém valores não numéricos.")

        # Verificar sequencialidade
        sequencia = df['item_num'].dropna().astype(int).sort_values().unique()
        esperado = list(range(sequencia.min(), sequencia.max() + 1))
        if not all(item in sequencia for item in esperado):
            faltando = set(esperado) - set(sequencia)
            erros.append(f"Números sequenciais faltando em 'item_num': {sorted(faltando)}")

        # Verificar se catalogo, descricao_tr, e descricao_detalhada são textos
        df['catalogo'] = df['catalogo'].astype(str)
        df['descricao_tr'] = df['descricao_tr'].astype(str)
        df['descricao_detalhada'] = df['descricao_detalhada'].astype(str)

        # Verificar valores em branco nas colunas obrigatórias
        for coluna in colunas_obrigatorias:
            if df[coluna].isnull().any() or df[coluna].eq("").any():
                erros.append(f"A coluna '{coluna}' contém valores em branco.")

        # Verificar se há erros
        if erros:
            erros.insert(0, "Não foi possível carregar a tabela devido aos seguintes erros:")

        return erros

    def atualizar_modelo_com_dados(self, df_relevante):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Item', 'Catálogo', 'Descrição', 'Descrição Detalhada'])
        for _, row in df_relevante.iterrows():
            item_num = QStandardItem(str(row['item_num']))
            catalogo = QStandardItem(str(row['catalogo']))
            descricao_tr = QStandardItem(str(row['descricao_tr']))
            descricao_detalhada = QStandardItem(str(row['descricao_detalhada']))
            item_num.setEditable(False)
            catalogo.setEditable(False)
            descricao_tr.setEditable(False)
            descricao_detalhada.setEditable(False)
            self.model.appendRow([item_num, catalogo, descricao_tr, descricao_detalhada])
        self.treeView.expandAll()
        for column in range(self.model.columnCount()):
            self.treeView.resizeColumnToContents(column)

    def atualizar_alerta_apos_importar_tr(self):
        icon_path = str(self.icons_dir / 'confirm.png')
        new_text = (f"<img src='{icon_path}' style='vertical-align: middle;' width='24' height='24'> "
                    "Salve os Termos de Homologação na pasta correta e pressione '<b><u>Termo de Homologação</u></b>' para processar os dados. "
                    f"<img src='{icon_path}' style='vertical-align: middle;' width='24' height='24'>")
        self.alert_label.setText(new_text)

    def atualizar_alerta_apos_processar_homologacao(self):
        icon_path = str(self.icons_dir / 'sicaf.png')
        new_text = (f"<img src='{icon_path}' style='vertical-align: middle;' width='24' height='24'> "
                    "Clique com o botão direito no TreeView para copiar o CNPJ para facilitar a busca do SICAF Nível I. "
                    f"<img src='{icon_path}' style='vertical-align: middle;' width='24' height='24'>")
        self.alert_label.setText(new_text)

    def processar_homologacao(self):
        # Verifica se a pasta de PDFs existe
        if not self.pdf_dir.exists():
            QMessageBox.warning(self, "Erro", "Pasta de PDFs não encontrada.")
            return
        
        # Lista todos os arquivos PDF na pasta
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        
        # Inicializa o ProgressDialog e processa todos os arquivos, sem verificar por novos arquivos
        total_files = len(pdf_files)
        self.progressDialog = ProgressDialog(total_files, self.pdf_dir, self)
        self.progressDialog.processing_complete.connect(self.finalizar_processamento_homologacao)
        self.progressDialog.show()

    def finalizar_processamento_homologacao(self, extracted_data):
        self.homologacao_dataframe = save_to_dataframe(extracted_data, self.tr_variavel_df_carregado, DATABASE_DIR, self.current_dataframe)
        
        if self.homologacao_dataframe is not None:
            self.current_dataframe = self.homologacao_dataframe  # Atualiza o DataFrame corrente
            self.update_treeview_with_dataframe(self.homologacao_dataframe)
            self.atualizar_alerta_apos_processar_homologacao()
            
            # Verifica se as colunas necessárias existem
            if {'num_pregao', 'ano_pregao', 'uasg'}.issubset(self.current_dataframe.columns):
                # Filtra linhas onde qualquer uma das colunas chave contém NaN
                filtered_df = self.current_dataframe.dropna(subset=['num_pregao', 'ano_pregao', 'uasg'])
                
                # Gera o nome da tabela apenas para linhas sem NaN
                def create_table_name(row):
                    return f"{row['num_pregao']}-{row['ano_pregao']}-{row['uasg']}-Homolog"

                filtered_df['table_name'] = filtered_df.apply(create_table_name, axis=1)
                
                # Debugging output
                print("Valores de 'num_pregao':", filtered_df['num_pregao'].unique())
                print("Valores de 'ano_pregao':", filtered_df['ano_pregao'].unique())
                print("Valores de 'uasg':", filtered_df['uasg'].unique())
                print("Nomes de tabelas gerados:", filtered_df['table_name'].unique())
                
                if filtered_df['table_name'].nunique() == 1:
                    table_name = filtered_df['table_name'].iloc[0]
                    self.save_data(table_name)  # Chama a função de salvar com o nome da tabela
                else:
                    QMessageBox.critical(self, "Erro", "A combinação de 'num_pregao', 'ano_pregao', e 'uasg' não é única. Por favor, verifique os dados.")
            else:
                QMessageBox.critical(self, "Erro", "Dados necessários para criar o nome da tabela não estão presentes.")
            return self.current_dataframe  # Retorna o DataFrame atualizado
        else:
            QMessageBox.warning(self, "Erro", "Falha ao salvar os dados.")
            return None  # Retorna None para indicar que o processo falhou

    def save_data(self, table_name):
        if isinstance(self.current_dataframe, pd.DataFrame) and not self.current_dataframe.empty:
            print("Salvando DataFrame com as colunas:", self.current_dataframe.columns)
            try:
                with self.db_manager as conn:
                    self.current_dataframe.to_sql(table_name, conn, if_exists='replace', index=False)
                QMessageBox.information(self, "Sucesso", f"DataFrame salvo com sucesso em '{table_name}'!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar os dados no banco de dados: {e}")
        else:
            QMessageBox.critical(self, "Erro", "Nenhum DataFrame válido disponível para salvar ou o objeto não é um DataFrame.")

    def processar_sicaf(self):
        if self.current_dataframe is not None:
            dataframe_to_use = self.current_dataframe
        else:
            QMessageBox.warning(self, "Erro", "Primeiro processe a homologação ou carregue os dados do banco de dados.")
            return

        if not self.sicaf_dir.exists():
            QMessageBox.warning(self, "Erro", "Pasta de PDFs não encontrada.")
            return

        self.progressSicafDialog = SICAFDialog(self.sicaf_dir, dataframe_to_use, self)
        # Conecta o sinal a ambos os métodos
        self.progressSicafDialog.processing_complete.connect(self.finalizar_processamento_sicaf)
        self.progressSicafDialog.processing_complete.connect(self.receber_df_final)
        self.progressSicafDialog.show()

    def receber_df_final(self, df_final):
        if isinstance(df_final, pd.DataFrame):
            self.current_dataframe = df_final  # Atualize o DataFrame atual
            print("DataFrame final recebido do SICAF:")
            print(df_final)

            # Verifica se as colunas necessárias existem
            if {'num_pregao', 'ano_pregao', 'uasg'}.issubset(self.current_dataframe.columns):
                # Filtra linhas onde qualquer uma das colunas chave contém NaN
                filtered_df = self.current_dataframe.dropna(subset=['num_pregao', 'ano_pregao', 'uasg'])
                
                # Gera o nome da tabela apenas para linhas sem NaN
                def create_table_name(row):
                    return f"{row['num_pregao']}-{row['ano_pregao']}-{row['uasg']}-Homolog-Sicaf"

                filtered_df['table_name'] = filtered_df.apply(create_table_name, axis=1)
                
                # Debugging output
                print("Valores de 'num_pregao':", filtered_df['num_pregao'].unique())
                print("Valores de 'ano_pregao':", filtered_df['ano_pregao'].unique())
                print("Valores de 'uasg':", filtered_df['uasg'].unique())
                print("Nomes de tabelas gerados:", filtered_df['table_name'].unique())
                
                if filtered_df['table_name'].nunique() == 1:
                    table_name = filtered_df['table_name'].iloc[0]
                    self.save_data(table_name)  # Chama a função de salvar com o nome da tabela
                else:
                    QMessageBox.critical(self, "Erro", "A combinação de 'num_pregao', 'ano_pregao', e 'uasg' não é única. Por favor, verifique os dados.")
            else:
                QMessageBox.critical(self, "Erro", "Dados necessários para criar o nome da tabela não estão presentes.")
            return self.current_dataframe  # Retorna o DataFrame atualizado
        else:
            QMessageBox.warning(self, "Erro", "Dados recebidos não são válidos.")

    def finalizar_processamento_sicaf(self, extracted_data):
        if isinstance(extracted_data, pd.DataFrame):
            print("DataFrame resultante do SICAF:")
            print(extracted_data)
            self.update_treeview_with_dataframe(extracted_data)
        else:
            print("Erro: Dados recebidos não são um DataFrame.")
            QMessageBox.warning(self, "Erro", "Os dados recebidos não são válidos.")

    def handle_loaded_data(self, loaded_dataframe, pe_pattern=None):
        if isinstance(loaded_dataframe, pd.DataFrame) and not loaded_dataframe.empty:
            self.current_dataframe = loaded_dataframe  # Atualiza o DataFrame corrente
            self.pe_pattern = pe_pattern  # Armazena o padrão PE identificado
            print(f"DataFrame atualizado e carregado:\n{self.current_dataframe.head()}")
            print(f"Padrão PE identificado: {self.pe_pattern}")

            # Verifique se o treeView já foi inicializado, se não, inicialize-o
            if not hasattr(self, 'treeView'):
                self.setup_treeview()

            self.update_treeview_with_dataframe(self.current_dataframe)
        else:
            QMessageBox.warning(self, "Aviso", "Os dados carregados não são um DataFrame válido ou estão vazios.")

    def update_treeview_with_dataframe(self, dataframe):
        if dataframe is None:
            QMessageBox.critical(self, "Erro", "O DataFrame não está disponível para atualizar a visualização.")
            return
        
        creator = ModeloTreeview(self.icons_dir)
        self.model = creator.criar_modelo(dataframe)
        
        # Verifique se o treeView está inicializado
        if not hasattr(self, 'treeView'):
            self.setup_treeview()

        self.treeView.setModel(self.model)
        # self.treeView.setItemDelegate(HTMLDelegate())
        self.treeView.reset()


    def update_database(self):
        # Sempre abre o diálogo, independentemente da existência de um DataFrame atual
        dialog = DatabaseDialog(self, self.current_dataframe, self.handle_loaded_data)
        dialog.exec()

    def update_progress(self, value):
        if self.progressDialog.isVisible():
            self.progressDialog.progressBar.setValue(value)
        else:
            # Caso a barra de progresso não esteja visível, você pode optar por mostrá-la aqui
            self.progressDialog.show()
            self.progressDialog.progressBar.setValue(value)
                    
    def abrir_dialog_atas(self):
        if self.current_dataframe is not None:
            dataframe_to_use = self.current_dataframe
            if all(col in dataframe_to_use.columns for col in ['empresa', 'num_pregao', 'ano_pregao']):
                print("Colunas de 'empresa', 'num_pregao', 'ano_pregao' do DataFrame:")
                print(dataframe_to_use[['empresa', 'num_pregao', 'ano_pregao']])
            else:
                print("Alguma das colunas 'empresa', 'num_pregao', 'ano_pregao' não está presente no DataFrame.")
        else:
            dataframe_to_use = None
            print("Nenhum DataFrame atual disponível.")

        if self.atasDialog is None or not self.atasDialog.isVisible():
            self.atasDialog = AtasDialog(self, pe_pattern=self.pe_pattern, dataframe=dataframe_to_use)
            self.atasDialog.dataframe_updated.connect(self.on_dataframe_updated)  # Conectar ao método que trata o DataFrame
            self.atasDialog.show()
        else:
            self.atasDialog.raise_()
            self.atasDialog.activateWindow()

    def on_dataframe_updated(self, updated_dataframe):
        # Atualiza o DataFrame atual com as modificações recebidas
        self.current_dataframe = updated_dataframe
        print("DataFrame atualizado recebido do diálogo Atas:")

        # Verifica se o DataFrame é None ou se as colunas necessárias estão ausentes
        if self.current_dataframe is None or not {'numero_ata', 'item_num'}.issubset(self.current_dataframe.columns):
            return 

        print(self.current_dataframe[['numero_ata', 'item_num']])

        # Verifica se as colunas necessárias existem
        if {'num_pregao', 'ano_pregao', 'uasg'}.issubset(self.current_dataframe.columns):
            # Filtra linhas onde qualquer uma das colunas chave contém NaN
            filtered_df = self.current_dataframe.dropna(subset=['num_pregao', 'ano_pregao', 'uasg'])
            
            # Gera o nome da tabela apenas para linhas sem NaN
            def create_table_name(row):
                return f"{row['num_pregao']}-{row['ano_pregao']}-{row['uasg']}-Final"

            filtered_df['table_name'] = filtered_df.apply(create_table_name, axis=1)
            
            # Debugging output
            print("Valores de 'num_pregao':", filtered_df['num_pregao'].unique())
            print("Valores de 'ano_pregao':", filtered_df['ano_pregao'].unique())
            print("Valores de 'uasg':", filtered_df['uasg'].unique())
            print("Nomes de tabelas gerados:", filtered_df['table_name'].unique())
            
            if filtered_df['table_name'].nunique() == 1:
                table_name = filtered_df['table_name'].iloc[0]
                self.save_data(table_name)  # Chama a função de salvar com o nome da tabela
            else:
                QMessageBox.critical(self, "Erro", "A combinação de 'num_pregao', 'ano_pregao', e 'uasg' não é única. Por favor, verifique os dados.")
        else:
            QMessageBox.critical(self, "Erro", "Dados necessários para criar o nome da tabela não estão presentes.")

    def salvar_tabela(self):
        if self.current_dataframe is not None:
            # Define o caminho do arquivo a ser salvo
            arquivo_excel = str(self.pdf_dir / 'TabelaAtual.xlsx')
            # Salva o DataFrame no arquivo Excel
            self.current_dataframe.to_excel(arquivo_excel, index=False)
            # Abre o arquivo Excel
            os.startfile(arquivo_excel)
        else:
            QMessageBox.warning(self, "Aviso", "Não há dados para salvar.")

    def indicadores_normceim(self):
        if self.current_dataframe is not None:
            # Supondo que pe_pattern é armazenado em algum lugar após ser determinado
            self.dialogo_indicadores = RelatorioIndicadores(dataframe=self.current_dataframe, parent=self, pe_pattern=self.pe_pattern)
            self.dialogo_indicadores.show()
        else:
            QMessageBox.warning(self, "Aviso", "Não há dados carregados.")

class ModeloTreeview:
    def __init__(self, icons_dir):
        print(f"Carregando ícones de: {icons_dir}")
        self.icons = load_icons(icons_dir)

    def determinar_itens_iguais(self, row, empresa_items):
        empresa_name = str(row['empresa']) if pd.notna(row['empresa']) else ""
        cnpj = str(row['cnpj']) if pd.notna(row['cnpj']) else ""
        situacao = str(row['situacao']) if pd.notna(row['situacao']) else "Não definido"
        is_situacao_only = not empresa_name and not cnpj
        parent_key = f"{situacao}" if is_situacao_only else f"{cnpj} - {empresa_name}".strip(" -")
        
        if parent_key not in empresa_items:
            parent_item = QStandardItem()
            parent_item.setEditable(False)
            icon_key = 'alert' if is_situacao_only else ('checked' if pd.notna(row['endereco']) else 'unchecked')
            icon = self.icons.get(icon_key, QIcon())  # Obtém o ícone ou um ícone vazio se não encontrado
            parent_item.setIcon(icon)
            return parent_key, parent_item

        return parent_key, None

    def update_view(self, view):
        # Força a atualização da view para garantir que os ícones sejam exibidos
        view.viewport().update()
        
    def criar_modelo(self, dataframe):
        model, header = self.initializar_modelo(dataframe)
        empresa_items = self.processar_linhas(dataframe, model)
        self.atualizar_contador_cabecalho(empresa_items, model)
        return model

    def initializar_modelo(self, dataframe):
        total_items = len(dataframe)
        situacoes_analizadas = ['Adjudicado e Homologado', 'Fracassado e Homologado', 'Deserto e Homologado', 'Anulado e Homologado']
        nao_analisados = len(dataframe[~dataframe['situacao'].isin(situacoes_analizadas)])
        header = f"Total de itens da licitação {total_items} | Total de itens analisados {total_items - nao_analisados} | Total de itens não analisados {nao_analisados}"
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([header])
        return model, header

    def processar_linhas(self, dataframe, model):
        empresa_items = {}
        for _, row in dataframe.iterrows():
            self.processar_linhas_individualmente(row, model, empresa_items)
        return empresa_items

    def processar_linhas_individualmente(self, row, model, empresa_items):
        parent_key, parent_item = self.determinar_itens_iguais(row, empresa_items)
        if parent_item:
            model.appendRow(parent_item)
            if parent_key not in empresa_items:
                empresa_items[parent_key] = {
                    'item': parent_item,
                    'count': 0,
                    'details_added': False,
                    'items_container': QStandardItem()  # Não defina o texto aqui
                }
                empresa_items[parent_key]['items_container'].setEditable(False)

        # Ajuste para incrementar a contagem em todas as situações
        if parent_key in empresa_items:
            empresa_items[parent_key]['count'] += 1

        self.adicionar_informacao_ao_item(row, empresa_items[parent_key]['item'], empresa_items, parent_key)

    def adicionar_informacao_ao_item(self, row, parent_item, empresa_items, parent_key):
        font_size = "14px"  # Define o tamanho da fonte
        situacoes_especificas = ['Fracassado e Homologado', 'Deserto e Homologado', 'Anulado e Homologado']
        situacao = row['situacao']

        # Determinar se a situação é específica ou "Não definido"
        if situacao not in situacoes_especificas and situacao != 'Adjudicado e Homologado':
            situacao = 'Não definido'

        if situacao in situacoes_especificas or situacao == 'Não definido':
            # Cria um item com informações básicas sem detalhes extras para situações específicas
            item_text = f"Item {row['item_num']} - {row['descricao_tr']} - {situacao}"
            item_info = QStandardItem(item_text)
            item_info.setEditable(False)
            parent_item.appendRow(item_info)
        else:
            # Processo normal para 'Adjudicado e Homologado'
            if not empresa_items[parent_key]['details_added']:
                self.adicionar_detalhes_empresa(row, parent_item)
                empresa_items[parent_key]['items_container'].setText("")  # Limpa o texto se necessário
                parent_item.appendRow(empresa_items[parent_key]['items_container'])
                empresa_items[parent_key]['details_added'] = True

            # Adicionando itens específicos da licitação
            self.adicionar_subitens_detalhados(row, empresa_items[parent_key]['items_container'])

        # Atualizar o texto do container com base na contagem de itens
        item_count_text = "Item" if empresa_items[parent_key]['count'] == 1 else "Relação de itens:"
        empresa_items[parent_key]['items_container'].setText(f"{item_count_text} ({empresa_items[parent_key]['count']})")
        
    def atualizar_contador_cabecalho(self, empresa_items, model):
        font_size = "16px"  # Definir o tamanho da fonte para os cabeçalhos dos itens
        for chave_item_pai, empresa in empresa_items.items():
            count = empresa['count']
            # Formatar o texto com HTML para ajustar o tamanho da fonte
            display_text = f"{chave_item_pai} (1 item)" if count == 1 else f"{chave_item_pai} ({count} itens)"
            empresa['item'].setText(display_text)

    def adicionar_detalhes_empresa(self, row, parent_item):
        infos = [
            f"Endereço: {row['endereco']}, CEP: {row['cep']}, Município: {row['municipio']}" if pd.notna(row['endereco']) else "Endereço: Não informado",
            f"Contato: {row['telefone']} Email: {row['email']}" if pd.notna(row['telefone']) else "Contato: Não informado",
            f"Responsável Legal: {row['responsavel_legal']}" if pd.notna(row['responsavel_legal']) else "Responsável Legal: Não informado"
        ]
        for info in infos:
            info_item = QStandardItem(info)
            info_item.setEditable(False)
            parent_item.appendRow(info_item)

    def criar_dados_sicaf_do_item(self, row):
        fields = ['endereco', 'cep', 'municipio', 'telefone', 'email', 'responsavel_legal']
        return [self.criar_detalhe_item(field.capitalize(), row[field]) for field in fields if pd.notna(row[field])]

    def adicionar_subitens_detalhados(self, row, sub_items_layout):
        item_info_html = f"Item {row['item_num']} - {row['descricao_tr']} - {row['situacao']}"
        item_info = QStandardItem(item_info_html)
        item_info.setEditable(False)
        sub_items_layout.appendRow(item_info)

        detalhes = [
            f"Descrição Detalhada: {row['descricao_detalhada']}",
            f"Unidade de Fornecimento: {row['unidade']} Quantidade: {self.formatar_quantidade(row['quantidade'])} "
            f"Valor Estimado: {self.formatar_brl(row['valor_estimado'])} Valor Homologado: {self.formatar_brl(row['valor_homologado_item_unitario'])} "
            f"Desconto: {self.formatar_percentual(row['percentual_desconto'])} Marca: {row['marca_fabricante']} Modelo: {row['modelo_versao']}",
        ]

        for detalhe in detalhes:
            detalhe_item = QStandardItem(detalhe)
            detalhe_item.setEditable(False)
            item_info.appendRow(detalhe_item)


    def criar_detalhe_item(self, label, data):
        return QStandardItem(f"<b>{label}:</b> {data if pd.notna(data) else 'Não informado'}")

    def formatar_brl(self, valor):
        try:
            if valor is None:
                return "Não disponível"  # ou outra representação adequada para seu caso de uso
            return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except ValueError:
            return "Valor inválido"

    def formatar_quantidade(self, valor):
        try:
            float_value = float(valor)
            if float_value.is_integer():
                return f"{int(float_value)}"
            else:
                return f"{float_value:.2f}".replace('.', ',')
        except ValueError:
            return "Erro de Formatação"

    def formatar_percentual(self, valor):
        try:
            percent_value = float(valor)
            return f"{percent_value:.2f}%"
        except ValueError:
            return "Erro de Formatação"
        


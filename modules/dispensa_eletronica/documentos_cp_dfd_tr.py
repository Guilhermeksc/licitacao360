import sys
import string
import json
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from diretorios import *
import fitz
from docxtpl import DocxTemplate
import pandas as pd
import win32com.client
import os
import stat
from PyPDF2 import PdfMerger
import re
from num2words import num2words
from datetime import datetime
import subprocess
from fpdf import FPDF
from modules.dispensa_eletronica.merge_pdf.merge_anexos import MergePDFDialog


class Worker(QThread):
    update_status = pyqtSignal(str, str, int) 
    task_complete = pyqtSignal()
    
    def __init__(self, documentos, df_registro_selecionado, parent=None):
        super().__init__(parent)
        self.documentos = documentos

        self.config = load_config_path_id()

        self.df_registro_selecionado = df_registro_selecionado  # Adiciona df_registro_selecionado aqui
        self.pasta_base = Path(self.config.get('pasta_base', str(Path.home() / 'Desktop')))
        self.id_processo = self.df_registro_selecionado['id_processo'].iloc[0]
        self.objeto = self.df_registro_selecionado['objeto'].iloc[0]
        self.ICONS_DIR = ICONS_DIR  # Atualize com o caminho real
        
        self.pdf_paths = []

    def run(self):
        pdf_paths = []

        for doc in self.documentos:
            doc_desc = doc.get('desc', doc.get('subfolder', 'Documento desconhecido'))

            # Atualiza o status para "sendo gerado" e emite o sinal para atualização do ícone
            self.update_status.emit(doc_desc, "sendo gerado", 50)

            if "template" in doc:
                docx_path = self.gerarDocumento(doc["template"], doc["subfolder"], doc["desc"])
                if docx_path:
                    pdf_path = self.salvarPDF(docx_path)
                    if pdf_path:
                        pdf_info = {"pdf_path": pdf_path}
                        if "cover" in doc:
                            pdf_info["cover_path"] = TEMPLATE_DISPENSA_DIR / doc["cover"]
                        pdf_paths.append(pdf_info)
            else:
                pdf_path = self.get_latest_pdf(self.pasta_base / self.nome_pasta / doc["subfolder"])
                if pdf_path:
                    pdf_paths.append({"pdf_path": pdf_path, "cover_path": TEMPLATE_DISPENSA_DIR / doc["cover"]})
                else:
                    QMessageBox.warning(None, "Erro", f"Arquivo PDF não encontrado: {doc['subfolder']}")

            # Atualiza o status para "concluído" e emite o sinal para mudar o ícone
            self.update_status.emit(doc_desc, "concluído", 100)

        self.concatenar_e_abrir_pdfs(pdf_paths)
        self.task_complete.emit()

    def concatenar_e_abrir_pdfs(self, pdf_paths):
        if not pdf_paths:
            QMessageBox.warning(None, "Erro", "Nenhum PDF foi gerado para concatenar.")
            return

        output_pdf_path = self.pasta_base / self.nome_pasta / "2. CP e anexos" / "CP_e_anexos.pdf"
        merger = PdfMerger()

        try:
            for pdf in pdf_paths:
                if "cover_path" in pdf:
                    merger.append(str(pdf["cover_path"]))
                merger.append(str(pdf["pdf_path"]))

            merger.write(str(output_pdf_path))
            merger.close()

            os.startfile(output_pdf_path)
            print(f"PDF concatenado salvo e aberto: {output_pdf_path}")
        except Exception as e:
            print(f"Erro ao concatenar os PDFs: {e}")
            QMessageBox.warning(None, "Erro", f"Erro ao concatenar os PDFs: {e}")

    def get_latest_pdf(self, directory):
        pdf_files = list(directory.glob("*.pdf"))
        if not pdf_files:
            return None
        latest_pdf = max(pdf_files, key=os.path.getmtime)
        return latest_pdf

    def alterar_posto(self, posto):
        # Define um dicionário de mapeamento de postos e suas respectivas abreviações
        mapeamento_postos = {
            r'Capitão[\s\-]de[\s\-]Corveta': 'CC',
            r'Capitão[\s\-]de[\s\-]Fragata': 'CF',
            r'Capitão[\s\-]de[\s\-]Mar[\s\-]e[\s\-]Guerra': 'CMG',
            r'Capitão[\s\-]Tenente': 'CT',
            r'Primeiro[\s\-]Tenente': '1ºTen',
            r'Segundo[\s\-]Tenente': '2ºTen',
            r'Primeiro[\s\-]Sargento': '1ºSG',
            r'Segundo[\s\-]Sargento': '2ºSG',
            r'Terceiro[\s\-]Sargento': '3ºSG',
            r'Cabo': 'CB',
            r'Sub[\s\-]oficial': 'SO',
        }

        # Itera sobre o dicionário de mapeamento e aplica a substituição
        for padrao, substituicao in mapeamento_postos.items():
            if re.search(padrao, posto, re.IGNORECASE):
                return re.sub(padrao, substituicao, posto, flags=re.IGNORECASE)

        # Retorna o posto original se nenhuma substituição for aplicada
        return posto

    def valor_por_extenso(self, valor):
        if not valor or valor.strip() == '':  # Verifica se o valor está vazio ou None
            return None  # Retorna None se o valor não for válido

        try:
            valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
            valor_float = float(valor)
            parte_inteira = int(valor_float)
            parte_decimal = int(round((valor_float - parte_inteira) * 100))

            if parte_decimal > 0:
                valor_extenso = f"{num2words(parte_inteira, lang='pt_BR')} reais e {num2words(parte_decimal, lang='pt_BR')} centavos"
            else:
                valor_extenso = f"{num2words(parte_inteira, lang='pt_BR')} reais"

            # Corrige "um reais" para "um real"
            valor_extenso = valor_extenso.replace("um reais", "um real")

            return valor_extenso

        except ValueError:
            return None
                
    def gerarDocumento(self, template, subfolder, desc):
        """
        Gera um documento baseado em um template .docx.
        """
        if self.df_registro_selecionado.empty:
            QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
            return

        # Caminhos dos templates e do arquivo a ser salvo
        template_filename = f"template_{template}.docx"
        template_path, save_path = self.setup_document_paths(template_filename, subfolder, desc)

        # Verificar e criar as pastas necessárias
        self.verificar_e_criar_pastas(self.pasta_base / self.nome_pasta)

        # Verifica se o template existe
        if not template_path.exists():
            QMessageBox.warning(None, "Erro de Template", f"O arquivo de template não foi encontrado: {template_path}")
            return

        # Carregar e renderizar o template
        with open(str(template_path), 'rb') as template_file:
            doc = DocxTemplate(template_file)
            context = self.df_registro_selecionado.to_dict('records')[0]
            context = self.prepare_context(context)
            doc.render(context)
            doc.save(str(save_path))

        return save_path  # Retorna o caminho do documento gerado

    def setup_document_paths(self, template_filename, subfolder_name, file_description):
        """
        Configura os caminhos para os templates e os documentos gerados.
        """
        template_path = TEMPLATE_DISPENSA_DIR / template_filename
        id_processo = self.df_registro_selecionado['id_processo'].iloc[0].replace('/', '-')
        objeto = self.df_registro_selecionado['objeto'].iloc[0]
        self.nome_pasta = f"{id_processo} - {objeto}"

        # Verifica ou altera o diretório base
        if 'pasta_base' not in self.config:
            self.alterar_diretorio_base()

        # Define o caminho para salvar o arquivo gerado
        pasta_base = Path(self.config['pasta_base']) / self.nome_pasta / subfolder_name
        pasta_base.mkdir(parents=True, exist_ok=True)
        save_path = pasta_base / f"{id_processo} - {file_description}.docx"

        return template_path, save_path

    def verificar_e_criar_pastas(self, pasta_base):
        id_processo_modificado = self.id_processo.replace("/", "-")
        objeto_modificado = self.objeto.replace("/", "-")
        base_path = pasta_base / f'{id_processo_modificado} - {objeto_modificado}'

        pastas_necessarias = [
            pasta_base / '1. Autorizacao',
            pasta_base / '2. CP e anexos',
            pasta_base / '3. Aviso',
            pasta_base / '2. CP e anexos' / 'DFD',
            pasta_base / '2. CP e anexos' / 'DFD' / 'Anexo A - Relatorio Safin',
            pasta_base / '2. CP e anexos' / 'DFD' / 'Anexo B - Especificações e Quantidade',
            pasta_base / '2. CP e anexos' / 'TR',
            pasta_base / '2. CP e anexos' / 'TR' / 'Pesquisa de Preços',
            pasta_base / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária',
            pasta_base / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária' / 'Relatório do PDM-Catser',
            pasta_base / '2. CP e anexos' / 'Justificativas Relevantes',
        ]
        for pasta in pastas_necessarias:
            if not pasta.exists():
                pasta.mkdir(parents=True)
        return pastas_necessarias

    def salvarPDF(self, docx_path):
        """
        Converte um arquivo .docx em PDF.
        """
        try:
            # Converte o caminho do arquivo para Path, caso não seja.
            docx_path = Path(docx_path) if not isinstance(docx_path, Path) else docx_path
            pdf_path = docx_path.with_suffix('.pdf')

            # Abre o Word e converte o arquivo .docx em .pdf
            word = win32com.client.Dispatch("Word.Application")
            doc = None
            try:
                doc = word.Documents.Open(str(docx_path))
                doc.SaveAs(str(pdf_path), FileFormat=17)  # 17 é o código para salvar como PDF
            except Exception as e:
                raise e
            finally:
                if doc is not None:
                    doc.Close()
                word.Quit()

            # Verifica se o PDF foi criado corretamente
            if not pdf_path.exists():
                raise FileNotFoundError(f"O arquivo PDF não foi criado: {pdf_path}")

            return pdf_path  # Retorna o caminho do arquivo PDF gerado
        except Exception as e:
            print(f"Erro ao converter o documento: {e}")
            QMessageBox.warning(None, "Erro", f"Erro ao converter o documento: {e}")
            return None

    def formatar_responsavel(self, chave, data, context):
        responsavel = data.get(chave)
        if responsavel and isinstance(responsavel, str):
            try:
                nome, posto, funcao = responsavel.split('\n')
                posto_alterado = self.alterar_posto(posto)
                responsavel_dict = {
                    'nome': nome,
                    'posto': posto_alterado,
                }
                responsavel_extenso = f"{responsavel_dict.get('posto', '')} {responsavel_dict.get('nome', '')}"
                context.update({f'{chave}_formatado': responsavel_extenso})
            except ValueError:
                context.update({f'{chave}_formatado': 'Não especificado\nNão especificado'})
        else:
            context.update({f'{chave}_formatado': 'Não especificado\nNão especificado'})

    def prepare_context(self, data):
        context = {key: (str(value) if value is not None else 'Não especificado') for key, value in data.items()}
        descricao_servico = "aquisição de" if data['material_servico'] == "Material" else "contratação de empresa especializada em"
        descricao_servico_primeira_letra_maiuscula = descricao_servico[0].upper() + descricao_servico[1:]
        context.update({'descricao_servico': descricao_servico})
        context.update({'descricao_servico_primeira_letra_maiuscula': descricao_servico_primeira_letra_maiuscula})

        # Processar responsável pela demanda e operador
        self.formatar_responsavel('responsavel_pela_demanda', data, context)
        self.formatar_responsavel('operador', data, context)

        valor_total = data.get('valor_total')
        if valor_total and isinstance(valor_total, str):
            valor_extenso = self.valor_por_extenso(valor_total)
            valor_total_e_extenso = f"{valor_total} ({valor_extenso})"
            context.update({'valor_total_e_extenso': valor_total_e_extenso})
        else:
            context.update({'valor_total_e_extenso': 'Não especificado'})

        # Lógica para atividade_custeio
        if data.get('atividade_custeio') == 'Sim':
            texto_custeio = (
                "A presente contratação por dispensa de licitação está enquadrada como atividade de custeio, "
                "conforme mencionado no artigo 2º da Portaria ME nº 7.828, de 30 de agosto de 2022. "
                "Conforme previsão do art. 3º do Decreto nº 10.193, de 27 de dezembro de 2019, e as normas "
                "infralegais de delegação de competência no âmbito da Marinha, que estabelecem limites e instâncias "
                "de governança, essa responsabilidade é delegada ao ordenador de despesas, respeitando os valores "
                "estipulados no decreto."
            )
        else:
            texto_custeio = (
                "A presente contratação por dispensa de licitação não se enquadra nas hipóteses de atividades de "
                "custeio previstas no Decreto nº 10.193, de 27 de dezembro de 2019, pois o objeto contratado não se "
                "relaciona diretamente às atividades comuns de suporte administrativo mencionadas no artigo 2º da "
                "Portaria ME nº 7.828, de 30 de agosto de 2022."
            )
        context.update({'texto_custeio': texto_custeio})

        # Alterar formato de data_sessao
        data_sessao = data.get('data_sessao')
        if data_sessao:
            try:
                data_obj = datetime.strptime(data_sessao, '%Y-%m-%d')
                dia_semana = data_obj.strftime('%A')
                data_formatada = data_obj.strftime('%d/%m/%Y') + f" ({dia_semana})"
                context.update({'data_sessao_formatada': data_formatada})
            except ValueError as e:
                context.update({'data_sessao_formatada': 'Data inválida'})
                print("Erro ao processar data da sessão:", e)
        else:
            context.update({'data_sessao_formatada': 'Não especificado'})
            print("Data da sessão não especificada")

        return context
    

class ProgressDialog(QDialog):
    def __init__(self, documentos, df_registro_selecionado):
        super().__init__()
        self.setWindowTitle("Progresso")
        self.setFixedSize(500, 300)
        self.layout = QVBoxLayout(self)

        # Inicializa os labels e ícones para cada documento
        self.labels = {}
        self.icons = {}
        self.icon_loading = QIcon(str(ICONS_DIR / "loading_table.png"))  # Ícone para carregamento
        self.icon_done = QIcon(str(ICONS_DIR / "aproved.png"))  # Ícone para conclusão

        # Adiciona os labels e ícones para cada documento com 'template'
        for doc in documentos:
            if "template" in doc:  # Somente para documentos que têm a chave 'template'
                doc_desc = doc.get('desc', doc.get('subfolder', 'Documento desconhecido'))

                layout_h = QHBoxLayout()

                # Cria o QLabel para o texto do documento e ajusta o estilo
                label = QLabel(f"{doc_desc}")
                label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Alinha o texto verticalmente ao centro e à esquerda
                label.setStyleSheet("font-size: 14px;")  # Define o tamanho da fonte para 14px

                # Cria o QLabel para o ícone e alinha ao centro verticalmente
                icon_label = QLabel()
                icon_label.setPixmap(self.icon_loading.pixmap(24, 24))  # Tamanho do ícone: 24x24
                icon_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Alinha o ícone verticalmente ao centro

                layout_h.addWidget(icon_label)
                layout_h.addWidget(label)
                layout_h.addStretch()  # Adiciona um espaçador para garantir que o texto e ícone fiquem à esquerda
                self.layout.addLayout(layout_h)

                # Armazena os labels e ícones para atualizá-los mais tarde
                self.labels[doc_desc] = label
                self.icons[doc_desc] = icon_label

        # Layout para "Consolidar Documentos PDFs"
        layout_h_consolidar = QHBoxLayout()

        # Cria o QLabel para o texto "Consolidar Documentos PDFs"
        self.label_consolidar = QLabel("Consolidar Documentos PDFs.")
        self.label_consolidar.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.label_consolidar.setStyleSheet("font-size: 14px;")

        # Cria o QLabel para o ícone de carregamento
        self.icon_label_consolidar = QLabel()
        self.icon_label_consolidar.setPixmap(self.icon_loading.pixmap(24, 24))  # Exibe o ícone de carregamento inicialmente
        self.icon_label_consolidar.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        layout_h_consolidar.addWidget(self.icon_label_consolidar)
        layout_h_consolidar.addWidget(self.label_consolidar)
        layout_h_consolidar.addStretch()
        self.layout.addLayout(layout_h_consolidar)

        # Adiciona a barra de progresso indeterminada
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # Define a barra como indeterminada
        self.layout.addWidget(self.progress_bar)

        # Botão de fechar
        self.close_button = QPushButton("Fechar")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.close)
        self.layout.addWidget(self.close_button)

        # Passe o df_registro_selecionado para o Worker
        self.worker = Worker(documentos, df_registro_selecionado)
        self.worker.update_status.connect(self.update_label)
        self.worker.task_complete.connect(self.on_task_complete)  # Conectar ao novo método
        self.worker.task_complete.connect(self.enable_close_button)

        self.worker.start()

    @pyqtSlot(str, str, int)
    def update_label(self, doc_desc, status_text, progress):
        """
        Atualiza o texto do label e o ícone correspondente.
        """
        # Atualiza o label de progresso
        label = self.labels.get(doc_desc)
        if label:
            label.setText(f"{doc_desc} {status_text}")
        
        # Atualiza o ícone após a conclusão do documento
        if progress == 100:
            icon_label = self.icons.get(doc_desc)
            if icon_label:
                icon_label.setPixmap(self.icon_done.pixmap(24, 24))  # Altera para o ícone de 'concluído'

    @pyqtSlot()
    def enable_close_button(self):
        self.close_button.setEnabled(True)

    @pyqtSlot()
    def on_task_complete(self):
        """
        Atualiza o ícone de "Consolidar Documentos PDFs" quando o processo de consolidação for concluído.
        """
        self.label_consolidar.setText("Consolidar Documentos PDFs concluído.")
        self.icon_label_consolidar.setPixmap(self.icon_done.pixmap(24, 24))  # Altera para o ícone de 'concluído'

        # Oculta a barra de progresso quando o processo for concluído
        self.progress_bar.hide()



class PDFAddDialog(QDialog):

    def __init__(self, df_registro_selecionado, icons_dir, pastas_necessarias, pasta_base, parent=None):
        super().__init__(parent)
        self.df_registro_selecionado = df_registro_selecionado
        self.ICONS_DIR = Path(icons_dir)
        self.pastas_necessarias = pastas_necessarias
        self.pasta_base = pasta_base
        self.icon_existe = QIcon(str(self.ICONS_DIR / "checked.png"))
        self.icon_nao_existe = QIcon(str(self.ICONS_DIR / "cancel.png"))
        self.id_processo = df_registro_selecionado['id_processo'].iloc[0]
        self.tipo = df_registro_selecionado['tipo'].iloc[0]
        self.ano = df_registro_selecionado['ano'].iloc[0]
        self.numero = df_registro_selecionado['numero'].iloc[0]
        self.objeto = df_registro_selecionado['objeto'].iloc[0]  # Supondo que 'objeto' é uma coluna no DataFrame
        self.setWindowTitle('Adicionar PDF')
        self.setup_ui()

    def setup_ui(self):
        self.setFixedSize(1520, 780)  # Tamanho ajustado para acomodar todos os componentes

        # Layout principal vertical
        main_layout = QVBoxLayout(self)

        # Layout para a visualização, slider e QTreeWidget
        view_and_slider_and_tree_layout = QHBoxLayout()
        # Layout vertical para a visualização do PDF e botões de navegação
        pdf_view_layout = QVBoxLayout()

        # DraggableGraphicsView para visualizar o PDF
        self.pdf_view = DraggableGraphicsView()
        self.scene = QGraphicsScene()
        self.pdf_view.setScene(self.scene)
        self.pdf_view.setFixedSize(1000, 730)  # Tamanho da visualização do PDF
        pdf_view_layout.addWidget(self.pdf_view)

        # Botões de navegação de páginas abaixo da visualização do PDF
        navigation_widget = QWidget()
        nav_buttons_layout = QHBoxLayout(navigation_widget)
        
        self.prev_page_button = QPushButton("← Página Anterior")
        self.prev_page_button.clicked.connect(self.prev_page)

        # Inicializa o QLabel para o contador de páginas
        self.page_label = QLabel("1 de 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("font-size: 14px; margin: 5px;")

        self.next_page_button = QPushButton("Próxima Página →")
        self.next_page_button.clicked.connect(self.next_page)

        # Adiciona os botões e o QLabel ao layout de navegação
        nav_buttons_layout.addWidget(self.prev_page_button)
        nav_buttons_layout.addWidget(self.page_label, 1)  # O argumento 1 faz com que o QLabel expanda para preencher o espaço
        nav_buttons_layout.addWidget(self.next_page_button)

        # Define o tamanho máximo para o widget de navegação
        navigation_widget.setMaximumWidth(980)

        # Adiciona o widget de navegação ao layout principal
        pdf_view_layout.addWidget(navigation_widget)

        # Adiciona o layout da visualização do PDF ao layout horizontal
        view_and_slider_and_tree_layout.addLayout(pdf_view_layout)
        
        # Slider de Zoom ao lado da visualização
        self.zoom_slider = QSlider(Qt.Orientation.Vertical)
        self.zoom_slider.setMinimum(50)  # 50% do zoom original
        self.zoom_slider.setMaximum(200)  # 200% do zoom original
        self.zoom_slider.setValue(50)  # Valor inicial do zoom (50%)
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.zoom_slider.setTickInterval(10)
        self.zoom_slider.valueChanged.connect(self.adjust_zoom)
        view_and_slider_and_tree_layout.addWidget(self.zoom_slider)

        # Layout vertical para o QTreeWidget e seus botões
        tree_layout = QVBoxLayout()

        # Cria e adiciona o cabeçalho acima do QTreeWidget
        header_widget = self.create_header()
        tree_layout.addWidget(header_widget)

        # QTreeWidget para exibir dados
        self.data_view = QTreeWidget()
        self.data_view.setHeaderHidden(True)
        self.data_view.setStyleSheet("""
            QTreeWidget::item { 
                height: 40px;
                font-size: 14px;
            }
        """)
        self.data_view.itemClicked.connect(self.display_pdf)
        tree_layout.addWidget(self.data_view)

        # Adiciona o layout do QTreeWidget ao layout horizontal principal
        view_and_slider_and_tree_layout.addLayout(tree_layout)

        # Adiciona o layout combinado ao layout principal
        main_layout.addLayout(view_and_slider_and_tree_layout)

        self.add_initial_items()

    def adjust_zoom(self, value):
        # Calcula o fator de escala baseado no valor do slider
        scale_factor = max(value / 100.0, 0.2)  # Garante que o fator de escala não seja menor que 0.5
        # Reseta a transformação atual e aplica o novo zoom
        self.pdf_view.resetTransform()
        self.pdf_view.scale(scale_factor, scale_factor)

    def verificar_arquivo_pdf(self, pasta):
        arquivos_pdf = []
        if not pasta.exists():
            print(f"Pasta não encontrada: {pasta}")
            return 'no_pdf', None  # Retorna uma tupla quando a pasta não é encontrada
        for arquivo in pasta.iterdir():
            if arquivo.suffix.lower() == ".pdf":
                arquivos_pdf.append(arquivo)
                print(f"Arquivo PDF encontrado: {arquivo.name}")
        
        # Verifica se há mais de um PDF na pasta
        if len(arquivos_pdf) > 1:
            print(f"Mais de um arquivo PDF encontrado na pasta: {pasta}")
            return 'multiple_pdfs', arquivos_pdf
        elif arquivos_pdf:
            pdf_mais_recente = max(arquivos_pdf, key=lambda p: p.stat().st_mtime)
            print(f"PDF mais recente: {pdf_mais_recente}")
            return 'single_pdf', pdf_mais_recente
        return 'no_pdf', None  # Garante que retorne uma tupla quando não há PDFs
   
    def display_pdf(self, item, column):
        file_path = item.data(0, Qt.ItemDataRole.UserRole)

        # Verifica se o caminho do arquivo é uma lista (múltiplos PDFs)
        if isinstance(file_path, list):
            # Ordena os arquivos pela data de modificação e pega o mais recente
            file_path = max(file_path, key=lambda p: os.path.getmtime(p))

        if file_path:
            print(f"Tentando abrir o arquivo PDF mais recente: {file_path}")
            self.load_pdf(file_path)

    def load_pdf(self, file_path):
        try:
            self.document = fitz.open(file_path) 
            self.current_page = 0  # Define a primeira página como a atual
            self.show_page(self.current_page)  # Mostra a primeira página
        except Exception as e:
            print(f"Erro ao abrir o arquivo PDF: {e}")

    def show_page(self, page_number):
        if self.document:
            page = self.document.load_page(page_number)
            mat = fitz.Matrix(5, 5)  # Ajuste para a escala desejada, mantém alta qualidade
            pix = page.get_pixmap(matrix=mat)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            self.scene.clear()
            self.scene.addPixmap(pixmap)
            # Aplica o fator de escala inicial de 50%
            self.pdf_view.resetTransform()
            self.pdf_view.scale(0.5, 0.5)
            # Atualiza o contador de páginas
            self.page_label.setText(f"{page_number + 1} de {self.document.page_count}")

    def next_page(self):
        if self.document and self.current_page < self.document.page_count - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def prev_page(self):
        if self.document and self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

    def select_pdf_file(self):
        selected_item = self.data_view.currentItem()
        if selected_item:
            file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar PDF", "", "PDF Files (*.pdf)")
            if file_path:
                selected_item.setText(0, selected_item.text(0))  # Atualiza o texto sem o caminho
                selected_item.setIcon(0, self.icon_existe)
                selected_item.setData(0, Qt.ItemDataRole.UserRole, file_path)  # Armazena o caminho do PDF
                self.save_file_paths()
            else:
                selected_item.setIcon(0, self.icon_nao_existe)

    def create_header(self):
        html_text = f"Anexos da {self.tipo} nº {self.numero}/{self.ano}<br>"
        
        self.titleLabel = QLabel()
        self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
        self.titleLabel.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.titleLabel.setText(html_text)

        self.header_layout = QHBoxLayout()
        self.header_layout.addWidget(self.titleLabel)

        header_widget = QWidget()
        header_widget.setLayout(self.header_layout)

        return header_widget

    def add_initial_items(self):
        id_processo_modificado = self.id_processo.replace("/", "-")
        objeto_modificado = self.objeto.replace("/", "-")
        base_path = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}'

        initial_items = {
            "DFD": [
                ("Anexo A - Relatório Safin", base_path / '2. CP e anexos' / 'DFD' / 'Anexo A - Relatorio Safin'),
                ("Anexo B - Especificações e Quantidade", base_path / '2. CP e anexos' / 'DFD' / 'Anexo B - Especificações e Quantidade')
            ],
            "TR": [
                ("Pesquisa de Preços", base_path / '2. CP e anexos' / 'TR' / 'Pesquisa de Preços')
            ],
            "Declaração de Adequação Orçamentária": [
                ("Relatório do PDM-Catser", base_path / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária' / 'Relatório do PDM-Catser')
            ]
        }

        for parent_text, children in initial_items.items():
            parent_item = QTreeWidgetItem(self.data_view, [parent_text])
            parent_item.setFont(0, QFont('SansSerif', 14))
            for child_text, pasta in children:
                child_item = QTreeWidgetItem(parent_item, [child_text])
                child_item.setForeground(0, QBrush(QColor(0, 0, 0)))
                child_item.setFont(0, QFont('SansSerif', 14))

                print(f"Verificando pasta: {pasta}")
                result, pdf_files = self.verificar_arquivo_pdf(pasta) or ('no_pdf', None)
                
                # Criação do layout do widget e botão de merge
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                label = QLabel(child_text)
                item_layout.addWidget(label)

                if result == 'multiple_pdfs':
                    merge_button = QPushButton("Merge PDFs")
                    merge_button.clicked.connect(lambda _, p=pdf_files: self.open_merge_dialog(p))  # Conectar ao diálogo de merge
                    item_layout.addWidget(merge_button)

                item_layout.addStretch()
                item_widget.setLayout(item_layout)
                self.data_view.setItemWidget(child_item, 0, item_widget)

                # Definir ícones
                if result == 'multiple_pdfs':
                    child_item.setIcon(0, QIcon(str(self.ICONS_DIR / "multiple_pdfs.png")))
                    child_item.setData(0, Qt.ItemDataRole.UserRole, pdf_files)
                elif result == 'single_pdf':
                    child_item.setIcon(0, self.icon_existe)
                    child_item.setData(0, Qt.ItemDataRole.UserRole, str(pdf_files))
                else:
                    child_item.setIcon(0, self.icon_nao_existe)

            parent_item.setExpanded(True)


    def open_merge_dialog(self, pdf_files):
        if isinstance(pdf_files, list) and len(pdf_files) > 1:
            # Abrir QDialog para realizar o merge dos arquivos PDF
            merge_dialog = MergePDFDialog(pdf_files, self)
            merge_dialog.exec()
        else:
            QMessageBox.information(self, "Merge PDFs", "Não há múltiplos arquivos PDF para mesclar.")


class DraggableGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self._panning = False
        self._last_mouse_position = QPoint()
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)  # Zoom focalizado no cursor do mouse

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._panning = True
            self._last_mouse_position = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.pos() - self._last_mouse_position
            self._last_mouse_position = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:  # Verifica se o Ctrl está pressionado
            factor = 1.15 if event.angleDelta().y() > 0 else 0.85  # Ajusta o fator de zoom baseado na direção do scroll
            scale = self.transform().m11() * factor
            if scale >= 0.1:  # Garante que o fator de escala não seja menor que 0.5
                self.scale(factor, factor)
        else:
            super().wheelEvent(event) 

CONFIG_FILE = 'config.json'

def load_config_path_id():
    if not Path(CONFIG_FILE).exists():
        return {}
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

class ConsolidarDocumentos:
    def __init__(self, df_registro_selecionado):
        self.df_registro_selecionado = df_registro_selecionado
        self.config = load_config_path_id()
        self.pasta_base = Path(self.config.get('pasta_base', str(Path.home() / 'Desktop')))
        self.id_processo = self.df_registro_selecionado['id_processo'].iloc[0]
        self.objeto = self.df_registro_selecionado['objeto'].iloc[0]
        self.ICONS_DIR = ICONS_DIR  # Atualize com o caminho real

        # Exemplo de dados de índice
        self.data = {
            'id_processo': 'DE 15/2024',
            'tipo': 'DE',
            'numero': '50',
            'ano': '2024',
            'situacao': 'Planejamento, Sessão Pública, Concluído',
            'nup': '62055.00055/2024-01',
            'material_servico': 'Material ou Serviço',
            'objeto': 'Suprimentos de informática',
            'vigencia': '12 meses a partir da assinatura',
            'data_sessao': '15/10/2024',
            'operador': 'João da Silva',
            'criterio_julgamento': 'Menor preço, Técnica e preço',
            'com_disputa': 'Sim, Não',
            'pesquisa_preco': 'Sim, Não',
            'previsao_contratacao': 'Exemplo: Novembro de 2024',
            'uasg': 'Exemplo: 110155',
            'orgao_responsavel': 'Exemplo: Ministério da Economia',
            'sigla_om': 'Exemplo: ME',
            'setor_responsavel': 'Exemplo: Departamento de Compras',
            'responsavel_pela_demanda': 'Exemplo: Maria de Souza',
            'ordenador_despesas': 'Exemplo: Carlos Ferreira',
            'agente_fiscal': 'Exemplo: Ana Paula',
            'gerente_de_credito': 'Exemplo: Marcos Lima',
            'cod_par': '123456',
            'prioridade_par': 'Alta',
            'cep': '70040-010',
            'endereco': 'Esplanada dos Ministérios, Bloco P',
            'email': 'contato@orgao.gov.br',
            'telefone': 'Exemplo: (61) 3412-3456',
            'dias_para_recebimento': 'Exemplo: 30 dias úteis',
            'horario_para_recebimento': 'Exemplo: 9h às 17h',
            'valor_total': 'Exemplo: R$ 150.000,00',
            'acao_interna': 'Exemplo: Verificação de conformidade',
            'fonte_recursos': 'Exemplo: Tesouro Nacional',
            'natureza_despesa': 'Exemplo: Material de Consumo',
            'unidade_orcamentaria': 'Exemplo: 20203',
            'programa_trabalho_resuminho': 'Exemplo: Apoio Administrativo',
            'atividade_custeio': 'Exemplo: Manutenção Predial',
            'comentarios': 'Exemplo: Necessidade urgente devido ao fim do estoque',
            'justificativa': 'Exemplo: Demanda emergencial para continuidade dos serviços',
            'link_pncp': 'Exemplo: https://www.gov.br/compras',
            'comunicacao_padronizada': 'Exemplo: E-mail institucional',
            'modalidade_licitacao': 'Exemplo: Pregão Eletrônico',
            'justificativa_dispensa': 'Exemplo: Situação de emergência',
            'fundamento_legal': 'Exemplo: Art. 24, Inciso IV da Lei 8.666/93',
            'numero_processo': 'Exemplo: 001/2024',
            'data_processo': 'Exemplo: 01/01/2024',
            'nome_empresa': 'Exemplo: Empresa XYZ Ltda.',
            'cnpj_empresa': 'Exemplo: 12.345.678/0001-90',
            'endereco_empresa': 'Exemplo: Rua Exemplo, 123 - Brasília, DF',
            'email_empresa': 'Exemplo: contato@empresaxyz.com.br',
            'telefone_empresa': 'Exemplo: (61) 9999-8888',
            'representante_legal': 'Exemplo: Pedro Alves',
            'cpf_representante': 'Exemplo: 123.456.789-10',
            'cargo_representante': 'Exemplo: Diretor Comercial',
            'valor_estimado': 'Exemplo: R$ 100.000,00',
            'prazo_execucao': 'Exemplo: 60 dias',
            'garantia_contratual': 'Exemplo: 5% do valor contratado',
            'observacoes': 'Exemplo: Contrato deve ser assinado em até 5 dias úteis após homologação',
            'data_inicio': 'Exemplo: 01/03/2024',
            'data_fim': 'Exemplo: 28/02/2025',
            'duracao_contrato': 'Exemplo: 12 meses',
            'metodologia': 'Exemplo: Metodologia de aquisição por pregão eletrônico',
            'resultados_esperados': 'Exemplo: Aquisição de 100 computadores em até 30 dias',
            'plano_trabalho': 'Exemplo: Definido conforme Termo de Referência',
            'cronograma': 'Exemplo: Entrega prevista para o segundo trimestre de 2024',
            'responsavel_execucao': 'Exemplo: José Martins',
            'medidas_mitigacao': 'Exemplo: Monitoramento contínuo do contrato',
            'risco_identificado': 'Exemplo: Atraso na entrega dos itens',
            'plano_contingencia': 'Exemplo: Recurso a outro fornecedor em caso de inadimplência',
            'autoridade_licitante': 'Exemplo: Diretor de Compras',
            'data_aprovacao': 'Exemplo: 15/02/2024',
            'assinatura_autoridade': 'Exemplo: Assinatura digitalizada do Diretor de Compras'
        }

    def editar_modelo(self, button_font_size=18, icon_size=QSize(40, 40)):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Template")
        
        # Adicionar ícone ao título
        icon_confirm = QIcon(str(self.ICONS_DIR / "confirm_green.png"))
        dialog.setWindowIcon(icon_confirm)

        # Ícones para os botões
        icon_index = QIcon(str(self.ICONS_DIR / "pdf.png"))  # Ícone para "Abrir índice"
        icon_open = QIcon(str(self.ICONS_DIR / "open_icon.png"))  # Ícone para os demais botões "Abrir"

        # Layout principal do diálogo
        main_layout = QVBoxLayout(dialog)
        
        # Layout horizontal para o botão "Abrir índice"
        top_layout = QHBoxLayout()
        button_open_index = QPushButton("Índice")
        button_open_index.setIcon(icon_index)
        button_open_index.setFixedSize(110, 40)  # Definir tamanho fixo para uniformidade
        button_open_index.setIconSize(icon_size)  # Ajusta o tamanho do ícone
        button_open_index.setStyleSheet("font-size: 18px;")  # Ajusta o tamanho da fonte
        button_open_index.clicked.connect(self.abrir_indice)
        
        # Adicionar o texto ao lado do botão "Abrir índice"
        label_info = QLabel("Relação de Variáveis e exemplos de uso")
        label_info.setStyleSheet("font-size: 18px;")  # Definir tamanho da fonte para 14

        top_layout.addWidget(button_open_index, alignment=Qt.AlignmentFlag.AlignLeft)
        top_layout.addWidget(label_info, alignment=Qt.AlignmentFlag.AlignLeft)
        
        top_layout.addStretch()
        # Layout para os templates
        templates_layout = QVBoxLayout()

        # Lista de templates e seus caminhos
        templates = [
            ("Template Autorização", TEMPLATE_DISPENSA_DIR / "template_autorizacao_dispensa.docx"),
            ("Template Comunicação Padronizada", TEMPLATE_DISPENSA_DIR / "template_cp.docx"),
            ("Template DFD", TEMPLATE_DISPENSA_DIR / "template_dfd.docx"),
            ("Template Termo de Referência", TEMPLATE_DISPENSA_DIR / "template_tr.docx"),
            ("Template Declaração de Adequação Orçamentária", TEMPLATE_DISPENSA_DIR / "template_dec_adeq.docx"),
            ("Template Aviso de Dispensa", TEMPLATE_DISPENSA_DIR / "template_aviso_dispensa.docx")
        ]

        # Adicionar os templates ao layout
        for template_name, template_path in templates:
            template_row = QHBoxLayout()
            
            label = QLabel(template_name)
            label.setStyleSheet("font-size: 18px;")  # Definir tamanho da fonte para 14
            button_open_template = QPushButton("Abrir")
            button_open_template.setIcon(icon_open)
            button_open_template.setFixedSize(110, 40)  # Definir tamanho fixo para uniformidade
            button_open_template.setIconSize(icon_size)  # Ajusta o tamanho do ícone
            button_open_template.setStyleSheet("font-size: 18px;")  # Ajusta o tamanho da fonte
            button_open_template.clicked.connect(lambda _, path=template_path: self.abrir_template(path))
            
            template_row.addWidget(button_open_template)
            template_row.addWidget(label)
            templates_layout.addLayout(template_row)

        # Adicionar layouts ao layout principal
        main_layout.addLayout(top_layout)
        main_layout.addLayout(templates_layout)

        dialog.setLayout(main_layout)
        dialog.exec()

    def abrir_template(self, path):
        # Verificar se o arquivo existe
        if path.exists() and path.is_file():
            print(f"Arquivo encontrado: {path}")
            try:
                # Abre o arquivo utilizando o caminho absoluto
                full_path = str(path.resolve())  # Resolve para o caminho absoluto
                subprocess.run(f'start "" "{full_path}"', shell=True)  # Windows
                # Para Linux ou macOS, use os comandos adequados
                # subprocess.run(['xdg-open', full_path])  # Linux
                # subprocess.run(['open', full_path])  # macOS
            except Exception as e:
                print(f"Erro ao abrir o template: {e}")
        else:
            print(f"Arquivo não encontrado: {path}")

    def abrir_indice(self):
        # Cria o PDF dos índices
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Adicionar título
        pdf.cell(200, 10, txt="Índices Utilizados nos Templates", ln=True, align='C')

        # Adicionar exemplos de cada índice com cores personalizadas
        for key, example in self.data.items():
            # Definir cor para o 'key' (azul marinho)
            pdf.set_text_color(0, 0, 128)  # Azul marinho (RGB: 0, 0, 128)
            pdf.write(10, f"{{{{{key}}}}}: ")

            # Definir cor para o 'example' (vermelho escuro)
            pdf.set_text_color(139, 0, 0)  # Vermelho escuro (RGB: 139, 0, 0)
            pdf.write(10, f"Exemplo: {example}\n")  # Adiciona texto com nova linha

        # Salva o PDF
        pdf_path = self.pasta_base / "indice_templates.pdf"
        pdf.output(str(pdf_path))

        print(f"Arquivo PDF de índices criado: {pdf_path}")

        # Abrir o PDF criado
        if pdf_path.exists() and pdf_path.is_file():
            try:
                subprocess.run(f'start "" "{str(pdf_path)}"', shell=True)  # Windows
                # Para Linux ou macOS, use os comandos adequados
                # subprocess.run(['xdg-open', str(pdf_path)])  # Linux
                # subprocess.run(['open', str(pdf_path)])  # macOS
            except Exception as e:
                print(f"Erro ao abrir o PDF de índices: {e}")
        else:
            print(f"Arquivo PDF de índices não encontrado: {pdf_path}")



    def alterar_diretorio_base(self):
        new_dir = QFileDialog.getExistingDirectory(None, "Selecione o Novo Diretório Base", str(Path.home()))
        if new_dir:
            self.pasta_base = Path(new_dir)
            self.config['pasta_base'] = str(self.pasta_base)
            save_config(self.config)
            QMessageBox.information(None, "Diretório Base Alterado", f"O novo diretório base foi alterado para: {self.pasta_base}")

    def abrir_pasta_base(self):
        try:
            os.startfile(self.pasta_base)
        except Exception as e:
            print(f"Erro ao abrir a pasta base: {e}")
            QMessageBox.warning(None, "Erro", f"Erro ao abrir a pasta base: {e}")

    def abrirDocumento(self, docx_path):
        try:
            pdf_path = self.convert_to_pdf(docx_path)
            os.startfile(pdf_path)
            print(f"Documento PDF aberto: {pdf_path}")
        except Exception as e:
            print(f"Erro ao abrir ou converter o documento: {e}")
            QMessageBox.warning(None, "Erro", f"Erro ao abrir ou converter o documento: {e}")

    def salvarPDF(self, docx_path):
        try:
            pdf_path = self.convert_to_pdf(docx_path)
            print(f"Documento PDF salvo: {pdf_path}")
            return pdf_path
        except Exception as e:
            print(f"Erro ao converter o documento: {e}")
            QMessageBox.warning(None, "Erro", f"Erro ao converter o documento: {e}")
            return None

    def convert_to_pdf(self, docx_path):
        docx_path = Path(docx_path) if not isinstance(docx_path, Path) else docx_path
        pdf_path = docx_path.with_suffix('.pdf')
        word = win32com.client.Dispatch("Word.Application")
        doc = None
        try:
            doc = word.Documents.Open(str(docx_path))
            doc.SaveAs(str(pdf_path), FileFormat=17)
        except Exception as e:
            raise e
        finally:
            if doc is not None:
                doc.Close()
            word.Quit()
        if not pdf_path.exists():
            raise FileNotFoundError(f"O arquivo PDF não foi criado: {pdf_path}")
        return pdf_path

    def valor_por_extenso(self, valor):
        if not valor or valor.strip() == '':  # Verifica se o valor está vazio ou None
            return None  # Retorna None se o valor não for válido

        try:
            valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
            valor_float = float(valor)
            parte_inteira = int(valor_float)
            parte_decimal = int(round((valor_float - parte_inteira) * 100))

            if parte_decimal > 0:
                valor_extenso = f"{num2words(parte_inteira, lang='pt_BR')} reais e {num2words(parte_decimal, lang='pt_BR')} centavos"
            else:
                valor_extenso = f"{num2words(parte_inteira, lang='pt_BR')} reais"

            # Corrige "um reais" para "um real"
            valor_extenso = valor_extenso.replace("um reais", "um real")

            return valor_extenso

        except ValueError:
            return None

    def alterar_posto(self, posto):
        # Define um dicionário de mapeamento de postos e suas respectivas abreviações
        mapeamento_postos = {
            r'Capitão[\s\-]de[\s\-]Corveta': 'CC',
            r'Capitão[\s\-]de[\s\-]Fragata': 'CF',
            r'Capitão[\s\-]de[\s\-]Mar[\s\-]e[\s\-]Guerra': 'CMG',
            r'Capitão[\s\-]Tenente': 'CT',
            r'Primeiro[\s\-]Tenente': '1ºTen',
            r'Segundo[\s\-]Tenente': '2ºTen',
            r'Primeiro[\s\-]Sargento': '1ºSG',
            r'Segundo[\s\-]Sargento': '2ºSG',
            r'Terceiro[\s\-]Sargento': '3ºSG',
            r'Cabo': 'CB',
            r'Sub[\s\-]oficial': 'SO',
        }

        # Itera sobre o dicionário de mapeamento e aplica a substituição
        for padrao, substituicao in mapeamento_postos.items():
            if re.search(padrao, posto, re.IGNORECASE):
                return re.sub(padrao, substituicao, posto, flags=re.IGNORECASE)

        # Retorna o posto original se nenhuma substituição for aplicada
        return posto

    def formatar_responsavel(self, chave, data, context):
        responsavel = data.get(chave)
        if responsavel and isinstance(responsavel, str):
            try:
                nome, posto, funcao = responsavel.split('\n')
                posto_alterado = self.alterar_posto(posto)
                responsavel_dict = {
                    'nome': nome,
                    'posto': posto_alterado,
                }
                responsavel_extenso = f"{responsavel_dict.get('posto', '')} {responsavel_dict.get('nome', '')}"
                context.update({f'{chave}_formatado': responsavel_extenso})
            except ValueError:
                context.update({f'{chave}_formatado': 'Não especificado\nNão especificado'})
        else:
            context.update({f'{chave}_formatado': 'Não especificado\nNão especificado'})

    def prepare_context(self, data):
        context = {key: (str(value) if value is not None else 'Não especificado') for key, value in data.items()}
        descricao_servico = "aquisição de" if data['material_servico'] == "Material" else "contratação de empresa especializada em"
        descricao_servico_primeira_letra_maiuscula = descricao_servico[0].upper() + descricao_servico[1:]
        context.update({'descricao_servico': descricao_servico})
        context.update({'descricao_servico_primeira_letra_maiuscula': descricao_servico_primeira_letra_maiuscula})

        # Processar responsável pela demanda e operador
        self.formatar_responsavel('responsavel_pela_demanda', data, context)
        self.formatar_responsavel('operador', data, context)

        valor_total = data.get('valor_total')
        if valor_total and isinstance(valor_total, str):
            valor_extenso = self.valor_por_extenso(valor_total)
            valor_total_e_extenso = f"{valor_total} ({valor_extenso})"
            context.update({'valor_total_e_extenso': valor_total_e_extenso})
        else:
            context.update({'valor_total_e_extenso': 'Não especificado'})

        # Lógica para atividade_custeio
        if data.get('atividade_custeio') == 'Sim':
            texto_custeio = (
                "A presente contratação por dispensa de licitação está enquadrada como atividade de custeio, "
                "conforme mencionado no artigo 2º da Portaria ME nº 7.828, de 30 de agosto de 2022. "
                "Conforme previsão do art. 3º do Decreto nº 10.193, de 27 de dezembro de 2019, e as normas "
                "infralegais de delegação de competência no âmbito da Marinha, que estabelecem limites e instâncias "
                "de governança, essa responsabilidade é delegada ao ordenador de despesas, respeitando os valores "
                "estipulados no decreto."
            )
        else:
            texto_custeio = (
                "A presente contratação por dispensa de licitação não se enquadra nas hipóteses de atividades de "
                "custeio previstas no Decreto nº 10.193, de 27 de dezembro de 2019, pois o objeto contratado não se "
                "relaciona diretamente às atividades comuns de suporte administrativo mencionadas no artigo 2º da "
                "Portaria ME nº 7.828, de 30 de agosto de 2022."
            )
        context.update({'texto_custeio': texto_custeio})

        # Alterar formato de data_sessao
        data_sessao = data.get('data_sessao')
        if data_sessao:
            try:
                data_obj = datetime.strptime(data_sessao, '%Y-%m-%d')
                dia_semana = data_obj.strftime('%A')
                data_formatada = data_obj.strftime('%d/%m/%Y') + f" ({dia_semana})"
                context.update({'data_sessao_formatada': data_formatada})
            except ValueError as e:
                context.update({'data_sessao_formatada': 'Data inválida'})
                print("Erro ao processar data da sessão:", e)
        else:
            context.update({'data_sessao_formatada': 'Não especificado'})
            print("Data da sessão não especificada")

        return context

    def gerarDocumento(self, template_type, subfolder_name, file_description):
        if self.df_registro_selecionado.empty:
            QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
            return

        template_filename = f"template_{template_type}.docx"
        template_path, save_path = self.setup_document_paths(template_filename, subfolder_name, file_description)

        self.verificar_e_criar_pastas(self.pasta_base / self.nome_pasta)

        if not template_path.exists():
            QMessageBox.warning(None, "Erro de Template", f"O arquivo de template não foi encontrado: {template_path}")
            return

        with open(str(template_path), 'rb') as template_file:
            doc = DocxTemplate(template_file)
            context = self.df_registro_selecionado.to_dict('records')[0]
            context = self.prepare_context(context)
            doc.render(context)
            doc.save(str(save_path))
        return save_path

    def setup_document_paths(self, template_filename, subfolder_name, file_description):
        template_path = TEMPLATE_DISPENSA_DIR / template_filename
        id_processo = self.df_registro_selecionado['id_processo'].iloc[0].replace('/', '-')
        objeto = self.df_registro_selecionado['objeto'].iloc[0]
        self.nome_pasta = f"{id_processo} - {objeto}"
        if 'pasta_base' not in self.config:
            self.alterar_diretorio_base()
        pasta_base = Path(self.config['pasta_base']) / self.nome_pasta / subfolder_name
        pasta_base.mkdir(parents=True, exist_ok=True)
        save_path = pasta_base / f"{id_processo} - {file_description}.docx"
        return template_path, save_path

    def verificar_e_criar_pastas(self, pasta_base):
        id_processo_modificado = self.id_processo.replace("/", "-")
        objeto_modificado = self.objeto.replace("/", "-")
        base_path = pasta_base / f'{id_processo_modificado} - {objeto_modificado}'

        pastas_necessarias = [
            pasta_base / '1. Autorizacao',
            pasta_base / '2. CP e anexos',
            pasta_base / '3. Aviso',
            pasta_base / '2. CP e anexos' / 'DFD',
            pasta_base / '2. CP e anexos' / 'DFD' / 'Anexo A - Relatorio Safin',
            pasta_base / '2. CP e anexos' / 'DFD' / 'Anexo B - Especificações e Quantidade',
            pasta_base / '2. CP e anexos' / 'TR',
            pasta_base / '2. CP e anexos' / 'TR' / 'Pesquisa de Preços',
            pasta_base / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária',
            pasta_base / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária' / 'Relatório do PDM-Catser',
            pasta_base / '2. CP e anexos' / 'Justificativas Relevantes',
        ]
        for pasta in pastas_necessarias:
            if not pasta.exists():
                pasta.mkdir(parents=True)
        return pastas_necessarias
        
    def gerar_e_abrir_documento(self, template_type, subfolder_name, file_description):
        docx_path = self.gerarDocumento(template_type, subfolder_name, file_description)
        if docx_path:
            self.abrirDocumento(docx_path)

    def gerar_autorizacao(self):
        self.gerar_e_abrir_documento("autorizacao_dispensa", "1. Autorizacao", "Autorizacao para abertura de Processo Administrativo")

    def gerar_comunicacao_padronizada(self):
        documentos = [
            {"template": "cp", "subfolder": "2. CP e anexos", "desc": "Comunicacao Padronizada"},
            {"template": "dfd", "subfolder": "2. CP e anexos/DFD", "desc": "Documento de Formalizacao de Demanda", "cover": "dfd.pdf"},
            {"subfolder": "2. CP e anexos/DFD/Anexo A - Relatorio Safin", "cover": "anexo-a-dfd.pdf"},
            {"subfolder": "2. CP e anexos/DFD/Anexo B - Especificações e Quantidade", "cover": "anexo-b-dfd.pdf"},
            {"template": "tr", "subfolder": "2. CP e anexos/TR", "desc": "Termo de Referencia", "cover": "tr.pdf"},
            {"subfolder": "2. CP e anexos/TR/Pesquisa de Preços", "cover": "anexo-tr.pdf"},
            {"template": "dec_adeq", "subfolder": "2. CP e anexos/Declaracao de Adequação Orçamentária", "desc": "Declaracao de Adequação Orçamentária", "cover": "dec_adeq.pdf"},
            {"subfolder": "2. CP e anexos/Declaracao de Adequação Orçamentária/Relatório do PDM-Catser", "cover": "anexo-dec-adeq.pdf"},
            {"template": "justificativas", "subfolder": "2. CP e anexos/Justificativas Relevantes", "desc": "Justificativas Relevantes", "cover": "justificativas.pdf"},
        ]
        
        # Certifique-se de passar o df_registro_selecionado aqui
        dialog = ProgressDialog(documentos, self.df_registro_selecionado)
        dialog.exec()  

    def gerar_documento_de_formalizacao_de_demanda(self):
        self.gerarDocumento("dfd", "2. CP e anexos/DFD", "Documento de Formalizacao de Demanda")

    def gerar_declaracao_orcamentaria(self):
        self.gerarDocumento("declaracao_orcamentaria", "2. CP e anexos/Declaracao de Adequação Orçamentária", "Declaracao Orcamentaria")

    def gerar_termo_de_referencia(self):
        self.gerarDocumento("tr", "2. CP e anexos/TR", "Termo de Referencia")

    def gerar_aviso_dispensa(self):
        self.gerar_e_abrir_documento("aviso_dispensa", "3. Aviso", "Aviso de Dispensa")
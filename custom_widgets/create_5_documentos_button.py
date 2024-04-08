from PyQt6.QtWidgets import QWidget, QPushButton, QApplication, QDialog, QVBoxLayout, QLabel, QHBoxLayout, QToolButton, QSizePolicy, QGridLayout
from PyQt6.QtCore import Qt, QPoint, QSize, QRect, QLineF, QPointF
from PyQt6.QtGui import QPainter, QPen, QIcon, QPolygonF
from diretorios import *
import os

class DocumentosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        # Adicionando ProcessoLicitacaoWidget ao layout
        self.processo_widget = ProcessoLicitacaoWidget()
        self.layout.addWidget(self.processo_widget)

    def get_content_widget(self):
        # Retorna o widget que contém os botões e setas do processo de licitação
        return self.processo_widget

# Títulos dos botões
button_titles = [
    ("Autorização\npara Abertura\nde Licitação", "aut", "Autorização para Abertura de Licitação"),
    ("Portaria de\nEquipe de\nPlanejamento", "port", "Portaria de Equipe de Planejamento"),
    ("Documento de\nFormalização\nde Demanda\n(DFD)", "dfd", "Documento de Formalização de Demanda (DFD)"),
    ("Estudo Técnico\nPreliminar\n(ETP)", "etp", "Estudo Técnico Preliminar (ETP)"),
    ("Matriz\nde Riscos", "mr", "Matriz de Riscos"),
    ("Declaração de\nAdequação\nOrçamentária", "dec_adeq", "Declaração de Adequação Orçamentária"),
    ("Intenção de\nRegistro de\nPreços (IRP)", "irp", "Intenção de Registro de Preços (IRP)"),
    ("Termo de\nReferência", "tr", "Termo de Referência"),
    ("Edital", "edital", "Edital")
]

class ProcessoLicitacaoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        # Definindo o layout como um QGridLayout para melhor controle dos widgets
        self.grid_layout = QGridLayout(self)

        # Adicionar os botões ao layout da grade
        positions = [
            (0, 0),  # Autorização para Abertura de Licitação
            (0, 1),  # Portaria de Equipe de Planejamento
            (0, 2),  # Documento de Formalização de Demanda (DFD)
            (1, 0),  # Estudo Técnico Preliminar (ETP)
            (1, 1),  # Matriz de Riscos
            (1, 2),  # Declaração de Adequação Orçamentária
            (2, 0),  # Intenção de Registro de Preços (IRP)
            (2, 1),  # Termo de Referência
            (2, 2),   # Edital
            # (3, 0),   # Edital
            # (3, 1),   # Edital
            # (3, 2)   # Edital
        ]

        # Definir o ícone para os botões
        icon_path = ICONS_DIR / "docx_menu.png"  # Certifique-se de que este caminho está correto

        for i, (row, col) in enumerate(positions):
            btn = QToolButton(self)
            btn.setText(button_titles[i][0])
            btn.setIcon(QIcon(str(icon_path)))
            btn.setIconSize(QSize(60, 60))
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

            # Estilo do botão com fundo azul ciano transparente, bordas arredondadas e espaço extra
            btn.setStyleSheet("""
                QToolButton {
                    font-size: 24px;
                    padding-top: 20px;  
                    background-color: rgba(0, 0, 0, 0.5);
                    font-weight: bold;
                    color: white;
                    border-radius: 10px;  
                }
                QToolButton:hover {
                    color: rgb(0, 85, 85); 
                    background-color: rgba(0, 255, 255, 0.6);  
                }
            """)


            # Configuração da política de tamanho e tamanho mínimo/máximo
            btn.setMinimumSize(QSize(200, 200))  # Defina a altura e largura mínimas
            btn.setMaximumSize(QSize(200, 200))  # Defina a altura e largura máximas

            sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

            sizePolicy.setHorizontalStretch(1)
            sizePolicy.setVerticalStretch(1)
            btn.setSizePolicy(sizePolicy)

            # Adicionar o botão à posição especificada na grade
            # Conectar o botão à função ao_clicar_no_icone_documento
            btn.clicked.connect(lambda _, x=i: self.ao_clicar_no_botao(x))

            self.grid_layout.addWidget(btn, row, col)

    def ao_clicar_no_botao(self, index):
        titulo_botao, nome_template, titulo_formatado = button_titles[index]
        ao_clicar_no_icone_documento(nome_template, titulo_formatado)


class ErrorDialog(QDialog):
    def __init__(self, error_message, file_path, parent=None):
        super(ErrorDialog, self).__init__(parent)
        self.file_path = file_path

        self.setWindowTitle("Erro ao Gerar Documento")

        layout = QVBoxLayout(self)

        # Mensagem de erro
        label = QLabel(error_message)
        layout.addWidget(label)

        # Botão para abrir o template
        open_button = QPushButton("Abrir Template", self)
        open_button.clicked.connect(self.open_template)
        layout.addWidget(open_button)

        # Botão de fechar
        close_button = QPushButton("Fechar", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def open_template(self):
        try:
            os.startfile(self.file_path)  # Para Windows
            # Em sistemas não Windows, use:
            # webbrowser.open(self.file_path)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir o arquivo: {e}")


df_licitacao = None

from docxtpl import DocxTemplate
from PyQt6.QtWidgets import QApplication, QMessageBox
import pandas as pd

def carregar_dados_pregao():
    try:
        df = pd.read_csv(ITEM_SELECIONADO_PATH)
        return df
    except Exception as e:
        QMessageBox.warning(None, "Erro", f"Erro ao carregar dados: {e}")
        return None

df_registro_selecionado = carregar_dados_pregao()

def criar_pasta_e_salvar_docx(df, template_path, salvar_nome):
    relatorio_path = get_relatorio_path()
    num_pregao = df['num_pregao'].iloc[0]
    ano_pregao = df['ano_pregao'].iloc[0]

    # Usando formatação de strings para clareza
    nome_dir_principal = f"PE {num_pregao}-{ano_pregao}"
    path_dir_principal = relatorio_path / nome_dir_principal
    if not path_dir_principal.exists():
        path_dir_principal.mkdir(parents=True)

    path_subpasta = path_dir_principal / salvar_nome
    if not path_subpasta.exists():
        path_subpasta.mkdir()

    nome_do_arquivo = f"PE {num_pregao}-{ano_pregao} - {salvar_nome}.docx"
    local_para_salvar = path_subpasta / nome_do_arquivo
    gerar_documento_com_dados(df, template_path, local_para_salvar)

def gerar_documento_com_dados(df, template_path, save_path):
    # Verifica se o arquivo do template existe
    if not os.path.exists(template_path):
        QMessageBox.warning(None, "Erro", f"O arquivo de template '{template_path}' não foi encontrado.")
        return

    try:
        doc = DocxTemplate(template_path)
        data = df.iloc[0].to_dict()
        doc.render(data)
        doc.save(save_path)
    except Exception as e:
        nome_arquivo = os.path.basename(template_path)
        error_message = f"Erro ao gerar documento com o template '{nome_arquivo}': {e}"
        dialog = ErrorDialog(error_message, template_path)
        dialog.exec_()

def safe_format(template, **kwargs):
    class SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"  # Retorna a chave não encontrada como está

    return template.format_map(SafeDict(**kwargs))

def safe_format(template, **kwargs):
    class SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"  # Retorna a chave não encontrada como está

    return template.format_map(SafeDict(**kwargs))

def gerar_txt_com_dados(df, template_path, save_path, salvar_nome):
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()

        data = df.iloc[0].to_dict()
        data['tipo_documento'] = salvar_nome  # Adicionando 'tipo_documento' manualmente

        content = safe_format(template_content, **data)

        with open(save_path, 'w', encoding='utf-8') as file:
            file.write(content)
    except Exception as e:
        QMessageBox.warning(None, "Erro", f"Erro ao manipular arquivo: {e}")


        content = safe_format(template_content, **data)

        with open(save_path, 'w', encoding='utf-8') as file:
            file.write(content)
    except Exception as e:
        QMessageBox.warning(None, "Erro", f"Erro ao manipular arquivo: {e}")

def ao_clicar_no_icone_documento(nome_template, salvar_nome, evento=None):
    relatorio_path = get_relatorio_path()

    df_registro_selecionado = carregar_dados_pregao() 
    if df_registro_selecionado is None or df_registro_selecionado.empty:
        QMessageBox.warning(None, "Aviso", "Por favor, selecione um item primeiro!")
        return
        
    if df_registro_selecionado is not None:
        caminho_template_docx = PASTA_TEMPLATE / f'template_{nome_template}.docx'
        criar_pasta_e_salvar_docx(df_registro_selecionado, caminho_template_docx, salvar_nome)

        # Generating and saving the .txt file
        caminho_template_txt = PASTA_TEMPLATE / 'SIGDEM.txt'
        num_pregao = df_registro_selecionado['num_pregao'].iloc[0]
        ano_pregao = df_registro_selecionado['ano_pregao'].iloc[0]
        nome_do_arquivo_txt = f"PE {num_pregao}-{ano_pregao} - {salvar_nome}.txt"
        path_dir_principal = relatorio_path / f"PE {num_pregao}-{ano_pregao}"
        path_subpasta = path_dir_principal / salvar_nome
        local_para_salvar_txt = path_subpasta / nome_do_arquivo_txt
        
        gerar_txt_com_dados(df_registro_selecionado, caminho_template_txt, local_para_salvar_txt, salvar_nome)

        os.startfile(str(path_subpasta))
        
def ao_clicar_no_icone_pasta():
    relatorio_path = get_relatorio_path()

    df_registro_selecionado = carregar_dados_pregao()  # Carrega os dados mais recentes

    if df_registro_selecionado is None or df_registro_selecionado.empty:
        QMessageBox.warning(None, "Atenção", "Por favor, selecione um item primeiro.")
        return
    
    num_pregao = df_registro_selecionado['num_pregao'].iloc[0]
    ano_pregao = df_registro_selecionado['ano_pregao'].iloc[0]

    # Adicione estas linhas para imprimir os valores e verificar se estão corretos
    print(f"num_pregao: {num_pregao}")
    print(f"ano_pregao: {ano_pregao}")

    nome_diretorio_principal = f"PE {num_pregao}-{ano_pregao}"
    caminho_diretorio_principal = relatorio_path / nome_diretorio_principal

    # Imprima o caminho do diretório para verificar se está correto
    print(f"Caminho do diretório: {caminho_diretorio_principal}")

    if not caminho_diretorio_principal.exists():
        # Cria a pasta se ela não existir
        caminho_diretorio_principal.mkdir(parents=True)

    # Abre a pasta
    os.startfile(caminho_diretorio_principal)

def gerar_todos_documentos(evento=None):
    df_registro_selecionado = carregar_dados_pregao()  # Carrega os dados mais recentes

    if df_registro_selecionado is None or df_registro_selecionado.empty:
        QMessageBox.warning(None, "Atenção", "Por favor, selecione um pregão primeiro.")
        return

    for texto, nome_template in button_titles:
        ao_clicar_no_icone_documento(nome_template, texto, evento)
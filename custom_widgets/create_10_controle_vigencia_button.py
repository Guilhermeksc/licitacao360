# create_contratos_button.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QTreeView, QLabel, QHBoxLayout, 
    QPushButton, QHeaderView, QDialog, QTextEdit, QApplication
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor, QBrush, QTextOption
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QDate
from diretorios import *
import pandas as pd
import re
from pathlib import Path
from datetime import datetime, timedelta
from styles.styless import get_transparent_title_style

class DetalhesContratoDialog(QDialog):
    def __init__(self, detalhes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mensagem Cobrança")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # Campo de texto editável
        self.textEdit = QTextEdit()
        self.textEdit.setText(detalhes)
        self.textEdit.setReadOnly(False)  # Se desejar que o texto seja editável, defina como False
        layout.addWidget(self.textEdit)

        # Botão para copiar o texto para a área de transferência
        self.btnCopy = QPushButton("Copiar", self)
        self.btnCopy.clicked.connect(self.copyTextToClipboard)
        layout.addWidget(self.btnCopy)

    def copyTextToClipboard(self):
        text = self.textEdit.toPlainText()
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", "Texto copiado para a área de transferência.")

def calcular_prazo_limite(data_fim):
    data_fim_obj = datetime.strptime(data_fim, "%d/%m/%Y")
    prazo_limite = data_fim_obj - timedelta(days=90)

    # Ajusta para o primeiro dia útil anterior se cair em um fim de semana
    while prazo_limite.weekday() > 4:  # 5 = sábado, 6 = domingo
        prazo_limite -= timedelta(days=1)

    return prazo_limite.strftime("%d/%m/%Y")

def formatar_mensagem_contrato(numero_contrato, cnpj, nome_empresa, prazo_limite, fim_vigencia, valor_global):
    mes_atual = datetime.now().strftime("%b").upper()
    ano_atual = datetime.now().strftime("%Y")

    # Usar HTML para formatar o texto e aplicar cor às variáveis
    mensagem = (
        "ROTINA<br>"
        f"R000000Z/<span style='color: blue;'>{mes_atual}</span>/<span style='color: blue;'>{ano_atual}</span><br>"
        "DE NICITB<br>"
        "PARA SETDIS<br>"
        "GRNC<br>"
        "BT<br><br>"
        "Renovação de Contrato Administrativo<br><br>"
        f"VTD proximidade de termo final da vigência do contrato administrativo n° <span style='color: blue;'>{numero_contrato}</span>, de natureza continuada, "
        f"firmado com a empresa <span style='color: blue;'>{nome_empresa}</span>, inscrita no CNPJ: <span style='color: blue;'>{cnpj}</span>, com o valor global de <span style='color: blue;'>{valor_global}</span>, "
        "cujo objeto é xxxxxxxx, CNS PSB:<br><br>"
        "ALFA - INF intenção, ou não, de iniciar os procedimentos para a prorrogação<br>"
        "contratual;<br><br>"
        "BRAVO - Havendo interesse em prorrogar o REF contrato, PTC NEC ENC subsídios<br>"
        f"para referida renovação ao CeIMBra, até <span style='color: blue;'>{prazo_limite}</span>; e<br><br>"
        "CHARLIE - Informações adicionais:<br><br>"
        "UNO - Gestora do contrato: POSTO (ESPECIALIDADE) NOME; e<br><br>"
        f"DOIS - Término da vigência contratual: <span style='color: blue;'>{fim_vigencia}</span> BT"
    )

    return mensagem

# Ler o arquivo CSV
def ler_dados_contratos():
    if Path(CONTRATOS_PATH).exists():
        return pd.read_csv(CONTRATOS_PATH)
    else:
        return pd.DataFrame()  

class ContratosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        label_controle_vigencia = QLabel("Vigência de Contratos")
        label_controle_vigencia.setStyleSheet(get_transparent_title_style())
        self.layout.addWidget(label_controle_vigencia)

        # Configura o QTreeView e carrega os dados
        self.tree_view = QTreeView(self)
        self.layout.addWidget(self.tree_view)
        self.carregarDados()

        # Layout para os botões
        self.buttons_layout = QHBoxLayout()

        # Botão "CP Alerta Prazo"
        self.alerta_prazo_btn = QPushButton("CP Alerta Prazo", self)
        self.buttons_layout.addWidget(self.alerta_prazo_btn)

        # Botão "Mensagem Cobrança"
        self.mensagem_cobranca_btn = QPushButton("Mensagem Cobrança", self)
        self.buttons_layout.addWidget(self.mensagem_cobranca_btn)

        # Adiciona o layout dos botões ao layout principal
        self.layout.addLayout(self.buttons_layout)

        self.mensagem_cobranca_btn.clicked.connect(self.exibirDetalhesContrato)

    def exibirDetalhesContrato(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            row = index.row()
            numero_contrato = self.model.item(row, 1).text()
            fornecedor = self.model.item(row, 2).text()
            fim_vigencia = self.model.item(row, 4).text()
            valor_global = self.model.item(row, 6).text()
            prazo_limite = calcular_prazo_limite(fim_vigencia)

            # Usar expressão regular para encontrar a posição do hífen após o CNPJ
            match = re.search(r'/\d{4}-\d{2}', fornecedor)
            if match:
                posicao_hifen = match.end()
                cnpj = fornecedor[:posicao_hifen].strip()
                nome_empresa = fornecedor[posicao_hifen + 1:].lstrip(" -")  # Remover hífen e espaços no início
            else:
                cnpj = nome_empresa = ""

            detalhes = formatar_mensagem_contrato(numero_contrato, cnpj, nome_empresa, prazo_limite, fim_vigencia, valor_global)
            dialog = DetalhesContratoDialog(detalhes, self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Seleção", "Por favor, selecione um contrato para exibir os detalhes.")
            
    def carregarDados(self):
        # Lê os dados do CSV
        dados = pd.read_csv(CONTRATOS_PATH)

        # Remove colunas indesejadas
        dados = dados.drop(columns=['Núm. Parcelas', 'Atualizado em', 'Valor Parcela'])

        # Adiciona a coluna 'Contador' com três dígitos
        dados['Contador'] = [str(i).zfill(3) for i in range(1, len(dados) + 1)]

        # Formata a coluna 'Número do instrumento' e calcula 'Dias p. Vencer'
        dados['Número do instrumento'] = dados['Número do instrumento'].apply(self.formatar_numero_instrumento)
        dados['Dias p. Vencer'] = dados['Vig. Fim'].apply(self.calcular_dias_para_vencer).astype(int)

        # Filtra as linhas onde 'Dias p. Vencer' é negativo
        dados = dados[dados['Dias p. Vencer'] >= 0]

        # Formata a coluna 'Dias p. Vencer' para ordenação
        dados['Dias p. Vencer'] = dados['Dias p. Vencer'].apply(lambda x: f'{x:04d}')

        # Ordena os dados por 'Dias p. Vencer'
        dados = dados.sort_values(by='Dias p. Vencer')

        # Cabeçalhos das colunas
        colunas = ['Contador', 'Número do instrumento', 'Fornecedor', 'Vig. Início', 'Vig. Fim', 'Dias p. Vencer', 'Valor Global']

        # Configura o modelo personalizado
        self.model = CustomTableModel(dados, colunas)
        self.tree_view.setModel(self.model)
        self.tree_view.setSortingEnabled(True)

        # Ajusta as larguras das colunas após o modelo estar totalmente carregado
        self.tree_view.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Definir a cor de fundo para preto
        palette = self.tree_view.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(Qt.GlobalColor.black))
        self.tree_view.setPalette(palette)
        
    @staticmethod
    def calcular_dias_para_vencer(data_fim):
        data_atual = QDate.currentDate()
        data_fim = QDate.fromString(data_fim, "dd/MM/yyyy")
        return data_atual.daysTo(data_fim)

    @staticmethod
    def formatar_numero_instrumento(numero):
        partes = numero.split('/')
        numero_instrumento = partes[0].lstrip('0')  # Remove zeros à esquerda
        dois_ultimos_digitos = partes[1][-2:]  # Pega os dois últimos dígitos de partes[1]
        numero_formatado = f"87000/{dois_ultimos_digitos}-{numero_instrumento.zfill(3)}/00"
        return numero_formatado
    
class CustomTableModel(QStandardItemModel):
    def __init__(self, dados, colunas, parent=None):
        super(CustomTableModel, self).__init__(parent)
        self.dados = dados
        self.colunas = colunas
        self.setupModel()

    def setupModel(self):
        self.setHorizontalHeaderLabels(self.colunas)
        for i, row in self.dados.iterrows():
            for j, col in enumerate(self.colunas):
                item = QStandardItem(str(row[col]))

                # Configuração de cores para a coluna 'Dias p. Vencer'
                if col == 'Dias p. Vencer':
                    num_value = int(row[col])
                    if num_value < 60:
                        item.setForeground(QColor(Qt.GlobalColor.red))
                    elif 60 <= num_value <= 180:
                        item.setForeground(QColor("orange"))
                    else:
                        item.setForeground(QColor(Qt.GlobalColor.green))
                else:
                    # Cor branca para as demais colunas
                    item.setForeground(QBrush(QColor(Qt.GlobalColor.white)))

                self.setItem(i, j, item)
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QTextEdit
import re

class RegexDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Buscar Expressão Regular")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("Digite o texto aqui...")
        layout.addWidget(self.text_edit)

        self.search_button = QPushButton("Buscar", self)
        self.search_button.clicked.connect(self.search_regex)
        layout.addWidget(self.search_button)

        self.results_text_edit = QTextEdit(self)
        self.results_text_edit.setReadOnly(True)  # Torna o campo de resultados somente leitura
        self.results_text_edit.setPlaceholderText("Resultados aparecerão aqui...")
        layout.addWidget(self.results_text_edit)

        self.setLayout(layout)

    def search_regex(self):
        text = self.text_edit.toPlainText()
        patterns = {
            'padrao_1': r"Item\s+(?P<item_num>\d+)\s+do\s+Grupo\s+G(?P<grupo>\d+).*?Valor\s+estimado:\s+R\$\s+(?P<valor>[\d,\.]+).*?Critério\s+de\s+julgamento:\s+(?P<crit_julgamento>.*?)\s+Quantidade:\s+(?P<quantidade>\d+)\s+Unidade\s+de\s+fornecimento:\s+(?P<unidade>.*?)\s+Situação:\s+(?P<situacao>Adjudicado e Homologado|Deserto e Homologado|Fracassado e Homologado)",
            'padrao_3': (
                r"Adjucado e Homologado por CPF (?P<cpf_od>\*\*\*.\d{3}.\*\*\*-\*\d{1})\s+-\s+"
                r"(?P<ordenador_despesa>[^\d,]+?)\s+para\s+"
                r"(?P<empresa>(?:(?!Adjucado e Homologado).)+?)(?=\s*,\s*CNPJ\s+)"
                r"\s*,\s*CNPJ\s+(?P<cnpj>\d{2}\s*\.\s*\d{3}\s*\.\s*\d{3}\s*/\s*\d{4}\s*-\s*\d{2}),\s+"
                r"melhor lance:\s*(?:[\d,]+%\s*\()?"
                r"R\$ (?P<melhor_lance>[\d,.]+)(?:\))?(?:,\s+"
                r"valor negociado: R\$ (?P<valor_negociado>[\d,.]+))?\s+Propostas do Item"),
            'padrao_4': (
                # r"Proposta adjudicada.*? Marca/Fabricante:(?P<marca_fabricante>.*?) Modelo/versão:(?P<modelo_versao>.*?)(?=\d{2}/\d{2}/\d{4}|\s*Valor proposta:)")
                # r"(?!Proposta adjudicada[^,]*,)\bProposta adjudicada\s+Porte.*?Marca/Fabricante:\s*(?P<marca_fabricante>[^,]*),\s*Modelo/versão:\s*(?P<modelo_versao>[^,]*?)(?=\s*Valor proposta:)")
                r"\bProposta adjudicada Porte\b.*?Marca/Fabricante:(?P<marca_fabricante>.*?) Modelo/versão:(?P<modelo_versao>.*?)(?=\d{2}/\d{2}/\d{4}|\s*Valor proposta:)")
        }

        found_pattern_1 = False
        result = ""

        # Verifica o padrão 1
        for match in re.finditer(patterns['padrao_1'], text, re.DOTALL):
            found_pattern_1 = True
            result += f"Item: {match.group('item_num')}, Grupo: {match.group('grupo')}, Valor: {match.group('valor')}, Critério de Julgamento: {match.group('crit_julgamento')}, Quantidade: {match.group('quantidade')}, Unidade: {match.group('unidade')}, Situação: {match.group('situacao')}\n"

        # Se padrão 1 foi encontrado, verifica os padrões 3 e 4
        if found_pattern_1:
            for name in ['padrao_3', 'padrao_4']:
                for match in re.finditer(patterns[name], text, re.DOTALL):
                    result += ', '.join(f"{k}: {v}" for k, v in match.groupdict().items()) + '\n'

        # Exibe os resultados na área de texto com barra de rolagem
        self.results_text_edit.setPlainText(result)

class MainWindow(QPushButton):
    def __init__(self):
        super().__init__("Abrir Dialog")
        self.clicked.connect(self.openDialog)

    def openDialog(self):
        dialog = RegexDialog()
        dialog.exec()

app = QApplication([])
window = MainWindow()
window.show()
app.exec()

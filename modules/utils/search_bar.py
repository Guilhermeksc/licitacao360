from PyQt6.QtWidgets import QLabel, QLineEdit
from PyQt6.QtCore import QSortFilterProxyModel, Qt, QRegularExpression

class MultiColumnFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_regular_expression = QRegularExpression()
    
    def setFilterRegularExpression(self, regex):
        self.filter_regular_expression = regex
        self.invalidateFilter()  # Revalida o filtro sempre que o regex é atualizado

    def filterAcceptsRow(self, source_row, source_parent):
        # Verifica o valor do filtro em cada coluna da linha
        for column in range(self.sourceModel().columnCount()):
            index = self.sourceModel().index(source_row, column, source_parent)
            data = self.sourceModel().data(index, Qt.ItemDataRole.DisplayRole)
            if data and self.filter_regular_expression.match(data).hasMatch():
                return True  # Mostra a linha se houver correspondência em qualquer coluna
        return False  # Oculta a linha se não houver correspondência em nenhuma coluna


def on_search_text_changed(text, proxy_model):
    """
    Atualiza o filtro do proxy_model com base no texto da barra de pesquisa.
    
    :param text: Texto inserido na barra de pesquisa.
    :param proxy_model: O modelo proxy que será filtrado com base no texto.
    """
    regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
    proxy_model.setFilterRegularExpression(regex)

def setup_search_bar(layout, proxy_model):
    search_label = QLabel("Localizar:")
    search_label.setStyleSheet("""
        color: #8AB4F7;
        font-size: 14px;
        font-weight: bold;
        margin-right: 10px;
    """)
    layout.addWidget(search_label)

    search_bar = QLineEdit()
    search_bar.setPlaceholderText("Digite para buscar...")
    search_bar.setStyleSheet("""
        QLineEdit {
            background-color: #13141F;
            color: #8AB4F7;
            font-size: 14px;
            font-weight: bold;
            padding: 8px;
            border: 2px solid #8AB4F7;
            border-radius: 6px;
        }
        QLineEdit:focus {
            border: 2px solid #8AB4F7;
            background-color: #181928;
            color: #FFFFFF;
        }
    """)
    search_bar.textChanged.connect(lambda text: on_search_text_changed(text, proxy_model))
    layout.addWidget(search_bar)

    return search_bar

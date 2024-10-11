from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, icons, status_column_index, parent=None):
        super().__init__(parent)
        self.icons = icons
        self.status_column_index = status_column_index

    def paint(self, painter, option, index):
        if index.column() == self.status_column_index:
            situacao = index.model().data(index, Qt.ItemDataRole.DisplayRole)
            icon = self.icons.get(situacao, None)

            if icon:
                icon_size = 24
                icon_x = option.rect.left() + 5
                icon_y = option.rect.top() + (option.rect.height() - icon_size) // 2
                icon_rect = QRect(int(icon_x), int(icon_y), icon_size, icon_size)
                
                # Obtém o pixmap no tamanho desejado
                pixmap = icon.pixmap(icon_size, icon_size)
                painter.drawPixmap(icon_rect, pixmap)

                # Ajusta o retângulo para o texto para ficar ao lado do ícone
                text_rect = QRect(
                    icon_rect.right() + 5,
                    option.rect.top(),
                    option.rect.width() - icon_size - 10,
                    option.rect.height()
                )
                option.rect = text_rect
            else:
                print(f"Ícone não encontrado para a situação: {situacao}")

        # Chama o método padrão para desenhar o texto ajustado
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if index.column() == self.status_column_index:
            size.setWidth(size.width() + 30)
        return size


class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter


etapas = {
    'Planejamento': None,
    'Consolidar Demandas': None,
    'Montagem do Processo': None,
    'Nota Técnica': None,
    'AGU': None,
    'Recomendações AGU': None,
    'Pré-Publicação': None,
    'Sessão Pública': None,
    'Assinatura Contrato': None,
    'Concluído': None
}

def load_and_map_icons(icons_dir, image_cache):
    icons = {}
    icon_mapping = {
        'Planejamento': 'business.png',
        'Consolidar Demandas': 'loading_table.png',
        'Concluído': 'aproved.png',
        'AGU': 'deal.png',
        'Pré-Publicação': 'loading_table.png',
        'Montagem do Processo': 'loading_table.png',
        'Nota Técnica': 'law_menu.png',
        'Assinatura Contrato': 'contrato.png',
        'Recomendações AGU': 'loading_table.png',
        'Sessão Pública': 'session.png'
    }
    for status, filename in icon_mapping.items():
        if filename in image_cache:
            pixmap = image_cache[filename]
        else:
            icon_path = icons_dir / filename
            if icon_path.exists():
                pixmap = QPixmap(str(icon_path))
                image_cache[filename] = pixmap
            else:
                print(f"Warning: Icon file {filename} not found in {icons_dir}")
                continue
        icon = QIcon(pixmap)
        icons[status] = icon
    return icons



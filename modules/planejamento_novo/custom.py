from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, icons, parent=None):
        super().__init__(parent)
        self.icons = icons

    def paint(self, painter, option, index):
        painter.save()
        super().paint(painter, option, index)  # Draw default text and background first
        status = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        icon = self.icons.get(status, None)

        if icon:
            icon_size = 24  # Using the original size of the icon
            icon_x = option.rect.left() + 5  # X position with a small offset to the left
            icon_y = option.rect.top() + (option.rect.height() - icon_size) // 2  # Centered Y position

            icon_rect = QRect(int(icon_x), int(icon_y), icon_size, icon_size)
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setWidth(size.width() + 30)  # Add extra width for the icon
        return size

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Garante que o alinhamento centralizado seja aplicado
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

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


def load_and_map_icons(icons_dir):
    icons = {}
    icon_mapping = {
        'Planejamento': 'business.png',
        'Consolidar Demandas': 'puzzle.png',
        'Concluído': 'concluido.png',
        'AGU': 'law.png',
        'Pré-Publicação': 'arrows.png',
        'Montagem do Processo': 'arrows.png',
        'Nota Técnica': 'law_menu.png',
        'Assinatura Contrato': 'contrato.png',
        'Recomendações AGU': 'certified.png',
        'Sessão Pública': 'deal.png'
    }
    # print(f"Verificando ícones no diretório: {icons_dir}")
    for status, filename in icon_mapping.items():
        icon_path = Path(icons_dir) / filename
        # print(f"Procurando ícone para status '{status}': {icon_path}")
        if icon_path.exists():
            # print(f"Ícone encontrado: {filename}")
            pixmap = QPixmap(str(icon_path))
            pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icons[status] = QIcon(pixmap)
        else:
            print(f"Ignore warning: Icon file {filename} not found in {icons_dir}")
    return icons
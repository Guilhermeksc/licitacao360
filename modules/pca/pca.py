from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import ICONS_DIR


class PCAWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(ICONS_DIR)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        # Título do módulo
        self.title_label = QLabel("Planejamento de Contratações Anual")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 30px; font-weight: bold;")

        # Descrição do módulo
        self.description_label = QLabel(
            "Este módulo permite o planejamento anual de contratações, garantindo a organização e execução" 
            "eficiente das licitações. O objetivo é auxiliar na preparação e gerenciamento das contratações" 
            "públicas, visando atender aos requisitos da administração de forma planejada."
        )
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignJustify)
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("font-size: 16px; padding: 10px;")

        # Adiciona os widgets ao layout
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.description_label)

        # Carregar ícones
        self.image_cache = self.load_initial_data()

        # Exemplo de submodulo
        self.add_submodule("Planejamento Estratégico", "Ferramenta para definir estratégias de contratação.", "planning.png")
        self.add_submodule("Monitoramento de Contratações", "Acompanhe as contratações planejadas ao longo do ano.", "monitoring.png")

        self.layout.addStretch(1)

    def add_submodule(self, title, description, icon_name):
        """Adiciona um submódulo com ícone, título e descrição alinhados corretamente."""
        icon = self.image_cache.get(icon_name.split('.')[0], QIcon())
        submodule_layout = QHBoxLayout()
        
        # Define espaçamento 0,0,0,0
        submodule_layout.setContentsMargins(0, 0, 0, 0)
        submodule_layout.setSpacing(0)
        
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(40, 40))
        
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(title_label)
        
        description_label = QLabel(description)
        description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignJustify)
        description_label.setWordWrap(True)
        description_label.setFixedWidth(800)
        description_label.setStyleSheet("font-size: 16px; padding-left: 5px;")
        title_layout.addWidget(description_label)
        
        submodule_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignRight)
        submodule_layout.addLayout(title_layout)
        
        submodule_widget = QWidget()
        submodule_widget.setLayout(submodule_layout)
        
        self.layout.addWidget(submodule_widget)
        
    def load_initial_data(self):
        image_file_names = [
            "planning.png", "monitoring.png"
        ]
        return self.load_images(self.icons_dir, image_file_names)
    
    def load_images(self, icons_dir, image_file_names):
        images = {}
        for image_file_name in image_file_names:
            image_path = icons_dir / image_file_name
            if not image_path.is_file():
                print(f"Image file not found: {image_path}")
                continue
            icon = QIcon(str(image_path))
            images[image_file_name.split('.')[0]] = icon
        return images
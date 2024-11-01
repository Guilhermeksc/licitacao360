from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from config.paths import ICONS_DIR, IMAGES_DIR

class InicioWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(ICONS_DIR)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        # Título do projeto
        self.title_label = QLabel("Licitação 360")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 30px; font-weight: bold;")
        
        # Sinopse do projeto
        self.synopsis_label = QLabel(
            "Licitação 360 é um projeto desenvolvido em Python para automatizar processos repetitivos relacionados "
            "a licitações e acordos administrativos. Com um foco na otimização e eficiência, o projeto oferece ferramentas "
            "para manipulação de documentos PDF, DOCX e XLSX, geração de relatórios, e automação de tarefas via RPA. "
            "O objetivo principal é melhorar a qualidade de vida no trabalho, minimizando erros e reduzindo a quantidade "
            "de cliques necessários para completar uma tarefa."
        )
        self.synopsis_label.setAlignment(Qt.AlignmentFlag.AlignJustify)
        self.synopsis_label.setWordWrap(True)
        self.synopsis_label.setStyleSheet("font-size: 16px; padding: 10px;")

        # Adiciona os widgets ao layout
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.synopsis_label)

        # Agora cria um QHBoxLayout para os módulos e a imagem
        modules_and_image_layout = QHBoxLayout()

        # Layout à esquerda para os módulos
        self.modules_layout = QVBoxLayout()

        # Carregar ícones
        self.image_cache = self.load_initial_data()

        # Adiciona os módulos
        self.add_module("Atas", "Automação para criação de Atas de Registro de Preços.", "report.png")
        self.add_module("Contratos", "Gerenciamento de contratos administrativos.", "signature.png")
        self.add_module("Planejamento", "Ferramentas de planejamento para licitações.", "planning.png")
        self.add_module("Web Scraping", "Coleta automática de dados do Comprasnet.", "website_menu.png")
        self.add_module("RPA", "Automação de processos repetitivos via RPA.", "automation.png")
        self.add_module("Funcionalidades PDF", "Manipulação avançada de documentos PDF.", "pdf.png")
        self.add_module("API PNCP e ComprasnetContratos", "Consulta de dados do PNCP e ComprasnetContratos via API.", "api.png")

        # Adiciona o layout dos módulos à esquerda no layout horizontal
        modules_and_image_layout.addLayout(self.modules_layout)

        # Adiciona uma imagem à direita com smooth scaling
        self.image_tucano_label = QLabel()
        self.image_tucano = QPixmap(str(IMAGES_DIR / "marinha_logo.png"))
        
        # Redimensiona a imagem mantendo a qualidade com smooth scaling
        self.image_tucano_label.setPixmap(self.image_tucano.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.image_tucano_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Adiciona a imagem ao layout horizontal
        modules_and_image_layout.addWidget(self.image_tucano_label)

        # Adiciona o layout horizontal de módulos e imagem ao layout principal vertical
        self.layout.addLayout(modules_and_image_layout)

        # Adiciona um espaço flexível para empurrar o contato para o final
        self.layout.addStretch()

        # Contato
        self.contact_label = QLabel(
            'Para mais informações, entre em contato pelo e-mail: <a href="mailto:siqueira.campos@marinha.mil.br">siqueira.campos@marinha.mil.br</a>'
        )
        self.contact_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.contact_label.setOpenExternalLinks(True)
        self.contact_label.setStyleSheet("font-size: 16px; padding: 10px;")

        # Adiciona o contato ao final
        self.layout.addWidget(self.contact_label)

    def add_module(self, title, description, icon_name):
        """Adiciona um módulo com ícone, título e descrição alinhados corretamente."""
        icon = self.image_cache.get(icon_name.split('.')[0], QIcon())
        module_layout = QHBoxLayout()

        # Define espaçamento 0,0,0,0
        module_layout.setContentsMargins(0, 0, 0, 0)
        module_layout.setSpacing(0)

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

        module_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignRight)
        module_layout.addLayout(title_layout)

        module_widget = QWidget()
        module_widget.setLayout(module_layout)

        self.modules_layout.addWidget(module_widget)
        
    def load_initial_data(self):
        image_file_names = [
            "report.png", "signature.png", "planning.png", 
            "website_menu.png", "automation.png", "pdf.png", "api.png"
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

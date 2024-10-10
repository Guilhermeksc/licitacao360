import json
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.planejamento_novo.edit_data.edit_dialog_utils import (
    apply_widget_style_11, create_button, get_descricao_servico, copyToClipboard, 
    get_preposicao_tipo, create_sinopse_text, validate_and_convert_date, create_sigdem_layout)
from diretorios import *
import os

class AutorizacaoWidget(QWidget):  # Mudando para herdar de QWidget para ser utilizada como widget na UI
    def __init__(self, data, templatePath, pasta_base, config):
        super().__init__()  # Inicializa o QWidget
        self.pasta_base = pasta_base  # Recebe pasta_base como argumento
        self.config = config
        self.data = data
        self.templatePath = templatePath
        self.pastas_necessarias = self.definir_pastas_necessarias()
        self.init_ui()  # Inicializa a interface do usuário

    def definir_pastas_necessarias(self):
        id_processo_modificado = self.data.get('id_processo', '').replace("/", "-")
        objeto_modificado = self.data.get('objeto', '').replace("/", "-")
        base_path = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}'

        return [
            base_path / '1. Autorizacao',
            base_path / '2. Portaria da Equipe de Planejamento',
            base_path / '3. IRP',
            base_path / '3. IRP' / 'Orgaos Participantes',
            base_path / '4. DFD',
            base_path / '5. ETP',
            base_path / '5. ETP' / 'Anexos',
            base_path / '6. Matriz de Riscos',
            base_path / '6. Matriz de Riscos' / 'Anexos',
            base_path / '7. TR',
            base_path / '7. TR' / 'Anexos',
            base_path / '8. Edital',
            base_path / '8. Edital' / 'Anexos',
            base_path / '9. Check-List',
            base_path / '9. Check-List' / 'Anexos',
            base_path / '10. Nota Técnica',
            base_path / '11. Justificativas Relevantes',
        ]
    
    def init_ui(self):
        layout = QVBoxLayout()
        autorizacao_group = self.create_autorizacao_group()
        layout.addWidget(autorizacao_group)
        self.setLayout(layout)

    def create_autorizacao_group(self):
        # Cria o layout principal
        main_layout = QVBoxLayout()

        # Layout para título e status na mesma linha
        titulo_status_layout = QHBoxLayout()

        # Adiciona a label para o título
        titulo_label = QLabel("Autorização para Abertura de Processo")
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_label.setStyleSheet("color: #8AB4F7; font-size: 18px; font-weight: bold")
        titulo_status_layout.addWidget(titulo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Verifica se a estrutura de pastas existe e adiciona o status
        status_layout = self.create_status_layout()
        titulo_status_layout.addStretch()  # Adiciona um espaço flexível
        titulo_status_layout.addLayout(status_layout)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Adiciona o layout de título e status ao layout principal
        main_layout.addLayout(titulo_status_layout)

        # Armazena o valor do título
        titulo = titulo_label.text()

        # Cria a barra de rolagem
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Cria o conteúdo da barra de rolagem
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Layout para Informações Básicas
        informacoes_basicas_layout = self.create_autorizacao_layout()
        scroll_layout.addLayout(informacoes_basicas_layout)

        # Define o layout do conteúdo da barra de rolagem
        scroll_area.setWidget(scroll_content)

        # Adiciona a barra de rolagem ao layout principal
        main_layout.addWidget(scroll_area)

        # Layout para Sigdem e Menu (fora da barra de rolagem)
        sigdem_layout = create_sigdem_layout(self.data, titulo)
        menu_layout = self.create_menu_layout()

        sigdem_menu_layout = QHBoxLayout()
        sigdem_menu_layout.addWidget(sigdem_layout)
        sigdem_menu_layout.addWidget(menu_layout)

        sigdem_menu_layout.setStretch(0, 4)
        sigdem_menu_layout.setStretch(1, 1)

        # Cria um widget para conter o layout sigdem_menu_layout
        sigdem_menu_widget = QWidget()
        sigdem_menu_widget.setLayout(sigdem_menu_layout)
        sigdem_menu_widget.setFixedHeight(250)  # Define a altura fixa de 250

        main_layout.addWidget(sigdem_menu_widget)

        # Cria um widget para o grupo MR e define o layout
        mr_group_widget = QWidget()
        mr_group_widget.setLayout(main_layout)

        return mr_group_widget

    def create_status_layout(self):
        # Cria um layout horizontal para exibir o ícone e o status juntos
        status_layout = QHBoxLayout()

        # Verifica se a estrutura de pastas existe
        pastas_existentes = self.verificar_pastas()

        # Define o ícone com base no status da verificação
        if pastas_existentes:
            self.status_label = QLabel("Pastas encontradas")  # Define status_label como atributo da classe
            self.status_label.setStyleSheet("font-size: 14px;")
            self.icon_label = QLabel()
            icon_folder = QIcon(str(ICONS_DIR / "folder_v.png"))  # Ícone de sucesso
        else:
            self.status_label = QLabel("Pastas não encontradas")  # Define status_label como atributo da classe
            self.status_label.setStyleSheet("font-size: 14px;")
            self.icon_label = QLabel()
            icon_folder = QIcon(str(ICONS_DIR / "folder_x.png"))  # Ícone de erro

        self.icon_label.setPixmap(icon_folder.pixmap(40, 40))
        status_layout.addWidget(self.icon_label)
        status_layout.addWidget(self.status_label)

        return status_layout

    def create_autorizacao_layout(self):
        # Cria um layout vertical principal
        layout = QVBoxLayout()
        status_label = QLabel("Incluir informações") 
        status_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(status_label)

        return layout

    def verificar_pastas(self):
        print("Verificando se as pastas existem...")  # Print de verificação
        pastas_existentes = all(pasta.exists() for pasta in self.pastas_necessarias)
        print(f"Pastas existentes: {pastas_existentes}")  # Print de verificação
        return pastas_existentes

    def verificar_e_criar_pastas(self):
        print("Verificando e criando pastas...")  # Print de verificação
        for pasta in self.pastas_necessarias:
            if not pasta.exists():
                print(f"Criando pasta: {pasta}")  # Print de verificação
                pasta.mkdir(parents=True, exist_ok=True)

        # Abre a pasta criada ou existente
        self.abrir_pasta(self.pasta_base / f'{self.data.get("id_processo", "").replace("/", "-")} - {self.data.get("objeto", "").replace("/", "-")}')

        # Atualiza o status após criar as pastas
        self.update_status_layout()

    def abrir_pasta(self, pasta_path):
        if pasta_path.exists() and pasta_path.is_dir():
            # Abre a pasta no explorador de arquivos usando QDesktopServices
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(pasta_path)))

    def update_status_layout(self):
        print("Atualizando o layout de status...")  # Print de verificação
        # Atualiza o layout de status após verificar/criar pastas
        pastas_existentes = self.verificar_pastas()
        if pastas_existentes:
            self.status_label.setText("Pastas encontradas")
            icon_folder = QIcon(str(ICONS_DIR / "folder_v.png"))
        else:
            self.status_label.setText("Pastas não encontradas")
            icon_folder = QIcon(str(ICONS_DIR / "folder_x.png"))
        self.icon_label.setPixmap(icon_folder.pixmap(40, 40))

    def create_menu_layout(self):
        menu_group_box = QGroupBox("Menu")
        apply_widget_style_11(menu_group_box)
        menu_group_box.setFixedWidth(230)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(10)

        icon_open_folder = QIcon(str(ICONS_DIR / "open-folder.png"))
        icon_save_folder = QIcon(str(ICONS_DIR / "zip-folder.png"))
        icon_gerar_documento = QIcon(str(ICONS_DIR / "contract.png"))

        # O callback agora chama um lambda para garantir que o botão está sendo conectado corretamente
        buttons = [
            create_button(
                text="  Criar/Abrir Pastas  ",
                icon=icon_open_folder,
                tooltip_text="Clique para criar ou abrir pastas",
                callback=lambda: self.on_criar_abrir_pastas_clicked(),
                button_size=QSize(200, 50),
                icon_size=QSize(45, 45)
            ),
            create_button(
                text="Local de Salvamento",
                icon=icon_save_folder,
                tooltip_text="Selecione o local de salvamento",
                callback=lambda: self.alterar_local_salvamento(),
                button_size=QSize(200, 50),
                icon_size=QSize(45, 45)
            ),
            create_button(
                text=" Gerar Documento ",
                icon=icon_gerar_documento,
                callback=lambda: print("Gerar Documento clicked"),
                tooltip_text="Clique para gerar o ETP",
                button_size=QSize(200, 50),
                icon_size=QSize(45, 45)
            )
        ]

        layout.addStretch()
        for button in buttons:
            layout.addWidget(button)
        layout.addStretch()

        menu_group_box.setLayout(layout)
        return menu_group_box

    def on_criar_abrir_pastas_clicked(self):
        print("Botão Criar/Abrir Pastas foi clicado.")
        self.verificar_e_criar_pastas()

    def alterar_local_salvamento(self):
        new_dir = QFileDialog.getExistingDirectory(None, "Selecione o Local de Salvamento", str(Path.home()))
        if new_dir:
            self.pasta_base = Path(new_dir)
            self.config['pasta_base'] = str(self.pasta_base)
            save_config('pasta_base', str(self.pasta_base))
            QMessageBox.information(None, "Local de Salvamento Alterado", f"O novo local de salvamento foi alterado para: {self.pasta_base}\n\nReabra novamente a janela de edição para que alterações tenham efeito")
            self.update_status_layout()

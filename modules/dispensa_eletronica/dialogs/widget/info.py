from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QHBoxLayout

class InfoWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Configuração do layout com dados específicos
        contratacao_group_box = self.create_contratacao_group()
        layout.addWidget(contratacao_group_box)

        classificacao_orcamentaria_group_box = self.create_classificacao_orcamentaria_group()
        layout.addWidget(classificacao_orcamentaria_group_box)

        formulario_group_box = self.create_frame_formulario_group()
        layout.addWidget(formulario_group_box)

        self.setLayout(layout)

    def create_contratacao_group(self):
        group_box = QGroupBox("Contratação")
        layout = QVBoxLayout()
        
        # Exemplo de utilização de `data`
        layout.addWidget(QLabel(f"ID Processo: {self.data[0]}"))
        group_box.setLayout(layout)
        return group_box

    def create_classificacao_orcamentaria_group(self):
        group_box = QGroupBox("Classificação Orçamentária")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Orçamento: Detalhes específicos aqui"))
        group_box.setLayout(layout)
        return group_box

    def create_frame_formulario_group(self):
        group_box = QGroupBox("Formulário de Dados")
        layout = QVBoxLayout()
        
        # Exemplo de campo com `data`
        layout.addWidget(QLabel(f"Objeto: {self.data[1]}"))
        group_box.setLayout(layout)
        return group_box

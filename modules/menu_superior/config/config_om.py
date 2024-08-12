from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox

class OrganizacoesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Organizações")
        self.setLayout(self._create_layout())
        
    def _create_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nome da Organização:"))
        self.org_name_input = QLineEdit()
        layout.addWidget(self.org_name_input)
        
        layout.addWidget(QLabel("Tipo de Organização:"))
        self.org_type_input = QComboBox()
        self.org_type_input.addItems(["Pública", "Privada", "ONG"])
        layout.addWidget(self.org_type_input)
        
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        
        return layout
        
    def save_settings(self):
        # Lógica para salvar as organizações
        org_name = self.org_name_input.text()
        org_type = self.org_type_input.currentText()
        print(f"Organização: {org_name}, Tipo: {org_type}")
        self.accept()
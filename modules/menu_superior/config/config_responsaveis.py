from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox

class AgentesResponsaveisDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agentes Responsáveis")
        self.setLayout(self._create_layout())
        
    def _create_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nome do Agente:"))
        self.agent_name_input = QLineEdit()
        layout.addWidget(self.agent_name_input)
        
        layout.addWidget(QLabel("Função:"))
        self.agent_role_input = QLineEdit()
        layout.addWidget(self.agent_role_input)
        
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        
        return layout
        
    def save_settings(self):
        # Lógica para salvar os agentes responsáveis
        agent_name = self.agent_name_input.text()
        agent_role = self.agent_role_input.text()
        print(f"Agente: {agent_name}, Função: {agent_role}")
        self.accept()
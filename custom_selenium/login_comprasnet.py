from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtGui import *
from custom_selenium.divulgacao_compras import DivulgacaoComprasDialog
from PyQt6.QtCore import pyqtSignal
import json

class LoginDialog(QDialog):
    # Definir um sinal que carrega username e password
    login_successful = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        self.username_label = QLabel("Usuário:")
        self.layout.addWidget(self.username_label)

        self.username_input = QLineEdit()
        self.layout.addWidget(self.username_input)

        self.password_label = QLabel("Senha:")
        self.layout.addWidget(self.password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addWidget(self.password_input)

        # Checkbox para mostrar/ocultar senha
        self.show_password_checkbox = QCheckBox("Mostrar senha")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)

        self.layout.addWidget(self.show_password_checkbox)

        # Checkbox para memorizar senha
        self.remember_password_checkbox = QCheckBox("Memorizar senha")
        self.layout.addWidget(self.remember_password_checkbox)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        self.layout.addWidget(self.login_button)
        
        self.settings_file = 'settings_comprasnet.json'  # Caminho para o arquivo de configurações
        self.load_settings()
        self.setWindowTitle("Login")

    def handle_login(self):
        # Lógica de tratamento do login
        username = self.username_input.text()
        password = self.password_input.text()
        print(f"Username: {username}, Password: {password}")
        
        # Se o login for considerado bem-sucedido:
        QMessageBox.information(self, "Login bem-sucedido", "Você entrou com sucesso!")
        self.login_successful.emit(username, password)

        self.accept()  # Fechar o diálogo com um resultado "Aceito"
        self.save_settings()  # Salvar configurações

    def toggle_password_visibility(self):
        if self.show_password_checkbox.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.repaint()

    def save_settings(self):
        data = {
            'username': self.username_input.text(),
            'remember_password': self.remember_password_checkbox.isChecked(),
        }
        if self.remember_password_checkbox.isChecked():
            # Implemente a criptografia aqui para maior segurança
            data['password'] = self.encrypt_password(self.password_input.text())
        
        with open(self.settings_file, 'w') as f:
            json.dump(data, f)

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                data = json.load(f)
                self.username_input.setText(data.get('username', ''))
                self.remember_password_checkbox.setChecked(data.get('remember_password', False))
                if self.remember_password_checkbox.isChecked():
                    # Descriptografe a senha aqui
                    self.password_input.setText(self.decrypt_password(data.get('password', '')))
        except FileNotFoundError:
            pass  # Arquivo não existe ainda, nenhuma ação necessária

    def show_login_dialog(self):
        dialog = LoginDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Armazenar as credenciais inseridas
            self.username = dialog.username_input.text()
            self.password = dialog.password_input.text()
            # Lógica após login bem-sucedido
            print(f"Login successful with username: {self.username} and password: {self.password}")
        else:
            # Lógica após cancelamento de login ou falha
            pass

    def encrypt_password(self, password):
        # Implemente a lógica de criptografia aqui
        return password  # substitua isso pela sua senha criptografada

    def decrypt_password(self, password):
        # Implemente a lógica de descriptografia aqui
        return password
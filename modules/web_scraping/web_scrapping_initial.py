from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from diretorios import ICONS_DIR, IMAGE_PATH, WEBDRIVER_FIREFOX_PATH
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from modules.web_scraping.macros.divulgacao_compras import DivulgacaoComprasMacro
class SeleniumDriverThread(QThread):
    login_detected = pyqtSignal()  # Sinal para indicar que o login foi detectado

    def __init__(self, webdriver_path, parent=None):
        super().__init__(parent)
        self.webdriver_path = webdriver_path
        self.driver = None

    def run(self):
        self._initialize_webdriver()
        self._perform_login_actions()

    def _initialize_webdriver(self):
        options = Options()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')

        service = Service(executable_path=self.webdriver_path)
        self.driver = webdriver.Firefox()
        self.driver.get("http://www.comprasnet.gov.br/seguro/loginPortal.asp")
        self.driver.maximize_window()

    def _perform_login_actions(self):
        try:
            # Clique no botão com a classe 'governo'
            button_selector = "button.governo"
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))).click()

            # Preencha os campos de login
            login_field = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#txtLogin")))
            login_field.send_keys("07668525475")

            password_field = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#txtSenha")))
            password_field.send_keys("sPORT.07")

            # Clique no botão de login
            submit_button_selector = "#card2 > div > div > div.br-form > div.actions.text-right.mt-4 > button"
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, submit_button_selector))).click()

            self.login_detected.emit()  # Emite o sinal quando o login for detectado

        except TimeoutException as e:
            print(f"Erro ao tentar realizar o login: {e}")
            QMessageBox.critical(None, "Erro", f"Erro durante o processo de login: {e}")
        except Exception as e:
            print(f"Erro inesperado: {e}")
            QMessageBox.critical(None, "Erro inesperado", f"Ocorreu um erro inesperado: {e}")

    def _wait_for_user_to_click_login(self):
        try:
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".is-primary"))
            )
            while True:
                try:
                    WebDriverWait(self.driver, 120).until(
                        EC.staleness_of(login_button)
                    )
                    self.login_detected.emit()  # Emite o sinal quando o login for detectado
                    break
                except TimeoutException:
                    response = self._ask_to_close_driver()
                    if response == QMessageBox.StandardButton.Yes:
                        self.driver.quit()
                        break
        except Exception as e:
            print(f"Erro ao tentar monitorar o clique no botão: {e}")

    def _ask_to_close_driver(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Login não digitado, deseja encerrar o driver?")
        msg.setWindowTitle("Encerrar Driver")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return msg.exec()

    def close_driver(self):
        if self.driver:
            self.driver.quit()
            self.quit()  # Termina a thread imediatamente

class WebScrapingWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.icons_dir = Path(ICONS_DIR)
        self.image_cache = self._load_images()
        self.driver_thread = None
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self._on_inactivity_timeout)
        self.inactivity_timer.setInterval(5 * 60 * 1000)  # 5 minutos em milissegundos
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: transparent;")
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self._create_title_layout())

        access_button = QPushButton("Acessar")
        access_button.setFont(self._get_title_font(12))
        access_button.clicked.connect(self._show_dialog)
        main_layout.addWidget(access_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def _create_title_layout(self):
        layout = QHBoxLayout()
        icon_label = QLabel()
        icon = self.image_cache.get('graph')
        if icon:
            scaled_icon = icon.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled_icon)
        title_label = QLabel("Web Scraping do Comprasnet")
        title_label.setFont(self._get_title_font(30, bold=True))
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return layout

    def _get_title_font(self, size=14, bold=False):
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def _load_images(self):
        images = {
            'graph': QPixmap(str(self.icons_dir / "graph.png")),
            'firefox': QPixmap(str(self.icons_dir / "firefox.png")),
            'continue': QPixmap(str(self.icons_dir / "continue.png")),
            'close': QPixmap(str(self.icons_dir / "close.png"))
        }
        return images

    def _show_dialog(self):
        self._minimize_main_window()
        dialog = self._create_dialog()
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            self._restore_main_window()
        else:
            if self.driver_thread and self.driver_thread.driver:
                self.driver_thread.close_driver()  # Fecha o driver quando o diálogo for fechado
                self.driver_thread.wait()  # Aguarda o término da thread antes de restaurar a main_window
            self._restore_main_window()

    def _minimize_main_window(self):
        self.main_window.showMinimized()

    def _initialize_driver_thread(self):
        self.driver_thread = SeleniumDriverThread(webdriver_path=WEBDRIVER_FIREFOX_PATH)
        self.driver_thread.login_detected.connect(self._show_login_message)
        self.driver_thread.start()

    def _show_login_message(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("Usuário logado!")
        msg.setWindowTitle("Login")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        msg.exec()

    def _create_dialog(self):
        dialog = QDialog(self, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        dialog.setFixedSize(230, 70)
        self._position_dialog_on_primary_screen(dialog)
        dialog.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._add_image_to_dialog(layout)
        self._add_buttons_to_dialog(layout, dialog)
        
        dialog.rejected.connect(self._close_driver_on_dialog_reject)

        return dialog

    def _close_driver_on_dialog_reject(self):
        if self.driver_thread and self.driver_thread.driver:
            self.driver_thread.close_driver()
            self.driver_thread.wait()  # Aguarda o término da thread antes de prosseguir
            print("Driver fechado ao rejeitar o diálogo")

    def _position_dialog_on_primary_screen(self, dialog):
        screen_geometry = QApplication.primaryScreen().geometry()
        dialog_x = screen_geometry.x() + (screen_geometry.width() - dialog.width()) // 2
        dialog_y = screen_geometry.y()
        dialog.move(dialog_x, dialog_y)

    def _add_image_to_dialog(self, layout):
        image_label = QLabel()
        pixmap = QPixmap(str(IMAGE_PATH / "titulo360superior"))
        image_label.setPixmap(pixmap.scaledToWidth(230, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(image_label)

    def _add_buttons_to_dialog(self, layout, dialog):
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)

        init_icon = self.image_cache.get('firefox')
        continue_icon = self.image_cache.get('continue')
        close_icon = self.image_cache.get('close')

        self.init_button = QPushButton("Iniciar")
        self.init_button.setIcon(QIcon(init_icon))
        self.init_button.setStyleSheet(self._button_stylesheet())
        self.init_button.clicked.connect(self._on_init_clicked)

        self.continue_button = QPushButton("Continuar")
        self.continue_button.setIcon(QIcon(continue_icon))
        self.continue_button.setStyleSheet(self._button_stylesheet())
        self.continue_button.setEnabled(False)

        # Criar o menu com as opções
        menu = QMenu(self)
        menu.addAction("Pesquisa de Preços")
        divulgacao_action = QAction("Divulgação de Compras", self)
        divulgacao_action.triggered.connect(self._start_divulgacao_de_compras_macro)
        divulgacao_action.triggered.connect(self._reset_inactivity_timer)  # Reinicia o timer ao selecionar uma opção
        menu.addAction(divulgacao_action)

        self.continue_button.setMenu(menu)

        close_button = QPushButton("Fechar")
        close_button.setIcon(QIcon(close_icon))
        close_button.setStyleSheet(self._button_stylesheet())
        close_button.clicked.connect(dialog.reject)

        button_layout.addWidget(self.init_button)
        button_layout.addWidget(self.continue_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def _reset_inactivity_timer(self):
        self.inactivity_timer.start()  # Reinicia o temporizador ao interagir com o menu

    def _on_inactivity_timeout(self):
        response = QMessageBox.warning(self, "Encerramento de Driver",
                                       "Nenhuma ação foi realizada nos últimos 5 minutos. O driver será encerrado. Deseja continuar?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if response == QMessageBox.StandardButton.No:
            if self.driver_thread and self.driver_thread.driver:
                self.driver_thread.close_driver()
                self.driver_thread.wait()
            self._restore_main_window()
        else:
            self._reset_inactivity_timer()

    def _on_init_clicked(self):
        self._initialize_driver_thread()
        self.continue_button.setEnabled(True)
        self.init_button.setEnabled(False)

    def _button_stylesheet(self):
        return """
            QPushButton {
                background-color: black;
                color: white;
                border: none;
                text-align: center;
            }
            QPushButton:hover {
                background-color: white;
                color: black;
            }
        """

    def _restore_main_window(self):
        self.main_window.showNormal()

    def _start_divulgacao_de_compras_macro(self):
        if not self.driver_thread or not self.driver_thread.driver:
            QMessageBox.warning(self, "Erro", "Driver do Selenium não inicializado.")
            return

        macro = DivulgacaoComprasMacro(self.driver_thread.driver)
        macro.executar()
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from datetime import datetime
import pandas as pd
import locale
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, ElementClickInterceptedException
from diretorios import WEBDRIVER_FIREFOX_PATH, ICONS_DIR
from custom_selenium.seletores_selenium import *
from custom_selenium.utils_selenium import *
import re
import time
import numpy as np
import json

class IRPDialog(QDialog):
    def __init__(self, parent=None):
        super(IRPDialog, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.settings_file = 'settings_comprasnet.json'
        self.dataframe = None
        self.model = QStandardItemModel()  # Modelo de dados para a QTableView

        # Layout horizontal para Nº da IRP e Ano
        self.irp_num_layout = QHBoxLayout()
        self.irp_num_input = QLineEdit(self)
        self.irp_num_input.setPlaceholderText("Nº da IRP")
        self.irp_num_layout.addWidget(self.irp_num_input)

        self.ano_irp_input = QLineEdit(self)
        self.ano_irp_input.setText(str(datetime.now().year))  # Ano atual
        self.irp_num_layout.addWidget(self.ano_irp_input)

        self.layout.addLayout(self.irp_num_layout)

        # Botão para carregar o arquivo de tabela
        self.load_table_button = QPushButton("Carregar Tabela", self)
        self.load_table_button.clicked.connect(self.load_table)
        self.layout.addWidget(self.load_table_button)

        # TableView para mostrar os dados da tabela
        self.dataframe_table_view = QTableView(self)
        self.layout.addWidget(self.dataframe_table_view)

        # Botão para confirmar a entrada
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.setWindowTitle("Digite o número da IRP e carregue o arquivo de tabela")
        self.load_credentials_from_json()

    def load_credentials_from_json(self):
        try:
            with open(self.settings_file, 'r') as f:
                data = json.load(f)
                self.username = data.get('username', '')
                if data.get('remember_password', False):
                    # Descriptografe a senha aqui
                    self.password = self.decrypt_password(data.get('password', ''))
                else:
                    self.password = ''
        except FileNotFoundError:
            self.username = ''
            self.password = ''
            print("Arquivo de configurações não encontrado.")

    def decrypt_password(self, password):
        # Implemente a lógica de descriptografia aqui
        return password  # substitua isso pela sua senha descriptografada
    
    def get_irp_number(self):
        irp_num = self.irp_num_input.text().strip()  # Remove espaços extras
        ano_irp = self.ano_irp_input.text()
        return irp_num + ano_irp

    def load_table(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Arquivos de Tabela (*.xlsx *.xls *.ods)")
        if file_name:
            # Especifica as colunas a serem carregadas
            columns_to_load = ['item_num', 'catalogo', 'descricao_tr', 'unidade_fornecimento']
            self.dataframe = pd.read_excel(file_name, usecols=columns_to_load)

            # Aplicar strip em todas as colunas de texto
            for col in ['item_num', 'catalogo', 'descricao_tr', 'unidade_fornecimento']:
                self.dataframe[col] = self.dataframe[col].astype(str).str.strip()

            self.update_table_view()
            print("Arquivo de tabela carregado com sucesso!")

    def update_table_view(self):
        self.model.clear()  # Limpa o modelo existente
        if self.dataframe is not None:
            # Definir cabeçalhos das colunas no modelo
            self.model.setHorizontalHeaderLabels(['Número do Item', 'Catálogo', 'Descrição', 'Unidade de Fornecimento'])

            # Adiciona os dados ao modelo
            for index, row in self.dataframe.iterrows():
                formatted_row = [QStandardItem(str(cell)) for cell in row]  # Formata cada célula como string
                self.model.appendRow(formatted_row)

            self.dataframe_table_view.setModel(self.model)

            # Ajustar o tamanho das colunas para melhor visualização
            self.dataframe_table_view.setColumnWidth(0, 100)  # Largura para item_num
            self.dataframe_table_view.setColumnWidth(1, 200)  # Largura para catalogo
            self.dataframe_table_view.setColumnWidth(2, 300)  # Largura para descricao_tr
            self.dataframe_table_view.setColumnWidth(3, 200)  # Largura para unidade_fornecimento

        # Definir o tamanho mínimo da janela de diálogo
        self.setMinimumSize(600, 400)

    def fluxo_lancamento_irp(self):
        irp_dialog = IRPDialog(self)
        if irp_dialog.exec() == QDialog.DialogCode.Accepted:
            irp_number = irp_dialog.get_irp_number()
            dataframe = irp_dialog.dataframe
            if irp_number and dataframe is not None and not dataframe.empty:
                self.abrir_comprasnet_irp(irp_number)
                self.inserir_catmat(dataframe)
            else:
                print("Número da IRP ou dados da tabela não fornecidos.")
        else:
            print("Ação cancelada pelo usuário.")

    def abrir_comprasnet_irp(self, irp_number):
        self.load_credentials_from_json()
        options = Options()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')

        service = Service(executable_path=WEBDRIVER_FIREFOX_PATH)        
        self.driver = webdriver.Firefox()
        self.driver.get("http://www.comprasnet.gov.br/seguro/loginPortal.asp")
        esperar_e_clicar(self.driver, "button.governo")
        esperar_e_preencher(self.driver, USER_FIELD_SELECTOR, self.username)
        esperar_e_preencher(self.driver, PASSWORD_FIELD_SELECTOR, self.password)
        esperar_e_clicar(self.driver, LOGIN_BUTTON_SELECTOR)

        # # Aguardar até que o overlay desapareça
        esperar_invisibilidade_elemento(self.driver, OVERLAY_SELECTOR)
        time.sleep(0.5)  # Necessário para carregar a página

        timeout = 20

        # Espera até que o overlay desapareça
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ui-blockui.ui-widget-overlay.ui-blockui-document"))
        )
        # Localizar e clicar no elemento desejado usando XPath
        try:
            # Tenta clicar
            esperar_e_clicar(self.driver, PAGINATION_ELEMENT_XPATH, by=By.XPATH)
        except ElementClickInterceptedException:
            # Espera um pouco e tenta novamente
            time.sleep(1)
            esperar_e_clicar(self.driver, PAGINATION_ELEMENT_XPATH, by=By.XPATH)
            
        time.sleep(0.3)
        esperar_e_clicar(self.driver, ABRIR_JANELA_IRP) # Abrir nova janela IRP

        aguardar_mudanca_janela(self.driver, titulo_desejado="SIASGnet IRP")

        # time.sleep(1)
        # esperar_e_clicar(self.driver, CONFIRM_BUTTON_SELECTOR)

        hover_sobre_elemento(self.driver, HOVER_ELEMENT_SELECTOR) # Abrir menu dinâmico IRP
        esperar_e_clicar(self.driver, MENU_OPTION_SELECTOR) # Opção abrir irp existente
        esperar_e_clicar(self.driver, SPECIFIC_ELEMENT_SELECTOR)
        # Digitar texto no campo de entrada
        esperar_e_preencher(self.driver, INPUT_FIELD_SELECTOR, irp_number)

        esperar_e_clicar(self.driver, CONSULT_BUTTON_SELECTOR)
        esperar_e_clicar(self.driver, RESULT_LINK_SELECTOR)
        esperar_e_clicar(self.driver, TD_ITEM_SELECTOR)

    def inserir_catmat(self, dataframe):
        esperar_e_clicar(self.driver, NEW_ITEM_BUTTON_SELECTOR)
        itens_inseridos = 0  # Contador para os itens inseridos com sucesso
        for index, row in dataframe.iterrows():
            id_item = row['catalogo']  # Assumindo que 'id' é o nome da coluna
            unidade = row['unidade_fornecimento']  # Substitua 'unidade' pelo nome correto da coluna

            # Espera e muda para a janela do pop-up
            aguardar_e_mudar_para_popup(self.driver)
            time.sleep(0.2)  # Pequeno delay

            # Espera pela presença do campo CATMAT e interage com ele
            campo_catmat_xpath = "/html/body/app-root/div/main/app-busca/div[1]/div/div/div[4]/div/div/p-autocomplete/span/input"
            campo_catmat = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, campo_catmat_xpath))
            )
            campo_catmat.clear()
            campo_catmat.send_keys(id_item)
            print(f"Valor {id_item} inserido no campo CATMAT.")
            
            time.sleep(0.2)  # Pequeno delay após inserir o valor
            esperar_e_clicar(self.driver, "/html/body/app-root/div/main/app-busca/div[1]/div/div/div[4]/div/div/button/i", By.XPATH)
            self.selecionar_unidade(unidade)
            time.sleep(0.3)

            # Clicar no botão especificado pelo XPath
            botao_xpath = "/html/body/app-root/div/main/app-busca/app-detalhe-material-siasgnet-lote/div/div[2]/div[2]/p-table/div/div/table/tbody/tr/td[3]/button"
            esperar_e_clicar(self.driver, botao_xpath, By.XPATH)
            print("Botão clicado após a seleção de 'Unidade'.")

            # Incrementa o contador após cada inserção bem-sucedida
            itens_inseridos += 1

        # Clicar no botão especificado pelo XPath
        botao_carrinho = "/html/body/app-root/div/main/app-busca/div[1]/div/div/div[2]/div[2]/button/i"
        esperar_e_clicar(self.driver, botao_carrinho, By.XPATH)
        print("Botão 'Carrinho' clicado.")

        botao_adicionar_siasg = "/html/body/app-root/div/main/app-busca/app-exibir-selecionados-siasgnet-lote/div/div[1]/div/div[3]/button"
        esperar_e_clicar(self.driver, botao_adicionar_siasg, By.XPATH)
        print("Botão 'Adicionar no SIASG' clicado.")

        self.clicar_botao_ok_popup()      
        
        self.raise_()
        self.activateWindow()              
        QMessageBox.information(self, "Inserção Concluída", f"{itens_inseridos} itens inseridos com sucesso.")

    def selecionar_unidade(self, unidade_nome):
        possiveis_nomes = [unidade_nome,
                        re.sub(r'(\d+)\s*G\b', r'\1 Grama', unidade_nome),
                        re.sub(r'(\d+)\s*ML\b', r'\1 Mililitro', unidade_nome),
                        re.sub(r'(\d+)\s*M\b', r'\1 Metro', unidade_nome),
                        re.sub(r'(\d+)\s*KG\b', r'\1 Quilograma', unidade_nome),
                        re.sub(r'(\d+)\s*UN\b', r'\1 Metro', unidade_nome),
                        unidade_nome + " Grama",
                        unidade_nome + " Mililitro",
                        unidade_nome + " Metro",
                        unidade_nome + " Quilograma",
                        unidade_nome + " Unidade",
                        "Unidade" if unidade_nome.lower() == "unidade" else unidade_nome]

        for nome in possiveis_nomes:
            try:
                time.sleep(0.1)  # Pequena pausa
                dropdown = WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH, "/html/body/app-root/div/main/app-busca/app-detalhe-material-siasgnet-lote/div/div[2]/div[1]/div[2]/select"))
                )
                time.sleep(0.2)  # Pequena pausa
                Select(dropdown).select_by_visible_text(nome)
                print(f"Opção '{nome}' selecionada no dropdown.")
                return
            except Exception as e:
                print(f"Erro ao tentar selecionar '{nome}' no dropdown:", str(e))

        try:
            # Se nenhuma opção funcionou, tenta encontrar um elemento que contenha o texto
            all_options = dropdown.find_elements_by_tag_name('option')
            for option in all_options:
                if unidade_nome.lower() in option.text.lower():
                    option.click()
                    print(f"Opção contendo '{unidade_nome}' selecionada no dropdown.")
                    return
        except Exception as e:
            print(f"Erro ao tentar encontrar uma opção contendo '{unidade_nome}':", str(e))

        print(f"Nenhuma opção válida encontrada para '{unidade_nome}'.")

    def clicar_botao_ok_popup(self):
        # Aguardar a abertura do pop-up e mudar o foco para ele
        self.aguardar_e_mudar_para_popup()

        # Localizar e clicar no botão "OK" no pop-up
        botao_ok_xpath = "//*[@id='btOk']"
        try:
            # Espera até que o botão "OK" esteja visível e clicável
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, botao_ok_xpath)))
            self.driver.find_element(By.XPATH, botao_ok_xpath).click()
            print("Botão 'OK' clicado no pop-up.")
        except Exception as e:
            print(f"Erro ao clicar no botão 'OK' do pop-up: {e}")
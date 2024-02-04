from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from styles.styless import get_transparent_title_style
from datetime import datetime
import pandas as pd
import time
from diretorios import WEBDRIVER_FIREFOX_PATH, ICONS_DIR
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, ElementClickInterceptedException
from custom_selenium.seletores_selenium import *
from custom_selenium.utils_selenium import *
import re
import os
import json
import locale
from pathlib import Path
import traceback
import sys

class DivulgacaoComprasDialog(QDialog):
    def __init__(self, username, password, parent=None):
        super(DivulgacaoComprasDialog, self).__init__(parent)
        self.item_input_selector = "#corpo > form:nth-child(10) > fieldset:nth-child(49) > table:nth-child(5) > tbody:nth-child(1) > tr:nth-child(3) > td:nth-child(1) > input:nth-child(1)"
        self.driver = None  # Inicialize o driver como None aqui
        self.settings_file = 'settings_comprasnet.json'
        self.username = username
        self.password = password
        self.layout = QVBoxLayout(self) 
        
        # Layout horizontal para Nº da Licitação e Ano
        self.licitacao_layout = QHBoxLayout()
        self.licitacao_num_input = QLineEdit(self)
        self.licitacao_num_input.setPlaceholderText("Nº da Licitação")
        self.licitacao_layout.addWidget(self.licitacao_num_input)  # Correção aqui

        self.licitacao_ano_input = QLineEdit(self)
        self.licitacao_ano_input.setText(str(datetime.now().year))  # Ano atual
        self.licitacao_layout.addWidget(self.licitacao_ano_input)  # Correção aqui
        self.layout.addLayout(self.licitacao_layout)  # Adiciona o layout horizontal ao layout principal

        # Botão para carregar o arquivo da tabela
        self.load_table_button = QPushButton("Carregar Tabela", self)
        self.load_table_button.clicked.connect(self.load_table)
        self.layout.addWidget(self.load_table_button)

        # Modelo e TableView para exibir dados
        self.model = QStandardItemModel(self)  
        self.tableView = QTableView(self)
        self.tableView.setModel(self.model)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Correção aplicada aqui
        self.layout.addWidget(self.tableView)

        # Label para instrução de escolha do item inicial
        self.item_inicio_label = QLabel("Escolha a partir de qual item o fluxo se iniciará:")
        self.layout.addWidget(self.item_inicio_label)  # Adiciona a Label ao layout

        # ComboBox para o número inicial do item
        self.item_inicio_combo = QComboBox(self)
        self.layout.addWidget(self.item_inicio_combo)  # Adiciona a ComboBox ao layout

        # Botão para confirmar a entrada
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.table_data = None  # DataFrame para armazenar dados da tabela
        self.setWindowTitle("Carregue a tabela para atualizar o IRP")
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
            
    def load_table(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.ods)")
        if file_name:
            self.table_data = pd.read_excel(file_name)
            self.model.clear()
            self.model.setHorizontalHeaderLabels(self.table_data.columns)

            for index, row in self.table_data.iterrows():
                items = [QStandardItem(str(cell)) for cell in row]
                self.model.appendRow(items)

            # Preencher a ComboBox com os números dos itens
            self.item_inicio_combo.clear()  # Limpa os itens antigos
            item_nums = self.table_data['item_num'].astype(str).tolist()  # Converte os números dos itens para string
            self.item_inicio_combo.addItems(item_nums)  # Adiciona os números dos itens à ComboBox

            QMessageBox.information(self, "Carregamento Concluído", "Tabela carregada com sucesso!")

    def get_licitacao_number(self):
        licitacao_num = self.licitacao_num_input.text().strip()
        licitacao_ano = self.licitacao_ano_input.text()
        return licitacao_num + licitacao_ano

    def get_item_inicio(self):
        return self.item_inicio_combo.currentText()  # Retorna o item selecionado na ComboBox

    def accept(self):
        super().accept()
        item_selecionado = self.get_item_inicio()
        print(f"Item selecionado: {item_selecionado}")

    def abrir_fluxo_divulgacao_compras(self):
        # Abre o diálogo para o usuário carregar e manipular os dados da tabela.
        if self.exec() == QDialog.DialogCode.Accepted:
            # O usuário aceitou o diálogo, continue com a execução do fluxo.
            self.fluxo_divulgacao_compras()
        else:
            print("Ação cancelada pelo usuário.")

    def fluxo_divulgacao_compras(self):
        # Verifica se o driver é None e precisa ser inicializado
        if not self.driver:
            self.driver = webdriver.Firefox()  # Inicialize o driver aqui, se necessário
            print("Novo driver inicializado.")
        
        # Carrega as credenciais antes de chamar a função
        self.load_credentials_from_json()

        # Chame a função com os atributos corretos
        menu_principal_comprasnet(self.driver, self.username, self.password, self.settings_file)

        # Prossegue com o fluxo de divulgação de compras.
        numero_licitacao = self.get_licitacao_number()
        if self.table_data is not None:
            self.divulgacao_compras_click(numero_licitacao)

            item_inicio = int(self.get_item_inicio())
            primeiro_item = True

            for item_index in range(item_inicio - 1, len(self.table_data)):
                if primeiro_item:
                    # Para o primeiro item, clique em 'Alterar' e verifique o número do item
                    self.clicar_botao_alterar_e_verificar(item_index)
                    primeiro_item = False
                else:
                    # Para os próximos itens, apenas verifique o número do item
                    self.verificar_numero_item(item_index)

                self.conformidade_itens_comprasnet(item_index)
        else:
            print("Dados da tabela não carregados.")

    def divulgacao_compras_click(self, licitacao_num_input):
        try:
            # Esperar até que o overlay desapareça
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ui-blockui.ui-widget-overlay.ui-blockui-document"))
            )

            # Encontrar o elemento e rolar até ele
            elemento = self.driver.find_element(By.CSS_SELECTOR, ABRIR_DIVULGACAO_COMPRAS)
            self.driver.execute_script("arguments[0].scrollIntoView();", elemento)
            
            # Clicar no elemento usando JavaScript
            self.driver.execute_script("arguments[0].click();", elemento)

            aguardar_mudanca_janela(self.driver)
            hover_sobre_elemento(self.driver, MENU_LICITACAO)
            esperar_e_clicar(self.driver, ALTERAR_LICITACAO)
            esperar_e_preencher(self.driver, INPUT_LICITACAO_NUMERO, licitacao_num_input)
            esperar_e_clicar(self.driver, PESQUISAR_LICITACAO_BOTAO)
            esperar_e_clicar(self.driver, SELECIONAR_LICITACAO_ESCOLHIDA)
            esperar_e_clicar(self.driver, SELECIONAR_ITENS_LICITACAO)

        except Exception as e:
            print(f"Ocorreu um erro durante a navegação: {e}")
            import traceback
            traceback.print_exc()

    def clicar_botao_alterar_e_verificar(self, item_index):
        item_inicio = int(self.table_data.iloc[item_index]['item_num'])
        tabela = self.table_data  # DataFrame com os dados da tabela

        # Assegura que o driver está inicializado
        if not hasattr(self, 'driver') or self.driver is None:
            menu_principal_comprasnet(self.driver, self.username, self.password, self.settings_file)

        try:
            # Cria o seletor CSS para o botão "Alterar" do item inicial
            row_type = 'odd' if item_inicio % 2 != 0 else 'even'
            alterar_button_selector = f"tr.{row_type}:nth-child({item_inicio}) > td:nth-child(12) > a:nth-child(1)"

            # Clica no botão "Alterar" usando o seletor
            esperar_e_clicar(self.driver, alterar_button_selector, by=By.CSS_SELECTOR)

            # Aguarda até que o input com o número do item esteja visível
            item_input_selector = "#corpo > form:nth-child(10) > fieldset:nth-child(49) > table:nth-child(5) > tbody:nth-child(1) > tr:nth-child(3) > td:nth-child(1) > input:nth-child(1)"
            item_input_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, self.item_input_selector))
            )
            item_number_on_page = item_input_element.get_attribute('value')  # Pega o valor do atributo 'value' do input

            if str(item_inicio) == item_number_on_page:  # Compara o número do item escolhido com o número do item na página
                print(f"Item número {item_inicio} verificado com sucesso na página.")
                # Aqui você pode continuar com a próxima etapa do seu fluxo
            else:
                print(f"Erro: O número do item na página ({item_number_on_page}) não corresponde ao número do item escolhido ({item_inicio}).")
                QMessageBox.critical(None, "Erro de Verificação", f"O número do item na página ({item_number_on_page}) não corresponde ao número do item escolhido ({item_inicio}). O programa será encerrado.")
                # self.driver.quit()  # Fecha o navegador

        except TimeoutException:
            print("O campo com o número do item não foi encontrado na página dentro do tempo esperado.")
            QMessageBox.critical(None, "Erro de Carregamento", "O campo com o número do item não foi encontrado na página dentro do tempo esperado.")
            # self.driver.quit()  # Fecha o navegador

        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            # Imprime a stacktrace completa
            import traceback
            traceback.print_exc()
            # self.driver.quit()  # Fecha o navegador

    def conformidade_itens_comprasnet(self, item_index):
        try:
            # Obter os dados da linha atual baseado no index fornecido
            linha_atual = self.table_data.iloc[item_index]
            # Obter valores de 'quantidade_estimada' e 'valor_unitario' e calcular o valor total
            quantidade_estimada = float(linha_atual['quantidade_estimada'])
            valor_unitario = float(linha_atual['valor_unitario'])
            valor_total = quantidade_estimada * valor_unitario

            # Preencher a quantidade estimada
            quantidade_estimada_selector = "#corpo > form:nth-child(10) > fieldset:nth-child(49) > table:nth-child(13) > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(1) > input:nth-child(1)"
            quantidade_estimada_input = self.driver.find_element(By.CSS_SELECTOR, quantidade_estimada_selector)
            quantidade_estimada_input.clear()
            quantidade_estimada_input.send_keys(str(linha_atual['quantidade_estimada']))

            # Preencher a quantidade mínima (mesmo valor que a quantidade estimada)
            quantidade_minima_selector = "#corpo > form:nth-child(10) > fieldset:nth-child(49) > table:nth-child(13) > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(2) > input:nth-child(1)"
            quantidade_minima_input = self.driver.find_element(By.CSS_SELECTOR, quantidade_minima_selector)
            quantidade_minima_input.clear()
            quantidade_minima_input.send_keys(str(linha_atual['quantidade_estimada']))

            # Selecionar 'Menor Preço' no dropdown
            criterio_julgamento_selector = "#idComboCriterioJulgamento"
            criterio_julgamento_dropdown = Select(self.driver.find_element(By.CSS_SELECTOR, criterio_julgamento_selector))
            criterio_julgamento_dropdown.select_by_value("1")  # Assumindo que o valor '1' corresponde a 'Menor Preço'

            # Preencher o valor unitário
            valor_unitario_selector = "#corpo > form:nth-child(10) > fieldset:nth-child(49) > table:nth-child(13) > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(5) > input:nth-child(1)"
            valor_unitario_input = self.driver.find_element(By.CSS_SELECTOR, valor_unitario_selector)
            valor_unitario_input.clear()
            valor_unitario_formatado = "{:.4f}".format(valor_unitario)  # Formatar para 4 casas decimais
            valor_unitario_input.send_keys(valor_unitario_formatado)

            # Verificar se a opção está marcada
            carater_sigiloso_selector = "#corpo > form:nth-child(10) > fieldset:nth-child(49) > table:nth-child(13) > tbody:nth-child(1) > tr:nth-child(5) > td:nth-child(1) > input:nth-child(3)"
            carater_sigiloso_input = self.driver.find_element(By.CSS_SELECTOR, carater_sigiloso_selector)
            if not carater_sigiloso_input.is_selected():
                carater_sigiloso_input.click()  # Marcar a opção se não estiver marcada
                print("Opção de caráter sigiloso marcada.")

            # Selecionar 'Tipo I' ou 'Sem Benefício' no dropdown baseado no valor total
            tipo_beneficio_selector = "#idTipoBeneficio"
            tipo_beneficio_dropdown = Select(self.driver.find_element(By.CSS_SELECTOR, tipo_beneficio_selector))
            
            if valor_total <= 80000:
                tipo_beneficio_dropdown.select_by_value("1")  # Assumindo que o valor '1' corresponde a 'Tipo I'
                print("Tipo de benefício 'Tipo I' selecionado para o valor total de {:.2f}".format(valor_total))
            else:
                tipo_beneficio_dropdown.select_by_value("-1")  # Assumindo que o valor '-1' corresponde a 'Sem Benefício'
                print("Tipo de benefício 'Sem Benefício' selecionado para o valor total de {:.2f}".format(valor_total))
                
            print(f"Conformidade de itens realizada para o item {item_index + 1}.")

            # Selecionar 'Percentual' no dropdown de Tipo de Redução
            tipo_reducao_selector = "#idComboTipoReducao"
            tipo_reducao_dropdown = Select(self.driver.find_element(By.CSS_SELECTOR, tipo_reducao_selector))
            tipo_reducao_dropdown.select_by_value("1")
            print("Tipo de redução 'Percentual' selecionado.")

            # Preencher o valor '2,00' no campo de Intervalo Mínimo Entre Lances
            intervalo_minimo_lances_selector = "#idInputIntervaloMinimoEntreLances"
            intervalo_minimo_lances_input = self.driver.find_element(By.CSS_SELECTOR, intervalo_minimo_lances_selector)
            intervalo_minimo_lances_input.clear()
            intervalo_minimo_lances_input.send_keys("2,00")
            print("Valor de '2,00' inserido no campo de Intervalo Mínimo Entre Lances.")

            # Clicar no botão de opção "Permitir Adesão Ata"
            adesao_ata_selector = "#corpo > form:nth-child(10) > fieldset:nth-child(49) > table:nth-child(16) > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(1) > fieldset:nth-child(1) > legend:nth-child(1) > input:nth-child(3)"
            adesao_ata_input = self.driver.find_element(By.CSS_SELECTOR, adesao_ata_selector)
            adesao_ata_input.click()
            print("Opção 'Permitir Adesão Ata' selecionada.")

            # Clique no botão 'Salvar' antes de ir para o próximo item
            salvar_btn_selector = '#salvar'
            esperar_e_clicar(self.driver, salvar_btn_selector, by=By.CSS_SELECTOR)
            print(f"Botão 'Salvar' clicado para o item {item_index + 1}.")

            # Executar o JavaScript para clicar no botão 'Próximo Item'
            self.driver.execute_script("vaiParaProximoItem();")
            print(f"Botão 'Próximo Item' clicado para o item {item_index + 1}.")

            # Espere que o número do item seja atualizado para o próximo item
            numero_proximo_item_esperado = str(self.table_data.iloc[item_index + 1]['item_num']) if item_index + 1 < len(self.table_data) else None
            if numero_proximo_item_esperado:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.find_element(By.CSS_SELECTOR, self.item_input_selector).get_attribute('value') == numero_proximo_item_esperado
                )
                print(f"O número do item foi atualizado para {numero_proximo_item_esperado} na página.")
        
        except Exception as e:
            print(f"Ocorreu um erro durante a conformidade de itens: {e}")
            # Talvez você queira imprimir a stacktrace completa aqui
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "Erro de Conformidade", f"Ocorreu um erro durante a conformidade de itens para o item {item_index + 1}: {e}")
            # self.driver.quit()  # Fecha o navegador

    def verificar_numero_item(self, item_index):
        try:
            # Obter o número esperado do item a partir do DataFrame
            numero_item_esperado = str(self.table_data.iloc[item_index]['item_num'])

            # Aguarda até que o input com o número do item esteja visível
            item_input_selector = "#corpo > form:nth-child(10) > fieldset:nth-child(49) > table:nth-child(5) > tbody:nth-child(1) > tr:nth-child(3) > td:nth-child(1) > input:nth-child(1)"
            item_input_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, item_input_selector))
            )
            numero_item_na_pagina = item_input_element.get_attribute('value')  # Pega o valor do atributo 'value' do input

            if numero_item_esperado == numero_item_na_pagina:  # Compara o número do item esperado com o número do item na página
                print(f"Item número {numero_item_esperado} verificado com sucesso na página.")
                # Continua com a próxima etapa do seu fluxo
            else:
                print(f"Erro: O número do item na página ({numero_item_na_pagina}) não corresponde ao número do item esperado ({numero_item_esperado}).")
                QMessageBox.critical(None, "Erro de Verificação", f"O número do item na página ({numero_item_na_pagina}) não corresponde ao número do item esperado ({numero_item_esperado}). O programa será encerrado.")
                self.driver.quit()  # Fecha o navegador
                sys.exit()  # Encerra o programa

        except TimeoutException:
            print("O campo com o número do item não foi encontrado na página dentro do tempo esperado.")
            QMessageBox.critical(None, "Erro de Carregamento", "O campo com o número do item não foi encontrado na página dentro do tempo esperado.")

        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            import traceback
            traceback.print_exc()

class ParticipantsDialog(QDialog):
    def __init__(self, data, parent=None):
        super(ParticipantsDialog, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.table_view = QTableView(self)
        self.model = QStandardItemModel(self)
        self.table_view.setModel(self.model)
        self.layout.addWidget(self.table_view)
        
        # Configura os cabeçalhos e preenche a tabela com os dados
        self.model.setHorizontalHeaderLabels([str(col) for col in data.columns])
        for index, row in data.iterrows():
            items = [QStandardItem(str(cell)) for cell in row]
            self.model.appendRow(items)
        
        self.setWindowTitle("Órgãos Participantes")
        self.resize(800, 600)  # Ajuste o tamanho conforme necessário

class ParticipantesIRPDialog(QDialog):
    def __init__(self, parent=None):
        super(ParticipantesIRPDialog, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.settings_file = 'settings.json'
        self.last_opened_file = None # Último arquivo carregado

        # Layout horizontal para Nº da Licitação e Ano
        self.licitacao_layout = QHBoxLayout()
        self.licitacao_num_input = QLineEdit(self)
        self.licitacao_num_input.setPlaceholderText("Nº da Licitação")
        self.licitacao_layout.addWidget(self.licitacao_num_input)  # Correção aqui
        
        # Conectar o sinal de texto alterado ao método de salvamento das configurações
        self.licitacao_num_input.textChanged.connect(self.save_settings)

        self.licitacao_ano_input = QLineEdit(self)
        self.licitacao_ano_input.setText(str(datetime.now().year))  # Ano atual
        self.licitacao_layout.addWidget(self.licitacao_ano_input)  # Correção aqui
        self.layout.addLayout(self.licitacao_layout)  # Adiciona o layout horizontal ao layout principal

        # Botão para carregar o arquivo da tabela
        self.load_table_button = QPushButton("Carregar Tabela", self)
        self.load_table_button.clicked.connect(self.load_table)
        self.layout.addWidget(self.load_table_button)

        # Botão para conferir os órgãos participantes
        self.check_participants_button = QPushButton("Conferir Órgãos Participantes", self)
        self.check_participants_button.clicked.connect(self.check_participantes)
        self.layout.addWidget(self.check_participants_button)
        
        # Modelo e TableView para exibir dados
        self.model = QStandardItemModel(self)  
        self.tableView = QTableView(self)
        self.tableView.setModel(self.model)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Correção aplicada aqui
        self.layout.addWidget(self.tableView)

        # Label para instrução de escolha do item inicial
        self.item_inicio_label = QLabel("Escolha a partir de qual item o fluxo se iniciará:")
        self.layout.addWidget(self.item_inicio_label)  # Adiciona a Label ao layout

        # ComboBox para o número inicial do item
        self.item_inicio_combo = QComboBox(self)
        self.layout.addWidget(self.item_inicio_combo)  # Adiciona a ComboBox ao layout

        # Botão para confirmar a entrada
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.table_data = None  # DataFrame para armazenar dados da tabela
        self.setWindowTitle("Conferência dos Orgãos Participantes")

        self.load_settings()

    def check_participantes(self):
        if self.table_data_participantes is not None:
            # Cria e exibe a nova janela de diálogo com os dados da tabela
            dialog = ParticipantsDialog(self.table_data_participantes, self)
            dialog.exec()

        else:
            QMessageBox.warning(self, "Aviso", "Nenhuma aba de participantes carregada.")

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as file:
                settings = json.load(file)
                self.licitacao_num_input.setText(settings.get('licitacao_num', ''))
                self.last_opened_file = settings.get('last_opened_file', '')
                if self.last_opened_file and Path(self.last_opened_file).exists():
                    self.load_table(self.last_opened_file)
                else:
                    QMessageBox.warning(self, "Aviso", "O último arquivo carregado foi deletado ou está aberto em outro programa.")

    def save_settings(self):
        settings = {
            'licitacao_num': self.licitacao_num_input.text(),
            'last_opened_file': self.last_opened_file
        }
        with open(self.settings_file, 'w') as file:
            json.dump(settings, file, indent=4)
    
    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def load_table(self, file_name=None):
        if not file_name:
            file_name, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.ods)")
        if file_name:
            self.last_opened_file = file_name
            self.save_settings()  # Salvar configurações após carregar um novo arquivo
            try:
                # Carrega a primeira aba por padrão
                self.table_data = pd.read_excel(file_name)

                # Tentativa de carregar a aba "Participantes"
                try:
                    self.table_data_participantes = pd.read_excel(file_name, sheet_name='Participantes')
                    # Após carregar os dados em ParticipantesIRPDialog
                    # self.selenium_automation_instance.table_data_participantes = self.table_data_participantes

                except ValueError as e:
                    QMessageBox.critical(self, "Erro de Carregamento", f"Aba 'Participantes' não encontrada. Detalhes do erro: {e}")
                    self.table_data_participantes = None

                self.model.clear()
                self.model.setHorizontalHeaderLabels(self.table_data.columns)
                
                for index, row in self.table_data.iterrows():
                    items = [QStandardItem(str(cell)) for cell in row]
                    self.model.appendRow(items)

                # Preencher a ComboBox com os números dos itens
                self.item_inicio_combo.clear()  # Limpa os itens antigos
                item_nums = self.table_data['item_num'].astype(str).tolist()  # Converte os números dos itens para string
                self.item_inicio_combo.addItems(item_nums)  # Adiciona os números dos itens à ComboBox

                QMessageBox.information(self, "Carregamento Concluído", "Tabela carregada com sucesso!")

            except Exception as e:
                QMessageBox.critical(self, "Erro de Carregamento", f"Erro ao carregar o arquivo da tabela. Detalhes do erro: {e}")
                self.table_data = None
                self.table_data_participantes = None
        else:
            QMessageBox.warning(self, "Carregamento Cancelado", "Nenhum arquivo foi selecionado.")

    def get_licitacao_number(self):
        licitacao_num = self.licitacao_num_input.text().strip()
        licitacao_ano = self.licitacao_ano_input.text()
        return licitacao_num + licitacao_ano

    def get_item_inicio(self):
        return self.item_inicio_combo.currentText()  # Retorna o item selecionado na ComboBox

    def accept(self):
        super().accept()
        item_selecionado = self.get_item_inicio()
        print(f"Item selecionado: {item_selecionado}")
        self.save_settings()
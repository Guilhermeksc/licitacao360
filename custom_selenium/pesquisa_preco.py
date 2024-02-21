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
import json

class PesquisaPrecos(QDialog):
    def __init__(self, parent=None):
        super(PesquisaPrecos, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # Botão para carregar o arquivo da tabela
        self.load_table_button = QPushButton("Carregar Tabela", self)
        self.load_table_button.clicked.connect(self.load_table)
        self.layout.addWidget(self.load_table_button)

        # Adicionando QLineEdit para número da pesquisa de preços
        self.numero_pesquisa_edit = QLineEdit(self)
        self.numero_pesquisa_edit.setPlaceholderText("Informe o número da pesquisa de preços")
        self.layout.addWidget(self.numero_pesquisa_edit)

        # Número de pesquisa que vai está vazio quando o programa iniciar
        self.numero_pesquisa = ""

        # Adicionando botão de confirmação
        self.confirmar_button = QPushButton("Confirmar Número de Pesquisa", self)
        self.confirmar_button.clicked.connect(self.confirmar_numero_pesquisa)
        self.layout.addWidget(self.confirmar_button)

        # Ganchos de desencadeadores
        self.numero_pesquisa_edit.textChanged.connect(self.atualiza_numero_pesquisa)

        # Modelo e TableView para exibir dados
        self.model = QStandardItemModel(self)  
        self.tableView = QTableView(self)
        self.tableView.setModel(self.model)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Correção aplicada aqui
        self.layout.addWidget(self.tableView)

        # Botão para confirmar a entrada
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.table_data = None  # DataFrame para armazenar dados da tabela
        self.setWindowTitle("Carregue a tabela para pesquisa de preços")
        self.settings_file = 'settings_comprasnet.json'  # Caminho para o arquivo de configurações
        self.load_credentials_from_json()

    def atualiza_numero_pesquisa(self):
        self.numero_pesquisa = self.numero_pesquisa_edit.text().strip()
        print(f"atualiza_numero_pesquisa: Número de pesquisa de preços atualizado: {self.numero_pesquisa}")

    def confirmar_numero_pesquisa(self):
        # Forçar a atualização baseada no valor atual do QLineEdit, para diagnóstico
        temp_numero_pesquisa = self.numero_pesquisa_edit.text().strip()
        print(f"confirmar_numero_pesquisa: Número de pesquisa de preços confirmado: {temp_numero_pesquisa}")
        self.numero_pesquisa = temp_numero_pesquisa

        # Usar temp_numero_pesquisa para formar valor_pesquisa para diagnóstico
        valor_pesquisa = f"{temp_numero_pesquisa}/2024"
        print(f"confirmar_numero_pesquisa: Valor a ser usado na pesquisa: {valor_pesquisa}")


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

            # Aplicar a função de conversão à coluna "unidade_fornecimento"
            self.table_data["unidade_fornecimento"] = self.table_data["unidade_fornecimento"].apply(self.converter_unidade)

            for index, row in self.table_data.iterrows():
                items = [QStandardItem(str(cell)) for cell in row]
                self.model.appendRow(items)

            QMessageBox.information(self, "Carregamento Concluído", "Tabela carregada com sucesso!")

    def fluxo_pesquisa_de_precos(self):
        pesquisa_precos_dialog = PesquisaPrecos(self)
        if pesquisa_precos_dialog.exec() == QDialog.DialogCode.Accepted:
            self.table_data = pesquisa_precos_dialog.table_data
            if self.table_data is not None:
                self.abrir_comprasnet_pesquisa_precos()
            else:
                print("Dados da tabela não carregados.")
        else:
            print("Ação cancelada pelo usuário.")

    def abrir_comprasnet_pesquisa_precos(self):
        options = Options()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')

        service = Service(executable_path=WEBDRIVER_FIREFOX_PATH)    
        # self.driver = webdriver.Firefox(service=service, options=options)
    
        self.driver = webdriver.Firefox()
        self.driver.get("https://www.comprasnet.gov.br/seguro/loginPortal.asp")

        esperar_e_clicar(self.driver, "button.governo")
        esperar_e_preencher(self.driver, USER_FIELD_SELECTOR, self.username)
        esperar_e_preencher(self.driver, PASSWORD_FIELD_SELECTOR, self.password)
        esperar_e_clicar(self.driver, LOGIN_BUTTON_SELECTOR)

        # # Aguardar até que o overlay desapareça
        esperar_invisibilidade_elemento(self.driver, OVERLAY_SELECTOR)
        time.sleep(0.5)  # Necessário para carregar a página

        # Localizar e clicar no elemento desejado usando XPath
        esperar_e_clicar(self.driver, PAGINATION_ELEMENT_XPATH, by=By.XPATH)
        time.sleep(0.3)
        esperar_e_clicar(self.driver, OPTION_XPATH, by=By.XPATH) # Clicar na opção '2'
        time.sleep(0.3)
        esperar_e_clicar(self.driver, ABRIR_JANELA_PESQUISA_PRECOS) # Abrir nova janela IRP

        print(f"Janela atual: {self.driver.current_url}")
        aguardar_mudanca_janela(self.driver)
        print(f"Janela atual: {self.driver.current_url}")

        # Esperar até que o spinner desapareça
        WebDriverWait(self.driver, 20).until(
            EC.invisibility_of_element((By.ID, "spinner"))
        )
        print("Spinner desapareceu.")

        # Checar se há iframes e mudar para o iframe apropriado, se necessário
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        if len(iframes) > 0:
            self.driver.switch_to.frame(iframes[0])  # Assumindo que é o primeiro iframe

        # Substitua 0 pelo índice correto do iframe se houver mais de um
        if len(iframes) > 0:
            self.driver.switch_to.frame(0)

        try:
            campo_pesquisa = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, "//*[@id='termo-pesquisa']"))
            )
            campo_pesquisa.clear()  # Limpa qualquer texto existente no campo
            campo_pesquisa.send_keys(self.numero_pesquisa)

            try:
                # Esperar até que a lupa esteja visível e clicável
                lupa_pesquisa = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, LUPA_PESQUISA_PRECOS))
                )

                # Rolando a página até a lupa
                self.driver.execute_script("arguments[0].scrollIntoView(true);", lupa_pesquisa)
                time.sleep(1)  # Pequena pausa para permitir que a página se ajuste

                # Clicando na lupa com JavaScript
                self.driver.execute_script("arguments[0].click();", lupa_pesquisa)
            except TimeoutException:
                print("A lupa de pesquisa não ficou clicável no tempo esperado.")
            except ElementClickInterceptedException as e:
                print(f"Erro ao tentar clicar na lupa de pesquisa: {e}")

            print(f"Valor de self.numero_pesquisa antes de formar valor_pesquisa: {self.numero_pesquisa}")
            valor_pesquisa = f"{self.numero_pesquisa}/2024"
            print(f"Valor a ser usado na pesquisa: {valor_pesquisa}")

            clicar_no_botao_editar(self.driver, valor_pesquisa)

            print("Aguardando o desaparecimento do spinner...")
            esperar_invisibilidade_elemento(self.driver, "div#spinner")
            print("Spinner desapareceu.")

            # Esperar explicitamente até que o elemento esteja clicável antes de tentar clicar nele
            try:
                # Esperar até que o elemento esteja visível e clicável
                elemento_a_clicar = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, SELECIONAR_ITEM_CSS))
                )
                
                # Rolando a página até o elemento
                self.driver.execute_script("arguments[0].scrollIntoView(true);", elemento_a_clicar)
                time.sleep(1)  # Espera para permitir que a página se ajuste

                # Clicando no elemento com JavaScript
                self.driver.execute_script("arguments[0].click();", elemento_a_clicar)
            except TimeoutException:
                print("O elemento não ficou clicável no tempo esperado.")
            except ElementClickInterceptedException as e:
                print(f"Erro ao tentar clicar no elemento: {e}")

            # Substitua 'ELEMENTO_INDICATIVO_POS_SELECAO' pelo seletor CSS do elemento indicativo
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, TITULO_ADICIONAR_ITEM_XPATH)))

            self.processar_linhas_tabela()

        except NoSuchElementException:
            print("Campo de pesquisa não encontrado. Verifique o XPath e a presença de iframes.")


    def aguardar_e_interagir_com_modal(self):
        print("Aguardando a abertura do modal...")

        try:
            # Espera até que o modal com o título específico seja visível
            titulo_modal = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//h6[contains(text(), 'Catálogo Compras.gov.br')]"))
            )
            print("Modal encontrado.")

        except TimeoutException:
            print("Modal com título 'Catálogo Compras.gov.br' não encontrado.")
        except NoSuchElementException:
            print("Elemento específico dentro do modal não encontrado.")

    def processar_linhas_tabela(self):
        for index, row in self.table_data.iterrows():
            try:
                self.processar_linha(row, index)
            except Exception as e:
                print(f"Erro ao processar a linha {index}: {str(e)}")
                continue

    def processar_linha(self, row, index):
        time.sleep(0.3)
        try:
            # print("Esperando até que o elemento esteja visível...")
            elemento_a_clicar = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ADICIONAR_ITEM_PP_CSS))
            )
            
            # Use JavaScript para clicar no elemento
            self.driver.execute_script("arguments[0].click();", elemento_a_clicar)
            # print("Elemento clicado com sucesso usando JavaScript.")
        except TimeoutException:
            print("O elemento não ficou visível no tempo esperado.")
        except Exception as e:
            print(f"Erro ao clicar no elemento: {str(e)}")
        print("mudando a tela")
        time.sleep(0.3)
        self.aguardar_e_interagir_com_modal()

        catalogo = row['catalogo']
        quantidade_estimada = row['quantidade_estimada']
        unidade_fornecimento = row['unidade_fornecimento']
        print(f"Unidade de fornecimento encontrada na tabela: {unidade_fornecimento}")

        # Digitar o valor de 'catalogo' no campo de pesquisa
        campo_pesquisa = self.driver.find_element(By.XPATH, "//input[@placeholder='Digite aqui o material ou serviço a ser pesquisado']")
        campo_pesquisa.clear()
        campo_pesquisa.send_keys(catalogo)

        WebDriverWait(self.driver, 20).until(EC.invisibility_of_element_located((By.ID, "spinner")))

        try:
            # Tente clicar normalmente primeiro
            lupa = self.driver.find_element(By.CSS_SELECTOR, ".br-input > button:nth-child(2)")
            lupa.click()
        except ElementClickInterceptedException:
            # Se o clique normal falhar, use JavaScript para forçar o clique
            self.driver.execute_script("arguments[0].click();", lupa)

        # Aguardar os dados da página carregarem
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ELEMENTO_VOLTAR_INDICATIVO_CARREGAMENTO))
        )

        # Inserir a quantidade estimada no campo de quantidade
        campo_quantidade = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".p-inputnumber-input"))
        )
        campo_quantidade.clear()
        campo_quantidade.send_keys(str(quantidade_estimada))

        # Tentar inserir a quantidade estimada usando JavaScript
        self.driver.execute_script("arguments[0].value = arguments[1];", campo_quantidade, str(quantidade_estimada))

        try:
            # Esperar até que o spinner desapareça
            WebDriverWait(self.driver, 20).until(EC.invisibility_of_element_located((By.ID, "spinner")))
            time.sleep(0.5)  # Pequena pausa adicional para garantir que tudo esteja carregado

            # Esperar até que o dropdown esteja visível
            dropdown = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "select.ng-pristine"))
            )

            # Scroll até o dropdown para garantir que está na tela
            self.driver.execute_script("arguments[0].scrollIntoView(true);", dropdown)
            time.sleep(0.5)  # Pequena pausa após o scroll

            try:
                dropdown.click()
            except ElementClickInterceptedException:
                # Se o clique normal falhar, use JavaScript para forçar o clique
                self.driver.execute_script("arguments[0].click();", dropdown)

            # Selecionar a unidade de fornecimento na lista suspensa
            print(f"Tentando selecionar a unidade de fornecimento: {row['unidade_fornecimento']}")
            unidade_selecionada = self.selecionar_unidade(row['unidade_fornecimento'])

            if not unidade_selecionada:
                QMessageBox.critical(self, "Erro de Seleção", f"Erro ao selecionar unidade para o item {row['catalogo']}.")
                return  # Encerra a execução se a unidade não foi selecionada

            if unidade_selecionada:
                # Se a unidade foi selecionada, então proceda para clicar no botão adicionar
                xpath_linha_catalogo = f"//tr[.//td[contains(text(), '{catalogo}')]]"
                linha_catalogo = WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH, xpath_linha_catalogo))
                )

                verificar_modal(self.driver)
                botao_adicionar = linha_catalogo.find_element(By.XPATH, ".//button[@title='Adicionar']")
                botao_adicionar = WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH, f"//tr[.//td[contains(text(), '{row['catalogo']}')]]//button[@title='Adicionar']"))
                )
                botao_adicionar.click()

                WebDriverWait(self.driver, 20).until(
                    EC.invisibility_of_element((By.ID, "spinner"))
                )
                print("Spinner desapareceu.")

        except Exception as e:
            QMessageBox.critical(self, "Erro no Processamento", f"Erro ao processar a linha {index}: {str(e)}")
            return

    def esperar_invisibilidade_element(self, driver, seletor):
        try:
            print(f"Esperando pela invisibilidade do elemento: {seletor}")
            WebDriverWait(driver, 30).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, seletor))
            )
            print(f"Elemento {seletor} agora está invisível.")
        except TimeoutException:
            print(f"O elemento '{seletor}' ainda está visível após o tempo de espera.")

    def selecionar_unidade(self, unidade_nome):
        try:
            # Aguardar até que o spinner desapareça
            self.esperar_invisibilidade_element(self.driver, "div#spinner")
            time.sleep(0.5)  # Pequena pausa após o desaparecimento do spinner
            print("DROPBOX - Spinner desapareceu.")

            print("Localizando o dropdown...")
            dropdown = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "select.ng-pristine"))
            )
            print("Dropdown localizado.")

            # Verifica novamente a presença do spinner antes de clicar
            if self.driver.find_elements(By.CSS_SELECTOR, "div#spinner"):
                print("Spinner detectado novamente, aguardando...")
                self.esperar_invisibilidade_element(self.driver, "div#spinner")
                print("Spinner não mais presente.")

            action = ActionChains(self.driver)
            action.move_to_element(dropdown).perform()
            print("Cursor movido para o dropdown.")

            try:
                time.sleep(0.5)  # Pequena pausa antes de tentar clicar
                dropdown.click()
                print("Dropdown clicado com sucesso.")
            except ElementClickInterceptedException:
                print("Clique interceptado, tentando com JavaScript...")
                self.driver.execute_script("arguments[0].click();", dropdown)
                print("Clique no dropdown realizado com JavaScript.")

            print("Criando objeto Select...")
            select = Select(dropdown)

            # Procura pela unidade na lista de opções
            print("Procurando pela unidade na lista de opções...")
            opcoes_texto = [opcao.text.strip() for opcao in select.options]
            if unidade_nome in opcoes_texto:
                select.select_by_visible_text(unidade_nome)
                print(f"Unidade '{unidade_nome}' selecionada.")
                return True
            else:
                # Se não encontrar, tenta com a vírgula no lugar do ponto
                unidade_nome_alternativo = substituir_ponto_por_virgula(unidade_nome)
                if unidade_nome_alternativo in opcoes_texto:
                    select.select_by_visible_text(unidade_nome_alternativo)
                    print(f"Unidade '{unidade_nome_alternativo}' selecionada com substituição de ponto por vírgula.")
                    return True
                else:
                    print(f"Nenhuma opção válida encontrada para '{unidade_nome}' ou '{unidade_nome_alternativo}'.")
                    return False

        except Exception as e:
            print(f"Erro ao tentar selecionar '{unidade_nome}' no dropdown:", str(e))
            self.driver.save_screenshot("erro_diagnostico.png")
            print("Screenshot salvo para diagnóstico de erro.")
            return False

    def converter_unidade(self, unidade):
        unidade = unidade.strip()
        
        # Verificar se é abreviação de Grama
        if re.search(r'(\d+)\s*G\b', unidade, re.IGNORECASE):
            return re.sub(r'(\d+)\s*G\b', r'\1 Grama', unidade, flags=re.IGNORECASE)
        
        # Verificar se é abreviação de Mililitro
        elif re.search(r'(\d+)\s*ML\b', unidade, re.IGNORECASE):
            return re.sub(r'(\d+)\s*ML\b', r'\1 Mililitro', unidade, flags=re.IGNORECASE)
        
        # Verificar se é "Unidade"
        elif unidade.lower() == "unidade":
            return "Unidade"
        
        return unidade

def substituir_ponto_por_virgula(valor):
    return valor.replace(".", ",")

def clicar_no_botao_editar(driver, texto):
    try:
        # Esperar até que o spinner desapareça para garantir que a página esteja totalmente carregada
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element((By.ID, "spinner"))
        )

        # Localizar a linha da tabela que contém o texto especificado
        linha = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, f"//tr[.//span[text()='{texto}']]"))
        )

        # Dentro dessa linha, encontrar o botão 'editar' e clicar
        botao_editar = linha.find_element(By.XPATH, ".//button[@data-target='#editarCotacao']")
        botao_editar.click()

    except TimeoutException:
        print(f"Não foi possível encontrar a linha com o texto {texto} ou o botão editar.")
    except NoSuchElementException:
        print("Botão editar não encontrado na linha.")
    except ElementClickInterceptedException:
        print("Elemento ainda está sendo interceptado por outro elemento.")

# Função para verificar se o modal está presente e visível
def verificar_modal(driver):
    try:
        modal = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "modal-container.modal.fade.show"))
        )
        # Se o modal estiver presente, tente fechar ou aguardar seu desaparecimento
        # Se houver um botão de fechar no modal, você pode tentar clicar nele
        botao_fechar = modal.find_element(By.CSS_SELECTOR, "botão de fechar")  # Atualize com o seletor correto
        botao_fechar.click()
    except TimeoutException:
        print("Modal não encontrado ou já desapareceu.")
    except NoSuchElementException:
        print("Botão de fechar não encontrado no modal.")
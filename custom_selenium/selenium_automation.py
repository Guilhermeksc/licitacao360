from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtGui import *
from database.styles.styless import get_transparent_title_style
from database.styles.button_styles import apply_button_style, CustomToolButton
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, ElementClickInterceptedException
from diretorios import WEBDRIVER_FIREFOX_PATH, ICONS_DIR
from custom_selenium.gui_module import (
    JSONDialog, AlteracaoIRPDialog, DivulgacaoComprasDialog,
    ParticipantesIRPDialog, AnaliseParticipantesIRPDialog
)
from custom_selenium.seletores_selenium import *
from custom_selenium.utils_selenium import *
from custom_selenium.pesquisa_preco import PesquisaPrecos
from custom_selenium.divulgacao_compras import DivulgacaoComprasDialog
from custom_selenium.login_comprasnet import LoginDialog
from custom_selenium.inserir_catalogo import IRPDialog
import time
import re
import numpy as np
import json

class SeleniumAutomacao(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.username = None
        self.password = None
        self.dataframe = None  # Armazena o DataFrame carregado
        self.item_input_selector = "#corpo > form:nth-child(10) > fieldset:nth-child(49) > table:nth-child(5) > tbody:nth-child(1) > tr:nth-child(3) > td:nth-child(1) > input:nth-child(1)"
        self.table_data_participantes = None
        self.settings_file = 'settings_comprasnet.json'  # Caminho para o arquivo de configurações
        self.initUI()

    def check_credentials_exist(self):
        try:
            with open(self.settings_file, 'r') as f:
                data = json.load(f)
                username = data.get('username', '')
                remember_password = data.get('remember_password', False)
                if username and remember_password:
                    return True, username  # Credenciais existem
                else:
                    return False, None  # Credenciais não existem
        except FileNotFoundError:
            return False, None  # Arquivo não existe
        
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

    def initUI(self):
        # Layout Vertical Principal
        grid_layout = QGridLayout(self)

        # Verificar se credenciais existem
        credentials_exist, username = self.check_credentials_exist()

        # Ajustar o texto do label com base na existência de credenciais
        if credentials_exist:
            access_label_text = "Acesso ao Comprasnet - Status: Logado"
        else:
            access_label_text = "Acesso ao Comprasnet"

        # Rótulo para "Acesso ao Comprasnet"
        self.label_acesso_comprasnet = QLabel(access_label_text)
        self.label_acesso_comprasnet.setStyleSheet(get_transparent_title_style())
        grid_layout.addWidget(self.label_acesso_comprasnet, 0, 0, 1, 3) 

        # Criação de botao login
        self.login_comprasnet = LoginDialog(self)
        self.login_comprasnet.login_successful.connect(self.on_login_successful)

        self.btn_login = self.createButton(
            "login_branco.svg",
            "login_ciano.svg", "Login", self.login_comprasnet.show_login_dialog)
        grid_layout.addWidget(self.btn_login, 1, 0)

        # Rótulo para "Planejamento da Contratação"
        label_planejamento = QLabel("Planejamento da Contratação")
        label_planejamento.setStyleSheet(get_transparent_title_style())  # Ajuste o estilo conforme necessário
        grid_layout.addWidget(label_planejamento, 2, 0, 1, 3)  # Span across 3 columns

        # Criação de botões e adição ao grid_layout para a primeira linha de botões
        self.btn_tratar_dados_json = self.createButton("json_branco.svg", "json_ciano.svg", "Gerar\nTabela\n(JSON)", self.mostrar_dialogo_json)
        grid_layout.addWidget(self.btn_tratar_dados_json, 3, 0)

        self.lancamento_catmat = IRPDialog(self)
        self.btn_lancamento_catmat = self.createButton("catalog_branco.svg", "catalog_ciano.svg", "Inserir\nCatálogo", self.lancamento_catmat.fluxo_lancamento_irp)
        grid_layout.addWidget(self.btn_lancamento_catmat, 3, 1)

        self.pesquisa_precos = PesquisaPrecos(self)
        self.btn_pesquisa_precos = self.createButton("money_branco.svg", "money_ciano.svg", "Pesquisa\nde Preços", self.pesquisa_precos.fluxo_pesquisa_de_precos)
        grid_layout.addWidget(self.btn_pesquisa_precos, 3, 2)

        self.pesquisa_precos = PesquisaPrecos(self)
        self.btn_pesquisa_precos = self.createButton("money_branco.svg", "money_ciano.svg", "Revisão da\nPesquisa\nde Preços", self.pesquisa_precos.fluxo_pesquisa_de_precos)
        grid_layout.addWidget(self.btn_pesquisa_precos, 3, 3)

        # Criação de botões e adição ao grid_layout para a segunda linha de botões
        self.btn_alterar_dados = self.createButton("engineering_branco.svg", "engineering_ciano.svg", "Conformidade\ndo IRP", self.fluxo_alteracao_irp)
        grid_layout.addWidget(self.btn_alterar_dados, 3, 4)

        # Rótulo para "Consolidação de Demandas"
        label_consolidacao = QLabel("Consolidação de Demandas")
        label_consolidacao.setStyleSheet(get_transparent_title_style())  # Ajuste o estilo conforme necessário
        grid_layout.addWidget(label_consolidacao, 4, 0, 1, 3)  # Span across 3 columns
        username = None
        password = None
        self.divulgacao_compras = DivulgacaoComprasDialog(username, password, self)
        self.btn_tratar_dados_json.clicked.connect(self.divulgacao_compras.abrir_fluxo_divulgacao_compras)
        self.btn_tratar_dados_json = self.createButton("megaphone_branco.svg", "megaphone_ciano.svg", "Divulgação\nIRP", self.divulgacao_compras.abrir_fluxo_divulgacao_compras)
        grid_layout.addWidget(self.btn_tratar_dados_json, 5, 0)

        self.btn_analisar_participantes = self.createButton("confirmation_branco.svg", "confirmation_ciano.svg", "Analisar\nParticipantes", self.fluxo_analise_participantes)
        grid_layout.addWidget(self.btn_analisar_participantes, 5, 1)

        self.btn_om_participantes = self.createButton("planilha_branco.svg", "planilha_ciano.svg", "Planilha de\nConsolidação", self.fluxo_participantes_irp)
        grid_layout.addWidget(self.btn_om_participantes, 5, 2)

        self.btn_om_participantes = self.createButton("stakeholder_branco.svg", "stakeholder_ciano.svg", "Verificar\nParticipantes", self.fluxo_participantes_irp)
        grid_layout.addWidget(self.btn_om_participantes, 5, 3)

    def on_login_successful(self, username, password):
        self.divulgacao_compras = DivulgacaoComprasDialog(username, password, self)

        # Agora que o login foi bem-sucedido, habilite o botão e defina a ação
        self.btn_tratar_dados_json.setEnabled(True)

        # Conecte o sinal clicked após criar a instância divulgacao_compras
        self.btn_tratar_dados_json.clicked.connect(self.divulgacao_compras.fluxo_divulgacao_compras)

    def createButton(self, icon_white, icon_cyan, text, click_function, isTransparent=False, iconSize=QSize(60, 60), buttonSize=QSize(140, 160)):
        button = CustomToolButton(icon_white, icon_cyan, iconSize, buttonSize, isTransparent)
        if text:
            button.setText(text)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # Conecte o botão apenas se click_function não for None
        if click_function is not None:
            button.clicked.connect(click_function)
        
        apply_button_style(button, isTransparent)
        return button

    def mostrar_dialogo_json(self):
        dialogo = JSONDialog(self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.dataframe = dialogo.dataframe  # Atualiza o DataFrame

    def esperar_e_clicar(self, selector, by=By.XPATH, max_tentativas=3, timeout=20):
        tentativas = 0
        while tentativas < max_tentativas:
            try:
                elemento = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                elemento.click()
                print(f"Elemento {selector} clicado com sucesso.")
                return
            except TimeoutException:
                print(f"Tentativa {tentativas + 1}: O elemento {selector} não ficou clicável após {timeout} segundos. Tentando novamente...")
            except Exception as e:
                print(f"Tentativa {tentativas + 1}: Erro ao tentar clicar no elemento {selector}: {e}")
            tentativas += 1

        # Se todas as tentativas normais falharem, tenta clicar via JavaScript
        try:
            self.driver.execute_script("arguments[0].click();", self.driver.find_element(by, selector))
            print(f"Clique forçado via JavaScript no elemento {selector}.")
        except Exception as e:
            print(f"Erro ao tentar clicar via JavaScript no elemento {selector}: {e}")

    def esperar_e_clicar(self, selector, by=By.CSS_SELECTOR, timeout=20):
        try:
            elemento = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            if elemento:
                elemento.click()
                print(f"Clicado com sucesso no elemento: {selector}")
        except TimeoutException:
            print(f"Timeout: O elemento {selector} não ficou clicável após {timeout} segundos.")
        except NoSuchElementException:
            print(f"Elemento não encontrado: {selector}")
        except Exception as e:
            print(f"Erro ao clicar no elemento {selector}: {e}")

    def esperar_elemento_clicavel(self, selector, by=By.CSS_SELECTOR, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )

    def esperar_e_preencher(self, selector, texto, by=By.CSS_SELECTOR, timeout=20):
        elemento = self.esperar_elemento_visivel(selector, by, timeout)
        if elemento:
            elemento.clear()
            elemento.send_keys(texto)
        else:
            print(f"Não foi possível preencher o campo de texto: {selector}")

    def esperar_elemento_visivel(self, selector, by=By.CSS_SELECTOR, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, selector))
            )
        except TimeoutException:
            print(f"Timeout: O elemento {selector} não ficou visível após {timeout} segundos.")
            return None

    def esperar_elemento_estado(self, selector, by, estado_esperado, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.find_element(by, selector).get_attribute("estado") == estado_esperado
            )
        except TimeoutException:
            print(f"Timeout: O estado do elemento {selector} não mudou para {estado_esperado} após {timeout} segundos.")

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

    def esperar_invisibilidade_elemento(self, selector, by=By.CSS_SELECTOR, timeout=20):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element((by, selector))
            )
        except TimeoutException:
            print(f"O elemento com o seletor {selector} não se tornou invisível no tempo esperado.")

    def aguardar_mudanca_janela(self, timeout=20):
        janelas_iniciais = self.driver.window_handles
        print("Janelas antes da mudança:", janelas_iniciais)

        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: len(driver.window_handles) != len(janelas_iniciais)
            )
            janelas_novas = self.driver.window_handles
            print("Janelas após a mudança:", janelas_novas)

            # Muda para a nova janela
            for janela in janelas_novas:
                if janela not in janelas_iniciais:
                    self.driver.switch_to.window(janela)
                    print("Mudou para nova janela:", self.driver.title)
                    break
        except TimeoutException:
            print("A nova janela não foi detectada no tempo esperado.")

    def tratar_alertas_seguranca(self):
        try:
            self.esperar_e_clicar("#advancedButton", timeout=5)
            self.esperar_e_clicar("#exceptionDialogButton", timeout=5)
        except TimeoutException:
            print("Nenhum alerta de segurança foi encontrado.")

    def hover_sobre_elemento(self, selector, by=By.CSS_SELECTOR, timeout=20):
        try:
            elemento = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, selector))
            )
            ActionChains(self.driver).move_to_element(elemento).perform()
        except TimeoutException:
            print(f"Não foi possível passar o mouse sobre o elemento com o seletor {selector}.")

    def get_title(self):
        return "Selenium Automação"

    def get_content_widget(self):
        return self

    def aguardar_e_mudar_para_popup(self):
        time.sleep(2)  # Pequena pausa
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if "Catálogo Compras.gov.br" in self.driver.title:
                print("Foco mudado para a janela do pop-up.")
                break

    def fluxo_alteracao_irp(self):
        alteracao_irp_dialog = AlteracaoIRPDialog(self)
        if alteracao_irp_dialog.exec() == QDialog.DialogCode.Accepted:
            irp_number = alteracao_irp_dialog.get_irp_number()
            item_inicio = int(alteracao_irp_dialog.get_item_inicio())

            print(f"Iniciando a partir do item: {item_inicio}")
            self.table_data = alteracao_irp_dialog.table_data
            if self.table_data is not None:
                self.abrir_comprasnet_irp(irp_number)
                self.alterar_dados(item_inicio)  # Passar o item de início como argumento
            else:
                print("Dados da tabela não carregados.")
        else:
            print("Ação cancelada pelo usuário.")

    def alterar_dados(self, item_inicio):
        if self.table_data is None:
            print("Dados da tabela não estão disponíveis.")
            return

        itens_alterados_sucesso = []  # Lista para armazenar os itens alterados com sucesso
        item_erro = None  # Variável para armazenar o item que causou o erro

        # item_inicio = int(self.get_item_inicio())  # Linha 433 do erro
        linha_inicio = self.table_data.index[self.table_data['item_num'] == item_inicio].tolist()

        if not linha_inicio:
            print(f"Item de início {item_inicio} não encontrado na tabela.")
            return

        linha_inicio = linha_inicio[0]
        tentativas_max = 3
        for index_global in range(linha_inicio, len(self.table_data)):
            row = self.table_data.iloc[index_global]
            seletor_paginacao = self.determinar_seletor_paginacao(index_global + 1)
            if seletor_paginacao:
                self.esperar_e_clicar(seletor_paginacao, By.CSS_SELECTOR)

            index_local = index_global % 20  # Índice local à página (0 a 19)
            item_num_sequencial = row['item_num']

            try:
                # Código para clicar no botão "Alterar"
                nth_child = index_local + 1
                row_type = "odd" if nth_child % 2 != 0 else "even"
                botao_alterar = f"tr.{row_type}:nth-child({nth_child}) > td:nth-child(9) > a:nth-child(1)"
                self.esperar_e_clicar(botao_alterar, By.CSS_SELECTOR)

                janela_principal = self.driver.current_window_handle

                # Verificação após clicar no botão "Alterar"
                seletor_item_num = f"input[name='item.numeroOrdemItem'][value='{item_num_sequencial}']"
                if self.verificar_existencia_elemento(seletor_item_num):
                    print(f"Item número {item_num_sequencial} encontrado e pronto para ser alterado.")
                    itens_alterados_sucesso.append(item_num_sequencial)  # Adicionar à lista de sucesso
                else:
                    print(f"Erro: Item número {item_num_sequencial} não encontrado na página após clicar em Alterar.")
                    item_erro = item_num_sequencial
                    break  # Sair do loop

                valor_unitario_xpath = "/html/body/div[2]/table/tbody/tr[2]/td/div[3]/form/table[1]/tbody/tr[2]/td/div[3]/table[2]/tbody/tr[2]/td[5]/input"
                elemento_valor_unitario = self.tentar_localizar_elemento(valor_unitario_xpath)
                if elemento_valor_unitario is None:
                    continue  # Se não encontrou o elemento, pula para a próxima iteração

                valor_unitario = row['valor_unitario']
                print(f"Preparando para inserir o valor unitário: {valor_unitario}")

                if not self.preencher_e_verificar_valor_unitario(valor_unitario, valor_unitario_xpath):
                    continue  # Pula para a próxima iteração se não for bem-sucedido

                # Selecionar a opção "Não" em 'valor_sigiloso'
                valor_sigiloso_nao_xpath = "/html/body/div[2]/table/tbody/tr[2]/td/div[3]/form/table[1]/tbody/tr[2]/td/div[3]/table[3]/tbody/tr[1]/td/div/input[2]"
                self.esperar_e_clicar(valor_sigiloso_nao_xpath, By.XPATH)

                # Clicar no botão "Localizar"
                botao_localizar_xpath = "/html/body/div[2]/table/tbody/tr[2]/td/div[3]/form/table[1]/tbody/tr[2]/td/div[3]/fieldset/table/tbody/tr[2]/td[2]/input"
                self.esperar_e_clicar(botao_localizar_xpath, By.XPATH)

                # Verificar a existência do elemento adicional e clicar nele se existir
                elemento_adicional_xpath = "/html/body/div[2]/table/tbody/tr[2]/td/div[3]/form/table[1]/tbody/tr[2]/td/div[3]/fieldset/div/table/tbody/tr/td[3]/a"
                try:
                    elemento_adicional = self.driver.find_element(By.XPATH, elemento_adicional_xpath)
                    elemento_adicional.click()
                    print("Elemento adicional clicado.")
                except NoSuchElementException:
                    print("Elemento adicional não encontrado. Continuando.")

                # Tratar pop-up de localização
                self.tratar_popup_localizacao()

                # Voltar para a janela principal
                self.driver.switch_to.window(janela_principal)

                time.sleep(0.2)
                # Digitar quantidade (da tabela) e incluir município
                quantidade_xpath = "/html/body/div[2]/table/tbody/tr[2]/td/div[3]/form/table[1]/tbody/tr[2]/td/div[3]/fieldset/table/tbody/tr[2]/td[3]/input"
                self.esperar_e_preencher(quantidade_xpath, str(row['quantidade_estimada']), By.XPATH)

                botao_incluir_municipio_xpath = "//*[@id='incluirMunicipio']"
                self.esperar_e_clicar(botao_incluir_municipio_xpath, By.XPATH)

                self.driver.switch_to.window(janela_principal)

                self.aguardar_e_mudar_para_popup()
                time.sleep(0.2)
                # Clicar no botão "Salvar Item" para finalizar a alteração
                botao_salvar_item = "//*[@id='alterar']"
                time.sleep(0.2)
                self.esperar_e_clicar(botao_salvar_item, By.XPATH)
                time.sleep(0.2)
                self.clicar_botao_ok_popup()
                time.sleep(0.2)
                self.aguardar_e_mudar_para_popup()

                tentativas = 0
                while tentativas < tentativas_max:
                    try:
                        # Clicar no botão "Salvar Item" para finalizar a alteração
                        botao_itens_relacao = "//*[@id='itens']"
                        time.sleep(0.2)
                        self.esperar_e_clicar(botao_itens_relacao, By.XPATH)
                        time.sleep(0.2)
                        print(f"Tentativa {tentativas + 1}: Clicou no botão 'Salvar Item'.")

                        # Verificar se a mudança esperada ocorreu na página
                        if self.verificar_mudanca_esperada_apos_clique():
                            time.sleep(0.2)
                            print("Mudança confirmada após clique no botão 'Salvar Item'.")
                            break  # Sair do loop de tentativas
                        else:
                            print(f"Tentativa {tentativas + 1}: Mudança esperada não detectada. Tentando novamente.")
                            tentativas += 1
                    except Exception as e:
                        print(f"Erro ao tentar clicar no botão 'Salvar Item': {e}")
                        tentativas += 1
                        if tentativas == tentativas_max:
                            print("Número máximo de tentativas atingido. Encerrando a operação.")
                            return  # Encerra a função se o número máximo de tentativas for atingido

            except Exception as e:
                print(f"Erro durante a alteração de dados: {e}")

        # Código para exibir a mensagem de alerta se houver um erro
        if item_erro is not None:
            itens_alterados_texto = ', '.join(str(num) for num in itens_alterados_sucesso)
            mensagem_erro = (f"Itens alterados com sucesso: {itens_alterados_texto}\n"
                            f"Erro encontrado no item número: {item_erro}\n"
                            "O programa será encerrado.")
            QMessageBox.critical(None, "Erro de Alteração", mensagem_erro)
        self.driver.quit()  # Fecha o navegador   

    def tentar_localizar_elemento(self, xpath, max_tentativas=3):
        tentativas = 0
        while tentativas < max_tentativas:
            try:
                elemento = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, xpath))
                )
                return elemento
            except TimeoutException:
                print(f"Tentativa {tentativas + 1}: Não foi possível localizar o elemento {xpath}. Tentando novamente...")
                tentativas += 1
                if tentativas == max_tentativas:
                    print("Não foi possível localizar o elemento após várias tentativas.")
                    return None
            except Exception as e:
                print(f"Tentativa {tentativas + 1}: Erro ao tentar localizar o elemento: {e}")
                tentativas += 1
                if tentativas == max_tentativas:
                    print("Erro na localização do elemento após várias tentativas.")
                    return None
        return None
    
    def verificar_mudanca_esperada_apos_clique(self):
        try:
            # Aguarda a presença do elemento específico na página
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='copiarItens']"))
            )
            print("Elemento 'copiarItens' encontrado após o clique.")
            return True  # O elemento foi encontrado
        except TimeoutException:
            print("Aguardando o elemento 'copiarItens' após o clique...")
            return False  # O elemento não foi encontrado no tempo esperado

    def tratar_popup_localizacao(self):
        # Aguardar e mudar para o pop-up
        self.aguardar_e_mudar_para_popup()

        # Preencher o campo com "Brasília"
        campo_brasilia_xpath = "/html/body/table/tbody/tr/td/div[2]/form/table/tbody/tr[1]/td/table[1]/tbody/tr[2]/td/input"
        self.esperar_e_preencher(campo_brasilia_xpath, "Brasília", By.XPATH)

        # Clicar no botão "Pesquisar"
        botao_pesquisar_xpath = "//*[@id='consultar']"
        self.esperar_e_clicar(botao_pesquisar_xpath, By.XPATH)

        # Selecionar o município e fechar o pop-up
        selecionar_municipio_xpath = "/html/body/table/tbody/tr/td/div[2]/form/table/tbody/tr[2]/td/table/tbody/tr[1]/td[3]/a"
        self.esperar_e_clicar(selecionar_municipio_xpath, By.XPATH)

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

    def preencher_e_verificar_valor_unitario(self, valor_unitario, xpath, max_tentativas=3):
        tentativas = 0
        while tentativas < max_tentativas:
            try:
                time.sleep(0.2)
                valor_unitario_formatado = "{:.4f}".format(float(valor_unitario)).replace('.', ',')
                print(f"valor_unitario: {valor_unitario}, valor_unitario_xpath: {xpath}, valor_unitario_formatado: {valor_unitario_formatado}")
                time.sleep(0.2)
                elemento = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, xpath))
                )
                elemento.clear()
                time.sleep(0.2)
                elemento.send_keys(valor_unitario_formatado)
                time.sleep(0.2)  # Aumentando o delay para permitir a atualização do campo

                # Captura e verificação do valor inserido
                valor_inserido = elemento.get_attribute('value')
                print(f"Valor lido do campo após inserção: '{valor_inserido}'")

                valor_inserido_formatado = valor_inserido.replace('.', '').replace(',', '.')
                if valor_inserido and abs(float(valor_inserido_formatado) - float(valor_unitario)) < 0.0001:
                    print(f"Valor {valor_unitario_formatado} inserido com sucesso.")
                    return True
                else:
                    print(f"Tentativa {tentativas + 1}: Valor inserido difere do esperado. Esperado: {valor_unitario_formatado}, Inserido: {valor_inserido}")

            except Exception as e:
                print(f"Tentativa {tentativas + 1}: Não foi possível verificar o valor inserido: {e}")

            tentativas += 1

        print(f"Não foi possível inserir o valor corretamente após {max_tentativas} tentativas.")
        return False

    def determinar_seletor_paginacao(self, numero_item):
        # Cada página contém 20 itens, então determinar o número da página
        numero_pagina = (numero_item - 1) // 20 + 1
        # Não é necessário selecionar a página para a primeira página
        if numero_pagina == 1:
            return None
        # Calcula qual filho 'nth-child' deve ser selecionado
        nth_child = numero_pagina + 2
        return f".pagelinks > a:nth-child({nth_child})"

    def verificar_existencia_elemento(self, seletor):
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor)))
            return True
        except TimeoutException:
            return False

    def fluxo_divulgacao_compras(self):
        divulgacao_compras_dialog = DivulgacaoComprasDialog(self)
        if divulgacao_compras_dialog.exec() == QDialog.DialogCode.Accepted:
            numero_licitacao = divulgacao_compras_dialog.get_licitacao_number()
            self.table_data = divulgacao_compras_dialog.table_data

            if self.table_data is not None:
                if not hasattr(self, 'driver') or self.driver is None:
                    self.menu_principal_comprasnet()

                self.divulgacao_compras_click(numero_licitacao)

                item_inicio = int(divulgacao_compras_dialog.get_item_inicio())
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
        else:
            print("Ação cancelada pelo usuário.")

    def fluxo_analise_participantes(self):
        analise_participantes_dialog = AnaliseParticipantesIRPDialog(self)
        if analise_participantes_dialog.exec() == QDialog.DialogCode.Accepted:
            irp_number = analise_participantes_dialog.get_irp_number()
            item_inicio = int(analise_participantes_dialog.get_item_inicio())
            pagina_inicial = (item_inicio - 1) // 20 + 1

            print(f"Iniciando a partir do item: {item_inicio} na página {pagina_inicial}")
            self.table_data = analise_participantes_dialog.table_data
            if self.table_data is not None:
                self.load_credentials_from_json()
                self.driver = create_driver(WEBDRIVER_FIREFOX_PATH)
                abrir_comprasnet(self.driver, self.username, self.password)
                selecionar_analise_irp(self.driver)
                selecionar_irp(self.driver, irp_number)

                # Navega até a página inicial necessária
                for i in range(1, pagina_inicial):
                    sucesso, msg = navegar_para_pagina(self.driver, i + 1)
                    if not sucesso:
                        print(f"Falha na navegação: {msg}")
                        self.driver.quit()
                        return

                try:
                    # Chamando a função analisar_itens com o item de início e os dados da tabela
                    analisar_itens(self.driver, item_inicio, self.table_data)
                    print("Todos os itens foram processados.")
                except Exception as e:
                    print(f"Erro ao analisar itens: {e}")
            else:
                print("Dados da tabela não carregados.")
        else:
            print("Ação cancelada pelo usuário.")


    def fluxo_participantes_irp(self):
        participantes_irp_dialog = ParticipantesIRPDialog(self)
        try:
            if participantes_irp_dialog.exec() == QDialog.DialogCode.Accepted:
                numero_licitacao = participantes_irp_dialog.get_licitacao_number()
                self.table_data = participantes_irp_dialog.table_data

                if self.table_data is not None and not self.table_data.empty:
                    if not hasattr(self, 'driver') or self.driver is None:
                        self.menu_principal_comprasnet()

                    self.divulgacao_compras_click(numero_licitacao)

                    item_inicio = int(participantes_irp_dialog.get_item_inicio())
                    primeiro_item = True

                    for item_index in range(item_inicio - 1, len(self.table_data)):
                        if primeiro_item:
                            # Para o primeiro item, clique em 'Alterar' e verifique o número do item
                            self.clicar_botao_alterar_e_verificar(item_index)
                            primeiro_item = False

                        # Conferir órgãos participantes para o item atual
                        self.conferir_orgaos_participantes(item_index)

                        # Verificar se as quantidades estão corretas
                        self.verificar_quantidades(item_index)
                else:
                    QMessageBox.critical(self, "Erro de Dados", "Dados da tabela não carregados ou tabela vazia.")
            else:
                print("Ação cancelada pelo usuário.")
        except Exception as e:
            print(f"Ocorreu um erro durante o fluxo: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", "Ocorreu um erro durante o processo.")

    def conferir_orgaos_participantes(self, item_index):
        # item_inicio = int(self.table_data.iloc[item_index]['item_num'])
        print(f"Iniciando conferência para o item de índice {item_index}.")

        try:
            if not hasattr(self, 'driver') or self.driver is None:
                self.menu_principal_comprasnet()

            # Tente clicar no #localEntrega e aguarde até que o elemento esteja clicável
            self.esperar_e_clicar("#localEntrega", by=By.CSS_SELECTOR)

            print("Waiting for the table to be present in the DOM...")
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr"))
            )
            print("Table is present in the DOM.")

            # Encontra todas as linhas na tabela
            rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr.odd, tbody tr.even")
            print(f"Found {len(rows)} rows in the table.")

            # Itera pelas linhas e extrai as informações necessárias
            for i, row in enumerate(rows, start=1):
                # Extrai informações
                uasg_code, agency, _, quantity, _ = [td.text for td in row.find_elements(By.TAG_NAME, "td")]
                print(f"Row {i}: UASG Code: {uasg_code}, Agency: {agency}, Quantity: {quantity}")

                # Extrai o atributo onclick e o respectivo valor 'id_codigoLocalEntregaSelecionado'
                onclick_attr = row.find_element(By.CSS_SELECTOR, "td a").get_attribute("onclick")
                id_codigo = onclick_attr.split("'")[1] if "'" in onclick_attr else "N/A"
                print(f"Row {i}: OnClick Attribute: {onclick_attr}, ID Codigo: {id_codigo}")

            # After checking, click on the #id_btnSalvarLocal button
            print("Clicando no botão 'Salvar Local'.")
            self.esperar_e_clicar("#id_btnSalvarLocal", by=By.CSS_SELECTOR)

            # Then, click on the #btnProximoItem button
            print("Clicando no botão 'Próximo Item'.")
            self.esperar_e_clicar("#btnProximoItem", by=By.CSS_SELECTOR)

            print(f"Conferência e ações realizadas com sucesso para o item de índice {item_index}.")

        except Exception as e:
            print(f"Ocorreu um erro durante a conferência do item de índice {item_index}: {e}")
            import traceback
            traceback.print_exc()

    def verificar_quantidades(self, item_index):
        # Garantir que a tabela de participantes foi carregada
        if self.table_data_participantes is not None:
            try:
                # Encontrar todas as linhas na página
                rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr.odd, tbody tr.even")
                for row in rows:
                    uasg_code, _, _, quantity, _ = [td.text for td in row.find_elements(By.TAG_NAME, "td")]

                    # Converter UASG code para a coluna correspondente na tabela de participantes
                    column_name = uasg_code.split(' - ')[0]  # Pega apenas o código numérico

                    if column_name in self.table_data_participantes.columns:
                        # Encontrar a quantidade esperada na tabela de participantes
                        expected_quantity = self.table_data_participantes.iloc[item_index][column_name]
                        
                        # Verificar se a quantidade na página corresponde à quantidade esperada
                        if int(quantity) == expected_quantity:
                            print(f"Quantidade verificada com sucesso para {uasg_code}. Quantidade na página: {quantity}, Quantidade esperada: {expected_quantity}")
                        else:
                            print(f"Inconsistência para {uasg_code}. Quantidade na página: {quantity}, Quantidade esperada: {expected_quantity}")
                    else:
                        print(f"Código UASG {column_name} não encontrado na tabela de participantes.")
            except Exception as e:
                print(f"Ocorreu um erro durante a verificação das quantidades: {e}")
        else:
            print("A tabela de participantes não está carregada.")

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
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, WebDriverException, NoSuchElementException
from modules.custom_selenium.seletores_selenium import *
import time
import traceback
from selenium.webdriver import Firefox, FirefoxOptions
from selenium.webdriver.firefox.service import Service
import re

def esperar_rolar_e_clicar(driver, selectors_with_types, tentativas=3, timeout=5):
    for tentativa_atual in range(tentativas):
        for (by, selector) in selectors_with_types:
            try:
                time.sleep(0.2)  # Pequeno atraso para permitir que o elemento possa ser carregado
                elemento = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )
                elemento.click()  # Tenta clicar no elemento
                print(f"Elemento clicado com sucesso usando {by}: {selector}")
                return
            except (TimeoutException, ElementClickInterceptedException, NoSuchElementException) as e:
                print(f"Tentativa {tentativa_atual + 1} com {by}: {selector} falhou: {e}")
                continue  # Tenta o próximo seletor na lista
        time.sleep(1)  # Pausa antes da próxima tentativa total
    print("Não foi possível clicar em nenhum dos elementos após todas as tentativas.")


def esperar_e_clicar(driver, selector, by=By.CSS_SELECTOR, timeout=20):
    elemento = esperar_elemento_clicavel(driver, selector, by, timeout)
    if elemento:
        elemento.click()
    else:
        print(f"Não foi possível clicar no elemento: {selector}")

def esperar_e_preencher(driver, selector, texto, by=By.CSS_SELECTOR, timeout=20):
    elemento = esperar_elemento_visivel(driver, selector, by, timeout)
    if elemento:
        elemento.clear()
        elemento.send_keys(texto)
    else:
        print(f"Não foi possível preencher o campo de texto: {selector}")

def esperar_elemento_visivel(driver, selector, by=By.CSS_SELECTOR, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, selector))
        )
    except TimeoutException:
        print(f"Timeout: O elemento {selector} não ficou visível após {timeout} segundos.")
        return None

def esperar_elemento_clicavel(driver, selector, by=By.CSS_SELECTOR, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
    except TimeoutException:
        print(f"Timeout: O elemento {selector} não ficou clicável após {timeout} segundos.")
        return None

def esperar_invisibilidade_elemento(driver, selector, by=By.CSS_SELECTOR, timeout=20):
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((by, selector))
        )
    except TimeoutException:
        print(f"O elemento {selector} ainda está visível após {timeout} segundos.")

def aguardar_mudanca_janela(driver, titulo_desejado=None, timeout=20, tentativas=3):
    janelas_iniciais = driver.window_handles
    print("Janelas antes da mudança:", janelas_iniciais)
    for janela in janelas_iniciais:
        driver.switch_to.window(janela)
        print(f"Título da janela inicial: {driver.title}")

    for tentativa in range(tentativas):
        janelas_atual = driver.window_handles
        print("Verificando janelas disponíveis:", janelas_atual)

        for janela in janelas_atual:
            driver.switch_to.window(janela)
            if titulo_desejado and driver.title == titulo_desejado:
                print(f"Mudou para a janela desejada: {driver.title}")
                return
        print(f"Tentativa {tentativa + 1} de encontrar a janela falhou. Tentando novamente...")
        time.sleep(1)  # Pequena pausa antes da próxima tentativa

    print("A janela com o título '{}' não foi encontrada após todas as tentativas.".format(titulo_desejado))


def hover_sobre_elemento(driver, selector, by=By.CSS_SELECTOR, timeout=20):
    try:
        elemento = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, selector))
        )
        ActionChains(driver).move_to_element(elemento).perform()
    except TimeoutException:
        print(f"Não foi possível passar o mouse sobre o elemento com o seletor {selector}.")

def menu_principal_comprasnet(driver, username, password, settings_file):
    try:
        if not driver:
            driver = webdriver.Firefox()
            print("Novo driver inicializado.")
        else:
            print("Reutilizando o driver existente.")
            driver.get("http://www.comprasnet.gov.br/seguro/loginPortal.asp")

        driver.get("http://www.comprasnet.gov.br/seguro/loginPortal.asp")
        
        # Agora passando driver como primeiro argumento para as funções esperar_e_clicar e esperar_e_preencher
        esperar_e_clicar(driver, "button.governo")
        esperar_e_preencher(driver, USER_FIELD_SELECTOR, username)
        esperar_e_preencher(driver, PASSWORD_FIELD_SELECTOR, password)
        
        esperar_e_clicar(driver, LOGIN_BUTTON_SELECTOR)
        esperar_invisibilidade_elemento(driver, OVERLAY_SELECTOR)
        time.sleep(0.5)

        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ui-blockui.ui-widget-overlay.ui-blockui-document"))
        )

        try:
            esperar_e_clicar(driver, PAGINATION_ELEMENT_XPATH, by=By.XPATH)
        except ElementClickInterceptedException:
            time.sleep(1)
            esperar_e_clicar(driver, PAGINATION_ELEMENT_XPATH, by=By.XPATH)
        
        time.sleep(0.3)
        esperar_e_clicar(driver, OPTION_XPATH, by=By.XPATH)
    except Exception as e:
        print(f"Erro ao inicializar o driver ou ao acessar o portal: {e}")
        traceback.print_exc()
        raise  # Relança a exceção para notificar que um erro ocorreu

def aguardar_e_mudar_para_popup(driver):
    time.sleep(2)  # Pequena pausa
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "Catálogo Compras.gov.br" in driver.title:
            print("Foco mudado para a janela do pop-up.")
            break

def create_driver(webdriver_path):
    options = FirefoxOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    
    service = Service(executable_path=webdriver_path)
    driver =  webdriver.Firefox()
    driver.maximize_window()  # Maximiza a janela do navegador
    return driver
    
def abrir_comprasnet(driver, username, password):
    driver.get("http://www.comprasnet.gov.br/seguro/loginPortal.asp")
    esperar_e_clicar(driver, "button.governo")

    esperar_e_preencher(driver, USER_FIELD_SELECTOR, username)
    esperar_e_preencher(driver, PASSWORD_FIELD_SELECTOR, password)
    esperar_e_clicar(driver, LOGIN_BUTTON_SELECTOR)

    # Aguardar até que o overlay desapareça
    esperar_invisibilidade_elemento(driver, OVERLAY_SELECTOR)
    time.sleep(0.5)  # Necessário para carregar a página
    timeout = 20
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ui-blockui.ui-widget-overlay.ui-blockui-document"))
        )
    except TimeoutException:
        print("O overlay não desapareceu após {} segundos.".format(timeout))

def selecionar_analise_irp(driver):
    try:
        esperar_e_clicar(driver, PAGINATION_ELEMENT_XPATH, by=By.XPATH)
    except ElementClickInterceptedException:
        time.sleep(1)
        esperar_e_clicar(driver, PAGINATION_ELEMENT_XPATH, by=By.XPATH)

    time.sleep(0.3)
    esperar_e_clicar(driver, ABRIR_JANELA_IRP)

    aguardar_mudanca_janela(driver, titulo_desejado="SIASGnet IRP")

    esperar_e_clicar(driver, ANALISE_IRP_SELECTOR)

def selecionar_irp(driver, irp_number):
    # Verificar se o irp_number já contém o separador '/'
    if '/' not in irp_number:
        # Supõe que os últimos 4 dígitos são o ano
        number_part = irp_number[:-4]
        year_part = irp_number[-4:]
        irp_number = f"{number_part}/{year_part}"
    
    # Dividir o irp_number em número e ano
    number_part, year_part = irp_number.split('/')
    formatted_number_part = number_part.zfill(5)  # Adiciona zeros à esquerda para completar 5 dígitos
    search_pattern = re.compile(r"(\d{{6}}) - {}/{}".format(formatted_number_part, year_part))  # Escape the curly braces

    # Esperar e localizar o seletor de dropdown
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, BOX_SELETOR)))
    select_element = driver.find_element(By.CSS_SELECTOR, BOX_SELETOR)
    select_box = Select(select_element)

    print(f"Formato ajustado de IRP: {irp_number}")
    print("Opções disponíveis no dropdown:")
    found = False
    for option in select_box.options:
        print(f"Option text: {option.text}, Value: {option.get_attribute('value')}")
        # Usar regex para buscar padrão na opção
        if search_pattern.search(option.text):
            select_box.select_by_visible_text(option.text)
            found = True
            break

    if not found:
        print("Não foi possível encontrar a opção correta para o IRP fornecido.")

# def analisar_itens(driver, item_inicio, table_data):
#     linha_inicio = table_data.index[table_data['item_num'] == item_inicio].tolist()

#     if not linha_inicio:
#         print(f"Item de início {item_inicio} não encontrado na tabela.")
#         return

#     linha_inicio = linha_inicio[0]
#     total_itens = len(table_data)
#     pagina_atual = (linha_inicio // 20) + 1
#     ultima_pagina = False

#     while not ultima_pagina:
#         # Espera a tabela ser visível para garantir que a página correta foi carregada
#         WebDriverWait(driver, 10).until(
#             EC.visibility_of_element_located((By.ID, "itemAnalise")),
#             message=f"Esperando a tabela de itens ser visível na página {pagina_atual}."
#         )

#         total_rows = len(driver.find_elements(By.CSS_SELECTOR, "#itemAnalise tbody tr"))
#         for index_local in range(1, total_rows + 1):
#             row_class = 'odd' if index_local % 2 != 0 else 'even'
#             analisar_button_selector = f"tr.{row_class}:nth-child({index_local}) > td:nth-child(9) > a"
#             try:
#                 WebDriverWait(driver, 10).until(
#                     EC.element_to_be_clickable((By.CSS_SELECTOR, analisar_button_selector)),
#                     message=f"Esperando o botão de análise para o item {index_local} na página {pagina_atual}."
#                 )
#                 driver.find_element(By.CSS_SELECTOR, analisar_button_selector).click()

#                 # Espera até que a janela de análise esteja visível
#                 WebDriverWait(driver, 10).until(
#                     EC.element_to_be_clickable((By.CSS_SELECTOR, "#analisarirp")),
#                     message="Esperando botão de retorno após análise."
#                 )
#                 driver.find_element(By.CSS_SELECTOR, "#analisarirp").click()
#                 time.sleep(0.2)
#                 # Aguarda a tabela ser visível novamente após retornar
#                 WebDriverWait(driver, 10).until(
#                     EC.visibility_of_element_located((By.ID, "itemAnalise"))
#                 )
#                 time.sleep(0.2)
#             except TimeoutException:
#                 print(f"Timeout: O botão de análise para o item {index_local} na página {pagina_atual} não está clicável.")
#                 break

#             pagina_atual, ultima_pagina = verificar_navegacao_pagina(driver, index_local, total_rows, pagina_atual)
#             if ultima_pagina:
#                 break

#     print(f"Todos os itens a partir do item {item_inicio} foram analisados.")

def analisar_itens(driver, item_inicio, table_data):
    total_itens = len(table_data)
    item_atual = item_inicio

    while item_atual <= total_itens:
        pagina_atual = (item_atual - 1) // 20 + 1
        navegar_para_pagina(driver, pagina_atual)  # Assegura que está na página correta

        index_na_pagina = ((item_atual - 1) % 20) + 1
        row_class = 'odd' if index_na_pagina % 2 != 0 else 'even'
        analisar_button_selector = f"tr.{row_class}:nth-child({index_na_pagina}) > td:nth-child(9) > a"

        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, analisar_button_selector)),
                message=f"Esperando o botão de análise para o item {item_atual} na página {pagina_atual}."
            )
            button = driver.find_element(By.CSS_SELECTOR, analisar_button_selector)
            button.click()  # Clique no botão de análise

            marcar_checkboxes_para_brasilia(driver)
            time.sleep(2)
            marcar_checkboxes_para_outros(driver)

            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#analisarirp")),
                message="Esperando botão de retorno após análise."
            )
            analisarirp_button = driver.find_element(By.CSS_SELECTOR, "#analisarirp")
            analisarirp_button.click()

            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "itemAnalise")),
                message="Esperando a tabela de itens ser visível após retorno."
            )
        except TimeoutException as e:
            print(f"Erro: {e}")
            break  # Sai do loop em caso de erro

        item_atual += 1  # Avança para o próximo item

    print(f"Todos os itens a partir do item {item_inicio} foram analisados.")

def marcar_checkboxes_para_brasilia(driver):
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#itemManifestacao")),
        message="Esperando a tabela de manifestações estar visível."
    )
    
    linhas = driver.find_elements(By.CSS_SELECTOR, "#itemManifestacao > tbody > tr")
    algum_checkbox_marcado = False

    for linha in linhas:
        try:
            coluna_endereco = linha.find_element(By.CSS_SELECTOR, "td:nth-child(5) > table > tbody > tr > td:nth-child(1)").text.strip()
            coluna_status = linha.find_element(By.CSS_SELECTOR, "td.colunaCentralizada:last-child").text.strip()
        except NoSuchElementException:
            continue  # Se não encontrar os elementos, pula para a próxima linha

        if 'BRASÍLIA/DF' in coluna_endereco and coluna_status == "Manifestado":
            checkbox = linha.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
            if not checkbox.is_selected():
                checkbox.click()
                algum_checkbox_marcado = True

    if algum_checkbox_marcado:
        botao_aceitar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#aceitar")),
            message="Esperando botão Aceitar ficar disponível."
        )
        botao_aceitar.click()
        print("Botão Aceitar clicado após marcar todos os checkboxes necessários.")

        # Trata o primeiro popup com o botão #btSim
        if listar_titulos_janelas(driver, titulo_desejado="SIASGnet IRP", elemento_distintivo="#btSim"):
            print("Popup inicial tratado com sucesso.")
            # Trata o segundo popup com o botão #btOk
            if aguardar_e_confirmar_popup(driver, elemento_distintivo="#btOk"):
                print("Popup de confirmação de brasília tratado com sucesso.")
            else:
                print("Falha ao tratar o popup de confirmação #btOk.")
        else:
            print("Falha ao tratar o popup inicial #btSim.")

def marcar_checkboxes_para_outros(driver):
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#itemManifestacao")),
        message="Esperando a tabela de manifestações estar visível."
    )
    
    linhas = driver.find_elements(By.CSS_SELECTOR, "#itemManifestacao > tbody > tr")
    algum_checkbox_marcado = False

    for linha in linhas:
        try:
            coluna_endereco = linha.find_element(By.CSS_SELECTOR, "td:nth-child(5) > table > tbody > tr > td:nth-child(1)").text.strip()
            coluna_status = linha.find_element(By.CSS_SELECTOR, "td.colunaCentralizada:last-child").text.strip()
            checkbox = linha.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
        except NoSuchElementException:
            continue

        # Desmarcar o checkbox se estiver associado a 'BRASÍLIA/DF'
        if 'BRASÍLIA/DF' in coluna_endereco:
            if checkbox.is_selected():
                checkbox.click()
                print(f"Checkbox desmarcado para BRASÍLIA/DF em status {coluna_status}.")

        # Marcar o checkbox para outras localidades se o status é "Manifestado" e não é BRASÍLIA/DF
        elif coluna_status == "Manifestado" and 'BRASÍLIA/DF' not in coluna_endereco:
            if not checkbox.is_selected():
                checkbox.click()
                algum_checkbox_marcado = True
                print(f"Checkbox marcado para localidade {coluna_endereco} com status Manifestado.")

    if algum_checkbox_marcado:
        botao_recusar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#recusar")),
            message="Esperando botão Recusar ficar disponível."
        )
        botao_recusar.click()
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "textarea[name='justificativa']")),
            message="Esperando o campo de justificativa estar visível."
        )
        campo_justificativa = driver.find_element(By.CSS_SELECTOR, "textarea[name='justificativa']")
        campo_justificativa.send_keys("Localidade geográfica difere da do órgão gerenciador.")
        print("Justificativa inserida e ação de recusa executada.")

        # Confirma a ação de recusa
        botao_confirmar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#confirmar")),
            message="Esperando botão Confirmar ficar disponível."
        )
        botao_confirmar.click()
        print("Botão Confirmar clicado, confirmando a ação.")
        if aguardar_e_confirmar_popup(driver, elemento_distintivo="#btOk"):
            print("Popup de confirmação tratado com sucesso.")
    else:
        print("Nenhum item fora de 'BRASÍLIA/DF' com status 'Manifestado' encontrado. Continuando com o fluxo atual.")

def navegar_para_pagina(driver, pagina_desejada):
    if pagina_desejada == 1:
        return True, "Já na página 1"

    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".pagelinks > a")),
            message=f"Esperando os seletores de paginação estarem visíveis para navegar para a página {pagina_desejada}."
        )
        
        if pagina_desejada <= 5:
            link_index = 2 + pagina_desejada  # Página 2 é o quarto filho (3 + 1), página 3 é o quinto filho (4 + 1), etc.
            pagina_link = driver.find_element(By.CSS_SELECTOR, f".pagelinks > a:nth-child({link_index})")
        else:
            # Para páginas além da quinta, considera que os links para páginas e o próximo botão se alternam
            link_index = 2 + pagina_desejada
            try:
                pagina_link = driver.find_element(By.CSS_SELECTOR, f".pagelinks > a:nth-child({link_index})")
            except NoSuchElementException:
                pagina_link = driver.find_element(By.CSS_SELECTOR, f".pagelinks > a:nth-child({link_index}) > img:nth-child(1)")
        
        if pagina_link:
            pagina_link.click()
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "itemAnalise")),
                message=f"Esperando a tabela de itens ser visível na página {pagina_desejada}."
            )
            return True, "Navegação bem-sucedida"
        else:
            return False, f"Link de paginação para a página {pagina_desejada} não encontrado"
    except TimeoutException as e:
        return False, f"Erro durante a navegação: {e}"
    except NoSuchElementException:
        return False, "Seletores de paginação não encontrados"


# def navegar_para_pagina(driver, pagina_desejada):
#     if pagina_desejada == 1:
#         # Já iniciado na página 1, então não precisa de ação
#         return True, "Já na página 1"
#     try:
#         # Espera até que os seletores de paginação estejam visíveis ou até que um tempo limite seja atingido
#         WebDriverWait(driver, 10).until(
#             EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".pagelinks > a")),
#             message=f"Esperando os seletores de paginação estarem visíveis para navegar para a página {pagina_desejada}."
#         )
#         # Localiza e clica no link correto para a página desejada
#         # Calcula o índice do elemento a baseado na página desejada, assumindo que a página 2 é o quarto filho, página 3 o quinto, e assim por diante
#         link_index = 2 + pagina_desejada
#         pagina_link = driver.find_element(By.CSS_SELECTOR, f".pagelinks > a:nth-child({link_index})")
#         if pagina_link:
#             pagina_link.click()
#             WebDriverWait(driver, 10).until(
#                 EC.visibility_of_element_located((By.ID, "itemAnalise")),
#                 message=f"Esperando a tabela de itens ser visível na página {pagina_desejada}."
#             )
#             return True, "Navegação bem-sucedida"
#         else:
#             return False, f"Link de paginação para a página {pagina_desejada} não encontrado"
#     except TimeoutException as e:
#         return False, f"Erro durante a navegação: {e}"
#     except NoSuchElementException:
#         return False, "Seletores de paginação não encontrados"

def verificar_navegacao_pagina(driver, index_local, total_rows, pagina_atual):
    if index_local % 20 == 0 and index_local != total_rows:
        proxima_pagina = pagina_atual + 1
        links_paginacao = determinar_seletores_paginacao(driver, proxima_pagina)
        if links_paginacao:
            if executar_script_clicar(driver, links_paginacao[0]):
                pagina_atual += 1
                print(f"Indo para a página {pagina_atual}.")
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "itemAnalise")),
                    message=f"Esperando a tabela de itens ser visível na página {pagina_atual}."
                )
            else:
                print("Nenhuma próxima página encontrada ou clique falhou.")
                return pagina_atual, True  # Retorna a nova página e o sinalizador de última página
        else:
            print("Nenhum link de paginação encontrado.")
    return pagina_atual, False  # Continua na página atual sem ser a última

def determinar_seletores_paginacao(driver, proxima_pagina):
    # Busca o link de paginação que leva à próxima página
    links = driver.find_elements(By.CSS_SELECTOR, ".pagelinks > a")
    for link in links:
        if link.get_attribute("title") == f"Ir para página {proxima_pagina}":
            return [link]
    return []

def executar_script_clicar(driver, elemento):
    try:
        driver.execute_script("arguments[0].click();", elemento)
        return True
    except Exception as e:
        print(f"Erro ao clicar no elemento usando JavaScript: {e}")
        return False
    
def listar_titulos_janelas(driver, titulo_desejado=None, elemento_distintivo="#btSim", timeout=20):
    janela_controle_principal = driver.current_window_handle
    janelas_iniciais = driver.window_handles
    print("Janelas antes da mudança:", janelas_iniciais)

    for tentativa in range(timeout):
        janelas_atual = driver.window_handles
        print("Verificando janelas disponíveis:", janelas_atual)

        for janela in janelas_atual:
            driver.switch_to.window(janela)
            if titulo_desejado and driver.title == titulo_desejado:
                try:
                    if driver.find_element(By.CSS_SELECTOR, elemento_distintivo):
                        print(f"Mudou para a janela desejada: {driver.title}")
                        botao_sim = driver.find_element(By.CSS_SELECTOR, elemento_distintivo)
                        botao_sim.click()
                        print("Botão #btSim clicado.")

                        driver.switch_to.window(janela_controle_principal)
                        print("Retorno à janela principal após operações.")
                        return True
                except NoSuchElementException:
                    print("Elemento distintivo não encontrado nesta janela.")
                    continue
                except TimeoutException:
                    print("Timeout esperando por nova janela ou popup.")
        print(f"Tentativa {tentativa + 1} de encontrar a janela falhou. Tentando novamente...")
        time.sleep(1)

    print(f"A janela com o título '{titulo_desejado}' não foi encontrada após todas as tentativas.")
    return False

def aguardar_e_confirmar_popup(driver, elemento_distintivo="#btOk", timeout=20):
    janela_principal = driver.current_window_handle  # Guarda a referência da janela principal antes de qualquer mudança
    print("Janela principal antes de qualquer operação:", janela_principal)
    
    janelas_iniciais = driver.window_handles
    print("Janelas abertas antes da mudança:", janelas_iniciais)

    for tentativa in range(timeout):
        janelas_atual = driver.window_handles
        print("Verificando janelas disponíveis:", janelas_atual)

        # Identificar se novas janelas foram abertas ou se já estão disponíveis
        for janela in janelas_atual:
            driver.switch_to.window(janela)
            print(f"Atualmente na janela: {driver.title}")
            if driver.find_elements(By.CSS_SELECTOR, elemento_distintivo):
                try:
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, elemento_distintivo)),
                        message="Esperando botão de confirmação #btOk estar visível."
                    )
                    botao_ok = driver.find_element(By.CSS_SELECTOR, elemento_distintivo)
                    botao_ok.click()
                    print("Botão #btOk clicado para confirmar.")
                    
                    # Após clicar em #btOk, garantir que o driver retorne à janela principal
                    driver.switch_to.window(janela_principal)
                    print("Retorno à janela principal após clicar em #btOk.")
                    
                    # Verificar se o elemento #analisarirp está disponível para confirmar que está na janela correta
                    if driver.find_elements(By.CSS_SELECTOR, "#analisarirp"):
                        print("Elemento #analisarirp encontrado, confirmação de estar na janela correta.")
                    return True
                except NoSuchElementException:
                    print("Elemento distintivo não encontrado nesta janela.")
                except TimeoutException:
                    print("Timeout ao tentar clicar no botão #btOk.")
            else:
                print("Botão #btOk não encontrado nesta janela.")

        print(f"Tentativa {tentativa + 1} de encontrar o popup de confirmação falhou. Tentando novamente...")
        time.sleep(1)

    print("Não foi possível encontrar o popup de confirmação após todas as tentativas.")
    return False

def aguardar_e_confirmar_popup_recusa(driver, elemento_distintivo="#btOk", timeout=20):
    janela_principal = driver.current_window_handle  # Guarda a referência da janela principal antes de qualquer mudança
    print("Janela principal antes de qualquer operação:", janela_principal)
    
    janelas_iniciais = driver.window_handles
    print("Janelas abertas antes da mudança:", janelas_iniciais)

    for tentativa in range(timeout):
        janelas_atual = driver.window_handles
        print("Verificando janelas disponíveis:", janelas_atual)

        # Identificar se novas janelas foram abertas ou se já estão disponíveis
        for janela in janelas_atual:
            driver.switch_to.window(janela)
            print(f"Atualmente na janela: {driver.title}")
            if driver.find_elements(By.CSS_SELECTOR, elemento_distintivo):
                try:
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, elemento_distintivo)),
                        message="Esperando botão de confirmação #btOk estar visível."
                    )
                    botao_ok = driver.find_element(By.CSS_SELECTOR, elemento_distintivo)
                    botao_ok.click()
                    print("Botão #btOk clicado para confirmar.")
                    
                    # Após clicar em #btOk, garantir que o driver retorne à janela principal
                    driver.switch_to.window(janela_principal)
                    print("Retorno à janela principal após clicar em #btOk.")
                    
                    # Verificar se o elemento #analisarirp está disponível para confirmar que está na janela correta
                    if driver.find_elements(By.CSS_SELECTOR, "#analisarirp"):
                        print("Elemento #analisarirp encontrado, confirmação de estar na janela correta.")
                    return True
                except NoSuchElementException:
                    print("Elemento distintivo não encontrado nesta janela.")
                except TimeoutException:
                    print("Timeout ao tentar clicar no botão #btOk.")
            else:
                print("Botão #btOk não encontrado nesta janela.")

        print(f"Tentativa {tentativa + 1} de encontrar o popup de confirmação falhou. Tentando novamente...")
        time.sleep(1)

    print("Não foi possível encontrar o popup de confirmação após todas as tentativas.")
    return False

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, WebDriverException, NoSuchElementException
from custom_selenium.seletores_selenium import *
import time
import traceback

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

def aguardar_mudanca_janela(driver, timeout=20):
    janelas_iniciais = driver.window_handles
    print("Janelas antes da mudança:", janelas_iniciais)

    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.window_handles) != len(janelas_iniciais)
        )
        janelas_novas = driver.window_handles
        print("Janelas após a mudança:", janelas_novas)

        # Muda para a nova janela
        for janela in janelas_novas:
            if janela not in janelas_iniciais:
                driver.switch_to.window(janela)
                print("Mudou para nova janela:", driver.title)
                break
    except TimeoutException:
        print("A nova janela não foi detectada no tempo esperado.")

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

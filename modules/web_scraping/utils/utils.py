import time
from PyQt6.QtWidgets import QMessageBox

def aguardar_mudanca_janela(driver, titulo_desejado=None, timeout=20, tentativas=3):
    janelas_iniciais = driver.window_handles
    print("Janelas iniciais:", janelas_iniciais)

    for tentativa in range(tentativas):
        time.sleep(1)  # Pausa antes de verificar novamente
        janelas_atual = driver.window_handles
        print(f"Tentativa {tentativa + 1}: Janelas encontradas:", janelas_atual)

        for janela in janelas_atual:
            driver.switch_to.window(janela)
            print(f"Título da janela atual: {driver.title}")
            if titulo_desejado and driver.title == titulo_desejado:
                print(f"Mudou para a janela desejada: {driver.title}")
                return

        print(f"Tentativa {tentativa + 1} falhou. Tentando novamente...")

    QMessageBox.warning(None, "Aviso", "Não foi possível encontrar a janela com o título desejado.")

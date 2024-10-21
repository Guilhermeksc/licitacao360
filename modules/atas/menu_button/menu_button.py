from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import requests
import os
import time
import webbrowser

def get_icon_pair(icons, icon_key):
    """
    Obtém os ícones padrão e selecionado com base na chave do ícone fornecida.
    """
    icon_default = icons.get(f"{icon_key}_azul")
    icon_selected = icons.get(icon_key)
    if not icon_default or not icon_selected:
        raise ValueError(f"Os ícones para '{icon_key}' não foram encontrados.")
    return icon_default, icon_selected

def configure_button_style(button):
    """
    Configura o estilo do botão.
    """
    button.setIconSize(QSize(40, 40))
    button.setStyleSheet("""
        QPushButton {
            border: none;
            background-color: transparent;
        }
        QPushButton:hover {
            background-color: rgba(0, 0, 0, 0);
        }
        QToolTip {
            background-color: #13141F;
            color: white;
            border: none;
            font-size: 14px;
        }
    """)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setFixedSize(50, 50)

class ButtonManager:
    """
    Classe para gerenciar o estado dos botões do menu.
    """
    def __init__(self):
        self.selected_button = None  # Armazena o botão atualmente selecionado

    def update_button_icon_on_hover(self, event, button):
        """
        Atualiza o ícone do botão com base no evento de entrada/saída do mouse.
        """
        if event.type() == QEvent.Type.Enter:
            if self.selected_button != button:
                button.setIcon(button.icon_selected)  # Altera para o ícone "_azul" ao passar o mouse
        elif event.type() == QEvent.Type.Leave:
            if self.selected_button != button:
                button.setIcon(button.icon_default)  # Retorna ao ícone padrão ao sair, se não for o selecionado

    def select_button(self, button):
        """
        Atualiza o botão selecionado e altera os ícones de todos os botões conforme o estado.
        """
        # Desseleciona o botão anteriormente selecionado
        if self.selected_button:
            self.selected_button.setIcon(self.selected_button.icon_default)

        # Seleciona o novo botão e mantém o ícone "_azul"
        self.selected_button = button
        button.setIcon(button.icon_selected)

# Instancia o gerenciador de botões
button_manager = ButtonManager()

def create_menu_button(icons, icon_key, tooltip_text):
    """
    Função principal para criar o botão do menu.
    """
    # Obtém os ícones
    icon_default, icon_selected = get_icon_pair(icons, icon_key)

    # Cria o botão e configura os ícones e estilo
    button = QPushButton()
    button.setIcon(icon_default)  # Usa o ícone padrão inicialmente
    configure_button_style(button)

    # Configura o tooltip
    button.setToolTip(tooltip_text)
    button.setToolTipDuration(0)  # Faz o tooltip aparecer instantaneamente

    # Armazena os ícones no próprio botão (opcional, se necessário para outros usos)
    button.icon_default = icon_default
    button.icon_selected = icon_selected

    # Conecta os eventos de hover para atualizar o ícone
    button.enterEvent = lambda event, btn=button: button_manager.update_button_icon_on_hover(event, btn)
    button.leaveEvent = lambda event, btn=button: button_manager.update_button_icon_on_hover(event, btn)

    return button


def update_button_icon_on_hover(event, button):
    """
    Atualiza o ícone do botão com base no evento de entrada/saída do mouse.
    """
    if event.type() == QEvent.Type.Enter:
        button.setIcon(button.icon_selected)  # Altera para o ícone "_azul" ao entrar
    elif event.type() == QEvent.Type.Leave:
        button.setIcon(button.icon_default)  # Volta ao ícone padrão ao sair

def visualizar_ata(df_registro_selecionado, parent):
    """
    Função para visualizar a ata selecionada na tabela.
    """
    try:
        if df_registro_selecionado.empty:
            QMessageBox.warning(parent, "Erro", "Nenhum registro foi encontrado ou ocorreu um erro ao carregar os dados.")
            return

        # Obter os valores necessários do DataFrame
        cnpj = df_registro_selecionado.get("CNPJ", [None])[0]
        ano = df_registro_selecionado.get("sequencial_ano_pncp", [None])[0]
        sequencial = df_registro_selecionado.get("sequencial", [None])[0]
        numero_ata = df_registro_selecionado.get("sequencial_ata_pncp", [None])[0]

        if not all([cnpj, ano, sequencial, numero_ata]):
            QMessageBox.warning(parent, "Erro", "Valores necessários não estão disponíveis para a consulta.")
            return

        # Formar a URL da API
        url = f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/atas/{numero_ata}/arquivos"

        # Fazer a requisição HTTP
        response = requests.get(url)
        if response.status_code != 200:
            QMessageBox.warning(parent, "Erro", f"Erro ao acessar a API: {response.status_code}")
            return

        # Processar a resposta JSON
        arquivos = response.json()
        if not arquivos:
            QMessageBox.warning(parent, "Erro", "Nenhum arquivo encontrado.")
            return

        # Obter a URL do primeiro arquivo
        arquivo_url = arquivos[0].get("url")
        if not arquivo_url:
            QMessageBox.warning(parent, "Erro", "URL do arquivo não disponível.")
            return

        # Tentar baixar o arquivo PDF até 10 vezes
        for tentativa in range(10):
            try:
                arquivo_response = requests.get(arquivo_url)
                if arquivo_response.status_code == 200:
                    # Salvar o arquivo PDF
                    caminho_pdf = os.path.join(os.getcwd(), f"{sequencial}-{numero_ata}-{ano}.pdf")
                    with open(caminho_pdf, 'wb') as f:
                        f.write(arquivo_response.content)

                    # Abrir o arquivo PDF
                    webbrowser.open_new(caminho_pdf)
                    QMessageBox.information(parent, "Sucesso", "Arquivo baixado e aberto com sucesso.")
                    return
                else:
                    print(f"Tentativa {tentativa + 1} falhou, status: {arquivo_response.status_code}")
            except Exception as e:
                print(f"Tentativa {tentativa + 1} falhou, erro: {e}")
            # Aguardar 2 segundos antes de tentar novamente
            time.sleep(2)

        # Caso falhe após 10 tentativas
        QMessageBox.warning(parent, "Erro", "Falha ao baixar o arquivo após 10 tentativas.")

    except Exception as e:
        QMessageBox.critical(parent, "Erro", f"Ocorreu um erro ao tentar visualizar a ata: {str(e)}")


def create_action(parent, text, callback):
    """
    Cria uma ação de menu com o texto especificado e o callback associado.
    """
    action = QAction(text, parent)
    action.triggered.connect(callback)
    return action

def map_actions_to_callbacks(parent):
    """
    Mapeia os textos das ações para os respectivos callbacks.
    """
    return [
        ("Visualizar Ata", visualizar_ata),
        ("Relação de Itens", relacao_itens),
        ("Empenhos", empenhos)
    ]

def create_menu_actions(parent):
    """
    Cria uma lista de ações do menu com base nos textos e callbacks fornecidos.
    """
    action_mappings = map_actions_to_callbacks(parent)
    return [create_action(parent, text, callback) for text, callback in action_mappings]

def relacao_itens(table_view, proxy_model, database_path, parent):
    # Implementação da função relacao_itens utilizando os dados carregados
    print("Relação de itens:")
    # Adicione a lógica aqui

def empenhos(table_view, proxy_model, database_path, parent):
    # Método para empenhos
    print("Empenhos selecionado")
    # Adicione a lógica aqui
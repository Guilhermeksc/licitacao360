# config.py

# Seletores CSS para elementos da página de login
# LOGIN_BUTTON_SELECTOR = ".is-primary"
# USERNAME_FIELD_SELECTOR = "#username"
# PASSWORD_FIELD_SELECTOR = "#password"

# Constantes para seletores
LOGIN_BUTTON_SELECTOR = ".is-primary"
USER_FIELD_SELECTOR = "#txtLogin"
PASSWORD_FIELD_SELECTOR = "#txtSenha"
GOVERNO_BUTTON_SELECTOR = "button.governo"
OVERLAY_SELECTOR = "div.ui-blockui.ui-widget-overlay.ui-blockui-document"
# PAGINATION_ELEMENT_XPATH = "/html/body/app-root/div/app-area-governo/div/app-hub-acesso-sistemas/div[2]/div/div/p-dataview/div/p-paginator/div/span"

PAGINATION_ELEMENT_XPATH = "/html/body/app-root/div/app-area-governo/div/app-hub-acesso-sistemas/div[2]/div/div/p-dataview/div/p-paginator/div/span/a[2]"

OPTION_XPATH = "/html/body/app-root/div/app-area-governo/div/app-hub-acesso-sistemas/div[2]/div/div/p-dataview/div/p-paginator/div/span/a[2]"
ABRIR_JANELA_IRP = "div.col-xl-2:nth-child(2) > app-redirect-sistemas:nth-child(1) > span:nth-child(1) > span:nth-child(1) > div:nth-child(1) > p:nth-child(1) > img:nth-child(1)"
ABRIR_JANELA_PESQUISA_PRECOS = "div.col-xl-2:nth-child(3) > app-redirect-sistemas:nth-child(1) > span:nth-child(1) > span:nth-child(1) > div:nth-child(1) > p:nth-child(1) > img:nth-child(1)"

MARKER_SELECTOR = ".conteudoSemAbas > tbody:nth-child(1) > tr:nth-child(4) > td:nth-child(1) > input:nth-child(1)"
CONFIRM_BUTTON_SELECTOR = "#confirmar"
HOVER_ELEMENT_SELECTOR = "#mi_0_5 > div:nth-child(1)"
MENU_OPTION_SELECTOR = "#mi_0_7 > div:nth-child(1)"
SPECIFIC_ELEMENT_SELECTOR = "table.dados:nth-child(1) > tbody:nth-child(1) > tr:nth-child(3) > td:nth-child(1) > input:nth-child(1)"

INPUT_FIELD_SELECTOR = "input.field"
CONSULT_BUTTON_SELECTOR = "#btnConsultar"
RESULT_LINK_SELECTOR = ".odd > td:nth-child(7) > a:nth-child(1)"
TD_ITEM_SELECTOR = "#td_Item"
NEW_ITEM_BUTTON_SELECTOR = "#btnNovoItem"
# XPath atualizado para apontar diretamente para o campo de entrada
CAMPO_DIGITAR_CATMAT_CSS = "input.ng-tns-c238-1.p-autocomplete-input"  # Seletor CSS mais específico
CAMPO_ADICIONAR_CATMAT = "button.ng-star-inserted"


#Seletores CSS para elementos da página de pesquisa de preços
CAMPO_PESQUISA_PRECOS = "//*[@id='termo-pesquisa']" 
LUPA_PESQUISA_PRECOS = ".fa-search"


SELECIONAR_ITEM_CSS = ".secao-lateral > a:nth-child(2) > li:nth-child(1)"
TITULO_ADICIONAR_ITEM_XPATH = "/html/body/app-root/main/app-manter-cotacao-basica/div/div/div[3]/div/app-manter-itens/div[3]/div[1]/h3"
ADICIONAR_ITEM_PP_CSS = ".is-primary"

ELEMENTO_VOLTAR_INDICATIVO_CARREGAMENTO = "div.col-md-4:nth-child(2) > button:nth-child(1)"

#Divulgação de Compras
ABRIR_DIVULGACAO_COMPRAS = "div.col-xl-2:nth-child(4) > app-redirect-sistemas:nth-child(1) > span:nth-child(1) > span:nth-child(1) > div:nth-child(1) > p:nth-child(2)"
MENU_LICITACAO = "#oCMenu_menuLicitacao"
ALTERAR_LICITACAO = "#oCMenu_menuAlterarExcluirLicitacao"
INPUT_LICITACAO_NUMERO = "#corpo > form:nth-child(5) > table:nth-child(11) > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(1) > input:nth-child(1)"
PESQUISAR_LICITACAO_BOTAO = "#pesquisar"
SELECIONAR_LICITACAO_ESCOLHIDA = "td.centralizado:nth-child(7)"
SELECIONAR_ITENS_LICITACAO = "#itens"
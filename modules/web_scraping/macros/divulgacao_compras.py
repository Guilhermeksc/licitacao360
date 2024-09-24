from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from PyQt6.QtWidgets import QMessageBox
from modules.web_scraping.utils.utils import aguardar_mudanca_janela
import pandas as pd
import os

class DivulgacaoComprasMacro:
    def __init__(self, driver):
        self.driver = driver

    def executar(self):
        try:
            self._clicar_pagina2_comprasnet()
            self._clicar_divulgacao_de_compras()
            self._alternar_para_janela_siasgnet()
            self._navegar_menu_licitacao()
            self._exibir_mensagem_selecao_licitacao()
            self._aguardar_usuario_clicar_visualizar()
            self._aguardar_elemento_itens()
            self._iniciar_scraping_itens()

        except TimeoutException as e:
            QMessageBox.critical(None, "Erro", f"Erro durante a automação: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erro inesperado", f"Ocorreu um erro inesperado: {e}")

    def _clicar_pagina2_comprasnet(self):
        try:
            # Primeiro, localize o componente app-hub-acesso-sistemas
            app_hub_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "app-hub-acesso-sistemas"))
            )

            # Dentro deste componente, localize o botão da página 2 no paginador
            pagina2_botao = WebDriverWait(app_hub_element, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.p-paginator.p-component.ng-star-inserted button.p-ripple.p-element.p-paginator-page.p-paginator-element.p-link.ng-star-inserted:nth-child(2)"))
            )

            # Clica no botão da página 2
            pagina2_botao.click()

            # Aguardar até que a nova página seja carregada
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "app-hub-acesso-sistemas p-dataview.p-element"))  # Aguarda a atualização da tabela
            )

            print("Página 2 clicada com sucesso.")
        except TimeoutException:
            print("Não foi possível encontrar o botão da página 2 no tempo esperado.")
            QMessageBox.critical(None, "Erro", "Não foi possível clicar na página 2, botão não encontrado.")
        except NoSuchElementException:
            print("Elemento da página 2 não foi encontrado.")
            QMessageBox.critical(None, "Erro", "Elemento da página 2 não foi encontrado.")
        except Exception as e:
            print(f"Erro ao tentar clicar na página 2: {e}")
            QMessageBox.critical(None, "Erro", f"Erro inesperado ao tentar clicar na página 2: {e}")


    def _clicar_divulgacao_de_compras(self):
        try:
            # Primeiro, localize o componente app-hub-acesso-sistemas
            app_hub_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "app-hub-acesso-sistemas"))
            )

            # Dentro deste componente, localize o elemento "Divulgação de Compras"
            divulgacao_compras_element = WebDriverWait(app_hub_element, 10).until(
                EC.element_to_be_clickable((By.XPATH, ".//p[@class='h2 main-title' and contains(text(), 'Divulgação de Compras')]"))
            )

            # Clica no botão "Divulgação de Compras"
            divulgacao_compras_element.click()

            print("Botão 'Divulgação de Compras' clicado com sucesso.")
        except TimeoutException:
            print("Não foi possível encontrar o botão 'Divulgação de Compras' no tempo esperado.")
            QMessageBox.critical(None, "Erro", "Não foi possível clicar no botão 'Divulgação de Compras', elemento não encontrado.")
        except NoSuchElementException:
            print("Elemento 'Divulgação de Compras' não foi encontrado.")
            QMessageBox.critical(None, "Erro", "Elemento 'Divulgação de Compras' não foi encontrado.")
        except Exception as e:
            print(f"Erro ao tentar clicar no botão 'Divulgação de Compras': {e}")
            QMessageBox.critical(None, "Erro", f"Erro inesperado ao tentar clicar no botão 'Divulgação de Compras': {e}")


    def _alternar_para_janela_siasgnet(self):
        aguardar_mudanca_janela(self.driver, titulo_desejado="SIASGnet-DC - Divulgação de Compras")

    def _navegar_menu_licitacao(self):
        # Clicar no menu 'Licitacao'
        menu_licitacao = "#oCMenu_menuLicitacao"
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, menu_licitacao))).click()

        # Clicar na opção 'Consultar Licitação'
        consultar_licitacao = "#oCMenu_menuConsultarLicitacao"
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, consultar_licitacao))).click()

        # Aguardar aparecer o botão 'Pesquisar' e clicar nele
        pesquisar = "#pesquisar"
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, pesquisar))).click()

    def _exibir_mensagem_selecao_licitacao(self):
        QMessageBox.information(None, "Seleção de Licitação", "Selecione a Licitação desejada para webscraping.")

    def _aguardar_usuario_clicar_visualizar(self):
        script = '''
        function selecionarVisualizar(rowNumber) {
            var selector = "#licitacao > tbody > tr:nth-child(" + rowNumber + ") > td:nth-child(7) > a";
            var element = document.querySelector(selector);
            if (element) {
                element.click();
                return true;
            } else {
                return false;
            }
        }
        document.addEventListener("click", function(event) {
            if (event.target.matches("#licitacao > tbody > tr > td:nth-child(7) > a")) {
                window.userClicked = true;
            }
        });
        return new Promise(function(resolve) {
            var checkInterval = setInterval(function() {
                if (window.userClicked) {
                    clearInterval(checkInterval);
                    resolve(true);
                }
            }, 100);
        });
        '''
        self.driver.execute_script(script)
        WebDriverWait(self.driver, 60).until(lambda d: d.execute_script("return window.userClicked === true;"))

    def _aguardar_elemento_itens(self):
        try:
            # Aguardar até que o botão 'Itens' esteja presente e clicável na página
            botao_itens = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#id_botaoItens"))
            )

            # Raspagem dos valores necessários
            uasg_responsavel = self._raspar_valor_input("input[name='versaoCompraComLicitacao.compra.uasgResponsavel.uasgFormatada']")
            nup = self._raspar_valor_input("input[name='versaoCompraComLicitacao.numeroProcesso']")
            quantidade_itens = self._raspar_valor_input("input[name='versaoCompraComLicitacao.quantidadeItensIncluidos']")
            objeto = self._raspar_textarea("textarea[name='versaoCompraComLicitacao.objeto']")

            # Armazena quantidade_itens para uso futuro
            self.quantidade_itens = int(quantidade_itens) if quantidade_itens.isdigit() else 0

            # Imprimir os valores encontrados
            print(f"UASG Responsável: {uasg_responsavel}")
            print(f"NUP: {nup}")
            print(f"Quantidade de Itens: {quantidade_itens}")
            print(f"Objeto: {objeto}")

            # Exibir uma mensagem de sucesso
            QMessageBox.information(None, "Sucesso", "Valores raspados e botão 'Itens' encontrado e clicado!")

            # Clicar no botão 'Itens'
            botao_itens.click()

            # Aguardar o carregamento da nova página e clicar no botão "Visualizar"
            self._clicar_visualizar_itens()

        except TimeoutException:
            QMessageBox.critical(None, "Erro", "O botão 'Itens' não foi encontrado na página carregada.")

    def _raspar_valor_input(self, css_selector):
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, css_selector)
            return element.get_attribute('value')
        except Exception as e:
            print(f"Erro ao raspar o valor do input {css_selector}: {e}")
            return None

    def _raspar_textarea(self, css_selector):
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, css_selector)
            return element.text
        except Exception as e:
            print(f"Erro ao raspar o valor do textarea {css_selector}: {e}")
            return None

    def _clicar_visualizar_itens(self):
        try:
            # Aguardar até que o botão "Visualizar" do primeiro item esteja presente e clicável na página
            visualizar_botao = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#item > tbody > tr:nth-child(1) > td:nth-child(13) > a"))
            )

            # Clicar no botão "Visualizar"
            visualizar_botao.click()

        except TimeoutException:
            QMessageBox.critical(None, "Erro", "O botão 'Visualizar' do item não foi encontrado na página carregada.")

    def _aguardar_item_da_licitacao(self):
        try:
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//div[text()='Item da Licitação']"))
            )
        except TimeoutException:
            print("O elemento 'Item da Licitação' não foi encontrado dentro do tempo esperado.")
            raise

    def _iniciar_scraping_itens(self):
        try:
            aguardar_mudanca_janela(self.driver, titulo_desejado="SIASGnet-DC - Item da Licitação")
            
            # Cria uma instância de ItemLicitacaoScraper e inicia o processo de raspagem
            scraper = ItemLicitacaoScraper(driver=self.driver, quantidade_itens=self.quantidade_itens)
            scraper.iniciar_scraping()

            # Obtém os DataFrames resultantes da raspagem
            df_itens, df_uasg = scraper.get_dataframe()

            # Exibe os resultados no console (ou pode ser salvo em um arquivo, dependendo da necessidade)
            print("Itens Raspados:")
            print(df_itens)
            print("\nUASGs Raspados:")
            print(df_uasg)

            # Exibe uma mensagem de sucesso ao final da raspagem
            QMessageBox.information(None, "Sucesso", "Raspagem dos itens concluída com sucesso!")

        except TimeoutException:
            QMessageBox.critical(None, "Erro", "Timeout ao tentar localizar o input de quantidade de itens.")
        except NoSuchElementException:
            QMessageBox.critical(None, "Erro", "O elemento de quantidade de itens não foi encontrado na página.")
        except Exception as e:
            QMessageBox.critical(None, "Erro durante a raspagem", f"Ocorreu um erro ao raspar os itens: {e}")
            
class ItemLicitacaoScraper:
    def __init__(self, driver, quantidade_itens):
        self.driver = driver
        self.quantidade_itens = quantidade_itens
        self.df_itens = pd.DataFrame(columns=[
            'numero_item', 'tipo_item', 'descricao_item', 'descricao_detalhada', 'unidade_fornecimento',
            'quantidade_total', 'valor_unitario', 'valor_total_estimado'
        ])
        self.df_uasg = pd.DataFrame(columns=[
            'numero_item', 'uasg', 'tipo', 'municipio_uf', 'quantidade'
        ])

    def iniciar_scraping(self):
        for i in range(1, self.quantidade_itens + 1):
            try:
                self._processar_item(i)
                self._clicar_proximo_item(i + 1)
            except TimeoutException:
                print(f"Erro ao processar o item {i}. Continuando para o próximo.")
                continue
        salvar_dataframes_em_excel(self.df_itens, self.df_uasg)

    def _processar_item(self, numero_item):
        print(f"Processando item {numero_item}...")

        # Raspagem dos dados do item
        numero_item = self._raspar_valor_input("input[name='itemLicitacao.numeroItem']")
        tipo_item = self._raspar_valor_input("input[name='itemLicitacao.tipoItem']")
        descricao_item = self._raspar_valor_input("input[name='itemLicitacao.descricaoFormatada']")
        unidade_fornecimento = self._raspar_valor_input("input[name='itemLicitacao.unidadeFornecimento.unidadeFornecimento']")
        descricao_detalhada = self._raspar_valor_textarea("textarea[name='itemLicitacao.descricaoDetalhada']")
        quantidade_total = self._raspar_valor_input("input[name='quantidadeTotal']")
        valor_unitario = self._raspar_valor_input("input[name='itemLicitacao.valorUnitarioEstimado']")
        valor_total_estimado = self._raspar_valor_input("input[name='itemLicitacao.valorTotalEstimado']")

        # Criar um DataFrame com a linha do item e concatenar ao DataFrame principal
        novo_item = pd.DataFrame([{
            'numero_item': numero_item,
            'tipo_item': tipo_item,
            'descricao_item': descricao_item,
            'unidade_fornecimento': unidade_fornecimento,
            'descricao_detalhada': descricao_detalhada,
            'quantidade_total': quantidade_total,
            'valor_unitario': valor_unitario,
            'valor_total_estimado': valor_total_estimado
        }])
        self.df_itens = pd.concat([self.df_itens, novo_item], ignore_index=True)

        # Raspagem dos dados da tabela UASG
        self._raspar_tabela_uasg(numero_item)

    def _raspar_tabela_uasg(self, numero_item):
        print(f"Raspando tabela UASG para o item {numero_item}...")

        try:
            # Encontrar todas as linhas da tabela de UASG
            linhas = self.driver.find_elements(By.CSS_SELECTOR, "#localEnt tbody tr")

            if not linhas:
                print(f"Não foram encontradas linhas na tabela de UASG para o item {numero_item}.")
                return

            for linha in linhas:
                colunas = linha.find_elements(By.TAG_NAME, "td")

                if len(colunas) < 4:
                    print(f"Erro: A linha não contém colunas suficientes para o item {numero_item}.")
                    continue

                uasg = colunas[0].text
                tipo = colunas[1].text
                municipio_uf = colunas[2].text
                quantidade = colunas[3].text

                # Criar um DataFrame com a linha da UASG e concatenar ao DataFrame principal
                nova_uasg = pd.DataFrame([{
                    'numero_item': numero_item,
                    'uasg': uasg,
                    'tipo': tipo,
                    'municipio_uf': municipio_uf,
                    'quantidade': quantidade
                }])
                self.df_uasg = pd.concat([self.df_uasg, nova_uasg], ignore_index=True)

        except Exception as e:
            print(f"Erro ao raspar a tabela UASG para o item {numero_item}: {e}")

    def _clicar_proximo_item(self, proximo_item):
        try:
            proximo_item_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#btnProximoItem"))
            )
            proximo_item_button.click()

            # Verificar se o próximo item foi carregado corretamente
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element_value((By.CSS_SELECTOR, "input[name='itemLicitacao.numeroItem']"), str(proximo_item))
            )
        except Exception as e:
            print(f"Erro ao clicar no próximo item {proximo_item}: {e}")

    def _raspar_valor_textarea(self, css_selector):
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, css_selector)
            return element.text
        except Exception as e:
            print(f"Erro ao raspar o valor do textarea {css_selector}: {e}")
            return None

    def _raspar_valor_input(self, css_selector):
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, css_selector)
            return element.get_attribute('value')
        except Exception as e:
            print(f"Erro ao raspar o valor do input {css_selector}: {e}")
            return None

    def get_dataframe(self):
        return self.df_itens, self.df_uasg
    
def salvar_dataframes_em_excel(df_itens, df_uasg, caminho_arquivo="resultado_licitacao.xlsx"):
    try:
        # Separar uasg e nome_uasg em colunas diferentes
        df_uasg[['uasg', 'nome_uasg']] = df_uasg['uasg'].str.split(' - ', expand=True)

        # Converter 'numero_item' e 'quantidade' para inteiros
        df_itens['numero_item'] = df_itens['numero_item'].astype(int)
        df_itens['quantidade_total'] = df_itens['quantidade_total'].astype(int)
        df_uasg['numero_item'] = df_uasg['numero_item'].astype(int)
        df_uasg['quantidade'] = df_uasg['quantidade'].astype(int)

        # Remover a coluna 'tipo_item' do df_itens
        if 'tipo_item' in df_itens.columns:
            df_itens.drop(columns=['tipo_item'], inplace=True)

        # Reorganizar o DataFrame df_uasg
        df_uasg_pivot = df_uasg.pivot(index='numero_item', columns='uasg', values='quantidade').fillna(0)

        # Adicionar coluna 'Total' com o somatório das quantidades
        df_uasg_pivot['Total'] = df_uasg_pivot.sum(axis=1)

        # Ajustar os índices e colunas conforme solicitado
        df_uasg_pivot.index.name = "Item"
        df_uasg_pivot.columns.name = "UASG"
        df_uasg_pivot.reset_index(inplace=True)

        # Alterar o nome da coluna de "numero_item" para "Item"
        df_itens.rename(columns={'numero_item': 'Item', 'quantidade_total': 'Quantidade'}, inplace=True)

        with pd.ExcelWriter(caminho_arquivo, engine='xlsxwriter') as writer:
            # Salvar df_itens na aba 'Itens'
            df_itens.to_excel(writer, sheet_name='Itens', index=False)
            # Salvar df_uasg reorganizado na aba 'UASG_ordenada'
            df_uasg_pivot.to_excel(writer, sheet_name='UASG_ordenada', index=False)

        QMessageBox.information(None, "Sucesso", f"Os dados foram salvos com sucesso em {caminho_arquivo}")

        # Abrir o arquivo Excel gerado
        abrir_arquivo_excel(caminho_arquivo)

    except Exception as e:
        QMessageBox.critical(None, "Erro", f"Erro ao salvar o arquivo Excel: {e}")



def abrir_arquivo_excel(caminho_arquivo):
    try:
        if os.name == 'nt':  # Windows
            os.startfile(caminho_arquivo)
        else:
            subprocess.call(['open', caminho_arquivo] if os.name == 'posix' else ['xdg-open', caminho_arquivo])
    except Exception as e:
        QMessageBox.critical(None, "Erro", f"Erro ao abrir o arquivo Excel: {e}")

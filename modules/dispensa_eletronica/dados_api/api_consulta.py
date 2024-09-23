import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import *
from diretorios import *
import sqlite3
import re
from pathlib import Path
class ProgressoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Progresso da Consulta")

        # Layout principal
        layout = QVBoxLayout()

        # Label para o status do sequencial
        self.sequencial_label = QLabel("Verificando o sequencial no PNCP para a Dispensa Eletrônica...")
        layout.addWidget(self.sequencial_label)

        # Adicionar ícone e status do sequencial
        self.icon_label = QLabel()
        self.icon_label.setPixmap(QPixmap("aproved.png"))  # Assumindo que você tenha o ícone 'ok.png'
        self.sequencial_status = QLabel("Sequencial Compatível")
        sequencial_layout = QHBoxLayout()
        sequencial_layout.addWidget(self.icon_label)
        sequencial_layout.addWidget(self.sequencial_status)
        layout.addLayout(sequencial_layout)

        # Label para o progresso da verificação de itens
        self.itens_label = QLabel("Verificando itens...")
        layout.addWidget(self.itens_label)

        # Barra de progresso para acompanhamento
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Botão de Fechar
        self.close_button = QPushButton("Fechar")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def atualizar_progresso(self, mensagem, valor_atual, valor_total):
        self.itens_label.setText(mensagem)
        self.progress_bar.setMaximum(valor_total)
        self.progress_bar.setValue(valor_atual)

class PNCPConsultaThread(QThread):
    consulta_concluida = pyqtSignal(list, list)  # Certifique-se de que dois argumentos estão sendo passados
    erro_consulta = pyqtSignal(str)
    progresso_consulta = pyqtSignal(str, int, int)

    def __init__(self, numero, ano, link_pncp, uasg, parent=None):
        super().__init__(parent)
        self.numero = numero
        self.ano = ano
        self.link_pncp = link_pncp
        self.uasg = uasg

    def run(self):
        consulta_pncp = PNCPConsulta(self.numero, self.ano, self.link_pncp, self.uasg, self)
        try:
            data_informacoes_lista, resultados_completos = consulta_pncp.consultar_por_sequencial(self.progresso_consulta)
            self.consulta_concluida.emit(data_informacoes_lista, resultados_completos)  # Emitir ambos os conjuntos de dados
        except Exception as e:
            self.erro_consulta.emit(f"Erro ao realizar a consulta: {str(e)}")

class PNCPConsulta:
    def __init__(self, numero, ano, link_pncp, uasg, parent=None):
        self.numero = numero
        self.ano = ano
        self.link_pncp = link_pncp
        self.uasg = uasg
        self.parent = parent
        self.db_path = CONTROLE_DADOS_PNCP

    def consultar(self):
        # Simulação da consulta que retornaria dados JSON (essa parte deve ser adaptada ao seu contexto real)
        dados_json = [
            {"ano": self.ano, "link_pncp": self.link_pncp},
            # outros possíveis dados retornados...
        ]
        # Retorna apenas ano e link_pncp
        return [{"ano": item["ano"], "link_pncp": item["link_pncp"]} for item in dados_json]

    def salvar_json_na_area_de_trabalho(self, json_data, filename):
        # Salva os resultados filtrados no arquivo JSON
        with open(Path.home() / f"{filename}.json", 'w') as file:
            json.dump(json_data, file, indent=4)

    def integrar_dados(self, data_informacoes_lista, resultados_completos):
        # Verificação dos dados recebidos
        print(f"Dados recebidos para salvar no banco:")
        print(f"data_informacoes: {json.dumps(data_informacoes_lista, indent=2)}")
        print(f"resultados_completos: {json.dumps(resultados_completos, indent=2)}")

        # Nomes dinâmicos das tabelas
        table_name_info = f"INFO_DE{self.numero}{self.ano}{self.link_pncp}{self.uasg}"
        table_name_resultados = f"DE{self.numero}{self.ano}{self.link_pncp}{self.uasg}"

        # Remover caracteres especiais dos nomes das tabelas
        table_name_info = re.sub(r'[^\w]', '_', table_name_info)
        table_name_resultados = re.sub(r'[^\w]', '_', table_name_resultados)

        # Salvar os dados de 'data_informacoes' no banco (dicionário)
        self.salvar_dados_no_banco_lista_tupla(data_informacoes_lista, table_name_info)

        # Salvar os dados de 'resultados_completos' no banco (lista)
        self.salvar_dados_no_banco_lista(resultados_completos, table_name_resultados)

        # Confirmação de sucesso
        QMessageBox.information(self.parent, "Integrar Dados", 
                                f"Os dados foram integrados com sucesso nas tabelas '{table_name_info}' e '{table_name_resultados}'.")

    def salvar_dados_no_banco_lista(self, dados, nome_tabela):
        """
        Função para salvar uma lista de dicionários no banco de dados.
        Cada dicionário da lista representa uma linha na tabela.
        """
        try:
            # Conectar ao banco de dados
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if not dados or len(dados) == 0:
                raise ValueError("Lista de dados está vazia ou inválida.")

            # Identificar todas as colunas únicas presentes nos dados
            colunas_set = set()
            for item in dados:
                colunas_set.update(item.keys())

            # Ordenar as colunas
            colunas = sorted(colunas_set)
            colunas_str = ", ".join(colunas)
            valores_placeholder = ", ".join("?" for _ in colunas)

            # Criar a tabela se não existir
            colunas_definicao = ", ".join([f"{coluna} TEXT" for coluna in colunas])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {nome_tabela} ({colunas_definicao})")

            # Inserir dados no banco de dados
            for item in dados:
                # Garantir que cada item tenha um valor (ou None) para cada coluna
                valores = [item.get(coluna, None) for coluna in colunas]
                cursor.execute(f"INSERT INTO {nome_tabela} ({colunas_str}) VALUES ({valores_placeholder})", valores)

            # Confirmar as mudanças e fechar a conexão
            conn.commit()
            conn.close()

            print(f"Dados salvos com sucesso na tabela: {nome_tabela}")

        except Exception as e:
            print(f"Erro ao salvar os dados (lista): {str(e)}")
            QMessageBox.critical(self.parent, "Erro", f"Erro ao salvar os dados (lista): {str(e)}")

    def salvar_dados_no_banco_lista_tupla(self, dados, nome_tabela):
        """
        Função para salvar uma lista de tuplas (chave, valor) no banco de dados.
        Cada tupla representa uma coluna e valor correspondente.
        """
        try:
            # Conectar ao banco de dados
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if not dados or len(dados) == 0:
                raise ValueError("Lista de dados está vazia ou inválida.")

            # Obter colunas e valores da lista de tuplas
            colunas = ", ".join([chave for chave, _ in dados])
            valores_placeholder = ", ".join("?" for _ in dados)
            valores = tuple([valor for _, valor in dados])

            # Criar a tabela se não existir
            colunas_definicao = ", ".join([f"{chave} TEXT" for chave, _ in dados])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {nome_tabela} ({colunas_definicao})")

            # Inserir os dados no banco de dados
            insert_query = f"INSERT INTO {nome_tabela} ({colunas}) VALUES ({valores_placeholder})"
            cursor.execute(insert_query, valores)

            # Confirmar as mudanças e fechar a conexão
            conn.commit()
            conn.close()

            print(f"Dados salvos com sucesso na tabela: {nome_tabela}")

        except Exception as e:
            print(f"Erro ao salvar os dados (lista): {str(e)}")
            QMessageBox.critical(self.parent, "Erro", f"Erro ao salvar os dados (lista): {str(e)}")


    # Método para exibir os dados obtidos no QDialog
    def exibir_dados_em_dialog(self, data_informacoes_lista, resultados_completos):
        # Cria o QDialog para exibir os dados
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Dados do PNCP")

        # Define o tamanho fixo do QDialog
        dialog.setFixedSize(800, 400)  # Aumenta o tamanho para acomodar os dois layouts

        # Cria um layout horizontal principal
        layout_horizontal = QHBoxLayout()

        # Cria os layouts verticais para os dois conjuntos de dados
        layout_informacoes = QVBoxLayout()
        layout_resultados = QVBoxLayout()

        # Campo de texto para exibir 'data_informacoes'
        text_edit_informacoes = QTextEdit()
        text_edit_informacoes.setReadOnly(True)

        # Campo de texto para exibir 'resultados_completos'
        text_edit_resultados = QTextEdit()
        text_edit_resultados.setReadOnly(True)

        # Função para formatar a lista de pares (chave, valor)
        def formatar_lista_pares(lista_pares):
            texto = ""
            for chave, valor in lista_pares:
                texto += f"{chave}: {valor}\n"
            return texto

        # Exibir 'data_informacoes_lista' como uma lista de pares chave-valor
        texto_informacoes = "Informações:\n"
        texto_informacoes += formatar_lista_pares(data_informacoes_lista)

        # Exibir 'resultados_completos'
        texto_resultados = "Resultados:\n"
        if isinstance(resultados_completos, list):
            for i, resultado in enumerate(resultados_completos, 1):
                texto_resultados += f"\nItem {i}:\n"
                texto_resultados += json.dumps(resultado, indent=2)  # Formatação básica para exibir o JSON dos resultados
        else:
            texto_resultados += json.dumps(resultados_completos, indent=2)

        # Adiciona os textos formatados aos QTextEdits
        text_edit_informacoes.setText(texto_informacoes)
        text_edit_resultados.setText(texto_resultados)

        # Adiciona os QTextEdits aos layouts verticais
        layout_informacoes.addWidget(QLabel("Informações"))
        layout_informacoes.addWidget(text_edit_informacoes)

        layout_resultados.addWidget(QLabel("Resultados"))
        layout_resultados.addWidget(text_edit_resultados)

        # Adiciona os dois layouts verticais ao layout horizontal
        layout_horizontal.addLayout(layout_informacoes)
        layout_horizontal.addLayout(layout_resultados)

        # Adiciona o layout principal ao QDialog
        layout = QVBoxLayout()
        layout.addLayout(layout_horizontal)

        # Botão para integrar dados
        button_integrar = QPushButton("Integrar Dados")
        button_integrar.clicked.connect(lambda: self.integrar_dados(data_informacoes_lista, resultados_completos))
        layout.addWidget(button_integrar)

        # Botão de fechar o diálogo
        button_close = QPushButton("Fechar")
        button_close.clicked.connect(dialog.accept)
        layout.addWidget(button_close)

        # Define o layout no diálogo
        dialog.setLayout(layout)

        # Exibe o diálogo
        dialog.exec()


    def limpar_dados(self, json_data):
        campos_para_remover = [
            "orcamentoSigiloso",
            "itemCategoriaId",
            "itemCategoriaNome",
            "patrimonio",
            "codigoRegistroImobiliario",
            "criterioJulgamentoId",
            "situacaoCompraItem",
            "tipoBeneficio",
            "incentivoProdutivoBasico",
            "imagem",
            "aplicabilidadeMargemPreferenciaNormal",
            "aplicabilidadeMargemPreferenciaAdicional",
            "percentualMargemPreferenciaNormal",
            "percentualMargemPreferenciaAdicional",
            "ncmNbsCodigo",
            "ncmNbsDescricao",
            "tipoPessoa",
            "timezoneCotacaoMoedaEstrangeira",
            "moedaEstrangeira",
            "valorNominalMoedaEstrangeira",
            "dataCotacaoMoedaEstrangeira",
            "codigoPais",
            "porteFornecedorId",
            "amparoLegalMargemPreferencia",
            "amparoLegalCriterioDesempate",
            "paisOrigemProdutoServico",
            "indicadorSubcontratacao",
            "ordemClassificacaoSrp",
            "motivoCancelamento",
            "situacaoCompraItemResultadoId",
            "sequencialResultado",
            "naturezaJuridicaNome",
            "porteFornecedorNome",
            "naturezaJuridicaId",
            "dataCancelamento",
            "aplicacaoMargemPreferencia",
            "aplicacaoBeneficioMeEpp",
            "aplicacaoCriterioDesempate"
        ]

        # Remover os campos de cada item no json_data
        for item in json_data:
            for campo in campos_para_remover:
                item.pop(campo, None)

        return json_data
        
    def consultar_por_sequencial(self, progresso_callback):
        url_informacoes = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.link_pncp}"
        try:
            progresso_callback.emit(f"Procurando '{self.link_pncp}' no PNCP\nUASG: {self.uasg}", 0, 0)

            # Primeira requisição
            response_informacoes = requests.get(url_informacoes)
            response_informacoes.raise_for_status()
            data_informacoes = response_informacoes.json()

            existe_resultado = data_informacoes.get("existeResultado", False)
            ano_compra = int(data_informacoes.get("anoCompra"))
            numero_compra = str(data_informacoes.get("numeroCompra")).strip()

            if not existe_resultado:
                raise Exception("Nenhum resultado encontrado para o sequencial.")

            if ano_compra != int(self.ano):
                raise Exception(f"Ano da compra não corresponde: {ano_compra} (esperado: {self.ano})")

            if numero_compra != str(self.numero).strip():
                raise Exception(f"Número da compra não corresponde: {numero_compra} (esperado: {self.numero})")

            progresso_callback.emit("Sequencial compatível", 0, 0)

            # Função auxiliar para converter o dicionário em uma lista de pares (chave, valor)
            def dicionario_para_lista(d):
                lista = []
                for chave, valor in d.items():
                    if isinstance(valor, dict):
                        # Se o valor é um dicionário, achatar também o subdicionário
                        sub_lista = dicionario_para_lista(valor)
                        for sub_chave, sub_valor in sub_lista:
                            lista.append((f"{chave}_{sub_chave}", sub_valor))
                    else:
                        lista.append((chave, valor))
                return lista

            # Converter data_informacoes para lista
            data_informacoes_lista = dicionario_para_lista(data_informacoes)

            # Consultar quantidade de itens
            qnt_itens = self.consultar_quantidade_de_itens()

            # Consultar os detalhes dos itens
            resultados_completos = self.consultar_detalhes_dos_itens(qnt_itens, progresso_callback)

            # Depuração: Verificar os dados recebidos
            print(f"Conteúdo de data_informacoes: {json.dumps(data_informacoes_lista, indent=2)}")
            print(f"Tipo de data_informacoes: {type(data_informacoes_lista)}")

            # Limpar os dados e retornar os dois conjuntos de dados
            return data_informacoes_lista, self.limpar_dados(resultados_completos)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Falha na consulta: {str(e)}")

    def consultar_quantidade_de_itens(self):
        url_quantidade = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.link_pncp}/itens/quantidade"
        response_quantidade = requests.get(url_quantidade)
        response_quantidade.raise_for_status()
        data_quantidade = response_quantidade.json()

        if isinstance(data_quantidade, int):
            return data_quantidade
        else:
            raise Exception("Resposta inesperada da API para quantidade.")
        
    def consultar_detalhes_dos_itens(self, qnt_itens, progresso_callback):
        resultados_completos = []
        
        for i in range(1, qnt_itens + 1):
            url_item_info = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.link_pncp}/itens/{i}"
            response_item_info = requests.get(url_item_info)
            response_item_info.raise_for_status()
            data_item_info = response_item_info.json()

            progresso_callback.emit(f"Verificando item {i}/{qnt_itens}", i, qnt_itens)

            if data_item_info.get('temResultado', False):
                # Se tem resultado, faz a consulta adicional
                url_item_resultados = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.link_pncp}/itens/{i}/resultados"
                response_item_resultados = requests.get(url_item_resultados)
                response_item_resultados.raise_for_status()
                data_item_resultados = response_item_resultados.json()

                if isinstance(data_item_resultados, list):
                    for resultado in data_item_resultados:
                        for key, value in resultado.items():
                            data_item_info[key] = value
            else:
                # Se não há resultado, adicionar 'None' para as chaves esperadas
                expected_keys = ['dataResultado', 'niFornecedor', 'nomeRazaoSocialFornecedor', 'numeroControlePNCPCompra', 'tipoBeneficioNome', 'valorUnitarioEstimado']
                for key in expected_keys:
                    data_item_info[key] = None

            # Adiciona o item, seja com resultado ou com valores 'None'
            resultados_completos.append(data_item_info)

        return resultados_completos

    def converter_para_lista(self, dados):
        """
        Converte um dicionário aninhado em uma lista de pares chave: valor.
        Substitui os subdicionários por pares chave: valor com a chave concatenada.
        """
        lista_resultado = []

        def _achatar(sub_dados, chave_pai=""):
            if isinstance(sub_dados, dict):
                for chave, valor in sub_dados.items():
                    nova_chave = f"{chave_pai}.{chave}" if chave_pai else chave
                    if isinstance(valor, (dict, list)):
                        _achatar(valor, nova_chave)
                    else:
                        lista_resultado.append((nova_chave, valor))
            elif isinstance(sub_dados, list):
                for index, item in enumerate(sub_dados):
                    nova_chave = f"{chave_pai}[{index}]" if chave_pai else f"[{index}]"
                    _achatar(item, nova_chave)

        _achatar(dados)
        return lista_resultado


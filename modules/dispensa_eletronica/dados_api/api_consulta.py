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
    consulta_concluida = pyqtSignal(list)
    erro_consulta = pyqtSignal(str)
    progresso_consulta = pyqtSignal(str, int, int)

    def __init__(self, numero, ano, link_pncp, uasg, parent=None):
        super().__init__(parent)
        self.numero = numero
        self.ano = ano
        self.link_pncp = link_pncp
        self.uasg = uasg

    def run(self):
        consulta_pncp = PNCPConsulta(self.numero, self.ano, self.link_pncp, self.uasg, self.parent)
        try:
            json_data = consulta_pncp.consultar_por_sequencial(self.progresso_consulta)
            if json_data:
                self.consulta_concluida.emit(json_data)
            else:
                self.erro_consulta.emit("Nenhum resultado encontrado.")
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
                raise Exception("Nenhum resultado encontrado para o sequencial.")  # Lançar exceção para interromper a execução

            if ano_compra != int(self.ano):
                raise Exception(f"Ano da compra não corresponde: {ano_compra} (esperado: {self.ano})")  # Interromper

            if numero_compra != str(self.numero).strip():
                raise Exception(f"Número da compra não corresponde: {numero_compra} (esperado: {self.numero})")  # Interromper

            progresso_callback.emit("Sequencial compatível", 0, 0)

            # Prosseguir com a consulta de quantidade de itens
            url_quantidade = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.link_pncp}/itens/quantidade"
            response_quantidade = requests.get(url_quantidade)
            response_quantidade.raise_for_status()
            data_quantidade = response_quantidade.json()

            if isinstance(data_quantidade, int):
                qnt_itens = data_quantidade
                progresso_callback.emit(f"Iniciando verificação de {qnt_itens} itens.", 0, qnt_itens)
            else:
                raise Exception("Resposta inesperada da API para quantidade.")

            resultados_completos = []
            for i in range(1, qnt_itens + 1):
                url_item_info = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.link_pncp}/itens/{i}"
                response_item_info = requests.get(url_item_info)
                response_item_info.raise_for_status()
                data_item_info = response_item_info.json()

                progresso_callback.emit(f"Verificando item {i}/{qnt_itens}", i, qnt_itens)

                if data_item_info.get('temResultado', False):
                    url_item_resultados = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.link_pncp}/itens/{i}/resultados"
                    response_item_resultados = requests.get(url_item_resultados)
                    response_item_resultados.raise_for_status()
                    data_item_resultados = response_item_resultados.json()

                    if isinstance(data_item_resultados, list):
                        for resultado in data_item_resultados:
                            for key, value in resultado.items():
                                data_item_info[key] = value

                resultados_completos.append(data_item_info)

            # Limpar os dados e retornar
            return self.limpar_dados(resultados_completos)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Falha na consulta: {str(e)}")

    def integrar_dados(self, json_data):
        """
        Função para salvar os dados no banco de dados CONTROLE_DADOS_PNCP.
        Também salva os dados em formato JSON no BASE_DIR.
        """

        # Cria o nome da tabela dinamicamente com base nos atributos da classe
        table_name = f"DE{self.numero}{self.ano}{self.link_pncp}{self.uasg}"

        # Remover caracteres especiais do nome da tabela
        table_name = re.sub(r'[^\w]', '_', table_name)  # Substitui caracteres especiais por "_"

        # Salvar os dados no banco de dados
        self.salvar_dados_no_banco(json_data, table_name)

        # Salvar os dados como arquivo JSON
        self.salvar_dados_json(json_data, table_name)

        # Confirmação de sucesso
        QMessageBox.information(self.parent, "Integrar Dados", f"Os dados foram integrados com sucesso na tabela '{table_name}' e salvos como JSON.")

    def salvar_dados_no_banco(self, json_data, table_name):
        """
        Salva os dados obtidos no banco de dados CONTROLE_DADOS_PNCP com numeroItem como chave primária.
        """
        # Conecta ao banco de dados
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Obter as colunas do JSON (assumindo que todos os itens têm as mesmas chaves)
        columns = json_data[0].keys()

        # Criar a tabela dinamicamente com base nas colunas do JSON
        col_defs = ", ".join([f"{col} TEXT" for col in columns if col != "numeroItem"])  # Define as colunas como TEXT
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                numeroItem INTEGER PRIMARY KEY, 
                {col_defs}
            )
        """
        cursor.execute(create_table_query)

        # Inserir os dados no banco de dados
        for item in json_data:
            # Preparar os valores para inserção
            values = tuple(str(item[col]) for col in columns)

            # Gerar a query de inserção
            placeholders = ", ".join("?" for _ in columns)
            insert_query = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(insert_query, values)

        # Commit e fechamento da conexão
        conn.commit()
        conn.close()


    def salvar_dados_json(self, json_data, table_name):
        """
        Salva os dados obtidos em um arquivo JSON no diretório BASE_DIR.
        """
        # Gera o caminho para salvar o arquivo JSON
        file_path = BASE_DIR / f"{table_name}.json"

        # Salvar o conteúdo JSON no arquivo
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

        print(f"Arquivo JSON salvo com sucesso em: {file_path}")

    # Método para exibir os dados obtidos no QDialog
    def exibir_dados_em_dialog(self, json_data):
        # Cria o QDialog para exibir os dados
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Dados do PNCP")
        
        # Define o tamanho fixo do QDialog
        dialog.setFixedSize(600, 400)  # Defina o tamanho fixo (largura, altura)

        # Cria um layout vertical
        layout = QVBoxLayout()

        # Campo de texto para exibir o JSON formatado
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        # Exibir os dados de forma legível no QTextEdit
        texto_exibicao = ""
        for item in json_data:
            for key, value in item.items():
                texto_exibicao += f"{key}: {value}\n"
            texto_exibicao += "\n"  # Separar itens com uma linha em branco
        text_edit.setText(texto_exibicao)

        # Botão para integrar dados
        button_integrar = QPushButton("Integrar Dados")
        button_integrar.clicked.connect(lambda: self.integrar_dados(json_data))

        # Botão de fechar o diálogo
        button_close = QPushButton("Fechar")
        button_close.clicked.connect(dialog.accept)

        # Adiciona os widgets ao layout
        layout.addWidget(text_edit)
        layout.addWidget(button_integrar)  # Adiciona o botão 'Integrar Dados' ao layout
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
        
    def salvar_json_na_area_de_trabalho(self, json_data, filename):
        try:
            # Obter o caminho da área de trabalho
            desktop_path = Path.home() / 'Desktop'
            file_path = desktop_path / f"{filename}.json"

            # Salvar o conteúdo JSON no arquivo
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)

            print(f"Arquivo JSON salvo com sucesso em: {file_path}")

            # Verificar se parent é válido antes de usar QMessageBox
            if isinstance(self.parent, QWidget):
                QMessageBox.information(self.parent, "Sucesso", f"Arquivo JSON salvo em: {file_path}")
            else:
                QMessageBox.information(None, "Sucesso", f"Arquivo JSON salvo em: {file_path}")

        except Exception as e:
            # Verificar se parent é válido antes de usar QMessageBox
            if isinstance(self.parent, QWidget):
                QMessageBox.critical(self.parent, "Erro", f"Erro ao salvar o arquivo JSON: {str(e)}")
            else:
                QMessageBox.critical(None, "Erro", f"Erro ao salvar o arquivo JSON: {str(e)}")



    # def formatar_resultados(self, data):
    #     """
    #     Formata os dados da resposta JSON exibindo apenas os campos especificados no mapeamento.
    #     """
    #     mapeamento_chaves = {
    #         'numeroItem': 'Item:',
    #         'descricao': 'Descrição:',
    #         'materialOuServicoNome': 'Material/Serviço:',
    #         'valorUnitarioEstimado': 'Valor unitário estimado:',
    #         'valorTotal': 'Valor total estimado:',
    #         'unidadeMedida': 'Unidade de medida:',
    #         'situacaoCompraItemNome': 'Situação:',
    #         'dataAtualizacao': 'Atualizado em:',
    #         'niFornecedor': 'CNPJ/CPF:',
    #         'nomeRazaoSocialFornecedor': 'Nome:',
    #         'quantidadeHomologada': 'Quantidade:',
    #         'valorUnitarioHomologado': 'Valor unitário:',
    #         'valorTotalHomologado': 'Valor total homologado:',
    #         'dataResultado': 'Resultado:',
    #         'numeroControlePNCPCompra': 'ID PNCP:',
    #     }

    #     resultados_formatados = []
        
    #     # Iterar pelos itens da resposta (que pode ser uma lista de dicionários)
    #     if isinstance(data, list):
    #         for item in data:
    #             for chave, valor in item.items():
    #                 if chave in mapeamento_chaves:  # Exibe apenas os valores mapeados
    #                     resultados_formatados.append(f"{mapeamento_chaves[chave]} {valor}")
    #     elif isinstance(data, dict):
    #         for chave, valor in data.items():
    #             if chave in mapeamento_chaves:  # Exibe apenas os valores mapeados
    #                 resultados_formatados.append(f"{mapeamento_chaves[chave]} {valor}")

    #     return resultados_formatados
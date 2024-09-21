import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QThread, pyqtSignal

class PNCPConsultaThread(QThread):
    consulta_concluida = pyqtSignal(list)
    erro_consulta = pyqtSignal(str)
    progresso_consulta = pyqtSignal(str)

    def __init__(self, ano, link_pncp, uasg, parent=None):
        super().__init__(parent)
        self.ano = ano
        self.link_pncp = link_pncp
        self.uasg = uasg

    def run(self):
        try:
            self.progresso_consulta.emit(f"Procurando '{self.link_pncp}' no PNCP\nUASG: {self.uasg}")
            consulta_pncp = PNCPConsulta(self.ano, self.link_pncp, self.uasg, self.parent)
            json_data = consulta_pncp.consultar_por_sequencial()

            if json_data:
                print(f"Ano: {self.ano}, Link: {self.link_pncp}, UASG: {self.uasg}")
                self.consulta_concluida.emit(json_data)
            else:
                self.erro_consulta.emit("Nenhum resultado encontrado.")
        except Exception as e:
            self.erro_consulta.emit(f"Erro ao realizar a consulta: {str(e)}")
class PNCPConsulta:
    def __init__(self, ano, link_pncp, uasg, parent=None):
        self.ano = ano
        self.link_pncp = link_pncp
        self.uasg = uasg
        self.parent = parent

    def consultar(self):
        # Simulação da consulta que retornaria dados JSON (essa parte deve ser adaptada ao seu contexto real)
        dados_json = [
            {"ano": self.ano, "link_pncp": self.link_pncp},
            # outros possíveis dados retornados...
        ]
        # Retorna apenas ano e link_pncp
        return [{"ano": item["ano"], "link_pncp": item["link_pncp"]} for item in dados_json]

    def formatar_resultados(self, item_data):
        # Apenas retorna ano e link_pncp para exibição
        return [f"Ano: {item_data['ano']}, Link: {item_data['link_pncp']}, UASG: {self.uasg}"]

    def salvar_json_na_area_de_trabalho(self, json_data, filename):
        # Salva os resultados filtrados no arquivo JSON
        with open(Path.home() / f"{filename}.json", 'w') as file:
            json.dump(json_data, file, indent=4)

    def consultar_por_sequencial(self):
        url_quantidade = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.link_pncp}/itens/quantidade"
        try:
            response_quantidade = requests.get(url_quantidade)
            response_quantidade.raise_for_status()
            data_quantidade = response_quantidade.json()

            if isinstance(data_quantidade, int):
                qnt_itens = data_quantidade
            else:
                QMessageBox.warning(self.parent, "Erro", "Resposta inesperada da API.")
                return None

            resultados_completos = []
            for i in range(1, qnt_itens + 1):
                url_item_info = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.link_pncp}/itens/{i}"
                response_item_info = requests.get(url_item_info)
                response_item_info.raise_for_status()
                data_item_info = response_item_info.json()

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
            QMessageBox.critical(self.parent, "Erro", f"Falha na consulta: {str(e)}")
            return None

    # Método para exibir os dados obtidos no QDialog
    def exibir_dados_em_dialog(self, json_data):
        # Cria o QDialog para exibir os dados
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Dados do PNCP")

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

        # Botão de fechar o diálogo
        button_close = QPushButton("Fechar")
        button_close.clicked.connect(dialog.accept)

        # Adiciona os widgets ao layout
        layout.addWidget(text_edit)
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
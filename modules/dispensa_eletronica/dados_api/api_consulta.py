import requests
from PyQt6.QtWidgets import QMessageBox

class PNCPConsulta:
    def __init__(self, numero, ano, parent=None):
        self.numero = numero
        self.ano = ano
        self.parent = parent

    def consultar(self):
        # Etapa 1: Consultar a quantidade de itens
        url_quantidade = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.sequencial}/itens/quantidade"
        try:
            response_quantidade = requests.get(url_quantidade)
            response_quantidade.raise_for_status()
            data_quantidade = response_quantidade.json()

            # Verificar se o retorno é um número inteiro
            if isinstance(data_quantidade, int):
                qnt_itens = data_quantidade
            else:
                QMessageBox.warning(self.parent, "Erro", "Resposta inesperada da API.")
                return None

            # Etapa 2 e Etapa 3: Consultar detalhes de cada item e seus resultados (se houver)
            resultados_completos = []
            for i in range(1, qnt_itens + 1):
                # Etapa 2: Consulta item específico
                url_item_info = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.sequencial}/itens/{i}"
                response_item_info = requests.get(url_item_info)
                response_item_info.raise_for_status()
                data_item_info = response_item_info.json()

                # Se 'temResultado' for true, fazer consulta da Etapa 3 e mesclar resultados
                if data_item_info.get('temResultado', False):
                    url_item_resultados = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{self.sequencial}/itens/{i}/resultados"
                    response_item_resultados = requests.get(url_item_resultados)
                    response_item_resultados.raise_for_status()
                    data_item_resultados = response_item_resultados.json()

                    # Verificar se a resposta da Etapa 3 é uma lista e iterar sobre ela
                    if isinstance(data_item_resultados, list):
                        for resultado in data_item_resultados:
                            # Mesclar os dados da Etapa 3 no dicionário da Etapa 2
                            for key, value in resultado.items():
                                data_item_info[key] = value

                # Adicionar o item com dados combinados (Etapa 2 e possivelmente Etapa 3)
                resultados_completos.append(data_item_info)

            return resultados_completos

        except requests.exceptions.RequestException as e:
            if self.parent:
                QMessageBox.critical(self.parent, "Erro", f"Falha na consulta: {str(e)}")
            return None

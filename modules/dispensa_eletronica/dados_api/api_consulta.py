import requests
from PyQt6.QtWidgets import QMessageBox

class PNCPConsulta:
    def __init__(self, sequencial, parent=None):
        self.sequencial = sequencial
        self.parent = parent

    def consultar(self):
        url = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/2024/{self.sequencial}/itens/1/resultados"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Verificar se 'data' é uma lista ou um dicionário
            if isinstance(data, list):
                resultados = []
                for item in data:
                    if isinstance(item, dict):
                        resultados.extend([f"{key}: {value}" for key, value in item.items()])
                    else:
                        resultados.append(str(item))
                return resultados
            elif isinstance(data, dict):
                return [f"{key}: {value}" for key, value in data.items()]
            else:
                return ["Formato de resposta desconhecido"]

        except requests.exceptions.RequestException as e:
            if self.parent:
                QMessageBox.critical(self.parent, "Erro", f"Falha na consulta: {str(e)}")
            return None

import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QMessageBox, QWidget

from PyQt6.QtCore import QThread, pyqtSignal

class PNCPConsultaThread(QThread):
    # Sinais para comunicar a thread principal
    consulta_concluida = pyqtSignal(list)
    erro_consulta = pyqtSignal(str)
    progresso_consulta = pyqtSignal(str)  # Sinal para enviar progresso

    def __init__(self, numero, ano, data_sessao, uasg, uf, codigoMunicipioIbge, parent=None):
        super().__init__(parent)
        self.numero = numero
        self.ano = ano
        self.data_sessao = data_sessao
        self.uasg = uasg
        self.uf = uf
        self.codigoMunicipioIbge = codigoMunicipioIbge

    def run(self):
        try:
            # Enviar sinal de progresso para exibir a mensagem "Procurando"
            self.progresso_consulta.emit(f"Procurando '{self.numero}/{self.ano}' no PNCP\nData considerada: {self.data_sessao}\nUASG: {self.uasg}\nUF: {self.uf}\nCódigo IBGE: {self.codigoMunicipioIbge}")
            
            # Instanciar a classe PNCPConsulta e realizar a consulta
            consulta_pncp = PNCPConsulta(self.numero, self.ano, self.data_sessao, self.uasg, self.uf, self.codigoMunicipioIbge)
            json_data = consulta_pncp.consultar()

            if json_data:
                self.consulta_concluida.emit(json_data)
            else:
                self.erro_consulta.emit("Nenhum resultado encontrado.")
        except Exception as e:
            self.erro_consulta.emit(f"Erro ao realizar a consulta: {str(e)}")

class PNCPConsulta:
    def __init__(self, numero, ano, data_sessao, uasg, uf, codigoMunicipioIbge, parent=None):
        self.numero = numero
        self.ano = ano
        self.data_sessao = data_sessao
        self.uasg = uasg
        self.uf = uf
        self.codigoMunicipioIbge = codigoMunicipioIbge
        self.parent = parent
                
    def consultar(self):
        # Exibe uma mensagem com o número que está sendo procurado
        if self.parent:
            QMessageBox.information(self.parent, "Procurando", f"Procurando '{self.numero}'/{self.ano} no PNCP\n{self.data_sessao}{self.uasg}\n{self.uf} - {self.codigoMunicipioIbge}")


        # Formatar as datas (dataFinal e dataInicial)
        dataFinal = datetime.strptime(self.data_sessao, '%Y-%m-%d').strftime('%Y%m%d')
        dataInicial = (datetime.strptime(self.data_sessao, '%Y-%m-%d') - timedelta(days=60)).strftime('%Y%m%d')

        # Exibir prints das variáveis
        print(f"dataFinal: {dataFinal}")
        print(f"dataInicial: {dataInicial}")
        print(f"codigoUnidadeAdministrativa: {self.uasg}")
        print(f"codigoMunicipioIbge: { self.codigoMunicipioIbge}")

        # Fazer a requisição do sequencial
        url_sequencial = (f"https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?"
                        f"dataInicial={dataInicial}&dataFinal={dataFinal}"
                        f"&codigoModalidadeContratacao=8&codigoModoDisputa=4"
                        f"&uf={self.uf}&codigoMunicipioIbge={self.codigoMunicipioIbge}"
                        f"&cnpj=00394502000144&codigoUnidadeAdministrativa={self.uasg}"
                        f"&idUsuario=3&pagina=1")

        print(f"url_sequencial: {url_sequencial}")

        try:
            response_sequencial = requests.get(url_sequencial)
            response_sequencial.raise_for_status()
            data_sequencial = response_sequencial.json()

            # Verifica se há algum match entre self.numero e self.ano com os dados da resposta
            sequencial_encontrado = None
            for contratacao in data_sequencial.get('data', []):
                if str(self.numero) == contratacao['numeroCompra'] and int(self.ano) == contratacao['anoCompra']:
                    sequencial_encontrado = contratacao['sequencialCompra']
                    break

            # Mesmo se não houver match, salvar o JSON na área de trabalho
            if not sequencial_encontrado:
                QMessageBox.information(self.parent, "Informação", "Nenhum match encontrado. Salvando dados da requisição.")
                self.salvar_json_na_area_de_trabalho(data_sequencial, 'sem_match')
                return None

            # Realizar a consulta final com o sequencial encontrado
            return self.consultar_por_sequencial(sequencial_encontrado)

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self.parent, "Erro", f"Falha na consulta: {str(e)}")
            return None


    def consultar_por_sequencial(self, sequencial_encontrado):
        # Etapa 1: Consultar a quantidade de itens usando o sequencial encontrado
        url_quantidade = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{sequencial_encontrado}/itens/quantidade"
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
                url_item_info = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{sequencial_encontrado}/itens/{i}"
                response_item_info = requests.get(url_item_info)
                response_item_info.raise_for_status()
                data_item_info = response_item_info.json()

                # Se 'temResultado' for true, fazer consulta da Etapa 3 e mesclar resultados
                if data_item_info.get('temResultado', False):
                    url_item_resultados = f"https://pncp.gov.br/api/pncp/v1/orgaos/00394502000144/compras/{self.ano}/{sequencial_encontrado}/itens/{i}/resultados"
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

            # Retornar os resultados completos após limpar os dados
            return self.limpar_dados(resultados_completos)

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self.parent, "Erro", f"Falha na consulta: {str(e)}")
            return None

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

    def formatar_resultados(self, data):
        """
        Formata os dados da resposta JSON exibindo apenas os campos especificados no mapeamento.
        """
        mapeamento_chaves = {
            'numeroItem': 'Item:',
            'descricao': 'Descrição:',
            'materialOuServicoNome': 'Material/Serviço:',
            'valorUnitarioEstimado': 'Valor unitário estimado:',
            'valorTotal': 'Valor total estimado:',
            'unidadeMedida': 'Unidade de medida:',
            'situacaoCompraItemNome': 'Situação:',
            'dataAtualizacao': 'Atualizado em:',
            'niFornecedor': 'CNPJ/CPF:',
            'nomeRazaoSocialFornecedor': 'Nome:',
            'quantidadeHomologada': 'Quantidade:',
            'valorUnitarioHomologado': 'Valor unitário:',
            'valorTotalHomologado': 'Valor total homologado:',
            'dataResultado': 'Resultado:',
            'numeroControlePNCPCompra': 'ID PNCP:',
        }

        resultados_formatados = []
        
        # Iterar pelos itens da resposta (que pode ser uma lista de dicionários)
        if isinstance(data, list):
            for item in data:
                for chave, valor in item.items():
                    if chave in mapeamento_chaves:  # Exibe apenas os valores mapeados
                        resultados_formatados.append(f"{mapeamento_chaves[chave]} {valor}")
        elif isinstance(data, dict):
            for chave, valor in data.items():
                if chave in mapeamento_chaves:  # Exibe apenas os valores mapeados
                    resultados_formatados.append(f"{mapeamento_chaves[chave]} {valor}")

        return resultados_formatados
        
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

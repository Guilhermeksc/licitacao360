from diretorios import *
import pandas as pd
from pathlib import Path
import re

padrao_1 = (r"UASG\s+(?P<uasg>\d+)\s+-\s+(?P<orgao_responsavel>.+?)\s+PREGÃO\s+(?P<num_pregao>\d+)/(?P<ano_pregao>\d+)")
padrao_srp = r"(?P<srp>SRP - Registro de Preço|SISPP - Tradicional)"
padrao_objeto = (r"Objeto da compra:\s*(?P<objeto>.*?)\s*Entrega de propostas:")
padrao_grupo2 = (r"Item\s+(?P<item_num>\d+)\s+do\s+Grupo\s+G(?P<grupo>\d+).+?Valor\s+estimado:\s+R\$\s+(?P<valor>[\d,.]+).+?Critério\s+de\s+julgamento:\s+(?P<crit_julgamento>.+?)\s+Quantidade:\s+(?P<quantidade>\d+)\s+Unidade\s+de\s+fornecimento:\s+(?P<unidade>[^S]+?)\s+Situação:\s+(?P<situacao>Adjudicado e Homologado|Deserto e Homologado|Fracassado e Homologado)")
padrao_item2 = (r"Item\s+(?P<item_num>\d+)\s+-\s+.*?Quantidade:\s+(?P<quantidade>\d+)\s+Valor\s+estimado:\s+R\$\s+(?P<valor>[\d,.]+)\s+Unidade\s+de\s+fornecimento:\s+(?P<unidade>.+?)\s+Situação:\s+(?P<situacao>Adjudicado e Homologado|Deserto e Homologado|Fracassado e Homologado)")
padrao_3 = (
    r"Adjucado e Homologado por CPF (?P<cpf_od>\*\*\*.\d{3}.\*\*\*-\*\d{1})\s+-\s+"
    r"(?P<ordenador_despesa>.+?)\s+para\s+"
    r"(?P<empresa>.+?)\s*,\s+CNPJ\s+"
    r"(?P<cnpj>\d{2}\s*\.\s*\d{3}\s*\.\s*\d{3}\s*/\s*\d{4}\s*-\s*\d{2}),\s+"
    r"melhor lance:\s*(?:[\d,]+%\s*\()?"
    r"R\$ (?P<melhor_lance>[\d,.]+)(?:\))?(?:,\s+"
    r"valor negociado: R\$ (?P<valor_negociado>[\d,.]+))?\s+Propostas do Item"
)
padrao_4 = (r"Proposta adjudicada.*? Marca/Fabricante:(?P<marca_fabricante>.*?) Modelo/versão:(?P<modelo_versao>.*?)(?=\d{2}/\d{2}/\d{4}|\s*Valor proposta:)")

def encontre_valor_ou_NA(item, chave, match=None):
    if match:
        return match.group(chave) if match and match.group(chave) else "N/A"
    return item.get(chave, 'N/A')

def extrair_uasg_e_pregao(conteudo: str, padrao_1: str, padrao_srp: str, padrao_objeto: str) -> dict:
    match = re.search(padrao_1, conteudo)
    match2 = re.search(padrao_srp, conteudo)
    match3 = re.search(padrao_objeto, conteudo)
    
    srp_valor = match2.group("srp") if match2 else "N/A"
    objeto_valor = match3.group("objeto") if match3 else "N/A"

    if match:
        return {
            "uasg": match.group("uasg"),
            "orgao_responsavel": match.group("orgao_responsavel"),
            "num_pregao": match.group("num_pregao"),
            "ano_pregao": match.group("ano_pregao"),
            "srp": srp_valor,
            "objeto": objeto_valor
        }
    return {}

def buscar_itens(conteudo: str, padrao_grupo2: str, padrao_item2: str) -> list:
    return list(re.finditer(padrao_grupo2, conteudo)) + list(re.finditer(padrao_item2, conteudo))

def ajuste_cnpj(cnpj: str) -> str:
    cnpj = re.sub(r'\s+', '', cnpj)
    return cnpj

def processar_item(match, conteudo: str, ultima_posicao_processada: int, padrao_3: str, padrao_4: str) -> dict:
    item = match.groupdict()
    match_3 = re.search(padrao_3, conteudo[ultima_posicao_processada:])
    match_4 = re.search(padrao_4, conteudo[ultima_posicao_processada:])
    
    if match_3:
        ultima_posicao_processada += match_3.end()
    item_num_convertido = int(item.get('item_num')) if item.get('item_num', 'N/A') != 'N/A' else 'N/A'
    item_data = {
        "item_num": item_num_convertido,
        "grupo": encontre_valor_ou_NA(item, 'grupo'),
        "valor_estimado": encontre_valor_ou_NA(item, 'valor'),
        "quantidade": encontre_valor_ou_NA(item, 'quantidade'),
        "unidade": encontre_valor_ou_NA(item, 'unidade'),
        "situacao": encontre_valor_ou_NA(item, 'situacao'),
        "melhor_lance": encontre_valor_ou_NA(item, 'melhor_lance', match_3),
        "valor_negociado": encontre_valor_ou_NA(item, 'valor_negociado', match_3),
        "ordenador_despesa": encontre_valor_ou_NA(item, 'ordenador_despesa', match_3),
        "empresa": encontre_valor_ou_NA(item, 'empresa', match_3),
        "cnpj": ajuste_cnpj(encontre_valor_ou_NA(item, 'cnpj', match_3)),
        "marca_fabricante": encontre_valor_ou_NA(item, 'marca_fabricante', match_4),
        "modelo_versao": encontre_valor_ou_NA(item, 'modelo_versao', match_4),
    }
    return item_data, ultima_posicao_processada

def process_cnpj_data(cnpj_dict):
    """Converter "valor_estimado", "melhor_lance", e "valor_negociado" para float se não for possível deverá pular"""
    for field in ["valor_estimado", "melhor_lance", "valor_negociado"]:
        if isinstance(cnpj_dict[field], str):
            try:
                cnpj_dict[field] = float(cnpj_dict[field].replace(".", "").replace(",", "."))
            except ValueError:
                cnpj_dict[field] = 'N/A'

    # Convert "quantidade" to integer if possible, otherwise keep as is
    try:
        cnpj_dict["quantidade"] = int(cnpj_dict["quantidade"])
    except ValueError:
        pass

    # Ensure valor_homologado_item_unitario is defined
    if cnpj_dict["valor_negociado"] in [None, "N/A", "", "none", "null"]:
        cnpj_dict["valor_homologado_item_unitario"] = cnpj_dict["melhor_lance"]
    else:
        cnpj_dict["valor_homologado_item_unitario"] = cnpj_dict["valor_negociado"]

    # Now perform the other calculations
    if cnpj_dict["valor_estimado"] != 'N/A' and cnpj_dict["valor_homologado_item_unitario"] != 'N/A':
        try:
            cnpj_dict["valor_estimado_total_do_item"] = cnpj_dict["quantidade"] * float(cnpj_dict["valor_estimado"])
            cnpj_dict["valor_homologado_total_item"] = cnpj_dict["quantidade"] * float(cnpj_dict["valor_homologado_item_unitario"])
            cnpj_dict["percentual_desconto"] = (1 - (float(cnpj_dict["valor_homologado_item_unitario"]) / float(cnpj_dict["valor_estimado"])))
        except ValueError:
            pass
            
    return cnpj_dict

def identificar_itens_e_grupos(conteudo: str, padrao_grupo2: str, padrao_item2: str, padrao_3: str, padrao_4: str, df: pd.DataFrame) -> list:
    itens_data = []
    itens = buscar_itens(conteudo, padrao_grupo2, padrao_item2)
    ultima_posicao_processada = 0

    for match in itens:
        item_data, ultima_posicao_processada = processar_item(match, conteudo, ultima_posicao_processada, padrao_3, padrao_4)
        
        item_data = process_cnpj_data(item_data)

        itens_data.append(item_data)

    return itens_data
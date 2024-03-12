    # @staticmethod
    # def load_data():
    #     contratos_path = Path(CONTRATOS_PATH)  # Certifique-se de que CONTRATOS_PATH é definido anteriormente
    #     novos_dados_path = Path(NOVOS_DADOS_PATH)
    #     adicionais_path = Path(ADICIONAIS_PATH)
    # colunas_necessarias = [
    # 'Número do instrumento', 'Tipo', 'Processo', 'NUP', 'Objeto', 'OM', 'Setor', 'Natureza Continuada', 'Comentários', 'Termo Aditivo'
    # ]
    #     contratos_data = pd.read_csv(contratos_path, usecols=colunas_contratos, dtype=str)
    #     novos_dados = pd.read_csv(novos_dados_path, usecols=colunas_necessarias, dtype=str)
    #     atualizar_dados_novos = pd.merge(contratos_data, novos_dados, on='Número do instrumento', how='left')
    #     print(atualizar_dados_novos) 
    #     atualizar_dados_novos.to_csv(adicionais_path, index=False)
    #     return atualizar_dados_novos
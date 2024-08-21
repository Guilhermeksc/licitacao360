import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilename

def verificar_duplicidade(nome_coluna):
    # Ocultar a janela principal do Tkinter
    Tk().withdraw()
    
    # Abrir janela de diálogo para o usuário escolher o arquivo
    arquivo_excel = askopenfilename(
        title="Selecione o arquivo Excel",
        filetypes=[("Arquivo Excel", "*.xlsx *.xls")]
    )
    
    if not arquivo_excel:
        print("Nenhum arquivo selecionado.")
        return
    
    # Carregar o arquivo Excel
    df = pd.read_excel(arquivo_excel)
    
    # Verificar duplicidades na coluna especificada
    duplicados = df[df.duplicated(subset=[nome_coluna], keep=False)]
    
    if not duplicados.empty:
        print(f"Contratos duplicados encontrados na coluna '{nome_coluna}':")
        print(duplicados[[nome_coluna]])
    else:
        print(f"Não há duplicidade na coluna '{nome_coluna}'.")

# Exemplo de uso
nome_coluna = 'numero_contrato'
verificar_duplicidade(nome_coluna)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
from pathlib import Path
import textwrap

# # Defina o caminho completo para o CSV (este código precisa ser idêntico ao do PyQt)
BASE_DIR = Path(__file__).resolve().parent
STREAMLIT_CSV = BASE_DIR / "dataframe_planejamento.csv"

# Carrega o DataFrame do arquivo CSV usando o caminho absoluto
df = pd.read_csv(STREAMLIT_CSV)

# Função para ajustar o texto do 'Objeto' para caber no espaço disponível
def wrap_text(text, width):
    return "\n".join(textwrap.wrap(text, width))

# Definir a ordem dos status (ajuste conforme necessário)
order = [
    'Planejamento', 'Consolidar Demandas', 'Montagem do Processo', 
    'Nota Técnica', 'AGU', 'Recomendações AGU', 
    'Pré-Publicação', 'Sessão Pública', 'Assinatura Contrato', 'Concluído'
]

# Garantir que a coluna 'Status' siga a ordem especificada
df['Status'] = pd.Categorical(df['Status'], categories=order, ordered=True)
df.sort_values('Status', inplace=True)

# Criar o gráfico empilhado
fig, ax = plt.subplots(figsize=(12, 8))

# Inicializar o acumulador de posições na pilha como float
bottom = pd.Series(0.0, index=order)  # Inicializa como float

# Empilhar processos
for i, row in df.iterrows():
    status_index = df['Status'].cat.categories.get_loc(row['Status'])
    ax.bar(status_index, 0.9, bottom=bottom[row['Status']], color='skyblue', edgecolor='black', width=0.8)
    
    # Adicionar texto do ID Processo e Objeto empilhados
    ax.text(status_index, bottom[row['Status']] + 0.45, f"{row['ID Processo']}", ha='center', va='center', color='black', fontsize=9, fontweight='bold')
    ax.text(status_index, bottom[row['Status']] + 0.15, wrap_text(f"{row['Objeto']}", 15), ha='center', va='center', color='black', fontsize=8)
    
    # Atualizar a posição para o próximo item na mesma pilha
    bottom[row['Status']] += 0.9  # Reduzir a altura de cada bloco empilhado

# Configurar título e rótulos do gráfico
ax.set_title('Processos por Status')
ax.set_xlabel('Status')
ax.set_ylabel('Número de Processos')

# Ajustar o eixo y para mostrar apenas números inteiros
ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

# Definir a altura mínima e ajustar o valor máximo conforme necessário
y_max = max(bottom.max(), 10)  # Define o máximo entre o valor necessário e 10
ax.set_ylim(0, y_max)

# Ajustar os rótulos do eixo x para melhor legibilidade
plt.xticks(ticks=range(len(order)), labels=order, rotation=0, ha='center')

# Ajustar layout
plt.tight_layout()

# Renderizar o gráfico no Streamlit
st.pyplot(fig)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
from pathlib import Path
import textwrap
import matplotlib.offsetbox as offsetbox

# Defina o caminho completo para o CSV
BASE_DIR = Path(__file__).resolve().parent
STREAMLIT_CSV = BASE_DIR / "dataframe_planejamento.csv"
PRIORIDADE_ICON_PATH = BASE_DIR / "prioridade.png"

# Carrega o DataFrame do arquivo CSV usando o caminho absoluto
df = pd.read_csv(STREAMLIT_CSV)

# Filtrar processos que não estão "Concluídos" e que não estão em "Planejamento"
df = df[(df['Status'] != 'Concluído') & (df['Status'] != 'Planejamento')]

# Função para ajustar o texto do 'Objeto' para caber no espaço disponível
def wrap_text(text, width):
    return "\n".join(textwrap.wrap(text, width))

# Definir a ordem dos status (ajuste conforme necessário)
order = [
    'Consolidar Demandas', 'Montagem do Processo', 
    'Nota Técnica', 'AGU', 'Recomendações AGU', 
    'Pré-Publicação', 'Sessão Pública', 'Assinatura Contrato'
]

# Garantir que a coluna 'Status' siga a ordem especificada
df['Status'] = pd.Categorical(df['Status'], categories=order, ordered=True)
df.sort_values('Status', inplace=True)

# Adicionar um slider vertical para definir o limite do eixo Y
y_max_slider = st.slider('Definir limite do eixo Y', min_value=5, max_value=20, step=5, value=10)

# Determinar a altura de cada bloco empilhado com base no valor do slider
block_height = y_max_slider / y_max_slider  # Mantém a altura proporcional ao valor do slider

# Criar o gráfico empilhado com uma largura maior
fig, ax = plt.subplots(figsize=(16, 8))  # Aumentado para 14 de largura

# Inicializar o acumulador de posições na pilha como float
bottom = pd.Series(0.0, index=order)  # Inicializa como float

# Tentar carregar o ícone de prioridade
if PRIORIDADE_ICON_PATH.exists():
    prioridade_icon = plt.imread(PRIORIDADE_ICON_PATH)
    print(f"Ícone de prioridade carregado com sucesso: {prioridade_icon.shape}")
else:
    st.warning(f"Ícone de prioridade não encontrado no caminho: {PRIORIDADE_ICON_PATH}")
    print(f"Ícone de prioridade não encontrado no caminho: {PRIORIDADE_ICON_PATH}")
    prioridade_icon = None

# Empilhar processos
for i, row in df.iterrows():
    status_index = df['Status'].cat.categories.get_loc(row['Status'])
    ax.bar(status_index, block_height, bottom=bottom[row['Status']], color='skyblue', edgecolor='black', width=0.9)
    
    # Adicionar texto do ID Processo e Objeto empilhados
    ax.text(status_index, bottom[row['Status']] + block_height / 2, f"{row['ID Processo']}", ha='center', va='center', color='black', fontsize=9, fontweight='bold')
    ax.text(status_index, bottom[row['Status']] + block_height * 0.1, wrap_text(f"{row['Objeto']}", 15), ha='center', va='center', color='black', fontsize=8)
    
    # Depuração: Verificar se a prioridade está sendo verificada
    print(f"Processo ID {row['ID Processo']} - Prioridade: {row.get('prioridade', False)}")
    
    # Adicionar ícone de prioridade se a coluna 'prioridade' for True e o ícone foi carregado
    if row.get('prioridade', False) and prioridade_icon is not None:
        print(f"Adicionando ícone de prioridade para o processo ID {row['ID Processo']}")
        icon_offsetbox = offsetbox.OffsetImage(prioridade_icon, zoom=0.5)  # Aumentado para 0.15
        icon_ab = offsetbox.AnnotationBbox(icon_offsetbox, (status_index, bottom[row['Status']] + block_height - 0.1),
                                           frameon=False, xybox=(-10, 10), xycoords='data', boxcoords="offset points")
        ax.add_artist(icon_ab)
    
    # Atualizar a posição para o próximo item na mesma pilha
    bottom[row['Status']] += block_height  # Incrementa a altura de cada bloco empilhado

# Configurar título e rótulos do gráfico
ax.set_title('Processos por Status')
ax.set_xlabel('Status')
ax.set_ylabel('Número de Processos')

# Ajustar o eixo y para mostrar apenas números inteiros
ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

# Ajustar o valor máximo do eixo Y conforme o valor do slider
ax.set_ylim(0, y_max_slider)

# Ajustar os rótulos do eixo x para melhor legibilidade, com inclinação
plt.xticks(ticks=range(len(order)), labels=order, rotation=45, ha='right')

# Ajustar layout
plt.tight_layout()

# Renderizar o gráfico no Streamlit
st.pyplot(fig)

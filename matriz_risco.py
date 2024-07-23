import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

# Dados dos riscos
data = {
    'Risco': ['R-01', 'R-02', 'R-03', 'R-04', 'R-05', 'R-06', 'R-07', 'R-08', 'R-09', 'R-10', 'R-11', 'R-12', 'R-13', 'R-14', 'R-15', 'R-16', 'R-17'],
    'Probabilidade': [3, 3, 2, 2, 3, 3, 2, 2, 3, 3, 4, 2, 3, 2, 2, 3, 4],
    'Impacto': [2, 5, 3, 3, 4, 4, 2, 5, 4, 4, 4, 5, 4, 3, 4, 4, 4]
}

df = pd.DataFrame(data)

# Ajustar a matriz de risco para garantir que todas as combinações possíveis estejam presentes
full_range = [(i, j) for i in range(1, 6) for j in range(1, 6)]
full_df = pd.DataFrame(full_range, columns=['Probabilidade', 'Impacto'])
merged_df = pd.merge(full_df, df, on=['Probabilidade', 'Impacto'], how='left')

# Função para concatenar riscos, lidando com valores NaN
def agg_func(x):
    return ', '.join([str(i) for i in x if not pd.isna(i)])

pivot_table = merged_df.pivot_table(values='Risco', index='Probabilidade', columns='Impacto', aggfunc=agg_func, fill_value='')

# Função para adicionar quebras de linha a cada 4 riscos
def format_risks(risks):
    risk_list = risks.split(', ')
    formatted_risks = '\n'.join([', '.join(risk_list[i:i+4]) for i in range(0, len(risk_list), 4)])
    return formatted_risks

# Aplicar a função de formatação aos riscos
for col in pivot_table.columns:
    pivot_table[col] = pivot_table[col].apply(format_risks)

# Definir a matriz de calor fixa
heat_map_data = np.array([
    [5, 6, 7, 8, 9],
    [4, 5, 6, 7, 8],
    [3, 4, 5, 6, 7],
    [2, 3, 4, 5, 6],
    [1, 2, 3, 4, 5]
])

# Definir a paleta de cores personalizada
colors = [
    (0, "green"),       # Verde para valores 1
    (0.15, "greenyellow"),  # Verde amarelado para valores 2
    (0.35, "yellow"),    # Amarelo para valores 3
    (0.55, "orange"),   # Laranja para valores 4
    (0.75, "orangered"),  # Laranja avermelhado para valores 5
    (1, "red")          # Vermelho para valores 6 e acima
]

custom_cmap = LinearSegmentedColormap.from_list('custom_cmap', colors)

# Configurar o gráfico de calor com a paleta de cores personalizada
fig, ax = plt.subplots(figsize=(12, 8))
heatmap = sns.heatmap(heat_map_data, cmap=custom_cmap, cbar=True, linewidths=.5, ax=ax, annot=pivot_table, fmt="", annot_kws={"size": 10})

# Ajustar os eixos e rótulos
ax.set_title('Mapa de Calor dos Riscos Identificados')
ax.set_xlabel('Impacto')
ax.set_ylabel('Probabilidade')
ax.set_yticklabels(['Praticamente certo', 'Muito provável', 'Provável', 'Pouco provável', 'Raro'], rotation=0)
ax.set_xticklabels(['Muito baixo', 'Baixo', 'Médio', 'Alto', 'Muito alto'], rotation=45, ha="right")

# Mostrar o gráfico
plt.tight_layout()
plt.show()

# Salvar o gráfico como imagem
plt.savefig('/mnt/data/mapa_de_calor_riscos_customizado_v5.png')

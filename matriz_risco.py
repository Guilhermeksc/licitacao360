import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

def create_data():
    data = {
        'Risco': ['R-01', 'R-02', 'R-03', 'R-04', 'R-05', 'R-06', 'R-07', 'R-08', 'R-09', 'R-10', 'R-11', 'R-12', 'R-13', 'R-14', 'R-15', 'R-16', 'R-17'],
        'Probabilidade': [3, 3, 2, 2, 3, 3, 2, 2, 3, 3, 4, 2, 3, 2, 2, 3, 4],
        'Impacto': [2, 5, 3, 3, 4, 4, 2, 5, 4, 4, 4, 5, 4, 3, 4, 4, 4]
    }
    return pd.DataFrame(data)

def adjust_risk_matrix(df):
    full_range = [(i, j) for i in range(1, 6) for j in range(1, 6)]
    full_df = pd.DataFrame(full_range, columns=['Probabilidade', 'Impacto'])
    merged_df = pd.merge(full_df, df, on=['Probabilidade', 'Impacto'], how='left')
    return merged_df

def agg_func(x):
    return ', '.join([str(i) for i in x if not pd.isna(i)])

def format_risks(risks):
    risk_list = risks.split(', ')
    formatted_risks = '\n'.join([', '.join(risk_list[i:i+3]) for i in range(0, len(risk_list), 3)])
    return formatted_risks

def create_pivot_table(merged_df):
    pivot_table = merged_df.pivot_table(values='Risco', index='Probabilidade', columns='Impacto', aggfunc=agg_func, fill_value='')
    for col in pivot_table.columns:
        pivot_table[col] = pivot_table[col].apply(format_risks)
    return pivot_table

def create_custom_cmap():
    colors = [
        (0, "green"),       # Verde para valores 1
        (0.10, "greenyellow"),  # Verde amarelado para valores 2
        (0.25, "yellow"),    # Amarelo para valores 3
        (0.50, "orange"),   # Laranja para valores 5
        (0.75, "orangered"),  # Laranja avermelhado para valores 7
        (0.90, "red"),          # Vermelho para valores 9 e acima
        (1, "darkred")          # Vermelho para valores 10
    ]
    return LinearSegmentedColormap.from_list('custom_cmap', colors)

def plot_heatmap(heat_map_data, pivot_table, custom_cmap):
    fig, ax = plt.subplots(figsize=(16, 4))  # Ajustando o tamanho para ser mais largo e achatado
    heatmap = sns.heatmap(heat_map_data, cmap=custom_cmap, cbar=True, linewidths=.5, ax=ax, annot=pivot_table, fmt="", annot_kws={"size": 14}, square=False)  # Definido square=False

    # Definindo rótulos customizados
    yticklabels = ['5             \nPraticamente certo', '4             \n   Muito provável   ', '3             \n      Provável        ', '2             \n    Pouco provável  ', '1             \n      Raro          ']
    xticklabels = ['1\nMuito baixo', '2\nBaixo', '3\nMédio', '4\nAlto', '5\nMuito alto']
    
    ax.set_yticklabels(yticklabels, rotation=0)
    ax.set_xticklabels(xticklabels, rotation=0)
    
    ax.set_title('Mapa de Calor dos Riscos Identificados', fontsize=14, weight='bold')
    ax.set_xlabel('Impacto', fontsize=12, weight='bold')
    ax.set_ylabel('Probabilidade', fontsize=12, weight='bold')

    
    plt.tight_layout()
    plt.show()

def main():
    df = create_data()
    merged_df = adjust_risk_matrix(df)
    pivot_table = create_pivot_table(merged_df)
    custom_cmap = create_custom_cmap()
    heat_map_data = np.array([
        [8, 12, 15, 20, 25],
        [5, 9, 13, 15, 20],
        [3, 6, 10, 13, 15],
        [2, 3, 6, 9, 12],
        [1, 2, 3, 5, 8]
    ])
    plot_heatmap(heat_map_data, pivot_table, custom_cmap)

if __name__ == "__main__":
    main()

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
import os

class HeatmapGenerator:
    def __init__(self, dados):
        self.dados = dados
        self.data = self.create_data()

    def create_data(self):
        df = pd.DataFrame({
            'Risco': self.dados['Risco'],
            'Probabilidade': self.dados['P'],
            'Impacto': self.dados['I']
        })
        return df

    def adjust_risk_matrix(self, df):
        full_range = [(i, j) for i in range(1, 6) for j in range(1, 6)]
        full_df = pd.DataFrame(full_range, columns=['Probabilidade', 'Impacto'])
        merged_df = pd.merge(full_df, df, on=['Probabilidade', 'Impacto'], how='left')
        return merged_df

    @staticmethod
    def agg_func(x):
        return ', '.join([str(i) for i in x if not pd.isna(i)])

    @staticmethod
    def format_risks(risks):
        risk_list = risks.split(', ')
        formatted_risks = '\n'.join([', '.join(risk_list[i:i+4]) for i in range(0, len(risk_list), 4)])
        return formatted_risks

    def create_pivot_table(self, merged_df):
        pivot_table = merged_df.pivot_table(values='Risco', index='Probabilidade', columns='Impacto', aggfunc=self.agg_func, fill_value='')
        for col in pivot_table.columns:
            pivot_table[col] = pivot_table[col].apply(self.format_risks)
        return pivot_table

    @staticmethod
    def create_custom_cmap():
        colors = [
            (0, "#9FEB2B"),       # Verde para valores 1
            (0.04, "greenyellow"),  # Verde amarelado para valores 2
            (0.25, "yellow"),    # Amarelo para valores 3
            (0.50, "yellow"),    # Amarelo para valores 3
            (0.60, "orange"),   # Laranja para valores 5
            (0.85, "orangered"),  # Laranja avermelhado para valores 7
            (1, "red")          # Vermelho para valores 10
        ]
        return LinearSegmentedColormap.from_list('custom_cmap', colors)

    def generate_heatmap(self):
        merged_df = self.adjust_risk_matrix(self.data)
        pivot_table = self.create_pivot_table(merged_df)
        custom_cmap = self.create_custom_cmap()
        heat_map_data = np.array([
            [1, 2, 3, 5, 13],
            [2, 3, 5, 13, 15],
            [3, 5, 13, 15, 18],
            [5, 13, 15, 18, 20],
            [13, 15, 18, 20, 25]
        ])
        
        # Plotar o heatmap e salvar a imagem
        fig, ax = plt.subplots(figsize=(16, 4))
        sns.heatmap(heat_map_data[::-1], cmap=custom_cmap, cbar=True, linewidths=.5, ax=ax, annot=pivot_table[::-1], fmt="", annot_kws={"size": 14}, square=False)
        
        yticklabels = ['1             \n      Raro          ', 
                       '2             \n    Pouco provável  ',
                       '3             \n      Provável        ',
                       '4             \n   Muito provável   ',
                       '5             \nPraticamente certo']
        xticklabels = ['1\nMuito baixo', '2\nBaixo', '3\nMédio', '4\nAlto', '5\nMuito alto']

        ax.set_yticklabels(yticklabels[::-1], rotation=0)
        ax.set_xticklabels(xticklabels, rotation=0)

        ax.set_title('Mapa de Calor dos Riscos Identificados', fontsize=14, weight='bold')
        ax.set_xlabel('Impacto', fontsize=12, weight='bold')
        ax.set_ylabel('Probabilidade', fontsize=12, weight='bold')

        plt.tight_layout()
        
        # Salvar a imagem ajustada ao conteúdo com maior resolução
        image_path = "heatmap.png"
        plt.savefig(image_path, bbox_inches='tight', dpi=300)
        plt.close(fig)
        
        return image_path


if __name__ == "__main__":
    heatmap_generator = HeatmapGenerator()
    heatmap_generator.generate_heatmap()

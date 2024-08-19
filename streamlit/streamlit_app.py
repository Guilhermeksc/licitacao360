import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
from pathlib import Path

# Defina o caminho completo para o CSV (este código precisa ser idêntico ao do PyQt)
BASE_DIR = Path(__file__).resolve().parent
STREAMLIT_CSV = BASE_DIR / "current_dataframe.csv"

# Configurar o tema do seaborn
sns.set_theme(style="whitegrid")

# Carrega o DataFrame do arquivo CSV usando o caminho absoluto
df = pd.read_csv(STREAMLIT_CSV)

def formatar_brl(valor):
    try:
        if valor is None or pd.isna(valor):
            return "R$ 0,00"  # Retorna string formatada se não for um valor válido
        valor_formatado = f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return valor_formatado
    except Exception as e:
        print(f"Erro ao formatar valor: {valor} - Erro: {str(e)}")
        return "R$ 0,00"
    
def calcular_percentual_desconto_total(df):
    df_valid = df.dropna(subset=['valor_estimado_total_do_item', 'valor_homologado_total_item'])
    total_estimado = df_valid['valor_estimado_total_do_item'].sum()
    total_homologado = df_valid['valor_homologado_total_item'].sum()

    if total_estimado > 0:
        percentual_desconto = (1 - (total_homologado / total_estimado)) * 100
    else:
        percentual_desconto = 0
    
    return percentual_desconto, total_estimado, total_homologado

# Função para o controle deslizante
def selecionar_num_items():
    return st.slider('Selecione o número de itens para exibir', min_value=1, max_value=30, value=10, step=1)

# Calcular o percentual de desconto total
percentual_desconto, total_estimado, total_homologado = calcular_percentual_desconto_total(df)

# Formatar os valores
total_estimado_fmt = formatar_brl(total_estimado)
total_homologado_fmt = formatar_brl(total_homologado)

# Exibir título do dashboard
st.title("Dashboard de Licitações")

# Exibir o cálculo detalhado
st.markdown("### Cálculo do Percentual de Desconto")
st.markdown("A fórmula utilizada para calcular o percentual de desconto é:")
st.latex(r'''
\text{Percentual de Desconto} = \left(1 - \frac{\text{Total Homologado}}{\text{Total Estimado}}\right) \times 100
''')
# Substituindo pelos valores obtidos sem formatação
# Exibir os valores formatados em BRL separadamente
st.markdown(f"Total Homologado: {total_homologado_fmt}")
st.markdown(f"Total Estimado: {total_estimado_fmt}")

# Exibir o resultado do cálculo
st.markdown(f"### Média do Percentual de Desconto: **{percentual_desconto:.2f}%**")


def grafico_percentual_desconto(df, num_items):
    # Preparar os dados
    df_analysis = df[['item_num', 'valor_estimado', 'valor_homologado_item_unitario']].dropna()
    df_analysis['valor_estimado'] = pd.to_numeric(df_analysis['valor_estimado'], errors='coerce')
    df_analysis['valor_homologado_item_unitario'] = pd.to_numeric(df_analysis['valor_homologado_item_unitario'], errors='coerce')
    df_analysis.dropna(inplace=True)
    df_analysis['economia'] = df_analysis['valor_estimado'] - df_analysis['valor_homologado_item_unitario']
    df_analysis['percentual_desconto'] = (df_analysis['economia'] / df_analysis['valor_estimado']) * 100
    df_top_desconto = df_analysis.nlargest(num_items, 'percentual_desconto').sort_index()

    fig, ax1 = plt.subplots(figsize=(12, 8))
    bar_width = 0.35
    index = np.arange(len(df_top_desconto))

    bars1 = ax1.bar(index - bar_width/2, df_top_desconto['valor_estimado'], bar_width, label='Valor Estimado', color='navy')
    bars2 = ax1.bar(index + bar_width/2, df_top_desconto['valor_homologado_item_unitario'], bar_width, label='Valor Homologado', color='darkorange')

    for bar in bars1.patches:
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'R$ {bar.get_height():,.0f}'.replace(',', '.').replace('.', ','),
                 ha='center', va='bottom', fontsize=14, color='navy', fontweight='bold')

    for bar in bars2.patches:
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'R$ {bar.get_height():,.0f}'.replace(',', '.').replace('.', ','),
                 ha='center', va='bottom', fontsize=14, color='darkorange', fontweight='bold')

    ax1.set_xlabel('Número do Item')
    ax1.set_ylabel('Valores em Reais')
    ax1.set_title(f'Top {num_items} Maiores Percentuais de Desconto, Valores Estimados e Valores Homologados por Item')
    ax1.set_xticks(index)
    ax1.set_xticklabels(df_top_desconto['item_num'])
    ax1.legend(loc='upper left')

    # Desativar o grid de ax2
    ax2 = ax1.twinx()
    ax2.grid(False)  # Desativar o grid de ax2
    ax2.plot(index, df_top_desconto['percentual_desconto'], 'r-o', label='Percentual de Desconto', linewidth=2, markersize=8)
    ax2.set_ylabel('Percentual de Desconto (%)')
    ax2.legend(loc='upper right')

    for i, txt in enumerate(df_top_desconto['percentual_desconto']):
        ax2.annotate(f'{txt:.1f}%', (index[i], df_top_desconto['percentual_desconto'].iloc[i]), textcoords="offset points", xytext=(0,10), ha='center', color='darkred', fontsize=14, fontweight='bold')

    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

# Distribuição do Percentual de Desconto
def grafico_dispersao(df, num_items, media_percentual_desconto):
    df_analysis = df[['item_num', 'percentual_desconto']].dropna()

    plt.figure(figsize=(10, 6))
    plt.scatter(df_analysis['item_num'], df_analysis['percentual_desconto'], color='blue', label='Percentual de Desconto')

    # Adicionar linha tracejada verde em 30%
    plt.axhline(y=30, color='green', linestyle='--', label='30% de Desconto')
    
    # Adicionar linha tracejada vermelha na média do percentual de desconto
    plt.axhline(y=media_percentual_desconto, color='red', linestyle='--', label=f'Média ({media_percentual_desconto:.2f}%)')

    df_top10_desconto = df_analysis.nlargest(num_items, 'percentual_desconto')
    for i, row in df_top10_desconto.iterrows():
        percentual_desconto = row['percentual_desconto']
        item_num = int(row['item_num'])  # Remover o '.0' ao transformar para int
        plt.annotate(f"Item: {item_num}", (item_num, percentual_desconto),
                     textcoords="offset points", xytext=(5, 5), ha='center', color='red', fontsize=10, fontweight='bold')

    plt.xlabel('Número do Item')
    plt.ylabel('Percentual de Desconto (%)')
    plt.title('Distribuição Percentual de Desconto por Item')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()
    st.pyplot(plt)

# Gráfico de Pizza - Quantidade por Situação
def grafico_situacao(df):
    # Substituir valores nulos ou ausentes por "Outros"
    df['situacao'] = df['situacao'].fillna('Outros')

    # Agrupar os dados corretamente usando 'item_num' para contagem única
    df_situacao = df.groupby('situacao')['item_num'].nunique().reset_index()
    df_situacao.columns = ['situacao', 'quantidade']

    # Definir as cores para cada situação específica
    cores = {
        'Adjudicado e Homologado': 'green',
        'Fracassado e Homologado': 'yellow',
        'Deserto e Homologado': 'orange',
        'Cancelado e Homologado': 'red',
        'Anulado e Homologado': 'purple',
        'Outros': 'gray'
    }

    # Criar o gráfico de pizza interativo com Plotly
    fig = px.pie(df_situacao, values='quantidade', names='situacao',
                 color='situacao', color_discrete_map=cores,
                 title='Distribuição por Situação')

    # Exibir o gráfico interativo
    st.plotly_chart(fig, use_container_width=True)

    # Permitir que o usuário selecione a situação da tabela correspondente
    selected_situacao = st.selectbox("Selecione uma situação para ver os itens correspondentes:", df_situacao['situacao'].unique())
    
    if selected_situacao:
        st.write(f"Itens na situação **{selected_situacao}**:")
        st.dataframe(df[df['situacao'] == selected_situacao][['item_num', 'valor_estimado', 'valor_homologado_item_unitario', 'percentual_desconto']])

st.subheader("Itens por Empresa e Número de Ata")
def grafico_treeview_empresa(df):
    # Preencher valores ausentes em 'empresa' e 'numero_ata'
    df['empresa'] = df['empresa'].fillna('Empresa Desconhecida')
    df['numero_ata'] = df['numero_ata'].fillna('Sem Ata')

    # Agrupar os dados por 'empresa', 'numero_ata' e contar os 'item_num'
    df_grouped = df.groupby(['empresa', 'numero_ata', 'item_num']).size().reset_index(name='count')

    # Criar o gráfico treemap
    fig = px.treemap(df_grouped, path=['empresa', 'numero_ata', 'item_num'], values='count',
                     title='Hierarquia de Itens por Empresa e Número de Ata')

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)
    
# Chama o slider e gera os gráficos
num_items = selecionar_num_items()

st.subheader("Maiores Percentuais de Desconto")
grafico_percentual_desconto(df, num_items)

st.subheader("Distribuição do Percentual de Desconto")
grafico_dispersao(df, num_items, percentual_desconto)

st.subheader("Quantidade de Itens por Situação")
grafico_situacao(df)
st.subheader("Itens por Empresa e Número de Ata")
grafico_treeview_empresa(df)
# Exibe o DataFrame no Streamlit
st.subheader("Tabela Atual")
st.dataframe(df)
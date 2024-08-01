import pandas as pd
import matplotlib.pyplot as plt
import os
import textwrap
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# Definir o caminho base
base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, 'controle_processos.xlsx')
icon_path = os.path.join(base_path, 'target.png')  # Caminho do ícone

# Verificar se o arquivo de ícone existe
if not os.path.exists(icon_path):
    raise FileNotFoundError(f"Ícone não encontrado no caminho: {icon_path}")

# Carregar o arquivo Excel
df = pd.read_excel(file_path)

# Filtrar processos para remover as fases "Planejamento" e "Setor Responsável"
df = df[~df['Status'].isin(['Planejamento', 'Setor Responsável'])]

# Preencher valores NaN na coluna 'Prioridade' com 'Normal' sem usar inplace=True
df['Prioridade'] = df['Prioridade'].fillna('Normal')

# Definir a ordem dos status, com 'Concluído' sendo o último e incluindo quebras de linha
order = [
    'IRP', 'Montagem\ndo Processo', 'Nota\nTécnica', 'AGU', 'Recomendações\nAGU', 
    'Pré-\nPublicação', 'Impugnado', 'Sessão\nPública', 'Assinatura\nContrato', 'Concluído'
]

# Renomear os status no DataFrame para incluir quebras de linha
df['Status'] = df['Status'].replace({
    'Montagem do Processo': 'Montagem\ndo Processo',
    'Nota Técnica': 'Nota\nTécnica',
    'Recomendações AGU': 'Recomendações\nAGU',
    'Pré-Publicação': 'Pré-\nPublicação',
    'Sessão Pública': 'Sessão\nPública',
    'Assinatura Contrato': 'Assinatura\nContrato'
})

# Garantir que a coluna 'Status' siga a ordem especificada
df['Status'] = pd.Categorical(df['Status'], categories=order, ordered=True)
df.sort_values('Status', inplace=True)

# Criar um mapa de cores para destacar 'Prioritário'
colors = df['Prioridade'].map({'Prioritário': 'red', 'Normal': 'blue'})

# Função para ajustar o texto do 'Objeto' para caber no espaço disponível
def wrap_text(text, width):
    return "\n".join(textwrap.wrap(text, width))

# Função para adicionar a imagem do ícone
def add_icon(ax, x, y, icon_path, offset=-0.15):
    print(f"Adicionando ícone em: Status={x}, Posição={y}")
    try:
        icon = plt.imread(icon_path)
        print(f"Ícone carregado: {icon.shape}")
        imagebox = OffsetImage(icon, zoom=0.1)  # Ajustar o zoom conforme necessário
        ab = AnnotationBbox(imagebox, (x + offset, y), frameon=False)
        ax.add_artist(ab)
    except FileNotFoundError:
        print(f"Ícone não encontrado no caminho: {icon_path}")

# Plotar os dados com IDs de processo e objetos empilhados
fig, ax = plt.subplots(figsize=(12, 8))

# Empilhar processos sem muito espaço
bottom = pd.Series(0, index=order)
icon_positions = []  # Para armazenar as posições dos ícones
for i, row in df.iterrows():
    status_index = df['Status'].cat.categories.get_loc(row['Status'])
    print(f"Status: {row['Status']}, Index: {status_index}")
    ax.bar(status_index, 1, bottom=bottom[row['Status']], color=colors[i], edgecolor='black')
    ax.text(status_index, bottom[row['Status']] + 0.75, f"{row['ID Processo']}", ha='center', va='center', color='white', fontsize=10, fontweight='bold')
    ax.text(status_index, bottom[row['Status']] + 0.25, wrap_text(f"{row['Objeto']}", 15), ha='center', va='center', color='white', fontsize=8)
    if row['Prioridade'] == 'Prioritário':
        icon_positions.append((status_index, bottom[row['Status']] + 1))
    bottom[row['Status']] += 1

# Adicionar os ícones após a plotagem dos itens
for pos in icon_positions:
    add_icon(ax, pos[0], pos[1], icon_path)

# Configurar título e rótulos do gráfico
ax.set_title('Processos por Status com Destaque para Prioritários')
ax.set_xlabel('Status')
ax.set_ylabel('Número de Processos')

# Ajustar os rótulos do eixo x para melhor legibilidade
plt.xticks(ticks=range(len(order)), labels=order, rotation=0, ha='center')

# Exibir o gráfico
plt.tight_layout()
plt.show()

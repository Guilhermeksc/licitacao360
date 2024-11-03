import os
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, QFileDialog
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patheffects as pe
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch
from diretorios import ICONS_DIR

class GraficTableDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gráficos Dispensa Eletrônica")
        self.setFixedSize(1200, 600)
        icon_confirm = QIcon(str(ICONS_DIR / "performance.png"))
        self.setWindowIcon(icon_confirm)

        # Layout principal horizontal
        main_layout = QHBoxLayout(self)

        # Layout vertical para os botões (lado esquerdo)
        buttons_layout = QVBoxLayout()
        self.create_buttons(buttons_layout)

        # Frame para separação visual
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.VLine)
        frame.setFrameShadow(QFrame.Shadow.Sunken)
        buttons_layout.addWidget(frame)

        # Adiciona o layout de botões ao layout principal
        main_layout.addLayout(buttons_layout)

        # Área para gráficos (lado direito)
        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)  # Subplot inicial para os gráficos

        # Chama a função para gerar o gráfico automaticamente
        self.infografico_dispensa_eletronica()

    def create_buttons(self, layout):
        # Botão para gerar gráfico de pizza
        btn_grafico = QPushButton("Gráfico de Pizza", self)
        btn_grafico.setIcon(QIcon(str(self.parent().icons_dir / "complete_table.png")))
        btn_grafico.setIconSize(QSize(30, 30))
        btn_grafico.clicked.connect(self.infografico_dispensa_eletronica)
        layout.addWidget(btn_grafico)

        # Botão para gerar gráfico de combinações
        btn_combinacoes = QPushButton("Gráfico de Combinações", self)
        btn_combinacoes.setIcon(QIcon(str(self.parent().icons_dir / "combination_table.png")))
        btn_combinacoes.setIconSize(QSize(30, 30))
        btn_combinacoes.clicked.connect(self.grafico_combinacoes)
        layout.addWidget(btn_combinacoes)

        # Botão para salvar a imagem
        btn_salvar = QPushButton("Salvar Imagem", self)
        btn_salvar.setIcon(QIcon(str(ICONS_DIR / "save.png")))
        btn_salvar.setIconSize(QSize(30, 30))
        btn_salvar.clicked.connect(self.salvar_imagem)
        layout.addWidget(btn_salvar)

        # Botão para copiar a imagem para a área de transferência
        btn_copiar = QPushButton("Copiar Imagem", self)
        btn_copiar.setIcon(QIcon(str(ICONS_DIR / "copy.png")))
        btn_copiar.setIconSize(QSize(30, 30))
        btn_copiar.clicked.connect(self.copiar_para_clipboard)
        layout.addWidget(btn_copiar)

    def infografico_dispensa_eletronica(self):
        # Limpa a figura e cria um novo eixo
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        # Obtém os dados do modelo para gerar o gráfico
        model = self.parent().model
        df = self.model_to_dataframe(model)
        
        # Gera um gráfico de pizza com os dados de 'Status'
        status_counts = df['Status'].value_counts()

        # Definir a ordem desejada
        ordem_desejada = ['Planejamento', 'Aprovado', 'Sessão Pública', 'Homologado', 'Empenhado', 'Concluído', 'Arquivado']
        status_counts = status_counts.reindex(ordem_desejada).fillna(0)

        total_processos = int(status_counts.sum())

        # Paleta de cores personalizada
        colors = plt.cm.Set1(range(len(status_counts)))
        # colors = plt.cm.Pastel1(range(len(status_counts)))
        # Set1: Uma paleta de cores brilhantes e distintas.
        # Set2: Uma paleta de cores suaves.
        # Set3: Uma paleta de cores suaves e variadas.
        # Accent: Uma paleta com cores vibrantes e contrastantes.
        # Dark2: Uma paleta com cores escuras e bem definidas.
        # Paired: Uma paleta com pares de cores relacionadas.
        # Gera os rótulos no formato desejado: "{Status} - {número} ({percentual})"
        labels = [f"{status} - {int(count)}" for status, count in zip(status_counts.index, status_counts)]

        # Gráfico de pizza com sombras
        wedges, texts = self.ax.pie(
            status_counts, 
            labels=labels, 
            startangle=140, 
            colors=colors, 
            wedgeprops=dict(width=1, edgecolor='w'),  # Diminuindo o círculo branco interno
            pctdistance=0.85  # Distância dos rótulos percentuais para a borda externa
        )

        # Configurações de estilo para os textos do gráfico
        for text in texts:
            text.set_color('black')
            text.set_fontsize(10)

        # Exibe o "Total de Processos" no lugar do título
        self.ax.set_title(f"Total de Processos: {total_processos}", fontsize=14, fontweight='bold')

        # Criação de uma legenda personalizada mais à direita, sem título
        patches = [
            Patch(
                color=colors[i],
                label=f"{status_counts.index[i]} - {int(status_counts.iloc[i])} ({status_counts.iloc[i] / total_processos * 100:.1f}%)"
            )
            for i in range(len(status_counts))
        ]
        self.ax.legend(handles=patches, loc='lower right', bbox_to_anchor=(1.60, 0.80), fontsize=10)

        self.canvas.draw()
            
    def grafico_combinacoes(self):
        # Limpa a figura e cria um novo eixo
        self.figure.clear()

        # Obtém os dados do modelo para gerar o gráfico
        model = self.parent().model
        df = self.model_to_dataframe(model)

        # Filtra os dados pelos status especificados
        status_interessantes = ['Aprovado', 'Sessão Pública', 'Homologado']
        df_filtrado = df[df['Status'].isin(status_interessantes)]

        # Dados para o gráfico de combinações
        combinacoes = {status: [] for status in status_interessantes}

        # Preparando os dados para o gráfico
        for status in status_interessantes:
            df_status = df_filtrado[df_filtrado['Status'] == status]

            for _, row in df_status.iterrows():
                id_processo = row['ID Processo']
                objeto = row['Objeto']
                valor_total = row['valor_total']

                combinacao = {
                    'ID Processo': id_processo,
                    'Objeto': objeto,
                    'valor_total': valor_total
                }
                combinacoes[status].append(combinacao)

        # Definir caminhos de ícones para cada status
        icons_paths = {
            'Aprovado': str(ICONS_DIR / "aproved.png"),
            'Sessão Pública': str(ICONS_DIR / "session.png"),
            'Homologado': str(ICONS_DIR / "deal.png")
        }

        # Configurar o número de colunas e gráficos
        num_colunas = len(status_interessantes)
        max_items_por_coluna = 12  # Limite de itens por coluna antes de quebrar

        # Criar subplots dinamicamente
        for i, status in enumerate(status_interessantes):
            ax = self.figure.add_subplot(1, num_colunas, i + 1)

            data = combinacoes[status]

            # Se houver mais de 8 itens, dividimos a coluna em subcolunas
            if len(data) > max_items_por_coluna:
                subcol_data = [data[i:i + max_items_por_coluna] for i in range(0, len(data), max_items_por_coluna)]
            else:
                subcol_data = [data]

            # Configurar o gráfico para cada subcoluna
            for sub_idx, sub_data in enumerate(subcol_data):
                # Aumentar o deslocamento entre subcolunas
                x_base = sub_idx * 2.65  # Ajustar a posição x base para cada subcoluna com espaçamento maior

                # Definir um fator de espaçamento para os itens
                spacing_factor = 1.5  # Fator de espaçamento para aumentar a distância entre itens

                # Posições y ajustadas para incluir espaçamento extra
                y_positions = [y * spacing_factor for y in range(len(sub_data))]

                # Adicionar cada item no gráfico
                for y, combinacao in zip(y_positions, sub_data):
                    # Ajustar a posição de texto
                    ax.text(
                        x_base,
                        y,
                        combinacao['ID Processo'],
                        ha='center',
                        va='center',
                        fontsize=10,
                        fontweight='bold',
                        color='black'
                    )
                    ax.text(
                        x_base,
                        y - 0.5,
                        combinacao['Objeto'],
                        ha='center',
                        va='center',
                        fontsize=8,
                        color='black',
                        fontstyle='italic'
                    )
                    ax.text(
                        x_base,
                        y - 0.9,
                        combinacao['valor_total'],
                        ha='center',
                        va='center',
                        fontsize=8,
                        color='darkred',
                        fontweight='bold'
                    )

                    # Adicionar uma linha discreta abaixo de cada combinação
                    ax.hlines(
                        y - 1.1,  # Posição da linha logo abaixo da última linha de texto
                        x_base - 0.4,  # Início da linha (ajustar conforme necessário)
                        x_base + 0.4,  # Fim da linha (ajustar conforme necessário)
                        color='gray',  # Cor da linha
                        linestyle='--',  # Estilo da linha (tracejada)
                        linewidth=0.8,  # Espessura da linha
                        alpha=0.7  # Transparência da linha para ser discreta
                    )
                    
            # Calcular a posição x central para a linha vertical
            num_subcolunas = len(subcol_data)
            central_x = (num_subcolunas - 1) * 2.5 / 2  # Centralizando com base na posição das subcolunas

            # Adicionar uma linha bem centralizada no status com cor lightblue
            ax.axvline(x=central_x, color='lightblue', linestyle='--', linewidth=1)

            # Adicionar o ícone ao lado do título
            icon_path = icons_paths[status]  # Usar o caminho correto do ícone
            icon_image = plt.imread(icon_path)  # Carregar imagem usando Matplotlib

            # OffsetImage para adicionar o ícone ao lado do título
            imagebox = OffsetImage(icon_image, zoom=0.5)  # Ajuste o zoom conforme necessário para o tamanho do ícone
            # Calcular a posição para colocar o ícone ao lado do título
            title_x_pos = 0.5  # Posição x do título centralizado
            icon_x_pos = title_x_pos - 0.50  # Posição x do ícone, ajustada para ficar ao lado do título
            icon_y_pos = 1.0  # Posição y do título no topo do gráfico
            ab = AnnotationBbox(imagebox, (icon_x_pos, icon_y_pos), frameon=False, xycoords='axes fraction')
            ax.add_artist(ab)

            # Ajustar a estética do gráfico
            ax.set_title(status, fontsize=14, fontweight='bold', loc='center')
            ax.set_xlim(-1, (num_subcolunas - 1) * 2.5 + 1)  # Definir limites x para cada status
            ax.set_ylim(-1, max(len(data), max_items_por_coluna) * spacing_factor)  # Ajustar o limite y com o fator de espaçamento

            # Remover eixos e bordas completamente
            ax.axis('off')
            ax.set_frame_on(False)  # Remove o quadro em volta dos subplots

        # Ajustar o espaçamento entre subplots para remover margens e espaços extras
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0.2)

        self.canvas.draw()

    def salvar_imagem(self):
        """Salva a imagem gerada em um local selecionado pelo usuário."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Imagem", "", "PNG Files (*.png);;All Files (*)")
        if file_path:
            self.figure.savefig(file_path)
            print(f"Imagem salva em: {file_path}")

    def salvar_imagem_automatica(self, file_path):
        """Salva a imagem gerada no caminho especificado."""
        if file_path:
            self.figure.savefig(file_path)
            print(f"Imagem salva em: {file_path}")

    def copiar_para_clipboard(self):
        """Salva a imagem no desktop e copia para a área de transferência."""
        # Obtém o caminho do desktop do usuário
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        save_dir = os.path.join(desktop_path, "licitação360", "graficos_dispensa_eletronica")

        # Cria o diretório se não existir
        os.makedirs(save_dir, exist_ok=True)

        # Define o caminho completo para salvar a imagem
        file_path = os.path.join(save_dir, "grafico_dispensa_eletronica.png")

        # Salva a imagem no diretório especificado
        self.salvar_imagem_automatica(file_path)

        # Copia a imagem para a área de transferência
        image = QImage(file_path)
        if not image.isNull():
            clipboard = QGuiApplication.clipboard()
            clipboard.setImage(image)
            print("Imagem copiada para a área de transferência.")
        else:
            print("Erro ao copiar a imagem para a área de transferência.")

    def model_to_dataframe(self, model):
        """Converte os dados do modelo para um DataFrame pandas."""
        records = []
        for row in range(model.rowCount()):
            record = {model.headerData(col, Qt.Orientation.Horizontal): model.index(row, col).data()
                      for col in range(model.columnCount())}
            records.append(record)
        return pd.DataFrame(records)
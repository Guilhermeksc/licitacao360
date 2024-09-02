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
        self.canvas = FigureCanvas(plt.Figure())
        main_layout.addWidget(self.canvas)

        self.ax = self.canvas.figure.subplots()  # Subplot para os gráficos

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
        # Obtém os dados do modelo para gerar o gráfico
        model = self.parent().model
        df = self.model_to_dataframe(model)
        
        # Gera um gráfico de pizza com os dados de 'Status'
        status_counts = df['Status'].value_counts()

        # Definir a ordem desejada
        ordem_desejada = ['Planejamento', 'Aprovado', 'Sessão Pública', 'Homologado', 'Empenhado', 'Concluído', 'Arquivado']
        status_counts = status_counts.reindex(ordem_desejada).fillna(0)

        total_processos = status_counts.sum()
        self.ax.clear()

        # Paleta de cores personalizada
        colors = plt.cm.Pastel1(range(len(status_counts)))

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
        self.ax.legend(handles=patches, loc='lower right', bbox_to_anchor=(1.65, 0.80), fontsize=10)

        self.canvas.draw()
            
    def grafico_combinacoes(self):
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

        # Limpa o gráfico existente
        self.ax.clear()

        # Configurar o número de colunas e gráficos
        num_colunas = len(status_interessantes)
        max_items_por_coluna = 10  # Limite de itens por coluna antes de quebrar

        # Criar uma nova figura com tamanho ajustado
        fig = plt.figure(figsize=(num_colunas * 3, 6))  # Reduzindo o multiplicador horizontal para 3

        # Criar subplots dinamicamente
        axs = []
        for i in range(num_colunas):
            ax = fig.add_subplot(1, num_colunas, i + 1)
            axs.append(ax)

        # Definir caminhos de ícones para cada status
        icons_paths = {
            'Aprovado': str(ICONS_DIR / "aproved.png"),
            'Sessão Pública': str(ICONS_DIR / "session.png"),
            'Homologado': str(ICONS_DIR / "deal.png")
        }

        for col_idx, (status, ax) in enumerate(zip(status_interessantes, axs)):
            data = combinacoes[status]

            # Se houver mais de 8 itens, dividimos a coluna em subcolunas
            if len(data) > max_items_por_coluna:
                subcol_data = [data[i:i + max_items_por_coluna] for i in range(0, len(data), max_items_por_coluna)]
            else:
                subcol_data = [data]

            # Configurar o gráfico para cada subcoluna
            for sub_idx, sub_data in enumerate(subcol_data):
                # Aumentar o deslocamento entre subcolunas
                x_base = sub_idx * 2.5  # Ajustar a posição x base para cada subcoluna com espaçamento maior
                y_positions = range(len(sub_data))  # Posições y para os itens da subcoluna

                # Adicionar cada item no gráfico
                for y, combinacao in zip(y_positions, sub_data):
                    # Ajustar a posição de texto
                    ax.text(
                        x_base,
                        y,
                        combinacao['ID Processo'],
                        ha='center',
                        va='center',
                        fontsize=12,
                        fontweight='bold',
                        color='black'
                    )
                    ax.text(
                        x_base,
                        y - 0.3,
                        combinacao['Objeto'],
                        ha='center',
                        va='center',
                        fontsize=8,
                        color='black',
                        fontstyle='italic'
                    )
                    ax.text(
                        x_base,
                        y - 0.6,
                        combinacao['valor_total'],
                        ha='center',
                        va='center',
                        fontsize=10,
                        color='darkred',
                        fontweight='bold'
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
            icon_x_pos = title_x_pos - 0.45  # Posição x do ícone, ajustada para ficar ao lado do título
            icon_y_pos = 1.0  # Posição y do título no topo do gráfico
            ab = AnnotationBbox(imagebox, (icon_x_pos, icon_y_pos), frameon=False, xycoords='axes fraction')
            ax.add_artist(ab)

            # Ajustar a estética do gráfico
            ax.set_title(status, fontsize=14, fontweight='bold', loc='center')
            ax.set_xlim(-1, (num_subcolunas - 1) * 2.5 + 1)  # Definir limites x para cada status
            ax.set_ylim(-1, max(len(data), max_items_por_coluna))  # Ajustar o limite y
            ax.axis('off')  # Remover eixos

        # Ajustar o espaçamento entre colunas (wspace)
        plt.subplots_adjust(wspace=0.1)  # Diminuindo ainda mais o espaço entre colunas

        plt.tight_layout()

        # Definir o canvas do Matplotlib e desenhar o gráfico
        self.canvas.figure = fig
        self.canvas.draw()

    def salvar_imagem(self):
        """Salva a imagem gerada em um local selecionado pelo usuário."""
        # Remove a linha que causa o erro
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Imagem", "", "PNG Files (*.png);;All Files (*)")
        if file_path:
            self.canvas.figure.savefig(file_path)
            print(f"Imagem salva em: {file_path}")


    def copiar_para_clipboard(self):
        """Copia a imagem gerada para a área de transferência."""
        # Salva o gráfico como uma imagem QPixmap
        buf = QImage(self.canvas.width(), self.canvas.height(), QImage.Format.Format_ARGB32)
        painter = QPainter(buf)
        self.canvas.render(painter)
        painter.end()

        # Copia para a área de transferência
        clipboard = QGuiApplication.clipboard()
        clipboard.setImage(buf)
        print("Imagem copiada para a área de transferência")

    def model_to_dataframe(self, model):
        """Converte os dados do modelo para um DataFrame pandas."""
        records = []
        for row in range(model.rowCount()):
            record = {model.headerData(col, Qt.Orientation.Horizontal): model.index(row, col).data()
                      for col in range(model.columnCount())}
            records.append(record)
        return pd.DataFrame(records)
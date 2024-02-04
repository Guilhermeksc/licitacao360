import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from diretorios import *
import os

def adicionar_rotulo(quadro, texto, linha, fonte="calibri", tamanho="12", bold=True, pady_value=0, padx_value=(0, 0), columnspan=1, anchor="w", justify=tk.LEFT):
    # Define a fonte com base nos argumentos
    estilo = "bold" if bold else ""
    
    fonte_selecionada = (fonte, tamanho, estilo)
    
    rotulo = tk.Label(quadro, text=texto, font=fonte_selecionada, anchor=anchor, justify=justify, bg="#FFFFFF")
    rotulo.grid(row=linha, column=0, columnspan=columnspan, sticky=tk.W, pady=pady_value, padx=padx_value)

def adicionar_traco_preto(quadro, linha):
    canvas_traco = tk.Canvas(quadro, bg="#FFFFFF", width=410, height=2, bd=0, highlightthickness=0)  # Ajuste a largura do Canvas
    canvas_traco.create_line(0, 0, 410, 0, fill="#000000")  # Ajuste as coordenadas conforme necessário
    canvas_traco.grid(row=linha, column=0, sticky=tk.W, pady=(5, 5))  # Adiciona um pequeno espaçamento vertical

def criar_label_com_imagem(quadro, caminho_imagem, texto="", tamanho=(32, 32), fonte="Verdana", tamanho_fonte=10, bold=False, comando=None, espessura_borda=0, cor_borda="#000000", cor_bg="#FFFFFF", **opcoes_grid):
    def on_click(event):
        event.widget.config(bg="gray", relief="sunken")
        if comando:
            comando()

    def on_release(event):
        event.widget.config(bg=cor_bg, relief="flat")  # Modificado para usar cor_bg

    img = carregar_imagem_icone(caminho_imagem, tamanho)
    estilo_fonte = "bold" if bold else "normal"
    fonte_config = (fonte, tamanho_fonte, estilo_fonte)
    label_img = tk.Label(quadro, image=img, text=texto, compound=tk.RIGHT, bg=cor_bg, bd=espessura_borda, highlightbackground=cor_borda, highlightthickness=espessura_borda, font=fonte_config)
    label_img.image = img
    label_img.grid(**opcoes_grid)

    label_img.bind("<Button-1>", on_click)
    label_img.bind("<ButtonRelease-1>", on_release)

    return label_img

def carregar_imagem_icone(caminho, tamanho):
    imagem_original = tk.PhotoImage(file=caminho)
    
    # Obter as dimensões originais da imagem
    largura_original, altura_original = imagem_original.width(), imagem_original.height()
    
    # Obter os fatores de redução
    fator_largura, fator_altura = tamanho
    
    # Usar subsample para reduzir a imagem com base nos fatores fornecidos
    imagem_final = imagem_original.subsample(int(fator_largura), int(fator_altura))
    
    return imagem_final

def ao_clicar_no_icone_pasta(evento, df):
    """Manipula o clique no ícone da pasta."""
    efeito_visual_apos_clique(evento)
    if df is None:
        messagebox.showwarning("Atenção", "Por favor, selecione um item primeiro.")
        return
    
    num_pregao = df['num_pregao'].iloc[0]
    ano_pregao = df['ano_pregao'].iloc[0]
    nome_diretorio_principal = f"PE {num_pregao}-{ano_pregao}"
    caminho_diretorio_principal = RELATORIO_PATH / nome_diretorio_principal

    if not caminho_diretorio_principal.exists():
        # Cria a pasta se ela não existir
        caminho_diretorio_principal.mkdir(parents=True)

    # Abre a pasta
    os.startfile(caminho_diretorio_principal)

def efeito_visual_apos_clique(evento):
    """Aplica um efeito visual ao widget após um clique."""
    evento.widget.config(bg="gray", relief="sunken")
    evento.widget.update()  # Atualiza o widget para mostrar a mudança visual imediatamente
    evento.widget.after(100)  # Adiciona um atraso de 100ms
    evento.widget.config(bg="#FFFFFF", relief="flat")

def ao_clicar_no_label(evento, diretorio):
    efeito_visual_apos_clique(evento)
    abrir_pasta(diretorio)

def abrir_pasta(directory_path):
    os.startfile(directory_path)
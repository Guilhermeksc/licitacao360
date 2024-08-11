import tkinter as tk
from tkinter import Canvas, ttk, PhotoImage
from diretorios import *
import os

def carregar_imagem_redimensionada(caminho):
    imagem_original = tk.PhotoImage(file=caminho)
    metade_largura = imagem_original.width() // 6
    metade_altura = imagem_original.height() // 6
    return imagem_original.subsample(6, 6)

def abrir_pasta(directory_path):
    os.startfile(directory_path)

def criar_button_personalizado(canvas, x, y, text="", image=None, command=None, width=None, compound=None, font=10):
    if not text:
        compound = tk.CENTER
    else:
        compound = compound if compound else tk.RIGHT

    style = ttk.Style()
    style.configure("Custom.TButton", font=("Arial", font))
    btn = ttk.Button(canvas, text=text, image=image, compound=compound, command=command, width=width, style="Custom.TButton")
    canvas.create_window(x, y, window=btn, anchor=tk.CENTER)
    return btn

def criar_button(canvas, x, y, text="", image=None, command=None, width=None, compound=None, tooltip_text=None):
    if not text:
        compound = tk.CENTER
    else:
        compound = compound if compound else tk.RIGHT

    btn = ttk.Button(canvas, text=text, image=image, compound=compound, command=command, width=width)
    btn_window = canvas.create_window(x, y, window=btn, anchor=tk.CENTER)

    # Se um tooltip for fornecido, cria uma dica de ferramenta para o botão
    if tooltip_text:
        ToolTip(btn, text=tooltip_text)

    return btn_window

def config_canvas(canvas):
    global new_folder_image

    y_positions = [20]
    x_positions = [260]

    textos = [
        "Alteração de Diretórios"
    ]

    for i, texto in enumerate(textos):
        canvas.create_text(x_positions[i], (canvas.winfo_height() // 2) + y_positions[i], text=texto, font=("Arial", 16, "bold"), anchor=tk.CENTER)

    # Carregar imagens
    new_folder_image = tk.PhotoImage(file=ICONS_DIR / "new-folder.png")

    # Textos ao lado dos botões
    atualizar_textos = [
        "Atualizar Pasta (Termo de Homologação)",
        "Atualizar Pasta (SICAF)",
        "Atualizar Pasta (Templates)",
        "Atualizar Pasta (Relatório)",
        "Atualizar Pasta (Database)",
        "Atualizar Pasta (Lista de Verificação)"     
    ]

    button_labels = ["", "", "", "", "", ""]
    button_commands = [
        lambda: update_dir("Selecione o novo diretório para PDF_DIR", "PDF_DIR", DATABASE_DIR / "pasta_homologacao"),
        lambda: update_dir("Selecione o novo diretório para SICAF_DIR", "SICAF_DIR", DATABASE_DIR / "pasta_sicaf"),
        lambda: update_dir("Selecione o novo diretório para PASTA_TEMPLATE", "PASTA_TEMPLATE", BASE_DIR / "template"),
        lambda: update_dir("Selecione o novo diretório para RELATORIO_PATH", "RELATORIO_PATH", DATABASE_DIR / "relatorio"),
        lambda: update_dir("Selecione o novo diretório para DATABASE_DIR", "DATABASE_DIR", BASE_DIR / "database"),
        lambda: update_dir("Selecione o novo diretório para LV_DIR", "LV_DIR", BASE_DIR / "Lista_de_Verificacao")
    ]

    for idx, (texto, label, cmd) in enumerate(zip(atualizar_textos, button_labels, button_commands)):
        # Criar texto ao lado esquerdo do botão
        canvas.create_text(x_positions[0]+ 130, (canvas.winfo_height() // 2) + y_positions[0] + 40 + (idx * 40), text=texto, font=("Arial", 14), anchor=tk.E)

        # Criar botão
        criar_button(canvas, x_positions[0] + 160, (canvas.winfo_height() // 2) + y_positions[0] + 40 + (idx * 40), image=new_folder_image, command=cmd, width=1)

class ToolTip(object):
    def __init__(self, widget, text='widget info', font_size=12):
        self.waittime = 5     # tempo de espera até a tooltip aparecer em milissegundos
        self.wraplength = 250   # largura máxima do texto em pixels antes de passar para a próxima linha
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)
        self.id = None
        self.tw = None
        self.font_size = font_size

    def on_enter(self, event=None):
        self.schedule()

    def on_leave(self, event=None):
        self.unschedule()
        self.hide()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def show(self):
        x, y, cx, cy = self.widget.bbox("insert")  # get size of widget
        x += self.widget.winfo_rootx() + 25         # calculate to display tooltip 
        y += self.widget.winfo_rooty() + 20         # below and to the right
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                         background="#ffffff", relief='solid', borderwidth=1,
                         wraplength=self.wraplength,
                         font=("tahoma", self.font_size, "normal"))
        label.pack(ipadx=1)

    def hide(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()


import tkinter as tk
from tkinter import ttk, messagebox
from config.configuracoes import abrir_pasta, criar_button, criar_button_personalizado
import pandas as pd
from pathlib import Path
from diretorios import *
import tkinter.filedialog as filedialog
from docxtpl import DocxTemplate
import string
import fitz  # PyMuPDF
from tkinter import filedialog
import io
import os
import PyPDF2
from PyPDF2 import PdfWriter, PdfReader, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black
import io
from tkinter import simpledialog

def obter_texto_pregao():
    if os.path.exists(ITEM_SELECIONADO_PATH):
        df = pd.read_csv(ITEM_SELECIONADO_PATH)
        num_pregao = df['num_pregao'].iloc[0]
        ano_pregao = df['ano_pregao'].iloc[0]
        return f"PE {num_pregao}/{ano_pregao}"
    else:
        return "Nenhum pregão eletrônico selecionado"
    
Y_POSITIONS = [30]
X_POSITIONS = [100]

TEXTOS = [
    obter_texto_pregao()
]

FONT_STYLE = ("Arial", 20, "bold")

last_fim_value = None

def create_canvas_text(canvas):
    texto = obter_texto_pregao()
    canvas.create_text(X_POSITIONS[0], (canvas.winfo_height() // 2) + Y_POSITIONS[0], text=texto, font=FONT_STYLE, anchor=tk.CENTER)


dados = [
    ("Capa de Abertura do Pregão Eletrônico e Termo de Autuação", "termo_autuacao", "1", "4"),
    ("Autorização para Abertura de Processo", "termo_abertura", "5", "6"),
    ("Documento de Formalização da Demanda (DFD)", "dfd", "7", "16"),
    ("Comprovação da Divulgação da Intenção do Registro de Preços", "termo_irp", "17", "18"),
    ("Despacho", "Despacho", "19", "20"),
    ("Portaria nº 221-2023 Com7°DN de Designação de Ordenador de Despesas", "portaria_od", "21", "23"),
    ("Portaria nº 92-2023 Com7°DN de Designação de Militares para Comissão de Licitação", "portaria_comissao", "24", "27"),
    ("Portaria nº XX-2023 Com7°DN de Designação de Equipe de Planejamento", "portaria_plan", "28", "31"),
    ("Termo de Referência", "tr", "32", "51"),
    ("Estudo Técnico Preliminar (ETP)", "etp", "52", "68"),
    ("Matriz de Gerenciamento de Riscos", "mr", "69", "79"),
    ("Pesquisa de Preços", "pesquisa_precos", "80", "137"),   
    ("Minuta do Edital", "minuta_edital", "138", "164"),
    ("Minuta do Contrato", "minuta_contrato", "165", "173"),
    ("Minuta da Ata de Registro de Preços", "minuta_arp", "174", "183"),
    ("Lista de Verificação", "checklist", "184", "190"),    
    ("Despacho", "despacho", "191", "192"),
    ("Nota Técnica", "nota_tecnica", "193", "200"),
    ("Comunicação Padronizada", "termo", "201", "202"),
    ("Despacho de Encaminhamento para AGU", "termo", "203", "204"),
]

def create_treeview(canvas):
    # Use a classe DraggableTreeview logo no início    
    style = ttk.Style()
    style.configure("Custom.Treeview", background="#DCDCDC")
    style.configure("Custom.Treeview.Row", background="#DCDCDC", fieldbackground="#DCDCDC")
    tree = DraggableTreeview(canvas)
    
    tree["columns"] = ("Identificação", "SAPIENS", "Início", "Fim", "qnt_pag")
    
    # Configuração das colunas
    tree.column("#0", anchor=tk.W, width=40)
    tree.column("qnt_pag", width=0, stretch=tk.NO)
    tree.column("Identificação", anchor=tk.CENTER, width=450)
    tree.column("SAPIENS", anchor=tk.CENTER, width=150)
    tree.column("Início", anchor=tk.CENTER, width=100)
    tree.column("Fim", anchor=tk.CENTER, width=100)
    
    # Definindo os cabeçalhos
    tree.heading("#0", text="")
    tree.heading("Identificação", text="Identificação")
    tree.heading("SAPIENS", text="SAPIENS")
    tree.heading("Início", text="Início")
    tree.heading("Fim", text="Fim")
    
    # Verificar se o arquivo TREEVIEW_DATA_PATH existe
    if os.path.exists(TREEVIEW_DATA_PATH):
        df = pd.read_csv(TREEVIEW_DATA_PATH, usecols=['Identificação', 'SAPIENS', 'Início', 'Fim'])
        dados_from_file = df.values.tolist()
    else:
        dados_from_file = dados
    
    # Inserting data into the treeview
    for idx, item in enumerate(dados_from_file, 1):  # Start counting from 1
        identificacao, sapiens, inicio, fim, *_ = item
        qnt_pag = int(fim) - int(inicio) + 1
        tree.insert("", "end", text=f"{idx:02}", values=(identificacao, sapiens, inicio, fim, qnt_pag))
       
    # Criando e configurando o scrollbar
    scrollbar = ttk.Scrollbar(canvas, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    # # Colocando o tree e o scrollbar no canvas
    scrollbar_window = canvas.create_window(1087, 260, anchor=tk.CENTER, window=scrollbar, height=400)
    
    tree.bind("<Delete>", lambda event: delete_selected_rows(tree))
    tree.bind("<Double-1>", lambda e: open_popup(tree, overwrite=True))

    return tree


def ajustar_dataframe(df):
    inicio_atual = 1
    for index, row in df.iterrows():
        df.at[index, 'Início'] = inicio_atual
        # Convertendo 'qnt_pag' para inteiro antes de somar
        fim_atual = inicio_atual + int(row['qnt_pag']) - 1
        df.at[index, 'Fim'] = fim_atual
        inicio_atual = fim_atual + 1
    return df

def resetar_treeview(tree):
    # Limpar todos os itens do treeview
    for item in tree.get_children():
        tree.delete(item)

    # Inserir os dados padrão no treeview
    for idx, item in enumerate(dados, 1):  # Start counting from 1
        identificacao, sapiens, inicio, fim = item
        qnt_pag = int(fim) - int(inicio) + 1
        tree.insert("", "end", text=f"{idx:02}", values=(identificacao, sapiens, inicio, fim, qnt_pag))

import webbrowser

def abrir_site_sapiens():
    webbrowser.open(URL_SAPIENS)

def alterar_site_sapiens():
    global URL_SAPIENS  # Declara que queremos usar a variável global
    root = tk.Tk()  # Você pode usar a janela principal se já tiver uma
    root.withdraw()  # Esconde a janela extra que aparece com o Toplevel

    # Pede ao usuário o novo URL
    novo_url = simpledialog.askstring("Alterar URL do Sapiens", "Insira o novo URL:", parent=root)
    
    if novo_url:  # Se o usuário inseriu algo, atualiza o URL
        URL_SAPIENS = novo_url
        print(f"O novo URL padrão é: {URL_SAPIENS}")
    else:
        print("Nenhuma alteração foi feita no URL.")
        
    root.destroy()


def checklist_canvas(canvas):
    global delete_image, abrir_pasta_image, load_image, adicionar_image, salvar_image, pdf_image, add24_image, docx_image, reset_image, link_image, url_image

    # Carregar imagens
    delete_image = tk.PhotoImage(file=ICONS_DIR / "delete.png")
    abrir_pasta_image = tk.PhotoImage(file=ICONS_DIR / "abrir_pasta.png")
    load_image = tk.PhotoImage(file=ICONS_DIR / "loading.png")
    adicionar_image = tk.PhotoImage(file=ICONS_DIR / "plus.png")
    salvar_image = tk.PhotoImage(file=ICONS_DIR / "save_to_drive.png")
    pdf_image = tk.PhotoImage(file=ICONS_DIR / "pdf.png")
    add24_image = tk.PhotoImage(file=ICONS_DIR / "plus24.png")
    docx_image = tk.PhotoImage(file=ICONS_DIR / "docx-file.png") 
    reset_image = tk.PhotoImage(file=ICONS_DIR / "reset.png") 
    link_image = tk.PhotoImage(file=ICONS_DIR / "url.png") 
    url_image = tk.PhotoImage(file=ICONS_DIR / "url2.png") 

    create_canvas_text(canvas)
    tree = create_treeview(canvas)
    criar_button_personalizado(canvas, 100, 100, "      Despacho      ", add24_image, command=lambda: inserir_item(tree), font=10)
    criar_button_personalizado(canvas, 100, 140, "Desentranhamento", add24_image, command=lambda: inserir_item(tree, "Termo de Desentranhamento", "Termo"), font=10)
    criar_button_personalizado(canvas, 100, 180, "    Comunicação    ", add24_image, command=lambda: inserir_item(tree, "Comunicação Padronizada nº", "Comunicação"), font=10)
    criar_button_personalizado(canvas, 100, 220, "        Portaria       ", add24_image, command=lambda: inserir_item(tree, "Portaria nº", "Termo"), font=10)
    criar_button(canvas, 298, 480, "   Excluir  ", delete_image,command=lambda: delete_selected_rows(tree))
    criar_button(canvas, 451, 480, "  Adicionar ", adicionar_image, command=lambda: open_popup(tree, overwrite=False))
    criar_button(canvas, 605, 480, "   Salvar   ", salvar_image, command=lambda: save_treeview_to_xlsx(tree))
    criar_button(canvas, 759, 480, "  Carregar  ", load_image, command=lambda: carregar_dataframe(tree))
    criar_button(canvas, 914, 480, "Processar", pdf_image, command=lambda: processar_pdf_na_integra_e_gerar_documentos())
    criar_button(canvas, 1060, 480, "", abrir_pasta_image, lambda: abrir_pasta(LV_FINAL_DIR), width=1)
    criar_button(canvas, 650, 30, " Numerar PDF ", pdf_image, command=numerar_pdf_gui, tooltip_text="Selecione o processo na íntegra do SIGDEM para ser numerado")
    criar_button(canvas, 870, 30, " Link Sapiens ", link_image, command=abrir_site_sapiens, tooltip_text="Clique para acessar o site do SAPIENS AGU")
    criar_button(canvas, 990, 30, "", url_image, command=alterar_site_sapiens, width=1, tooltip_text="Clique para alterar o URL padrão")
    criar_button(canvas, 100, 480, " Resetar ", reset_image, command=lambda: resetar_treeview(tree))

    canvas.create_window(630, 260, anchor=tk.CENTER, window=tree, height=400, width=900)

def split_pdf_using_dataframe(arquivo_numerado):
    # Static counter to keep track of how many times the function has been called
    if not hasattr(split_pdf_using_dataframe, "counter"):
        split_pdf_using_dataframe.counter = 0
    
    split_pdf_using_dataframe.counter += 1

    # Static directory to keep track of the latest output directory
    split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR = LV_BASE_DIR / f"Processo {split_pdf_using_dataframe.counter}"
    split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR.mkdir(parents=True, exist_ok=True)
        
    df = pd.read_csv(TREEVIEW_DATA_PATH)
    
    # Use the numerated PDF file as input
    pdf_file_path = arquivo_numerado
    
    with open(pdf_file_path, "rb") as original_pdf_file:
        original_pdf = PyPDF2.PdfReader(original_pdf_file)
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            start_page = int(row["Início"]) - 1
            end_page = int(row["Fim"])
            if row["Início"] == row["Fim"]:
                output_filename = split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR / f"{idx:02} - {row['Identificação']} (Fl. {row['Início']}).pdf"
            else:
                output_filename = split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR / f"{idx:02} - {row['Identificação']} (Fls {row['Início']} a {row['Fim']}).pdf"
            new_pdf = PyPDF2.PdfWriter()
            for page_num in range(start_page, end_page):
                page = original_pdf.pages[page_num]
                new_pdf.add_page(page)
            with open(output_filename, "wb") as output_pdf_file:
                new_pdf.write(output_pdf_file)
    return "PDF dividido com sucesso!"

class DraggableTreeview(ttk.Treeview):
    def __init__(self, master=None, **kw):
        # Configure o estilo
        style = ttk.Style()
        style.configure("Custom.Treeview", background="#DCDCDC", fieldbackground="#DCDCDC")
        style.configure("Custom.Treeview.Row", background="#DCDCDC")    
        kw["style"] = "Custom.Treeview"
        super().__init__(master, **kw)
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_drop)
        self.drag_data = {"item": None, "original_position": None}

    def on_click(self, event):
        # Selecione o item sob o cursor
        item = self.identify_row(event.y)
        if item:
            self.drag_data["item"] = item
            self.drag_data["original_position"] = self.index(item)

    def on_drag(self, event):
        # Se o item estiver sendo arrastado, identifique a posição atual e mude se necessário
        if self.drag_data["item"]:
            current_position = self.index(self.drag_data["item"])
            item_below = self.identify_row(event.y)
            if item_below and current_position != self.index(item_below):
                self.move(self.drag_data["item"], "", self.index(item_below))

    def on_drop(self, event):
        # Quando soltar o item, finalize o processo de arrastar e soltar
        if self.drag_data["item"]:
            new_position = self.index(self.drag_data["item"])
            if new_position != self.drag_data["original_position"]:
                # Se a posição mudou, atualize o dataframe
                df = save_treeview_to_dataframe(self)
                df = ajustar_dataframe(df)
                atualizar_tree_from_dataframe(self, df)
            self.drag_data = {"item": None, "original_position": None}

def save_treeview_to_dataframe(tree):
    # Coleta de dados do treeview
    items = tree.get_children()
    data = [tree.item(item, "values") for item in items]
    
    # Criação do dataframe
    df = pd.DataFrame(data, columns=["Identificação", "SAPIENS", "Início", "Fim", "qnt_pag"])
    
    # Salvar o dataframe em um arquivo (por exemplo, um arquivo CSV)
    df.to_csv(TREEVIEW_DATA_PATH, index=False)
    return df  # Certifique-se de retornar o dataframe

def save_treeview_to_xlsx(tree):
    # Coleta de dados do treeview
    items = tree.get_children()
    data = [tree.item(item, "values") for item in items]
    
    # Criação do dataframe
    df = pd.DataFrame(data, columns=["Identificação", "SAPIENS", "Início", "Fim", "qnt_pag"])
    
    # Pede ao usuário para escolher o local e nome do arquivo para salvar
    filepath = filedialog.asksaveasfilename(initialdir=DATABASE_DIR, title="Salvar como", 
                                            filetypes=(("Excel files", "*.xlsx"), ("Todos os arquivos", "*.*")), 
                                            defaultextension=".xlsx", initialfile="checklist")
    
    if filepath:
        df.to_excel(filepath, index=False)

def delete_selected_rows(tree):
    selected_items = tree.selection()
    for item in selected_items:
        tree.delete(item)
    
    # Saving the treeview to a dataframe and adjusting it
    df = save_treeview_to_dataframe(tree)
    df = ajustar_dataframe(df)
    
    # Clearing the treeview
    for i in tree.get_children():
        tree.delete(i)
    
    # Repopulating the treeview with updated indices
    for idx, (_, row) in enumerate(df.iterrows(), 1):  # Start counting from 1
        tree.insert("", "end", text=f"{idx:02}", values=(row["Identificação"], row["SAPIENS"], row["Início"], row["Fim"], row["qnt_pag"]))

def open_popup(tree, overwrite=False):
    selected_items = tree.selection()
    insert_position = None  # Default position is None, which will append to the end
    
    # If overwrite is False and there are selected items, then deselect them
    if not overwrite and selected_items:
        last_fim_value = tree.item(selected_items[0], "values")[3]
        insert_position = tree.index(selected_items[0]) + 1
        selected_items = ()
    elif selected_items:  # If overwrite is True and there are selected items
        last_fim_value = tree.item(selected_items[0], "values")[3]
        selected_item = tree.item(selected_items[0], "values")
        identificacao_value, marcador_sapiens_value, inicio_value, fim_value, _ = selected_item
    elif tree.get_children():  # If there are no selected items, but there are items in the treeview
        last_item = tree.get_children()[-1]
        last_fim_value = tree.item(last_item, "values")[3]
    else:  # If there are no items in the treeview
        last_fim_value = 0

    # Define the default value for the 'inicio_entry' field based on 'last_fim_value'
    inicio_default = int(last_fim_value) + 1

    def submit():
        identificacao = combo1.get()
        marcador_sapiens = combo2.get()
        inicio_value = inicio_entry.get() or inicio_default  # Se 'inicio_entry' estiver vazio, use 'inicio_default'
        fim_value = fim_entry.get()
        
        if inicio_value and fim_value:
            try:
                inicio = int(inicio_value)
                fim = int(fim_value)
                num_paginas = fim - inicio + 1
            except ValueError:
                messagebox.showerror("Erro", "Por favor, insira números válidos para o início e o fim.")
                return
        else:
            try:
                num_paginas = int(num_pag_entry.get())
                inicio = inicio_default
                fim = inicio + num_paginas - 1
            except ValueError:
                messagebox.showerror("Erro", "Por favor, insira um número válido para o número de páginas.")
                return

        # Se houver um item selecionado, atualize o item selecionado com os novos valores
        if selected_items:
            tree.item(selected_items[0], values=(identificacao, marcador_sapiens, inicio, fim, num_paginas))
        else:
            if overwrite:
                tree.insert("", "end", values=(identificacao, marcador_sapiens, inicio, fim, num_paginas))
            else:
                if insert_position is not None:
                    tree.insert("", insert_position, values=(identificacao, marcador_sapiens, inicio, fim, num_paginas))
                else:
                    tree.insert("", "end", values=(identificacao, marcador_sapiens, inicio, fim, num_paginas))
            
        if overwrite and selected_items:
            inicio_entry.delete(0, tk.END)
            inicio_entry.insert(0, inicio_value)
        else:
            inicio_entry.delete(0, tk.END)
            inicio_entry.insert(0, str(inicio_default))

        atualizar_idx_treeview(tree)

        df = save_treeview_to_dataframe(tree)

        df = ajustar_dataframe(df)

        atualizar_tree_from_dataframe(tree, df)

        popup.destroy()

        
    popup = tk.Toplevel()
    popup.title("Informe os valores")
    popup.configure(bg='#C8C8C8')
    popup.geometry('+800+200')
    font_style = ("Arial", 14)
    combo_width = 50

    # Combobox para "Identificação"
    label1 = ttk.Label(popup, text="Identificação: ", background='#C8C8C8', font=font_style, foreground='black')
    label1.grid(row=0, column=0, sticky=tk.E)

    # Criação do Combobox
    combo1 = ttk.Combobox(popup, font=font_style, width=combo_width)
    combo1.grid(row=0, column=1, sticky=tk.W)

    # Ajuste dos paddings para controlar o espaço entre o label e o combobox
    label1.grid_configure(padx=(10, 0), pady=10)  # Espaço à esquerda do label
    combo1.grid_configure(padx=(0, 10), pady=10)

    # Combobox para "Marcador SAPIENS"
    label2 = ttk.Label(popup, text="Marcador SAPIENS: ", background='#C8C8C8', font=font_style, foreground='black', anchor=tk.E)
    label2.grid(row=1, column=0, sticky=tk.E)
    combo2 = ttk.Combobox(popup, font=font_style, width=combo_width)
    combo2.grid(row=1, column=1, sticky=tk.W)
    label2.grid_configure(padx=(10, 0), pady=10)
    combo2.grid_configure(padx=(0, 10), pady=10)

    # Entry para número de páginas
    label3 = ttk.Label(popup, text="Número de páginas:", background='#C8C8C8', font=font_style, foreground='black', anchor=tk.E)
    label3.grid(row=2, column=0, sticky=tk.E)
    num_pag_entry = ttk.Entry(popup, font=font_style, width=5)
    num_pag_entry.grid(row=2, column=1, sticky=tk.W)
    label3.grid_configure(padx=(10, 0), pady=10)
    num_pag_entry.grid_configure(padx=(0, 10), pady=10)


    label5 = ttk.Label(popup, text="ou", background='#C8C8C8', font=font_style, foreground='black', anchor=tk.E)
    label5.grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)

    # Entry para início
    label4 = ttk.Label(popup, text="Número da página 'início':", background='#C8C8C8', font=font_style, foreground='black', anchor=tk.E)
    label4.grid(row=4, column=0, sticky=tk.E)
    inicio_entry = ttk.Entry(popup, font=font_style, width=5)
    inicio_entry.insert(0, str(inicio_default))  # Aqui, definimos o valor padrão no campo
    inicio_entry.grid(row=4, column=1, sticky=tk.W)
    label4.grid_configure(padx=(10, 0), pady=10)
    inicio_entry.grid_configure(padx=(0, 10), pady=10)

    # Entry para fim
    label5 = ttk.Label(popup, text="Número da página 'fim':", background='#C8C8C8', font=font_style, foreground='black', anchor=tk.E)
    label5.grid(row=5, column=0, sticky=tk.E)
    fim_entry = ttk.Entry(popup, font=font_style, width=5)
    fim_entry.grid(row=5, column=1, sticky=tk.W)
    label5.grid_configure(padx=(10, 0), pady=10)
    fim_entry.grid_configure(padx=(0, 10), pady=10)

    # Botão "Adicionar"
    button_text = "Alterar" if overwrite else "Adicionar"
    
    submit_btn = ttk.Button(popup, text=button_text, command=submit)
    submit_btn.grid(row=6, column=0, columnspan=2, pady=20)

        # Carregar os dados de MARCADORES_DIR
    df = pd.read_excel(MARCADORES_PATH)
    
    # Preencher o primeiro Combobox com dados da primeira coluna
    combo1["values"] = df.iloc[:, 0].dropna().tolist()
    
    # Preencher o segundo Combobox com dados da segunda coluna
    combo2["values"] = df.iloc[:, 1].dropna().tolist()

    # Adicione o código abaixo depois de criar o widget 'combo1':
    if selected_items:
        combo1.set(identificacao_value)

    # Adicione o código abaixo depois de criar o widget 'combo2':
    if selected_items:
        combo2.set(marcador_sapiens_value)

    # Adicione o código abaixo depois de criar o widget 'inicio_entry':
    if selected_items:
        inicio_entry.delete(0, tk.END)
        inicio_entry.insert(0, inicio_value)

    # Adicione o código abaixo depois de criar o widget 'fim_entry':
    if selected_items:
        fim_entry.delete(0, tk.END)
        fim_entry.insert(0, fim_value)

def add_new_item(tree):
    open_popup(tree, overwrite=False)

def overwrite_existing_item(tree):
    open_popup(tree, overwrite=True)

def carregar_dataframe(tree):
    # Solicitar ao usuário que escolha um arquivo
    filepath = filedialog.askopenfilename(title="Escolha um arquivo", 
                                          filetypes=(("Excel files", "*.xlsx"),
                                                     ("CSV files", "*.csv"),
                                                     ("ODS files", "*.ods"),
                                                     ("Todos os arquivos", "*.*")))
    
    if not filepath:
        return None  # O usuário cancelou a operação

    # Determinar o tipo de arquivo pela extensão
    ext = filepath.split('.')[-1]

    if ext == "xlsx":
        df = pd.read_excel(filepath)
    elif ext == "csv":
        df = pd.read_csv(filepath)
    elif ext == "ods":
        df = pd.read_excel(filepath, engine="odf")
    else:
        raise ValueError(f"Formato de arquivo {ext} não suportado.")

    # Limpar itens existentes no Treeview
    for i in tree.get_children():
        tree.delete(i)

    # Adicionar os novos dados no Treeview
    for _, row in df.iterrows():
        tree.insert("", "end", values=(row["Identificação"], row["SAPIENS"], row["Início"], row["Fim"], row["qnt_pag"]))
    
    return df

def atualizar_idx_treeview(tree):
    for idx, item in enumerate(tree.get_children(), 1):  # Comece a contar de 1
        tree.item(item, text=f"{idx:02}")

def atualizar_tree_from_dataframe(tree, df):
    tree_items = tree.get_children()
    
    # Atualizar ou adicionar itens com base no DataFrame
    for idx, (_, row) in enumerate(df.iterrows(), 1):  # Comece a contar de 1
        values = (row["Identificação"], row["SAPIENS"], row["Início"], row["Fim"], row["qnt_pag"])
        
        if idx <= len(tree_items):
            # Se o item já existe, atualize seus valores
            tree.item(tree_items[idx-1], text=f"{idx:02}", values=values)
        else:
            # Caso contrário, adicione um novo item
            tree.insert("", "end", text=f"{idx:02}", values=values)
            
    # Remova quaisquer itens excedentes do Treeview
    for item in tree_items[idx:]:
        tree.delete(item)

def load_treeview_data():
    return pd.read_csv(TREEVIEW_DATA_PATH)

from datetime import datetime
from num2words import num2words

def substituir_marcadores_com_relacao(docx_path):
    # Carregar os dados do arquivo CSV
    df = load_treeview_data()
    
    # Processar os dados para criar a relação de documentos
    relacao_documentos = []
    for idx, row in enumerate(df.iterrows(), 1):
        if idx == len(df) - 1:  # Se for a penúltima linha
            terminacao = "; e"
        elif idx == len(df):  # Se for a última linha
            terminacao = "."
        else:
            terminacao = ";"

        if row[1]["Início"] == row[1]["Fim"]:
            relacao = f"{string.ascii_lowercase[idx-1]}) {row[1]['Identificação']} (Fl. {row[1]['Início']}){terminacao}"
        else:
            relacao = f"{string.ascii_lowercase[idx-1]}) {row[1]['Identificação']} (Fls. {row[1]['Início']} a {row[1]['Fim']}){terminacao}"
        relacao_documentos.append(relacao)

    relacao_documentos_str = "\n".join(relacao_documentos)
    
    # Obter o último valor de "Fim"
    ultima_folha = df["Fim"].iloc[-1]
    quantidade_folhas = f"{ultima_folha} ({num2words(ultima_folha, lang='pt_BR')}) folhas"
    
    # Obter a data atual no formato desejado
    hoje = datetime.now().strftime("%d/%m/%Y")
    
    # Carregar dados do item selecionado
    df_item_selecionado = pd.read_csv(ITEM_SELECIONADO_PATH)
    num_pregao = df_item_selecionado['num_pregao'].iloc[0]
    ano_pregao = df_item_selecionado['ano_pregao'].iloc[0]
    nup = df_item_selecionado['nup'].iloc[0]
    objeto = df_item_selecionado['objeto'].iloc[0]
    
    # Carregar e processar o template
    doc = DocxTemplate(docx_path)
    context = {
        'relacao_documentos': relacao_documentos_str,
        'quantidade_folhas': quantidade_folhas,
        'hoje': hoje,
        'num_pregao': num_pregao,
        'ano_pregao': ano_pregao,
        'nup': nup,
        'objeto': objeto
    }
    doc.render(context)
    
    output_path = split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR / "termo_de_autuacao_modificado.docx"
    doc.save(output_path)
    return output_path

import webbrowser

def numerar_pdf_gui():
    arquivo_entrada = filedialog.askopenfilename(title="Selecione o arquivo PDF de entrada")
    
    # Se nenhum arquivo for selecionado, retorne
    if not arquivo_entrada:
        return None

    # Construir o nome do arquivo de saída baseado no arquivo de entrada
    base, ext = os.path.splitext(arquivo_entrada)
    arquivo_saida = base + "_numerado" + ext
    
    numerar_pdf_com_pypdf2(arquivo_entrada, arquivo_saida)

    # Abrir o arquivo no navegador padrão do usuário
    webbrowser.open(arquivo_saida)

def numerar_pdf_com_pypdf2(arquivo_entrada, output_pdf_path):
    # arquivo_entrada = filedialog.askopenfilename(title="Selecione o arquivo PDF de entrada")
    # Crie um novo PdfFileWriter object
    output = PdfWriter()
    input_pdf = PdfReader(open(arquivo_entrada, "rb"))

    # Processo de numeração
    for i in range(len(input_pdf.pages)):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        width = input_pdf.pages[i].mediabox[2]
        height = input_pdf.pages[i].mediabox[3]

        # Aqui, estamos colocando o número no canto superior direito.
        can = canvas.Canvas(packet, pagesize=(width, height))
        can.setFont("Helvetica", 14)
        can.setFillColor(black)  # Definindo a cor da fonte para preto
        can.drawString(float(width) - 30, float(height) - 30, str(i + 1))

        can.save()

        # Mova o buffer de posição para o início e crie um novo objeto PDF a partir dele
        packet.seek(0)
        new_pdf = PdfReader(packet)

        # Combine as páginas
        page = input_pdf.pages[i]
        page.merge_page(new_pdf.pages[0])

        output.add_page(page)

    # Escreva a saída
    with open(output_pdf_path, "wb") as output_file_handle:
        output.write(output_file_handle)

def inserir_item(tree, identificacao="Despacho", marcador_sapiens="Termo"):
    # Verifique se há uma linha selecionada
    selected_items = tree.selection()
    
    # Obtenha o último valor de 'fim' da linha selecionada ou, se não houver linha selecionada, da última linha
    if selected_items:
        last_fim_value = tree.item(selected_items[0], "values")[3]
        insert_position = tree.index(selected_items[0]) + 1
    elif tree.get_children():
        last_item = tree.get_children()[-1]
        last_fim_value = tree.item(last_item, "values")[3]
        insert_position = "end"
    else:
        last_fim_value = 0
        insert_position = "end"

    inicio = int(last_fim_value) + 1
    fim = inicio + 1
    num_paginas = fim - inicio + 1

    tree.insert("", insert_position, values=(identificacao, marcador_sapiens, inicio, fim, num_paginas))
    atualizar_idx_treeview(tree)

    df = save_treeview_to_dataframe(tree)
    df = ajustar_dataframe(df)
    atualizar_tree_from_dataframe(tree, df)

def substituir_variaveis_docx():
    # Lendo o arquivo CSV
    df = pd.read_csv(TREEVIEW_DATA_PATH)
    
    # Inicializando o template DOCX
    doc = DocxTemplate(TEMPLATE_CHECKLIST)
    
    # Dicionário para mapear as variáveis para os valores
    context = {}
    
    # Lista de variáveis para substituir
    variaveis = ["abertura", "port_od", "port_comissao", "port_plan", "dfd", "etp", "mr", "tr", "pesquisa_precos", "minuta_edital"]
    
    for var in variaveis:
        subset_df = df[df["SAPIENS"] == var]
        
        # Check if subset is not empty
        if not subset_df.empty:
            row = subset_df.iloc[0]
            inicio, fim = row["Início"], row["Fim"]
            
            # Formatando o texto com base nos valores de "Início" e "fim"
            if inicio == fim:
                context[var] = f"Fl. {inicio}"
            else:
                context[var] = f"Fls. {inicio} a {fim}"
        else:
            print(f"Entrada não encontrada para variável: {var}")
            context[var] = "N/A"
    
    # Substituindo as variáveis no documento
    doc.render(context)
    
    # Determinando o nome do arquivo modificado
    arquivo_saida = split_pdf_using_dataframe.LV_SPLIT_FINAL_DIR / (TEMPLATE_CHECKLIST.name.replace(".docx", "_modificado.docx"))
    
    # Salvando o documento modificado
    doc.save(arquivo_saida)

def processar_pdf_na_integra_e_gerar_documentos():
    arquivo_numerado = filedialog.askopenfilename(title="Selecione o arquivo PDF numerado")
    if not arquivo_numerado:
        return
    
    split_pdf_using_dataframe(arquivo_numerado)
    substituir_marcadores_com_relacao(TEMPLATE_AUTUACAO)
    substituir_variaveis_docx()
    mensagem = "Todas as operações foram concluídas com sucesso!"
    print(mensagem)
    
    abrir_pasta(LV_FINAL_DIR)

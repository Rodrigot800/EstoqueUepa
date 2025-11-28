import tkinter as tk
from tkinter import ttk
from funcsEstoque import (
    listar_produtos,
    inserir_produto,
    registrar_movimento,
    calcular_saldo
)

# ----------------------------------------
# Tela principal
# ----------------------------------------
class TelaPrincipal:
    def __init__(self, root):
        self.root = root
        root.title("Controle de Estoque - Excel")
        root.geometry("900x500")
        root.configure(bg="#f0f0f0")

        # ------- TÍTULO -------
        titulo = tk.Label(root, text="Controle de Estoque - UEPA",
                          font=("Arial", 18, "bold"), bg="#f0f0f0")
        titulo.pack(pady=10)

        # ------- BARRA DE PESQUISA -------
        frame_search = tk.Frame(root, bg="#f0f0f0")
        frame_search.pack(fill="x", padx=15, pady=5)

        tk.Label(frame_search, text="Pesquisar:", bg="#f0f0f0").pack(side="left")
        self.entry_pesquisa = tk.Entry(frame_search)
        self.entry_pesquisa.pack(side="left", fill="x", expand=True, padx=10)
        self.entry_pesquisa.bind("<KeyRelease>", self.filtrar_tabela)

        # ------- FRAME TABELA -------
        frame_tab = tk.Frame(root)
        frame_tab.pack(fill="both", expand=True, padx=15)

        self.tabela = ttk.Treeview(
            frame_tab,
            columns=("id", "nome", "saldo"),
            show="headings",
            height=12
        )
        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Produto")
        self.tabela.heading("saldo", text="Saldo")

        self.tabela.column("id", width=80, anchor="center")
        self.tabela.column("nome", width=350, anchor="w")
        self.tabela.column("saldo", width=100, anchor="center")

        scroll = ttk.Scrollbar(frame_tab, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scroll.set)

        self.tabela.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # ------- FRAME BOTÕES -------
        frame_btn = tk.Frame(root, bg="#f0f0f0")
        frame_btn.pack(pady=12)

        estilo_btn = {"font": ("Arial", 11), "width": 20}

        tk.Button(frame_btn, text="Cadastrar Produto",
                  command=self.janela_produto, **estilo_btn).pack(side="left", padx=10)

        tk.Button(frame_btn, text="Movimentar",
                  command=self.janela_movimento, **estilo_btn).pack(side="left", padx=10)

        tk.Button(frame_btn, text="Atualizar",
                  command=self.carregar, **estilo_btn).pack(side="left", padx=10)

        # ------- Carregar dados -------
        self.produtos_lista = []  # lista completa
        self.carregar()

    # ----------------------------------------
    # Carregar dados da tabela
    # ----------------------------------------
    def carregar(self):
        self.produtos_lista = listar_produtos()  # salva a lista completa
        self.atualizar_tabela(self.produtos_lista)

    # ----------------------------------------
    # Atualizar tabela com lista fornecida
    # ----------------------------------------
    def atualizar_tabela(self, lista):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for id_, nome, cat, un, min_ in lista:
            saldo = calcular_saldo(id_)
            self.tabela.insert("", "end", values=(id_, nome, saldo))

    # ----------------------------------------
    # Filtrar tabela conforme pesquisa
    # ----------------------------------------
    def filtrar_tabela(self, event):
        termo = self.entry_pesquisa.get().lower()
        filtrados = [p for p in self.produtos_lista if termo in p[1].lower()]
        self.atualizar_tabela(filtrados)

    # ----------------------------------------
    # Janela cadastro de produto
    # ----------------------------------------
    def janela_produto(self):
        win = tk.Toplevel()
        win.title("Cadastrar Produto")
        win.geometry("350x330")
        win.configure(bg="#fafafa")

        tk.Label(win, text="Cadastrar novo produto",
                 font=("Arial", 14, "bold"), bg="#fafafa").pack(pady=10)

        def campo(label):
            tk.Label(win, text=label, bg="#fafafa", anchor="w").pack(fill="x", padx=20)
            entrada = tk.Entry(win)
            entrada.pack(fill="x", padx=20, pady=5)
            return entrada

        nome = campo("Nome:")
        cat = campo("Categoria:")
        un = campo("Unidade (ex: ml, kg):")
        minimo = campo("Estoque mínimo:")

        def salvar():
            inserir_produto(nome.get(), cat.get(), un.get(), minimo.get())
            self.carregar()
            win.destroy()

        tk.Button(win, text="Salvar", bg="#4CAF50", fg="white",
                  font=("Arial", 11), command=salvar).pack(pady=15)

    # ----------------------------------------
    # Janela movimentação
    # ----------------------------------------
    def janela_movimento(self):
        win = tk.Toplevel()
        win.title("Movimentação de Estoque")
        win.geometry("350x320")
        win.configure(bg="#fafafa")

        tk.Label(win, text="Registrar movimento",
                 font=("Arial", 14, "bold"), bg="#fafafa").pack(pady=10)

        produtos = listar_produtos()

        # Produto
        tk.Label(win, text="Produto:", bg="#fafafa").pack(anchor="w", padx=20)
        combo = ttk.Combobox(win, values=[f"{p[0]} - {p[1]}" for p in produtos])
        combo.pack(fill="x", padx=20, pady=5)

        # Tipo
        tk.Label(win, text="Tipo:", bg="#fafafa").pack(anchor="w", padx=20)
        tipo = ttk.Combobox(win, values=["ENTRADA", "SAIDA"])
        tipo.pack(fill="x", padx=20, pady=5)

        # Quantidade
        tk.Label(win, text="Quantidade:", bg="#fafafa").pack(anchor="w", padx=20)
        qtd = tk.Entry(win)
        qtd.pack(fill="x", padx=20, pady=5)

        def salvar():
            produto_id = int(combo.get().split(" - ")[0])
            registrar_movimento(produto_id, tipo.get(), int(qtd.get()))
            self.carregar()
            win.destroy()

        tk.Button(win, text="Registrar", bg="#2196F3", fg="white",
                  font=("Arial", 11), command=salvar).pack(pady=15)

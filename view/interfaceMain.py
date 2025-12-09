import tkinter as tk
from tkinter import ttk, messagebox
from funcsEstoque import (
    listar_produtos,
    inserir_produto,
    registrar_movimento,
    calcular_saldo
)
from view.janela_produto import JanelaCadastroProduto
from view.janela_movimento import JanelaMovimentacao

class TelaPrincipal:
    def __init__(self, root):
        self.root = root
        root.title("Controle de Estoque - Excel")
        root.geometry("1080x800")
        root.configure(bg="#f0f0f0")

        # ------- TÍTULO -------
        titulo = tk.Label(root, text="Controle de Estoque - UEPA",
                          font=("Arial", 20, "bold"), bg="#f0f0f0")
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
            height=15
        )
        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Produto")
        self.tabela.heading("saldo", text="Saldo")

        # Ajustei widths para algo mais legível
        self.tabela.column("id", width=60, anchor="e")
        self.tabela.column("nome", width=800, anchor="w")
        self.tabela.column("saldo", width=120, anchor="center")

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
        self.produtos_lista = listar_produtos() or []  # salva a lista completa
        self.atualizar_tabela(self.produtos_lista)

    # ----------------------------------------
    # Atualizar tabela com lista fornecida
    # ----------------------------------------
    def atualizar_tabela(self, lista):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for linha in lista:
            # defensivo: linha pode não ter todos os campos
            try:
                id_, nome, cat, un, min_ = linha
            except Exception:
                # se a estrutura for diferente, tente preencher com valores padrão
                values = tuple(linha)[:3]
                self.tabela.insert("", "end", values=values)
                continue

            saldo = calcular_saldo(id_) if id_ is not None else 0
            self.tabela.insert("", "end", values=(id_, nome or "", saldo))

    def janela_produto(self):
        JanelaCadastroProduto(self.root, self.carregar)

    def janela_movimento(self):
        JanelaMovimentacao(self.root, self.carregar)

    # ----------------------------------------
    # Filtrar tabela conforme pesquisa
    # ----------------------------------------
    def filtrar_tabela(self, event):
        termo = self.entry_pesquisa.get().strip().lower()
        if termo == "":
            self.atualizar_tabela(self.produtos_lista)
            return

        filtrados = []
        for p in self.produtos_lista:
            nome = p[1] if len(p) > 1 else ""
            if nome and termo in str(nome).lower():
                filtrados.append(p)

        self.atualizar_tabela(filtrados)


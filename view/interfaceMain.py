import tkinter as tk
from tkinter import ttk
from view.janela_produto import JanelaCadastroProduto
from view.janela_movimento import JanelaMovimentacao
from view.janela_movimentos_datas import JanelaMovimentacoes
from funcsEstoque import listar_produtos, calcular_saldo, listar_movimentacoes


class TelaPrincipal:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle de Estoque - Excel")
        self.root.geometry("1080x800")
        self.root.configure(bg="#f0f0f0")

        self.produtos_lista = []

        self.criar_titulo()
        self.criar_barra_superior()
        self.criar_tabela()
        self.criar_botoes()
        self.modo_tabela = "estoque"  # ou "movimentacoes"
        self.carregar()

    # ---------------- UI ----------------

    def criar_titulo(self):
        tk.Label(
            self.root,
            text="Controle de Estoque - UEPA",
            font=("Arial", 20, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)
    
    def criar_barra_superior(self):
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.pack(fill="x", padx=15, pady=5)

        # Pesquisa
        tk.Label(frame, text="Pesquisar:", bg="#f0f0f0").pack(side="left")

        self.entry_pesquisa = tk.Entry(frame)
        self.entry_pesquisa.pack(side="left", fill="x", expand=True, padx=10)
        self.entry_pesquisa.bind("<KeyRelease>", self.filtrar_e_ordenar)

        # Ordenação
        tk.Label(frame, text="Ordenar por:", bg="#f0f0f0").pack(side="left", padx=(10, 5))

        self.ordem_var = tk.StringVar(value="Nome (A-Z)")
        self.combo_ordem = ttk.Combobox(
            frame,
            textvariable=self.ordem_var,
            state="readonly",
            width=22,
            values=[
                "Nome (A-Z)",
                "ID",
                "Saldo (Maior → Menor)"
            ]
        )
        self.combo_ordem.pack(side="left")
        self.combo_ordem.bind("<<ComboboxSelected>>", self.filtrar_e_ordenar)

    def criar_tabela(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=15)

        self.tabela = ttk.Treeview(
            frame,
            columns=("id", "nome", "saldo"),
            show="headings",
            height=15
        )

        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Produto")
        self.tabela.heading("saldo", text="Saldo")

        self.tabela.column("id", width=60, anchor="center")
        self.tabela.column("nome", width=800, anchor="sw")
        self.tabela.column("saldo", width=120, anchor="center")

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scroll.set)

        self.tabela.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Zebra
        self.tabela.tag_configure("BlueRow", background="#E3F2FD")
        self.tabela.tag_configure("WhiteRow", background="#FFFFFF")

    def criar_botoes(self):
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.pack(pady=12)

        estilo = {"font": ("Arial", 11), "width": 20}

        tk.Button(frame, text="Cadastrar Produto",
                  command=self.janela_produto, **estilo).pack(side="left", padx=10)

        tk.Button(frame, text="Movimentar",
                  command=self.janela_movimento, **estilo).pack(side="left", padx=10)

        tk.Button(frame, text="Atualizar",
                  command=self.carregar, **estilo).pack(side="left", padx=10)
        tk.Button(
            frame,
            text="Ver Estoque",
            command=self.mostrar_estoque,
            **estilo
        ).pack(side="left", padx=5)

        tk.Button(
            frame,
            text="Ver Movimentações",
            command=self.janela_movimentacoes,
            **estilo
        ).pack(side="left", padx=10)



    # ---------------- Lógica ----------------

    def carregar(self):
        self.produtos_lista = listar_produtos() or []

        if self.modo_tabela == "estoque":
            self.atualizar_tabela_estoque()
        self.ordem_var.set("Nome (A-Z)")
        self.filtrar_e_ordenar()

    def filtrar_e_ordenar(self, event=None):
        termo = self.entry_pesquisa.get().lower().strip()
        ordem = self.ordem_var.get()

        lista = self.produtos_lista

        # Filtro por nome
        if termo:
            lista = [p for p in lista if termo in str(p[1]).lower()]

        # Ordenação
        if ordem == "Nome (A-Z)":
            lista.sort(key=lambda x: str(x[1]).lower())
        elif ordem == "ID":
            lista.sort(key=lambda x: x[0])
        elif ordem == "Saldo (Maior → Menor)":
            lista.sort(
                key=lambda x: calcular_saldo(x[0]) if x[0] else 0,
                reverse=True
            )

        self.atualizar_tabela(lista)

    def atualizar_tabela(self, lista):
        self.tabela.delete(*self.tabela.get_children())

        for index, linha in enumerate(lista):
            id_, nome = linha[0], linha[1]
            saldo = calcular_saldo(id_) if id_ else 0

            tag = "BlueRow" if index % 2 == 0 else "WhiteRow"

            self.tabela.insert(
                "",
                "end",
                values=(id_, nome or "", saldo),
                tags=(tag,)
            )

    def janela_produto(self):
        JanelaCadastroProduto(self.root, self.carregar)

    def janela_movimento(self):
        JanelaMovimentacao(self.root, self.carregar)
    
    def configurar_colunas(self, colunas, titulos, larguras):
        self.tabela.delete(*self.tabela.get_children())

        self.tabela["columns"] = colunas

        for col in colunas:
            self.tabela.heading(col, text="")
            self.tabela.column(col, width=0)

        for col, titulo, largura in zip(colunas, titulos, larguras):
            self.tabela.heading(col, text=titulo)
            self.tabela.column(col, width=largura, anchor="center")
    def mostrar_estoque(self):
        self.modo_tabela = "estoque"

        self.configurar_colunas(
            colunas=("id", "nome", "saldo"),
            titulos=("ID", "Produto", "Saldo"),
            larguras=(60, 800, 120)
        )

        self.atualizar_tabela_estoque()

    def atualizar_tabela_estoque(self):
        self.tabela.delete(*self.tabela.get_children())

        for index, linha in enumerate(self.produtos_lista):
            id_, nome = linha[0], linha[1]
            saldo = calcular_saldo(id_) if id_ else 0

            tag = "BlueRow" if index % 2 == 0 else "WhiteRow"

            self.tabela.insert(
                "",
                "end",
                values=(id_, nome, saldo),
                tags=(tag,)
            )

    def janela_movimentacoes(self):
        JanelaMovimentacoes(self.root)

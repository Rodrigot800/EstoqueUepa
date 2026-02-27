import tkinter as tk
from tkinter import ttk
from view.janela_produto import JanelaCadastroProduto
from view.janela_movimento import JanelaMovimentacao
from view.janela_movimentos_datas import JanelaMovimentacoes
from funcsEstoque import listar_produtos, calcular_saldos, listar_movimentacoes
from config import salvar_caminho_planilha
from funcsEstoque import set_arquivo
from funcsEstoque import selecionar_e_preparar_planilha
from config import carregar_caminho_planilha
from config import salvar_caminho_planilha

import os

class TelaPrincipal:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle de Estoque - Excel")
        self.root.geometry("1080x800")
        self.root.configure(bg="#f0f0f0")

        self.caminho_planilha = None
        self.titulo_var = tk.StringVar()
        self.planilha_var = tk.StringVar(value="Nenhuma planilha carregada")
        self.produtos_lista = []
        self.win_produtos = None
        self.win_movimento = None
        self.win_movimentos = None


        # 🔹 CRIA A INTERFACE PRIMEIRO
        self.criar_titulo()
        self.criar_barra_superior()
        self.criar_tabela()
        self.criar_botoes()

        # 🔹 DEPOIS carrega a planilha salva
        self.carregar_planilha_salva()



    # ---------------- UI ----------------

    def criar_titulo(self):
        self.titulo_var.set("Controle de Estoque - Nenhuma planilha carregada")

        self.label_titulo = tk.Label(
            self.root,
            textvariable=self.titulo_var,
            font=("Arial", 20, "bold"),
            bg="#f0f0f0"
        )
        self.label_titulo.pack(pady=10)


    
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
        self.combo_ordem.pack(side="left", padx=(0, 15))
        self.combo_ordem.bind("<<ComboboxSelected>>", self.filtrar_e_ordenar)

        # -----------------------------
        # PLANILHA
        # -----------------------------
        tk.Label(frame, text="Planilha:", bg="#f0f0f0").pack(side="left")

        self.entry_planilha = tk.Entry(
            frame,
            textvariable=self.planilha_var,
            state="readonly",
            width=30
        )

        tk.Button(
            frame,
            text="Selecionar",
            command=self.selecionar_planilha
        ).pack(side="left")


    def criar_tabela(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=15)

        self.tabela = ttk.Treeview(
            frame,
            columns=("id", "nome", "saldo", "saidaMes", "entradaMes"),
            show="headings",
            height=15
        )

        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Produto")
        self.tabela.heading("saldo", text="Saldo")
        self.tabela.heading("saidaMes", text="media_saida")
        self.tabela.heading("entradaMes", text="media_entrada")

        self.tabela.column("id", width=20, anchor="center")
        self.tabela.column("nome", width=250, anchor="sw")
        self.tabela.column("saldo", width=200, anchor="sw")
        self.tabela.column("saidaMes", width=200, anchor="sw")
        self.tabela.column("entradaMes", width=200, anchor="sw")


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
            text="Ver Movimentações",
            command=self.janela_movimentacoes,
            **estilo
        ).pack(side="left", padx=10)



    # ---------------- Lógica ----------------

    def carregar(self):
        self.produtos_lista = listar_produtos() or []
        self.ordem_var.set("Nome (A-Z)")
        self.filtrar_e_ordenar()

        
    def selecionar_planilha(self):
        caminho, nome = selecionar_e_preparar_planilha()

        if not caminho:
            return

        set_arquivo(caminho)
        salvar_caminho_planilha(caminho)  
        self.planilha_var.set(nome)
        self.atualizar_titulo()
        self.carregar()



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
            saldos = calcular_saldos()
            lista.sort(
                key=lambda x: saldos.get(x[0], 0),
                reverse=True
            )

        self.atualizar_tabela(lista)

    def atualizar_tabela(self, lista):
        self.tabela.delete(*self.tabela.get_children())

        for index, linha in enumerate(lista):
            id_, nome = linha[0], linha[1]
            saldo = calcular_saldos().get(id_, 0)

            tag = "BlueRow" if index % 2 == 0 else "WhiteRow"

            self.tabela.insert(
                "",
                "end",
                values=(id_, nome or "", saldo),
                tags=(tag,)
            )

    def janela_produto(self):
        if self.win_produtos and self.win_produtos.win.winfo_exists():
            self.win_produtos.win.lift()
            self.win_produtos.win.focus_force()
            return

        self.win_produtos = JanelaCadastroProduto(self.root, self.carregar)

        self.win_produtos.win.protocol(
            "WM_DELETE_WINDOW",
        self.fechar_win_produtos
         )
    def fechar_win_produtos(self):
        if self.win_produtos:
            self.win_produtos.win.destroy()
            self.win_produtos = None

    def janela_movimento(self):
        if self.win_movimento and self.win_movimento.win.winfo_exists():
            self.win_movimento.win.lift()
            self.win_movimento.win.focus_force()
            return

        self.win_movimento = JanelaMovimentacao(self.root, self.carregar)

        self.win_movimento.win.protocol(
            "WM_DELETE_WINDOW",
            self.fechar_janela_movimento
        )

    def fechar_janela_movimento(self):
        if self.win_movimento:
            self.win_movimento.win.destroy()
            self.win_movimento = None
            return
    
    def configurar_colunas(self, colunas, titulos, larguras):
        self.tabela.delete(*self.tabela.get_children())

        self.tabela["columns"] = colunas

        for col in colunas:
            self.tabela.heading(col, text="")
            self.tabela.column(col, width=0)

        for col, titulo, largura in zip(colunas, titulos, larguras):
            self.tabela.heading(col, text=titulo)
            self.tabela.column(col, width=largura, anchor="center")

    def janela_movimentacoes(self):
        if self.win_movimentos and self.win_movimentos.win.winfo_exists():
            self.win_movimentos.win.lift()
            self.win_movimentos.win.focus_force()
            return

        self.win_movimentos = JanelaMovimentacoes(self.root)

        self.win_movimentos.win.protocol(
            "WM_DELETE_WINDOW",
            self.fechar_janela_movimentacoes
        )

    def fechar_janela_movimentacoes(self):
        if self.win_movimentos:
            self.win_movimentos.win.destroy()
            self.win_movimentos = None

    def atualizar_titulo(self):
        caminho_salvo = carregar_caminho_planilha()
        nome = os.path.splitext(os.path.basename(caminho_salvo))[0]
        self.titulo_var.set(
            f"Controle de Estoque - {nome} "
        )
        
    def carregar_planilha_salva(self):
        caminho_salvo = carregar_caminho_planilha()

        if not caminho_salvo or not os.path.exists(caminho_salvo):
            return

        set_arquivo(caminho_salvo)

        nome = os.path.splitext(os.path.basename(caminho_salvo))[0]

        self.planilha_var.set(nome)
        self.atualizar_titulo()
        self.carregar()

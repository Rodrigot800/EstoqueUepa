import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from view.janela_produto import JanelaCadastroProduto
from view.janela_movimento import JanelaMovimentacao
from view.janela_movimentos_datas import JanelaMovimentacoes
from funcsEstoque import listar_produtos, calcular_saldos
from config import salvar_caminho_planilha
from funcsEstoque import set_arquivo
from funcsEstoque import selecionar_e_preparar_planilha
from config import carregar_caminho_planilha
from config import salvar_caminho_planilha

import os

import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

class TelaPrincipal:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle de Estoque - Excel")
        self.root.geometry("1080x800")

        self.caminho_planilha = None
        self.titulo_var = tk.StringVar()
        self.planilha_var = tk.StringVar(value="Nenhuma planilha carregada")
        self.produtos_lista = []
        self.win_produtos = None
        self.win_movimento = None
        self.win_movimentos = None

        # Interface
        self.criar_titulo()
        self.criar_barra_superior()
        self.criar_tabela()
        self.criar_botoes()

        self.carregar_planilha_salva()
       
    # ---------------- UI ----------------

    def criar_titulo(self):
        header = tb.Frame(self.root, bootstyle="primary")
        header.pack(fill="x")

        self.titulo_var.set("Controle de Estoque")

        tb.Label(
            header,
            textvariable=self.titulo_var,
            font=("Segoe UI", 24, "bold"),
            bootstyle="inverse-primary"
        ).pack(pady=(5, 5))


    def criar_barra_superior(self):
        container = tb.Frame(self.root)
        container.pack(fill="x", padx=20, pady=(5, 15))

        frame = tb.Labelframe(
            container,
            text=" 🔧 Filtros e Ações ",
            bootstyle="secondary"
        )
        frame.pack(fill="x")

        # ---- Pesquisa ----
        tb.Label(
            frame,
            text="🔍 Pesquisar",
            font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=0, padx=(10,4), pady=10, sticky="w")

        self.entry_pesquisa = tb.Entry(frame, width=120)
        self.entry_pesquisa.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.entry_pesquisa.bind("<KeyRelease>", self.filtrar_e_ordenar)

        # ---- Ordenação ----
        tb.Label(
            frame,
            text="↕️ Ordenar por",
            font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=2, padx=(20, 5), pady=10, sticky="w")

        self.ordem_var = tk.StringVar(value="Nome (A-Z)")
        self.combo_ordem = tb.Combobox(
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
        self.combo_ordem.grid(row=0, column=3, padx=5, pady=10)
        self.combo_ordem.bind("<<ComboboxSelected>>", lambda e: (
        self.filtrar_e_ordenar(e),
        self.root.focus()))
        
                # ---- Planilha ----
        tb.Label(
            frame,
            text="📂 Planilha",
            font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=4, padx=(20, 5), pady=10, sticky="w")

        self.entry_planilha = tb.Entry(
            frame,
            textvariable=self.planilha_var,
            state="readonly",
            width=28
        )
        self.entry_planilha.grid(row=0, column=5, padx=5, pady=10)

        tb.Button(
            frame,
            text="Selecionar",
            bootstyle="info-outline",
            command=self.selecionar_planilha
        ).grid(row=0, column=6, padx=10, pady=10)

        # Ajuste de colunas (responsivo)
        frame.columnconfigure(1, weight=1)

    def criar_tabela(self):
        frame = tb.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        style = tb.Style()

        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#f8fafc",
            foreground="#212529",
            padding=(18, 10),   # padding lateral maior → separação visual
            relief="flat",      # remove bordas reais
            borderwidth=0
        )

        style.configure(
            "Treeview",
            rowheight=34,
            font=("Segoe UI", 12),
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#212529"
        )


        style.map(
            "Treeview",
            background=[("selected", "#3a88fd")],
            foreground=[("selected", "#ffffff")]
        )

        self.tabela = ttk.Treeview(
            frame,
            columns=("id", "nome", "saldo", "saidaMes", "entradaMes"),
            show="headings",
            height=15
        )

        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Produto")
        self.tabela.heading("saldo", text="Saldo")
        self.tabela.heading("saidaMes", text="Média Saída")
        self.tabela.heading("entradaMes", text="Média Entrada")

        self.tabela.column("id", width=60, anchor="center")
        self.tabela.column("nome", width=300, anchor="w")
        self.tabela.column("saldo", width=150, anchor="w")
        self.tabela.column("saidaMes", width=150, anchor="e")
        self.tabela.column("entradaMes", width=150, anchor="e")

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scroll.set)

        self.tabela.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Estilo da tabela
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)

        self.tabela.tag_configure("BlueRow", background="#E3F2FD")
        self.tabela.tag_configure("WhiteRow", background="#FFFFFF")

    def criar_botoes(self):
        frame = tb.Frame(self.root)
        frame.pack(pady=18)

        estilo = {
            "width": 22,
            "padding": (12, 6)
        }

        tb.Button(
            frame,
            text="Cadastrar Produto",
            bootstyle="outline-primary",
            **estilo,
            command=self.janela_produto
        ).pack(side="left", padx=8)

        tb.Button(
            frame,
            text="Movimentar",
            bootstyle="outline-primary",
            **estilo,
            command=self.janela_movimento
        ).pack(side="left", padx=8)

        tb.Button(
            frame,
            text="Atualizar",
            bootstyle="outline-primary",
            **estilo,
            command=self.carregar
        ).pack(side="left", padx=8)

        tb.Button(
            frame,
            text="Ver Movimentações",
            bootstyle="outline-primary",
            **estilo,
            command=self.janela_movimentacoes
        ).pack(side="left", padx=8)
        
    # ---------------- Lógica ----------------

    def carregar(self):
        self.produtos_lista = listar_produtos() or []
        self.ordem_var.set("Nome (A-Z)")
        self.filtrar_e_ordenar()
        calcular_saldos() # pré-calcula os saldos para otimizar exibição

        
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
            lista.sort(key=lambda p: locale.strxfrm(str(p[1]).lower()))

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

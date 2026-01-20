import tkinter as tk
from tkinter import ttk
from funcsEstoque import listar_movimentacoes


class JanelaMovimentacoes:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Histórico de Movimentações")
        self.win.geometry("900x500")
        self.win.resizable(False, False)
        self.win.configure(bg="#fafafa")

        # -------- TÍTULO --------
        tk.Label(
            self.win,
            text="Histórico de Movimentações",
            font=("Arial", 16, "bold"),
            bg="#fafafa"
        ).pack(pady=10)

        # -------- TABELA --------
        frame = tk.Frame(self.win)
        frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.tabela = ttk.Treeview(
            frame,
            columns=( "produto", "tipo", "qtd" , "data" ),
            show="headings",
            height=15
        )

        self.tabela.heading("data", text="Data")
        self.tabela.heading("produto", text="Produto")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("qtd", text="Quantidade")

        self.tabela.column("data", width=150, anchor="center")
        self.tabela.column("produto", width=400, anchor="w")
        self.tabela.column("tipo", width=120, anchor="center")
        self.tabela.column("qtd", width=120, anchor="center")

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scroll.set)

        self.tabela.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Zebra
        self.tabela.tag_configure("BlueRow", background="#E3F2FD")
        self.tabela.tag_configure("WhiteRow", background="#FFFFFF")

        self.carregar()

    def carregar(self):
        movimentacoes = listar_movimentacoes() or []

        for index, mov in enumerate(movimentacoes):
            tag = "BlueRow" if index % 2 == 0 else "WhiteRow"

            # desempacotando apenas o que interessa
            _, _, produto_nome, tipo, quantidade, data = mov

            self.tabela.insert(
                "",
                "end",
                values=(produto_nome, tipo, quantidade, data),
                tags=(tag,)
            )


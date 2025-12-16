import tkinter as tk
from tkinter import ttk, messagebox
from funcsEstoque import listar_produtos, inserir_produto


class JanelaCadastroProduto:
    def __init__(self, parent, callback_reload):
        self.parent = parent
        self.callback_reload = callback_reload

        self.produtos_temp = []  # ← produtos adicionados antes de salvar

        self.win = tk.Toplevel(parent)
        self.win.geometry("420x500")
        self.win.resizable(False, False)
        self.win.configure(bg="#fafafa")

        # ---------------- TÍTULO ----------------
        tk.Label(
            self.win,
            text="Cadastrar novos produtos",
            font=("Arial", 14, "bold"),
            bg="#fafafa"
        ).pack(pady=10)

        # ---------------- NOME ----------------
        tk.Label(self.win, text="Nome:", bg="#fafafa").pack(anchor="w", padx=20)
        self.nome_var = tk.StringVar()
        self.nome_entry = tk.Entry(self.win, textvariable=self.nome_var)
        self.nome_entry.pack(fill="x", padx=20, pady=5)

        # Produtos já existentes
        self.nomes_existentes = {p[1].lower() for p in listar_produtos()}

        # ---------------- UNIDADE ----------------
        tk.Label(self.win, text="Unidade:", bg="#fafafa").pack(anchor="w", padx=20)
        self.unidade_var = tk.StringVar()
        self.unidade_entry = ttk.Combobox(self.win, textvariable=self.unidade_var)
        self.unidade_entry.pack(fill="x", padx=20, pady=5)

        self.unidade_entry["values"] = sorted({p[3] for p in listar_produtos()})

        # ---------------- BOTÃO ADICIONAR ----------------
        tk.Button(
            self.win,
            text="Adicionar",
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11),
            command=self.adicionar_produto
        ).pack(pady=10)

        # ---------------- TABELA ----------------
        tk.Label(self.win, text="Produtos adicionados:", bg="#fafafa") \
            .pack(anchor="w", padx=20)

        self.tabela = ttk.Treeview(
            self.win,
            columns=("nome", "unidade"),
            show="headings",
            height=8
        )

        self.tabela.heading("nome", text="Produto")
        self.tabela.heading("unidade", text="Unidade")

        self.tabela.column("nome", width=220)
        self.tabela.column("unidade", width=100, anchor="center")

        self.tabela.pack(fill="both", expand=True, padx=20, pady=5)

        # Tags de cor (igual à movimentação)
        self.tabela.tag_configure("BlueRow", background="#E3F2FD")
        self.tabela.tag_configure("WhiteRow", background="#FFFFFF")

        # ---------------- BOTÃO SALVAR TUDO ----------------
        tk.Button(
            self.win,
            text="Salvar Lista",
            bg="#2196F3",
            fg="white",
            font=("Arial", 11),
            command=self.salvar_todos
        ).pack(pady=15)

    # ----------------------------------------------------------
    # ADICIONAR PRODUTO NA TABELA
    # ----------------------------------------------------------
    def adicionar_produto(self):
        nome = self.nome_var.get().strip()
        unidade = self.unidade_var.get().strip()

        if not nome:
            messagebox.showerror("Erro", "O nome é obrigatório.")
            self.focar_janela()
            return

        if not unidade:
            messagebox.showerror("Erro", "Unidade é obrigatória.")
            self.focar_janela()
            return

        if nome.lower() in self.nomes_existentes:
            messagebox.showerror("Erro", f"O produto '{nome}' já existe.")
            self.focar_janela()
            return

        # Salva na lista temporária
        self.produtos_temp.append((nome, unidade))
        self.nomes_existentes.add(nome.lower())

        # Alternância de cores
        index = len(self.tabela.get_children())
        tag = "BlueRow" if index % 2 == 0 else "WhiteRow"

        self.tabela.insert(
            "",
            tk.END,
            values=(nome, unidade),
            tags=(tag,)
        )

        # Limpa campos
        self.nome_entry.delete(0, tk.END)
        self.unidade_entry.set("")
        self.nome_entry.focus_set()

    # ----------------------------------------------------------
    # SALVAR TODOS NO EXCEL
    # ----------------------------------------------------------
    def salvar_todos(self):
        if not self.produtos_temp:
            messagebox.showwarning("Aviso", "Nenhum produto adicionado.")
            self.focar_janela()
            return

        for nome, unidade in self.produtos_temp:
            inserir_produto(nome, "", unidade, 0)

        messagebox.showinfo("Sucesso", "Produtos cadastrados com sucesso!")
        self.callback_reload()
        self.win.destroy()

    def focar_janela(self):
        self.win.lift()
        self.win.focus_force()

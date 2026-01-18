import tkinter as tk
from tkinter import ttk, messagebox
from funcsEstoque import listar_produtos, inserir_produto


class JanelaCadastroProduto:
    def __init__(self, parent, callback_reload):
        self.parent = parent
        self.callback_reload = callback_reload

        self.produtos_temp = []  # ← produtos adicionados antes de salvar

        self.win = tk.Toplevel(parent)
        self.win.geometry("420x640")
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

        self.nomes_existentes = {
            str(p[1]).lower()
            for p in listar_produtos()
            if p[1] not in (None, "")
        }


        frame_inputs = tk.Frame(self.win, bg="#fafafa")
        frame_inputs.pack(fill="x", padx=20, pady=10)

        # ---------------- UNIDADE ----------------
        tk.Label(
            frame_inputs,
            text="Unidade:",
            bg="#fafafa"
        ).pack(side="left", padx=(0, 5))

        self.unidade_var = tk.StringVar()
        self.unidade_entry = ttk.Combobox(
            frame_inputs,
            textvariable=self.unidade_var,
            width=10
        )
        self.unidade_entry.pack(side="left", padx=(0, 20))

        self.unidade_entry["values"] = sorted({p[3] for p in listar_produtos()})

        # ---------------- QTD MÍNIMA ----------------
        tk.Label(
            frame_inputs,
            text="Quantidade Mínima:",
            bg="#fafafa"
        ).pack(side="left", padx=(0, 5))

        self.qtd_min_var = tk.StringVar(value="0")
        self.qtd_min_entry = tk.Entry(
            frame_inputs,
            textvariable=self.qtd_min_var,
            width=8
        )
        self.qtd_min_entry.pack(side="left")


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
            columns=("nome", "qtd_min", "unidade" ),
            show="headings",
            height=8
        )

        self.tabela.heading("nome", text="Produto")
        self.tabela.heading("qtd_min", text="Qtd_Min")
        self.tabela.heading("unidade", text="Unidade")
        

        self.tabela.column("nome", width=210)
        self.tabela.column("unidade", width=75, anchor="center")
        self.tabela.column("qtd_min", width=75, anchor="center")

        self.tabela.pack(fill="both", expand=True, padx=20, pady=5)

        # Tags de cor (igual à movimentação)
        self.tabela.tag_configure("BlueRow", background="#E3F2FD")
        self.tabela.tag_configure("WhiteRow", background="#FFFFFF")

        frame_buttons = tk.Frame(self.win, bg="#fafafa")
        frame_buttons.pack(pady=10)

        tk.Button(
            frame_buttons,
            text="Salvar Lista",
            bg="#2196F3",
            fg="white",
            font=("Arial", 11),
            width=20,
            command=self.salvar_todos
        ).pack(side="left", padx=5, pady=15)

        tk.Button(
            frame_buttons, 
            text="Remover Produto",
            bg="#f44336",
            fg="white",
            font=("Arial", 11),
            width=20,
            command=self.remover_produto
        ).pack(side="left", padx=5, pady=15)


    # ----------------------------------------------------------
    # ADICIONAR PRODUTO NA TABELA
    # ----------------------------------------------------------
    def adicionar_produto(self):
        nome = self.nome_var.get().strip()
        unidade = self.unidade_var.get().strip()
        qtd_min = self.qtd_min_var.get().strip()

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
        
        if not qtd_min:
            messagebox.showerror("Erro","quantidade mínima é obrigatória.")
            self.focar_janela()
            return
        
        if not qtd_min or not qtd_min.isdigit() or int(qtd_min) < 0:
            messagebox.showerror(
                "Erro",
                "Quantidade mínima deve ser um número inteiro maior ou igual a zero."
            )
            returngit 


        # Salva na lista temporária
        self.produtos_temp.append((nome, qtd_min, unidade))
        self.nomes_existentes.add(nome.lower())

        # Alternância de cores
        index = len(self.tabela.get_children())
        tag = "BlueRow" if index % 2 == 0 else "WhiteRow"

        self.tabela.insert(
            "",
            tk.END,
            values=(nome, qtd_min, unidade),
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

        for nome, unidade, qtd_min in self.produtos_temp:
            inserir_produto(nome, qtd_min, unidade, 0)

        messagebox.showinfo("Sucesso", "Produtos cadastrados com sucesso!")
        self.callback_reload()
        self.win.destroy()
    def remover_produto(self):

        selecionados = self.tabela.selection()

        if not selecionados:
            messagebox.showwarning(
                "Aviso",
                "Selecione pelo menos um produto para remover."
            )
            self.focar_janela()
            return

        for item_id in selecionados:
            valores = self.tabela.item(item_id, "values")
            nome = valores[0]

            # Remove da lista temporária
            self.produtos_temp = [
                p for p in self.produtos_temp if p[0] != nome
            ]

            # Remove da tabela
            self.tabela.delete(item_id)
        self.atualizar_cores()
    
    def atualizar_cores(self):
        for i, item in enumerate(self.tabela.get_children()):
            tag = "BlueRow" if i % 2 == 0 else "WhiteRow"
            self.tabela.item(item, tags=(tag,))


    def focar_janela(self):
        self.win.lift()
        self.win.focus_force()

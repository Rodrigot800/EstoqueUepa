import tkinter as tk
from tkinter import ttk, messagebox
from funcsEstoque import listar_produtos, registrar_movimento


class JanelaMovimentacao:
    def __init__(self, parent, callback_reload):
        self.parent = parent
        self.callback_reload = callback_reload
        
        self.movimentos = []  # ← lista que armazena as movimentações antes de registrar

        self.win = tk.Toplevel(parent)
        self.win.title("Movimentação de Estoque")
        self.win.geometry("420x600")
        self.win.configure(bg="#fafafa")

        tk.Label(self.win, text="Registrar movimento",
                 font=("Arial", 14, "bold"), bg="#fafafa").pack(pady=10)

        produtos = listar_produtos()

       # Produto
        tk.Label(self.win, text="Produto:", bg="#fafafa").pack(anchor="w", padx=20)

        produtos_formatados = [f"{p[0]} - {p[1]}" for p in produtos]
        self.todos_produtos = produtos_formatados

        self.produto_var = tk.StringVar()

        self.combo = ttk.Combobox(
            self.win,
            textvariable=self.produto_var
        )
        self.combo["values"] = self.todos_produtos
        self.combo.pack(fill="x", padx=20, pady=5)

        # Atualiza as opções quando digita
        self.produto_var.trace_add("write", self.autocomplete_produto)



        # Tipo
        tk.Label(self.win, text="Tipo:", bg="#fafafa").pack(anchor="w", padx=20)

        self.tipo = ttk.Combobox(
            self.win,
            values=["ENTRADA", "SAIDA"],
            state="readonly"   # ← impede digitação
        )

        self.tipo.set("ENTRADA")  # valor padrão

        self.tipo.pack(fill="x", padx=20, pady=5)


        # Quantidade
        tk.Label(self.win, text="Quantidade:", bg="#fafafa").pack(anchor="w", padx=20)
        self.qtd = tk.Entry(self.win)
        self.qtd.pack(fill="x", padx=20, pady=5)

        # Botão ADICIONAR
        tk.Button(
            self.win,
            text="Adicionar",
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11),
            command=self.adicionar_mov
        ).pack(pady=10)

       ## ---------------- TABELA DE MOVIMENTOS ----------------
        tk.Label(self.win, text="Movimentações adicionadas:", bg="#fafafa").pack(anchor="w", padx=20)

        self.tabela = ttk.Treeview(
            self.win,
            columns=("produto", "tipo", "qtd"),
            show="headings",
            height=8
        )

        self.tabela.heading("produto", text="Produto")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("qtd",  text="Qtd")

        self.tabela.column("produto", width=200)
        self.tabela.column("tipo",    width=80, anchor="center")
        self.tabela.column("qtd",     width=60, anchor="center")

        self.tabela.pack(fill="both", expand=True, padx=20, pady=5)

        # CONFIGURA AS TAGS DE COR AQUI, DEPOIS DA TABELA EXISTIR
        self.tabela.tag_configure("BlueRow", background="#E3F2FD")
        self.tabela.tag_configure("WhiteRow", background="#FFFFFF")


        # Botão REGISTRAR TUDO
        tk.Button(
            self.win,
            text="Registrar Tudo",
            bg="#2196F3",
            fg="white",
            font=("Arial", 11),
            command=self.registrar_tudo
        ).pack(pady=15)
    def autocomplete_produto(self, *_):
        
        texto = self.produto_var.get().lower()

        if not texto:
            filtrados = self.todos_produtos
        else:
            filtrados = [p for p in self.todos_produtos if texto in p.lower()]

        # Atualiza as opções do combobox
        self.combo["values"] = filtrados

        # Mantém o foco no próprio combobox
        self.win.after(1, lambda: self.combo.focus_set())


    # ----------------------------------------------------------
    # ADICIONAR MOVIMENTO NA LISTA, MAS NÃO SALVAR
    # ----------------------------------------------------------
    def adicionar_mov(self):
        try:
            produto_id = int(self.combo.get().split(" - ")[0])
            produto_nome = self.combo.get().split(" - ")[1]
        except:
            messagebox.showerror("Erro", "Selecione um produto válido.")
            return

        if not self.tipo.get():
            messagebox.showerror("Erro", "Selecione o tipo.")
            return

        if not self.qtd.get().isdigit():
            messagebox.showerror("Erro", "Quantidade deve ser número inteiro.")
            return

        qtd = int(self.qtd.get())

        # Salva internamente
        self.movimentos.append((produto_id, produto_nome, self.tipo.get(), qtd))

        # Número da próxima linha
        index = len(self.tabela.get_children())

        # Alternância de cores
        tag = "BlueRow" if index % 2 == 0 else "WhiteRow"

        # Insere com cor
        self.tabela.insert(
            "",
            tk.END,
            values=(produto_nome, self.tipo.get(), qtd),
            tags=(tag,)
        )

        # Limpa campos
        self.qtd.delete(0, tk.END)
        self.combo.delete(0, tk.END)

    # ----------------------------------------------------------
    # REGISTRAR TODAS AS MOVIMENTAÇÕES NO BANCO
    # ----------------------------------------------------------
    def registrar_tudo(self):
        if not self.movimentos:
            messagebox.showwarning("Aviso", "Nenhuma movimentação adicionada.")
            return
        
        for mov in self.movimentos:
            produto_id, nome, tipo, qtd = mov
            registrar_movimento(produto_id, tipo, qtd)

        messagebox.showinfo("Sucesso", "Movimentações registradas com sucesso!")

        self.callback_reload()
        self.win.destroy()

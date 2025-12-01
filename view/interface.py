import tkinter as tk
from tkinter import ttk, messagebox
from funcsEstoque import (
    listar_produtos,
    inserir_produto,
    registrar_movimento,
    calcular_saldo
)

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

    # ----------------------------------------
    # Janela cadastro de produto (corrigida)
    # ----------------------------------------
    def janela_produto(self):
        win = tk.Toplevel(self.root)
        win.title("Cadastrar Produto")
        win.geometry("350x360")
        win.configure(bg="#fafafa")

        tk.Label(
            win,
            text="Cadastrar novo produto",
            font=("Arial", 14, "bold"),
            bg="#fafafa"
        ).pack(pady=10)

        # ---------------- NOME ----------------
        tk.Label(win, text="Nome:", bg="#fafafa").pack(anchor="w", padx=20)
        nome_var = tk.StringVar()
        nome_entry = ttk.Combobox(win, textvariable=nome_var)
        nome_entry.pack(fill="x", padx=20, pady=5)

        nomes_existentes = sorted({p[1] for p in listar_produtos() if len(p) > 1 and p[1]})
        nome_entry["values"] = nomes_existentes

        def atualizar_sugestoes(*_):
            texto = nome_var.get().lower()
            if not texto:
                nome_entry["values"] = nomes_existentes
                return
            filtrados = [n for n in nomes_existentes if texto in n.lower()]
            nome_entry["values"] = filtrados

        nome_var.trace_add("write", atualizar_sugestoes)

        # ---------------- UNIDADE ----------------
        tk.Label(win, text="Unidade:", bg="#fafafa").pack(anchor="w", padx=20)
        unidade_var = tk.StringVar()
        unidade_entry = ttk.Combobox(win, textvariable=unidade_var)
        unidade_entry.pack(fill="x", padx=20, pady=5)

        unidades_existentes = sorted({p[3] for p in listar_produtos() if len(p) > 3 and p[3]})
        unidade_entry["values"] = unidades_existentes

        # ---------------- MÍNIMO ----------------
        tk.Label(win, text="Estoque mínimo (opcional):", bg="#fafafa").pack(anchor="w", padx=20)
        minimo_var = tk.StringVar()
        minimo_entry = tk.Entry(win, textvariable=minimo_var)
        minimo_entry.pack(fill="x", padx=20, pady=5)

        # ---------------- SALVAR ----------------
        def salvar_produto():
            nome = nome_var.get().strip()
            unidade = unidade_var.get().strip()
            minimo = minimo_var.get().strip()

            if not nome:
                messagebox.showerror("Erro", "O nome do produto é obrigatório.")
                return

            if not unidade:
                messagebox.showerror("Erro", "A unidade é obrigatória (ex: kg, ml, caixa).")
                return

            if minimo and not minimo.isdigit():
                messagebox.showerror("Erro", "O mínimo deve ser um número inteiro.")
                return

            minimo_int = int(minimo) if minimo else 0

            inserir_produto(nome, "", unidade, minimo_int)
            # atualiza a lista local para que sugestões reflitam novo produto
            self.carregar()
            win.destroy()

        btn = tk.Button(
            win,
            text="Salvar",
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11),
            width=20,
            command=salvar_produto
        )
        btn.pack(pady=20)

    # ----------------------------------------
    # Janela movimentação
    # ----------------------------------------
    def janela_movimento(self):
        win = tk.Toplevel(self.root)
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

        def salvar_mov():
            try:
                produto_id = int(str(combo.get()).split(" - ")[0])
            except Exception:
                messagebox.showerror("Erro", "Selecione um produto válido.")
                return

            if not tipo.get():
                messagebox.showerror("Erro", "Selecione o tipo (ENTRADA ou SAIDA).")
                return

            if not qtd.get().isdigit():
                messagebox.showerror("Erro", "Quantidade deve ser um número inteiro.")
                return

            registrar_movimento(produto_id, tipo.get(), int(qtd.get()))
            self.carregar()
            win.destroy()

        tk.Button(win, text="Registrar", bg="#2196F3", fg="white",
                  font=("Arial", 11), command=salvar_mov).pack(pady=15)

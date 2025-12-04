import tkinter as tk
from tkinter import ttk, messagebox
from funcsEstoque import listar_produtos, inserir_produto


class JanelaCadastroProduto:
    def __init__(self, parent, callback_reload):
        self.parent = parent
        self.callback_reload = callback_reload

        self.win = tk.Toplevel(parent)
        self.win.title("Cadastrar Produto")
        self.win.geometry("350x300")
        self.win.configure(bg="#fafafa")

        self.win.bind("<Return>", lambda event: self.salvar())


        tk.Label(
            self.win,
            text="Cadastrar novo produto",
            font=("Arial", 14, "bold"),
            bg="#fafafa"
        ).pack(pady=10)

        # ---------------- NOME ----------------
        tk.Label(self.win, text="Nome:", bg="#fafafa").pack(anchor="w", padx=20)
        self.nome_var = tk.StringVar()
        self.nome_entry = tk.Entry(self.win, textvariable=self.nome_var)
        self.nome_entry.pack(fill="x", padx=20, pady=5)

        # Lista de produtos existentes (somente nomes)
        self.nomes_existentes = {p[1].lower() for p in listar_produtos()}

        # ---------------- UNIDADE ----------------
        tk.Label(self.win, text="Unidade:", bg="#fafafa").pack(anchor="w", padx=20)
        self.unidade_var = tk.StringVar()
        self.unidade_entry = ttk.Combobox(self.win, textvariable=self.unidade_var)
        self.unidade_entry.pack(fill="x", padx=20, pady=5)

        self.unidades_existentes = sorted({p[3] for p in listar_produtos()})
        self.unidade_entry["values"] = self.unidades_existentes

        # ---------------- BOTÃO ----------------
        tk.Button(
            self.win,
            text="Salvar",
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11),
            width=20,
            command=self.salvar
        ).pack(pady=20)

    def salvar(self):
        nome = self.nome_var.get().strip()
        unidade = self.unidade_var.get().strip()

        if not nome:
            messagebox.showerror("Erro", "O nome é obrigatório.")
            return
        
        if not unidade:
            messagebox.showerror("Erro", "Unidade é obrigatória.")
            return

        # ---------- BLOQUEAR DUPLICADO ----------
        if nome.lower() in self.nomes_existentes:
            messagebox.showerror(
                "Erro",
                f"O produto '{nome}' já está cadastrado."
            )
            return

        # Salva com mínimo = 0 sempre
        inserir_produto(nome, "", unidade, 0)

        self.callback_reload()
        self.win.destroy()

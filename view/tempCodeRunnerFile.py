def mostrar_movimentacoes(self):
        # Limpa tabela atual
        self.tabela.delete(*self.tabela.get_children())

        # Muda colunas
        self.tabela["columns"] = ("data", "produto", "tipo", "qtd")

        self.tabela.heading("data", text="Data")
        self.tabela.heading("produto", text="Produto")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("qtd", text="Quantidade")

        self.tabela.column("data", width=150, anchor="center")
        self.tabela.column("produto", width=500, anchor="w")
        self.tabela.column("tipo", width=120, anchor="center")
        self.tabela.column("qtd", width=120, anchor="center")

        movimentacoes = listar_movimentacoes() or []

        for index, mov in enumerate(movimentacoes):
            tag = "BlueRow" if index % 2 == 0 else "WhiteRow"

            self.tabela.insert(
                "",
                "end",
                values=mov,
                tags=(tag,)
            )
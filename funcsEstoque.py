from openpyxl import load_workbook
from datetime import datetime
import os

ARQUIVO = "estoque.xlsx"

def carregar():
    if not os.path.exists(ARQUIVO):
        raise Exception("Arquivo estoque.xlsx não encontrado.")
    return load_workbook(ARQUIVO)

# ----------------------------
# PRODUTOS
# ----------------------------
def listar_produtos():
    wb = carregar()
    ws = wb["produtos"]

    produtos = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        produtos.append(row)

    wb.close()
    return produtos

def inserir_produto(nome, categoria, unidade, minimo):
    wb = carregar()
    ws = wb["produtos"]

    novo_id = ws.max_row  # simples: ID = linha
    ws.append([novo_id, nome, categoria, unidade, minimo])

    wb.save(ARQUIVO)
    wb.close()

# ----------------------------
# MOVIMENTOS
# ----------------------------
def listar_movimentos():
    wb = carregar()
    ws = wb["movimentos"]

    movimentos = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        movimentos.append(row)

    wb.close()
    return movimentos

def registrar_movimento(produto_id, tipo, quantidade):
    wb = carregar()
    ws = wb["movimentos"]

    novo_id = ws.max_row
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ws.append([novo_id, produto_id, tipo, quantidade, data])

    wb.save(ARQUIVO)
    wb.close()

# ----------------------------
# SALDO
# ----------------------------
def calcular_saldo(produto_id):
    movimentos = listar_movimentos()
    saldo = 0

    for _, pid, tipo, qtd, _ in movimentos:
        if pid == produto_id:
            if tipo == "ENTRADA":
                saldo += qtd
            else:
                saldo -= qtd

    return saldo

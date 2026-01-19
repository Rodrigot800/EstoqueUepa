import json
import os

CONFIG_FILE = "config.json"


def salvar_caminho_planilha(caminho):
    dados = {"planilha": caminho}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)


def carregar_caminho_planilha():
    if not os.path.exists(CONFIG_FILE):
        return None

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        dados = json.load(f)

    return dados.get("planilha")

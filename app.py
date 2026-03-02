import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from utils import resource_path
from tkinter import PhotoImage
from view.interfaceMain import TelaPrincipal


if __name__ == "__main__":
    root = tb.Window(
    themename="flatly",   # tema claro moderno
    title="Controle de Estoque",
    size=(1080, 800)
    )
    icon = PhotoImage(file=resource_path("assets/UepaEstoqueIcone.png"))
    root.iconphoto(True, icon)
    TelaPrincipal(root)
    root.mainloop()


#  pyinstaller \
#   --onefile \
#   --windowed \
#   --name EstoqueUEPA \
#   --icon assets/UepaEstoqueIcone.ico \
#   --add-data "assets;assets" \
#   app.py

import tkinter as tk
from utils import resource_path
from tkinter import PhotoImage
from view.interfaceMain import TelaPrincipal


if __name__ == "__main__":
    root = tk.Tk()
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

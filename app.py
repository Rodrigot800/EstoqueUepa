import tkinter as tk
import os
from view.interfaceMain import TelaPrincipal

root = tk.Tk()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(BASE_DIR, "assets", "UepaEstoqueIcone.png")

icon = tk.PhotoImage(file=icon_path)
root.iconphoto(True, icon)

app = TelaPrincipal(root)
root.mainloop()

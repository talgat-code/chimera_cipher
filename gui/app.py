import tkinter as tk
from tkinter import ttk
from .cipher_tab import CipherTab
from .analysis_tab import AnalysisTab


class ChimeraCipherApp:
    def __init__(self, root: tk.Tk) -> None:
        root.title("CHIMERA Cipher — Cryptography Project")
        root.geometry("700x600")
        root.minsize(600, 500)
        root.resizable(True, True)

        style = ttk.Style()
        style.configure("Success.TLabel", foreground="green")
        style.configure("Error.TLabel", foreground="red")

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=5, pady=5)

        tab1 = ttk.Frame(nb)
        tab2 = ttk.Frame(nb)
        nb.add(tab1, text="  Шифрование  ")
        nb.add(tab2, text="  Анализ  ")

        CipherTab(tab1, root)
        AnalysisTab(tab2)

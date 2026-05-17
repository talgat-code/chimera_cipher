import tkinter as tk
from tkinter import ttk
from . import theme as T
from .cipher_tab import CipherTab
from .analysis_tab import AnalysisTab
from .viz_tab import VizTab


class ChimeraCipherApp:
    def __init__(self, root: tk.Tk) -> None:
        root.title("CHIMERA Cipher — Cryptography Project")
        root.geometry("820x680")
        root.minsize(720, 580)
        root.resizable(True, True)

        T.setup(root)

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True)

        t1 = ttk.Frame(nb); t2 = ttk.Frame(nb); t3 = ttk.Frame(nb)
        nb.add(t1, text="   🔐  Шифрование   ")
        nb.add(t2, text="   🔬  Анализ   ")
        nb.add(t3, text="   🧬  Визуализация   ")

        CipherTab(t1, root)
        AnalysisTab(t2)
        VizTab(t3)

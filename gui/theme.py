import tkinter as tk
from tkinter import ttk

# ── Palette ──────────────────────────────────────────────────────────────────
BG      = "#F0F4F8"   # page background
CARD    = "#FFFFFF"   # card surface
BORDER  = "#D1D9E3"   # card border / separators
ACCENT  = "#4F46E5"   # indigo – primary
ACCENT2 = "#4338CA"   # indigo hover
SUCCESS = "#059669"   # emerald
ERROR   = "#E11D48"   # rose
TEXT    = "#0F172A"   # near-black
SUB     = "#64748B"   # slate-500, secondary text
INP_BG  = "#F8FAFC"   # text-area background


def setup(root: tk.Tk) -> None:
    """Apply the light theme to every ttk widget."""
    root.configure(bg=BG)
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure(".", background=BG, foreground=TEXT,
                font=("Segoe UI", 10), relief="flat")
    s.configure("TFrame",    background=BG)
    s.configure("TLabel",    background=BG, foreground=TEXT)
    s.configure("Card.TLabel",  background=CARD, foreground=TEXT)
    s.configure("Sub.TLabel",   background=CARD, foreground=SUB,
                font=("Segoe UI", 9))
    s.configure("Ok.TLabel",    background=BG, foreground=SUCCESS,
                font=("Segoe UI", 10, "bold"))
    s.configure("Err.TLabel",   background=BG, foreground=ERROR,
                font=("Segoe UI", 10, "bold"))

    s.configure("TNotebook", background=BG, tabmargins=[2, 4, 2, 0])
    s.configure("TNotebook.Tab", background="#E2E8F0", foreground=SUB,
                padding=[22, 9], font=("Segoe UI", 10))
    s.map("TNotebook.Tab",
          background=[("selected", ACCENT)],
          foreground=[("selected", "#FFFFFF")])

    s.configure("TEntry", fieldbackground=INP_BG, padding=[8, 6],
                relief="solid", bordercolor=BORDER, borderwidth=1)
    s.map("TEntry",
          bordercolor=[("focus", ACCENT)],
          fieldbackground=[("focus", CARD)])

    s.configure("TButton", background=CARD, foreground=TEXT,
                padding=[12, 6], bordercolor=BORDER, relief="solid",
                borderwidth=1)
    s.map("TButton",
          background=[("active", BG)],
          bordercolor=[("active", ACCENT)])

    s.configure("Accent.TButton", background=ACCENT, foreground="white",
                bordercolor=ACCENT, padding=[20, 10],
                font=("Segoe UI", 11, "bold"))
    s.map("Accent.TButton",
          background=[("active", ACCENT2), ("pressed", "#312E81")])

    s.configure("Go.TButton", background=SUCCESS, foreground="white",
                bordercolor=SUCCESS, padding=[20, 10],
                font=("Segoe UI", 11, "bold"))
    s.map("Go.TButton",
          background=[("active", "#047857"), ("pressed", "#065F46")])

    s.configure("TRadiobutton", background=BG, foreground=TEXT)
    s.configure("TProgressbar", background=ACCENT, troughcolor=BORDER,
                bordercolor=BORDER, thickness=8)
    s.configure("Fat.TProgressbar", background=ACCENT, troughcolor=BORDER,
                bordercolor=BORDER, thickness=16)
    s.configure("TScrollbar", background=BORDER, troughcolor=BG,
                bordercolor=BG, arrowcolor=SUB)


class Card(tk.Frame):
    """White rounded-look card: 1-px border frame wrapping a white inner frame."""

    def __init__(self, parent: tk.Widget, padx: int = 12,
                 pady: int = 10, **kw) -> None:
        self._bf = tk.Frame(parent, bg=BORDER)
        super().__init__(self._bf, bg=CARD, padx=padx, pady=pady, **kw)
        tk.Frame.pack(self, fill="both", expand=True)

    # Delegate geometry management to the border frame
    def pack(self, **kw) -> None:       self._bf.pack(**kw)
    def grid(self, **kw) -> None:       self._bf.grid(**kw)
    def place(self, **kw) -> None:      self._bf.place(**kw)
    def pack_forget(self) -> None:      self._bf.pack_forget()
    def grid_forget(self) -> None:      self._bf.grid_forget()

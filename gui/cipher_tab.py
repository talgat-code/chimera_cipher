import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from core import ChimeraCipher
from . import theme as T


def _key_strength(key: str) -> tuple[int, str, str]:
    """Return (score 0-100, label, color)."""
    if not key:
        return 0, "—", T.SUB
    s = min(len(key) * 5, 40)
    if any(c.islower() for c in key): s += 10
    if any(c.isupper() for c in key): s += 10
    if any(c.isdigit() for c in key): s += 10
    if any(not c.isalnum() for c in key): s += 10
    if len(key) >= 16: s = min(s + 20, 100)
    if s < 30: return s, "Weak",   "#EF4444"
    if s < 55: return s, "Fair",   "#F59E0B"
    if s < 80: return s, "Good",   "#10B981"
    return s,           "Strong", "#059669"


class CipherTab:
    def __init__(self, frame: ttk.Frame, root: tk.Tk) -> None:
        self._root = root
        self._file_path = ""
        self._build(frame)

    def _build(self, f) -> None:
        # Header
        hdr = tk.Frame(f, bg=T.ACCENT, height=54)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="  🔐  CHIMERA Cipher", bg=T.ACCENT, fg="white",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=14, pady=14)

        # Key card
        kc = T.Card(f); kc.pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(kc, text="SECRET KEY", bg=T.CARD, fg=T.SUB,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        kr = tk.Frame(kc, bg=T.CARD); kr.pack(fill="x", pady=(4, 0))
        self._key = tk.StringVar()
        self._key.trace_add("write", lambda *_: self._on_key())
        self._key_e = ttk.Entry(kr, textvariable=self._key, show="*",
                                font=("Segoe UI", 11))
        self._key_e.pack(side="left", fill="x", expand=True)
        self._show_key = False
        ttk.Button(kr, text="👁", width=3,
                   command=self._toggle_key).pack(side="left", padx=(6, 0))
        srow = tk.Frame(kc, bg=T.CARD); srow.pack(fill="x", pady=(6, 0))
        self._str_bar = ttk.Progressbar(srow, length=120, mode="determinate",
                                        maximum=100)
        self._str_bar.pack(side="left")
        self._str_lbl = tk.Label(srow, text="—", bg=T.CARD, fg=T.SUB,
                                  font=("Segoe UI", 9))
        self._str_lbl.pack(side="left", padx=(8, 0))

        # Mode
        mf = tk.Frame(f, bg=T.BG); mf.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(mf, text="MODE:", bg=T.BG, fg=T.SUB,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 8))
        self._mode = tk.StringVar(value="text")
        ttk.Radiobutton(mf, text="Text", variable=self._mode, value="text",
                        command=self._on_mode).pack(side="left")
        ttk.Radiobutton(mf, text="File", variable=self._mode, value="file",
                        command=self._on_mode).pack(side="left", padx=(12, 0))

        # 3-column I/O area
        io = tk.Frame(f, bg=T.BG)
        io.pack(fill="both", expand=True, padx=12, pady=4)
        io.columnconfigure(0, weight=1); io.columnconfigure(2, weight=1)
        io.rowconfigure(0, weight=1)

        # Input card
        ic = T.Card(io, padx=10, pady=8); ic.grid(row=0, column=0, sticky="nsew")
        tk.Label(ic, text="INPUT", bg=T.CARD, fg=T.SUB,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self._inp_wrap = tk.Frame(ic, bg=T.CARD)
        self._inp_wrap.pack(fill="both", expand=True, pady=(4, 0))
        self._inp = scrolledtext.ScrolledText(
            self._inp_wrap, height=8, wrap="word", relief="flat",
            bg=T.INP_BG, font=("Segoe UI", 10), borderwidth=0)
        self._inp.pack(fill="both", expand=True)
        self._file_frame = tk.Frame(self._inp_wrap, bg=T.CARD)
        self._file_lbl = tk.Label(self._file_frame, text="No file selected",
                                   bg=T.CARD, fg=T.SUB, font=("Segoe UI", 9))
        self._file_lbl.pack(anchor="w", pady=(0, 6))
        ttk.Button(self._file_frame, text="📂  Browse…",
                   command=self._load_file).pack(anchor="w")

        # Center buttons
        mid = tk.Frame(io, bg=T.BG, width=148)
        mid.grid(row=0, column=1, padx=8); mid.pack_propagate(False)
        bc = tk.Frame(mid, bg=T.BG)
        bc.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Button(bc, text="🔒  ENCRYPT",
                   style="Accent.TButton",
                   command=self._encrypt).pack(fill="x", pady=(0, 10))
        ttk.Button(bc, text="🔓  DECRYPT",
                   style="Go.TButton",
                   command=self._decrypt).pack(fill="x")

        # Output card
        oc = T.Card(io, padx=10, pady=8); oc.grid(row=0, column=2, sticky="nsew")
        oh = tk.Frame(oc, bg=T.CARD); oh.pack(fill="x")
        tk.Label(oh, text="OUTPUT", bg=T.CARD, fg=T.SUB,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        ttk.Button(oh, text="💾", command=self._save).pack(side="right")
        ttk.Button(oh, text="📋", command=self._copy).pack(side="right", padx=(0, 4))
        self._out = scrolledtext.ScrolledText(
            oc, height=8, wrap="word", relief="flat",
            bg=T.INP_BG, font=("Segoe UI", 10), state="disabled", borderwidth=0)
        self._out.pack(fill="both", expand=True, pady=(4, 0))

        # Status bar
        sb = tk.Frame(f, bg=T.BG); sb.pack(fill="x", padx=12, pady=(4, 10))
        self._dot = tk.Label(sb, text="●", bg=T.BG, fg=T.SUB, font=("Segoe UI", 14))
        self._dot.pack(side="left")
        self._status = tk.StringVar(value="Ready")
        tk.Label(sb, textvariable=self._status, bg=T.BG, fg=T.SUB,
                 font=("Segoe UI", 10)).pack(side="left", padx=(4, 0))

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _set_status(self, msg: str, ok: bool | None = None) -> None:
        self._status.set(msg)
        self._dot.configure(fg={True: T.SUCCESS, False: T.ERROR, None: T.SUB}[ok])

    def _on_key(self) -> None:
        score, label, color = _key_strength(self._key.get())
        self._str_bar["value"] = score
        self._str_lbl.configure(text=label, fg=color)

    def _toggle_key(self) -> None:
        self._show_key = not self._show_key
        self._key_e.configure(show="" if self._show_key else "*")

    def _on_mode(self) -> None:
        if self._mode.get() == "file":
            self._inp.pack_forget()
            self._file_frame.pack(fill="both", expand=True)
        else:
            self._file_frame.pack_forget()
            self._inp.pack(fill="both", expand=True)

    def _load_file(self) -> None:
        path = filedialog.askopenfilename()
        if path:
            self._file_path = path
            self._file_lbl.configure(text=path, fg=T.TEXT)

    def _get_key(self) -> str | None:
        k = self._key.get()
        if not k:
            self._set_status("Enter a key first", ok=False)
            return None
        return k

    def _set_out(self, text: str) -> None:
        self._out.configure(state="normal")
        self._out.delete("1.0", "end")
        self._out.insert("1.0", text)
        self._out.configure(state="disabled")

    # ── Actions ──────────────────────────────────────────────────────────────
    def _encrypt(self) -> None:
        key = self._get_key()
        if not key: return
        c = ChimeraCipher(key)
        try:
            if self._mode.get() == "text":
                text = self._inp.get("1.0", "end-1c")
                if not text.strip():
                    self._set_status("Input is empty", ok=False); return
                self._set_out(c.encrypt(text))
                self._set_status("Encrypted successfully ✓", ok=True)
            else:
                if not self._file_path:
                    self._set_status("Select a file first", ok=False); return
                out = self._file_path + ".chimera"
                c.encrypt_file(self._file_path, out)
                self._set_out(out); self._set_status(f"Saved → {out}", ok=True)
        except Exception as e:
            self._set_status(str(e), ok=False)

    def _decrypt(self) -> None:
        key = self._get_key()
        if not key: return
        c = ChimeraCipher(key)
        try:
            if self._mode.get() == "text":
                text = self._inp.get("1.0", "end-1c").strip()
                if not text:
                    self._set_status("Input is empty", ok=False); return
                self._set_out(c.decrypt(text))
                self._set_status("Decrypted successfully ✓", ok=True)
            else:
                if not self._file_path:
                    self._set_status("Select a file first", ok=False); return
                out = self._file_path.removesuffix(".chimera")
                if out == self._file_path: out += ".dec"
                c.decrypt_file(self._file_path, out)
                self._set_out(out); self._set_status(f"Saved → {out}", ok=True)
        except ValueError:
            self._set_status("Decryption failed — wrong key?", ok=False)
        except Exception as e:
            self._set_status(str(e), ok=False)

    def _copy(self) -> None:
        self._out.configure(state="normal")
        text = self._out.get("1.0", "end-1c")
        self._out.configure(state="disabled")
        if text:
            self._root.clipboard_clear(); self._root.clipboard_append(text)
            self._set_status("Copied to clipboard ✓", ok=True)

    def _save(self) -> None:
        self._out.configure(state="normal")
        text = self._out.get("1.0", "end-1c")
        self._out.configure(state="disabled")
        if not text:
            self._set_status("Nothing to save", ok=False); return
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            with open(path, "w", encoding="utf-8") as fh: fh.write(text)
            self._set_status(f"Saved → {path}", ok=True)

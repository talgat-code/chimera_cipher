import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from core import ChimeraCipher


class CipherTab:
    def __init__(self, frame: ttk.Frame, root: tk.Tk) -> None:
        self._root = root
        self._file_path: str = ""
        self._build(frame)

    def _build(self, f: ttk.Frame) -> None:
        ttk.Label(f, text="CHIMERA Cipher", font=("", 13, "bold")).pack(pady=(8, 4))

        kf = ttk.Frame(f)
        kf.pack(fill="x", padx=10, pady=3)
        ttk.Label(kf, text="Key:").pack(side="left")
        self._key = tk.StringVar()
        self._key_e = ttk.Entry(kf, textvariable=self._key, show="*")
        self._key_e.pack(side="left", padx=5, fill="x", expand=True)
        self._show = False
        ttk.Button(kf, text="👁", width=3, command=self._toggle_key).pack(side="left")

        mf = ttk.Frame(f)
        mf.pack(fill="x", padx=10, pady=3)
        self._mode = tk.StringVar(value="text")
        ttk.Radiobutton(mf, text="Text", variable=self._mode, value="text",
                        command=self._on_mode).pack(side="left")
        ttk.Radiobutton(mf, text="File", variable=self._mode, value="file",
                        command=self._on_mode).pack(side="left", padx=8)

        ttk.Label(f, text="Input:").pack(anchor="w", padx=10)
        self._inp_container = ttk.Frame(f)
        self._inp_container.pack(fill="both", expand=True, padx=10, pady=(0, 3))

        self._inp_text = scrolledtext.ScrolledText(
            self._inp_container, height=5, wrap="word")
        self._inp_text.pack(fill="both", expand=True)

        self._inp_file_frame = ttk.Frame(self._inp_container)
        self._file_lbl = ttk.Label(self._inp_file_frame,
                                   text="No file selected", foreground="gray")
        self._file_lbl.pack(side="left", padx=5)
        ttk.Button(self._inp_file_frame, text="Load File…",
                   command=self._load_file).pack(side="left")

        bf = ttk.Frame(f)
        bf.pack(fill="x", padx=10, pady=3)
        ttk.Button(bf, text="🔒  ENCRYPT", command=self._encrypt).pack(
            side="left", expand=True, fill="x", padx=(0, 3))
        ttk.Button(bf, text="🔓  DECRYPT", command=self._decrypt).pack(
            side="left", expand=True, fill="x")

        ttk.Label(f, text="Output:").pack(anchor="w", padx=10)
        self._out = scrolledtext.ScrolledText(f, height=5, wrap="word",
                                              state="disabled")
        self._out.pack(fill="both", expand=True, padx=10, pady=(0, 3))

        cf = ttk.Frame(f)
        cf.pack(fill="x", padx=10, pady=(0, 4))
        ttk.Button(cf, text="Copy to Clipboard",
                   command=self._copy).pack(side="left", padx=(0, 4))
        ttk.Button(cf, text="Save to File…", command=self._save).pack(side="left")

        self._status = tk.StringVar(value="Status: Ready")
        self._status_lbl = ttk.Label(f, textvariable=self._status)
        self._status_lbl.pack(fill="x", padx=10, pady=(0, 5))

    def _set_status(self, msg: str, ok: bool | None = None) -> None:
        self._status.set(f"Status: {msg}")
        self._status_lbl.configure(
            foreground={True: "green", False: "red"}.get(ok, ""))  # type: ignore[arg-type]

    def _toggle_key(self) -> None:
        self._show = not self._show
        self._key_e.configure(show="" if self._show else "*")

    def _on_mode(self) -> None:
        if self._mode.get() == "file":
            self._inp_text.pack_forget()
            self._inp_file_frame.pack(fill="x", pady=10)
        else:
            self._inp_file_frame.pack_forget()
            self._inp_text.pack(fill="both", expand=True)

    def _load_file(self) -> None:
        path = filedialog.askopenfilename()
        if path:
            self._file_path = path
            self._file_lbl.configure(text=path, foreground="")

    def _get_key(self) -> str | None:
        k = self._key.get().strip()
        if not k:
            self._set_status("Enter a key first", ok=False)
            return None
        return k

    def _set_out(self, text: str) -> None:
        self._out.configure(state="normal")
        self._out.delete("1.0", "end")
        self._out.insert("1.0", text)
        self._out.configure(state="disabled")

    def _encrypt(self) -> None:
        key = self._get_key()
        if not key:
            return
        c = ChimeraCipher(key)
        try:
            if self._mode.get() == "text":
                text = self._inp_text.get("1.0", "end-1c")
                if not text.strip():
                    self._set_status("Input is empty", ok=False)
                    return
                self._set_out(c.encrypt(text))
                self._set_status("Encrypted successfully", ok=True)
            else:
                if not self._file_path:
                    self._set_status("Select a file first", ok=False)
                    return
                out = self._file_path + ".chimera"
                c.encrypt_file(self._file_path, out)
                self._set_out(out)
                self._set_status(f"Saved → {out}", ok=True)
        except Exception as e:
            self._set_status(str(e), ok=False)

    def _decrypt(self) -> None:
        key = self._get_key()
        if not key:
            return
        c = ChimeraCipher(key)
        try:
            if self._mode.get() == "text":
                text = self._inp_text.get("1.0", "end-1c").strip()
                if not text:
                    self._set_status("Input is empty", ok=False)
                    return
                self._set_out(c.decrypt(text))
                self._set_status("Decrypted successfully", ok=True)
            else:
                if not self._file_path:
                    self._set_status("Select a file first", ok=False)
                    return
                out = self._file_path.removesuffix(".chimera")
                if out == self._file_path:
                    out += ".dec"
                c.decrypt_file(self._file_path, out)
                self._set_out(out)
                self._set_status(f"Saved → {out}", ok=True)
        except ValueError:
            self._set_status("Decryption failed — wrong key?", ok=False)
        except Exception as e:
            self._set_status(str(e), ok=False)

    def _copy(self) -> None:
        self._out.configure(state="normal")
        text = self._out.get("1.0", "end-1c")
        self._out.configure(state="disabled")
        if text:
            self._root.clipboard_clear()
            self._root.clipboard_append(text)
            self._set_status("Copied to clipboard", ok=True)

    def _save(self) -> None:
        self._out.configure(state="normal")
        text = self._out.get("1.0", "end-1c")
        self._out.configure(state="disabled")
        if not text:
            self._set_status("Nothing to save", ok=False)
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            self._set_status(f"Saved → {path}", ok=True)

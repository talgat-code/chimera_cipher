import math
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from core import ChimeraCipher
from analysis.security_analysis import SecurityAnalyzer
from . import theme as T


class AnalysisTab:
    def __init__(self, frame: ttk.Frame) -> None:
        self._frame = frame
        self._build(frame)

    def _build(self, f) -> None:
        # Header
        hdr = tk.Frame(f, bg="#0891B2", height=54)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="  🔬  Security Analysis", bg="#0891B2", fg="white",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=14, pady=14)

        # Run button + progress bar
        ctrl = tk.Frame(f, bg=T.BG)
        ctrl.pack(fill="x", padx=12, pady=10)
        self._run_btn = ttk.Button(ctrl, text="▶  Run All Tests",
                                   style="Accent.TButton", command=self._run)
        self._run_btn.pack(side="left")
        pf = tk.Frame(ctrl, bg=T.BG)
        pf.pack(side="left", fill="x", expand=True, padx=(14, 0))
        self._progress = ttk.Progressbar(pf, mode="determinate",
                                         maximum=100, style="Fat.TProgressbar")
        self._progress.pack(fill="x")
        self._prog_lbl = tk.Label(pf, text="", bg=T.BG, fg=T.SUB,
                                   font=("Segoe UI", 8))
        self._prog_lbl.pack(anchor="w", pady=(2, 0))

        # ── 4 metric cards in 2×2 grid ───────────────────────────────────────
        g = tk.Frame(f, bg=T.BG)
        g.pack(fill="x", padx=12, pady=4)
        g.columnconfigure(0, weight=1); g.columnconfigure(1, weight=1)

        def _mcard(row, col, title):
            c = T.Card(g, padx=10, pady=10)
            c.grid(row=row, column=col, sticky="ew",
                   padx=(0, 5) if col == 0 else (5, 0), pady=4)
            tk.Label(c, text=title, bg=T.CARD, fg=T.SUB,
                     font=("Segoe UI", 8, "bold")).pack(anchor="w")
            return c

        # Avalanche
        ac = _mcard(0, 0, "AVALANCHE EFFECT")
        self._av_val = tk.Label(ac, text="—", bg=T.CARD, fg=T.TEXT,
                                 font=("Segoe UI", 26, "bold"))
        self._av_val.pack(anchor="w")
        self._av_bar = ttk.Progressbar(ac, mode="determinate", maximum=100,
                                        length=220)
        self._av_bar.pack(anchor="w", pady=(4, 2))
        tk.Label(ac, text="ideal ≈ 50%  (1-bit input → ~half output bits flip)",
                 bg=T.CARD, fg=T.SUB, font=("Segoe UI", 8)).pack(anchor="w")

        # Key space
        kc = _mcard(0, 1, "KEY SPACE  (16-char key)")
        self._ks_val = tk.Label(kc, text="—", bg=T.CARD, fg=T.TEXT,
                                 font=("Segoe UI", 20, "bold"), wraplength=220)
        self._ks_val.pack(anchor="w")
        self._ks_sub = tk.Label(kc, text="", bg=T.CARD, fg=T.SUB,
                                 font=("Segoe UI", 9))
        self._ks_sub.pack(anchor="w", pady=(4, 0))

        # Frequency
        fc = _mcard(1, 0, "FREQUENCY RESISTANCE")
        self._fr_val = tk.Label(fc, text="—", bg=T.CARD, fg=T.TEXT,
                                 font=("Segoe UI", 18, "bold"))
        self._fr_val.pack(anchor="w")
        self._fr_sub = tk.Label(fc, text="", bg=T.CARD, fg=T.SUB,
                                 font=("Segoe UI", 9))
        self._fr_sub.pack(anchor="w", pady=(4, 0))

        # Brute-force
        bc = _mcard(1, 1, "BRUTE-FORCE ESTIMATE  (16-char key)")
        self._bf_val = tk.Label(bc, text="—", bg=T.CARD, fg=T.TEXT,
                                 font=("Segoe UI", 18, "bold"))
        self._bf_val.pack(anchor="w")
        self._bf_sub = tk.Label(bc, text="", bg=T.CARD, fg=T.SUB,
                                 font=("Segoe UI", 9))
        self._bf_sub.pack(anchor="w", pady=(4, 0))

        # Comparison table
        tc = T.Card(f, padx=10, pady=8)
        tc.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        tk.Label(tc, text="CIPHER COMPARISON", bg=T.CARD, fg=T.SUB,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self._table = scrolledtext.ScrolledText(
            tc, height=8, font=("Courier New", 9),
            state="disabled", wrap="none",
            bg=T.INP_BG, relief="flat", borderwidth=0)
        self._table.pack(fill="both", expand=True, pady=(6, 0))

    # ── Threading ─────────────────────────────────────────────────────────────
    def _post(self, fn) -> None:
        self._frame.after(0, fn)

    def _run(self) -> None:
        self._run_btn.configure(state="disabled")
        self._progress["value"] = 0
        self._prog_lbl.configure(text="Starting…")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self) -> None:
        sa = SecurityAnalyzer(ChimeraCipher("AnalysisKey"))

        av = sa.avalanche_test(300)
        self._post(lambda: self._set_avalanche(av))

        ks = sa.key_space_report()
        self._post(lambda: self._set_keyspace(ks))

        fa = sa.frequency_analysis()
        self._post(lambda: self._set_freq(fa))

        bf = sa.brute_force_estimate(16)
        tbl = sa.comparison_table()
        self._post(lambda: self._set_brute(bf, tbl))

    # ── Updaters (called on main thread via after) ────────────────────────────
    def _set_avalanche(self, av: dict) -> None:
        color = T.SUCCESS if av["avg_pct"] > 40 else T.ERROR
        self._av_val.configure(text=f"{av['avg_pct']:.1f}%", fg=color)
        self._av_bar["value"] = av["avg_pct"]
        self._set_prog(25, "Key space…")

    def _set_keyspace(self, ks: dict) -> None:
        v = ks["16_chars"]
        self._ks_val.configure(text=f"{v['keys']:.2e}")
        self._ks_sub.configure(text=f"≈ {v['bits']:.0f} bits of security  "
                                     f"(AES-256 = 256 bits)")
        self._set_prog(50, "Frequency analysis…")

    def _set_freq(self, fa: dict) -> None:
        self._fr_val.configure(text=f"{fa['unique_bytes']}/256 unique bytes")
        self._fr_sub.configure(text=f"Shannon entropy: {fa['entropy']:.2f} / 8.0 bits/byte")
        self._set_prog(75, "Brute-force estimate…")

    def _set_brute(self, bf: dict, tbl: str) -> None:
        exp = math.log10(max(bf["years"], 1))
        self._bf_val.configure(text=f"~10^{exp:.0f} years")
        self._bf_sub.configure(text=f"{bf['single_enc_us']:.2f} µs/enc on this machine")
        self._table.configure(state="normal")
        self._table.delete("1.0", "end")
        self._table.insert("1.0", tbl)
        self._table.configure(state="disabled")
        self._set_prog(100, "Complete ✓")
        self._run_btn.configure(state="normal")

    def _set_prog(self, val: int, label: str = "") -> None:
        self._progress["value"] = val
        self._prog_lbl.configure(text=label)

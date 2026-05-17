import math
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from core import ChimeraCipher
from analysis.security_analysis import SecurityAnalyzer


class AnalysisTab:
    def __init__(self, frame: ttk.Frame) -> None:
        self._frame = frame
        self._build(frame)

    def _build(self, f: ttk.Frame) -> None:
        ttk.Label(f, text="Security Analysis",
                  font=("", 13, "bold")).pack(pady=(8, 4))

        ctrl = ttk.Frame(f)
        ctrl.pack(fill="x", padx=10, pady=4)
        self._run_btn = ttk.Button(ctrl, text="▶  Run All Tests",
                                   command=self._run)
        self._run_btn.pack(side="left")
        self._progress = ttk.Progressbar(ctrl, mode="determinate",
                                         maximum=100, length=300)
        self._progress.pack(side="left", padx=10, fill="x", expand=True)

        stats = ttk.Frame(f)
        stats.pack(fill="x", padx=10, pady=4)

        self._av_lbl = ttk.Label(stats, text="Avalanche effect: —")
        self._av_lbl.grid(row=0, column=0, sticky="w", pady=1)
        self._av_bar = ttk.Progressbar(stats, mode="determinate",
                                       maximum=100, length=320)
        self._av_bar.grid(row=1, column=0, sticky="w", pady=(0, 6))

        self._ks_lbl = ttk.Label(stats, text="Key space (16 chars): —")
        self._ks_lbl.grid(row=2, column=0, sticky="w", pady=1)

        self._freq_lbl = ttk.Label(stats, text="Frequency resistance: —")
        self._freq_lbl.grid(row=3, column=0, sticky="w", pady=1)

        self._bf_lbl = ttk.Label(stats, text="Brute-force time (16-char key): —")
        self._bf_lbl.grid(row=4, column=0, sticky="w", pady=1)

        ttk.Label(f, text="Comparison with classical ciphers:").pack(
            anchor="w", padx=10, pady=(8, 2))
        self._table = scrolledtext.ScrolledText(
            f, height=10, font=("Courier New", 8), state="disabled", wrap="none")
        self._table.pack(fill="both", expand=True, padx=10, pady=(0, 8))

    def _post(self, fn) -> None:
        self._frame.after(0, fn)

    def _run(self) -> None:
        self._run_btn.configure(state="disabled")
        self._progress["value"] = 0
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
        table = sa.comparison_table()
        self._post(lambda: self._set_brute(bf, table))

    def _set_avalanche(self, av: dict) -> None:
        self._av_lbl.configure(
            text=(f"Avalanche effect:  {av['avg_pct']:.1f}%"
                  f"  (min {av['min']} / max {av['max']} bits out of 128)"))
        self._av_bar["value"] = av["avg_pct"]
        self._progress["value"] = 25

    def _set_keyspace(self, ks: dict) -> None:
        v = ks["16_chars"]
        self._ks_lbl.configure(
            text=f"Key space (16 chars):  {v['keys']:.2e}  (~{v['bits']:.0f} bits)")
        self._progress["value"] = 50

    def _set_freq(self, fa: dict) -> None:
        self._freq_lbl.configure(
            text=(f"Frequency resistance:  "
                  f"Unique bytes: {fa['unique_bytes']}/256  "
                  f"Entropy: {fa['entropy']:.2f}/8.0"))
        self._progress["value"] = 75

    def _set_brute(self, bf: dict, table: str) -> None:
        exp = math.log10(max(bf["years"], 1))
        self._bf_lbl.configure(
            text=(f"Brute-force time (16-char key):  ~10^{exp:.0f} years"
                  f"  ({bf['single_enc_us']:.2f} µs/enc)"))
        self._table.configure(state="normal")
        self._table.delete("1.0", "end")
        self._table.insert("1.0", table)
        self._table.configure(state="disabled")
        self._progress["value"] = 100
        self._run_btn.configure(state="normal")

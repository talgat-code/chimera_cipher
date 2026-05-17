"""
Feistel Network Visualizer — draws every round as colored hex-byte grids.
Changed bytes (vs previous round) are highlighted in amber.
"""
import colorsys
import tkinter as tk
from tkinter import ttk
from core.key_scheduler import KeyScheduler
from core.cipher import _feistel_f
from . import theme as T


def _byte_color(val: int) -> str:
    """Map 0-255 to a distinct pastel hue (HSV with fixed S and V)."""
    h, s, v = val / 256, 0.50, 0.96
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"


def _fg(bg_hex: str) -> str:
    """Black or white text depending on background luminance."""
    r, g, b = int(bg_hex[1:3], 16), int(bg_hex[3:5], 16), int(bg_hex[5:7], 16)
    return "#1E293B" if 0.299*r + 0.587*g + 0.114*b > 140 else "#FFFFFF"


def _compute_rounds(plaintext: str, key: str) -> list[tuple[str, list, list]]:
    """Return [(label, L[8], R[8]), ...] for pre-whitening + 8 Feistel rounds."""
    ks = KeyScheduler(key)
    raw = plaintext.encode("utf-8")
    data = (raw + b"\x00" * 16)[:16]
    block = [b ^ ks.pre_wk[i] for i, b in enumerate(data)]
    L, R = list(block[:8]), list(block[8:])
    states: list[tuple[str, list, list]] = [
        ("Pre-whitening  (XOR with key material)", list(L), list(R))
    ]
    for rnd in range(8):
        f = _feistel_f(R, ks.round_keys[rnd], ks.sbox, ks.rotations[rnd])
        L, R = R, [L[i] ^ f[i] for i in range(8)]
        states.append((f"Round {rnd + 1}  (L ← prev R,   R ← prev L ⊕ F(prev R, K{rnd+1}))",
                       list(L), list(R)))
    return states


class VizTab:
    BW, BH, GAP = 44, 32, 4   # box width, height, gap between boxes
    LBL_W = 54                  # left label column width (pixels)
    MX, MY = 18, 16            # canvas margins

    def __init__(self, frame) -> None:
        self._frame = frame
        self._states: list = []
        self._step = 0
        self._after_id: str | None = None
        self._build(frame)

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self, f) -> None:
        hdr = tk.Frame(f, bg="#7C3AED", height=54)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="  🧬  Feistel Network Visualizer",
                 bg="#7C3AED", fg="white",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=14, pady=14)

        # Controls row
        ctrl = tk.Frame(f, bg=T.BG)
        ctrl.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(ctrl, text="Message:", bg=T.BG,
                 font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        self._msg_e = ttk.Entry(ctrl, width=22, font=("Segoe UI", 10))
        self._msg_e.insert(0, "Hello, CHIMERA!")
        self._msg_e.grid(row=0, column=1, padx=(4, 14))
        tk.Label(ctrl, text="Key:", bg=T.BG,
                 font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w")
        self._key_e = ttk.Entry(ctrl, width=14, font=("Segoe UI", 10))
        self._key_e.insert(0, "SecretKey")
        self._key_e.grid(row=0, column=3, padx=(4, 14))
        ttk.Button(ctrl, text="▶  Show All", style="Accent.TButton",
                   command=self._show_all).grid(row=0, column=4, padx=(0, 6))
        ttk.Button(ctrl, text="⏯  Animate",
                   command=self._start_anim).grid(row=0, column=5, padx=(0, 6))
        ttk.Button(ctrl, text="⏹",
                   command=self._stop_anim).grid(row=0, column=6)

        # Legend
        leg = tk.Frame(f, bg=T.BG)
        leg.pack(fill="x", padx=12, pady=(0, 6))
        tk.Label(leg, text="■", bg=T.BG, fg="#FCD34D",
                 font=("Segoe UI", 13)).pack(side="left")
        tk.Label(leg, text=" Changed byte   ", bg=T.BG, fg=T.SUB,
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Label(leg, text="■■■", bg=T.BG, fg="#94A3B8",
                 font=("Segoe UI", 10)).pack(side="left", padx=(8, 0))
        tk.Label(leg, text=" Color = byte value (hue-mapped)",
                 bg=T.BG, fg=T.SUB, font=("Segoe UI", 9)).pack(side="left")

        # Canvas + vertical scrollbar inside a card border
        outer = tk.Frame(f, bg=T.BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        inner = tk.Frame(outer, bg=T.CARD)
        inner.pack(fill="both", expand=True)
        inner.rowconfigure(0, weight=1); inner.columnconfigure(0, weight=1)

        self._cv = tk.Canvas(inner, bg=T.CARD, highlightthickness=0)
        vs = ttk.Scrollbar(inner, orient="vertical", command=self._cv.yview)
        self._cv.configure(yscrollcommand=vs.set)
        self._cv.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        self._cv.bind("<MouseWheel>",
                      lambda e: self._cv.yview_scroll(-1 if e.delta > 0 else 1, "units"))

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _draw_row(self, y: int, data: list[int],
                  prev: list[int] | None, label: str) -> None:
        c = self._cv
        x = self.MX + self.LBL_W
        c.create_text(x - 6, y + self.BH // 2, text=label,
                      anchor="e", font=("Segoe UI", 9, "bold"), fill=T.SUB)
        for i, val in enumerate(data):
            bx = x + i * (self.BW + self.GAP)
            changed = prev is not None and prev[i] != val
            fill   = "#FCD34D" if changed else _byte_color(val)
            outln  = "#D97706" if changed else "#E2E8F0"
            lw     = 2 if changed else 1
            c.create_rectangle(bx, y, bx + self.BW, y + self.BH,
                                fill=fill, outline=outln, width=lw)
            c.create_text(bx + self.BW // 2, y + self.BH // 2,
                          text=f"{val:02X}",
                          font=("Courier New", 9, "bold"), fill=_fg(fill))

    def _draw_states(self, up_to: int | None = None) -> None:
        c = self._cv; c.delete("all")
        n = len(self._states) if up_to is None else up_to + 1
        ROW_H = 96
        total_h = self.MY + n * ROW_H + 40
        c.configure(scrollregion=(0, 0, 620, total_h))

        for i in range(n):
            lbl, L, R = self._states[i]
            y     = self.MY + i * ROW_H
            final = (i == n - 1)
            head_color = T.ACCENT if final else T.TEXT
            c.create_text(self.MX, y + 4, anchor="nw", text=lbl,
                          font=("Segoe UI", 9, "bold" if final else "normal"),
                          fill=head_color)
            pL = self._states[i-1][1] if i else None
            pR = self._states[i-1][2] if i else None
            self._draw_row(y + 22, L, pL, "L:")
            self._draw_row(y + 22 + self.BH + 6, R, pR, "R:")
            if i < n - 1:
                mid_x = self.MX + self.LBL_W + 4 * (self.BW + self.GAP)
                c.create_line(mid_x, y + 86, mid_x, y + 94,
                              fill=T.BORDER, width=1, arrow="last")

        if up_to is None or up_to >= len(self._states) - 1:
            fy = self.MY + n * ROW_H
            c.create_text(self.MX, fy, anchor="nw",
                          text="✓  Encryption complete — post-whitening XOR applied",
                          font=("Segoe UI", 10, "bold"), fill=T.SUCCESS)

    # ── Controls ──────────────────────────────────────────────────────────────
    def _show_all(self) -> None:
        self._stop_anim()
        self._states = _compute_rounds(
            self._msg_e.get() or "Hello!", self._key_e.get() or "Key")
        self._draw_states()

    def _start_anim(self) -> None:
        self._stop_anim()
        self._states = _compute_rounds(
            self._msg_e.get() or "Hello!", self._key_e.get() or "Key")
        self._step = 0; self._tick()

    def _tick(self) -> None:
        if self._step < len(self._states):
            self._draw_states(self._step)
            self._step += 1
            self._after_id = self._frame.after(750, self._tick)

    def _stop_anim(self) -> None:
        if self._after_id:
            self._frame.after_cancel(self._after_id)
            self._after_id = None

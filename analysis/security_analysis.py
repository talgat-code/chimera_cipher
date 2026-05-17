import math
import time
import random
import base64
from core import ChimeraCipher
from core.key_scheduler import KeyScheduler


class SecurityAnalyzer:
    def __init__(self, cipher: ChimeraCipher):
        self.cipher = cipher

    def avalanche_test(self, n_trials: int = 500) -> dict:
        """Flip 1 random bit in a random 16-byte block, encrypt both, count differing bits."""
        rng = random.Random(0)
        results = []
        for _ in range(n_trials):
            m1 = [rng.randint(0, 255) for _ in range(16)]
            m2 = m1[:]
            m2[rng.randint(0, 15)] ^= (1 << rng.randint(0, 7))
            e1 = self.cipher._encrypt_block(m1)
            e2 = self.cipher._encrypt_block(m2)
            bits = sum(bin(a ^ b).count("1") for a, b in zip(e1, e2))
            results.append(bits)
        return {
            "avg_bits": sum(results) / len(results),
            "avg_pct": sum(results) / len(results) / 128 * 100,
            "min": min(results),
            "max": max(results),
        }

    def key_space_report(self) -> dict:
        """Key space = 95^n (printable ASCII chars) for n = 8, 12, 16, 20, 24."""
        out: dict = {}
        for n in [8, 12, 16, 20, 24]:
            keys = 95 ** n
            bits = n * math.log2(95)
            out[f"{n}_chars"] = {"keys": float(keys), "bits": round(bits, 1)}
        return out

    def frequency_analysis(self, repeat_char: str = "a", count: int = 256) -> dict:
        """Encrypt 'count' identical chars; measure byte diversity and Shannon entropy."""
        enc_b64 = self.cipher.encrypt(repeat_char * count)
        raw = base64.b64decode(enc_b64)
        ct = raw[16:]  # strip IV
        freq = [0] * 256
        for b in ct:
            freq[b] += 1
        total = len(ct)
        entropy = -sum((f / total) * math.log2(f / total) for f in freq if f)
        return {
            "unique_bytes": sum(1 for f in freq if f),
            "total_bytes": total,
            "entropy": round(entropy, 4),
        }

    def chaos_sensitivity(self) -> dict:
        """Compare S-Boxes from 'Key1' vs 'Key2' (1 char diff)."""
        ks1 = KeyScheduler("Key1")
        ks2 = KeyScheduler("Key2")
        changed = sum(1 for a, b in zip(ks1.sbox, ks2.sbox) if a != b)
        return {"sbox_entries_changed": changed, "pct": round(changed / 256 * 100, 1)}

    def brute_force_estimate(self, key_length: int = 16) -> dict:
        """Benchmark block encrypt speed and extrapolate to full key-space search time."""
        block = [0] * 16
        trials = 1000
        t0 = time.perf_counter()
        for _ in range(trials):
            self.cipher._encrypt_block(block)
        elapsed = time.perf_counter() - t0
        single_us = elapsed / trials * 1e6
        total_keys = float(95 ** key_length)
        years = total_keys * (elapsed / trials) / (365.25 * 24 * 3600)
        return {"keys": total_keys, "single_enc_us": round(single_us, 3), "years": years}

    def comparison_table(self) -> str:
        """Formatted comparison table: Caesar | Vigenère | AES | CHIMERA."""
        rows = [
            ("Property",          "Caesar",   "Vigenère",  "AES-256",        "CHIMERA"),
            ("Key space",         "26",        "26^n",      "2^256",          "95^n"),
            ("Frequency resist",  "None",      "Partial",   "Full",           "Full"),
            ("Avalanche",         "None",      "None",      "~50%",           "~50%"),
            ("Architecture",      "Shift",     "Polyalpha", "SPN",            "Feistel"),
            ("Brute-force",       "Trivial",   "Feasible",  "Infeasible",     "Infeasible"),
            ("Key derivation",    "None",      "None",      "Rijndael sched", "Logistic map"),
        ]
        col_w = [max(len(r[i]) for r in rows) for i in range(5)]
        sep = "+" + "+".join("-" * (w + 2) for w in col_w) + "+"
        lines = [sep]
        for i, row in enumerate(rows):
            line = "| " + " | ".join(cell.ljust(col_w[j]) for j, cell in enumerate(row)) + " |"
            lines.append(line)
            if i == 0:
                lines.append(sep)
        lines.append(sep)
        return "\n".join(lines)

    def full_report(self) -> str:
        """Run all analyses and return a formatted report string."""
        av = self.avalanche_test(500)
        ks = self.key_space_report()
        fa = self.frequency_analysis()
        cs = self.chaos_sensitivity()
        bf = self.brute_force_estimate()
        lines = [
            "=" * 55,
            "  CHIMERA Security Analysis Report",
            "=" * 55,
            "",
            "[ Avalanche Effect — 500 trials ]",
            f"  Average bit flips : {av['avg_bits']:.1f} / 128",
            f"  Average %         : {av['avg_pct']:.1f}%",
            f"  Min / Max         : {av['min']} / {av['max']}",
            "",
            "[ Key Space ]",
            *[f"  {lbl:10s}: 2^{v['bits']:.0f}" for lbl, v in ks.items()],
            "",
            "[ Frequency Analysis — 256 identical 'a' chars ]",
            f"  Unique bytes : {fa['unique_bytes']} / 256",
            f"  Total bytes  : {fa['total_bytes']}",
            f"  Shannon H    : {fa['entropy']:.4f} / 8.0",
            "",
            "[ Chaos Sensitivity — 'Key1' vs 'Key2' ]",
            f"  S-Box entries changed: {cs['sbox_entries_changed']} / 256 ({cs['pct']}%)",
            "",
            "[ Brute-Force Estimate — 16-char key ]",
            f"  Key space       : 95^16 ≈ {bf['keys']:.2e}",
            f"  Single enc time : {bf['single_enc_us']:.3f} µs",
            f"  Estimated years : {bf['years']:.2e}",
            "",
            "[ Cipher Comparison ]",
            self.comparison_table(),
        ]
        return "\n".join(lines)

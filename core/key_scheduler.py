import hashlib
from .logistic_map import LogisticMap


class KeyScheduler:
    """
    Derives ALL cryptographic material from user key via chaotic logistic map.

    Pipeline:
      key (string)
        → SHA-256 hash (32 bytes)
          → extract x0 from bytes[0:8]   → initial condition for logistic map
          → extract r  from bytes[8:16]   → chaos parameter
        → LogisticMap(x0, r)
          → 256 bytes for S-Box generation (Fisher-Yates shuffle)
          → 8 × 8 = 64 bytes for round keys
          → 8 × 8 = 64 bytes for rotation amounts
          → 16 bytes for pre-whitening key
          → 16 bytes for post-whitening key
    """

    ROUNDS = 8

    def __init__(self, key: str):
        h = hashlib.sha256(key.encode("utf-8")).digest()

        # Derive chaos parameters from hash
        x0_int = int.from_bytes(h[:8], "big")
        x0 = 0.1 + (x0_int / (2**64 - 1)) * 0.8     # map to (0.1, 0.9)

        r_int = int.from_bytes(h[8:16], "big")
        r = 3.9 + (r_int / (2**64 - 1)) * 0.09999    # map to [3.9, 4.0)

        chaos = LogisticMap(x0, r)

        # Generate key material (order matters — deterministic stream!)
        sbox_material   = chaos.next_bytes(256)
        self.round_keys = [chaos.next_bytes(8) for _ in range(self.ROUNDS)]
        self.rotations  = [chaos.next_bytes(8) for _ in range(self.ROUNDS)]
        self.pre_wk     = chaos.next_bytes(16)
        self.post_wk    = chaos.next_bytes(16)

        # Build S-Box via Fisher-Yates with chaotic bytes
        self.sbox = list(range(256))
        j = 0
        for i in range(256):
            j = (j + self.sbox[i] + sbox_material[i]) % 256
            self.sbox[i], self.sbox[j] = self.sbox[j], self.sbox[i]

        # Build inverse S-Box
        self.inv_sbox = [0] * 256
        for i, v in enumerate(self.sbox):
            self.inv_sbox[v] = i

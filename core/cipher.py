import os
import base64
from .key_scheduler import KeyScheduler


def _rotate_left(byte: int, n: int) -> int:
    """Circular left rotation of a single byte by n bits."""
    n %= 8
    return ((byte << n) | (byte >> (8 - n))) & 0xFF


def _feistel_f(
    half: list[int],
    round_key: list[int],
    sbox: list[int],
    rotations: list[int],
) -> list[int]:
    """
    Feistel round function F(half, K).

    Unlike AES, F() does NOT need to be invertible — that property is
    guaranteed by the L/R/XOR structure of the Feistel network.

    Pipeline:
      1. XOR with round key        — key mixing
      2. S-Box substitution        — confusion (non-linearity)
      3. Bit rotation per byte     — diffusion (positional mixing);
                                     each byte rotated by a different chaotic amount
      4. Forward cascade XOR       — byte[i+1] ^= byte[i];
                                     each byte now depends on all prior bytes
      5. Reverse cascade XOR       — byte[i] ^= byte[i+1];
                                     each byte now depends on all other bytes
      6. Second S-Box pass         — confusion after linear cascade
    """
    # Step 1: key mixing
    mixed = [half[i] ^ round_key[i] for i in range(8)]
    # Step 2: S-Box substitution
    subbed = [sbox[b] for b in mixed]
    # Step 3: per-byte bit rotation
    rotated = [_rotate_left(subbed[i], rotations[i]) for i in range(8)]
    # Step 4: forward cascade XOR
    result = list(rotated)
    for i in range(7):
        result[i + 1] ^= result[i]
    # Step 5: reverse cascade XOR
    for i in range(6, -1, -1):
        result[i] ^= result[i + 1]
    # Step 6: second S-Box pass
    result = [sbox[b] for b in result]
    return result


class ChimeraCipher:
    ROUNDS = 8
    BLOCK_SIZE = 16

    def __init__(self, key: str):
        self.ks = KeyScheduler(key)

    # ------------------------------------------------------------------
    # Padding
    # ------------------------------------------------------------------

    def _pad(self, data: bytes) -> bytes:
        n = self.BLOCK_SIZE - (len(data) % self.BLOCK_SIZE)
        return data + bytes([n] * n)

    def _unpad(self, data: bytes) -> bytes:
        n = data[-1]
        if n < 1 or n > self.BLOCK_SIZE:
            raise ValueError("Invalid padding — wrong key?")
        if data[-n:] != bytes([n] * n):
            raise ValueError("Corrupted padding — wrong key?")
        return data[:-n]

    # ------------------------------------------------------------------
    # Block-level encrypt / decrypt
    # ------------------------------------------------------------------

    def _encrypt_block(self, block: list[int]) -> list[int]:
        block = [block[i] ^ self.ks.pre_wk[i] for i in range(16)]
        L, R = block[:8], block[8:]
        for rnd in range(self.ROUNDS):
            f_out = _feistel_f(R, self.ks.round_keys[rnd],
                               self.ks.sbox, self.ks.rotations[rnd])
            L, R = R, [L[i] ^ f_out[i] for i in range(8)]
        result = L + R
        return [result[i] ^ self.ks.post_wk[i] for i in range(16)]

    def _decrypt_block(self, block: list[int]) -> list[int]:
        block = [block[i] ^ self.ks.post_wk[i] for i in range(16)]
        L, R = block[:8], block[8:]
        for rnd in reversed(range(self.ROUNDS)):
            f_out = _feistel_f(L, self.ks.round_keys[rnd],
                               self.ks.sbox, self.ks.rotations[rnd])
            L, R = [R[i] ^ f_out[i] for i in range(8)], L
        result = L + R
        return [result[i] ^ self.ks.pre_wk[i] for i in range(16)]

    # ------------------------------------------------------------------
    # Public API — strings
    # ------------------------------------------------------------------

    def encrypt(self, plaintext: str) -> str:
        """
        PKCS7 pad → random IV → CBC encrypt → base64 output.
        Output format: base64( IV_16bytes || ciphertext_blocks )
        """
        data = self._pad(plaintext.encode("utf-8"))
        iv = os.urandom(self.BLOCK_SIZE)
        prev = list(iv)
        ciphertext = bytearray()

        for offset in range(0, len(data), self.BLOCK_SIZE):
            block = list(data[offset : offset + self.BLOCK_SIZE])
            # CBC: XOR with previous cipherblock (or IV for first block)
            block = [block[i] ^ prev[i] for i in range(self.BLOCK_SIZE)]
            enc = self._encrypt_block(block)
            ciphertext.extend(enc)
            prev = enc

        return base64.b64encode(iv + bytes(ciphertext)).decode("ascii")

    def decrypt(self, ciphertext_b64: str) -> str:
        """
        base64 decode → extract IV → CBC decrypt → PKCS7 unpad → string.
        Raises ValueError if key is wrong (padding check fails).
        """
        raw = base64.b64decode(ciphertext_b64)
        if len(raw) < self.BLOCK_SIZE or (len(raw) - self.BLOCK_SIZE) % self.BLOCK_SIZE != 0:
            raise ValueError("Invalid ciphertext length")

        iv = list(raw[: self.BLOCK_SIZE])
        ciphertext = raw[self.BLOCK_SIZE :]
        prev = iv
        plaintext = bytearray()

        for offset in range(0, len(ciphertext), self.BLOCK_SIZE):
            block = list(ciphertext[offset : offset + self.BLOCK_SIZE])
            dec = self._decrypt_block(block)
            # CBC: XOR with previous cipherblock (or IV for first block)
            dec = [dec[i] ^ prev[i] for i in range(self.BLOCK_SIZE)]
            plaintext.extend(dec)
            prev = block

        return self._unpad(bytes(plaintext)).decode("utf-8")

    # ------------------------------------------------------------------
    # Public API — files
    # ------------------------------------------------------------------

    def encrypt_file(self, in_path: str, out_path: str) -> None:
        """Read binary file, encrypt, write to out_path."""
        with open(in_path, "rb") as f:
            data = f.read()

        padded = self._pad(data)
        iv = os.urandom(self.BLOCK_SIZE)
        prev = list(iv)
        ciphertext = bytearray()

        for offset in range(0, len(padded), self.BLOCK_SIZE):
            block = list(padded[offset : offset + self.BLOCK_SIZE])
            block = [block[i] ^ prev[i] for i in range(self.BLOCK_SIZE)]
            enc = self._encrypt_block(block)
            ciphertext.extend(enc)
            prev = enc

        with open(out_path, "wb") as f:
            f.write(iv + bytes(ciphertext))

    def decrypt_file(self, in_path: str, out_path: str) -> None:
        """Read encrypted file, decrypt, write original bytes."""
        with open(in_path, "rb") as f:
            raw = f.read()

        if len(raw) < self.BLOCK_SIZE or (len(raw) - self.BLOCK_SIZE) % self.BLOCK_SIZE != 0:
            raise ValueError("Invalid encrypted file length")

        iv = list(raw[: self.BLOCK_SIZE])
        ciphertext = raw[self.BLOCK_SIZE :]
        prev = iv
        plaintext = bytearray()

        for offset in range(0, len(ciphertext), self.BLOCK_SIZE):
            block = list(ciphertext[offset : offset + self.BLOCK_SIZE])
            dec = self._decrypt_block(block)
            dec = [dec[i] ^ prev[i] for i in range(self.BLOCK_SIZE)]
            plaintext.extend(dec)
            prev = block

        with open(out_path, "wb") as f:
            f.write(self._unpad(bytes(plaintext)))

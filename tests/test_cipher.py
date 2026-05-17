import pytest
from core import ChimeraCipher


def test_roundtrip_basic():
    c = ChimeraCipher("TestKey!")
    assert c.decrypt(c.encrypt("Hello")) == "Hello"


def test_roundtrip_empty():
    c = ChimeraCipher("TestKey!")
    assert c.decrypt(c.encrypt("")) == ""


def test_roundtrip_unicode():
    c = ChimeraCipher("TestKey!")
    msg = "Привет 你好 🚀🔥"
    assert c.decrypt(c.encrypt(msg)) == msg


def test_roundtrip_long():
    c = ChimeraCipher("TestKey!")
    msg = "X" * 100_000
    assert c.decrypt(c.encrypt(msg)) == msg


def test_wrong_key_raises():
    c1 = ChimeraCipher("CorrectKey")
    c2 = ChimeraCipher("WrongKey!!")
    enc = c1.encrypt("Secret")
    with pytest.raises(ValueError):
        c2.decrypt(enc)


def test_random_iv():
    c = ChimeraCipher("Key")
    e1 = c.encrypt("same")
    e2 = c.encrypt("same")
    assert e1 != e2  # Random IV → different ciphertext each time


def test_avalanche():
    """At least 30% of bits should flip when 1 input bit changes."""
    from core.key_scheduler import KeyScheduler
    from core.cipher import _feistel_f
    import random
    random.seed(42)
    ks = KeyScheduler("AvalancheKey")
    total_pct = 0
    trials = 100
    for _ in range(trials):
        m1 = [random.randint(0, 255) for _ in range(16)]
        m2 = m1[:]
        m2[random.randint(0, 15)] ^= (1 << random.randint(0, 7))

        def enc(m):
            L, R = m[:8], m[8:]
            for rnd in range(8):
                f = _feistel_f(R, ks.round_keys[rnd], ks.sbox, ks.rotations[rnd])
                L, R = R, [L[i] ^ f[i] for i in range(8)]
            return L + R

        e1, e2 = enc(m1), enc(m2)
        bits = sum(bin(a ^ b).count("1") for a, b in zip(e1, e2))
        total_pct += bits / 128
    avg = total_pct / trials * 100
    assert avg > 30, f"Avalanche too low: {avg:.1f}%"


def test_file_encrypt_decrypt(tmp_path):
    c = ChimeraCipher("FileKey!")
    src = tmp_path / "test.bin"
    enc = tmp_path / "test.bin.chimera"
    dec = tmp_path / "test_dec.bin"
    src.write_bytes(b"\x00\x01\x02" * 1000)
    c.encrypt_file(str(src), str(enc))
    c.decrypt_file(str(enc), str(dec))
    assert src.read_bytes() == dec.read_bytes()

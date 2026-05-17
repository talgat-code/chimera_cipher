import sys
sys.stdout.reconfigure(encoding="utf-8")

from core import ChimeraCipher
from core.key_scheduler import KeyScheduler
from analysis.security_analysis import SecurityAnalyzer

SEP = "═" * 51


def main() -> None:
    print(SEP)
    print("  CHIMERA Cipher — Demo")
    print(SEP)
    print()

    # [1] Basic encrypt/decrypt
    key, pt = "MySecret2024!", "Attack at dawn!"
    c = ChimeraCipher(key)
    enc = c.encrypt(pt)
    dec = c.decrypt(enc)
    print("[1] Basic encrypt/decrypt")
    print(f"    Key       : '{key}'")
    print(f"    Plaintext : '{pt}'")
    print(f"    Ciphertext: {enc}")
    print(f"    Decrypted : '{dec}'")
    print(f"    Match     : {dec == pt}")
    print()

    # [2] Random IV — same plaintext yields different ciphertext
    c2 = ChimeraCipher("DemoKey")
    e1 = c2.encrypt("same plaintext")
    e2 = c2.encrypt("same plaintext")
    print("[2] Random IV — same plaintext, different ciphertext")
    print(f"    Encrypt 1 : {e1}")
    print(f"    Encrypt 2 : {e2}")
    print(f"    Different : {e1 != e2}")
    print()

    # [3] Wrong key detection
    c3 = ChimeraCipher("CorrectKey")
    enc3 = c3.encrypt("Secret message")
    c4 = ChimeraCipher("WrongKey!!")
    print("[3] Wrong key detection")
    try:
        c4.decrypt(enc3)
    except ValueError as e:
        print(f"    ValueError: {e}")
    print()

    # [4] Chaos sensitivity
    ks1 = KeyScheduler("Secret1")
    ks2 = KeyScheduler("Secret2")
    changed = sum(1 for a, b in zip(ks1.sbox, ks2.sbox) if a != b)
    pct = changed / 256 * 100
    print("[4] Chaos sensitivity — change key by 1 char")
    print('    Key "Secret1" vs "Secret2":')
    print(f"    S-Box entries changed: {changed}/256 ({pct:.0f}%)")
    print()

    # [5] Avalanche test
    sa = SecurityAnalyzer(ChimeraCipher("AvalancheKey"))
    av = sa.avalanche_test(100)
    print("[5] Avalanche test (100 trials)")
    print(f"    Average: {av['avg_pct']:.1f}% bit flip ✓")
    print()

    # [6] Frequency analysis
    sa6 = SecurityAnalyzer(ChimeraCipher("FreqKey"))
    fa = sa6.frequency_analysis("a", 128)
    print("[6] Frequency analysis")
    print("    Input: 128 identical ‘a’ characters")
    print(f"    Unique ciphertext bytes: {fa['unique_bytes']}/256")
    print(f"    Shannon entropy: {fa['entropy']:.1f} / 8.0")


if __name__ == "__main__":
    main()

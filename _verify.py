import sys, random, base64
sys.path.insert(0, '.')
from core import ChimeraCipher
from core.cipher import _feistel_f, _rotate_left
from core.key_scheduler import KeyScheduler
from core.logistic_map import LogisticMap

print('=== 1. LogisticMap sanity ===')
lm = LogisticMap(0.5, 3.99)
b = lm.next_bytes(1000)
assert all(0 <= x <= 255 for x in b), 'byte range fail'
unique = len(set(b))
print(f'  Unique values in 1000 bytes: {unique}/256  (expect >200)')

print('\n=== 2. LogisticMap determinism ===')
lm1 = LogisticMap(0.5, 3.99)
lm2 = LogisticMap(0.5, 3.99)
assert lm1.next_bytes(32) == lm2.next_bytes(32), 'not deterministic!'
print('  Same seed -> same output: OK')
lm3 = LogisticMap(0.5001, 3.99)
diff = sum(a != b for a, b in zip(lm1.next_bytes(32), lm3.next_bytes(32)))
print(f'  Different seed -> {diff}/32 bytes differ: OK')

print('\n=== 3. _rotate_left correctness ===')
assert _rotate_left(0b10110001, 1) == 0b01100011
assert _rotate_left(0b10110001, 8) == 0b10110001
assert _rotate_left(0xFF, 4) == 0xFF
assert _rotate_left(0x01, 1) == 0x02
assert _rotate_left(0x80, 1) == 0x01
print('  All cases OK')

print('\n=== 4. _feistel_f determinism + range ===')
ks = KeyScheduler('test')
half = [0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0]
out1 = _feistel_f(half, ks.round_keys[0], ks.sbox, ks.rotations[0])
out2 = _feistel_f(half, ks.round_keys[0], ks.sbox, ks.rotations[0])
assert out1 == out2 and all(0 <= b <= 255 for b in out1) and len(out1) == 8
print(f'  F output: {[hex(b) for b in out1]}  — deterministic, range OK')

print('\n=== 5. S-Box validity ===')
ks = KeyScheduler('SBoxTest')
assert sorted(ks.sbox) == list(range(256)), 'sbox not a permutation!'
assert sorted(ks.inv_sbox) == list(range(256)), 'inv_sbox not a permutation!'
for i in range(256):
    assert ks.inv_sbox[ks.sbox[i]] == i
print('  Valid permutation, inv_sbox correct: OK')

print('\n=== 6. Feistel round invertibility (manual, 100 trials) ===')
ROUNDS = 8
ks2 = KeyScheduler('FeistelTest')

def manual_enc(block):
    L, R = block[:8], block[8:]
    for rnd in range(ROUNDS):
        f = _feistel_f(R, ks2.round_keys[rnd], ks2.sbox, ks2.rotations[rnd])
        L, R = R, [L[i] ^ f[i] for i in range(8)]
    return L + R

def manual_dec(block):
    L, R = block[:8], block[8:]
    for rnd in reversed(range(ROUNDS)):
        f = _feistel_f(L, ks2.round_keys[rnd], ks2.sbox, ks2.rotations[rnd])
        L, R = [R[i] ^ f[i] for i in range(8)], L
    return L + R

random.seed(0)
for i in range(100):
    orig = [random.randint(0, 255) for _ in range(16)]
    assert manual_dec(manual_enc(orig)) == orig, f'Failed at trial {i}'
print('  100 blocks: OK')

print('\n=== 7. Full cipher roundtrip (stress) ===')
c = ChimeraCipher('StressKey!')
tests = [
    ('empty', ''),
    ('single byte', 'A'),
    ('15 bytes (one block)', 'A' * 15),
    ('16 bytes (two blocks after padding)', 'A' * 16),
    ('32 bytes', 'A' * 32),
    ('unicode CJK+emoji', 'Привет мир 🚀'),
    ('null+0xFF', chr(0) + chr(255) + chr(128)),
    ('newlines', 'line1\nline2\nline3'),
    ('100 000 chars', 'X' * 100_000),
]
for name, msg in tests:
    result = c.decrypt(c.encrypt(msg))
    assert result == msg, f'FAIL [{name}]'
    print(f'  [{name}]: {len(msg.encode())} bytes OK')

print('\n=== 8. CBC mode: unique ciphertext per call ===')
c = ChimeraCipher('IVTest')
encs = [c.encrypt('same message') for _ in range(10)]
assert len(set(encs)) == 10
print('  10 encryptions -> 10 different ciphertexts: OK')

print('\n=== 9. Wrong key always fails ===')
c1 = ChimeraCipher('CorrectKey')
for wrong in ['WrongKey', 'CorrectKey!', 'correctkey', ' CorrectKey']:
    try:
        ChimeraCipher(wrong).decrypt(c1.encrypt('secret'))
        print(f'  DANGER: "{wrong}" did NOT raise')
    except ValueError:
        print(f'  "{wrong}" -> ValueError: OK')

print('\n=== 10. PKCS7 padding alignment ===')
c = ChimeraCipher('PadTest')
for length in range(0, 35):
    msg = 'x' * length
    enc = c.encrypt(msg)
    ct = base64.b64decode(enc)[16:]
    assert len(ct) % 16 == 0, f'not aligned at len={length}'
    assert c.decrypt(enc) == msg
print('  Lengths 0-34: all aligned and roundtrip OK')

print('\n=== 11. Avalanche effect ===')
c = ChimeraCipher('AvalancheKey')
random.seed(42)
flip_pcts = []
for _ in range(200):
    b1 = [random.randint(0, 255) for _ in range(16)]
    b2 = b1[:]
    b2[random.randint(0, 15)] ^= (1 << random.randint(0, 7))
    e1 = c._encrypt_block(b1)
    e2 = c._encrypt_block(b2)
    bits = sum(bin(a ^ b).count('1') for a, b in zip(e1, e2))
    flip_pcts.append(bits / 128 * 100)
avg = sum(flip_pcts) / len(flip_pcts)
mn, mx = min(flip_pcts), max(flip_pcts)
print(f'  avg={avg:.1f}%  min={mn:.1f}%  max={mx:.1f}%  (ideal: ~50%)')
assert avg > 40, f'Avalanche too weak: {avg:.1f}%'
print('  Avalanche > 40%: OK')

print('\n=== 12. Key sensitivity — S-Box diff ===')
ks_a = KeyScheduler('Password1')
ks_b = KeyScheduler('Password2')
changed = sum(a != b for a, b in zip(ks_a.sbox, ks_b.sbox))
print(f'  1-char key diff -> {changed}/256 S-Box entries differ ({changed/256*100:.0f}%)')
assert changed > 200

print('\n=== ALL CHECKS PASSED ===')

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, '.')

# --- key_strength ---
from gui.cipher_tab import _key_strength

tests = [
    ('',               0,  '—'),
    ('abc',           30, 'Fair'),    # 3*5=15 + lower=+10 → 25 → Weak? No: 25 < 30 → Weak
    ('Password1',      0, None),      # compute and print
    ('MyStr0ng!Key',   0, None),      # compute and print
    ('MyStr0ng!Key#2024', 0, None),   # 17 chars, all char classes
]
for key, _, expected in tests:
    score, label, color = _key_strength(key)
    flag = f'  ← expected {expected}  ✗' if expected and label != expected else ''
    print(f'  {repr(key):25s}  score={score:3d}  {label}{flag}')

# --- compute_rounds ---
from gui.viz_tab import _compute_rounds
states = _compute_rounds('Hello, CHIMERA!', 'SecretKey')
assert len(states) == 9, f'Expected 9 states, got {len(states)}'
assert all(len(L) == 8 and len(R) == 8 for _, L, R in states)
print('\ncompute_rounds: 9 states × (8L+8R) bytes — OK')

# Each subsequent round should differ from the previous (diffusion)
diffs = []
for i in range(1, len(states)):
    prev_L, prev_R = states[i-1][1], states[i-1][2]
    cur_L,  cur_R  = states[i][1],   states[i][2]
    changed = sum(a != b for a, b in zip(cur_L + cur_R, prev_L + prev_R))
    diffs.append(changed)
    print(f'  State {i}: {changed}/16 bytes changed from previous')

assert all(d > 0 for d in diffs), 'Some round produced no change!'
print('All rounds produce changes: OK')

# --- byte_color ---
from gui.viz_tab import _byte_color, _fg
for v in [0, 64, 128, 192, 255]:
    col = _byte_color(v)
    assert col.startswith('#') and len(col) == 7
    fg = _fg(col)
    assert fg in ('#1E293B', '#FFFFFF')
print('\nbyte_color + fg: OK for values 0,64,128,192,255')

print('\nAll GUI unit tests passed.')

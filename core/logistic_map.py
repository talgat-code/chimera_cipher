"""
Logistic map: x_{n+1} = r · x_n · (1 − x_n)

At r ≈ 3.99 — chaotic regime:
 - Aperiodic (never repeats)
 - Sensitive to initial conditions (x0 ± 10⁻¹⁵ → completely different sequence)
 - Pseudo-random byte stream

This is NOT LCG and NOT SHA. This is chaos theory — a unique key stream generation approach.
"""


class LogisticMap:
    def __init__(self, x0: float, r: float):
        """
        x0 — initial condition, range (0.001, 0.999)
        r  — chaos parameter, range [3.9, 4.0)
        """
        self.x = max(0.001, min(0.999, x0))
        self.r = max(3.9, min(3.9999999, r))
        # Skip 200 transient iterations (settling into chaotic regime)
        for _ in range(200):
            self.x = self.r * self.x * (1.0 - self.x)

    def next_byte(self) -> int:
        """Generate one pseudo-random byte from the chaotic sequence."""
        self.x = self.r * self.x * (1.0 - self.x)
        return int(self.x * 256) & 0xFF

    def next_bytes(self, n: int) -> list[int]:
        """Generate n pseudo-random bytes."""
        return [self.next_byte() for _ in range(n)]

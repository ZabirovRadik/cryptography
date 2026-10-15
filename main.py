import os
from math import gcd

from gen import SelectingGenerator, is_primitive
import nist_tests

N = 1_000_000


def load_bits(name, n):
    here = os.path.dirname(os.path.abspath(__file__))
    for folder in (here, os.path.join(here, "constants")):
        path = os.path.join(folder, name)
        if os.path.exists(path):
            with open(path) as f:
                return [int(ch) for ch in f.read() if ch in "01"][:n]
    raise FileNotFoundError(name)


print("x^7 + x + 1 примитивен:", is_primitive([7, 1, 0]))
print("x^7 + x^5 + x^3 + 1 примитивен:", is_primitive([7, 5, 3, 0]))

polys = [[7, 1, 0], [29, 2, 0], [31, 3, 0]]
seeds = [0b1011001, 0x0ABCDEF1 & (2 ** 29 - 1), 0x2D3C4B5A & (2 ** 31 - 1)]
periods = [2 ** p[0] - 1 for p in polys]
assert all(is_primitive(p) for p in polys)
assert all(gcd(a, b) == 1 for i, a in enumerate(periods) for b in periods[i + 1:])
gen = SelectingGenerator(polys, seeds)

small = SelectingGenerator([[5, 2, 0], [7, 1, 0], [6, 1, 0]], [0b10110, 0b1011001, 0b110101])
print(f"Период генератора: {gen.theoretical_period():.3e} "
      f"(проверка на малых регистрах: формула {small.theoretical_period()}, измерено {small.measured_period()})")

seq = gen.bits(N)
with open("sequence.txt", "w") as f:
    f.write("".join(map(str, seq)))

kind = lambda bits: "e" if bits[1] == 0 else "pi"    # pi = 11.001..., e = 10.101...
data = {}
for name in ("data.pi", "data.e"):
    bits = load_bits(name, N)
    data[f"{name} [{kind(bits)}]"] = bits
data["Генератор"] = seq

res = {name: (nist_tests.cusum_test(b), nist_tests.excursions_test(b), nist_tests.rank_test(b)) for name, b in data.items()}


def cell(p):
    return "неприменим" if p is None else f"{p:.6f} {'+' if p >= nist_tests.ALPHA else '-'}"


print(f"\nP-value, n = {N}:")
print(f"{'':<28}" + "".join(f"{name:<18}" for name in data))
rows = [("Кумул. сумм, forward", lambda r: r[0][0]),
        ("Кумул. сумм, reverse", lambda r: r[0][1]),
        ("Произв. отклонения, x=+1", lambda r: r[1] and r[1][1]),
        ("Рангов бинарных матриц", lambda r: r[2])]
for title, get in rows:
    print(f"{title:<28}" + "".join(f"{cell(get(res[name])):<18}" for name in data)) 
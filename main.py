"""Вариант 14: селектирующий генератор + тесты рангов матриц, кумулятивных сумм, произвольных отклонений.

Запуск:  python3 main.py [--nbits 1000000] [--out sequence.txt]
Рядом должны лежать data.pi и data.e (или папка constants/ с ними).
"""
import argparse
from math import gcd

from gen import SelectingGenerator, is_primitive, find_primitive, poly_str, deg
from constants import pi_bits, e_bits
import nist_tests as T


def mark(ok):
    return "пройден" if ok else "НЕ пройден"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nbits", type=int, default=1_000_000)
    ap.add_argument("--out", default="sequence.txt")
    args = ap.parse_args()

    # --- 1. примитивность многочленов из задания ---
    print("Примитивность по модулю 2:")
    for name, f in (("x^7 + x + 1", 0b10000011), ("x^7 + x^5 + x^3 + 1", 0b10101001)):
        print(f"  {name}: {'примитивен' if is_primitive(f) else 'НЕ примитивен'}")

    # --- 2. генератор и период ---
    pa, pb, pc = 0b10000011, find_primitive(29), find_primitive(31)
    seeds = (0b1011001, 0x0ABCDEF1 & ((1 << 29) - 1), 0x2D3C4B5A & ((1 << 31) - 1))
    g = SelectingGenerator(pa, pb, pc, *seeds)
    print("\nГенератор (A управляет выбором между B и C):")
    for role, p in (("A", pa), ("B", pb), ("C", pc)):
        print(f"  {role}: {poly_str(p)}")
    periods = [(1 << deg(p)) - 1 for p in (pa, pb, pc)]
    assert all(gcd(x, y) == 1 for i, x in enumerate(periods) for y in periods[i + 1:])
    print(f"  период = {periods[0]} * {periods[1]} * {periods[2]} = {g.theoretical_period():.3e} (максимальный)")

    small = SelectingGenerator(find_primitive(5), 0b10000011, find_primitive(6), 0b10110, 0b1011001, 0b110101)
    P_th, P_ms = small.theoretical_period(), small.measured_period()
    print(f"  проверка программой на малых регистрах (5, 7, 6): формула {P_th}, измерено {P_ms} "
          f"-> {'совпало' if P_th == P_ms else 'НЕ совпало'}")

    # --- 3. последовательность и тесты ---
    seq = list(g.fresh().bits(args.nbits))
    with open(args.out, "w") as fh:
        fh.write("".join(map(str, seq)))
    data = {"pi": pi_bits(args.nbits), "e": e_bits(args.nbits), "Генератор": seq}

    res = {}
    for name, bits in data.items():
        res[name] = (T.binary_matrix_rank_test(bits), T.cumulative_sums_test(bits),
                     T.random_excursions_test(bits))

    # Таблица в том же порядке строк, что и в методичке (n = 10^6)
    print(f"\nP-value, n = {args.nbits} (порог {T.ALPHA}; + пройден, - не пройден):")
    print(f"{'Тест':<30}" + "".join(f"{n:<16}" for n in data))
    print("-" * (30 + 16 * len(data)))

    def row(title, cell):
        print(f"{title:<30}" + "".join(f"{cell(res[n]):<16}" for n in data))

    def pv(p):
        return f"{p:.6f} {'+' if p >= T.ALPHA else '-'}"

    row("Кумул. сумм, forward", lambda r: pv(r[1]["forward"]["p"]))
    row("Кумул. сумм, reverse", lambda r: pv(r[1]["backward"]["p"]))
    row("Произв. отклонения, x=+1",
        lambda r: pv(r[2]["states"][1]["p"]) if r[2]["applicable"] else "неприменим")
    row("Рангов бинарных матриц", lambda r: pv(r[0]["p"]))

    # остальные состояния x теста на произвольные отклонения: сообщаем только о неудачах
    for name in data:
        e = res[name][2]
        if e["applicable"]:
            bad = [f"x={x:+d} (P={v['p']:.4f})" for x, v in e["states"].items() if not v["passed"]]
            if bad:
                print(f"  Прим.: {name}, другие состояния x не прошли: {', '.join(bad)}")
    print(f"\nПоследовательность записана в {args.out}")


if __name__ == "__main__":
    main()
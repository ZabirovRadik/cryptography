import math
import numpy as np
from scipy.special import gammaincc

ALPHA = 0.01


def phi(x):
    return 0.5 * math.erfc(-x / math.sqrt(2))


def gf2_rank(rows):
    rank = 0
    while rows:
        p = rows.pop()
        if p:
            rank += 1
            low = p & -p
            rows = [x ^ p if x & low else x for x in rows]
    return rank


def rank_prob(r, M=32, Q=32):
    prod = 1.0
    for i in range(r):
        prod *= (1 - 2.0 ** (i - Q)) * (1 - 2.0 ** (i - M)) / (1 - 2.0 ** (i - r))
    return 2.0 ** (r * (Q + M - r) - M * Q) * prod


def rank_test(bits, M=32):
    N = len(bits) // (M * M)
    counts = [0, 0, 0]
    for k in range(N):
        block = bits[k * M * M:(k + 1) * M * M]
        rows = [int("".join(map(str, block[i * M:(i + 1) * M])), 2) for i in range(M)]
        r = gf2_rank(rows)
        counts[0 if r == M else 1 if r == M - 1 else 2] += 1
    p = [rank_prob(M), rank_prob(M - 1)]
    p.append(1 - p[0] - p[1])
    chi2 = sum((c - N * q) ** 2 / (N * q) for c, q in zip(counts, p))
    return math.exp(-chi2 / 2)


def _cusum_p(n, z):
    s = math.sqrt(n)
    s1 = sum(phi((4 * k + 1) * z / s) - phi((4 * k - 1) * z / s)
             for k in range(int((-n / z + 1) // 4), int((n / z - 1) // 4) + 1))
    s2 = sum(phi((4 * k + 3) * z / s) - phi((4 * k + 1) * z / s)
             for k in range(int((-n / z - 3) // 4), int((n / z - 1) // 4) + 1))
    return 1 - s1 + s2


def cusum_test(bits):
    # (P forward, P reverse)
    x = 2 * np.array(bits, dtype=np.int64) - 1
    return tuple(_cusum_p(len(x), int(np.abs(np.cumsum(seq)).max())) for seq in (x, x[::-1]))


def _visit_prob(x, k):
    a = abs(x)
    if k == 0:
        return 1 - 1 / (2 * a)
    if k < 5:
        return (1 / (4 * a * a)) * (1 - 1 / (2 * a)) ** (k - 1)
    return (1 / (2 * a)) * (1 - 1 / (2 * a)) ** 4


def excursions_test(bits):
    # {x: P} для x = -4..-1, 1..4; None, если циклов меньше 500
    s = np.concatenate(([0], np.cumsum(2 * np.array(bits, dtype=np.int64) - 1), [0]))
    zeros = np.flatnonzero(s == 0)
    J = len(zeros) - 1
    if J < 500:
        return None
    states = [-4, -3, -2, -1, 1, 2, 3, 4]
    nu = {x: [0] * 6 for x in states}
    for j in range(J):
        cycle = s[zeros[j] + 1:zeros[j + 1]]
        for x in states:
            nu[x][min(int(np.count_nonzero(cycle == x)), 5)] += 1
    return {x: float(gammaincc(2.5, sum((nu[x][k] - J * _visit_prob(x, k)) ** 2 / (J * _visit_prob(x, k))
                                        for k in range(6)) / 2)) for x in states}
import math
import numpy as np
from scipy.special import gammaincc

ALPHA = 0.01


def _phi(x):
    return 0.5 * math.erfc(-x / math.sqrt(2))


def _gf2_rank(rows):
    rows = list(rows)
    rank = 0
    while rows:
        p = rows.pop()
        if p:
            rank += 1
            low = p & -p
            rows = [x ^ p if x & low else x for x in rows]
    return rank


def _rank_prob(r, M, Q):
    if r == 0:
        return 2.0 ** (1 - M * Q)
    prod = 1.0
    for i in range(r):
        prod *= (1 - 2.0 ** (i - Q)) * (1 - 2.0 ** (i - M)) / (1 - 2.0 ** (i - r))
    return 2.0 ** (r * (Q + M - r) - M * Q) * prod


def binary_matrix_rank_test(bits, M=32, Q=32):
    bits = np.asarray(bits, dtype=np.uint8)
    N = len(bits) // (M * Q)
    if N < 38:
        raise ValueError("для теста рангов нужно не менее 38 матриц")
    f_full = f_m1 = 0
    for k in range(N):
        blk = bits[k * M * Q:(k + 1) * M * Q].reshape(M, Q)
        rows = [int("".join(map(str, row)), 2) for row in blk]
        r = _gf2_rank(rows)
        if r == min(M, Q):
            f_full += 1
        elif r == min(M, Q) - 1:
            f_m1 += 1
    f_rest = N - f_full - f_m1
    p_full = _rank_prob(min(M, Q), M, Q)
    p_m1 = _rank_prob(min(M, Q) - 1, M, Q)
    p_rest = 1.0 - p_full - p_m1
    chi2 = ((f_full - N * p_full) ** 2 / (N * p_full)
            + (f_m1 - N * p_m1) ** 2 / (N * p_m1)
            + (f_rest - N * p_rest) ** 2 / (N * p_rest))
    p_value = math.exp(-chi2 / 2)
    return {"p": p_value, "chi2": chi2, "N": N, "F": (f_full, f_m1, f_rest),
            "passed": p_value >= ALPHA}


def _cusum_p(x, z):
    n = len(x)
    sn = math.sqrt(n)
    s1 = sum(_phi((4 * k + 1) * z / sn) - _phi((4 * k - 1) * z / sn)
             for k in range(int((-n / z + 1) // 4), int((n / z - 1) // 4) + 1))
    s2 = sum(_phi((4 * k + 3) * z / sn) - _phi((4 * k + 1) * z / sn)
             for k in range(int((-n / z - 3) // 4), int((n / z - 1) // 4) + 1))
    return 1.0 - s1 + s2


def cumulative_sums_test(bits):
    x = 2 * np.asarray(bits, dtype=np.int64) - 1
    res = {}
    for name, seq in (("forward", x), ("backward", x[::-1])):
        z = int(np.max(np.abs(np.cumsum(seq))))
        res[name] = {"z": z, "p": _cusum_p(seq, z)}
    res["p"] = min(res["forward"]["p"], res["backward"]["p"])
    res["passed"] = res["forward"]["p"] >= ALPHA and res["backward"]["p"] >= ALPHA
    return res


def _excursion_pi(x, k):
    ax = abs(x)
    if k == 0:
        return 1 - 1 / (2 * ax)
    if k < 5:
        return (1 / (4 * ax * ax)) * (1 - 1 / (2 * ax)) ** (k - 1)
    return (1 / (2 * ax)) * (1 - 1 / (2 * ax)) ** 4


def random_excursions_test(bits):
    x = 2 * np.asarray(bits, dtype=np.int64) - 1
    s = np.concatenate(([0], np.cumsum(x), [0]))
    zeros = np.flatnonzero(s == 0)
    J = len(zeros) - 1
    out = {"J": J, "states": {}}
    if J < 500:
        out["applicable"] = False
        out["passed"] = None
        out["p"] = float("nan")
        return out
    out["applicable"] = True
    states = [-4, -3, -2, -1, 1, 2, 3, 4]
    nu = {st: np.zeros(6, dtype=np.int64) for st in states}
    for j in range(J):
        cyc = s[zeros[j] + 1:zeros[j + 1]]
        for st in states:
            nu[st][min(int(np.count_nonzero(cyc == st)), 5)] += 1
    all_ok = True
    for st in states:
        chi2 = sum((nu[st][k] - J * _excursion_pi(st, k)) ** 2 / (J * _excursion_pi(st, k))
                   for k in range(6))
        p = float(gammaincc(2.5, chi2 / 2))
        ok = p >= ALPHA
        all_ok &= ok
        out["states"][st] = {"chi2": chi2, "p": p, "passed": ok, "nu": nu[st].tolist()}
    out["p"] = min(v["p"] for v in out["states"].values())
    out["passed"] = all_ok
    return out
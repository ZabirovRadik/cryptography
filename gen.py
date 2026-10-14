from math import gcd
from functools import reduce

try:
    (1).bit_count()
    def _parity(x): return x.bit_count() & 1
except AttributeError:
    def _parity(x): return bin(x).count("1") & 1


def deg(f):
    return f.bit_length() - 1


def poly_str(f):
    terms = []
    for i in range(deg(f), -1, -1):
        if (f >> i) & 1:
            terms.append("1" if i == 0 else ("x" if i == 1 else f"x^{i}"))
    return " + ".join(terms)


def _mulmod(a, b, f):
    n = deg(f)
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if (a >> n) & 1:
            a ^= f
    return r


def _x_pow_mod(e, f):
    result, base = 1, 2
    while e:
        if e & 1:
            result = _mulmod(result, base, f)
        base = _mulmod(base, base, f)
        e >>= 1
    return result


def _prime_factors(n):
    res, p = set(), 2
    while p * p <= n:
        while n % p == 0:
            res.add(p)
            n //= p
        p += 1
    if n > 1:
        res.add(n)
    return res


def is_primitive(f):
    n = deg(f)
    if n < 2 or not (f & 1):
        return False
    order = (1 << n) - 1
    if _x_pow_mod(order, f) != 1:
        return False
    return all(_x_pow_mod(order // p, f) != 1 for p in _prime_factors(order))


def primitive_polys(n):
    return [f for f in range((1 << n) | 1, 1 << (n + 1), 2) if is_primitive(f)]


def find_primitive(n):
    top = 1 << n
    for k in range(1, n):
        f = top | (1 << k) | 1
        if is_primitive(f):
            return f
    for k1 in range(3, n):
        for k2 in range(2, k1):
            for k3 in range(1, k2):
                f = top | (1 << k1) | (1 << k2) | (1 << k3) | 1
                if is_primitive(f):
                    return f
    raise ValueError(f"примитивный многочлен степени {n} не найден")


class LFSR:
    def __init__(self, poly, seed):
        self.poly = poly
        self.n = deg(poly)
        self.mask = poly & ((1 << self.n) - 1)
        self.state = seed & ((1 << self.n) - 1)
        if self.state == 0:
            raise ValueError("нулевое начальное состояние недопустимо")

    def step(self):
        out = self.state & 1
        fb = _parity(self.state & self.mask)
        self.state = (self.state >> 1) | (fb << (self.n - 1))
        return out


class SelectingGenerator:
    def __init__(self, poly_a, poly_b, poly_c, seed_a, seed_b, seed_c):
        self.a = LFSR(poly_a, seed_a)
        self.b = LFSR(poly_b, seed_b)
        self.c = LFSR(poly_c, seed_c)
        self._init = (poly_a, poly_b, poly_c, seed_a, seed_b, seed_c)

    def fresh(self):
        return SelectingGenerator(*self._init)

    def bits(self, nbits):
        a, b, c = self.a, self.b, self.c
        sa, sb, sc = a.state, b.state, c.state
        ma, mb, mc = a.mask, b.mask, c.mask
        ha, hb, hc = a.n - 1, b.n - 1, c.n - 1
        out = bytearray(nbits)
        for i in range(nbits):
            out[i] = (sb & 1) if (sa & 1) else (sc & 1)
            sa = (sa >> 1) | (_parity(sa & ma) << ha)
            sb = (sb >> 1) | (_parity(sb & mb) << hb)
            sc = (sc >> 1) | (_parity(sc & mc) << hc)
        a.state, b.state, c.state = sa, sb, sc
        return out

    def theoretical_period(self):
        per = [(1 << r.n) - 1 for r in (self.a, self.b, self.c)]
        return reduce(lambda x, y: x * y // gcd(x, y), per)

    def measured_period(self):
        P = self.theoretical_period()
        s = self.fresh().bits(2 * P)
        L = len(s)
        fail = [0] * L
        k = 0
        for i in range(1, L):
            while k and s[i] != s[k]:
                k = fail[k - 1]
            if s[i] == s[k]:
                k += 1
            fail[i] = k
        return L - fail[-1]
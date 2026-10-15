from math import lcm


def parity(x):
    return bin(x).count("1") & 1


class LFSR:
    # многочлен списком степеней: x^7 + x + 1 -> [7, 1, 0]
    def __init__(self, poly, seed):
        self.n = poly[0]
        self.mask = sum(1 << t for t in poly[1:])
        assert 0 < seed < 2 ** self.n
        self.state = seed

    def step(self):
        out = self.state & 1
        fb = parity(self.state & self.mask)
        self.state = (self.state >> 1) | (fb << (self.n - 1))
        return out


class SelectingGenerator:
    # бит A выбирает выход: B (если 1) или C (если 0)
    def __init__(self, polys, seeds):
        self.polys, self.seeds = polys, seeds
        self.reset()

    def reset(self):
        self.a, self.b, self.c = (LFSR(p, s) for p, s in zip(self.polys, self.seeds))

    def bits(self, count):
        out = []
        for _ in range(count):
            a, b, c = self.a.step(), self.b.step(), self.c.step()
            out.append(b if a else c)
        return out

    def theoretical_period(self):
        return lcm(*[2 ** p[0] - 1 for p in self.polys])

    def measured_period(self):
        self.reset()
        s = self.bits(2 * self.theoretical_period())
        fail = [0] * len(s)
        k = 0
        for i in range(1, len(s)):
            while k and s[i] != s[k]:
                k = fail[k - 1]
            if s[i] == s[k]:
                k += 1
            fail[i] = k
        self.reset()
        return len(s) - fail[-1]


# многочлен над GF(2) как число: бит i - коэффициент при x^i

def _mulmod(a, b, f):
    n, r = f.bit_length() - 1, 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if (a >> n) & 1:
            a ^= f
    return r


def _x_pow(e, f):
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


def is_primitive(poly):
    f, order = sum(1 << e for e in poly), 2 ** poly[0] - 1
    if f & 1 == 0:
        return False
    return _x_pow(order, f) == 1 and all(_x_pow(order // p, f) != 1 for p in _prime_factors(order))
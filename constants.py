def _load(name, n):
    with open(name) as f:
        return [int(c) for c in f.read() if c in '01'][:n]

def pi_bits(n):
    return _load('constants//data.pi', n)

def e_bits(n):
    return _load('constants//data.e', n)
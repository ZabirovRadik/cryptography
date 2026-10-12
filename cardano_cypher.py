import random
import sys

N = 8
BLOCK = N * N
PAD = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЭЮЯ"


def rotate_cell(r, c):
    return c, N - 1 - r


def rotate(holes):
    return sorted(rotate_cell(r, c) for r, c in holes)


def load_grille(path):
    with open(path, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    if len(lines) != N or any(len(line) != N or set(line) - {"0", "1"} for line in lines):
        raise ValueError("Файл решётки должен содержать 8 строк по 8 символов из 0 и 1")
    holes = sorted((r, c) for r in range(N) for c in range(N) if lines[r][c] == "1")
    covered = set()
    cur = holes
    for _ in range(4):
        covered.update(cur)
        cur = rotate(cur)
    if len(holes) != BLOCK // 4 or len(covered) != BLOCK:
        raise ValueError("Решётка некорректна: повороты не покрывают все клетки ровно по разу")
    return holes


def encrypt(text, holes):
    if len(text) % BLOCK:
        text += "".join(random.choice(PAD) for _ in range(BLOCK - len(text) % BLOCK))
    out = []
    for b in range(0, len(text), BLOCK):
        block = text[b:b + BLOCK]
        table = [[None] * N for _ in range(N)]
        cur = holes
        pos = 0
        for _ in range(4):
            for r, c in cur:
                table[r][c] = block[pos]
                pos += 1
            cur = rotate(cur)
        out.append("".join("".join(row) for row in table))
    return "".join(out)


def decrypt(cipher, holes):
    if len(cipher) % BLOCK:
        raise ValueError("Длина шифртекста должна быть кратна 64")
    out = []
    for b in range(0, len(cipher), BLOCK):
        block = cipher[b:b + BLOCK]
        table = [block[r * N:(r + 1) * N] for r in range(N)]
        cur = holes
        for _ in range(4):
            for r, c in cur:
                out.append(table[r][c])
            cur = rotate(cur)
    return "".join(out)


def main():
    if len(sys.argv) != 5 or sys.argv[1] not in ("enc", "dec"):
        print("Использование: python cardano_cipher.py enc|dec файл_решётки входной_файл выходной_файл")
        sys.exit(1)
    mode, grille_path, in_path, out_path = sys.argv[1:]
    holes = load_grille(grille_path)
    with open(in_path, encoding="utf-8") as f:
        data = f.read().rstrip("\r\n")
    result = encrypt(data, holes) if mode == "enc" else decrypt(data, holes)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result + "\n")
    print("Готово, результат записан в", out_path)


if __name__ == "__main__":
    main()
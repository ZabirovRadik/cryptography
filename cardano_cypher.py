import random
import sys

PAD = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЭЮЯ"


def rotate_cell(r, c, n):
    return c, n - 1 - r


def rotate(holes, n):
    return sorted(rotate_cell(r, c, n) for r, c in holes)


def load_grille(path):
    with open(path, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    n = len(lines)
    if n == 0 or n % 2:
        raise ValueError("Размер решётки должен быть чётным числом")
    if any(len(line) != n or set(line) - {"0", "1"} for line in lines):
        raise ValueError("Файл решётки должен быть квадратом из символов 0 и 1")
    holes = sorted((r, c) for r in range(n) for c in range(n) if lines[r][c] == "1")
    covered = set()
    cur = holes
    for _ in range(4):
        covered.update(cur)
        cur = rotate(cur, n)
    if len(holes) != n * n // 4 or len(covered) != n * n:
        raise ValueError("Решётка некорректна: повороты не покрывают все клетки ровно по разу")
    return holes, n


def encrypt(text, holes, n):
    block_len = n * n
    if len(text) % block_len:
        text += "".join(random.choice(PAD) for _ in range(block_len - len(text) % block_len))
    out = []
    for b in range(0, len(text), block_len):
        block = text[b:b + block_len]
        table = [[None] * n for _ in range(n)]
        cur = holes
        pos = 0
        for _ in range(4):
            for r, c in cur:
                table[r][c] = block[pos]
                pos += 1
            cur = rotate(cur, n)
        out.append("".join("".join(row) for row in table))
    return "".join(out)


def decrypt(cipher, holes, n):
    block_len = n * n
    if len(cipher) % block_len:
        raise ValueError(f"Длина шифртекста должна быть кратна {block_len}")
    out = []
    for b in range(0, len(cipher), block_len):
        block = cipher[b:b + block_len]
        table = [block[r * n:(r + 1) * n] for r in range(n)]
        cur = holes
        for _ in range(4):
            for r, c in cur:
                out.append(table[r][c])
            cur = rotate(cur, n)
    return "".join(out)


def main():
    if len(sys.argv) != 5 or sys.argv[1] not in ("enc", "dec"):
        print("Использование: python cardano_cipher.py enc|dec файл_решётки входной_файл выходной_файл")
        sys.exit(1)
    mode, grille_path, in_path, out_path = sys.argv[1:]
    holes, n = load_grille(grille_path)
    with open(in_path, encoding="utf-8") as f:
        raw = f.read()
    if mode == "enc":
        data = " ".join(line.strip() for line in raw.splitlines() if line.strip())
        result = encrypt(data, holes, n)
    else:
        result = decrypt(raw.rstrip("\r\n"), holes, n)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result + "\n")
    print(f"Готово (решётка {n}x{n}), результат записан в {out_path}")


if __name__ == "__main__":
    main()
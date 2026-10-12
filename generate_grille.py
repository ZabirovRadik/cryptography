import random
import sys

N = 8


def rotate_cell(r, c):
    return c, N - 1 - r


def generate():
    seen = set()
    holes = set()
    for r in range(N):
        for c in range(N):
            if (r, c) in seen:
                continue
            orbit = [(r, c)]
            for _ in range(3):
                orbit.append(rotate_cell(*orbit[-1]))
            seen.update(orbit)
            holes.add(random.choice(orbit))
    return holes


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "INPUT//grille.txt"
    holes = generate()
    lines = ["".join("1" if (r, c) in holes else "0" for c in range(N)) for r in range(N)]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("Решётка 8x8 сохранена в", path)
    for line in lines:
        print(" ".join("○" if ch == "1" else "█" for ch in line))


if __name__ == "__main__":
    main()
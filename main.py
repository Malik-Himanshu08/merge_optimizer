# main.py
import sys
from lcs import read_lines
from merge import merge


def run(base_path, a_path, b_path, out_path):
    base = read_lines(base_path)
    devA = read_lines(a_path)
    devB = read_lines(b_path)

    merged, conflicts = merge(base, devA, devB)

    with open(out_path, "w") as f:
        f.write("\n".join(merged) + "\n")

    print("Merged file written to:", out_path)
    print("Conflicts:", len(conflicts))
    for n, c in enumerate(conflicts, start=1):
        print(f"  Conflict {n}: base lines {c['start'] + 1} to {c['end']}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python main.py base.txt devA.txt devB.txt output.txt")
    else:
        run(*sys.argv[1:5])
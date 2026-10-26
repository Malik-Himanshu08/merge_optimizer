# analysis.py
import os
import random
import time
import tracemalloc
import matplotlib.pyplot as plt

from lcs import build_table
from merge import merge
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "graphs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def make_files(n, change_ratio=0.1, seed=1):
    """Make a base file of n lines, and two versions with ~10% of lines changed."""
    random.seed(seed)
    base = ["line " + str(k) for k in range(n)]
    devA = base[:]
    devB = base[:]
    changes = max(1, int(n * change_ratio))
    for k in random.sample(range(n), changes):
        devA[k] = "A edit " + str(k)
    for k in random.sample(range(n), changes):
        devB[k] = "B edit " + str(k)
    return base, devA, devB


def time_merge(base, devA, devB):
    start = time.perf_counter()
    merge(base, devA, devB)
    return time.perf_counter() - start


def peak_memory_kb(base, devA):
    tracemalloc.start()
    build_table(base, devA)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return peak / 1024


if __name__ == "__main__":
    sizes = [100, 200, 400, 800, 1600]
    times = []
    memory = []

    print("Lines | Time (s)  | Time / n^2 (microsec) | Peak memory (KB)")
    for n in sizes:
        base, devA, devB = make_files(n)
        t = time_merge(base, devA, devB)
        mem = peak_memory_kb(base, devA)
        times.append(t)
        memory.append(mem)
        print(f"{n:5d} | {t:9.4f} | {t / (n * n) * 1e6:21.3f} | {mem:10.0f}")

    # --- Graph 1: time vs input size, with an n^2 reference curve ---
    scale = times[-1] / (sizes[-1] ** 2)
    plt.figure()
    plt.plot(sizes, times, "o-", label="Measured time")
    plt.plot(sizes, [scale * n * n for n in sizes], "--", label="O(n^2) reference")
    plt.xlabel("Number of lines (n)")
    plt.ylabel("Time (seconds)")
    plt.title("Merge time vs input size")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(OUTPUT_DIR, "time_graph.png"), dpi=150)

    # --- Graph 2: memory vs input size ---
    plt.figure()
    plt.plot(sizes, memory, "o-", color="green")
    plt.xlabel("Number of lines (n)")
    plt.ylabel("Peak memory of DP table (KB)")
    plt.title("Memory vs input size")
    plt.grid(True)
    plt.savefig(os.path.join(OUTPUT_DIR, "memory_graph.png"), dpi=150)

    print("Saved time_graph.png and memory_graph.png")
    print("Graphs saved in:", OUTPUT_DIR)
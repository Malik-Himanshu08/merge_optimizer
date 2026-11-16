# Version Control Merge Optimizer

A small Python project that merges two edited versions of a text file back into the original. It works the same way Git does when two people change the same file and then combine their work. It is built from scratch and uses the Longest Common Subsequence (LCS) algorithm to find what changed.

---

## The Problem It Solves

Imagine a file called `base.txt`. Two developers, Dev A and Dev B, each make their own changes to a copy of it.

- If their changes are in different parts of the file, the merge is easy: take both sets of changes.
- If they changed the same part of the file in different ways, the merge is a **conflict**. A person has to decide which version to keep.

This project does the merge automatically when it can, and marks the conflicts clearly when it cannot.

---

## How It Works (Step by Step)

1. **Find what changed.** The program compares the base file with Dev A's file, and then with Dev B's file. It uses LCS to find the lines that stayed the same. Everything else is treated as a change.
2. **Group the changes into hunks.** A hunk is a block of consecutive changed lines. Each hunk is labeled as `added`, `deleted`, or `modified`.
3. **Merge the hunks.** The program walks through both developers' hunks in order:
   - If two hunks touch different parts of the base file, both are applied.
   - If two hunks overlap, the program looks at the whole overlapping region. If both developers made the exact same change, it is kept once. If not, it becomes a conflict.
4. **Write the result.** Conflicts are written with standard markers:

```
<<<<<<< Dev A
(Dev A's version of the lines)
=======
(Dev B's version of the lines)
>>>>>>> Dev B
```

---

## Project Structure

| File | Purpose |
|------|---------|
| `lcs.py` | Core algorithm. Reads files and computes the LCS table and matching lines. |
| `diff.py` | Turns LCS results into a list of changes and groups them into hunks. |
| `merge.py` | Three-way merge. Combines the two developers' hunks and detects conflicts. |
| `main.py` | Command-line entry point. |
| `gui.py` | Graphical app (Tkinter) for loading files, merging, resolving conflicts, and saving. |
| `analysis.py` | Benchmark script. Measures time and memory as the file size grows, and saves graphs. |
| `merged.txt` | Example of a merged output file that contains a conflict. |
| `samples/` | Folder of test sets (not included in this upload). Each set has `base.txt`, `devA.txt`, and `devB.txt`. |

---

## Requirements

- Python 3.8 or newer
- `tkinter` (usually included with Python; needed only for `gui.py`)
- `matplotlib` (needed only for `analysis.py`)

Install matplotlib if you plan to run the benchmark:

```bash
pip install matplotlib
```

---

## How to Use It

### 1. Command line

```bash
python main.py base.txt devA.txt devB.txt output.txt
```

The program writes the merged file to `output.txt`. It also prints the number of conflicts and the line range of each one in the base file.

### 2. Graphical app

```bash
python gui.py
```

The window lets you:

- Pick the Base, Dev A, and Dev B files with **Browse**, or choose a sample set and click **Load sample**.
- Click **Merge** to run the merge.
- See a summary of the changes in each version, the conflict count, and the merge time in milliseconds.
- Click a conflict in the list on the left, then choose **Use Dev A**, **Use Dev B**, or **Use Both**.
- Switch to the **Side by side** tab to see the three files next to each other. Deleted lines in Base are shown in red, and added lines in Dev A and Dev B are shown in green.
- Click **Save merged file**. Saving is blocked until every conflict is resolved.

### 3. Benchmark

```bash
python analysis.py
```

This generates test files of 100, 200, 400, 800, and 1600 lines. Each base file has two versions with about 10% of lines changed. The script prints a table with the time, the time divided by n², and the peak memory of the LCS table. It then saves two graphs in a `graphs/` folder:

- `time_graph.png`: measured merge time compared with an O(n²) reference curve
- `memory_graph.png`: peak memory of the LCS table against input size

---

## Key Concepts

**LCS (Longest Common Subsequence).** The longest set of lines that appear in both files, in the same order. Lines that are not part of the LCS are the changes. The program builds a table of size (n+1) × (m+1) to find it, and then walks backward through the table to get the matching pairs.

**Hunk.** A group of consecutive changed lines. Each hunk stores:
- `start` and `end`: the position in the base file (`end` is not included)
- `new_lines`: the replacement lines from the developer
- `type`: `added`, `deleted`, or `modified`

**Three-way merge.** Uses the base file as the reference point. Each developer's changes are measured against the base, and then combined. Because the base is known, the program can tell when both developers changed the same place.

**Conflict.** Happens when two hunks change the same part of the base file and the results are not identical. Two inserts at the same position also count as a conflict.

---

## Complexity

| Part | Time | Memory |
|------|------|--------|
| LCS table | O(n × m) | O(n × m) |
| Finding hunks | O(n × m) for each developer | Same as above |
| Merging hunks | Linear in the number of hunks | Output size |

Because the table grows with the product of the two file lengths, the program slows down quickly on very large files. The benchmark is designed to show this.

---

## Known Issues and Limitations

- **Hardcoded Windows paths in `lcs.py`.** The test block at the bottom uses paths with backslashes, such as `merge_optimizer\\samples\\...`. These will not work on Linux or macOS. Replace them with `os.path.join` calls, like the ones used in other files.
- **Sample folder is required for some scripts.** `diff.py`, `merge.py`, and `gui.py` look for a `samples/` folder next to the code. If it is missing, the GUI shows an empty sample list.
- **`diff.py` test block does nothing useful.** The code that prints the hunks is commented out, so running the file directly prints nothing.
- **Memory usage is high for large files.** The LCS table is stored in full. For files with tens of thousands of lines, a more memory-efficient method would be needed.
- **Conflict markers can clash with real content.** If a file already contains a line that matches a marker exactly, the GUI may read it as a conflict boundary when it loads the merged output.
- **Benchmark measures only part of the work.** `peak_memory_kb` measures only the LCS table, not the full merge. The time measurement covers the whole merge.
- **Line endings.** Files are read in text mode and split with `splitlines()`, so the output uses `\n` line endings.

---

## Example

Base file:

```
def greet(name):
    print("Hello", name)
```

Dev A changes the greeting. Dev B changes the same line differently. The result is:

```
def greet(name):
<<<<<<< Dev A
    print("Hi", name)
=======
    print("Hey", name)
>>>>>>> Dev B
```

If only Dev A changed the greeting and Dev B changed a different line, both changes would be applied with no conflict markers.

---


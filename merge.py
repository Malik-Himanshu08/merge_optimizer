# merge.py
import os

from lcs import read_lines
from diff import get_hunks, sample_path


def is_insert(h):
    """A pure insertion removes nothing from base."""
    return h["start"] == h["end"]


def overlaps(h1, h2):
    """Do two hunks touch the same part of the base file?"""
    if is_insert(h1) and is_insert(h2):
        return h1["start"] == h2["start"]       # both insert at the same spot
    if is_insert(h1):
        return h2["start"] < h1["start"] < h2["end"]   # insert inside other's range
    if is_insert(h2):
        return h1["start"] < h2["start"] < h1["end"]
    return h1["start"] < h2["end"] and h2["start"] < h1["end"]   # ranges intersect


def apply_hunks(base, hunks, s, e):
    """Build one developer's version of base[s:e] by applying their hunks."""
    out = []
    pos = s
    for h in hunks:
        out += base[pos:h["start"]]     # untouched base lines before the hunk
        out += h["new_lines"]           # the developer's replacement
        pos = h["end"]
    out += base[pos:e]                  # untouched lines after the last hunk
    return out


def merge(base, devA, devB):
    """Three-way merge. Returns (merged_lines, conflicts)."""
    A = get_hunks(base, devA)
    B = get_hunks(base, devB)

    merged = []
    conflicts = []
    pos = 0             # how many base lines have been copied so far
    ia = 0                  # next unused hunk in A
    ib = 0                     # next unused hunk in B

    while ia < len(A) or ib < len(B):
        if ia<len(A):
            ha = A[ia]
        else:
            ha = None
        if ib<len(B):
            hb = B[ib]
        else:
            hb = None

        # Case 1: only one developer has hunks left, or the next hunks don't overlap
        if ha is None or hb is None or not overlaps(ha, hb):
            if hb is None or (ha is not None and (ha["start"], ha["end"]) <= (hb["start"], hb["end"])):
                h = ha
                ia += 1
            else:
                h = hb
                ib += 1
            merged += base[pos:h["start"]]      # copy base up to the change
            merged += h["new_lines"]            # take the change
            pos = h["end"]
            continue

        # Case 2: ha and hb overlap -> grow a region covering everything involved
        s = min(ha["start"], hb["start"])
        e = max(ha["end"], hb["end"])
        a_hunks = [ha]
        b_hunks = [hb]
        ia += 1
        ib += 1
        grew = True
        while grew:                     # absorb further hunks that fall inside the region
            grew = False
            if ia < len(A) and A[ia]["start"] < e:
                a_hunks.append(A[ia])
                e = max(e, A[ia]["end"])
                ia += 1
                grew = True
            if ib < len(B) and B[ib]["start"] < e:
                b_hunks.append(B[ib])
                e = max(e, B[ib]["end"])
                ib += 1
                grew = True

        a_lines = apply_hunks(base, a_hunks, s, e)
        b_lines = apply_hunks(base, b_hunks, s, e)

        merged += base[pos:s]
        if a_lines == b_lines:
            merged += a_lines           # both made the same change: not a conflict
        else:
            conflicts.append({"start": s, "end": e,
                              "a_lines": a_lines, "b_lines": b_lines})
            merged.append("<<<<<<< Dev A")
            merged += a_lines
            merged.append("=======")
            merged += b_lines
            merged.append(">>>>>>> Dev B")
        pos = e

    merged += base[pos:]                # rest of the file nobody touched
    return merged, conflicts


if __name__ == "__main__":
    for folder in ["set1_no_conflict", "set2_conflict"]:
        base =read_lines(sample_path(folder, "base.txt"))
        devA = read_lines(sample_path(folder, "devA.txt"))
        devB = read_lines(sample_path(folder, "devB.txt"))
        merged, conflicts = merge(base, devA, devB)
        print("=" * 10, folder, "=" * 10)
        print("\n".join(merged))
        print("Conflicts found:", len(conflicts))
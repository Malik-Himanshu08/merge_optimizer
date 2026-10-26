import  os
from lcs import backtrack, build_table, read_lines
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def sample_path(*parts):
    return os.path.join(BASE_DIR, "samples", *parts)

def diff(base, dev):
    table = build_table(base, dev)
    pairs = backtrack(base, dev, table)
    diff_result = []
    base_index = 0
    dev_index = 0
    for base_pos, dev_pos in pairs:

        #deleted lines in base before the matched line
        while base_index < base_pos:
            diff_result.append(("deleted", base[base_index], base_index, None))
            base_index+=1

        #added lines in dev before the matched line
        while dev_index < dev_pos:
            diff_result.append(("added", dev[dev_index], None, dev_index))
            dev_index+=1

        #matched line is common to both base and dev
        diff_result.append(("unchanged", base[base_index], base_index, dev_index))
        base_index+=1
        dev_index+=1

    #left after the last match
    while base_index < len(base):
        diff_result.append(("deleted", base[base_index], base_index, None))
        base_index+=1
    while dev_index < len(dev):
        diff_result.append(("added", dev[dev_index], None, dev_index))
        dev_index+=1
    return diff_result

def print_diff(diff_result):
    for change_type, line, _, _ in diff_result:
        if change_type == "added":
            print(f"+ {line}")
        elif change_type == "deleted":
            print(f"- {line}")
        else:
            print(f"  {line}")

def get_hunks(base,devA):
    diff_result = diff(base, devA)
    hunks = []
    current = None
    base_pos = 0
    for change_type, line, base_index, dev_index in diff_result:
        label = change_type
        bi = base_index
        di = dev_index
        if label == "unchanged":
            # an unchanged line ends the current hunk
            if current is not None:
                hunks.append(current)
                current = None
            base_pos = bi + 1
        else:
            # first changed line after unchanged ones: open a new hunk
            if current is None:
                current = {"start": base_pos, "end": base_pos, "new_lines": []}

            if label == "deleted":
                current["end"] = bi + 1
                base_pos = bi + 1
            else:  # added
                current["new_lines"].append(line)

    # a hunk can run to the end of the file
    if current is not None:
        hunks.append(current)

    # label each hunk
    for h in hunks:
        if h["end"] == h["start"]:
            h["type"] = "added"
        elif not h["new_lines"]:
            h["type"] = "deleted"
        else:
            h["type"] = "modified"

    return hunks

if __name__ == "__main__":
    sample_dir = "set1_no_conflict"
    base = read_lines(os.path.join(sample_path(sample_dir), "base.txt"))
    devA = read_lines(os.path.join(sample_path(sample_dir), "devA.txt"))
    devB = read_lines(os.path.join(sample_path(sample_dir), "devB.txt"))
    """print("A: ", get_hunks(base, devA))
    print("B: ", get_hunks(base, devB))"""

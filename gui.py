# gui.py
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from lcs import read_lines
from diff import diff, get_hunks, sample_path
from merge import merge

START = "<<<<<<< Dev A"
MID = "======="
END = ">>>>>>> Dev B"


def parse_segments(merged):
    """
    Turn the merged lines (with conflict markers) into segments:
      {"type": "text", "lines": [...]}
      {"type": "conflict", "a": [...], "b": [...], "choice": None}
    """
    segments = []
    text = []
    i = 0
    while i < len(merged):
        if merged[i] == START:
            if text:
                segments.append({"type": "text", "lines": text})
                text = []
            a, b = [], []
            i += 1
            while merged[i] != MID:
                a.append(merged[i])
                i += 1
            i += 1
            while merged[i] != END:
                b.append(merged[i])
                i += 1
            segments.append({"type": "conflict", "a": a, "b": b, "choice": None})
        else:
            text.append(merged[i])
        i += 1
    if text:
        segments.append({"type": "text", "lines": text})
    return segments


def count_types(hunks):
    """Count how many hunks are added, deleted and modified."""
    counts = {"added": 0, "deleted": 0, "modified": 0}
    for h in hunks:
        counts[h["type"]] += 1
    return counts


class MergeApp:
    def __init__(self, root):
        self.root = root
        root.title("Version Control Merge Optimizer")
        root.geometry("1000x680")

        self.paths = {"Base": tk.StringVar(),
                      "Dev A": tk.StringVar(),
                      "Dev B": tk.StringVar()}
        self.segments = []
        self.conflict_idx = []      # positions of conflict segments in self.segments
        self.conflict_pos = []      # text widget positions, used for scrolling

        # --- file selection rows ---
        top = tk.Frame(root)
        top.pack(fill="x", padx=10, pady=10)
        for row, name in enumerate(self.paths):
            tk.Label(top, text=name + " file:", width=10, anchor="w").grid(row=row, column=0)
            tk.Entry(top, textvariable=self.paths[name], width=70).grid(row=row, column=1, padx=5, pady=2)
            tk.Button(top, text="Browse",
                      command=lambda n=name: self.browse(n)).grid(row=row, column=2)

        # --- load sample row ---
        tk.Label(top, text="Samples:", width=10, anchor="w").grid(row=3, column=0)
        self.sample_choice = tk.StringVar()
        folders = self.sample_folders()
        box = ttk.Combobox(top, textvariable=self.sample_choice,
                           values=folders, state="readonly", width=30)
        if folders:
            box.current(0)
        box.grid(row=3, column=1, sticky="w", padx=5, pady=4)
        tk.Button(top, text="Load sample", command=self.load_sample).grid(row=3, column=2)

        # --- buttons ---
        btns = tk.Frame(root)
        btns.pack(fill="x", padx=10)
        tk.Button(btns, text="Merge", width=10, command=self.run_merge).pack(side="left")
        tk.Button(btns, text="Use Dev A", command=lambda: self.resolve("a")).pack(side="left", padx=(15, 3))
        tk.Button(btns, text="Use Dev B", command=lambda: self.resolve("b")).pack(side="left", padx=3)
        tk.Button(btns, text="Use Both", command=lambda: self.resolve("both")).pack(side="left", padx=3)
        tk.Button(btns, text="Save merged file", command=self.save).pack(side="right")

        # --- status line ---
        self.status = tk.Label(root, text="Select the three files and click Merge.", anchor="w")
        self.status.pack(fill="x", padx=10, pady=5)

        # --- summary panel ---
        self.summary = tk.Label(root, text="", anchor="w", justify="left",
                                wraplength=950, fg="#333333")
        self.summary.pack(fill="x", padx=10)

        # --- two tabs: merge result, side by side ---
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        main = tk.Frame(self.tabs)
        self.tabs.add(main, text="Merge result")
        side = tk.Frame(self.tabs)
        self.tabs.add(side, text="Side by side")

        # --- merge result tab: conflict list + output area ---
        self.listbox = tk.Listbox(main, width=28, exportselection=False)
        self.listbox.pack(side="left", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        self.text = tk.Text(main, wrap="none", font=("Consolas", 10), state="disabled")
        yscroll = tk.Scrollbar(main, command=self.text.yview)
        self.text.config(yscrollcommand=yscroll.set)
        yscroll.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.text.tag_config("head", background="#dddddd")
        self.text.tag_config("a", background="#cfe8ff")
        self.text.tag_config("b", background="#ffe0b8")
        self.text.tag_config("resolved", background="#d4f5d4")

        # --- side-by-side tab: three panes with a shared scrollbar ---
        self.panes = {}
        for col, name in enumerate(["Base", "Dev A", "Dev B"]):
            side.columnconfigure(col, weight=1)
            tk.Label(side, text=name, font=("Segoe UI", 10, "bold")).grid(row=0, column=col)
            pane = tk.Text(side, wrap="none", width=30,
                           font=("Consolas", 10), state="disabled")
            pane.grid(row=1, column=col, sticky="nsew", padx=2)
            pane.tag_config("del", background="#ffd0d0")
            pane.tag_config("add", background="#c9f2c9")
            pane.bind("<MouseWheel>", self.on_wheel)
            self.panes[name] = pane
        side.rowconfigure(1, weight=1)

        shared_scroll = tk.Scrollbar(side, command=self.scroll_all)
        shared_scroll.grid(row=1, column=3, sticky="ns")
        for pane in self.panes.values():
            pane.config(yscrollcommand=shared_scroll.set)

    # ---------- actions ----------
    def browse(self, name):
        path = filedialog.askopenfilename(title="Select " + name + " file")
        if path:
            self.paths[name].set(path)

    def sample_folders(self):
        folder = sample_path()
        if not os.path.isdir(folder):
            return []
        return sorted(d for d in os.listdir(folder)
                      if os.path.isdir(os.path.join(folder, d)))

    def load_sample(self):
        folder = self.sample_choice.get()
        if not folder:
            messagebox.showinfo("No samples", "No sample folders found.")
            return
        self.paths["Base"].set(sample_path(folder, "base.txt"))
        self.paths["Dev A"].set(sample_path(folder, "devA.txt"))
        self.paths["Dev B"].set(sample_path(folder, "devB.txt"))
        self.run_merge()            # one click: load and merge

    def run_merge(self):
        try:
            base = read_lines(self.paths["Base"].get())
            devA = read_lines(self.paths["Dev A"].get())
            devB = read_lines(self.paths["Dev B"].get())
        except (OSError, ValueError) as err:
            messagebox.showerror("Error", "Could not read a file:\n" + str(err))
            return

        start = time.perf_counter()
        merged, conflicts = merge(base, devA, devB)
        elapsed = time.perf_counter() - start

        self.segments = parse_segments(merged)
        self.conflict_idx = [k for k, s in enumerate(self.segments) if s["type"] == "conflict"]
        self.render()
        self.refresh_list()
        self.update_status()
        self.update_summary(base, devA, devB, len(conflicts), elapsed)
        self.show_side_by_side(base, devA, devB)

    def resolve(self, choice):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Select a conflict", "Click a conflict in the list first.")
            return
        k = sel[0]
        self.segments[self.conflict_idx[k]]["choice"] = choice
        self.render()
        self.refresh_list()
        self.listbox.selection_set(k)
        self.update_status()

    def on_select(self, event):
        sel = self.listbox.curselection()
        if sel:
            self.text.see(self.conflict_pos[sel[0]])

    def final_lines(self):
        out = []
        for seg in self.segments:
            if seg["type"] == "text":
                out += seg["lines"]
            elif seg["choice"] == "a":
                out += seg["a"]
            elif seg["choice"] == "b":
                out += seg["b"]
            else:
                out += seg["a"] + seg["b"]
        return out

    def save(self):
        if not self.segments:
            messagebox.showinfo("Nothing to save", "Run a merge first.")
            return
        unresolved = sum(1 for k in self.conflict_idx if self.segments[k]["choice"] is None)
        if unresolved:
            messagebox.showwarning("Unresolved conflicts",
                                   str(unresolved) + " conflict(s) still need to be resolved.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", title="Save merged file")
        if path:
            with open(path, "w") as f:
                f.write("\n".join(self.final_lines()) + "\n")
            messagebox.showinfo("Saved", "Merged file saved.")

    # ---------- side-by-side helpers ----------
    def scroll_all(self, *args):
        for pane in self.panes.values():
            pane.yview(*args)

    def on_wheel(self, event):
        for pane in self.panes.values():
            pane.yview_scroll(int(-event.delta / 120), "units")
        return "break"

    def fill_pane(self, name, lines, marked, tag):
        pane = self.panes[name]
        pane.config(state="normal")
        pane.delete("1.0", "end")
        for n, line in enumerate(lines):
            tags = (tag,) if n in marked else ()
            pane.insert("end", f"{n + 1:3d}  {line}\n", tags)
        pane.config(state="disabled")

    def show_side_by_side(self, base, devA, devB):
        da = diff(base, devA)
        db = diff(base, devB)
        deleted = {bi for lab, _, bi, _ in da if lab == "deleted"}
        deleted |= {bi for lab, _, bi, _ in db if lab == "deleted"}
        added_a = {dj for lab, _, _, dj in da if lab == "added"}
        added_b = {dj for lab, _, _, dj in db if lab == "added"}
        self.fill_pane("Base", base, deleted, "del")
        self.fill_pane("Dev A", devA, added_a, "add")
        self.fill_pane("Dev B", devB, added_b, "add")

    def update_summary(self, base, devA, devB, n_conflicts, elapsed):
        ca = count_types(get_hunks(base, devA))
        cb = count_types(get_hunks(base, devB))
        self.summary.config(text=(
            f"Base: {len(base)} lines  |  "
            f"Dev A: {ca['modified']} modified, {ca['added']} added, {ca['deleted']} deleted  |  "
            f"Dev B: {cb['modified']} modified, {cb['added']} added, {cb['deleted']} deleted  |  "
            f"Conflicts: {n_conflicts}  |  Merge time: {elapsed * 1000:.1f} ms"))

    # ---------- merge result display ----------
    def add_lines(self, lines, tag=None):
        tags = (tag,) if tag else ()
        for line in lines:
            self.text.insert("end", line + "\n", tags)

    def render(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.conflict_pos = []
        for seg in self.segments:
            if seg["type"] == "text":
                self.add_lines(seg["lines"])
                continue
            self.conflict_pos.append(self.text.index("end-1c"))
            if seg["choice"] is None:
                self.add_lines([START], "head")
                self.add_lines(seg["a"], "a")
                self.add_lines([MID], "head")
                self.add_lines(seg["b"], "b")
                self.add_lines([END], "head")
            elif seg["choice"] == "a":
                self.add_lines(seg["a"], "resolved")
            elif seg["choice"] == "b":
                self.add_lines(seg["b"], "resolved")
            else:
                self.add_lines(seg["a"] + seg["b"], "resolved")
        self.text.config(state="disabled")

    def refresh_list(self):
        self.listbox.delete(0, "end")
        for n, k in enumerate(self.conflict_idx, start=1):
            choice = self.segments[k]["choice"]
            state = "unresolved" if choice is None else "resolved (" + choice + ")"
            self.listbox.insert("end", "Conflict " + str(n) + " - " + state)

    def update_status(self):
        total = len(self.conflict_idx)
        unresolved = sum(1 for k in self.conflict_idx if self.segments[k]["choice"] is None)
        if total == 0:
            self.status.config(text="Merged automatically. No conflicts found.")
        else:
            self.status.config(text=str(total) + " conflict(s) found, " +
                               str(unresolved) + " unresolved.")


if __name__ == "__main__":
    root = tk.Tk()
    MergeApp(root)
    root.mainloop()
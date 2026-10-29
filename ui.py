# Tkinter front end for the same pipeline as app.py:
# pick folder -> readFolderFiles -> loadMapping -> mapFiles -> preview / export.
import os
import queue
import sys
import threading
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, ttk

from Config import columnMapping
from Input import readFolderFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_PATH = os.path.join(BASE_DIR, "Config", "mapping.yaml")  # absolute, so cwd doesn't matter
PREVIEW_ROWS = 200  # keep the Treeview fast on big files


class QueueWriter:
    """File-like object that sends print() output to a queue (read by the UI thread)."""

    def __init__(self, q):
        self.q = q

    def write(self, text):
        if text:
            self.q.put(("log", text))

    def flush(self):
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SQL cleaner to BI")
        self.geometry("900x600")
        self.q = queue.Queue()   # worker thread -> UI thread messages
        self.mapped = {}         # {filename: mapped DataFrame}, filled after a run
        self._build()
        self.after(100, self._poll)

    def _build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        self.folder = tk.StringVar()
        ttk.Button(top, text="Browse…", command=self._browse).pack(side="left")
        ttk.Entry(top, textvariable=self.folder).pack(side="left", fill="x", expand=True, padx=8)
        self.runBtn = ttk.Button(top, text="Run", command=self._run)
        self.runBtn.pack(side="left")
        self.exportBtn = ttk.Button(top, text="Export to csv…", command=self._export, state="disabled")
        self.exportBtn.pack(side="left", padx=(8, 0))

        panes = ttk.PanedWindow(self, orient="vertical")
        panes.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tabs = ttk.Notebook(panes)          # one tab per mapped file
        panes.add(self.tabs, weight=3)
        self.log = tk.Text(panes, height=8, state="disabled")
        panes.add(self.log, weight=1)

    # --- actions -------------------------------------------------------------
    def _browse(self):
        path = filedialog.askdirectory(parent=self)
        if path:
            self.folder.set(path)

    def _run(self):
        folder = self.folder.get()
        if not os.path.isdir(folder):
            messagebox.showwarning("No folder", "Pick a valid folder first.")
            return
        self.runBtn.config(state="disabled")
        self.exportBtn.config(state="disabled")
        self._logWrite(f"--- running on {folder}\n")
        # heavy work off the UI thread so the window doesn't freeze
        threading.Thread(target=self._work, args=(folder,), daemon=True).start()

    def _work(self, folder):
        old = sys.stdout
        sys.stdout = QueueWriter(self.q)  # capture the print() calls in the input/mapping code
        try:
            found = readFolderFiles.readFolderFiles(folder)
            mapped = columnMapping.mapFiles(found, columnMapping.loadMapping(MAPPING_PATH))
            self.q.put(("done", mapped))
        except Exception as e:
            self.q.put(("error", f"{e}\n{traceback.format_exc()}"))
        finally:
            sys.stdout = old

    def _export(self):
        if not self.mapped:
            return
        outDir = filedialog.askdirectory(parent=self, title="Export to folder")
        if not outDir:
            return
        for name, df in self.mapped.items():
            df.to_csv(os.path.join(outDir, os.path.splitext(name)[0] + "_clean.csv"), index=False)
        self._logWrite(f"exported {len(self.mapped)} file(s) to {outDir}\n")

    # --- UI thread plumbing ----------------------------------------------------
    def _poll(self):
        """Drain worker messages; widgets may only be touched from this thread."""
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "log":
                    self._logWrite(payload)
                elif kind == "done":
                    self._show(payload)
                elif kind == "error":
                    self._logWrite(payload)
                    messagebox.showerror("Error", payload.splitlines()[0])
                    self.runBtn.config(state="normal")
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _logWrite(self, text):
        self.log.config(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.config(state="disabled")

    def _show(self, mapped):
        self.mapped = mapped
        for tab in self.tabs.tabs():
            self.tabs.forget(tab)
        for name, df in mapped.items():
            frame = ttk.Frame(self.tabs)
            tree = ttk.Treeview(frame, columns=list(df.columns), show="headings")
            for c in df.columns:
                tree.heading(c, text=c)
                tree.column(c, width=110)
            for row in df.head(PREVIEW_ROWS).itertuples(index=False):
                tree.insert("", "end", values=["" if v is None or v != v else v for v in row])
            sx = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
            sy = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
            sy.pack(side="right", fill="y")
            sx.pack(side="bottom", fill="x")
            tree.pack(fill="both", expand=True)
            self.tabs.add(frame, text=f"{name} ({len(df)} rows)")
        self._logWrite(f"done: {len(mapped)} file(s) mapped\n")
        self.runBtn.config(state="normal")
        self.exportBtn.config(state="normal" if mapped else "disabled")


if __name__ == "__main__":
    App().mainloop()

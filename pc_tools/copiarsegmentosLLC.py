#!/usr/bin/env python3
"""
Copiar segmentos LLC / LosslessCut PC.

Herramienta Windows con tkinter para buscar recursivamente fragmentos editados,
seleccionarlos y copiarlos a una carpeta destino sin duplicar nombres existentes.
"""

from __future__ import annotations

import os
import re
import shutil
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".3gp",
    ".webm",
    ".m4v",
    ".mts",
    ".m2ts",
    ".avi",
}

EDITED_TIME_RANGE = re.compile(
    r".*\d{2}\.\d{2}\.\d{2}\.\d{3}.*\d{2}\.\d{2}\.\d{2}\.\d{3}.*",
    re.IGNORECASE,
)


def is_edited_segment(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS and bool(EDITED_TIME_RANGE.match(path.name))


class SegmentCollector:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("copiarsegmentosLLC")
        self.root.geometry("980x680")

        self.source_folder = tk.StringVar()
        self.dest_folder = tk.StringVar()
        self.segments: list[Path] = []
        self.check_vars: list[tk.BooleanVar] = []

        top = ttk.LabelFrame(root, text="Carpetas", padding=10)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Origen:").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.source_folder, width=90).grid(row=0, column=1, padx=5)
        ttk.Button(top, text="Examinar", command=lambda: self.select_folder(self.source_folder)).grid(row=0, column=2)

        ttk.Label(top, text="Destino:").grid(row=1, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.dest_folder, width=90).grid(row=1, column=1, padx=5)
        ttk.Button(top, text="Examinar", command=lambda: self.select_folder(self.dest_folder)).grid(row=1, column=2)

        actions = ttk.Frame(root, padding=8)
        actions.pack(fill="x")
        self.btn_scan = ttk.Button(actions, text="BUSCAR SEGMENTOS", command=self.start_scan)
        self.btn_scan.pack(side="left")
        self.var_select_all = tk.BooleanVar()
        ttk.Checkbutton(actions, text="Seleccionar todos", variable=self.var_select_all, command=self.toggle_all).pack(side="left", padx=12)
        self.btn_copy = ttk.Button(actions, text="COPIAR SELECCIONADOS", command=self.start_copy, state="disabled")
        self.btn_copy.pack(side="right")

        self.status = ttk.Label(root, text="Listo.", foreground="blue")
        self.status.pack(fill="x", padx=10)

        frame_list = ttk.LabelFrame(root, text="Segmentos encontrados", padding=8)
        frame_list.pack(fill="both", expand=True, padx=10, pady=8)
        self.canvas = tk.Canvas(frame_list, bg="white")
        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.canvas.yview)
        self.scrollable = ttk.Frame(self.canvas)
        self.scrollable.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.progress = ttk.Progressbar(root, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0, 10))

    def select_folder(self, var: tk.StringVar) -> None:
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)

    def start_scan(self) -> None:
        if not self.source_folder.get():
            messagebox.showerror("Error", "Selecciona carpeta origen.")
            return
        self.clear_list()
        self.btn_scan.config(state="disabled")
        self.status.config(text="Buscando segmentos...")
        threading.Thread(target=self.scan_worker, daemon=True).start()

    def scan_worker(self) -> None:
        source = Path(self.source_folder.get())
        found = [path for path in source.rglob("*") if path.is_file() and is_edited_segment(path)]
        found.sort(key=lambda p: (p.name.lower(), str(p.parent).lower()))
        self.root.after(0, self.show_results, found)

    def show_results(self, found: list[Path]) -> None:
        self.segments = found
        self.btn_scan.config(state="normal")
        if not found:
            self.status.config(text="No se encontraron segmentos.")
            return
        for path in found:
            var = tk.BooleanVar()
            self.check_vars.append(var)
            row = ttk.Frame(self.scrollable)
            row.pack(fill="x", pady=2, anchor="w")
            ttk.Checkbutton(row, variable=var).pack(side="left")
            label = tk.Label(row, text=str(path), justify="left", anchor="w", bg="white", borderwidth=1, relief="solid")
            label.pack(side="left", fill="x", expand=True, padx=5)
        self.status.config(text=f"Segmentos encontrados: {len(found)}")
        self.btn_copy.config(state="normal")

    def toggle_all(self) -> None:
        state = self.var_select_all.get()
        for var in self.check_vars:
            var.set(state)

    def start_copy(self) -> None:
        if not self.dest_folder.get():
            messagebox.showerror("Error", "Selecciona carpeta destino.")
            return
        selected = [self.segments[i] for i, var in enumerate(self.check_vars) if var.get()]
        if not selected:
            messagebox.showwarning("Aviso", "No hay archivos seleccionados.")
            return
        self.btn_copy.config(state="disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = len(selected)
        self.status.config(text="Copiando...")
        threading.Thread(target=self.copy_worker, args=(selected,), daemon=True).start()

    def copy_worker(self, selected: list[Path]) -> None:
        dest = Path(self.dest_folder.get())
        copied = skipped = errors = 0
        for idx, src in enumerate(selected, start=1):
            try:
                target = dest / src.name
                if target.exists():
                    skipped += 1
                else:
                    shutil.copy2(src, target)
                    copied += 1
            except Exception as exc:
                print(f"Error copiando {src}: {exc}")
                errors += 1
            self.root.after(0, self.update_progress, idx)
        self.root.after(0, self.copy_finished, copied, skipped, errors)

    def update_progress(self, value: int) -> None:
        self.progress["value"] = value
        self.status.config(text=f"Procesados {value}/{int(self.progress['maximum'])}")

    def copy_finished(self, copied: int, skipped: int, errors: int) -> None:
        messagebox.showinfo("Resultado", f"Copiados: {copied}\nOmitidos: {skipped}\nErrores: {errors}")
        self.status.config(text="Proceso finalizado.")
        self.btn_copy.config(state="normal")

    def clear_list(self) -> None:
        for widget in self.scrollable.winfo_children():
            widget.destroy()
        self.segments.clear()
        self.check_vars.clear()
        self.var_select_all.set(False)
        self.btn_copy.config(state="disabled")
        self.progress["value"] = 0


if __name__ == "__main__":
    app_root = tk.Tk()
    SegmentCollector(app_root)
    app_root.mainloop()

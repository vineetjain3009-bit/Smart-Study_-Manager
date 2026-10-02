"""Attendance tracking page with automatic percentage calculations."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ui_helpers import COLORS, make_tree, selected_tree_id
from utils import attendance_percentage


class AttendancePage(tk.Frame):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.subject_choice = tk.StringVar()
        self.total = tk.StringVar()
        self.attended = tk.StringVar()
        self.subject_map: dict[str, int] = {}
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Attendance", bg=COLORS["bg"], fg=COLORS["text"], font=("Segoe UI Semibold", 22)).pack(anchor="w", padx=28, pady=(26, 2))
        tk.Label(self, text="Record classes held and classes attended. Below 75% is highlighted as a warning.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=28, pady=(0, 16))
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        form = tk.Frame(body, bg="white", highlightbackground=COLORS["border"], highlightthickness=1, width=305)
        form.grid(row=0, column=0, sticky="ns", padx=(0, 15))
        form.grid_propagate(False)
        tk.Label(form, text="Update attendance", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=20, pady=(20, 17))
        tk.Label(form, text="Subject", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=20, pady=(0, 5))
        self.subject_combo = ttk.Combobox(form, textvariable=self.subject_choice, state="readonly")
        self.subject_combo.pack(fill="x", padx=20, pady=(0, 12))
        self._entry(form, "Total classes held", self.total)
        self._entry(form, "Classes attended", self.attended)
        self.preview = tk.Label(form, text="Attendance: 0.0%", bg="#eff6ff", fg="#1e40af", font=("Segoe UI Semibold", 10), pady=9)
        self.preview.pack(fill="x", padx=20, pady=(4, 13))
        self.total.trace_add("write", lambda *_: self.update_preview())
        self.attended.trace_add("write", lambda *_: self.update_preview())
        ttk.Button(form, text="Save attendance", style="Primary.TButton", command=self.save_attendance).pack(fill="x", padx=20, pady=(0, 7))
        ttk.Button(form, text="Clear form", command=self.clear_form).pack(fill="x", padx=20, pady=(0, 20))

        card = tk.Frame(body, bg="white", highlightbackground=COLORS["border"], highlightthickness=1)
        card.grid(row=0, column=1, sticky="nsew")
        tk.Label(card, text="Attendance overview", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=20, pady=(20, 5))
        tk.Label(card, text="Double-click a record to load it in the form.", bg="white", fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 12))
        tree_frame = tk.Frame(card, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.tree = make_tree(tree_frame, ("subject", "total", "attended", "percentage", "status"), (170, 110, 120, 115, 125), 15)
        self.tree.bind("<Double-1>", self.load_selected)
        ttk.Button(card, text="Delete selected", style="Danger.TButton", command=self.delete_attendance).pack(anchor="e", padx=20, pady=(0, 18))

    def _entry(self, parent: tk.Widget, label: str, value: tk.StringVar) -> None:
        tk.Label(parent, text=label, bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=20, pady=(0, 5))
        ttk.Entry(parent, textvariable=value).pack(fill="x", padx=20, pady=(0, 12))

    def refresh(self) -> None:
        if not self.app.current_user:
            return
        subjects = self.app.db.get_subjects(self.app.current_user["id"])
        self.subject_map = {f"{row['code']} — {row['name']}": row["id"] for row in subjects}
        self.subject_combo["values"] = tuple(self.subject_map)
        if self.subject_choice.get() not in self.subject_map:
            self.subject_choice.set("")
        for item in self.tree.get_children():
            self.tree.delete(item)
        for record in self.app.db.get_attendance(self.app.current_user["id"]):
            percentage = attendance_percentage(record["total_classes"], record["attended_classes"])
            status = "No classes yet" if record["total_classes"] == 0 else ("On track" if percentage >= 75 else "Below 75%")
            self.tree.insert("", "end", iid=str(record["id"]), values=(f"{record['code']} — {record['name']}", record["total_classes"], record["attended_classes"], f"{percentage:.1f}%", status))

    def update_preview(self) -> None:
        try:
            percentage = attendance_percentage(int(self.total.get() or 0), int(self.attended.get() or 0))
            self.preview.config(text=f"Attendance: {percentage:.1f}%")
        except ValueError:
            self.preview.config(text="Attendance: enter valid numbers")

    def clear_form(self) -> None:
        self.subject_choice.set("")
        self.total.set("")
        self.attended.set("")
        self.tree.selection_remove(self.tree.selection())

    def load_selected(self, _event=None) -> None:
        attendance_id = selected_tree_id(self.tree)
        if not attendance_id:
            return
        records = self.app.db.get_attendance(self.app.current_user["id"])
        record = next((item for item in records if item["id"] == attendance_id), None)
        if not record:
            return
        self.subject_choice.set(next((text for text, ident in self.subject_map.items() if ident == record["subject_id"]), ""))
        self.total.set(str(record["total_classes"]))
        self.attended.set(str(record["attended_classes"]))

    def save_attendance(self) -> None:
        if not self.subject_choice.get() or not self.total.get().strip() or not self.attended.get().strip():
            messagebox.showerror("Missing details", "Subject, total classes, and attended classes are required.")
            return
        try:
            total, attended = int(self.total.get()), int(self.attended.get())
            if total < 0 or attended < 0 or attended > total:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid attendance", "Use whole numbers, with attended classes between 0 and total classes.")
            return
        subject_id = self.subject_map.get(self.subject_choice.get())
        if not subject_id:
            messagebox.showerror("Invalid subject", "Choose a subject from the list.")
            return
        success, message = self.app.db.upsert_attendance(self.app.current_user["id"], subject_id, total, attended)
        if success:
            messagebox.showinfo("Attendance", message)
            self.clear_form()
            self.app.refresh_all_pages()
        else:
            messagebox.showerror("Attendance", message)

    def delete_attendance(self) -> None:
        attendance_id = selected_tree_id(self.tree)
        if not attendance_id:
            messagebox.showwarning("No selection", "Select an attendance record to delete.")
            return
        if not messagebox.askyesno("Delete attendance", "Delete the selected attendance record?"):
            return
        success, message = self.app.db.delete_attendance(attendance_id, self.app.current_user["id"])
        if success:
            messagebox.showinfo("Attendance", message)
            self.clear_form()
            self.app.refresh_all_pages()
        else:
            messagebox.showerror("Attendance", message)

"""Subject CRUD page."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ui_helpers import COLORS, make_tree, selected_tree_id


class SubjectsPage(tk.Frame):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.selected_id: int | None = None
        self.code = tk.StringVar()
        self.name = tk.StringVar()
        self.teacher = tk.StringVar()
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Subjects", bg=COLORS["bg"], fg=COLORS["text"], font=("Segoe UI Semibold", 22)).pack(anchor="w", padx=28, pady=(26, 2))
        tk.Label(self, text="Keep your courses and faculty details in one place.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=28, pady=(0, 16))
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        form = tk.Frame(body, bg="white", highlightbackground=COLORS["border"], highlightthickness=1, width=290)
        form.grid(row=0, column=0, sticky="ns", padx=(0, 15))
        form.grid_propagate(False)
        tk.Label(form, text="Add or edit subject", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=20, pady=(20, 18))
        self._field(form, "Subject code", self.code)
        self._field(form, "Subject name", self.name)
        self._field(form, "Teacher name (optional)", self.teacher)
        self.save_button = ttk.Button(form, text="Add subject", style="Primary.TButton", command=self.save_subject)
        self.save_button.pack(fill="x", padx=20, pady=(12, 8))
        ttk.Button(form, text="Clear form", command=self.clear_form).pack(fill="x", padx=20, pady=5)
        ttk.Button(form, text="Delete selected", style="Danger.TButton", command=self.delete_subject).pack(fill="x", padx=20, pady=(5, 20))

        table_card = tk.Frame(body, bg="white", highlightbackground=COLORS["border"], highlightthickness=1)
        table_card.grid(row=0, column=1, sticky="nsew")
        tk.Label(table_card, text="Your subjects", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=20, pady=(20, 5))
        tk.Label(table_card, text="Double-click a row to edit it.", bg="white", fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 12))
        tree_frame = tk.Frame(table_card, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.tree = make_tree(tree_frame, ("code", "name", "teacher"), (120, 260, 190), 16)
        self.tree.bind("<Double-1>", self.load_selected)

    def _field(self, parent: tk.Widget, label: str, value: tk.StringVar) -> None:
        tk.Label(parent, text=label, bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=20, pady=(0, 5))
        ttk.Entry(parent, textvariable=value).pack(fill="x", padx=20, pady=(0, 14))

    def refresh(self) -> None:
        if not self.app.current_user:
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        for subject in self.app.db.get_subjects(self.app.current_user["id"]):
            self.tree.insert("", "end", iid=str(subject["id"]), values=(subject["code"], subject["name"], subject["teacher"] or "—"))

    def load_selected(self, _event=None) -> None:
        subject_id = selected_tree_id(self.tree)
        if not subject_id:
            return
        item = self.tree.item(str(subject_id))["values"]
        self.selected_id = subject_id
        self.code.set(item[0])
        self.name.set(item[1])
        self.teacher.set("" if item[2] == "—" else item[2])
        self.save_button.config(text="Update subject")

    def clear_form(self) -> None:
        self.selected_id = None
        self.code.set("")
        self.name.set("")
        self.teacher.set("")
        self.save_button.config(text="Add subject")
        self.tree.selection_remove(self.tree.selection())

    def save_subject(self) -> None:
        if not self.code.get().strip() or not self.name.get().strip():
            messagebox.showerror("Missing details", "Subject code and subject name are required.")
            return
        user_id = self.app.current_user["id"]
        if self.selected_id:
            success, message = self.app.db.update_subject(self.selected_id, user_id, self.code.get(), self.name.get(), self.teacher.get())
        else:
            success, message = self.app.db.add_subject(user_id, self.code.get(), self.name.get(), self.teacher.get())
        if success:
            messagebox.showinfo("Subjects", message)
            self.clear_form()
            self.app.refresh_all_pages()
        else:
            messagebox.showerror("Subjects", message)

    def delete_subject(self) -> None:
        subject_id = selected_tree_id(self.tree)
        if not subject_id:
            messagebox.showwarning("No selection", "Select a subject to delete.")
            return
        if not messagebox.askyesno("Delete subject", "Delete this subject? Related study sessions and attendance will also be removed."):
            return
        success, message = self.app.db.delete_subject(subject_id, self.app.current_user["id"])
        if success:
            messagebox.showinfo("Subjects", message)
            self.clear_form()
            self.app.refresh_all_pages()
        else:
            messagebox.showerror("Subjects", message)

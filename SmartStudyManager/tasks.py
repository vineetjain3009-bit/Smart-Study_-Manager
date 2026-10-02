"""Task and assignment management page."""

from __future__ import annotations

from datetime import date
import tkinter as tk
from tkinter import messagebox, ttk

from ui_helpers import COLORS, make_tree, selected_tree_id
from utils import is_valid_date


class TasksPage(tk.Frame):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.selected_id: int | None = None
        self.subject_choice = tk.StringVar()
        self.title = tk.StringVar()
        self.deadline = tk.StringVar(value=date.today().isoformat())
        self.priority = tk.StringVar(value="Medium")
        self.filter_status = tk.StringVar(value="All")
        self.subject_map: dict[str, int] = {}
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Tasks & assignments", bg=COLORS["bg"], fg=COLORS["text"], font=("Segoe UI Semibold", 22)).pack(anchor="w", padx=28, pady=(26, 2))
        tk.Label(self, text="Plan deadlines, assign priorities, and keep progress visible.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=28, pady=(0, 16))
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        form = tk.Frame(body, bg="white", highlightbackground=COLORS["border"], highlightthickness=1, width=305)
        form.grid(row=0, column=0, sticky="ns", padx=(0, 15))
        form.grid_propagate(False)
        tk.Label(form, text="Add or edit task", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=20, pady=(20, 16))
        self.subject_combo = self._combo(form, "Subject", self.subject_choice, ())
        self._entry(form, "Task title", self.title)
        tk.Label(form, text="Description (optional)", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=20, pady=(0, 5))
        self.description = tk.Text(form, height=4, font=("Segoe UI", 9), relief="solid", bd=1, highlightthickness=0)
        self.description.pack(fill="x", padx=20, pady=(0, 12))
        self._entry(form, "Deadline (YYYY-MM-DD)", self.deadline)
        self._combo(form, "Priority", self.priority, ("Low", "Medium", "High"))
        self.save_button = ttk.Button(form, text="Add task", style="Primary.TButton", command=self.save_task)
        self.save_button.pack(fill="x", padx=20, pady=(8, 7))
        ttk.Button(form, text="Clear form", command=self.clear_form).pack(fill="x", padx=20, pady=(0, 18))

        table_card = tk.Frame(body, bg="white", highlightbackground=COLORS["border"], highlightthickness=1)
        table_card.grid(row=0, column=1, sticky="nsew")
        toolbar = tk.Frame(table_card, bg="white")
        toolbar.pack(fill="x", padx=20, pady=(17, 10))
        tk.Label(toolbar, text="Task list", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 13)).pack(side="left")
        ttk.Combobox(toolbar, textvariable=self.filter_status, values=("All", "Pending", "Completed"), state="readonly", width=12).pack(side="right")
        self.filter_status.trace_add("write", lambda *_: self.refresh())
        tree_frame = tk.Frame(table_card, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.tree = make_tree(tree_frame, ("subject", "title", "deadline", "priority", "status"), (95, 225, 105, 90, 95), 13)
        self.tree.bind("<Double-1>", self.load_selected)
        buttons = tk.Frame(table_card, bg="white")
        buttons.pack(fill="x", padx=20, pady=(0, 18))
        ttk.Button(buttons, text="Mark completed", command=lambda: self.set_status("Completed")).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Mark pending", command=lambda: self.set_status("Pending")).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Delete selected", style="Danger.TButton", command=self.delete_task).pack(side="right")

    def _entry(self, parent: tk.Widget, label: str, variable: tk.StringVar) -> None:
        tk.Label(parent, text=label, bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=20, pady=(0, 5))
        ttk.Entry(parent, textvariable=variable).pack(fill="x", padx=20, pady=(0, 12))

    def _combo(self, parent: tk.Widget, label: str, variable: tk.StringVar, values: tuple[str, ...]) -> ttk.Combobox:
        tk.Label(parent, text=label, bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=20, pady=(0, 5))
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
        combo.pack(fill="x", padx=20, pady=(0, 12))
        return combo

    def refresh_subjects(self) -> None:
        if not self.app.current_user:
            return
        subjects = self.app.db.get_subjects(self.app.current_user["id"])
        self.subject_map = {f"{row['code']} — {row['name']}": row["id"] for row in subjects}
        self.subject_combo["values"] = tuple(self.subject_map)
        if self.subject_choice.get() not in self.subject_map:
            self.subject_choice.set("")

    def refresh(self) -> None:
        if not self.app.current_user:
            return
        self.refresh_subjects()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for task in self.app.db.get_tasks(self.app.current_user["id"], self.filter_status.get()):
            self.tree.insert("", "end", iid=str(task["id"]), values=(task["subject_code"], task["title"], task["deadline"], task["priority"], task["status"]))

    def load_selected(self, _event=None) -> None:
        task_id = selected_tree_id(self.tree)
        if not task_id:
            return
        task = self.app.db.get_task(task_id, self.app.current_user["id"])
        if not task:
            return
        self.selected_id = task_id
        self.title.set(task["title"])
        self.deadline.set(task["deadline"])
        self.priority.set(task["priority"])
        self.description.delete("1.0", "end")
        self.description.insert("1.0", task["description"] or "")
        subject_display = next((text for text, ident in self.subject_map.items() if ident == task["subject_id"]), "")
        self.subject_choice.set(subject_display)
        self.save_button.config(text="Update task")

    def clear_form(self) -> None:
        self.selected_id = None
        self.subject_choice.set("")
        self.title.set("")
        self.deadline.set(date.today().isoformat())
        self.priority.set("Medium")
        self.description.delete("1.0", "end")
        self.save_button.config(text="Add task")
        self.tree.selection_remove(self.tree.selection())

    def save_task(self) -> None:
        if not self.subject_choice.get() or not self.title.get().strip() or not self.deadline.get().strip():
            messagebox.showerror("Missing details", "Subject, task title, and deadline are required.")
            return
        if not is_valid_date(self.deadline.get()):
            messagebox.showerror("Invalid date", "Use the date format YYYY-MM-DD, for example 2026-10-05.")
            return
        subject_id = self.subject_map.get(self.subject_choice.get())
        if not subject_id:
            messagebox.showerror("Invalid subject", "Choose a subject from the list.")
            return
        user_id = self.app.current_user["id"]
        values = (user_id, subject_id, self.title.get(), self.description.get("1.0", "end-1c"), self.deadline.get(), self.priority.get())
        if self.selected_id:
            success, message = self.app.db.update_task(self.selected_id, *values)
        else:
            success, message = self.app.db.add_task(*values)
        if success:
            messagebox.showinfo("Tasks", message)
            self.clear_form()
            self.app.refresh_all_pages()
        else:
            messagebox.showerror("Tasks", message)

    def set_status(self, status: str) -> None:
        task_id = selected_tree_id(self.tree)
        if not task_id:
            messagebox.showwarning("No selection", "Select a task first.")
            return
        success, message = self.app.db.set_task_status(task_id, self.app.current_user["id"], status)
        if success:
            self.app.refresh_all_pages()
        else:
            messagebox.showerror("Tasks", message)

    def delete_task(self) -> None:
        task_id = selected_tree_id(self.tree)
        if not task_id:
            messagebox.showwarning("No selection", "Select a task to delete.")
            return
        if not messagebox.askyesno("Delete task", "Delete the selected task?"):
            return
        success, message = self.app.db.delete_task(task_id, self.app.current_user["id"])
        if success:
            messagebox.showinfo("Tasks", message)
            self.clear_form()
            self.app.refresh_all_pages()
        else:
            messagebox.showerror("Tasks", message)

"""Study session entry and history page."""

from __future__ import annotations

from datetime import date
import tkinter as tk
from tkinter import messagebox, ttk

from ui_helpers import COLORS, make_tree, selected_tree_id
from utils import display_hours, is_valid_date


class StudySessionsPage(tk.Frame):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.subject_choice = tk.StringVar()
        self.duration = tk.StringVar()
        self.session_date = tk.StringVar(value=date.today().isoformat())
        self.subject_map: dict[str, int] = {}
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Study sessions", bg=COLORS["bg"], fg=COLORS["text"], font=("Segoe UI Semibold", 22)).pack(anchor="w", padx=28, pady=(26, 2))
        tk.Label(self, text="Log focused study time by subject. A simple record is often all you need.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=28, pady=(0, 16))
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        form = tk.Frame(body, bg="white", highlightbackground=COLORS["border"], highlightthickness=1, width=305)
        form.grid(row=0, column=0, sticky="ns", padx=(0, 15))
        form.grid_propagate(False)
        tk.Label(form, text="Log a session", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=20, pady=(20, 17))
        self.subject_combo = self._combo(form, "Subject", self.subject_choice, ())
        self._entry(form, "Duration in minutes", self.duration)
        self._entry(form, "Study date (YYYY-MM-DD)", self.session_date)
        tk.Label(form, text="Notes (optional)", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=20, pady=(0, 5))
        self.notes = tk.Text(form, height=5, font=("Segoe UI", 9), relief="solid", bd=1, highlightthickness=0)
        self.notes.pack(fill="x", padx=20, pady=(0, 15))
        ttk.Button(form, text="Save session", style="Primary.TButton", command=self.save_session).pack(fill="x", padx=20, pady=(2, 7))
        ttk.Button(form, text="Clear form", command=self.clear_form).pack(fill="x", padx=20, pady=(0, 20))

        card = tk.Frame(body, bg="white", highlightbackground=COLORS["border"], highlightthickness=1)
        card.grid(row=0, column=1, sticky="nsew")
        header = tk.Frame(card, bg="white")
        header.pack(fill="x", padx=20, pady=(18, 8))
        tk.Label(header, text="Study history", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 13)).pack(side="left")
        self.total_label = tk.Label(header, text="Total: 0.0 hrs", bg="#ecfdf5", fg="#166534", font=("Segoe UI Semibold", 9), padx=10, pady=5)
        self.total_label.pack(side="right")
        tree_frame = tk.Frame(card, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.tree = make_tree(tree_frame, ("date", "subject", "duration", "notes"), (105, 155, 105, 250), 15)
        ttk.Button(card, text="Delete selected", style="Danger.TButton", command=self.delete_session).pack(anchor="e", padx=20, pady=(0, 18))

    def _entry(self, parent: tk.Widget, label: str, value: tk.StringVar) -> None:
        tk.Label(parent, text=label, bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=20, pady=(0, 5))
        ttk.Entry(parent, textvariable=value).pack(fill="x", padx=20, pady=(0, 12))

    def _combo(self, parent: tk.Widget, label: str, value: tk.StringVar, choices: tuple[str, ...]) -> ttk.Combobox:
        tk.Label(parent, text=label, bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=20, pady=(0, 5))
        combo = ttk.Combobox(parent, textvariable=value, values=choices, state="readonly")
        combo.pack(fill="x", padx=20, pady=(0, 12))
        return combo

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
        sessions = self.app.db.get_study_sessions(self.app.current_user["id"])
        total_minutes = 0
        for session in sessions:
            total_minutes += session["duration_minutes"]
            self.tree.insert("", "end", iid=str(session["id"]), values=(session["session_date"], session["subject_code"], f"{session['duration_minutes']} min", session["notes"] or "—"))
        self.total_label.config(text=f"Total: {display_hours(total_minutes)}")

    def clear_form(self) -> None:
        self.subject_choice.set("")
        self.duration.set("")
        self.session_date.set(date.today().isoformat())
        self.notes.delete("1.0", "end")

    def save_session(self) -> None:
        if not self.subject_choice.get() or not self.duration.get().strip() or not self.session_date.get().strip():
            messagebox.showerror("Missing details", "Subject, duration, and study date are required.")
            return
        try:
            minutes = int(self.duration.get())
            if minutes <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid duration", "Duration must be a positive whole number of minutes.")
            return
        if not is_valid_date(self.session_date.get()):
            messagebox.showerror("Invalid date", "Use YYYY-MM-DD, for example 2026-10-05.")
            return
        subject_id = self.subject_map.get(self.subject_choice.get())
        if not subject_id:
            messagebox.showerror("Invalid subject", "Choose a subject from the list.")
            return
        success, message = self.app.db.add_study_session(self.app.current_user["id"], subject_id, minutes, self.session_date.get(), self.notes.get("1.0", "end-1c"))
        if success:
            messagebox.showinfo("Study sessions", message)
            self.clear_form()
            self.app.refresh_all_pages()
        else:
            messagebox.showerror("Study sessions", message)

    def delete_session(self) -> None:
        session_id = selected_tree_id(self.tree)
        if not session_id:
            messagebox.showwarning("No selection", "Select a study session to delete.")
            return
        if not messagebox.askyesno("Delete session", "Delete the selected study session?"):
            return
        success, message = self.app.db.delete_study_session(session_id, self.app.current_user["id"])
        if success:
            messagebox.showinfo("Study sessions", message)
            self.app.refresh_all_pages()
        else:
            messagebox.showerror("Study sessions", message)

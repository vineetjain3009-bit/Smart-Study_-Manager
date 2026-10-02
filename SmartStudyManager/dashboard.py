"""Dashboard page with at-a-glance academic statistics."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ui_helpers import COLORS, make_card


class DashboardPage(tk.Frame):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.values: dict[str, tk.Label] = {}
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Dashboard", bg=COLORS["bg"], fg=COLORS["text"], font=("Segoe UI Semibold", 22)).pack(anchor="w", padx=28, pady=(26, 2))
        self.welcome = tk.Label(self, bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10))
        self.welcome.pack(anchor="w", padx=28, pady=(0, 16))

        cards = tk.Frame(self, bg=COLORS["bg"])
        cards.pack(fill="x", padx=22)
        labels = [
            ("Subjects", "subjects", COLORS["blue"]),
            ("Pending tasks", "pending", COLORS["orange"]),
            ("Completed", "completed", COLORS["green"]),
            ("Study time", "study_hours", "#7c3aed"),
            ("Attendance", "attendance", "#0891b2"),
        ]
        for column, (title, key, accent) in enumerate(labels):
            self.values[key] = make_card(cards, column, title, "0", accent)

        action = tk.Frame(self, bg="white", highlightbackground=COLORS["border"], highlightthickness=1)
        action.pack(fill="x", padx=28, pady=(22, 12))
        tk.Label(action, text="Quick start", bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=20, pady=(17, 3))
        tk.Label(action, text="New to the project? Add a few demo records to explore the dashboard, charts, and reports.", bg="white", fg=COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(0, 13))
        ttk.Button(action, text="Add optional sample data", command=self.add_sample_data).pack(anchor="w", padx=20, pady=(0, 18))

        note = tk.Frame(self, bg="#eff6ff", highlightbackground="#bfdbfe", highlightthickness=1)
        note.pack(fill="x", padx=28, pady=8)
        tk.Label(note, text="Tip: Use the sidebar to add your subjects first, then track tasks, sessions, and attendance.", bg="#eff6ff", fg="#1e40af", font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=13)

    def refresh(self) -> None:
        if not self.app.current_user:
            return
        stats = self.app.db.get_dashboard_stats(self.app.current_user["id"])
        self.welcome.config(text=f"Welcome, {self.app.current_user['full_name']}. Here is your semester at a glance.")
        self.values["subjects"].config(text=str(stats["subjects"]))
        self.values["pending"].config(text=str(stats["pending"]))
        self.values["completed"].config(text=str(stats["completed"]))
        self.values["study_hours"].config(text=f"{stats['study_hours']:.1f} hrs")
        self.values["attendance"].config(text=f"{stats['attendance']:.1f}%")

    def add_sample_data(self) -> None:
        if not messagebox.askyesno("Optional sample data", "Add three sample subjects and related demo records? This is available only for a new account."):
            return
        success, message = self.app.db.insert_sample_data(self.app.current_user["id"])
        if success:
            messagebox.showinfo("Sample data", message)
            self.app.refresh_all_pages()
        else:
            messagebox.showwarning("Sample data", message)

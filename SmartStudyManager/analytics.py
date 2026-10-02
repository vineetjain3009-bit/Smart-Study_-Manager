"""Matplotlib charts based on the student's real SQLite data."""

from __future__ import annotations

import tkinter as tk

from ui_helpers import COLORS


class AnalyticsPage(tk.Frame):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.chart_area = tk.Frame(self, bg="white", highlightbackground=COLORS["border"], highlightthickness=1)
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Performance analytics", bg=COLORS["bg"], fg=COLORS["text"], font=("Segoe UI Semibold", 22)).pack(anchor="w", padx=28, pady=(26, 2))
        tk.Label(self, text="Visualise your recorded study time, attendance, and task progress.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=28, pady=(0, 16))
        self.chart_area.pack(fill="both", expand=True, padx=28, pady=(0, 28))

    def refresh(self) -> None:
        if not self.app.current_user:
            return
        for child in self.chart_area.winfo_children():
            child.destroy()
        data = self.app.db.get_analytics_data(self.app.current_user["id"])
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
        except ImportError:
            tk.Label(self.chart_area, text="Matplotlib is not installed. Run: pip install -r requirements.txt", bg="white", fg=COLORS["red"], font=("Segoe UI", 11)).pack(expand=True)
            return

        figure = Figure(figsize=(11, 5.2), dpi=100, facecolor="white")
        axes = figure.subplots(1, 3)
        figure.subplots_adjust(left=.06, right=.97, bottom=.17, top=.86, wspace=.35)
        self._study_chart(axes[0], data["study"])
        self._attendance_chart(axes[1], data["attendance"])
        self._task_chart(axes[2], data["tasks"])
        canvas = FigureCanvasTkAgg(figure, master=self.chart_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    @staticmethod
    def _empty(axis, title: str, message: str) -> None:
        axis.set_title(title, fontsize=12, fontweight="bold", color=COLORS["text"])
        axis.text(.5, .5, message, ha="center", va="center", wrap=True, color=COLORS["muted"], fontsize=10, transform=axis.transAxes)
        axis.set_xticks([])
        axis.set_yticks([])
        for spine in axis.spines.values():
            spine.set_visible(False)

    def _study_chart(self, axis, rows) -> None:
        rows = [row for row in rows if row["hours"] > 0]
        if not rows:
            self._empty(axis, "Study hours by subject", "No study sessions recorded yet.")
            return
        axis.bar([row["code"] for row in rows], [row["hours"] for row in rows], color="#2563eb", width=.58)
        axis.set_title("Study hours by subject", fontsize=12, fontweight="bold", color=COLORS["text"])
        axis.set_ylabel("Hours")
        axis.grid(axis="y", alpha=.2)
        for position in ("top", "right"):
            axis.spines[position].set_visible(False)

    def _attendance_chart(self, axis, rows) -> None:
        rows = [row for row in rows if row["attendance_id"] is not None]
        if not rows:
            self._empty(axis, "Attendance by subject", "No attendance records yet.")
            return
        values = [row["percentage"] for row in rows]
        colors = ["#16a34a" if value >= 75 else "#ea580c" for value in values]
        axis.bar([row["code"] for row in rows], values, color=colors, width=.58)
        axis.axhline(75, color="#dc2626", linestyle="--", linewidth=1, label="75% target")
        axis.set_ylim(0, 105)
        axis.set_ylabel("Percentage")
        axis.set_title("Attendance by subject", fontsize=12, fontweight="bold", color=COLORS["text"])
        axis.grid(axis="y", alpha=.2)
        axis.legend(fontsize=8, frameon=False)
        for position in ("top", "right"):
            axis.spines[position].set_visible(False)

    def _task_chart(self, axis, rows) -> None:
        counts = {row["status"]: row["total"] for row in rows}
        if not counts:
            self._empty(axis, "Task completion", "No tasks recorded yet.")
            return
        labels = ["Pending", "Completed"]
        values = [counts.get(label, 0) for label in labels]
        axis.bar(labels, values, color=["#f59e0b", "#16a34a"], width=.58)
        axis.set_title("Task completion", fontsize=12, fontweight="bold", color=COLORS["text"])
        axis.set_ylabel("Tasks")
        axis.grid(axis="y", alpha=.2)
        for position in ("top", "right"):
            axis.spines[position].set_visible(False)

"""Readable on-screen report plus TXT and CSV export."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ui_helpers import COLORS
from utils import attendance_percentage, display_hours


class ReportsPage(tk.Frame):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.report_data: dict[str, object] | None = None
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Reports", bg=COLORS["bg"], fg=COLORS["text"], font=("Segoe UI Semibold", 22)).pack(anchor="w", padx=28, pady=(26, 2))
        tk.Label(self, text="A concise semester summary that you can save as a TXT or CSV file.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=28, pady=(0, 14))
        toolbar = tk.Frame(self, bg=COLORS["bg"])
        toolbar.pack(fill="x", padx=28, pady=(0, 10))
        ttk.Button(toolbar, text="Refresh report", command=self.refresh).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Export TXT or CSV", style="Primary.TButton", command=self.export_report).pack(side="left")
        card = tk.Frame(self, bg="white", highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        self.text = tk.Text(card, font=("Consolas", 10), bg="white", fg=COLORS["text"], relief="flat", wrap="word", padx=20, pady=18, state="disabled")
        scroll = ttk.Scrollbar(card, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def refresh(self) -> None:
        if not self.app.current_user:
            return
        self.report_data = self.app.db.get_report_data(self.app.current_user["id"])
        content = self._format_report(self.report_data)
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.config(state="disabled")

    def _format_report(self, data: dict[str, object]) -> str:
        user, stats = data["user"], data["stats"]
        lines = [
            "SMART STUDY MANAGER — SEMESTER REPORT",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
            "",
            "STUDENT INFORMATION",
            f"Name: {user['full_name']}",
            f"Username: {user['username']}",
            "",
            "OVERALL STATISTICS",
            f"Subjects: {stats['subjects']}",
            f"Tasks: {stats['pending']} pending, {stats['completed']} completed",
            f"Total study time: {stats['study_hours']:.1f} hours",
            f"Overall attendance: {stats['attendance']:.1f}%",
            "",
            "SUBJECTS",
        ]
        subjects = data["subjects"]
        lines.extend([f"- {row['code']}: {row['name']} ({row['teacher'] or 'Teacher not entered'})" for row in subjects] or ["No subjects added yet."])
        lines.extend(["", "ATTENDANCE"])
        attendance = data["attendance"]
        for row in attendance:
            percent = attendance_percentage(row["total_classes"], row["attended_classes"])
            warning = " — BELOW 75%" if row["total_classes"] and percent < 75 else ""
            lines.append(f"- {row['code']}: {row['attended_classes']}/{row['total_classes']} classes ({percent:.1f}%){warning}")
        if not attendance:
            lines.append("No attendance records added yet.")
        lines.extend(["", "STUDY SESSIONS"])
        sessions = data["sessions"]
        lines.extend([f"- {row['session_date']} | {row['subject_code']} | {display_hours(row['duration_minutes'])}" for row in sessions] or ["No study sessions added yet."])
        lines.extend(["", "TASKS"])
        tasks = data["tasks"]
        lines.extend([f"- [{row['status']}] {row['subject_code']} — {row['title']} (Due: {row['deadline']}, {row['priority']} priority)" for row in tasks] or ["No tasks added yet."])
        return "\n".join(lines) + "\n"

    def export_report(self) -> None:
        if not self.report_data:
            self.refresh()
        filename = filedialog.asksaveasfilename(
            title="Export report",
            defaultextension=".txt",
            filetypes=(("Text report", "*.txt"), ("CSV spreadsheet", "*.csv")),
            initialfile="smart_study_report.txt",
        )
        if not filename:
            return
        try:
            path = Path(filename)
            if path.suffix.lower() == ".csv":
                self._write_csv(path, self.report_data)
            else:
                path.write_text(self._format_report(self.report_data), encoding="utf-8")
            messagebox.showinfo("Report exported", f"Saved report to:\n{path}")
        except OSError as error:
            messagebox.showerror("Export failed", f"Could not save the report:\n{error}")

    @staticmethod
    def _write_csv(path: Path, data: dict[str, object]) -> None:
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["SMART STUDY MANAGER REPORT"])
            writer.writerow(["Student", data["user"]["full_name"]])
            writer.writerow([])
            writer.writerow(["Subjects"])
            writer.writerow(["Code", "Name", "Teacher"])
            for row in data["subjects"]:
                writer.writerow([row["code"], row["name"], row["teacher"] or ""])
            writer.writerow([])
            writer.writerow(["Attendance"])
            writer.writerow(["Subject", "Total classes", "Attended classes", "Percentage"])
            for row in data["attendance"]:
                writer.writerow([row["code"], row["total_classes"], row["attended_classes"], f"{attendance_percentage(row['total_classes'], row['attended_classes']):.1f}%"])
            writer.writerow([])
            writer.writerow(["Study sessions"])
            writer.writerow(["Date", "Subject", "Duration minutes", "Notes"])
            for row in data["sessions"]:
                writer.writerow([row["session_date"], row["subject_code"], row["duration_minutes"], row["notes"] or ""])
            writer.writerow([])
            writer.writerow(["Tasks"])
            writer.writerow(["Subject", "Title", "Deadline", "Priority", "Status"])
            for row in data["tasks"]:
                writer.writerow([row["subject_code"], row["title"], row["deadline"], row["priority"], row["status"]])

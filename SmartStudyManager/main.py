"""Application entry point for Smart Study Manager."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from analytics import AnalyticsPage
from attendance import AttendancePage
from dashboard import DashboardPage
from database import Database
from login import LoginScreen
from reports import ReportsPage
from study_sessions import StudySessionsPage
from subjects import SubjectsPage
from tasks import TasksPage
from ui_helpers import COLORS, configure_styles


class SmartStudyManagerApp:
    """Coordinates the login screen, navigation shell, and feature pages."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Smart Study Manager")
        self.root.geometry("1180x720")
        self.root.minsize(1000, 620)
        configure_styles(self.root)
        self.db = Database()
        self.current_user = None
        self.login_screen: LoginScreen | None = None
        self.shell: tk.Frame | None = None
        self.pages: dict[str, tk.Frame] = {}
        self.nav_buttons: dict[str, tk.Button] = {}
        self.build_login()

    def build_login(self) -> None:
        self.login_screen = LoginScreen(self.root, self)
        self.login_screen.pack(fill="both", expand=True)

    def login_success(self, user) -> None:
        self.current_user = user
        if self.login_screen:
            self.login_screen.destroy()
            self.login_screen = None
        self.build_shell()
        self.show_page("Dashboard")

    def build_shell(self) -> None:
        self.shell = tk.Frame(self.root, bg=COLORS["bg"])
        self.shell.pack(fill="both", expand=True)
        sidebar = tk.Frame(self.shell, bg=COLORS["navy"], width=222)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="SMART STUDY", bg=COLORS["navy"], fg="white", font=("Segoe UI Semibold", 15)).pack(anchor="w", padx=20, pady=(25, 1))
        tk.Label(sidebar, text="MANAGER", bg=COLORS["navy"], fg="#93c5fd", font=("Segoe UI", 9)).pack(anchor="w", padx=21, pady=(0, 23))
        for name in ("Dashboard", "Subjects", "Tasks", "Study Sessions", "Attendance", "Analytics", "Reports"):
            button = tk.Button(sidebar, text=name, command=lambda page=name: self.show_page(page), anchor="w", relief="flat", bd=0, padx=20, pady=11, bg=COLORS["navy"], fg="#dbeafe", activebackground=COLORS["navy_light"], activeforeground="white", font=("Segoe UI Semibold", 10), cursor="hand2")
            button.pack(fill="x", padx=9, pady=1)
            self.nav_buttons[name] = button
        spacer = tk.Frame(sidebar, bg=COLORS["navy"])
        spacer.pack(fill="both", expand=True)
        tk.Label(sidebar, text=f"Signed in as\n{self.current_user['full_name']}", bg=COLORS["navy"], fg="#bfdbfe", justify="left", font=("Segoe UI", 9), wraplength=174).pack(anchor="w", padx=20, pady=(8, 9))
        tk.Button(sidebar, text="↪  Log out", command=self.logout, anchor="w", relief="flat", bd=0, padx=20, pady=11, bg=COLORS["navy"], fg="#fecaca", activebackground="#7f1d1d", activeforeground="white", font=("Segoe UI Semibold", 10), cursor="hand2").pack(fill="x", padx=9, pady=(0, 20))

        content = tk.Frame(self.shell, bg=COLORS["bg"])
        content.pack(side="left", fill="both", expand=True)
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=1)
        page_classes = {
            "Dashboard": DashboardPage,
            "Subjects": SubjectsPage,
            "Tasks": TasksPage,
            "Study Sessions": StudySessionsPage,
            "Attendance": AttendancePage,
            "Analytics": AnalyticsPage,
            "Reports": ReportsPage,
        }
        for name, page_class in page_classes.items():
            page = page_class(content, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page

    def show_page(self, name: str) -> None:
        page = self.pages[name]
        page.tkraise()
        if hasattr(page, "refresh"):
            page.refresh()
        for label, button in self.nav_buttons.items():
            selected = label == name
            button.config(bg=COLORS["navy_light"] if selected else COLORS["navy"], fg="white" if selected else "#dbeafe")

    def refresh_all_pages(self) -> None:
        """Refresh pages after a data change so dashboard and reports stay current."""
        for page in self.pages.values():
            if hasattr(page, "refresh"):
                page.refresh()

    def logout(self) -> None:
        if not messagebox.askyesno("Log out", "Log out of Smart Study Manager?"):
            return
        if self.shell:
            self.shell.destroy()
            self.shell = None
        self.pages.clear()
        self.nav_buttons.clear()
        self.current_user = None
        self.build_login()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    SmartStudyManagerApp().run()

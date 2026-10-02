"""Local login and registration screen."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ui_helpers import COLORS


class LoginScreen(tk.Frame):
    """A two-panel welcome screen containing login and registration forms."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.showing_login = True
        self.login_user = tk.StringVar()
        self.login_password = tk.StringVar()
        self.register_name = tk.StringVar()
        self.register_user = tk.StringVar()
        self.register_password = tk.StringVar()
        self.register_confirm = tk.StringVar()
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=5)
        self.columnconfigure(1, weight=6)
        self.rowconfigure(0, weight=1)

        intro = tk.Frame(self, bg=COLORS["navy"])
        intro.grid(row=0, column=0, sticky="nsew")
        tk.Label(intro, text="Smart\nStudy Manager", bg=COLORS["navy"], fg="white", font=("Segoe UI Semibold", 30), justify="left").place(relx=.12, rely=.30)
        tk.Label(intro, text="Organise your semester.\nFocus on what matters.", bg=COLORS["navy"], fg="#c7d7fe", font=("Segoe UI", 13), justify="left").place(relx=.12, rely=.53)
        tk.Label(intro, text="Offline • Private • Built for students", bg=COLORS["navy"], fg="#93c5fd", font=("Segoe UI", 10)).place(relx=.12, rely=.82)

        right = tk.Frame(self, bg=COLORS["bg"])
        right.grid(row=0, column=1, sticky="nsew")
        self.form_card = tk.Frame(right, bg="white", highlightbackground=COLORS["border"], highlightthickness=1)
        self.form_card.place(relx=.5, rely=.5, anchor="center", width=390, height=460)
        self.form_card.columnconfigure(0, weight=1)
        self.render_form()

    def render_form(self) -> None:
        for widget in self.form_card.winfo_children():
            widget.destroy()
        if self.showing_login:
            self._login_form()
        else:
            self._register_form()

    def _heading(self, title: str, subtitle: str) -> None:
        tk.Label(self.form_card, text=title, bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 22)).grid(row=0, column=0, sticky="w", padx=38, pady=(38, 5))
        tk.Label(self.form_card, text=subtitle, bg="white", fg=COLORS["muted"], font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=38, pady=(0, 22))

    def _entry(self, row: int, label: str, variable: tk.StringVar, secret: bool = False) -> None:
        tk.Label(self.form_card, text=label, bg="white", fg=COLORS["text"], font=("Segoe UI Semibold", 9)).grid(row=row, column=0, sticky="w", padx=38, pady=(0, 5))
        ttk.Entry(self.form_card, textvariable=variable, show="•" if secret else "", width=34).grid(row=row + 1, column=0, sticky="ew", padx=38, pady=(0, 14))

    def _login_form(self) -> None:
        self._heading("Welcome back", "Sign in to continue your study plan.")
        self._entry(2, "Username", self.login_user)
        self._entry(4, "Password", self.login_password, True)
        ttk.Button(self.form_card, text="Log in", style="Primary.TButton", command=self.login).grid(row=6, column=0, sticky="ew", padx=38, pady=(5, 14))
        tk.Button(self.form_card, text="New here? Create an account", command=self.switch_form, bg="white", fg=COLORS["blue"], activebackground="white", bd=0, cursor="hand2", font=("Segoe UI Semibold", 9)).grid(row=7, column=0, pady=3)
        self.form_card.bind_all("<Return>", lambda event: self.login() if self.showing_login else self.register())

    def _register_form(self) -> None:
        self._heading("Create account", "Your account stays only on this computer.")
        self._entry(2, "Full name", self.register_name)
        self._entry(4, "Username", self.register_user)
        self._entry(6, "Password", self.register_password, True)
        self._entry(8, "Confirm password", self.register_confirm, True)
        ttk.Button(self.form_card, text="Create account", style="Primary.TButton", command=self.register).grid(row=10, column=0, sticky="ew", padx=38, pady=(0, 10))
        tk.Button(self.form_card, text="Already registered? Log in", command=self.switch_form, bg="white", fg=COLORS["blue"], activebackground="white", bd=0, cursor="hand2", font=("Segoe UI Semibold", 9)).grid(row=11, column=0, pady=2)

    def switch_form(self) -> None:
        self.showing_login = not self.showing_login
        self.render_form()

    def login(self) -> None:
        username, password = self.login_user.get().strip(), self.login_password.get()
        if not username or not password:
            messagebox.showerror("Missing details", "Enter both username and password.")
            return
        user = self.app.db.authenticate(username, password)
        if not user:
            messagebox.showerror("Login failed", "Username or password is incorrect.")
            return
        self.login_password.set("")
        self.app.login_success(user)

    def register(self) -> None:
        name, username = self.register_name.get().strip(), self.register_user.get().strip()
        password, confirm = self.register_password.get(), self.register_confirm.get()
        if not name or not username or not password or not confirm:
            messagebox.showerror("Missing details", "Please complete every field.")
            return
        if len(username) < 3:
            messagebox.showerror("Invalid username", "Use at least 3 characters for the username.")
            return
        if len(password) < 4:
            messagebox.showerror("Invalid password", "Use at least 4 characters for the password.")
            return
        if password != confirm:
            messagebox.showerror("Password mismatch", "The passwords do not match.")
            return
        success, message = self.app.db.register_user(username, password, name)
        if success:
            messagebox.showinfo("Account created", message)
            self.login_user.set(username)
            self.register_name.set("")
            self.register_user.set("")
            self.register_password.set("")
            self.register_confirm.set("")
            self.showing_login = True
            self.render_form()
        else:
            messagebox.showerror("Registration failed", message)

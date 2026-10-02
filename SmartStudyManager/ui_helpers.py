"""Reusable Tkinter widgets and style configuration."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


COLORS = {
    "navy": "#172554",
    "navy_light": "#1e3a8a",
    "blue": "#2563eb",
    "blue_hover": "#1d4ed8",
    "bg": "#f4f7fb",
    "card": "#ffffff",
    "text": "#172033",
    "muted": "#64748b",
    "border": "#dbe3ef",
    "green": "#16a34a",
    "orange": "#ea580c",
    "red": "#dc2626",
}


def configure_styles(root: tk.Tk) -> None:
    """Apply a calm, consistent ttk theme to the whole app."""
    root.configure(bg=COLORS["bg"])
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Card.TFrame", background=COLORS["card"])
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI", 10))
    style.configure("Title.TLabel", font=("Segoe UI Semibold", 21), foreground=COLORS["text"], background=COLORS["bg"])
    style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground=COLORS["muted"], background=COLORS["bg"])
    style.configure("CardTitle.TLabel", font=("Segoe UI", 10), foreground=COLORS["muted"], background=COLORS["card"])
    style.configure("CardValue.TLabel", font=("Segoe UI Semibold", 22), foreground=COLORS["text"], background=COLORS["card"])
    style.configure("TButton", font=("Segoe UI Semibold", 9), padding=(12, 7))
    style.configure("Primary.TButton", background=COLORS["blue"], foreground="white", borderwidth=0)
    style.map("Primary.TButton", background=[("active", COLORS["blue_hover"])])
    style.configure("Danger.TButton", background=COLORS["red"], foreground="white", borderwidth=0)
    style.map("Danger.TButton", background=[("active", "#b91c1c")])
    style.configure("TEntry", padding=6)
    style.configure("TCombobox", padding=5)
    style.configure("Treeview", font=("Segoe UI", 9), rowheight=29, background="white", fieldbackground="white", foreground=COLORS["text"])
    style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9), background="#e8eef8", foreground=COLORS["text"], relief="flat", padding=7)
    style.map("Treeview", background=[("selected", "#c7d7fe")], foreground=[("selected", COLORS["text"])])


def make_card(parent: tk.Widget, column: int, title: str, value: str, accent: str = COLORS["blue"]) -> ttk.Label:
    card = tk.Frame(parent, bg=COLORS["card"], highlightbackground=COLORS["border"], highlightthickness=1)
    card.grid(row=0, column=column, sticky="nsew", padx=6, pady=6)
    tk.Frame(card, bg=accent, height=4).pack(fill="x")
    tk.Label(card, text=title, bg=COLORS["card"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(15, 2))
    value_label = tk.Label(card, text=value, bg=COLORS["card"], fg=COLORS["text"], font=("Segoe UI Semibold", 22))
    value_label.pack(anchor="w", padx=16, pady=(0, 15))
    parent.grid_columnconfigure(column, weight=1)
    return value_label


def make_tree(parent: tk.Widget, columns: tuple[str, ...], widths: tuple[int, ...], height: int = 14) -> ttk.Treeview:
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=height, selectmode="browse")
    for column, width in zip(columns, widths):
        tree.heading(column, text=column.replace("_", " ").title())
        tree.column(column, width=width, minwidth=70, anchor="w")
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)
    return tree


def selected_tree_id(tree: ttk.Treeview) -> int | None:
    selected = tree.selection()
    return int(selected[0]) if selected else None

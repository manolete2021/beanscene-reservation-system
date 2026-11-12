"""The shared look of every screen: colours, fonts and the message bar.

Keeping these in one module gives the four screens the same clear,
consistent and readable layout, which is what the paper marks.
"""

import tkinter as tk
from tkinter import ttk

COLOURS = {
    "background": "#f5f7f6",
    "text": "#17201d",
    "muted": "#56635e",
    "accent": "#1d6b57",
    "free": "#dcefe8",
    "free_text": "#1d6b57",
    "occupied": "#f1e6dc",
    "occupied_text": "#6b4428",
    "success": "#e1f2e5",
    "success_text": "#2c7a3f",
    "error": "#fbe3e1",
    "error_text": "#a12a1f",
}

FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_HEADING = ("Segoe UI", 14, "bold")
PAD = 8


def apply_style(window):
    """Give every ttk widget in the window the same theme, colours and fonts."""
    style = ttk.Style(window)
    style.theme_use("clam")
    window.configure(background=COLOURS["background"])
    style.configure(".", font=FONT, background=COLOURS["background"], foreground=COLOURS["text"])
    style.configure("TLabelframe.Label", font=FONT_BOLD, foreground=COLOURS["accent"])
    style.configure("Heading.TLabel", font=FONT_HEADING)
    style.configure("Muted.TLabel", foreground=COLOURS["muted"])
    style.configure("TNotebook.Tab", padding=(16, 6), font=FONT_BOLD)
    style.configure("Accent.TButton", font=FONT_BOLD, foreground="#ffffff", background=COLOURS["accent"])
    style.map("Accent.TButton", background=[("active", "#17594a")])
    style.configure("Treeview", rowheight=24)
    style.configure("Treeview.Heading", font=FONT_BOLD)


def make_message_bar(window):
    """The one line at the bottom of the window where every screen shows its messages."""
    bar = tk.Label(window, text="Ready.", anchor="w", padx=12, pady=6, font=FONT,
                   background="#e9eeec", foreground=COLOURS["text"])
    bar.pack(side="bottom", fill="x")
    return bar


def show_success(bar, text):
    """Show a success message in green."""
    bar.configure(text=text, background=COLOURS["success"], foreground=COLOURS["success_text"])


def show_error(bar, text):
    """Show a refused change or a mistake in red, in plain words. The app keeps running."""
    bar.configure(text=text, background=COLOURS["error"], foreground=COLOURS["error_text"])


def labelled_entry(parent, row, label, width=24):
    """Put a label and a text box on one row of a grid, and return the text box."""
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=PAD, pady=4)
    entry = ttk.Entry(parent, width=width)
    entry.grid(row=row, column=1, sticky="we", padx=PAD, pady=4)
    return entry


def read_whole_number(entry, field_name):
    """Read a whole number from a text box. Anything else is refused with a message."""
    text = entry.get().strip()
    if not text.isdigit():
        raise ValueError(f"{field_name} must be a whole number.")
    return int(text)


def clear_tree(tree):
    """Remove every row from a table (Treeview) before it is filled again."""
    for item in tree.get_children():
        tree.delete(item)

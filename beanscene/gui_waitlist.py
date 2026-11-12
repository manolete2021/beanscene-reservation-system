"""Waitlist screen: the queue in order, add at the front, end or a position, remove anyone.

Uses the waitlist module (1.3): read_forwards, read_backwards, add_to_end,
add_to_front, add_at and remove_at. Positions on screen count from 1 (the
front); the waitlist module counts from 0, so 1 is taken away.
"""

import tkinter as tk
from tkinter import ttk

from beanscene import waitlist
from beanscene import gui_look
from beanscene import operations
from beanscene.records import make_waiting_guest

screen = {}


def build(parent, state, bar):
    """Create the waitlist screen inside parent (one tab of the window)."""
    screen["state"] = state
    screen["bar"] = bar
    screen["order"] = tk.StringVar(value="forwards")

    list_box = ttk.LabelFrame(parent, text="Waiting guests", padding=gui_look.PAD)
    list_box.grid(row=0, column=0, sticky="nsew", padx=(0, gui_look.PAD))
    front_to_back = ttk.Radiobutton(list_box, text="Front to back", value="forwards",
                                    variable=screen["order"], command=refresh)
    front_to_back.grid(row=0, column=0, sticky="w", padx=gui_look.PAD, pady=4)
    back_to_front = ttk.Radiobutton(list_box, text="Back to front", value="backwards",
                                    variable=screen["order"], command=refresh)
    back_to_front.grid(row=0, column=1, sticky="w", padx=gui_look.PAD, pady=4)
    screen["tree"] = ttk.Treeview(list_box, columns=("position", "name", "party_size", "phone"),
                                  show="headings", height=12)
    screen["tree"].heading("position", text="Position")
    screen["tree"].heading("name", text="Name")
    screen["tree"].heading("party_size", text="Party size")
    screen["tree"].heading("phone", text="Phone")
    screen["tree"].grid(row=1, column=0, columnspan=2, sticky="nsew", padx=gui_look.PAD, pady=gui_look.PAD)

    guest_box = ttk.LabelFrame(parent, text="Guest details", padding=gui_look.PAD)
    guest_box.grid(row=0, column=1, sticky="nsew")
    screen["name"] = gui_look.labelled_entry(guest_box, 0, "Guest name", 24)
    screen["party_size"] = gui_look.labelled_entry(guest_box, 1, "Party size", 12)
    screen["phone"] = gui_look.labelled_entry(guest_box, 2, "Phone", 24)
    screen["position"] = gui_look.labelled_entry(guest_box, 3, "Position", 12)
    add_end = ttk.Button(guest_box, text="Add at the end", style="Accent.TButton", command=add_at_end)
    add_end.grid(row=4, column=0, columnspan=2, sticky="we", padx=gui_look.PAD, pady=(8, 4))
    add_front = ttk.Button(guest_box, text="Add a regular at the front", command=add_at_front)
    add_front.grid(row=5, column=0, columnspan=2, sticky="we", padx=gui_look.PAD, pady=4)
    add_position = ttk.Button(guest_box, text="Add at this position", command=add_at_position)
    add_position.grid(row=6, column=0, columnspan=2, sticky="we", padx=gui_look.PAD, pady=4)
    remove = ttk.Button(guest_box, text="Remove the selected guest", command=remove_selected)
    remove.grid(row=7, column=0, columnspan=2, sticky="we", padx=gui_look.PAD, pady=4)
    refresh()


def read_guest():
    """Read the guest's details from the text boxes and return a guest record."""
    name = screen["name"].get().strip()
    if name == "":
        raise ValueError("Enter the guest's name.")
    party_size = gui_look.read_whole_number(screen["party_size"], "Party size")
    if party_size < 1:
        raise ValueError("Party size must be at least 1.")
    phone = screen["phone"].get().strip()
    return make_waiting_guest(name, party_size, phone)


def clear_guest():
    """Empty the guest text boxes after a guest is added."""
    screen["name"].delete(0, "end")
    screen["party_size"].delete(0, "end")
    screen["phone"].delete(0, "end")


def add_at_end():
    """A walk-in joins the back of the queue."""
    try:
        guest = read_guest()
        message = operations.waitlist_add(screen["state"], guest, screen["state"]["waitlist"]["size"])
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    clear_guest()
    refresh()
    gui_look.show_success(screen["bar"], message)


def add_at_front():
    """A regular goes straight to the front."""
    try:
        guest = read_guest()
        message = operations.waitlist_add(screen["state"], guest, 0)
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    clear_guest()
    refresh()
    gui_look.show_success(screen["bar"], message)


def add_at_position():
    """Put a guest at the position typed in (1 = front)."""
    try:
        guest = read_guest()
        position = gui_look.read_whole_number(screen["position"], "Position")
        message = operations.waitlist_add(screen["state"], guest, position - 1)
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    clear_guest()
    refresh()
    gui_look.show_success(screen["bar"], message)


def remove_selected():
    """Remove the guest selected in the list, from anywhere in the queue."""
    try:
        selected = screen["tree"].selection()
        if len(selected) == 0:
            raise ValueError("Click a guest in the list first.")
        position = int(screen["tree"].item(selected[0])["values"][0])
        message = operations.waitlist_remove(screen["state"], position - 1)
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    refresh()
    gui_look.show_success(screen["bar"], message)


def refresh():
    """Fill the list by following the links: next links from the front, or prev links from the back."""
    gui_look.clear_tree(screen["tree"])
    queue = screen["state"]["waitlist"]
    if screen["order"].get() == "forwards":
        guests = waitlist.read_forwards(queue)
        position = 1
        step = 1
    else:
        guests = waitlist.read_backwards(queue)
        position = queue["size"]
        step = -1
    for guest in guests:
        screen["tree"].insert("", "end", values=(position, guest["name"], guest["party_size"], guest["phone"]))
        position = position + step

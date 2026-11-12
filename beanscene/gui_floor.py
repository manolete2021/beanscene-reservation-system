"""Floor plan screen: the thirty tables, each marked free or occupied.

Seat calls operations.seat(). Free calls operations.complete().
The screen then draws the tables from the floor data.
"""

import tkinter as tk
from tkinter import ttk

from beanscene import floor_plan
from beanscene import gui_look
from beanscene import ipc
from beanscene import operations

# This screen's data and widgets, kept in one dictionary so that the
# button functions (which Tkinter calls with no arguments) can reach them.
screen = {}


def build(parent, state, bar):
    """Create the floor plan screen inside parent (one tab of the window)."""
    screen["state"] = state
    screen["bar"] = bar
    screen["tiles"] = {}
    screen["selected"] = None

    floor_box = ttk.LabelFrame(parent, text="Dining floor", padding=gui_look.PAD)
    floor_box.grid(row=0, column=0, sticky="nsew", padx=(0, gui_look.PAD))
    per_line = state["settings"]["gui"]["tables_per_line"]     # from config.json, not hard-coded
    count = 0
    for row in state["floor"]:
        for table in row:
            tile = tk.Label(floor_box, width=9, height=2, font=gui_look.FONT, relief="flat", cursor="hand2")
            tile.grid(row=count // per_line, column=count % per_line, padx=3, pady=3)
            tile.bind("<Button-1>", on_tile_click)            # a click on a tile calls on_tile_click
            screen["tiles"][table["code"]] = tile
            count = count + 1

    side = ttk.LabelFrame(parent, text="Selected table", padding=gui_look.PAD)
    side.grid(row=0, column=1, sticky="nsew")
    screen["title"] = ttk.Label(side, text="Click a table", style="Heading.TLabel")
    screen["title"].grid(row=0, column=0, columnspan=2, sticky="w", padx=gui_look.PAD)
    screen["occupant"] = ttk.Label(side, text="", style="Muted.TLabel")
    screen["occupant"].grid(row=1, column=0, columnspan=2, sticky="w", padx=gui_look.PAD, pady=(0, 8))
    screen["reference"] = gui_look.labelled_entry(side, 2, "Booking reference", 14)
    seat = ttk.Button(side, text="Seat booking at this table", style="Accent.TButton", command=seat_booking)
    seat.grid(row=3, column=0, columnspan=2, sticky="we", padx=gui_look.PAD, pady=(8, 4))
    free = ttk.Button(side, text="Free this table", command=free_table)
    free.grid(row=4, column=0, columnspan=2, sticky="we", padx=gui_look.PAD, pady=4)
    screen["occupancy"] = ttk.Label(side, text="", font=gui_look.FONT_BOLD)
    screen["occupancy"].grid(row=5, column=0, columnspan=2, sticky="w", padx=gui_look.PAD, pady=(16, 0))
    refresh()


def on_tile_click(event):
    """A table was clicked: its code is the first line of the tile, e.g. "A4\nfree" -> "A4"."""
    code = event.widget.cget("text").split("\n")[0]
    screen["selected"] = code
    refresh()
    gui_look.show_success(screen["bar"], f"Table {code} selected.")


def selected_code():
    """The code of the table that was clicked, or a message if none was."""
    if screen["selected"] is None:
        raise ValueError("Click a table first.")
    return screen["selected"]


def seat_booking():
    """Seat button: put the booking reference on the selected table."""
    try:
        code = selected_code()
        reference = screen["reference"].get().strip().upper()
        if reference == "":
            raise ValueError("Enter a booking reference.")
        # Keep the booking, table, journal and undo in sync.
        operations.seat(screen["state"], reference, code)
    except ValueError as error:                 # refused: say why, change nothing
        gui_look.show_error(screen["bar"], str(error))
        return
    screen["reference"].delete(0, "end")
    refresh()
    # The seat has already succeeded. Only the Tablet tells the Desk.
    show_tablet_result(f"{reference} seated at {code}.", f"SEAT {reference} {code}")


def free_table():
    """Free button: take the booking off the selected table."""
    try:
        code = selected_code()
        reference = floor_plan.read_occupant(screen["state"]["floor"], code)
        if reference is None:
            raise ValueError(f"Table {code} is already free.")
        operations.complete(screen["state"], reference)
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    refresh()
    # The complete has already succeeded. Only the Tablet tells the Desk.
    show_tablet_result(f"Table {code} is now free.", f"COMPLETE {reference}")


def show_tablet_result(local_message, update_line):
    """Show the local result. The Tablet also sends that result to the Desk.

    Only the Floor Tablet sends. The Desk does not. This runs only after
    the seat or complete has succeeded. If the Desk is not listening, the
    booking change stays. A sent line means the text was handed over, not
    that the Desk has redrawn its window.
    """
    if screen["state"]["role"] != "tablet":
        gui_look.show_success(screen["bar"], local_message)
        return
    delivered, note = ipc.send_update(update_line)
    if delivered:
        gui_look.show_success(screen["bar"], local_message + " " + note)
        return
    gui_look.show_error(
        screen["bar"],
        local_message + " The Desk did not receive the update. " + note,
    )


def refresh():
    """Redraw every tile and the side panel from the floor data."""
    floor = screen["state"]["floor"]
    for row in floor:
        for table in row:
            tile = screen["tiles"][table["code"]]
            if table["booking_reference"] is None:
                tile.configure(text=table["code"] + "\nfree", background=gui_look.COLOURS["free"],
                               foreground=gui_look.COLOURS["free_text"])
            else:
                tile.configure(text=table["code"] + "\n" + table["booking_reference"],
                               background=gui_look.COLOURS["occupied"], foreground=gui_look.COLOURS["occupied_text"])
            if table["code"] == screen["selected"]:
                tile.configure(relief="solid", borderwidth=2, font=gui_look.FONT_BOLD)
            else:
                tile.configure(relief="flat", borderwidth=0, font=gui_look.FONT)
    if screen["selected"] is not None:
        occupant = floor_plan.read_occupant(floor, screen["selected"])
        screen["title"].configure(text="Table " + screen["selected"])
        if occupant is None:
            screen["occupant"].configure(text="Free")
        else:
            screen["occupant"].configure(text="Seated: " + occupant)
    occupied, total = floor_plan.occupancy(floor)
    screen["occupancy"].configure(text=f"Occupied {occupied} of {total} tables")

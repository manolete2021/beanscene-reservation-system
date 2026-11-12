"""Bookings screen: for now, only the member part (1.2).

When a member books, their details are filled in automatically: the member
number is found with the binary search (binary_search_by_number), and the
directory is listed in surname order (directory["by_surname"], sorted by
the custom sort). New bookings, find by reference and status changes are
added to this screen in 1.5; the journal and Undo in 1.6.
"""

import tkinter as tk
from tkinter import ttk

from beanscene import member_directory
from beanscene import gui_floor
from beanscene import gui_look
from beanscene import ipc
from beanscene import journal
from beanscene import operations

screen = {}


def build(parent, state, bar):
    """Create the bookings screen inside parent (one tab of the window)."""
    screen["state"] = state
    screen["bar"] = bar

    canvas = tk.Canvas(parent, highlightthickness=0, background=gui_look.COLOURS["background"])
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    content = ttk.Frame(canvas)
    content_window = canvas.create_window((0, 0), window=content, anchor="nw")

    def update_scroll_region(event=None):
        """Keep the scroll area the same size as the sections inside it."""
        canvas.configure(scrollregion=canvas.bbox("all"))

    def fit_content_width(event):
        """Make the sections as wide as the visible part of the tab."""
        canvas.itemconfigure(content_window, width=event.width)

    def scroll_bookings(event):
        """Scroll this tab when the pointer is over it. Other tabs are left alone."""
        widget = event.widget
        while widget is not None:
            if widget == canvas:
                if event.delta > 0:
                    canvas.yview_scroll(-1, "units")
                elif event.delta < 0:
                    canvas.yview_scroll(1, "units")
                return
            widget = getattr(widget, "master", None)

    content.bind("<Configure>", update_scroll_region)
    canvas.bind("<Configure>", fit_content_width)
    canvas.bind_all("<MouseWheel>", scroll_bookings)

    member_box = ttk.LabelFrame(content, text="Member details (filled in from the member number)", padding=gui_look.PAD)
    member_box.grid(row=0, column=0, sticky="nsew", padx=(0, gui_look.PAD))
    screen["number"] = gui_look.labelled_entry(member_box, 0, "Member number", 12)
    find = ttk.Button(member_box, text="Find member", style="Accent.TButton", command=find_member)
    find.grid(row=1, column=1, sticky="we", padx=gui_look.PAD, pady=4)
    screen["name"] = gui_look.labelled_entry(member_box, 2, "Guest name", 24)
    screen["phone"] = gui_look.labelled_entry(member_box, 3, "Phone", 24)
    screen["steps"] = ttk.Label(member_box, text="", style="Muted.TLabel")
    screen["steps"].grid(row=4, column=0, columnspan=2, sticky="w", padx=gui_look.PAD, pady=(0, 8))

    list_box = ttk.LabelFrame(content, text="Member directory, sorted by surname", padding=gui_look.PAD)
    list_box.grid(row=0, column=1, sticky="nsew")
    screen["tree"] = ttk.Treeview(list_box, columns=("surname", "first_name", "number", "phone"),
                                  show="headings", height=14)
    screen["tree"].heading("surname", text="Surname")
    screen["tree"].heading("first_name", text="First name")
    screen["tree"].heading("number", text="Member no.")
    screen["tree"].heading("phone", text="Phone")
    screen["tree"].grid(row=0, column=0, sticky="nsew", padx=gui_look.PAD, pady=gui_look.PAD)

    booking_box = ttk.LabelFrame(content, text="New Booking", padding=gui_look.PAD)
    booking_box.grid(row=1, column=0, sticky="nsew", padx=(0, gui_look.PAD), pady=(gui_look.PAD, 0))
    screen["booking_name"] = gui_look.labelled_entry(booking_box, 0, "Guest name", 24)
    screen["party_size"] = gui_look.labelled_entry(booking_box, 1, "Party size", 12)
    screen["source"] = gui_look.labelled_entry(booking_box, 2, "Source", 24)
    screen["notes"] = gui_look.labelled_entry(booking_box, 3, "Notes", 24)
    create = ttk.Button(booking_box, text="Create Booking", style="Accent.TButton", command=create_booking)
    create.grid(row=4, column=1, sticky="we", padx=gui_look.PAD, pady=(8, 4))

    find_box = ttk.LabelFrame(content, text="Find Booking", padding=gui_look.PAD)
    find_box.grid(row=1, column=1, sticky="nsew", pady=(gui_look.PAD, 0))
    screen["booking_reference"] = gui_look.labelled_entry(find_box, 0, "Booking reference", 14)
    find_button = ttk.Button(find_box, text="Find Booking", style="Accent.TButton", command=find_booking)
    find_button.grid(row=1, column=1, sticky="we", padx=gui_look.PAD, pady=(8, 4))
    screen["found"] = ttk.Label(find_box, text="", justify="left")
    screen["found"].grid(row=2, column=0, columnspan=2, sticky="w", padx=gui_look.PAD, pady=(8, 0))

    status_box = ttk.LabelFrame(content, text="Change Booking Status", padding=gui_look.PAD)
    status_box.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(gui_look.PAD, 0))
    screen["table_code"] = gui_look.labelled_entry(status_box, 0, "Table code", 12)
    seat = ttk.Button(status_box, text="Seat Booking", style="Accent.TButton", command=seat_booking)
    seat.grid(row=1, column=1, sticky="we", padx=gui_look.PAD, pady=(8, 4))
    complete = ttk.Button(status_box, text="Complete Booking", command=complete_booking)
    complete.grid(row=2, column=1, sticky="we", padx=gui_look.PAD, pady=4)
    cancel = ttk.Button(status_box, text="Cancel Booking", command=cancel_booking)
    cancel.grid(row=3, column=1, sticky="we", padx=gui_look.PAD, pady=4)

    journal_box = ttk.LabelFrame(content, text="Journal — Recent Changes", padding=gui_look.PAD)
    journal_box.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(gui_look.PAD, 0))
    screen["journal_tree"] = ttk.Treeview(
        journal_box,
        columns=("entry_number", "timestamp", "staff_code", "action", "booking_reference", "cancelled"),
        show="headings",
        height=10,
    )
    screen["journal_tree"].heading("entry_number", text="Entry number")
    screen["journal_tree"].heading("timestamp", text="Timestamp")
    screen["journal_tree"].heading("staff_code", text="Staff code")
    screen["journal_tree"].heading("action", text="Action")
    screen["journal_tree"].heading("booking_reference", text="Booking reference")
    screen["journal_tree"].heading("cancelled", text="Cancelled")
    screen["journal_tree"].grid(row=0, column=0, sticky="nsew", padx=gui_look.PAD, pady=gui_look.PAD)
    undo = ttk.Button(journal_box, text="Undo Last Change", style="Accent.TButton", command=undo_last_change)
    undo.grid(row=1, column=0, sticky="w", padx=gui_look.PAD, pady=(0, gui_look.PAD))
    refresh()
    refresh_journal()
    content.update_idletasks()
    update_scroll_region()


def find_member():
    """Find member button: binary search by number, then fill in the guest's details."""
    directory = screen["state"]["directory"]
    try:
        number = gui_look.read_whole_number(
            screen["number"], "Member number"
        )
        member, steps = member_directory.binary_search_by_number(
            directory, number
        )
        total = len(directory["by_number"])
        if member is None:
            raise ValueError(
                f"There is no member {number} "
                f"(checked {steps} of {total} members)."
            )
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    name = member["first_name"] + " " + member["surname"]
    screen["name"].delete(0, "end")
    screen["phone"].delete(0, "end")
    screen["name"].insert(0, name)
    screen["phone"].insert(0, member["phone"])
    screen["steps"].configure(text=f"Found in {steps} step(s) out of {total} members.")
    row_id = str(member["number"])
    screen["tree"].selection_set(row_id)
    screen["tree"].see(row_id)
    gui_look.show_success(screen["bar"], f"Member {number}: {name}.")


def create_booking():
    """Create Booking button: take a new pending booking."""
    try:
        guest_name = screen["booking_name"].get().strip()
        if guest_name == "":
            guest_name = screen["name"].get().strip()
        party_size = gui_look.read_whole_number(screen["party_size"], "Party size")
        source = screen["source"].get().strip().lower()
        notes = screen["notes"].get().strip()
        if screen["number"].get().strip() == "":
            member_number = None
        else:
            member_number = gui_look.read_whole_number(screen["number"], "Member number")
        message = operations.new_booking(
            screen["state"], guest_name, party_size, source, notes, member_number
        )
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    if refresh_journal():
        gui_look.show_success(screen["bar"], message)


def find_booking():
    """Find Booking button: look up a booking by its reference."""
    try:
        reference = screen["booking_reference"].get().strip().upper()
        if reference == "":
            raise ValueError("Enter a booking reference.")
        booking = operations.find_booking(screen["state"], reference)
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    table = booking["table_code"]
    if table is None:
        table = ""
    screen["found"].configure(
        text=f"Reference: {booking['reference']}\n"
             f"Guest name: {booking['guest_name']}\n"
             f"Party size: {booking['party_size']}\n"
             f"Source: {booking['source']}\n"
             f"Status: {booking['status']}\n"
             f"Table code: {table}"
    )
    gui_look.show_success(screen["bar"], f"Booking {booking['reference']} found.")


def read_reference():
    """The booking reference from Find Booking, with spaces removed and capitals."""
    reference = screen["booking_reference"].get().strip().upper()
    if reference == "":
        raise ValueError("Enter a booking reference.")
    return reference


def show_found_booking(booking):
    """Show the booking's current details in the Find Booking section."""
    table = booking["table_code"]
    if table is None:
        table = ""
    screen["found"].configure(
        text=f"Reference: {booking['reference']}\n"
             f"Guest name: {booking['guest_name']}\n"
             f"Party size: {booking['party_size']}\n"
             f"Source: {booking['source']}\n"
             f"Status: {booking['status']}\n"
             f"Table code: {table}"
    )


def finish_status_change(reference, message, update_line=None):
    """Redraw the floor and the found booking after a status change is accepted.

    update_line is set only for a seat or complete that has already
    succeeded. Only the Floor Tablet sends it. The Desk does not. Cancel
    passes no line. If the send fails, the local booking change stays.
    A sent line means the text was handed over, not that the Desk has
    redrawn its window.
    """
    gui_floor.refresh()
    show_found_booking(operations.find_booking(screen["state"], reference))
    journal_ok = refresh_journal()
    if update_line is not None and screen["state"]["role"] == "tablet":
        delivered, note = ipc.send_update(update_line)
        if not delivered:
            gui_look.show_error(
                screen["bar"],
                message + " The Desk did not receive the update. " + note,
            )
            return
        message = message + " " + note
    if journal_ok:
        gui_look.show_success(screen["bar"], message)


def seat_booking():
    """Seat Booking button: seat the booking at the typed table."""
    try:
        reference = read_reference()
        table_code = screen["table_code"].get().strip().upper()
        if table_code == "":
            raise ValueError("Enter a table code.")
        message = operations.seat(screen["state"], reference, table_code)
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    finish_status_change(reference, message, f"SEAT {reference} {table_code}")


def complete_booking():
    """Complete Booking button: complete the booking and free its table."""
    try:
        reference = read_reference()
        message = operations.complete(screen["state"], reference)
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    finish_status_change(reference, message, f"COMPLETE {reference}")


def cancel_booking():
    """Cancel Booking button: cancel the booking and free its table if it had one."""
    try:
        reference = read_reference()
        message = operations.cancel(screen["state"], reference)
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    finish_status_change(reference, message)


def undo_last_change():
    """Undo Last Change button: reverse the most recent change."""
    try:
        message = operations.undo_last(screen["state"])
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return
    gui_floor.refresh()
    reference = screen["booking_reference"].get().strip().upper()
    if reference != "":
        try:
            show_found_booking(operations.find_booking(screen["state"], reference))
        except ValueError:
            pass
    if refresh_journal():
        gui_look.show_success(screen["bar"], message)


def refresh_journal():
    """Fill the journal list with the newest records first."""
    try:
        entries = journal.read_recent(
            screen["state"]["journal"],
            screen["state"]["settings"]["journal"]["recent_entries"],
        )
    except ValueError as error:
        gui_look.show_error(screen["bar"], str(error))
        return False
    gui_look.clear_tree(screen["journal_tree"])
    for entry in entries:
        screen["journal_tree"].insert(
            "",
            "end",
            iid=str(entry["entry_number"]),
            values=(
                entry["entry_number"],
                entry["timestamp"],
                entry["staff_code"],
                entry["action"],
                entry["booking_reference"],
                entry["cancelled"],
            ),
        )
    return True


def refresh():
    """Fill the list from the directory, in surname order (already sorted by the custom sort)."""
    gui_look.clear_tree(screen["tree"])

    for member in screen["state"]["directory"]["by_surname"]:
        screen["tree"].insert(
            "",
            "end",
            iid=str(member["number"]),
            values=(
                member["surname"],
                member["first_name"],
                member["number"],
                member["phone"]
            )
        )

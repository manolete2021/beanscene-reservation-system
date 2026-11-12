"""Bean Scene - the windowed application.

The data is loaded exactly as in main.py (load_config and build_state),
then each screen module builds its own tab. The screens only show the data
and pass what the user does to the Task 1 modules; all the rules stay in
those modules.

Two copies can run at once. The Floor Tablet sends seat and complete
updates. The Reservation Desk listens and redraws. The Desk does not
send anything back.
"""

import queue
import signal
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from main import load_config, build_state
from beanscene import booking_index, bookings, ipc, journal
from beanscene import gui_look, gui_floor, gui_bookings, gui_waitlist, gui_menu


def read_role():
    """Return desk or tablet from the command that started the program."""
    if len(sys.argv) == 2 and sys.argv[1] in ("desk", "tablet"):
        return sys.argv[1]
    raise ValueError('Start Bean Scene as "python app.py desk" or "python app.py tablet".')


def apply_received_update(state, update):
    """Apply one tablet update to this Desk's own memory.

    bookings.seat_booking and bookings.complete_booking change the
    booking and the floor only. They do not write a journal record and
    they do not push an undo item. The Tablet already did that, so the
    Desk must not do it again.
    """
    action = update["action"]
    reference = update["reference"]
    booking = booking_index.index_find(state["index"], reference)
    if booking is None:
        raise ValueError(f"No booking found with reference '{reference}'.")
    if action == "SEAT":
        bookings.seat_booking(booking, state["floor"], update["table"])
        return booking, f"{booking['reference']} seated at {booking['table_code']}."
    if action == "COMPLETE":
        previous_table = booking["table_code"]
        bookings.complete_booking(booking, state["floor"])
        return booking, f"{booking['reference']} completed; table {previous_table} is free."
    raise ValueError("The update action is not SEAT or COMPLETE.")


def show_received_update(state, bar, update):
    """Redraw the Desk after a tablet update. A refused update stays red."""
    try:
        booking, message = apply_received_update(state, update)
    except (KeyError, ValueError) as error:
        gui_look.show_error(bar, str(error))
        return
    # The floor tiles read the Desk's own floor data.
    gui_floor.refresh()
    # Update the Find Booking lines only when this booking is the one on screen.
    selected = gui_bookings.screen["booking_reference"].get().strip().upper()
    if selected == booking["reference"]:
        gui_bookings.show_found_booking(booking)
    # Re-read the journal file. This does not append a new record.
    if gui_bookings.refresh_journal():
        gui_look.show_success(bar, message)


def main():
    """Open the window. Chapter 1 adds the Floor plan tab; each later chapter adds one more."""
    window = tk.Tk()
    gui_look.apply_style(window)

    try:
        role = read_role()
    except ValueError as error:
        messagebox.showerror("Bean Scene could not start", str(error))
        window.destroy()
        return

    # The title shows which copy this window is. The tabs stay the same.
    if role == "desk":
        window.title("Bean Scene - Reservation Desk")
    else:
        window.title("Bean Scene - Floor Tablet")

    try:
        settings = load_config()
        state = build_state(settings)
    except (ValueError, SystemExit) as error:
        messagebox.showerror("Bean Scene could not start", str(error))
        window.destroy()
        return

    # The screens read this role to decide whether a seat or complete
    # update may be sent. Only the Floor Tablet sends.
    state["role"] = role

    header = ttk.Label(window, text="Bean Scene  ·  Reservation desk", style="Heading.TLabel")
    header.pack(side="top", anchor="w", padx=14, pady=(10, 4))

    bar = gui_look.make_message_bar(window)

    tabs = ttk.Notebook(window)
    tabs.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 10))

    floor_tab = ttk.Frame(tabs, padding=gui_look.PAD)
    tabs.add(floor_tab, text="Floor plan")
    gui_floor.build(floor_tab, state, bar)

    bookings_tab = ttk.Frame(tabs, padding=gui_look.PAD)
    tabs.add(bookings_tab, text="Bookings")
    gui_bookings.build(bookings_tab, state, bar)

    waitlist_tab = ttk.Frame(tabs, padding=gui_look.PAD)
    tabs.add(waitlist_tab, text="Waitlist")
    gui_waitlist.build(waitlist_tab, state, bar)

    menu_tab = ttk.Frame(tabs, padding=gui_look.PAD)
    tabs.add(menu_tab, text="Menu")
    gui_menu.build(menu_tab, state, bar)

    # Cleanup runs only once. The close button and mainloop's finally
    # can both reach shutdown, and the second call must do nothing.
    shutdown_started = False
    # A signal only raises this flag. It must not close the window or the file.
    shutdown_requested = False

    def shutdown():
        """Flush the journal, stop the listener, and close the window."""
        nonlocal shutdown_started
        if shutdown_started:
            return
        # Set this first so the Desk does not schedule another queue check.
        shutdown_started = True
        try:
            # Each journal write is already flushed. Flush once more so the
            # last record is on disk, then close this copy's file handle.
            # Closing does not delete the records.
            log = state["journal"]
            handle = log["file"]
            if not handle.closed:
                try:
                    handle.flush()
                finally:
                    journal.close_journal(log)
        finally:
            try:
                # Close the Desk's listening socket and stop its thread.
                # The Tablet never listened. This call is still safe there.
                ipc.stop_listener()
            finally:
                try:
                    if window.winfo_exists():
                        window.destroy()
                except tk.TclError:
                    pass

    def request_shutdown(signum, frame):
        """Remember that Ctrl+C or SIGTERM asked this copy to stop."""
        nonlocal shutdown_requested
        shutdown_requested = True

    def watch_shutdown():
        """On the window thread, shut down if a signal asked for it.

        after() waits. It does not spin. Both the Desk and the Tablet use it.
        """
        if shutdown_started:
            return
        if shutdown_requested:
            shutdown()
            return
        window.after(200, watch_shutdown)

    # The window close button uses the same cleanup as a signal.
    # The handler only sets a flag. This window thread runs shutdown().
    window.protocol("WM_DELETE_WINDOW", shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    # The Desk listens for seat and complete lines from the Floor Tablet.
    # The Tablet copy does not listen, and the Desk does not reply.
    if role == "desk":
        # The listener runs in the background and only puts updates on
        # this queue. The window is updated here, on the main thread,
        # because Tkinter is not safe to change from the listener thread.
        updates = queue.Queue()
        try:
            ipc.start_listener(updates)
        except OSError as error:
            gui_look.show_error(bar, "The Desk could not listen for tablet updates. " + str(error))
        else:
            def take_updates():
                """Check the queue without waiting, then look again shortly."""
                # Shutdown has started, so do not poll or schedule another check.
                if shutdown_started:
                    return
                try:
                    while True:
                        update = updates.get_nowait()
                        show_received_update(state, bar, update)
                except queue.Empty:
                    pass
                if shutdown_started:
                    return
                # after() returns to the window immediately. It does not
                # block the Desk while it waits for the next tablet line.
                window.after(200, take_updates)

            window.after(200, take_updates)

    window.after(200, watch_shutdown)
    try:
        window.mainloop()
    finally:
        shutdown()


if __name__ == "__main__":
    main()

"""Operations: every change the staff can make, in one place.

Each function makes the change, writes a journal entry and pushes an undo
item, so the three always stay together. Each one returns a message to
show the user, or raises ValueError if the change is refused.
"""

from beanscene import booking_index, bookings, floor_plan, journal, member_directory, undo_stack, waitlist
from beanscene.records import make_member, make_undo_item


def record_change(state, item):
    """Write the journal entry for a change and push its undo item."""
    entry = journal.append_entry(state["journal"], state["staff_code"], item["action"], item["booking_reference"])
    item["entry_number"] = entry["entry_number"]
    undo_stack.push(state["undo"], item)


def find_booking(state, reference):
    """Return the booking with this reference, or refuse with a message."""
    booking = booking_index.index_find(state["index"], reference)
    if booking is None:
        raise ValueError(f"No booking found with reference '{reference.strip()}'.")
    return booking


def new_booking(state, guest_name, party_size, source, notes="", member_number=None):
    """Take a new booking. A member's name is filled in from the directory."""
    if member_number is not None:
        member = member_directory.find_member(state["directory"], member_number)
        if member is None:
            raise ValueError(f"There is no member number {member_number}.")
        guest_name = member["first_name"] + " " + member["surname"]
    rules = state["settings"]["bookings"]
    reference = bookings.next_reference(booking_index.all_bookings(state["index"]), rules)
    booking = bookings.create_booking(reference, guest_name, party_size, source, rules, notes, member_number)
    booking_index.index_add(state["index"], booking)
    record_change(state, make_undo_item("NEW BOOKING", reference))
    return f"Booking {reference} added for {booking['guest_name']} (party of {party_size})."


def register_member(state, first_name, surname, phone=""):
    """Register a new member with the next free number."""
    number = member_directory.next_member_number(state["directory"])
    member = make_member(number, first_name.strip(), surname.strip(), phone.strip())
    member_directory.add_member(state["directory"], member)
    record_change(state, make_undo_item("NEW MEMBER", "M" + str(number)))
    return member


def seat(state, reference, table_code):
    """Seat a booking at a table."""
    booking = find_booking(state, reference)
    item = make_undo_item("SEAT BOOKING", booking["reference"])
    item["previous_status"] = booking["status"]
    bookings.seat_booking(booking, state["floor"], table_code)
    record_change(state, item)
    return f"{booking['reference']} seated at {booking['table_code']}."


def complete(state, reference):
    """Complete a booking and free its table."""
    booking = find_booking(state, reference)
    item = make_undo_item("COMPLETE BOOKING", booking["reference"])
    item["previous_status"] = booking["status"]
    item["previous_table"] = booking["table_code"]
    bookings.complete_booking(booking, state["floor"])
    record_change(state, item)
    return f"{booking['reference']} completed; table {item['previous_table']} is free."


def cancel(state, reference):
    """Cancel a booking, freeing its table if it was seated."""
    booking = find_booking(state, reference)
    item = make_undo_item("CANCEL BOOKING", booking["reference"])
    item["previous_status"] = booking["status"]
    item["previous_table"] = booking["table_code"]
    bookings.cancel_booking(booking, state["floor"])
    record_change(state, item)
    return f"{booking['reference']} cancelled."


def waitlist_add(state, guest, position):
    """Add a walk-in to the waitlist at a position (0 is the front)."""
    waitlist.add_at(state["waitlist"], position, guest)
    item = make_undo_item("WAITLIST ADD", "")
    item["waitlist_position"] = position
    record_change(state, item)
    return f"{guest['name']} added to the waitlist at position {position + 1}."


def waitlist_remove(state, position):
    """Remove the guest at a position (0 is the front)."""
    guest = waitlist.remove_at(state["waitlist"], position)
    item = make_undo_item("WAITLIST REMOVE", "")
    item["waitlist_position"] = position
    item["guest"] = guest
    record_change(state, item)
    return f"{guest['name']} removed from the waitlist."


def undo_last(state):
    """Reverse the most recent change and set its cancelled flag in the journal.

    If the change can no longer be reversed (for example, the table has been
    given to someone else) the item goes back on the stack and nothing changes.
    """
    item = undo_stack.pop(state["undo"])
    try:
        reverse_change(state, item)
    except ValueError:
        undo_stack.push(state["undo"], item)
        raise
    journal.set_cancelled(state["journal"], item["entry_number"])
    return f"Undid {item['action'].lower()} (journal entry {item['entry_number']})."


def reverse_change(state, item):
    """Put the data back the way it was before the change."""
    action = item["action"]
    if action == "NEW BOOKING":
        # The hash table has no delete, so an undone booking is cancelled instead
        booking = find_booking(state, item["booking_reference"])
        booking["status"] = "cancelled"
    elif action == "SEAT BOOKING":
        booking = find_booking(state, item["booking_reference"])
        floor_plan.release_table(state["floor"], booking["table_code"])
        booking["status"] = item["previous_status"]
        booking["table_code"] = None
    elif action == "COMPLETE BOOKING" or action == "CANCEL BOOKING":
        booking = find_booking(state, item["booking_reference"])
        table_code = item["previous_table"]
        if table_code is not None:
            if floor_plan.read_occupant(state["floor"], table_code) is not None:
                raise ValueError(f"Can't undo: table {table_code} has been given to another booking.")
            floor_plan.assign_booking(state["floor"], table_code, booking["reference"])
        booking["status"] = item["previous_status"]
        booking["table_code"] = table_code
    elif action == "WAITLIST ADD":
        waitlist.remove_at(state["waitlist"], item["waitlist_position"])
    elif action == "WAITLIST REMOVE":
        waitlist.add_at(state["waitlist"], item["waitlist_position"], item["guest"])
    elif action == "NEW MEMBER":
        number = int(item["booking_reference"][1:])
        member_directory.remove_member(state["directory"], number)

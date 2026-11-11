"""Record types used by Bean Scene - built with functions, no classes.

Each record is a dictionary with a fixed set of fields. One "make_" function
creates every record of that type, so they always have the same fields.
"""


def make_table(code, row, column):
    """Return a new table record, e.g. make_table("A4", "A", 4).

    code (text) "A4", row (text) "A", column (whole number) 4,
    booking_reference (text, or None while the table is free)
    """
    return {"code": code, "row": row, "column": column, "booking_reference": None}


def make_member(number, first_name, surname, phone=""):
    """Return a new member record, e.g. make_member(1007, "Siobhan", "O'Brien")."""
    return {"number": number, "first_name": first_name, "surname": surname, "phone": phone}


def make_waiting_guest(name, party_size, phone=""):
    """Return a new waitlist guest record, e.g. make_waiting_guest("Ravi Patel", 2)."""
    return {"name": name, "party_size": party_size, "phone": phone}


def make_dish(name, category, price, description=""):
    """Return a new dish record, e.g. make_dish("Pavlova", "Dessert", 14.00)."""
    return {"name": name, "category": category, "price": price, "description": description}


def make_booking(reference, guest_name, party_size, source, notes="", member_number=None):
    """Return a new booking record. A new booking is pending and has no table yet."""
    return {"reference": reference, "guest_name": guest_name, "party_size": party_size,
            "source": source, "notes": notes, "member_number": member_number,
            "status": "pending", "table_code": None}


def make_journal_entry(entry_number, timestamp, staff_code, action, booking_reference, cancelled):
    """Return a journal entry record - one 60-byte record in the journal file."""
    return {"entry_number": entry_number, "timestamp": timestamp, "staff_code": staff_code,
            "action": action, "booking_reference": booking_reference, "cancelled": cancelled}


def make_undo_item(action, booking_reference):
    """Return an undo item: what the undo stack needs to reverse one change.

    The other fields are filled in by the change that creates it.
    """
    return {"action": action, "booking_reference": booking_reference, "entry_number": None,
            "previous_status": None, "previous_table": None, "waitlist_position": None, "guest": None}

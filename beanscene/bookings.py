"""Booking rules: create bookings and change their status.

A booking is pending until the guests arrive, seated once they have a
table, and completed when they leave. It can be cancelled at any time
before it is completed. Completing or cancelling frees the table. Any other
change is refused with a message.
"""

from beanscene import floor_plan
from beanscene.records import make_booking

# The only changes that make sense. Anything else is refused.
ALLOWED_CHANGES = {
    "pending": ["seated", "cancelled"],
    "seated": ["completed", "cancelled"],
    "completed": [],
    "cancelled": [],
}

def check_change(booking, new_status):
    """Refuse (ValueError) if the booking may not change to new_status."""
    if new_status not in ALLOWED_CHANGES[booking["status"]]:
        raise ValueError(f"Booking {booking['reference']} is {booking['status']} "
                         f"and cannot be changed to {new_status}.")

def create_booking(reference, guest_name, party_size, source, rules, notes="", member_number=None):
    """Check the details and return a new pending booking.

    rules is the "bookings" section of config.json.
    """
    if guest_name.strip() == "":
        raise ValueError("Enter the guest's name.")
    if party_size < 1 or party_size > rules["max_party_size"]:
        raise ValueError(f"Party size must be between 1 and {rules['max_party_size']}.")
    if source not in rules["sources"]:
        raise ValueError(f"How the request came in must be one of: {', '.join(rules['sources'])}.")
    return make_booking(reference, guest_name.strip(), party_size, source, notes.strip(), member_number)

def next_reference(existing, rules):
    """Return the next free reference: one more than the highest in use."""
    prefix = rules["reference_prefix"]                 # "BS-"
    highest = rules["first_reference_number"]
    for booking in existing:
        number = int(booking["reference"][len(prefix):])   # "BS-10432" -> 10432
        if number > highest:
            highest = number
    return prefix + str(highest + 1)

def seat_booking(booking, floor, table_code):
    """Seat a pending booking at a free table. The booking is changed in place."""
    check_change(booking, "seated")
    table = floor_plan.assign_booking(floor, table_code, booking["reference"])
    booking["status"] = "seated"
    booking["table_code"] = table["code"]

def complete_booking(booking, floor):
    """The guests have left: complete the booking and free its table."""
    check_change(booking, "completed")
    floor_plan.release_table(floor, booking["table_code"])
    booking["status"] = "completed"
    booking["table_code"] = None

def cancel_booking(booking, floor):
    """Cancel a pending or seated booking, freeing the table if it had one."""
    check_change(booking, "cancelled")
    if booking["table_code"] is not None:
        floor_plan.release_table(floor, booking["table_code"])
    booking["status"] = "cancelled"
    booking["table_code"] = None

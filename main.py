"""Bean Scene - main program.

Task 1 builds the data structures one module at a time. Each module is
imported here and used from a text menu. In Task 2 the text menus are
replaced by the windowed interface.
"""

import json
from pathlib import Path

from beanscene import floor_plan
from beanscene import member_directory, seed_loader
from beanscene import waitlist
from beanscene import menu_tree
from beanscene import booking_index
from beanscene import journal, operations, undo_stack
from beanscene.records import make_waiting_guest

# The folder this file is in. File paths in config.json start from here.
BASE_FOLDER = Path(__file__).parent


def load_config():
    """Read the settings file config.json."""
    config_file = BASE_FOLDER / "config.json"
    if not config_file.exists():
        raise SystemExit(f"The settings file {config_file} could not be found.")
    with open(config_file, encoding="utf-8") as file:
        return json.load(file)


def data_file(settings, name):
    """The full path of a file listed in the 'files' section of config.json."""
    return BASE_FOLDER / settings["files"][name]


def ask(prompt):
    """Ask the user a question and return the answer without extra spaces."""
    return input(prompt).strip()


def show_menu(title, options):
    """Print a menu and return what the user chose."""
    print()
    print(title)
    for option in options:
        print("  " + option)
    return ask("Choose: ")


def ask_whole_number(prompt):
    """Ask for a whole number. Anything else is refused with a message."""
    text = ask(prompt)
    if not text.isdigit():
        raise ValueError(f"'{text}' is not a whole number.")
    return int(text)


# ------------------------------------------------------------------ floor plan (1.1)

def show_floor(state):
    """Print the floor and how many tables are taken."""
    print()
    print(floor_plan.floor_as_text(state["floor"]))
    occupied, total = floor_plan.occupancy(state["floor"])
    print(f"  Occupied {occupied} of {total} tables   (. free   X occupied)")


def seat_guests(state):
    """Seat a pending booking at a free table (recorded in the journal)."""
    code = ask("Table code (e.g. A4): ")
    reference = ask("Booking reference (e.g. BS-10432): ")
    print("  " + operations.seat(state, reference, code))


def free_table(state):
    """The guests have left: complete the booking at a table, which frees the table."""
    code = ask("Table code to free: ")
    reference = floor_plan.read_occupant(state["floor"], code)
    if reference is None:
        raise ValueError(f"Table {code.upper()} is already free.")
    print("  " + operations.complete(state, reference))


def check_table(state):
    """Show who is at one table."""
    code = ask("Table code: ")
    occupant = floor_plan.read_occupant(state["floor"], code)
    if occupant is None:
        print(f"  {code.upper()} is free.")
    else:
        print(f"  {code.upper()}: {occupant}")


def floor_menu(state):
    """The floor plan menu. It keeps going until the user chooses 0."""
    while True:
        choice = show_menu("FLOOR PLAN", ["1 Show floor", "2 Seat guests", "3 Free a table", "4 Check a table", "0 Back"])
        if choice == "0":
            return
        try:
            if choice == "1":
                show_floor(state)
            elif choice == "2":
                seat_guests(state)
            elif choice == "3":
                free_table(state)
            elif choice == "4":
                check_table(state)
            else:
                print("  Please choose 0 to 4.")
        except ValueError as error:          # a refused change: show the message and carry on
            print("  " + str(error))


# ------------------------------------------------------------------ member directory (1.2)

def list_members(state):
    """Print the directory in surname order."""
    print()
    print(member_directory.directory_report(state["directory"]))


def find_member(state):
    """Find a member by number with the binary search."""
    number = ask_whole_number("Member number: ")
    member, steps = member_directory.binary_search_by_number(state["directory"], number)
    total = len(state["directory"]["by_number"])
    if member is None:
        raise ValueError(f"There is no member {number} (checked {steps} of {total} members).")
    print(f"  {member['number']}  {member['first_name']} {member['surname']}  {member['phone']}")
    print(f"  Found in {steps} step(s) out of {total} members.")


def register_member(state):
    """Add a new member with the next free number (recorded in the journal)."""
    first_name = ask("First name: ")
    surname = ask("Surname: ")
    phone = ask("Phone (optional): ")
    member = operations.register_member(state, first_name, surname, phone)
    print(f"  Registered member {member['number']}: {first_name} {surname}.")


def members_menu(state):
    """The member directory menu."""
    while True:
        choice = show_menu(
            "MEMBER DIRECTORY",
            [
                "1 List members in surname order",
                "2 Find a member by number",
                "3 Register a new member",
                "0 Back"
            ]
        )
        if choice == "0":
            return
        try:
            if choice == "1":
                list_members(state)
            elif choice == "2":
                find_member(state)
            elif choice == "3":
                register_member(state)
            else:
                print("  Please choose 0 to 3.")
        except ValueError as error:
            print("  " + str(error))


# ------------------------------------------------------------------ waitlist (1.3)

def show_waitlist(state):
    """Print the queue from front to back (following the next links)."""
    guests = waitlist.read_forwards(state["waitlist"])
    if len(guests) == 0:
        print("  Nobody is waiting.")
    position = 1
    for guest in guests:
        print(f"  {position}. {guest['name']}  (party of {guest['party_size']})")
        position = position + 1


def show_waitlist_backwards(state):
    """Print the queue from back to front (following the prev links)."""
    guests = waitlist.read_backwards(state["waitlist"])
    if len(guests) == 0:
        print("  Nobody is waiting.")
    position = len(guests)
    for guest in guests:
        print(f"  {position}. {guest['name']}  (party of {guest['party_size']})")
        position = position - 1


def ask_guest():
    """Ask for a walk-in guest's details and return a guest record."""
    name = ask("Guest name: ")
    if name == "":
        raise ValueError("Enter the guest's name.")
    party_size = ask_whole_number("Party size: ")
    if party_size < 1:
        raise ValueError("Party size must be at least 1.")
    phone = ask("Phone (optional): ")
    return make_waiting_guest(name, party_size, phone)


def add_guest_at_end(state):
    """A walk-in joins the back of the queue (recorded in the journal)."""
    guest = ask_guest()
    print("  " + operations.waitlist_add(state, guest, state["waitlist"]["size"]))


def add_guest_at_front(state):
    """A regular goes straight to the front (recorded in the journal)."""
    guest = ask_guest()
    print("  " + operations.waitlist_add(state, guest, 0))


def add_guest_at_position(state):
    """Put a guest at a chosen position, 1 = front (recorded in the journal)."""
    position = ask_whole_number("Position (1 = front): ")
    guest = ask_guest()
    print("  " + operations.waitlist_add(state, guest, position - 1))


def remove_guest(state):
    """Remove a guest from anywhere in the queue (recorded in the journal)."""
    position = ask_whole_number("Position to remove (1 = front): ")
    print("  " + operations.waitlist_remove(state, position - 1))


def waitlist_menu(state):
    """The waitlist menu."""
    while True:
        choice = show_menu("WAITLIST", ["1 Show waitlist", "2 Show waitlist last to first", "3 Add a guest at the end", "4 Add a regular at the front", "5 Add a guest at a position", "6 Remove a guest", "0 Back"])
        if choice == "0":
            return
        try:
            if choice == "1":
                show_waitlist(state)
            elif choice == "2":
                show_waitlist_backwards(state)
            elif choice == "3":
                add_guest_at_end(state)
            elif choice == "4":
                add_guest_at_front(state)
            elif choice == "5":
                add_guest_at_position(state)
            elif choice == "6":
                remove_guest(state)
            else:
                print("  Please choose 0 to 6.")
        except ValueError as error:          # a refused change: show the message and carry on
            print("  " + str(error))


# ------------------------------------------------------------------ menu (1.4)

def list_dishes(state):
    """Print the whole menu in name order (an in-order traversal of the tree)."""
    for dish in menu_tree.in_order(state["menu"]):
        print(f"  {dish['name']:<22} {dish['category']:<10} ${dish['price']:.2f}")


def find_a_dish(state):
    """Find one dish by name and show how many dishes were visited."""
    name = ask("Dish name: ")
    dish, visited = menu_tree.find_dish(state["menu"], name)
    size = state["menu"]["size"]
    if dish is None:
        raise ValueError(f"'{name}' is not on the menu (visited {visited} of {size} dishes).")
    print(f"  {dish['name']} - {dish['description']} - ${dish['price']:.2f}")
    print(f"  Found after visiting {visited} of {size} dishes.")


def dishes_menu(state):
    """The restaurant menu screen."""
    while True:
        choice = show_menu("MENU", ["1 List the menu in name order", "2 Find a dish", "0 Back"])
        if choice == "0":
            return
        try:
            if choice == "1":
                list_dishes(state)
            elif choice == "2":
                find_a_dish(state)
            else:
                print("  Please choose 0 to 2.")
        except ValueError as error:
            print("  " + str(error))


# ------------------------------------------------------------------ bookings (1.5)

def list_bookings(state):
    """Print every booking."""
    for booking in booking_index.all_bookings(state["index"]):
        table = booking["table_code"]
        if table is None:
            table = ""
        print(f"  {booking['reference']}  {booking['guest_name']:<18} party of {booking['party_size']:<3}"
              f" {booking['status']:<10} {table}")


def show_booking(state):
    """Find one booking by its reference and show how it was hashed."""
    booking = operations.find_booking(state, ask("Booking reference: "))
    print(f"  {booking['reference']}  {booking['guest_name']}, party of {booking['party_size']},"
          f" came by {booking['source']}")
    print(f"  Status: {booking['status']}   Table: {booking['table_code']}   Notes: {booking['notes']}")
    print("  Hash: " + booking_index.explain_hash(booking["reference"], state["index"]["bucket_count"]))


def new_booking(state):
    """Take a new booking (recorded in the journal)."""
    member_number = None
    guest_name = ""
    member_text = ask("Member number (leave blank if not a member): ")
    if member_text == "":
        guest_name = ask("Guest name: ")
    else:
        if not member_text.isdigit():
            raise ValueError(f"'{member_text}' is not a member number.")
        member_number = int(member_text)          # operations fills in the member's name
    party_size = ask_whole_number("Party size: ")
    source = ask("Request came by (in person, email, phone): ").lower()
    notes = ask("Notes (optional): ")
    print("  " + operations.new_booking(state, guest_name, party_size, source, notes, member_number))


def change_status(state):
    """Seat, complete or cancel a booking (recorded in the journal)."""
    reference = ask("Booking reference: ")
    choice = ask("S = seat, C = complete, X = cancel: ").upper()
    if choice == "S":
        print("  " + operations.seat(state, reference, ask("Table code: ")))
    elif choice == "C":
        print("  " + operations.complete(state, reference))
    elif choice == "X":
        print("  " + operations.cancel(state, reference))
    else:
        raise ValueError("Please type S, C or X.")


def bookings_menu(state):
    """The bookings menu."""
    while True:
        choice = show_menu("BOOKINGS", ["1 List bookings", "2 Find a booking", "3 New booking", "4 Seat / complete / cancel", "0 Back"])
        if choice == "0":
            return
        try:
            if choice == "1":
                list_bookings(state)
            elif choice == "2":
                show_booking(state)
            elif choice == "3":
                new_booking(state)
            elif choice == "4":
                change_status(state)
            else:
                print("  Please choose 0 to 4.")
        except ValueError as error:          # a refused change: show the message and carry on
            print("  " + str(error))


# ------------------------------------------------------------------ journal and undo (1.6)

def show_journal(state):
    """Print the most recent journal entries, newest first."""
    print(f"  Changes are being recorded as staff {state['staff_code']}.")
    entries = journal.read_recent(state["journal"], state["settings"]["journal"]["recent_entries"])
    if len(entries) == 0:
        print("  The journal is empty.")
    for entry in entries:
        undone = ""
        if entry["cancelled"]:
            undone = "UNDONE"
        print(f"  {entry['entry_number']:>3}  {entry['timestamp']}  {entry['staff_code']}"
              f"  {entry['action']:<17} {entry['booking_reference']:<9} {undone}")


def undo_change(state):
    """Reverse the most recent change."""
    print("  " + operations.undo_last(state))


def change_staff(state):
    """Choose which staff member's code goes into the journal."""
    codes = state["settings"]["staff"]["codes"]
    code = ask(f"Staff code ({', '.join(codes)}): ").upper()
    if code not in codes:
        raise ValueError(f"'{code}' is not a staff code.")
    state["staff_code"] = code
    print(f"  Changes are now recorded as {code}.")


def journal_menu(state):
    """The journal and undo menu."""
    while True:
        choice = show_menu("JOURNAL AND UNDO", ["1 Show recent changes", "2 Undo the most recent change", "3 Change staff code", "0 Back"])
        if choice == "0":
            return
        try:
            if choice == "1":
                show_journal(state)
            elif choice == "2":
                undo_change(state)
            elif choice == "3":
                change_staff(state)
            else:
                print("  Please choose 0 to 3.")
        except ValueError as error:          # a refused change: show the message and carry on
            print("  " + str(error))


# ------------------------------------------------------------------ start-up

def build_state(settings):
    """Load the data files and build every data structure.

    Everything is kept in one dictionary called state, so each menu
    function only needs to be given one thing.
    """
    state = {"settings": settings}
    state["floor"] = floor_plan.create_floor(settings["floor"]["rows"], settings["floor"]["columns"])
    members = seed_loader.load_members(data_file(settings, "seed_members"))
    state["directory"] = member_directory.build_directory(members)
    state["waitlist"] = waitlist.new_waitlist()
    state["menu"] = menu_tree.new_menu()
    for dish in seed_loader.load_menu(data_file(settings, "seed_menu")):
        menu_tree.add_dish(state["menu"], dish)
    state["index"] = booking_index.new_index(settings["hash_table"]["buckets"])
    for booking in seed_loader.load_bookings(data_file(settings, "seed_bookings")):
        booking_index.index_add(state["index"], booking)
        if booking["status"] == "seated":
            floor_plan.assign_booking(state["floor"], booking["table_code"], booking["reference"])
    state["journal"] = journal.open_journal(data_file(settings, "journal"))
    state["undo"] = undo_stack.new_stack()
    state["staff_code"] = settings["staff"]["codes"][0]
    return state


def main():
    """Load the settings and data, then run the main menu until the user chooses 0."""
    settings = load_config()
    try:
        state = build_state(settings)
    except ValueError as error:                   # e.g. a missing or broken data file
        raise SystemExit("Bean Scene could not start: " + str(error))

    while True:
        choice = show_menu("BEAN SCENE", ["1 Floor plan", "2 Member directory", "3 Waitlist", "4 Menu", "5 Bookings", "6 Journal and undo", "0 Exit"])
        if choice == "0":
            break
        if choice == "1":
            floor_menu(state)
        elif choice == "2":
            members_menu(state)
        elif choice == "3":
            waitlist_menu(state)
        elif choice == "4":
            dishes_menu(state)
        elif choice == "5":
            bookings_menu(state)
        elif choice == "6":
            journal_menu(state)
        else:
            print("  Please choose 0 to 6.")
    journal.close_journal(state["journal"])      # close the file before the program ends
    print("Goodbye.")


if __name__ == "__main__":
    main()

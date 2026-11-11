"""Floor plan: the dining floor as a two-dimensional grid of tables.

The floor is a list of rows, and each row is a list of table records.
The floor size comes from config.json: rows A, B and C, with 10 tables
in each row, so table A4 is floor[0][3]. Change the rows or columns in
config.json and the same code gives a different floor.
"""

from beanscene.records import make_table


def create_floor(row_letters, column_count):
    """Build an empty floor: one row for each letter, column_count tables in each row."""
    floor = []
    for letter in row_letters:
        row = []
        for number in range(1, column_count + 1):
            row.append(make_table(letter + str(number), letter, number))
        floor.append(row)
    return floor


def parse_table_code(floor, code):
    """Turn a table code such as "A4" into its row and column positions, e.g. (0, 3).

    Raises ValueError if the code is not a table on this floor.
    """
    code = code.strip().upper()
    error_message = f"'{code}' is not a table on the floor plan."
    if len(code) < 2 or not code[1:].isdigit():
        raise ValueError(error_message)

    # Find which row has this letter
    row_index = -1
    for index in range(len(floor)):
        if floor[index][0]["row"] == code[0]:
            row_index = index
    if row_index == -1:
        raise ValueError(error_message)

    # Table 1 is at position 0 in the list, so take 1 away
    column_index = int(code[1:]) - 1
    if column_index < 0 or column_index >= len(floor[row_index]):
        raise ValueError(error_message)
    return row_index, column_index


def get_table(floor, code):
    """Return the table record for a code, e.g. get_table(floor, "A4")."""
    row_index, column_index = parse_table_code(floor, code)
    return floor[row_index][column_index]


def read_occupant(floor, code):
    """Return the booking reference seated at a table, or None if it is free."""
    table = get_table(floor, code)
    return table["booking_reference"]


def assign_booking(floor, code, booking_reference):
    """Seat a booking at a free table, changing the table record in place.

    Raises ValueError if the table is already occupied.
    """
    table = get_table(floor, code)
    if table["booking_reference"] is not None:
        # One booking per table is a business rule, so refuse rather than overwrite
        raise ValueError(f"Table {table['code']} is already occupied by {table['booking_reference']}.")
    table["booking_reference"] = booking_reference
    return table


def release_table(floor, code):
    """Free a table. Freeing a table that is already free is refused."""
    table = get_table(floor, code)
    if table["booking_reference"] is None:
        raise ValueError(f"Table {table['code']} is already free.")
    table["booking_reference"] = None
    return table


def occupancy(floor):
    """Return two numbers: how many tables are occupied, and how many there are."""
    total = 0
    occupied = 0
    for row in floor:
        for table in row:
            total = total + 1
            if table["booking_reference"] is not None:
                occupied = occupied + 1
    return occupied, total


def free_table_codes(floor):
    """Return a list of the codes of every free table."""
    codes = []
    for row in floor:
        for table in row:
            if table["booking_reference"] is None:
                codes.append(table["code"])
    return codes


def floor_as_text(floor):
    """Draw the floor as text: '.' is a free table and 'X' is an occupied one."""
    text = "     "
    for number in range(1, len(floor[0]) + 1):
        text = text + str(number).rjust(3)
    for row in floor:
        text = text + "\n  " + row[0]["row"] + "  "
        for table in row:
            if table["booking_reference"] is None:
                text = text + "  ."
            else:
                text = text + "  X"
    return text

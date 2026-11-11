"""Read the seed data files (CSV) supplied by the assessor.

Each loader checks the column headings first, then turns every row into a
record. Problems are reported with the file name and line number.
"""

import csv

from beanscene.records import make_booking, make_dish, make_member


def read_rows(path, expected_columns):
    """Read a CSV file and return its rows as a list of dictionaries."""
    if not path.exists():
        raise ValueError(f"The data file {path} could not be found.")
    with open(path, newline="", encoding="utf-8-sig") as data_file:
        reader = csv.DictReader(data_file)
        rows = list(reader)
        headings = reader.fieldnames
    if headings is None:
        headings = []
    for column in expected_columns:
        if column not in headings:
            raise ValueError(f"{path.name} is missing the column '{column}'.")
    return rows


def to_whole_number(text, field, file_name, line):
    """Turn text into a whole number, or report which line is wrong."""
    text = text.strip()
    if not text.isdigit():
        raise ValueError(f"{file_name} line {line}: {field} must be a whole number, not '{text}'.")
    return int(text)


def load_members(path):
    """Load the member records from members.csv."""
    members = []
    line = 1
    for row in read_rows(path, ["number", "first_name", "surname", "phone"]):
        line = line + 1
        number = to_whole_number(row["number"], "number", path.name, line)
        members.append(make_member(number, row["first_name"].strip(), row["surname"].strip(),
                                   row["phone"].strip()))
    return members


def load_menu(path):
    """Load the dish records from menu.csv."""
    dishes = []
    line = 1
    for row in read_rows(path, ["name", "category", "price", "description"]):
        line = line + 1
        try:
            price = float(row["price"])
        except ValueError:
            raise ValueError(f"{path.name} line {line}: price must be a number, not '{row['price']}'.")
        dishes.append(make_dish(row["name"].strip(), row["category"].strip(), price,
                                row["description"].strip()))
    return dishes


def load_bookings(path):
    """Load the booking records from bookings.csv. A blank member number means not a member."""
    loaded = []
    line = 1
    columns = ["reference", "guest_name", "member_number", "party_size", "source", "notes", "status", "table_code"]
    for row in read_rows(path, columns):
        line = line + 1
        member_number = None
        if row["member_number"].strip() != "":
            member_number = to_whole_number(row["member_number"], "member_number", path.name, line)
        party_size = to_whole_number(row["party_size"], "party_size", path.name, line)
        booking = make_booking(row["reference"].strip(), row["guest_name"].strip(), party_size,
                               row["source"].strip(), row["notes"].strip(), member_number)
        if row["status"].strip() != "":
            booking["status"] = row["status"].strip()
        if row["table_code"].strip() != "":
            booking["table_code"] = row["table_code"].strip()
        loaded.append(booking)
    return loaded

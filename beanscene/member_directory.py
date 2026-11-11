"""Member directory: a sorted list with a custom sort and a binary search.

The directory keeps two sorted lists of the same member records:

* "by_surname" - for printing. The custom sort ignores capitals,
  apostrophes and hyphens, so O'Brien, Obrien and O-Brien file together.
* "by_number"  - for searching. A binary search only works on the value
  the list is sorted by, so searching by number needs a list sorted by number.
"""

from tabulate import tabulate   # third-party library (MIT licence)


def surname_key(surname):
    """Return a surname ready for sorting: lower case, with no ' ’ or - in it.

    O'Brien, Obrien and O-Brien all give "obrien".
    """
    key = surname.lower()
    key = key.replace("'", "")
    key = key.replace("’", "")
    key = key.replace("-", "")
    return key


def sort_value(member, order):
    """The value a member is sorted on. order is "surname" or "number"."""
    if order == "number":
        return member["number"]
    return surname_key(member["surname"]) + " " + member["first_name"].lower()


def custom_sort(members, order):
    """Return a new list of members sorted by surname or by number (a custom sort).

    Find the member with the smallest sort value, move it to the end of the result, repeat.
    """
    remaining = list(members)
    result = []
    while len(remaining) > 0:
        smallest = 0
        for index in range(1, len(remaining)):
            if sort_value(remaining[index], order) < sort_value(remaining[smallest], order):
                smallest = index
        member = remaining.pop(smallest)
        result.append(member)
    return result


def build_directory(members):
    """Build the directory: the same members sorted two ways."""
    by_number = custom_sort(members, "number")
    for position in range(1, len(by_number)):
        if by_number[position]["number"] == by_number[position - 1]["number"]:
            raise ValueError(f"Member number {by_number[position]['number']} appears twice in the member file.")
    by_surname = custom_sort(members, "surname")
    return {"by_surname": by_surname, "by_number": by_number}


def binary_search_by_number(directory, number):
    """Find a member by number without checking every member.

    Returns two values: the member (or None if not found) and how many
    members were compared.
    """
    members = directory["by_number"]
    low = 0
    high = len(members) - 1
    steps = 0
    while low <= high:
        steps = steps + 1
        middle = (low + high) // 2
        if members[middle]["number"] == number:
            return members[middle], steps
        if members[middle]["number"] < number:
            low = middle + 1
        else:
            high = middle - 1
    return None, steps


def find_member(directory, number):
    """Return the member with this number, or None."""
    member, steps = binary_search_by_number(directory, number)
    return member


def next_member_number(directory):
    """Return the next unused member number: one more than the highest."""
    if len(directory["by_number"]) == 0:
        return 1001
    highest = directory["by_number"][-1]["number"]
    return highest + 1


def add_member(directory, member):
    """Add a member and sort both lists again (changes the directory in place)."""
    if member["first_name"] == "" or member["surname"] == "":
        raise ValueError("A member needs both a first name and a surname.")
    if find_member(directory, member["number"]) is not None:
        raise ValueError(f"Member number {member['number']} is already in use.")
    directory["by_surname"].append(member)
    directory["by_number"].append(member)
    directory["by_surname"] = custom_sort(directory["by_surname"], "surname")
    directory["by_number"] = custom_sort(directory["by_number"], "number")


def remove_member(directory, number):
    """Take a member out of both lists (undo uses this in step 1.6)."""
    member = find_member(directory, number)
    if member is not None:
        directory["by_surname"].remove(member)
        directory["by_number"].remove(member)


def directory_report(directory):
    """Return the directory, in surname order, as a printable table."""
    rows = []
    for member in directory["by_surname"]:
        rows.append([member["surname"], member["first_name"], member["number"], member["phone"]])
    return tabulate(rows, headers=["Surname", "First name", "Member no.", "Phone"])

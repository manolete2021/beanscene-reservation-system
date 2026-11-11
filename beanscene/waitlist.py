"""Waitlist: a doubly-linked list of walk-in guests.

Each node is a small dictionary that holds one guest and links to the node
before it ("prev") and the node after it ("next"). Adding or removing a
guest only changes the links of its neighbours, so nobody else moves.

    head                                     tail
     |                                         |
    [Rita] <-> [Ana] <-> [Dev] <-> [Ben] <-> [Cara]
"""


def new_waitlist():
    """Return an empty waitlist: no first node, no last node, size 0."""
    return {"head": None, "tail": None, "size": 0}


def make_node(guest):
    """Return a new node holding one guest, not linked to anything yet."""
    return {"guest": guest, "prev": None, "next": None}


def add_to_end(waitlist, guest):
    """Add a guest at the back of the queue."""
    node = make_node(guest)
    if waitlist["size"] == 0:
        # An empty list: the new node is both the first and the last
        waitlist["head"] = node
        waitlist["tail"] = node
    else:
        node["prev"] = waitlist["tail"]
        waitlist["tail"]["next"] = node
        waitlist["tail"] = node
    waitlist["size"] = waitlist["size"] + 1


def add_to_front(waitlist, guest):
    """Put a guest (a regular) at the front of the queue."""
    node = make_node(guest)
    if waitlist["size"] == 0:
        waitlist["head"] = node
        waitlist["tail"] = node
    else:
        node["next"] = waitlist["head"]
        waitlist["head"]["prev"] = node
        waitlist["head"] = node
    waitlist["size"] = waitlist["size"] + 1


def node_at(waitlist, index):
    """Return the node at a position (0 is the front) by following the next links."""
    if index < 0 or index >= waitlist["size"]:
        raise ValueError(f"There is no guest at position {index + 1}.")
    node = waitlist["head"]
    for step in range(index):
        node = node["next"]
    return node


def add_at(waitlist, index, guest):
    """Put a guest at a position: 0 is the front, size is the back."""
    if index < 0 or index > waitlist["size"]:
        raise ValueError(f"Position must be between 1 and {waitlist['size'] + 1}.")
    if index == 0:
        add_to_front(waitlist, guest)
    elif index == waitlist["size"]:
        add_to_end(waitlist, guest)
    else:
        after = node_at(waitlist, index)      # this guest moves back one place
        before = after["prev"]
        node = make_node(guest)
        node["prev"] = before
        node["next"] = after
        before["next"] = node
        after["prev"] = node
        waitlist["size"] = waitlist["size"] + 1


def remove_at(waitlist, index):
    """Remove the guest at a position (0 is the front) and return the guest."""
    node = node_at(waitlist, index)
    before = node["prev"]
    after = node["next"]

    # Link the two neighbours to each other; nobody else moves
    if before is None:
        waitlist["head"] = after         # we removed the first guest
    else:
        before["next"] = after
    if after is None:
        waitlist["tail"] = before        # we removed the last guest
    else:
        after["prev"] = before

    waitlist["size"] = waitlist["size"] - 1
    return node["guest"]


def read_forwards(waitlist):
    """Return the guests from front to back by following the next links."""
    guests = []
    node = waitlist["head"]
    while node is not None:
        guests.append(node["guest"])
        node = node["next"]
    return guests


def read_backwards(waitlist):
    """Return the guests from back to front by following the prev links."""
    guests = []
    node = waitlist["tail"]
    while node is not None:
        guests.append(node["guest"])
        node = node["prev"]
    return guests

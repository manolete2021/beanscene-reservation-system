"""Menu: a binary search tree of dishes, sorted by dish name.

Each node is a small dictionary with a dish and two links, "left" and
"right". A name that comes before the node's name in the alphabet goes to
the left; a name that comes after goes to the right. Finding a dish follows
one path down the tree, so it does not visit every dish.
"""


def new_menu():
    """Return an empty tree: no root node, size 0."""
    return {"root": None, "size": 0}


def make_node(dish):
    """Return a new tree node holding one dish, with no children yet."""
    return {"dish": dish, "left": None, "right": None}


def add_dish(menu, dish):
    """Add a dish to the tree. Each dish name may appear only once."""
    new_node = make_node(dish)
    if menu["root"] is None:
        menu["root"] = new_node
        menu["size"] = 1
        return

    name = dish["name"].lower()
    node = menu["root"]
    while True:
        node_name = node["dish"]["name"].lower()
        if name == node_name:
            raise ValueError(f"'{dish['name']}' is already on the menu.")
        if name < node_name:
            if node["left"] is None:
                node["left"] = new_node
                break
            node = node["left"]
        else:
            if node["right"] is None:
                node["right"] = new_node
                break
            node = node["right"]
    menu["size"] = menu["size"] + 1


def find_dish(menu, name):
    """Find a dish by name.

    Returns two values: the dish (or None) and how many nodes were visited.
    """
    name = name.strip().lower()
    node = menu["root"]
    visited = 0
    while node is not None:
        visited = visited + 1
        node_name = node["dish"]["name"].lower()
        if name == node_name:
            return node["dish"], visited
        if name < node_name:
            node = node["left"]
        else:
            node = node["right"]
    return None, visited


def in_order(menu):
    """Return every dish in name order, using an in-order traversal."""
    dishes = []
    visit(menu["root"], dishes)
    return dishes


def visit(node, dishes):
    """In-order: visit the left side, then this dish, then the right side."""
    if node is None:
        return
    visit(node["left"], dishes)
    dishes.append(node["dish"])
    visit(node["right"], dishes)

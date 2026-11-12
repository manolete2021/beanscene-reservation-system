"""Menu screen: the dishes in name order, and a search along one path of the tree.

Uses the menu tree (1.4): in_order lists every dish from A to Z, and
find_dish follows one path, so it does not visit every dish.
"""

from tkinter import ttk

from beanscene import menu_tree
from beanscene import gui_look

screen = {}


def build(parent, state, bar):
    """Create the menu screen inside parent (one tab of the window)."""
    screen["state"] = state
    screen["bar"] = bar

    menu_box = ttk.LabelFrame(parent, text="The menu, in name order", padding=gui_look.PAD)
    menu_box.grid(row=0, column=0, sticky="nsew", padx=(0, gui_look.PAD))
    screen["tree"] = ttk.Treeview(menu_box, columns=("dish", "category", "price"), show="headings", height=14)
    screen["tree"].heading("dish", text="Dish")
    screen["tree"].heading("category", text="Category")
    screen["tree"].heading("price", text="Price")
    screen["tree"].grid(row=0, column=0, sticky="nsew", padx=gui_look.PAD, pady=gui_look.PAD)

    find_box = ttk.LabelFrame(parent, text="Find a dish", padding=gui_look.PAD)
    find_box.grid(row=0, column=1, sticky="nsew")
    screen["dish_name"] = gui_look.labelled_entry(find_box, 0, "Dish name", 24)
    find = ttk.Button(find_box, text="Find dish", style="Accent.TButton", command=find_a_dish)
    find.grid(row=1, column=1, sticky="we", padx=gui_look.PAD, pady=(8, 4))
    screen["details"] = ttk.Label(find_box, text="", wraplength=280, justify="left")
    screen["details"].grid(row=2, column=0, columnspan=2, sticky="w", padx=gui_look.PAD, pady=(8, 0))
    screen["visits"] = ttk.Label(find_box, text="", style="Muted.TLabel")
    screen["visits"].grid(row=3, column=0, columnspan=2, sticky="w", padx=gui_look.PAD, pady=(4, 0))
    refresh()


def find_a_dish():
    """Find dish button: search by name and show how many dishes were visited."""
    name = screen["dish_name"].get().strip()
    if name == "":
        gui_look.show_error(screen["bar"], "Enter a dish name.")
        return
    dish, visited = menu_tree.find_dish(screen["state"]["menu"], name)
    size = screen["state"]["menu"]["size"]
    if dish is None:
        selected = screen["tree"].selection()
        if len(selected) > 0:
            screen["tree"].selection_remove(selected)
        screen["details"].configure(text="")
        screen["visits"].configure(text="")
        gui_look.show_error(screen["bar"], f"'{name}' is not on the menu (visited {visited} of {size} dishes).")
        return
    price = f"${dish['price']:.2f}"
    screen["details"].configure(text=f"{dish['name']}: {dish['description']}, {price}")
    screen["visits"].configure(text=f"Found after visiting {visited} of {size} dishes.")
    screen["tree"].selection_set(dish["name"])
    screen["tree"].see(dish["name"])
    gui_look.show_success(screen["bar"], f"{dish['name']}: {dish['description']}, {price}")


def refresh():
    """Fill the menu in name order. The tree is already sorted."""
    gui_look.clear_tree(screen["tree"])
    for dish in menu_tree.in_order(screen["state"]["menu"]):
        screen["tree"].insert("", "end", iid=dish["name"],
                              values=(dish["name"], dish["category"], f"${dish['price']:.2f}"))

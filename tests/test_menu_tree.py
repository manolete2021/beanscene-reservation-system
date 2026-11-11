"""Tests for the binary-tree menu."""

from pathlib import Path

import pytest

from beanscene import menu_tree, seed_loader
from beanscene.records import make_dish

MENU_FILE = Path(__file__).parent.parent / "data" / "seed" / "menu.csv"


@pytest.fixture
def menu():
    tree = menu_tree.new_menu()
    for dish in seed_loader.load_menu(MENU_FILE):
        menu_tree.add_dish(tree, dish)
    return tree


def test_in_order_lists_dishes_in_name_order(menu):
    names = [dish["name"] for dish in menu_tree.in_order(menu)]
    assert names == sorted(names, key=str.lower)
    assert len(names) == menu["size"] == 14


def test_find_dish_without_visiting_every_node(menu):
    dish, visited = menu_tree.find_dish(menu, "pavlova")
    assert dish["name"] == "Pavlova"
    assert visited < menu["size"]


def test_missing_dish_is_not_found(menu):
    dish, visited = menu_tree.find_dish(menu, "Pizza")
    assert dish is None and visited >= 1


def test_duplicate_dish_is_refused(menu):
    with pytest.raises(ValueError, match="already on the menu"):
        menu_tree.add_dish(menu, make_dish("PAVLOVA", "Dessert", 1.0))

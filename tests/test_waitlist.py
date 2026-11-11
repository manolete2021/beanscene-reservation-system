"""Tests for the doubly-linked waitlist."""

import pytest

from beanscene import waitlist
from beanscene.records import make_waiting_guest


def names(guests):
    return [guest["name"] for guest in guests]


@pytest.fixture
def queue():
    """Ana, Ben, Cara, Dev waiting, in that order."""
    new_queue = waitlist.new_waitlist()
    for name in ["Ana", "Ben", "Cara", "Dev"]:
        waitlist.add_to_end(new_queue, make_waiting_guest(name, 2))
    return new_queue


def test_add_regular_at_front(queue):
    waitlist.add_to_front(queue, make_waiting_guest("Regular Rita", 2))
    assert names(waitlist.read_forwards(queue)) == ["Regular Rita", "Ana", "Ben", "Cara", "Dev"]


def test_remove_from_middle_moves_nobody_else(queue):
    cara_node = waitlist.node_at(queue, 2)
    removed = waitlist.remove_at(queue, 1)              # Ben
    assert removed["name"] == "Ben"
    assert names(waitlist.read_forwards(queue)) == ["Ana", "Cara", "Dev"]
    assert waitlist.node_at(queue, 1) is cara_node      # the same node - only links changed


def test_reads_forwards_and_backwards(queue):
    waitlist.add_at(queue, 2, make_waiting_guest("Eli", 3))
    assert names(waitlist.read_forwards(queue)) == ["Ana", "Ben", "Eli", "Cara", "Dev"]
    assert names(waitlist.read_backwards(queue)) == ["Dev", "Cara", "Eli", "Ben", "Ana"]


def test_remove_head_tail_until_empty(queue):
    waitlist.remove_at(queue, 0)
    waitlist.remove_at(queue, queue["size"] - 1)
    assert names(waitlist.read_forwards(queue)) == ["Ben", "Cara"]
    waitlist.remove_at(queue, 0)
    waitlist.remove_at(queue, 0)
    assert queue["head"] is None and queue["tail"] is None and queue["size"] == 0


def test_bad_positions_are_refused(queue):
    with pytest.raises(ValueError):
        waitlist.remove_at(queue, 4)
    with pytest.raises(ValueError):
        waitlist.add_at(queue, 6, make_waiting_guest("Xavier", 1))
